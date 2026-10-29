# V9 native 5×5 gearbox

Open the root `gearbox_controls.solidcraft` in SolidCraft and use **Parameters**.
The file owns the complete feature graph; no external regeneration process or
linked part is needed. All clearances below are radial unless stated otherwise.

The main preset is **35:1** with 34 rotor lobes, **1.5 mm contact radius**,
**0.7 mm eccentricity**, two **6808** casing bearings, two **6702** disc bearings
and a **6701** front shaft bearing. The output is **74×74 mm**, the standard
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
| `profile_clearance` | 0.2 mm | Rotor-to-contact clearance. |
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

The two halves now share named D-key dimensions. The socket uses the same
radius and flat plus its clearance. Journals derive from the selected bearing
bores. Shaft end, grub-screw height, joining nut/head seat and reliefs are also named.

| Fit control | Default | Result |
|---|---:|---|
| `shaft_bore_clearance` | 0.05 mm | Ø5.10 mm bore for the Ø5 mm motor shaft. |
| `wiggle_journal_clearance` | 0.075 mm | Ø14.85 mm journals for Ø15 mm bearing bores. |
| `wiggle_key_clearance` | 0.10 mm | Socket radius and flat offset beyond the male key. |
| `wiggle_axial_clearance` | 0.10 mm | Key socket end allowance. |

Journal and key clearances were previously 0.10 and 0.15 mm respectively.
Print the two hub halves first to assess the tighter fit on your printer.
Tighten the base grub screw **before fitting the motor plate**. Both shaft nuts
retain OOBB overhang geometry.

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
orientations. Casing height remains 27.3 mm; the drive reaches 32 mm above the motor face.

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

`python action_export_native.py --populate` recreates both catalogue presets
from the root graph using exposed parameter overrides. Preserve independent
variant edits before repopulating. The verbose populate → working_oomp route
remains in place; legacy regeneration cannot replace the native master.

Fixed equation sampling is checked through shared `validate_edit` to 0.005 mm.
Regenerate the mathematical construction and repeat native checks if an edit
needs finer sampling. V1–V8 and the acceptance policy remain unchanged.
See `solidcraft/native_v9.json` for evidence; physical print/load testing remains outstanding.
