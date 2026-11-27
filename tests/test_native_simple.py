"""Packaging, assembly and editable-interface checks for consolidated V5."""
import math
import pytest
from shapely.geometry import LineString, Point
from gearbox_native.captured import resolve, build
from gearbox_native.cycloid_equation import CycloidEquation
from gearbox_native.lobe import profile_points
from gearbox_native.presentation import assembly_parts, pose


def config(**kwargs):
    return resolve(dict(architecture='simple_6810', **kwargs))


def test_bearing_limited_package_and_seven_parts():
    c=config()
    assert resolve(c)==c
    assert c['output_bearing']==dict(id=50,od=65,depth=7)
    assert 2*c['housing_radius']==pytest.approx(69.2)
    assert c['housing_depth']==50
    assert set(build(**c))=={'motor_mount','pin_front','output_casing','rotor_a','rotor_b',
                            'eccentric_hub_lower','eccentric_hub_upper'}
    assert c['housing_positions']==[] and c['single_output_ring']
    assert c['coupling_top']==24 and c['coupling_screw_up']
    with pytest.raises(ValueError,match='locks'):
        config(bearing_output='6814')


def test_m3_clamps_fit_inside_main_bearing_with_bottom_loaded_nuts():
    c=config();guide=c['fastener_interfaces']['guide_clamp']
    assert guide['size']=='m3' and guide['head']=='socket_cap' and guide['length']==35
    assert guide['head_z']-guide['length']<=guide['nut_bottom']
    assert guide['nut_bottom']>c['motor_plate_depth']
    assert c['guide_pin_pitch_radius']+1.5<c['output_bearing']['id']/2
    assert len(guide['positions'])==6
    assert c['guide_bolt_head_z']-c['rotor_a_z']==pytest.approx(12.4)
    with pytest.raises(ValueError,match='35 mm'):
        config(guide_bolt_length=40)


def test_named_seats_and_orbit_holes_track_overrides():
    c=config(bearing_seat_clearance=.15,guide_pin_clearance=.25)
    seat=c['bearing_seats']['cycloid_drive']
    assert seat['size']=='6703' and seat['nominal']==dict(id=17,od=23,depth=4)
    assert seat['seat_radius']==pytest.approx(11.65)
    assert c['bearing_seats']['output_casing']['seat_radius']==pytest.approx(32.65)
    for name in ('guide_orbit','support_post_orbit'):
        h=c['cycloid_holes'][name]
        assert h['radius']==pytest.approx(h['pin_radius']+h['orbit_radius']+h['radial_clearance'])
    assert c['cycloid_holes']['guide_orbit']['radius']==3
    assert c['rotor_thickness']-seat['seat_depth']>=.8-1e-9


def test_opposed_discs_and_bearing_reliefs_outside_the_working_band():
    c=config();rows=assembly_parts(c)
    for turns in (0,.125,.5,.875,1):
        a=pose(next(r for r in rows if r['name']=='rotor_a'),c,input_turns=turns)[0]
        b=pose(next(r for r in rows if r['name']=='rotor_b'),c,input_turns=turns)[0]
        assert a[:2]==pytest.approx([-v for v in b[:2]])
    assert c['rotor_b_z']-c['rotor_a_z']-c['rotor_thickness']==.5
    assert c['casing_features']['rear_6810_seat']['top']<c['rotor_a_z']
    assert c['casing_features']['front_6810_seat']['bottom']>c['rotor_b_z']+c['rotor_thickness']


def test_analytic_profile_adapter_stays_within_chord_tolerance():
    c=config();eq=CycloidEquation(c['ring_pin_count'],c['pitch_radius'],c['radius_offset'],
                                 c['lobe_radius'],c['lobe_clearance'])
    assert eq.point(0)==pytest.approx(eq.point(2*math.pi))
    from oobb_solidcraft.registry import discover
    from gearbox_native.lobe import shared_component
    vertices=discover().module('cycloidal_disc').profile(shared_component(c,c['rotor_thickness']))['points']
    boundary=LineString(vertices+[vertices[0]])
    assert max(boundary.distance(Point(eq.point(2*math.pi*i/10003)))
               for i in range(10003))<=c['profile_tolerance']*1.01
    for key,value in eq.definition().items():
        if key!='native_representation':assert c['cycloid_equation'][key]==value
    assert 'parametric_profile' in c['cycloid_equation']['native_representation']


def test_reduction_sizes_lobes_unless_explicitly_overridden():
    assert config(reduction=12)['lobe_radius']==pytest.approx(2.75)
    assert config(reduction=20)['lobe_radius']==pytest.approx(1.65)
    assert config(reduction=12,lobe_radius=2)['lobe_radius']==2
