"""Measure the V9 motor retrofit against the print-oriented native exports."""
import itertools
import json
from pathlib import Path

from gearbox_native.exact_geometry import _move
from gearbox_native.verification import read_step
from gearbox_native.verify_native_v8 import overlap
from gearbox_native.verify_native_v9 import shaft_hardware


def verify(views):
    export = json.loads((views/'export.json').read_text(encoding='utf-8'))
    assert export['status'] == 'native_export_checked'
    v = {p['name']: p['value'] for p in export['parameters']['parameters']}
    locations = {
        'motor_mount': (0, 0, 0), 'motor_spacer': (0, 0, -v['motor_spacer_depth']),
        'pin_front': (0, 0, v['front_z']),
        'eccentric_hub_lower': (0, 0, v['drive_base_bottom']),
        'eccentric_hub_upper': (0, 0, v['seam_z']),
        'rotor_a': (v['eccentricity'], 0, v['rotor_a_z']),
        'rotor_b': (-v['eccentricity'], 0, v['rotor_b_z'] + v['disc_thickness']),
        'output_casing_lower': (0, 0, v['lower_split_z']),
        'output_casing_lobes': (0, 0, v['lower_split_z']),
        'output_casing_upper': (0, 0, v['upper_split_z']),
    }
    assert set(export['parts']) == set(locations)
    shapes = {}
    for name, location in locations.items():
        shape = read_step(views/'parts'/(name+'.step'))
        if name in ('rotor_b', 'output_casing_lower'):
            shape = _move(shape, 'rotate', [180,0,0])
        shapes[name] = _move(shape, 'translate', location)
    checks = []
    def clear(label, tool, targets):
        for name, body in targets.items():
            amount = overlap(tool, body)
            assert amount < .03, (label, name, amount)
            checks.append(dict(check=label, part=name, overlap_mm3=amount))
    shaft_hardware(clear, shapes, v)
    revised = {'motor_spacer', 'eccentric_hub_lower', 'eccentric_hub_upper'}
    for a,b in itertools.combinations(locations, 2):
        if a in revised or b in revised:
            clear(a, shapes[a], {b: shapes[b]})
    return dict(status='passed', source_sha256=export['source_sha256'], checks=checks,
                sampling_error_mm=export['sampling']['max_sampled_chord_error_mm'],
                print_parts=len(shapes), shaft_end_to_join_head_mm=v['wiggle_join_head_seat']-2.5-v['motor_shaft_end'])


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('views', type=Path)
    args = parser.parse_args()
    (args.views/'motor_fit.json').write_text(json.dumps(verify(args.views),indent=2)+'\n',encoding='utf-8')
