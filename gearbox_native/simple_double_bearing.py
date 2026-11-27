"""SolidCraft master for the double-bearing gearbox with removable M3 ring contacts."""
import argparse
import json
import math
from pathlib import Path

from oobb_solidcraft import api as oobb
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.registry import discover
from gearbox_native.acceptance import health_check
from gearbox_native.native_v8 import patterned_holes, rotor_outline
from gearbox_native import stacked_disc_shaft as stack
from gearbox_native.project import PROJECT

from gearbox_native import double_bearing_housing as housing

STYLE = 'simple_double_bearing_version_2'
MASTER = STYLE + '.solidcraft'
PROFILE = PROJECT/'solidcraft'/(STYLE + '_profile.json')
POSITIONS = {
    'output_nut_plate': (54,54), 'output_cap_plate': (162,54),
    'rotor_a': (43,148), 'rotor_b': (125,148),
    'carrier_bottom': (199,145), 'carrier_top': (199,204),
    'input_d_shaft': (18,213), 'round_shim_bottom': (45,213),
    'eccentric_spacer_a': (72,213), 'eccentric_spacer_b': (99,213),
    'round_shim_top': (126,213), 'shaft_end_washer': (153,213),
}

OLD_POSITIONS = POSITIONS.copy()
POSITIONS.update(rotor_b=(120,147), carrier_bottom=(194,189), carrier_top=(43,214), input_d_shaft=(84,207),
                 round_shim_bottom=(108,206), eccentric_spacer_a=(132,206),
                 eccentric_spacer_b=(94,228), round_shim_top=(120,228), shaft_end_washer=(146,228))
LOOSE_DISC_POSITIONS=POSITIONS.copy()
POSITIONS.update(rotor_a=(284,44), rotor_a_cap=(364,44), rotor_b=(284,124), rotor_b_cap=(364,124),
                 input_d_shaft=(258,220), input_d_shaft_b=(279,168),
                 shaft_bush_bottom=(309,190), shaft_bush_top=(337,190))
CLAMSHELL_POSITIONS=POSITIONS.copy()
POSITIONS.update(carrier_bottom_cap=(430,38),carrier_top_cap=(430,94))
SECOND_BED={'carrier_bottom_cap','carrier_top_cap','rotor_a','rotor_a_cap','rotor_b','rotor_b_cap','input_d_shaft','input_d_shaft_b','shaft_bush_bottom','shaft_bush_top'}
RING_NAME = 'connected_contact_ring'
RING_PRINT = (194,189)


CARRIER_POSITIONS = POSITIONS.copy()
THIRD_BED = {*housing.CYLINDERS, housing.FOOT}
POSITIONS.update(output_nut_cylinder=(542,54),output_cap_cylinder=(654,54),output_lower_row_plate=(550,175))
POSITIONS[housing.CIRCLE]=(790,80)


PRE_STACK_POSITIONS = POSITIONS.copy()
RETIRED_SHAFT = {n for n in POSITIONS if n.startswith(('shaft_', 'input_d_', 'round_shim_', 'eccentric_spacer_'))}
for n in RETIRED_SHAFT:
    del POSITIONS[n]
SECOND_BED.difference_update(RETIRED_SHAFT)
for i, row in enumerate(stack.LAYERS):
    POSITIONS[row[0]] = (266 + 34*(i%4), 185 + 36*(i//4))
    SECOND_BED.add(row[0])


def connected_ring(d):
    d.component(RING_NAME)
    d.cylinder('pitch + contact_radius + 1.5 mm','middle_length',
               inner='pitch + contact_radius - 0.5 mm',operation='new',name='outer_connecting_wall')
    face=d.sketch('spacer_bosses')
    d.pattern(d.circle('contact_radius',('pitch',0)),'ring_count')
    d.extrude(face,'middle_length','join',all_profiles=True)
    patterned_holes(d,'spacer_bore','middle_length',pitch='pitch',count='ring_count',phase='0 deg',name='ring_bores')
    d.move(axis=[0,0,1],angle='output_angle * (1 - print_layout)')
    d.move(translate=['194 mm * layout_scale * print_layout','189 mm * layout_scale * print_layout','(middle_start + 5 * explode) * (1 - print_layout)'])



def parameters(d):
    for name,expr,unit,note in [
        ('reduction','20','','Ring contacts. The fixed disc orientation gives this output reduction.'),
        ('pitch','39 mm','mm','Radius to M3 ring screws.'),
        ('eccentricity','1.5 mm','mm','Offset of each eccentric journal, in opposite directions.'),
        ('contact_radius','3.5 mm','mm','Outside radius of the round M3 spacers.'),
        ('profile_clearance','0.15 mm','mm','Running allowance at the round spacers.'),
        ('middle_length','16 mm','mm','Matched round spacer length. Use 16 or 20 mm for the 7 mm clamshell discs.'),
        ('disc_gap','0.50 mm','mm','Clearance between the cycloids.'),
        ('spacer_bore','1.65 mm','mm','Bore radius of the printed M3 sleeves and ring.'),
        ('guide_running_gap','0.15 mm','mm','Target radial clearance after the cycloid takes up its full eccentric orbit.'),
        ('guide_entry','0.60 mm','mm','45-degree lead-in on both exterior faces of each cycloid.'),
        ('input_angle','0 deg','deg','Input position. Output turns by input angle / reduction.'),
        ('print_layout','0','','1 selects the flat print layout.'),
        ('explode','0 mm','mm','Axial separation per assembly level.'),
    ]: d.parameter(name,expr,unit=unit,favorite=True,comment=note)
    for name,expr,unit in [
        ('ring_count','reduction',''),('profile_phase','180 deg / (ring_count - 1)','deg'),
        ('output_angle','input_angle / ring_count','deg'),('plate_height','9 mm','mm'),
        ('mount_flange_depth','3 mm','mm'),('bearing_ring_radius','pitch + max(contact_radius + 1.25 mm, 4.75 mm)','mm'),
        ('middle_start','plate_height','mm'),('middle_end','plate_height + middle_length','mm'),
        ('stack_height','2 * plate_height + middle_length','mm'),
        ('disc_thickness','7 mm','mm'),('disc_half','disc_thickness / 2','mm'),
        ('end_gap','(middle_length - 2 * disc_thickness - disc_gap) / 2','mm'),
        ('guide_socket_depth','min(0.45 mm, end_gap - 0.2 mm)','mm'),
        ('guide_socket_fit','0.08 mm','mm'),
        ('stack_gap_guard','sqrt((end_gap - 0.25 mm) / native_unit)',''),
        ('join_length','5 mm * floor((stack_height - 3 mm) / (5 mm))','mm'),
        ('cap_recess','stack_height - join_length','mm'),
        ('clamp_pitch','26.5 mm','mm'),('clamp_phase','45 deg','deg'),
        ('disc_a_z','middle_start + end_gap','mm'),('disc_b_z','middle_end - end_gap - disc_thickness','mm'),
        ('m6_bore',f"{oobb.gv('hole_radius_m6','3dpr')} mm",'mm'),
        ('m3_bore',f"{oobb.gv('hole_radius_m3','3dpr')} mm",'mm'),
        ('shaft_journal',f"{oobb.gv('bearing_6704_id','true')} mm - 0.05 mm",'mm'),
        ('shaft_race_od',f"{2*oobb.gv('bearing_6704_od','true')} mm",'mm'),('shaft_race_width',f"{oobb.gv('bearing_6704_depth','true')} mm",'mm'),
        ('main_bearing_bore',f"{2*oobb.gv('bearing_6810_id','true')} mm",'mm'),('main_bearing_od',f"{2*oobb.gv('bearing_6810_od','true')} mm",'mm'),
        ('main_bearing_width',f"{oobb.gv('bearing_6810_depth','true')} mm",'mm'),
        ('seat_fit','0.10 mm','mm'),('main_inner_face','plate_height - mount_flange_depth','mm'),
        ('carrier_split','main_inner_face','mm'),('race_end_gap','carrier_split - shaft_race_width - 0.05 mm','mm'),
        ('carrier_extension','3 mm','mm'),
        ('carrier_drive_length','35 mm','mm'),('drive_tip','(stack_height - carrier_drive_length - 2.4 mm) / 2','mm'),
        ('main_outer_face','main_inner_face - main_bearing_width','mm'),
        ('main_shoulder','main_bearing_bore / 2 + 1.25 mm','mm'),
        ('carrier_core','plate_height - carrier_split + guide_socket_depth','mm'),('carrier_cap_height','carrier_split + carrier_extension','mm'),
        ('disc_lip','(disc_thickness - shaft_race_width) / 2','mm'),
        ('guide_pitch','20.0 mm','mm'),('guide_count','6',''),('guide_pair_a','8 deg','deg'),
        ('guide_pair_b','82 deg','deg'),('guide_pair_c','135 deg','deg'),
        ('guide_track','min(contact_radius + eccentricity + guide_running_gap, guide_pitch - shaft_race_od / 2 - seat_fit - 0.75 mm)','mm'),
        ('ring_wall_gap_guard','sqrt((2 * contact_radius - 2 * eccentricity + profile_clearance - 0.6 mm) / native_unit)',''),
        ('guide_motion_guard','sqrt((guide_track - contact_radius - eccentricity - guide_socket_fit - 0.02 mm) / native_unit)',''),
        ('track_guard','sqrt((guide_pitch - guide_track - shaft_race_od / 2 - seat_fit - 0.7499999 mm) / native_unit)',''),
        ('profile_guard','sqrt((pitch^2 - (ring_count * eccentricity)^2 - (contact_radius + profile_clearance)^2 * (ring_count + 1)^3 / (27 * (ring_count - 1))) / native_unit^2)',''),
        ('disc_guard','sqrt((disc_lip - 0.35 mm) / native_unit)',''),
        ('hardware_guard','sqrt((2 * pitch * sin(180 deg / ring_count) - 6.6 mm) / native_unit)',''),
    ]: d.parameter(name,expr,unit=unit)


    stack.parameters(d)
    housing.parameters(d)


def carrier_mounts():
    return [(x,y) for x in (-15,-7.5,7.5,15) for y in (-15,-7.5,7.5,15) if abs(x)!=abs(y)]


def guide_angles(flipped=False):
    """Angles in the local sketch, mirrored when the part is turned over."""
    pairs=('guide_pair_a','guide_pair_b','guide_pair_c')
    angles=(*pairs, *(f'({p} + 180 deg)' for p in pairs))
    return [f'-({a})' if flipped else a for a in angles]


def guide_holes(d,radius,depth,flipped,name,z=0):
    positions=[(f'guide_pitch * cos({a})',f'guide_pitch * sin({a})') for a in guide_angles(flipped)]
    d.holes(radius,depth,z=z,positions=positions,name=name)


def carrier_socket_overhang(d):
    """OOBB's two bridge layers above the downward-opening M3 head seats."""
    from gearbox_native.carrier_overhang import socket_roof_layers
    seat='stack_height + carrier_extension - drive_tip - carrier_drive_length'
    for layer in socket_roof_layers():
        sk=d.sketch('OOBB_socket_cap_overhang_true',f'({seat}) + {layer["z"]} mm')
        for phase in guide_angles(True):
            d.line([[f'(guide_pitch + ({u}) * native_unit) * cos({phase}) - ({w}) * native_unit * sin({phase})',
                     f'(guide_pitch + ({u}) * native_unit) * sin({phase}) + ({w}) * native_unit * cos({phase})']
                    for u,w in layer['points']])
        d.extrude(sk,layer['depth'],'cut',all_profiles=True)


def carrier(d,name):
    d.component(name)
    cap=name.endswith('_cap')
    bottom='bottom' in name
    flipped=bottom != cap
    points=[(x,-y if flipped else y) for x,y in carrier_mounts()]
    height='carrier_cap_height' if cap else 'carrier_core'
    if cap:
        d.cylinder('main_bearing_bore / 2 - 0.05 mm',height,operation='new',name='outer_carrier_half')
        d.cylinder('main_shoulder','carrier_extension + main_outer_face',name='outside_6810_inner_race_cap')
        d.holes('shaft_race_od / 2 - 0.8 mm',height,name='6704_retaining_lip')
        d.holes('shaft_race_od / 2 + seat_fit','carrier_split - race_end_gap + 0.06 mm',
                z='carrier_extension + race_end_gap - 0.05 mm',name='6704_outer_half_seat')
        if bottom:
            # Socket is open at the bed. Mirror the catalogue nut roof steps about its seat.
            layers=discover().module('native_hardware_pattern').prisms(dict(radius_name='m3',depth=2.7,zz='bottom',overhang=True))
            seat='carrier_extension + drive_tip + 2.4 mm'
            for layer in sorted(layers,key=lambda q:-q['depth']):
                if layer['z']>0:continue
                z='-0.01 mm' if layer['z']==0 else f'({seat}) - ({layer["z"] + layer["depth"] + .02}) * native_unit'
                depth=f'({seat}) + 0.02 mm' if layer['z']==0 else layer['depth']+.04
                sk=d.sketch('drive_nut_socket',z)
                pp=layer['points']
                if layer['z']==-.3:pp=[(u+math.copysign(.03,u),w) for u,w in pp]
                for phase in guide_angles(flipped):
                    d.line([[f'(guide_pitch + ({u}) * native_unit) * cos({phase}) - ({w}) * native_unit * sin({phase})',
                             f'(guide_pitch + ({u}) * native_unit) * sin({phase}) + ({w}) * native_unit * cos({phase})'] for u,w in pp])
                d.extrude(sk,depth,'cut',all_profiles=True)
        else:
            guide_holes(d,3.1,'stack_height + carrier_extension - drive_tip - carrier_drive_length + 0.01 mm',
                        flipped,'drive_cap_recess',z=-.01)
    else:
        d.cylinder('main_shoulder',height,operation='new',name='flat_6810_inner_race_shoulder')
        d.holes('shaft_race_od / 2 - 0.8 mm',height,name='6704_flat_retaining_face')
        guide_holes(d,'contact_radius + guide_socket_fit','guide_socket_depth',flipped,'sleeve_end_register')
        # Two bridge layers reduce the blind sleeve seat to the screw bore on the print bed.
        for index,length in enumerate(('1.68 * contact_radius','3.50 mm')):
            sk=d.sketch('sleeve_seat_bridge',f'guide_socket_depth + {index*.3} mm')
            for phase in guide_angles(flipped):
                d.line([[f'(guide_pitch + ({u}) * native_unit) * cos({phase}) - ({w}) * sin({phase})',
                         f'(guide_pitch + ({u}) * native_unit) * sin({phase}) + ({w}) * cos({phase})']
                        for u,w in [(-1.75,f'-({length}) / 2'),(1.75,f'-({length}) / 2'),
                                    (1.75,f'({length}) / 2'),(-1.75,f'({length}) / 2')]])
            d.extrude(sk,.3,'cut',all_profiles=True)
        for x,y in points:
            angle=math.degrees(math.atan2(y,x))+30
            d.oobb_cut('oobb_nut',position=[x,y,'carrier_core - 2.55 mm'],rotation=[0,0,angle],
                       radius_name='m3',depth=2.6,zz='bottom',overhang=True)
    guide_holes(d,1.7,height,flipped,'six_drive_axes')
    d.holes('m3_bore',height,positions=points,name='OOBB_M3_half_grid')
    if cap and not bottom:carrier_socket_overhang(d)


def disc(d,name,geo):
    side=int(name.startswith('rotor_b'))
    cap=name.endswith('_cap')
    flip=bool(side) != cap
    screw_phase='-clamp_phase' if flip else 'clamp_phase'
    rotor_outline(d,side,geo,name=name,depth='disc_half',phase='-profile_phase' if cap else 'profile_phase')
    guide_holes(d,'guide_track','disc_half',flip,'round_drive_tracks')
    for phase in guide_angles(flip):
        xy=[f'guide_pitch * cos({phase})',f'guide_pitch * sin({phase})']
        d.cone('guide_track + guide_entry + 0.01 mm','guide_track - 0.02 mm','guide_entry + 0.03 mm',
               z=-.01,xy=xy,operation='cut',name='guide_entry_funnel')
    d.holes('shaft_race_od / 2 - 0.8 mm','disc_half',name='outer_race_retaining_lip')
    d.holes('shaft_race_od / 2 + seat_fit','shaft_race_width / 2 + 0.07 mm',
            z='disc_lip - 0.05 mm',name='open_half_bearing_seat')
    for i in range(3):
        angle=f'({screw_phase} + {120*i} deg)'
        xy=[f'clamp_pitch * cos({angle})', f'clamp_pitch * sin({angle})']
        if cap:
            # Nut starts 0.35 mm below the outer face. Extend the catalogue opening to air.
            d.oobb_cut('oobb_nut',position=[*xy,-.1],radius_name='m3',depth=2.85,
                       zz='bottom',overhang=True)
            d.holes(1.65,'disc_half',positions=[xy],name='M3_clamp_shank')
        else:
            # Trim the oversized 3dpr catalogue cone at the actual Ø6 head.
            # The 7 mm cutter spans the disc; the installed hardware is M3 × 6.
            head = oobb.gv('screw_countersunk_radius_m3','3dpr')
            bore = oobb.gv('hole_radius_m3','3dpr')
            depth = oobb.gv('screw_countersunk_depth_m3','3dpr')
            trim = depth * (head - 3.0) / (head - bore)
            d.oobb_cut('oobb_screw_countersunk',position=[*xy,-trim],rotation=[180,0,0],
                       radius_name='m3',depth=7,zz='top',nut_include=False,overhang=False)


def place(d,name):
    if name in stack.NAMES:return stack.place(d,name,POSITIONS[name])
    x,y=POSITIONS[name]; d.body=name
    p='(1 - print_layout)'
    flip=name in ('output_nut_plate','output_cap_cylinder','carrier_bottom','carrier_top_cap','rotor_b','rotor_a_cap')
    if flip:d.move(axis=[1,0,0],angle=f'180 deg * {p}')
    z,level={
      'output_nut_plate':('middle_start',.35),'output_cap_plate':('middle_end',9.65),
      'output_nut_cylinder':('-housing_lip_depth',-.4),'output_cap_cylinder':('stack_height + housing_lip_depth',10.4),
      housing.FOOT:('middle_end',9.65),
      housing.CIRCLE:('middle_end',9.65),
      'carrier_bottom':('middle_start + guide_socket_depth',1),'carrier_top':('middle_end - guide_socket_depth',9),
      'carrier_bottom_cap':('-carrier_extension',0.3),'carrier_top_cap':('stack_height + carrier_extension',9.7),
      'rotor_a':('disc_a_z',4),'rotor_b':('disc_b_z + disc_thickness',7),
      'rotor_a_cap':('disc_a_z + disc_thickness',4.55),'rotor_b_cap':('disc_b_z',6.45),
    }[name]
    angle='output_angle' if name.startswith('output_') else None
    if name in (housing.FOOT,housing.CIRCLE):angle=None
    if angle:d.move(axis=[0,0,1],angle=f'{angle} * {p}')
    orbit={'rotor_a':'eccentricity','rotor_b':'-eccentricity','rotor_a_cap':'eccentricity','rotor_b_cap':'-eccentricity'}.get(name,'0 mm')
    if name==housing.FOOT:orbit='housing_preview_x'
    if name==housing.CIRCLE:orbit='-2 * circle_plate_radius - 20 mm'
    assembly_angle='0 deg' if name in (housing.FOOT,housing.CIRCLE) else 'input_angle'
    d.move(translate=[f'{x} mm * layout_scale * print_layout + ({orbit}) * cos({assembly_angle}) * {p}',
                      f'{y} mm * layout_scale * print_layout + ({orbit}) * sin({assembly_angle}) * {p}',
                      f'(({z}) + ({level}) * explode) * {p}'])


def profile():
    return discover().module('cycloidal_pattern').profile(
        dict(ring_pin_count=20,pitch_radius=39,eccentricity=1.5,roller_radius=3.5,clearance=.15),
        validation_cases=[dict(ring_pin_count=15,eccentricity=2)])


def build(folder):
    folder.mkdir(parents=True,exist_ok=False)
    geo=profile()
    (folder/'profile.json').write_text(json.dumps(geo),encoding='utf8')
    with MCPClient(folder/'author',allow_path=PROJECT,timeout=600) as client:
        d=discover().module('native_design').Design(client);parameters(d)
        for name in POSITIONS:
            print('Building',name,flush=True)
            if name==housing.CIRCLE:housing.circle_plate(d)
            elif name in housing.CYLINDERS:housing.cylinder(d,name)
            elif name.startswith('output_'):housing.plate(d,name)
            elif name.startswith('carrier_'):carrier(d,name)
            elif name.startswith('rotor_'):disc(d,name,geo)
            else:stack.part(d,name)
        for name in POSITIONS:place(d,name)
        connected_ring(d)
        require_ok(client.execute('browser.visibility',items=[RING_NAME],visible=False))
        health_check(client,folder/'health.json')
        assert require_ok(client.call('measure'))['body_count']==len(POSITIONS)+1
        require_ok(client.call('save',dict(path=str(folder/'gearbox_controls.solidcraft'))))
    from gearbox_native.double_bearing_hardware import append
    append(folder/'gearbox_controls.solidcraft',folder/'complete.solidcraft',folder/'hardware')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path)
    build(parser.parse_args().folder.resolve())
