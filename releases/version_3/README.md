# Version 3 — sealed

Approved 25 October 2026: compact 20:1 rotating-casing output, opposed 19-lobe discs, nine printed pieces, NEMA 17 mount and shaft-tip flange-down 5 mm coupler. Two opposite M3 flange screws use straight radial nut-loading channels; all nut pockets retain overhang support.

`version_3.zip` preserves the approved Python sources, verbose populate options, generated SCAD/STL, fit coupons, PNG previews, GIF/MP4 animation and validation reports. `release.json` records the archive hash, every archived file hash and every sealed catalogue file hash. Verification: 34 automated tests, 10 watertight meshes including the print layout, 73 motion poses, assembly insertion checks, two continuous nut-loading sweeps and 192 distinct animation frames.

Extract the archive into a separate folder to inspect or reproduce it. The archived Python remains the editable version 3 generator; it requires the existing local OOBB/OOMP dependencies, OpenSCAD and ffmpeg. Generated SCAD files are portable. The live version 3 parts, parts_source and navigation folders are sealed and skipped by normal generation. Active development continues as an identical version 4 baseline. Versions 1 and 2 remain sealed independently.
