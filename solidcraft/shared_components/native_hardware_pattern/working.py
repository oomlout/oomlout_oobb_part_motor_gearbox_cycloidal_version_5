"""OOBB nut cavities with a native variable-count sketch pattern.

Replays the actual OOBB nut/overhang prisms, not a separately sized hexagon.
Only planar, untranslated rotations are supported; unsupported trees fail.
"""
import copy,math
from oobb_solidcraft import api
from oobb_solidcraft.compiler import compile_thing

def prisms(request):
 thing=dict(id='pattern_nut',mode='3dpr',components=[])
 api.append_full(thing,shape='oobb_nut',type='p',**request)
 result=[]
 def visit(node,offset=(0,0,0)):
  op=node['op'];children=node.get('children',[])
  if op=='difference':
   assert all(not c.get('children') for c in children[1:]),'Subtractive catalogue nut unsupported'
   visit(children[0],offset)
  elif op=='union':
   for c in children:visit(c,offset)
  elif op=='translate':visit(children[0],tuple(a+b for a,b in zip(offset,node['value'])))
  elif op=='rotate':
   assert all(abs(v)<1e-12 for v in node['value']),'Rotated catalogue input unsupported'
   visit(children[0],offset)
  elif op=='solid':
   g=node['value'];x,y,z=offset
   if g['kind']=='cube':
    w,h,depth=g['size'];points=[(x,y),(x+w,y),(x+w,y+h),(x,y+h)]
   elif g['kind']=='polyg':
    depth=g['height'];z+=g.get('z_offset',0)
    points=[(x+g['radius']*math.cos(i*2*math.pi/g['sides']),y+g['radius']*math.sin(i*2*math.pi/g['sides'])) for i in range(g['sides'])]
   else:raise ValueError('Unsupported nut prism: '+g['kind'])
   result.append(dict(points=points,z=z,depth=depth))
  else:raise ValueError(op)
 visit(compile_thing(thing)['tree'])
 return result

def cut(design,*,pitch,count,z,phase='0 deg',rotation='0 deg',radius_name='m3',depth=3,selector=None,open_bottom=False):
 """Cut shared OOBB overhang=True nuts; optional 0/1 M3-to-M6 selector."""
 request=dict(radius_name=radius_name,depth=depth,zz='bottom',overhang=True)
 primary=prisms(request)
 other=prisms(dict(request,radius_name='m6',depth=depth if open_bottom else 5.5)) if selector else primary
 assert len(primary)==len(other)
 def value(a,b):
  return f'({a!r}) * native_unit' if not selector else f'((1 - {selector}) * {a!r} + {selector} * {b!r}) * native_unit'
 # Main hex first, then roof steps: keeps every active cut connected to its cavity.
 for a,b in sorted(zip(primary,other),key=lambda pair:-pair[0]['depth']):
  if open_bottom and a['z']<0:
   continue  # The extended pocket starts below the part; its lower roof is outside it.
  assert len(a['points'])==len(b['points'])
  sketch=design.sketch('OOBB_nut_pattern',f'({z}) + ({value(a["z"],b["z"])})')
  points=[]
  for (ax,ay),(bx,by) in zip(a['points'],b['points']):
   x,y=value(ax,bx),value(ay,by)
   px=f'({pitch}) + ({x}) * cos({rotation}) - ({y}) * sin({rotation})'
   py=f'({x}) * sin({rotation}) + ({y}) * cos({rotation})'
   points.append([f'({px}) * cos({phase}) - ({py}) * sin({phase})',f'({px}) * sin({phase}) + ({py}) * cos({phase})'])
  curves=design.line(points);design.pattern(curves,count)
  design.extrude(sketch,value(a['depth'],b['depth']),'cut',all_profiles=True)

COMPONENT={'name':'native_hardware_pattern','name_long':'Native OOBB hardware patterns','category':'Construction','kind':'service','shape_aliases':[],'entry_point':'cut','returns':'Native patterned nut cuts','description':'OOBB nut and roof prisms in native count-driven patterns.','variables':[]}
def describe():return copy.deepcopy(COMPONENT)
define=describe
action=cut

