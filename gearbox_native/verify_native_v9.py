"""Native 5x5 configuration, motion, hardware and fit checks."""
import argparse
import itertools
import json
import math
from oobb_solidcraft.registry import discover
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.validation import inspect_shape
from oobb_solidcraft import api
from gearbox_native.project import PROJECT
from gearbox_native.acceptance import health_check, verify_mesh
from gearbox_native.verification import read_step
from gearbox_native.verify_native_v8 import overlap
from gearbox_native.verify_v8_hardware import cylinder, hexagon
from gearbox_native.exact_geometry import _move, _boolean
from gearbox_native.native_v9 import mounting_holes, CLAMPS, PRINT_POSITIONS


def hardware(shapes, v, shaft_checks=True):
    checks = []
    rings = [_boolean('cut', cylinder(26, 7, [0, 0, z]),
                      [cylinder(20, 7.02, [0, 0, z-.01])])
             for z in (v['casing_bottom'], v['front_seat_bottom'])]
    def clear(label, tool, targets):
        for name, shape in targets.items():
            amount = overlap(tool, shape)
            checks.append(dict(check=label, part=name, overlap_mm3=amount))
            assert amount < .03, (label, name, amount)
    bearing_targets = {f'casing_bearing_{i}': ring for i, ring in enumerate(rings)}
    cases = {name: shape for name, shape in shapes.items() if name.startswith('output_casing')}
    for x, y in CLAMPS:
        clear('clamp_shank', cylinder(1.5, v['join_screw_length'], [x,y,v['join_tip_z']]), cases)
        clear('clamp_head', cylinder(2.9, 3, [x,y,v['join_head_seat']]), cases)
        clear('clamp_nut_loading', hexagon('m3', 4.5, [x,y,v['casing_bottom']]), cases)
        clear('clamp_nut_vs_bearing', hexagon('m3', 2.5, [x,y,v['casing_bottom']+2]), bearing_targets)
    m6, m3 = mounting_holes()
    for x, y in m6:
        clear('M6_shank', cylinder(3, v['housing_top']-v['casing_bottom'], [x,y,v['casing_bottom']]), cases)
        clear('M6_nut_loading', hexagon('m6', 6.3, [x,y,v['casing_bottom']]), cases)
        clear('M6_nut_vs_bearing', hexagon('m6', 5, [x,y,v['casing_bottom']+1.3]), bearing_targets)
    for x, y in m3:
        clear('M3_mount_shank', cylinder(1.5, v['housing_top']-v['casing_bottom'], [x,y,v['casing_bottom']]), cases)
    for i in range(int(v['guide_count'])):
        angle = v['guide_phase']+i*360/v['guide_count']; a = math.radians(angle)
        x, y = v['guide_pitch']*math.cos(a), v['guide_pitch']*math.sin(a)
        seat=v['front_z']+1.4; tip=seat-v['guide_screw_length']
        clear('guide_shank', cylinder(1.5,v['guide_screw_length'],[x,y,tip]), shapes)
        head=cylinder(2.9,3,[x,y,seat]); clear('guide_head',head,shapes);clear('guide_head_bearing',head,bearing_targets)
        nut=hexagon('m3',2.5,[x,y,tip+.3],angle+30)
        clear('guide_nut',nut,{'motor_mount':shapes['motor_mount'],**bearing_targets})
        clear('guide_nut_loading',hexagon('m3',tip+.3+2.5,[x,y,0],angle+30),{'motor_mount':shapes['motor_mount']})
    if v['posts_enabled']:
        for i in range(3):
            a=math.radians(i*120);x=v['post_pitch']*math.cos(a);y=v['post_pitch']*math.sin(a)
            seat=v['front_z']+2.6;tip=seat-25
            clear('post_shank',cylinder(1.5,25,[x,y,tip]),shapes)
            head=cylinder(2.9,3,[x,y,seat]);clear('post_head',head,shapes);clear('post_head_bearing',head,bearing_targets)
            nut=hexagon('m3',2.5,[x,y,tip+.3])
            clear('post_nut',nut,{'motor_mount':shapes['motor_mount'],**bearing_targets})
    # Nominal rotating disc bearings must clear the edited shaft journals.
    for side, x, z in [('bottom',v['eccentricity'],v['bottom_journal_z']),
                       ('top',-v['eccentricity'],v['rotor_b_z']+.1)]:
        ring=_boolean('cut',cylinder(v[side+'_od']/2,v[side+'_width'],[x,0,z]),
                      [cylinder(v[side+'_bore']/2,v[side+'_width']+.02,[x,0,z-.01])])
        clear(side+'_bearing',ring,{name:shape for name,shape in shapes.items() if name.startswith('eccentric_hub')})
    hubs={name:shape for name,shape in shapes.items() if name.startswith('eccentric_hub')}
    if shaft_checks:
        shaft_hardware(clear, shapes, v)
        ring=_boolean('cut',cylinder(9,4,[0,0,v['housing_top']-4.1]),
                      [cylinder(6,4.02,[0,0,v['housing_top']-4.11])])
        clear('6701_front_bearing',ring,hubs)
    return dict(status='passed',checks=checks,maximum_overlap_mm3=max(c['overlap_mm3'] for c in checks))


def shaft_hardware(clear, shapes, v):
    """Probe nominal hardware and its insertion paths in the assembled native BReps."""
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCone
    hubs = {name: shapes[name] for name in ('eccentric_hub_lower', 'eccentric_hub_upper')}
    fixed = {name: shapes[name] for name in ('motor_mount', 'motor_spacer')}
    seat = v['wiggle_join_head_seat']
    tip = v['motor_shaft_end']
    base = -v['motor_spacer_depth']
    z = v['wiggle_grub_z']
    def radial(shape, x):
        return _move(_move(shape, 'rotate', [0,90,0]), 'translate', [x,0,z])
    shaft = cylinder(2.5, v['motor_shaft_length'], [0,0,base])
    clear('24mm_motor_shaft', shaft, {**hubs, **fixed})
    clear('M2.5_socket_head_insertion', cylinder(2.25,seat-base,[0,0,base]), hubs)
    clear('M2.5x12_join_shank', cylinder(1.25,12,[0,0,seat]), hubs)
    clear('top_nut_loading', hexagon('m2d5', 3.5,[0,0,v['wiggle_join_nut_bottom']]), hubs)
    assert seat-2.5-tip >= .49
    assert v['wiggle_join_nut_bottom']+2 <= seat+12 <= v['hub_top']
    # Contact either the round shaft or a 0.5 mm D-flat. The nominal countersunk
    # screw length includes the head. Probe a 6.72 mm head with a 90-degree cone.
    for x in (2,2.5):
        clear('M3_radial_shank', radial(cylinder(1.5,6.5,[0,0,0]), x), hubs)
        clear('M3_radial_head', radial(BRepPrimAPI_MakeCone(1.5,3.36,1.86).Shape(), x+8-1.86),
              {**hubs, **fixed})
    # Sweep the entire specified opening, including the former floor of the notch.
    gap = _move(BRepPrimAPI_MakeBox(22, 10, -base).Shape(), 'translate', [0, -5, base])
    clear('full_height_10mm_spacer_gap', gap, {'motor_spacer': shapes['motor_spacer']})
    clear('radial_hex_key_access', radial(cylinder(1.16,30,[0,0,0]),10), {**hubs, **fixed})
    nut = radial(hexagon('m3',2.4,[0,0,0],0),v['wiggle_grub_nut_radius'])
    clear('radial_nut',nut,hubs)
    for step in range(1,9):
        clear('radial_nut_bottom_loading', _move(nut,'translate',[0,0,-step]), hubs)
    clear('24mm_shaft_to_join_head', cylinder(2.25,2.5,[0,0,seat-2.5]),{'motor_shaft':shaft})
    clear('spacer_to_hubs', shapes['motor_spacer'], hubs)
    for x in (-15.5,15.5):
        for y in (-15.5,15.5):
            clear('NEMA17_mount_screw',cylinder(1.5,-base+4,[x,y,base]), fixed)


def main(name):
    folder=PROJECT/'build/native_v9'/name
    geometry=json.loads((folder/'profile.json').read_text())
    report={'status':'running','cases':{}}
    cases={'baseline':{},'ratio_32':{'reduction':'32'},'eccentricity_edit':{'eccentricity':'0.68 mm'},
           'posts_off':{'standoff_radius':'0 mm'},
           'shaft_fit_edit':{'wiggle_key_clearance':'0.08 mm','wiggle_journal_clearance':'0.05 mm'},
           'compact_10':{'reduction':'10','eccentricity':'0.9 mm','standoff_radius':'0 mm'}}
    with MCPClient(folder/'verify',design=folder/'gearbox.solidcraft',allow_path=PROJECT,timeout=600) as client:
        params=require_ok(client.execute('parameters.list',filter='user'))
        defaults={p['name']:p['expression'] for p in params['parameters']}
        for label,changes in cases.items():
            reset={k:defaults[k] for changeset in cases.values() for k in changeset};reset.update(changes)
            require_ok(client.execute('parameters.change',changes=reset))
            health_check(client,folder/(label+'_health.json'))
            params=require_ok(client.execute('parameters.list',filter='user'));v={p['name']:p['value'] for p in params['parameters']}
            sampling=discover().module('cycloidal_pattern').validate_edit(geometry,dict(
                ring_pin_count=int(v['ring_count']),pitch_radius=v['pitch'],eccentricity=v['eccentricity'],roller_radius=v['contact_radius'],clearance=v['profile_clearance']))
            row=dict(sampling={k:x for k,x in sampling.items() if k!='points'},parameters=v,parts={})
            case=folder/label;case.mkdir(exist_ok=True);shapes={}
            affected = {'ratio_32': ['rotor_a','rotor_b','output_casing_lobes'],
                        'posts_off': ['motor_mount','pin_front','rotor_a','rotor_b'],
                        'shaft_fit_edit': ['eccentric_hub_lower','eccentric_hub_upper']}.get(label, list(PRINT_POSITIONS))
            for part in affected:
                for ext in ('step','stl'):require_ok(client.call('export',dict(bodies=[part],path=str(case/(part+'.'+ext)))))
                shape=read_step(case/(part+'.step'));info=inspect_shape(shape)
                assert info['valid'] and info['solid_count']==1,(label,part)
                mesh=verify_mesh(case/(part+'.stl'),shape)
                row['parts'][part]=dict(valid=info['valid'],volume=info['volume_mm3'],bounds=info['bounds_mm'],mesh=mesh)
                shapes[part]=shape
            assert v['casing_bearing']==6808 and v['tab_plate_size']==5
            for part in ('output_casing_lower','output_casing_lobes','output_casing_upper'):
                if part not in row['parts']: continue
                bounds=row['parts'][part]['bounds'];assert max(bounds[3]-bounds[0],bounds[4]-bounds[1])<=74.05
            if label in ('baseline','compact_10'):
                row['intersections']=[]
                for a,b in itertools.combinations(shapes,2):
                    amount=overlap(shapes[a],shapes[b]);row['intersections'].append(dict(parts=[a,b],overlap_mm3=amount))
                    assert amount<.03,(a,b,amount)
                row['hardware']=hardware(shapes,v)
                row['motion']=[]
                for angle in range(0,361,30):
                    radians=math.radians(angle);e=v['eccentricity']
                    ring=_move(shapes['output_casing_lobes'],'rotate',[0,0,angle/v['ring_count']])
                    for side,sign in [('a',1),('b',-1)]:
                        rotor=_move(shapes['rotor_'+side],'translate',[sign*e*(math.cos(radians)-1),sign*e*math.sin(radians),0])
                        amount=overlap(rotor,ring);assert amount<.03,(angle,side,amount)
                        row['motion'].append(dict(angle=angle,side=side,overlap_mm3=amount))
            require_ok(client.call('save',dict(path=str(case/'gearbox.solidcraft'))))
            row['status']='passed';report['cases'][label]=row
            (folder/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
            print(label,'passed',flush=True)
    for label in ('baseline','eccentricity_edit','shaft_fit_edit','compact_10'):
        case=folder/label
        for index,source in [(1,case/'gearbox.solidcraft'),(2,case/'resaved.solidcraft')]:
            with MCPClient(case/f'reopen_{index}',design=source,allow_path=PROJECT,timeout=600) as client:
                health_check(client,case/f'reopened_{index}.json')
                assert require_ok(client.call('measure'))['body_count']==len(PRINT_POSITIONS)
                if index==1:require_ok(client.call('save',dict(path=str(case/'resaved.solidcraft'))))
        report['cases'][label]['reopens']=2
    report['status']='passed'
    (folder/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('V9 verification passed',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--name',required=True);a=p.parse_args();main(a.name)
