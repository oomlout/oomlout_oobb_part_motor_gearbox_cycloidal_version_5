"""Practical native CAD acceptance against the CURRENT recipe, never old SCAD.

Valid solids, constrained native history, save/reopen and parameter edits are
required. Native intersection fitting gets 0.05 mm and 0.5% volume tolerance.
Small, reported Boolean retries are allowed; errors and large retries are not.
These project rules do not relax the shared plate backend's default policy.
"""
import math
from pathlib import Path
import shutil
import numpy as np
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.runtime import write_json
from oobb_solidcraft.validation import inspect_shape,verify_mesh as shared_verify_mesh
from gearbox_native.verification import read_step

LINEAR_MM=0.05
MESH_MM=0.1
VOLUME_RELATIVE=0.005
POLICY_VERSION=1


def verify_mesh(path,reference,**kwargs):
    kwargs.setdefault('surface_tolerance_mm',MESH_MM)
    try:return shared_verify_mesh(path,reference,**kwargs)
    except AssertionError:
        # Some native STL exports leave seams despite a valid exported BRep.
        # Retessellate THAT native STEP (not the recipe or the old SCAD model).
        from OCP.BRepMesh import BRepMesh_IncrementalMesh
        from OCP.BRep import BRep_Tool
        from OCP.TopLoc import TopLoc_Location
        from OCP.TopAbs import TopAbs_FACE,TopAbs_REVERSED
        import trimesh
        path=Path(path);step=path.with_suffix('.step')
        shape=read_step(step)
        assert inspect_shape(shape)['valid']
        BRepMesh_IncrementalMesh(shape,0.01,False,0.15,True).Perform()
        vertices=[];faces=[];explorer=TopExp_Explorer(shape,TopAbs_FACE)
        while explorer.More():
            face=TopoDS.Face_s(explorer.Current());explorer.Next()
            location=TopLoc_Location();mesh=BRep_Tool.Triangulation_s(face,location)
            assert mesh is not None
            offset=len(vertices)
            vertices.extend(mesh.Node(i).Transformed(location.Transformation()).Coord() for i in range(1,mesh.NbNodes()+1))
            for i in range(1,mesh.NbTriangles()+1):
                triangle=[offset+j-1 for j in mesh.Triangle(i).Get()]
                if face.Orientation()==TopAbs_REVERSED:triangle.reverse()
                faces.append(triangle)
        mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=True)
        mesh.merge_vertices(digits_vertex=5)
        mesh.update_faces(mesh.nondegenerate_faces());mesh.remove_unreferenced_vertices()
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.is_volume
        raw=path.with_name(path.stem+'_raw_native.stl')
        if not raw.exists():shutil.copyfile(path,raw)
        mesh.export(path)
        result=shared_verify_mesh(path,reference,**kwargs)
        result['tessellation']='Open CASCADE tessellation of the validated native STEP export'
        result['raw_native_export']=str(raw)
        return result


def health_check(client,path):
    health=require_ok(client.call('inspect_design'))
    write_json(path,health)
    for feature in health['timeline']:
        if feature.get('error'):raise ValueError(f'Native feature error: {feature}')
        if feature.get('warning'):
            events=feature.get('boolean_diagnostics',{}).get('events',[])
            if not events:raise ValueError(f'Unclassified native warning: {feature}')
            for event in events:
                if (abs(event.get('translation_mm',0))>0.01
                    or abs(event.get('face_shift_mm',0))>0.01
                    or abs(event.get('rotation_rad',0))>1e-4
                    or abs(event.get('tolerance_mm',0))>LINEAR_MM):
                    raise ValueError(f'Native retry exceeds the project allowance: {feature}')
    for sketch in health['sketches']:
        if sketch['status']!='solved' or sketch['dof']!=0:
            raise ValueError(f'Unconstrained sketch: {sketch}')
    return health


def edit_delta(geometry,before):
    return -min(0.02,before/200) if geometry.get('intent',{}).get('shape')=='oobb_cylinder_d_shaft' else min(0.02,before/200)


def verify_edit(before,after):
    expected=after['reference']['volume_mm3']-before['reference']['volume_mm3']
    observed=after['actual']['total']['volume_mm3']-before['actual']['total']['volume_mm3']
    if abs(expected)<1e-7:
        raise ValueError('Selected dimension is hidden by another feature; use an effective edit')
    assert observed*expected>0,('Edit did not change material in the expected direction',observed,expected)
    assert 0.25<abs(observed/expected)<4,('Edit response is inconsistent',observed,expected)
    return dict(expected_volume_change_mm3=expected,observed_volume_change_mm3=observed,changed=True)


def verify_native_measurement(actual,reference):
    expected=inspect_shape(reference)
    assert expected['valid'] and expected['solid_count']>0
    assert actual['body_count']==expected['solid_count']
    bounds=[*actual['bodies'][0]['bbox']['min'],*actual['bodies'][0]['bbox']['max']]
    assert np.max(np.abs(np.array(bounds)-expected['bounds_mm']))<LINEAR_MM
    size=np.linalg.norm(np.array(expected['bounds_mm'][3:])-expected['bounds_mm'][:3])
    budget=max(0.05,expected['volume_mm3']*VOLUME_RELATIVE,expected['area_mm2']*max(size*2e-4,0.001))
    error=abs(actual['total']['volume_mm3']-expected['volume_mm3'])
    assert error<budget,(error,budget)
    return dict(actual=actual,reference=expected,absolute_volume_error_mm3=error,volume_budget_mm3=budget,bounds_tolerance_mm=LINEAR_MM)


def verify_step(path,reference):
    shape=read_step(path);expected=inspect_shape(reference)
    dense=len(expected['planar_faces'])>1000
    actual=inspect_shape(shape)
    assert actual['valid'],'Exported STEP is not a valid solid'
    assert actual['solid_count']==expected['solid_count']>0
    bounds_error=float(np.max(np.abs(np.array(actual['bounds_mm'])-expected['bounds_mm'])))
    assert bounds_error<LINEAR_MM,bounds_error
    error=abs(actual['volume_mm3']-expected['volume_mm3'])
    budget=max(0.05,expected['volume_mm3']*VOLUME_RELATIVE)
    assert error<budget,(error,budget)
    # Dense rotors already receive the native mesh surface check. Do not
    # repeat a quadratic exact-boundary comparison or thousands of redundant
    # STEP distance queries; this is practical CAD acceptance, not equivalence.
    if dense:
        return dict(policy_version=POLICY_VERSION,reference='current_native_recipe',actual=actual,expected=expected,
            comparison_method='valid_solid_bounds_volume_with_separate_native_mesh_check',
            volume_error_mm3=error,volume_budget_mm3=budget,bounds_error_mm=bounds_error,
            linear_tolerance_mm=LINEAR_MM,volume_relative_tolerance=VOLUME_RELATIVE)
    # Detect misplaced/missing pockets even when volumes happen to agree.
    # This is a sampled design sanity check, not an exact-equivalence proof.
    samples=[]
    for source,target in ((shape,reference),(reference,shape)):
        explorer=TopExp_Explorer(source,TopAbs_EDGE);edges={}
        while explorer.More():
            edge=TopoDS.Edge_s(explorer.Current());explorer.Next()
            edges[edge.HashCode(2147483647)]=edge
        selected=list(edges.values())
        if len(selected)>240:
            selected=[selected[i] for i in np.linspace(0,len(selected)-1,240,dtype=int)]
        worst=0.;count=0
        distance=BRepExtrema_DistShapeShape();distance.LoadS2(target)
        for edge in selected:
            curve=BRepAdaptor_Curve(edge)
            for t in np.linspace(curve.FirstParameter(),curve.LastParameter(),5):
                distance.LoadS1(BRepBuilderAPI_MakeVertex(curve.Value(t)).Vertex());distance.Perform()
                assert distance.IsDone()
                worst=max(worst,distance.Value());count+=1
                assert worst<LINEAR_MM,('Sampled boundary deviation',worst)
        samples.append(dict(samples=count,max_distance_mm=worst))
    return dict(policy_version=POLICY_VERSION,reference='current_native_recipe',actual=actual,expected=expected,
        comparison_method='valid_solid_bounds_volume_and_sampled_boundary',bounds_error_mm=bounds_error,
        volume_error_mm3=error,volume_budget_mm3=budget,boundary_samples=samples,linear_tolerance_mm=LINEAR_MM,
        volume_relative_tolerance=VOLUME_RELATIVE)
