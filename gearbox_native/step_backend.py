"""Historical STEP-backed diagnostic; never used by the native publisher.

This is not the helper's native feature backend. Recipe parameters remain in
Python/YAML; the saved SolidCraft documents contain imported exact BRep solids.
No mesh import, tolerance increase, cutter displacement or shape healing is used.
"""
import math
from pathlib import Path

from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon, BRepBuilderAPI_Transform
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeCone, BRepPrimAPI_MakePrism, BRepPrimAPI_MakeRevol
from OCP.IFSelect import IFSelect_RetDone
from OCP.Interface import Interface_Static
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCP.TopTools import TopTools_ListOfShape
from OCP.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Dir, gp_Ax1

from oobb_solidcraft.backend import require_ok, health_check
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.runtime import write_json, digest
from oobb_solidcraft.validation import inspect_shape, verify_mesh, verify_native_measurement
from gearbox_native.verification import verify_step


from gearbox_native.exact_geometry import build_shape


def render(thing, *, plan, output_dir, export_stl, export_extras, verify_solidcraft=False):
    output=Path(output_dir)
    shape=build_shape(plan['tree'])
    geometry=inspect_shape(shape)
    if not geometry['valid'] or geometry['solid_count']!=1:
        raise RuntimeError('Each printed gearbox piece must be one valid solid')
    print('  exact BRep constructed',flush=True)
    writer=STEPControl_Writer()
    # 3D curves fully define this analytic BRep. Omitting duplicate surface
    # pcurves substantially reduces dense rotor STEP parsing cost. Geometry
    # still has to pass exact comparison after the entire SolidCraft roundtrip.
    previous=Interface_Static.IVal_s('write.surfacecurve.mode')
    Interface_Static.SetIVal_s('write.surfacecurve.mode',0)
    try:
        if writer.Transfer(shape,STEPControl_AsIs)!=IFSelect_RetDone or writer.Write(str(output/'source.step'))!=IFSelect_RetDone:
            raise RuntimeError('Exact STEP source export failed')
    finally:
        Interface_Static.SetIVal_s('write.surfacecurve.mode',previous)
    checks={'source_step':dict(sha256=digest(output/'source.step'),
        acceptance='checked end-to-end by SolidCraft STEP export versus the constructed BRep')}
    with MCPClient(output/'session',design=output/'source.step',allow_path=output,timeout=600) as client:
        version=client.initialized['serverInfo']['version']
        health_check(client,output/'native_inspection.json')
        checks['native']=verify_native_measurement(require_ok(client.call('measure')),shape)
        require_ok(client.call('save',{'path':str(output/'generated.solidcraft')}))
        # STEP is always produced privately for acceptance, even if the user
        # chooses not to publish extra formats.
        require_ok(client.call('export',{'path':str(output/'generated.step')}))
        if export_stl:require_ok(client.call('export',{'path':str(output/'generated.stl')}))
        if export_extras:
            require_ok(client.call('screenshot',{'source':'model','view':'iso','path':str(output/'native.png'),
                'width':1100,'height':760,'grid':False,'axes':False}))
    checks['step']=verify_step(output/'generated.step',shape)
    print('  SolidCraft STEP roundtrip checked',flush=True)
    if export_stl:checks['stl']=verify_mesh(output/'generated.stl',shape)
    with MCPClient(output/'reopen',design=output/'generated.solidcraft',allow_path=output,timeout=600) as client:
        health_check(client,output/'reopened_inspection.json')
        checks['reopened']=verify_native_measurement(require_ok(client.call('measure')),shape)
        require_ok(client.call('export',{'path':str(output/'reopened.step')}))
    def step_data(path):
        return path.read_text(encoding='utf-8').split('DATA;',1)[1].split('ENDSEC;',1)[0]
    if step_data(output/'generated.step')==step_data(output/'reopened.step'):
        checks['reopened_step']=dict(comparison_method='byte_identical_verified_STEP_DATA',
            verification_inherited_from='step',sha256=digest(output/'reopened.step'))
    else:
        checks['reopened_step']=verify_step(output/'reopened.step',shape)
    write_json(output/'measurements.json',checks)
    write_json(output/'cad_structure.json',dict(construction='step_backed',native_feature_history=False,
        parameter_source='gearbox_native/*.yaml and working.yaml; regenerate after edits',
        body_count=1,profile_vertices_preserved=True))
    formats=['solidcraft']+(['step'] if export_extras else [])+(['stl'] if export_stl else [])
    return dict(construction='step_backed',backend_version=version,
        artifacts=[dict(path=str(output/('generated.'+ext)),sha256=digest(output/('generated.'+ext)),format=ext) for ext in formats],
        verification=dict(enabled=True,status='passed',native_feature_edit='not applicable to imported BRep'),
        measurements=str(output/'measurements.json'))
