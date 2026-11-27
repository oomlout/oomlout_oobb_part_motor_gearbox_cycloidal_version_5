"""The two removable outer-race seats and their interchangeable OOBB flanges."""
import math

from oobb_solidcraft import api as oobb
from oobb_solidcraft.registry import discover
from gearbox_native.native_v8 import patterned_holes

FOOT = 'output_lower_row_plate'
CIRCLE = 'output_circle_plate'
CYLINDERS = ('output_nut_cylinder', 'output_cap_cylinder')
GRID_LIMIT = 60  # nine full-grid stations in each direction; native guard below
NUT_ENVELOPE = {'m6': 5.774, 'm3': 3.176}
CLEARANCE = .15


def parameters(d):
    d.parameter('housing_race_allowance','0 mm',favorite=True,comment='Total axial allowance between the 6810 outer-race stops. Zero is nominal contact at both ends.')
    for name, expression in (
        ('housing_lip_depth', '2.5 mm'),
        ('housing_grid_radius', '15 mm * ceil((bearing_ring_radius - 6.5 mm) / (15 mm))'),
        ('housing_plate_half', 'housing_grid_radius + 7 mm'),
        ('housing_cylinder_depth', 'plate_height + housing_lip_depth - mount_flange_depth'),
        ('housing_outer_stop', 'housing_cylinder_depth - main_bearing_width - housing_race_allowance'),
        ('housing_nut_seat', 'housing_lip_depth + 2.65 mm'),
        ('housing_cap_seat', 'housing_lip_depth + cap_recess'),
        ('housing_preview_x', '(1 + sqrt(2)) * housing_plate_half + 15 mm'),
    ):
        d.parameter(name, expression)
    d.parameter('layout_scale','max(1, housing_plate_half / (52 mm), bearing_ring_radius / (43.75 mm))',unit='')
    d.parameter('housing_grid_guard', 'sqrt((60 mm - housing_grid_radius) / native_unit)', unit='')
    circle_parameters(d)


def circle_parameters(d):
    """The same odd-size OOBB circle used by the motor option, without its joins."""
    d.parameter('circle_grid_radius','15 mm * ceil((bearing_ring_radius + 6 mm) / (15 mm))')
    d.parameter('circle_plate_radius','circle_grid_radius + 7 mm')
    d.parameter('circle_grid_guard','sqrt((90 mm - circle_grid_radius) / native_unit)',unit='')


def circle_plate(d):
    d.component(CIRCLE)
    d.cylinder('circle_plate_radius','mount_flange_depth',inner='main_bearing_od / 2 - 0.85 mm',
               operation='new',name='flat_circular_OOBB_plate')
    patterned_holes(d,1.7,'mount_flange_depth',pitch='pitch',count='ring_count',phase='0 deg',name='lobe_screw_through')
    # Native expressions keep the same nut clearance at the inner and outer
    # edges when the ring size changes. All holes are straight through.
    for size in ('m6','m3'):
        envelope=NUT_ENVELOPE[size]+CLEARANCE
        sk=d.sketch('circular_OOBB_'+size)
        for i in range(13):
            for j in range(1,13):
                if (size=='m6') != (not(i%2 or j%2)):continue
                x,y=7.5*i,7.5*j;r=math.hypot(x,y)
                blocked=f'max(bearing_ring_radius + {envelope} mm - {r} mm, {r+envelope} mm - circle_plate_radius)'
                park=f'300 mm * min(1, max(0, ceil(({blocked}) / native_unit)))'
                d.pattern(d.circle(size+'_bore',[f'{x} mm + {park}',y]),'4')
        d.extrude(sk,'mount_flange_depth','cut',all_profiles=True)


def output_mounts(ring_radius, foot=False):
    """Usable OOBB v5 both_holes centers, with the larger bore at shared stations."""
    half_steps = 2 * math.ceil((ring_radius - 6.5) / 15)
    first_row = -half_steps - (2 if foot else 0)
    last_row = 0 if foot else half_steps
    result = {'m6': [], 'm3': []}
    for i in range(-half_steps, half_steps+1):
        for j in range(first_row, last_row+1):
            size = 'm6' if not (i%2 or j%2) else 'm3'
            x,y = 7.5*i,7.5*j
            if math.hypot(x,y) >= ring_radius + NUT_ENVELOPE[size] + CLEARANCE:
                result[size].append((x,y))
    return result


def grid_holes(d, foot, depth='mount_flange_depth'):
    # One quadrant and a native circular pattern cover the full plate. Inactive
    # drills are parked clear of the blank, so changing pitch never leaves a
    # partial hole through the wall. The foot uses the lower half of the grid.
    for size in ('m6','m3'):
        sk = d.sketch('OOBB_'+size)
        seeds = []
        limit = int(GRID_LIMIT / 7.5)
        for i in range(-limit if foot else 0, limit+1):
            for j in (range(-limit,1) if foot else range(1,limit+1)):
                x,y = 7.5*i,7.5*j
                if (size=='m6') != (not (i%2 or j%2)):
                    continue
                distance = math.hypot(x,y)
                if distance < 32.5 + NUT_ENVELOPE[size]:
                    continue
                blocked = (f'max(bearing_ring_radius + {NUT_ENVELOPE[size]+CLEARANCE} mm - {distance:.10f} mm, '
                           f'{max(abs(x),abs(y))} mm - housing_grid_radius)')
                park = f'200 mm * min(1, max(0, ceil(({blocked}) / native_unit)))'
                seeds.extend(d.circle(size+'_bore',[f'{x} mm + {park}',y]))
        if not foot:
            d.pattern(seeds,'4')
        if foot:
            # The extra 15 mm band has one M6 row and the intervening M3 half-row.
            for j in (1,2):
                for i in range(-limit,limit+1):
                    if (size=='m6') != (not (i%2 or j%2)):
                        continue
                    x = 7.5*i
                    row = f'(housing_grid_radius + {j*7.5} mm)'
                    blocked = f'max({abs(x)} mm - housing_grid_radius, bearing_ring_radius + {NUT_ENVELOPE[size]+CLEARANCE} mm - sqrt(({x} mm)^2 + {row}^2))'
                    park = f'450 mm * min(1, max(0, ceil(({blocked}) / native_unit)))'
                    d.circle(size+'_bore',[f'{x} mm + {park}',f'-housing_grid_radius - {j*7.5} mm'])
        d.extrude(sk,depth,'cut',all_profiles=True)


def plate(d,name):
    d.component(name)
    foot = name == FOOT
    sk = d.sketch('lower_row_blank' if foot else 'square_odd_OOBB_blank')
    d.rounded_rectangle('-housing_plate_half','housing_plate_half',
                        '-housing_plate_half - 15 mm' if foot else '-housing_plate_half',
                        7 if foot else 'housing_plate_half',4)
    d.extrude(sk,'mount_flange_depth','new')
    if foot:
        d.cylinder('bearing_ring_radius','mount_flange_depth',name='round_top')
    d.holes('main_bearing_od / 2 - 0.85 mm','mount_flange_depth',name='6810_outer_race_lip')
    patterned_holes(d,1.7,'mount_flange_depth',pitch='pitch',count='ring_count',phase='0 deg',name='lobe_screw_through')
    grid_holes(d,foot)


def cylinder(d,name):
    d.component(name)
    d.cylinder('bearing_ring_radius','housing_cylinder_depth',
               inner='main_bearing_od / 2 - 0.85 mm',operation='new',name='6810_outer_retainer')
    d.holes('main_bearing_od / 2 + seat_fit','housing_cylinder_depth - housing_outer_stop + 0.01 mm',
            z='housing_outer_stop',name='6810_open_seat')
    cap = name == CYLINDERS[1]
    seat = 'housing_cap_seat' if cap else 'housing_nut_seat'
    if cap:
        patterned_holes(d,oobb.gv('screw_socket_cap_radius_m3','3dpr')+.1,seat,
                        pitch='pitch',count='ring_count',phase='0 deg',name='lobe_socket_caps')
    prisms = discover().module('native_hardware_pattern').prisms(dict(radius_name='m3',depth=2.7,zz='bottom',overhang=True))
    for prism in sorted(prisms,key=lambda p:-p['depth']):
        offset=prism['z']
        if offset>0 or (cap and offset==0):
            continue
        z=0 if offset==0 else f'{seat} + {-offset-.32:.3f} mm'
        depth=seat if offset==0 else .34
        sk=d.sketch('M3_nut' if offset==0 else 'support_free_socket_roof',z)
        points=prism['points']
        if offset==-.3:
            points=[(x+math.copysign(.03,x),y) for x,y in points]
        curves=d.line([[f'pitch + ({x}) * native_unit',y] for x,y in points])
        d.pattern(curves,'ring_count')
        d.extrude(sk,depth,'cut',all_profiles=True)
    patterned_holes(d,1.7,'housing_cylinder_depth',pitch='pitch',count='ring_count',phase='0 deg',name='lobe_screw_through')
