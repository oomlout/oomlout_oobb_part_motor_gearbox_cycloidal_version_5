# Cycloidal gearbox — native SolidCraft V7

Open [gearbox_controls.solidcraft](gearbox_controls.solidcraft) and edit its
favourite parameters. The complete eight-part gearbox recalculates **inside
SolidCraft**, including reduction/count, cycloid equations, seats, journals,
clearance tracks, casing, axial stack and assembly positions. No external
regeneration action is needed.

[Parameter guide and examples](NATIVE_V7.md) ·
[Verification index](solidcraft/native_v7.json) ·
[V6 sealed release](releases/version_6/README.md)

The starting design remains 20:1, with a 72.3 mm core diameter, 32 mm maximum
height above the motor face, 6810 casing bearings, 6703 disc bearings, a 6701
front shaft bearing and direct 5 mm input. Contacts have a 3 mm **radius**;
eccentricity is 1.4 mm. The two 5 mm discs have a 0.5 mm gap.

Set `explode=12 mm` to separate the printed components, or `print_layout=1`
to put them on their print faces. Save your changes normally. For optional
STEP/STL exports and view snapshots, run `python action_export_native.py`.
The exporter reads the saved native geometry and never overwrites the master.

Initial [assembled](parts/oobb_part_motor_gearbox_cycloidal_version_7_20_to_1_reduction/true.solidcraft),
[print](parts/oobb_part_motor_gearbox_cycloidal_version_7_20_to_1_reduction/3dpr.solidcraft)
and [exploded](parts/oobb_part_motor_gearbox_cycloidal_version_7_20_to_1_reduction/exploded.solidcraft)
snapshots are in the V7 part directory. Individual current STEP/STL files are
in its `native_parts/` folder. Snapshots are independent copies; continue editing
the root master to keep one working source.

The shared MCP helper now provides `cycloidal_pattern` and `native_design`
components. Python authors the initial history and verifies exports; it does
not supply geometry during native parameter edits. The fixed mathematical
sampling is checked to 0.005 mm by the export utility. The existing CAD
acceptance policy is unchanged, and V1–V6 remain sealed.

Physical print/load testing is still required. Older recipe/control tools and
inherited documents are retained for comparison; legacy regeneration is
blocked from replacing the native master. See [development and validation
notes](VERSION_7_DEVELOPMENT.md) for the evidence and known legacy test failures.
