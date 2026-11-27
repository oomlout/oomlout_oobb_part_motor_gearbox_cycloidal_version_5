"""Independent hardware/access checks against the published native STEP bodies."""
import json,math
from pathlib import Path
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder,BRepPrimAPI_MakePrism
from OCP.gp import gp_Vec
from oobb_solidcraft import api
from gearbox_native.exact_geometry import _polygon,_move,_boolean
from gearbox_native.verification import read_step
from gearbox_native.verify_native_v8 import overlap


def cylinder(radius,height,xyz):
 return _move(BRepPrimAPI_MakeCylinder(radius,height).Shape(),'translate',xyz)


def hexagon(size,height,xyz,angle=30):
 radius=api.gv('nut_radius_'+size,'true')
 points=[(radius*math.cos(math.radians(angle+i*60)),radius*math.sin(math.radians(angle+i*60))) for i in range(6)]
 return _move(BRepPrimAPI_MakePrism(_polygon(points),gp_Vec(0,0,height)).Shape(),'translate',xyz)


def verify(case,views):
 case,views=Path(case),Path(views)
 report=json.loads((views/'export.json').read_text(encoding='utf-8'))
 v={p['name']:p['value'] for p in report['parameters']['parameters']}
 shapes={name:read_step(case/(name+'.step')) for name in report['parts']}
 checks=[]
 rings=[_boolean('cut',cylinder(v['casing_od']/2,v['casing_width'],[0,0,z]),[cylinder(v['casing_bore_diameter']/2,v['casing_width']+.02,[0,0,z-.01])]) for z in (v['casing_bottom'],v['front_seat_bottom'])]
 def bearing_clear(label,tool):
  for index,ring in enumerate(rings):
   amount=overlap(tool,ring);checks.append(dict(check=label+'_vs_casing_bearing',bearing_index=index,overlap_mm3=amount));assert amount<.03,(label,index,amount)
 def clear(label,tool,targets):
  for target in targets:
   amount=overlap(tool,shapes[target]);checks.append(dict(check=label,part=target,overlap_mm3=amount))
   assert amount<.03,(label,target,amount)
 cases=['output_casing_lower','output_casing_lobes','output_casing_upper']
 for i in range(4):
  a=math.radians(i*90);co,si=round(math.cos(a)),round(math.sin(a))
  def xy(x,y):return [x*co-y*si,x*si+y*co]
  x,y=xy(v['tab_radius']-7.5,22.5)
  clear('M3_clamp_shank',cylinder(1.5,v['join_screw_length'],[x,y,v['join_tip_z']]),cases)
  clear('M3_clamp_head',cylinder(2.9,3,[x,y,v['join_head_seat']]),cases)
  # Nominal nut and its entire loading path from below, inset from bottom.
  clear('M3_clamp_nut_access',hexagon('m3',4.5,[x,y,v['casing_bottom']]),cases)
  bearing_clear('M3_clamp_nut',hexagon('m3',2.5,[x,y,v['casing_bottom']+2]))
  for pos in (-15,0,15):
   x,y=xy(v['tab_radius'],pos)
   clear('M6_mount_shank',cylinder(3,v['housing_top']-v['casing_bottom'],[x,y,v['casing_bottom']]),cases)
   clear('M6_nut_access',hexagon('m6',6.3,[x,y,v['casing_bottom']]),cases)
   bearing_clear('M6_mount_nut',hexagon('m6',5,[x,y,v['casing_bottom']+1.3]))
 for i in range(int(v['guide_count'])):
  a=v['guide_phase']+i*360/v['guide_count'];rad=math.radians(a)
  x,y=v['guide_pitch']*math.cos(rad),v['guide_pitch']*math.sin(rad)
  seat=v['front_z']+1.4;tip=seat-v['guide_screw_length'];nut_top=tip+.3+v['guide_nut_depth']
  size='m6' if v['guide_radius']==3 else 'm3'
  clear('guide_screw',cylinder(v['guide_radius'],v['guide_screw_length'],[x,y,tip]),list(shapes))
  head=cylinder(api.gv('screw_socket_cap_radius_'+size,'true'),api.gv('screw_socket_cap_height_'+size,'true'),[x,y,seat])
  clear('guide_head',head,list(shapes))
  clear('guide_nut_access',hexagon(size,nut_top-.2,[x,y,0],a+30),['motor_mount'])
  # Nut must fit inside the bearing bore, or lie entirely below the bearing.
  nut=hexagon(size,api.gv('nut_depth_'+size,'true'),[x,y,tip+.3],a+30)
  bearing_clear('guide_nut',nut);bearing_clear('guide_head',head)
 output=dict(status='passed',checks=checks,overlap_tolerance_mm3=.03)
 (case/'hardware_verification.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
 print(case.name,'hardware/access checks passed:',len(checks),flush=True)
 return output


if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('case',type=Path);p.add_argument('views',type=Path);a=p.parse_args();verify(a.case,a.views)
