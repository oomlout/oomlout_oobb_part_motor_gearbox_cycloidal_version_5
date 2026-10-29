"""Prove a taller native stack selects a standard clamp longer than 25 mm."""
import json
from gearbox_native.project import PROJECT
from gearbox_native.native_v8 import SCRATCH
from gearbox_native.acceptance import health_check,verify_mesh
from gearbox_native.verification import read_step
from oobb_solidcraft.validation import inspect_shape
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok

def main():
 folder=PROJECT/'build/native_v8/assembly_06/long_clamp';folder.mkdir(exist_ok=True)
 logs=SCRATCH/'assembly_06/long_clamp'
 with MCPClient(logs/'session',design=folder.parent/'gearbox.solidcraft',allow_path=PROJECT,timeout=600) as c:
  require_ok(c.execute('parameters.change',changes={'casing_bearing':'6820'}))
  health_check(c,logs/'health.json')
  params=require_ok(c.execute('parameters.list',filter='user'));v={p['name']:p['value'] for p in params['parameters']}
  assert v['join_screw_length']>25 and v['join_screw_length']%5==0
  assert v['join_head_seat']-v['upper_split_z']>=1
  for ext in ('step','stl'):require_ok(c.call('export',dict(bodies=['output_casing_upper'],path=str(folder/('upper.'+ext)))))
  require_ok(c.call('save',dict(path=str(folder/'gearbox.solidcraft'))))
 shape=read_step(folder/'upper.step');assert inspect_shape(shape)['valid']
 mesh=verify_mesh(folder/'upper.stl',shape)
 with MCPClient(logs/'reopen',design=folder/'gearbox.solidcraft',allow_path=PROJECT,timeout=600) as c:
  health_check(c,logs/'reopened_health.json');assert require_ok(c.call('measure'))['body_count']==9
 report=dict(status='passed',changes={'casing_bearing':'6820'},parameters={k:v[k] for k in ('casing_width','housing_top','join_screw_length','join_head_recess','join_head_seat','upper_split_z')},mesh=mesh,note='Clamp geometry and native health only; no full mechanism fit certification for 6820.')
 (folder/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(report['parameters'],flush=True)

if __name__=='__main__':main()
