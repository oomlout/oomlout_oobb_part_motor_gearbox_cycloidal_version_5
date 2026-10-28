# Version 7 — native dependency graph

Starts from the accepted V6 20:1 configuration_3d9262f6 with identical printed
geometry, 6810 casing bearings, 6703 centre bearings, 1.4 mm eccentricity and
3 mm contact radius. The accepted 16:1 configuration and diagnostic studies
remain sealed in V6. The acceptance policy remains unchanged.

## Native implementation

The root `gearbox_controls.solidcraft` owns the complete native dependency graph.
All eight printed components use native sketches, extrudes, revolves, combines,
moves and associative patterns. No imported BRep or linked source-part file is
used. Read [NATIVE_V7.md](NATIVE_V7.md) for controls and examples.

The shared helper's `cycloidal_pattern` component defines an expression-driven
mathematical sector. Its native pattern count is `reduction−1`; ring contacts
and their backing bands use `reduction`. The shared `native_design` component
provides expression-constrained construction and real OOBB cutters with native
placements and paired catalogue-size selection.

`gearbox_native/native_v7.py` authors the initial history into a fresh build
directory. The saved document owns its expressions thereafter. `native_exports.py`
reads and exports the current document without regenerating its geometry.
`publish_native_v7.py` installs the verified document once and refuses to overwrite
an already-installed editable master. Legacy recipe publication is guarded.

## Verification

`solidcraft/native_v7.json` indexes the accepted source and verification. The
isolated rotor proof is in `build/native_v7/rotor_10/verification.json`. The full
source/evidence is in `build/native_v7/assembly_03/`; native view exports are in
`build/native_v7/presentation_01/`.

The whole-model suite edits only native parameters, compares each body against
independent reference geometry, checks STEP/STL, and performs two save/reopen
cycles per case. Cases cover baseline, 16:1, combined dimensions, bottom bearing,
M6 guides, motion, print layout, and manual pitch/top bearing. Fit checks use
actual native exports with the existing motion, installation and tool-access
policy. Guard tests verify rollback of fractional reduction, unknown bearing,
excessive eccentricity and unsupported guide-size edits.

`gearbox_native/acceptance.py` is unchanged (SHA-256
`aef1e8a522769f4e35fd83bccd3a281fa35bf24b36d6034549d42dad786bb311`).
This retains 0.05 mm / 0.5% native geometry thresholds and the existing 0.1 mm
mesh policy. Fixed cycloid sampling is checked separately at 0.005 mm. Sampled
fits are not a continuous-motion proof or a physical load test.

The broader historical project suite reports 22 failures / 121 passes
(`outputs/v7_project_tests.log`), including old 9/15-part layouts, retired versions,
removed couplers and an old hardware-presentation API. Those tests have not been
rewritten to conceal their older assumptions. Current native and V7-specific
tests are recorded separately. The helper's 150-test regression suite passed;
component-specific cycloid tests are separate.

The first M6 experiment used an 18.7 mm guide circle. Its bores clipped the motor
screw-access bores at the carrier shoulder, and native STEP validation rejected
a face with bad wire orientation. Evidence remains in
`verification/M6_guides_rejected_18_7/`. The accepted example moves the guide
circle inward to 18.2 mm; no acceptance repair or tolerance relaxation was used.

## Preserved starting point

- Sixteen accepted native part documents and nine fit samples are inherited
  byte-for-byte from V6, with immutable acceptance provenance.
- The initial linked layouts and old control master are preserved in explicitly
  named `inherited_*` folders. Current views are self-contained native snapshots.
- V6 presentation assets are retained as labelled reference images/animation of
  the unchanged mechanism. They are not evidence of new V7 parametric behaviour.
- Existing populate/working_oomp/working_solidcraft recipes remain independent
  verification references; they do not drive the active V7 native model.

Do not regenerate any directory carrying SEALED.json. Frozen sources, examples
and evidence are in releases/version_6/version_6.zip.
