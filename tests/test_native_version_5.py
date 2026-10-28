"""The approved V5 catalogue remains sealed during subsequent development."""
import hashlib,json
from gearbox_native.project import PROJECT,require_editable
import pytest


def test_version_five_is_sealed_with_accepted_native_documents():
    release=json.loads((PROJECT/'releases/version_5/release.json').read_text())
    part=PROJECT/'parts/oobb_part_motor_gearbox_cycloidal_version_5_20_to_1_reduction'
    assert release['status']=='sealed' and release['next_editable_version']=='version_6'
    assert json.loads((part/'SEALED.json').read_text())['version']=='version_5'
    for path in (part/'solidcraft').rglob('*.solidcraft'):
        expected=release['sealed_catalogue_sha256'][path.relative_to(PROJECT).as_posix()]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected


def test_version_five_rejects_regeneration():
    import working_solidcraft
    from working_oomp_populate import get_options
    with pytest.raises(ValueError,match='sealed'):working_solidcraft.get_version_5({})
    with pytest.raises(ValueError,match='sealed'):get_options([dict(style='version_5')])
    with pytest.raises(ValueError,match='Sealed release'):
        require_editable(PROJECT/'parts/oobb_part_motor_gearbox_cycloidal_version_5_20_to_1_reduction')
