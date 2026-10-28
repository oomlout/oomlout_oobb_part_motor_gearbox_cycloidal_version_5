"""Publish this checked V7 revision without replacing concurrent master edits."""
import hashlib
import json
import shutil
from pathlib import Path
from gearbox_native.project import PROJECT, active_part, require_editable


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    build=PROJECT/'build/native_v7/casing_bearings_02'
    views=PROJECT/'build/native_v7/casing_bearings_views_01'
    original='a66a9d1eac47e364987a32dcd7ddf8d9959e14f026513f8dc08024dee96e8084'
    master=PROJECT/'gearbox_controls.solidcraft'
    assert sha(master)==original,'Master changed while the revision was being checked; preserve those edits first.'
    read=lambda path:json.loads(path.read_text(encoding='utf-8'))
    baseline=read(build/'assembly_verification.json');edits=read(build/'casing_verification.json')
    exports=read(views/'export.json');selector=read(PROJECT/'build/native_v7/casing_selector/verification.json')
    assert baseline['status']==edits['status']==selector['status']=='passed'
    assert exports['status']=='native_export_checked'
    digest=sha(build/'gearbox.solidcraft')
    assert baseline['native_sha256']==edits['source_sha256']==exports['source_sha256']==digest
    assert set(edits['cases'])=={'6710','6811'} and len(selector['options'])==40
    assert read(PROJECT/'solidcraft/preservation.json')['status']=='passed'
    acceptance=sha(PROJECT/'gearbox_native/acceptance.py')
    assert acceptance=='aef1e8a522769f4e35fd83bccd3a281fa35bf24b36d6034549d42dad786bb311'
    from gearbox_native.verify_casing_bearings import verify_seat_faces
    verify_seat_faces(build)
    part=active_part();require_editable(part)
    backup=PROJECT/'solidcraft/revisions/v7_before_casing_bearings'
    backup.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(master,backup/master.name)
    record=dict(status='verified_native_revision',master='gearbox_controls.solidcraft',initial_sha256=digest,
                previous_sha256=original,previous_master=str((backup/master.name).relative_to(PROJECT)),
                baseline_verification=str((build/'assembly_verification.json').relative_to(PROJECT)),
                edit_verification=str((build/'casing_verification.json').relative_to(PROJECT)),
                seat_verification=str((build/'seat_verification.json').relative_to(PROJECT)),
                selector_verification='build/native_v7/casing_selector/verification.json',
                export_verification=str((views/'export.json').relative_to(PROJECT)),
                acceptance_sha256=acceptance,mechanical_fit_checked=False,default_casing_bearing=6810,
                options='solidcraft/casing_bearings.json',
                shared_catalogue='C:/od/OneDrive/docs/software_cad_mcp_helper/catalog',
                note='Native health, baseline equivalence, 6710/6811 edits, STEP/STL and two reopens checked. Optional casing fit guards default off.')
    shutil.copyfile(build/'gearbox.solidcraft',master)
    shutil.copyfile(master,part/master.name)
    for source,target in [('assembled','true'),('3dpr','3dpr'),('exploded','exploded')]:
        for ext in ('solidcraft','png','step','stl'):
            shutil.copyfile(views/(source+'.'+ext),part/(target+'.'+ext))
        for ext in ('png','stl'):
            shutil.copyfile(views/(source+'.'+ext),part/(target+'_solidcraft.'+ext))
        path=part/(target+'_solidcraft_manifest.json');manifest=read(path)
        manifest.update(verification_evidence=str(build),export_evidence=str(views),
                        revision='configurable_casing_bearings',source_sha256=digest)
        path.write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
    for path in (views/'parts').iterdir():shutil.copyfile(path,part/'native_parts'/path.name)
    (PROJECT/'solidcraft/native_v7_casing_bearings.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    index_path=PROJECT/'solidcraft/native_v7.json';index=read(index_path)
    index.setdefault('revisions',[]).append('solidcraft/native_v7_casing_bearings.json')
    index_path.write_text(json.dumps(index,indent=2),encoding='utf-8')
    print('Published configurable casing bearings to',master)


if __name__=='__main__':main()
