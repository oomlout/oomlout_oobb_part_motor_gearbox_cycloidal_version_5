# Version 9 — high reduction in a 5×5 output

Version 8 is sealed. V9 initially inherited both V8 presets byte-for-byte; those setup hashes remain in `solidcraft/version_9_baseline.json`. The new revision deliberately changes geometry: a 35:1 main preset, full-width 74×74 mm OOBB output, 6808 casing bearings and a refactored wiggle shaft. The acceptance policy is unchanged.

The contact radius remains 1.5 mm. A 0.7 mm eccentricity gives a 27.9 mm automatically calculated pitch at 35:1. The output keeps its three support-free printing pieces, now with full five-wide outlines and only the middle M6 hole removed from each edge. Four inner half-grid M3 socket-cap screws join the pieces; M6 and M3 nuts retain OOBB overhang pockets. Six guide screws and three standoffs fit inside the 6808 arrangement with 6702 disc bearings.

`gearbox_native/native_v9.py` authors the new native construction using the existing shared equation-profile, native-design and OOBB APIs. The two shaft halves share named D-key dimensions; radial key clearance is 0.10 mm and journal clearance 0.075 mm. The source keeps V8 authoring and all sealed assets intact.

Edit the root `gearbox_controls.solidcraft` in SolidCraft Parameters for 35:1, or the local 10:1 master for that preset. Both use the same native feature graph. Populate and working_oomp still supply the catalogue, while native parameter edits supply geometry. The old V9 20:1 folder is the original inherited reference, not the current populated design.

See [parameter instructions](NATIVE_V9.md), [V8 release](releases/version_8/README.md), and [revision evidence](solidcraft/native_v9.json). The isolated rotor receives real eccentricity edits and save/reopen checks before assembly integration. Verification includes native health, fixed sampling, STEP/STL, pairwise intersections, sampled motion and purchased hardware/access envelopes. New parameter cases cover 32:1, eccentricity, post removal, tighter shaft fits and 10:1. Physical printing and load testing remain outstanding. Exports target `outputs/native_v9/`.
