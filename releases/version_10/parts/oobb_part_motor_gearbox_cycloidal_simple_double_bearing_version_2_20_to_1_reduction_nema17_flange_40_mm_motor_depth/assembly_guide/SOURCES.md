# Assembly guide sources and regeneration

This guide describes the 40 mm motor-depth circular-plate adaptation. It does not change the native model, acceptance policy or preserved manual release.

## Geometry and validation

- Current native master: `simple_double_bearing_version_2_nema17_flange.solidcraft` in the repository root.
- Meshes: the accepted `build/nema17_separate_joiners_r2/views` export, staged by `gearbox_native.nema17_render.stage` into `build/nema17_depth40_guide/studio.npz`.
- Guide content and exact visible-body inventory: `gearbox_native/nema17_depth40_guide.py`; the exported inventory is `scene_manifest.json`.
- Full core path proof: `gearbox_native/nema17_depth40_access.py`; 19 steps and 2,023 native Boolean checks passed.
- Bench motor/tube proof: `gearbox_native/nema17_depth40_motor_access.py`; two axial paths and 174 Boolean checks passed, plus the three radial nut-loading paths and four grub key paths.
- The curved-face sweep uses the existing production verifier's conservative envelopes and independently verified clear through bores. It does not alter the acceptance threshold.
- Existing cover, joining screw, rotation and native export evidence is copied into `proofs/` and tied to the same source hash.
- Cable and connector geometry is not modeled. The guide explicitly routes the cable before closing the rear cover and requires a connector fit check on the bench.

## Documentation sources

- OOBB `RENDER_STYLE.md` and `presentation/STYLE.md`: teal casing, black stationary structure, yellow contact and guide sleeves, mixed-colour shaft; orthographic actual-CAD renders.
- Existing base guide and continuous insertion proofs establish the front-face-down core build and temporary shaft-tie reversal. This version retains that method but delays three long guides for the motor adapter.
- Hardware identities are checked against local OOMP records where an exact record exists. `hardware.csv` contains source links, alpha codes and dimensional requirements. No exact M3 x 14 socket-cap catalogue entry was found; the required size is retained from the current checked CAD.
- Assembly presentation references: [Prusa X-axis/extruder guide](https://help.prusa3d.com/guide/3-x-axis-extruder-assembly_199519) and [Voron Trident documentation](https://github.com/VoronDesign/Voron-Trident/blob/main/README.md). Geometry and assembly instructions here come from this project, not those mechanisms.

## Regeneration

Run from the repository root. The CAD checks require the CAD helper Python environment with OCP and the OOMP modules on PYTHONPATH. They are read-only checks.

```powershell
& 'C:/od/OneDrive/docs/software_cad_mcp_helper/.venv/Scripts/python.exe' -m gearbox_native.nema17_depth40_access
& 'C:/od/OneDrive/docs/software_cad_mcp_helper/.venv/Scripts/python.exe' -m gearbox_native.nema17_depth40_motor_access
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' -b -t 8 --python gearbox_native/nema17_depth40_studio.py -- 'C:/gh/oomlout_oobb_part_motor_gearbox_cycloidal_version_5/build/nema17_depth40_guide'
python -m gearbox_native.nema17_depth40_manual
python -m gearbox_native.nema17_depth40_qa
```

Re-stage meshes after any geometry change. Unset `NEMA_GUIDE_RENDER_ONLY` for a complete render; it may otherwise contain comma-separated scene keys for a targeted refresh. The QA command renders all PDF pages and checks bounds, local links, inventory, guide timing and source hashes. Inspect the resulting PNG pages before marking the visual review passed.
