"""Isolated equation rotor proof before assembly integration."""
import json
from oobb_solidcraft.registry import discover
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.validation import inspect_shape
from gearbox_native.project import PROJECT
from gearbox_native.acceptance import health_check, verify_mesh
from gearbox_native.verification import read_step


def main():
    folder = PROJECT/'build/native_v9/rotor_03'
    geometry = json.loads((folder/'profile.json').read_text())
    report = {'status': 'running', 'cases': {}}
    for label, source, changes in [
        ('initial', folder/'gearbox.solidcraft', {}),
        ('eccentricity_edit', folder/'initial.solidcraft', {'eccentricity': '0.68 mm'}),
        ('edited_reopen', folder/'eccentricity_edit.solidcraft', {}),
        ('second_reopen', folder/'edited_reopen.solidcraft', {}),
    ]:
        with MCPClient(folder/label, design=source, allow_path=PROJECT, timeout=600) as client:
            if changes: require_ok(client.execute('parameters.change', changes=changes))
            health_check(client, folder/(label+'_health.json'))
            params = require_ok(client.execute('parameters.list', filter='user'))
            v = {p['name']: p['value'] for p in params['parameters']}
            sampling = discover().module('cycloidal_pattern').validate_edit(geometry, dict(
                ring_pin_count=int(v['ring_count']), pitch_radius=v['pitch'], eccentricity=v['eccentricity'],
                roller_radius=v['contact_radius'], clearance=v['profile_clearance']))
            require_ok(client.call('save', dict(path=str(folder/(label+'.solidcraft')))))
            for ext in ('step', 'stl'):
                require_ok(client.call('export', dict(path=str(folder/(label+'.'+ext)))))
        shape = read_step(folder/(label+'.step'))
        info = inspect_shape(shape)
        assert info['valid'] and info['solid_count'] == 1
        mesh = verify_mesh(folder/(label+'.stl'), shape)
        report['cases'][label] = dict(eccentricity=v['eccentricity'], pitch=v['pitch'], volume=info['volume_mm3'],
                                     sampling={k: x for k, x in sampling.items() if k != 'points'}, mesh=mesh)
        print(label, 'passed', flush=True)
    assert abs(report['cases']['initial']['volume'] - report['cases']['eccentricity_edit']['volume']) > .01
    report['status'] = 'passed'
    (folder/'verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__': main()
