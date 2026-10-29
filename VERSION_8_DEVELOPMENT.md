# Version 8 — three-piece casing and compact native presets

V7 is sealed. V8 initially inherited its exact native model and eight manufacturing exports; the initial hashes remain in `solidcraft/version_8_baseline.json`. The current revision has nine printed parts: the casing is split into two bearing holders and one straight lobe band. The acceptance policy is unchanged.

Edit the root gearbox_controls.solidcraft using SolidCraft Parameters. The 40 casing-bearing choices and automatic odd OOBB footprint formulas are retained. The default is 20:1, 6810 casing bearings, 3 mm contact radius, 1.4 mm eccentricity, 5 mm discs, 0.5 mm gap and a 7 × 7 mounting footprint. The 10:1 populate preset changes only exposed native parameters: 1.5 mm contacts, 0.9 mm eccentricity, 6808 casing bearings, 6702 centre bearings, no standoffs and M3 × 25 guide screws. Its casing core is 56.2 mm diameter and its tabs remain on 7 × 7 positions to clear the M6 hardware.

See [parameter instructions](NATIVE_V8.md), [baseline hashes](solidcraft/version_8_baseline.json), and [sealed V7](releases/version_7/README.md). Its verification evidence is preserved in the archive. No new physical fit or print/load certification is claimed. Exports now go to outputs/native_v8.

Initial setup verification: 29 native/export files matched V7 byte-for-byte and 15 targeted tests passed. This remains provenance for the starting point, not a claim that the current revision has unchanged geometry. Complete V7 evidence remains in its release archive.

The new native authoring implementation is `gearbox_native/native_v8.py`. It uses the shared equation profile and native sketch patterns. `native_hardware_pattern` in the underlying MCP helper expands actual OOBB nut and overhang primitives into variable-count native sketch patterns. A project snapshot of that small component is retained with the verification evidence for reproducibility. No helper is required to edit the saved SolidCraft document.

The lower bearing holder prints inverted on its split face; the upper holder prints on its split face; the straight lobe band prints on either end. Full-depth tabs run through all three pieces. Four corner pads carry recessed M3 socket-cap clamps; calculated lengths are multiples of 5 mm. The lower holder retains inset M3 joining nuts and twelve optional M6 mounting nuts, all with OOBB overhang geometry. Guide nuts load through open hexagonal channels from below the motor plate.

The NEMA mounting access bores use the full OOBB M3 countersunk-head clearance diameter (7.2 mm). Their countersink mouths sit 0.02 mm below the motor plate face, avoiding a coincident union face in the compact bearing configuration. This is explicit construction geometry; the native retry allowance and all acceptance thresholds remain unchanged.

Verification covers native edits at 16:1 and 24:1, no standoffs, changed guide count, guide spacers, M6 guide screws and the compact 10:1 preset. The two published presets also receive pairwise native STEP intersection checks, sampled rotor/ring motion checks, individual STEP/STL validation and two save/reopen cycles. See `solidcraft/native_v8.json` for final evidence and export hashes. Physical print/load testing is still needed; the smaller 6807 trial was rejected because its inner ring intersected the guide screw heads; 6808 provides clearance.
