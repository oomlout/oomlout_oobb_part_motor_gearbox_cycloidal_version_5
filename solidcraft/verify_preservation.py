"""Verify sealed V1–V8 archives, catalogue artifacts and native evidence."""
import hashlib
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    report = dict(status='passed', releases={}, violations=[])
    for number in (1, 2, 3, 4, 5, 6, 7, 8):
        folder = PROJECT/'releases'/f'version_{number}'
        manifest = json.loads((folder/'release.json').read_text())
        expected = {folder/manifest['archive']: manifest['archive_sha256']}
        protected = manifest.get('sealed_catalogue_sha256') or {
            k: v for k, v in manifest['files_sha256'].items()
            if k.startswith(('parts/', 'parts_source/', 'navigation_oobb/'))
        }
        expected.update({PROJECT/k: v for k, v in protected.items()})
        expected.update({folder/k: v for k, v in manifest.get('evidence_sha256', {}).items()})
        for path, digest in expected.items():
            if not path.is_file() or sha(path) != digest:
                report['violations'].append(str(path))
        report['releases'][f'version_{number}'] = dict(checked_files=len(expected))
    if report['violations']:
        report['status'] = 'failed'
    (PROJECT/'solidcraft/preservation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    if report['violations']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
