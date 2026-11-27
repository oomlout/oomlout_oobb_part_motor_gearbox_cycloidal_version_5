"""One-file native V7. Python authors it once; saved parameters drive the design.

No linked geometry, imported BReps, web server or regeneration callback.
The old recipe is used only as an independent baseline/reference for verification.
"""
import argparse
import json
import math
from pathlib import Path
import uuid

from oobb_solidcraft.registry import discover
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft import api as oobb
from gearbox_native.project import PROJECT
from gearbox_native import controls
from gearbox_native.acceptance import health_check
from gearbox_native.native_tabs import tab_parameters, TAB_RADIUS


def polar(radius, count, phase=0):
    return [[f'({radius}) * cos({phase+i*360/count!r} deg)',
             f'({radius}) * sin({phase+i*360/count!r} deg)'] for i in range(count)]


def parameters(d):
    values=controls.defaults()
    for name in ('reduction','automatic_pitch','radius_buffer','contact_pitch_radius','contact_radius',
                 'eccentricity','profile_clearance','casing_wall','disc_thickness','disc_gap',
                 'standoff_radius','standoff_pitch_radius','guide_radius','guide_pitch_radius',
                 'top_bearing','bottom_bearing','input_angle'):
        spec=controls.SPECS[name]
        comment=spec['description'].replace(' Rebuild required.','').replace('Update gearbox','Native model')
        d.parameter(name,f"{values[name]} {spec['unit']}".strip(),unit=spec['unit'],favorite=True,comment=comment)
    d.parameter('explode','0 mm',favorite=True,comment='Axial exploded spacing; 0 mm assembles the mechanism.')
    d.parameter('print_layout','0',unit='',favorite=True,comment='0 = assembled/exploded; 1 = all eight parts laid out on their print faces.')
    d.parameter('casing_bearing','6810',unit='',favorite=True,comment='Catalogue code for BOTH casing bearings. See CASING_BEARINGS.md for options. Fit is not guaranteed.')
    d.parameter('casing_fit_checks','0',unit='',favorite=True,comment='Optional casing passage/backing/pin-envelope guards: 0 off, 1 on. Not a complete collision check.')
    # Catalogue codes select dimensions inside the native expression graph.
    # A selector is 1 at its integer code and zero at all other integer codes.
    from gearbox_native.parts import bearing_spec
    catalogue={}
    for code in [*range(6700,6800),*range(6800,6900)]:
        try:catalogue[code]=bearing_spec(str(code))
        except ValueError:pass  # Unsupported catalogue codes fail the native selector guard.
    for side in ('bottom','top','casing'):
        for field,key in [('bore','id'),('od','od'),('width','depth')]:
            expr=' + '.join(f'max(0, 1 - abs({side}_bearing - {code})) * {spec[key]} mm' for code,spec in catalogue.items())
            name='casing_bore_catalogue' if side=='casing' and field=='bore' else f'{side}_{field}'
            d.parameter(name,expr)
        selector=' + '.join(f'max(0, 1 - abs({side}_bearing - {code}))' for code in catalogue)
        d.parameter(f'{side}_catalogue_guard',f'sqrt(-abs(({selector}) - 1)) + sqrt(-abs({side}_bearing - floor({side}_bearing)))',unit='')
    expressions=[
        ('ring_count','reduction',''),
        ('reduction_integer_guard','sqrt(-abs(reduction - floor(reduction)))',''),
        ('reduction_range_guard','sqrt(min(reduction - 12, 24 - reduction))',''),
        ('auto_switch_guard','sqrt(-abs(automatic_pitch - floor(automatic_pitch))) + sqrt(automatic_pitch * (1 - automatic_pitch))',''),
        ('print_switch_guard','sqrt(-abs(print_layout - floor(print_layout))) + sqrt(print_layout * (1 - print_layout))',''),
        ('casing_checks_switch_guard','sqrt(-abs(casing_fit_checks - floor(casing_fit_checks))) + sqrt(casing_fit_checks * (1 - casing_fit_checks))',''),
        ('unit_guard','sqrt(-abs(native_unit / (1 mm) - 1))',''),
        ('seat_clearance','0.1 mm','mm'),('endplay','0.1 mm','mm'),
        ('journal_clearance','0.1 mm','mm'),('minimum_web','2 mm','mm'),
        ('guide_orbit_radius','guide_radius + eccentricity + 0.2 mm','mm'),
        ('guide_m6','(guide_radius - 1.5 mm) / (1.5 mm)',''),
        ('guide_bore_radius','1.8 mm + guide_m6 * (3.25 mm - 1.8 mm)','mm'),
        ('guide_head_radius',f"3 mm + guide_m6 * ({oobb.gv('screw_socket_cap_radius_m6','3dpr')} mm - 3 mm)",'mm'),
        ('guide_nut_depth',f"2.5 mm + guide_m6 * ({oobb.gv('nut_depth_m6','true')} mm - 2.5 mm)",'mm'),
        ('post_orbit_radius','standoff_radius + eccentricity + 0.15 mm','mm'),
        ('feature_pitch_limit','max(guide_pitch_radius + guide_orbit_radius, standoff_pitch_radius + post_orbit_radius) + minimum_web + eccentricity + contact_radius + profile_clearance','mm'),
        ('bearing_pitch_limit','max(bottom_od, top_od) / 2 + seat_clearance + minimum_web + eccentricity + contact_radius + profile_clearance','mm'),
        ('contact_spacing_limit','(contact_radius + minimum_web / 2) / sin(180 deg / ring_count)','mm'),
        # Analytic maximum-curvature bound for the offset roller envelope.
        # rho_stationary = 3*sqrt(3*(N-1))*sqrt(R^2-(N*e)^2)/(N+1)^1.5.
        ('undercut_pitch_limit','sqrt((ring_count * eccentricity)^2 + (contact_radius + profile_clearance)^2 * (ring_count + 1)^3 / (27 * (ring_count - 1)))','mm'),
        ('minimum_pitch','max(max(feature_pitch_limit, bearing_pitch_limit), max(undercut_pitch_limit, max(contact_spacing_limit, ring_count * eccentricity / 0.9)))','mm'),
        ('pitch','automatic_pitch * ceil((minimum_pitch + radius_buffer) / (0.05 mm) - 0.000000001) * 0.05 mm + (1 - automatic_pitch) * contact_pitch_radius','mm'),
        ('casing_bore','pitch + max(0 mm, 2 * eccentricity - contact_radius)','mm'),
        ('casing_radius','max(pitch + contact_radius + casing_wall, casing_od / 2 + seat_clearance + casing_wall)','mm'),
        ('bearing_lip_radius','casing_od / 2 - 1.3 mm','mm'),
        ('rotor_swept_radius','pitch + 2 * eccentricity - contact_radius - profile_clearance','mm'),
        ('motor_plate_depth','4 mm','mm'),('drive_start','2.5 mm','mm'),('drive_radius','11 mm','mm'),
        ('rear_seat_top','motor_plate_depth + 0.3 mm + casing_width + endplay','mm'),
        ('drive_depth','9 mm','mm'),('rotor_a_z','max(drive_start + drive_depth + 0.5 mm, rear_seat_top + 0.6 mm)','mm'),
        ('rear_support_top','rotor_a_z - 0.5 mm','mm'),
        ('rotor_b_z','rotor_a_z + disc_thickness + disc_gap','mm'),
        ('seam_z','rotor_a_z + disc_thickness + disc_gap / 2','mm'),
        ('front_z','rotor_b_z + disc_thickness + 0.5 mm','mm'),
        ('front_depth','casing_width + 1.1 mm','mm'),('housing_top','front_z + front_depth','mm'),
        ('hub_top','max(housing_top, 32 mm)','mm'),('casing_bottom','4.5 mm','mm'),
        ('front_seat_bottom','front_z + 0.8 mm','mm'),
        ('casing_bore_diameter','casing_bore_catalogue','mm'),
        ('carrier_radius','casing_bore_diameter / 2 - journal_clearance','mm'),
        ('carrier_shoulder_radius','casing_bore_diameter / 2 + 1.5 mm','mm'),
        ('motor_plate_half','max(37 mm, carrier_shoulder_radius + minimum_web)','mm'),
        ('bottom_seat_depth','bottom_width + 2 * endplay','mm'),
        ('top_seat_depth','top_width + 2 * endplay','mm'),
        ('bottom_journal','bottom_bore / 2 - journal_clearance','mm'),
        ('top_journal','top_bore / 2 - journal_clearance','mm'),
        ('bottom_shoulder','bottom_bore / 2 + 0.8 mm','mm'),
        ('top_shoulder','top_bore / 2 + 0.8 mm','mm'),
        ('bottom_journal_z','rotor_a_z + disc_thickness - bottom_seat_depth','mm'),
        ('top_journal_end','rotor_b_z + top_seat_depth','mm'),
        ('key_top','27.5 mm','mm'),('key_depth','key_top - seam_z','mm'),
        *tab_parameters(),
        ('tab_radius',TAB_RADIUS,'mm'),('tab_depth','3 mm','mm'),
        ('tab_root','sqrt(casing_radius^2 - (22 mm)^2) - 0.8 mm','mm'),
        ('split_extent','max(100 mm, tab_radius + 10 mm)','mm'),
        ('layout_scale','max(1, (2 * (tab_radius + 7 mm) + 6 mm) / (110 mm))',''),
        ('output_angle','input_angle / ring_count','deg'),
        ('profile_phase','180 deg / (ring_count - 1)','deg'),
        ('pitch_guard','sqrt((pitch - minimum_pitch + 0.00000001 mm) / (1 mm))',''),
        ('bearing_backing_margin','(bearing_lip_radius - casing_bore + 0.00000001 mm) / (1 mm)',''),
        ('bearing_backing_guard','sqrt(max(0, bearing_backing_margin) + casing_fit_checks * min(0, bearing_backing_margin))',''),
        ('assembly_pass_margin','(bearing_lip_radius - rotor_swept_radius - 0.05 mm + 0.00000001 mm) / (1 mm)',''),
        ('assembly_pass_guard','sqrt(max(0, assembly_pass_margin) + casing_fit_checks * min(0, assembly_pass_margin))',''),
        ('disc_lip_guard','sqrt((disc_thickness - max(bottom_seat_depth, top_seat_depth) - 0.8 mm + 0.00000001 mm) / (1 mm))',''),
        ('guide_web_guard','sqrt((guide_pitch_radius - guide_orbit_radius - max(bottom_od, top_od) / 2 - seat_clearance - minimum_web) / (1 mm))',''),
        ('post_web_guard','sqrt((standoff_pitch_radius - post_orbit_radius - max(bottom_od, top_od) / 2 - seat_clearance - minimum_web) / (1 mm))',''),
        ('post_wall_guard','sqrt((standoff_radius - 2.5 mm) / (1 mm))',''),
        ('track_separation_guard','sqrt((sqrt(guide_pitch_radius^2 + standoff_pitch_radius^2 - 2 * guide_pitch_radius * standoff_pitch_radius * cos(30 deg)) - guide_orbit_radius - post_orbit_radius - minimum_web) / (1 mm))',''),
        ('key_wall_guard','sqrt((min(bottom_journal, top_journal) - eccentricity - 6.45 mm) / (1 mm))',''),
        ('fixed_pin_envelope_margin','(carrier_radius - max(guide_pitch_radius + guide_radius + minimum_web, standoff_pitch_radius + standoff_radius)) / (1 mm)',''),
        ('fixed_pin_envelope_guard','sqrt(max(0, fixed_pin_envelope_margin) + casing_fit_checks * min(0, fixed_pin_envelope_margin))',''),
        ('key_depth_guard','sqrt((key_depth - 2 mm) / (1 mm))',''),
        ('post_screw_tip_guard','sqrt((front_z + 2.6 mm - 25 mm - 0.2 mm) / (1 mm))',''),
        ('guide_nut_roof_guard','sqrt((rear_support_top - front_z - 1.4 mm + 20 mm - 0.2 mm - guide_nut_depth - 0.5 mm) / (1 mm))',''),
        ('guide_radius_guard','sqrt(-abs(guide_m6 - floor(guide_m6))) + sqrt(guide_m6 * (1 - guide_m6))',''),
        ('gap_guard','sqrt((disc_gap - 0.1 mm) / (1 mm))',''),
    ]
    for name,expr,unit in expressions:d.parameter(name,expr,unit=unit)


def profile_geometry():
    cases=[dict(ring_pin_count=n,pitch_radius=31.15,eccentricity=e) for n in (12,16,18,20) for e in (1.,1.2,1.4)]
    cases += [dict(ring_pin_count=16,pitch_radius=29.4),dict(eccentricity=1.39)]
    return discover().module('cycloidal_pattern').profile(dict(ring_pin_count=20,pitch_radius=31.15,
        eccentricity=1.4,roller_radius=3.,clearance=.2),validation_cases=cases)


def rotor(d,side,geometry):
    name='rotor_'+('a','b')[side];bearing=('bottom','top')[side]
    d.component(name)
    api=discover().module('parametric_profile')
    prefix=name
    setup=api.parameter_commands(geometry,prefix=prefix)
    aliases={'pitch_radius':'pitch','eccentricity':'eccentricity','roller_radius':'contact_radius',
             'clearance':'profile_clearance','ring_pin_count':'ring_count'}
    for entry in setup['commands']:
        for key,native in setup['parameters'].items():
            if entry['params']['name']==native:entry['params']['expression']=aliases[key]
        d.do(entry['command'],**entry['params'])
    sketch=d.sketch('equation')
    xy=api.coordinate_expressions(geometry,prefix=prefix)
    curves=d.line(xy,closed=False)
    d.pattern(curves,'ring_count - 1')
    d.extrude(sketch,'disc_thickness','new',all_profiles=True)
    if side:d.move(axis=[0,0,1],angle='profile_phase')
    sketch=d.sketch('orbit_holes')
    for pitch,radius,count,phase in [('guide_pitch_radius','guide_orbit_radius',6,30),
                                    ('standoff_pitch_radius','post_orbit_radius',3,0)]:
        for pos in polar(pitch,count,phase):
            if side:pos[1]=f'-({pos[1]})'
            d.circle(radius,pos)
    d.circle(f'{bearing}_od / 2 - 0.8 mm')
    d.extrude(sketch,'disc_thickness','cut')
    d.holes(f'{bearing}_od / 2 + seat_clearance',f'{bearing}_seat_depth + 0.01 mm',
            z=f'disc_thickness - {bearing}_seat_depth',name='bearing_seat')
    return name


def nut(d,xy,top,depth=40,rotation=30,guide=False):
    d.oobb_cut('oobb_nut',position=[*xy,top],radius_name='m3',depth=depth,
               zz='top',rot=[0,0,rotation],overhang=True,
               catalogue_variant={'request':{'radius_name':'m6'},'selector':'guide_m6'} if guide else None)


def motor_mount(d):
    d.component('motor_mount')
    sketch=d.sketch('OOBB_5x5')
    d.rounded_rectangle('-motor_plate_half','motor_plate_half','-motor_plate_half','motor_plate_half',5)
    d.extrude(sketch,'motor_plate_depth','new')
    d.cylinder('carrier_radius','rear_support_top',name='casing_inner_journal')
    d.cylinder('carrier_shoulder_radius',.3,z='motor_plate_depth',name='casing_inner_shoulder')
    posts=polar('standoff_pitch_radius',3)
    for xy in posts:
        d.cylinder('standoff_radius','front_z - rear_support_top',z='rear_support_top',xy=xy,name='integral_standoff')
        d.cylinder(2.3,1.6,z='front_z',xy=xy,name='front_register')
    d.holes(11.2,'motor_plate_depth + 0.05 mm',name='NEMA17_pilot')
    d.holes(11.25,'rear_support_top - motor_plate_depth + 0.05 mm',z='motor_plate_depth',name='drive_clearance')
    d.oobb_cut('oobb_holes',width=5,height=5,depth=4,holes=['perimeter'],radius_name='m6',both_holes=True)
    for xy in ((15.5,15.5),(-15.5,15.5),(-15.5,-15.5),(15.5,-15.5)):
        d.oobb_cut('oobb_screw_countersunk',position=[*xy,'motor_plate_depth'],radius_name='m3',
                   depth=4.02,zz='top',nut_include=False,overhang=False,coaxial_extension=(3,0,7.6))
    guides=polar('guide_pitch_radius',6,30)
    d.holes('guide_bore_radius','rear_support_top',positions=guides,name='guide_screws')
    for xy in guides:nut(d,xy,'front_z + 1.4 mm - 20 mm + 0.2 mm + guide_nut_depth + 0.1 mm',rotation=0,guide=True)
    d.holes(1.7,'front_z + 1.6 mm',positions=posts,name='standoff_screws')
    for xy in posts:nut(d,xy,'front_z + 2.6 mm - 25 mm + 0.2 mm + 2.5 mm + 0.1 mm')


def front_carrier(d):
    d.component('pin_front')
    d.cylinder('carrier_shoulder_radius',.8,operation='new',name='bearing_shoulder')
    d.cylinder('carrier_radius','front_depth',name='casing_inner_journal')
    d.holes(7.5,'front_depth',name='6701_retaining_lip')
    d.holes(9.1,4.2,z='front_depth - 4.2 mm',name='6701_seat')
    guides=polar('guide_pitch_radius',6,30);posts=polar('standoff_pitch_radius',3)
    d.holes('guide_bore_radius','front_depth',positions=guides,name='guide_screws')
    d.holes('guide_head_radius','front_depth - 1.4 mm + 0.1 mm',z=1.4,positions=guides,name='guide_socket_access')
    d.holes(2.45,1.75,positions=posts,name='standoff_registers')
    d.holes(1.8,'front_depth',positions=posts,name='standoff_screws')
    d.holes(3,'front_depth - 2.6 mm + 0.1 mm',z=2.6,positions=posts,name='standoff_socket_access')


def key(d,z,depth,clearance=0,operation='join'):
    # Circle plus one flat; the temporary cutting tool is fully native.
    target=d.body;d.index+=1;tool=target+f'_key_{d.index}';d.body=tool
    d.cylinder(4.9+clearance,depth,z=z,operation='new',name='D_key')
    d.box(4.3+clearance,25,-15,15,f'({depth}) + 0.05 mm',z=f'({z}) - 0.01 mm',operation='cut',name='key_flat')
    d.body=target
    d.do('solid.combine',target=target,tools=[tool],operation=operation)


def lower_hub(d):
    d.component('eccentric_hub_lower')
    d.cylinder('drive_radius','drive_depth',z='drive_start',operation='new',name='direct_drive')
    d.cylinder('bottom_journal - eccentricity - 0.35 mm','seam_z - drive_start - drive_depth',
               z='drive_start + drive_depth',name='spine')
    d.cylinder('bottom_shoulder','bottom_journal_z - drive_start - drive_depth',
               z='drive_start + drive_depth',xy=('eccentricity',0),name='eccentric_shoulder')
    d.cylinder('bottom_journal','bottom_seat_depth',z='bottom_journal_z',xy=('eccentricity',0),name='eccentric_journal')
    key(d,'seam_z','key_depth + 0.02 mm')
    d.holes(1.8,'key_top + 0.1 mm - drive_start',z='drive_start',name='hub_joining_screw')
    d.holes(2.55,'24.2 mm - drive_start',z='drive_start',name='5mm_motor_shaft')
    d.oobb_cut('oobb_nut',position=[0,0,24.8],radius_name='m3',depth=2.9,zz='bottom',rot=[0,0,30],overhang=True)
    d.oobb_cut('oobb_nut',position=[5,0,'drive_start + 4 mm'],radius_name='m3',depth=2.8,
               zz='bottom',rot=[0,90,0],clearance='left',clearance_tightness=.15,overhang=True)
    d.box(0,12,-1.8,1.8,3.6,z='drive_start + 4 mm - 1.8 mm',operation='cut',name='grub_screw_access')


def upper_hub(d):
    d.component('eccentric_hub_upper')
    d.revolve([[0,'seam_z'],['top_journal','seam_z'],['top_journal','top_journal_end'],
               ['top_shoulder','top_journal_end + 0.8 mm'],[0,'top_journal_end + 0.8 mm']],
              operation='new',name='eccentric_journal_and_shoulder')
    d.move(translate=['-eccentricity',0,0])
    d.cylinder('top_journal - eccentricity - 0.35 mm','front_z - seam_z',z='seam_z',name='spine')
    d.cone('top_journal - eccentricity',5.9,'front_z - top_journal_end',z='top_journal_end',name='front_shaft_taper')
    d.cylinder(5.9,'hub_top - front_z',z='front_z',name='6701_journal')
    key(d,'seam_z - 0.01 mm','key_depth + 0.17 mm',.15,'cut')
    d.holes(1.8,'hub_top - seam_z + 0.1 mm',z='seam_z',name='hub_joining_screw')
    d.holes(3.1,'hub_top - 28.8 mm + 0.1 mm',z=28.8,name='socket_cap_clearance')


def output_half(d,side):
    d.component('output_casing_'+('lower','upper')[side])
    depth='housing_top - casing_bottom'
    d.cylinder('casing_radius',depth,z='casing_bottom',inner='casing_bore',operation='new',name='continuous_shell')
    sketch=d.sketch('ring_contacts','casing_bottom')
    curves=d.circle('contact_radius',('pitch',0));d.pattern(curves,'ring_count')
    d.extrude(sketch,depth,all_profiles=True)
    sketch=d.sketch('straight_contact_backs','casing_bottom')
    curves=d.line([['pitch','-contact_radius'],['casing_radius - 0.1 mm','-contact_radius'],
                   ['casing_radius - 0.1 mm','contact_radius'],['pitch','contact_radius']])
    d.pattern(curves,'ring_count');d.extrude(sketch,depth,all_profiles=True)
    for z in ('rear_seat_top','front_seat_bottom - minimum_web'):
        d.cylinder('casing_radius','minimum_web',z=z,inner='bearing_lip_radius',name='bearing_outer_shoulder')
    d.holes('casing_od / 2 + seat_clearance','rear_seat_top - casing_bottom + 0.02 mm',z='casing_bottom - 0.01 mm',name='rear_casing_seat')
    d.holes('casing_od / 2 + seat_clearance','housing_top - front_seat_bottom + 0.02 mm',z='front_seat_bottom - 0.01 mm',name='front_casing_seat')
    for i in range(3):
        r=f'bearing_lip_radius - (bearing_lip_radius - pitch + contact_radius) * {i}/3'
        d.holes(r,.21,z=f'rear_seat_top + {i*.2-.005!r} mm',name='bearing_run_transition')
    d.holes('bearing_lip_radius','housing_top - front_z',z='front_z',name='front_bearing_clearance')
    if side:d.box('-split_extent','split_extent','-split_extent','split_extent','seam_z + 1 mm',z=-1,operation='cut',name='middle_split')
    else:d.box('-split_extent','split_extent','-split_extent','split_extent','housing_top',z='seam_z',operation='cut',name='middle_split')
    z='seam_z' if side else 'seam_z - tab_depth'
    shell=d.body
    for angle in (0,90,180,270):
        d.body=shell+f'_tab_{angle}'
        sketch=d.sketch('OOBB_1x3',z)
        d.rounded_rectangle('tab_radius - 7 mm','tab_radius + 7 mm',-22,22,5)
        d.extrude(sketch,'tab_depth','new')
        d.box('tab_root','tab_radius',-22,22,'tab_depth',z=z,name='full_length_connection')
        d.holes('casing_radius - 0.8 mm','tab_depth',z=z,name='clear_working_cavity')
        d.move(axis=[0,0,1],angle=f'{angle} deg')
        a=math.radians(angle);co,si=round(math.cos(a)),round(math.sin(a))
        def xy(x,y):return [f'({x}) * {co} - ({y}) * {si}',f'({x}) * {si} + ({y}) * {co}']
        for radius,offsets in [(oobb.gv('hole_radius_m6','3dpr'),(-15,0,15)),(oobb.gv('hole_radius_m3','3dpr'),(-7.5,7.5))]:
            if side and radius==oobb.gv('hole_radius_m3','3dpr'):offsets=(-7.5,)
            d.holes(radius,'tab_depth + 0.02 mm',z=f'({z}) - 0.01 mm',
                positions=[xy('tab_radius',f'{v} mm') for v in offsets],name='OOBB_mount_holes')
        join=xy('tab_radius','7.5 mm')
        if side:
            d.oobb_cut('oobb_screw_countersunk',position=[*join,'seam_z + tab_depth'],radius_name='m3',
                       depth=3.02,zz='top',nut_include=False,overhang=False)
        else:
            # Lower half prints inverted. Its nut roof and overhang layers
            # therefore face the seam after applying the print orientation.
            d.oobb_cut('oobb_nut',position=[*join,'seam_z - tab_depth - 0.1 mm'],radius_name='m3',
                       depth=2.7,zz='top',rotation=[180,0,-30],overhang=True)
        tool=d.body;d.body=shell
        d.do('solid.combine',target=shell,tools=[tool],operation='join')


PRINT_POSITIONS={'output_casing_lower':(55,55),'output_casing_upper':(165,55),
    'motor_mount':(40,153),'rotor_a':(115,150),'rotor_b':(185,150),
    'pin_front':(30,224),'eccentric_hub_lower':(78,215),'eccentric_hub_upper':(108,215)}


def place(d,name):
    d.body=name
    x,y=PRINT_POSITIONS[name]
    ax=ay='0 mm';az='0 mm';pz='0 mm'
    if name=='pin_front':az='front_z + 5 * explode'
    elif name=='rotor_a':ax='eccentricity * cos(input_angle)';ay='eccentricity * sin(input_angle)';az='rotor_a_z + 2 * explode'
    elif name=='rotor_b':
        d.move(axis=[1,0,0],angle='180 deg * (1 - print_layout)')
        ax='-eccentricity * cos(input_angle)';ay='-eccentricity * sin(input_angle)';az='rotor_b_z + disc_thickness + 3 * explode'
    elif name.startswith('eccentric_hub'):
        d.move(axis=[0,0,1],angle='input_angle * (1 - print_layout)')
        az=('1' if name.endswith('lower') else '4')+' * explode'
        pz='-drive_start' if name.endswith('lower') else '-seam_z'
    elif name.startswith('output_casing'):
        if name.endswith('lower'):
            d.move(axis=[1,0,0],angle='180 deg * print_layout');pz='seam_z'
        else:pz='-seam_z'
        d.move(axis=[0,0,1],angle='output_angle * (1 - print_layout)')
        az=('1' if name.endswith('lower') else '6')+' * explode'
    d.move(translate=[f'(1 - print_layout) * ({ax}) + print_layout * layout_scale * {x} mm',
                      f'(1 - print_layout) * ({ay}) + print_layout * layout_scale * {y} mm',
                      f'(1 - print_layout) * ({az}) + print_layout * ({pz})'])


BUILDERS={'motor_mount':motor_mount,'pin_front':front_carrier,'eccentric_hub_lower':lower_hub,
          'eccentric_hub_upper':upper_hub,'output_casing_lower':lambda d:output_half(d,0),
          'output_casing_upper':lambda d:output_half(d,1)}


def run(output,only_rotor=False,piece=None):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    geometry=profile_geometry()
    (output/'profile.json').write_text(json.dumps(geometry),encoding='utf-8')
    with MCPClient(output/'author',allow_path=output,timeout=600) as client:
        d=discover().module('native_design').Design(client)
        parameters(d)
        if piece:
            print('Native',piece,flush=True);BUILDERS[piece](d)
        else:
            print('Native rotor A',flush=True);rotor(d,0,geometry)
            if not only_rotor:
                print('Native rotor B',flush=True);rotor(d,1,geometry)
                for name,fn in BUILDERS.items():
                    print('Native',name,flush=True);fn(d)
                for name in ['rotor_a','rotor_b',*BUILDERS]:place(d,name)
        health_check(client,output/'health.json')
        require_ok(client.call('save',dict(path=str(output/'gearbox.solidcraft'))))
        require_ok(client.call('export',dict(path=str(output/'gearbox.step'))))
        require_ok(client.call('export',dict(path=str(output/'gearbox.stl'))))
        (output/'commands.json').write_text(json.dumps(d.commands),encoding='utf-8')
    print('Saved',output,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path)
    parser.add_argument('--rotor',action='store_true');parser.add_argument('--piece',choices=list(BUILDERS));args=parser.parse_args()
    run(args.output or PROJECT/'build/native_v7'/('author_'+uuid.uuid4().hex[:8]),args.rotor,args.piece)
