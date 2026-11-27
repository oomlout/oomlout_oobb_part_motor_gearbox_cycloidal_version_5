# Cycloidal gearbox styles

**Active style · simple_double_bearing_version_2.** The 20:1 external-input gearbox uses two 6810 casing bearings, four 6704 shaft/disc bearings and an eight-disc shaft with an open Ø6.50 mm passage. At 1.5 mm eccentricity, twenty Ø7 × 16 mm printed sleeves form the ring contacts. A connected ring is supplied as a second print option. Six M3 × 35 drive screws pass through matching sleeves and clamp the split inner carriers around their 6704s. Each carrier projects 3 mm beyond its output plate and has eight captive M3 mounting nuts in its flat split. Each 7 mm cycloid captures its 6704 between two screwed halves. Each 6810 fits fully in an 8.5 mm cylinder. The lobe screws fasten a flat 3 mm OOBB plate over its outer race. The stationary carrier cap passes through the bearing to meet the core, retaining the inner race on both sides. The default 7×7 square and the alternate lower-row flange size themselves from the ring. Two opposed M3 × 35 ties clamp the shaft; print two end journals, two nut carriers and four identical eccentric halves. [Parts, printing and assembly](parts/oobb_part_motor_gearbox_cycloidal_simple_double_bearing_version_2_20_to_1_reduction/README.md) · [Editable native master](simple_double_bearing_version_2.solidcraft)

[Labeled exploded diagram](parts/oobb_part_motor_gearbox_cycloidal_simple_double_bearing_version_2_20_to_1_reduction/exploded_labeled.png) · [Sealed double-bearing version 1](releases/simple_double_bearing_version_1/release.json)

Use `python action_export_native.py` to export the selected master or `python action_export_native.py --populate --style simple_double_bearing_version_2` to update its catalogue entry and print files.

For a visible, paced rebuild of a separate copy, run `cad_live_run.bat --speed 4`
from this project directory (the CAD helper directory must be on PATH). It reads
this directory's `working_solidcraft.py` and the active saved native definition,
then saves all run files under `cad_live_run/`. Completed components move above
and below the active piece for viewing, and a lower-left caption explains each
stage. The source master and catalogue outputs remain untouched. Space pauses,
N steps, +/- changes speed and Q stops in the terminal. Use descriptive named
groups in new/revised drawings and retain their memberships; follow the
[helper authoring guide](C:/od/OneDrive/docs/software_cad_mcp_helper/PROJECT_INSTRUCTIONS.md).

## Version 9 · 5×5 gearbox

The V9 design is **35:1 in a 74×74 mm (5×5 OOBB) output**, using **6808 casing bearings**, **1.5 mm contact radius** and **0.7 mm eccentricity**. Six guide screws and all three standoffs fit. V8 remains sealed.

Open [the stepper master](gearbox_controls.solidcraft) or [the bearing-input master](gearbox_bearing_controls.solidcraft) and change its favourite parameters in SolidCraft. Each complete gearbox updates inside its file: eleven printed pieces for stepper input, fourteen for bearing input. [Parameter and printing guide](NATIVE_V9.md) · [Verification](solidcraft/native_v9.json) · [Sealed V8](releases/version_8/README.md)

The three output pieces have full-width square outlines. Only the centre M6 hole on each edge is omitted. Four inner half-grid M3 socket-cap screws join the stack; the lower holder retains overhang-enabled M3 and M6 nut pockets.

For the stepper retrofit, [print the six replacement pieces](parts/oobb_part_motor_gearbox_cycloidal_version_9_35_to_1_reduction/shaft_reprint/3dpr.stl): both hubs, D-sleeve, front carrier and both cycloids. Retain the existing motor mount, casing and 8 mm access spacer. Replace the front 6701 with a 6702. The Ø5.40 mm motor bore, upward M2.5 × 12 joining screw and M3 × 8 countersunk motor clamp remain.

The bearing-only variant bolts a separate 6702 bearing cup beneath the shared stepper motor plate, using four M3 × 10 countersunk screws on the NEMA17 hole pattern. The cup prints flat with its bearing opening upward. Its two eccentric hubs now print as four longitudinal halves. The bottom retainer and open-ended D-sleeve complete the six-piece shaft kit. An M3 × 35 socket-cap screw enters from underneath and engages a side-loaded M3 nut. Allow 3.5 mm below the cup. [Bearing-input parts, prints and hardware](parts/oobb_part_motor_gearbox_cycloidal_version_9_35_to_1_reduction_bearing_input/README.md).

Profile clearance is now 0.15 mm, guide and standoff running allowances 0.10 mm, and key/journal allowances 0.05 mm. Contact pitch stays 27.9 mm and casing height 27.3 mm. [Original, balanced and close rotor trials](parts/oobb_part_motor_gearbox_cycloidal_version_9_35_to_1_reduction/clearance_trials/README.md) and [small fit gauges](parts/oobb_part_motor_gearbox_cycloidal_version_9_35_to_1_reduction/fit_samples/README.md) support physical tuning. Calculated profile-only free movement decreases from 0.94° to 0.70° at the default; this is not measured total gearbox backlash.

[35:1 parts and hardware](parts/oobb_part_motor_gearbox_cycloidal_version_9_35_to_1_reduction/README.md) · [Exploded view](parts/oobb_part_motor_gearbox_cycloidal_version_9_35_to_1_reduction/exploded.png) · [Print layout](parts/oobb_part_motor_gearbox_cycloidal_version_9_35_to_1_reduction/3dpr.png) · [10:1 preset](parts/oobb_part_motor_gearbox_cycloidal_version_9_10_to_1_reduction/README.md)

The two stepper presets share the same feature graph and differ only in exposed native parameters. The bearing-input graph shares its core builders, adds the bearing cup and revises the shaft stack. The 10:1 preset uses 0.9 mm eccentricity and disables the standoffs. View files are independent snapshots; save and run `python action_export_native.py --design gearbox_controls.solidcraft` after editing (`--design gearbox_bearing_controls.solidcraft` for bearing input). Use `--populate` to recreate the catalogue presets through populate and working_oomp. The original V9 20:1 folder remains a reference snapshot.

Native health, equation sampling, STEP/STL, save/reopen edits, motion and hardware clearances are checked under the unchanged acceptance policy. Physical printing and load testing remain outstanding. [Development notes](VERSION_9_DEVELOPMENT.md) describe the revision.
