"""Publish the verified native OOBB tab rule and refreshed view snapshots."""
import hashlib
import json
from pathlib import Path
import shutil
from gearbox_native.project import PROJECT, active_part, require_editable


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    read=lambda path:json.loads(path.read_text(encoding='utf-8'))
    build=PROJECT/'build/native_v7/odd_oobb_tabs_01';views=PROJECT/'build/native_v7/odd_oobb_tabs_views_01'
    upgrade=read(build/'upgrade.json');proof=read(build/'casing_verification.json')
    rule=read(PROJECT/'build/native_v7/odd_oobb_tab_rule/verification.json')
    hardware=read(build/'tab_geometry.json');default_hardware=read(build/'default_tab_geometry.json');export=read(views/'export.json')
    assert upgrade['status']=='native_upgrade_checked' and upgrade['preserved_existing_parameters']
    assert proof['status']==rule['status']==hardware['status']=='passed'
    assert default_hardware['status']=='passed' and default_hardware['plate_size']==7
    assert proof['cases']['6812']['second_reopen_body_count']==8
    assert export['status']=='native_export_checked'
    source=PROJECT/'gearbox_controls.solidcraft'
    assert sha(source)==upgrade['source_sha256'],'Working master changed during verification; preserve its edits first.'
    digest=sha(build/'gearbox.solidcraft')
    assert digest==upgrade['updated_sha256']==proof['source_sha256']==export['source_sha256']
    part=active_part();require_editable(part)
    # This revision changes automatic sizing. The default 7x7 geometry is identical.
    default_parts={}
    for path in (views/'parts').glob('*.stl'):
        previous=part/'native_parts'/path.name
        assert sha(path)==sha(previous),('Default geometry changed:',path.name)
        default_parts[path.stem]=sha(path)
    assert len(default_parts)==8
    acceptance=sha(PROJECT/'gearbox_native/acceptance.py')
    assert acceptance=='aef1e8a522769f4e35fd83bccd3a281fa35bf24b36d6034549d42dad786bb311'
    backup=PROJECT/'solidcraft/revisions/v7_before_odd_oobb_tabs';backup.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(source,backup/source.name)
    record=dict(status='verified_native_revision',master='gearbox_controls.solidcraft',initial_sha256=digest,
        previous_sha256=upgrade['source_sha256'],previous_master=str((backup/source.name).relative_to(PROJECT)),
        upgrade_verification=str((build/'upgrade.json').relative_to(PROJECT)),
        edit_verification=str((build/'casing_verification.json').relative_to(PROJECT)),
        rule_verification='build/native_v7/odd_oobb_tab_rule/verification.json',
        hardware_verification=str((build/'tab_geometry.json').relative_to(PROJECT)),
        default_hardware_verification=str((build/'default_tab_geometry.json').relative_to(PROJECT)),
        export_verification=str((views/'export.json').relative_to(PROJECT)),
        acceptance_sha256=acceptance,unchanged_default_part_stl_sha256=default_parts,
        note='Smallest odd OOBB footprint; outer M6 head/nut envelopes plus 0.5 mm radial clearance. Only mounting hardware clearance checked.')
    shutil.copyfile(build/'gearbox.solidcraft',source);shutil.copyfile(source,part/source.name)
    for name,target in [('assembled','true'),('exploded','exploded'),('3dpr','3dpr')]:
        for ext in ('solidcraft','png','step','stl'):shutil.copyfile(views/(name+'.'+ext),part/(target+'.'+ext))
        for ext in ('png','stl'):shutil.copyfile(views/(name+'.'+ext),part/(target+'_solidcraft.'+ext))
        path=part/(target+'_solidcraft_manifest.json');manifest=read(path)
        manifest.update(revision='odd_oobb_tabs',source_sha256=digest,verification_evidence=str(build),export_evidence=str(views))
        path.write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
    for path in (views/'parts').iterdir():shutil.copyfile(path,part/'native_parts'/path.name)
    index=PROJECT/'solidcraft/native_v7_odd_tabs.json';index.write_text(json.dumps(record,indent=2),encoding='utf-8')
    path=PROJECT/'solidcraft/native_v7.json';data=read(path)
    data.setdefault('revisions',[]).append(str(index.relative_to(PROJECT)))
    path.write_text(json.dumps(data,indent=2),encoding='utf-8')
    print('Published native odd OOBB tabs:',source)


if __name__=='__main__':main()
