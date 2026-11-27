"""Build the separate paired output joiners and tubular motor surround in isolation.

Preserves the accepted core, including its overhang features, byte-for-byte in
the merged feature graph. No assembly instructions are regenerated here.
"""
import copy
import json
import re
import shutil
import zipfile
from pathlib import Path

from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.registry import discover
from gearbox_native.acceptance import health_check, verify_mesh
from gearbox_native.verification import read_step
from gearbox_native.nema17_double_bearing import PROJECT, MASTER
from gearbox_native.nema17_end_caps import BUILDERS, REVISED_PLATES, place, hardware

CHANGED = ({'motor_cage', 'rear_output_extension'} | REVISED_PLATES |
           {'rear_output_spacer_1','rear_output_spacer_2'} |
           {f'rear_output_joiner_{i}' for i in range(1,4)})


def write(path, doc):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('document.json', json.dumps(doc))
        z.writestr('container.json', '{"format":"solidcraft-container/1"}')


def build(folder, source=None):
    folder=Path(folder).resolve();folder.mkdir(parents=True,exist_ok=False)
    snapshot=Path(source) if source else PROJECT/'solidcraft/nema17_flange_before_tube_revision.solidcraft'
    if not snapshot.exists():shutil.copyfile(PROJECT/MASTER,snapshot)
    with zipfile.ZipFile(snapshot) as z:original=json.loads(z.read('document.json'))
    shutil.copyfile(snapshot,folder/'baseline.solidcraft')
    removed={c['id'] for c in original['components'] if c['name'] in CHANGED or c['name'].startswith(('hardware_endcap_','hardware_cage_'))}
    removed_names={c['name'] for c in original['components'] if c['id'] in removed}
    base=copy.deepcopy(original)
    base['components']=[c for c in base['components'] if c['id'] not in removed]
    base['occurrences']=[o for o in base['occurrences'] if o['component'] not in removed]
    base['features']=[f for f in base['features'] if f.get('component') not in removed and not (f['type']=='move' and set(f.get('bodies',[])) & removed_names)]
    valid={f['id'] for f in base['features']}
    for g in base.get('timeline_groups',[]):g['features']=[i for i in g['features'] if i in valid]
    isolated=copy.deepcopy(base);isolated['features']=[];isolated['timeline_groups']=[];isolated['visibility']={}
    write(folder/'isolated.solidcraft',isolated)
    with MCPClient(folder/'author',design=folder/'isolated.solidcraft',allow_path=PROJECT,timeout=1800) as client:
        cls=discover().module('native_design').Design;d=cls.__new__(cls)
        d.client=client;d.commands=[];d.body=None
        # Retained catalogue-cut parameters still occupy their names even when
        # their old component is replaced. Allocate fresh authoring prefixes.
        used=[int(value) for value in re.findall(r'_(\d+)_',json.dumps(original))]
        d.index=max([60000]+used)+1000
        existing={p['name'] for p in original['params']}
        for name,expr in [('motor_tube_wall','3 mm'),('motor_cable_window_clock','30 deg'),
                          ('rear_joiner_pitch','52.5 mm'),('rear_joiner_screw_pitch','15 mm'),
                          ('rear_joiner_height','rear_extension_height - rear_extension_flange_depth'),
                          ('rear_joiner_base','rear_extension_base + rear_extension_flange_depth')]:
            if name not in existing:d.parameter(name,expr,unit='deg' if name.endswith('clock') else 'mm')
        (folder/'parts').mkdir()
        for name in sorted(CHANGED,key=lambda n:(not n.startswith('rear_output'),n)):
            print('BUILD',name,flush=True);BUILDERS[name](d)
            for ext in ('step','stl'):
                require_ok(client.call('export',dict(bodies=[name],path=str(folder/'parts'/(name+'.'+ext)))))
            from gearbox_native.nema17_mesh import verify_print_mesh
            verify_print_mesh(folder/'parts'/(name+'.stl'),read_step(folder/'parts'/(name+'.step')))
            place(d,name)
        hardware(d)
        health_check(client,folder/'isolated_health.json')
        require_ok(client.call('save',dict(path=str(folder/'isolated_checked.solidcraft'))))
    with zipfile.ZipFile(folder/'isolated_checked.solidcraft') as z:checked=json.loads(z.read('document.json'))
    base['features'] += checked['features']
    for key in ('components','occurrences','params','favorites','next_id'):
        base[key]=checked[key]
    base['visibility']={}
    write(folder/'candidate.solidcraft',base)
    print('ISOLATED PARTS VERIFIED; NATIVE CANDIDATE READY',flush=True)


def finalize(folder):
    """Restore browser groups and expose the coupler's actual bolt-circle size."""
    folder=Path(folder)
    with zipfile.ZipFile(folder/'baseline.solidcraft') as z:old=json.loads(z.read('document.json'))
    with zipfile.ZipFile(folder/'candidate.solidcraft') as z:doc=json.loads(z.read('document.json'))
    # Empty isolated histories can reuse *implicit* d-number slots from the
    # original history. Reserve a disjoint namespace for every new feature,
    # including generated plane/move parameters that aren't in params[].
    old_ids={f['id'] for f in old['features']}
    new_features=[f for f in doc['features'] if f['id'] not in old_ids]
    token=re.compile(r'\bd\d+\b')
    new_refs=set(token.findall(json.dumps(new_features)))
    offset=max(int(s[1:]) for s in token.findall(json.dumps(old)))+100
    mapping={name:f'd{int(name[1:])+offset}' for name in new_refs}
    def rename(value):
        return json.loads(token.sub(lambda m:mapping.get(m[0],m[0]),json.dumps(value)))
    doc['features']=[rename(f) if f['id'] not in old_ids else f for f in doc['features']]
    old_names={p['name'] for p in old['params']}
    doc['params']=copy.deepcopy(old['params'])+[
        rename(p) for p in doc['params'] if p['name'] in new_refs or
        (not p.get('model') and p['name'] not in old_names)]
    assert len({p['name'] for p in doc['params']})==len(doc['params'])
    parents={c['name']:c['parent'] for c in old['components']}
    for c in doc['components']:
        if c['name'] in parents:c['parent']=parents[c['name']]
        elif c['name'].startswith('hardware_endcap_'):c['parent']=parents['hardware_endcap_outer_extension_screw_0']
        elif c['name'].startswith('rear_output_joiner_'):c['parent']=parents['rear_output_extension']
    byid={c['id']:c for c in doc['components']}
    for o in doc['occurrences']:o['parent']=byid[o['component']]['parent']
    if 'coupler_bolt_circle_diameter' not in {p['name'] for p in doc['params']}:
        doc['params'].append(dict(name='coupler_bolt_circle_diameter',expr='16 mm',unit='mm',model=False,
                                 comment='Four M3 flange screws on this diameter; both motor-end 6704 inner pieces and nuts follow.'))
    for p in doc['params']:
        if p['name']=='coupler_mount_radius':p['expr']='coupler_bolt_circle_diameter / 2'
    if 'coupler_bolt_circle_diameter' not in doc['favorites']:doc['favorites'].append('coupler_bolt_circle_diameter')
    if not any(p['name']=='motor_cable_window_clock' for p in doc['params']):
        doc['params'].append(dict(name='motor_cable_window_clock',expr='30 deg',unit='deg',model=False,
                                 comment='Cable window clocked away from the rear-cover nut bosses.'))
    if not any(f.get('angle')=='motor_cable_window_clock' for f in doc['features']):
        tool_move=next(f for f in doc['features'] if f['type']=='move' and f.get('bodies')==['motor_tube_cable_window'])
        at=doc['features'].index(tool_move)+1
        number=max(int(s[1:]) for s in token.findall(json.dumps(doc)))+100
        doc['features'].insert(at,dict(type='move',id=doc['next_id'],component=tool_move['component'],
            name='Cable_window_clear_of_rear_nuts',bodies=['motor_tube_cable_window'],
            rotate_axis=[0.,0.,1.],angle='motor_cable_window_clock',translate=['0','0','0'],
            suppressed=False,param_names=[f'd{number+i}' for i in range(4)]))
        doc['next_id']+=1
    write(folder/'prepared.solidcraft',doc)
    return folder/'prepared.solidcraft'


if __name__=='__main__':
    import sys
    build(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else None)
    finalize(sys.argv[1])

