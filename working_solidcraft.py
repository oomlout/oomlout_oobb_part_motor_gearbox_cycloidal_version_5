"""Generate latest-version SolidCraft files; construction is explicit in config."""
import argparse
import copy
import json
import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
CAD_API = "solidcraft"
# Optional cosmetic detail for positive screws, nuts and bearings.
RENDER_DETAIL = False
# Generate only native .solidcraft files by default.
EXPORT_STL = False
EXPORT_EXTRAS = False  # STEP and PNG previews.
VERIFY_SOLIDCRAFT = True

# Explicit extension of the shared recipe schema, including editable defaults.
def _detail_keys():
    # Read only the simple YAML top-level keys without importing CAD packages
    # into the launcher Python.
    names = {'style', 'reduction_text', 'oobb_name', 'oobb_type', 'run_scad', 'run_solidcraft'}
    names.update('taxonomy_' + str(i) for i in range(1, 10))
    for file in ('common_defaults.yaml', 'captured_defaults.yaml', 'compact_defaults.yaml', 'simple_defaults.yaml'):
        for line in (PROJECT / 'gearbox_native' / file).read_text(encoding='utf-8').splitlines():
            if line and not line[0].isspace() and ':' in line:
                names.add(line.split(':', 1)[0])
    names.update(('case_split_z', 'pitch_radius', 'housing_mount_offset', 'housing_screw_length',
                  'eccentric_shoulder_radius', 'print_gap'))
    names.update(('casing_tab_depth','casing_tab_radius','casing_tab_units',
                  'casing_join_screw_length','casing_join_nut_setback','casing_tab_wall_overlap',
                  'casing_tab_join_offset','output_casing_split_z'))
    from gearbox_native.controls import SPECS
    names.update(s['recipe'] for s in SPECS.values() if s['recipe'])
    return sorted(names)

OOBB_DETAILS = _detail_keys()


def get_version_4(thing, **kwargs):
    raise ValueError("Version 4 is sealed; use version_8")


def get_version_5(thing, **kwargs):
    raise ValueError("Version 5 is sealed; use version_8")


def get_version_6(thing, **kwargs):
    raise ValueError("Version 6 is sealed; use version_8")


def get_version_7(thing, **kwargs):
    """Build the current recipe's pieces in one linked print layout."""
    from gearbox_native.captured import resolve, build
    from gearbox_native.parts import layout
    import yaml
    design=yaml.safe_load((PROJECT/'gearbox_native/design.yaml').read_text(encoding='utf-8'))
    overrides=design.get('parameters',{})
    if not isinstance(overrides,dict):raise ValueError('design.yaml parameters must be a mapping')
    unknown=set(overrides)-set(OOBB_DETAILS)
    if unknown:raise ValueError(f'Unknown native design parameters: {sorted(unknown)}')
    kwargs.update(overrides)
    config = resolve(kwargs)
    pieces = build(**config)
    placements = layout(pieces, **config)
    thing['sequential_unions'] = True
    thing['compound_cuts'] = True
    thing["gearbox"] = {"config": config, "pieces": pieces, "layout": placements}
    for placement in placements:
        thing["components"].append({
            "type": "rotation", "typetype": "p", "pos": placement["pos"],
            "rot": [0, 0, 0],
            "objects": copy.deepcopy(pieces[placement["part"]]["thing"]["components"]),
        })


def get_cycloidal(thing, **kwargs):
    # V7 remains readable for reference tests; main blocks legacy writes.
    if kwargs.get("style", "version_8") not in ("version_7", "version_8"):
        raise ValueError("Only V7 reference and V8 recipes are supported; earlier versions are sealed")
    return get_version_7(thing, **kwargs)


def build_policy():
    """Share the stdlib-only per-part policy with the normal SCAD Python."""
    import working_cad
    return working_cad


# Shared support is stdlib-only here; CAD imports run in the configured Python.
def launch_support():
    import importlib.util
    config = json.loads((PROJECT / "solidcraft/config.json").read_text(encoding="utf-8"))
    helper = Path(os.environ.get("OOBB_SOLIDCRAFT_ROOT", config["helper_root"]))
    path = helper / "components/project_launcher/working.py"
    if not path.is_file():
        raise RuntimeError(f"SolidCraft launcher unavailable: {path}; check solidcraft/config.json")
    spec = importlib.util.spec_from_file_location("_project_solidcraft_launcher", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def configuration():
    return launch_support().configuration(PROJECT)


def main(*, solidcraft_context=None, **kwargs):
    from gearbox_native.project import require_legacy_authoring
    require_legacy_authoring()
    context = dict(solidcraft_context or {})
    context.setdefault("export_stl", EXPORT_STL)
    context.setdefault("export_extras", EXPORT_EXTRAS)
    context["verify_solidcraft"] = kwargs.pop("verify_solidcraft", context.get("verify_solidcraft", VERIFY_SOLIDCRAFT))
    return launch_support().main(project_dir=PROJECT, solidcraft_context=context, **kwargs)


def publish(summary):
    if not any(result["status"] == "success" for result in summary["results"]):
        return
    return launch_support().publish(summary, project_dir=PROJECT)


def worker(part_filter, modes, *, export_stl=False, export_extras=False, verify_solidcraft=False):
    from gearbox_native.project import require_legacy_authoring
    require_legacy_authoring()
    from gearbox_native.export import run
    summary=run(PROJECT, part_filter, modes, export_stl=export_stl, export_extras=export_extras, verify_solidcraft=verify_solidcraft)
    if any(r.get('piece')=='print_layout' and r['status']=='success' for r in summary['results']):
        import importlib.util
        spec=importlib.util.spec_from_file_location('_layout_verify',PROJECT/'solidcraft/verify_layout.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.verify(modes,export_stl=export_stl)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the latest gearbox with editable native SolidCraft features.")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--filter", default="", help="Optional part ID substring; default builds all parts.")
    parser.add_argument("--modes", nargs="+", choices=["true", "3dpr"], default=None)
    parser.add_argument("--stl", action=argparse.BooleanOptionalAction, default=EXPORT_STL,
                        help="Also export STL files (default: off).")
    parser.add_argument('--extras', action=argparse.BooleanOptionalAction, default=EXPORT_EXTRAS,
                        help='Also generate STEP and PNG previews (default: off).')
    parser.add_argument('--verify', action=argparse.BooleanOptionalAction, default=VERIFY_SOLIDCRAFT,
                        help='Request extended verification. Geometry and reopening checks are always required for publication.')
    args = parser.parse_args()
    modes = args.modes or configuration()["modes"]
    if args.worker:
        worker(args.filter, modes, export_stl=args.stl, export_extras=args.extras, verify_solidcraft=args.verify)
    else:
        main(solidcraft_context={"part_filter": args.filter, "modes": modes, "export_stl": args.stl, "export_extras": args.extras, "verify_solidcraft": args.verify})
