# Native NEMA17 parameters

Open `gearbox_controls.solidcraft` and use the Parameters menu. Change
`motor_depth` to the motor body length, excluding its shaft. The black tube,
three identical joiners, rear ring and rear cover follow that value. The rear
black mounting face remains 1.5 mm proud of the teal ring.

`coupler_bolt_circle_diameter` is 16 mm. It controls the four M3 axes in both
motor-side 6704 inner pieces. `motor_tube_wall` is 3 mm.

The three joiners share `rear_joiner_height`, `rear_extension_post_radius`,
`rear_joiner_screw_pitch` and `rear_joiner_pitch`. Their stations are 120 degrees
apart. Keep the calculated height expression to retain motor-depth propagation.
Changing the radial placement or screw pitch requires another plate and OOBB
hole clearance check; the current checked values are 52.5 mm and 15 mm.

Set `print_layout=0`, `explode=0 mm` for the assembly. Increase `explode` for
the exploded view, or set `print_layout=1`, `explode=0 mm` for print placement.
The supplied STL files are snapshots and need exporting again after an edit.

To make a separate catalogue variant, set `motor_depth` in the verbose NEMA
entry in `working_oomp_populate.py`. Its depth becomes part of the catalogue ID
and is passed to the native master through `native_parameters`. Regenerate
through the existing populate/working_oomp/working_scad pipeline.
