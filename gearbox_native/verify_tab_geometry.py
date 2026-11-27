"""Check native M6 bores and hardware envelopes against actual casing STEP bodies."""
import json
import math
from pathlib import Path
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepGProp import BRepGProp
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCP.GProp import GProp_GProps
from OCP.GeomAbs import GeomAbs_Cylinder
from OCP.TopAbs import TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS
from OCP.gp import gp_Ax2,gp_Pnt,gp_Dir
from gearbox_native.verification import read_step
from gearbox_native.verify_tab_rule import smallest_plate
from gearbox_native.acceptance import LINEAR_MM


def check(shapes,v,output):
    radius=v['tab_radius'];seam=v['seam_z'];depth=v['tab_depth']
    assert v['tab_plate_size']==smallest_plate(v['casing_radius'],v['tab_m6_envelope_radius'],v['tab_m6_clearance'])
    positions=[(sign*radius,y) for sign in (-1,1) for y in (-15,15)]
    positions += [(x,sign*radius) for sign in (-1,1) for x in (-15,15)]
    # Match the existing project fit.py contact-volume policy. Native Boolean
    # retries can move faces by fractions of a micron; exact decimal equality
    # is not the project's geometry acceptance criterion.
    volume_threshold=.03
    report=dict(status='running',plate_size=v['tab_plate_size'],tab_radius=radius,parameters=v,bodies={},
                bore_position_tolerance_mm=LINEAR_MM,overlap_tolerance_mm3=volume_threshold)
    for name,shape in shapes.items():
        faces=TopExp_Explorer(shape,TopAbs_FACE);bores=[]
        while faces.More():
            face=TopoDS.Face_s(faces.Current());faces.Next();surface=BRepAdaptor_Surface(face)
            if surface.GetType()!=GeomAbs_Cylinder:continue
            cylinder=surface.Cylinder()
            if abs(cylinder.Radius()-3.25)<1e-5:
                axis=cylinder.Axis();p=axis.Location()
                if abs(axis.Direction().Z())>.99999:bores.append((p.X(),p.Y()))
        checks=[];bore_errors=[]
        for x,y in positions:
            error=min(math.hypot(x-a,y-b) for a,b in bores)
            assert error<LINEAR_MM,(name,x,y,error)
            bore_errors.append(error)
            for kind,r,z,h in [
                ('M6_shank',3.,-10.,v['housing_top']+20),
                ('head_or_nut_above',v['tab_m6_envelope_radius']+v['tab_m6_clearance'],seam+depth,6.2),
                ('head_or_nut_below',v['tab_m6_envelope_radius']+v['tab_m6_clearance'],seam-depth-6.2,6.2)]:
                tool=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(0,0,1)),r,h).Shape()
                intersection=BRepAlgoAPI_Common(shape,tool);assert intersection.IsDone()
                props=GProp_GProps();BRepGProp.VolumeProperties_s(intersection.Shape(),props)
                volume=abs(props.Mass());assert volume<volume_threshold,(name,x,y,kind,volume)
                checks.append(dict(position=[x,y],envelope=kind,overlap_mm3=volume))
        report['bodies'][name]=dict(outer_holes=8,max_bore_position_error_mm=max(bore_errors),hardware_checks=checks)
    report['status']='passed'
    Path(output).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Verified eight outer M6 holes per casing half and',sum(len(r['hardware_checks']) for r in report['bodies'].values()),'native hardware clearance checks')
    return report


def verify(folder,code=6812):
    folder=Path(folder)
    record=json.loads((folder/'casing_verification.json').read_text(encoding='utf-8'))['cases'][str(code)]
    v=dict(record['derived'],**record['tabs'])
    shapes={name:read_step(folder/f'bearing_{code}'/(name+'.step'))
            for name in ('output_casing_lower','output_casing_upper')}
    return check(shapes,v,folder/'tab_geometry.json')


def verify_default(folder,views):
    from gearbox_native.exact_geometry import _move
    folder,views=Path(folder),Path(views)
    export=json.loads((views/'export.json').read_text(encoding='utf-8'))
    v={p['name']:p['value'] for p in export['parameters']['parameters']}
    shapes={}
    for name in ('output_casing_lower','output_casing_upper'):
        shape=read_step(views/'parts'/(name+'.step'))
        # Local STEP exports sit on their split/print faces. Return to assembly.
        if name.endswith('lower'):shape=_move(shape,'rotate',[180,0,0])
        shapes[name]=_move(shape,'translate',[0,0,v['seam_z']])
    return check(shapes,v,folder/'default_tab_geometry.json')


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('folder');p.add_argument('--code',type=int,default=6812);p.add_argument('--views')
    args=p.parse_args();verify(args.folder,args.code)
    if args.views:verify_default(args.folder,args.views)
