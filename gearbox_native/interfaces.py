"""Named mechanical interfaces shared by production parts and fit samples.

All radii are millimetres. Bearing sizes come from the OOBB catalogue; only
manufacturing clearances and retaining-lip overlaps are project choices.
"""
from gearbox_native import parts as p


def bearing_seat(c, role, *, lip_overlap=.8, inner_overlap=.8):
    spec=c[role+'_bearing']
    return dict(name=role+'_bearing_seat',size=c['bearing_'+role],nominal=dict(spec),
        seat_radius=spec['od']/2+c['bearing_seat_clearance'],
        seat_depth=spec['depth']+2*c['bearing_endplay'],
        through_radius=spec['od']/2-lip_overlap,
        journal_radius=spec['id']/2-c['journal_clearance'],
        inner_shoulder_radius=spec['id']/2+inner_overlap)


def define(c):
    c['bearing_seats']={
        'cycloid_drive':bearing_seat(c,'eccentric'),
        'front_shaft':bearing_seat(c,'shaft',lip_overlap=1.5),
        'output_casing':bearing_seat(c,'output',lip_overlap=1.3,inner_overlap=1.5),
    }
    for side, label in enumerate(('bottom','top')):
        local=dict(c, eccentric_bearing=c['eccentric_bearings'][side],
                   bearing_eccentric=c['bearing_eccentric_'+label])
        c['bearing_seats']['cycloid_'+label]=bearing_seat(local,'eccentric')
    c['cycloid_holes']={
        'drive_bearing':dict(kind='bearing',positions=[[0,0]],seat='cycloid_drive'),
        'guide_orbit':dict(kind='through',positions=c['guide_positions'],
            pitch_radius=c['guide_pin_pitch_radius'],pin_radius=c['guide_pin_diameter']/2,
            orbit_radius=c['radius_offset'],radial_clearance=c['guide_pin_clearance'],
            radius=c['guide_hole_radius']),
        'support_post_orbit':dict(kind='through',positions=c['post_positions'],
            pitch_radius=c['post_pitch_radius'],pin_radius=c['post_radius'],
            orbit_radius=c['radius_offset'],radial_clearance=c['post_clearance'],
            radius=c['post_hole_radius']),
    }


def for_disc(c, side):
    """Select a physical bearing without losing the shared interface vocabulary."""
    if 'eccentric_bearings' not in c:return c
    label=('bottom','top')[side];seat=c['bearing_seats']['cycloid_'+label]
    return dict(c, eccentric_bearing=c['eccentric_bearings'][side],
        bearing_eccentric=c['bearing_eccentric_'+label],
        bearing_seats=dict(c['bearing_seats'],cycloid_drive=seat),
        eccentric_journal_radius=seat['journal_radius'],
        eccentric_journal_depth=seat['seat_depth'],
        eccentric_shoulder_radius=seat['inner_shoulder_radius'])


def cut_bearing(t, seat, *, top, through_depth, xy=(0,0)):
    p.hole(t,seat['through_radius'],through_depth,xy)
    p.hole(t,seat['seat_radius'],seat['seat_depth'],xy,z=top-seat['seat_depth'])


def cut_cycloid_holes(t,c,depth):
    for feature in c['cycloid_holes'].values():
        for xy in feature['positions']:
            if feature['kind']=='bearing':
                cut_bearing(t,c['bearing_seats'][feature['seat']],top=depth,through_depth=depth,xy=xy)
            else:p.hole(t,feature['radius'],depth,xy)
