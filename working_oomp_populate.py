"""Active catalogue. The complete preceding definitions live in working_oomp_populate_version_10.py."""
import copy
from oomp_populate_helper import build_oomp_id, write_extras


RATIOS = (20, 30)


def get_options(reductions=None):
    requested = RATIOS if reductions is None else [
        row["reduction"] if isinstance(row, dict) else row for row in reductions
    ]
    if len(set(requested)) != len(requested):
        raise ValueError("Each reduction must appear once")
    options = []
    for ratio in requested:
        if type(ratio) is not int or ratio < 3:
            raise ValueError(f"Expected an integer reduction of at least 3, got {ratio!r}")
        if ratio not in RATIOS:
            raise ValueError(f"Unknown gearbox ratio: {ratio}")
        option = {
            "style": "version_11",
            "reduction": ratio,
            "reduction_text": f"{ratio}_to_1",
            "native_master": "version_11.solidcraft",
            "native_parameters": {"reduction": str(ratio)},
        }
        if ratio > 20:
            # Preserve the reference orbit-to-lobe-pitch proportion on the same casing.
            option["native_parameters"]["eccentricity"] = "30 mm / reduction"
        options.append(option)

    for option in options:
        option["taxonomy_1"] = "oobb"
        option["taxonomy_2"] = "part"
        option["taxonomy_3"] = "motor_gearbox"
        option["taxonomy_4"] = "cycloidal"

        value_name = "style"
        value = option.get(value_name, "version_11")
        option["taxonomy_5"] = f"{value}"

        value_name = "reduction_text"
        value = option.get(value_name, None)
        option["taxonomy_6"] = f"{value}_reduction"

        oobb_details = {}
        value_name = "style"
        value = option.get(value_name, "version_11")
        oobb_details["oobb_name"] = value
        oobb_details.update(copy.deepcopy(option))
        oobb_details["oobb_type"] = "cycloidal"
        oobb_details["run_scad"] = False
        oobb_details["run_solidcraft"] = True
        option["oobb_details"] = oobb_details

    return options


def main(**kwargs):
    options = get_options(kwargs.get("reductions"))
    extras = []
    for option in options:
        if kwargs.get("style") and option["style"] != kwargs["style"]:
            continue
        extra = {}
        extra.update(option)
        extras.append(extra)

    import working_oomp_populate_extra_detail

    working_oomp_populate_extra_detail.main(extras=extras)
    write_extras(extras)




def define_assembly_cards(ratio=20):
    """Explosion heights are above the socket-end bench, in CAD millimetres."""
    return [
        {
            "title": "Set down the socket end",
            "action": "Place the socket-side cylinder, black carrier cap and yellow two-socket journal flange-down on a support with access underneath. The native model calls this end “upper”.",
            "add": {"output_cap_cylinder": 0, "carrier_top_cap": 0, "shaft_end_upper": 0},
        },
        {
            "title": f"Stand all {ratio + 8} screws",
            "action": f"Insert {ratio} M3 × 30 socket caps through the outer ring, six M3 × 35 through the carrier and two M3 × 35 through the yellow journal. Both shaft screw heads sit at this end. Support the heads while building upward.",
            "add": {"hardware_ring_*": -16, "hardware_drive_caps*": -16, "hardware_drive_shanks*": -16, "hardware_shaft_M3x35*": -16},
        },
        {
            "title": "Seat the first two bearings",
            "action": "Lower the 6810 over the black journal and the centred 6704 over the yellow journal. Seat both flat on their shoulders.",
            "add": {"hardware_6810_top": 18, "hardware_6704_top": 22},
        },
        {
            "title": "Place the empty nut trays",
            "action": "Lower the square socket-side plate. Slide the large black eight-pocket tray and small turquoise four-pocket tray over the standing screws, with both sets of pockets open upward.",
            "add": {"output_cap_plate": 12, "carrier_top_nut_tray": 19, "shaft_mount_upper_nut_tray": 25},
        },
        {
            "title": "Load the twelve mounting nuts",
            "action": "Drop eight M3 nuts into the black tray and four into the turquoise tray. Seat the flats in their pockets while the screw heads remain supported.",
            "add": {"hardware_carrier_top_mount_nut*": 14, "hardware_shaft_mount_nut_upper*": 14},
        },
        {
            "title": "Close both trays",
            "action": "Lower the socket-end carrier core over the eight outer nuts and the small shaft nut carrier over the four inner nuts. Both covers should settle flat.",
            "add": {"carrier_top": 16, "shaft_mount_upper": 21},
        },
        {
            "title": "Add the sleeves",
            "action": f"Slide {ratio} yellow contact sleeves onto the ring screws and six yellow guide sleeves onto the inner screws. Seat the six guides in the carrier sockets.",
            "add": {"printed_contact*": 12, "printed_drive*": 12},
        },
        {
            "title": "Start cam B",
            "action": "Slide the B outer cam onto the two shaft screws with its narrow eccentric journal facing up.",
            "add": {"shaft_cam_b_outer": 18},
        },
        {
            "title": "Prepare disc B",
            "action": "On the bench, seat one 6704 between the B screw half and the B nut half. Match the three clamp holes before closing the halves.",
            "add": {"rotor_b": 48, "hardware_6704_disc_b": 60, "rotor_b_cap": 72},
        },
        {
            "title": "Clamp disc B",
            "action": "Fit three M3 nuts and three M3 × 6 countersunk screws. Seat the heads flush. Orient the closed disc with the screw heads facing down for installation.",
            "add": {"hardware_disc_b_M3*": 37, "hardware_disc_b_nut*": 70},
        },
        {
            "title": "Install B and oppose the cams",
            "action": "Lower the closed B disc over all six guide sleeves and onto the B journal. Point its indexed clamp screw toward the wide guide gap. Add B inner cam journal-down, then A inner cam journal-up. Their eccentric offsets face opposite ways.",
            "add": {"shaft_cam_b_inner": 22, "shaft_cam_a_inner": 32},
        },
        {
            "title": "Prepare disc A",
            "action": "Seat a 6704 bearing between the two A disc halves. Orient the A screw half upward and align all three clamp holes.",
            "add": {"rotor_a_cap": 48, "hardware_6704_disc_a": 60, "rotor_a": 72},
        },
        {
            "title": "Clamp disc A",
            "action": "Fit three M3 nuts and three M3 × 6 countersunk screws. Seat the heads flush with the upward-facing screw half.",
            "add": {"hardware_disc_a_nut*": 38, "hardware_disc_a_M3*": 71},
        },
        {
            "title": "Install A and close its cam",
            "action": "Lower disc A onto the six guides and the A journal with the indexed clamp screw toward the same wide gap. Fit the A outer cam journal-down.",
            "add": {"shaft_cam_a_outer": 21},
        },
        {
            "title": "Fit the finishing plate and carriers",
            "action": "Lower the nut-side square plate, carrier core and shaft nut carrier. Seat the six guide sleeves in the matching recesses. Keep both sets of mounting pockets facing up.",
            "add": {"output_nut_plate": 13, "carrier_bottom": 20, "shaft_mount_lower": 25},
        },
        {
            "title": "Load the finishing nuts",
            "action": "Seat eight M3 mounting nuts in the black core and four in the turquoise shaft nut carrier before fitting the bearings and caps.",
            "add": {"hardware_carrier_bottom_mount_nut*": 16, "hardware_shaft_mount_nut_lower*": 16},
        },
        {
            "title": "Seat the second pair of bearings",
            "action": "Lower the second 6810 onto the casing and carrier seat. Lower the remaining centred 6704 onto the shaft nut carrier.",
            "add": {"hardware_6810_bottom": 17, "hardware_6704_base": 22},
        },
        {
            "title": "Close the nut end",
            "action": "Lower the nut-side cylinder, black carrier cap and yellow two-hex-pocket end journal. Check that the two shaft screw tips reach the yellow hex pockets.",
            "add": {"output_nut_cylinder": 15, "carrier_bottom_cap": 18, "shaft_end_lower": 22},
        },
        {
            "title": "Secure and turn the gearbox",
            "action": f"Start both shaft-tie nuts, the six guide nuts and the {ratio} ring nuts. Snug each group evenly, turning the shaft by hand between groups. For {ratio}:1, mount the black inner carrier to the frame, drive the yellow centre and attach the load to the turquoise outer casing.",
            "add": {"hardware_shaft_tie_nut*": 12, "hardware_drive_nuts*": 12, "hardware_M3_ring_nuts*": 12},
        },
    ]


def define_assembly_book(ratio=20):
    return {
        "cover_title": "Cycloidal gearbox",
        "cover_subtitle": f"{ratio}:1 reduction / manual input",
        "project_name": "OOBB cycloidal gearbox",
        "project_url": "https://github.com/oomlout/oomlout_oobb_part_motor_gearbox_cycloidal_version_5",
        "viewer_url": f"https://oomlout.github.io/oomlout_oobb_part_motor_gearbox_cycloidal_version_5/{ratio}-to-1/",
        "description": f"A 3D-printable cycloidal gearbox for OOBB mechanisms. Drive the centre shaft and hold the inner carrier fixed to turn the outer casing once per {ratio} input turns.",
        "details_title": "Building the gearbox",
        "details": [
            f"Print all four plates from the P1S project. This build uses two square flanges and {ratio} loose contact sleeves.",
            "Two 6810 bearings (50 × 65 × 7 mm) support the casing. Four 6704 bearings (20 × 27 × 4 mm) support the shaft and cycloids.",
            f"Use {ratio} 7 mm OD × 16 mm contact sleeves and six matching guide sleeves.",
            "Use a 2.5 mm hex key for the socket caps and a 2 mm key for the countersunk disc screws.",
            "Start at the socket end and build upwards. The two shaft screws stay parallel throughout assembly.",
            f"Mount the black carrier for {ratio}:1 casing output. With the casing fixed, the carrier gives {ratio - 1}:1 in the opposite direction.",
            "Regenerate the drawings from the project root with python working.py --assembly-only.",
            "Clearances and nut access were checked in CAD. Physical fit and load capacity are unverified.",
            "AI-generated CAD images and instructions. Errors possible.",
        ],
        "signature_pages": 4,
        "summary_step": True,
        "summary_view": "book_cover",
        "summary_title": "Printed parts",
        "hardware_title": "Hardware",
        "viewer_start": "page-03",
        "viewer_layout": "a4-landscape-four-step",
        "logo_svg": "gearbox_native/book/oomlout.svg",
        "logo_symbol_subpaths": 3,
    }

if __name__ == "__main__":
    main()
