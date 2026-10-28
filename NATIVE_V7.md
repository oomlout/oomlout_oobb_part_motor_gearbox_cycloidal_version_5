# Native V7 parameters

Open `gearbox_controls.solidcraft` in this project. This is the editable master.
Use **Parameters → favourites**. SolidCraft recalculates all eight printed
components in that same document; no Python process, web explorer, linked part
update or external regeneration is needed when you change a parameter.

Save a copy before a major experiment. The first open and a substantial geometry
edit can take a few minutes because SolidCraft solves the complete native history.

## Controls

| Parameter | Default | Effect |
|---|---:|---|
| `reduction` | 20 | Ring contact count; the rotors have one fewer lobe. Integer 12–24, subject to the remaining fit limits. |
| `automatic_pitch` | 1 | 1 calculates the minimum pitch; 0 uses `contact_pitch_radius`. |
| `radius_buffer` | 0 mm | Additional automatic pitch radius. |
| `contact_pitch_radius` | 31.15 mm | Manual contact centre radius; inactive while automatic sizing is on. |
| `contact_radius` | 3 mm | Circular contact **radius**, not diameter. |
| `eccentricity` | 1.4 mm | Both opposed eccentric journals, rotor orbits and clearance tracks. |
| `profile_clearance` | 0.2 mm | Clearance between contacts and the mathematical rotor boundary. |
| `casing_wall` | 2 mm | Radial wall beyond the contacts and bearing seats. |
| `disc_thickness` | 5 mm | Both discs; also moves the split, front carrier, casing and hubs. |
| `disc_gap` | 0.5 mm | Separation of the two discs. |
| `standoff_radius` | 2.7 mm | Three integral standoffs and their rotor clearance tracks. |
| `standoff_pitch_radius` | 18.55 mm | Standoffs, front registers, fasteners and clearance tracks. |
| `guide_radius` | 1.5 mm | M3 guides. Set 3 mm for M6; holes, head access and nut pockets switch together. |
| `guide_pitch_radius` | 17.4 mm | All six guide positions and their rotor clearance tracks. |
| `top_bearing` / `bottom_bearing` | 6703 | Integer catalogue codes; changes seats, retaining lips and eccentric journals. |
| `input_angle` | 0° | Eccentric input and opposing rotor orbits; casing turns by input/reduction. |
| `explode` | 0 mm | Axial separation for inspecting the eight printed components. Try 12 mm. |
| `print_layout` | 0 | Set 1 to lay all eight parts on their print faces. |

Non-favourite parameters are derived dimensions or construction constraints.
Leave `native_unit` at 1 mm. Use whole catalogue bearing codes, not intermediate
numeric values. The two casing bearings remain **6810**, and the front shaft
bearing remains **6701**. The 5 mm motor shaft and NEMA 17 mounting interface are
unchanged. Explorer underlays and amber warning colours are not native geometry
controls and are not included in this document.

## What changes together

Automatic pitch considers the two bearing envelopes, guide/standoff tracks,
contact spacing, eccentricity and an analytic undercut bound. A single shared
pitch drives the rotor equations, ring contacts, backing bands and casing wall.
Native circular patterns change the actual number of contacts and rotor lobes.

Disc thickness and gap drive the complete axial stack. Bearing dimensions drive
the actual disc seats and both sides of the eccentric support. M3/M6 selection
uses the shared OOBB screw/nut dimensions, including nut overhang geometry.
Assembly and print positions are native expressions applied after construction.

The compact 6810 envelope still imposes limits: increasing a bearing, track or
eccentricity may require changing the neighbouring settings together. A rejected
edit is not a request to run Python. Correct the incompatible dimensions in the
Parameters menu. The native guards cover pitch, backing, passage, retained bearing
lips, webs, key engagement and screw clearances. They are not a complete physical
load or continuous collision proof.

## Examples to try

Start each example from the default master, rather than stacking the examples.

| Example | Changes |
|---|---|
| 16:1 | `reduction=16`; automatic pitch becomes 29.4 mm. |
| Different bottom bearing | `bottom_bearing=6803`, `disc_thickness=6 mm`, `eccentricity=1 mm`, `guide_pitch_radius=18.2 mm`, `standoff_pitch_radius=19.5 mm`. |
| M6 guides | `guide_radius=3 mm`, `eccentricity=0.5 mm`, `guide_pitch_radius=18.2 mm`, `standoff_pitch_radius=20 mm`. |
| Manual pitch / different top bearing | `automatic_pitch=0`, `contact_pitch_radius=29.6 mm`, `top_bearing=6803`, `disc_thickness=6 mm`, `eccentricity=1 mm`, `guide_pitch_radius=18.2 mm`, `standoff_pitch_radius=19.5 mm`. |

Apply coupled changes together where possible. A temporary intermediate state
can violate a guard even when the final combination fits.

Keep the M6 example's guide circle at 18.2 mm. An experimental 18.7 mm guide
circle slightly intersected the NEMA screw-access bores at the carrier shoulder
and produced an invalid native STEP face. It was rejected, not repaired or
published. The guards do not catch every possible feature interaction; use the
export and fit checks before printing a new combination.

## Save and export

Save the master normally in SolidCraft. Export bodies directly from SolidCraft,
or run `python action_export_native.py` after saving. That optional utility reads
the saved native file and writes a new output directory with assembled, exploded
and print snapshots, previews, and eight individual STEP/STL files. It never
regenerates the geometry or overwrites the master. `action_make_solidcraft.py`
uses this export path for native V7; the old recipe authoring path is protected.

The active part directory contains initial `true.solidcraft`, `3dpr.solidcraft`
and `exploded.solidcraft` snapshots. They are self-contained and editable, but
later edits in one snapshot do not synchronize into another: keep the root
master as your working document. `native_parts/` contains its initial individual
print exports. Old `solidcraft/true`, `solidcraft/3dpr` and fit coupons are retained
as labelled V6 inheritance evidence, not live dependencies of this master.

## Mathematical profile and validation

The shared `cycloidal_pattern` component defines one roller-envelope sector using
the shared `parametric_profile` expression APIs. Native formulas drive its sampled
boundary and a native pattern repeats it `reduction−1` times. Both frequency and
pattern count change inside SolidCraft. Extrusion uses the same boundary for both
caps and every wall, keeping the rotor closed after edits.

This is an expression-driven approximation of the equation, not an exact analytic
CAD spline. The saved fractional stations are checked with `validate_edit` against
a 0.005 mm chord tolerance. The optional export utility performs that check again
for the current parameters and refuses exports if the sampling is insufficient.
Outside the tested range, resampling is a deliberate authoring operation; a native
edit does not silently call Python or replace the document.

Verification records are indexed by `solidcraft/native_v7.json`: isolated rotor
edits, whole-model native edits, valid STEP/STL, zero-DOF health, repeated
save/reopen, motion/install/access fits, and guard rollback checks. The existing
0.05 mm / 0.5% native acceptance policy remains unchanged. Physical print and
load testing remains outstanding. V1–V6 archives and their protected files remain
sealed.
