"""Published casing-bearing revision retains native edits and their evidence."""
import hashlib
import json
import zipfile
from gearbox_native.project import PROJECT, active_part


def test_bearing_selector_matches_the_shared_catalogue():
    from gearbox_native.parts import bearing_spec
    record=json.loads((PROJECT/'solidcraft/casing_bearings.json').read_text(encoding='utf-8'))
    assert record['default']==6810
    assert set(record['new_entries'])=={'6708','6709','6710','6711','6712'}
    for code,dimensions in record['options'].items():
        assert bearing_spec(code)==dimensions


def test_all_published_native_views_include_the_bearing_control():
    for path in [PROJECT/'gearbox_controls.solidcraft',*(active_part()/(name+'.solidcraft')
                  for name in ('gearbox_controls','true','3dpr','exploded'))]:
        with zipfile.ZipFile(path) as archive:
            document=json.loads(archive.read('document.json'))
        assert {'casing_bearing','casing_fit_checks'}<=set(document['favorites'])
        params={p['name']:p['expr'] for p in document['params']}
        assert params['casing_bearing']=='6810'
        assert params['casing_fit_checks']=='0'
        assert 'casing_width' in params['front_depth']
        assert 'casing_od' in params['casing_radius']
        assert len(document['components'])==9
        assert all(f['type'] in {'sketch','extrude','revolve','combine','move'} for f in document['features'])


def test_native_bearing_revision_has_real_edit_and_reopen_evidence():
    index=json.loads((PROJECT/'solidcraft/native_v7_casing_bearings.json').read_text(encoding='utf-8'))
    proof=json.loads((PROJECT/index['edit_verification']).read_text(encoding='utf-8'))
    assert proof['status']=='passed' and not proof['mechanical_fit_checked']
    assert set(proof['cases'])=={'6710','6811'}
    for row in proof['cases'].values():
        assert row['status']=='passed' and row['second_reopen_body_count']==8
        assert len(row['parts'])==8
        assert all(p['step']['valid'] for p in row['parts'].values())
    selector=json.loads((PROJECT/index['selector_verification']).read_text(encoding='utf-8'))
    assert selector['status']=='passed' and len(selector['options'])==40
    assert hashlib.sha256((PROJECT/'gearbox_native/acceptance.py').read_bytes()).hexdigest()==index['acceptance_sha256']
