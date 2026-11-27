"""Real mesh, complete motion sweep and staged assembly tests for captured discs."""

import hashlib
import json
import shutil
import tempfile
import math
from functools import lru_cache
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import trimesh
from validate_gearbox import run_scad


def validate(folder, frames=73, workers=3):
    folder = Path(folder).resolve()
    if (folder / "SEALED.json").exists():
        raise ValueError("Sealed release")
    exe = shutil.which("openscad.com") or shutil.which("openscad")
    m = json.loads((folder / "gearbox.json").read_text(encoding="utf-8"))
    c = m["parameters"]
    report = dict(
        status="running",
        architecture=c["architecture"],
        reduction=c["reduction"],
        motion_frames=frames,
    )
    (folder / "validation.json").write_text(json.dumps(report))

    def mesh_check(name):
        run_scad(exe, folder / (name + ".scad"), folder / (name + ".stl"))
        mesh = trimesh.load_mesh(folder / (name + ".stl"))
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, (
            name + " invalid mesh"
        )
        expected = len(m["pieces"]) if name == "3dpr" else m["fit_coupons"].get(name, 1)
        count = len(mesh.split())
        assert count == expected, f"{name}: {count} solids, expected {expected}"
        assert abs(mesh.bounds[0, 2]) < 1e-5, f"{name}: off bed {mesh.bounds}"
        if name in m["pieces"]:
            assert (
                abs(mesh.bounds[1, 2] - m["pieces"][name]["depth"]) < 1e-5
            ), f"{name}: wrong height {mesh.bounds}"
        return dict(
            part=name,
            watertight=True,
            solid_count=count,
            bounds_mm=mesh.bounds.tolist(),
            volume_mm3=float(mesh.volume),
        )

    with ThreadPoolExecutor(max_workers=workers) as pool:
        report["meshes"] = list(
            pool.map(mesh_check, [*m["pieces"], "3dpr", *m["fit_coupons"]])
        )
    print(f"Rendered {len(report['meshes'])} printable meshes", flush=True)
    # Check actual STL pocket/retaining-lip cross sections, including the mirrored halves.
    from shapely.geometry import Point

    @lru_cache(maxsize=None)
    def section_at(name, z):
        mesh = trimesh.load_mesh(folder / (name + ".stl"))
        section = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        assert section is not None
        planar, transform = section.to_2D()
        return planar.polygons_full, np.linalg.inv(transform)

    def contains(name, z, xy):
        polys, inverse = section_at(name, z)
        local = inverse @ np.array([*xy, z, 1])
        return any(poly.contains(Point(local[:2])) for poly in polys)

    for name in ("rotor_a_lower", "rotor_a_upper", "rotor_b_lower", "rotor_b_upper"):
        mirror = -1 if name.endswith("upper") else 1
        for x, y in c["guide_positions"]:
            y *= mirror
            assert not contains(name, 2, (x + 7.45, y)), (
                name + " bearing pocket too small"
            )
            assert contains(name, 0.5, (x + 7.3, y)), name + " retaining lip absent"
            assert not contains(name, 0.5, (x + 6.8, y)), (
                name + " shield clearance blocked"
            )
    report["disc_pocket_sections"] = 24
    for side, name in enumerate(("eccentric_hub_lower", "eccentric_hub_upper")):
        base = c["drive_flange_top"] if side == 0 else c["hub_split_z"]
        z = c["eccentric_bearing_z"][side] - base
        for deg in range(0, 360, 5):
            a = math.radians(deg)
            r = c["eccentric_journal_radius"] - 0.15
            assert contains(
                name,
                z,
                (
                    (1 if side == 0 else -1) * c["radius_offset"] + r * math.cos(a),
                    r * math.sin(a),
                ),
            ), (
                name + " bearing journal interrupted"
            )
    report["continuous_journal_samples"] = 144
    head = c["housing_depth"] + c["front_retainer_depth"] - c["case_screw_head_z"]
    for x, y in c["housing_positions"]:
        assert not contains(
            "output_cover", head - 1, (x + 2.85, y)
        ), "Socket head top access blocked"
        assert contains(
            "output_cover", head + 0.5, (x + 2.2, y)
        ), "Socket head has no supporting floor"
        assert contains(
            "output_cover", head - 1, (x + 3.4, y)
        ), "Cover screw tube wall absent"
    report["recessed_case_screw_floors_and_access"] = 4
    # The base's broad joining face lies on the bed, with the bearing cup up.
    for deg in range(0, 360, 15):
        a = math.radians(deg)
        xy = (40 * math.cos(a), 40 * math.sin(a))
        assert contains("output_base", 0.25, xy), "Base joint face is not flat on bed"
        assert not contains(
            "output_base", c["case_base_depth"] - 0.5, xy
        ), "Unused lower lobes remain in bearing base"
    for x, y in c["housing_positions"]:
        assert not contains("output_base", 0.25, (x, -y)), "Base screw passage blocked"
        assert not contains("output_casing", 0.25, (x, y)), "Ring screw passage blocked"
        assert contains("output_base", 0.25, (x + 3, -y)), "Base has no clamping land"
        assert contains("output_casing", 0.25, (x + 3, y)), "Ring has no clamping land"
    report["split_casing_flat_base_samples"] = 24
    report["split_casing_clamp_passages"] = 4
    with tempfile.TemporaryDirectory(prefix="captured-fit-") as temp:
        temp = Path(temp)

        def motion(i):
            turn = c["reduction"] * i / (frames - 1)
            run_scad(
                exe,
                folder / "fit_check.scad",
                temp / f"motion_{i}.stl",
                "-D",
                f"input_turns={turn:.12f}",
                empty=True,
            )
            return i

        with ThreadPoolExecutor(max_workers=workers) as pool:
            for i in pool.map(motion, range(frames)):
                if i % 12 == 0:
                    print(f"Motion {i+1}/{frames}", flush=True)
        report["motion_collisions"] = 0
        jobs = []
        for name in m["installation_checks"]:
            values = [0] if name == "flange_nuts" else np.linspace(0, 45, 19)
            if name in ("guide_bearing", "disc_upper", "nuts", "hub_nut"):
                values = np.linspace(0, 20, 17)
            for i, shift in enumerate(values):
                jobs.append((name, i, float(shift)))

        def installation(job):
            name, i, shift = job
            run_scad(
                exe,
                folder / (name + "_installation_check.scad"),
                temp / f"{name}_{i}.stl",
                "-D",
                f"installation_shift={shift}",
                empty=True,
            )
            return name

        results = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for i, name in enumerate(pool.map(installation, jobs)):
                results.append(name)
                if (i + 1) % 40 == 0:
                    print(f"Assembly {i+1}/{len(jobs)}", flush=True)
        report["installation_poses"] = {
            n: results.count(n) for n in m["installation_checks"]
        }
        run_scad(exe, folder / "grub_access_check.scad", temp / "grub.stl", empty=True)
        report["grub_access_paths"] = 2
        run_scad(exe, folder / "wrong_phase_check.scad", temp / "wrong_phase.stl")
        assert (
            trimesh.load_mesh(temp / "wrong_phase.stl").volume > 0.01
        ), "Wrong-phase key unexpectedly fits"
        report["wrong_phase_key_blocked"] = True
    print("Motion and assembly paths clear", flush=True)
    from gearbox.annotations import render_annotations

    render_annotations(folder)
    for name in (
        "3dpr",
        "section",
        "motor_drive",
        "guide_rollers",
        "grub_access",
        "nut_loading",
        "flange_nut_loading",
    ):
        run_scad(
            exe,
            folder / (name + ".scad"),
            folder / (name + ".png"),
            "--render",
            "--autocenter",
            "--viewall",
            "--imgsize=1400,1100",
            "--projection=ortho",
        )
    report["scad_sha256"] = {
        f.name: hashlib.sha256(f.read_bytes()).hexdigest()
        for f in sorted(folder.glob("*.scad"))
    }
    report["status"] = "passed"
    (folder / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    motion_report = {
        k: report[k]
        for k in ("status", "motion_frames", "motion_collisions", "scad_sha256")
    }
    motion_report["source_report"] = "validation.json"
    (folder / "motion_validation.json").write_text(
        json.dumps(motion_report, indent=2) + "\n"
    )
    print("Captured-bearing validation passed", flush=True)
    return report
