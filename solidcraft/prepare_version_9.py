"""One-time V9 setup: copy sealed native assets exactly; advance editable routes."""
import json
from pathlib import Path
import shutil
from seal_version_8 import read, sha, write

ROOT = Path(__file__).resolve().parents[1]


def edit(path, pairs):
    text = path.read_text(encoding='utf-8')
    for old, new in pairs:
        assert old in text, (str(path), old)
        text = text.replace(old, new)
    path.write_text(text, encoding='utf-8', newline='\n')


def main():
    release = read(ROOT/'releases/version_8/release.json')
    assert release['status'] == 'sealed'
    assert read(ROOT/'solidcraft/active_design.json')['version'] == 'version_8'
    assert sha(ROOT/'gearbox_controls.solidcraft') == release['master_sha256']
    assert sha(ROOT/'releases/version_8/version_8.zip') == release['archive_sha256']
    for name, digest in release['sealed_catalogue_sha256'].items():
        assert sha(ROOT/name) == digest, name
    variants = {}
    inherited = {}
    for ratio, variant in release['variants'].items():
        old_id = variant['part_id']
        new_id = old_id.replace('version_8', 'version_9')
        variants[ratio] = dict(variant, part_id=new_id)
        for parent in ('parts', 'parts_source'):
            old = ROOT/parent/old_id
            new = ROOT/parent/new_id
            assert not new.exists(), 'Refusing to replace an existing V9 directory'
            shutil.copytree(old, new, ignore=shutil.ignore_patterns('SEALED.json'))
            for path in new.rglob('*'):
                if not path.is_file():
                    continue
                relative = path.relative_to(new)
                if path.suffix in {'.solidcraft', '.step', '.stl', '.png'}:
                    assert sha(path) == sha(old/relative)
                    inherited[path.relative_to(ROOT).as_posix()] = dict(
                        source=(old/relative).relative_to(ROOT).as_posix(), sha256=sha(path))
                elif path.name != 'native_export_verification.json' and path.suffix in {'.json', '.yaml', '.md'}:
                    text = path.read_text(encoding='utf-8').replace('version_8', 'version_9').replace('native_v8', 'native_v9').replace('V8', 'V9')
                    if path.suffix == '.yaml':
                        text = text.replace('Version 8', 'Version 9').replace('version 8', 'version 9').replace('VERSION 8', 'VERSION 9')
                    path.write_text(text, encoding='utf-8', newline='\n')
            if parent == 'parts':
                for path in new.glob('*_solidcraft_manifest.json'):
                    data = read(path)
                    data['inherited_from'] = 'releases/version_8/release.json'
                    write(path, data)
                path = new/'README.md'
                path.write_text(path.read_text(encoding='utf-8') +
                    '\nV9 starts with byte-identical native geometry and exports from sealed V8. '
                    'The inherited CAD evidence applies to this starting point.\n', encoding='utf-8', newline='\n')
        nav = ROOT/f'navigation_oobb/oobb/part/motor_gearbox/cycloidal/version_9/{ratio}_to_1_reduction'
        assert not nav.exists()
        write(nav/'active_part.json', dict(version='version_9', part_id=new_id, path='parts/'+new_id))
        (nav/'README.md').write_text(f'# Native V9 — {ratio}:1\n\n[Parts and editing instructions](../../../../../../../parts/{new_id}/README.md)\n', encoding='utf-8', newline='\n')
    main_id = variants['20']['part_id']
    write(ROOT/'solidcraft/version_9_baseline.json', dict(
        version='version_9', part_id=main_id, parent_release='releases/version_8/release.json',
        mechanical_changes=False, master_sha256=release['master_sha256'],
        acceptance_sha256=release['acceptance_sha256'], variants=variants, inherited_files=inherited))
    shutil.copyfile(ROOT/'solidcraft/native_v8_profile.json', ROOT/'solidcraft/native_v9_profile.json')
    write(ROOT/'solidcraft/native_v9.json', dict(
        version='version_9', state='native-only', master='gearbox_controls.solidcraft',
        initial_sha256=release['master_sha256'], master_sha256=release['master_sha256'],
        part_id=main_id, profile='solidcraft/native_v9_profile.json', baseline='solidcraft/version_9_baseline.json',
        parent_release='releases/version_8/release.json', variants=variants, component_count=9,
        acceptance_sha256=release['acceptance_sha256'],
        inherited_verification='solidcraft/native_v8_three_piece_verification.json',
        setup_verification='solidcraft/version_9_validation.json'))
    write(ROOT/'solidcraft/active_design.json', dict(
        version='version_9', part_id=main_id, state='native-only', baseline='solidcraft/version_9_baseline.json',
        master='gearbox_controls.solidcraft', verification='solidcraft/native_v9.json'))
    edit(ROOT/'gearbox_native/project.py', [('VERSION = "version_8"', 'VERSION = "version_9"')])
    edit(ROOT/'working_oomp_populate.py', [('version_8', 'version_9'), ('V8', 'V9'),
        ('Versions 1–7', 'Versions 1–8'), ('Version 8 starts', 'Version 9 starts'),
        ('"version_6", "version_7")', '"version_6", "version_7", "version_8")')])
    edit(ROOT/'working_solidcraft.py', [('use version_8', 'use version_9'),
        ('kwargs.get("style", "version_8") not in ("version_7", "version_8")',
         'kwargs.get("style", "version_9") not in ("version_7", "version_8", "version_9")'),
        ('Only V7 reference and V8 recipes', 'Only V7/V8 reference and V9 recipes')])
    edit(ROOT/'working_scad.py', [('use version_8', 'use version_9')])
    controls = read(ROOT/'gearbox_native/control_values.json')
    controls['version'] = 'version_9'
    write(ROOT/'gearbox_native/control_values.json', controls)
    edit(ROOT/'solidcraft/verify_preservation.py', [('V1–V7', 'V1–V8'),
        ('(1, 2, 3, 4, 5, 6, 7)', '(1, 2, 3, 4, 5, 6, 7, 8)')])
    for name in ('README.md', 'NATIVE_V8.md'):
        text = (ROOT/name).read_text(encoding='utf-8').replace('version_8', 'version_9').replace('native_v8', 'native_v9').replace('V8', 'V9').replace('VERSION_8', 'VERSION_9').replace('V1–V7', 'V1–V8')
        if name == 'README.md':
            text = text.replace('V7 sealed release', 'V8 sealed release').replace('releases/version_7/README.md', 'releases/version_8/README.md')
            text = text.replace('V7 is sealed. V9 now has', 'V8 is sealed. V9 starts with identical geometry and parameters in both presets.\n\nThe design has')
        else:
            text += '\nV9 begins as an unchanged copy of both sealed V8 presets. See releases/version_8/release.json for the inherited acceptance evidence.\n'
        (ROOT/('NATIVE_V9.md' if name == 'NATIVE_V8.md' else name)).write_text(text, encoding='utf-8', newline='\n')
    for variant in variants.values():
        shutil.copyfile(ROOT/'NATIVE_V9.md', ROOT/'parts'/variant['part_id']/'EDITING_PARAMETERS.md')
    (ROOT/'VERSION_9_DEVELOPMENT.md').write_text(
        '# Version 9 — editable native baseline\n\n'
        'Version 8 is sealed. Both 20:1 and compact 10:1 presets start with byte-identical '
        'native models, assembled/exploded/print views and nine individual manufacturing exports. '
        'No geometry or acceptance thresholds changed for this transition.\n\n'
        'Edit the root gearbox_controls.solidcraft in SolidCraft Parameters for the main 20:1 '
        'design, or the master in the V9 10:1 parts folder for that preset. The view files are '
        'independent snapshots; re-export after editing. The populate route targets V9 and '
        'changes only exposed native parameters.\n\n'
        'See [parameter instructions](NATIVE_V9.md), [baseline hashes](solidcraft/version_9_baseline.json), '
        '[V8 release](releases/version_8/README.md), and [setup checks](solidcraft/version_9_validation.json). '
        'The original native authoring implementation remains gearbox_native/native_v8.py; '
        'the saved V9 documents contain the complete editable feature graph. Previous CAD '
        'verification is inherited by byte identity, not rerun or claimed as new geometry testing. '
        'Physical printing and load testing remain outstanding. Exports target outputs/native_v9.\n',
        encoding='utf-8', newline='\n')
    assert sha(ROOT/'gearbox_controls.solidcraft') == release['master_sha256']
    print(f'Prepared V9: {len(inherited)} byte-identical CAD/export files across both presets')


if __name__ == '__main__':
    main()
