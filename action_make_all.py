import copy
import working_scad

def main(**kwargs):
    kwargs.setdefault("run_solidcraft", True)
    kwargs.setdefault("export_extras", True)
    kwargs.setdefault("export_stl", True)
    kwargs["run_oomp_populate"] = True

    kwargs["run_oomp"] = True

    kwargs["run_action"] = True
    #kwargs["run_action"] = False

    kwargs["run_scad"] = True

    kwargs["run_svg"] = True

    kwargs["generate_stl"] = True

    import working
    working.run(**kwargs)

if __name__ == '__main__':
    kwargs = {}
    main(**kwargs)
