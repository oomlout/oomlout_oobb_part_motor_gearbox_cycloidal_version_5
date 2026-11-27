"""Version 4: opposed cycloidal discs, a rotating output casing and fixed NEMA 17 pin mount."""

import copy
import math
import oobb
from gearbox import lobe


def polar(radius, angle):
    a = math.radians(angle)
    return [radius * math.cos(a), radius * math.sin(a)]


def ring(radius, count, phase=0):
    return [polar(radius, phase + i * 360 / count) for i in range(count)]


def bearing_spec(name):
    objects = oobb.oe(shape="oobb_bearing", bearing_size=name, type="p", pos=[0, 0, 0])
    while isinstance(objects, list):
        objects = objects[0]
    return {"id": objects["id"] * 2, "od": objects["od"] * 2, "depth": objects["depth"]}


def default_parameters():
    """Common motor, coupler and legacy-layout defaults, without derived geometry."""
    return dict(
        reduction=20,
        radius_offset=1.75,
        lobe_radius=2.0,
        lobe_eccentricity_ratio=0.91,
        bearing_eccentric="6706",
        bearing_shaft="6706",
        bearing_output="6814",
        bearing_guide="MR106",
        guide_bolt_radius_name="m6",
        guide_spacer_radius=3.425,
        guide_spacer_bore=3.1,
        guide_head_depth=4.0,
        guide_head_clearance=0.2,
        rotor_thickness=7.0,
        disc_gap=0.5,
        axial_clearance=0.5,
        flange_depth=13.0,
        flange_web=2.0,
        guide_pin_diameter=6.0,
        guide_pin_pitch_radius=27.95,
        guide_head_wall=1.0,
        guide_pin_count=6,
        guide_pin_clearance=0.15,
        bearing_seat_clearance=0.1,
        bearing_endplay=0.1,
        journal_clearance=0.1,
        lobe_clearance=0.2,
        minimum_wall=2.0,
        motor_plate_depth=4.0,
        motor_hole_pitch=31.0,
        motor_pilot_diameter=22.0,
        motor_pilot_clearance=0.2,
        motor_shaft_length=24.0,
        motor_body_depth=40.0,
        motor_screw_length=6.0,
        shaft_radius_name="m5",
        # 5 mm bore flange coupler: reference project's flange/dimension.csv.
        coupling_diameter=22.0,
        coupling_barrel_diameter=10.0,
        coupling_length=12.0,
        coupling_barrel_length=10.0,
        coupling_pitch_diameter=16.0,
        coupling_flange_hole_diameter=3.0,
        coupling_face_clearance=0.2,
        motor_pilot_height=2.0,
        # User measured grub centres: 5 mm below the top of the 10 mm barrel.
        coupling_grub_from_barrel_top=5.0,
        coupling_grub_angles=[45, 135],
        coupling_service_angle=0.0,
        coupling_screw_length=10.0,
        coupling_nut_rotation_offset=180.0,
        coupling_nut_hex_rotation=30.0,
        coupling_nut_side_clearance=0.1,
        drive_roof_depth=2.0,
        drive_flange_clearance=0.2,
        drive_cavity_clearance=0.3,
        rear_bearing_lift=0.3,
        casing_bottom_clearance=0.5,
        case_nut_plate_clearance=3.0,
        grub_access_radius=1.7,
        samples_per_lobe=240,
        profile_tolerance=0.0005,
        front_retainer_depth=2.0,
        rotor_central_wall=1.5,
        motor_body_width=42.0,
        motor_body_clearance=0.4,
        guide_thread_allowance=18.0,
    )


def resolve(kwargs):
    if kwargs.get("architecture") == "captured_6810":
        from gearbox.captured import resolve as captured_resolve

        return captured_resolve(kwargs)
    c = copy.deepcopy(kwargs)
    # Keep older populate overrides meaningful while naming the fixed pins clearly.
    for old, new in (
        ("output_pin_diameter", "guide_pin_diameter"),
        ("output_pin_pitch_radius", "guide_pin_pitch_radius"),
        ("output_pin_count", "guide_pin_count"),
        ("output_pin_clearance", "guide_pin_clearance"),
    ):
        if old in c:
            c.setdefault(new, c[old])
    defaults = default_parameters()
    for k, v in defaults.items():
        c.setdefault(k, v)
    if float(c["reduction"]) != int(c["reduction"]) or c["reduction"] < 3:
        raise ValueError("reduction must be an integer >= 3")
    c["reduction"] = int(c["reduction"])
    c["ring_pin_count"] = c["reduction"]
    c["disc_lobes"] = c["reduction"] - 1
    c["output_member"] = "outer_casing"
    c["output_direction"] = "same_as_input"
    for key in [
        "radius_offset",
        "lobe_radius",
        "rotor_thickness",
        "disc_gap",
        "axial_clearance",
        "flange_depth",
        "flange_web",
        "motor_plate_depth",
        "guide_pin_diameter",
    ]:
        if c[key] <= 0:
            raise ValueError(key + " must be positive")
    if c["shaft_radius_name"] != "m5":
        raise ValueError("Version 4 input interface is M5")
    if not isinstance(c["samples_per_lobe"], int) or c["samples_per_lobe"] < 60:
        raise ValueError("samples_per_lobe must be an integer >= 60")
    if not isinstance(c["guide_pin_count"], int) or c["guide_pin_count"] < 3:
        raise ValueError("guide_pin_count must be an integer >= 3")
    for k in [
        "lobe_clearance",
        "guide_pin_clearance",
        "bearing_seat_clearance",
        "journal_clearance",
        "bearing_endplay",
    ]:
        if c[k] < 0:
            raise ValueError(k + " cannot be negative")
    if not 0 < c["profile_tolerance"] <= 0.05:
        raise ValueError("profile_tolerance must be positive and at most 0.05 mm")
    c["eccentric_bearing"] = bearing_spec(c["bearing_eccentric"])
    c["shaft_bearing"] = bearing_spec(c["bearing_shaft"])
    c["output_bearing"] = bearing_spec(c["bearing_output"])
    c["guide_bearing"] = bearing_spec(c["bearing_guide"])
    c.setdefault("rear_bearing_shoulder_radius", c["output_bearing"]["id"] / 2 + 1.5)
    # Flats face the motor's sides so the four diagonal nuts clear its body.
    c["guide_nut_rotations"] = [30.0] * c["guide_pin_count"]
    if "bearing_drive" in c:
        raise ValueError("The integrated motor faceplate uses no drive bearing")
    e = c["radius_offset"]
    n = c["ring_pin_count"]
    wall = c["minimum_wall"]
    pin = c["lobe_radius"]
    k = c["lobe_eccentricity_ratio"]
    if not 0 < k < 0.95:
        raise ValueError("lobe_eccentricity_ratio must be between 0 and 0.95")
    c["guide_hole_radius"] = c["guide_bearing"]["od"] / 2 + e + c["guide_pin_clearance"]
    c["guide_strategy"] = "fixed_bearing_centres_in_oversize_disc_tracks"
    limits = {
        "lobe_shape": n * e / k,
        "rotor_features": c["guide_pin_pitch_radius"]
        + c["guide_hole_radius"]
        + wall
        + e
        + pin
        + c["lobe_clearance"],
        "bearing_package": c["output_bearing"]["od"] / 2
        + wall
        + c["bearing_seat_clearance"]
        + pin
        + 0.5,
        "pin_spacing": (pin + wall / 2) / math.sin(math.pi / n),
    }
    automatic = (
        "pitch_radius" not in c
        or c.get("radius_calculation", {}).get("mode") == "automatic"
    )
    if automatic:
        c["pitch_radius"] = math.ceil(max(limits.values()) * 2) / 2
    c["radius_calculation"] = {
        "mode": "automatic" if automatic else "explicit_override",
        "limits_mm": limits,
        "limiting_feature": max(limits, key=limits.get),
        "selected_pitch_radius": c["pitch_radius"],
    }
    if c["pitch_radius"] <= n * e:
        raise ValueError("pitch_radius must exceed pin_count * eccentricity")
    c["ring_positions"] = ring(c["pitch_radius"], n)
    c["guide_positions"] = ring(c["guide_pin_pitch_radius"], c["guide_pin_count"], 30)
    # The orbit adds another eccentricity to the disc's maximum radius.
    # Deeper lobes need space between contacts, beyond the pitch circle.
    c["casing_bore_radius"] = c["pitch_radius"] + max(0, 2 * e - pin)
    if c["pitch_radius"] + pin - c["casing_bore_radius"] < 0.4:
        raise ValueError("Casing contacts need at least 0.4 mm radial attachment")
    c.setdefault(
        "housing_mount_offset",
        math.ceil(
            (c["casing_bore_radius"] + wall + oobb.gv("hole_radius_m3", "3dpr"))
            / math.sqrt(2)
            * 2
        )
        / 2,
    )
    s = c["housing_mount_offset"]
    c["housing_positions"] = [[s, s], [-s, s], [-s, -s], [s, -s]]
    s = c["motor_hole_pitch"] / 2
    c["motor_positions"] = [[s, s], [-s, s], [-s, -s], [s, -s]]
    c["housing_radius"] = c["pitch_radius"] + c["lobe_radius"] + 3
    c["housing_width"] = math.ceil((2 * c["housing_radius"] + 1) / 15)
    c["carrier_journal_radius"] = c["output_bearing"]["id"] / 2 - c["journal_clearance"]
    head_r = oobb.gv("nut_radius_" + c["guide_bolt_radius_name"], "3dpr")
    c["guide_heads_nested"] = (
        c["guide_pin_pitch_radius"] + head_r + c["guide_head_wall"]
        <= c["carrier_journal_radius"]
    )
    c["carrier_radius"] = c["output_bearing"]["id"] / 2 + 3
    c["bearing_pass_radius"] = c["carrier_radius"] + 0.5
    c["bearing_cup_radius"] = (
        c["output_bearing"]["od"] / 2 + c["bearing_seat_clearance"] + wall
    )
    c["bearing_cup_depth"] = c["flange_depth"] - c["flange_web"] + 0.2
    # Coordinates are measured from the motor face. The flange ends at the
    # shaft tip; the close disc stack is positioned immediately below it.
    c["motor_face_z"] = 0.0
    c["motor_plate_top"] = c["motor_plate_depth"]
    c["coupling_top"] = c["motor_shaft_length"]
    c["coupling_z"] = c["coupling_top"] - c["coupling_length"]
    c["coupling_flange_top"] = c["coupling_top"]
    c["coupling_flange_z"] = c["coupling_z"] + c["coupling_barrel_length"]
    c["coupling_grub_z"] = c["coupling_flange_z"] - c["coupling_grub_from_barrel_top"]
    c["coupling_orientation"] = "flange_up_at_motor_shaft_tip"
    c["coupling_hole_positions"] = ring(c["coupling_pitch_diameter"] / 2, 4)
    c["coupling_positions"] = c["coupling_hole_positions"][1::2]
    c["coupling_nut_rotations"] = [
        math.degrees(math.atan2(y, x)) + c["coupling_nut_rotation_offset"]
        for x, y in c["coupling_positions"]
    ]
    c["rotor_b_z"] = c["coupling_flange_z"] - 0.5 - c["rotor_thickness"]
    c["rotor_a_z"] = c["rotor_b_z"] - c["disc_gap"] - c["rotor_thickness"]
    c["rear_support_top"] = c["rotor_a_z"] - c["axial_clearance"]
    c["housing_depth"] = (
        c["rotor_b_z"] + c["rotor_thickness"] + c["axial_clearance"] + c["flange_depth"]
    )
    H, f, w = c["housing_depth"], c["flange_depth"], c["flange_web"]
    c["rear_bearing_top"] = (
        c["rotor_a_z"] - c["minimum_wall"] - c["bearing_endplay"] - 0.6
    )
    c["rear_bearing_bottom"] = c["rear_bearing_top"] - c["output_bearing"]["depth"]
    c["mount_rim_top"] = c["rear_bearing_bottom"] - c["rear_bearing_lift"]
    c["mount_bottom_z"] = c["mount_rim_top"] - 6.0
    c["integrated_mount_depth"] = c["rear_support_top"] - c["mount_bottom_z"]
    c["casing_bottom_z"] = c["mount_rim_top"] + c["casing_bottom_clearance"]
    c["rear_retainer_depth"] = -c["casing_bottom_z"]
    c["output_bearing_z"] = [
        (c["rear_bearing_bottom"] + c["rear_bearing_top"]) / 2,
        H - f + w + c["output_bearing"]["depth"] / 2 + c["bearing_endplay"],
    ]
    c["shaft_bearing_z"] = [
        0,
        H - c["bearing_endplay"] - c["shaft_bearing"]["depth"] / 2,
    ]
    seat = c["eccentric_bearing"]["depth"] + 2 * c["bearing_endplay"]
    # Opposed axial seats allow one-piece shaft assembly from opposite ends.
    c["eccentric_bearing_z"] = [
        c["rotor_a_z"] + seat / 2,
        c["rotor_b_z"] + c["rotor_thickness"] - seat / 2,
    ]
    c["eccentric_journal_z"] = [
        c["rotor_a_z"],
        c["rotor_b_z"] + c["rotor_thickness"] - seat,
    ]
    c["eccentric_journal_depth"] = seat
    c["eccentric_journal_radius"] = (
        c["eccentric_bearing"]["id"] / 2 - c["journal_clearance"]
    )
    c["eccentric_shoulder_radius"] = c["eccentric_bearing"]["id"] / 2 + 0.5
    c["eccentric_exit_radius"] = c["eccentric_bearing"]["id"] / 2 + 1
    c["shaft_journal_radius"] = c["shaft_bearing"]["id"] / 2 - c["journal_clearance"]
    c["shaft_exit_radius"] = c["shaft_bearing"]["od"] / 2 - 1.5
    c["front_journal_bottom"] = (
        c["shaft_bearing_z"][1] - c["shaft_bearing"]["depth"] / 2 - 0.1
    )
    c["guide_bearing_z"] = [
        c["rotor_a_z"] + c["rotor_thickness"] / 2,
        c["rotor_b_z"] + c["rotor_thickness"] / 2,
    ]
    gd = c["guide_bearing"]["depth"]
    c["guide_spacer_z"] = [
        c["rear_support_top"],
        c["guide_bearing_z"][0] + gd / 2,
        c["guide_bearing_z"][1] + gd / 2,
    ]
    c["guide_spacer_depths"] = [
        c["guide_bearing_z"][0] - gd / 2 - c["rear_support_top"],
        c["guide_bearing_z"][1] - c["guide_bearing_z"][0] - gd,
        H - f - c["guide_bearing_z"][1] - gd / 2,
    ]
    c["guide_bolt_head_z"] = H - c["guide_head_depth"] - c["guide_head_clearance"]
    c["guide_nut_loading"] = "bottom"
    # Smaller roller tracks move the bolts inward. Their nuts then sit above
    # the motor face, loaded from the underside before mounting the motor.
    c.setdefault("guide_nut_roof", 1.0)
    c["guide_nut_top"] = (
        c["rear_support_top"] - c["guide_nut_roof"]
        if c["guide_heads_nested"]
        else c["rear_bearing_bottom"] - 0.5
    )
    c["guide_nut_bottom"] = c["guide_nut_top"] - oobb.gv(
        "nut_depth_" + c["guide_bolt_radius_name"], "true"
    )
    c["disc_phase_degrees"] = [0, -180 / c["disc_lobes"]]
    c["eccentric_phase_degrees"] = [0, 180]
    target_nut = max(
        c["casing_bottom_z"] + 0.2, c["mount_rim_top"] + c["case_nut_plate_clearance"]
    )
    case_head = H + c["front_retainer_depth"]
    c["case_nut_bottom"] = case_head - 5 * math.floor((case_head - target_nut) / 5)
    c["drive_start"] = c["rotor_a_z"]
    # These are clamped faces, so they meet the flange without axial gaps.
    c["drive_end"] = c["coupling_flange_z"]
    c["drive_roof_top"] = c["coupling_flange_z"] - 1.5  # side-loaded nut roof
    c["drive_roof_z"] = c["drive_roof_top"] - oobb.gv("nut_depth_m3", "true")
    c["drive_cavity_radius"] = (
        c["coupling_barrel_diameter"] / 2 + c["drive_cavity_clearance"]
    )
    c["drive_journal_radius"] = c["eccentric_journal_radius"]
    c["drive_shoulder_radius"] = c["eccentric_shoulder_radius"] + e
    c["rear_carrier_bore"] = c["motor_pilot_diameter"] / 2 + c["motor_pilot_clearance"]
    c["cap_start"] = c["coupling_flange_z"] + 0.2
    c["cap_roof_bottom"] = c["coupling_top"]
    c["cap_screw_head_z"] = c["cap_roof_bottom"] + c["drive_roof_depth"]
    c["hub_upper_end"] = H + 0.2
    c["hub_upper_start"] = c["cap_start"]
    c["hub_retainer_outer_radius"] = c["shaft_journal_radius"]
    c["hub_split_z"] = c["drive_end"]
    c["gap"] = H
    c["thickness_outer_rotor"] = c["flange_depth"]  # renderer envelope compatibility
    c.setdefault("animation_explode", 12)
    c.setdefault("animation_size", [960, 1600])
    c.setdefault("animation_camera_distance", 1450)
    c.setdefault("print_width", 240)
    if c["rotor_thickness"] < seat + 1.2:
        raise ValueError("Rotor too thin for eccentric bearing and shoulder")
    if (
        2 * c["guide_pin_pitch_radius"] * math.sin(math.pi / c["guide_pin_count"])
        < 2 * c["guide_hole_radius"] + wall
    ):
        raise ValueError("Too many guide holes for the chosen pitch circle")
    if (
        c["guide_pin_pitch_radius"] - c["guide_hole_radius"]
        < c["eccentric_bearing"]["od"] / 2
        + c["bearing_seat_clearance"]
        + c["rotor_central_wall"]
    ):
        raise ValueError(
            "Output holes leave insufficient wall around eccentric bearing"
        )
    root = c["pitch_radius"] - e - pin - c["lobe_clearance"]
    if c["guide_pin_pitch_radius"] + c["guide_hole_radius"] + wall > root:
        raise ValueError("Output holes leave insufficient rotor rim")
    head_r = oobb.gv("nut_radius_" + c["guide_bolt_radius_name"], "3dpr")
    head_envelope = c["guide_pin_pitch_radius"] + head_r
    if head_envelope + c["guide_head_wall"] > c["carrier_radius"]:
        raise ValueError("Output fastener heads break out of carrier journal")
    if c["guide_bearing"]["id"] != c["guide_pin_diameter"] or c["guide_bearing"][
        "id"
    ] != 2 * oobb.gv("hole_radius_" + c["guide_bolt_radius_name"], "true"):
        raise ValueError("Guide bearing bore must match the smooth guide-bolt diameter")
    if c["rotor_thickness"] < gd + 0.8 or min(c["guide_spacer_depths"]) <= 0:
        raise ValueError(
            "Guide bearings must be recessed into the discs with positive race spacer lengths"
        )
    # EZO MR106ZZ abutment diameter is 6.8..6.9 mm; 8 mm 606 spacers
    # would rub its shields. Keep the steel spacer specification explicit.
    spacer_min, spacer_max = (
        (3.4, 3.45) if c["bearing_guide"].lower() == "mr106" else (3.2, 4.0)
    )
    if not (
        c["guide_spacer_bore"] < c["guide_spacer_radius"]
        and spacer_min <= c["guide_spacer_radius"] <= spacer_max
    ):
        raise ValueError(
            "Guide spacers must contact only the selected bearing's inner races"
        )
    if c["bearing_pass_radius"] + 2 > c["output_bearing"]["od"] / 2:
        raise ValueError("Output bearing shoulder too narrow")
    if c["disc_gap"] < 0.4:
        raise ValueError("Discs need at least 0.4 mm axial gap")
    if c["rear_support_top"] < c["motor_plate_depth"] + 1.5:
        raise ValueError(
            "Shaft too short for the close disc stack above the motor plate"
        )
    if c["mount_bottom_z"] >= 0:
        raise ValueError(
            "Shaft too long for the recessed motor bracket; revise the mounting skirt"
        )
    if c["coupling_z"] < c["motor_pilot_height"] + c["coupling_face_clearance"]:
        raise ValueError("Coupler barrel reaches the motor pilot")
    if c["eccentric_bearing"]["id"] / 2 < c["coupling_diameter"] / 2 + e + 0.3:
        raise ValueError("Eccentric bearings must pass over the installed flange")
    if (
        c["shaft_journal_radius"]
        < c["coupling_diameter"] / 2 + c["drive_cavity_clearance"] + wall
    ):
        raise ValueError("Front bearing cap needs wall around the flange")
    if not c["guide_heads_nested"] and (
        c["guide_bolt_head_z"] - 0.2
        < c["output_bearing_z"][1] + c["output_bearing"]["depth"] / 2
    ):
        raise ValueError(
            "Guide heads must clear the front output bearing radially or axially"
        )
    if c["guide_heads_nested"]:
        if c["guide_nut_bottom"] < 0.3 or c["guide_nut_roof"] < 1:
            raise ValueError(
                "Nested guide nuts need motor-face clearance and a retaining roof"
            )
        if any(
            max(abs(x), abs(y)) - c["guide_pin_diameter"] / 2
            < c["motor_body_width"] / 2 + 0.2
            for x, y in c["guide_positions"]
        ):
            raise ValueError("Guide bolt tips need clearance outside the motor body")
    elif c["guide_nut_top"] > c["rear_bearing_bottom"] - 0.2:
        raise ValueError("Outer guide nuts must sit below the rear output bearing")
    if c["rear_bearing_top"] + c["bearing_endplay"] + wall >= c["rotor_a_z"]:
        raise ValueError("Rear bearing cup reaches the lower disc")
    if not 0 < c["coupling_grub_from_barrel_top"] < c["coupling_barrel_length"]:
        raise ValueError("Grub screw centre must lie within coupling barrel")
    screw_tip = c["cap_screw_head_z"] - c["coupling_screw_length"]
    if screw_tip > c["drive_roof_z"] or screw_tip < c["drive_start"]:
        raise ValueError("Coupling screws must engage the nuts and remain within shaft")
    if not 0 < c["motor_screw_length"] - c["motor_plate_depth"] <= 2.5:
        raise ValueError("NEMA screws must engage 0..2.5 mm")
    if c["flange_depth"] - c["flange_web"] < c["output_bearing"]["depth"] + 0.8:
        raise ValueError("Flange journal too short for output bearing")
    if (
        math.sqrt(2) * c["housing_mount_offset"]
        - oobb.gv("hole_radius_m3", "3dpr")
        - c["casing_bore_radius"]
        < wall
    ):
        raise ValueError("Housing bolts break through stator inner wall")
    if math.sqrt(2) * c["housing_mount_offset"] > c["housing_radius"] + 2:
        raise ValueError("Housing mounting lugs disconnected")
    if c["print_width"] < 2 * c["housing_radius"]:
        raise ValueError("print_width smaller than housing")
    return c


def blank():
    return {"components": [], "components_objects": [], "components_string": []}


def add(t, shape, typ="p", pos=None, **kw):
    oobb.append_full(t, shape=shape, type=typ, pos=pos or [0, 0, 0], **kw)


def cylinder(t, radius, depth, z=0, typ="p", xy=(0, 0)):
    add(t, "oobb_cylinder", typ, [*xy, z], radius=radius, depth=depth, zz="bottom")


def hole(t, radius, depth, xy=(0, 0), z=-0.01):
    add(t, "oobb_hole", "n", [*xy, z], radius=radius, depth=depth + 0.02)


def through(t, positions, depth, size="m3", countersink=False, nut=False):
    for xy in positions:
        if countersink:
            add(
                t,
                "oobb_screw_countersunk",
                "n",
                [*xy, depth],
                radius_name=size,
                depth=depth + 0.02,
                zz="top",
                nut_include=False,
                overhang=False,
            )
        else:
            add(t, "oobb_hole", "n", [*xy, -0.01], radius_name=size, depth=depth + 0.02)
        if nut:
            add(
                t,
                "oobb_nut",
                "n",
                [*xy, depth + 0.1],
                radius_name=size,
                depth=oobb.gv("nut_depth_" + size, "true") + 0.2,
                zz="top",
                overhang=True,
            )


def layout(parts, **kwargs):
    c = kwargs
    placements = []
    x = 0
    y = 0
    row = 0
    gap = c.get("print_gap", 8.0)
    for name, p in sorted(parts.items(), key=lambda item: -item[1]["width"]):
        for i in range(p["quantity"]):
            w = p["width"]
            if x + w > c.get("print_width", 240.0) and x:
                x = 0
                y += row + gap
                row = 0
            placements.append(
                {
                    "part": name,
                    "copy": i + 1,
                    "pos": [x + w / 2, y + w / 2, 0],
                    "width": w,
                }
            )
            x += w + gap
            row = max(row, w)
    return placements


def group(t, child, pos=(0, 0, 0), rot=(0, 0, 0), typ="p"):
    """Nested OOBB CSG preserves local cuts before union with other features."""
    t["components"].append(
        {
            "type": "rotation",
            "typetype": typ,
            "pos": list(pos),
            "rot": list(rot),
            "objects": child["components"],
        }
    )


def cut_group(t, cuts, pos, rot):
    cuts = copy.deepcopy(cuts)

    def invert(items):
        for item in items:
            if isinstance(item, list):
                invert(item)
            elif item.get("type") in ("n", "negative"):
                item["type"] = "positive"
            elif item.get("type") == "rotation":
                item["typetype"] = "p"

    invert(cuts["components"])
    group(t, cuts, pos, rot, typ="n")


def seat(t, name, spec, top, clearance, endplay=0.1):
    depth = spec["depth"] + 2 * endplay
    # Dimensions come from the OOBB bearing lookup. A plain OOBB cylindrical
    # seat avoids its legacy through-relief cutter, which removes the entire
    # core for bearings with an ID below 20 mm.
    hole(t, spec["od"] / 2 + clearance, depth, z=top - depth)


def mounting_lugs(t, c, depth, z=0):
    for xy in c["housing_positions"]:
        cylinder(t, c.get("housing_lug_radius", 5), depth, z, xy=xy)


def radial_bore(t, radius, start, length, z, angle):
    cutter = blank()
    cylinder(cutter, radius, length)
    group(t, cutter, [*polar(start, angle), z], [0, 90, angle], typ="n")


def motor_mount(**kwargs):
    c = resolve(kwargs)
    t = blank()
    bottom, top = c["mount_bottom_z"], c["rear_support_top"]
    # A skirt around the motor carries the rear 6814 below the mounting face.
    add(
        t,
        "oobb_plate",
        pos=[0, 0, bottom],
        width=c["housing_width"],
        height=c["housing_width"],
        depth=c["mount_rim_top"] - bottom,
        holes=False,
    )
    cylinder(t, c["carrier_journal_radius"], top - bottom, bottom)
    cylinder(
        t, c["rear_bearing_shoulder_radius"], c["rear_bearing_lift"], c["mount_rim_top"]
    )
    side = c["motor_body_width"] + 2 * c["motor_body_clearance"]
    add(
        t,
        "oobb_cube",
        "n",
        [0, 0, bottom - 0.01],
        size=[side, side, -bottom + 0.01],
        zz="bottom",
    )
    hole(t, c["rear_carrier_bore"], top + 0.1)
    add(
        t,
        "oobb_holes",
        "n",
        [0, 0, bottom],
        width=c["housing_width"],
        height=c["housing_width"],
        holes=["perimeter"],
        radius_name="m6",
        both_holes=True,
    )
    for xy, angle in zip(c["guide_positions"], c["guide_nut_rotations"]):
        add(
            t,
            "oobb_nut",
            "n",
            [*xy, c["guide_nut_top"] + 0.05],
            radius_name=c["guide_bolt_radius_name"],
            depth=c["guide_nut_top"] - bottom + 0.1,
            zz="top",
            overhang=True,
            rot=[0, 0, angle],
        )
        hole(
            t,
            oobb.gv("hole_radius_" + c["guide_bolt_radius_name"], "3dpr"),
            top - c["guide_nut_top"] + 0.2,
            xy,
            z=c["guide_nut_top"] - 0.1,
        )
    through(t, c["motor_positions"], c["motor_plate_depth"], countersink=True)
    for xy in c["motor_positions"]:
        hole(t, 3, top - c["motor_plate_depth"] + 0.1, xy, z=c["motor_plate_depth"])
    printed = blank()
    group(printed, t, [0, 0, -bottom])
    return printed


def output_casing(**kwargs):
    c = resolve(kwargs)
    t = blank()
    h = c["housing_depth"]
    base = c["rear_retainer_depth"]
    # Open underside: lower this casing onto the bearing already on the mount.
    shell = blank()
    cylinder(shell, c["housing_radius"], h + base)
    mounting_lugs(shell, c, h + base)
    hole(shell, c["casing_bore_radius"], h + base)
    group(t, shell)
    for xy in c["ring_positions"]:
        cylinder(t, c["lobe_radius"], h, base, xy=xy)
        # Preserve the round working face, back it with parallel straight sides.
        angle = math.degrees(math.atan2(xy[1], xy[0]))
        length = c["housing_radius"] - c["pitch_radius"] - 0.2
        back = blank()
        add(
            back,
            "oobb_cube",
            pos=[c["pitch_radius"] + length / 2, 0, base],
            size=[length, 2 * c["lobe_radius"], h],
            zz="bottom",
        )
        group(t, back, rot=[0, 0, angle])
    shoulder = c["rear_bearing_top"] + c["bearing_endplay"] - c["casing_bottom_z"]
    cup = blank()
    cylinder(cup, c["bearing_cup_radius"], shoulder)
    hole(cup, c["output_bearing"]["od"] / 2 + c["bearing_seat_clearance"], shoulder)
    group(t, cup)
    bridge = blank()
    cylinder(bridge, c["housing_radius"], c["minimum_wall"], shoulder)
    hole(bridge, c["output_bearing"]["od"] / 2 - 1.3, c["minimum_wall"], z=shoulder)
    group(t, bridge)
    through(t, c["housing_positions"], base + h)
    nut_top = (
        c["case_nut_bottom"] - c["casing_bottom_z"] + oobb.gv("nut_depth_m3", "true")
    )
    for xy in c["housing_positions"]:
        add(
            t,
            "oobb_nut",
            "n",
            [*xy, nut_top + 0.1],
            radius_name="m3",
            depth=nut_top + 0.2,
            zz="top",
            overhang=True,
        )
    # One index dimple makes casing rotation and assembly orientation visible.
    hole(t, 1, 1, xy=(c["pitch_radius"] + 3, 0), z=base + h - 1)
    return t


def front_retainer(**kwargs):
    c = resolve(kwargs)
    t = blank()
    h = c["front_retainer_depth"]
    cylinder(t, c["housing_radius"], h)
    mounting_lugs(t, c, h)
    cylinder(t, c["bearing_cup_radius"], c["bearing_cup_depth"], h)
    hole(t, c["bearing_pass_radius"], h + c["bearing_cup_depth"])
    seat(
        t,
        c["bearing_output"],
        c["output_bearing"],
        h + c["bearing_cup_depth"],
        c["bearing_seat_clearance"],
        0.2,
    )
    cuts = blank()
    through(cuts, c["housing_positions"], h, countersink=True)
    cut_group(t, cuts, [0, 0, h], [180, 0, 0])
    return t


def carrier(front=False, **kwargs):
    c = resolve(kwargs)
    t = blank()
    h = c["flange_depth"]
    cylinder(t, c["carrier_radius"], c["flange_web"])
    cylinder(t, c["carrier_journal_radius"], h)
    if front and not c["guide_heads_nested"]:
        cylinder(
            t,
            c["carrier_radius"],
            c["guide_head_depth"] + 0.4,
            h - c["guide_head_depth"] - 0.4,
        )
    if front:
        hole(t, c["shaft_exit_radius"], h)
        seat(
            t,
            c["bearing_shaft"],
            c["shaft_bearing"],
            h,
            c["bearing_seat_clearance"],
            c["bearing_endplay"],
        )
    else:
        hole(t, c["rear_carrier_bore"], h)
    positions = (
        c["guide_positions"] if front else [[x, -y] for x, y in c["guide_positions"]]
    )
    through(t, positions, h, size=c["guide_bolt_radius_name"])
    if front:
        for xy, angle in zip(positions, c["guide_nut_rotations"]):
            add(
                t,
                "oobb_nut",
                "n",
                [*xy, h + 0.1],
                radius_name=c["guide_bolt_radius_name"],
                depth=c["guide_head_depth"] + c["guide_head_clearance"] + 0.1,
                zz="top",
                rot=[0, 0, angle],
                overhang=True,
            )
    return t


def rotor(side=0, **kwargs):
    c = resolve(kwargs)
    t = blank()
    h = c["rotor_thickness"]
    profile = lobe.component(c, h)
    if side:
        a = math.radians(c["disc_phase_degrees"][side])
        profile["points"] = [
            [x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)]
            for x, y in profile["points"]
        ]
    t["components"].append(profile)
    hole(t, c["eccentric_exit_radius"], h)
    if side == 0:
        hole(
            t,
            c["eccentric_bearing"]["od"] / 2 + c["bearing_seat_clearance"],
            c["eccentric_bearing"]["depth"] + 2 * c["bearing_endplay"],
        )
    else:
        seat(
            t,
            c["bearing_eccentric"],
            c["eccentric_bearing"],
            h,
            c["bearing_seat_clearance"],
            c["bearing_endplay"],
        )
    positions = c["guide_positions"]
    for xy in positions:
        hole(t, c["guide_hole_radius"], h, xy)
    # Common +X assembly index: keep the two small holes aligned.
    hole(t, 0.7, h, xy=(c["guide_pin_pitch_radius"] + 8, 0))
    return t


def coupling_nut_pockets(t, c, top):
    """Shared production/coupon cutters: full-size outward loading channels."""

    def orient_hex(item):
        if isinstance(item, list):
            return [orient_hex(child) for child in item]
        if item.get("shape") == "polyg":
            return {
                "type": "rotation",
                "typetype": "p",
                "pos": [0, 0, 0],
                "rot": [0, 0, c["coupling_nut_hex_rotation"]],
                "objects": [item],
            }
        if "objects" in item:
            item["objects"] = orient_hex(item["objects"])
        return item

    for xy, angle in zip(c["coupling_positions"], c["coupling_nut_rotations"]):
        cutter = blank()
        add(
            cutter,
            "oobb_nut",
            "n",
            [*xy, top + 0.1],
            radius_name="m3",
            depth=oobb.gv("nut_depth_m3", "true") + 0.2,
            zz="top",
            overhang=True,
            clearance="right",
            extra_clearance=c["coupling_nut_side_clearance"],
            rot=[0, 0, angle],
        )
        # Retain OOBB's right clearance and overhang geometry. Only the hex
        # receives this extra rotation; the rectangular channel stays radial.
        t["components"].extend(orient_hex(cutter["components"]))


def eccentric_hub_lower(**kwargs):
    """One hollow shaft carries both opposed eccentrics, without a centre joint."""
    c = resolve(kwargs)
    t = blank()
    start, end = c["drive_start"], c["drive_end"]
    e = c["radius_offset"]
    spine = c["eccentric_journal_radius"] - e - 0.35
    cylinder(t, spine, end - start)
    a, b = c["eccentric_journal_z"]
    d = c["eccentric_journal_depth"]
    cylinder(t, c["eccentric_journal_radius"], d, a - start, xy=(e, 0))
    cylinder(t, c["eccentric_shoulder_radius"], 2, a + d - start, xy=(e, 0))
    taper_start = c["rotor_a_z"] + c["rotor_thickness"] + 0.1
    add(
        t,
        "oobb_cylinder",
        pos=[-e, 0, taper_start - start],
        radius_1=spine - e - 0.05,
        radius_2=c["eccentric_shoulder_radius"],
        depth=b - taper_start,
        zz="bottom",
    )
    cylinder(t, c["eccentric_journal_radius"], end - b, b - start, xy=(-e, 0))
    hole(t, c["drive_cavity_radius"], end - start)
    for xy in c["coupling_positions"]:
        hole(t, oobb.gv("hole_radius_m3", "3dpr"), end - start, xy)
    coupling_nut_pockets(t, c, c["drive_roof_top"] - start)
    for angle in c["coupling_grub_angles"]:
        radial_bore(
            t,
            c["grub_access_radius"],
            0,
            c["drive_shoulder_radius"] + 1,
            c["coupling_grub_z"] - start,
            angle,
        )
    return t


def eccentric_hub_upper(**kwargs):
    """Bearing cap clamps the upward flange with the two vertical M3 screws."""
    c = resolve(kwargs)
    t = blank()
    start, end = c["cap_start"], c["hub_upper_end"]
    cylinder(t, c["shaft_journal_radius"], end - start)
    hole(
        t,
        c["coupling_diameter"] / 2 + c["drive_flange_clearance"],
        c["cap_roof_bottom"] - start,
    )
    # Open top gives access to the recessed screw heads and saves material.
    hole(
        t,
        c["shaft_journal_radius"] - 2.5,
        end - c["cap_screw_head_z"],
        z=c["cap_screw_head_z"] - start,
    )
    through(t, c["coupling_positions"], end - start)
    printed = blank()
    group(printed, t, [0, 0, end - start], [180, 0, 0])
    return printed


def build(**kwargs):
    if kwargs.get("architecture") == "captured_6810":
        from gearbox.captured import build as captured_build

        return captured_build(**kwargs)
    c = resolve(kwargs)
    parts = {}

    def put(name, thing, width, depth):
        parts[name] = {"thing": thing, "width": width, "depth": depth, "quantity": 1}

    width = max(
        c["housing_width"] * 15 - 1,
        2 * c["housing_radius"],
        2 * c["housing_mount_offset"] + 10,
    )
    case_width = max(2 * c["housing_radius"], 2 * c["housing_mount_offset"] + 10)
    put("motor_mount", motor_mount(**c), width, c["integrated_mount_depth"])
    put(
        "output_casing",
        output_casing(**c),
        case_width,
        c["housing_depth"] + c["rear_retainer_depth"],
    )
    put(
        "output_cover",
        front_retainer(**c),
        case_width,
        c["front_retainer_depth"] + c["bearing_cup_depth"],
    )
    for side in ("front",):
        put(
            "pin_" + side,
            carrier(front=side == "front", **c),
            2 * c["carrier_radius"],
            c["flange_depth"],
        )
    for i in range(2):
        put(
            "rotor_" + ("a", "b")[i],
            rotor(side=i, **c),
            2 * c["pitch_radius"],
            c["rotor_thickness"],
        )
    put(
        "eccentric_hub_lower",
        eccentric_hub_lower(**c),
        2 * c["drive_shoulder_radius"],
        c["hub_split_z"] - c["drive_start"],
    )
    put(
        "eccentric_hub_upper",
        eccentric_hub_upper(**c),
        2 * (c["hub_retainer_outer_radius"] + c["radius_offset"]),
        c["hub_upper_end"] - c["hub_upper_start"],
    )
    return parts
