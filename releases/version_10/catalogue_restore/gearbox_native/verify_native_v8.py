"""Native V8 edits, exports, mechanical clearance and archived evidence."""
import json,hashlib,itertools
from pathlib import Path
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.registry import discover
from oobb_solidcraft.validation import inspect_shape
from gearbox_native import acceptance
from gearbox_native.project import PROJECT
from gearbox_native.verification import read_step
from gearbox_native.native_v8 import SCRATCH,PRINT_POSITIONS
from gearbox_native.exact_geometry import _move
from working_oomp_populate import get_options

FOLDER=PROJECT/'build/native_v8/assembly_06'
VARIANT=next(o['native_parameters'] for o in get_options() if o['reduction']==10)
CASES={'baseline':{},'ratio_16':{'reduction':'16'},'guide_spacers':{'standoff_radius':'0 mm','guide_count':'4','guide_outer_radius':'2 mm'},
 'M6_guides':{'standoff_radius':'0 mm','guide_count':'3','guide_radius':'3 mm','guide_outer_radius':'3 mm','eccentricity':'0.5 mm'},'large_lobes':{'reduction':'24'},'compact_10':VARIANT}

def volume(shape):
 props=GProp_GProps();BRepGProp.VolumeProperties_s(shape,props);return props.Mass()
def overlap(a,b):
 op=BRepAlgoAPI_Common(a,b);op.Build();assert op.IsDone();return max(0,volume(op.Shape()))

def check_case(client,name,changes,base_values,geometry):
 if changes:require_ok(client.execute('parameters.change',changes=changes))
 logs=SCRATCH/'assembly_06/verification'/name;logs.mkdir(parents=True,exist_ok=True)
 acceptance.health_check(client,logs/'health.json')
 params=require_ok(client.execute('parameters.list',filter='user'))
 v={p['name']:p['value'] for p in params['parameters']}
 sampling=discover().module('cycloidal_pattern').validate_edit(geometry,dict(ring_pin_count=int(v['ring_count']),pitch_radius=v['pitch'],eccentricity=v['eccentricity'],roller_radius=v['contact_radius'],clearance=v['profile_clearance']))
 row=dict(status='running',changes=changes,dimensions={k:v[k] for k in ('reduction','contact_radius','tab_plate_size','guide_screw_length','casing_radius','lobe_band_radius','pitch','guide_pitch','guide_count','guide_outer_radius','posts_enabled','join_screw_length','join_head_recess')},sampling={k:x for k,x in sampling.items() if k!='points'},parts={})
 assert abs(v['join_screw_length']/5-round(v['join_screw_length']/5))<1e-9
 assert v['join_head_seat']-v['upper_split_z']>=1
 assert v['guide_orbit_radius']-v['guide_outer_radius']-v['eccentricity']>=.2-1e-8
 path=FOLDER/name;path.mkdir(exist_ok=True)
 shapes={}
 for part in PRINT_POSITIONS:
  for ext in ('step','stl'):require_ok(client.call('export',dict(bodies=[part],path=str(path/(part+'.'+ext)))))
  shape=read_step(path/(part+'.step'));info=inspect_shape(shape);assert info['valid'],(name,part)
  mesh=acceptance.verify_mesh(path/(part+'.stl'),shape)
  row['parts'][part]=dict(shape=info,mesh=mesh);shapes[part]=shape
 if name in ('baseline','compact_10'):
  row['intersections']=[]
  for a,b in itertools.combinations(shapes,2):
   amount=overlap(shapes[a],shapes[b]);row['intersections'].append(dict(parts=[a,b],volume=amount))
   assert amount<.03,(name,a,b,amount)
  # Independent rigid motion check of the actual exported native BReps.
  row['motion']=[]
  for angle in range(0,361,30):
   import math
   radians=math.radians(angle);e=v['eccentricity']
   ring=_move(shapes['output_casing_lobes'],'rotate',[0,0,angle/v['ring_count']])
   for side,sgn in [('a',1),('b',-1)]:
    rotor=_move(shapes['rotor_'+side],'translate',[sgn*e*(math.cos(radians)-1),sgn*e*math.sin(radians),0])
    amount=overlap(rotor,ring);row['motion'].append(dict(angle=angle,rotor=side,volume=amount));assert amount<.03,(name,angle,side,amount)
  require_ok(client.call('save',dict(path=str(path/'gearbox.solidcraft'))))
 row['status']='passed';(logs/'report.json').write_text(json.dumps(row,indent=2),encoding='utf-8')
 print(name,'passed',row['dimensions'],flush=True)
 return row

def main(selected=None):
 selected=selected or list(CASES)
 geometry=json.loads((FOLDER/'profile.json').read_text(encoding='utf-8'))
 report_path=SCRATCH/'verification/report.json'
 report=json.loads(report_path.read_text(encoding='utf-8')) if selected!=list(CASES) else dict(cases={})
 report['status']='running'
 import uuid
 with MCPClient(SCRATCH/'assembly_06/verification'/('session_'+uuid.uuid4().hex[:8]),design=FOLDER/'gearbox.solidcraft',allow_path=PROJECT,timeout=600) as c:
  params=require_ok(c.execute('parameters.list',filter='user'));baseline={p['name']:p['expression'] for p in params['parameters']}
  for name,changes in CASES.items():
   if name not in selected:continue
   # Reset only the controls exercised by preceding cases, in one native rebuild.
   reset={k:baseline[k] for case in CASES.values() for k in case};reset.update(changes)
   report['cases'][name]=check_case(c,name,reset,baseline,geometry)
   (SCRATCH/'verification/report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 for name in ('baseline','compact_10'):
  if name not in selected:continue
  path=FOLDER/name;logs=SCRATCH/'assembly_06/verification'/name
  for index,source in [(1,path/'gearbox.solidcraft'),(2,path/'resaved.solidcraft')]:
   with MCPClient(logs/f'reopen_{index}',design=source,allow_path=PROJECT,timeout=600) as c:
    acceptance.health_check(c,logs/f'reopened_{index}.json');assert require_ok(c.call('measure'))['body_count']==9
    if index==1:require_ok(c.call('save',dict(path=str(path/'resaved.solidcraft'))))
  report['cases'][name]['reopens']=2
 assert report['cases']['ratio_16']['dimensions']['pitch']<report['cases']['baseline']['dimensions']['pitch']
 assert report['cases']['compact_10']['dimensions']['casing_radius']<report['cases']['baseline']['dimensions']['casing_radius']
 report['status']='passed';(SCRATCH/'verification/report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print('All native V8 verification passed',flush=True)

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--cases',nargs='+',choices=list(CASES));args=parser.parse_args();main(args.cases)
