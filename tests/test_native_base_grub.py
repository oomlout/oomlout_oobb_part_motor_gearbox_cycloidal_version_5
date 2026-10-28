"""Compressed axial package and mounting order constraints."""
import pytest
from gearbox_native.captured import resolve,build

def config(**kw):
    return resolve(dict(architecture='simple_6810',drive_connection='grub_nut',
                        direct_stack_layout='base_grub',**kw))

def test_stack_compresses_around_bearings_and_full_disc_band():
    c=config()
    assert c==resolve(c)
    assert c['housing_depth']==pytest.approx(31.1)
    assert c['housing_depth']-c['casing_bottom_z']==pytest.approx(26.6)
    assert c['overall_height']==32
    assert c['hub_upper_end']-c['housing_depth']==pytest.approx(.9)
    ramp=c['casing_features']['lobe_start_ramp']
    assert ramp['bottom']+ramp['depth']<=c['rotor_a_z']+1e-9
    assert c['casing_requires_lobe_support']
    assert c['flange_depth']==pytest.approx(c['output_bearing']['depth']+.8+.3)

def test_hub_installs_before_motor_plate_and_clears_pilot():
    c=config()
    assert c['drive_start']>c['motor_pilot_height']
    assert c['drive_flange_radius']+.1<c['motor_pilot_diameter']/2+c['motor_pilot_clearance']
    assert c['coupling_grub_z']==6.5
    assert c['fastener_interfaces']['shaft_grub']['access']=='before fitting motor plate'
    assert c['hub_bolt_length']==4
    assert c['hub_bolt_head_z']-c['hub_bolt_length']>c['motor_shaft_length']
    assert len(build(**c))==7

def test_overrides_preserve_clearances_and_reject_impossible_plate_passage():
    c=config(disc_gap=.7,direct_base_front_web=1)
    assert c['housing_depth']==pytest.approx(31.5)
    with pytest.raises(ValueError,match='pass over'):
        config(direct_drive_radius=12)
    with pytest.raises(ValueError,match='entry ramp'):
        config(direct_base_ramp_depth=1)
    with pytest.raises(ValueError,match='retaining roof'):
        config(direct_base_hub_bolt_length=3)
