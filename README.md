# Cycloidal gearbox — native SolidCraft V8

Open [gearbox_controls.solidcraft](gearbox_controls.solidcraft) and edit its
favourite parameters. The complete nine-part gearbox recalculates **inside
SolidCraft**, including reduction/count, cycloid equations, seats, journals,
clearance tracks, casing, axial stack and assembly positions. No external
regeneration action is needed.

[Parameter guide and examples](NATIVE_V8.md) ·
[Verification index](solidcraft/native_v8.json) ·
[V7 sealed release](releases/version_7/README.md)

V7 is sealed. V8 now has separate lower bearing holder, lobe band and upper
bearing holder, with full-depth OOBB tabs and recessed M3 socket-cap joining
screws. The lower holder includes OOBB overhang nut pockets for M3 joining and
M6 mounting hardware.

The starting design remains 20:1, with a 72.3 mm core diameter, 32 mm maximum
height above the motor face, 6810 casing bearings, 6703 disc bearings, a 6701
front shaft bearing and direct 5 mm input. Contacts have a 3 mm **radius**;
eccentricity is 1.4 mm. The two 5 mm discs have a 0.5 mm gap.

A second populate entry provides a compact **10:1** variant with **1.5 mm contact
radius**, 0.9 mm eccentricity, 6808 casing bearings and 6702 cycloid bearings.
Its casing core is **56.2 mm diameter**. M6 hardware clearance keeps the tabs
on 7 × 7 OOBB positions. It uses the
same native feature graph; only exposed parameter values differ.

Set `standoff_radius=0` to remove the printed posts and their holes. Guide screw
count, screw radius and spacer outside radius are independent native controls.
Automatic internal positions let smaller ratios shrink until another clearance
or bearing dimension sets the minimum.

Change `casing_bearing` to select both casing bearings from 40 catalogue options,
including the added 6708–6712 sizes. Seats, journals, shoulders and spacing follow
the selection inside SolidCraft. Casing fit guards are optional and off by default.
See [the bearing table and editing notes](parts/oobb_part_motor_gearbox_cycloidal_version_8_20_to_1_reduction/CASING_BEARINGS.md).

Set `explode=12 mm` to separate the printed components, or `print_layout=1`
to put them on their print faces. Save your changes normally. For optional
STEP/STL exports and view snapshots, run `python action_export_native.py`.
The exporter reads the saved native geometry and never overwrites the master.

Current [assembled](parts/oobb_part_motor_gearbox_cycloidal_version_8_20_to_1_reduction/true.solidcraft),
[print](parts/oobb_part_motor_gearbox_cycloidal_version_8_20_to_1_reduction/3dpr.solidcraft)
and [exploded](parts/oobb_part_motor_gearbox_cycloidal_version_8_20_to_1_reduction/exploded.solidcraft)
snapshots are in the V8 part directory. Individual current STEP/STL files are
in its `native_parts/` folder. Snapshots are independent copies; continue editing
the root master to keep one working source.

The shared MCP helper now provides `cycloidal_pattern` and `native_design`
components. Python authors the initial history and verifies exports; it does
not supply geometry during native parameter edits. The fixed mathematical
sampling is checked to 0.005 mm by the export utility. The existing CAD
acceptance policy is unchanged, and V1–V7 remain sealed.

Physical print/load testing is still required. Older recipe/control tools and
inherited documents are retained for comparison; legacy regeneration is
blocked from replacing the native master. See [development and validation
notes](VERSION_8_DEVELOPMENT.md) for the evidence and known legacy test failures.
