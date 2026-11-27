# Version 7 — fresh development baseline

Starts from the accepted V6 20:1 configuration_3d9262f6 with identical printed
geometry, 6810 casing bearings, 6703 centre bearings, 1.4 mm eccentricity and
3 mm contact radius. The accepted 16:1 configuration and diagnostic studies
remain sealed in V6. The acceptance policy remains unchanged.

## Requirement for the next iteration

Build a SolidCraft-only design. The user changes values in SolidCraft's
Parameters menu and the complete model propagates those changes internally.
An external Python regeneration or web-explorer Update action is not the
requested solution. The implementation of this behaviour is future V7 work.

## Preserved starting point

- Sixteen accepted native part documents and nine fit samples are inherited
  byte-for-byte from V6, with immutable acceptance provenance.
- true.solidcraft and 3dpr.solidcraft have fresh links to V7 source parts.
- gearbox_controls.solidcraft remains an inherited control-model starting point;
  its current whole-gearbox update limitation has not been redesigned yet.
- V6 presentation assets are retained as labelled reference images/animation of
  the unchanged mechanism. They are not evidence of new V7 parametric behaviour.
- Existing populate/working_oomp/working_solidcraft infrastructure remains for
  baseline maintenance while the native dependency structure is developed.

Do not regenerate any directory carrying SEALED.json. Frozen sources, examples
and evidence are in releases/version_6/version_6.zip.
