# Selecting the casing bearings in SolidCraft

Open the project-root `gearbox_controls.solidcraft`. In **Parameters → favourites**,
change **`casing_bearing`** from `6810` to a whole code in the table below.
Both casing bearings use this selection. Save the master, then use
`python action_export_native.py` for new assembled, exploded and print snapshots.
No Python regeneration is needed for parameter changes inside SolidCraft.

The selection drives the outer bearing seats and retaining lips, inner journals
and shoulders, front carrier thickness, rear support height, disc and casing
positions, casing diameter, tab positions and print-layout spacing. The tabs
snap to the smallest odd OOBB plate with M6 head/nut clearance at their outer
holes; see [the editing guide](EDITING_PARAMETERS.md#automatic-oobb-tab-positions). The pitch
and rotor dimensions remain controlled by their existing parameters; selecting
a smaller bearing does not automatically shrink the cycloids.

**`casing_fit_checks=0`** is the default. Bearing passage, backing and fixed-pin
envelope guards are disabled so you can experiment. Set it to `1` to enable those
three limited checks. Other construction and profile guards remain. There is no
complete fit check, and choosing a listed bearing does not promise an assemblable
gearbox. Some choices can also make the native geometry impossible to construct.

The front shaft bearing remains 6701. `top_bearing` and `bottom_bearing` select the
centre bearings of the discs and also have access to these catalogue sizes.
The 6700 entry preserves the existing 10×15×4 mm variant; check your actual bearing
if it is a different width. Large bearings may exceed a printer's bed.

## Catalogue options

Dimensions are bore × outside diameter × width, in mm. Newly added 6708–6712
entries use [Ningbo Kecheng's manufacturer table](https://www.cxnjs.com/content/150.html).
Other entries retain the installed OOBB catalogue dimensions.

| Code | Bore | Outside diameter | Width |
|---|---:|---:|---:|
| 6700 | 10 | 15 | 4 |
| 6701 | 12 | 18 | 4 |
| 6702 | 15 | 21 | 4 |
| 6703 | 17 | 23 | 4 |
| 6704 | 20 | 27 | 4 |
| 6705 | 25 | 32 | 4 |
| 6706 | 30 | 37 | 4 |
| 6707 | 35 | 44 | 5 |
| 6708 | 40 | 50 | 6 |
| 6709 | 45 | 55 | 6 |
| 6710 | 50 | 62 | 6 |
| 6711 | 55 | 68 | 7 |
| 6712 | 60 | 75 | 7 |
| 6800 | 10 | 19 | 5 |
| 6801 | 12 | 21 | 5 |
| 6802 | 15 | 24 | 5 |
| 6803 | 17 | 26 | 5 |
| 6804 | 20 | 32 | 7 |
| 6805 | 25 | 37 | 7 |
| 6806 | 30 | 42 | 7 |
| 6807 | 35 | 47 | 7 |
| 6808 | 40 | 52 | 7 |
| 6809 | 45 | 58 | 7 |
| 6810 | 50 | 65 | 7 |
| 6811 | 55 | 72 | 9 |
| 6812 | 60 | 78 | 10 |
| 6813 | 65 | 85 | 10 |
| 6814 | 70 | 90 | 10 |
| 6815 | 75 | 95 | 10 |
| 6816 | 80 | 100 | 10 |
| 6817 | 85 | 110 | 13 |
| 6818 | 90 | 115 | 13 |
| 6819 | 95 | 120 | 13 |
| 6820 | 100 | 125 | 13 |
| 6821 | 105 | 130 | 13 |
| 6822 | 110 | 140 | 16 |
| 6824 | 120 | 150 | 16 |
| 6826 | 130 | 165 | 18 |
| 6828 | 140 | 175 | 18 |
| 6830 | 150 | 190 | 20 |
