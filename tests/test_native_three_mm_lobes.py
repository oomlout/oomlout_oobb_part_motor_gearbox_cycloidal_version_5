"""Large printed contacts must retain a simple, uncut cycloid profile."""
import pytest
from shapely.geometry import Polygon,Point
from working_oomp_populate import get_options
from gearbox_native.captured import resolve
from gearbox_native.lobe import component
from gearbox_native.cycloid_equation import CycloidEquation


def test_active_three_mm_contacts_fit_bearings_and_keep_disc_webs():
    c=resolve(get_options()[0]['oobb_details'])
    assert c['lobe_radius']==3 and c['radius_offset']==1.4
    assert c['pitch_radius']==31.15
    assert 2*c['housing_radius']==pytest.approx(72.3)
    assert c['overall_height']==32 and c['bearing_output']=='6810'
    assert resolve(c)==c
    poly=Polygon(component(c,c['rotor_thickness'])['points'])
    assert poly.is_valid and poly.area>0
    for name in ('guide_orbit','support_post_orbit'):
        hole=c['cycloid_holes'][name]
        for xy in hole['positions']:
            assert poly.contains(Point(xy))
            assert poly.boundary.distance(Point(xy))-hole['radius']>=c['minimum_wall']-c['profile_tolerance']
    assert c['casing_lip_pass_clearance']>.4


def test_oversize_contact_at_old_pitch_is_rejected_before_cad_export():
    old=CycloidEquation(20,30.15,1.4,3,.2)
    assert old.minimum_convex_radius()==pytest.approx(2.6316239485)
    with pytest.raises(ValueError,match='undercut'):
        old.validate_offset()
    CycloidEquation(20,31.15,1.4,3,.2).validate_offset()
