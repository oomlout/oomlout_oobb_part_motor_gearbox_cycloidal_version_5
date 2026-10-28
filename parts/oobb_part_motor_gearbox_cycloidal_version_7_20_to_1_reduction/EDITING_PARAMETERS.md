# Editing the V7 gearbox parameters

## 1. Open the working master

Open [the project-root gearbox_controls.solidcraft](../../gearbox_controls.solidcraft)
in SolidCraft:

```text
C:\gh\oomlout_oobb_part_motor_gearbox_cycloidal_version_5\gearbox_controls.solidcraft
```

Keep your design changes in this one file. The similarly named file in this
parts folder, and `true.solidcraft`, `exploded.solidcraft` and `3dpr.solidcraft`,
are initial snapshots. Editing them does not update the root master or each other.

## 2. Change parameters in SolidCraft

1. Open SolidCraft's **Parameters** menu and show **favourites**.
2. Edit the value/expression of the parameter you want to change. Include units
   for dimensions, for example `5.2 mm`; use plain numbers for counts and switches.
3. Apply the change and let SolidCraft finish recalculating. A substantial change
   can take a few minutes.
4. Inspect the result, then save the master normally.

All eight printed parts update inside SolidCraft. You do not need to edit Python
or run a regeneration command for these changes to take effect.

Start with a simple example: change `reduction` from `20` to `16`, leaving
`automatic_pitch` at `1`. The ring changes to 16 contacts, the discs to 15 lobes,
and the calculated contact pitch radius becomes 29.4 mm.

## Main design parameters

These are the initial defaults, not a record of any later edits you make.

| Parameter | Default | What it changes |
|---|---:|---|
| `reduction` | 20 | Ring contacts; disc lobes are one fewer. Integer 12–24, subject to fit limits. |
| `automatic_pitch` | 1 | `1` calculates pitch automatically; `0` enables the manual radius below. |
| `radius_buffer` | 0 mm | Extra radius added during automatic sizing. |
| `contact_pitch_radius` | 31.15 mm | Manual centre-to-contact radius; used only with automatic sizing off. |
| `contact_radius` | 3 mm | Circular contact radius, not diameter. |
| `eccentricity` | 1.4 mm | Rotor orbit, eccentric journals and moving clearance holes. |
| `profile_clearance` | 0.2 mm | Running clearance between discs and ring contacts. |
| `casing_wall` | 2 mm | Outer casing wall thickness. |
| `disc_thickness` | 5 mm | Both discs and the corresponding axial stack dimensions. |
| `disc_gap` | 0.5 mm | Space between the discs. |
| `standoff_radius` | 2.7 mm | Radius of the three printed standoffs. |
| `standoff_pitch_radius` | 18.55 mm | Position radius of the standoffs and their mating features. |
| `guide_radius` | 1.5 mm | M3 guides; `3 mm` selects M6 and changes associated holes and nut pockets. |
| `guide_pitch_radius` | 17.4 mm | Position radius of the six guide screws. |
| `casing_bearing` | 6810 | Both casing bearing seats, lips, journals, shoulders and axial spacing. |
| `casing_fit_checks` | 0 | Optional casing passage/backing/pin-envelope checks; `0` leaves them off. |
| `top_bearing` | 6703 | Upper disc bearing, seat and eccentric journal. |
| `bottom_bearing` | 6703 | Lower disc bearing, seat and eccentric journal. |

Use whole bearing catalogue codes. See [casing bearing options](CASING_BEARINGS.md).
The front shaft bearing remains 6701. Leave derived parameters and `native_unit`
alone; the favourites are the intended editing controls.

Dimensions must fit together. For example, a larger bearing may require moving
the guide holes and increasing disc thickness. If SolidCraft rejects an edit,
restore the last working values and check the related dimensions. Apply coupled
changes together where possible. The [full guide](../../NATIVE_V7.md) includes
tested bearing and M6 combinations and their limits; changing only `guide_radius`
to M6 is not the tested M6 configuration.

## Automatic OOBB tab positions

The four three-wide casing tabs follow the **smallest odd square OOBB plate**
that fits the casing and clears M6 hardware at the two outer holes of every tab.
They use the centred 15 mm OOBB grid: 5×5, 7×7, 9×9, and so on.
M3 half-grid holes and the existing casing joining screws move with each tab.

Sizing allows the larger of the shared OOBB M6 socket-head radius and M6 nut
corner radius, plus `tab_m6_clearance` (initially **0.5 mm**). This is clearance
around the hardware, in addition to the existing Ø6.5 mm through holes.
The middle M6 hole is not the sizing constraint; the two outer holes are.

In Parameters → all, the derived `tab_plate_size` gives the selected grid count,
`tab_plate_width` its physical width, and `tab_outer_bolt_gap` the radial space
between the hardware envelope and casing. These recalculate when the bearing,
wall or cycloid dimensions change. Leave the OOBB pitch and inset constants alone.

At the default settings the tabs match **7×7**: 104 mm plate width and centres
45 mm from the gearbox axis. A 6811 also uses 7×7; a 6812 moves to 9×9, with
centres 60 mm from the axis. The print layout expands with the tabs.

## 3. Switch between views in the same file

| View | `print_layout` | `explode` |
|---|---:|---:|
| Assembled | 0 | 0 mm |
| Exploded | 0 | 12 mm |
| Parts on their print faces | 1 | 0 mm |

Increase `explode` for more separation. `input_angle` changes the mechanism's
position; try `75 deg`, or return it to `0 deg` for the initial pose.

These controls change presentation without requiring a second set of design
dimensions.

## 4. Generate separate native outputs from the master

Save the master first. Open PowerShell and run:

```powershell
Set-Location 'C:\gh\oomlout_oobb_part_motor_gearbox_cycloidal_version_5'
python action_export_native.py
```

The exporter reads the saved master and creates a fresh directory under
`outputs/native_v7/`. It prints that directory's path when finished. It contains:

- `assembled.solidcraft` — assembled native model.
- `exploded.solidcraft` — native model with 12 mm exploded spacing.
- `3dpr.solidcraft` — native print layout.
- PNG previews and STEP/STL exports for those views.
- `parts/` — eight individual STEP/STL part exports.

The exporter switches native view parameters and saves copies; it does not
rebuild the geometry from Python or overwrite the master. The generated files
are snapshots, so rerun the exporter after saving new design changes. Existing
snapshots in this parts folder are not automatically replaced.

The exporter checks native health, fixed cycloid sampling and export validity.
That is not a new mechanical fit or load certification for every possible
parameter combination. Use the documented tested combinations as starting
points, and check new fits before printing.
