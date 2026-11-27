"""Verify an actual native drive edit and its saved/reopened geometry."""
import argparse
import json
from pathlib import Path
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.validation import inspect_shape
from gearbox_native.project import PROJECT
from gearbox_native.acceptance import health_check, verify_mesh
from gearbox_native.verification import read_step


def verify(source, output, holder=False):
    output.mkdir(parents=True, exist_ok=False)
    saved = output / 'edited.solidcraft'
    changes = {'bearing_holder_depth':'7.5 mm'} if holder else {'drive_extension_length': '16 mm', 'drive_socket_clearance': '0.08 mm'}
    piece='bearing_holder' if holder else 'drive_sleeve'
    with MCPClient(output/'edit', design=source, allow_path=PROJECT, timeout=600) as client:
        health_check(client, output/'before_health.json')
        body_count=require_ok(client.call('measure'))['body_count']
        require_ok(client.execute('parameters.change', changes={'print_layout': '0', 'explode': '0 mm'}))
        require_ok(client.call('export', dict(path=str(output/'before.step'), bodies=[piece])))
        require_ok(client.execute('parameters.change', changes=changes))
        health_check(client, output/'edited_health.json')
        assert require_ok(client.call('measure'))['body_count'] == body_count
        require_ok(client.call('save', dict(path=str(saved))))
    with MCPClient(output/'reopen', design=saved, allow_path=PROJECT, timeout=600) as client:
        health_check(client, output/'reopened_health.json')
        values = {p['name']: p['value'] for p in require_ok(client.execute('parameters.list', filter='user'))['parameters']}
        if holder:assert values['bearing_holder_depth']==7.5
        else:assert values['drive_extension_length'] == 16 and abs(values['drive_socket_clearance']-.08) < 1e-8
        for ext in ('step', 'stl'):
            require_ok(client.call('export', dict(path=str(output/('after.'+ext)), bodies=[piece])))
        require_ok(client.call('save', dict(path=str(output/'resaved.solidcraft'))))
    with MCPClient(output/'second_reopen', design=output/'resaved.solidcraft', allow_path=PROJECT, timeout=600) as client:
        health_check(client, output/'resaved_health.json')
        assert require_ok(client.call('measure'))['body_count'] == body_count
    before = inspect_shape(read_step(output/'before.step'))
    after_shape = read_step(output/'after.step')
    after = inspect_shape(after_shape)
    assert before['valid'] and after['valid']
    delta = before['bounds_mm'][2]-after['bounds_mm'][2] if holder else after['bounds_mm'][5] - before['bounds_mm'][5]
    assert abs(delta-(1 if holder else 4)) < .001
    mesh = verify_mesh(output/'after.stl', after_shape)
    result = dict(status='passed', changes=changes, height_change_mm=delta, reopens=2,
                  native_body_count=body_count, before=before, after=after, mesh=mesh)
    (output/'verification.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    print('Native drive edit passed', flush=True)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--holder',action='store_true')
    a = p.parse_args()
    verify(a.source.resolve(), a.output.resolve(), a.holder)
