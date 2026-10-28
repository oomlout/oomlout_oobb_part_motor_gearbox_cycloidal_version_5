"""Larger eccentricity without silently expanding the main bearing package."""
import math
import pytest
from shapely.geometry import Polygon,Point
from gearbox_native.captured import resolve
from gearbox_native.lobe import component

def config(**kw):
    return resolve(dict(architecture='simple_6810',drive_connection='grub_nut',
                        direct_stack_layout='base_grub',**kw))

def active(**kw):
    options=dict(radius_offset=1.4,pitch_radius_increment=.05,post_fasteners=True,lobe_eccentricity_ratio=.93)
    options.update(kw)
    return config(**options)

def test_more_eccentricity_preserves_external_package_and_hardware():
    old=config();new=active()
    assert resolve(new)==new
    assert new['pitch_radius']==pytest.approx(30.15)
    for key in ('housing_radius','housing_depth','overall_height','motor_plate_depth',
                'bearing_output','bearing_eccentric','bearing_shaft','guide_bolt_length',
                'hub_bolt_length','direct_grub_length','rotor_thickness','disc_gap'):
        assert new[key]==old[key]
    assert new['casing_bore_radius']-new['pitch_radius']+new['lobe_radius']==pytest.approx(2.8)
    assert new['guide_hole_radius']*2==pytest.approx(6.2)
    assert new['post_hole_radius']*2==pytest.approx(8.5)
    assert new['radius_calculation']['mode']=='automatic'
    assert new['radius_calculation']['rounding_increment_mm']==.05

def test_new_profile_is_simple_and_retains_web_around_disc_features():
    c=active()
    poly=Polygon(component(c,c['rotor_thickness'])['points'])
    assert poly.is_valid and poly.area>0
    for feature in ('guide_orbit','support_post_orbit'):
        hole=c['cycloid_holes'][feature]
        for xy in hole['positions']:
            assert poly.contains(Point(xy))
            assert poly.boundary.distance(Point(xy))-hole['radius']>=c['minimum_wall']-c['profile_tolerance']
    assert c['housing_radius']-c['casing_bore_radius']>=c['casing_wall']
    assert c['pitch_radius']+c['lobe_radius']-c['casing_bore_radius']>=.4
    # Casing must slide over both eccentric discs through its bearing lips.
    swept_radius=c['pitch_radius']+2*c['radius_offset']-c['lobe_radius']-c['lobe_clearance']
    assert swept_radius+.09<c['casing_features']['bearing_lip']['radius']

def test_automatic_radius_grows_when_envelope_needs_it():
    c=config(radius_offset=1.5,lobe_radius=1.8,pitch_radius_increment=.05)
    assert c['housing_radius']>34.6
    with pytest.raises(ValueError,match='envelope'):
        config(radius_offset=1.4,pitch_radius=30.5)
    for invalid in (0,-.1,math.nan,math.inf):
        with pytest.raises(ValueError,match='increment'):
            config(pitch_radius_increment=invalid)
    with pytest.raises(ValueError,match='casing bearing lip'):
        active(radius_offset=1.45,lobe_radius=1.8)
