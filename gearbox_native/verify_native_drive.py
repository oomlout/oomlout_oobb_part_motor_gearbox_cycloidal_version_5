"""Hardware, bearing and assembly checks for the two V9 input arrangements."""
import argparse
import itertools
import json
from pathlib import Path
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from gearbox_native.verification import read_step
from gearbox_native.exact_geometry import _move,_boolean
from gearbox_native.verify_native_v8 import overlap
from gearbox_native.verify_v8_hardware import cylinder,hexagon
from gearbox_native.verify_native_v9 import hardware,shaft_hardware
from oobb_solidcraft.validation import inspect_shape

def check(shapes,v,bearing=False,core=True):
    checks=[]
    retention={}
    def clear(label,tool,targets):
        for name,shape in targets.items():
            amount=overlap(tool,shape)
            checks.append(dict(check=label,part=name,overlap_mm3=amount))
            assert amount<.03,(label,name,amount)
    if core:
        test_shapes=dict(shapes)
        if 'bearing_baseplate' in test_shapes:test_shapes['motor_mount']=test_shapes.pop('bearing_baseplate')
        common=hardware(test_shapes,v,shaft_checks=False)
        checks.extend(common['checks'])
    info={n:inspect_shape(s) for n,s in shapes.items()}
    for a,b in itertools.combinations(shapes,2):
        aa=info[a]['bounds_mm'];bb=info[b]['bounds_mm']
        if any(aa[i]>=bb[i+3]-.00001 or bb[i]>=aa[i+3]-.00001 for i in range(3)):
            continue
        clear(a,shapes[a],{b:shapes[b]})
    rings=[
        ('lower_disc_6702',v['bottom_bore']/2,v['bottom_od']/2,v['bottom_width'],v['eccentricity'],v['bottom_journal_z']+.1),
        ('upper_disc_6702',v['top_bore']/2,v['top_od']/2,v['top_width'],-v['eccentricity'],v['rotor_b_z']+.1),
        ('front_shaft_6702',7.5,10.5,4,0,v['housing_top']-4.1),
    ]
    if bearing:rings.append(('base_shaft_6702',7.5,10.5,4,0,v.get('bearing_holder_bearing_z',.1)))
    if core:
        rings.extend([('rear_6808',20,26,7,0,4.3),('front_6808',20,26,7,0,v['front_seat_bottom'])])
    for name,ri,ro,h,x,z in rings:
        ring=_boolean('cut',cylinder(ro,h,[x,0,z]),[cylinder(ri,h+.02,[x,0,z-.01])])
        clear(name,ring,shapes)
    hubs={n:s for n,s in shapes.items() if n.startswith('eccentric_hub')}
    seat=v['wiggle_join_head_seat']
    length=35 if bearing else 12
    if 'eccentric_hub_lower_a' in shapes:
        clear('upward_M3x35_join_shank',cylinder(1.5,35,[0,0,seat]),shapes)
        head=cylinder(2.85,3,[0,0,seat-3])
        clear('upward_M3_socket_cap_head',head,shapes)
        retention['cap_seat_stop_mm3']=overlap(_move(head,'translate',[0,0,1]),shapes['bearing_retainer'])
        assert retention['cap_seat_stop_mm3']>1, 'Cap has no load-bearing seat'
        cap_nut=hexagon('m3',2.4,[0,0,v['wiggle_join_nut_bottom']],30)
        clear('upper_M3_join_nut',cap_nut,shapes)
        assert seat+35>=v['wiggle_join_nut_bottom']+2.4
        for offset in range(-8,9):
            clear('upper_M3_side_loading',_move(cap_nut,'translate',[0,offset,0]),hubs)
        retention['tip_beyond_nut_mm']=seat+35-v['wiggle_join_nut_bottom']-2.4
        retention['nut_side_stops_mm3']=[overlap(_move(cap_nut,'translate',[0,offset,0]),shapes['drive_sleeve']) for offset in (-4,4)]
        assert min(retention['nut_side_stops_mm3'])>1,'Fitted sleeve must retain the upper nut'
        retention['wrong_phase_stops_mm3']={angle:sum(overlap(hubs[lo],_move(hubs[hi],'rotate',[0,0,angle]))
            for lo in ('eccentric_hub_lower_a','eccentric_hub_lower_b')
            for hi in ('eccentric_hub_upper_a','eccentric_hub_upper_b')) for angle in (90,180,270)}
        assert min(retention['wrong_phase_stops_mm3'].values())>.03,'Clock key admits an incorrect phase'
    else:
        clear('upward_M2_5_join_shank',cylinder(1.25,length,[0,0,seat]),shapes)
        clear('upward_M2_5_join_head',cylinder(2.25,2.5,[0,0,seat-2.5]),shapes)
        clear('upper_M2_5_nut',hexagon('m2d5',2,[0,0,v['wiggle_join_nut_bottom']]),shapes)
        clear('upper_M2_5_nut_loading',hexagon('m2d5',v['drive_key_top']-v['wiggle_join_nut_bottom']+1,[0,0,v['wiggle_join_nut_bottom']]),hubs)
    z=v['drive_clamp_z'];tip=v['drive_clamp_tip']
    def radial(shape,x):
        return _move(_move(shape,'rotate',[0,90,0]),'translate',[x,0,z])
    clear('sleeve_M3x6_shank',radial(cylinder(1.5,6,[0,0,0]),tip),shapes)
    clear('sleeve_M3_socket_head',radial(cylinder(2.9,3,[0,0,0]),tip+6),shapes)
    clear('sleeve_hex_key_access',radial(cylinder(1.16,30,[0,0,0]),tip+9),shapes)
    nut=_move(_move(hexagon('m3',2.4,[0,0,0],0),'rotate',[90,0,90]),'translate',[5.8,0,z])
    clear('sleeve_M3_nut',nut,shapes)
    for offset in (2,4,6,8,10,12,14):
        clear('sleeve_side_nut_loading',_move(nut,'translate',[0,offset,0]),{'drive_sleeve':shapes['drive_sleeve']})
    if 'bearing_holder' in shapes:
        from OCP.BRepPrimAPI import BRepPrimAPI_MakeCone
        for x in (-15.5,15.5):
            for y in (-15.5,15.5):
                seat=v['motor_plate_depth']-.02
                clear('holder_M3x10_shank',cylinder(1.5,10-1.86,[x,y,seat-10]),shapes)
                clear('holder_countersunk_head',_move(BRepPrimAPI_MakeCone(1.5,3.36,1.86).Shape(),'translate',[x,y,seat-1.86]),shapes)
                z=v['bearing_holder_nut_top']-2.5
                clear('holder_M3_nut',hexagon('m3',2.5,[x,y,z]),shapes)
                clear('holder_nut_bottom_loading',hexagon('m3',v['bearing_holder_depth']+v['bearing_holder_nut_top'],[x,y,-v['bearing_holder_depth']]),{'bearing_holder':shapes['bearing_holder']})
        clear('holder_axial_tool_access',cylinder(1.05,12,[0,0,v['wiggle_join_head_seat']-12]),shapes)
        # The cup must widen upward; no bearing-seat roof can overhang its bore.
        holder=shapes['bearing_holder']
        clear('holder_open_bearing_loading',cylinder(10.5,-v['bearing_holder_seat_floor']+2,[0,0,v['bearing_holder_seat_floor']]),{'bearing_holder':holder})
    if not bearing:
        shaft_hardware(clear,shapes,v)
    return dict(status='passed',checks=checks,retention=retention,maximum_overlap_mm3=max(c['overlap_mm3'] for c in checks))


def fit_print_parts(views,names,v):
    bearing=bool({'bearing_baseplate','bearing_holder'} & set(names))
    placements={
        'motor_mount':(0,0,0),'bearing_baseplate':(0,0,0),
        'motor_spacer':(0,0,-v['motor_spacer_depth']),
        'bearing_holder':(0,0,-v.get('bearing_holder_depth',0)),
        'pin_front':(0,0,v['front_z']),
        'eccentric_hub_lower':(0,0,v['lower_support_bottom'] if bearing else v['drive_base_bottom']),
        'eccentric_hub_upper':(0,0,v['seam_z']),
        'drive_sleeve':(0,0,v['drive_sleeve_bottom']),
        'bearing_retainer':(0,0,v['wiggle_join_head_seat']),
        'rotor_a':(v['eccentricity'],0,v['rotor_a_z']),
        'rotor_b':(-v['eccentricity'],0,v['rotor_b_z']+v['disc_thickness']),
        'output_casing_lower':(0,0,v['lower_split_z']),
        'output_casing_lobes':(0,0,v['lower_split_z']),
        'output_casing_upper':(0,0,v['upper_split_z']),
    }
    shapes={}
    for name in names:
        shape=read_step(views/'parts'/(name+'.step'))
        if name.startswith('eccentric_hub_') and name.endswith(('_a','_b')):
            shape=_move(shape,'rotate',[-90 if name.endswith('_a') else 90,0,0])
            placements[name]=(0,0,0)
        if name=='bearing_retainer' and 'eccentric_hub_lower_a' in names:
            shape=_move(shape,'rotate',[180,0,0]);placements[name]=(0,0,v['lower_support_bottom'])
        if name in ('rotor_b','output_casing_lower'):shape=_move(shape,'rotate',[180,0,0])
        shapes[name]=_move(shape,'translate',placements[name])
    return check(shapes,v,bearing)


def verify(views):
    record=json.loads((views/'export.json').read_text(encoding='utf8'))
    assert record['status']=='native_export_checked'
    v={p['name']:p['value'] for p in record['parameters']['parameters']}
    bearing=bool({'bearing_baseplate','bearing_holder'} & set(record['parts']))
    result=fit_print_parts(views,record['parts'],v)
    result.update(source_sha256=record['source_sha256'],parameters=v,sampling=record['sampling'],
                  native_parts=record['parts'],bearing_input=bearing)
    (views/'mechanical.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('views',type=Path);a=p.parse_args();verify(a.views)
