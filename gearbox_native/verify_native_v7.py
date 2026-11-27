"""Independent native-only edit/reopen proof, never a regeneration path."""
import argparse,json,math
from pathlib import Path
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.registry import discover
from oobb_solidcraft.compiler import compile_thing
from gearbox_native import acceptance,controls
from gearbox_native.configurator import recipe
from gearbox_native.simple import rotor
from gearbox_native.exact_geometry import build_shape


def rotor_reference(values):
    c=recipe(values)[2]
    thing=dict(id='independent_rotor',mode='true',**rotor(c,0))
    plan=compile_thing(thing)
    return build_shape(plan['tree']),c


def verify(folder):
    folder=Path(folder).resolve();native=folder/'gearbox.solidcraft'
    geometry=json.loads((folder/'profile.json').read_text(encoding='utf-8'))
    report={'status':'running','native_only':True,'cases':{}}
    baseline=controls.defaults()
    for name,changes in [('baseline',{}),('eccentricity',{'eccentricity':1.39}),
                         ('reduction',{'reduction':16}),('thickness',{'disc_thickness':5.2})]:
        values=dict(baseline,**changes);reference,c=rotor_reference(values)
        path=folder/name;path.mkdir(exist_ok=True)
        mapped=dict(ring_pin_count=c['ring_pin_count'],pitch_radius=c['pitch_radius'],eccentricity=c['radius_offset'],
                    roller_radius=c['lobe_radius'],clearance=c['lobe_clearance'])
        checked=discover().module('cycloidal_pattern').validate_edit(geometry,mapped)
        row={'sampling':{k:v for k,v in checked.items() if k!='points'}}
        with MCPClient(path/'session',design=native,allow_path=folder,timeout=600) as client:
            acceptance.health_check(client,path/'opened_health.json')
            if changes:
                expressions={k:f"{v} {controls.SPECS[k]['unit']}".strip() for k,v in changes.items()}
                row['edit']=require_ok(client.execute('parameters.change',changes=expressions))
            acceptance.health_check(client,path/'edited_health.json')
            row['measurement']=acceptance.verify_native_measurement(require_ok(client.call('measure')),reference)
            require_ok(client.call('save',dict(path=str(path/'edited.solidcraft'))))
            require_ok(client.call('export',dict(path=str(path/'edited.step'))))
            require_ok(client.call('export',dict(path=str(path/'edited.stl'))))
        row['step']=acceptance.verify_step(path/'edited.step',reference)
        row['mesh']=acceptance.verify_mesh(path/'edited.stl',reference)
        with MCPClient(path/'reopen',design=path/'edited.solidcraft',allow_path=folder,timeout=600) as client:
            acceptance.health_check(client,path/'reopened_health.json')
            row['reopened_measurement']=acceptance.verify_native_measurement(require_ok(client.call('measure')),reference)
            require_ok(client.call('export',dict(path=str(path/'reopened.step'))))
        row['reopened_step']=acceptance.verify_step(path/'reopened.step',reference)
        report['cases'][name]=row
        print(name,'passed',flush=True)
        (folder/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    report['status']='passed'
    (folder/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);verify(p.parse_args().folder)
