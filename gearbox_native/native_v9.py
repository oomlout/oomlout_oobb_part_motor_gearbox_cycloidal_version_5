"""Native 5x5, 6808 gearbox. Named wiggle-shaft fits remain editable in CAD."""
import argparse
import json
from pathlib import Path
from oobb_solidcraft.registry import discover
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft import api as oobb
from gearbox_native import native_v8 as previous
from gearbox_native.project import PROJECT
from gearbox_native.acceptance import health_check

DEFAULTS = {
    'reduction': '35', 'contact_radius': '1.5 mm', 'eccentricity': '0.7 mm',
    'casing_bearing': '6808', 'top_bearing': '6702', 'bottom_bearing': '6702',
    'standoff_radius': '2.7 mm', 'guide_count': '6', 'guide_radius': '1.5 mm',
    'guide_outer_radius': '1.5 mm', 'guide_screw_length': '25 mm',
    'automatic_internal_positions': '1', 'automatic_pitch': '1',
}
FITS = [
    ('shaft_bore_clearance', '0.05 mm', 'Radial clearance around the 5 mm motor shaft.'),
    ('wiggle_journal_clearance', '0.075 mm', 'Radial clearance of the two eccentric journals.'),
    ('wiggle_key_clearance', '0.10 mm', 'Radial and flat clearance of the D-shaped hub connection.'),
    ('wiggle_axial_clearance', '0.10 mm', 'Extra depth at the end of the D-key socket.'),
]
SHAFT = [
    ('motor_shaft_radius', '2.5 mm'), ('motor_shaft_end', '24.2 mm'),
    ('wiggle_key_radius', '4.9 mm'), ('wiggle_key_flat', '4.3 mm'),
    ('wiggle_join_nut_bottom', '24.8 mm'), ('wiggle_join_head_seat', '28.8 mm'),
    ('wiggle_grub_nut_radius', '5 mm'), ('wiggle_grub_z', 'drive_start + 4 mm'),
    ('wiggle_spine_relief', '0.35 mm'),
]


def parameters(d):
    for name, expression, comment in FITS:
        d.parameter(name, expression, favorite=True, comment=comment)
    # Shaft dimensions that do not depend on the axial stack can be named first.
    for name, expression in SHAFT:
        if name != 'wiggle_grub_z': d.parameter(name, expression)
    overrides = dict(DEFAULTS, **{
        'reduction_range_guard': 'sqrt(min(reduction - 10, 35 - reduction))',
        'bottom_journal': 'bottom_bore / 2 - wiggle_journal_clearance',
        'top_journal': 'top_bore / 2 - wiggle_journal_clearance',
        'tab_plate_size': '5', 'tab_radius': '30 mm', 'tab_plate_width': '74 mm',
        'tab_required_radius': '30 mm',
        'tab_outer_bolt_gap': 'sqrt(2) * 30 mm - casing_radius - tab_m6_envelope_radius',
        'tab_root': '0 mm',
        'layout_scale': '1',
    })
    class Proxy:
        def parameter(self, name, expression, **kwargs):
            expression = overrides.get(name, expression)
            if name == 'casing_bearing':
                kwargs['comment'] = 'V9 design bearing: 6808, 40 mm bore, 52 mm OD, 7 mm wide.'
            d.parameter(name, expression, **kwargs)
    previous.parameters(Proxy())
    d.parameter('wiggle_grub_z', 'drive_start + 4 mm')
    d.parameter('output_footprint_guard', 'sqrt((37 mm - casing_radius) / (1 mm))', unit='')
    d.parameter('output_hole_web_guard', 'sqrt((sqrt((30 mm)^2 + (7.5 mm)^2) - 1.8 mm - casing_bore - 1 mm) / (1 mm))', unit='')
    d.parameter('wiggle_key_wall_guard', 'sqrt((min(bottom_journal, top_journal) - eccentricity - wiggle_key_radius - wiggle_key_clearance - 1.5 mm) / (1 mm))', unit='')


def key(d, z, depth, socket=False):
    """Same named D profile for both halves, with explicit socket fit allowance."""
    clearance = 'wiggle_key_clearance' if socket else '0 mm'
    target = d.body
    d.index += 1
    tool = target + f'_key_{d.index}'
    d.body = tool
    d.cylinder(f'wiggle_key_radius + {clearance}', depth, z=z, operation='new', name='D_key_profile')
    d.box(f'wiggle_key_flat + {clearance}', 25, -15, 15, f'({depth}) + 0.05 mm',
          z=f'({z}) - 0.01 mm', operation='cut', name='D_key_flat')
    d.body = target
    d.do('solid.combine', target=target, tools=[tool], operation='cut' if socket else 'join')


def lower_hub(d):
    d.component('eccentric_hub_lower')
    d.cylinder('drive_radius', 'drive_depth', z='drive_start', operation='new', name='motor_drive_base')
    d.cylinder('bottom_journal - eccentricity - wiggle_spine_relief', 'seam_z - drive_start - drive_depth',
               z='drive_start + drive_depth', name='lower_spine')
    d.cylinder('bottom_shoulder', 'bottom_journal_z - drive_start - drive_depth',
               z='drive_start + drive_depth', xy=('eccentricity', 0), name='bottom_bearing_shoulder')
    d.cylinder('bottom_journal', 'bottom_seat_depth', z='bottom_journal_z',
               xy=('eccentricity', 0), name='bottom_bearing_journal')
    key(d, 'seam_z', 'key_depth + 0.02 mm')
    d.holes(oobb.gv('hole_radius_m3', '3dpr'), 'key_top + 0.1 mm - drive_start', z='drive_start', name='hub_joining_screw')
    d.holes('motor_shaft_radius + shaft_bore_clearance', 'motor_shaft_end - drive_start', z='drive_start', name='motor_shaft_bore')
    d.oobb_cut('oobb_nut', position=[0, 0, 'wiggle_join_nut_bottom'], radius_name='m3',
               depth=2.9, zz='bottom', rot=[0, 0, 30], overhang=True)
    d.oobb_cut('oobb_nut', position=['wiggle_grub_nut_radius', 0, 'wiggle_grub_z'], radius_name='m3',
               depth=2.8, zz='bottom', rot=[0, 90, 0], clearance='left', clearance_tightness=.15, overhang=True)
    d.box(0, 12, -1.8, 1.8, 3.6, z='wiggle_grub_z - 1.8 mm', operation='cut', name='grub_screw_access')


def upper_hub(d):
    d.component('eccentric_hub_upper')
    d.revolve([[0, 'seam_z'], ['top_journal', 'seam_z'], ['top_journal', 'top_journal_end'],
               ['top_shoulder', 'top_journal_end + 0.8 mm'], [0, 'top_journal_end + 0.8 mm']],
              operation='new', name='top_bearing_journal_and_shoulder')
    d.move(translate=['-eccentricity', 0, 0])
    d.cylinder('top_journal - eccentricity - wiggle_spine_relief', 'front_z - seam_z', z='seam_z', name='upper_spine')
    d.cone('top_journal - eccentricity', 5.9, 'front_z - top_journal_end', z='top_journal_end', name='front_shaft_taper')
    d.cylinder(5.9, 'hub_top - front_z', z='front_z', name='6701_journal')
    key(d, 'seam_z - 0.01 mm', 'key_depth + wiggle_axial_clearance + 0.03 mm', socket=True)
    d.holes(oobb.gv('hole_radius_m3', '3dpr'), 'hub_top - seam_z + 0.1 mm', z='seam_z', name='hub_joining_screw')
    d.holes(oobb.gv('screw_socket_cap_radius_m3', '3dpr'), 'hub_top - wiggle_join_head_seat + 0.1 mm',
            z='wiggle_join_head_seat', name='hub_socket_cap_access')


def mounting_holes():
    """Full five-wide perimeter, omitting the middle M6 hole on every side."""
    m6 = set()
    m3 = set()
    for side in (-1, 1):
        for offset in (-30, -15, 15, 30):
            m6.add((side * 30, offset)); m6.add((offset, side * 30))
        for offset in (-22.5, -7.5, 7.5, 22.5):
            m3.add((side * 30, offset)); m3.add((offset, side * 30))
    return sorted(m6), sorted(m3)


CLAMPS = [(22.5, 22.5), (-22.5, 22.5), (-22.5, -22.5), (22.5, -22.5)]


def output_piece(d, side):
    z, end, radius = previous.BOUNDS[side]
    depth = f'({end}) - ({z})'
    d.component('output_casing_' + side)
    sketch = d.sketch('full_width_OOBB_5x5', z)
    d.rounded_rectangle(-37, 37, -37, 37, 5)
    d.extrude(sketch, depth, 'new')
    bore = 'casing_bore' if side == 'lobes' else 'bearing_lip_radius'
    d.holes(bore, f'({depth}) + 0.02 mm', z=f'({z}) - 0.01 mm', name='working_cavity')
    if side == 'lobes':
        sketch = d.sketch('ring_contacts', z)
        curves = d.circle('contact_radius', ('pitch', 0)); d.pattern(curves, 'ring_count')
        d.extrude(sketch, depth, all_profiles=True)
        sketch = d.sketch('contact_backs', z)
        curves = d.line([['pitch', '-contact_radius'], ['lobe_band_radius - 0.1 mm', '-contact_radius'],
                         ['lobe_band_radius - 0.1 mm', 'contact_radius'], ['pitch', 'contact_radius']])
        d.pattern(curves, 'ring_count'); d.extrude(sketch, depth, all_profiles=True)
    elif side == 'lower':
        d.holes('casing_od / 2 + seat_clearance', 'rear_seat_top - casing_bottom + 0.01 mm',
                z='casing_bottom - 0.01 mm', name='rear_bearing_seat')
    else:
        d.holes('casing_od / 2 + seat_clearance', 'housing_top - front_seat_bottom + 0.02 mm',
                z='front_seat_bottom', name='front_bearing_seat')
    m6, m3 = mounting_holes()
    for size, points in [('m6', m6), ('m3', m3 + CLAMPS)]:
        d.holes(oobb.gv('hole_radius_' + size, '3dpr'), f'({depth}) + 0.02 mm', z=f'({z}) - 0.01 mm',
                positions=points, name='OOBB_' + size)
    if side == 'upper':
        d.holes(oobb.gv('screw_socket_cap_radius_m3', '3dpr'), 'housing_top - join_head_seat + 0.01 mm',
                z='join_head_seat', positions=CLAMPS, name='recessed_M3_clamps')
    elif side == 'lower':
        for x, y in m6:
            d.oobb_cut('oobb_nut', position=[x, y, 'casing_bottom + 6.5 mm'], radius_name='m6',
                       depth=6.6, zz='bottom', rotation=[180, 0, 30], overhang=True)
        for x, y in CLAMPS:
            d.oobb_cut('oobb_nut', position=[x, y, 'casing_bottom + 4.7 mm'], radius_name='m3',
                       depth=4.8, zz='bottom', rotation=[180, 0, 30], overhang=True)


def profile_geometry():
    return discover().module('cycloidal_pattern').profile(
        dict(ring_pin_count=35, pitch_radius=27.9, eccentricity=.7, roller_radius=1.5, clearance=.2),
        validation_cases=[dict(ring_pin_count=32, pitch_radius=25.55),
                          dict(eccentricity=.68), dict(eccentricity=.72, pitch_radius=28.05),
                          dict(ring_pin_count=20, pitch_radius=24.1),
                          dict(ring_pin_count=10, pitch_radius=22.4, eccentricity=.9)])


BUILDERS = dict(previous.BUILDERS, eccentric_hub_lower=lower_hub, eccentric_hub_upper=upper_hub,
                output_casing_lower=lambda d: output_piece(d, 'lower'),
                output_casing_lobes=lambda d: output_piece(d, 'lobes'),
                output_casing_upper=lambda d: output_piece(d, 'upper'))


def run(name, piece=None):
    out = PROJECT/'build/native_v9'/name
    out.mkdir(parents=True, exist_ok=False)
    geometry = profile_geometry()
    (out/'profile.json').write_text(json.dumps(geometry), encoding='utf-8')
    with MCPClient(out/'author', allow_path=PROJECT, timeout=600) as client:
        d = discover().module('native_design').Design(client)
        parameters(d)
        if piece in ('rotor_a', 'rotor_b'):
            previous.rotor(d, piece == 'rotor_b', geometry)
        elif piece:
            BUILDERS[piece](d)
        else:
            for side in (0, 1):
                print('Rotor', side, flush=True); previous.rotor(d, side, geometry)
            for part, fn in BUILDERS.items():
                print('Building', part, flush=True); fn(d)
            for part in previous.PRINT_POSITIONS: previous.place(d, part)
        health_check(client, out/'health.json')
        require_ok(client.call('save', dict(path=str(out/'gearbox.solidcraft'))))
        for ext in ('step', 'stl'):
            require_ok(client.call('export', dict(path=str(out/('gearbox.' + ext)))))
        (out/'commands.json').write_text(json.dumps(d.commands), encoding='utf-8')
    print('Saved', out, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    parser.add_argument('--piece', choices=[*BUILDERS, 'rotor_a', 'rotor_b'])
    args = parser.parse_args()
    run(args.name, args.piece)
