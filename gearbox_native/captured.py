"""Native captured-disc baseline and compact plain-guide V7 construction.

All coordinates are measured from the NEMA mounting face. captured_6810 retains
the migration reference, compact_6810 the first compact iteration, and
simple_6810 the current consolidated design.
"""

import copy
import math
from oobb_solidcraft import api as oobb
from gearbox_native import parts as p, lobe
from pathlib import Path
import yaml


def resolve(kwargs):
    if kwargs.get("architecture", "captured_6810") not in ("captured_6810", "compact_6810", "simple_6810"):
        raise ValueError("Only the latest captured_6810 V7 architecture is migrated")
    # Share the established motor, coupler, printing and tolerance defaults.
    # Derived coordinates are calculated here, not inherited from another layout.
    c = p.default_parameters()
    defaults = yaml.safe_load(Path(__file__).with_name("captured_defaults.yaml").read_text(encoding="utf-8"))
    simple = kwargs.get("architecture") == "simple_6810"
    compact = kwargs.get("architecture") in ("compact_6810", "simple_6810")
    if compact:
        defaults.update(yaml.safe_load(Path(__file__).with_name("compact_defaults.yaml").read_text(encoding="utf-8")))
    if simple:
        defaults.update(yaml.safe_load(Path(__file__).with_name("simple_defaults.yaml").read_text(encoding="utf-8")))
    for k, v in defaults.items():
        c[k] = kwargs.get(k, v)
    c.update(copy.deepcopy(kwargs))
    if simple and c['post_fasteners']:
        from gearbox_native.standoffs import configure_early
        configure_early(c,kwargs)
    c["architecture"] = "simple_6810" if simple else "compact_6810" if compact else "captured_6810"
    c["simple_assembly"] = simple
    c["plain_guides"] = compact
    if compact and c["bearing_output"] != "6810":
        raise ValueError("Compact V7 locks the motor-side casing bearing to 6810")
    c["output_member"] = "outer_casing"
    c["output_direction"] = "same_as_input"
    c["eccentric_phase_degrees"] = [0, 180]
    c["coupling_orientation"] = "flange_up_at_motor_shaft_tip"
    c["reduction"] = int(c["reduction"])
    if float(kwargs.get("reduction", 20)) != c["reduction"] or c["reduction"] < 3:
        raise ValueError("reduction must be an integer >= 3")
    c["ring_pin_count"] = n = c["reduction"]
    if simple and c['lobe_radius'] is None:
        # Keep a comparable fraction of the circumference per contact. The
        # envelope constraints below still enlarge the pitch circle if needed.
        c['lobe_radius']=c['lobe_reference_radius']*c['lobe_reference_reduction']/n
    c["disc_lobes"] = n - 1
    c["disc_phase_degrees"] = [0, -180 / (n - 1)]
    for k in ("eccentric", "shaft", "output", "guide"):
        c[k + "_bearing"] = p.bearing_spec(c["bearing_" + k])
    c['eccentric_bearings']=[]
    for label in ('bottom','top'):
        size=str(c.get('bearing_eccentric_'+label,c['bearing_eccentric']))
        c['bearing_eccentric_'+label]=size
        c['eccentric_bearings'].append(p.bearing_spec(size))
    e, wall, pin = c["radius_offset"], c["minimum_wall"], c["lobe_radius"]
    h, ep, bc = c["rotor_thickness"], c["bearing_endplay"], c["bearing_seat_clearance"]
    c["guide_strategy"] = "outer_races_captured_in_split_discs_inner_races_orbit_M6"
    c["guide_hole_radius"] = c["guide_bearing"]["od"] / 2 + bc
    c["guide_running_clearance"] = (
        c["guide_bearing"]["id"] - c["guide_pin_diameter"]
    ) / 2 - e
    if compact:
        c["guide_strategy"] = "plain_orbit_holes_on_smooth_M3_shanks"
        c["guide_hole_radius"] = c["guide_pin_diameter"] / 2 + e + c["guide_pin_clearance"]
        c["guide_running_clearance"] = c["guide_pin_clearance"]
    c["guide_positions"] = p.ring(c["guide_pin_pitch_radius"], c["guide_pin_count"], 30)
    c["post_positions"] = p.ring(c["post_pitch_radius"], 3)
    c["post_hole_radius"] = c["post_radius"] + e + c["post_clearance"]
    c["disc_join_positions"] = p.ring(
        c["disc_join_radius"], c["disc_join_count"], c["disc_join_phase"]
    )
    c["deck_positions"] = p.ring(c["deck_screw_radius"], 3)
    c["guide_nut_rotations"] = [30.0] * c["guide_pin_count"]
    limits = dict(
        lobe_shape=n * e / c["lobe_eccentricity_ratio"],
        rotor_features=c["guide_pin_pitch_radius"]
        + c["guide_hole_radius"]
        + wall
        + e
        + pin
        + c["lobe_clearance"],
        support_tracks=c["post_pitch_radius"]
        + c["post_hole_radius"]
        + wall
        + e
        + pin
        + c["lobe_clearance"],
        bearing_package=c["output_bearing"]["od"] / 2 + wall + bc + pin + 0.5,
        pin_spacing=(pin + wall / 2) / math.sin(math.pi / n),
        disc_fasteners=c["disc_join_radius"]
        + 3.5
        + wall
        + e
        + pin
        + c["lobe_clearance"],
    )
    if not c["disc_join_count"]:
        limits.pop("disc_fasteners")
    if simple:
        # End bearing seats are axially outside the working disc band.
        # They determine the shell OD, not the cycloid pitch circle.
        limits.pop("bearing_package")
    auto = kwargs.get("automatic_pitch", (
        "pitch_radius" not in kwargs
        or kwargs.get("radius_calculation", {}).get("mode") == "automatic"
    ))
    increment=c.get('pitch_radius_increment',.5)
    if not math.isfinite(increment) or increment<=0:
        raise ValueError('pitch_radius_increment must be positive and finite')
    c["pitch_radius"] = (
        round(math.ceil(max(limits.values())/increment-1e-10)*increment,10)
        if auto else kwargs["pitch_radius"]
    )
    if simple:
        from gearbox_native.cycloid_equation import CycloidEquation
        limits['centre_bearings']=max(b['od']/2 for b in c['eccentric_bearings'])+bc+wall+e+pin+c['lobe_clearance']
        minimum=math.ceil(max(limits.values())/increment-1e-10)*increment
        while CycloidEquation(n,minimum,e,pin,c['lobe_clearance']).minimum_convex_radius()<=pin+c['lobe_clearance']:
            minimum=round(minimum+increment,10)
            if minimum>150:raise ValueError('No non-undercut pitch radius below 150 mm')
        limits['analytic_undercut']=minimum
        if auto:
            c['pitch_radius']=round(math.ceil((minimum+c.get('pitch_radius_buffer',0))/increment-1e-10)*increment,10)
    c["radius_calculation"] = dict(
        mode="automatic" if auto else "explicit_override",
        limits_mm=limits,
        limiting_feature=max(limits, key=limits.get),
        selected_pitch_radius=c["pitch_radius"],
        rounding_increment_mm=increment,
    )
    c["ring_positions"] = p.ring(c["pitch_radius"], n)
    c["casing_bore_radius"] = c["pitch_radius"] + max(0, 2 * e - pin)
    c["housing_radius"] = c["pitch_radius"] + pin + 3
    if simple:
        c["housing_radius"] = max(c["pitch_radius"]+pin+c["casing_wall"],
            c["output_bearing"]["od"]/2+bc+c["casing_wall"])
    c["housing_width"] = math.ceil((2 * c["housing_radius"] + 1) / 15)
    c["housing_mount_offset"] = kwargs.get(
        "housing_mount_offset",
        math.ceil(
            (
                c["casing_bore_radius"]
                + wall
                + c["case_cover_post_radius"]
                + c["case_cover_post_clearance"]
            )
            / math.sqrt(2)
            * 2
        )
        / 2,
    )
    s = c["housing_mount_offset"]
    c["housing_positions"] = [[s, s], [-s, s], [-s, -s], [s, -s]]
    s = c["motor_hole_pitch"] / 2
    c["motor_positions"] = [[s, s], [-s, s], [-s, -s], [s, -s]]
    c["carrier_journal_radius"] = c["output_bearing"]["id"] / 2 - c["journal_clearance"]
    c["carrier_radius"] = c["output_bearing"]["id"] / 2 + 3
    c["bearing_pass_radius"] = c["carrier_radius"] + 0.5
    c["bearing_cup_radius"] = c["output_bearing"]["od"] / 2 + bc + wall
    c["bearing_cup_depth"] = c["flange_depth"] - c["flange_web"] - 0.1
    c["guide_heads_nested"] = False
    c["motor_face_z"] = c["mount_bottom_z"] = 0.0
    c["motor_plate_top"] = c["motor_plate_depth"]
    c["mount_rim_top"] = c["motor_plate_top"]
    c["rear_bearing_bottom"] = c["mount_rim_top"] + c["rear_bearing_lift"]
    c["rear_bearing_top"] = c["rear_bearing_bottom"] + c["output_bearing"]["depth"]
    c["rear_bearing_shoulder_radius"] = c["output_bearing"]["id"] / 2 + 1.5
    c["casing_bottom_z"] = c["mount_rim_top"] + c["casing_bottom_clearance"]
    c["rear_retainer_depth"] = -c["casing_bottom_z"]
    c["integrated_mount_depth"] = c["deck_bottom"]
    c["coupling_top"] = c["coupling_flange_top"] = c["motor_shaft_length"]
    c["coupling_z"] = c["coupling_top"] - c["coupling_length"]
    c["coupling_flange_z"] = c["coupling_z"] + c["coupling_barrel_length"]
    c["hub_nut_bottom"] = kwargs.get("hub_nut_bottom", c["coupling_top"] + 0.2)
    c["collar_bottom"] = kwargs.get("collar_bottom", c["coupling_flange_z"] - 6)
    c["coupling_grub_z"] = c["coupling_flange_z"] - c["coupling_grub_from_barrel_top"]
    c["coupling_hole_positions"] = p.ring(c["coupling_pitch_diameter"] / 2, 4)
    c["coupling_positions"] = c["coupling_hole_positions"][1::2]
    c["coupling_nut_rotations"] = [
        math.degrees(math.atan2(y, x)) + c["coupling_nut_rotation_offset"]
        for x, y in c["coupling_positions"]
    ]
    c["drive_roof_top"] = c["coupling_flange_z"] - 1.5
    c["drive_roof_z"] = c["drive_roof_top"] - oobb.gv("nut_depth_m3", "true")
    c["drive_start"] = c["coupling_top"]
    c['direct_drive']=simple and c.get('drive_connection')=='grub_nut'
    c['base_grub']=c['direct_drive'] and c.get('direct_stack_layout')=='base_grub'
    if c['direct_drive']:
        c['drive_start']=c['motor_plate_depth']+c['direct_drive_bottom_clearance']
        if c['base_grub']:
            c['drive_start']=c['motor_pilot_height']+c['direct_base_clearance']
            c['direct_grub_height']=c['direct_base_grub_height']
            c['flange_web']=c['direct_base_front_web']
            c['flange_depth']=c['flange_web']+c['output_bearing']['depth']+2*ep+.1
            c['bearing_cup_depth']=c['output_bearing']['depth']+2*ep
        c['drive_flange_depth']=c['direct_drive_depth']
        c['drive_flange_radius']=c['direct_drive_radius']
        c['drive_flange_clearance']=c['direct_drive_clearance']
        c['guide_bolt_length']=c['direct_guide_bolt_length']
        c['hub_bolt_length']=c['direct_hub_bolt_length']
        if c['base_grub']:c['hub_bolt_length']=c['direct_base_hub_bolt_length']
        c['hub_nut_bottom']=c['motor_shaft_length']+c['direct_shaft_endplay']+c['direct_nut_floor']
        c['coupling_grub_z']=c['drive_start']+c['direct_grub_height']
        c['coupling_grub_angles']=[c['direct_grub_angle']]
    c["drive_flange_top"] = c["drive_start"] + c["drive_flange_depth"]
    c["cap_screw_head_z"] = c["drive_flange_top"] - 3.0
    c["rotor_a_z"] = c["drive_flange_top"] + c["axial_clearance"]
    c["rotor_b_z"] = c["rotor_a_z"] + h + c["disc_gap"]
    c["rear_support_top"] = c["rotor_a_z"] - c["axial_clearance"]
    c["front_support_bottom"] = c["rotor_b_z"] + h + c["axial_clearance"]
    c["housing_depth"] = H = c["front_support_bottom"] + c["flange_depth"]
    c["output_bearing_z"] = [
        (c["rear_bearing_bottom"] + c["rear_bearing_top"]) / 2,
        c["front_support_bottom"]
        + c["flange_web"]
        + c["output_bearing"]["depth"] / 2
        + ep,
    ]
    c["shaft_bearing_z"] = [0, H - ep - c["shaft_bearing"]["depth"] / 2]
    c["eccentric_bearing_z"] = [c["rotor_a_z"] + h / 2, c["rotor_b_z"] + h / 2]
    if compact:
        # Single-piece discs: lower bearing loads from above, upper from below.
        seat = c["eccentric_bearing"]["depth"] + 2 * ep
        c["eccentric_bearing_z"] = [c["rotor_a_z"] + h - seat / 2,
                                      c["rotor_b_z"] + seat / 2]
    if compact:
        seats=[b['depth']+2*ep for b in c['eccentric_bearings']]
        c['eccentric_bearing_z']=[c['rotor_a_z']+h-seats[0]/2,c['rotor_b_z']+seats[1]/2]
    c["guide_bearing_z"] = c["eccentric_bearing_z"][:]
    c["eccentric_journal_depth"] = c["eccentric_bearing"]["depth"] + 2 * ep
    c["eccentric_journal_z"] = [
        z - (c["eccentric_bearings"][i]["depth"]+2*ep) / 2 for i,z in enumerate(c["eccentric_bearing_z"])
    ]
    c["eccentric_journal_radius"] = (
        c["eccentric_bearing"]["id"] / 2 - c["journal_clearance"]
    )
    # JTEKT 6704: inner abutment >=21.6, outer abutment <=25.4 mm.
    c["eccentric_shoulder_radius"] = kwargs.get("eccentric_shoulder_radius", c.get("eccentric_shoulder_radius", 10.8))
    c["shaft_journal_radius"] = c["shaft_bearing"]["id"] / 2 - c["journal_clearance"]
    c["shaft_exit_radius"] = c["shaft_bearing"]["od"] / 2 - 1.5
    c["hub_split_z"] = c["rotor_a_z"] + h + c["disc_gap"] / 2
    if c['direct_drive']:
        # The hollow keyed stem passes around the motor shaft. Its top nut sits
        # above the shaft tip, allowing a short axial bolt to retain the upper cam.
        c['hub_key_depth']=(c['hub_nut_bottom']+oobb.gv('nut_depth_m3','true')
                            +c['direct_key_roof_clearance']-c['hub_split_z'])
    c["hub_upper_start"] = c["hub_split_z"]
    c["hub_upper_end"] = H + 0.2
    c["hub_bolt_head_z"] = c["hub_nut_bottom"] + c["hub_bolt_length"]
    c["guide_bolt_head_z"] = (
        c["front_support_bottom"] + c["flange_web"] - c["guide_head_depth"] - 0.3
    )
    if compact:
        c["guide_bolt_head_z"] = c["front_support_bottom"] + c["flange_web"] - 0.3
        c["guide_nut_bottom"] = kwargs.get("guide_nut_bottom", max(c["deck_bottom"] + 0.9,
            c["guide_bolt_head_z"] - c["guide_bolt_length"] + 0.2))
    c["guide_nut_top"] = c["guide_nut_bottom"] + oobb.gv("nut_depth_" + c["guide_bolt_radius_name"], "true")
    c["guide_spacer_depths"] = (
        []
    )  # Captured outer races must not be clamped to fixed pins.
    c["guide_spacer_z"] = []
    c["post_depth"] = c["front_support_bottom"] - c["rear_support_top"]
    c["post_screw_head_z"] = c["front_support_bottom"] + 2
    c["front_hub_bottom"] = c["front_support_bottom"] + c["flange_web"]
    c["front_hub_screw_head_z"] = H - 0.2
    c["front_hub_nut_bottom"] = (
        c["front_hub_screw_head_z"] - c["front_hub_screw_length"] + 0.2
    )
    target = c["casing_bottom_z"] + 0.2
    c["case_nut_bottom"] = (
        H
        + c["front_retainer_depth"]
        - 5 * math.floor((H + c["front_retainer_depth"] - target) / 5)
    )
    if compact:
        c["case_nut_bottom"] = kwargs.get("case_nut_bottom", 7.0)
    c["housing_screw_length"] = min(
        35.0, c["housing_screw_max_length"], kwargs.get("housing_screw_length", 35.0)
    )
    c["case_screw_head_z"] = c["case_nut_bottom"] + c["housing_screw_length"]
    c["case_cover_post_bottom"] = c["case_screw_head_z"] - c["case_cover_post_floor"]
    c["case_cover_depth"] = max(
        c["front_retainer_depth"] + c["bearing_cup_depth"],
        H + c["front_retainer_depth"] - c["case_cover_post_bottom"],
    )
    c["case_split_z"] = kwargs.get("case_split_z", c["rear_bearing_top"] + ep + wall)
    c["case_base_depth"] = c["case_split_z"] - c["casing_bottom_z"]
    c["case_ring_depth"] = H - c["case_split_z"]
    c["central_to_guide_race_gap"] = (
        c["guide_pin_pitch_radius"]
        - (c["guide_bearing"]["od"] + c["eccentric_bearing"]["od"]) / 2
    )
    c["gap"] = H
    c["thickness_outer_rotor"] = c["flange_depth"]
    c["disc_half_depth"] = h / 2
    c["disc_join_head_z"] = h - 0.3
    c["disc_join_nut_bottom"] = c["disc_join_head_z"] - c["disc_join_length"]
    # Small fasteners share the same M3 primitive and remain below the faces.
    if simple:
        from gearbox_native.simple import configure
        configure(c, kwargs)
    validate(c)
    return c


def validate(c):
    if c.get("simple_assembly"):
        from gearbox_native.simple import validate as validate_simple
        validate_simple(c)
        return
    e, w = c["radius_offset"], c["minimum_wall"]
    if (
        c["case_split_z"]
        < max(
            c["rear_bearing_top"] + c["bearing_endplay"] + w,
            c["case_nut_bottom"] + oobb.gv("nut_depth_m3", "true") + w,
        )
        - 1e-9
    ):
        raise ValueError("Casing base must retain the bearing shoulder and bottom nuts")
    if c["case_split_z"] >= min(c["rotor_a_z"], c["case_cover_post_bottom"]):
        raise ValueError("Casing split must stay below the discs and cover screw posts")
    if c["guide_running_clearance"] < 0.1 - 1e-9:
        raise ValueError(
            "Captured bearing needs at least 0.10 mm radial running clearance"
        )
    if not c["plain_guides"] and c["central_to_guide_race_gap"] < c["bearing_outer_race_gap_min"] - 1e-9:
        raise ValueError(
            "Central and guide bearing outer races overlap or lack assembly clearance"
        )
    if not c["allow_shared_bearing_pockets"] and (
        c["guide_pin_pitch_radius"]
        - c["guide_hole_radius"]
        - c["eccentric_bearing"]["od"] / 2
        - c["bearing_seat_clearance"]
        < c["rotor_central_wall"] - 1e-9
    ):
        raise ValueError("Insufficient web between 6700 pockets and central bearing")
    if (
        c["guide_pin_pitch_radius"] + oobb.gv("hole_radius_" + c["guide_bolt_radius_name"], "3dpr") + 0.5
        > c["carrier_journal_radius"]
    ):
        raise ValueError("M6 guides do not fit inside output bearing journal")
    if (
        c["case_screw_head_z"] + oobb.gv("screw_socket_cap_height_m3", "true")
        >= c["housing_depth"] + c["front_retainer_depth"]
    ):
        raise ValueError("Casing socket heads must be recessed below cover top")
    if c["case_cover_post_bottom"] <= c["case_nut_bottom"] + 3:
        raise ValueError("Casing cover posts reach the bottom nut pockets")
    if (
        math.sqrt(2) * c["housing_mount_offset"]
        - c["case_cover_post_radius"]
        - c["case_cover_post_clearance"]
        < c["casing_bore_radius"] + 1.5
    ):
        raise ValueError(
            "Recessed casing screws need more radial clearance from cycloids"
        )
    if (
        c["pitch_radius"] <= c["ring_pin_count"] * e
        or c["pitch_radius"] + c["lobe_radius"] - c["casing_bore_radius"] < 0.4 - 1e-9
    ):
        raise ValueError("Invalid lobe shape/contact attachment")
    if c["deck_bottom"] <= c["rear_bearing_top"] + c["bearing_endplay"] + w:
        raise ValueError("Rear carrier deck must clear rotating bearing shoulder")
    if c["deck_bore"] < c["drive_flange_radius"] + 0.15:
        raise ValueError("Drive flange needs running clearance inside deck")
    if not c["plain_guides"] and (
        c["rotor_thickness"]
        < max(c["guide_bearing"]["depth"], c["eccentric_bearing"]["depth"])
        + 2 * c["bearing_endplay"]
        + 2
    ):
        raise ValueError("Split discs need at least 1 mm bearing retaining lips")
    if not c["plain_guides"] and (
        c["guide_lip_radius"] <= c["guide_bearing"]["id"] / 2
        or c["guide_lip_radius"] >= c["guide_bearing"]["od"] / 2
    ):
        raise ValueError("Guide retaining lip must overlap only outer race")
    if c["guide_bolt_head_z"] - c["guide_bolt_length"] < c["motor_plate_depth"]:
        raise ValueError("Guide bolt tips reach motor mounting screws")
    if not (
        c["guide_bolt_head_z"] - c["guide_bolt_length"] <= c["guide_nut_bottom"] + 0.2
    ):
        raise ValueError("Guide bolts do not fully engage nuts")
    if c["cap_screw_head_z"] - c["coupling_screw_length"] > c["drive_roof_z"]:
        raise ValueError("Flange screws do not engage coupling nuts")
    if c["cap_screw_head_z"] < c["hub_nut_bottom"] + oobb.gv("nut_depth_" + c["hub_bolt_radius_name"], "true") + 0.2:
        raise ValueError("M6 hub nut overlaps flange screw heads")
    if (
        c["hub_key_radius"] + c["hub_key_clearance"] + e + 1.4
        > c["eccentric_journal_radius"]
    ):
        raise ValueError("Key pocket leaves too little eccentric journal wall")
    for xy in c["post_positions"]:
        if (
            min(math.dist(xy, g) for g in c["guide_positions"])
            < c["post_hole_radius"] + c["guide_hole_radius"] + 2
        ):
            raise ValueError("Post tracks overlap guide bearing seats")
    if not 0 < c["motor_screw_length"] - c["motor_plate_depth"] <= 2.5:
        raise ValueError("Motor screw engagement must be between 0 and 2.5 mm")
    if c["plain_guides"]:
        if c["rotor_thickness"] < c["eccentric_bearing"]["depth"] + 2 * c["bearing_endplay"] + 0.8 - 1e-9:
            raise ValueError("Single discs need a 0.8 mm outer-race retaining lip")
        if c["guide_pin_diameter"] != 3 or c["guide_bolt_radius_name"] != "m3":
            raise ValueError("Compact guide hardware must be M3")
        if c["guide_nut_bottom"] < c["deck_bottom"] + 0.5:
            raise ValueError("Guide nuts need a locating recess in the rear carrier")
        if c["guide_pin_pitch_radius"] - c["guide_hole_radius"] - c["eccentric_bearing"]["od"] / 2 - c["bearing_seat_clearance"] < w:
            raise ValueError("Plain guide holes need a web around the central bearing")
        if c["bearing_cup_depth"] < c["output_bearing"]["depth"] + 2*c["bearing_endplay"]:
            raise ValueError("Cover cup is too short for the 6810")
        if not (c["front_support_bottom"] <= c["front_hub_nut_bottom"] and
                c["front_hub_nut_bottom"] + 2.5 <= c["front_hub_bottom"]):
            raise ValueError("Front hub nuts must fit entirely in the front carrier")


def nut(t, xy, top, depth, size="m3", angle=0):
    p.add(
        t,
        "oobb_nut",
        "n",
        [*xy, top],
        radius_name=size,
        depth=depth,
        zz="top",
        overhang=True,
        rot=[0, 0, angle],
    )


def motor_mount(c):
    t = p.blank()
    top = c["deck_bottom"]
    p.add(
        t,
        "oobb_plate",
        width=c["housing_width"],
        height=c["housing_width"],
        depth=c["motor_plate_depth"],
        holes=False,
    )
    p.cylinder(t, c["carrier_journal_radius"], top)
    p.cylinder(
        t,
        c["rear_bearing_shoulder_radius"],
        c["rear_bearing_lift"],
        c["motor_plate_depth"],
    )
    p.hole(t, c["motor_pilot_diameter"] / 2 + c["motor_pilot_clearance"], top)
    p.add(
        t,
        "oobb_holes",
        "n",
        width=c["housing_width"],
        height=c["housing_width"],
        depth=c["motor_plate_depth"],
        holes=["perimeter"],
        radius_name="m6",
        both_holes=True,
    )
    p.through(t, c["motor_positions"], c["motor_plate_depth"], countersink=True)
    for xy in c["motor_positions"]:
        p.hole(t, 3, top - c["motor_plate_depth"] + 0.1, xy, z=c["motor_plate_depth"])
    for xy in c["deck_positions"]:
        p.hole(t, oobb.gv("hole_radius_m3", "3dpr"), top, xy)
        nut(t, xy, 2.8, 2.9)
    for xy in c["guide_positions"]:
        tip = c["guide_bolt_head_z"] - c["guide_bolt_length"] - 0.3
        if tip < top:
            p.hole(t, oobb.gv("hole_radius_" + c["guide_bolt_radius_name"], "3dpr"), top - tip + 0.1, xy, z=tip)
    return t


def rear_deck(c):
    t = p.blank()
    h = c["rear_support_top"] - c["deck_bottom"]
    p.cylinder(t, c["deck_radius"], h)
    p.hole(t, c["deck_bore"], h)
    for xy, a in zip(c["guide_positions"], c["guide_nut_rotations"]):
        p.hole(t, oobb.gv("hole_radius_" + c["guide_bolt_radius_name"], "3dpr"), h, xy)
        nut(
            t,
            xy,
            c["guide_nut_top"] - c["deck_bottom"] + 0.1,
            c["guide_nut_top"] - c["deck_bottom"] + 0.2,
            c["guide_bolt_radius_name"],
            a,
        )
    p.through(
        t,
        c["deck_positions"],
        c["deck_screw_head_z"] - c["deck_bottom"],
        countersink=True,
    )
    for xy in c["deck_positions"]:
        p.hole(t, 3, h, xy, z=c["deck_screw_head_z"] - c["deck_bottom"])
    for xy in c["post_positions"]:
        p.hole(t, oobb.gv("hole_radius_m3", "3dpr"), h, xy)
        nut(
            t,
            xy,
            c["post_nut_bottom"] + 2.5 - c["deck_bottom"],
            c["post_nut_bottom"] + 2.6 - c["deck_bottom"],
        )
    return t


def front_carrier(c):
    t = p.blank()
    h = c["flange_web"]
    p.cylinder(t, c["deck_radius"], h)
    p.cylinder(t, 13, 1, h)
    p.hole(t, c["shaft_exit_radius"], h)
    p.hole(t, c["shaft_exit_radius"], 1.1, z=h)
    if c["plain_guides"]:
        p.through(t, c["guide_positions"], h - 0.3, size="m3", countersink=True)
        for xy in c["guide_positions"]:
            p.hole(t, 3.05, 0.32, xy, z=h-0.3)
    else:
        p.through(t, c["guide_positions"], h, size=c["guide_bolt_radius_name"])
        for xy, a in zip(c["guide_positions"], c["guide_nut_rotations"]):
            nut(t, xy, h + 0.1, c["guide_head_depth"] + 0.4, c["guide_bolt_radius_name"], a)
    p.through(t, c["post_positions"], 2, countersink=True)
    for xy in c["post_positions"]:
        p.hole(t, 3, h, xy, z=2)
    for xy in c["deck_positions"]:
        p.hole(t, oobb.gv("hole_radius_m3", "3dpr"), h, xy)
        top = c["front_hub_nut_bottom"] + 2.5 - c["front_support_bottom"]
        nut(t, xy, top, top + 0.1)
    return t


def front_hub(c):
    t = p.blank()
    h = c["housing_depth"] - c["front_hub_bottom"]
    p.cylinder(t, c["carrier_journal_radius"], h)
    p.hole(t, c["shaft_exit_radius"], h)
    p.hole(t, 13.15, 1.15)
    p.seat(
        t,
        c["bearing_shaft"],
        c["shaft_bearing"],
        h,
        c["bearing_seat_clearance"],
        c["bearing_endplay"],
    )
    p.through(t, c["deck_positions"], h - 0.2, countersink=True)
    for xy in c["deck_positions"]:
        p.hole(t, 3, 0.3, xy, z=h - 0.2)
    return t


def output_base(c):
    """Rear bearing holder: broad joint face on the bed, bearing pocket upward."""
    t = p.blank()
    h = c["case_base_depth"]
    shoulder = c["rear_bearing_top"] + c["bearing_endplay"] - c["casing_bottom_z"]
    shell = p.blank()
    p.cylinder(shell, c["housing_radius"], h)
    p.mounting_lugs(shell, c, h)
    p.hole(shell, c["casing_bore_radius"], h)
    p.group(t, shell)
    cup = p.blank()
    p.cylinder(cup, c["bearing_cup_radius"], shoulder)
    p.hole(cup, c["output_bearing"]["od"] / 2 + c["bearing_seat_clearance"], shoulder)
    p.group(t, cup)
    bridge = p.blank()
    p.cylinder(bridge, c["housing_radius"], h - shoulder, shoulder)
    p.hole(bridge, c["output_bearing"]["od"] / 2 - 1.3, h - shoulder, z=shoulder)
    p.group(t, bridge)
    p.through(t, c["housing_positions"], h)
    nut_top = (
        c["case_nut_bottom"] - c["casing_bottom_z"] + oobb.gv("nut_depth_m3", "true")
    )
    for xy in c["housing_positions"]:
        nut(t, xy, nut_top + 0.1, nut_top + 0.2)
    printed = p.blank()
    p.group(printed, t, [0, 0, h], [180, 0, 0])
    return printed


def casing_socket_cuts(c, positions):
    cuts = p.blank()
    for xy in positions:
        p.add(
            cuts,
            "oobb_screw_socket_cap",
            "n",
            [*xy, c["case_screw_head_z"]],
            radius_name="m3",
            depth=c["housing_screw_length"],
            zz="none",
            nut_include=False,
            clearance="top",
            overhang=False,
        )
    return cuts


def output_cover(c):
    """Deep screw tubes let 35 mm socket bolts reach the original bottom nuts."""
    t = p.blank()
    h = c["front_retainer_depth"]
    p.cylinder(t, c["housing_radius"], h)
    p.mounting_lugs(t, c, h)
    p.cylinder(t, c["bearing_cup_radius"], c["bearing_cup_depth"], h)
    p.hole(t, c["bearing_pass_radius"], h + c["bearing_cup_depth"])
    p.seat(
        t,
        c["bearing_output"],
        c["output_bearing"],
        h + c["bearing_cup_depth"],
        c["bearing_seat_clearance"],
        0.2,
    )
    for xy in c["housing_positions"]:
        p.cylinder(
            t,
            c["case_cover_post_radius"],
            c["housing_depth"] - c["case_cover_post_bottom"],
            h,
            xy=xy,
        )
    cuts = casing_socket_cuts(c, c["housing_positions"])
    p.cut_group(t, cuts, [0, 0, c["housing_depth"] + h], [180, 0, 0])
    return t


def rotor(c, side, half):
    # Both halves print with their bearing pockets UP. The top half flips in assembly.
    t = p.blank()
    h = c["rotor_thickness"]
    hh = h / 2
    shape = lobe.component(c, hh)
    a = math.radians(c["disc_phase_degrees"][side])
    shape["points"] = [
        [x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)]
        for x, y in shape["points"]
    ]
    t["components"].append(shape)
    for xy, spec, lip in [
        (q, c["guide_bearing"], c["guide_lip_radius"]) for q in c["guide_positions"]
    ] + [([0, 0], c["eccentric_bearing"], c["eccentric_lip_radius"])]:
        p.hole(t, lip, hh, xy)
        depth = spec["depth"] / 2 + c["bearing_endplay"]
        p.hole(
            t,
            spec["od"] / 2 + c["bearing_seat_clearance"],
            depth + 0.02,
            xy,
            z=hh - depth,
        )
    for xy in c["post_positions"]:
        p.hole(t, c["post_hole_radius"], hh, xy)
    # Three M3 screws register the halves; close-fitting holes constrain their alignment.
    for xy in c["disc_join_positions"]:
        p.hole(t, 1.6, hh, xy)
        if half == 0:
            nut(
                t,
                xy,
                c["disc_join_nut_bottom"] + c["disc_join_nut_depth"] + 0.1,
                c["disc_join_nut_bottom"] + c["disc_join_nut_depth"] + 0.2,
            )
        else:
            cut = p.blank()
            p.through(cut, [xy], hh, countersink=True)
            # Counterbore to put the head .3 mm beneath the exterior face.
            p.cut_group(t, cut, [0, 0, hh + 0.3], [180, 0, 0])
            p.hole(t, 3, 0.32, xy, z=-0.01)
    if half:
        # Reflect Y only: when rotated 180 about X the profile and holes coincide.
        def mirror_y(items):
            for item in items:
                if isinstance(item, list):
                    mirror_y(item)
                    continue
                if "pos" in item:
                    item["pos"][1] *= -1
                if "points" in item:
                    item["points"] = [[x, -y] for x, y in item["points"]][::-1]
                if "rot" in item:
                    item["rot"][2] *= -1
                if "objects" in item:
                    mirror_y(item["objects"])

        mirror_y(t["components"])
    return t


def plain_rotor(c, side):
    """One disc, plain orbit tracks, and an open central bearing counterbore."""
    t = p.blank()
    h = c["rotor_thickness"]
    shape = lobe.component(c, h)
    a = math.radians(c["disc_phase_degrees"][side])
    shape["points"] = [[x*math.cos(a)-y*math.sin(a), x*math.sin(a)+y*math.cos(a)]
                       for x, y in shape["points"]]
    t["components"].append(shape)
    p.hole(t, c["eccentric_lip_radius"], h)
    p.seat(t, c["bearing_eccentric"], c["eccentric_bearing"], h,
           c["bearing_seat_clearance"], c["bearing_endplay"])
    for xy in c["guide_positions"]:
        p.hole(t, c["guide_hole_radius"], h, xy)
    for xy in c["post_positions"]:
        p.hole(t, c["post_hole_radius"], h, xy)
    if side:
        # Upper disc prints pocket-up and flips over at installation.
        for item in t["components"]:
            if "pos" in item:
                item["pos"][1] *= -1
            if "points" in item:
                item["points"] = [[x, -y] for x, y in item["points"]][::-1]
    return t


def collar(c):
    t = p.blank()
    z = c["collar_bottom"]
    h = c["coupling_flange_z"] - z
    p.cylinder(t, c["drive_flange_radius"], h)
    p.hole(t, c["coupling_barrel_diameter"] / 2 + c["drive_cavity_clearance"], h)
    p.through(t, c["coupling_positions"], h)
    p.coupling_nut_pockets(t, c, c["drive_roof_top"] - z)
    for a in c["coupling_grub_angles"]:
        p.radial_bore(
            t,
            c["grub_access_radius"],
            0,
            c["drive_flange_radius"] + 1,
            c["coupling_grub_z"] - z,
            a,
        )
    return t


def key(c, clearance=0):
    t = p.blank()
    r = c["hub_key_radius"] + clearance
    flat = c["hub_key_flat"] + clearance
    p.cylinder(t, r, c["hub_key_depth"] + 0.02 + clearance)
    # A single flat makes the key asymmetric: the opposed eccentric cannot
    # accidentally be assembled 180 degrees out of its intended phase.
    for s in (1,):
        p.add(
            t,
            "oobb_cube",
            "n",
            [s * (flat + 10), 0, -0.01],
            size=[20, 20, c["hub_key_depth"] + 0.05 + clearance],
            zz="bottom",
        )
    return t


def coupling_drive(c):
    t = p.blank()
    start = c["drive_start"]
    h = c["drive_flange_depth"]
    p.cylinder(t, c["drive_flange_radius"], h)
    p.group(t, key(c), [0, 0, h])
    p.through(t, c["coupling_positions"], h)
    for xy in c["coupling_positions"]:
        p.hole(t, 3.05, h, xy, z=c["cap_screw_head_z"] - start)
    nut_depth = oobb.gv("nut_depth_" + c["hub_bolt_radius_name"], "true")
    nut(
        t,
        [0, 0],
        c["hub_nut_bottom"] + nut_depth + 0.1 - start,
        c["hub_nut_bottom"] + nut_depth + 0.2 - start,
        c["hub_bolt_radius_name"],
        30,
    )
    p.hole(t, oobb.gv("hole_radius_" + c["hub_bolt_radius_name"], "3dpr"), h + c["hub_key_depth"] + 0.1)
    return t


def shaft(c, upper=False, *, key_socket=True):
    if c.get('simple_assembly'):
        from gearbox_native.interfaces import for_disc
        c=for_disc(c,int(upper))
    t = p.blank()
    e = c["radius_offset"]
    d = c["eccentric_journal_depth"]
    start = c["hub_split_z"] if upper else c["drive_flange_top"]
    end = c["hub_upper_end"] if upper else c["hub_split_z"]
    spine = c["eccentric_journal_radius"] - e - 0.35
    # The smaller front shaft journal must not inherit the eccentric core OD.
    spine_end = min(end, c["front_support_bottom"]) if upper else end
    p.cylinder(t, spine, spine_end - start)
    i = int(upper)
    j = c["eccentric_journal_z"][i] - start
    xy = ((-e if upper else e), 0)
    p.cylinder(
        t,
        c["eccentric_journal_radius"],
        j + d if upper else d,
        0 if upper else j,
        xy=xy,
    )
    # Lower shoulder grows from its print-bed footprint. Upper shoulder and
    # front journal have supported tapers rather than abrupt radial overhangs.
    if upper:
        p.add(
            t,
            "oobb_cylinder",
            pos=[*xy, j + d],
            radius_1=c["eccentric_journal_radius"],
            radius_2=c["eccentric_shoulder_radius"],
            depth=0.8,
            zz="bottom",
        )
        p.add(
            t,
            "oobb_cylinder",
            pos=[0, 0, j + d],
            radius_1=c["eccentric_journal_radius"] - e,
            radius_2=c["shaft_journal_radius"],
            depth=c["front_support_bottom"] - start - j - d,
            zz="bottom",
        )
    else:
        p.cylinder(t, c["eccentric_shoulder_radius"], j, xy=xy)
    if key_socket:
        p.group(t, key(c, c["hub_key_clearance"]), [0, 0, -0.01], typ="n")
    if upper:
        p.cylinder(
            t,
            c["shaft_journal_radius"],
            end - c["front_support_bottom"],
            c["front_support_bottom"] - start,
        )
        p.hole(
            t, (3.1 if c["hub_bolt_radius_name"] == "m3" else 6.05), end - c["hub_bolt_head_z"] + 0.1, z=c["hub_bolt_head_z"] - start
        )
    else:
        p.group(t, key(c), [0, 0, end - start])
        # Recess only the underside over the flange screw heads; do not cut
        # axial access holes through the 6703 bearing journal.
        if key_socket:
            for xy2 in c["coupling_positions"]:
                p.hole(t, 3.05, 0.25, xy2)
    p.hole(t, oobb.gv("hole_radius_" + c["hub_bolt_radius_name"], "3dpr"), end - start + c["hub_key_depth"] + 0.1)
    if upper:
        from gearbox_native.geometry import continuous_positive_sections
        continuous_positive_sections(t)
    return t


def output_ring(c):
    """Shared casing ring above the separately printable bearing base."""
    cw=max(2*c['housing_radius'],2*c['housing_mount_offset']+2*c['housing_lug_radius'])
    case=p.output_casing(**c)
    cut_depth=c['housing_depth']+100
    p.add(case,'oobb_cube','n',[0,0,c['case_base_depth']-cut_depth],
          size=[2*cw+20,2*cw+20,cut_depth],zz='bottom')
    for xy in c['housing_positions']:
        p.hole(case,c['case_cover_post_radius']+c['case_cover_post_clearance'],
               c['housing_depth']-c['case_cover_post_bottom']+.3,xy,
               z=c['case_cover_post_bottom']-c['casing_bottom_z']-.2)
    ring=p.blank();p.group(ring,case,[0,0,-c['case_base_depth']])
    return ring


def build(**kwargs):
    c = resolve(kwargs)
    if c.get("simple_assembly"):
        from gearbox_native.simple import build as build_simple
        return build_simple(c)
    result = {}

    def put(name, t, w, h):
        result[name] = dict(thing=t, width=w, depth=h, quantity=1)

    cw = max(
        2 * c["housing_radius"],
        2 * c["housing_mount_offset"] + 2 * c["housing_lug_radius"],
    )
    put(
        "motor_mount",
        motor_mount(c),
        max(cw, c["housing_width"] * 15 - 1),
        c["deck_bottom"],
    )
    put(
        "pin_rear",
        rear_deck(c),
        2 * c["deck_radius"],
        c["rear_support_top"] - c["deck_bottom"],
    )
    put("output_base", output_base(c), cw, c["case_base_depth"])
    # Retain only the lobe ring above the bearing holder. All cutters are in
    # the original casing coordinates before translating the split to the bed.
    case = p.output_casing(**c)
    cut_depth = c["housing_depth"] + 100
    p.add(
        case,
        "oobb_cube",
        "n",
        [0, 0, c["case_base_depth"] - cut_depth],
        size=[2 * cw + 20, 2 * cw + 20, cut_depth],
        zz="bottom",
    )
    for xy in c["housing_positions"]:
        p.hole(
            case,
            c["case_cover_post_radius"] + c["case_cover_post_clearance"],
            c["housing_depth"] - c["case_cover_post_bottom"] + 0.3,
            xy,
            z=c["case_cover_post_bottom"] - c["casing_bottom_z"] - 0.2,
        )
    ring = p.blank()
    p.group(ring, case, [0, 0, -c["case_base_depth"]])
    put("output_casing", ring, cw, c["case_ring_depth"])
    put(
        "output_cover",
        output_cover(c),
        cw,
        c["case_cover_depth"],
    )
    put("pin_front", front_carrier(c), 2 * c["deck_radius"], c["flange_web"] + 1)
    put(
        "front_bearing_hub",
        front_hub(c),
        2 * c["carrier_journal_radius"],
        c["housing_depth"] - c["front_hub_bottom"],
    )
    for i, word in enumerate(("a", "b")):
        if c["plain_guides"]:
            put(f"rotor_{word}", plain_rotor(c, i), 2*c["pitch_radius"], c["rotor_thickness"])
            continue
        for half, tag in enumerate(("lower", "upper")):
            put(
                f"rotor_{word}_{tag}",
                rotor(c, i, half),
                2 * c["pitch_radius"],
                c["disc_half_depth"],
            )
    put(
        "coupling_collar",
        collar(c),
        2 * c["drive_flange_radius"],
        c["coupling_flange_z"] - c["collar_bottom"],
    )
    put(
        "coupling_drive",
        coupling_drive(c),
        2 * c["drive_flange_radius"],
        c["drive_flange_depth"] + c["hub_key_depth"] + 0.02,
    )
    put(
        "eccentric_hub_lower",
        shaft(c),
        2 * c["drive_flange_radius"],
        c["hub_split_z"] - c["drive_flange_top"] + c["hub_key_depth"] + 0.02,
    )
    put(
        "eccentric_hub_upper",
        shaft(c, True),
        2 * (c["eccentric_shoulder_radius"] + c["radius_offset"]),
        c["hub_upper_end"] - c["hub_split_z"],
    )
    from gearbox_native.geometry import continuous_negative_sections, subtract_axial_sections
    for piece in result.values():
        continuous_negative_sections(piece['thing'])
        subtract_axial_sections(piece['thing'])
    return result
