"""Additive, native-parametric NEMA17 adaptation of the accepted manual gearbox.

The baseline archive is read only. Its two motor-end mounting patterns are
adapted in a copy; all new features and their edits live in that copy's graph.
"""
import argparse
import hashlib
import json
import math
import zipfile
from pathlib import Path

from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.registry import discover
from gearbox_native.project import PROJECT
from gearbox_native.acceptance import health_check

BASE = PROJECT/'simple_double_bearing_version_2.solidcraft'
MASTER = 'simple_double_bearing_version_2_nema17_flange.solidcraft'
PART_ID = 'oobb_part_motor_gearbox_cycloidal_simple_double_bearing_version_2_20_to_1_reduction_nema17_flange_40_mm_motor_depth'
POSITIONS = dict(motor_inner_adapter=(790,54), motor_cage=(790,190),
                 output_circle_plate=(940,70), output_plain_circle_plate=(940,195))
LONG_INDICES = (0,2,4)
ANGLES = ('guide_pair_a','guide_pair_b','guide_pair_c',
          'guide_pair_a + 180 deg','guide_pair_b + 180 deg','guide_pair_c + 180 deg')


def adapt_copy(target):
    """Change only named lower E/N sketch centres; retain the native history.

    No numerical mesh replacement. Native expression centres are re-evaluated
    on open, including the four physical nut references. Assertions deliberately
    stop this migration if the accepted source architecture changes.
    """
    with zipfile.ZipFile(BASE) as archive:
        files={n:archive.read(n) for n in archive.namelist()}
    doc=json.loads(files['document.json'])
    byid={c['id']:c['name'] for c in doc['components']}
    doc['params'].append(dict(name='coupler_mount_radius',expr='8 mm',unit='mm',model=False,
                             comment='5 mm flange coupler: four holes on a 16 mm bolt circle.'))
    changed=0
    for f in doc['features']:
        name=byid.get(f.get('component'))
        if f['type']!='sketch':continue
        if name in ('shaft_end_lower','shaft_mount_lower') and any(k in f['name'] for k in ('four_OOBB_mounts','flat_mount_nut')):
            for point in f['sketch']['points']:
                for axis,expr in point.get('exprs',{}).items():
                    for old,new in [('(-7.5) * native_unit','-coupler_mount_radius'),('(7.5) * native_unit','coupler_mount_radius'),
                                    ('(-7.5 mm)','(-coupler_mount_radius)'),('(7.5 mm)','(coupler_mount_radius)')]:
                        expr=expr.replace(old,new)
                    point['exprs'][axis]=expr
            changed+=1
        if name and name.startswith('hardware_shaft_mount_nut_lower_'):
            i=int(name.rsplit('_',1)[1])-1
            for point in f['sketch']['points']:
                for j,axis in enumerate(('x','y')):
                    direction=((1,0),(0,1),(-1,0),(0,-1))[i][j]
                    if direction and axis in point.get('exprs',{}):
                        point['exprs'][axis]=f"({point['exprs'][axis]}) + ({direction}) * (coupler_mount_radius - 7.5 mm)"
    assert changed==6,changed
    # These batches are replaced by explicit references: three 35 and three 40.
    removed={c['id'] for c in doc['components'] if c['name'] in ('hardware_drive_nuts','hardware_drive_caps','hardware_drive_shanks')}
    assert len(removed)==3
    # The manual model now carries its own plain circular option. The motor
    # migration owns a differently placed circle with later joiner features.
    removed.update(c['id'] for c in doc['components'] if c['name']=='output_circle_plate')
    doc['params']=[p for p in doc['params'] if p['name'] not in ('circle_grid_radius','circle_plate_radius','circle_grid_guard')]
    doc['features']=[f for f in doc['features'] if f.get('component') not in removed]
    doc['components']=[c for c in doc['components'] if c['id'] not in removed]
    doc['occurrences']=[o for o in doc['occurrences'] if o['component'] not in removed]
    files['document.json']=json.dumps(doc).encode('utf8')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,content in files.items():archive.writestr(name,content)
    return hashlib.sha256(BASE.read_bytes()).hexdigest()


def parameters(d):
    for name,expr,note in [
        ('motor_depth','40 mm','NEMA17 body length, excluding shaft; cage follows this directly.'),
        ('motor_shaft_length','24 mm','Shaft projection from the motor face.'),
        ('motor_body_width','42.3 mm','Square motor envelope, excluding connector and cable.'),
        ('motor_rear_gap','3 mm','Space between motor rear and the 3 mm mounting flange.'),
    ]:d.parameter(name,expr,favorite=True,comment=note)
    for name,expr,unit in [
        ('motor_clock','18.5 deg','deg'),
        ('motor_face','-22 mm','mm'),
        ('motor_adapter_height','-carrier_extension - motor_face','mm'),
        ('motor_plate_depth','4 mm','mm'),
        ('motor_cage_post_pitch','36 mm','mm'),
        ('motor_cage_post_radius','4.5 mm','mm'),
        ('motor_cage_height','motor_depth + motor_rear_gap + mount_flange_depth','mm'),
        ('motor_cage_base','motor_face - motor_cage_height','mm'),
        ('motor_clear_radius','motor_body_width / sqrt(2) + 1.5 mm','mm'),
        ('circle_grid_radius','15 mm * ceil((bearing_ring_radius + 6 mm) / (15 mm))','mm'),
        ('circle_plate_radius','circle_grid_radius + 7 mm','mm'),
        ('motor_guide_extension','5 mm','mm'),
        ('motor_guide_length','carrier_drive_length + motor_guide_extension','mm'),
        ('motor_guard','sqrt((40 mm - motor_guide_length) / native_unit)',''),
        ('motor_body_guard','sqrt((motor_cage_post_pitch - motor_cage_post_radius - motor_clear_radius) / native_unit)',''),
        ('motor_depth_guard','sqrt((motor_depth - 10 mm) / native_unit)',''),
        ('circle_grid_guard','sqrt((90 mm - circle_grid_radius) / native_unit)',''),
    ]:d.parameter(name,expr,unit=unit)


def centers(pitch,angles):
    return [(f'({pitch}) * cos({a})',f'({pitch}) * sin({a})') for a in angles]


def circle_grid(d,inner,depth='mount_flange_depth'):
    """OOBB full/half grid, filtered for nut clearance at both circular edges."""
    for size,envelope in [('m6',5.924),('m3',3.326)]:
        sk=d.sketch('circular_OOBB_'+size)
        for i in range(13):
            for j in range(1,13):
                if (size=='m6') != (not(i%2 or j%2)):continue
                x,y=7.5*i,7.5*j;r=math.hypot(x,y)
                blocked=f'max(({inner}) + {envelope} mm - {r} mm, {r+envelope} mm - circle_plate_radius)'
                park=f'300 mm * min(1, max(0, ceil(({blocked}) / native_unit)))'
                d.pattern(d.circle(size+'_bore',[f'{x} mm + {park}',y]),'4')
        d.extrude(sk,depth,'cut',all_profiles=True)


def circle_plate(d,name,extended=True):
    from gearbox_native.native_v8 import patterned_holes
    d.component(name)
    d.cylinder('circle_plate_radius' if extended else 'bearing_ring_radius','mount_flange_depth',
               inner='main_bearing_od / 2 - 0.85 mm',operation='new',name='flat_circular_output_plate')
    patterned_holes(d,1.7,'mount_flange_depth',pitch='pitch',count='ring_count',phase='0 deg',name='ring_screw_pattern')
    if extended:circle_grid(d,'bearing_ring_radius')


def side_window(d,angle):
    target=d.body;tool=f'access_window_{angle}';d.body=tool
    # Window floor and 45-degree roof; no unsupported horizontal ceiling.
    d.polygon([[-4.8,6],[4.8,6],[4.8,10],[0,14.8],[-4.8,10]],35,operation='new',name='grub_key_access')
    d.move(axis=[1,0,0],angle='90 deg')
    d.move(axis=[0,0,1],angle=f'{angle} deg')
    d.body=target;d.do('solid.combine',target=target,tools=[tool],operation='cut')


def adapter(d):
    d.component('motor_inner_adapter')
    d.cylinder(40,'motor_plate_depth',inner=15,operation='new',name='NEMA17_front_plate')
    d.cylinder('main_shoulder','motor_adapter_height',inner=15,name='stationary_carrier_extension')
    # Three 40 mm guides. Side-loading nuts stay accessible with motor installed.
    for a in [ANGLES[i] for i in LONG_INDICES]:
        x,y=centers('guide_pitch',[a])[0]
        d.holes(1.7,'motor_adapter_height',positions=[(x,y)],name='M3x40_guide_axis')
        seat='drive_tip - motor_guide_extension + 2.4 mm - motor_face'
        prisms=discover().module('native_hardware_pattern').prisms(dict(radius_name='m3',depth=2.7,zz='bottom',overhang=True))
        for layer in sorted(prisms,key=lambda q:-q['depth']):
            if layer['z']>0:continue
            sk=d.sketch('catalogue_nut_overhang',f'({seat}) - 2.7 mm' if layer['z']==0 else f'({seat}) - ({layer["z"] + layer["depth"] + .02}) * native_unit')
            points=layer['points']
            if layer['z']==0:
                # One continuous nut-and-entry outline avoids microscopic
                # sliver faces where separately cut rectangles meet a hex flat.
                radius=max(q[0] for q in points);half_width=max(q[1] for q in points)
                points=[(-radius,0),(-radius/2,-half_width),(10,-half_width),
                        (10,half_width),(-radius/2,half_width)]
            d.line([[f'({x}) + ({u}) * cos({a}) - ({w}) * sin({a})',
                     f'({y}) + ({u}) * sin({a}) + ({w}) * cos({a})']
                    for u,w in [(f'{u} mm',f'{w} mm') for u,w in points]])
            d.extrude(sk,2.7 if layer['z']==0 else layer['depth']+.04,'cut')
    for i in range(4):
        a=f'motor_clock + {45+90*i} deg';xy=centers('31 mm / sqrt(2)',[a])
        d.holes('m3_bore','motor_adapter_height',positions=xy,name='NEMA17_M3_mount')
        d.holes(3.1,'motor_adapter_height - motor_plate_depth + 0.01 mm',z='motor_plate_depth',positions=xy,name='M3x8_socket_access')
    for a in [ANGLES[i] for i in LONG_INDICES]:
        d.holes('m3_bore','motor_plate_depth',positions=centers('motor_cage_post_pitch',[a]),name='cage_M3x10_mount')
    for angle in (0,90,180,270):side_window(d,angle)


def cage(d):
    d.component('motor_cage')
    d.cylinder('circle_plate_radius','mount_flange_depth',inner='motor_clear_radius',operation='new',name='rear_OOBB_circle_flange')
    circle_grid(d,'motor_cage_post_pitch + motor_cage_post_radius')
    for a in [ANGLES[i] for i in LONG_INDICES]:
        xy=centers('motor_cage_post_pitch',[a])[0]
        d.cylinder('motor_cage_post_radius','motor_cage_height',xy=xy,name='motor_surround_post')
        cage_post_holes(d,a)


def cage_post_holes(d,a):
    x,y=centers('motor_cage_post_pitch',[a])[0]
    d.holes('m3_bore',10,z='motor_cage_height - 10 mm',positions=[(x,y)],name='short_cage_screw')
    d.oobb_cut('oobb_nut',position=[x,y,'motor_cage_height - 5.3 mm'],rotation=[0,0,a],
               radius_name='m3',depth=2.7,zz='bottom',overhang=True)
    sk=d.sketch('cage_radial_nut_entry','motor_cage_height - 5.3 mm')
    d.line([[f'({x}) + {u} mm * cos({a}) - {w} mm * sin({a})',
             f'({y}) + {u} mm * sin({a}) + {w} mm * cos({a})']
            for u,w in [(0,-3.0),(8,-3.0),(8,3.0),(0,3.0)]])
    d.extrude(sk,2.7,'cut')


def place(d,name):
    d.body=name;p='(1 - print_layout)';x,y=POSITIONS[name]
    z={'motor_inner_adapter':'motor_face - 2 * explode','motor_cage':'motor_cage_base - 4 * explode',
       'output_circle_plate':'middle_end + 9.65 * explode','output_plain_circle_plate':'middle_end + 9.65 * explode'}[name]
    parked={'output_circle_plate':'-2 * circle_plate_radius - 20 mm',
            'output_plain_circle_plate':'-4 * circle_plate_radius - 40 mm'}.get(name,'0 mm')
    d.move(translate=[f'{x} mm * layout_scale * print_layout + ({parked}) * {p}',
                      f'{y} mm * layout_scale * print_layout',f'({z}) * {p}'])


def screw(d,name,length,xy,z,level,up=False,turn=False):
    d.component(name)
    d.cylinder(1.5,length,operation='new',name='M3_thread_envelope')
    d.cylinder(2.75,3,z=-3,name='socket_cap')
    from gearbox_native.stacked_disc_shaft import polygon
    d.polygon(polygon('0 mm','0 mm',0,1.45),1.5,z=-3,operation='cut',name='hex_socket')
    if not up:d.move(axis=[1,0,0],angle='180 deg')
    d.move(translate=[*xy,0])
    if turn:d.move(axis=[0,0,1],angle='input_angle')
    d.move(translate=[0,0,f'({z}) + ({level}) * explode + 150 mm * print_layout'])


def nut(d,name,xy,z,level,angle=None):
    from gearbox_native.stacked_disc_shaft import polygon
    d.component(name)
    d.polygon(polygon('0 mm','0 mm',0,3.17543),2.4,operation='new',name='M3_nut')
    d.holes(1.55,2.4,name='thread')
    if angle:d.move(axis=[0,0,1],angle=angle)
    d.move(translate=[*xy,f'({z}) + ({level}) * explode + 150 mm * print_layout'])


def hardware(d):
    for i,a in enumerate(ANGLES):
        long=i in LONG_INDICES;xy=centers('guide_pitch',[a])[0]
        screw(d,f'hardware_guide_M3x{40 if long else 35}_{i+1}',
              'motor_guide_length' if long else 'carrier_drive_length',xy,'drive_tip + carrier_drive_length',10)
        nut(d,f'hardware_guide_nut_{i+1}',xy,'drive_tip - motor_guide_extension' if long else 'drive_tip',-2 if long else -1,angle=a)
    for i in range(4):
        xy=centers('31 mm / sqrt(2)',[f'motor_clock + {45+i*90} deg'])[0]
        screw(d,f'hardware_NEMA17_M3x8_{i+1}',8,xy,'motor_face + motor_plate_depth',-2)
        xy=centers('coupler_mount_radius',[f'{45+i*90} deg'])[0]
        screw(d,f'hardware_coupler_M3x14_{i+1}',14,xy,'shaft_face_z - 2.5 mm',-1.5,up=True,turn=True)
        d.component(f'hardware_coupler_washer_{i+1}')
        d.cylinder(3,.5,xy=xy,inner=1.65,operation='new',name='M3_half_mm_washer')
        d.move(axis=[0,0,1],angle='input_angle')
        d.move(translate=[0,0,'shaft_face_z - 2.5 mm - 1.5 * explode + 150 mm * print_layout'])
    for i in LONG_INDICES:
        xy=centers('motor_cage_post_pitch',[ANGLES[i]])[0]
        screw(d,f'hardware_cage_M3x10_{i}',10,xy,'motor_face + motor_plate_depth',-2)
        nut(d,f'hardware_cage_nut_{i}',xy,'motor_face - 5 mm',-4,angle=ANGLES[i])
    d.component('hardware_flange_coupler_5mm')
    d.cylinder(11,2,z=-2,inner=2.5,operation='new',name='coupler_flange')
    d.cylinder(5,12,z=-12,inner=2.5,name='coupler_barrel')
    d.holes(1.5,2,z=-2,positions=centers('coupler_mount_radius',[f'{45+i*90} deg' for i in range(4)]),name='coupler_flange_holes')
    d.move(axis=[0,0,1],angle='input_angle')
    d.move(translate=[0,0,'shaft_face_z - 1.5 * explode + 150 mm * print_layout'])
    d.component('hardware_NEMA17_motor')
    d.box('-motor_body_width / 2','motor_body_width / 2','-motor_body_width / 2','motor_body_width / 2',
          'motor_depth',z='-motor_depth',operation='new',name='motor_body_envelope')
    d.cylinder(11,2,name='NEMA17_boss')
    d.cylinder(2.5,'motor_shaft_length',name='five_mm_shaft')
    d.holes(1.5,6,z=-6,positions=[(x,y) for x in (-15.5,15.5) for y in (-15.5,15.5)],name='mounting_threads')
    d.move(axis=[0,0,1],angle='motor_clock')
    d.move(translate=[0,0,'motor_face - 3 * explode + 150 mm * print_layout'])


def group_new(client):
    tree=require_ok(client.execute('component.list',compact=True))['components']
    groups={}
    for c in tree:
        if c['id']==0 or c['parent']!=0 or c.get('children'):continue
        if c['name'].startswith('hardware_'):group='Motor hardware'
        elif c['name'].startswith('output_'):group='Circular output plate options'
        else:group='NEMA17 adapter and rear flange'
        groups.setdefault(group,[]).extend(o['id'] for o in c['occurrences'])
    for group,occurrences in groups.items():
        require_ok(client.execute('component.create',name=group,parent='Hardware' if group=='Motor hardware' else 0,activate=False))
        require_ok(client.execute('browser.reparent',component=group,occurrences=occurrences))


def build(folder):
    folder.mkdir(parents=True,exist_ok=False)
    digest=adapt_copy(folder/'adapted.solidcraft')
    with MCPClient(folder/'author',design=folder/'adapted.solidcraft',allow_path=PROJECT,timeout=600) as client:
        cls=discover().module('native_design').Design
        d=cls.__new__(cls);d.client=client;d.commands=[];d.index=4000;d.body=None
        parameters(d)
        require_ok(client.execute('parameters.change',changes={'coupler_mount_radius':'8.01 mm'}))
        require_ok(client.execute('parameters.change',changes={'coupler_mount_radius':'8 mm'}))
        for name,builder in [('motor_inner_adapter',adapter),('motor_cage',cage),
                             ('output_circle_plate',lambda d:circle_plate(d,'output_circle_plate')),
                             ('output_plain_circle_plate',lambda d:circle_plate(d,'output_plain_circle_plate',False))]:
            print('Building',name,flush=True);builder(d);place(d,name)
        hardware(d);group_new(client)
        health_check(client,folder/'health.json')
        require_ok(client.call('save',dict(path=str(folder/'complete.solidcraft'))))
    assert hashlib.sha256(BASE.read_bytes()).hexdigest()==digest
    (folder/'baseline.json').write_text(json.dumps(dict(source=str(BASE),sha256=digest),indent=2),encoding='utf8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);args=p.parse_args();build(args.folder.resolve())
