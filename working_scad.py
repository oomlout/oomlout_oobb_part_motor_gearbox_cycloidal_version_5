import copy
import oobb
import yaml
import os
import scad_help


def main(**kwargs):
    make_scad(**kwargs)


def make_scad(**kwargs):
    typ = scad_help.get_typ(**kwargs)
    oomp_mode = "project"
    # oomp_mode = "oobb"
    filt = ""
    build_variables = scad_help.get_build_variables(typ, filter=filt)
    for key, value in build_variables.items():
        kwargs.setdefault(key, value)
    kwargs.setdefault("oomp_mode", oomp_mode)
    parts = get_parts(kwargs, oomp_mode)

    kwargs["parts"] = parts

    scad_help.make_parts(**kwargs)

    if kwargs["navigation"]:
        oobb_style = False
        sort = scad_help.get_navigation_sort(oobb_style=oobb_style)
        scad_help.generate_navigation(sort=sort)


def get_parts(kwargs, oomp_mode):
    parts = []

    # load parts from parts/folder/working.yaml
    parts_directory = kwargs.get(
        "parts_directory", os.path.join(os.path.dirname(__file__), "parts")
    )
    if not os.path.isdir(parts_directory):
        return parts

    for folder in os.listdir(parts_directory):
        folder_path = os.path.join(parts_directory, folder)
        if not os.path.isdir(folder_path):
            continue
        if os.path.isfile(os.path.join(folder_path, "SEALED.json")):
            continue

        working_yaml_path = os.path.join(folder_path, "working.yaml")
        if not os.path.isfile(working_yaml_path):
            continue

        with open(working_yaml_path, "r", encoding="utf-8") as infile:
            loaded_part = yaml.safe_load(infile)

        if not isinstance(loaded_part, dict):
            continue

        oobb_details = loaded_part.get("oobb_details")
        if not isinstance(oobb_details, dict):
            continue
        import working_cad
        if not working_cad.enabled(oobb_details, "scad"):
            continue

        part = loaded_part

        part_kwargs = copy.deepcopy(kwargs)
        part_kwargs.update(copy.deepcopy(loaded_part.get("kwargs", {})))
        part_kwargs.update(copy.deepcopy(oobb_details))
        for key in ("modes", "save_type", "overwrite", "filter", "navigation", "oomp_run"):
            if key in kwargs:
                part_kwargs[key] = copy.deepcopy(kwargs[key])
        part_kwargs = working_cad.geometry_parameters(part_kwargs)
        part["kwargs"] = part_kwargs
        part["oobb_name"] = part.get(
            "oobb_name", oobb_details.get("oobb_name", "default")
        )

        if oomp_mode == "oobb":
            part["kwargs"]["oomp_size"] = part["oobb_name"]

        parts.append(part)

    return parts


def get_version_1(thing, **kwargs):
    raise ValueError(
        "Version 1 is sealed; use version_7 or inspect releases/version_1."
    )


def get_version_2(thing, **kwargs):
    raise ValueError(
        "Version 2 is sealed; use version_7 or inspect releases/version_2."
    )


def get_version_3(thing, **kwargs):
    raise ValueError(
        "Version 3 is sealed; use version_7 or inspect releases/version_3."
    )


def get_version_4(thing, **kwargs):
    raise ValueError("Version 4 is sealed; inspect releases/version_4")


def _legacy_reference(thing, **kwargs):
    """One catalogue item is a complete gearbox, not one item per printed piece."""
    from gearbox.parts import build, layout, resolve

    config = resolve(kwargs)
    pieces = build(**config)
    placements = layout(pieces, **config)
    thing["gearbox"] = {"config": config, "pieces": pieces, "layout": placements}
    for placement in placements:
        components = copy.deepcopy(pieces[placement["part"]]["thing"]["components"])
        thing["components"].append(
            {
                "type": "rotation",
                "typetype": "p",
                "pos": placement["pos"],
                "rot": [0, 0, 0],
                "objects": components,
            }
        )


def get_base(thing, **kwargs):
    raise ValueError(
        "Unknown gearbox style; add a get_<style> builder in working_scad.py"
    )


def get_cycloidal(thing, **kwargs):
    raise ValueError("Version 6 uses native SolidCraft; run action_make_solidcraft.py")


if __name__ == "__main__":
    main()
