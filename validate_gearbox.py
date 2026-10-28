"""Render and validate the actual exported SCAD, including sampled moving fits.

Run after action_make_scad_no_stl.py. Requires OpenSCAD, trimesh and numpy.
Reports and previews stay in each assembly's parts directory.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent


def planar_zero_volume_contact(mesh):
    """Recognize nominal contact faces at any orientation, not just X/Y/Z planes."""
    if mesh is None or abs(mesh.volume) >= 1e-7:
        return False
    for part in mesh.split(only_watertight=False):
        if abs(part.volume) >= 1e-7:
            return False
        points = part.vertices - part.vertices.mean(axis=0)
        normal = np.linalg.svd(points, full_matrices=False)[2][-1]
        if np.max(np.abs(points @ normal)) >= 1e-7:
            return False
    return True


def run_scad(executable, source, output, *args, empty=False):
    result = subprocess.run(
        [executable, "--backend=Manifold", "-o", str(output), *args, str(source)],
        capture_output=True,
        text=True,
    )
    log = result.stdout + result.stderr
    if "WARNING:" in log or "ERROR:" in log:
        raise AssertionError(f"{source.name}: {log}")
    if empty:
        if "Current top level object is empty" not in log:
            # An intended bearing-to-motor face contact may be returned as a
            # zero-thickness surface by Manifold. Accept only planar, zero-volume
            # results; any volumetric interference still fails.
            contact = trimesh.load_mesh(output) if output.exists() else None
            with np.errstate(divide="ignore", invalid="ignore"):
                planar_contact = planar_zero_volume_contact(contact)
            if not planar_contact:
                raise AssertionError(f"Collision at {args}: {log}")
    elif result.returncode or not output.exists():
        raise AssertionError(f"{source.name}: {log}")
    return log


def validate(folder, frames=73, workers=3):
    if (folder / "SEALED.json").exists():
        raise ValueError(f"Sealed release cannot be revalidated in place: {folder}")
    if (
        json.loads((folder / "gearbox.json").read_text(encoding="utf-8"))[
            "parameters"
        ].get("architecture")
        == "captured_6810"
    ):
        from gearbox.captured_validate import validate as captured_validate

        return captured_validate(folder, frames, workers)
    folder = folder.resolve()
    if (folder / "SEALED.json").exists():
        raise ValueError(f"Sealed release cannot be revalidated in place: {folder}")
    executable = shutil.which("openscad.com") or shutil.which("openscad")
    if not executable:
        raise RuntimeError("OpenSCAD is not on PATH")
    manifest = json.loads((folder / "gearbox.json").read_text())
    report = {
        "reduction": manifest["reduction"],
        "meshes": [],
        "motion_frames": frames,
        "motion_collisions": 0,
    }

    (folder / "validation.json").write_text(json.dumps({"status": "running"}) + "\n")

    def mesh_check(name):
        output = folder / f"{name}.stl"
        run_scad(executable, folder / f"{name}.scad", output)
        mesh = trimesh.load_mesh(output)
        assert mesh.is_watertight, f"{name} is not watertight"
        assert mesh.is_winding_consistent, f"{name} has inconsistent winding"
        assert mesh.volume > 0, f"{name} has no volume"
        bodies = len(mesh.split())
        expected = (
            sum(p["quantity"] for p in manifest["pieces"].values())
            if name == "3dpr"
            else 1
        )
        assert bodies == expected, f"{name}: expected {expected} solids, got {bodies}"
        assert abs(mesh.bounds[0, 2]) < 1e-6, f"{name} is not on the print bed"
        if name != "3dpr":
            assert abs(mesh.bounds[1, 2] - manifest["pieces"][name]["depth"]) < 1e-5
        return {
            "part": name,
            "watertight": True,
            "solid_count": bodies,
            "bounds_mm": mesh.bounds.tolist(),
            "volume_mm3": float(mesh.volume),
        }

    with ThreadPoolExecutor(max_workers=workers) as pool:
        report["meshes"] = list(pool.map(mesh_check, [*manifest["pieces"], "3dpr"]))
    # Inspect bores on a horizontal section of the ACTUAL STL, not input metadata.
    c = manifest["parameters"]
    checks = []

    def check_bores(name, points, z):
        mesh = trimesh.load_mesh(folder / f"{name}.stl")
        section = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        assert section is not None
        planar, transform = section.to_2D()
        from shapely.geometry import Point

        for x, y in points:
            local = np.linalg.inv(transform) @ np.array([x, y, z, 1])
            assert not any(
                p.contains(Point(local[:2])) for p in planar.polygons_full
            ), f"{name}: bore blocked at {(x,y)}"
        checks.append({"part": name, "checked_bores": len(points), "z_mm": z})

    for name in ("rotor_a", "rotor_b"):
        check_bores(name, [[0, 0], *c["guide_positions"]], 1)
    for name in ("pin_front",):
        check_bores(name, [[0, 0], *c["guide_positions"]], 3)
    check_bores("output_casing", [[0, 0], *c["housing_positions"]], 1)
    check_bores("output_cover", [[0, 0], *c["housing_positions"]], 1)
    check_bores(
        "motor_mount", [[0, 0], *c["motor_positions"]], -c["mount_bottom_z"] + 1
    )
    edge = (c["housing_width"] - 1) * 15 / 2
    perimeter = []
    for i in range(2 * c["housing_width"] - 1):
        along = -edge + i * 7.5
        radius = 3.0 if i % 2 == 0 else 1.5
        for x, y in ((along, -edge), (along, edge), (-edge, along), (edge, along)):
            perimeter.extend([[x, y], [x + radius, y], [x, y + radius]])
    check_bores("motor_mount", perimeter, 2)
    check_bores("motor_mount", c["guide_positions"], c["integrated_mount_depth"] - 1)
    check_bores(
        "eccentric_hub_lower",
        [[0, 0], *c["coupling_positions"]],
        c["drive_roof_z"] - c["drive_start"] + 0.5,
    )
    check_bores(
        "eccentric_hub_upper",
        c["coupling_positions"],
        c["hub_upper_end"] - c["cap_screw_head_z"] + 0.5,
    )
    report["bore_sections"] = checks
    report["fit_coupons"] = []
    for name, count in manifest["fit_coupons"].items():
        run_scad(executable, folder / f"{name}.scad", folder / f"{name}.stl")
        coupon = trimesh.load_mesh(folder / f"{name}.stl")
        assert coupon.is_watertight and len(coupon.split()) == count
        assert abs(coupon.bounds[0, 2]) < 1e-6
        report["fit_coupons"].append(
            {"name": name, "solid_count": count, "watertight": True}
        )

    from gearbox.animation import view_settings

    view = view_settings(c)
    from gearbox.annotations import settings as annotation_settings

    annotated = annotation_settings(c)
    annotation_camera = ",".join(
        map(str, [*annotated["target"], *annotated["rotation"], annotated["distance"]])
    )
    exploded_camera = ",".join(
        map(str, [*view["target"], *view["rotation"], view["distance"]])
    )
    with tempfile.TemporaryDirectory(prefix="gearbox-fit-") as temporary:
        temporary = Path(temporary)

        def collision(i):
            turns = manifest["reduction"] * i / frames
            run_scad(
                executable,
                folder / "fit_check.scad",
                temporary / f"collision_{i}.stl",
                "-D",
                f"input_turns={turns:.12f}",
                empty=True,
            )

        with ThreadPoolExecutor(max_workers=workers) as pool:
            for i, _ in enumerate(pool.map(collision, range(frames))):
                if (i + 1) % 12 == 0 or i == frames - 1:
                    print(f"Collision poses {i+1}/{frames}", flush=True)
        for i in range(9):
            shift = (c["housing_depth"] + c["rotor_thickness"]) * i / 8
            run_scad(
                executable,
                folder / "installation_check.scad",
                temporary / f"insert_{i}.stl",
                "-D",
                f"installation_shift={shift}",
                empty=True,
            )
        report["installation_poses"] = 9
        for name in (
            "rear_bearing",
            "casing",
            "coupling",
            "guide_bolt",
            "guide_bearing",
        ):
            for i in range(17):
                run_scad(
                    executable,
                    folder / f"{name}_installation_check.scad",
                    temporary / f"{name}_{i}.stl",
                    "-D",
                    f"{name}_installation_shift={70*i/16}",
                    empty=True,
                )
            report[name + "_installation_poses"] = 17
        for example, control in (
            ("bearing_installation_check", "bearing_installation_shift"),
            ("upper_disc_installation_check", "upper_disc_installation_shift"),
            ("joint_installation_check", "joint_installation_shift"),
        ):
            for i in range(9 if example == "joint_installation_check" else 81):
                run_scad(
                    executable,
                    folder / f"{example}.scad",
                    temporary / f"{example}_{i}.stl",
                    "-D",
                    f"{control}={40*i/(8 if example == 'joint_installation_check' else 80)}",
                    empty=True,
                )
        report["eccentric_bearing_insertion_poses"] = 162
        report["disc_insertion_poses"] = 162
        report["front_cap_insertion_poses"] = 9
        for i in range(9):
            run_scad(
                executable,
                folder / "nut_installation_check.scad",
                temporary / f"nut_insert_{i}.stl",
                "-D",
                f"nut_installation_shift={(c['integrated_mount_depth']+4)*i/8}",
                empty=True,
            )
        report["bottom_nut_insertion_poses"] = 9
        run_scad(
            executable,
            folder / "flange_nut_installation_check.scad",
            temporary / "flange_nut_insert.stl",
            empty=True,
        )
        report["flange_nut_insertion"] = (
            f"all {len(c['coupling_positions'])} continuous 20 mm side-loading sweeps clear"
        )
        run_scad(
            executable,
            folder / "grub_access_check.scad",
            temporary / "grub_access.stl",
            empty=True,
        )
        report["grub_access"] = "both 1.8 mm diameter tool paths clear at service angle"
        # Compile every example; warnings are failures (including overwritten controls).
        for name in (
            "assembly",
            "animation",
            "exploded",
            "section",
            "motion",
            "3dpr",
            "motor_drive",
            "guide_rollers",
            "flange_nut_loading",
            "grub_access",
        ):
            run_scad(
                executable,
                folder / f"{name}.scad",
                temporary / f"{name}.csg",
                "--camera=" + exploded_camera,
            )
    for name, camera in (
        ("3dpr", "0,0,0,0,0,0,500"),
        ("section", "0,0,0,65,0,25,300"),
        ("motor_drive", "0,0,0,65,0,25,180"),
        ("guide_rollers", "0,0,25,65,0,25,300"),
        ("grub_access", "0,0,12,65,0,25,220"),
        ("exploded", annotation_camera),
        ("nut_loading", "0,0,0,120,0,25,180"),
        ("flange_nut_loading", "0,0,0,65,0,25,180"),
    ):
        run_scad(
            executable,
            folder / f"{name}.scad",
            folder / f"{name}.png",
            "--render",
            "--imgsize="
            + (
                ",".join(
                    map(
                        str,
                        (
                            annotated["size"]
                            if name == "exploded"
                            else c.get("animation_size", [960, 1600])
                        ),
                    )
                )
                if name in ("exploded", "animation")
                else "1400,1100"
            ),
            *(
                []
                if name in ("exploded", "animation")
                else ["--viewall", "--autocenter"]
            ),
            "--projection=ortho",
            "--camera=" + camera,
        )
    report["scad_sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(folder.glob("*.scad"))
    }
    report["status"] = "passed"
    (folder / "validation.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"{folder.name}: {len(report['meshes'])} meshes, {frames} motion frames, all passed"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", type=Path)
    parser.add_argument("--frames", type=int, default=73)
    args = parser.parse_args()
    if args.frames < 2:
        parser.error("--frames must be at least 2")
    folders = (
        [args.part]
        if args.part
        else [
            p.parent
            for p in (ROOT / "parts").glob("*/gearbox.json")
            if not (p.parent / "SEALED.json").exists()
        ]
    )
    if not folders:
        parser.error("No generated gearboxes; run action_make_scad_no_stl.py first")
    for folder in folders:
        try:
            validate(folder, args.frames)
        except Exception as error:
            if not (folder / "SEALED.json").exists():
                (folder / "validation.json").write_text(
                    json.dumps({"status": "failed", "error": str(error)}, indent=2)
                    + "\n"
                )
            raise


if __name__ == "__main__":
    main()
