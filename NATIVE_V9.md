# V9 native 5×5 gearbox

Open the root `gearbox_controls.solidcraft` in SolidCraft and use **Parameters**.
The file owns the complete feature graph; no external regeneration process or
linked part is needed. All clearances below are radial unless stated otherwise.

The main preset is **35:1** with 34 rotor lobes, **1.5 mm contact radius**,
**0.7 mm eccentricity**, two **6808** casing bearings, two **6702** disc bearings
and a **6702** front shaft bearing supporting the external-drive sleeve. The output is **74×74 mm**, the standard
outer size of a 5×5 OOBB plate. All six guide screws and three standoffs remain.

## Mechanical parameters

| Control | Main preset | Effect |
|---|---:|---|
| `reduction` | 35 | Ring contacts; rotor lobes are one fewer. Current range 10–35. |
| `contact_radius` | 1.5 mm | Circular contact radius, not diameter. |
| `eccentricity` | 0.7 mm | Opposed disc orbit radius. |
| `automatic_pitch` | 1 | Sizes pitch for undercut, contact spacing and internal features. |
| `radius_buffer` | 0 mm | Extra automatic pitch; the fixed footprint still limits it. |
| `contact_pitch_radius` | 27.9 mm | Used only with automatic pitch off. |
| `profile_clearance` | 0.15 mm | Rotor-to-contact clearance. |
| `casing_bearing` | 6808 | Design choice: 40 bore × 52 OD × 7 mm. Keep this for the 5×5 configuration. |
| `bottom_bearing`, `top_bearing` | 6702 | Disc bearings: 15 bore × 21 OD × 4 mm. |
| `disc_thickness` | 5 mm | Each disc's thickness. |
| `disc_gap` | 0.5 mm | Axial gap between discs. |
| `standoff_radius` | 2.7 mm | Set to 0 to remove posts and matching registers/holes. |
| `guide_count` | 6 | Guide screw count; changed counts need fit checks. |
| `guide_radius` | 1.5 mm | M3 screw radius. |
| `guide_outer_radius` | 1.5 mm | Spacer outside radius; equal to screw radius means no sleeve. |
| `guide_screw_length` | 25 mm | Under-head length, with linked lower nut position. |
| `automatic_internal_positions` | 1 | Computes guide and standoff pitch radii. |

Manual `guide_pitch_radius` and `standoff_pitch_radius` apply only with automatic
internal positioning off. The main preset resolves to 15 mm guide pitch and
16.15 mm standoff pitch. The 10:1 preset shares the same graph and 5×5 output,
with 0.9 mm eccentricity and disabled standoffs. Its local master is independently editable.

## Wiggle shaft

The lower hub fits the motor shaft. The upper hub receives its D-key. Two
opposed journals still carry the 6702 bearings.

| Fit control | Default | Result |
|---|---:|---|
| `shaft_bore_clearance` | 0.20 mm | Ø5.40 mm entry for the Ø5 mm shaft and the upward M2.5 cap head. |
| `motor_shaft_length` | 24 mm | Projection measured from the motor face. |
| `motor_spacer_depth` | 8 mm | Motor setback behind the plate. The spacer has a Ø30 mm centre opening. |
| `wiggle_journal_clearance` | 0.05 mm | Ø14.90 mm eccentric and support journals. |
| `wiggle_key_clearance` | 0.05 mm | Radial and flat clearance on the D-key. |
| `wiggle_axial_clearance` | 0.10 mm | Key socket end allowance. |

The stepper version uses an M3 × 8 countersunk screw and M3 nut to clamp
the motor shaft. Its 8 mm spacer has a full-height, 10 mm access gap.
The Ø5.40 mm motor bore provides entry for an upward M2.5 × 12 joining
screw, with its nut loaded into the upper hub from above. Tighten this join
before inserting the motor. Use M3 × 14 countersunk motor screws.

Both versions now carry a separate D-socket sleeve through the front 6702.
The sleeve's M3 × 6 socket-cap screw presses into a shallow recess in the
upper D-key. Load its M3 nut sideways through the collar, then tighten the
screw through the square head-access opening. The sleeve provides a 12 mm
long exposed D-shaft with nominal Ø14.90 mm round diameter and a flat
6.5 mm from the centre. Its external end is at 53.8 mm above the baseplate.
The sloping collar is built into the print geometry.

## Bearing-supported input

The `bearing_input` populate item has its own parts folder and a native
master named `gearbox_bearing_controls.solidcraft` at the project root.
Its local editable file is also named `gearbox_controls.solidcraft`.
A separate **42 × 42 × 6.5 mm bearing holder** bolts beneath the **same motor
plate used by the stepper variant**. Its 6702 recess opens upward. Print the
cup on its broad underside: the central opening grows wider toward the top,
so the bearing seat has no unsupported roof. Four **M3 × 10 countersunk screws**
use the existing **31 mm square NEMA17 pattern** and bottom-loaded M3 nuts
with `overhang=True`. The bearing variant has fourteen printed pieces; the stepper variants have eleven.

The bearing-only lower and upper eccentric hubs each split lengthwise into an A/B pair. Print all four on the flat split faces, the retainer wide face down, and the open-ended D-sleeve upright. The four 6702 bearings locate the journals. The asymmetric key fixes the relative phase of the two hubs. Load the M3 nut from the split in the upper hub. One **M3 × 35 socket-cap screw** runs up through the washer and both hub pairs. The screw and nut both use OOBB overhang relief. Tighten the screw before sliding the sleeve over the key and fitting its separate M3 × 6 clamp. Allow 3.5 mm beneath the detachable cup for the retaining collar. The D-sleeve drives the input; the outer casing remains the reduced-speed output.

`bearing_holder_depth` changes the cup's underside thickness without moving the bearing. Recheck fastener length after large edits. Load the motor-plate guide/standoff nuts and fit the lower 6702 in the cup before mounting it. For the existing detachable-cup gearbox, print **shaft_reprint/3dpr.stl** (six pieces). For a stepper conversion print **bearing_conversion/3dpr.stl** (the same six pieces plus the cup). The motor plate, front carrier, both rotors and three casing pieces are shared. If replacing the original integrated bearing baseplate, also print `native_parts/motor_mount.stl`. The bearing parts folder includes `shaft_stackup.png` and `HARDWARE.md`.

The two input arrangements share the same core feature builders. Each
saved native master contains its own complete editable graph. Populate
selects the appropriate master and applies its exposed parameters.
Changing one saved file does not rewrite the other file automatically.

## Clearance experiments

| Native control | Selected value |
|---|---:|
| `profile_clearance` | 0.15 mm |
| `guide_running_clearance` | 0.10 mm |
| `post_running_clearance` | 0.10 mm |
| `wiggle_key_clearance` | 0.05 mm |
| `wiggle_journal_clearance` | 0.05 mm |
| `drive_socket_clearance` | 0.05 mm |
| `drive_extension_length` | 12 mm |
| `drive_shaft_flat` | 6.5 mm |

Track allowances are added to the required eccentric orbit. The 35:1 contact
pitch and guide/post centres match the earlier gearbox, allowing direct
rotor comparisons. The running-fit experiments include the original,
balanced and close settings in `clearance_trials/`, each with its own
print layout and editable native file. `fit_samples/3dpr.stl` contains
6702 journal gauges and D-socket samples. See their instructions before
choosing tighter settings for a complete print.

The selected clearances are a geometric trial. Actual backlash depends on
printed dimensions, bearing fit, fastener clamping and elastic deformation.
The recorded profile-only comparison excludes those other sources.

## Output mounting and printing

The lower bearing holder, middle lobe band and upper bearing holder remain
separate. Each has a full 74×74 mm rounded-square outline. Only the centre M6
hole on each edge is omitted. There are twelve unique perimeter M6 holes,
sixteen perimeter M3 holes, and four M3 joining holes at `(±22.5, ±22.5)` mm.

The joining holes sit on the inner OOBB half-grid to separate their nut pockets
from the M6 pockets. Lower M6 and M3 pockets all use `overhang=True`; M6 nuts
are optional in unused mounting holes. Four recessed M3 socket-cap screws join
the stack. Their default length is 20 mm; changed axial stacks select 5 mm increments.

Print the lower holder inverted on its split face, the upper holder on its
split face, and the band on either end. Native print layout supplies these
orientations. Casing height remains 27.3 mm; the drive reaches 53.8 mm above the gearbox mounting face (61.8 mm above the motor face with the stepper spacer).

The native print layout is about 309 x 228 mm. Each populated folder also has
`compact_print/3dpr.stl`, which packs its eleven or fourteen checked parts within a
240 x 240 mm area without changing their geometry or print orientation.

Native guards stop edits that exceed the fixed footprint or leave less than
1 mm of material between the working cavity and the closest perimeter M3 holes.
This is not a universal fit check: hardware and motion need verification for new combinations.

## Views and export

Use `explode=12 mm` for the exploded view, `print_layout=1` for printing, or
`print_layout=0` and `explode=0 mm` for assembly. `input_angle` positions the
mechanism; one output revolution needs 360° × reduction at the input.

Save first, then run `python action_export_native.py`. It reads the saved master
and exports native assembled/exploded/print snapshots and STEP/STL files under
`outputs/native_v9/`; it never overwrites the master. Pass `--design` for another
saved native file. View files are independent snapshots and need re-exporting after edits.

`python action_export_native.py --populate` recreates all catalogue presets
from the two root masters selected by populate, using exposed parameter overrides. Preserve independent
variant edits before repopulating. The verbose populate → working_oomp route
remains in place; legacy regeneration cannot replace the native master.

Fixed equation sampling is checked through shared `validate_edit` to 0.005 mm.
Regenerate the mathematical construction and repeat native checks if an edit
needs finer sampling. V1–V8 and the acceptance policy remain unchanged.
See `solidcraft/native_v9.json` for evidence; physical print/load testing remains outstanding.

## Reproducing the drive experiments

`gearbox_native.native_v9_drive` authors the two native input architectures from
shared builders. Use `--name <new-build-name>` and add `--bearing` for the bearing
base. It refuses unexpected disconnected bodies. Routine edits should still be
made in the saved native master; rebuilding replaces its editable history.

`gearbox_native.clearance_trials` reproduces the three matched 35:1 rotor pairs
and their 180-angle contact checks. `gearbox_native.drive_fit_samples` produces
the small bearing and D-socket gauges. `gearbox_native.verify_native_drive`
checks exported assembly BReps against hardware, bearing and nut-loading paths.
`gearbox_native.verify_drive_edit` makes and reopens a real native drive edit.
Run these modules with the CAD Python configured in `solidcraft/config.json`.
