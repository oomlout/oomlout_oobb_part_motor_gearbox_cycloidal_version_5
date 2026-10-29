"""V8 native three-piece casing and configurable internal guide system."""
import argparse,json,math,zipfile
from pathlib import Path
from oobb_solidcraft.registry import discover
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft import api as oobb
from gearbox_native import native_v7 as base
from gearbox_native.project import PROJECT
from gearbox_native.acceptance import health_check

SCRATCH=Path('D:/codex_builds/gearbox_v8_three_piece_20261028')
EXTRA=[
 ('guide_screw_length','20 mm','mm',True,'Under-head guide screw length; 25 mm seats the compact variant nuts below its bearing.'),
 ('automatic_internal_positions','1','',True,'1 shrinks guide/standoff positions to their clearance limits; 0 uses manual radii.'),
 ('guide_outer_radius','1.5 mm','mm',True,'Outside RADIUS of guide sleeve/spacer; same as screw radius means no sleeve.'),
 ('guide_count','6','',True,'Number of equally spaced guide screws, integer 3 to 12.'),
 ('posts_enabled','ceil(min(1, standoff_radius / (1 mm)))','',False,''),
 ('guide_phase','180 deg * (1 + 2 * max(0, 1 - abs(guide_count - 3 * floor(guide_count / 3)))) / (3 * guide_count)','deg',False,''),
 ('guide_clearance_radius','guide_outer_radius + eccentricity + 0.2 mm','mm',False,''),
 ('post_clearance_radius','standoff_radius + eccentricity + 0.15 mm','mm',False,''),
 ('guide_minimum_pitch','max(max(bottom_od, top_od) / 2 + seat_clearance + minimum_web + guide_clearance_radius, (guide_clearance_radius + minimum_web / 2) / sin(180 deg / guide_count))','mm',False,''),
 ('guide_pitch','automatic_internal_positions * guide_minimum_pitch + (1 - automatic_internal_positions) * guide_pitch_radius','mm',False,''),
 ('post_minimum_pitch','max(max(bottom_od, top_od) / 2 + seat_clearance + minimum_web + post_clearance_radius, guide_pitch * cos(guide_phase) + sqrt(max((0 mm)^2, (guide_clearance_radius + post_clearance_radius + minimum_web)^2 - (guide_pitch * sin(guide_phase))^2)))','mm',False,''),
 ('post_pitch','automatic_internal_positions * post_minimum_pitch + (1 - automatic_internal_positions) * standoff_pitch_radius','mm',False,''),
 ('post_construction_pitch','posts_enabled * post_pitch + (1 - posts_enabled) * 4 mm','mm',False,''),
 ('post_construction_radius','posts_enabled * standoff_radius + (1 - posts_enabled) * 2.7 mm','mm',False,''),
 ('post_hole_radius','posts_enabled * post_clearance_radius + (1 - posts_enabled) * 1 mm','mm',False,''),
 ('internal_switch_guard','sqrt(-abs(automatic_internal_positions - floor(automatic_internal_positions))) + sqrt(automatic_internal_positions * (1 - automatic_internal_positions))','',False,''),
 ('guide_count_guard','sqrt(-abs(guide_count-floor(guide_count))) + sqrt(min(guide_count-3,12-guide_count))','',False,''),
 ('guide_spacer_guard','sqrt((guide_outer_radius-guide_radius)/(1 mm))','',False,''),
]
OVERRIDES={
 'reduction_range_guard':'sqrt(min(reduction - 10, 24 - reduction))',
 'guide_orbit_radius':'guide_clearance_radius',
 'guide_nut_roof_guard':'sqrt((rear_support_top - front_z - 1.4 mm + guide_screw_length - 0.2 mm - guide_nut_depth - 0.5 mm) / (1 mm))',
 'feature_pitch_limit':'max(guide_pitch + guide_orbit_radius, posts_enabled * (post_pitch + post_orbit_radius)) + minimum_web + eccentricity + contact_radius + profile_clearance',
 'rotor_a_z':'max(drive_start + drive_depth + 0.5 mm, lower_split_z + 0.3 mm)',
 'rear_support_top':'rotor_a_z - 0.5 mm',
 'post_web_guard':'sqrt(posts_enabled * (post_pitch - post_orbit_radius - max(bottom_od, top_od) / 2 - seat_clearance - minimum_web + 0.00000001 mm) / (1 mm))',
 'post_wall_guard':'sqrt(min(standoff_radius / (1 mm), posts_enabled * (standoff_radius - 2.5 mm) / (1 mm)))',
 'track_separation_guard':'sqrt(posts_enabled * (sqrt(guide_pitch^2 + post_pitch^2 - 2 * guide_pitch * post_pitch * cos(guide_phase)) - guide_orbit_radius - post_orbit_radius - minimum_web + 0.00000001 mm) / (1 mm))',
 'post_screw_tip_guard':'sqrt(posts_enabled * (front_z + 2.6 mm - 25 mm - 0.2 mm) / (1 mm))',
 'fixed_pin_envelope_margin':'(carrier_radius - max(guide_pitch + guide_outer_radius + minimum_web, posts_enabled * (post_pitch + standoff_radius))) / (1 mm)',
 'guide_web_guard':'sqrt((guide_pitch - guide_orbit_radius - max(bottom_od, top_od) / 2 - seat_clearance - minimum_web + 0.00000001 mm)/(1 mm))',
 'tab_root':'sqrt(casing_radius^2 - (22 mm)^2) - 0.8 mm',
 'layout_scale':'max(1, (2 * (tab_radius + 7 mm) + 6 mm) / (110 mm))',
}

def parameters(d):
 with zipfile.ZipFile(PROJECT/'gearbox_controls.solidcraft') as z:doc=json.loads(z.read('document.json'))
 saved={p['name']:p['expr'] for p in doc['params'] if p['name'] in doc['favorites']}
 class Proxy:
  def parameter(self,name,expression,**kwargs):
   if name=='ring_count':
    # Dependencies already exist here except constants defined below; add those first.
    for n,e,u in [('seat_clearance','0.1 mm','mm'),('minimum_web','2 mm','mm')]:d.parameter(n,e,unit=u)
    for n,e,u,f,c in EXTRA:d.parameter(n,saved.get(n,e) if f else e,unit=u,favorite=f,comment=c)
   if name in ('seat_clearance','minimum_web'):return
   if name=='rotor_a_z':d.parameter('lower_split_z','rear_seat_top + 1 mm')
   if name=='tab_radius':
    for n,e in [('upper_split_z','front_z - 0.2 mm'),('lobe_band_radius','pitch + contact_radius + casing_wall'),
                ('join_tip_z','casing_bottom + 1.5 mm'),('join_screw_length','5 mm * floor((housing_top - join_tip_z - 3.2 mm) / (5 mm))'),
                ('join_head_seat','join_tip_z + join_screw_length'),('join_head_recess','housing_top - join_head_seat'),
                ('join_head_web_guard','sqrt((join_head_seat - upper_split_z - 1.0 mm) / (1 mm))')]:
     d.parameter(n,e,unit='' if n.endswith('guard') else 'mm',comment='Derived casing clamp dimension; standard M3 screw length is a multiple of 5 mm.')
   expression=OVERRIDES.get(name,expression)
   if name not in saved and name not in OVERRIDES:
    expression=expression.replace('guide_pitch_radius','guide_pitch').replace('standoff_pitch_radius','post_pitch')
   if kwargs.get('favorite') and name in saved:expression=saved[name]
   if name=='standoff_radius':kwargs['comment']='Standoff body radius; 0 removes posts, registers, screws and rotor clearance holes.'
   if name=='guide_radius':kwargs['comment']='Guide screw RADIUS: 1.5 mm for M3 or 3 mm for M6. Set guide_outer_radius for sleeves.'
   if name in ('guide_pitch_radius','standoff_pitch_radius'):kwargs['comment']='Manual position radius; used when automatic_internal_positions=0.'
   if name=='print_layout':kwargs['comment']='1 lays out all nine printable parts; 0 assembled/exploded.'
   d.parameter(name,expression,**kwargs)
 base.parameters(Proxy())

def patterned_holes(d,radius,depth,z=0,pitch='guide_pitch',count='guide_count',phase='guide_phase',name='guide_holes'):
 sketch=d.sketch(name,z)
 curves=d.circle(radius,[f'({pitch}) * cos({phase})',f'({pitch}) * sin({phase})'])
 d.pattern(curves,count);d.extrude(sketch,depth,'cut',all_profiles=True)

def rotor(d,side,geometry):
 name='rotor_'+('a','b')[side];bearing=('bottom','top')[side];d.component(name)
 api=discover().module('parametric_profile');setup=api.parameter_commands(geometry,prefix=name)
 aliases={'pitch_radius':'pitch','eccentricity':'eccentricity','roller_radius':'contact_radius','clearance':'profile_clearance','ring_pin_count':'ring_count'}
 for entry in setup['commands']:
  for key,native in setup['parameters'].items():
   if entry['params']['name']==native:entry['params']['expression']=aliases[key]
  d.do(entry['command'],**entry['params'])
 sketch=d.sketch('equation');curves=d.line(api.coordinate_expressions(geometry,prefix=name),closed=False)
 d.pattern(curves,'ring_count - 1');d.extrude(sketch,'disc_thickness','new',all_profiles=True)
 if side:d.move(axis=[0,0,1],angle='profile_phase')
 patterned_holes(d,'guide_orbit_radius','disc_thickness',phase='-guide_phase' if side else 'guide_phase')
 patterned_holes(d,'post_hole_radius','disc_thickness',pitch='post_construction_pitch',count='3',phase='0 deg',name='optional_post_tracks')
 d.holes(f'{bearing}_od / 2 - 0.8 mm','disc_thickness',name='bearing_retaining_lip')
 d.holes(f'{bearing}_od / 2 + seat_clearance',f'{bearing}_seat_depth + 0.01 mm',z=f'disc_thickness - {bearing}_seat_depth',name='bearing_seat')

def motor_mount(d):
 d.component('motor_mount');sketch=d.sketch('OOBB_mount')
 d.rounded_rectangle('-motor_plate_half','motor_plate_half','-motor_plate_half','motor_plate_half',5);d.extrude(sketch,'motor_plate_depth','new')
 d.cylinder('carrier_radius','rear_support_top',name='casing_inner_journal')
 d.cylinder('carrier_shoulder_radius',.3,z='motor_plate_depth',name='casing_inner_shoulder')
 posts=base.polar('post_construction_pitch',3)
 for xy in posts:
  d.cylinder('post_construction_radius','posts_enabled * (front_z - rear_support_top) + (1 - posts_enabled) * 1 mm',z='posts_enabled * rear_support_top + (1 - posts_enabled) * 1 mm',xy=xy,name='optional_standoff')
  d.cylinder(2.3,1.6,z='posts_enabled * front_z + (1 - posts_enabled) * 1 mm',xy=xy,name='optional_register')
 # All disabled post details lie inside the subsequently removed motor pilot.
 d.holes(1.7,'front_z + 1.6 mm',positions=posts,name='optional_post_screws')
 for xy in posts:base.nut(d,xy,'front_z + 2.6 mm - 25 mm + 0.2 mm + 2.5 mm + 0.1 mm')
 patterned_holes(d,'guide_bore_radius','rear_support_top')
 discover().module('native_hardware_pattern').cut(d,pitch='guide_pitch',count='guide_count',phase='guide_phase',z='front_z + 1.4 mm - guide_screw_length + 0.2 mm + 0.1 mm + guide_nut_depth - 40 mm',depth=40,selector='guide_m6',rotation='30 deg',open_bottom=True)
 d.holes(11.2,'motor_plate_depth + 0.05 mm',name='NEMA17_pilot')
 d.holes(11.25,'rear_support_top - motor_plate_depth + 0.05 mm',z='motor_plate_depth',name='drive_clearance')
 d.oobb_cut('oobb_holes',width=5,height=5,depth=4,holes=['perimeter'],radius_name='m6',both_holes=True)
 # The access shaft clears the complete countersunk head. A narrower access
 # leaves a radial shelf exactly at the motor-plate/journal union plane.
 for xy in ((15.5,15.5),(-15.5,15.5),(-15.5,-15.5),(15.5,-15.5)):
  d.oobb_cut('oobb_screw_countersunk',position=[*xy,'motor_plate_depth - 0.02 mm'],radius_name='m3',depth=4.02,zz='top',nut_include=False,overhang=False,coaxial_extension=(oobb.gv('screw_countersunk_radius_m3','3dpr'),0,7.6))

def front_carrier(d):
 d.component('pin_front');d.cylinder('carrier_shoulder_radius',.8,operation='new',name='bearing_shoulder')
 d.cylinder('carrier_radius','front_depth',name='casing_inner_journal')
 posts=base.polar('post_construction_pitch',3)
 d.holes(2.45,1.75,positions=posts,name='optional_registers');d.holes(1.8,'front_depth',positions=posts,name='optional_post_screws')
 d.holes(3,'front_depth - 2.6 mm + 0.1 mm',z=2.6,positions=posts,name='optional_post_heads')
 patterned_holes(d,'guide_bore_radius','front_depth')
 patterned_holes(d,'guide_head_radius','front_depth - 1.4 mm + 0.1 mm',z=1.4,name='guide_socket_access')
 d.holes(7.5,'front_depth',name='6701_retaining_lip');d.holes(9.1,4.2,z='front_depth - 4.2 mm',name='6701_seat')

BOUNDS={'lower':('casing_bottom','lower_split_z','casing_radius'),
        'lobes':('lower_split_z','upper_split_z','lobe_band_radius'),
        'upper':('upper_split_z','housing_top','casing_radius')}

def output_piece(d,side):
 z,end,radius=BOUNDS[side];depth=f'({end}) - ({z})';name='output_casing_'+side;d.component(name)
 if side=='lobes':
  d.cylinder(radius,depth,z=z,inner='casing_bore',operation='new',name='straight_lobe_band')
  sketch=d.sketch('ring_contacts',z);curves=d.circle('contact_radius',('pitch',0));d.pattern(curves,'ring_count');d.extrude(sketch,depth,all_profiles=True)
  sketch=d.sketch('contact_backs',z);curves=d.line([['pitch','-contact_radius'],[f'{radius} - 0.1 mm','-contact_radius'],[f'{radius} - 0.1 mm','contact_radius'],['pitch','contact_radius']]);d.pattern(curves,'ring_count');d.extrude(sketch,depth,all_profiles=True)
 else:
  d.cylinder(radius,depth,z=z,inner='bearing_lip_radius',operation='new',name='bearing_holder')
  if side=='lower':d.holes('casing_od / 2 + seat_clearance','rear_seat_top - casing_bottom + 0.01 mm',z='casing_bottom - 0.01 mm',name='rear_bearing_seat')
  else:d.holes('casing_od / 2 + seat_clearance','housing_top - front_seat_bottom + 0.02 mm',z='front_seat_bottom',name='front_bearing_seat')
 shell=d.body
 for angle in (0,90,180,270):
  d.body=shell+f'_tab_{angle}';sketch=d.sketch('OOBB_three_wide_full_depth',z)
  d.rounded_rectangle('tab_radius - 7 mm','tab_radius + 7 mm',-22,22,5);d.extrude(sketch,depth,'new')
  root=f'sqrt(({radius})^2 - (22 mm)^2) - 0.8 mm'
  d.box(root,'tab_radius',-22,22,depth,z=z,name='full_length_connection')
  d.holes(f'({radius}) - 0.8 mm',depth,z=z,name='clear_internal_cavity')
  # A small corner pad holds a half-grid clamp hole inside the existing footprint.
  d.cylinder(5.5,depth,z=z,xy=['tab_radius - 7.5 mm','22.5 mm'],name='half_grid_clamp_pad')
  d.move(axis=[0,0,1],angle=f'{angle} deg')
  tool=d.body;d.body=shell;d.do('solid.combine',target=shell,tools=[tool],operation='join')
 # Cut hardware after all four tabs are joined: adjacent pads cannot refill holes.
 for angle in (0,90,180,270):
  a=math.radians(angle);co,si=round(math.cos(a)),round(math.sin(a))
  def xy(y,offset=0):return [f'(tab_radius + {offset} mm) * {co} - ({y} mm) * {si}',f'(tab_radius + {offset} mm) * {si} + ({y} mm) * {co}']
  join=xy(22.5,-7.5)
  d.holes(oobb.gv('hole_radius_m6','3dpr'),f'({depth}) + 0.02 mm',z=f'({z}) - 0.01 mm',positions=[xy(y) for y in (-15,0,15)],name='OOBB_M6_through')
  d.holes(oobb.gv('hole_radius_m3','3dpr'),f'({depth}) + 0.02 mm',z=f'({z}) - 0.01 mm',positions=[xy(-7.5),xy(7.5),join],name='OOBB_M3_through')
  if side=='upper':
   d.holes(oobb.gv('screw_socket_cap_radius_m3','3dpr'),'housing_top - join_head_seat + 0.01 mm',z='join_head_seat',positions=[join],name='recessed_M3_socket_cap')
  elif side=='lower':
   for y in (-15,0,15):
    d.oobb_cut('oobb_nut',position=[*xy(y),'casing_bottom + 5.5 mm + 1 mm'],radius_name='m6',depth=6.6,zz='bottom',rotation=[180,0,30],overhang=True)
   d.oobb_cut('oobb_nut',position=[*join,'casing_bottom + 4.7 mm'],radius_name='m3',depth=4.8,zz='bottom',rotation=[180,0,30],overhang=True)


PRINT_POSITIONS={'output_casing_lower':(55,55),'output_casing_lobes':(165,55),'output_casing_upper':(275,55),
 'motor_mount':(40,153),'rotor_a':(115,150),'rotor_b':(185,150),'pin_front':(30,224),'eccentric_hub_lower':(78,215),'eccentric_hub_upper':(108,215)}

def place(d,name):
 if name not in ('output_casing_lower','output_casing_lobes','output_casing_upper'):
  return base.place(d,name)
 d.body=name;side=name.removeprefix('output_casing_');z,end,_=BOUNDS[side];x,y=PRINT_POSITIONS[name]
 if side=='lower':d.move(axis=[1,0,0],angle='180 deg * print_layout');pz=end
 else:pz=f'-({z})'
 d.move(axis=[0,0,1],angle='output_angle * (1-print_layout)')
 layer={'lower':1,'lobes':4,'upper':7}[side]
 d.move(translate=[f'print_layout * layout_scale * {x} mm',f'print_layout * layout_scale * {y} mm',f'(1-print_layout) * {layer} * explode + print_layout * ({pz})'])

BUILDERS={'motor_mount':motor_mount,'pin_front':front_carrier,'eccentric_hub_lower':base.lower_hub,'eccentric_hub_upper':base.upper_hub,
 'output_casing_lower':lambda d:output_piece(d,'lower'),'output_casing_lobes':lambda d:output_piece(d,'lobes'),'output_casing_upper':lambda d:output_piece(d,'upper')}

def profile_geometry():
 return discover().module('cycloidal_pattern').profile(dict(ring_pin_count=20,pitch_radius=31.15,eccentricity=1.4,roller_radius=3.,clearance=.2),validation_cases=[dict(ring_pin_count=n,pitch_radius=p,eccentricity=e) for n,p,e in [(10,23.9,.9),(10,26.4,1.4),(16,29.6,1.4),(20,31.15,1.4)]] + [dict(ring_pin_count=10,pitch_radius=22.4,eccentricity=.9,roller_radius=1.5)])

def run(name,piece=None):
 out=PROJECT/'build/native_v8'/name;out.mkdir(parents=True,exist_ok=False)
 logs=SCRATCH/name;logs.mkdir(parents=True,exist_ok=False)
 geometry=profile_geometry();(out/'profile.json').write_text(json.dumps(geometry),encoding='utf-8')
 with MCPClient(logs/'author',allow_path=PROJECT,timeout=600) as client:
  d=discover().module('native_design').Design(client);parameters(d)
  if piece in ('rotor_a','rotor_b'):rotor(d,piece=='rotor_b',geometry)
  elif piece:BUILDERS[piece](d)
  else:
   for side in (0,1):print('Rotor',side,flush=True);rotor(d,side,geometry)
   for part,fn in BUILDERS.items():print('Building',part,flush=True);fn(d)
   for part in PRINT_POSITIONS:place(d,part)
  health_check(client,logs/'health.json')
  require_ok(client.call('save',dict(path=str(out/'gearbox.solidcraft'))))
  require_ok(client.call('export',dict(path=str(out/'gearbox.step'))))
  require_ok(client.call('export',dict(path=str(out/'gearbox.stl'))))
  (logs/'commands.json').write_text(json.dumps(d.commands),encoding='utf-8')
 print('Saved',out,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--piece',choices=[*BUILDERS,'rotor_a','rotor_b']);a=p.parse_args();run(a.name,a.piece)
