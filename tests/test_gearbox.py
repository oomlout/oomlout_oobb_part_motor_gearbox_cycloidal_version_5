"""Numerical motion, assembly interfaces and real framework regression tests."""

import copy
import json
import math
from pathlib import Path
import subprocess
import sys
import pytest
from shapely.affinity import rotate, translate
from shapely.geometry import Point, Polygon
from gearbox.lobe import profile_points
from gearbox.parts import build, layout, resolve
from working_oomp_populate import get_options

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("ratio", [8, 12, 16, 20])
def test_opposed_discs_clear_rotating_casing_for_full_output_turn(ratio):
    c = resolve({"reduction": ratio})
    profile = Polygon(
        profile_points(
            c["disc_lobes"],
            c["pitch_radius"],
            c["radius_offset"],
            c["lobe_radius"],
            c["lobe_clearance"],
        )
    )
    assert profile.is_valid
    minimum = math.inf
    for side in (0, 1):
        for angle in range(0, 360 * ratio, 11):
            phase = math.radians(angle + side * 180)
            rotor = translate(
                rotate(profile, c["disc_phase_degrees"][side], origin=(0, 0)),
                c["radius_offset"] * math.cos(phase),
                c["radius_offset"] * math.sin(phase),
            )
            psi = math.radians(angle / ratio)
            for x, y in c["ring_positions"]:
                centre = Point(
                    x * math.cos(psi) - y * math.sin(psi),
                    x * math.sin(psi) + y * math.cos(psi),
                )
                minimum = min(minimum, rotor.distance(centre) - c["lobe_radius"])
    assert 0.199 < minimum < 0.201


def test_guide_pin_clearance_and_opposed_mass_centres():
    c = resolve({})
    for angle in range(0, 4320, 7):
        a = math.radians(angle)
        out = 0
        centres = [
            [s * c["radius_offset"] * math.cos(a), s * c["radius_offset"] * math.sin(a)]
            for s in (1, -1)
        ]
        assert sum(v[0] for v in centres) == pytest.approx(0)
        assert sum(v[1] for v in centres) == pytest.approx(0)
        for x, y in c["guide_positions"]:
            pin = [
                x * math.cos(out) - y * math.sin(out),
                x * math.sin(out) + y * math.cos(out),
            ]
            for centre in centres:
                hole = [pin[0] + centre[0], pin[1] + centre[1]]
                clearance = (
                    c["guide_hole_radius"]
                    - math.dist(pin, hole)
                    - c["guide_bearing"]["od"] / 2
                )
                assert clearance == pytest.approx(0.15)
    assert c["disc_phase_degrees"] == [0, -180 / c["disc_lobes"]]
    assert c["output_member"] == "outer_casing"
    assert c["output_direction"] == "same_as_input"
    assert c["eccentric_phase_degrees"] == [0, 180]


def test_nine_piece_layout_is_disjoint():
    c = resolve({})
    parts = build(**c)
    placements = layout(parts, **c)
    assert len(parts) == len(placements) == 9
    for i, a in enumerate(placements):
        assert a["pos"][2] == 0
        for b in placements[i + 1 :]:
            required = (a["width"] + b["width"]) / 2
            assert (
                abs(a["pos"][0] - b["pos"][0]) >= required
                or abs(a["pos"][1] - b["pos"][1]) >= required
            )


def test_overrides_propagate_without_mutation():
    option = get_options(
        [
            {
                "reduction": 12,
                "architecture": "legacy",
                "rotor_thickness": 7,
                "guide_pin_diameter": 6,
                "pitch_radius": 52,
                "radius_offset": 1.5,
                "lobe_radius": 3.0,
                "lobe_eccentricity_ratio": 0.52,
                "lobe_clearance": 0.35,
                "guide_pin_clearance": 0.25,
                "guide_pin_pitch_radius": 30.6,
                "bearing_guide": "606",
                "guide_spacer_radius": 4.0,
                "flange_depth": 17,
                "motor_shaft_length": 26,
                "future_setting": "preserved",
            }
        ]
    )[0]
    before = copy.deepcopy(option)
    c = resolve(option["oobb_details"])
    parts = build(**c)
    assert option == before
    assert c["future_setting"] == "preserved"
    assert c["guide_hole_radius"] == 10.25
    assert c["motor_shaft_length"] == 26
    profile = parts["rotor_a"]["thing"]["components"][0]
    assert profile["points"][0][0] == pytest.approx(52 - 1.5 - 3 - 0.35)
    assert option["taxonomy_6"] == "12_to_1_reduction"


@pytest.mark.parametrize(
    "override",
    [
        {"reduction": 8.5},
        {"reduction": 2},
        {"radius_offset": 0},
        {"pitch_radius": 10},
        {"rotor_thickness": 3},
        {"disc_gap": 2},
        {"samples_per_lobe": 10},
        {"guide_pin_clearance": -0.1},
        {"guide_pin_pitch_radius": 15},
        {"shaft_radius_name": "m6"},
        {"motor_screw_length": 12},
        {"motor_shaft_length": 40},
    ],
)
def test_impossible_interfaces_fail_before_writing(override):
    with pytest.raises(ValueError):
        resolve(override)


def test_automatic_radius_and_explicit_override():
    small = resolve({"reduction": 8})
    medium = resolve({"reduction": 12})
    large = resolve({"reduction": 32})
    assert small["pitch_radius"] == medium["pitch_radius"] == 50
    assert large["pitch_radius"] == 62.0
    assert resolve(small)["radius_calculation"] == small["radius_calculation"]
    assert (
        resolve({"pitch_radius": 52})["radius_calculation"]["mode"]
        == "explicit_override"
    )


def test_full_framework_two_reductions(tmp_path):
    code = f"""
import sys
sys.path.insert(0,{str(ROOT)!r})
import working
working.run(run_oomp_populate=True,run_oomp=True,run_scad=True,
 generate_stl=False,navigation=False,parts_directory="parts",
 reductions=[{{"reduction":8}},{{"reduction":12,"lobe_clearance":.3}}])
"""
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    folders = sorted((tmp_path / "parts").iterdir())
    assert len(folders) == 2
    for folder in folders:
        import yaml
        part = yaml.safe_load((folder / "working.yaml").read_text())
        assert part["oobb_details"]["reduction"] in (8, 12)
        assert part["oobb_details"]["oobb_name"] == "version_5"
        assert part["oobb_details"]["run_solidcraft"] is True
        assert part["oobb_details"]["run_scad"] is False
        assert not list(folder.glob("*.scad"))


def test_pipeline_preserves_four_sealed_releases_and_creates_version_five(tmp_path):
    frozen = []
    for version in (1, 2, 3, 4):
        for parent in ("parts", "parts_source"):
            folder = tmp_path / parent / f"sealed_version_{version}"
            folder.mkdir(parents=True)
            for name, content in (
                ("SEALED.json", "{}\n"),
                ("working.yaml", "frozen: true\n"),
            ):
                path = folder / name
                path.write_text(content)
                frozen.append((path, path.read_bytes()))
    code = f"""
import sys
sys.path.insert(0, {str(ROOT)!r})
import working
working.run(run_oomp_populate=True, run_oomp=True, run_scad=True,
            generate_stl=False, navigation=False, parts_directory="parts")
"""
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert all(path.read_bytes() == content for path, content in frozen)
    folders = list((tmp_path / "parts").glob("*version_5*"))
    assert len(folders) == 1
    assert (folders[0] / "working.yaml").exists()
    assert not (folders[0] / "3dpr.scad").exists()
    assert not (folders[0] / "SEALED.json").exists()


def test_native_navigation_uses_catalogue_details_and_protects_seals(tmp_path, monkeypatch):
    import yaml
    import scad_help
    monkeypatch.chdir(tmp_path)
    folder = tmp_path / "parts" / "native_part"
    folder.mkdir(parents=True)
    (folder / "working.yaml").write_text(yaml.safe_dump({
        "taxonomy_1": "native", "oobb_details": {"taxonomy_1": "native"}
    }))
    (folder / "3dpr.solidcraft").write_bytes(b"native test fixture")
    scad_help.generate_navigation(sort=["taxonomy_1"])
    destination = tmp_path / "navigation_oobb" / "native"
    assert (destination / "3dpr.solidcraft").read_bytes() == b"native test fixture"
    (destination / "SEALED.json").write_text("{}")
    with pytest.raises(ValueError, match="Sealed navigation"):
        scad_help.generate_navigation(sort=["taxonomy_1"])


def test_sealed_release_rejects_direct_writers(tmp_path):
    from gearbox.export import export_gearbox
    from gearbox.animation import render_animation
    from validate_gearbox import validate

    (tmp_path / "SEALED.json").write_text("{}\n")
    for writer in (
        lambda: export_gearbox(tmp_path, {}),
        lambda: render_animation(tmp_path),
        lambda: validate(tmp_path),
    ):
        with pytest.raises(ValueError, match="Sealed release"):
            writer()
    import working_scad

    for version in (1, 2, 3, 4):
        with pytest.raises(ValueError, match=f"Version {version} is sealed"):
            get_options([{"style": f"version_{version}"}])
        with pytest.raises(ValueError, match=f"Version {version} is sealed"):
            getattr(working_scad, f"get_version_{version}")({})
    assert get_options()[0]["style"] == "version_5"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["SEALED.json"]


def test_coupler_dimensions_match_local_reference_snapshot():
    c = resolve({})
    assert c["coupling_diameter"] == 22
    assert c["coupling_barrel_diameter"] == 10
    assert c["coupling_barrel_length"] == 10
    assert c["coupling_pitch_diameter"] == 16
    assert len(c["coupling_hole_positions"]) == 4
    assert len(c["coupling_positions"]) == 2
    assert c["coupling_positions"][0] == pytest.approx(
        [-v for v in c["coupling_positions"][1]]
    )
    for (x, y), angle in zip(c["coupling_positions"], c["coupling_nut_rotations"]):
        dx, dy = -math.cos(math.radians(angle)), -math.sin(math.radians(angle))
        assert x * dy - y * dx == pytest.approx(0, abs=1e-9)
        assert x * dx + y * dy > 0
    assert all(math.hypot(*p) == pytest.approx(8) for p in c["coupling_positions"])
    assert c["coupling_grub_angles"] == [45, 135]
    assert c["coupling_flange_z"] - c["coupling_grub_z"] == 5
    assert c["coupling_grub_z"] - c["grub_access_radius"] > c["rear_bearing_top"]


def test_twenty_to_one_sizes_for_mr106_guides_and_6814_supports():
    # Regression coverage for the preserved compact MR106 alternative.
    c = resolve(
        get_options(
            [{"architecture": "legacy", "radius_offset": 1.75, "lobe_radius": 2.0,
              "rotor_thickness": 7, "guide_pin_diameter": 6}]
        )[0]["oobb_details"]
    )
    assert c["reduction"] == 20 and c["disc_lobes"] == 19
    assert c["pitch_radius"] == 50
    assert c["housing_radius"] == 55
    assert c["housing_width"] * 15 - 1 == 119
    assert c["radius_offset"] == 1.75
    assert c["lobe_radius"] == 2
    assert c["casing_bore_radius"] == 51.5
    profile = profile_points(
        c["disc_lobes"],
        c["pitch_radius"],
        c["radius_offset"],
        c["lobe_radius"],
        c["lobe_clearance"],
    )
    assert Polygon(profile).is_valid
    radii = [math.hypot(*point) for point in profile]
    assert max(radii) - min(radii) == pytest.approx(3.5, abs=0.002)
    assert (
        max(radii) + c["radius_offset"]
        <= c["casing_bore_radius"] - c["lobe_clearance"] + 0.001
    )
    # Refinement handles the tight valleys without forcing every span to use
    # the resolution of the highest-curvature span.
    assert 19 * 240 <= len(profile) < 19 * 1440


@pytest.mark.parametrize("ratio", [8, 12, 20])
def test_straight_contact_backs_clear_both_orbits(ratio):
    from shapely.geometry import box
    from shapely.ops import unary_union

    c = resolve({"reduction": ratio})
    profile = Polygon(
        profile_points(
            c["disc_lobes"],
            c["pitch_radius"],
            c["radius_offset"],
            c["lobe_radius"],
            c["lobe_clearance"],
        )
    )
    back = box(
        c["pitch_radius"],
        -c["lobe_radius"],
        c["housing_radius"] - 0.2,
        c["lobe_radius"],
    )
    backs = unary_union(
        [rotate(back, i * 360 / ratio, origin=(0, 0)) for i in range(ratio)]
    )
    for angle in range(0, 360 * ratio, 47):
        for side in (0, 1):
            phase = math.radians(angle + 180 * side)
            disc = translate(
                rotate(profile, c["disc_phase_degrees"][side], origin=(0, 0)),
                c["radius_offset"] * math.cos(phase),
                c["radius_offset"] * math.sin(phase),
            )
            in_case_frame = rotate(disc, -angle / ratio, origin=(0, 0))
            assert in_case_frame.distance(backs) > 0.19


@pytest.mark.parametrize(
    "overrides",
    [
        {"bearing_output": "6810"},
        {"bearing_guide": "608"},
        {"guide_pin_pitch_radius": 20.5},
        {"guide_spacer_radius": 4.5},
        {"rotor_thickness": 5.3},
    ],
)
def test_unsafe_guide_interfaces_rejected(overrides):
    with pytest.raises(ValueError):
        resolve(overrides)


def test_compact_stack_places_flange_at_tip_and_halves_nearly_total_height():
    c = resolve({})
    assert c["coupling_orientation"] == "flange_up_at_motor_shaft_tip"
    assert c["coupling_top"] == c["motor_shaft_length"] == 24
    assert c["coupling_flange_z"] == 22
    assert c["disc_gap"] == 0.5
    assert c["housing_depth"] + c["front_retainer_depth"] == 37
    assert c["rear_bearing_bottom"] < 0 < c["rear_bearing_top"]
    assert c["guide_spacer_depths"] == pytest.approx([2.5, 4.5, 2.5])
    assert c["guide_nut_bottom"] == pytest.approx(0.5)
    assert c["guide_heads_nested"]
    assert c["guide_bolt_head_z"] < c["output_bearing_z"][1] + 5
    assert c["coupling_z"] > c["motor_pilot_height"]
    assert c["drive_end"] == c["coupling_flange_z"]
    assert c["cap_roof_bottom"] == c["coupling_flange_top"]
    assert c["cap_start"] > c["drive_end"]
    for side in range(2):
        assert (
            c["eccentric_bearing"]["id"] / 2
            > c["coupling_diameter"] / 2 + c["radius_offset"]
        )


def test_hollow_shaft_has_no_central_joining_fastener():
    from gearbox.hardware import hardware_list, screw_lengths

    c = resolve({})
    bom = hardware_list(c)
    assert not any("joining" in v["item"] or "washer" in v["item"] for v in bom)
    assert sum(v["quantity"] for v in bom if v["item"].endswith(" bearing")) == 17
    assert c["eccentric_bearing"] == dict(id=30, od=37, depth=4)
    assert c["shaft_bearing"] == dict(id=30, od=37, depth=4)
    assert c["output_bearing"] == dict(id=70, od=90, depth=10)
    assert screw_lengths(c) == dict(guide=40, housing=40, motor=6)
    peg = next(v for v in bom if "hex guide bolts" in v["item"])
    assert peg["minimum_smooth_shank"] == pytest.approx(21.8)
    assert peg["length"] - peg["minimum_smooth_shank"] >= c["guide_thread_allowance"]
    assert c["cap_screw_head_z"] - c["coupling_screw_length"] <= c["drive_roof_z"]
    # Both real guide nuts and the longer bolt tips clear the motor sides.
    for x, y in c["guide_positions"]:
        assert max(abs(x), abs(y)) - 3 > c["motor_body_width"] / 2


def test_compact_settings_are_repeatable_and_forwarded():
    c = resolve(
        get_options(
            [
                {
                    "architecture": "legacy",
                    "rotor_thickness": 7,
                    "guide_pin_diameter": 6,
                    "radius_offset": 1.75,
                    "lobe_radius": 2.0,
                    "motor_shaft_length": 26,
                    "disc_gap": 0.8,
                }
            ]
        )[0]["oobb_details"]
    )
    assert c["coupling_top"] == 26
    assert c["disc_gap"] == 0.8
    assert resolve(c) == c
    assert c["guide_spacer_depths"][1] == pytest.approx(4.8)


@pytest.mark.parametrize(
    "overrides",
    [
        {"bearing_eccentric": "6704"},
        {"bearing_shaft": "6704"},
        {"disc_gap": 0.2},
        {"flange_depth": 12},
        {"motor_shaft_length": 20},
        {"coupling_screw_length": 4},
        {"rotor_central_wall": 3},
    ],
)
def test_compact_assembly_constraints(overrides):
    with pytest.raises(ValueError):
        resolve(overrides)


def test_contact_checker_accepts_tilted_planes_but_rejects_volume():
    import trimesh
    from validate_gearbox import planar_zero_volume_contact

    m = trimesh.Trimesh(
        vertices=[[0, 0, 0], [1, 1, 0], [1, 1, 2], [0, 0, 2]],
        faces=[[0, 1, 2], [0, 2, 3], [2, 1, 0], [3, 2, 0]],
        process=False,
    )
    assert planar_zero_volume_contact(m)
    assert not planar_zero_volume_contact(trimesh.creation.box(extents=[0.001, 1, 1]))


def test_nested_mr106_hardware_envelopes():
    import oobb

    c = resolve({})
    assert c["guide_bearing"] == dict(id=6, od=10, depth=3)
    assert 2 * c["guide_hole_radius"] == pytest.approx(13.8)
    assert 6.8 <= 2 * c["guide_spacer_radius"] <= 6.9
    assert (
        c["guide_pin_pitch_radius"]
        + oobb.gv("nut_radius_m6", "3dpr")
        + c["guide_head_wall"]
        <= c["carrier_journal_radius"]
    )
    assert c["rear_support_top"] - c["guide_nut_top"] >= 1
    for overrides in (
        {"guide_pin_pitch_radius": 28.5},
        {"guide_pin_pitch_radius": 27.8},
        {"guide_spacer_radius": 4},
        {"guide_spacer_radius": 3.3},
    ):
        with pytest.raises(ValueError):
            resolve(overrides)


def test_compact_motor_stack_and_standard_screw_lengths():
    from gearbox.hardware import screw_lengths, hardware_list
    c = resolve({})
    assert c["motor_mount_depth"] == 10
    assert c["coupling_z"]-c["motor_face_z"] == pytest.approx(2.2)
    assert c["coupling_top"]-c["coupling_z"] == 12
    assert c["drive_bearing_z"]-c["drive_bearing"]["depth"]/2 == c["motor_face_z"]
    assert c["drive_journal_radius"]-c["drive_cavity_radius"] >= c["minimum_wall"]
    assert c["hub_bolt_tip_z"] > c["motor_face_z"]+c["motor_shaft_length"]+1
    assert c["hub_bolt_tip_z"] <= c["hub_nut_bottom"]
    lengths = screw_lengths(c)
    assert lengths == dict(guide=50, housing=55, motor=6)
    assert c["hub_bolt_length"] == 30
    assert c["housing_depth"]-lengths["guide"] == c["guide_nut_bottom"]
    assert c["housing_depth"]+c["front_retainer_depth"]-lengths["housing"] > c["motor_face_z"]+c["motor_plate_depth"]
    bearings = [item for item in hardware_list(c) if item["item"].endswith(" bearing")]
    assert sum(item["quantity"] for item in bearings) == 6
    assert [item["quantity"] for item in bearings] == [2, 1, 2, 1]


def test_coupler_dimensions_match_local_reference_snapshot():
    c = resolve({})
    assert c["coupling_diameter"] == 22
    assert c["coupling_barrel_diameter"] == 10
    assert c["coupling_barrel_length"] == 10
    assert c["coupling_pitch_diameter"] == 16
    assert all(math.hypot(*p) == pytest.approx(8) for p in c["coupling_positions"])
    assert c["coupling_grub_angles"] == [0, 90]
    assert c["coupling_flange_z"]-c["coupling_grub_z"] == 5
    assert c["coupling_grub_z"]-c["grub_access_radius"] > c["drive_bearing_z"]+c["drive_bearing"]["depth"]/2


def test_split_hub_has_one_way_key_and_assembly_space():
    c = resolve({})
    assert c["hub_key_flat"] < c["hub_key_radius"]
    assert c["hub_key_flat"]-c["hub_key_clearance"]-2.75 >= 2
    assert c["hub_upper_start"] > c["hub_nut_top"]
    assert c["hub_split_z"] < c["rotor_b_z"]-1.5
    assert c["drive_roof_top"] < c["eccentric_journal_z"][0]
    assert c["shaft_shoulder_radius"]+c["radius_offset"] < c["eccentric_bearing"]["id"]/2


@pytest.mark.parametrize("override", [
    {"bearing_drive":"6705"},
    {"coupling_grub_from_flange":9},
    {"motor_mount_depth":6},
    {"hub_bolt_length":20},
    {"hub_bolt_length":50},
])
def test_incompatible_compact_interfaces_rejected(override):
    with pytest.raises(ValueError):
        resolve(override)
