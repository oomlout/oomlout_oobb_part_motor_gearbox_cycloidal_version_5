"""Verbose catalogue/reference recipe; native V9 parameters live in its CAD file."""
import copy
from oomp_populate_helper import build_oomp_id, write_extras


def get_options(reductions=None):
    options = []

    # Versions 1–8 are sealed in releases/. Version 9 starts from the accepted native baseline.
    # Add another option block here for another reduction.
    if True:
        option = {}
        option["style"] = "version_9"
        option["architecture"] = "simple_6810"
        option["drive_connection"] = "grub_nut"
        option["direct_stack_layout"] = "base_grub"
        option["reduction"] = 35 / 1
        option["reduction_text"] = f"{int(option['reduction'])}_to_1"
        option["lobe_radius"] = 1.5  # Contact RADIUS: 3 mm diameter.
        option["radius_offset"] = 0.70
        option["pitch_radius_increment"] = 0.05
        option["post_fasteners"] = True
        option["split_output_casing"] = True
        option["lobe_eccentricity_ratio"] = 0.90  # Larger contacts need gentler root curvature.
        option["shaft_radius_name"] = "m5"
        option["rotor_thickness"] = 5
        option["disc_gap"] = 0.5
        option["guide_pin_diameter"] = 3
        option["guide_pin_count"] = 6
        option["motor_hole_pitch"] = 31
        option["motor_screw_length"] = 14
        option["native_parameters"] = {
            "reduction": "35",
            "casing_bearing": "6808",
            "bottom_bearing": "6702",
            "top_bearing": "6702",
            "eccentricity": "0.7 mm",
            "contact_radius": "1.5 mm",
            "guide_screw_length": "25 mm",
            "standoff_radius": "2.7 mm",
            "guide_radius": "1.5 mm",
            "guide_outer_radius": "1.5 mm",
            "guide_count": "6",
            "automatic_internal_positions": "1",
        }
        options.append(copy.deepcopy(option))

    # This variant is made only by editing favourite native SolidCraft parameters.
    # It shares the complete V9 feature graph with the 35:1 master.
    if True:
        option = copy.deepcopy(options[0])
        option["reduction"] = 10 / 1
        option["reduction_text"] = "10_to_1"
        option["native_parameters"] = {
            "reduction": "10",
            "casing_bearing": "6808",
            "bottom_bearing": "6702",
            "top_bearing": "6702",
            "eccentricity": "0.9 mm",
            "contact_radius": "1.5 mm",
            "guide_screw_length": "25 mm",
            "standoff_radius": "0 mm",
            "guide_radius": "1.5 mm",
            "guide_outer_radius": "1.5 mm",
            "guide_count": "6",
            "automatic_internal_positions": "1",
        }
        options.append(copy.deepcopy(option))

    # Bearing-supported input, with its own fully editable native master.
    if True:
        option = copy.deepcopy(options[0])
        option["input_variant"] = "bearing_input"
        option["native_master"] = "gearbox_bearing_controls.solidcraft"
        option["taxonomy_7"] = "bearing_input"
        options.append(copy.deepcopy(option))

    # A separate native style. Its master contains the shaft, spacers and both plate patterns.
    if True:
        option = {}
        option["style"] = "simple_double_bearing_version_2"
        option["reduction"] = 20
        option["native_master"] = "simple_double_bearing_version_2.solidcraft"
        option["native_parameters"] = {
            "reduction": "20",
        }
        options.append(copy.deepcopy(option))

    # Motor adapter is its own part; the accepted manual-input part stays unchanged.
    if True:
        option = {}
        option["style"] = "simple_double_bearing_version_2"
        option["reduction"] = 20
        option["input_variant"] = "nema17_flange"
        option["motor_depth"] = 40
        option["taxonomy_7"] = "nema17_flange"
        option["native_master"] = "simple_double_bearing_version_2_nema17_flange.solidcraft"
        option["native_parameters"] = {
            "reduction": "20",
            "motor_depth": "40 mm",
            "coupler_bolt_circle_diameter": "16 mm",
        }
        options.append(copy.deepcopy(option))

    # Optional programmatic variants use the same taxonomy and generation path.
    if reductions is None:
        from gearbox_native.controls import saved_overrides, to_kwargs, VALUES_PATH
        options[0].update(to_kwargs(saved_overrides()))
        if VALUES_PATH.exists():
            import json
            revision = json.loads(VALUES_PATH.read_text(encoding='utf-8')).get('revision')
            if revision:
                options[0]['taxonomy_7'] = revision
    if reductions is not None:
        defaults = {opt["style"]: opt for opt in (options[0], options[3])}
        base = options[0]
        options = []
        for overrides in reductions:
            if overrides.get("input_variant") == "nema17_flange":
                template = next(
                    option for option in get_options()
                    if option.get("input_variant") == "nema17_flange"
                )
            else:
                template = defaults.get(overrides.get("style"), base)
            option = copy.deepcopy(template)
            option.update(overrides)
            options.append(option)

    for option in options:
        if option.get("style") == "simple_double_bearing_version_1":
            raise ValueError("Double-bearing version 1 is sealed; use simple_double_bearing_version_2.")
        if option.get("style") in ("version_1", "version_2", "version_3", "version_4", "version_5", "version_6", "version_7", "version_8"):
            version = option["style"].split("_")[-1]
            raise ValueError(
                f"Version {version} is sealed; use version_9 for new designs."
            )
        reduction = float(option.get("reduction", 12))
        if not reduction.is_integer() or reduction < 3:
            raise ValueError("reduction must be an integer >= 3")
        option["reduction"] = int(reduction)
        option["reduction_text"] = f"{int(reduction)}_to_1"
        if option.get("style") == "simple_double_bearing_version_2":
            option["native_parameters"]["reduction"] = str(int(reduction))
        if option.get("input_variant") == "nema17_flange":
            # The catalogue depth and native parameter are one setting. A copy
            # with motor_depth=48 gets a separate folder and a native 48 mm tube.
            depth = float(option.get("motor_depth", 40))
            if depth <= 10:
                raise ValueError("NEMA17 motor_depth must exceed 10 mm")
            option["native_parameters"]["motor_depth"] = f"{depth:g} mm"
            option["taxonomy_7"] = f"nema17_flange_{depth:g}_mm_motor_depth".replace(".", "d")

        option["taxonomy_1"] = "oobb"
        option["taxonomy_2"] = "part"
        option["taxonomy_3"] = "motor_gearbox"
        option["taxonomy_4"] = "cycloidal"

        value_name = "style"
        value = option.get(value_name, "version_9")
        option["taxonomy_5"] = f"{value}"

        value_name = "reduction_text"
        value = option.get(value_name, None)
        option["taxonomy_6"] = f"{value}_reduction"

        oobb_details = {}
        value_name = "style"
        value = option.get(value_name, "version_9")
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


if __name__ == "__main__":
    main()
