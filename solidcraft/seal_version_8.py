"""Seal both accepted V8 presets without regenerating CAD or changing policy."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def main():
    release = ROOT/'releases/version_8'
    assert not release.exists(), 'Refusing to overwrite a V8 release'
    index = read(ROOT/'solidcraft/native_v8.json')
    assert read(ROOT/'solidcraft/active_design.json')['version'] == 'version_8'
    assert sha(ROOT/'gearbox_controls.solidcraft') == index['master_sha256']
    assert sha(ROOT/'gearbox_native/acceptance.py') == index['acceptance_sha256']
    assert read(ROOT/index['revision_validation'])['status'] == 'passed'
    assert read(ROOT/index['verification'])['status'] == 'passed'
    assert read(ROOT/'solidcraft/preservation.json')['status'] == 'passed'
    folders = []
    for variant in index['variants'].values():
        part = ROOT/'parts'/variant['part_id']
        assert sha(part/'gearbox_controls.solidcraft') == variant['master_sha256']
        folders.extend([part, ROOT/'parts_source'/variant['part_id']])
    folders.append(ROOT/'navigation_oobb/oobb/part/motor_gearbox/cycloidal/version_8')
    assert all(p.is_dir() and not (p/'SEALED.json').exists() for p in folders)
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    files = {ROOT/name for name in tracked if name and name.split('/')[0] not in
             {'parts', 'parts_source', 'navigation_oobb', 'releases'}}
    files.add(Path(__file__).resolve())
    for folder in folders:
        files.update(p for p in folder.rglob('*') if p.is_file())
    entries = {p.relative_to(ROOT).as_posix(): p for p in files}
    assert all(p.is_file() for p in entries.values()), 'Missing source file'
    release.mkdir()
    archive = release/'version_8.zip'
    hashes = {}
    print(f'Archiving {len(entries)} source, preset and evidence files', flush=True)
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as out:
        for name, path in sorted(entries.items()):
            hashes[name] = sha(path)
            out.write(path, name)
    with zipfile.ZipFile(archive) as inp:
        for name, digest in hashes.items():
            with inp.open(name) as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == digest, name
            assert sha(entries[name]) == digest, 'Source changed: '+name
    shutil.copyfile(ROOT/'gearbox_controls.solidcraft', release/'gearbox_controls.solidcraft')
    date = datetime.now(timezone.utc).date().isoformat()
    marker = dict(version='version_8', sealed=date, release='releases/version_8/release.json',
                  note='Frozen V8. Do not regenerate. Development continues in version_9.')
    for folder in folders:
        write(folder/'SEALED.json', marker)
    protected = {p.relative_to(ROOT).as_posix(): sha(p)
                 for folder in folders for p in folder.rglob('*') if p.is_file()}
    write(release/'release.json', dict(
        version='version_8', status='sealed', date=date,
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
        primary_part_id=index['part_id'], variants=index['variants'],
        archive=archive.name, archive_sha256=sha(archive), master_sha256=index['master_sha256'],
        files_sha256=hashes, sealed_catalogue_sha256=protected,
        evidence_sha256={'gearbox_controls.solidcraft': index['master_sha256']},
        acceptance_sha256=index['acceptance_sha256'], next_editable_version='version_9',
        verification=dict(revision=index['verification'], validation=index['revision_validation'],
                          evidence='solidcraft/evidence/v8_three_piece.zip',
                          project_tests_passed=21, shared_helper_tests_passed=2,
                          geometry_changed_for_release=False, physical_testing=False)))
    (release/'README.md').write_text(
        '# Version 8 — sealed\n\n'
        'Preserves both native 20:1 and compact 10:1 presets, the nine printed parts, '
        'three-piece casing, full-depth OOBB tabs, recessed socket-cap clamps and '
        'configurable guide screws/spacers.\n\n'
        'The archive contains the source, both complete parts folders, populate metadata, '
        'navigation pointers and accepted CAD evidence (solidcraft/evidence/v8_three_piece.zip). '
        'Every archived file was verified by SHA-256. release.json also protects the frozen '
        'catalogue files in place. The master here is a frozen inspection copy; edit the '
        'root gearbox_controls.solidcraft or V9 variant masters for new work.\n\n'
        'Six native configurations were checked; both presets have STEP/STL, native health, '
        'save/reopen, motion, sampling and hardware/access evidence. Existing acceptance '
        'policy is unchanged. Physical printing and load testing remain outstanding.\n',
        encoding='utf-8', newline='\n')
    print(f'Sealed V8: {len(hashes)} archived files, {len(protected)} protected files', flush=True)


if __name__ == '__main__':
    main()
