"""Remove the narrow shelf above each shared OOBB NEMA countersink."""
import json,zipfile,shutil
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from gearbox_native.project import PROJECT
from gearbox_native.native_v8 import SCRATCH
from gearbox_native.acceptance import health_check
from working_oomp_populate import get_options

def main():
 source=PROJECT/'build/native_v8/assembly_04/baseline/gearbox.solidcraft'
 out=PROJECT/'build/native_v8/assembly_05';out.mkdir(exist_ok=True)
 shutil.copyfile(source.parent.parent/'profile.json',out/'profile.json')
 with zipfile.ZipFile(source) as z:d=json.loads(z.read('document.json'))
 params={p['name']:p['expr'] for p in d['params']};changes={}
 for index in range(31,35):
  prefix=f'cut_{index}_direct_000_revolved_profile_00_radius_'
  assert params[prefix+'2']=='3.0 mm' and params[prefix+'4']=='3.6 mm'
  for n in (2,3):changes[prefix+str(n)]=prefix+'4'
 with MCPClient(SCRATCH/'assembly_05/access_fix',design=source,allow_path=PROJECT,timeout=600) as c:
  require_ok(c.execute('parameters.change',changes=changes))
  health_check(c,SCRATCH/'assembly_05/baseline_health.json')
  require_ok(c.call('save',dict(path=str(out/'gearbox.solidcraft'))))
  variant=next(o['native_parameters'] for o in get_options() if o['reduction']==10)
  require_ok(c.execute('parameters.change',changes=variant))
  health_check(c,SCRATCH/'assembly_05/compact_health.json')
  require_ok(c.call('save',dict(path=str(out/'compact_probe.solidcraft'))))
 print('Full countersunk-head access: baseline and compact native health passed',flush=True)

if __name__=='__main__':main()
