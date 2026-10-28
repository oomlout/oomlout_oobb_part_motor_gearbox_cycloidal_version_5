"""Extend the existing native master in isolation; preserve all its current settings."""
import hashlib
import json
from pathlib import Path
import shutil
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from gearbox_native.project import PROJECT
from gearbox_native.acceptance import health_check
from gearbox_native.native_tabs import tab_parameters, TAB_RADIUS


def main():
    source=PROJECT/'gearbox_controls.solidcraft'
    folder=PROJECT/'build/native_v7/odd_oobb_tabs_01';folder.mkdir(parents=True,exist_ok=False)
    report=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),status='running')
    shutil.copyfile(PROJECT/'solidcraft/native_v7_profile.json',folder/'profile.json')
    with MCPClient(folder/'upgrade',design=source,allow_path=PROJECT,timeout=600) as client:
        health_check(client,folder/'original_health.json')
        before=require_ok(client.execute('parameters.list',filter='user'))
        old={p['name']:p['expression'] for p in before['parameters']}
        assert 'tab_plate_size' not in old,'Already upgraded; do not duplicate controls'
        for name,expression,unit in tab_parameters():
            require_ok(client.execute('parameters.add',name=name,expression=expression,unit=unit,
                favorite=False,comment='OOBB tab sizing: native derived dimension; M6 clearance is an additional radial gap.'))
        require_ok(client.execute('parameters.change',changes={'tab_radius':TAB_RADIUS}))
        after=require_ok(client.execute('parameters.list',filter='user'))
        new={p['name']:p['expression'] for p in after['parameters']}
        assert all(new[k]==v for k,v in old.items() if k!='tab_radius')
        health_check(client,folder/'health.json')
        require_ok(client.call('save',dict(path=str(folder/'gearbox.solidcraft'))))
        report.update(status='native_upgrade_checked',preserved_existing_parameters=True,
                      parameters=after,updated_sha256=hashlib.sha256((folder/'gearbox.solidcraft').read_bytes()).hexdigest())
    (folder/'upgrade.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Saved native tab upgrade',folder,flush=True)


if __name__=='__main__':main()
