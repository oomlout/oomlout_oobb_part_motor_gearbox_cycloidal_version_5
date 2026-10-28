"""Native casing-bearing edits, exports and reopen checks; no fit certification."""
import argparse
import hashlib
import json
from pathlib import Path

from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.registry import discover
from oobb_solidcraft.validation import inspect_shape
from gearbox_native.acceptance import health_check, verify_mesh
from gearbox_native.verification import read_step
from gearbox_native.native_v7 import PRINT_POSITIONS
from gearbox_native.parts import bearing_spec


def verify_seat_faces(folder):
    """Measure the actual exported cylindrical faces, independently of parameters."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.BRepBndLib import BRepBndLib
    from OCP.Bnd import Bnd_Box
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS
    from OCP.GeomAbs import GeomAbs_Cylinder
    folder=Path(folder);report={}
    for code in (6710,6811):
        spec=bearing_spec(str(code));row={}
        for name in ('motor_mount','pin_front','output_casing_lower','output_casing_upper'):
            shape=read_step(folder/f'bearing_{code}'/(name+'.step'))
            explorer=TopExp_Explorer(shape,TopAbs_FACE);cylinders=[]
            while explorer.More():
                face=TopoDS.Face_s(explorer.Current());explorer.Next()
                surface=BRepAdaptor_Surface(face)
                if surface.GetType()!=GeomAbs_Cylinder:continue
                box=Bnd_Box();BRepBndLib.Add_s(face,box)
                bounds=box.Get()
                cylinders.append(dict(radius=surface.Cylinder().Radius(),z_min=bounds[2],z_max=bounds[5]))
            radius=spec['od']/2+.1 if name.startswith('output_casing') else spec['id']/2-.1
            matches=[c for c in cylinders if abs(c['radius']-radius)<1e-5]
            assert matches,(code,name,radius)
            if name.startswith('output_casing'):
                height=max(c['z_max'] for c in matches)-min(c['z_min'] for c in matches)
                expected=spec['depth']+(.31 if name.endswith('upper') else -.09)
                assert abs(height-expected)<.001,(code,name,height,expected)
            row[name]=dict(expected_radius=radius,faces=matches)
        report[str(code)]=row
    (folder/'seat_verification.json').write_text(json.dumps(dict(status='passed',cases=report),indent=2),encoding='utf-8')
    return report


def verify(folder, codes):
    folder=Path(folder).resolve();source=folder/'gearbox.solidcraft'
    report_path=folder/'casing_verification.json'
    report=json.loads(report_path.read_text()) if report_path.exists() else dict(cases={})
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    assert report.get('source_sha256',digest)==digest
    report.update(source_sha256=digest,status='running',mechanical_fit_checked=False)
    profile=json.loads((folder/'profile.json').read_text())
    for code in codes:
        path=folder/f'bearing_{code}';path.mkdir(exist_ok=True)
        spec=bearing_spec(str(code));row=dict(dimensions=spec)
        with MCPClient(path/'edit',design=source,allow_path=folder,timeout=600) as client:
            health_check(client,path/'opened_health.json')
            require_ok(client.execute('parameters.change',changes={'casing_bearing':str(code)}))
            health_check(client,path/'edited_health.json')
            params=require_ok(client.execute('parameters.list',filter='user'))
            assert not any(p.get('error') for p in params['parameters'])
            values={p['name']:p['value'] for p in params['parameters']}
            for name,value in dict(casing_bore_diameter=spec['id'],casing_od=spec['od'],casing_width=spec['depth'],
                                   carrier_radius=spec['id']/2-.1,bearing_lip_radius=spec['od']/2-1.3,
                                   front_depth=spec['depth']+1.1,rear_seat_top=spec['depth']+4.4).items():
                assert abs(values[name]-value)<1e-7,(name,values[name],value)
            assert values['casing_fit_checks']==0
            row['derived']={k:values[k] for k in ('casing_bearing','casing_bore_diameter','casing_od','casing_width',
                'carrier_radius','bearing_lip_radius','front_depth','rear_seat_top','rotor_a_z','housing_top','tab_radius','layout_scale')}
            row['tabs']={k:values[k] for k in ('casing_radius','seam_z','tab_depth','tab_plate_size','tab_plate_width',
                'tab_m6_envelope_radius','tab_m6_clearance','tab_outer_bolt_gap') if k in values}
            sampling=discover().module('cycloidal_pattern').validate_edit(profile,dict(
                ring_pin_count=int(values['ring_count']),pitch_radius=values['pitch'],eccentricity=values['eccentricity'],
                roller_radius=values['contact_radius'],clearance=values['profile_clearance']))
            row['sampling']={k:v for k,v in sampling.items() if k!='points'}
            row['parts']={}
            for name in PRINT_POSITIONS:
                for ext in ('step','stl'):
                    require_ok(client.call('export',dict(bodies=[name],path=str(path/(name+'.'+ext)))))
                shape=read_step(path/(name+'.step'));info=inspect_shape(shape)
                assert info['valid'],(code,name,info)
                row['parts'][name]=dict(step=info,mesh=verify_mesh(path/(name+'.stl'),shape))
            require_ok(client.call('save',dict(path=str(path/'edited.solidcraft'))))
            require_ok(client.call('screenshot',dict(source='model',path=str(path/'model.png'),view='iso',width=1200,height=900,grid=False,axes=False)))
        print(code,'native edit and eight STEP/STL bodies passed',flush=True)
        with MCPClient(path/'reopen',design=path/'edited.solidcraft',allow_path=folder,timeout=600) as client:
            health_check(client,path/'reopened_health.json')
            assert require_ok(client.call('measure'))['body_count']==8
            require_ok(client.call('save',dict(path=str(path/'reopened.solidcraft'))))
        with MCPClient(path/'second_reopen',design=path/'reopened.solidcraft',allow_path=folder,timeout=600) as client:
            health_check(client,path/'second_reopened_health.json')
            assert require_ok(client.call('measure'))['body_count']==8
        row.update(status='passed',second_reopen_body_count=8)
        report['cases'][str(code)]=row
        report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(code,'two reopen checks passed',flush=True)
    report['status']='passed';report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder');parser.add_argument('--codes',type=int,nargs='+',default=[6710,6811])
    args=parser.parse_args();verify(args.folder,args.codes)
