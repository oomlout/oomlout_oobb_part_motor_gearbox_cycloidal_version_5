"""Editable assembly/explosion poses for the native V6 printed components.

Independent of SCAD. Poses use current resolved recipe dimensions. Upper rotor
halves and casing lids are flipped from their print orientations. The rotors
orbit without spinning; the outer casing turns at input / reduction.
"""
import math


def assembly_parts(c):
    if c.get('simple_assembly'):
        from gearbox_native.simple import assembly_parts as simple_parts
        return simple_parts(c)
    # name, assembled translation, print-to-assembly X rotation, explosion
    # direction (multiplied by the presentation spacing), moving member.
    rows = [
        ('motor_mount', [0, 0, 0], 0, [0, 0, -11], 'fixed'),
        ('pin_rear', [0, 0, c['deck_bottom']], 0, [0, 0, -7], 'fixed'),
        ('pin_front', [0, 0, c['front_support_bottom']], 0, [0, 0, 7], 'fixed'),
        ('front_bearing_hub', [0, 0, c['front_hub_bottom']], 0, [0, 0, 10], 'fixed'),
        ('output_base', [0, 0, c['case_split_z']], 180, [10, 0, -4], 'output'),
        ('output_casing', [0, 0, c['case_split_z']], 0, [10, 0, 1], 'output'),
        ('output_cover', [0, 0, c['housing_depth'] + c['front_retainer_depth']], 180, [0, 0, 14], 'output'),
        ('coupling_collar', [0, 0, c['collar_bottom']], 0, [-8, 0, -7], 'input'),
        ('coupling_drive', [0, 0, c['drive_start']], 0, [-8, 0, -4], 'input'),
        ('eccentric_hub_lower', [0, 0, c['drive_flange_top']], 0, [-8, 0, -1], 'input'),
        ('eccentric_hub_upper', [0, 0, c['hub_split_z']], 0, [-8, 0, 4], 'input'),
    ]
    for side, letter in enumerate(('a', 'b')):
        if c.get('plain_guides'):
            rows.append((f'rotor_{letter}', [0,0,c[f'rotor_{letter}_z'] + side*c['rotor_thickness']],
                         side*180, [0,0,-2 if side==0 else 3], f'orbit_{side}'))
            continue
        for half, tag in enumerate(('lower', 'upper')):
            rows.append((f'rotor_{letter}_{tag}', [0, 0, c[f'rotor_{letter}_z'] + half*c['rotor_thickness']],
                         half*180, [0, 0, (-4, -1, 2, 5)[side*2+half]], f'orbit_{side}'))
    return [dict(name=n, translation=p, rotation_x=rx, explode=d, member=m) for n,p,rx,d,m in rows]


def pose(item, c, expansion=0., input_turns=0., spacing=12.):
    angle = input_turns*2*math.pi
    member = item['member']
    rz = angle if member == 'input' else angle/c['reduction'] if member == 'output' else 0
    base=list(item['translation'])
    if item.get('rotate_position'):
        x,y=base[:2];base[:2]=[x*math.cos(rz)-y*math.sin(rz),x*math.sin(rz)+y*math.cos(rz)]
    location = [p + expansion*spacing*d for p,d in zip(base, item['explode'])]
    if member.startswith('orbit_'):
        sign = 1 if member == 'orbit_0' else -1
        location[0] += sign*c['radius_offset']*math.cos(angle)
        location[1] += sign*c['radius_offset']*math.sin(angle)
    return location, [math.radians(item['rotation_x']), math.radians(item.get('rotation_y',0)), rz+math.radians(item.get('rotation_z',0))]


def motion(seconds, reduction):
    """15 second loop: assemble, separate, operate exploded, reassemble."""
    def smooth(v):
        v = max(0., min(1., v))
        return v*v*(3-2*v)
    if seconds < 1: return 0., 0., 'ASSEMBLED'
    if seconds < 3.5: return smooth((seconds-1)/2.5), 0., 'EXPLODING'
    if seconds < 11.5: return 1., reduction*(seconds-3.5)/8, 'EXPLODED / IN MOTION'
    if seconds < 14: return 1-smooth((seconds-11.5)/2.5), float(reduction), 'REASSEMBLING'
    return 0., float(reduction), 'ASSEMBLED'
