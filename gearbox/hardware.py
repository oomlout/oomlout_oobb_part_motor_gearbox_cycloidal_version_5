"""OOBB nominal hardware previews, separate from printable parts."""

import copy
import math
import oobb
import opsc
from solid2 import scad_render
from gearbox.parts import blank, add, cylinder, hole, radial_bore


def hardware_list(c):
    lengths = screw_lengths(c)
    return [
        *[
            dict(
                item=c["bearing_" + k] + " bearing",
                quantity=(
                    2 * c["guide_pin_count"]
                    if k == "guide"
                    else (1 if k == "shaft" else 2)
                ),
                dimensions=c[k + "_bearing"],
            )
            for k in ("eccentric", "shaft", "output", "guide")
        ],
        dict(
            item="M6 partially threaded hex guide bolts + captive M6 nuts",
            quantity=c["guide_pin_count"],
            length=lengths["guide"],
            minimum_smooth_shank=c["guide_bolt_head_z"]
            - (c["guide_bearing_z"][0] - c["guide_bearing"]["depth"] / 2),
            maximum_thread_length=lengths["guide"]
            - (
                c["guide_bolt_head_z"]
                - c["guide_bearing_z"][0]
                + c["guide_bearing"]["depth"] / 2
            ),
        ),
        dict(
            item="M3 "
            + c.get("housing_screw_style", "countersunk")
            + " housing bolts + M3 nuts",
            quantity=4,
            length=lengths["housing"],
        ),
        dict(
            item="M3 countersunk motor screws",
            quantity=4,
            length=lengths["motor"],
            engagement=c["motor_screw_length"] - c["motor_plate_depth"],
        ),
        *[
            dict(
                item=c["bearing_guide"] + " inner-race spacer " + word,
                quantity=c["guide_pin_count"],
                od=2 * c["guide_spacer_radius"],
                id=2 * c["guide_spacer_bore"],
                length=depth,
                material="steel; clamp inner races only",
            )
            for word, depth in zip(
                ("rear", "middle", "front"), c["guide_spacer_depths"]
            )
        ],
        dict(
            item="M3 socket-cap flange screws + captive M3 nuts",
            quantity=len(c["coupling_positions"]),
            length=c["coupling_screw_length"],
        ),
        dict(
            item="5 mm bore flanged coupling",
            quantity=1,
            flange_diameter=c["coupling_diameter"],
            barrel_diameter=c["coupling_barrel_diameter"],
            length=c["coupling_length"],
            barrel_length=c["coupling_barrel_length"],
            bolt_circle_diameter=c["coupling_pitch_diameter"],
            source="oomp_mechanical_coupler/source_file/dimension/flange/dimension.csv, bore=5",
            note="Flange upward at the motor shaft tip; two grub screws 90 degrees apart, 5 mm below the barrel top per user measurement.",
        ),
        dict(item="M3 x 3 coupling grub screws", quantity=2),
        dict(
            item="NEMA 17 motor",
            quantity=1,
            hole_pitch=c["motor_hole_pitch"],
            shaft_diameter=5,
            shaft_length=c["motor_shaft_length"],
        ),
    ]


def screw_lengths(c):
    guide = c.get("guide_bolt_length")
    if guide is None:
        guide = 5 * math.ceil(
            max(
                c["guide_bolt_head_z"] - c["guide_nut_bottom"],
                c["guide_bolt_head_z"]
                - c["guide_bearing_z"][0]
                + c["guide_bearing"]["depth"] / 2
                + c["guide_thread_allowance"],
            )
            / 5
        )
    if float(guide).is_integer():
        guide = int(guide)
    return dict(
        guide=guide,
        housing=c.get(
            "housing_screw_length",
            5
            * math.ceil(
                (c["housing_depth"] + c["front_retainer_depth"] - c["case_nut_bottom"])
                / 5
            ),
        ),
        motor=c["motor_screw_length"],
    )


def export_fasteners(folder, c):
    modules = []

    def save(name, t):
        body = opsc.opsc_get_object(copy.deepcopy(t["components"]), mode="true")
        modules.append(f"module {name}() {{\n{scad_render(body)}\n}}\n")

    lengths = screw_lengths(c)
    for name, length in lengths.items():
        if name == "guide":
            continue
        t = blank()
        add(
            t,
            "oobb_screw_"
            + (
                c.get("housing_screw_style", "countersunk")
                if name == "housing"
                else "countersunk"
            ),
            radius_name="m3",
            depth=length,
            mode="true",
            nut_include=False,
            overhang=False,
        )
        save("hardware_screw_" + name, t)
    for name, size, length in (
        ("flange", "m3", c["coupling_screw_length"]),
        ("guide", c["guide_bolt_radius_name"], lengths["guide"]),
    ):
        t = blank()
        if name == "guide":
            # Installed OOBB has M3 socket heads only; use its M6 hex dimensions.
            add(
                t,
                "oobb_nut",
                radius_name=size,
                depth=oobb.gv("bolt_depth_" + size, "true"),
                mode="true",
                overhang=True,
                rot=[0, 0, c["guide_nut_rotations"][0] if name == "guide" else 0],
            )
            cylinder(t, oobb.gv("hole_radius_" + size, "true"), length, z=-length)
        else:
            add(
                t,
                "oobb_screw_socket_cap",
                radius_name=size,
                depth=length,
                mode="true",
                nut_include=False,
                overhang=False,
                zz="none",
            )
        save("hardware_screw_" + name, t)
    for size in ("m3",):
        t = blank()
        add(t, "oobb_nut", radius_name=size, mode="true", overhang=True)
        hole(
            t,
            oobb.gv("hole_radius_" + size, "true"),
            oobb.gv("nut_depth_" + size, "true") + 2,
            z=-1,
        )
        save("hardware_nut_" + size, t)
    for i, depth in enumerate(c["guide_spacer_depths"]):
        t = blank()
        cylinder(t, c["guide_spacer_radius"], depth)
        hole(t, c["guide_spacer_bore"], depth)
        save("hardware_guide_spacer_" + str(i), t)
    t = blank()
    add(
        t,
        "oobb_nut",
        radius_name=c["guide_bolt_radius_name"],
        mode="true",
        overhang=True,
    )
    hole(
        t,
        c["guide_pin_diameter"] / 2,
        oobb.gv("nut_depth_" + c["guide_bolt_radius_name"], "true") + 2,
        z=-1,
    )
    save("hardware_nut_guide", t)
    t = blank()
    cylinder(t, 1.5, 3, z=-3)
    save("hardware_set_screw", t)
    for name in ("eccentric", "shaft", "output", "guide"):
        spec = c[name + "_bearing"]
        t = blank()
        # Nominal annulus from OOBB bearing dimensions; no cutter relief.
        cylinder(t, spec["od"] / 2, spec["depth"], z=-spec["depth"] / 2)
        hole(t, spec["id"] / 2, spec["depth"], z=-spec["depth"] / 2)
        save("hardware_bearing_" + name, t)
    t = blank()
    flange_depth = c["coupling_length"] - c["coupling_barrel_length"]
    cylinder(t, c["coupling_diameter"] / 2, flange_depth, c["coupling_barrel_length"])
    cylinder(
        t,
        c["coupling_barrel_diameter"] / 2,
        c["coupling_barrel_length"],
        z=0,
    )
    hole(t, 2.55, c["coupling_length"])
    for xy in c["coupling_hole_positions"]:
        hole(
            t,
            c["coupling_flange_hole_diameter"] / 2 + 0.02,
            flange_depth,
            xy,
            z=c["coupling_barrel_length"],
        )
    for angle in c["coupling_grub_angles"]:
        radial_bore(
            t,
            1.52,
            0,
            c["coupling_barrel_diameter"],
            c["coupling_barrel_length"] - c["coupling_grub_from_barrel_top"],
            angle,
        )
    save("hardware_coupling", t)
    t = blank()
    add(
        t,
        "oobb_cube",
        size=[c["motor_body_width"], c["motor_body_width"], c["motor_body_depth"]],
        pos=[0, 0, -c["motor_body_depth"]],
        zz="bottom",
    )
    cylinder(t, c["motor_pilot_diameter"] / 2, c["motor_pilot_height"])
    cylinder(t, 2.5, c["motor_shaft_length"])
    for xy in c["motor_positions"]:
        hole(t, 1.5, 3, xy, z=-3)
    save("hardware_motor", t)
    (folder / "hardware.scad").write_text("\n".join(modules), encoding="utf-8")
    return lengths
