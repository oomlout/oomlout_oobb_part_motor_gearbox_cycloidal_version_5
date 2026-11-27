"""Append the manual gearbox's circular option; retain every existing part."""
import argparse,hashlib,json,shutil
from pathlib import Path
import numpy as np
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.registry import discover
from gearbox_native.project import PROJECT
from gearbox_native.simple_double_bearing import MASTER,place
from gearbox_native import double_bearing_housing as housing
from gearbox_native.acceptance import health_check


def build(folder):
    folder.mkdir(parents=True,exist_ok=False)
    source=PROJECT/MASTER;digest=hashlib.sha256(source.read_bytes()).hexdigest()
    shutil.copy2(source,folder/'before.solidcraft')
    with MCPClient(folder/'author',design=source,allow_path=PROJECT,timeout=1800) as c:
        before=health_check(c,folder/'before_health.json')
        assert housing.CIRCLE not in {b['name'] for b in before['bodies']}
        cls=discover().module('native_design').Design;d=cls.__new__(cls)
        d.client=c;d.commands=[];d.index=14000;d.body=None
        housing.circle_parameters(d);housing.circle_plate(d);place(d,housing.CIRCLE)
        tree=require_ok(c.execute('component.list',compact=True))['components']
        circle=next(x for x in tree if x['name']==housing.CIRCLE)
        require_ok(c.execute('browser.reparent',component='Alternative output plate',occurrences=[o['id'] for o in circle['occurrences']]))
        after=health_check(c,folder/'after_health.json')
        byname={b['name']:b for b in after['bodies']}
        for b in before['bodies']:
            current=byname[b['name']]
            assert abs(b['volume_mm3']-current['volume_mm3'])<.001,b['name']
            assert np.allclose(b['center_of_mass'],current['center_of_mass'],atol=.0001),b['name']
        require_ok(c.call('save',dict(path=str(folder/'complete.solidcraft'))))
    with MCPClient(folder/'edit',design=folder/'complete.solidcraft',allow_path=PROJECT,timeout=1800) as c:
        health_check(c,folder/'reopened_health.json')
        require_ok(c.execute('parameters.change',changes={'circle_grid_radius':'75 mm'}))
        edited=health_check(c,folder/'edited_health.json')
        require_ok(c.call('save',dict(path=str(folder/'edited.solidcraft'))))
    with MCPClient(folder/'reopen_edit',design=folder/'edited.solidcraft',allow_path=PROJECT,timeout=1800) as c:
        health_check(c,folder/'reopened_edit_health.json')
        v={p['name']:p['value'] for p in require_ok(c.execute('parameters.list',filter='user'))['parameters']}
        assert v['circle_plate_radius']==82
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    (folder/'option_verification.json').write_text(json.dumps(dict(status='passed',previous_master_sha256=digest,
        new_part=housing.CIRCLE,unchanged_existing_bodies=len(before['bodies']),
        default_diameter_mm=134,depth_mm=3,edited_diameter_mm=164,save_reopen=True,edit_save_reopen=True),indent=2))
    print('CIRCULAR OPTION AND PARAMETER EDIT PASSED',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);build(p.parse_args().folder.resolve())
