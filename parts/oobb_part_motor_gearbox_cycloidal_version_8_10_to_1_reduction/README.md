# Native V8 — 10:1

Edit [gearbox_controls.solidcraft](gearbox_controls.solidcraft) in SolidCraft's
Parameters menu. [Editing instructions](EDITING_PARAMETERS.md) explain the
controls and print orientations. This preset uses the same feature graph as
the other V8 presets, with exposed parameter overrides only.

| Dimension | Value |
|---|---:|
| Contact radius | 1.5 mm |
| Eccentricity | 0.9 mm |
| Casing bearing | 6808 |
| Casing core diameter | 56.2 mm |
| OOBB grid | 7 × 7 |
| Tab footprint | 104 × 104 mm |
| Guide screws | 6 × M3 × 25 mm |
| Casing joining screws | 4 × M3 socket cap × 20 mm |

[Assembled](true.solidcraft) · [Exploded](exploded.solidcraft) ·
[Print layout](3dpr.solidcraft) · [Print STL](3dpr.stl)

![Exploded printed components](exploded.png)

Individual print-oriented STEP/STL files are in `native_parts/`. The three
casing pieces print separately on their flat split/end faces. These view files
are independent snapshots. Native geometry and hardware clearance have been
checked; physical printing and load testing are still needed.
