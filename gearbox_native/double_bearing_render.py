"""Build V2 presentation sheets from named bodies in the published SolidCraft export.

Run with the project's CAD Python: python -m gearbox_native.double_bearing_render
"""
import argparse
import json
from pathlib import Path
import subprocess

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
PART = ROOT / 'parts/oobb_part_motor_gearbox_cycloidal_simple_double_bearing_version_2_20_to_1_reduction'
CACHE = ROOT / 'build/double_bearing_studio'


def stage(views):
    published = json.loads((PART / 'native_export_verification.json').read_text())
    export = json.loads((views / 'export.json').read_text())
    if published['source_sha256'] != export['source_sha256']:
        raise ValueError('Render health records and published meshes must come from the same master.')

    def boxes(view):
        records = json.loads((views / f'{view}_health.json').read_text())['bodies']
        return {r['name']: np.array([r['bbox']['min'], r['bbox']['max']]) for r in records}

    assembled = boxes('assembled')
    exploded = boxes('exploded')
    shells = trimesh.load_mesh(PART / 'exploded.stl').split(only_watertight=False)
    bounds = np.array([s.bounds for s in shells])
    assigned = set()
    models = {}

    def add(name, mesh):
        models[name + '_v'] = np.asarray(mesh.vertices, dtype='float32')
        models[name + '_f'] = np.asarray(mesh.faces, dtype='int32')

    for name, box in exploded.items():
        if name == 'connected_contact_ring':
            continue  # Mutually exclusive with the twenty fitted contact sleeves.
        errors = np.abs(bounds - box).max(axis=(1, 2))
        index = int(errors.argmin())
        if errors[index] > .08 or index in assigned:
            raise ValueError(f'Cannot identify a unique production shell for {name}')
        assigned.add(index)
        mesh = shells[index]
        mesh.apply_translation((assembled[name] - box).mean(axis=0))
        if not np.allclose(mesh.bounds, assembled[name], atol=.08):
            raise ValueError(f'Assembly registration failed for {name}')
        if name not in ('output_lower_row_plate','output_circle_plate'):
            add(name, mesh)
    if len(assigned) != len(shells):
        raise ValueError('Unidentified geometry in exploded export')

    for end, plate in [('top', 'output_cap_plate'), ('bottom', 'output_nut_plate')]:
        mesh = trimesh.load_mesh(PART / 'native_parts/output_lower_row_plate.stl')
        if end == 'bottom':
            mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 1, 0]))
        mesh.apply_translation([0, 0, assembled[plate][0, 2] - mesh.bounds[0, 2]])
        if not np.allclose(mesh.bounds[:, 2], assembled[plate][:, 2], atol=.01):
            raise ValueError(f'Incorrect placement of rounded {end} flange')
        add('rounded_' + end, mesh)
    np.savez(CACHE / 'studio.npz', **models)
    (CACHE / 'native_parameters.json').write_text(json.dumps(published['parameters']),encoding='utf8')


def main():
    import sys
    args = sys.argv[1:]
    if '--views' in args:
        raise SystemExit('Presentation uses reviewed health snapshots. Update presentation/project.json and source/cad for a new master.')
    layout_only = '--layout-only' in args
    args = [a for a in args if a != '--layout-only']
    command=[sys.executable, str(ROOT/'presentation/scripts/build.py')]
    if not layout_only:
        command.append('--render')
    subprocess.run(command+args,check=True)


if __name__ == '__main__':
    main()
