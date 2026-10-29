# Editing the native V8 gearbox

Open `gearbox_controls.solidcraft` and use **Parameters → favourites**. The nine
printed components rebuild within SolidCraft. Save normally; no Python process,
linked part update or external geometry regeneration is needed for an edit.

The root master is the 20:1 starting design. Each populate variant also has its
own `gearbox_controls.solidcraft` in its parts folder. Edit the master for the
variant you want. `true.solidcraft`, `exploded.solidcraft` and `3dpr.solidcraft`
are independent view snapshots, not linked documents.

## Controls

| Parameter | 20:1 default | Meaning |
|---|---:|---|
| `reduction` | 20 | Integer 10–24; ring contact count, with one fewer rotor lobe. |
| `automatic_pitch` | 1 | Calculate minimum contact pitch; 0 selects manual pitch. |
| `contact_pitch_radius` | 31.15 mm | Manual pitch, used with `automatic_pitch=0`. |
| `radius_buffer` | 0 mm | Extra radius above the automatic minimum. |
| `contact_radius` | 3 mm | Circular ring contact **radius**, not diameter. |
| `eccentricity` | 1.4 mm | Orbit radius; also changes journals and guide clearances. |
| `profile_clearance` | 0.2 mm | Clearance between rotor equation and ring contacts. |
| `casing_wall` | 2 mm | Wall outside the ring contacts and bearing seats. |
| `disc_thickness` | 5 mm | Both cycloids; propagates through the axial stack. |
| `disc_gap` | 0.5 mm | Separation between discs. |
| `automatic_internal_positions` | 1 | Automatically places guides and standoffs from clearance limits. Set 0 to use the manual position radii. |
| `standoff_radius` | 2.7 mm | Three printed standoffs. **0 removes them**, their registers, fastener holes and rotor tracks. |
| `standoff_pitch_radius` | 18.55 mm | Manual standoff position radius. |
| `guide_radius` | 1.5 mm | Screw radius: 1.5 for M3 or 3 for M6. Changes bores, heads and nut pockets. |
| `guide_outer_radius` | 1.5 mm | Outside radius of a spacer around each guide screw. Equal to screw radius means no spacer. |
| `guide_count` | 6 | Number of equally spaced guide screws; integer 3–12. |
| `guide_pitch_radius` | 17.4 mm | Manual guide position radius. |
| `guide_screw_length` | 20 mm | Under-head length; adjusts the underside-loaded nut pockets. |
| `casing_bearing` | 6810 | Both casing bearings; 40 catalogue choices from the 6700/6800 series. |
| `casing_fit_checks` | 0 | Optional conservative casing envelope guards; disabled by default. |
| `bottom_bearing`, `top_bearing` | 6703 | Cycloid centre bearing codes; seats, lips and journals follow. |
| `input_angle` | 0 deg | Mechanism position; output turns by input angle divided by reduction. |
| `explode` | 0 mm | Axial separation. Try 12 mm for the exploded view. |
| `print_layout` | 0 | 1 places all nine parts on their print faces. |

Use catalogue bearing codes as whole numbers. Keep `native_unit=1 mm`. The
front shaft bearing remains 6701, with a direct 5 mm input and NEMA 17 interface.
The bearing choices are listed in `CASING_BEARINGS.md` in each parts folder.

Apply related edits together where possible. A smaller reduction can still be
limited by bearing size, guide tracks, eccentricity or remaining material. The
native `pitch`, `casing_radius`, `guide_pitch`, `post_pitch` and `tab_plate_size`
parameters show the resulting dimensions. An incompatible edit can fail a guard;
correct its dimensions in Parameters. Guards do not prove every physical fit.

## Two populate presets

| Setting / result | Standard | Compact |
|---|---:|---:|
| Reduction | 20:1 | 10:1 |
| Contact radius | 3 mm | 1.5 mm |
| Eccentricity | 1.4 mm | 0.9 mm |
| Casing bearings | 6810, 50 × 65 × 7 mm | 6808, 40 × 52 × 7 mm |
| Cycloid centre bearings | 6703 | 6702 |
| Printed standoff radius | 2.7 mm | 0 mm |
| Guide screws | Six M3 × 20 | Six M3 × 25 |
| Contact pitch radius | 31.15 mm | 22.4 mm |
| Core casing diameter | 72.3 mm | 56.2 mm |
| OOBB positions | 7 × 7 plate, 45 mm radius | 7 × 7 plate, 45 mm radius |
| Overall casing tab footprint | 104 × 104 mm | 104 × 104 mm |

Both use the same native feature graph. The compact preset changes only
favourite parameters listed in `working_oomp_populate.py`; there is no separate
10:1 geometry implementation. Its longer guide screws place the nuts below the
casing bearing, accessible from the motor side. Load these nuts before mounting
the motor plate. The 6808 bore clears the guide screw heads. The outer M6 hardware clearance
keeps this preset on the 7 × 7 grid, despite its smaller circular casing. A smaller 6807 trial was rejected
because its inner ring overlapped those heads. Physical printing and strength
testing remain needed.

## Three-piece casing and printing

The output casing consists of `output_casing_lower`, `output_casing_lobes` and
`output_casing_upper`. The bearing holders are separate from the straight lobe
band, so a larger lobe circle does not create an unsupported bearing transition.
The full-depth OOBB tabs connect to the shell along their complete width.

Use the supplied `3dpr.solidcraft` or individual `native_parts/*.stl` files:

- Lower bearing holder: split face down, bearing opening and nut loading from above.
- Lobe band: either flat end down.
- Upper bearing holder: split face down, bearing opening upwards.

The combined layout is an overview of all parts. Arrange the individual STLs
to suit your printer's bed size.

Four M3 socket-cap screws clamp the stack through corner pads on the half-grid.
The original tab M3 holes remain available. The derived `join_screw_length`
selects a multiple of 5 mm, with `join_head_recess` taking up the remaining height.
The default stack uses **M3 × 20 mm**, with a 5.8 mm recess measured to the
under-head seat. Longer stacks can select screws longer than 25 mm.

The lower holder has four M3 joining-nut pockets and twelve M6 mounting-nut
pockets, using shared OOBB definitions with `overhang=True`. M6 nuts are optional
where a mounting hole is unused. The tabs use the smallest odd OOBB footprint
that accommodates the casing and the two outer M6 hardware envelopes.

Guide spacers are purchased or separately made sleeves, not additional printed
bodies in this model. At the default stack their working length is 11.5 mm; use
`front_z - rear_support_top` after axial edits. `guide_outer_radius` enlarges the
rotor tracks for them. It must be at least `guide_radius`.

## Save and export

Save your working master first. Export directly in SolidCraft, or run:

```text
python action_export_native.py
```

This reads the saved root master and writes fresh assembled, exploded and print
snapshots plus individual STEP/STL files under `outputs/native_v8/`. It does not
overwrite the master. For an edited variant file, pass `--design` and its path.

To recreate both populate entries and their parts folders from the saved root
feature graph, run `python action_export_native.py --populate`. That explicitly
reapplies each preset's exposed parameter overrides; preserve independent edits
to a variant master before repopulating. `action_make_solidcraft.py` uses this
same native populate route. Legacy recipe authoring cannot overwrite the master.

The exporter checks native health, STEP/STL validity and fixed equation sampling.
Sampling must meet the existing 0.005 mm accuracy limit. If an edit exceeds it,
regenerate the mathematical construction with adequate sampling and repeat the
native checks. The shared equation parameters remain linked within the file.

V1–V7 remain sealed. Native verification is recorded in `solidcraft/native_v8.json`;
physical print, wear and load testing are still required.
