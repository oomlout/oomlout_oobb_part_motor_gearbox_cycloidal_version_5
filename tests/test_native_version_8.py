"""Sealed V8 preserves the accepted three-piece native gearbox revision."""
import hashlib,json,zipfile
import pytest
from gearbox_native.project import PROJECT,VERSION,active_part,require_editable,require_legacy_authoring

def v8_part():
 return PROJECT/'parts/oobb_part_motor_gearbox_cycloidal_version_8_20_to_1_reduction'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def test_v8_retains_provenance_and_unchanged_acceptance():
 b=read(PROJECT/'solidcraft/version_8_baseline.json')
 assert not b['mechanical_changes']
 assert v8_part().name==b['part_id'] and (v8_part()/'SEALED.json').exists()
 parent=PROJECT/'parts'/b['parent_part_id']
 assert (parent/'SEALED.json').exists()
 for name,digest in b['inherited_files_sha256'].items():
  assert sha(parent/name)==digest
 assert len(list((v8_part()/'native_parts').glob('*.stl')))==9
 current=read(PROJECT/'solidcraft/native_v8.json')
 assert sha(v8_part()/'gearbox_controls.solidcraft')==current['master_sha256']
 assert current['initial_sha256']==b['master_sha256']
 assert sha(PROJECT/'gearbox_native/acceptance.py')==b['acceptance_sha256']

def test_v8_export_and_population_route_away_from_sealed_versions():
 import working_oomp_populate as populate
 assert populate.get_options()[0]['style']==VERSION
 with pytest.raises(ValueError,match='sealed'):populate.get_options([{'style':'version_7'}])
 with pytest.raises(ValueError,match='native-only'):require_legacy_authoring()
 with pytest.raises(ValueError,match='Sealed'):require_editable(PROJECT/'parts'/read(PROJECT/'solidcraft/version_8_baseline.json')['parent_part_id'])
 profile=read(PROJECT/'solidcraft/native_v8_profile.json')
 assert profile['definition']['profile_tolerance']<=.005
 with pytest.raises(ValueError,match='sealed'):populate.get_options([{'style':'version_8'}])
 with pytest.raises(ValueError,match='Sealed'):require_editable(v8_part())

def test_v7_archive_has_current_master_and_verification():
 r=read(PROJECT/'releases/version_7/release.json')
 assert r['status']=='sealed' and r['verification']['targeted_tests_passed']==12
 with zipfile.ZipFile(PROJECT/'releases/version_7'/r['archive']) as z:
  assert hashlib.sha256(z.read('gearbox_controls.solidcraft')).hexdigest()==r['master_sha256']
  for name in ('build/native_v7/odd_oobb_tabs_views_01/export.json','build/native_v7/odd_oobb_tabs_01/casing_verification.json'):
   assert json.loads(z.read(name))['status'] in ('passed','native_export_checked')


def native(path):
 with zipfile.ZipFile(path) as z:return json.loads(z.read('document.json'))


def test_compact_variant_changes_only_exposed_native_parameters():
 variants=read(PROJECT/'solidcraft/native_v8.json')['variants']
 a=native(v8_part()/'gearbox_controls.solidcraft')
 for option in variants.values():
  part=PROJECT/'parts'/option['part_id'];b=native(part/'gearbox_controls.solidcraft')
  pa={p['name']:p['expr'] for p in a['params']};pb={p['name']:p['expr'] for p in b['params']}
  changed={k for k in pa if pa[k]!=pb[k]}
  assert changed<=set(a['favorites'])
  assert changed<=set(option['native_parameters'])
  assert all(pb[k]==v for k,v in option['native_parameters'].items())
  assert a['components']==b['components']
  # Sketch solver caches and expanded pattern instances naturally change.
  # The feature history, operations, references and formulas do not.
  clean=lambda d:[{k:v for k,v in f.items() if k!='sketch'} for f in d['features']]
  assert clean(a)==clean(b)
  assert len(list((part/'native_parts').glob('*.stl')))==9
 compact=variants['10']
 assert compact['native_parameters']['contact_radius']=='1.5 mm'


def test_native_three_piece_revision_has_checked_edits_and_hardware():
 index=read(PROJECT/'solidcraft/native_v8.json');r=read(PROJECT/index['verification'])
 assert r['status']=='passed'
 assert set(r['cases'])=={'baseline','ratio_16','guide_spacers','M6_guides','large_lobes','compact_10'}
 for name,row in r['cases'].items():
  assert row['status']=='passed' and len(row['parts'])==9
  assert row['sampling']['max_sampled_chord_error_mm']<=.005
  assert all(p['valid'] and p['watertight'] for p in row['parts'].values())
 for name in ('baseline','compact_10'):
  row=r['cases'][name]
  assert row['reopens']==2 and row['maximum_intersection_mm3']<.03 and row['maximum_motion_overlap_mm3']<.03
  assert r['hardware'][name]['status']=='passed'
  assert r['hardware'][name]['maximum_overlap_mm3']<.03
 assert r['cases']['compact_10']['dimensions']['casing_radius']==pytest.approx(28.1)
 assert r['cases']['compact_10']['dimensions']['posts_enabled']==0
 assert r['long_clamp']['parameters']['join_screw_length']>25
 assert r['long_clamp']['parameters']['join_screw_length']%5==0
