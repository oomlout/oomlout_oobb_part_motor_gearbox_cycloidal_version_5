"""Publish already-verified V9 drive builds; never bypass geometry acceptance."""
import argparse
import json
import shutil
from pathlib import Path
from gearbox_native.project import PROJECT, require_editable
from gearbox_native.native_catalogue import publish, sha


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def write(path, data):
    path.write_text(json.dumps(data, indent=2)+'\n', encoding='utf8', newline='\n')


def hardware(part, values, bearing):
    posts = int(values['posts_enabled']) * 3
    rows = [
        ('6808 bearing (40 x 52 x 7 mm)', 2),
        ('6702 bearing (15 x 21 x 4 mm)', 4 if bearing else 3),
        (f"M3 x {values['guide_screw_length']:g} socket-cap guide screw + M3 nut", int(values['guide_count'])),
        ('M3 x 25 socket-cap standoff screw + M3 nut', posts),
        (f"M3 x {values['join_screw_length']:g} socket-cap casing screw + M3 nut", 4),
        ('M3 x 35 socket-cap axial tie screw + M3 nut' if 'bearing_tie_diameter' in values else f"M2.5 x {35 if bearing else 12} socket-cap hub joining screw + M2.5 nut", 1),
        ('M3 x 6 socket-cap D-sleeve clamp screw + M3 nut', 1),
    ]
    if not bearing:
        rows.extend([('M3 x 14 countersunk NEMA17 mounting screw', 4),
                     ('M3 x 8 countersunk motor-shaft clamp screw + M3 nut', 1)])
    elif 'bearing_holder_depth' in values:
        rows.append(('M3 x 10 countersunk bearing-holder mounting screw + M3 nut',4))
    rows.append(('M6 nuts for selected output mounting holes', 'Up to 12, optional'))
    text = '# Hardware\n\n| Item | Quantity |\n|---|---:|\n'
    text += ''.join(f'| {name} | {count} |\n' for name, count in rows if count != 0)
    text += '\nSocket-cap lengths are measured under the head; countersunk lengths include the head. '
    text += 'All captive nut pockets use `overhang=True`. The exploded native view shows printed pieces; hardware is listed here.\n\n'
    text += ('Print the separate bearing holder on its broad underside with the bearing recess opening upward. '
             'Fit the guide/standoff nuts in the shared motor plate before bolting the holder beneath it. '
             'Four M3 x 10 countersunk screws use the 31 mm square NEMA17 pattern; load the holder nuts from below. '
             'Fit the 6702 into the upward-open cup before assembly. Allow 2.7 mm below the holder for the axial screw head. '
             if bearing and 'bearing_holder_depth' in values else
             'The base 6702 bearing loads from underneath. Its inner race is retained by the printed washer and the long axial screw. '
             'Allow 5 mm beneath the baseplate for that screw head. '
             if bearing else
             'Keep the 8 mm motor spacer and its full-height access gap. Tighten the axial hub screw before inserting the motor shaft. ')
    if 'bearing_tie_diameter' in values:
        text=text.replace('2.7 mm below the holder for the axial screw head','at least 3.5 mm below the holder for the retaining collar')
        text += 'Fit the M3 nut into the upper hub split before closing the halves. Tighten the M3 x 35 through the cap washer and both hub pairs, then slide on the D-sleeve. '
    else:text += 'Load the top M2.5 nut and tighten the axial join before sliding on the D-sleeve. '
    text += 'Load its M3 nut sideways and tighten the M3 x 6 clamp into the locating recess. '
    text += 'The casing is the reduced-speed output; the exposed D-shaft is the input.\n'
    (part/'HARDWARE.md').write_text(text, encoding='utf8')


def samples(part, root, trials):
    target = part/'fit_samples'; target.mkdir(exist_ok=True)
    for name in ('3dpr.solidcraft', '3dpr.step', '3dpr.stl', 'samples.json'):
        shutil.copyfile(root/'drive_fit_samples_01'/name, target/name)
    (target/'README.md').write_text('''# Small fit samples

Print `3dpr.stl` using the material, orientation and settings intended for the gearbox.
There are seven separate pieces: three bearing-journal gauges, one common D-key,
and three matching socket rings. Recessed dots identify sample 1, 2 or 3.

| Dots | 6702 journal diameter | D-socket clearance |
|---|---:|---:|
| 1 | 14.85 mm | 0.100 mm |
| 2 | 14.90 mm | 0.050 mm |
| 3 | 14.95 mm | 0.025 mm |

Use an actual 6702 bearing to select the closest smooth-fitting journal.
Try each socket on the common D-key. Sample 2 matches the new defaults.
The allowances are radial and also apply at the D-flat, not diametral.
A tight gauge is useful evidence to retain or increase clearance; forcing a bearing
onto a printed journal is not the intended fit. These coupons do not measure gearbox backlash.
''', encoding='utf8')
    if not trials:
        return
    target = part/'clearance_trials'; target.mkdir(exist_ok=True)
    report = read(root/'clearance_trials_01/report.json')
    write(target/'report.json', report)
    for case in report:
        folder = target/case; folder.mkdir(exist_ok=True)
        for name in ('3dpr.solidcraft', '3dpr.step', '3dpr.stl'):
            shutil.copyfile(root/'clearance_trials_01'/case/name, folder/name)
    text = '''# 35:1 rotor clearance comparison

Each folder contains only the two cycloids, ready to print at Z=0. These are
35:1 rotors with the same 27.9 mm contact pitch, 15 mm guide pitch and 16.15 mm
standoff pitch as the assembled 35:1 gearbox. Do not use them in the 10:1 preset.
The centre bearings remain 6702. Use the print layout as a complete matched pair.

| Pair | Profile allowance | Guide allowance | Standoff allowance | Calculated profile-only freedom |
|---|---:|---:|---:|---:|
'''
    for case, row in report.items():
        text += f"| [{case}]({case}/3dpr.stl) | {row['profile_clearance']:.2f} mm | {row['guide_clearance']:.2f} mm | {row['post_clearance']:.2f} mm | {row['profile_only_deadband_deg']:.3f} degrees |\n"
    text += '''
**Balanced is the default.** Original recreates the earlier running allowances;
close is the tighter experiment. Guide/post allowances are added to the orbital
clearance and do not change eccentricity. All three pairs cleared 180 sampled
input angles, native health, fixed profile sampling and valid STEP/STL checks.

The last column is calculated casing freedom with the input fixed and ideal guide
constraints. It excludes guide, bearing, keyed-joint and elastic movement; it is
not a prediction or measurement of total gearbox backlash. Check easy full-turn
motion by hand before applying power. Compare output reversal at the same light
load with the input held, using the same casing and hardware for each pair.
'''
    (target/'README.md').write_text(text, encoding='utf8')


def run(stepper, bearing, auxiliary):
    import working_oomp_populate as populate
    sources = {'35': (stepper/'gearbox.solidcraft', stepper/'views_stepper'),
               '10': (stepper/'compact10.solidcraft', stepper/'views_10'),
               '35_bearing': (bearing/'gearbox.solidcraft', bearing/'views_bearing')}
    options = populate.get_options()
    rows = {}
    for key, (source, views) in sources.items():
        record, mechanical = read(views/'export.json'), read(views/'mechanical.json')
        assert record['status'] == 'native_export_checked' and mechanical['status'] == 'passed'
        assert record['source_sha256'] == mechanical['source_sha256'] == sha(source)
        assert len(record['parts']) == 11 and record['print_mesh']['watertight']
        assert all(p['native_shape']['valid'] and p['native_shape']['solid_count']==1 and p['mesh']['watertight'] for p in record['parts'].values())
        rows[key] = mechanical
    edit = read(auxiliary/'drive_edit_01/verification.json')
    trials = read(auxiliary/'clearance_trials_01/report.json')
    assert edit['status'] == 'passed' and all(t['status'] == 'passed' for t in trials.values())
    index_path = PROJECT/'solidcraft/native_v9.json'
    index = read(index_path)
    assert index['acceptance_sha256'] == sha(PROJECT/'gearbox_native/acceptance.py')
    if index['verification'] != 'solidcraft/native_v9_drive_verification.json':
        index['previous_motor_verification'] = index['verification']
    shutil.copyfile(sources['35'][0], PROJECT/'gearbox_controls.solidcraft')
    shutil.copyfile(sources['35_bearing'][0], PROJECT/'gearbox_bearing_controls.solidcraft')
    shutil.copyfile(stepper/'profile.json', PROJECT/'solidcraft/native_v9_profile.json')
    variants = {}
    for option in options:
        is_bearing = option.get('input_variant') == 'bearing_input'
        key = str(option['reduction']) + ('_bearing' if is_bearing else '')
        source, views = sources[key]
        part = PROJECT/'parts'/populate.build_oomp_id(option)
        require_editable(part)
        master_name = option.get('native_master', 'gearbox_controls.solidcraft')
        publish(part, source, views, option['native_parameters'], sha(PROJECT/master_name))
        hardware(part, rows[key]['parameters'], is_bearing)
        samples(part, auxiliary, option['reduction'] == 35)
        if not is_bearing:
            (part/'shaft_reprint/README.md').write_text('''# Revised stepper drive and rotors

`3dpr.stl` contains six replacements: lower hub, upper hub, external D-sleeve,
front pin carrier and both tighter-clearance cycloids. Keep the existing motor
mount, 8 mm access spacer and three casing pieces. Replace the old front 6701
with a 6702 bearing. Add one M3 x 6 socket-cap screw and nut for the sleeve.
The motor clamp and upward M2.5 x 12 hub screw remain in use.

Individual native STEP/STL files are in `../native_parts/`. The authoritative
editable master is `../gearbox_controls.solidcraft`; this STL is a convenience
layout assembled from its checked native exports.
''', encoding='utf8')
        variants[key] = dict(part_id=part.name, master_sha256=sha(source), source_master=master_name,
                             source_master_sha256=sha(PROJECT/master_name), native_parameters=option['native_parameters'])
        rows[key]['print_parts'] = 11
        rows[key]['native_body_count'] = 11
        rows[key]['native_parts'] = {n: dict(valid=r['native_shape']['valid'], mesh=r['mesh'])
                                    for n, r in rows[key]['native_parts'].items()}
        if not is_bearing:
            rows[key]['reprint_sha256'] = sha(part/'shaft_reprint/3dpr.stl')
    proof = dict(status='passed', variants=rows, native_drive_edit=edit, clearance_trials=trials,
                 reused_stepper_parts=read(auxiliary/'retrofit_reuse.json'),
                 physical_fit_tested=False, note='Sampled geometric motion and nominal hardware checks; backlash has not been physically measured.')
    write(PROJECT/'solidcraft/native_v9_drive_verification.json', proof)
    index.update(master_sha256=sha(PROJECT/'gearbox_controls.solidcraft'), variants=variants,
                 bearing_master='gearbox_bearing_controls.solidcraft', component_count=11,
                 bearing_master_sha256=sha(PROJECT/'gearbox_bearing_controls.solidcraft'),
                 revision='Tighter running clearances, shared 6702 front support, external D-sleeve and bearing-input variant',
                 verification='solidcraft/native_v9_drive_verification.json')
    write(index_path, index)
    print('Published', ', '.join(variants), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--stepper', type=Path, required=True)
    p.add_argument('--bearing', type=Path, required=True)
    p.add_argument('--auxiliary', type=Path, default=PROJECT/'build/native_v9')
    a = p.parse_args()
    run(a.stepper.resolve(), a.bearing.resolve(), a.auxiliary.resolve())
