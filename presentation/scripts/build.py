"""Rebuild the V2 README, CAD illustrations, BOM and manual from any directory.

python presentation/scripts/build.py --render  # production meshes -> Blender -> publications
python presentation/scripts/build.py           # reuse matching renders; rebuild layout and audit
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / 'presentation'
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(P / 'scripts/lib'))


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n', encoding='utf8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def assert_sources(data):
    src = data['source']
    assert sha(ROOT / src['master']) == src['master_sha256'], 'Master changed: review the manifest and assembly before rebuilding'
    part = ROOT / src['part_directory']
    exported = read(part / 'native_export_verification.json')
    assert exported['source_sha256'] == src['master_sha256']
    notes=read(P/'source-notes.json')
    for filename in ('assembled_health.json','exploded_health.json'):
        snapshot=P/'source/cad'/filename
        assert read(snapshot)['source_master_sha256']==src['master_sha256']
        assert sha(snapshot)==notes['source_hashes'][snapshot.relative_to(ROOT).as_posix()]
    for name, value in data['geometry'].items():
        if name in exported['parameters']:
            assert abs(value-exported['parameters'][name]) < 1e-6, 'Manifest dimension changed: ' + name
    for filename in ['layered_assembly_verification.json', 'assembly_sequence_verification.json']:
        assert read(part / filename)['master_sha256'] == src['master_sha256'], 'Stale assembly evidence: ' + filename
    return part


def render(data):
    from gearbox_native import double_bearing_render as legacy
    legacy.CACHE = P / 'raw'
    legacy.stage(P / 'source/cad')
    write(P / 'raw/provenance.json', {
        'master_sha256': data['source']['master_sha256'],
        'exploded_stl_sha256': sha(ROOT / data['source']['part_directory'] / 'exploded.stl'),
        'studio_sha256': sha(P / 'scripts/studio.py'),
    })
    with (P / 'qa/blender.log').open('w', encoding='utf8') as log:
        subprocess.run(['blender', '-b', '-t', '8', '--python-exit-code', '1', '-P',
                        str(P / 'scripts/studio.py'), '--', str(P / 'raw')],
                       stdout=log, stderr=subprocess.STDOUT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args()
    data = read(P / 'project.json')
    part = assert_sources(data)
    if args.render:
        render(data)
    info = read(P / 'raw/render-info.json')
    assert info['source_sha256'] == data['source']['master_sha256'], 'Render source is stale; use --render'
    assert info['studio_sha256'] == sha(P / 'scripts/studio.py'), 'Renderer changed; use --render'
    from sheets import publish
    publish(data)
    from manual import build_manual
    build_manual(data)
    # Migrate once, preserving the complete previous README as technical source.
    readme = ROOT / 'README.md'
    if '<!-- oobb-presentation:start -->' not in readme.read_text(encoding='utf8'):
        assert readme.read_bytes() == (P / 'source/README-before-migration.md').read_bytes(), 'Unreviewed README changes during migration'
        readme.write_text('', encoding='utf8')
    from build_readme import build
    build(ROOT, P / 'templates/README.template.md')
    root_text=readme.read_text(encoding='utf8')
    catalogue=part/'README.md'
    original=P/'source/catalogue-README-before-migration.md'
    if not original.exists():
        shutil.copyfile(catalogue,original)
    nav=ROOT/'navigation_oobb/oobb/part/motor_gearbox/cycloidal/simple_double_bearing_version_2/20_to_1_reduction'
    for destination in (catalogue,nav/'README.md'):
        def rebase(match):
            target=match.group(1)
            if re.match(r'^[a-z]+:',target) or target.startswith('#'):
                return match.group(0)
            return ']('+Path(os.path.relpath(ROOT/target,destination.parent)).as_posix()+')'
        destination.write_text(re.sub(r'\]\(([^)]+)\)',rebase,root_text),encoding='utf8')
    assembly=['# Gearbox assembly','', 'AI-generated images and instructions. Errors possible.','',
              '[Assembly PDF](../../presentation/assembly-guide.pdf) · [Parts and downloads](README.md)','']
    for index,step in enumerate(data['readme']['assembly_steps'],1):
        assembly += [f"## {index}. {step['title']}",'',step['body'],'',
                     f"![{step['alt']}](../../presentation/images/{step['image']})",'']
    (part/'ASSEMBLY.md').write_text('\n'.join(assembly),encoding='utf8')
    from build_readme import hardware_table
    (part/'HARDWARE.md').write_text('# Gearbox hardware\n\nAI-generated images and instructions. Errors possible.\n\n'+
        data['readme']['parts_scope']+'\n\n'+hardware_table(data)+'\n\n'+data['readme']['hardware_notes']+'\n',encoding='utf8')
    # Catalogue links use the same published images and quantities as the root README.
    for source, target in [('in-use.png', 'render_assembled_square.png'), ('rounded.png', 'render_assembled_rounded.png'),
                           ('exploded.png', 'render_exploded.png'), ('assembly-overview.png', 'render_installation.png'),
                           ('exploded.png', 'exploded_labeled.png'), ('carrier-nuts.png', 'carrier_split_faces.png'),
                           ('in-use.png', 'true.png'), ('exploded.png', 'exploded.png')]:
        shutil.copyfile(P / 'images' / source, part / target)
    from audit import audit
    audit(data)
    from validate_presentation import validate
    result = validate(ROOT)
    print(json.dumps(result, indent=2))
    if result['errors']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
