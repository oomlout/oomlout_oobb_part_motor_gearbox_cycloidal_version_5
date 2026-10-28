# Historical V6 control workflow

V6 is sealed in `releases/version_6/`. The workflow below is historical reference only. V7 uses direct, whole-design propagation from SolidCraft's Parameters menu: see [NATIVE_V7.md](NATIVE_V7.md). Do not follow the external Update steps below for the native V7 master.

# Version 6 gearbox controls

The explorer and native master now feed the same mechanical recipe. You can
change settings without editing Python. The selected default remains the 20:1,
72.3 mm core, 32 mm high gearbox with two 6810 casing bearings.

## Use the connected explorer

Run `python action_gearbox_controls.py` from this project, or open
<http://127.0.0.1:8766> while its local service is running.

1. Change the existing explorer controls.
2. **Check gearbox** checks catalogue choices, the complete axial/radial recipe,
   and the current cycloid's fixed sampling. The diagram alone is a study.
3. **Update gearbox** builds a separate OOMP catalogue revision, checks native
   solids and exports, reopens them, tests real native edits, and checks sampled
   assembly motion and installation. It selects the revision only after passing.
4. **Load accepted settings** returns to the selected working design.

Builds take several minutes. Status and the build log are shown on the page.
If a build fails, its evidence remains in `build/parametric_v6/updates/`; the
previous accepted parts and active selection remain available. Old revisions
are retained. Versions 1–5 remain sealed.

The offline HTML still works for studies and JSON export; it cannot launch CAD.
An exported `gearbox-controls.json` can be applied with:

```powershell
python action_update_gearbox.py --settings gearbox-controls.json --check
python action_update_gearbox.py --settings gearbox-controls.json
```

## Use SolidCraft parameters

Open `gearbox_controls.solidcraft` in the project root. Its favourite parameters
are the master controls. Edit them, save, then run:

```powershell
python action_update_gearbox.py --from-native gearbox_controls.solidcraft
```

You can also use **Load saved SolidCraft controls** in the connected explorer,
inspect the proposed geometry, and click **Update gearbox**.

**Master parameters need the update action.** SolidCraft's linked documents do
not inherit parameter overrides from their parent. A native parameter edit also
cannot run Python validation or replace the cycloid's sample stations. Changing
a contact count or bearing selection therefore regenerates the affected parts.

The individual `rotor_a.solidcraft` and `rotor_b.solidcraft` documents additionally
have genuine live local dimensions:

- Eccentricity changes the equation outline **and both orbit-hole families**.
- Guide/standoff pitch and body radii change their corresponding clearance holes.
- Disc thickness changes all cap/wall heights and the bearing-seat floor.
- Centre-bearing OD/width change the seat, retaining lip aperture and seat depth.
- Pitch, contact radius and profile clearance drive the shared equation profile.

The same expressions are used on all adjoining cap and wall boundaries so the
edited rotor remains closed. Local edits do not synchronize the other pieces.
Use the master update before manufacturing a changed gearbox. Local bearing
dimensions are geometric edit controls, not a substitute for selecting a real
bearing through the master.

## Controls and practical limits

| Master name | Default | What follows it |
|---|---:|---|
| `reduction` | 20 | N contacts, N−1 disc lobes, opposed phase and output ratio |
| `automatic_pitch` | 1 | Minimum pitch from feature webs, contact spacing and analytic undercut |
| `radius_buffer` | 0 mm | Extra automatic radius, rounded up to 0.05 mm |
| `contact_pitch_radius` | 31.15 mm | Manual pitch; ignored while automatic mode is on |
| `contact_radius` | 3 mm | Circular casing contact and conjugate disc profile |
| `eccentricity` | 1.4 mm | Cams, disc orbits, profile, both hole families and fit poses |
| `profile_clearance` | 0.2 mm | Profile/contact running clearance |
| `casing_wall` | 2 mm | Wall outside contacts and bearing seats |
| `disc_thickness` / `disc_gap` | 5 / 0.5 mm | Disc and carrier stack, casing split, cam positions |
| `standoff_radius` / `standoff_pitch_radius` | 2.7 / 18.55 mm | Integral posts, sockets and rotor clearance tracks |
| `guide_radius` / `guide_pitch_radius` | 1.5 / 17.4 mm | Screw size, head/nut cuts, guide tracks and hardware model |
| `top_bearing` / `bottom_bearing` | 6703 / 6703 | Independent seats, shoulders, journals, axial centres and hardware |
| `reference_bearing` | 6810 | Explorer scale only; actual casing bearings remain 6810 |
| `input_angle` | 0° | Explorer mechanism position |
| `reference_underlay` | 1 | Explorer reference bearing visibility |
| `amber_clearance` | 0.1 mm | Explorer warning threshold, not manufacturing clearance |

The installed OOBB socket-head catalogue supports M3 and M6, so production guide
radii are 1.5 or 3 mm. Other radii remain studies. M6 requires different spacing
and eccentricity and still needs a full fit check. Bearing selections use OOBB
dimensions. Unsupported catalogue sizes, omitted bearings and the explorer's
special-width `6700-open3` study are rejected by the production bridge.

Ranges are input bounds, **not a guarantee that every combination fits**. The
fixed 6810 casing limits insertion and bearing-wall support. Disc retaining lips,
eccentric key walls, post webs, fastener engagement and head clearances impose
further limits. Thin discs or a larger bearing can require other settings to
change. Screws remain capped at 35 mm. No hidden reduction in required material
or acceptance tolerance makes an invalid combination pass.

## Reproducibility and evidence

`gearbox_native/controls.py` is the shared control map. Saved values are in
`gearbox_native/control_values.json`; `solidcraft/active_design.json` identifies
the accepted revision. The normal verbose `working_oomp_populate.py` taxonomy
loop and kwargs flow remain in use. Each update follows populate → working_oomp
→ working_solidcraft. Local mechanism defaults remain beside their implementations.

The existing `design.yaml` can hold unrelated advanced overrides. Conflicting
overrides must be moved to shared controls, rather than silently masking them.

Native geometry uses the shared `cycloidal_disc` / normalized `parametric_profile`
component. Formula-linked polylines are not exact analytic CAD curves. The update
checks fixed stations with `validate_edit`, records whether new sampling is
required, then regenerates the profile. The existing acceptance policy is intact.

Useful evidence:

- `build/parametric_v6/isolated_rotor/measurements.json`: real eccentricity edit,
  native health, STEP/STL checks, save/reopen and edited save/reopen.
- `build/parametric_v6/dimension_edit/measurements.json`: coordinated native disc
  thickness and both hole-circle position edits against an independent solid.
- Each accepted revision's `control_build.json`, `parametric_fit.json` and
  individual native manifests: complete build and fit provenance.
- `examples/shared_controls/`: baseline and alternative settings. A JSON example
  is a starting point, not proof of a fully accepted native build. See its README.

Use `--no-select` to validate a complete example without changing the active
design. `--recipe-only` runs a diagnostic fit study; it does not produce newly
accepted native parts. Physical fit, wear and load testing remain necessary.
