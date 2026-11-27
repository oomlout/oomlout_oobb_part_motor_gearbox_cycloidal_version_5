"""Exports for the raised 6810 / captured-bearing architecture."""

import json
import math
from pathlib import Path
import oobb
from gearbox import parts as p
from gearbox.export import write, render
from gearbox.hardware import export_fasteners, hardware_list
from gearbox.animation import view_settings
from gearbox import captured


def extra_hardware(folder, c):
    modules = []

    def save(name, t):
        modules.append(f"module {name}() {{\n{render(t,'true')}\n}}\n")

    for name, length in (
        ("disc", c["disc_join_length"]),
        ("deck", c["deck_screw_length"]),
        ("post", c["post_screw_length"]),
        ("front_hub", c["front_hub_screw_length"]),
    ):
        t = p.blank()
        p.add(
            t,
            "oobb_screw_countersunk",
            radius_name="m3",
            depth=length,
            mode="true",
            nut_include=False,
            overhang=False,
        )
        save("hardware_screw_" + name, t)
    t = p.blank()
    p.add(
        t,
        "oobb_nut",
        radius_name="m6",
        depth=4,
        mode="true",
        overhang=True,
        rot=[0, 0, 30],
    )
    p.cylinder(t, 3, c["hub_bolt_length"], -c["hub_bolt_length"])
    save("hardware_screw_hub", t)
    t = p.blank()
    p.cylinder(t, c["post_radius"], c["post_depth"])
    p.hole(t, 1.6, c["post_depth"])
    save("hardware_post", t)
    with (folder / "hardware.scad").open("a", encoding="utf-8") as f:
        f.write("\n".join(modules))


def coupons(c):
    result = {}
    for kind in ("guide", "eccentric", "output", "shaft"):
        t = p.blank()
        spec = c[kind + "_bearing"]
        for i, cl in enumerate((0, 0.1, 0.2)):
            r = p.blank()
            depth = spec["depth"] / 2 + 1.5
            p.cylinder(r, spec["od"] / 2 + 2, depth)
            lip = c["guide_lip_radius"] if kind == "guide" else spec["od"] / 2 - 0.5
            p.hole(r, lip, depth)
            p.hole(r, spec["od"] / 2 + cl, spec["depth"] / 2 + 0.1, z=1.4)
            p.group(t, r, [(i - 1) * (spec["od"] + 6), 0, 0])
        result["fit_" + kind + "_bearings"] = (t, 3)
    # A real opposed pair of retaining rings, to try the bearing before printing discs.
    t = p.blank()
    for i in (0, 1):
        r = p.blank()
        p.cylinder(r, 12, 3.5)
        p.hole(r, c["guide_lip_radius"], 3.5)
        p.hole(r, c["guide_hole_radius"], 2.1, z=1.4)
        p.group(t, r, [i * 28, 0, 0])
    result["fit_6700_sandwich"] = (t, 2)
    t = p.blank()
    for i, cl in enumerate((0, 0.1, 0.2)):
        trial = p.blank()
        p.cylinder(trial, c["eccentric_bearing"]["id"] / 2 - cl, 5)
        p.hole(trial, 3.25, 5)
        p.group(t, trial, [i * 22, 0, 0])
    result["fit_" + c["bearing_eccentric"] + "_journals"] = (t, 3)
    result["fit_coupling_collar"] = (captured.collar(c), 1)
    t = p.blank()
    p.add(t, "oobb_plate", width=3, height=3, depth=c["motor_plate_depth"], holes=False)
    p.hole(
        t,
        c["motor_pilot_diameter"] / 2 + c["motor_pilot_clearance"],
        c["motor_plate_depth"],
    )
    p.through(t, c["motor_positions"], c["motor_plate_depth"], countersink=True)
    result["fit_nema17_mount"] = (t, 1)
    t = p.blank()
    for i in (0, 1):
        r = p.blank()
        p.cylinder(r, 9, 4)
        if i:
            p.group(r, captured.key(c, c["hub_key_clearance"]), [0, 0, 2], typ="n")
        else:
            p.group(r, captured.key(c), [0, 0, 4])
        p.hole(r, 3.25, 7)
        p.group(t, r, [i * 24, 0, 0])
    result["fit_hub_key"] = (t, 2)
    t = p.blank()
    p.cylinder(t, c["housing_lug_radius"], c["front_retainer_depth"])
    p.cylinder(t, c["case_cover_post_radius"], c["case_cover_depth"])
    p.cut_group(
        t,
        captured.casing_socket_cuts(c, [[0, 0]]),
        [0, 0, c["housing_depth"] + c["front_retainer_depth"]],
        [180, 0, 0],
    )
    result["fit_casing_socket_well"] = (t, 1)
    return result


def labels(folder, c):
    E = c["animation_explode"]
    rows = []

    def row(name, detail, anchor, left=True):
        rows.append(
            dict(
                name=name,
                detail=detail,
                anchor=anchor,
                side="left" if left else "right",
            )
        )

    for name, label, z, factor in [
        ("motor_mount", "Motor faceplate", 7, -11),
        ("pin_rear", "Rear pin carrier", 23, -7),
        ("pin_front", "Front pin carrier", 51, 7),
        ("front_bearing_hub", "Front bearing hub", 59, 9),
        ("output_cover", "Output cover", 66, 12),
    ]:
        row(label, name, [-20, 0, z + factor * E])
    for side, word in enumerate(("a", "b")):
        for half, tag in enumerate(("lower", "upper")):
            factor = ([-4, -1] if side == 0 else [2, 5])[half]
            row(
                "Disc " + word.upper() + " " + tag,
                "rotor_" + word + "_" + tag,
                [
                    -20,
                    0,
                    c["rotor_a_z"]
                    + side * (c["rotor_thickness"] + c["disc_gap"])
                    + half * c["rotor_thickness"] / 2
                    + factor * E,
                ],
            )
    row("Output lobe ring", "output_casing", [10 * E + 44, 0, 30])
    row(
        "Output casing base", "output_base", [10 * E + 38, 0, c["case_split_z"] - 4 * E]
    )
    row("Lower wiggle shaft", "eccentric_hub_lower", [-7 * E, 0, 36 - 3 * E])
    row("Coupling drive plate", "coupling_drive", [-7 * E, 0, 28 - 5 * E])
    row("Upper wiggle shaft", "eccentric_hub_upper", [-7 * E, 0, 50 + 5 * E])
    row("Coupling nut collar", "coupling_collar", [-7 * E, 0, 19 - 7 * E])
    for name, detail, anchor in [
        (
            "Casing bearings",
            "2 x 6810 / 50 x 65 x 7",
            [29, 0, c["output_bearing_z"][1] + 10 * E],
        ),
        (
            "Eccentric bearings",
            "2 x 6704 / 20 x 27 x 4",
            [9, 0, c["eccentric_bearing_z"][1] + 3.5 * E],
        ),
        (
            "Front shaft bearing",
            "6704 / 20 x 27 x 4",
            [9, 0, c["shaft_bearing_z"][1] + 9.8 * E],
        ),
        (
            "Disc bearing rows",
            "12 x 6700 / 10 x 15 x 4",
            [21, 0, c["guide_bearing_z"][0] - 2.5 * E],
        ),
        (
            "Fixed guide bolts",
            f"6 x M6 x {c['guide_bolt_length']:g} + nuts",
            [21, 0, c["guide_bolt_head_z"] + 11 * E],
        ),
        (
            "Carrier spacers",
            f"3 steel tubes / 6 OD x 3.2 ID x {c['post_depth']:g}",
            [29, 0, 38 + 6 * E],
        ),
        ("Disc screws", "6 x M3 x 6 countersunk + nuts", [30, 0, 47 + 5.7 * E]),
        (
            "Hub joining bolt",
            "M6 x 35 + captive M6 nut",
            [-7 * E, 0, c["hub_bolt_head_z"] + 7 * E],
        ),
        ("Flange coupling", "M5 bore / flange UP at 24 mm", [0, 0, 18 - 8 * E]),
        (
            "Flange screws",
            "2 x M3 x 12 + side-loaded nuts",
            [8, 0, c["cap_screw_head_z"] - 3 * E],
        ),
        ("Motor screws", "4 x M3 x 6 countersunk", [15.5, 15.5, 4 - 10.5 * E]),
        ("NEMA 17 motor", "5 mm shaft", [0, 0, -20 - 13 * E]),
        (
            "Support fasteners",
            "3 x M3x25 rear; 3 x M3x25 posts; 3 x M3x16 hub",
            [16.5, 0, 65 + 10.5 * E],
        ),
        (
            "Casing screws",
            "4 x M3x35 socket caps; clamp cover / ring / base",
            [*c["housing_positions"][0], c["case_screw_head_z"] + 15 * E],
        ),
    ]:
        row(name, detail, anchor, False)
    from gearbox.annotations import settings

    view = settings(c)

    def screen_y(r):
        x, y, z = [a - b for a, b in zip(r["anchor"], view["target"])]
        ax, ay, az = map(math.radians, view["rotation"])
        x, y = x * math.cos(az) + y * math.sin(az), -x * math.sin(az) + y * math.cos(az)
        x, z = x * math.cos(ay) - z * math.sin(ay), x * math.sin(ay) + z * math.cos(ay)
        return y * math.cos(ax) + z * math.sin(ax)

    entries = []
    for side in ("left", "right"):
        rr = sorted([r for r in rows if r["side"] == side], key=screen_y, reverse=True)
        for i, r in enumerate(rr):
            entries.append(
                [
                    r["name"],
                    r["detail"],
                    r["anchor"],
                    side == "left",
                    175 - i * 350 / (len(rr) - 1),
                ]
            )
    write(
        folder / "exploded_labels.scad",
        "annotation_rows="
        + json.dumps(entries)
        + ";\n"
        + Path(__file__)
        .with_name("annotations.scad.template")
        .read_text(encoding="utf-8"),
    )
    write(folder / "part_names.json", json.dumps(rows, indent=2))
    write(
        folder / "part_names.md",
        "# Version 4 part names\n\n| Name | File / hardware |\n| --- | --- |\n"
        + "\n".join(f"| {r['name']} | {r['detail']} |" for r in rows),
    )
    return view


def export_gearbox(folder, model, save_type="none"):
    folder = Path(folder)
    if (folder / "SEALED.json").exists():
        raise ValueError("Sealed release")
    folder.mkdir(parents=True, exist_ok=True)
    c = model["config"]
    pieces = model["pieces"]
    # Remove only obsolete generated artifacts listed in the previous manifest.
    # The complete previous design is preserved under outputs/v4_before_captured_6700.
    if (folder / "gearbox.json").exists():
        old = json.loads((folder / "gearbox.json").read_text(encoding="utf-8"))
        obsolete = set(old.get("pieces", {})) - set(pieces)
        obsolete.update(set(old.get("fit_coupons", {})) - set(coupons(c)))
        for name in obsolete:
            for ext in (".scad", ".stl"):
                (folder / (name + ext)).unlink(missing_ok=True)
    lengths = export_fasteners(folder, c)
    extra_hardware(folder, c)
    for name, item in pieces.items():
        write(
            folder / (name + ".scad"),
            "// Generated via working_scad. Edit populate/builders, not this file.\n$fn=96;\nmodule "
            + name
            + "(){\n"
            + render(item["thing"])
            + "\n}\n"
            + name
            + "();\n",
        )
    uses = "".join("use <" + name + ".scad>\n" for name in pieces)
    write(
        folder / "3dpr.scad",
        uses
        + "$fn=96;\n"
        + "\n".join(
            f"translate({json.dumps(i['pos'])}) {i['part']}();" for i in model["layout"]
        ),
    )
    fits = coupons(c)
    for name, (thing, _) in fits.items():
        write(folder / (name + ".scad"), "$fn=96;\n" + render(thing))
    assignments = "\n".join(
        k + "=" + json.dumps(v) + ";"
        for k, v in c.items()
        if isinstance(v, (str, int, float, list, bool))
    )
    write(
        folder / "assembly.scad",
        uses
        + "use <hardware.scad>\n"
        + assignments
        + "\n"
        + Path(__file__)
        .with_name("captured.scad.template")
        .read_text(encoding="utf-8"),
    )
    view = view_settings(c)
    cam = f"$vpt={json.dumps(view['target'])};\n$vpr={json.dumps(view['rotation'])};\n$vpd={view['distance']};\n"
    examples = {
        "animation": f"input_turns = {c['reduction']}*$t; explode={view['explode']};\n"
        + cam,
        "motion": f"input_turns={c['reduction']}*$t; cutaway=true;\n",
        "section": "cutaway=true;\n",
        "fit_check": "fit_only=true;\n",
        "guide_rollers": "guide_only=true;input_turns=$t;\n",
        "motor_drive": "drive_only=true;cutaway=true;\n",
        "grub_access": "grub_access_view=true;\n",
        "grub_access_check": 'check_kind="grub";\n',
        "nut_loading": "nut_loading_view=true;\n",
        "flange_nut_loading": "flange_nut_loading_view=true;\n",
    }
    checks = [
        "rear_bearing",
        "deck",
        "casing",
        "casing_base",
        "casing_ring",
        "lower_disc",
        "upper_unit",
        "drive",
        "lower_shaft",
        "upper_disc_bench",
        "guide_bearing",
        "disc_upper",
        "guide_bolt",
        "front_plate",
        "front_hub",
        "front_bearing",
        "cover",
        "casing_screws",
        "nuts",
        "flange_nuts",
        "hub_nut",
    ]
    for name in checks:
        examples[name + "_installation_check"] = (
            f'check_kind="{name}"; installation_shift=0;\n'
        )
    for name, controls in examples.items():
        write(folder / (name + ".scad"), controls + "include <assembly.scad>\n")
    write(
        folder / "wrong_phase_check.scad",
        '// A solid interference here confirms the shaft cannot be fitted in the wrong phase.\ncheck_kind="wrong_phase";\ninclude <assembly.scad>\n',
    )
    # Old assembly checks no longer describe this split-shaft sequence.
    keep = {n + "_installation_check.scad" for n in checks}
    for old in folder.glob("*_installation_check.scad"):
        if old.name not in keep:
            old.unlink()
    (folder / "installation_check.scad").unlink(missing_ok=True)
    annotated = labels(folder, c)
    acam = f"$vpt={json.dumps(annotated['target'])};\n$vpr={json.dumps(annotated['rotation'])};\n$vpd={annotated['distance']};\n"
    write(
        folder / "exploded.scad",
        f"explode={view['explode']};\n"
        + acam
        + "include <assembly.scad>\ninclude <exploded_labels.scad>\n",
    )
    bom = hardware_list(c)
    for name, qty, length in [
        ("M3 countersunk disc screws + nuts", 6, c["disc_join_length"]),
        ("M3 countersunk rear-deck screws + nuts", 3, c["deck_screw_length"]),
        ("M3 countersunk post screws + nuts", 3, c["post_screw_length"]),
        ("M3 countersunk front-hub screws + nuts", 3, c["front_hub_screw_length"]),
        ("M6 hex hub joining bolt + nut", 1, c["hub_bolt_length"]),
    ]:
        bom.append(dict(item=name, quantity=qty, length=length))
    bom.append(
        dict(
            item="Steel carrier spacer tubes",
            quantity=3,
            od=2 * c["post_radius"],
            id=3.2,
            length=c["post_depth"],
        )
    )
    manifest = dict(
        schema=4,
        reduction=c["reduction"],
        parameters=c,
        pieces={
            n: {k: v for k, v in item.items() if k != "thing"}
            for n, item in pieces.items()
        },
        print_layout=model["layout"],
        hardware=bom,
        preview_screw_lengths_mm=lengths,
        fit_coupons={n: count for n, (_, count) in fits.items()},
        installation_checks=checks,
        kinematics=dict(
            output_member="outer_casing",
            output_direction="same_as_input",
            disc_lobes=c["disc_lobes"],
            casing_contacts=c["ring_pin_count"],
            eccentric_phase_degrees=[0, 180],
            fixed_members=[
                "motor_mount",
                "pin_rear",
                "pin_front",
                "front_bearing_hub",
                "M6 guides",
                "carrier spacer posts",
            ],
            moving_guide_bearings=True,
        ),
        preview_hardware_counts=dict(
            bearings=17,
            guide_hex_bolts=6,
            hub_joining_bolts=1,
            nuts_m6=7,
            nuts_m3=21,
            countersunk_screws=19,
            casing_socket_cap_screws=4,
            flange_screws=2,
            carrier_spacers=3,
            guide_race_spacers=0,
            couplings=1,
            motors=1,
            coupling_set_screws=2,
        ),
    )
    write(folder / "gearbox.json", json.dumps(manifest, indent=2) + "\n")
    write(folder / "README.md", readme(c, lengths))
    for name in ("validation.json", "motion_validation.json", "animation_render.json"):
        write(
            folder / name,
            json.dumps(
                dict(
                    status="not_run",
                    reason="Generated geometry needs validation/rendering",
                )
            )
            + "\n",
        )
    if save_type != "none":
        from gearbox.captured_validate import validate

        validate(folder)
    if c.get("render_animation", False):
        from gearbox.animation import render_animation

        render_animation(folder, **c)


def readme(c, lengths):
    return f"""# Version 4: captured 6700 bearings / raised 6810 casing

Generated through working_oomp_populate -> working_oomp -> working_scad.
Edit populate overrides or gearbox/captured.py; defaults accept **kwargs.

{c['reduction']}:1, {c['disc_lobes']} lobes, eccentricity {c['radius_offset']:g} mm.
Casing outside diameter {2*c['housing_radius']:g} mm; cover height {c['housing_depth']+c['front_retainer_depth']:g} mm above motor face.
The flange remains UP at the {c['motor_shaft_length']:g} mm shaft tip. Rear 6810 sits above the motor.

15 printed parts. Each disc has two {c['disc_half_depth']:g} mm halves capturing six
6700 bearings (10 x 15 x 4). Their outer races move with the disc; their inner
bores orbit smooth M6 shanks, leaving {c['guide_running_clearance']:.2f} mm radial clearance.
The two eccentric bearings and the front shaft bearing are 6704 (20 x 27 x 4).
Both casing bearings are 6810 (50 x 65 x 7).
The central and guide-bearing outer races have {c['central_to_guide_race_gap']:.2f} mm nominal
radial separation. Their seat pockets merge; no plastic wall separates them at
the bearing midplane. The retaining lips on the two disc faces hold the bearing pack.

Four M3x{c['housing_screw_length']:g} SOCKET CAP screws close the casing. The nuts remain
at the bottom ({c['case_nut_bottom']:g} mm above motor face). Screw heads sit at
{c['case_screw_head_z']:g} mm, inside long cover bosses with OOBB clearance="top".
Use a straight hex key down the top channels. The maximum specified casing
screw length is 35 mm; the cover's bosses descend into matching casing sockets
so the recessed heads still clamp the cover. Overall cover height is unchanged.

The output casing has THREE pieces: output_base, output_casing (the lobe ring),
and output_cover. The joint is at {c['case_split_z']:g} mm above the motor face.
The {c['case_base_depth']:g} mm base prints joint-face down with its rear-bearing
pocket upward; flip it for assembly. The {c['case_ring_depth']:g} mm lobe ring
prints upright. The four existing M3x35 screws pass through all three parts,
with the captive nuts retained in the base. No additional fasteners are needed.
The flat joint is located by the four screw holes and clamped between the bearing
holder and cover; keep the ring concentric while tightening the screws evenly.

The six M6x{c['guide_bolt_length']:g} guides need smooth shanks at least
{c['guide_bolt_head_z']-c['guide_bearing_z'][0]+2:g} mm long below the head.
Use partially threaded bolts; threads must not enter either bearing bore.
Three steel spacers, 6 OD x 3.2 ID x {c['post_depth']:g} mm, maintain carrier spacing.
They pass through separate oversized orbit-clearance holes, not the 6700 bores.
No inner-race spacers clamp the moving guide bearings.

Assembly:
1. Print fit coupons first: 6700 seats, sandwich lips, 6704 journals/seats,
   6810 seats, NEMA mount, coupling collar and shaft key.
2. Load the three motor-faceplate M3 nuts underneath. Fix faceplate to motor
   with four M3x6 countersunk screws. Fit rear 6810 from above.
3. Load the collar's TWO M3 nuts through its straight outward-facing slots.
   Put collar and flange-up coupling on the shaft. Tighten grub screws now,
   with the rear deck and casing absent (grub_access.scad shows the tools).
4. Load casing-base nuts from below, lower the base onto the rear 6810,
   then lower the lobe ring onto its flat joint face, aligning all four screw holes.
   Load rear-carrier M6 and post M3 nuts from underneath, then fit the rear
   carrier with three M3x25 screws. Its central bore clears the coupling/collar.
5. Load the central M6 nut underneath the coupling drive plate; place it on the
   coupling flange and install two M3x12 socket screws into the collar nuts.
   Lower the lower wiggle shaft onto the drive plate's key. Its uninterrupted
   bearing journal has no coupling-screw access slots through it.
6. Assemble each disc around six 6700s and one 6704 on the bench. Use three
   M3x6 countersunk screws/nuts per disc; upper halves print pocket-up and flip
   for assembly. Keep the matching A/B half pairs and common XY orientation.
7. Lower disc A over the lower shaft from above. Fit disc B onto the upper
   shaft from below, then lower that unit onto the keyed lower shaft.
8. Insert three steel carrier spacers through their separate tracks. Fit front
   carrier, three M3x25 post screws and six M6x40 guide bolts. Fit the M6x35
   central shaft bolt; its head is recessed inside the front journal.
9. Load the front bearing hub's three nuts into the underside of the front
   carrier BEFORE step 8. Fit hub and front 6704 with three M3x16 screws.
   Lower the front 6810 over the hub, then fit the output cover and four
   M3x{lengths['housing']:g} socket-cap casing screws through the deep top-access channels.
   Turn by hand before motor power.

3dpr.scad/.stl contains all printed pieces. Individual files use the part names
in part_names.md. exploded.scad/.png is annotated; animation.scad/.gif/.mp4 shows
the two orbiting bearing rows and all hardware. *_installation_check.scad files
render only interference along the stated assembly sequence.

This is a narrower, taller alternative to the preserved 6814 layout. CAD checks
verify nominal geometry; printed tolerances, bearing retention and load capacity
still need the supplied coupons and a physical prototype. The 6700 retaining
lips overlap the outermost 0.5 mm of the bearing; confirm they clear the shields
of your actual bearings. Do not clamp a shield or inner race with the disc halves.
"""
