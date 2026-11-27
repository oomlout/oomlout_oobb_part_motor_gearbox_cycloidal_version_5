"""Three flat-printing shaft blanks. All eight instances use the same native recipes."""
import math
from oobb_solidcraft import api as oobb

# Name, blank, turn over about the SE/NW line, clock by half a turn, axial station, explosion level
LAYERS = [
    ('shaft_end_lower','E',False,False,'shaft_face_z',-.8),
    ('shaft_mount_lower','N',True,False,'shaft_end_station + shaft_mount_depth',2),
    ('shaft_cam_a_outer','C',False,False,'stack_height / 2 - 2 * shaft_cam_depth',3),
    ('shaft_cam_a_inner','C',True,False,'stack_height / 2',4.8),
    ('shaft_cam_b_inner','C',False,True,'stack_height / 2',5.3),
    ('shaft_cam_b_outer','C',True,True,'stack_height / 2 + 2 * shaft_cam_depth',7.2),
    ('shaft_mount_upper','N',False,False,'stack_height - shaft_end_station - shaft_mount_depth',8),
    ('shaft_end_upper','E',True,False,'stack_height - shaft_face_z',10.9),
]
NAMES = {row[0]:row for row in LAYERS}
MOUNTS=[(7.5,0),(0,7.5),(-7.5,0),(0,-7.5)]
def parameters(d):
    for key,value in [
        ('shaft_tie_pitch','6.52 mm'),('shaft_tie_length','35 mm'),
        ('shaft_head_depth','3.30 mm'),('shaft_nut_depth','3 mm'),
        ('shaft_open_bore','3.25 mm'),('shaft_tie_bore','1.70 mm'),
        ('shaft_face_z','(stack_height - shaft_tie_length - 3.4 mm) / 2'),
        ('shaft_end_station','race_end_gap + shaft_race_width'),
        ('shaft_end_depth','shaft_end_station - shaft_face_z'),
        ('shaft_cam_shoulder','disc_lip + disc_gap / 2'),
        ('shaft_cam_depth','shaft_cam_shoulder + shaft_race_width / 2'),
        ('shaft_mount_depth','disc_a_z + disc_lip - shaft_cam_shoulder - shaft_end_station'),
    ]:d.parameter(key,value,unit='mm')
def ties():
    return [(s+'shaft_tie_pitch / sqrt(2)',)*2 for s in ('','-')]
def polygon(x,y,angle,r):
    return [[f'({x}) + ({r*math.cos(math.radians(angle+i*60))}) * native_unit',
             f'({y}) + ({r*math.sin(math.radians(angle+i*60))}) * native_unit'] for i in range(6)]
def part(d,name):
    _,kind,*_=NAMES[name]
    h={'E':'shaft_end_depth','N':'shaft_mount_depth','C':'shaft_cam_depth'}[kind]
    xy=('eccentricity / sqrt(2)','-eccentricity / sqrt(2)') if kind=='C' else (0,0)
    d.component(name)
    if kind=='N':
        d.cylinder(11.75,h+' - 0.45 mm',operation='new',name='nut_carrier_blank')
        d.cylinder(11,h,name='inboard_6704_inner_race_land')
    else:
        shoulder='shaft_cam_shoulder' if kind=='C' else 'race_end_gap - shaft_face_z'
        d.cylinder(10.7 if kind=='C' else 11,shoulder,xy=xy,operation='new',name='inner_race_shoulder')
        d.cylinder('shaft_journal',h,xy=xy,name='6704_journal')
    d.holes('shaft_open_bore',h,name='open_M6_passage')
    d.holes('shaft_tie_bore',h,positions=ties(),name='opposed_tie_axes')
    if kind!='C':d.holes(1.80,h,positions=MOUNTS,name='four_OOBB_mounts')
    nut=oobb.gv('nut_radius_m3','3dpr')
    if kind=='E':
        head=ties()[1]
        d.holes(3,'shaft_head_depth',positions=[head],name='socket_head_seat')
        # Two short bridges close the bed-facing counterbore onto the tie bore.
        for index,length in enumerate((4.9,3.45)):
            points=[]
            for u,w in [(-1.725,-length/2),(1.725,-length/2),(1.725,length/2),(-1.725,length/2)]:
                points.append([f'({head[0]}) + ({(u-w)/math.sqrt(2)}) * native_unit',
                               f'({head[1]}) + ({(u+w)/math.sqrt(2)}) * native_unit'])
            d.polygon(points,.30,z=f'shaft_head_depth + {index*.3} mm',operation='cut',name='socket_bridge')
        d.polygon(polygon(*ties()[0],75,nut),'shaft_nut_depth',operation='cut',name='tie_nut_entry')
        d.oobb_cut('oobb_nut',position=[*ties()[0],'shaft_nut_depth - 3 mm'],rotation=[0,0,75],radius_name='m3',
                   depth=3,zz='bottom',overhang=True)
    if kind=='N':
        for i,(x,y) in enumerate(MOUNTS):
            d.polygon(polygon(f'{x} mm',f'{y} mm',30+90*i,nut),'shaft_nut_depth',z=h+' - shaft_nut_depth',operation='cut',name='flat_mount_nut')
def place(d,name,position):
    _,kind,flip,reverse,z,level=NAMES[name];p='(1 - print_layout)'
    d.body=name
    if flip:
        d.move(axis=[1,0,0],angle='180 deg * '+p)
        d.move(axis=[0,0,1],angle='-90 deg * '+p)
    ang=225 if reverse else 45
    d.move(axis=[0,0,1],angle=f'({ang} deg + input_angle) * {p}')
    d.move(translate=[*(f'{a} mm * layout_scale * print_layout' for a in position),f'(({z}) + ({level}) * explode) * {p}'])
def hardware(d,plane):
    # In assembly coordinates at input_angle=0 the ties lie on +/-Y.
    for bottom in (True,False):
        end='lower' if bottom else 'upper';y='-shaft_tie_pitch' if bottom else 'shaft_tie_pitch'
        z='shaft_face_z + shaft_head_depth' if bottom else 'stack_height - shaft_face_z - shaft_head_depth'
        def turn_move(y,z,level):
            d.move(translate=[0,y,0])
            d.move(axis=[0,0,1],angle='input_angle')
            d.move(translate=[0,0,plane(z,level)])
        d.component('hardware_shaft_M3x35_'+end)
        d.cylinder(1.5,'shaft_tie_length',operation='new',name='M3_shank')
        d.cylinder(2.75,3,z=-3,name='socket_head')
        d.polygon(polygon('0 mm','0 mm',0,1.45),1.5,z=-3,operation='cut',name='hex_socket')
        if not bottom:d.move(axis=[1,0,0],angle='180 deg')
        turn_move(y,z,-2 if bottom else 12)
        d.component('hardware_shaft_tie_nut_'+end)
        z='shaft_face_z + shaft_nut_depth - 2.5 mm' if bottom else 'stack_height - shaft_face_z - shaft_nut_depth'
        d.polygon(polygon('0 mm','0 mm',0,3.17543),2.5,operation='new',name='M3_nut')
        d.holes(1.55,2.5,name='thread')
        turn_move('shaft_tie_pitch' if bottom else '-shaft_tie_pitch',z,-.9 if bottom else 11.3)
        for i,(x,y) in enumerate(MOUNTS):
            d.component(f'hardware_shaft_mount_nut_{end}_{i+1}')
            d.polygon(polygon(f'{x} mm',f'{y} mm',30+i*90,3.17543),2.5,operation='new',name='M3_mount_nut')
            d.holes(1.55,2.5,positions=[(x,y)],name='thread')
            d.move(axis=[0,0,1],angle='45 deg + input_angle')
            z='shaft_end_station + shaft_nut_depth - 2.5 mm' if bottom else 'stack_height - shaft_end_station - shaft_nut_depth'
            d.move(translate=[0,0,plane(z,1.8 if bottom else 8.2)])

def stations(v):
    """Axial sketch planes in assembled mm for dimensioned illustrations."""
    h=v['stack_height'];z=v['shaft_end_station'];n=v['shaft_mount_depth'];c=v['shaft_cam_depth']
    return dict(zip(NAMES,(v['shaft_face_z'],z+n,h/2-2*c,h/2,h/2,h/2+2*c,h-z-n,h-v['shaft_face_z']),strict=True))
