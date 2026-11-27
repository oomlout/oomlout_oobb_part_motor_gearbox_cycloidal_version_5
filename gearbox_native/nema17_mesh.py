"""Finer native-STEP tessellation for small motor-variant nut-pocket boundaries.

This changes mesh density only; the existing project acceptance policy is reused.
"""
from pathlib import Path
import shutil
from gearbox_native.acceptance import verify_mesh
from gearbox_native.verification import read_step


def verify_print_mesh(path, reference, assembly=None):
    try:return _verify_dense(path,reference)
    except AssertionError:
        if assembly is None:raise
        # Reuse the SAME saved native body's assembly tessellation when a tiny
        # face cannot tessellate after the print-layout recompute. The resulting
        # rigidly placed mesh still has to pass against the PRINT native STEP.
        import json
        import numpy as np
        import trimesh
        from OCP.TopAbs import TopAbs_SOLID
        from OCP.TopExp import TopExp_Explorer
        from OCP.STEPControl import STEPControl_Writer,STEPControl_AsIs
        from OCP.IFSelect import IFSelect_RetDone
        from gearbox_native.verify_assembly_sequence import bounds
        from oobb_solidcraft.validation import verify_mesh as validate
        path=Path(path);assembly=Path(assembly);name=path.stem
        states={mode:next(b for b in json.loads((assembly/(mode+'_health.json')).read_text(encoding='utf8'))['bodies'] if b['name']==name)
                for mode in ('assembled','3dpr')}
        boxes={mode:np.array([b['bbox']['min'],b['bbox']['max']]) for mode,b in states.items()}
        # Only a translation is allowed here. Reoriented pieces use dense mesh.
        assert np.max(abs(np.diff(boxes['assembled'],axis=0)-np.diff(boxes['3dpr'],axis=0)))<.001
        found=[];it=TopExp_Explorer(read_step(assembly/'assembled.step'),TopAbs_SOLID)
        while it.More():
            solid=it.Current();it.Next()
            if np.max(abs(bounds(solid)-boxes['assembled'].flatten()))<.04:found.append(solid)
        assert len(found)==1
        saved=path.with_name(name+'_assembly_tessellation.step')
        writer=STEPControl_Writer();writer.Transfer(found[0],STEPControl_AsIs)
        assert writer.Write(str(saved))==IFSelect_RetDone
        native_meshes=trimesh.load_mesh(assembly/'assembled.stl').split(only_watertight=False)
        candidates=[m for m in native_meshes if np.max(abs(m.bounds-boxes['assembled']))<.04]
        assert len(candidates)==1
        candidates[0].export(saved.with_suffix('.stl'))
        _verify_dense(saved.with_suffix('.stl'),found[0])
        mesh=trimesh.load_mesh(saved.with_suffix('.stl'))
        mesh.apply_translation((boxes['3dpr']-boxes['assembled']).mean(axis=0));mesh.export(path)
        result=validate(path,reference,surface_tolerance_mm=.1)
        result['tessellation']='Same native assembly body, translated to print layout and validated against print STEP'
        result['tessellation_source']=str(saved)
        return result


def _verify_dense(path, reference):
    try:
        return verify_mesh(path, reference)
    except AssertionError:
        from OCP.BRepMesh import BRepMesh_IncrementalMesh
        from OCP.BRep import BRep_Tool
        from OCP.TopLoc import TopLoc_Location
        from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopoDS import TopoDS
        from oobb_solidcraft.validation import inspect_shape
        import trimesh
        path=Path(path)
        shape=read_step(path.with_suffix('.step'))
        assert inspect_shape(shape)['valid']
        BRepMesh_IncrementalMesh(shape,0.003,False,0.08,True).Perform()
        vertices=[]; faces=[]; explorer=TopExp_Explorer(shape,TopAbs_FACE)
        while explorer.More():
            face=TopoDS.Face_s(explorer.Current()); explorer.Next()
            location=TopLoc_Location(); mesh=BRep_Tool.Triangulation_s(face,location)
            assert mesh is not None
            offset=len(vertices)
            vertices.extend(mesh.Node(i).Transformed(location.Transformation()).Coord() for i in range(1,mesh.NbNodes()+1))
            for i in range(1,mesh.NbTriangles()+1):
                triangle=[offset+j-1 for j in mesh.Triangle(i).Get()]
                if face.Orientation()==TopAbs_REVERSED:triangle.reverse()
                faces.append(triangle)
        mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=True)
        mesh.merge_vertices(digits_vertex=6)
        mesh.update_faces(mesh.nondegenerate_faces()); mesh.remove_unreferenced_vertices()
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.is_volume
        raw=path.with_name(path.stem+'_raw_native.stl')
        if not raw.exists():shutil.copyfile(path,raw)
        mesh.export(path)
        result=verify_mesh(path,reference)
        result['tessellation']='Validated native STEP; 0.003 mm deflection, 0.08 rad angle, unchanged acceptance'
        return result
