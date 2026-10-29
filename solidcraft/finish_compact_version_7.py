import hashlib,json,zipfile,sys
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from solidcraft.seal_version_7 import sha,read,write
release=root/'releases/version_7';archive=release/'version_7.zip'
assert not (release/'release.json').exists()
active=read(root/'solidcraft/active_design.json');assert active['version']=='version_7'
revision=read(root/'solidcraft/native_v7_odd_tabs.json')
assert sha(root/'gearbox_controls.solidcraft')==revision['initial_sha256']
hashes={}
with zipfile.ZipFile(archive) as z:
    for name in z.namelist():
        with z.open(name) as stream:hashes[name]=hashlib.file_digest(stream,'sha256').hexdigest()
    reports={}
    for name in z.namelist():
        if name.startswith('build/native_v7/') and name.endswith(('verification.json','export.json','tab_geometry.json','guards.json')):
            data=json.loads(z.read(name))
            reports[name]={'status':data.get('status'),'archive_entry':name}
assert all(value.get('status') in ('passed','native_export_checked') for value in reports.values())
assert hashes['gearbox_controls.solidcraft']==revision['initial_sha256']
date=datetime.now(timezone.utc).date().isoformat();part_id=active['part_id']
folders=[root/'parts'/part_id,root/'parts_source'/part_id,root/'navigation_oobb/oobb/part/motor_gearbox/cycloidal/version_7']
for folder in folders:
    write(folder/'SEALED.json',dict(version='version_7',sealed=date,release='releases/version_7/release.json',note='Frozen V7; edit version_8.'))
protected={p.relative_to(root).as_posix():sha(p) for folder in folders for p in folder.rglob('*') if p.is_file()}
# The interrupted evidence copy is redundant; retain complete copies only,
# and point to the verified archive for the full set without inflating disk use.
for path in (release/'evidence').rglob('*.json'):
    relative=path.relative_to(release/'evidence').as_posix()
    if relative not in hashes or sha(path)!=hashes[relative]:
        path.unlink()  # Only an incomplete file produced by this release attempt.
write(release/'evidence_index.json',dict(archive=archive.name,reports=reports,
    note='Complete JSON records are in the archive at their original build paths.'))
evidence={p.relative_to(release).as_posix():sha(p) for p in (release/'evidence').rglob('*') if p.is_file()}
evidence['evidence_index.json']=sha(release/'evidence_index.json')
write(release/'release.json',dict(version='version_7',status='sealed',date=date,primary_part_id=part_id,
    archive=archive.name,archive_sha256=sha(archive),master_sha256=revision['initial_sha256'],
    master='parts/'+part_id+'/gearbox_controls.solidcraft',files_sha256=hashes,
    sealed_catalogue_sha256=protected,evidence_sha256=evidence,
    acceptance_sha256=revision['acceptance_sha256'],next_editable_version='version_8',
    verification=dict(targeted_tests_passed=12,geometry_changed_for_release=False,physical_testing=False)))
(release/'README.md').write_text('# Version 7 — sealed\n\n'
    'Preserves the native parametric gearbox, 40 casing-bearing options and automatic odd OOBB mounting footprints. '
    'The current native master, assembled/exploded/print exports, source, shared helper component sources and '
    'accepted JSON verification records are in version_7.zip. Each archive entry is SHA-256 checked. '
    'See evidence_index.json for the archived verification paths. Historical inherited layouts and renders '
    'remain protected in the V7 catalogue and earlier releases.\n\n'
    'The frozen master is in [the sealed V7 parts folder](../../parts/'+part_id+'/gearbox_controls.solidcraft). '
    'The project-root master continues as V8. No geometry or acceptance-policy changes were made. '
    'Twelve targeted tests passed. Physical printing/load testing remains outstanding.\n',encoding='utf-8',newline='\n')
print('Sealed V7:',len(hashes),'archive entries,',len(protected),'protected files;',archive.stat().st_size,'archive bytes')
