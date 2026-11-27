"""Native odd OOBB footprints and measured M6 hardware clearances."""
import json
import zipfile
from gearbox_native.project import PROJECT,active_part


def test_native_views_share_the_odd_plate_formula():
    # The automatic odd-plate rule belongs to sealed V8. V9 deliberately fixes 5x5.
    part=PROJECT/'parts/oobb_part_motor_gearbox_cycloidal_version_8_20_to_1_reduction'
    for path in [part/(name+'.solidcraft') for name in ('gearbox_controls','true','exploded','3dpr')]:
        with zipfile.ZipFile(path) as archive:document=json.loads(archive.read('document.json'))
        params={p['name']:p['expr'] for p in document['params']}
        assert 'tab_plate_size' in params['tab_radius']
        assert 'ceil' in params['tab_plate_size']
        assert params['tab_m6_clearance']=='0.5 mm'
        assert 'casing_radius' in params['tab_required_radius']


def test_native_rule_proves_minimality_at_plate_boundaries():
    record=json.loads((PROJECT/'solidcraft/native_v7_odd_tabs.json').read_text(encoding='utf-8'))
    proof=json.loads((PROJECT/record['rule_verification']).read_text(encoding='utf-8'))
    assert proof['status']=='passed' and len(proof['cases'])==20
    assert all(row['plate_size']%2==1 and row['outer_bolt_gap']>=.5-1e-8 for row in proof['cases'])
    assert {row['plate_size'] for row in proof['cases']} >= {3,5,7,9,11}
    assert len(record['unchanged_default_part_stl_sha256'])==8


def test_native_outer_bores_and_hardware_are_clear_on_both_halves():
    record=json.loads((PROJECT/'solidcraft/native_v7_odd_tabs.json').read_text(encoding='utf-8'))
    for key,size,radius in [('hardware_verification',9,60),('default_hardware_verification',7,45)]:
        proof=json.loads((PROJECT/record[key]).read_text(encoding='utf-8'))
        assert proof['status']=='passed' and proof['plate_size']==size
        assert proof['tab_radius']==radius
        assert proof['bore_position_tolerance_mm']==.05 and proof['overlap_tolerance_mm3']==.03
        for half in proof['bodies'].values():
            assert half['outer_holes']==8 and len(half['hardware_checks'])==24
            assert half['max_bore_position_error_mm']<.05
            assert all(check['overlap_mm3']<.03 for check in half['hardware_checks'])
