"""Regenerate the active shaft reference from its localized production meshes."""
import json
from gearbox_native.stacked_shaft_drawing import draw as draw_shaft_reference
from gearbox_native.project import active_part

if __name__=='__main__':
    part=active_part()
    draw_shaft_reference(part,json.loads((part/'native_export_verification.json').read_text(encoding='utf8'))['parameters'])
