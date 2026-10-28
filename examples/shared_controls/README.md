# Shared-control examples

Apply any file through the connected explorer's settings, or:

```powershell
python action_update_gearbox.py --settings examples/shared_controls/sixteen.json --no-select
```

`--no-select` keeps the current working gearbox selected. Omit it to select a
successfully validated revision. The default remains `baseline.json` (20:1).

| File | Main changes | Verification performed |
|---|---|---|
| `baseline.json` | Current 20:1, 1.4 mm eccentricity, 6703/6703 | Both native modes, exports, real edits, reopen, linked layouts; 143 sampled motion poses and installation/access checks |
| `sixteen.json` | 16:1; automatic pitch 29.4 mm | Both native modes and linked layouts; 141 sampled motion poses and installation/access checks |
| `asymmetric.json` | Lower 6803 / upper 6703, 6 mm discs, 1 mm eccentricity, revised hole circles | Recipe geometry, 143 sampled motion poses and installation/access checks; not a newly accepted native build |
| `m6.json` | M6 guides, 0.5 mm eccentricity, guide radius 18.7 mm and post radius 20 mm from centre | Recipe geometry, 143 sampled motion poses and installation/access checks; not a newly accepted native build |
| `e_1_2.json` | 1.2 mm eccentricity | Recipe screening and explorer/recipe pitch agreement only |
| `buffer.json` | 1.2 mm eccentricity with 0.1 mm extra pitch | Recipe screening and explorer/recipe pitch agreement only |
| `thicker.json` | 5.2 mm discs and 0.7 mm gap | Recipe screening; separate native rotor thickness/hole-circle edit proof |
| `manual.json` | Manual 31.2 mm pitch | Recipe screening and explorer/recipe pitch agreement only |

Accepted native examples:

- [20:1 control build](../../parts/oobb_part_motor_gearbox_cycloidal_version_6_20_to_1_reduction_configuration_3d9262f6/control_build.json)
- [16:1 control build](../../parts/oobb_part_motor_gearbox_cycloidal_version_6_16_to_1_reduction_configuration_805810a8/control_build.json)

Diagnostic evidence is under `build/parametric_v6/updates/configuration_cf886c08`
(mixed bearings) and `configuration_d73e6870` (M6). Both studies triggered a
fixed-station sampling rejection, correctly requiring a regenerated profile.
No example establishes physical load capacity or wear performance.
