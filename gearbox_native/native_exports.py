"""Export a saved native design. Never regenerate or overwrite its geometry."""
import argparse
import hashlib
import json
from pathlib import Path
import uuid
import zipfile

from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.registry import discover
from oobb_solidcraft.validation import inspect_shape
from gearbox_native.project import PROJECT, VERSION
from gearbox_native.acceptance import health_check, verify_mesh
from gearbox_native.verification import read_step
from gearbox_native.native_v7 import PRINT_POSITIONS
from gearbox_native.verify_v7_assembly import localize


def export(design, output, profile, evidence_dir=None):
    design=Path(design).resolve();output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    evidence=Path(evidence_dir).resolve() if evidence_dir else output
    evidence.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(design) as archive:document=json.loads(archive.read('document.json'))
    if any(c.get('name')=='output_casing_lobes' for c in document['components']):
        from gearbox_native.native_v8 import PRINT_POSITIONS as positions
    else:positions=PRINT_POSITIONS
    geometry=json.loads(Path(profile).read_text(encoding='utf-8'))
    report={'source':str(design),'source_sha256':hashlib.sha256(design.read_bytes()).hexdigest(),
            'status':'running','geometry_regenerated':False,'parts':{}}
    with MCPClient(evidence/'session',design=design,allow_path=PROJECT,timeout=600) as client:
        health_check(client,evidence/'opened_health.json')
        params=require_ok(client.execute('parameters.list',filter='user'))
        assert not any(p.get('error') for p in params['parameters'])
        values={p['name']:p['value'] for p in params['parameters']}
        report['parameters']=params
        sampling=discover().module('cycloidal_pattern').validate_edit(geometry,dict(
            ring_pin_count=int(values['ring_count']),pitch_radius=values['pitch'],
            eccentricity=values['eccentricity'],roller_radius=values['contact_radius'],
            clearance=values['profile_clearance']))
        report['sampling']={k:v for k,v in sampling.items() if k!='points'}
        for label,changes in [('assembled',{'print_layout':'0','explode':'0 mm'}),
                              ('exploded',{'print_layout':'0','explode':'12 mm'}),
                              ('3dpr',{'print_layout':'1','explode':'0 mm'})]:
            require_ok(client.execute('parameters.change',changes=changes))
            health_check(client,evidence/(label+'_health.json'))
            require_ok(client.call('save',dict(path=str(output/(label+'.solidcraft')))))
            require_ok(client.call('screenshot',dict(source='model',path=str(output/(label+'.png')),
                view='iso',width=1600,height=1200,grid=False,axes=False)))
            for ext in ('step','stl'):
                require_ok(client.call('export',dict(path=str(output/(label+'.'+ext)))))
        parts=output/'parts';parts.mkdir()
        for name,(x,y) in positions.items():
            # Export the current native bodies, then only remove layout translation.
            raw=output/'layout_bodies';raw.mkdir(exist_ok=True)
            for ext in ('step','stl'):
                require_ok(client.call('export',dict(bodies=[name],path=str(raw/(name+'.'+ext)))))
            native=read_step(raw/(name+'.step'));assert inspect_shape(native)['valid']
            mesh=verify_mesh(raw/(name+'.stl'),native)
            scale=values.get('layout_scale',1)
            localize(raw/(name+'.step'),raw/(name+'.stl'),parts/name,([x*scale,y*scale,0],[0,0,0]))
            report['parts'][name]={'native_shape':inspect_shape(native),'mesh':mesh}
    with MCPClient(evidence/'reopen_exploded',design=output/'exploded.solidcraft',allow_path=PROJECT,timeout=600) as client:
        health_check(client,evidence/'reopened_exploded_health.json')
        assert require_ok(client.call('measure'))['body_count']==len(positions)
    # Combined print exports can contain the same native tessellation seams as
    # individual bodies. Apply the unchanged native-STEP tessellation policy.
    print_shape=read_step(output/'3dpr.step')
    assert inspect_shape(print_shape)['valid']
    report['print_mesh']=verify_mesh(output/'3dpr.stl',print_shape)
    report['status']='native_export_checked'
    report['note']='Native health, fixed profile sampling and valid exports checked. This is not a new mechanical fit certification.'
    (output/'export.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(output,flush=True)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--populate',action='store_true',help='Export and publish all populate variants using only their exposed native parameters.')
    parser.add_argument('--evidence-dir',type=Path,default=None,help='Optional location for diagnostic logs and native health records.')
    parser.add_argument('--design',type=Path,default=PROJECT/'gearbox_controls.solidcraft')
    parser.add_argument('--output',type=Path,default=None)
    parser.add_argument('--profile',type=Path,default=PROJECT/f'solidcraft/native_v{VERSION.split("_")[-1]}_profile.json')
    args=parser.parse_args()
    if args.populate:
        from gearbox_native.native_catalogue import main as catalogue
        return catalogue(args.output,args.evidence_dir)
    export(args.design,args.output or PROJECT/f'outputs/native_v{VERSION.split("_")[-1]}'/('export_'+uuid.uuid4().hex[:8]),args.profile,args.evidence_dir)


if __name__=='__main__':main()
