"""V9 tighter running fits, 6702 front support and an external D-shaft sleeve."""
import argparse
import json

from oobb_solidcraft.registry import discover
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft import api as oobb
from gearbox_native import native_v9 as base
from gearbox_native import native_v8 as common
from gearbox_native.project import PROJECT
from gearbox_native.acceptance import health_check
from gearbox_native import split_stack as stack

CONTROLS = [
    ('guide_running_clearance', '0.10 mm', 'Extra radial guide-track clearance beyond the eccentric orbit.'),
    ('post_running_clearance', '0.10 mm', 'Extra radial standoff-track clearance beyond the eccentric orbit.'),
    ('drive_socket_clearance', '0.05 mm', 'Radial and flat clearance in the clamped external-drive D socket.'),
    ('drive_extension_length', '12 mm', 'Exposed D-shaft length beyond the coupling collar.'),
    ('drive_shaft_flat', '6.5 mm', 'Centre-to-flat distance on the exposed D shaft.'),
]
OVERRIDES = {
    'profile_clearance': '0.15 mm',
    'key_top': 'front_z - 1.2 mm',
    'wiggle_key_clearance': '0.05 mm',
    'wiggle_journal_clearance': '0.05 mm',
    'guide_clearance_radius': 'guide_outer_radius + eccentricity + guide_running_clearance',
    'post_clearance_radius': 'standoff_radius + eccentricity + post_running_clearance',
    # Clearance trials use the same pin pattern and contact pitch as the proven
    # gearbox. Increasing a clearance still expands the required envelope.
    'guide_minimum_pitch': 'max(max(bottom_od, top_od) / 2 + seat_clearance + minimum_web + guide_outer_radius + eccentricity + max(0.2 mm, guide_running_clearance), (guide_outer_radius + eccentricity + max(0.2 mm, guide_running_clearance) + minimum_web / 2) / sin(180 deg / guide_count))',
    'post_minimum_pitch': 'max(max(bottom_od, top_od) / 2 + seat_clearance + minimum_web + standoff_radius + eccentricity + max(0.15 mm, post_running_clearance), guide_pitch * cos(guide_phase) + sqrt(max((0 mm)^2, (guide_outer_radius + eccentricity + max(0.2 mm, guide_running_clearance) + standoff_radius + eccentricity + max(0.15 mm, post_running_clearance) + minimum_web)^2 - (guide_pitch * sin(guide_phase))^2)))',
    'undercut_pitch_limit': 'sqrt((ring_count * eccentricity)^2 + (contact_radius + max(profile_clearance, 0.2 mm))^2 * (ring_count + 1)^3 / (27 * (ring_count - 1)))',
}


def parameters(d, bearing=False):
    if bearing:
        d.parameter('bearing_tie_diameter','3 mm')
        d.parameter('bearing_tie_length','35 mm')
        d.parameter('bearing_holder_depth','6.5 mm',favorite=True,comment='Flat-bottomed lower bearing cup beneath the shared NEMA17 plate.')
        d.parameter('bearing_holder_seat_floor','-4.2 mm')
        d.parameter('bearing_holder_bearing_z','bearing_holder_seat_floor + 0.1 mm')
        d.parameter('bearing_holder_nut_top','-3.3 mm')
    for name, expr, comment in CONTROLS:
        d.parameter(name, expr, favorite=True, comment=comment)
    class Proxy:
        def parameter(self, name, expression, **kwargs):
            expression = OVERRIDES.get(name, expression)
            if bearing and name == 'wiggle_join_head_seat':
                expression = '-6.7 mm'
            if bearing and name == 'wiggle_join_nut_bottom':
                expression = 'hub_top - 7 mm'
            if bearing and name == 'join_screw_fit_guard':
                expression = 'sqrt((wiggle_join_head_seat + bearing_tie_length - wiggle_join_nut_bottom - 2.4 mm) / (1 mm))'
            if name == 'print_layout':
                kwargs['comment'] = f'1 lays out all {14 if bearing else 11} printable parts; 0 assembled/exploded.'
            d.parameter(name, expression, **kwargs)
    base.parameters(Proxy())
    for name, expression in [
        ('front_bearing_bore','15 mm'), ('front_bearing_od','21 mm'), ('front_bearing_width','4 mm'),
        ('front_shaft_radius','front_bearing_bore / 2 - wiggle_journal_clearance'),
        ('drive_key_radius','4.9 mm'), ('drive_key_flat','4.3 mm'),
        ('drive_key_top','housing_top + 8 mm'), ('drive_sleeve_bottom','front_z + 0.8 mm'),
        ('drive_collar_bottom','housing_top + 0.3 mm'), ('drive_collar_radius','11 mm'),
        ('drive_flare_top','drive_collar_bottom + drive_collar_radius - front_shaft_radius'),
        ('drive_collar_top','housing_top + 10 mm'), ('drive_clamp_z','housing_top + 5.5 mm'),
        ('drive_extension_top','drive_collar_top + drive_extension_length'),
        ('drive_clamp_tip','drive_key_flat - 0.4 mm'),
        ('lower_support_bottom','-0.2 mm'), ('lower_support_shoulder','4.3 mm'),
        ('drive_socket_wall_guard','sqrt((front_shaft_radius - drive_key_radius - drive_socket_clearance - 1.5 mm) / (1 mm))'),
    ]:
        if bearing and name=='lower_support_bottom':expression='bearing_holder_seat_floor - 0.2 mm'
        if bearing and name=='lower_support_shoulder':expression='0.1 mm'
        d.parameter(name, expression, unit='' if name.endswith('guard') else 'mm')
    if bearing:
        d.parameter('bearing_holder_floor_guard','sqrt((bearing_holder_depth + bearing_holder_seat_floor - 1.5 mm) / (1 mm))',unit='')


def d_profile(d, radius, flat, depth, z, operation):
    """One reusable flat-sided profile, also used for the sleeve's socket."""
    target = d.body
    d.index += 1
    tool = target + f'_D_{d.index}'
    d.body = tool
    d.cylinder(radius, depth, z=z, operation='new', name='D_profile')
    d.box(flat, 25, -20, 20, f'({depth}) + 0.02 mm',
          z=f'({z}) - 0.01 mm', operation='cut', name='D_flat')
    d.body = target
    d.do('solid.combine', target=target, tools=[tool], operation=operation)


def upper_hub(d,half=None):
    d.component(half or 'eccentric_hub_upper')
    d.revolve([[0,'seam_z'],['top_journal','seam_z'],['top_journal','top_journal_end'],
               ['top_shoulder','top_journal_end + 0.8 mm'],[0,'top_journal_end + 0.8 mm']],
              operation='new',name='upper_eccentric_journal')
    d.move(translate=['-eccentricity',0,0])
    d.cylinder('top_journal - eccentricity - wiggle_spine_relief','front_z - seam_z',z='seam_z',name='upper_spine')
    d.cone('top_journal - eccentricity','drive_key_radius','front_z - top_journal_end',z='top_journal_end')
    d_profile(d,'drive_key_radius','drive_key_flat','drive_key_top - front_z','front_z','join')
    if half:
        stack.clock_key(d,'seam_z - 0.01 mm','key_depth + wiggle_axial_clearance + 0.03 mm',True)
        stack.nut(d);stack.socket_cap(d);stack.channel(d)
        d.box('drive_clamp_tip',12,-8,8,3.25,z='drive_clamp_z - 1.625 mm',operation='cut',name='clamp_index_flat')
        stack.split(d,half)
        return
    base.key(d,'seam_z - 0.01 mm','key_depth + wiggle_axial_clearance + 0.03 mm',socket=True)
    d.holes(oobb.gv('hole_radius_m2d5','3dpr'),'drive_key_top - seam_z + 0.1 mm',z='seam_z',name='upward_M2_5_join')
    # Parameterized placement retains the catalogue pocket and its printable
    # bridges; the same hexagonal opening continues up to the end of the stem.
    d.oobb_cut('oobb_nut',position=[0,0,'wiggle_join_nut_bottom'],radius_name='m2d5',
               depth=30,zz='bottom',rot=[0,0,30],overhang=True)
    radial_hole(d,1.6,'drive_clamp_tip',1,'drive_clamp_z','clamp_retaining_dimple')


def radial_hole(d, radius, start, length, z, name):
    target=d.body
    d.index+=1
    tool=target+f'_{name}_{d.index}'
    d.body=tool
    d.cylinder(radius,length,operation='new',name=name)
    d.move(axis=[0,1,0],angle='90 deg')
    d.move(translate=[start,0,z])
    d.body=target
    d.do('solid.combine',target=target,tools=[tool],operation='cut')


def drive_sleeve(d,open_socket=False):
    d.component('drive_sleeve')
    d.cylinder('front_shaft_radius','drive_collar_bottom - drive_sleeve_bottom',
               z='drive_sleeve_bottom',operation='new',name='6702_journal')
    d.cone('front_shaft_radius','drive_collar_radius','drive_flare_top - drive_collar_bottom',z='drive_collar_bottom',name='printable_flare')
    d.cylinder('drive_collar_radius','drive_collar_top - drive_flare_top',z='drive_flare_top',name='clamp_collar')
    d_profile(d,'front_shaft_radius','drive_shaft_flat','drive_extension_length','drive_collar_top','join')
    d_profile(d,'drive_key_radius + drive_socket_clearance','drive_key_flat + drive_socket_clearance',
              'drive_extension_top - drive_sleeve_bottom + 0.02 mm' if open_socket else 'drive_key_top + wiggle_axial_clearance - drive_sleeve_bottom + 0.01 mm','drive_sleeve_bottom - 0.01 mm','cut')
    # Load the nut sideways through the collar, clear of the exposed D shaft.
    if open_socket:
        stack.sleeve_throat(d)
        stack.sleeve_roofs(d)
    d.oobb_cut('oobb_nut',position=[5.6,0,'drive_clamp_z'],radius_name='m3',depth=2.8,
               zz='bottom',rot=[90,0,90],clearance='left',overhang=True)
    if not open_socket:d.box(3.8,16,-1.9,1.9,3.8,z='drive_clamp_z - 1.9 mm',operation='cut',name='M3_clamp_throat')
    d.box('drive_clamp_tip + 5.8 mm',20,-3.2,3.2,'drive_collar_top - drive_clamp_z + 3.3 mm' if open_socket else 6.4,z='drive_clamp_z - 3.2 mm',operation='cut',name='M3_socket_head_access')


def front_carrier(d):
    class LargerBearing:
        def __getattr__(self,name):
            return getattr(d,name)
        def holes(self,radius,depth,**kwargs):
            if kwargs.get('name')=='6701_retaining_lip':
                radius='front_bearing_bore / 2 + 1 mm'
                kwargs['name']='6702_retaining_lip'
            elif kwargs.get('name')=='6701_seat':
                radius='front_bearing_od / 2 + seat_clearance'
                depth='front_bearing_width + 2 * endplay'
                kwargs.update(z='front_depth - front_bearing_width - 2 * endplay',name='6702_seat')
            return d.holes(radius,depth,**kwargs)
    common.front_carrier(LargerBearing())


def bearing_holder(d):
    """Cup prints on its broad underside: the bearing opening grows upward."""
    d.component('bearing_holder')
    sketch=d.sketch('NEMA17_bearing_cup')
    d.rounded_rectangle(-21,21,-21,21,3)
    d.extrude(sketch,'bearing_holder_depth','new')
    d.move(translate=[0,0,'-bearing_holder_depth'])
    d.holes('front_bearing_bore / 2 + 1.1 mm','bearing_holder_depth + 0.02 mm',
            z='-bearing_holder_depth - 0.01 mm',name='open_retainer_and_tool_access')
    d.holes('front_bearing_od / 2 + seat_clearance','-bearing_holder_seat_floor + 0.01 mm',
            z='bearing_holder_seat_floor',name='upward_open_6702_seat')
    for x in (-15.5,15.5):
        for y in (-15.5,15.5):
            d.oobb_cut('oobb_hole',position=[x,y,'-bearing_holder_depth - 0.01 mm'],
                       radius_name='m3',depth=40,zz='bottom')
            common.base.nut(d,(x,y),'bearing_holder_nut_top')


def bearing_lower_hub(d,half=None):
    d.component(half or 'eccentric_hub_lower')
    d.cylinder('front_shaft_radius','lower_support_shoulder - lower_support_bottom',
               z='lower_support_bottom',operation='new',name='bottom_6702_journal')
    d.cylinder('front_bearing_bore / 2 + 0.8 mm','drive_start + drive_depth - lower_support_shoulder',
               z='lower_support_shoulder',name='bottom_bearing_shoulder')
    d.cylinder('bottom_journal - eccentricity - wiggle_spine_relief','seam_z - drive_start - drive_depth',z='drive_start + drive_depth',name='lower_spine')
    d.cylinder('bottom_shoulder','bottom_journal_z - drive_start - drive_depth',z='drive_start + drive_depth',xy=('eccentricity',0),name='disc_bearing_shoulder')
    d.cylinder('bottom_journal','bottom_seat_depth',z='bottom_journal_z',xy=('eccentricity',0),name='bottom_eccentric_journal')
    if half:
        stack.clock_key(d,'seam_z','key_depth + 0.02 mm')
        stack.socket_cap(d);stack.channel(d);stack.split(d,half)
        return
    base.key(d,'seam_z','key_depth + 0.02 mm')
    d.holes(oobb.gv('hole_radius_m2d5','3dpr'),'key_top - lower_support_bottom + 0.1 mm',z='lower_support_bottom',name='M2_5_axial_join')


def bearing_retainer(d,split=False):
    d.component('bearing_retainer')
    if split:
        d.cylinder('front_bearing_bore / 2 + 0.8 mm','lower_support_bottom - wiggle_join_head_seat',z='wiggle_join_head_seat',operation='new',name='inner_race_washer')
        d.cylinder(4.5,3.15,z='wiggle_join_head_seat - 3.15 mm',name='socket_cap_collar')
        stack.socket_cap(d)
        return
    d.cylinder('front_bearing_bore / 2 + 0.8 mm','lower_support_bottom - wiggle_join_head_seat',
               z='wiggle_join_head_seat',inner=oobb.gv('hole_radius_m2d5','3dpr'),operation='new',name='lower_retaining_washer')


def layout(bearing=False,split=False):
    result=dict(base.PRINT_POSITIONS,drive_sleeve=(202,217))
    if bearing:
        del result['motor_spacer']
        result['bearing_holder']=(153,216)
        result['bearing_retainer']=(235,217)
    if split:
        del result['eccentric_hub_lower'],result['eccentric_hub_upper']
        result.update(stack.PRINT)
    return result


def place(d,name,bearing=False,split=False):
    if name in stack.HALVES:
        d.body=name; side=1 if name.endswith('_a') else -1
        x,y=stack.PRINT[name];level=1 if '_lower_' in name else 4
        d.move(axis=[1,0,0],angle=f'{side*90} deg * print_layout')
        d.move(axis=[0,0,1],angle='input_angle * (1 - print_layout)')
        d.move(translate=[f'{x} mm * layout_scale * print_layout',f'{y} mm * layout_scale * print_layout + {side} * explode * (1-print_layout)',f'{level} * explode * (1-print_layout)'])
        return
    if name not in ('bearing_holder','bearing_retainer','drive_sleeve') and not (bearing and name=='eccentric_hub_lower'):
        return base.place(d,name)
    d.body=name
    x,y=layout(bearing)[name]
    if name=='bearing_holder':
        pz='bearing_holder_depth';az='-explode'
    elif name=='bearing_retainer':
        if split:d.move(axis=[1,0,0],angle='180 deg * print_layout')
        pz='lower_support_bottom' if split else '-wiggle_join_head_seat';az='-2 * explode'
    elif name=='drive_sleeve':
        pz='-drive_sleeve_bottom';az='8 * explode'
        d.move(axis=[0,0,1],angle='input_angle * (1 - print_layout)')
    else:
        pz='-lower_support_bottom';az='explode'
        d.move(axis=[0,0,1],angle='input_angle * (1 - print_layout)')
    d.move(translate=[f'print_layout * layout_scale * {x} mm',f'print_layout * layout_scale * {y} mm',
                      f'print_layout * ({pz}) + (1 - print_layout) * ({az})'])


def builders(bearing=False,split=False):
    result=dict(base.BUILDERS,pin_front=front_carrier,eccentric_hub_upper=upper_hub,drive_sleeve=drive_sleeve)
    if bearing:
        del result['motor_spacer']
        result.update(bearing_holder=bearing_holder,eccentric_hub_lower=bearing_lower_hub,bearing_retainer=bearing_retainer)
    if split:
        del result['eccentric_hub_lower'],result['eccentric_hub_upper']
        for n in stack.HALVES:
            result[n]=lambda d,n=n: (bearing_lower_hub if '_lower_' in n else upper_hub)(d,n)
        result.update(bearing_retainer=lambda d:bearing_retainer(d,True),drive_sleeve=lambda d:drive_sleeve(d,True))
    return result


def run(name,bearing=False,piece=None,stack_only=False):
    out=PROJECT/'build/native_v9'/name
    out.mkdir(parents=True,exist_ok=False)
    geometry=base.profile_geometry()
    (out/'profile.json').write_text(json.dumps(geometry),encoding='utf8')
    with MCPClient(out/'author',allow_path=PROJECT,timeout=600) as client:
        d=discover().module('native_design').Design(client)
        parameters(d,bearing)
        if piece:
            builders(bearing,bearing)[piece](d)
        elif stack_only:
            for n in stack.STACK:builders(True,True)[n](d);place(d,n,True,True)
            require_ok(client.execute('parameters.change',changes={'print_layout':'1'}))
        else:
            for side in (0,1):
                print('Rotor',side,flush=True); common.rotor(d,side,geometry)
            for part,fn in builders(bearing,bearing).items():
                print('Building',part,flush=True);fn(d)
            for part in layout(bearing,bearing):place(d,part,bearing,bearing)
        health_check(client,out/'health.json')
        expected=1 if piece else len(stack.STACK) if stack_only else len(layout(bearing,bearing))
        assert require_ok(client.call('measure'))['body_count']==expected, 'Unexpected disconnected native bodies'
        require_ok(client.call('save',dict(path=str(out/'gearbox.solidcraft'))))
        for ext in ('step','stl'):
            require_ok(client.call('export',dict(path=str(out/('gearbox.'+ext)))))
        (out/'commands.json').write_text(json.dumps(d.commands),encoding='utf8')
    print('Saved',out,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--name',required=True)
    parser.add_argument('--bearing',action='store_true')
    parser.add_argument('--piece')
    parser.add_argument('--stack-only',action='store_true')
    args=parser.parse_args()
    run(args.name,args.bearing,args.piece,args.stack_only)
