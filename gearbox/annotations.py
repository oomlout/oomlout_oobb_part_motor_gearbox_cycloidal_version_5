"""Presentation-only labels generated from the resolved gearbox dimensions."""

import json
import math
import shutil
import subprocess
from pathlib import Path

from gearbox.animation import view_settings
from gearbox.hardware import screw_lengths


def settings(c):
    view = view_settings(c)
    view["distance"] = c.get("annotation_camera_distance", 1600)
    view["size"] = c.get("annotation_size", [2400, 2000])
    return view


def export_annotations(folder, c):
    folder = Path(folder)
    view = settings(c)
    e, h, f = view["explode"], c["housing_depth"], c["flange_depth"]
    r = c["housing_radius"]
    screw = screw_lengths(c)
    rows = []

    def label(name, detail, anchor, side):
        rows.append(dict(name=name, detail=detail, anchor=anchor, side=side))

    def bearing_name(kind):
        spec = c[kind + "_bearing"]
        return (
            c["bearing_" + kind]
            + " / "
            + " x ".join(f"{spec[key]:g}" for key in ("id", "od", "depth"))
            + " mm"
        )

    label("Output cover", "output_cover", [-r * 0.65, 0, h + 10 * e], "left")
    label("Front pin carrier", "pin_front", [-18, 0, h - f / 2 + 6 * e], "left")
    label("Cycloidal disc B", "rotor_b", [-20, 0, c["rotor_b_z"] + 3 * e + 3.5], "left")
    label(
        "Front bearing cap",
        "eccentric_hub_upper",
        [-6 * e, 0, c["hub_upper_end"] + 4.5 * e - 10],
        "left",
    )
    label(
        "Output casing",
        "output_casing (rotating output)",
        [9 * e + r * 0.7, 0, h / 2],
        "left",
    )
    label("Cycloidal disc A", "rotor_a", [-20, 0, c["rotor_a_z"] - 2 * e + 3.5], "left")
    label(
        "One-piece eccentric shaft",
        "eccentric_hub_lower (hollow wiggle shaft)",
        [-6 * e, 0, c["drive_start"] - 3.5 * e + 10],
        "left",
    )
    label(
        "Motor faceplate",
        "motor_mount + rear pin carrier",
        [-30, 0, c["mount_bottom_z"] - 10 * e + 2],
        "left",
    )

    p = c["housing_positions"][0]
    label(
        "Casing fasteners",
        f'4 x M3 x {screw["housing"]:g} countersunk + nuts',
        [*p, h + c["front_retainer_depth"] + 11 * e],
        "right",
    )
    p = c["guide_positions"][0]
    label(
        "Guide fasteners",
        f'{c["guide_pin_count"]} x M6 x {screw["guide"]:g} hex; smooth bearing shanks',
        [*p, c["guide_bolt_head_z"] + 8.5 * e],
        "right",
    )
    label(
        "Front shaft bearing",
        bearing_name("shaft"),
        [8, 0, c["shaft_bearing_z"][1] + 7 * e],
        "right",
    )
    for side, word in ((1, "Front"), (0, "Rear")):
        label(
            word + " casing bearing",
            bearing_name("output"),
            [29, 0, c["output_bearing_z"][side] + (5 if side else -4) * e],
            "right",
        )
    for side, word in ((1, "Disc B"), (0, "Disc A")):
        label(
            word + " eccentric bearing",
            bearing_name("eccentric"),
            [12, 0, c["eccentric_bearing_z"][side] + (4 if side else -3) * e],
            "right",
        )
    for side, word in ((0, "A"), (1, "B")):
        label(
            "Disc " + word + " guide rollers",
            f'{c["guide_pin_count"]} x ' + bearing_name("guide"),
            [
                *c["guide_positions"][0],
                c["guide_bearing_z"][side] + (-2.7 if side == 0 else 3.7) * e,
            ],
            "right",
        )
    label(
        "Guide inner-race spacers",
        f'{c["guide_pin_count"]} sets; {2*c["guide_spacer_radius"]:g} OD / {2*c["guide_spacer_bore"]:g} ID; '
        + " / ".join(f"{d:g}" for d in c["guide_spacer_depths"])
        + " mm",
        [
            *c["guide_positions"][0],
            c["guide_spacer_z"][1] + c["guide_spacer_depths"][1] / 2 + e,
        ],
        "right",
    )
    label(
        "Flange fasteners",
        f'{len(c["coupling_positions"])} x M3 x {c["coupling_screw_length"]:g} socket-cap + nuts',
        [*c["coupling_positions"][0], c["cap_screw_head_z"] + 8 * e],
        "right",
    )
    label(
        "Flanged shaft coupler",
        "5 mm bore; flange at shaft tip",
        [0, 0, c["coupling_z"] + 4.2 * e + 6],
        "right",
    )
    label(
        "Coupler grub screws",
        "2 x M3; 90 degrees apart",
        [
            c["coupling_barrel_diameter"] / 2 + 0.55 + 2 * e,
            0,
            c["coupling_grub_z"] + 4.2 * e,
        ],
        "right",
    )
    label(
        "Motor mounting screws",
        f'4 x M3 x {screw["motor"]:g} countersunk',
        [
            *c["motor_positions"][0],
            c["motor_face_z"] + c["motor_plate_depth"] - 9.5 * e,
        ],
        "right",
    )
    label(
        "Stepper motor",
        "NEMA 17 / 5 mm shaft",
        [0, 0, c["motor_face_z"] - 12 * e - c["motor_body_depth"] / 2],
        "right",
    )

    # Invert the camera rotation to order callouts vertically in screen space.
    def screen_y(row):
        x, y, z = [a - b for a, b in zip(row["anchor"], view["target"])]
        ax, ay, az = map(math.radians, view["rotation"])
        x, y = x * math.cos(az) + y * math.sin(az), -x * math.sin(az) + y * math.cos(az)
        x, z = x * math.cos(ay) - z * math.sin(ay), x * math.sin(ay) + z * math.cos(ay)
        return y * math.cos(ax) + z * math.sin(ax)

    entries = []
    for side in ("left", "right"):
        ordered = sorted(
            (r for r in rows if r["side"] == side), key=screen_y, reverse=True
        )
        for i, row in enumerate(ordered):
            row["label_y"] = 175 - i * 350 / max(1, len(ordered) - 1)
            entries.append(
                [
                    row["name"],
                    row["detail"],
                    row["anchor"],
                    side == "left",
                    row["label_y"],
                ]
            )
    (folder / "exploded_labels.scad").write_text(
        "// Generated presentation labels; not part of printable geometry.\n"
        + "annotation_rows = "
        + json.dumps(entries)
        + ";\n"
        + Path(__file__).with_name("annotations.scad.template").read_text(),
        encoding="utf-8",
    )
    (folder / "part_names.json").write_text(json.dumps(rows, indent=2) + "\n")
    table = "# Version 4 part names\n\nUse the printed identifier when requesting changes. Bearings are ID x OD x thickness in mm.\n\n| Name | Identifier / hardware |\n| --- | --- |\n"
    table += "\n".join(f'| {row["name"]} | {row["detail"]} |' for row in rows) + "\n"
    (folder / "part_names.md").write_text(table, encoding="utf-8")
    return view


def render_annotations(folder):
    folder = Path(folder).resolve()
    if (folder / "SEALED.json").exists():
        raise ValueError("Sealed release cannot be rendered in place")
    c = json.loads((folder / "gearbox.json").read_text())["parameters"]
    view = settings(c)
    executable = shutil.which("openscad.com") or shutil.which("openscad")
    result = subprocess.run(
        [
            executable,
            "--backend=Manifold",
            "--render",
            "--projection=ortho",
            "--imgsize=" + ",".join(map(str, view["size"])),
            "--camera="
            + ",".join(
                map(str, [*view["target"], *view["rotation"], view["distance"]])
            ),
            "-o",
            str(folder / "exploded.png"),
            str(folder / "exploded.scad"),
        ],
        capture_output=True,
        text=True,
    )
    log = result.stdout + result.stderr
    if result.returncode or "WARNING:" in log or "ERROR:" in log:
        raise RuntimeError(log)
    print("Rendered annotated exploded view")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    render_annotations(parser.parse_args().folder)
