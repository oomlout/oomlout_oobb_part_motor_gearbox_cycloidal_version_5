# Historical migration notes

The active design is now native V7. See [NATIVE_V7.md](NATIVE_V7.md).
The version-specific descriptions below are retained development history.

## Version 6: inherited baseline

V5 is sealed in `releases/version_5/`. V6 inherits its 16 accepted native part documents and nine fit samples byte-for-byte. Its linked layouts and presentation are regenerated for V6 paths. Mechanical dimensions and acceptance policy remain unchanged.

The following records the V5 development history; its version-specific paths now refer to sealed artifacts.

# Version 5: native SolidCraft workflow and migration history

**Version 5 / simple_6810 / 20:1** is the active native design: eight printed pieces,
72.3 mm casing diameter and 32 mm maximum above the motor face, single-piece plain-guide
discs, six M3×20 socket-cap guide screws, two 6703 eccentric bearings, one 6701
shaft bearing and two 6810 casing bearings. The motor mount incorporates the
rear carrier and spacers; the front carrier incorporates its bearing hub. The
output ring is one piece, without separate covers or casing clamp screws.
The current `grub_nut` drive holds the motor shaft directly with an M3×8 grub
screw and captured nut; the hollow key supports an axial joining nut above the
shaft tip. The earlier 50 mm flanged arrangement is preserved in
`outputs/v5_flanged_50mm/` and remains selectable as `flanged_coupler`.
The 36 mm direct-drive checkpoint is in `outputs/v5_direct_36mm/`. The active
`base_grub` layout secures the hub before fitting the motor plate. Its casing
is 26.6 mm deep, the 6701 nests within the upper 6810 region, and the centre
socket screw is M3×4. The output casing is split at the disc gap and prints
split-face down without supports under the internal transition. Four M3×6
countersunk screws and overhang-enabled M3 nut pockets join 3 mm-thick middle
flanges. Each middle face has four flat 3 mm, three-unit OOBB mounting tabs with
three M6 holes on 15 mm centres and two M3 midpoint holes. One midpoint hole per
tab joins the halves; there are no separate screw lugs. The tabs connect to the
curved wall along their full 44 mm length. Total tab span is 104 mm. The two halves form
a 6 mm mounting flange. A continuous annular wall backs the complete bearing lands.
Test the tab and screw/nut coupons before printing the full parts.

Split casing authoring merges redundant coplanar and coaxial face divisions
before making native sketches. Acceptance still compares the exported solid
against the original, unmerged recipe. The project uses one CAD worker because
large simultaneous surface histories exhausted memory during an earlier build.
The active eccentricity is 1.4 mm. The 3 mm contact radius uses a 31.15 mm pitch
radius to avoid profile undercutting, adding 3.1 mm to the casing diameter without
changing the height. The 1.65 mm contact checkpoint is in `outputs/v5_lobe_1_65/`. Three
M3×25 socket screws reinforce slimmer standoffs with 1.6 mm locating pegs. The
earlier 1.25 mm checkpoint is preserved in `outputs/v5_eccentric_1_25/`.
See the [project guide](README.md) for the current hardware and fit checks.
The active rotors now use the shared `cycloidal_disc` / `parametric_profile`
components. All cap and wall boundaries retain their native coordinate formulas.
The isolated actual-rotor proof is recorded in `outputs/equation_rotor_probe.json`;
the project acceptance policy remains unchanged. Native edits use fixed sample
stations and require `validate_edit`; coordinated gearbox changes regenerate.
The migration counts and provenance below describe the earlier unchanged baseline.

Version 4 is sealed with both its SCAD and SolidCraft implementations
in releases/version_4. Versions 1–3 remain sealed. V5 starts from the identical
native part documents; its two linked layouts point only to V5 parts.

Completed **26 October 2026**: all 15 pieces in both `true` and `3dpr` modes,
plus both linked print layouts, are generated and verified. The 30 part documents
contain native feature histories with no STEP/mesh imports: 20 use conventional
parametric features and 10 use native sketch surfaces. STEP/STL/PNG exports are
included. See [part audit](solidcraft/validation.json),
[layout audit](solidcraft/layout_validation.json), and
[design-edit check](solidcraft/design_edit_validation.json).

The original V4 migration passed 74 project tests and recorded 72 shared-helper
tests; those reports are preserved in its archive. The V5 migration additionally
checks native document identity, canonical geometry, sealed-writer guards and
V5-only linked layouts. The live preservation audit checks all four sealed releases.

## Edit the design

Edit `gearbox_native/design.yaml`, for example:

```yaml
parameters:
  rotor_thickness: 5.2
  disc_gap: 0.6
```

These overrides apply to the native recipe only. All supported defaults are in
`gearbox_native/common_defaults.yaml`, `captured_defaults.yaml`, and
`compact_defaults.yaml`, and `simple_defaults.yaml`; construction
is in `gearbox_native/simple.py`, `interfaces.py`, `captured.py` and `parts.py`.
The cycloid's analytic source is `cycloid_equation.py`; the installed CAD API
requires automatically sampled boundaries. Unknown override names and
invalid mechanical clearances are rejected. The native recipe imports no legacy
SCAD generator and does not require a SCAD snapshot to build or validate.

Then run from the project directory:

```powershell
python working_solidcraft.py --modes 3dpr true --stl --extras --verify
```

Changing a piece's geometry invalidates its cache; unchanged, verified pieces
are reused after checking the geometry, policy and artifact hashes. Use this command directly for
native iteration; it does not repopulate or regenerate the SCAD catalogue.
`action_make_solidcraft.py` additionally populates/materializes the catalogue.
The pipeline retains independent output switches. The V5 catalogue selects
`oobb_details.run_scad=False` and `run_solidcraft=True`; SCAD remains in the sealed V4 release.

Ordinary parts first use named native sketches, dimensions, extrusions,
revolutions and cuts. Dense cycloidal rotors, or pieces the Boolean kernel cannot
build reliably, use native sketch patches, surface extrusions/revolutions and
stitching. **There are no imported STEP or mesh bodies in the deliverables.**

Native dimensions can be edited in SolidCraft. Surface-built pieces expose their
sketch/surface history and a `profile_unit` scale; their semantic dimensions
(bearing seats, rotor thickness, lobe shape, etc.) are best changed in the recipe
and regenerated together. Changing an isolated boundary sketch without its
adjacent surfaces can break stitching. Recipe regeneration keeps them consistent.
Make a separate copy for manual SolidCraft edits: rebuilding replaces generated
outputs. The recipe is the source of truth for coordinated changes across parts.

The native lobe sampler starts with 48 spans per lobe and adaptively refines to a
0.005 mm chord target (1,292 outline vertices for this configuration). The old
SCAD sampler is unchanged. `samples_per_lobe` and `profile_tolerance` remain
editable design parameters; native generation retains every point it generates.

## Verification with room for the native kernel

The user explicitly requested practical native validation, not exact equivalence
to the old SCAD model. `gearbox_native/acceptance.py` applies only to this project;
the shared plate backend retains its stricter defaults.

Every published piece must pass:

- Native execution without feature errors, with fully constrained sketches.
- A valid exported solid with the expected solid count.
- Bounds within **0.05 mm** of the current recipe,
  and volume within **0.5%** (minimum allowance 0.05 mm³).
- Ordinary parts also receive STEP boundary samples at **0.05 mm**. Dense rotors
  use the native mesh surface check rather than repeating an exact comparison
  of thousands of faces. Their private validation mesh is made even when STL
  publication is turned off.
- A watertight, consistently wound, positive-volume STL when requested, with a
  **0.1 mm** sampled surface allowance for tessellation.
- Save/reopen checks and a real dimension edit, exported and reopened again.
  The edit must measurably change material in the expected direction; a loose
  geometry tolerance alone cannot make an unchanged model pass that test.

Small reported Boolean retries are allowed: translations/face shifts up to
0.01 mm, rotation up to 0.0001 rad, and kernel tolerance up to 0.05 mm. Their
original diagnostics remain in the attempt inspection files. Larger or
unclassified warnings fail. These checks are engineering sanity checks, not a
proof of exact mathematical equivalence or physical bearing fit.

If SolidCraft's STL has open tessellation seams but its exported STEP is valid,
the STL is tessellated from **that native export**, preserving the raw STL for
diagnostics. No reference/SCAD geometry is substituted into a deliverable.

The old exact comparator and SCAD snapshot remain available as historical
migration diagnostics. Neither is an ongoing acceptance requirement.

## Files and status

### Exploded still and animation

The native presentation is in
`parts/oobb_part_motor_gearbox_cycloidal_version_5_20_to_1_reduction/solidcraft_renders/true/`:

- `solidcraft_exploded.png`: 2000 × 2000 exploded still with numbered callouts.
- `solidcraft_exploded_key.png`: the same view with a component-name key.
- `solidcraft_exploded.mp4`: 1200 × 1200, 24 fps, 15-second animation.
- `solidcraft_exploded.gif`: a smaller looping preview.
- `solidcraft_exploded.blend`: editable objects, materials, camera and keyframes.

The animation separates the assembly, shows 20 input turns and one casing/output
turn while exploded, then reassembles it. It presents the current printed parts;
purchased bearings, screws, motor and coupler are omitted. The separation is an
illustrative presentation, not a collision-checked removal procedure. All visible
part meshes come from the verified native SolidCraft exports.

Regenerate native parts after changing `gearbox_native/design.yaml`, then run:

```powershell
& 'C:/od/OneDrive/docs/software_cad_mcp_helper/.venv/Scripts/python.exe' render_solidcraft_exploded.py
```

Blender and ffmpeg must be on PATH. `--preview` makes the still and editable scene;
`--mode 3dpr` selects print-clearance exports; `--spacing 15` increases separation.
The renderer checks source hashes and the current recipe to prevent using stale
native exports. It has no SCAD dependency. Assembly and explosion transforms live
in `gearbox_native/presentation.py`; appearance and camera setup live in
`gearbox_native/render_blender.py`. Save manual Blender edits to a separate copy
because rerendering regenerates the presentation scene.

For the hardware-inclusive version, add `--hardware`. Its still, numbered key,
MP4, GIF and editable Blender scene are saved separately in
`solidcraft_renders/true/with_hardware/`. Compact V5 includes **60 hardware
items**: five bearings, 26 bolts/screws, 22 nuts, three support posts, two grub
screws, one flanged coupler and one NEMA 17 motor, alongside the 13 native parts.
Hardware geometry and poses are generated by
`gearbox_native/presentation_hardware.py` from the current native recipe and
nominal OOBB dimensions. These are editable nominal visualization models with
bores, bearing race grooves and fastener drives; helical threads and bearing
rolling elements are omitted. They are not claimed as native SolidCraft feature
histories. No SCAD files or generator are needed for this route.

Outputs are under
`parts/oobb_part_motor_gearbox_cycloidal_version_5_20_to_1_reduction/`:

- `solidcraft/<mode>/<piece>.solidcraft`, with requested STEP/STL/PNG exports.
- `<mode>.solidcraft`: linked print layout, published after every current piece passes.
- `<mode>_solidcraft.stl/png` and `<mode>.step`: requested layout exports.

`build/solidcraft/latest_run.json` reports actual build status. Piece manifests
record hashes, the native construction method, validation policy and immutable
attempt evidence. Failed experiments remain under `build/solidcraft/` and are not
published. STEP-backed historical experiments are quarantined there.

Audit delivered files and their saved acceptance evidence:

```powershell
& 'C:/od/OneDrive/docs/software_cad_mcp_helper/.venv/Scripts/python.exe' -m gearbox_native.validate
```

Add `--deep` to repeat STEP/mesh checks against the **current native recipe**.
No SCAD files are read. `solidcraft/validation.json` records the result.
`solidcraft/verify_preservation.py` verifies the V1–V4 release archives, sealed
catalogue files and V4 native acceptance evidence. The original pre-migration
inventory and audit are historical records inside the V4 archive.

## Implementation lessons

Keep launchers stdlib-only and CAD dependencies in the configured worker Python.
Use private headless sessions and staged, checksummed publication. Preserve local
component trace ownership and explicit flat-bottom cavity depths. Coaxial
sections are resolved in radius/Z space before native construction.

For surface-built pieces, patch the selected outer wire so holes remain open;
use consistent arc partitions on adjacent surfaces; and compute a custom plane's
normal from X cross Y, including mirrored parts. Split only existing boundary
faces at axial stations, without adding internal cap material. The complete
cycloidal polygon remains in the native sketch.


## Version 5 preservation and presentation provenance

At the initial V5 baseline, native part documents were byte-identical to V4.
The compact revision regenerates changed pieces and its presentation from the
current recipe. Original raw frames and presentation are under
`outputs/v5_before_compact/solidcraft_renders/`; they are not current deliverables.
V5 manifests inherit immutable acceptance records from releases/version_4/evidence,
so clearing build/ does not remove the inherited part evidence. New linked layouts
were built and reopened using V5 paths. The current configuration, recipes and
newest build/audit reports live outside the sealed release and remain editable.

The shared compiler began omitting empty Boolean operands during migration.
The project's geometry hash now canonicalizes those no-ops, with a regression
test ensuring real solids and transforms still affect the hash. Original and
current plans match under that canonical comparison; no physical geometry was changed.

Initial V5 baseline presentation geometry and motion were identical to V4. Verified raw frames
were reused, labels and video overlays were changed to V5, and Blender document
links were rebased to V5. Both resulting videos/GIFs were decoded and checked.
The render reports record this provenance; future renders build from the active
native exports normally.
