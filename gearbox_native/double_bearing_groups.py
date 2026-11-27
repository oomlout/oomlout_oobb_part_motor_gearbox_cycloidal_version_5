"""Group the existing part placements into toggleable native subassemblies."""
from oobb_solidcraft.backend import require_ok


BROWSER_GUIDE = """## Browser visibility

Click the eye beside **Hardware** to hide or show all purchased parts. Expand it for separate **Bearings** and **Fasteners** controls. Fasteners includes the screws, their socket heads and all nuts.

**Top plate and carrier** and **Bottom plate and carrier** each contain the corresponding OOBB output plate, 6810 retaining cylinder and both halves of its stationary carrier. **Alternative output plate** contains the lower-row flange and, in the current manual model, the plain circular OOBB plate parked beside the main assembly. Toggle either child individually. **Disc A** is the lower cycloid and **Disc B** is the upper one. Each contains its two printed halves. Their bearings and clamps are in Hardware.

**Input shaft stack** contains two identical E end journals, two N mount carriers and four C eccentric halves. **Inner guide sleeves** and **Outer ring contacts** control the printed spacers. Expand Outer ring contacts to switch between the loose sleeves and the optional connected ring. The loose sleeves are selected in the assembly. The print view includes both options.
"""


def component_group(name):
    if name.startswith(('hardware_6704_', 'hardware_6810_')):
        return 'Bearings'
    if name.startswith('hardware_'):
        return 'Fasteners'
    if name in ('output_lower_row_plate','output_circle_plate'):
        return 'Alternative output plate'
    if name in ('output_cap_plate','output_cap_cylinder', 'carrier_top','carrier_top_cap','carrier_top_nut_tray'):
        return 'Top plate and carrier'
    if name in ('output_nut_plate','output_nut_cylinder', 'carrier_bottom','carrier_bottom_cap'):
        return 'Bottom plate and carrier'
    if name.startswith('rotor_a'):
        return 'Disc A'
    if name.startswith('rotor_b'):
        return 'Disc B'
    if name.startswith(('input_d_shaft', 'round_shim_', 'eccentric_spacer_', 'shaft_')):
        return 'Input shaft stack'
    if name in ('printed_contact_sleeve', 'connected_contact_ring'):
        return 'Outer ring contacts'
    if name == 'printed_drive_sleeve':
        return 'Inner guide sleeves'
    raise ValueError(f'Unassigned gearbox component: {name}')


def group_components(client):
    tree = require_ok(client.execute('component.list', compact=True))['components']
    sections = {}
    for part in tree:
        if part['id'] == 0:
            continue
        name = component_group(part['name'])
        sections.setdefault(name, []).extend(o['id'] for o in part['occurrences'])
    commands = [{'command':'component.create', 'params':dict(name='Hardware', parent=0, activate=False)}]
    for name, occurrences in sections.items():
        parent = 'Hardware' if name in ('Bearings','Fasteners') else 0
        commands.append({'command':'component.create', 'params':dict(name=name, parent=parent, activate=False)})
        commands.append({'command':'browser.reparent', 'params':dict(component=name, occurrences=occurrences)})
    require_ok(client.call('batch', dict(commands=commands, verbose=False)))
