"""Active native design identity; preserved releases do not follow this setting."""
from pathlib import Path
import json
import os

VERSION = "version_9"
PART_ID = f"oobb_part_motor_gearbox_cycloidal_{VERSION}_35_to_1_reduction"
PROJECT = Path(__file__).resolve().parents[1]


def active_part(project=PROJECT):
    project=Path(project)
    selected=os.environ.get('GEARBOX_ACTIVE_PART')
    pointer=project/'solidcraft/active_design.json'
    if not selected and pointer.exists():selected=json.loads(pointer.read_text(encoding='utf-8'))['part_id']
    if selected:
        if not selected.startswith(f'oobb_part_motor_gearbox_cycloidal_{VERSION}_') or Path(selected).name!=selected:
            raise ValueError(f'Active design must name a local {VERSION} catalogue item')
        return project/'parts'/selected
    return project / "parts" / PART_ID


def require_editable(folder):
    if (Path(folder) / "SEALED.json").exists():
        raise ValueError(f"Sealed release cannot be modified: {folder}")


def native_only():
    """The active native marker protects the master."""
    return (PROJECT / f'solidcraft/native_v{VERSION.split("_")[-1]}.json').exists()


def require_legacy_authoring():
    if native_only():
        raise ValueError(f'{VERSION} is native-only. Edit gearbox_controls.solidcraft in the Parameters menu. '
                         'Use action_export_native.py for exports; legacy regeneration cannot replace the native master.')
