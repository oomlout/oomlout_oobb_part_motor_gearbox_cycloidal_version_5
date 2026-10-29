"""One-time V7 release snapshot. Refuses to overwrite a release or changed master."""
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
    release = ROOT/'releases/version_7'
    assert not release.exists() or not any(release.iterdir()), 'Inspect the existing V7 release before continuing'
    active = read(ROOT/'solidcraft/active_design.json')
    assert active['version'] == 'version_7'
    part_id = active['part_id']
    revision = read(ROOT/'solidcraft/native_v7_odd_tabs.json')
    master = ROOT/'gearbox_controls.solidcraft'
    assert sha(master) == revision['initial_sha256'], 'Master has changed since verification'
    assert sha(ROOT/'parts'/part_id/master.name) == sha(master)
    assert sha(ROOT/'gearbox_native/acceptance.py') == revision['acceptance_sha256']
    assert read(ROOT/'solidcraft/preservation.json')['status'] == 'passed'
    assert '12 passed' in (ROOT/'outputs/v7_preseal_tests.log').read_text(encoding='utf-8')
    builds = [ROOT/'build/native_v7'/name for name in (
        'rotor_10', 'assembly_03', 'presentation_01', 'casing_bearings_02',
        'casing_bearings_views_01', 'casing_selector', 'odd_oobb_tab_rule',
        'odd_oobb_tabs_01', 'odd_oobb_tabs_views_01')]
    for relative, status in (
        ('assembly_03/assembly_verification.json', 'passed'),
        ('casing_bearings_02/casing_verification.json', 'passed'),
        ('odd_oobb_tabs_01/casing_verification.json', 'passed'),
        ('odd_oobb_tabs_01/tab_geometry.json', 'passed'),
        ('odd_oobb_tabs_01/default_tab_geometry.json', 'passed'),
        ('odd_oobb_tabs_views_01/export.json', 'native_export_checked')):
        assert read(ROOT/'build/native_v7'/relative)['status'] == status
    folders = [ROOT/'parts'/part_id, ROOT/'parts_source'/part_id,
               ROOT/'navigation_oobb/oobb/part/motor_gearbox/cycloidal/version_7']
    assert all(p.is_dir() and not (p/'SEALED.json').exists() for p in folders)
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    files = {ROOT/name for name in tracked if name and
             name.split('/')[0] not in {'parts', 'parts_source', 'navigation_oobb', 'releases'}}
    files.add(Path(__file__).resolve())
    # Current native assets plus evidence; older linked layouts and presentation
    # assets remain protected in-place and in the earlier release archives.
    for folder in folders[:2]:
        files.update(p for p in folder.iterdir() if p.is_file())
    files.update(p for p in (folders[0]/'native_parts').rglob('*') if p.is_file())
    for folder in builds:
        files.update(p for p in folder.rglob('*') if p.is_file() and p.suffix in {'.json', '.txt'})
    for pattern in ('v7*tests.log', 'v7_preseal*', 'odd_oobb_tabs_tests.log', 'casing*tests.log'):
        files.update((ROOT/'outputs').glob(pattern))
    entries = {p.relative_to(ROOT).as_posix(): p for p in files}
    helper = Path(read(ROOT/'solidcraft/config.json')['helper_root'])
    # Preserve the shared component implementation and bearing catalogue too.
    # Native models contain their own formulas; these sources are restoration aids.
    for folder in ('components', 'catalog', 'oobb_solidcraft', 'notes_for_ai'):
        for path in (helper/folder).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix in {'.py', '.yaml', '.json', '.md'}:
                entries['dependencies/software_cad_mcp_helper/'+path.relative_to(helper).as_posix()] = path
    for name in ('pyproject.toml', 'requirements.txt'):
        path = helper/name
        if path.is_file():
            entries['dependencies/software_cad_mcp_helper/'+name] = path
    release.mkdir(exist_ok=True)
    archive = release/'version_7.zip'
    print(f'Archiving {len(entries)} files ({sum(p.stat().st_size for p in entries.values())/1e9:.2f} GB)', flush=True)
    hashes = {}
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as out:
        for name, path in sorted(entries.items()):
            hashes[name] = sha(path)
            out.write(path, name)
    print('Verifying every archived entry against its source', flush=True)
    with zipfile.ZipFile(archive) as inp:
        for name, digest in hashes.items():
            with inp.open(name) as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == digest, name
            assert sha(entries[name]) == digest, 'Source changed: '+name
    evidence = {}
    for folder in builds:
        for path in folder.rglob('*'):
            if path.is_file() and path.suffix in {'.json', '.txt'}:
                target = release/'evidence'/path.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
                evidence[target.relative_to(release).as_posix()] = sha(target)
    for path in (master, ROOT/'outputs/v7_preseal_tests.log', ROOT/'outputs/v7_preseal_preservation.log'):
        target = release/path.name
        shutil.copyfile(path, target)
        evidence[target.name] = sha(target)
    date = datetime.now(timezone.utc).date().isoformat()
    marker = dict(version='version_7', sealed=date, release='releases/version_7/release.json',
                  note='Frozen native V7. Do not regenerate. Development continues in version_8.')
    for folder in folders:
        write(folder/'SEALED.json', marker)
    protected = {p.relative_to(ROOT).as_posix(): sha(p) for folder in folders for p in folder.rglob('*') if p.is_file()}
    write(release/'release.json', dict(
        version='version_7', status='sealed', date=date, primary_part_id=part_id,
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
        description='Native parametric gearbox with 40 casing-bearing options and automatic odd OOBB footprints.',
        archive=archive.name, archive_sha256=sha(archive), master_sha256=sha(master),
        files_sha256=hashes, sealed_catalogue_sha256=protected, evidence_sha256=evidence,
        acceptance_sha256=revision['acceptance_sha256'], next_editable_version='version_8',
        verification=dict(targeted_tests_passed=12, native_revision='solidcraft/native_v7_odd_tabs.json',
                          geometry_changed_for_release=False, physical_testing=False)))
    (release/'README.md').write_text(
        '# Version 7 — sealed\n\n'
        'Preserves the native Parameters-menu gearbox, configurable 6700/6800 casing bearings, '
        'and automatic smallest odd OOBB mounting footprint with outer M6 hardware clearance.\n\n'
        'Open `gearbox_controls.solidcraft` here to inspect the frozen master. Continue editing '
        'the root master as V8. The release archive contains the source, V7 catalogue, current '
        'exports, accepted native JSON evidence and shared helper component sources. Historical '
        'linked layouts and presentation assets stay protected in-place and in earlier release '
        'archives; they are not duplicated in this archive. Every '
        'archive entry was checked against its SHA-256; release.json also protects live V7 '
        'catalogue files and the exposed evidence. Original build paths remain as historical '
        'provenance; corresponding records are under evidence/build/native_v7/.\n\n'
        'The existing native health, real parameter edit, STEP/STL, save/reopen, fit and sampling '
        'records are retained. Twelve targeted tests passed before sealing. No geometry or '
        'acceptance-policy change was made. Fit checks for arbitrary bearing selections remain '
        'optional; physical printing and load testing remain outstanding.\n',
        encoding='utf-8', newline='\n')
    print(f'Sealed V7: {len(hashes)} archived, {len(protected)} protected, {len(evidence)} evidence files', flush=True)


if __name__ == '__main__':
    main()
