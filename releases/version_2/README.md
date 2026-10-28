# Version 2 - sealed

Approved 24 October 2026: rotating outer casing output, stationary guide pins bolted into the motor mount, opposed eccentric discs, M5 input axle and NEMA 17 countersunk M3 mounting screws. True 12:1 uses 11 disc lobes and 12 casing contacts, with output rotating in the input direction. Eight printed pieces.

`version_2.zip` preserves the approved source, verbose populate input, generated SCAD/STL, fit coupons, GIF/MP4 and validation reports. `release.json` records SHA-256 checksums for the archive, every archived file and the sealed catalogue directories. The approved checks comprise 24 gearbox tests, 9 mesh checks, 73 motion poses, 9 insertion poses and 192 distinct rendered animation frames.

SCAD snapshots are portable. Rebuilding the archived Python requires the existing local OOBB/OOMP dependencies, OpenSCAD and ffmpeg. Extract into a separate directory; the archived source retains its original version 2 generator for reproduction.

The version 2 parts, parts_source and navigation entries remain in place and are skipped by normal generation. Active development continues as an identical, editable version 3 baseline. Version 1 remains sealed independently.
