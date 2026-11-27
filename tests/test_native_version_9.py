"""Version handoff checks: exact geometry inheritance and editable route isolation."""
import hashlib
import json
import zipfile
import pytest
from gearbox_native.project import PROJECT, VERSION, active_part, require_editable, require_legacy_authoring


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def test_v9_starting_provenance_and_current_revision_are_preserved():
    baseline = read(PROJECT/'solidcraft/version_9_baseline.json')
    assert VERSION == 'version_9' and not baseline['mechanical_changes']
    assert set(baseline['variants']) == {'20', '10'}
    index = read(PROJECT/'solidcraft/native_v9.json')
    assert index['initial_sha256'] == baseline['master_sha256']
    assert sha(PROJECT/'gearbox_controls.solidcraft') == index['master_sha256']
    assert sha(PROJECT/'gearbox_native/acceptance.py') == baseline['acceptance_sha256']
    assert len(baseline['inherited_files']) == 74
    for name, record in baseline['inherited_files'].items():
        assert record['sha256'] == sha(PROJECT/record['source'])
    for variant in index['variants'].values():
        part = PROJECT/'parts'/variant['part_id']
        require_editable(part)
        assert not (part/'SEALED.json').exists()
        assert len(list((part/'native_parts').glob('*.stl'))) == variant.get('component_count',index['component_count'])


def test_v9_populate_metadata_and_export_route_are_consistent():
    import working_oomp_populate as populate
    from gearbox_native import native_catalogue
    index = read(PROJECT/'solidcraft/native_v9.json')
    assert (PROJECT/'parts'/index['part_id']).is_dir()
    assert native_catalogue.NATIVE_NAME == 'native_v9'
    assert native_catalogue.VERSION_LABEL == 'V9'
    for option in (o for o in populate.get_options() if o['style']=='version_9'):
        assert option['style'] == 'version_9'
        key = str(option['reduction']) + ('_bearing' if option.get('input_variant') == 'bearing_input' else '')
        variant = index['variants'][key]
        assert populate.build_oomp_id(option) == variant['part_id']
        assert option['native_parameters'] == variant['native_parameters']
        metadata = (PROJECT/'parts'/variant['part_id']/'working.yaml').read_text(encoding='utf-8')
        assert 'Version 9' in metadata and 'Version 8' not in metadata
        assert 'version_8' not in metadata
    for version in range(1, 9):
        with pytest.raises(ValueError, match='sealed'):
            populate.get_options([{'style': f'version_{version}'}])
    with pytest.raises(ValueError, match='native-only'):
        require_legacy_authoring()


def test_native_5x5_revision_has_real_edit_and_fit_evidence():
    index = read(PROJECT/'solidcraft/native_v9.json')
    proof = read(PROJECT/index['previous_verification'])
    assert proof['status'] == 'passed'
    for case in proof['cases'].values():
        assert case['status'] == 'passed'
        assert case['sampling']['max_sampled_chord_error_mm'] <= .005
        assert all(part['valid'] and part['mesh']['watertight'] for part in case['parts'].values())
    for name in ('baseline', 'compact_10'):
        row = proof['cases'][name]
        assert len(row['parts']) == 9 and row['reopens'] == 2
        assert row['hardware']['status'] == 'passed'
        assert row['hardware']['maximum_overlap_mm3'] < .03
        assert row['bearing_fits']['status'] == 'passed' and row['bearing_fits']['check_count'] == 45
        assert row['bearing_fits']['maximum_overlap_mm3'] < .03
        assert row['maximum_intersection_mm3'] < .03
        assert row['maximum_motion_overlap_mm3'] < .03
    values = proof['cases']['baseline']['parameters']
    assert values['reduction'] == 35 and values['contact_radius'] == 1.5
    assert values['eccentricity'] == .7 and values['casing_bearing'] == 6808
    assert values['posts_enabled'] == 1 and values['guide_count'] == 6
    assert values['wiggle_key_clearance'] == .1
    assert values['wiggle_journal_clearance'] == .075
    assert proof['cases']['eccentricity_edit']['reopens'] == 2
    assert proof['cases']['shaft_fit_edit']['reopens'] == 2


def test_drive_interfaces_and_prints_are_verified_in_every_preset():
    index = read(PROJECT/'solidcraft/native_v9.json')
    proof = read(PROJECT/index['verification'])
    for ratio, variant in index['variants'].items():
        part = PROJECT/'parts'/variant['part_id']
        row = proof['variants'][ratio]
        assert row['source_sha256'] == sha(part/'gearbox_controls.solidcraft')
        assert row['status'] == 'passed'
        assert row['print_parts'] == row['native_body_count'] == (14 if row['bearing_input'] else 11)
        assert all(p['valid'] and p['mesh']['watertight'] for p in row['native_parts'].values())
        assert all(check['overlap_mm3'] < .03 for check in row['checks'])
        names = {c['check'] for c in row['checks']}
        assert {'front_shaft_6702',
                'sleeve_side_nut_loading', 'sleeve_hex_key_access', 'sleeve_M3_socket_head'} <= names
        if row['bearing_input']:
            assert {'base_shaft_6702','upward_M3x35_join_shank','upward_M3_socket_cap_head','upper_M3_join_nut','upper_M3_side_loading'} <= names
            assert {'bearing_holder','motor_mount'} <= set(row['native_parts'])
            assert not {'motor_spacer','bearing_baseplate'} & set(row['native_parts'])
        else:
            assert row['reprint_sha256'] == sha(part/'shaft_reprint/3dpr.stl')
            assert {'upward_M2_5_join_head','upper_M2_5_nut_loading','M3_radial_head', 'M2.5_socket_head_insertion', 'full_height_10mm_spacer_gap'} <= names


def test_native_drive_edit_and_clearance_comparison_have_geometric_evidence():
    proof = read(PROJECT/read(PROJECT/'solidcraft/native_v9.json')['verification'])
    edit = proof['native_drive_edit']
    assert edit['status'] == 'passed' and edit['reopens'] == 2
    assert abs(edit['height_change_mm']-4) < .001 and edit['mesh']['watertight']
    trials = proof['clearance_trials']
    for row in trials.values():
        assert row['status'] == 'passed' and row['motion_samples'] == 180
        assert row['minimum_contact_gap_mm'] > row['profile_clearance']-.011
        assert row['sampling_error_mm'] <= .005 and row['mesh']['watertight']
        assert (row['pitch'], row['guide_pitch'], row['post_pitch']) == pytest.approx((27.9, 15, 16.15))
    assert trials['original']['profile_only_deadband_deg'] > trials['balanced']['profile_only_deadband_deg'] > trials['close']['profile_only_deadband_deg'] > 0
    assert not proof['physical_fit_tested']


def test_detachable_holder_reuses_motor_plate_and_has_accessible_hardware():
    proof=read(PROJECT/read(PROJECT/'solidcraft/native_v9.json')['verification'])
    shared=proof['shared_stepper_parts']
    assert set(shared)=={'motor_mount','pin_front','rotor_a','rotor_b',
                         'output_casing_lower','output_casing_lobes','output_casing_upper'}
    assert all(r['volume_delta_mm3']<.001 and r['maximum_bound_change_mm']<.001 for r in shared.values())
    row=proof['variants']['35_bearing']
    names={c['check'] for c in row['checks']}
    assert {'holder_M3x10_shank','holder_countersunk_head','holder_nut_bottom_loading',
            'holder_open_bearing_loading','holder_axial_tool_access'} <= names
    edit=proof['holder_edit']
    assert edit['status']=='passed' and edit['reopens']==2 and edit['mesh']['watertight']
    assert abs(edit['height_change_mm']-1)<.001


def test_bearing_stack_print_orientation_and_native_edit():
    from gearbox_native.split_stack import HALVES,STACK
    index=read(PROJECT/'solidcraft/native_v9.json')
    summary=read(PROJECT/index['revision_validation'])
    proof=read(PROJECT/index['verification'])
    part=PROJECT/'parts'/index['variants']['35_bearing']['part_id']
    assert set(summary['layer_checks'])==set(STACK)
    assert all(r['unsupported_islands']==0 and r['layer_height_mm']==.2 for r in summary['layer_checks'].values())
    assert all(summary['layer_checks'][n]['maximum_lateral_reach_mm']<.5 for n in (*HALVES,'drive_sleeve'))
    assert summary['print_plates']['shaft_reprint/3dpr.stl']['sha256']==sha(part/'shaft_reprint/3dpr.stl')
    assert summary['print_plates']['bearing_conversion/3dpr.stl']['parts']==7
    assert proof['split_sleeve_edit']['reopens']==2 and proof['split_sleeve_edit']['height_change_mm']==pytest.approx(4)


def test_presets_differ_only_in_exposed_native_parameters():
    def document(path):
        with zipfile.ZipFile(path) as archive:
            return json.loads(archive.read('document.json'))
    for variant in read(PROJECT/'solidcraft/native_v9.json')['variants'].values():
        a = document(PROJECT/variant['source_master'])
        pa = {p['name']: p['expr'] for p in a['params']}
        b = document(PROJECT/'parts'/variant['part_id']/'gearbox_controls.solidcraft')
        pb = {p['name']: p['expr'] for p in b['params']}
        changed = {k for k in pa if pa[k] != pb[k]}
        assert changed <= set(a['favorites'])
        assert changed <= set(variant['native_parameters'])
        assert all(pb[k] == v for k, v in variant['native_parameters'].items())
        assert a['components'] == b['components']
        clean = lambda d: [{k:v for k,v in f.items() if k != 'sketch'} for f in d['features']]
        assert clean(a) == clean(b)


def test_full_width_hole_map_has_only_edge_centres_removed():
    from gearbox_native.native_v9 import mounting_holes, CLAMPS
    m6, m3 = mounting_holes()
    assert len(m6) == 12 and len(m3) == 16 and len(CLAMPS) == 4
    assert not set(m6) & {(30,0), (-30,0), (0,30), (0,-30)}
    assert {(x,y) for x in (-30,30) for y in (-30,-15,15,30)} <= set(m6)
    assert set(CLAMPS) == {(x,y) for x in (-22.5,22.5) for y in (-22.5,22.5)}


def test_v8_release_is_complete_and_protected():
    release = read(PROJECT/'releases/version_8/release.json')
    assert release['status'] == 'sealed' and release['next_editable_version'] == 'version_9'
    assert sha(PROJECT/'releases/version_8'/release['archive']) == release['archive_sha256']
    with zipfile.ZipFile(PROJECT/'releases/version_8'/release['archive']) as archive:
        for name, digest in release['files_sha256'].items():
            with archive.open(name) as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == digest
    for variant in release['variants'].values():
        with pytest.raises(ValueError, match='Sealed'):
            require_editable(PROJECT/'parts'/variant['part_id'])
    for name, digest in release['sealed_catalogue_sha256'].items():
        assert sha(PROJECT/name) == digest
