"""Export a saved native design. Never regenerate or overwrite its geometry."""
import argparse
import hashlib
import json
import math
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


def export(design, output, profile, evidence_dir=None, *, resume=False, save_source_as=None):
    design=Path(design).resolve();output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=resume)
    evidence=Path(evidence_dir).resolve() if evidence_dir else output
    evidence.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(design) as archive:document=json.loads(archive.read('document.json'))
    if resume:
        # Resume only immutable, matching native snapshots after an interrupted export.
        for label in ('assembled','exploded','3dpr'):
            with zipfile.ZipFile(output/(label+'.solidcraft')) as archive:saved=json.loads(archive.read('document.json'))
            for key in ('features','components','occurrences'):
                assert saved[key]==document[key],('Snapshot differs from source',label,key)
            stable=lambda d:[p for p in d['params'] if p['name'] not in ('print_layout','explode')]
            assert stable(saved)==stable(document),('Snapshot parameters differ',label)
            for ext in ('step','stl','png'):assert (output/(label+'.'+ext)).exists()
    split=False
    optional_ring='connected_contact_ring'
    component_names={c.get('name') for c in document['components']}
    new_spacers=optional_ring in component_names
    if 'output_nut_plate' in component_names:
        from gearbox_native.simple_double_bearing import POSITIONS,PRE_STACK_POSITIONS,CARRIER_POSITIONS,CLAMSHELL_POSITIONS,OLD_POSITIONS,LOOSE_DISC_POSITIONS,PROFILE,RING_PRINT
        split='rotor_a_cap' in component_names
        carrier_positions=CLAMSHELL_POSITIONS
        if 'output_cap_cylinder' in component_names:
            carrier_positions=POSITIONS if 'shaft_end_lower' in component_names else PRE_STACK_POSITIONS
        elif 'carrier_top_cap' in component_names:
            carrier_positions=CARRIER_POSITIONS
        positions=dict(carrier_positions if split else LOOSE_DISC_POSITIONS,connected_contact_ring=RING_PRINT) if new_spacers else OLD_POSITIONS
        legacy_profile=PROFILE.with_name("simple_double_bearing_version_1_35_to_1_profile.json")
        unsplit_profile=PROFILE.with_name("simple_double_bearing_version_1_unsplit_20_profile.json")
        if not profile:
            profile=(legacy_profile if not new_spacers and legacy_profile.exists() else
                     unsplit_profile if not split and unsplit_profile.exists() else PROFILE.with_name("simple_double_bearing_version_1_profile.json")
                     if "simple_double_bearing_version_1" in str(design) else PROFILE)
    elif any(c.get('name')=='drive_sleeve' for c in document['components']):
        from gearbox_native.native_v9_drive import layout
        names={c.get('name') for c in document['components']}
        positions=layout('bearing_holder' in names,'eccentric_hub_lower_a' in names)
        if 'bearing_baseplate' in names:
            positions['bearing_baseplate']=positions.pop('motor_mount')
            del positions['motor_spacer']
            positions['bearing_retainer']=(152,217)
    elif any(c.get('name')=='motor_spacer' for c in document['components']):
        from gearbox_native.native_v9 import PRINT_POSITIONS as positions
    elif any(c.get('name')=='output_casing_lobes' for c in document['components']):
        from gearbox_native.native_v8 import PRINT_POSITIONS as positions
    else:positions=PRINT_POSITIONS
    if 'motor_inner_adapter' in component_names:
        from gearbox_native.nema17_double_bearing import POSITIONS as motor_positions
        positions.update(motor_positions)
        from gearbox_native.nema17_mesh import verify_print_mesh
        mesh_check=lambda path,shape:verify_print_mesh(path,shape,assembly=output)
        if 'front_cover_spacer' in component_names:
            from gearbox_native.nema17_end_caps import POSITIONS as cover_positions
            positions.update({name:xy for name,xy in cover_positions.items() if name in component_names})
    else:mesh_check=verify_mesh
    # Old sealed masters predate later optional plates. Export only components
    # actually present in the opened native design.
    positions={name:xy for name,xy in positions.items() if name in component_names}
    if 'carrier_top_nut_tray' in component_names:
        from gearbox_native.version_11 import TRAYS
        positions.update(TRAYS)
    profile=profile or PROJECT/f'solidcraft/native_v{VERSION.split("_")[-1]}_profile.json'
    geometry=json.loads(Path(profile).read_text(encoding='utf-8'))
    conversion_names=None
    if 'front_cover_spacer' in component_names:
        from gearbox_native.nema17_print_set import CONVERSION_PARTS
        conversion_names=set(CONVERSION_PARTS) & component_names
    report={'source':str(design),'source_sha256':hashlib.sha256(design.read_bytes()).hexdigest(),
            'status':'running','geometry_regenerated':False,'parts':{}}
    with MCPClient(evidence/('resume_session' if resume else 'session'),design=output/'3dpr.solidcraft' if resume else design,allow_path=PROJECT,timeout=1800) as client:
        opened=health_check(client,evidence/'opened_health.json')
        if save_source_as is not None:
            # Authoring migrations can normalize a candidate through the
            # native application once, then export that exact saved source.
            # Health still passes before saving; acceptance is unchanged.
            assert not resume
            design=Path(save_source_as).resolve()
            require_ok(client.call('save',dict(path=str(design))))
            report.update(source=str(design),source_sha256=hashlib.sha256(design.read_bytes()).hexdigest())
        hardware=[b['name'] for b in opened['bodies'] if b['name'].startswith('hardware_')]
        if hardware:report['hardware_reference_bodies']=hardware
        params=require_ok(client.execute('parameters.list',filter='user'))
        assert not any(p.get('error') for p in params['parameters'])
        values={p['name']:p['value'] for p in params['parameters']}
        if 'carrier_top_nut_tray' in component_names:
            spacing = 2 * values['pitch'] * math.sin(math.pi / values['ring_count'])
            diameter = 2 * values['contact_radius']
            if spacing <= diameter:
                raise ValueError(f"Ring sleeves overlap at this reduction: {spacing:.3f} mm centre spacing for {diameter:g} mm sleeves")
        report['parameters']=params
        sampling=discover().module('cycloidal_pattern').validate_edit(geometry,dict(
            ring_pin_count=int(values['ring_count']),pitch_radius=values['pitch'],
            eccentricity=values['eccentricity'],roller_radius=values['contact_radius'],
            clearance=values['profile_clearance']))
        report['sampling']={k:v for k,v in sampling.items() if k!='points'}
        for label,changes in [('assembled',{'print_layout':'0','explode':'0 mm'}),
                              ('exploded',{'print_layout':'0','explode':'12 mm'}),
                              ('3dpr',{'print_layout':'1','explode':'0 mm'})]:
            if resume:
                if label=='3dpr':
                    for body in opened['bodies']:
                        if body['name'].startswith('printed_'):positions[body['name']]=tuple(body['center_of_mass'][:2])
                continue
            if not (label=='assembled' and values.get('print_layout')==0 and values.get('explode')==0):
                require_ok(client.execute('parameters.change',changes=changes))
            print_only=bool(hardware and label=='3dpr')
            if new_spacers:require_ok(client.execute('browser.visibility',items=[optional_ring],visible=print_only))
            if print_only:require_ok(client.execute('browser.visibility',items=hardware,visible=False))
            if print_only and conversion_names:
                require_ok(client.execute('browser.visibility',items=[b['name'] for b in opened['bodies'] if not b['name'].startswith('hardware_') and b['name'] not in conversion_names],visible=False))
            state=health_check(client,evidence/(label+'_health.json'))
            if label in ('assembled','exploded') and split and evidence != output:
                (output/(label+'_health.json')).write_bytes((evidence/(label+'_health.json')).read_bytes())
            if print_only and new_spacers:
                if 'carrier_top_nut_tray' in component_names:
                    for prefix, count in (('printed_contact_sleeve', values['ring_count']), ('printed_drive_sleeve', values['guide_count'])):
                        actual = sum(b['name'].split(' (')[0] == prefix for b in state['bodies'])
                        if actual != count:
                            raise ValueError(f"Native print layout has {actual} separate {prefix} bodies; expected {int(count)}")
                # Positions are read from the bodies in the current native count-driven sketch pattern.
                for body in state['bodies']:
                    if body['name'].startswith('printed_'):
                        positions[body['name']]=tuple(body['center_of_mass'][:2])
            require_ok(client.call('save',dict(path=str(output/(label+'.solidcraft')))))
            require_ok(client.call('screenshot',dict(source='model',path=str(output/(label+'.png')),
                view='iso',width=1600,height=1200,grid=False,axes=False)))
            for ext in ('step','stl'):
                selection={'bodies':sorted(conversion_names) if conversion_names else list(positions)} if print_only else (
                    {'bodies':[body['name'] for body in state['bodies'] if body['name']!=optional_ring]} if new_spacers else {})
                require_ok(client.call('export',dict(path=str(output/(label+'.'+ext)),**selection)))
        parts=output/'parts';parts.mkdir(exist_ok=resume)
        for name,(x,y) in positions.items():
            # Export the current native bodies, then only remove layout translation.
            raw=output/'layout_bodies';raw.mkdir(exist_ok=True)
            for ext in ('step','stl'):
                if resume and (raw/(name+'.'+ext)).exists():continue
                require_ok(client.call('export',dict(bodies=[name],path=str(raw/(name+'.'+ext)))))
            native=read_step(raw/(name+'.step'))
            shape_info=inspect_shape(native)
            assert shape_info['valid'] and shape_info['solid_count']==1, (name, 'Disconnected or invalid printable part')
            mesh=mesh_check(raw/(name+'.stl'),native)
            scale=1 if new_spacers and name.startswith('printed_') else values.get('layout_scale',1)
            localize(raw/(name+'.step'),raw/(name+'.stl'),parts/name,([x*scale,y*scale,0],[0,0,0]))
            report['parts'][name]={'native_shape':shape_info,'mesh':mesh}
    with MCPClient(evidence/'reopen_exploded',design=output/'exploded.solidcraft',allow_path=PROJECT,timeout=1800) as client:
        reopened=health_check(client,evidence/'reopened_exploded_health.json')
        count=len(reopened['bodies']) if new_spacers else require_ok(client.call('measure'))['body_count']
        assert count==len(positions)+len(hardware)
        if 'carrier_bottom_cap' in positions:
            tree=require_ok(client.execute('component.list',compact=True,bodies=True))['components']
            components={c['id']:c for c in tree}
            shown={b['name'] for b in reopened['bodies'] if b['visible']}
            verified={}
            for group in (c for c in tree if c['id'] and c['children']):
                path=[group['occurrences'][0]['id']]
                if group['parent']:path.insert(0,components[group['parent']]['occurrences'][0]['id'])
                descendants={group['id']}
                for _ in range(2):
                    descendants.update(c['id'] for c in tree if c['parent'] in descendants)
                affected={body for c in tree if c['id'] in descendants for body in c['bodies']} & shown
                require_ok(client.execute('browser.visibility',paths=[path],visible=False))
                visible={b['name'] for b in require_ok(client.call('inspect_design',dict(sketches=False)))['bodies'] if b['visible']}
                assert affected and visible==shown-affected,group['name']
                verified[group['name']]=len(affected)
                require_ok(client.execute('browser.visibility',paths=[path],visible=True))
            report['browser_groups']=verified

    # Combined print exports can contain the same native tessellation seams as
    # individual bodies. Apply the unchanged native-STEP tessellation policy.
    print_shape=read_step(output/'3dpr.step')
    assert inspect_shape(print_shape)['valid']
    if 'motor_inner_adapter' in component_names:
        import trimesh
        import shutil
        original=output/'3dpr_raw_native.stl'
        if not original.exists():shutil.copyfile(output/'3dpr.stl',original)
        # Concatenate validated native print-position meshes; no recipe rebuild.
        trimesh.util.concatenate([trimesh.load_mesh(output/'layout_bodies'/(name+'.stl')) for name in positions if not conversion_names or name in conversion_names]).export(output/'3dpr.stl')
    report['print_mesh']=verify_mesh(output/'3dpr.stl',print_shape)
    report['status']='native_export_checked'
    report['note']='Native health, fixed profile sampling and valid exports checked. This is not a new mechanical fit certification.'
    (output/'export.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(output,flush=True)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--populate',action='store_true',help='Export and publish all populate variants using only their exposed native parameters.')
    parser.add_argument('--style',help='With --populate, rebuild only this catalogue style.')
    parser.add_argument('--evidence-dir',type=Path,default=None,help='Optional location for diagnostic logs and native health records.')
    active=json.loads((PROJECT/'solidcraft/active_design.json').read_text(encoding='utf8'))
    parser.add_argument('--design',type=Path,default=PROJECT/active['master'])
    parser.add_argument('--output',type=Path,default=None)
    parser.add_argument('--profile',type=Path)
    args=parser.parse_args()
    if args.populate:
        from gearbox_native.native_catalogue import main as catalogue
        return catalogue(args.output,args.evidence_dir,style=args.style)
    with zipfile.ZipFile(args.design) as archive:
        names={c.get('name') for c in json.loads(archive.read('document.json'))['components']}
    label=next((s for s in ('simple_double_bearing_version_1','simple_double_bearing_version_2') if s in str(args.design)), 'simple_double_bearing_version_2') if 'output_nut_plate' in names else f'native_v{VERSION.split("_")[-1]}'
    if 'carrier_top_nut_tray' in names:
        label='version_11'
    export(args.design,args.output or PROJECT/'outputs'/label/('export_'+uuid.uuid4().hex[:8]),args.profile,args.evidence_dir)


if __name__=='__main__':main()
