"""Repeatable native parameter-edit check for the generated V4 bearing."""
import copy
import json
from pathlib import Path
import sys

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))
sys.path.insert(0,json.loads((PROJECT/'solidcraft/config.json').read_text())['helper_root'])


def main():
    from oobb_solidcraft.mcp import MCPClient
    from oobb_solidcraft.backend import require_ok
    from gearbox_native.acceptance import health_check
    from gearbox_native.high_quality_presentation import check_mesh,digest
    named=PROJECT/'parts/oobb_part_motor_gearbox_cycloidal_version_4_20_to_1_reduction/solidcraft/high_quality_hardware/named'
    record=json.loads((named/'bearing_guide.json').read_text())
    output=PROJECT/'build/v4_presentation/parameter_edit';output.mkdir(parents=True,exist_ok=True)
    changed=output/'bearing_guide_width_4p2.solidcraft'
    with MCPClient(output/'edit',design=named/'bearing_guide.solidcraft',allow_path=PROJECT,timeout=600) as client:
        require_ok(client.call('set_parameter',{'name':'width','value':'4.2 mm'}))
        health_check(client,output/'edited_health.json')
        require_ok(client.call('save',{'path':str(changed)}))
    with MCPClient(output/'reopen',design=changed,allow_path=PROJECT,timeout=600) as client:
        health_check(client,output/'reopened_health.json')
        require_ok(client.call('export',{'path':str(changed.with_suffix('.stl'))}))
    spec=copy.deepcopy(record['spec']);spec['parameters']['width']=4.2
    result=dict(status='passed',parameter='width',before_mm=4,after_mm=4.2,
        saved_and_reopened=True,source_sha256=digest(named/'bearing_guide.solidcraft'),
        validation=check_mesh(changed.with_suffix('.stl'),spec))
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
