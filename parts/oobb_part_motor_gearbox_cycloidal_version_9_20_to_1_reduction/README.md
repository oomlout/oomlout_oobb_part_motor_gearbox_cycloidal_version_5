> Initial V9 reference snapshot. The current populated main design is 35:1; see the root README.

# Native V9 — 20:1

Edit [gearbox_controls.solidcraft](gearbox_controls.solidcraft) in SolidCraft's
Parameters menu. [Editing instructions](EDITING_PARAMETERS.md) explain the
controls and print orientations. This preset uses the same feature graph as
the other V9 presets, with exposed parameter overrides only.

| Dimension | Value |
|---|---:|
| Contact radius | 3 mm |
| Eccentricity | 1.4 mm |
| Casing bearing | 6810 |
| Casing core diameter | 72.3 mm |
| OOBB grid | 7 × 7 |
| Tab footprint | 104 × 104 mm |
| Guide screws | 6 × M3 × 20 mm |
| Casing joining screws | 4 × M3 socket cap × 20 mm |

[Assembled](true.solidcraft) · [Exploded](exploded.solidcraft) ·
[Print layout](3dpr.solidcraft) · [Print STL](3dpr.stl)

![Exploded printed components](exploded.png)

Individual print-oriented STEP/STL files are in `native_parts/`. The three
casing pieces print separately on their flat split/end faces. These view files
are independent snapshots. Native geometry and hardware clearance have been
checked; physical printing and load testing are still needed.

V9 starts with byte-identical native geometry and exports from sealed V8. The inherited CAD evidence applies to this starting point.
