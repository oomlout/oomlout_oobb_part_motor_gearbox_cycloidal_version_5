"""Publish the accepted 5x5 native revision after mechanical and export checks."""
import argparse
import json
import shutil
import zipfile
import uuid
from gearbox_native.project import PROJECT
from gearbox_native.publish_v8_revision import read, sha
from gearbox_native.native_catalogue import publish


def write(path, value):
    """Replace metadata atomically, including the pointer watched by editor tools."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
        temporary.replace(path)
    finally:
        if temporary.exists():temporary.unlink()


def main(name):
    import working_oomp_populate
    import working_oomp
    folder=PROJECT/'build/native_v9'/name
    report=read(folder/'verification.json')
    assert report['status']=='passed'
    assert read(PROJECT/'build/native_v9/rotor_03/verification.json')['status']=='passed'
    source=folder/'gearbox.solidcraft'
    compact=folder/'compact_10/gearbox.solidcraft'
    baseline=read(PROJECT/'solidcraft/version_9_baseline.json')
    assert sha(PROJECT/'gearbox_controls.solidcraft') in (baseline['master_sha256'],sha(source))
    assert sha(PROJECT/'gearbox_native/acceptance.py')==baseline['acceptance_sha256']
    bearing_fits={case:read(folder/case/'bearing_fit.json') for case in ('baseline','compact_10')}
    assert all(record['status']=='passed' for record in bearing_fits.values())
    for ratio,native in [(35,source),(10,compact)]:
        views=read(folder/f'views_{ratio}/export.json')
        assert views['status']=='native_export_checked' and views['source_sha256']==sha(native)
    shutil.copyfile(source,PROJECT/'gearbox_controls.solidcraft')
    shutil.copyfile(folder/'profile.json',PROJECT/'solidcraft/native_v9_profile.json')
    shutil.copyfile(PROJECT/'NATIVE_V9_5X5.md',PROJECT/'NATIVE_V9.md')
    working_oomp_populate.main()
    for option in working_oomp_populate.get_options():
        working_oomp.main(part_filter=working_oomp_populate.build_oomp_id(option),wait_for_completion=True)
    variants={}
    for option in working_oomp_populate.get_options():
        ratio=option['reduction'];part_id=working_oomp_populate.build_oomp_id(option)
        native=source if ratio==35 else compact
        part=PROJECT/'parts'/part_id
        publish(part,native,folder/f'views_{ratio}',option['native_parameters'],sha(source))
        variants[str(ratio)]=dict(part_id=part_id,master_sha256=sha(native),native_parameters=option['native_parameters'])
        (part/'HARDWARE.md').write_text(
            '# Hardware\n\n'
            '| Item | Quantity |\n|---|---:|\n'
            '| 6808 bearing (40 × 52 × 7 mm) | 2 |\n'
            '| 6702 bearing (15 × 21 × 4 mm) | 2 |\n'
            '| 6701 bearing (12 × 18 × 4 mm) | 1 |\n'
            '| M3 × 25 socket-cap guide screw + M3 nut | 6 |\n'
            f'| M3 × 25 socket-cap standoff screw + M3 nut | {3 if ratio==35 else 0} |\n'
            '| M3 × 20 socket-cap casing screw + M3 nut | 4 |\n'
            '| M3 × 6 countersunk NEMA17 mounting screw | 4 |\n'
            '| M3 × 4 socket-cap hub joining screw + M3 nut | 1 |\n'
            '| M3 × 8 grub screw + M3 nut | 1 |\n'
            '| M6 nuts for selected output mounting holes | Up to 12, optional |\n\n'
            'Lengths are nominal under-head dimensions except countersunk screws, which include the head. '
            'The base grub screw is tightened before fitting the motor plate. The native exploded view '
            'shows printed parts; purchased hardware is listed here. Mounting screws for an attached '
            'OOBB structure depend on that structure. Physical fit/load testing remains necessary.\n',
            encoding='utf-8',newline='\n')
        readme=part/'README.md'
        if '(HARDWARE.md)' not in readme.read_text(encoding='utf-8'):
            readme.write_text(readme.read_text(encoding='utf-8')+'\n[Hardware for this published preset](HARDWARE.md)\n',encoding='utf-8',newline='\n')
    evidence=PROJECT/'solidcraft/evidence/v9_5x5.zip'
    with zipfile.ZipFile(evidence,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in folder.rglob('*.json'):
            if any(p in ('author','verify','session','reopen_exploded') or p.startswith('reopen_') for p in path.relative_to(folder).parts[:-1]):continue
            archive.write(path,path.relative_to(folder).as_posix())
        rotor=PROJECT/'build/native_v9/rotor_03'
        for path in rotor.glob('*.json'):archive.write(path,'isolated_rotor/'+path.name)
    summary=dict(status='passed',master_sha256=sha(source),acceptance_sha256=baseline['acceptance_sha256'],
                 evidence_archive=evidence.relative_to(PROJECT).as_posix(),evidence_sha256=sha(evidence),cases={},
                 variants=variants,physical_print_load_tested=False)
    for label,row in report['cases'].items():
        item=dict(status=row['status'],sampling=row['sampling'],parameters=row['parameters'],parts=row['parts'])
        if 'hardware' in row:
            item['hardware']=dict(status='passed',check_count=len(row['hardware']['checks']),maximum_overlap_mm3=row['hardware']['maximum_overlap_mm3'])
            item['maximum_intersection_mm3']=max(c['overlap_mm3'] for c in row['intersections'])
            item['maximum_motion_overlap_mm3']=max(c['overlap_mm3'] for c in row['motion'])
            fit=bearing_fits[label]
            item['bearing_fits']=dict(status=fit['status'],check_count=len(fit['checks']),maximum_overlap_mm3=fit['maximum_overlap_mm3'])
        if 'reopens' in row:item['reopens']=row['reopens']
        summary['cases'][label]=item
    write(PROJECT/'solidcraft/native_v9_5x5_verification.json',summary)
    index=read(PROJECT/'solidcraft/native_v9.json')
    index.update(master_sha256=sha(source),part_id=variants['35']['part_id'],variants=variants,
                 revision='35:1, 6808, fixed 5x5 full-width output and named shaft fits',
                 verification='solidcraft/native_v9_5x5_verification.json')
    write(PROJECT/'solidcraft/native_v9.json',index)
    active=read(PROJECT/'solidcraft/active_design.json');active['part_id']=variants['35']['part_id']
    write(PROJECT/'solidcraft/active_design.json',active)
    path=PROJECT/'gearbox_native/project.py'
    text=path.read_text(encoding='utf-8').replace('{VERSION}_20_to_1_reduction','{VERSION}_35_to_1_reduction')
    path.write_text(text,encoding='utf-8',newline='\n')
    old=PROJECT/'parts/oobb_part_motor_gearbox_cycloidal_version_9_20_to_1_reduction/README.md'
    note='> Initial V9 reference snapshot. The current populated main design is 35:1; see the root README.\n\n'
    if not old.read_text(encoding='utf-8').startswith(note):
        old.write_text(note+old.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
    (PROJECT/'README.md').write_text(
        '# Cycloidal gearbox — native SolidCraft V9\n\n'
        'The current design is **35:1 in a 74×74 mm (5×5 OOBB) output**, using '
        '**6808 casing bearings**, **1.5 mm contact radius** and **0.7 mm eccentricity**. '
        'Six guide screws and all three standoffs fit. V8 remains sealed.\n\n'
        'Open [the native master](gearbox_controls.solidcraft) and change its favourite '
        'parameters in SolidCraft. The complete nine-part gearbox updates inside the file. '
        '[Parameter and printing guide](NATIVE_V9.md) · '
        '[Verification](solidcraft/native_v9.json) · [Sealed V8](releases/version_8/README.md)\n\n'
        'The three output pieces have full-width square outlines. Only the centre M6 hole '
        'on each edge is omitted. Four inner half-grid M3 socket-cap screws join the stack; '
        'the lower holder retains overhang-enabled M3 and M6 nut pockets.\n\n'
        'The wiggle shaft uses shared named D-key geometry and bearing-derived journals. '
        'Radial key clearance is 0.10 mm and journal clearance is 0.075 mm. '
        'The contact pitch is 27.9 mm; casing height remains 27.3 mm above its lower face.\n\n'
        f'[35:1 parts and hardware](parts/{variants["35"]["part_id"]}/README.md) · '
        f'[Exploded view](parts/{variants["35"]["part_id"]}/exploded.png) · '
        f'[Print layout](parts/{variants["35"]["part_id"]}/3dpr.png) · '
        f'[10:1 preset](parts/{variants["10"]["part_id"]}/README.md)\n\n'
        'Both presets share the same feature graph and differ only in exposed native parameters. '
        'The 10:1 preset uses 0.9 mm eccentricity and disables the standoffs. '
        'View files are independent snapshots; save and run `python action_export_native.py` '
        'after editing. Use `--populate` to recreate the current catalogue presets through '
        'populate and working_oomp. The original V9 20:1 folder remains a reference snapshot.\n\n'
        'Native health, equation sampling, STEP/STL, save/reopen edits, motion and hardware '
        'clearances are checked under the unchanged acceptance policy. '
        'Physical printing and load testing remain outstanding. '
        '[Development notes](VERSION_9_DEVELOPMENT.md) describe the revision.\n',
        encoding='utf-8',newline='\n')
    print('Published V9 35:1 and 10:1 native presets',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--name',required=True);args=parser.parse_args();main(args.name)
