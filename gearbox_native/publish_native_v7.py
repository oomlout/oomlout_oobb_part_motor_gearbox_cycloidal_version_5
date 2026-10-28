"""Install only the verified native V7, preserving the inherited starting files."""
import hashlib
import json
from pathlib import Path
import shutil
from gearbox_native.project import PROJECT, active_part, require_editable
from gearbox_native.verify_v7_assembly import CASES


def copy(source,destination):
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,destination)


def main():
    build=PROJECT/'build/native_v7/assembly_03';views=PROJECT/'build/native_v7/presentation_01'
    proof=json.loads((build/'assembly_verification.json').read_text())
    assert proof['status']=='passed' and set(proof['cases'])==set(CASES)
    assert all(row['status']=='passed' for row in proof['cases'].values())
    exported=json.loads((views/'export.json').read_text())
    assert exported['status']=='native_export_checked'
    assert exported['source_sha256']==proof['native_sha256']==hashlib.sha256((build/'gearbox.solidcraft').read_bytes()).hexdigest()
    guards=json.loads((build/'guard_checks/guards.json').read_text());assert guards['status']=='passed'
    fits={}
    for case in ('baseline','reduction_16','dimensions','different_bearings','M6_guides','manual_pitch'):
        path=build/'verification'/case/'fit/native_fit.json'
        data=json.loads(path.read_text());assert data['status']=='passed'
        fits[case]=str(path.relative_to(PROJECT))
    assert hashlib.sha256((PROJECT/'gearbox_native/acceptance.py').read_bytes()).hexdigest()=='aef1e8a522769f4e35fd83bccd3a281fa35bf24b36d6034549d42dad786bb311'
    assert json.loads((PROJECT/'solidcraft/preservation.json').read_text())['status']=='passed'
    part=active_part();require_editable(part)
    assert not (PROJECT/'solidcraft/native_v7.json').exists(),'Already installed; do not overwrite user edits'
    old=part/'solidcraft/inherited_layouts';old.mkdir(exist_ok=True)
    for filename in ('true.solidcraft','3dpr.solidcraft','gearbox_controls.solidcraft','README.md','VERSION_7_DEVELOPMENT.md',
                     'true_solidcraft_manifest.json','3dpr_solidcraft_manifest.json'):
        if (part/filename).exists():copy(part/filename,old/filename)
    copy(PROJECT/'gearbox_controls.solidcraft',PROJECT/'solidcraft/inherited_v6/gearbox_controls.solidcraft')
    copy(build/'gearbox.solidcraft',PROJECT/'gearbox_controls.solidcraft')
    copy(build/'gearbox.solidcraft',part/'gearbox_controls.solidcraft')
    copy(build/'profile.json',PROJECT/'solidcraft/native_v7_profile.json')
    for source,target in [('assembled','true'),('3dpr','3dpr'),('exploded','exploded')]:
        for ext in ('solidcraft','png','step','stl'):
            copy(views/(source+'.'+ext),part/(target+'.'+ext))
        for ext in ('png','stl'):
            copy(views/(source+'.'+ext),part/(target+'_solidcraft.'+ext))
        (part/(target+'_solidcraft_manifest.json')).write_text(json.dumps(dict(
            status='success',construction='native',native_only=True,version='version_7',
            canonical_master=str(PROJECT/'gearbox_controls.solidcraft'),
            snapshot=True,geometry='manufacturing clearances',external_piece_links=False,
            verification_evidence=str(build),export_evidence=str(views)),indent=2),encoding='utf-8')
    for file in (views/'parts').iterdir():copy(file,part/'native_parts'/file.name)
    (part/'README.md').write_text('# Native V7 snapshots\n\n'
        'The working master is [../../gearbox_controls.solidcraft](../../gearbox_controls.solidcraft). '
        'Change its favourite parameters inside SolidCraft; no regeneration action is needed.\n\n'
        'See [the parameter guide](../../NATIVE_V7.md) and [verification index](../../solidcraft/native_v7.json).\n\n'
        'Local gearbox_controls.solidcraft, true.solidcraft, 3dpr.solidcraft and exploded.solidcraft are initial '
        'self-contained snapshots, not synchronized copies of the master. Individual current STEP/STL files '
        'are in native_parts/. The solidcraft/true and solidcraft/3dpr source documents and fits/ are '
        'inherited V6 evidence, not dependencies of the new master.\n',encoding='utf-8')
    (part/'VERSION_7_DEVELOPMENT.md').write_text('See [the current V7 development record](../../VERSION_7_DEVELOPMENT.md).\n',encoding='utf-8')
    record=dict(version='version_7',state='native-only',master='gearbox_controls.solidcraft',
        initial_sha256=hashlib.sha256((PROJECT/'gearbox_controls.solidcraft').read_bytes()).hexdigest(),
        profile='solidcraft/native_v7_profile.json',assembly_verification=str((build/'assembly_verification.json').relative_to(PROJECT)),
        isolated_rotor_verification='build/native_v7/rotor_10/verification.json',
        guard_verification=str((build/'guard_checks/guards.json').relative_to(PROJECT)),
        fit_verification=fits,initial_parameters=proof['cases']['baseline']['parameters'],
        views=str(views.relative_to(PROJECT)),part_id=part.name,
        note='The master is editable. Its initial hash is provenance, not a requirement that later user edits match.')
    (PROJECT/'solidcraft/native_v7.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    pointer=json.loads((PROJECT/'solidcraft/active_design.json').read_text());pointer.update(state='native-only',master=record['master'],verification='solidcraft/native_v7.json')
    (PROJECT/'solidcraft/active_design.json').write_text(json.dumps(pointer,indent=2),encoding='utf-8')
    print('Installed native-only V7:',PROJECT/'gearbox_controls.solidcraft')


if __name__=='__main__':main()
