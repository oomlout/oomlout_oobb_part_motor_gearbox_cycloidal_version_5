"""Run with the configured SolidCraft Python; no CAD process needed here."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest
import yaml

PROJECT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((PROJECT/'solidcraft/config.json').read_text())
sys.path.insert(0, CONFIG['helper_root'])
from oobb_solidcraft.compiler import compile_thing
from oobb_solidcraft.construction import build_thing
from gearbox_native.captured import resolve,build
from gearbox_native.parts import layout
from gearbox_native.lobe import profile_points


@pytest.fixture(scope='module')
def pieces():
    return build(**resolve({}))


def test_latest_only_and_options():
    with pytest.raises(ValueError,match='latest'):
        resolve({'architecture':'legacy'})
    values={'radius_offset':1.85,'reduction':20,'rotor_thickness':7,'disc_gap':0.5}
    original=copy.deepcopy(values)
    c=resolve(values)
    assert values==original and c==resolve(c)
    assert c['guide_bearing']==dict(id=10,od=15,depth=4)
    assert c['output_bearing']==dict(id=50,od=65,depth=7)
    assert c['guide_running_clearance']==pytest.approx(0.15)
    assert resolve({'disc_gap':0.7})['rotor_b_z']-c['rotor_b_z']==pytest.approx(0.2)


def test_fifteen_separate_printed_pieces(pieces):
    assert len(pieces)==15
    assert all(p['quantity']==1 for p in pieces.values())
    assert len(layout(pieces,**resolve({})))==15


@pytest.mark.parametrize('mode',['true','3dpr'])
def test_every_piece_compiles(pieces,mode):
    for name,piece in pieces.items():
        plan=compile_thing(dict(id=name,mode=mode,**piece['thing']))
        assert plan['result_bodies']
        assert all(c['command']!='file.insert_mesh' for c in plan['commands'])


def test_dense_profile_preserves_every_vertex(pieces):
    piece=pieces['rotor_a_lower']['thing']
    profile=piece['components'][0]['points']
    c=resolve({})
    assert profile==profile_points(c['disc_lobes'],c['pitch_radius'],c['radius_offset'],c['lobe_radius'],c['lobe_clearance'],c['samples_per_lobe'],c['profile_tolerance'])
    plan=compile_thing(dict(id='rotor',mode='3dpr',**piece))
    feature=next(f for f in plan['features'] if f['geometry']['kind']=='polygon')
    assert feature['geometry']['points']==profile
    assert len(plan['parameters'])<200


def test_nested_local_requests_and_project_schema():
    from gearbox_native.project import active_part
    path=active_part(PROJECT)/'working.yaml'
    part=yaml.safe_load(path.read_text())
    thing=build_thing(part,builder_path=PROJECT/'working_solidcraft.py',mode='true')
    assert len(thing['components'])==8 and thing['trace']==[]
    assert thing['builder']['api']=='solidcraft'
    part['oobb_details']['radius_ofset']=1.85
    with pytest.raises(ValueError,match='radius_ofset'):
        build_thing(part,builder_path=PROJECT/'working_solidcraft.py',mode='true')


def test_recipe_imports_no_legacy_geometry():
    import ast
    for path in (PROJECT/'gearbox_native').glob('*.py'):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(node,ast.Import):
                assert all(n.name not in ('oobb','opsc','gearbox') for n in node.names)
            if isinstance(node,ast.ImportFrom):
                assert not node.module or node.module.split('.')[0] not in ('oobb','opsc','gearbox')


def test_early_sealed_versions_have_no_native_files():
    for path in (PROJECT/'parts').iterdir():
        if (path/'SEALED.json').exists() and json.loads((path/'SEALED.json').read_text()).get('version') in ('version_1','version_2','version_3'):
            assert not list(path.rglob('*.solidcraft'))


def test_native_builder_rejects_sealed_revision():
    import working_solidcraft
    with pytest.raises(ValueError, match='sealed'):
        working_solidcraft.get_version_4({})
    with pytest.raises(ValueError, match='sealed'):
        working_solidcraft.get_cycloidal({}, style='version_4')


@pytest.mark.parametrize('reduction', [8, 12])
def test_native_catalogue_reduction_overrides(reduction):
    from gearbox_native.project import active_part
    from working_oomp_populate import get_options
    part = yaml.safe_load((active_part(PROJECT)/'working.yaml').read_text())
    part['oobb_details'] = get_options([dict(reduction=reduction)]) [0]['oobb_details']
    thing = build_thing(part,builder_path=PROJECT/'working_solidcraft.py',mode='3dpr')
    assert thing['gearbox']['config']['reduction'] == reduction
    assert len(thing['gearbox']['pieces']) == 8
