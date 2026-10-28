"""Mechanical propagation and rejection at the public gearbox boundary."""
import copy,json
from pathlib import Path
import pytest
from gearbox_native import controls,interfaces
from gearbox_native.configurator import recipe,check
from gearbox_native.simple import rotor
from oobb_solidcraft.compiler import compile_thing
from gearbox_native.equation_surfaces import context,edited_plan
from gearbox_native.exact_geometry import build_shape
from oobb_solidcraft.validation import inspect_shape


def config(**overrides):return recipe(dict(controls.defaults(),**overrides))[2]


def test_public_defaults_resolve_to_current_device():
    c=config()
    assert (c['reduction'],c['disc_lobes'],c['pitch_radius'],c['overall_height'])==(20,19,31.15,32)
    assert c['bearing_output']=='6810'
    assert controls.from_config(c)==controls.defaults()


def test_pitch_modes_buffer_and_ratio_are_not_ignored():
    assert config(reduction=16)['pitch_radius']==29.4
    auto=config(eccentricity=1.2,radius_buffer=.1)
    assert auto['pitch_radius']==29.1
    manual=config(automatic_pitch=0,contact_pitch_radius=31.2,radius_buffer=8)
    assert manual['pitch_radius']==31.2
    assert manual['radius_calculation']['mode']=='explicit_override'
    with pytest.raises((ValueError,AssertionError)):config(radius_buffer=1)


def test_both_bearing_seats_journals_and_axial_centres_follow_selection():
    c=config(eccentricity=1,bottom_bearing=6803,guide_pitch_radius=18.2,standoff_pitch_radius=19.5,disc_thickness=6)
    lower,upper=(interfaces.for_disc(c,i) for i in (0,1))
    assert lower['bearing_eccentric']=='6803' and upper['bearing_eccentric']=='6703'
    assert lower['bearing_seats']['cycloid_drive']['seat_radius']==13.1
    assert upper['bearing_seats']['cycloid_drive']['seat_radius']==11.6
    assert lower['eccentric_journal_depth']==5.2 and upper['eccentric_journal_depth']==4.2
    assert c['eccentric_bearing_z'][0]==pytest.approx(c['rotor_a_z']+6-2.6)
    assert c['eccentric_bearing_z'][1]==pytest.approx(c['rotor_b_z']+2.1)
    with pytest.raises(ValueError,match='web'):config(top_bearing=6704)


def test_hardware_changes_include_heads_nuts_and_orbit_not_only_bores():
    c=config(guide_radius=3,eccentricity=.5,guide_pitch_radius=18.7,standoff_pitch_radius=20)
    assert c['guide_bolt_radius_name']=='m6' and c['guide_pin_diameter']==6
    assert c['guide_hole_radius']==3.7 and c['guide_socket_radius']==5.5
    assert c['guide_nut_top']-c['guide_nut_bottom']==pytest.approx(5.0)
    assert c['fastener_interfaces']['guide_clamp']['size']=='m6'
    with pytest.raises(ValueError,match='catalogue'):config(guide_radius=2)


def test_view_controls_do_not_change_manufacturing_dimensions():
    base=config();other=config(input_angle=360,reference_bearing=6805,reference_underlay=0,amber_clearance=.5)
    for key in ('bearing_output','pitch_radius','guide_hole_radius','rotor_thickness','housing_depth'):
        assert base[key]==other[key]


def test_invalid_inputs_rejected_before_cad():
    for value in ({'reduction':20.5},{'eccentricity':float('nan')},{'unknown':1},{'disc_thickness':1}):
        with pytest.raises(ValueError):controls.validate(value)
    with pytest.raises(ValueError):config(disc_thickness=3)


def test_explorer_roundtrip_preserves_manufacturing_settings():
    a=controls.defaults();a.update(reduction=16,eccentricity=1.2,top_bearing=6803)
    assert controls.from_explorer(controls.to_explorer(a))==a


def test_explorer_minimum_pitch_matches_recipe_for_examples():
    import subprocess
    root=Path(__file__).resolve().parents[1]
    for path in (root/'examples/shared_controls').glob('*.json'):
        values=json.loads(path.read_text(encoding='utf-8'))['values']
        c=recipe(values)[2]
        script="const g=require('./cycloidal_explorer/dist/geometry.js');const p=JSON.parse(process.argv[1]);console.log(g.calculate(p).p.radius)"
        radius=float(subprocess.check_output(['node','-e',script,json.dumps(controls.to_explorer(values))],cwd=root))
        assert radius==pytest.approx(c['pitch_radius']),path.name
