"""Mechanical constraints for the short plain-guide V5, without a CAD process."""
import math
import pytest
from gearbox_native.captured import resolve, build
from gearbox_native.presentation import assembly_parts, pose
from oobb_solidcraft.compiler import compile_thing


def config(**kwargs):
    return resolve(dict(architecture='compact_6810', **kwargs))


def test_short_stack_and_fixed_main_bearing():
    c=config()
    assert c==resolve(c)
    assert c['housing_depth']+c['front_retainer_depth']==pytest.approx(55.5)
    assert c['output_bearing']==dict(id=50,od=65,depth=7)
    assert c['rear_bearing_bottom']==pytest.approx(4.3)
    assert c['coupling_top']==24
    assert c['shaft_bearing']==dict(id=12,od=18,depth=4)
    assert c['guide_bolt_radius_name']==c['hub_bolt_radius_name']=='m3'
    with pytest.raises(ValueError,match='locks'):
        config(bearing_output='6814')


def test_plain_guide_holes_clear_the_complete_orbit():
    c=config()
    assert c['guide_hole_radius']*2==pytest.approx(7.1)
    for i in range(361):
        angle=math.radians(i)
        shift=[c['radius_offset']*math.cos(angle),c['radius_offset']*math.sin(angle)]
        assert math.hypot(*shift)+1.5 <= c['guide_hole_radius']-0.19
    assert c['rotor_thickness']==5 and c['disc_join_count']==0
    with pytest.raises(ValueError,match='retaining lip'):
        config(rotor_thickness=4.5)


def test_thirteen_native_pieces_and_opposed_single_discs():
    c=config(); pieces=build(**c); rows=assembly_parts(c)
    assert len(pieces)==13 and set(pieces)=={r['name'] for r in rows}
    assert 'rotor_a' in pieces and 'rotor_b' in pieces
    for mode in ('true','3dpr'):
        for name,piece in pieces.items():
            assert compile_thing(dict(id=name,mode=mode,**piece['thing']))['result_bodies']
    for turns in (0,.125,.25,.75,1):
        a=pose(next(r for r in rows if r['name']=='rotor_a'),c,input_turns=turns)[0]
        b=pose(next(r for r in rows if r['name']=='rotor_b'),c,input_turns=turns)[0]
        assert a[:2]==pytest.approx([-v for v in b[:2]])


def test_overrides_propagate_and_screws_engage():
    c=config(rotor_thickness=5.2,disc_gap=.6,guide_bolt_length=30)
    assert c['rotor_b_z']-c['rotor_a_z']==pytest.approx(5.8)
    assert c['guide_bolt_head_z']-c['guide_bolt_length'] <= c['guide_nut_bottom']
    assert c['guide_nut_bottom']>c['deck_bottom']
    assert c['hub_bolt_head_z']+3 < c['hub_upper_end']
    assert c['housing_screw_length']<=35


def test_lobe_radius_is_editable_with_a_defined_attachment_limit():
    c=config(lobe_radius=2.05)
    assert c['pitch_radius']+c['lobe_radius']-c['casing_bore_radius']==pytest.approx(.4)
    assert config(lobe_radius=2.4)['lobe_radius']==2.4
    with pytest.raises(ValueError,match='attachment'):
        config(lobe_radius=2.0)
