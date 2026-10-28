"""V7 owns its native dependency graph and preserves its V6 starting evidence."""
import hashlib,json,zipfile
from pathlib import Path
import pytest,yaml
from gearbox_native.project import PROJECT,VERSION,active_part
from gearbox_native.export import geometry_digest
from oobb_solidcraft.compiler import compile_thing
from oobb_solidcraft.construction import build_thing


def test_inherited_native_parts_are_byte_identical_and_immutable_provenance_exists():
    baseline=json.loads((PROJECT/'solidcraft/version_7_baseline.json').read_text())
    assert VERSION=='version_7' and len(baseline['inherited_documents'])==16
    assert not (active_part()/'SEALED.json').exists()
    for key,expected in baseline['inherited_documents'].items():
        mode,name=key.split('/');path=active_part()/'solidcraft'/mode/(name+'.solidcraft')
        record=json.loads(path.with_name(name+'_manifest.json').read_text())
        if record.get('inherited_from',{}).get('version')!='version_6':continue
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
        assert record['part_id']==active_part().name
        assert Path(record['verification_evidence']).is_dir()
        assert Path(record['verification_evidence']).is_relative_to(PROJECT/'releases')


def test_inherited_geometry_matches_frozen_parent():
    baseline=json.loads((PROJECT/'solidcraft/version_7_baseline.json').read_text())
    definition=yaml.safe_load((active_part()/'working.yaml').read_text())
    for mode in ('true','3dpr'):
        thing=build_thing(definition,builder_path=PROJECT/'working_solidcraft.py',mode=mode)
        for name,piece in thing['gearbox']['pieces'].items():
            record=json.loads((active_part()/'solidcraft'/mode/(name+'_manifest.json')).read_text())
            if record.get('inherited_from',{}).get('version')!='version_6':continue
            local=dict(id=definition['id']+'__'+name,mode=mode,**piece['thing'],sequential_unions=True,compound_cuts=True,dimensions=thing['dimensions'])
            assert geometry_digest(compile_thing(local))==baseline['canonical_geometry'][mode+'/'+name]


@pytest.mark.parametrize('mode',['true','3dpr'])
def test_layout_is_a_self_contained_native_graph(mode):
    with zipfile.ZipFile(active_part()/(mode+'.solidcraft')) as archive:
        document=json.loads(archive.read('document.json'))
    record=json.loads((active_part()/(mode+'_solidcraft_manifest.json')).read_text())
    assert record['native_only'] and not record['external_piece_links']
    assert len(document['components'])==8
    assert all(f['type'] in {'sketch','extrude','revolve','combine','move'} for f in document['features'])
    expressions={p['name']:p['expr'] for p in document['params']}
    assert expressions['ring_count']=='reduction'
    counts=[p['count_expression'] for f in document['features'] if f['type']=='sketch'
            for p in f['sketch'].get('patterns',[])]
    assert counts.count('ring_count - 1')==2
    assert counts.count('ring_count')==4
    assert {'reduction','eccentricity','disc_thickness','bottom_bearing','top_bearing','print_layout','explode'} <= set(document['favorites'])


def test_native_proof_includes_real_edits_and_unchanged_acceptance():
    record=json.loads((PROJECT/'solidcraft/native_v7.json').read_text())
    proof=json.loads((PROJECT/record['assembly_verification']).read_text())
    assert proof['status']=='passed' and proof['native_only_edits']
    assert {'reduction_16','dimensions','different_bearings','M6_guides','motion','print_layout'} <= set(proof['cases'])
    for case in proof['cases'].values():
        assert case['status']=='passed' and case['second_reopen_body_count']==8
        assert case['sampling']['max_sampled_chord_error_mm'] <= .005
    for path in record['fit_verification'].values():
        assert json.loads((PROJECT/path).read_text())['status']=='passed'
    assert hashlib.sha256((PROJECT/'gearbox_native/acceptance.py').read_bytes()).hexdigest()=='aef1e8a522769f4e35fd83bccd3a281fa35bf24b36d6034549d42dad786bb311'


def test_legacy_regeneration_cannot_replace_native_master():
    from gearbox_native.project import require_legacy_authoring
    with pytest.raises(ValueError,match='native-only'):require_legacy_authoring()
