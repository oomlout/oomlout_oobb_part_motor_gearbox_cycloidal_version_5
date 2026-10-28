"""Compact captured-nut drive and its shaft/fastener constraints."""
import pytest
from gearbox_native.captured import resolve,build
from gearbox_native.direct_drive import hub_sample
from gearbox_native.coupons import recipes
from oobb_solidcraft.compiler import compile_thing


def config(**kw):
    return resolve(dict(architecture='simple_6810',drive_connection='grub_nut',**kw))


def test_shorter_stack_preserves_bearings_and_lobe_envelope():
    c=config();old=resolve(dict(architecture='simple_6810'))
    assert c==resolve(c)
    assert c['housing_depth']==36 and old['housing_depth']==50
    assert c['rotor_a_z']==14 and c['drive_start']==4.5
    assert 2*c['housing_radius']==69.2
    assert c['output_bearing']==old['output_bearing']==dict(id=50,od=65,depth=7)
    assert c['eccentric_bearing']==old['eccentric_bearing']
    assert c['cycloid_equation']==old['cycloid_equation']
    assert set(build(**c))==set(build(**old))


def test_motor_shaft_passes_inside_key_below_joining_nut():
    c=config()
    assert c['hub_split_z']<c['motor_shaft_length']<c['hub_nut_bottom']
    assert c['hub_bolt_head_z']-c['hub_bolt_length']==pytest.approx(c['hub_nut_bottom'])
    assert c['hub_bolt_head_z']+3<c['housing_depth']
    assert c['hub_key_depth']>8
    assert 2*c['direct_shaft_bore_radius']==5.1
    assert c['guide_bolt_length']==20 and c['hub_bolt_length']==8


def test_grub_nut_is_radial_and_uses_bottom_loading_clearance():
    c=config();part=hub_sample(c)
    def visit(value):
        if isinstance(value,list):
            for child in value:yield from visit(child)
        elif isinstance(value,dict):
            yield value
            for child in value.values():yield from visit(child)
    requests=[v for v in visit(part) if v.get('shape')=='oobb_nut']
    assert requests and all(r['overhang'] for r in requests)
    assert all(r['rot']==[0,90,0] and r['clearance']=='left' for r in requests)
    assert c['direct_grub_outer_radius']<=c['drive_flange_radius']
    assert c['fastener_interfaces']['shaft_grub']['access']=='before fitting rear 6810'
    assert 'coupler_flange' not in c['fastener_interfaces']


def test_new_fit_sample_compiles_in_print_mode():
    sample=recipes(config())['fit_M3_grub_and_5mm_shaft']
    assert compile_thing(dict(id='direct_fit',mode='3dpr',**sample))['result_bodies']


def test_clearance_overrides_and_invalid_hardware_rejected():
    c=config(direct_shaft_clearance=.1,direct_grub_angle=45)
    assert c['direct_shaft_bore_radius']==2.6 and c['coupling_grub_angles']==[45]
    with pytest.raises(ValueError,match='Grub screw'):
        config(direct_grub_length=12)
    with pytest.raises(ValueError,match='35 mm'):
        config(direct_guide_bolt_length=40)
    with pytest.raises(ValueError,match='Socket|socket'):
        config(motor_shaft_length=30)
