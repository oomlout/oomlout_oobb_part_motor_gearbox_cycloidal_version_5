"""The complete V6 iteration is frozen while V7 is edited."""
import hashlib,json
import pytest
from gearbox_native.project import PROJECT,require_editable


def test_version_six_is_sealed_with_two_accepted_native_configurations():
    release=json.loads((PROJECT/'releases/version_6/release.json').read_text())
    assert release['status']=='sealed' and release['next_editable_version']=='version_7'
    assert set(release['verification']['native_examples'])=={'20','16'}
    for example in release['verification']['native_examples'].values():
        part=PROJECT/'parts'/example['part_id']
        assert json.loads((part/'SEALED.json').read_text())['version']=='version_6'
        for path in (part/'solidcraft').rglob('*.solidcraft'):
            expected=release['sealed_catalogue_sha256'][path.relative_to(PROJECT).as_posix()]
            assert hashlib.sha256(path.read_bytes()).hexdigest()==expected


def test_version_six_rejects_regeneration():
    import working_solidcraft
    from working_oomp_populate import get_options
    with pytest.raises(ValueError,match='sealed'):working_solidcraft.get_version_6({})
    with pytest.raises(ValueError,match='sealed'):get_options([dict(style='version_6')])
    for path in (PROJECT/'parts').glob('*version_6*'):
        with pytest.raises(ValueError,match='Sealed release'):require_editable(path)
