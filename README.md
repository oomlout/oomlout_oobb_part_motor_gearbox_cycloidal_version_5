# Cycloidal gearbox — native SolidCraft V9

The current design is **35:1 in a 74×74 mm (5×5 OOBB) output**, using **6808 casing bearings**, **1.5 mm contact radius** and **0.7 mm eccentricity**. Six guide screws and all three standoffs fit. V8 remains sealed.

Open [the native master](gearbox_controls.solidcraft) and change its favourite parameters in SolidCraft. The complete nine-part gearbox updates inside the file. [Parameter and printing guide](NATIVE_V9.md) · [Verification](solidcraft/native_v9.json) · [Sealed V8](releases/version_8/README.md)

The three output pieces have full-width square outlines. Only the centre M6 hole on each edge is omitted. Four inner half-grid M3 socket-cap screws join the stack; the lower holder retains overhang-enabled M3 and M6 nut pockets.

The wiggle shaft uses shared named D-key geometry and bearing-derived journals. Radial key clearance is 0.10 mm and journal clearance is 0.075 mm. The contact pitch is 27.9 mm; casing height remains 27.3 mm above its lower face.

[35:1 parts and hardware](parts/oobb_part_motor_gearbox_cycloidal_version_9_35_to_1_reduction/README.md) · [Exploded view](parts/oobb_part_motor_gearbox_cycloidal_version_9_35_to_1_reduction/exploded.png) · [Print layout](parts/oobb_part_motor_gearbox_cycloidal_version_9_35_to_1_reduction/3dpr.png) · [10:1 preset](parts/oobb_part_motor_gearbox_cycloidal_version_9_10_to_1_reduction/README.md)

Both presets share the same feature graph and differ only in exposed native parameters. The 10:1 preset uses 0.9 mm eccentricity and disables the standoffs. View files are independent snapshots; save and run `python action_export_native.py` after editing. Use `--populate` to recreate the current catalogue presets through populate and working_oomp. The original V9 20:1 folder remains a reference snapshot.

Native health, equation sampling, STEP/STL, save/reopen edits, motion and hardware clearances are checked under the unchanged acceptance policy. Physical printing and load testing remain outstanding. [Development notes](VERSION_9_DEVELOPMENT.md) describe the revision.
