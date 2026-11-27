"""Stationary captive-nut covers and a separate rotating rear output extension.

The motor cage and outer mounting plates receive revised attachments. The
original shaft, adapter and gearbox carriers retain their accepted geometry.
Positions and motor-depth dependencies live in the native SolidCraft graph.
"""
import argparse
import hashlib
import json
import math
import shutil
import zipfile
from pathlib import Path
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.registry import discover
from gearbox_native.acceptance import health_check
from gearbox_native.nema17_double_bearing import PROJECT,MASTER,PART_ID,ANGLES,LONG_INDICES,centers,cage_post_holes

BASE=PROJECT/'solidcraft/nema17_flange_before_end_caps.solidcraft'
POSITIONS=dict(front_cover_spacer=(1060,40),front_cover_face=(1150,45),front_cover_nuts=(1240,45),
               rear_cover_face=(1150,140),rear_cover_nuts=(1240,140),rear_output_extension=(1080,250))
POSITIONS.update({f'rear_output_spacer_{i+1}':(1180,200+15*i) for i in range(2)})
POSITIONS.update({f'rear_output_joiner_{i+1}':(1350,250+30*i) for i in range(3)})
POSITIONS.update(output_circle_rear_plate=(1410,70),output_lower_row_plate=(550,205),output_lower_row_rear_plate=(1540,100))
SUPPORT=[(x,y) for x in (-15,15) for y in (-7.5,7.5)]
FRONT_JOINS=[(x,y) for x in (-7.5,7.5) for y in (-15,15)]
REAR_ANGLES=[8,135,262]
REAR_JOINS=[(36*math.cos(math.radians(a)),36*math.sin(math.radians(a))) for a in REAR_ANGLES]
JOINER_ANGLES=(90,210,330)
JOINER_PITCH=52.5
JOINER_SCREW_PITCH=15
EXTENSION_POSTS=[tuple((JOINER_PITCH*math.cos(math.radians(a))+sign*JOINER_SCREW_PITCH/2*math.sin(math.radians(a)),
                        JOINER_PITCH*math.sin(math.radians(a))-sign*JOINER_SCREW_PITCH/2*math.cos(math.radians(a)))
                       for sign in (-1,1)) for a in JOINER_ANGLES]
EXTENSION_JOINS=[point for pair in EXTENSION_POSTS for point in pair]
SPACER_JOINS=[(-37.5,-45),(37.5,-45)]
# Two extra braces supplement the existing twenty contact sleeves. They are
# clocked away from the four lower-plate attachment heads and tool paths.
BUILDERS={}


def extension_positions():
    """Native centres shared by both end plates and all joining hardware."""
    return [(f'rear_joiner_pitch * cos({a} deg) + ({sign}) * rear_joiner_screw_pitch / 2 * sin({a} deg)',
             f'rear_joiner_pitch * sin({a} deg) - ({sign}) * rear_joiner_screw_pitch / 2 * cos({a} deg)')
            for a in JOINER_ANGLES for sign in (-1,1)]


def parameters(d):
    for name,expr,unit in [
        ('cover_radius','motor_cage_post_pitch + motor_cage_post_radius','mm'),
        ('cover_face_depth','3 mm','mm'),('cover_nut_depth','6 mm','mm'),
        ('cover_depth','cover_face_depth + cover_nut_depth','mm'),
        ('cover_socket_recess','0 mm','mm'),
        ('front_cover_base','stack_height + carrier_extension','mm'),
        ('front_cover_screw_length','25 mm','mm'),
        ('rear_cover_screw_length','16 mm','mm'),
        ('front_cover_standoff','front_cover_screw_length + middle_end + 0.3 mm + cover_socket_recess - front_cover_base - cover_depth','mm'),
        ('front_cover_standoff_guard','sqrt(front_cover_standoff / native_unit)',''),
        ('front_cover_screw_guard','sqrt((40 mm - front_cover_screw_length) / native_unit)',''),
        ('front_cover_inner','front_cover_base + front_cover_standoff','mm'),
        ('front_cover_face_z','front_cover_inner + cover_depth','mm'),
        ('rear_cover_face_z','motor_cage_base - cover_depth','mm'),
        ('rear_extension_inner','cover_radius + 1.5 mm','mm'),
        ('rear_holder_proud','1.5 mm','mm'),
        ('rear_extension_base','rear_cover_face_z + rear_holder_proud','mm'),
        ('rear_extension_height','main_inner_face - rear_extension_base','mm'),
        ('rear_extension_post_radius','6.5 mm','mm'),
        ('motor_tube_wall','3 mm','mm'),
        ('motor_cable_window_clock','30 deg','deg'),
        ('rear_extension_flange_depth','3 mm','mm'),
        ('rear_joiner_pitch','52.5 mm','mm'),
        ('rear_joiner_screw_pitch','15 mm','mm'),
        ('rear_joiner_height','rear_extension_height - rear_extension_flange_depth','mm'),
        ('rear_joiner_base','rear_extension_base + rear_extension_flange_depth','mm'),
        ('outer_connection_depth','3 mm','mm'),
        ('outer_socket_recess','0 mm','mm'),
        ('outer_screw_seat','middle_start','mm'),
        ('rear_extension_screw_length','10 mm','mm'),
        ('outer_spacer_screw_length','25 mm','mm'),
        ('rear_access_radius','3.2 mm','mm'),
        ('cage_join_length','16 mm','mm'),
        ('cage_nut_inset','11.3 mm','mm'),
        ('rear_square_edge','max(housing_plate_half, 52.5 mm + rear_extension_post_radius + 0.5 mm)','mm'),
        ('bracket_full_row_start','15 mm * ceil(max(bearing_ring_radius + 5.924 mm, 52.5 mm + rear_extension_post_radius + 6.724 mm) / (15 mm))','mm'),
        ('bracket_lower_edge','bracket_full_row_start + 22 mm','mm'),
        ('rear_extension_screw_guard','sqrt((40 mm - rear_extension_screw_length) / native_unit)',''),
        ('front_cover_shaft_clearance','shaft_race_od / 2 + 0.3 mm','mm'),
    ]:d.parameter(name,expr,unit=unit)
    d.parameter('rear_cable_radius','4 mm',favorite=True,comment='Radius of the fixed rear cable passage. The checked layout uses 4 mm; enlarging it requires a joining-screw clearance check.')
    d.parameter('rear_cable_guard','sqrt((6 mm - rear_cable_radius) / native_unit)',unit='')


def catalogue_hex(size,depth):
    layers=discover().module('native_hardware_pattern').prisms(dict(radius_name=size,depth=depth,zz='bottom',overhang=True))
    return layers,next(r for r in layers if r['z']==0 and len(r['points'])==6)


def mount_layout(end):
    """OOBB nuts on the actual 15/7.5 mm grid, with a solid web between pockets."""
    from shapely.geometry import Polygon,Point
    joins=FRONT_JOINS if end=='front' else REAR_JOINS
    obstacles=[Point(*xy).buffer(3.1) for xy in joins]
    if end=='rear':obstacles.append(Point(0,-30).buffer(6))
    accepted=[];boundary=Point(0,0).buffer(40.5-.8,quad_segs=128)
    for size,depth in [('m6',5.1),('m3',2.7)]:
        _,hexagon=catalogue_hex(size,depth)
        candidates=[]
        for i in range(-5,6):
            for j in range(-5,6):
                if (size=='m6') != (i%2==0 and j%2==0):continue
                candidates.append((7.5*i,7.5*j))
        for x,y in sorted(candidates,key=lambda q:(math.hypot(*q),q)):
            shape=Polygon([(x+u,y+w) for u,w in hexagon['points']])
            if not boundary.contains(shape):continue
            if any(shape.distance(obstacle)<.8 for obstacle in obstacles):continue
            accepted.append(dict(size=size,xy=[x,y],depth=depth,rotation=0))
            obstacles.append(shape)
    return accepted


def captive_pockets(d,rows):
    for size,depth in [('m6',5.1),('m3',2.7)]:
        chosen=[r for r in rows if r['size']==size]
        if not chosen:continue
        layers,_=catalogue_hex(size,depth)
        # Open at the split face. Both halves print flat without an internal roof.
        for layer in sorted(layers,key=lambda q:-q['depth']):
            if layer['z']>=depth:continue
            sk=d.sketch('OOBB_'+size+'_captive_overhang',f'cover_nut_depth - {depth} mm + {layer["z"]} mm')
            for row in chosen:
                x,y=row['xy'];d.line([[x+u,y+w] for u,w in layer['points']])
            d.extrude(sk,layer['depth'],'cut',all_profiles=True)


def side_nut(d,xy,z,angle,depth=2.7):
    # OOBB's "left" clearance extends local +X. Rotate +X toward the outside.
    d.oobb_cut('oobb_nut',position=[*xy,z],rotation=[0,0,angle],
               radius_name='m3',depth=depth,zz='bottom',overhang=True,clearance='left')


def motor_cage(d):
    d.component('motor_cage')
    d.cylinder('cover_radius + 0.3 mm','mount_flange_depth',inner='motor_clear_radius',operation='new',name='fixed_inner_rear_flange')
    d.cylinder('motor_clear_radius + motor_tube_wall','motor_cage_height',inner='motor_clear_radius',name='continuous_motor_support_tube')
    for a in [ANGLES[i] for i in LONG_INDICES]:
        xy=centers('motor_cage_post_pitch',[a])[0]
        d.cylinder('motor_cage_post_radius','motor_cage_height',xy=xy,name='fixed_motor_support')
    for a in [ANGLES[i] for i in LONG_INDICES]:
        xy=centers('motor_cage_post_pitch',[a])[0]
        d.holes('m3_bore','cage_join_length',z='motor_cage_height - cage_join_length',positions=[xy],name='cage_M3x16_axis')
        side_nut(d,xy,'motor_cage_height - cage_nut_inset',a)
        d.holes('m3_bore',12,positions=[xy],name='rear_cover_M3x16')
        side_nut(d,xy,'4 mm',a)
    # Open, peaked cable window: its sloped roof prints with the tube upright.
    target=d.body;tool='motor_tube_cable_window';d.body=tool
    d.polygon([[-5,0],[5,0],[5,9],[0,14],[-5,9]],45,operation='new',name='support_free_cable_window')
    d.move(axis=[1,0,0],angle='90 deg')
    d.move(axis=[0,0,1],angle='motor_cable_window_clock')
    d.body=target;d.do('solid.combine',target=target,tools=[tool],operation='cut')


def front_spacer(d):
    d.component('front_cover_spacer')
    d.cylinder('main_shoulder','front_cover_standoff',inner='front_cover_shaft_clearance',operation='new',name='fixed_front_cover_standoff')
    d.holes('m3_bore','front_cover_standoff',positions=FRONT_JOINS,name='front_cover_join_axes')


def cover(d,end,half):
    name=f'{end}_cover_{half}';d.component(name)
    depth='cover_face_depth' if half=='face' else 'cover_nut_depth'
    d.cylinder('cover_radius',depth,operation='new',name='stationary_OOBB_cover_'+half)
    mirror=-1 if (end,half) in [('front','face'),('rear','nuts')] else 1
    rows=[dict(r,xy=[r['xy'][0],mirror*r['xy'][1]]) for r in mount_layout(end)]
    joins=[(x,mirror*y) for x,y in (FRONT_JOINS if end=='front' else REAR_JOINS)]
    if half=='face':
        from oobb_solidcraft import api
        # Catalogue cone, trimmed to a Ø6 head plus 0.1 mm radial fit.
        head=api.gv('screw_countersunk_radius_m3','3dpr')
        bore=api.gv('hole_radius_m3','3dpr')
        cone=api.gv('screw_countersunk_depth_m3','3dpr')
        trim=cone*(head-3.1)/(head-bore)
        for xy in joins:
            d.oobb_cut('oobb_screw_countersunk',position=[*xy,-trim],rotation=[180,0,0],
                       radius_name='m3',depth=25,zz='top',nut_include=False,overhang=False)
    else:
        d.holes('m3_bore',depth,positions=joins,name='cover_clamp_axes')
        captive_pockets(d,rows)
    for size in ('m6','m3'):
        points=[r['xy'] for r in rows if r['size']==size]
        if points:d.holes(size+'_bore',depth,positions=points,name='OOBB_'+size+'_mounts')
    if end=='rear':d.holes('rear_cable_radius',depth,positions=[(0,-30*mirror)],name='fixed_cable_exit')


def rotating_extension(d):
    from shapely.geometry import Point,LineString
    d.component('rear_output_extension')
    d.cylinder('circle_plate_radius','rear_extension_flange_depth',inner='rear_extension_inner',operation='new',name='rotating_rear_OOBB_flange')
    for size,envelope in [('m6',5.924),('m3',3.326)]:
        points=[]
        for i in range(-8,9):
            for j in range(-8,9):
                if (size=='m6') != (i%2==0 and j%2==0):continue
                x,y=i*7.5,j*7.5;r=math.hypot(x,y)
                if r-envelope<42.8 or r+envelope>66.2:continue
                if any(LineString(pair).distance(Point(x,y))<envelope+7.3 for pair in EXTENSION_POSTS):continue
                points.append((x,y))
        d.holes(size+'_bore','rear_extension_flange_depth',positions=points,name='rear_output_OOBB_'+size)
    for xy in extension_positions():
        countersink(d,xy,0,up=True,length=10)


def rear_joiner(d,name):
    """One identical oblong joiner, used at three 120-degree stations."""
    d.component(name)
    d.cylinder('rear_extension_post_radius','rear_joiner_height',xy=['-rear_joiner_screw_pitch / 2',0],operation='new',name='first_round_end')
    d.box('-rear_joiner_screw_pitch / 2','rear_joiner_screw_pitch / 2',
          '-rear_extension_post_radius','rear_extension_post_radius','rear_joiner_height',name='straight_joiner_web')
    d.cylinder('rear_extension_post_radius','rear_joiner_height',xy=['rear_joiner_screw_pitch / 2',0],name='second_round_end')
    for x in ('-rear_joiner_screw_pitch / 2','rear_joiner_screw_pitch / 2'):
        d.holes('m3_bore','rear_joiner_height',positions=[(x,0)],name='M3_both_end_axis')
        side_nut(d,[x,0],'2.6 mm',90)
        side_nut(d,[x,0],'rear_joiner_height - 5.3 mm',90)


def rear_spacer(d,name):
    d.component(name)
    d.cylinder('contact_radius','middle_length',inner='spacer_bore',operation='new',name='existing_round_spacer_geometry')


REVISED_PLATES={'output_cap_plate','output_nut_plate','output_circle_plate','output_circle_rear_plate','output_lower_row_plate','output_lower_row_rear_plate'}


def countersink(d,xy,z,up=False,length=25):
    """OOBB countersink with the catalogue fit cone trimmed to a Ø6.2 mouth."""
    from oobb_solidcraft import api
    head=api.gv('screw_countersunk_radius_m3','3dpr')
    bore=api.gv('hole_radius_m3','3dpr')
    cone=api.gv('screw_countersunk_depth_m3','3dpr')
    trim=cone*(head-3.1)/(head-bore)
    d.oobb_cut('oobb_screw_countersunk',position=[*xy,f'({z}) + {trim if not up else -trim} mm'],
               rotation=[180,0,0] if up else None,radius_name='m3',depth=length,
               zz='top',nut_include=False,overhang=False)


def attachment_plate(d,name):
    """Flat 3 mm plates: rear attachment screws and independent clocked braces."""
    from gearbox_native.native_v8 import patterned_holes
    d.component(name)
    circular=name.startswith('output_circle')
    foot=name.startswith('output_lower_row')
    rear=name in ('output_nut_plate','output_circle_rear_plate','output_lower_row_rear_plate')
    if circular:
        d.cylinder('circle_plate_radius','mount_flange_depth',operation='new',name='flat_circular_flange')
    else:
        sk=d.sketch('two_full_rows_blank' if foot else 'square_flange_blank')
        d.rounded_rectangle('-housing_plate_half','housing_plate_half',
                            '-bracket_lower_edge' if foot else '-rear_square_edge',
                            7 if foot else 'rear_square_edge',4)
        d.extrude(sk,'mount_flange_depth','new')
        if foot:
            d.cylinder('bearing_ring_radius','mount_flange_depth',name='compact_round_upper_edge')
            sk=d.sketch('third_post_attachment_ear')
            d.rounded_rectangle('-7.5 mm - rear_extension_post_radius','7.5 mm + rear_extension_post_radius',
                                '38 mm','52.5 mm + rear_extension_post_radius + 0.5 mm',4)
            d.extrude(sk,'mount_flange_depth')
        # Complete support for the paired post footprints where the square or
        # cropped outline needs a small local ear, rather than a larger plate.
        for xy in extension_positions():
            d.cylinder('rear_extension_post_radius + 0.5 mm','mount_flange_depth',xy=xy,name='paired_joiner_plate_support')
    # The extended square edge is most robust when its independent grid is
    # drilled before the conical seats. Their axes never overlap that grid.
    if not (circular or foot):attachment_grid(d,circular,foot)
    # Cut heads into the blank before other holes; coincident pre-drilled bores
    # make the native catalogue Boolean unnecessarily fragile.
    for xy in (extension_positions() if rear else SPACER_JOINS):countersink(d,xy,'mount_flange_depth',length=10 if rear else 25)
    d.holes('m3_bore' if rear else 'rear_access_radius','mount_flange_depth',
            positions=SPACER_JOINS if rear else extension_positions(),name='brace_axes' if rear else 'extension_screw_and_driver_access')
    d.holes('main_bearing_od / 2 - 0.85 mm','mount_flange_depth',name='6810_outer_race_lip')
    patterned_holes(d,1.7,'mount_flange_depth',pitch='pitch',count='ring_count',phase='0 deg',name='contact_screw_pattern')
    if circular or foot:attachment_grid(d,circular,foot)


def attachment_grid(d,circular,foot):
    for size,envelope in [('m6',5.924),('m3',3.326)]:
        points=[]
        # Match the existing native housing_grid_guard (60 mm). Circular
        # alternatives have their own 90 mm guard. Keep solver sketches small.
        limit=12 if circular else 8
        for i in range(-limit,limit+1):
            for j in range(-14 if foot else -limit,1 if foot else limit+1):
                if (size=='m6') != (i%2==0 and j%2==0):continue
                x,y=7.5*i,7.5*j;r=math.hypot(x,y)
                if r<32.5+envelope:continue
                if any(math.dist((x,y),q)<envelope+3.3+.5 for q in SPACER_JOINS):continue
                if any(math.dist((x,y),q)<envelope+3.2+.5 for q in EXTENSION_JOINS):continue
                if circular:
                    if r>97:continue
                    edge=f'{r+envelope} mm - circle_plate_radius'
                elif foot:edge=f'max({abs(x)} mm - housing_grid_radius, {-y+envelope+.7} mm - bracket_lower_edge)'
                else:edge=f'{max(abs(x),abs(y))} mm - housing_grid_radius'
                block=f'max(bearing_ring_radius + {envelope} mm - {r} mm, {edge})'
                park=f'400 mm * min(1, max(0, ceil(({block}) / native_unit)))'
                points.append([f'{x} mm + {park}',y])
        for offset in range(0,len(points),40):
            sk=d.sketch('clear_OOBB_'+size+'_'+str(offset//40))
            for point in points[offset:offset+40]:d.circle(size+'_bore',point)
            d.extrude(sk,'mount_flange_depth','cut',all_profiles=True)


BUILDERS.update(motor_cage=motor_cage,front_cover_spacer=front_spacer,
                front_cover_face=lambda d:cover(d,'front','face'),front_cover_nuts=lambda d:cover(d,'front','nuts'),
                rear_cover_face=lambda d:cover(d,'rear','face'),rear_cover_nuts=lambda d:cover(d,'rear','nuts'),
                rear_output_extension=rotating_extension)
BUILDERS.update({f'rear_output_spacer_{i+1}':lambda d,i=i:rear_spacer(d,f'rear_output_spacer_{i+1}') for i in range(2)})
BUILDERS.update({f'rear_output_joiner_{i+1}':lambda d,i=i:rear_joiner(d,f'rear_output_joiner_{i+1}') for i in range(3)})
BUILDERS.update({n:lambda d,n=n:attachment_plate(d,n) for n in sorted(REVISED_PLATES)})

def place(d,name):
    if name in REVISED_PLATES:
        from gearbox_native.simple_double_bearing import POSITIONS as basic_positions
        from gearbox_native.nema17_double_bearing import POSITIONS as motor_positions
        d.body=name;p='(1 - print_layout)'
        x,y=dict(basic_positions,**motor_positions,**POSITIONS)[name]
        rear=name in ('output_nut_plate','output_circle_rear_plate','output_lower_row_rear_plate')
        z='main_inner_face' if rear else 'middle_end';level=.35 if rear else 9.65
        parked={'output_circle_plate':'-2 * circle_plate_radius - 20 mm',
                'output_circle_rear_plate':'-6 * circle_plate_radius - 60 mm',
                'output_lower_row_plate':'housing_preview_x',
                'output_lower_row_rear_plate':'2 * housing_preview_x'}.get(name,'0 mm')
        if name in ('output_cap_plate','output_nut_plate'):d.move(axis=[0,0,1],angle=f'output_angle * {p}')
        d.move(translate=[f'{x} mm * layout_scale * print_layout + ({parked}) * {p}',
                          f'{y} mm * layout_scale * print_layout',f'(({z}) + {level} * explode) * {p}'])
        return
    if name=='motor_cage':
        from gearbox_native.nema17_double_bearing import place as original_place
        return original_place(d,name)
    d.body=name;p='(1 - print_layout)';x,y=POSITIONS[name]
    if name.startswith('rear_output_joiner_'):
        a=JOINER_ANGLES[int(name.rsplit('_',1)[1])-1]
        d.move(axis=[0,0,1],angle=f'{a-90} deg * {p}')
        d.move(translate=[f'rear_joiner_pitch * cos({a} deg) * {p}',f'rear_joiner_pitch * sin({a} deg) * {p}',0])
        d.move(axis=[0,0,1],angle=f'output_angle * {p}')
        d.move(translate=[f'{x} mm * layout_scale * print_layout',f'{y} mm * layout_scale * print_layout',f'(rear_joiner_base - 4.5 * explode) * {p}'])
        return
    if name.startswith('rear_output_spacer_'):
        i=int(name.rsplit('_',1)[1])-1;ax,ay=SPACER_JOINS[i]
        d.move(translate=[ax,ay,0])
        d.move(axis=[0,0,1],angle=f'output_angle * {p}')
        d.move(translate=[f'({x} mm * layout_scale - ({ax}) * native_unit) * print_layout',
                          f'({y} mm * layout_scale - ({ay}) * native_unit) * print_layout',f'(middle_start + 5 * explode) * {p}'])
        return
    flip=name in ('front_cover_face','rear_cover_nuts')
    if flip:d.move(axis=[1,0,0],angle=f'180 deg * {p}')
    z,level={
        'front_cover_spacer':('front_cover_base',11),
        'front_cover_nuts':('front_cover_inner',12),
        'front_cover_face':('front_cover_face_z',13),
        'rear_cover_nuts':('motor_cage_base',-5),
        'rear_cover_face':('rear_cover_face_z',-6),
        'rear_output_extension':('rear_extension_base',-6),
    }[name]
    if name=='rear_output_extension':d.move(axis=[0,0,1],angle=f'output_angle * {p}')
    d.move(translate=[f'{x} mm * layout_scale * print_layout',f'{y} mm * layout_scale * print_layout',f'(({z}) + {level} * explode) * {p}'])


def hardware(d):
    from oobb_solidcraft import api
    from gearbox_native.stacked_disc_shaft import polygon
    def finish(xy,z,level,turn=False):
        d.move(translate=[*xy,0])
        if turn:d.move(axis=[0,0,1],angle='output_angle * (1 - print_layout)')
        d.move(translate=[0,0,f'({z}) + ({level}) * explode + 180 mm * print_layout'])
    def screw(tag,xy,z,length,level,up=False,turn=False):
        d.component('hardware_endcap_'+tag)
        d.cylinder(1.5,length,operation='new',name='M3_shank')
        d.cylinder(2.75,3,z=-3,name='M3_socket_cap')
        d.polygon(polygon('0 mm','0 mm',0,1.45),1.5,z=-3,operation='cut',name='socket')
        if not up:d.move(axis=[1,0,0],angle='180 deg')
        finish(xy,z,level,turn)
    def nut(tag,xy,z,level,size='m3',angle=0,turn=False):
        d.component('hardware_endcap_'+tag)
        depth=api.gv('nut_depth_'+size,'true');radius=api.gv('nut_radius_'+size,'true')
        d.polygon(polygon('0 mm','0 mm',0,radius),depth,operation='new',name=size+'_captive_nut')
        d.holes(1.55 if size=='m3' else 3.1,depth,name='thread')
        if angle:d.move(axis=[0,0,1],angle=f'{angle} deg')
        finish(xy,z,level,turn)
    def countersunk(tag,xy,z,length,level,up=False,turn=False):
        d.component('hardware_endcap_'+tag)
        # One revolved envelope avoids a coincident cone/shank Boolean seam.
        d.revolve([[0,0],[3,0],[1.5,1.7],[1.5,length],[0,length]],
                  operation='new',name='M3_countersunk_screw')
        d.polygon(polygon('0 mm','0 mm',0,1.15),1.05,operation='cut',name='hex_socket')
        if not up:d.move(axis=[1,0,0],angle='180 deg')
        finish(xy,z,level,turn)
    for i,xy in enumerate(FRONT_JOINS):
        countersunk(f'front_join_screw_{i}',xy,'front_cover_face_z','front_cover_screw_length',13)
    for i,(xy,a) in enumerate(zip(REAR_JOINS,REAR_ANGLES)):
        countersunk(f'rear_join_M3x16_{i}',xy,'rear_cover_face_z','rear_cover_screw_length',-6,up=True)
        nut(f'rear_join_nut_{i}',xy,'motor_cage_base + 4 mm',-4,angle=a)
    for i,xy in enumerate(extension_positions()):
        a=JOINER_ANGLES[i//2]
        countersunk(f'outer_extension_screw_{i}',xy,'outer_screw_seat','rear_extension_screw_length',.5,turn=True)
        nut(f'outer_extension_nut_{i}',xy,'main_inner_face - 5.1 mm',-4.5,angle=a,turn=True)
        countersunk(f'outer_ring_screw_{i}',xy,'rear_extension_base','rear_extension_screw_length',-6,up=True,turn=True)
        nut(f'outer_ring_nut_{i}',xy,'rear_joiner_base + 2.6 mm',-4.5,angle=a,turn=True)
    for i,xy in enumerate(SPACER_JOINS):
        countersunk(f'spacer_screw_{i}',xy,'middle_end + mount_flange_depth','outer_spacer_screw_length',10,turn=True)
        nut(f'spacer_nut_{i}',xy,'main_inner_face - 2.5 mm',.2,turn=True)
    from gearbox_native.nema17_double_bearing import screw as cage_screw,nut as cage_nut
    for i in LONG_INDICES:
        xy=centers('motor_cage_post_pitch',[ANGLES[i]])[0]
        cage_screw(d,f'hardware_cage_M3x16_{i}','cage_join_length',xy,'motor_face + motor_plate_depth',-2)
        cage_nut(d,f'hardware_cage_nut_{i}',xy,'motor_face - cage_nut_inset + 0.3 mm',-4,angle=ANGLES[i])
    for end in ('front','rear'):
        for i,row in enumerate(mount_layout(end)):
            depth=api.gv('nut_depth_'+row['size'],'true')
            z=f'front_cover_face_z - cover_face_depth - {depth} mm' if end=='front' else 'rear_cover_face_z + cover_face_depth'
            nut(f'{end}_{row["size"]}_mount_nut_{i}',row['xy'],z,12.5 if end=='front' else -5.5,size=row['size'])


def group_new(client):
    tree=require_ok(client.execute('component.list',compact=True))['components']
    groups={}
    for c in tree:
        if not c['id'] or c['parent'] or c.get('children'):continue
        if c['name'].startswith('hardware_'):group='End cover hardware'
        elif c['name'].startswith(('rear_output_','output_')):group='Rotating rear output extension'
        else:group='Stationary end covers'
        groups.setdefault(group,[]).extend(o['id'] for o in c['occurrences'])
    for name,occurrences in groups.items():
        require_ok(client.execute('component.create',name=name,parent='Hardware' if name=='End cover hardware' else 0,activate=False))
        require_ok(client.execute('browser.reparent',component=name,occurrences=occurrences))


def prepare(path,isolated=False):
    if not BASE.exists():shutil.copyfile(PROJECT/MASTER,BASE)
    with zipfile.ZipFile(BASE) as z:files={n:z.read(n) for n in z.namelist()}
    doc=json.loads(files['document.json'])
    removed={c['id'] for c in doc['components'] if c['id'] and (isolated or c['name'] in ({'motor_cage'}|REVISED_PLATES|{f'hardware_cage_M3x10_{i}' for i in LONG_INDICES}|{f'hardware_cage_nut_{i}' for i in LONG_INDICES}))}
    removed_names={c['name'] for c in doc['components'] if c['id'] in removed}
    doc['components']=[c for c in doc['components'] if c['id'] not in removed]
    # The old all-parts placement pass belongs to its final active component,
    # rather than to each moved body's component. Remove those moves as well.
    doc['features']=[f for f in doc['features'] if f.get('component') not in removed
                     and not (f['type']=='move' and set(f.get('bodies',[]))&removed_names)]
    doc['occurrences']=[o for o in doc['occurrences'] if o['component'] not in removed]
    valid_features={f['id'] for f in doc['features']}
    for group in doc.get('timeline_groups',[]):group['features']=[f for f in group['features'] if f in valid_features]
    kept={g['id'] for g in doc.get('timeline_groups',[]) if g['features']}
    for _ in range(5):kept.update(g['parent'] for g in doc.get('timeline_groups',[]) if g['id'] in kept and g.get('parent') is not None)
    doc['timeline_groups']=[g for g in doc.get('timeline_groups',[]) if g['id'] in kept]
    if isolated:doc['timeline_groups']=[];doc['visibility']={}
    files['document.json']=json.dumps(doc).encode('utf8')
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for n,data in files.items():z.writestr(n,data)


def build(folder,isolated=False):
    folder.mkdir(parents=True,exist_ok=False);prepare(folder/'start.solidcraft',isolated)
    with MCPClient(folder/'author',design=folder/'start.solidcraft',allow_path=PROJECT,timeout=600) as client:
        cls=discover().module('native_design').Design;d=cls.__new__(cls)
        d.client=client;d.commands=[];d.index=14000;d.body=None
        parameters(d)
        (folder/'parts').mkdir()
        for name,builder in BUILDERS.items():
            print('BUILD',name,flush=True);builder(d)
            if isolated:
                for ext in ('step','stl'):
                    require_ok(client.call('export',dict(bodies=[name],path=str(folder/'parts'/(name+'.'+ext)))))
            else:place(d,name)
        if not isolated:
            require_ok(client.call('save',dict(path=str(folder/'printed_parts.solidcraft'))))
            hardware(d);group_new(client)
            require_ok(client.call('save',dict(path=str(folder/'authored.solidcraft'))))
        health_check(client,folder/'health.json')
        require_ok(client.call('save',dict(path=str(folder/'complete.solidcraft'))))
    (folder/'nut_layouts.json').write_text(json.dumps({end:mount_layout(end) for end in ('front','rear')},indent=2),encoding='utf8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--isolated',action='store_true')
    a=p.parse_args();build(a.folder.resolve(),a.isolated)
