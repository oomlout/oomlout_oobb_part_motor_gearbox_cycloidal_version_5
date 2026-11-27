"""Separate the countersink mouth from the coincident motor-plate union face."""
import json,zipfile,shutil
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from gearbox_native.project import PROJECT
from gearbox_native.native_v8 import SCRATCH
from gearbox_native.acceptance import health_check
from working_oomp_populate import get_options

def main():
 source=PROJECT/'build/native_v8/assembly_05/gearbox.solidcraft'
 out=PROJECT/'build/native_v8/assembly_06';out.mkdir(exist_ok=True)
 shutil.copyfile(source.parent/'profile.json',out/'profile.json')
 with zipfile.ZipFile(source) as z:d=json.loads(z.read('document.json'))
 changes={next(f for f in d['features'] if f['id']==n)['param_names'][2]:'motor_plate_depth - 0.02 mm' for n in (266,270,274,278)}
 with MCPClient(SCRATCH/'assembly_06/seat_fix',design=source,allow_path=PROJECT,timeout=600) as c:
  require_ok(c.execute('parameters.change',changes=changes))
  health_check(c,SCRATCH/'assembly_06/baseline_health.json')
  require_ok(c.call('save',dict(path=str(out/'gearbox.solidcraft'))))
  variant=next(o['native_parameters'] for o in get_options() if o['reduction']==10)
  require_ok(c.execute('parameters.change',changes=variant))
  health_check(c,SCRATCH/'assembly_06/compact_health.json')
  require_ok(c.call('save',dict(path=str(out/'compact_probe.solidcraft'))))
 print('Countersink seat clearance: baseline and compact native health passed',flush=True)

if __name__=='__main__':main()
