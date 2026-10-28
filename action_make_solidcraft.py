"""Populate the parts and generate verified SolidCraft outputs only."""


def main(**kwargs):
    from gearbox_native.project import native_only
    if native_only():
        from action_export_native import main as export_native
        return export_native([])
    kwargs["run_oomp_populate"] = True
    kwargs["run_oomp"] = True
    kwargs["run_action"] = False
    kwargs["run_scad"] = False
    kwargs["run_solidcraft"] = True
    kwargs["run_svg"] = False
    # SCAD stays off; native STL is enabled by export_stl below.
    kwargs["generate_stl"] = False

    kwargs["export_extras"] = kwargs.get("export_extras", True)  # STEP and PNG previews.
    kwargs["export_stl"] = kwargs.get("export_stl", True)
    kwargs["verify_solidcraft"] = kwargs.get("verify_solidcraft", True)

    import working
    working.run(**kwargs)
    if kwargs.get("navigation", True):
        import scad_help
        scad_help.generate_navigation(sort=scad_help.get_navigation_sort(oobb_style=False))


if __name__ == "__main__":
    main()
