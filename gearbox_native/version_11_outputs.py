"""Verify V11 nut loading in build order on native solids and publish the selected part."""

import json
import shutil
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import numpy as np
from gearbox_native.verify_assembly_sequence import bounds
from gearbox_native.nema17_end_caps_checks import named_shapes, check_pairs
from gearbox_native.nema17_outputs import MotorAudit
from gearbox_native.version_11 import ROOT, STYLE, TRAYS
from gearbox_native.native_catalogue import sha


def verify(views):
    shapes = named_shapes(
        views / "assembled.step",
        json.loads((views / "assembled_health.json").read_text()),
    )
    report = check_assembly(shapes)
    report["assembled_step_sha256"] = sha(views / "assembled.step")
    (views / "v11_access.json").write_text(json.dumps(report, indent=2))
    return report


def check_assembly(shapes):
    for name in ["output_circle_plate", "output_lower_row_plate"]:
        shapes.pop(name)
    changed = list(TRAYS) + [
        "shaft_end_upper",
        "shaft_end_lower",
        "carrier_top",
        "shaft_mount_upper",
        "hardware_shaft_M3x35_lower",
        "hardware_shaft_tie_nut_upper",
    ]
    report = check_pairs(shapes, changed)
    assert not report["clashes"], report["clashes"]
    a = MotorAudit.__new__(MotorAudit)
    a.shapes = shapes
    a.boxes = {n: bounds(s) for n, s in shapes.items()}
    a.cache = {}
    a.records = []
    a.boolean_checks = 0
    a.slivers = []
    a.bore_exclusions = []
    a.through_bores = {}
    installed = []

    def family(*prefix):
        return sorted(n for n in shapes if n.startswith(prefix))

    def add(label, names, delta=-60):
        installed.extend(a.path(label, names, installed, delta))

    add(
        "Start from the socket cap end",
        ["shaft_end_upper", "carrier_top_cap", "output_cap_cylinder"],
    )
    add(
        "Stand ring, guide and both shaft screws",
        family(
            "hardware_ring_M3",
            "hardware_ring_cap",
            "hardware_drive_shanks",
            "hardware_drive_caps",
            "hardware_shaft_M3x35",
        ),
        60,
    )
    add("Seat both starting bearings", ["hardware_6810_top", "hardware_6704_top"])
    add("Place both empty trays and output plate", list(TRAYS) + ["output_cap_plate"])
    add(
        "Drop twelve M3 nuts into open trays",
        family("hardware_carrier_top_mount_nut", "hardware_shaft_mount_nut_upper"),
    )
    add("Close both nut trays", ["carrier_top", "shaft_mount_upper"])
    add("Fit all sleeves", family("printed_contact", "printed_drive"))
    add("Fit first cam", ["shaft_cam_b_outer"])
    add(
        "Slide on closed disc B",
        family("rotor_b", "hardware_disc_b", "hardware_6704_disc_b"),
    )
    add("Opposed cams", ["shaft_cam_b_inner", "shaft_cam_a_inner"])
    add(
        "Slide on closed disc A",
        family("rotor_a", "hardware_disc_a", "hardware_6704_disc_a"),
    )
    add("Close cam A", ["shaft_cam_a_outer"])
    add(
        "Fit finishing plate and empty carriers",
        ["output_nut_plate", "carrier_bottom", "shaft_mount_lower"],
    )
    add(
        "Drop finishing mounting nuts into open pockets",
        family("hardware_carrier_bottom_mount_nut", "hardware_shaft_mount_nut_lower"),
    )
    add("Seat finishing bearings", ["hardware_6810_bottom", "hardware_6704_base"])
    add(
        "Close finishing ends",
        ["shaft_end_lower", "carrier_bottom_cap", "output_nut_cylinder"],
    )
    add(
        "Tighten both shaft ties and remaining nuts",
        family(
            "hardware_shaft_tie_nut", "hardware_drive_nuts", "hardware_M3_ring_nuts"
        ),
    )
    assert set(installed) == set(shapes)
    for pref in ["hardware_shaft_M3x35", "hardware_shaft_tie_nut"]:
        pair = family(pref)
        assert len(pair) == 2
        assert np.allclose(
            a.boxes[pair[0]][[2, 5]], a.boxes[pair[1]][[2, 5]], atol=0.001
        )
    from gearbox_native.exact_geometry import _move
    from gearbox_native.nema17_outputs import overlap

    floors = {}
    for prefix, floor in [
        ("hardware_carrier_top_mount_nut", "carrier_top_cap"),
        ("hardware_shaft_mount_nut_upper", "shaft_end_upper"),
        ("hardware_carrier_bottom_mount_nut", "carrier_bottom"),
        ("hardware_shaft_mount_nut_lower", "shaft_mount_lower"),
    ]:
        for nut in family(prefix):
            # Gravity acts along native +Z with the socket heads on the bench.
            displaced = _move(shapes[nut], "translate", [0, 0, 0.8])
            assert overlap(displaced, shapes[floor]) > 0.03, (nut, floor)
            floors[nut] = floor
    assert len(floors) == 24
    screws = family("hardware_shaft_M3x35")
    nuts = family("hardware_shaft_tie_nut")
    engagement = []
    for screw in screws:
        box = a.boxes[screw]
        axis = (box[:2] + box[3:5]) / 2
        mate = next(
            n
            for n in nuts
            if np.linalg.norm((a.boxes[n][:2] + a.boxes[n][3:5]) / 2 - axis) < 0.03
        )
        low, high = a.boxes[mate][[2, 5]]
        length = min(box[5], high) - max(box[2], low)
        assert length >= 2.49, (screw, mate, length)
        engagement.append(round(length, 3))
    report.update(
        steps=a.records,
        boolean_checks=a.boolean_checks,
        installed_bodies=len(installed),
        gravity_supports=floors,
        shaft_thread_engagement_mm=engagement,
        physical_fit_tested=False,
    )
    return report


def upgrade_plate(part):
    from gearbox_native.split_stack import layer_audit
    import trimesh

    # A V10 manual build can reuse every other printed part and fastener.
    kit = part / "v10_upgrade"
    kit.mkdir(exist_ok=True)
    batch = []
    checks = {}
    for name, (x, y) in {
        "carrier_top": (29, 29),
        "carrier_top_nut_tray": (86, 29),
        "shaft_end_upper": (14, 73),
        "shaft_end_lower": (42, 73),
        "shaft_mount_upper": (70, 73),
        "shaft_mount_upper_nut_tray": (98, 73),
    }.items():
        mesh = trimesh.load_mesh(part / "native_parts" / (name + ".stl"))
        assert mesh.is_volume and abs(mesh.bounds[0, 2]) < 0.01, name
        checks[name] = layer_audit(mesh)
        assert checks[name]["unsupported_islands"] == 0, name
        centre = mesh.bounds.mean(axis=0)
        mesh.apply_translation([x - centre[0], y - centre[1], 0])
        assert all(
            np.any(
                (m.bounds[0, :2] - mesh.bounds[1, :2] > 2)
                | (mesh.bounds[0, :2] - m.bounds[1, :2] > 2)
            )
            for m in batch
        ), name
        batch.append(mesh)
    trimesh.util.concatenate(batch).export(kit / "3dpr.stl")
    (kit / "3dpr.scad").write_text('import("3dpr.stl", convexity=10);\n')
    (kit / "print_check.json").write_text(json.dumps(checks, indent=2))


def publish(part, source, views, template_sha=None):
    from gearbox_native.double_bearing_diagram import draw_exploded
    from gearbox_native.verify_double_bearing import swept
    from gearbox_native.simple_double_bearing import PROFILE
    from gearbox_native.verify_double_bearing_housing import inspect_plate, section
    import trimesh

    proof = views / "v11_access.json"
    verified = json.loads(proof.read_text()) if proof.exists() else {}
    if verified.get("assembled_step_sha256") != sha(views / "assembled.step"):
        verified = verify(views)
    rec = json.loads((views / "export.json").read_text())
    assert rec["source_sha256"] == sha(source)
    v = {p["name"]: p["value"] for p in rec["parameters"]["parameters"]}
    ring = int(v["reduction"])
    assert v["ring_count"] == ring
    assert sum(n.startswith("printed_contact_sleeve") for n in rec["parts"]) == ring
    assert rec["print_mesh"]["body_count"] == len(rec["parts"]) and rec["print_mesh"]["watertight"]
    motion = swept(v, json.loads(PROFILE.read_text()))
    motion["lobes_per_printed_half"] = {}
    for name in ("rotor_a", "rotor_a_cap", "rotor_b", "rotor_b_cap"):
        outline = section(trimesh.load_mesh(views / "parts" / (name + ".stl")), .25)[0]
        xy = np.asarray(outline.exterior.coords)[:-1] - np.asarray(outline.centroid.coords)[0]
        radius = np.linalg.norm(xy, axis=1)
        # A closed cycloid crosses its mid-radius outwards once per lobe.
        above = radius > (radius.max() + radius.min()) / 2
        lobes = int(np.count_nonzero(above & ~np.roll(above, 1)))
        assert lobes == ring - 1, (name, lobes, ring)
        motion["lobes_per_printed_half"][name] = lobes
    for name in ("output_cap_plate", "output_nut_plate"):
        mesh = trimesh.load_mesh(views / "parts" / (name + ".stl"))
        inspect_plate(mesh, name, v["bearing_ring_radius"], v["pitch"], ring)
    part.mkdir(exist_ok=True, parents=True)
    for orig, target in [
        ("assembled", "true"),
        ("exploded", "exploded"),
        ("3dpr", "3dpr"),
    ]:
        for ext in ("solidcraft", "step", "stl", "png"):
            shutil.copy2(views / (orig + "." + ext), part / (target + "." + ext))
    shutil.copytree(views / "parts", part / "native_parts", dirs_exist_ok=True)
    if ring == 20:
        upgrade_plate(part)
    shutil.copy2(source, part / "gearbox_controls.solidcraft")
    shutil.copy2(views / "v11_access.json", part / "assembly_verification.json")
    draw_exploded(part, views, v)
    (part / "3dpr.scad").write_text('import("3dpr.stl", convexity=10);\n')
    (part / "native_export_verification.json").write_text(
        json.dumps(
            dict(
                source_sha256=sha(source),
                template_sha256=template_sha or sha(ROOT / "version_11.solidcraft"),
                part_names=list(rec["parts"]),
                parameters=v,
                print_mesh=rec["print_mesh"],
                sampling=rec["sampling"],
            ),
            indent=2,
        )
    )
    from working_3mf import RECIPES, publish as publish_print_kit, slice_project
    (part / "motion_verification.json").write_text(json.dumps(motion, indent=2))
    kit = publish_print_kit(part, RECIPES / "version_11.json")
    with tempfile.TemporaryDirectory() as scratch:
        slice_project(kit, Path(scratch) / "slice")
    subprocess.run([sys.executable, str(ROOT / "working_assembly.py"), "--part", str(part),
                    "--views", str(views)], cwd=ROOT, check=True)

    nav = ROOT / "navigation_oobb/oobb/part/motor_gearbox/cycloidal" / STYLE / f"{ring}_to_1_reduction"
    nav.mkdir(parents=True, exist_ok=True)
    link = os.path.relpath(part / "README.md", nav).replace(os.sep, "/")
    (nav / "README.md").write_text(f"# Manual {ring}:1 cycloidal gearbox\n\n[Parts and assembly notes]({link})\n", newline="\n")
    (nav / "active_part.json").write_text(json.dumps(dict(version=STYLE, part_id=part.name,
        path=part.relative_to(ROOT).as_posix()), indent=2) + "\n", newline="\n")
    shutil.copy2(part / "3dpr.stl", nav / "3dpr.stl")
    print("Published", part, verified["boolean_checks"], flush=True)
