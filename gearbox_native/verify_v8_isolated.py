import json
from pathlib import Path
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.registry import discover
from oobb_solidcraft.validation import inspect_shape
from gearbox_native.project import PROJECT
from gearbox_native.acceptance import health_check,verify_mesh
from gearbox_native.verification import read_step
from gearbox_native.native_v8 import SCRATCH
cases={'rotor_01':{'standoff_radius':'0 mm','reduction':'10','guide_count':'3','eccentricity':'0.9 mm','top_bearing':'6702','bottom_bearing':'6702','casing_bearing':'6808'},
       'mount_01':{'standoff_radius':'0 mm','guide_count':'4','guide_outer_radius':'2 mm'}}
report={}
for name,changes in cases.items():
 folder=PROJECT/'build/native_v8'/name;logs=SCRATCH/name
 shape=read_step(folder/'gearbox.step');assert inspect_shape(shape)['valid']
 verify_mesh(folder/'gearbox.stl',shape)
 with MCPClient(logs/'edit',design=folder/'gearbox.solidcraft',allow_path=PROJECT,timeout=600) as c:
  require_ok(c.execute('parameters.change',changes=changes));health_check(c,logs/'edited_health.json')
  params=require_ok(c.execute('parameters.list',filter='user'))
  v={p['name']:p['value'] for p in params['parameters']}
  if name.startswith('rotor'):
   g=json.loads((folder/'profile.json').read_text(encoding='utf-8'))
   discover().module('cycloidal_pattern').validate_edit(g,dict(ring_pin_count=int(v['reduction']),pitch_radius=v['pitch'],eccentricity=v['eccentricity'],roller_radius=v['contact_radius'],clearance=v['profile_clearance']))
  require_ok(c.call('save',dict(path=str(folder/'edited.solidcraft'))))
  for ext in ('step','stl'):require_ok(c.call('export',dict(path=str(folder/('edited.'+ext)))))
 with MCPClient(logs/'reopen',design=folder/'edited.solidcraft',allow_path=PROJECT,timeout=600) as c:
  health_check(c,logs/'reopened_health.json');require_ok(c.call('save',dict(path=str(folder/'resaved.solidcraft'))))
 with MCPClient(logs/'second_reopen',design=folder/'resaved.solidcraft',allow_path=PROJECT,timeout=600) as c:health_check(c,logs/'second_reopened_health.json')
 shape=read_step(folder/'edited.step');assert inspect_shape(shape)['valid'];verify_mesh(folder/'edited.stl',shape)
 report[name]=dict(status='passed',changes=changes,pitch=v['pitch'],casing_diameter=2*v['casing_radius'],guide_count=v['guide_count'],posts_enabled=v['posts_enabled'])
 print(name,report[name],flush=True)
(SCRATCH/'isolated_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
