"""Physical envelopes, moving bearing bores and editable framework defaults."""

import copy
import math
import pytest
from shapely.affinity import rotate, translate
from shapely.geometry import Point, Polygon
from working_oomp_populate import get_options
from gearbox.parts import resolve, build, layout, bearing_spec
from gearbox.lobe import profile_points


def config(**kw):
    # This file exercises the sealed SCAD architecture, not active V5 defaults.
    return resolve({**get_options()[0], "architecture": "captured_6810",
                    "rotor_thickness": 7, "guide_pin_diameter": 6,
                    "radius_offset": 1.85, "lobe_radius": 2.1, **kw})


def test_dimensions_and_repeatable_resolve():
    c = config()
    assert c["radius_offset"] == 1.85
    assert c["output_bearing"] == dict(id=50, od=65, depth=7)
    assert c["guide_bearing"] == dict(id=10, od=15, depth=4)
    assert c["eccentric_bearing"] == dict(id=20, od=27, depth=4)
    assert c["shaft_bearing"] == dict(id=20, od=27, depth=4)
    assert c == resolve(c)
    assert c["guide_running_clearance"] == pytest.approx(0.15)
    assert c["coupling_top"] == 24 and c["coupling_flange_z"] == 22
    assert c["housing_radius"] < 50


def test_guide_bores_clear_bolts_over_full_cycle():
    c = config()
    for angle in range(0, 360, 3):
        for side in (0, 1):
            a = math.radians(angle + 180 * side)
            orbit = [c["radius_offset"] * math.cos(a), c["radius_offset"] * math.sin(a)]
            for x, y in c["guide_positions"]:
                clearance = (
                    c["guide_bearing"]["id"] / 2
                    - math.dist([x, y], [x + orbit[0], y + orbit[1]])
                    - 3
                )
                assert clearance == pytest.approx(0.15)
    with pytest.raises(ValueError, match="running clearance"):
        config(radius_offset=1.95)


@pytest.mark.parametrize("ratio", [8, 12, 16, 20])
def test_new_profile_motion(ratio):
    c = config(reduction=ratio)
    poly = Polygon(
        profile_points(
            c["disc_lobes"],
            c["pitch_radius"],
            c["radius_offset"],
            c["lobe_radius"],
            c["lobe_clearance"],
        )
    )
    assert poly.is_valid
    minimum = 100
    for angle in range(0, 360 * ratio, 37):
        for side in (0, 1):
            a = math.radians(angle + 180 * side)
            disc = translate(
                rotate(poly, c["disc_phase_degrees"][side], origin=(0, 0)),
                c["radius_offset"] * math.cos(a),
                c["radius_offset"] * math.sin(a),
            )
            for x, y in c["ring_positions"]:
                out = math.radians(angle / ratio)
                q = Point(
                    x * math.cos(out) - y * math.sin(out),
                    x * math.sin(out) + y * math.cos(out),
                )
                minimum = min(minimum, disc.distance(q) - c["lobe_radius"])
    assert 0.199 < minimum < 0.201


def test_bearing_mounts_and_fastener_assembly():
    c = config()
    assert c["rear_bearing_bottom"] > c["motor_plate_depth"]
    assert c["deck_bottom"] > c["rear_bearing_top"] + 2
    assert c["guide_nut_bottom"] >= c["deck_bottom"]
    assert c["guide_bolt_head_z"] + 4 < c["front_hub_bottom"]
    assert c["guide_bolt_head_z"] - c["guide_bolt_length"] < c["guide_nut_bottom"]
    assert c["guide_bolt_head_z"] - c["guide_bolt_length"] > 4
    assert c["carrier_journal_radius"] < c["output_bearing"]["id"] / 2
    assert c["guide_spacer_depths"] == []
    assert (
        c["guide_pin_pitch_radius"] + c["guide_hole_radius"] + 2
        < c["pitch_radius"] - c["radius_offset"] - c["lobe_radius"] - 0.2
    )
    assert (
        c["guide_pin_pitch_radius"]
        - c["guide_hole_radius"]
        - c["eccentric_bearing"]["od"] / 2
        - 0.1
        < 0  # Shared pocket is intentional; metal outer races still do not overlap.
    )
    assert c["central_to_guide_race_gap"] == pytest.approx(0.1)
    assert (
        c["guide_pin_pitch_radius"] - c["guide_lip_radius"] - c["eccentric_lip_radius"]
        >= 1
    )
    with pytest.raises(ValueError, match="web"):
        config(allow_shared_bearing_pockets=False)
    with pytest.raises(ValueError, match="outer races"):
        config(bearing_eccentric="6705")
    with pytest.raises(ValueError, match="inside output bearing"):
        config(guide_pin_pitch_radius=23)


def test_casing_socket_heads_recess_to_bottom_nuts_with_35mm_limit():
    from gearbox.hardware import screw_lengths

    c = config()
    assert c["housing_screw_style"] == "socket_cap"
    assert screw_lengths(c)["housing"] == 35
    assert c["case_nut_bottom"] == 7
    assert c["case_screw_head_z"] == 42
    assert c["case_screw_head_z"] - 35 == c["case_nut_bottom"]
    assert c["case_cover_post_bottom"] == 39.5
    assert c["housing_depth"] + c["front_retainer_depth"] == 67
    assert config(housing_screw_length=60)["housing_screw_length"] == 35
    assert config(housing_screw_max_length=30)["housing_screw_length"] == 30


def test_casing_split_retains_bearing_and_nut_support():
    c = config()
    assert c["case_split_z"] == pytest.approx(13.4)
    assert c["case_base_depth"] == pytest.approx(8.9)
    assert c["case_ring_depth"] == pytest.approx(51.6)
    assert c["case_split_z"] > c["case_nut_bottom"] + 2.4
    raised = config(case_split_z=15)
    assert raised["case_base_depth"] == pytest.approx(10.5)
    assert raised["housing_screw_length"] == c["housing_screw_length"] == 35
    with pytest.raises(ValueError, match="bearing shoulder"):
        config(case_split_z=10)
    with pytest.raises(ValueError, match="below the discs"):
        config(case_split_z=40)


def test_fifteen_parts_and_kwargs():
    c = config(disc_gap=0.8)
    assert c["rotor_b_z"] - c["rotor_a_z"] == pytest.approx(7.8)
    parts = build(**c)
    poses = layout(parts, **c)
    assert len(parts) == len(poses) == 15
    for i, a in enumerate(poses):
        for b in poses[i + 1 :]:
            needed = (a["width"] + b["width"]) / 2
            assert (
                abs(a["pos"][0] - b["pos"][0]) >= needed
                or abs(a["pos"][1] - b["pos"][1]) >= needed
            )


def test_6700_in_oobb_v5_component_and_legacy_lookup():
    import oobb

    assert bearing_spec("6700") == dict(id=10, od=15, depth=4)
    assert 2 * oobb.gv("bearing_6700_id", "true") == 10
    assert 2 * oobb.gv("bearing_6700_od", "true") == 15
    assert oobb.gv("bearing_6700_depth", "true") == 4
