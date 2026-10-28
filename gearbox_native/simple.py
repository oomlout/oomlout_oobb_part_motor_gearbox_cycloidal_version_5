"""Consolidated V7 mechanism with named, shared interfaces and optional split casing.

The motor mount includes the rear guide carrier and the three spacer posts.
The front carrier includes its 6810 journal and central shaft bearing seat.
The lower eccentric includes the drive flange; M3 screws enter the purchased
coupler flange from underneath into outward-loading nuts in the printed drive.
"""
import math
from gearbox_native import parts as p, lobe, interfaces
from oobb_solidcraft import api as oobb


def configure(c, kwargs):
    c['single_output_ring']=True
    c['housing_positions']=[]
    c['hub_upper_end']=c['housing_depth']
    if c['base_grub']:
        c['hub_upper_end']=max(c['housing_depth'],c['hub_bolt_head_z']+3+c['direct_base_top_clearance'])
    c['guide_screw_style']='socket_cap'
    c['guide_nut_rotations']=[c['guide_nut_rotation']]*c['guide_pin_count']
    c['guide_socket_radius']=oobb.gv('screw_socket_cap_radius_'+c['guide_bolt_radius_name'],'3dpr')
    c['guide_bolt_head_z']=c['front_support_bottom']+c['guide_socket_floor']
    c['guide_nut_bottom']=kwargs.get('guide_nut_bottom',c['guide_bolt_head_z']-c['guide_bolt_length']+.2)
    c['guide_nut_top']=c['guide_nut_bottom']+oobb.gv('nut_depth_'+c['guide_bolt_radius_name'],'true')
    c['integrated_mount_depth']=c['front_support_bottom']+c['post_register_depth']
    c['coupling_screw_up']=True
    c['cap_screw_head_z']=c['coupling_flange_z']
    c['drive_roof_z']=c['drive_start']+.3
    c['drive_roof_top']=c['drive_roof_z']+oobb.gv('nut_depth_m3','true')
    c['deck_radius']=c['rear_bearing_shoulder_radius']
    interfaces.define(c)
    from gearbox_native.cycloid_equation import CycloidEquation
    c['cycloid_equation']=CycloidEquation(c['ring_pin_count'],c['pitch_radius'],c['radius_offset'],
        c['lobe_radius'],c['lobe_clearance']).definition()
    c['cycloid_equation']['native_representation']='Shared cycloidal_disc / parametric_profile; fixed sampled line segments with native formula links on all caps and walls'
    c['bearing_pass_radius']=c['bearing_seats']['output_casing']['through_radius']
    c['disc_swept_radius']=c['pitch_radius']+2*c['radius_offset']-c['lobe_radius']-c['lobe_clearance']
    c['casing_lip_pass_clearance']=c['bearing_pass_radius']-c['disc_swept_radius']
    c['eccentric_lip_radius']=c['bearing_seats']['cycloid_drive']['through_radius']
    c['eccentric_shoulder_radius']=c['bearing_seats']['cycloid_drive']['inner_shoulder_radius']
    seat=c['bearing_seats']['output_casing'];base=c['casing_bottom_z']
    c['casing_features']={
        'main_bore':dict(radius=c['casing_bore_radius'],bottom=base,top=c['housing_depth']),
        'rear_6810_seat':dict(radius=seat['seat_radius'],bottom=base,top=c['rear_bearing_top']+c['bearing_endplay']),
        'front_6810_seat':dict(radius=seat['seat_radius'],bottom=c['output_bearing_z'][1]-c['output_bearing']['depth']/2-c['bearing_endplay'],top=c['housing_depth']),
        'bearing_lip':dict(radius=seat['through_radius'],depth=c['minimum_wall']),
        'lobe_start_ramp':dict(bottom=c['rear_bearing_top']+c['bearing_endplay'],
            radius_bottom=seat['through_radius'],radius_top=c['pitch_radius']-c['lobe_radius']),
    }
    ramp=c['casing_features']['lobe_start_ramp']
    ramp['depth']=c['direct_base_ramp_depth'] if c['base_grub'] else ramp['radius_bottom']-ramp['radius_top']
    c['casing_requires_lobe_support']=ramp['depth']<ramp['radius_bottom']-ramp['radius_top']-1e-9
    c['overall_height']=max(c['housing_depth'],c['hub_upper_end'])
    c['fastener_interfaces']={
        'guide_clamp':dict(size=c['guide_bolt_radius_name'],head='socket_cap',length=c['guide_bolt_length'],
            head_z=c['guide_bolt_head_z'],nut_bottom=c['guide_nut_bottom'],positions=c['guide_positions']),
        'coupler_flange':dict(size='m3',head='socket_cap',length=c['coupling_screw_length'],
            head_z=c['cap_screw_head_z'],nut_bottom=c['drive_roof_z'],direction='up',positions=c['coupling_positions']),
        'central_hub':dict(size='m3',head='socket_cap',length=c['hub_bolt_length'],
            head_z=c['hub_bolt_head_z'],nut_bottom=c['hub_nut_bottom'],positions=[[0,0]]),
    }
    if c['direct_drive']:
        from gearbox_native.direct_drive import configure
        configure(c)
    if c['post_fasteners']:
        from gearbox_native.standoffs import configure
        configure(c,kwargs)
    if c.get('split_output_casing'):
        from gearbox_native.split_casing import configure
        configure(c,kwargs)


def validate(c):
    w=c['minimum_wall'];e=c['radius_offset'];seat=c['bearing_seats']['cycloid_drive']
    checks=[
        (c['drive_connection'] in ('flanged_coupler','grub_nut'),'Unknown drive connection'),
        (c['bearing_output']=='6810','Motor-side bearing is locked to 6810'),

        (0<c['guide_bolt_length']<=35,'Socket screws must be at most 35 mm'),
        (c['guide_pin_pitch_radius']+oobb.gv('hole_radius_'+c['guide_bolt_radius_name'],'3dpr')+w<=c['carrier_journal_radius'],'Guide shafts need to fit inside the 6810 journal'),
        (c['guide_pin_pitch_radius']-c['guide_hole_radius']-seat['seat_radius']>=w-1e-9,'Drive bearing and guide tracks need a connecting web'),
        (c['guide_nut_bottom']>=c['motor_plate_depth']+.5,'Guide nuts must stay above the motor mounting plate'),
        (c['guide_bolt_head_z']-c['guide_bolt_length']<=c['guide_nut_bottom'],'Guide screws must engage the bottom nuts'),
        (c['guide_bolt_head_z']+oobb.gv('screw_socket_cap_height_'+c['guide_bolt_radius_name'],'true')<c['housing_depth'],'Guide socket heads need top clearance'),
        (c['rotor_thickness']>=seat['seat_depth']+.8-1e-9,'Disc bearing needs a 0.8 mm retaining lip'),
        (c['guide_running_clearance']>=.15,'Plain tracks need radial running clearance'),
        (c['hub_key_radius']+c['hub_key_clearance']+e+1.4<=c['eccentric_journal_radius'],'Eccentric key wall is too thin'),
        (c['hub_bolt_head_z']+3<=c['hub_upper_end'],'Central socket head protrudes'),
        (c['direct_drive'] or c['cap_screw_head_z']+c['coupling_screw_length']>=c['drive_roof_top'],'Upward flange screws must pass through the nuts'),
        (c['direct_drive'] or c['drive_roof_top']+.6<=c['drive_flange_top'],'Flange nuts need a roof'),
        (c['direct_drive'] or c['coupling_pitch_diameter']/2-2.9>c['coupling_barrel_diameter']/2,'Flange socket heads touch the coupler barrel'),
        (c['pitch_radius']>c['ring_pin_count']*e,'Invalid cycloid eccentricity'),
        (c['pitch_radius']>=max(c['radius_calculation']['limits_mm'].values())-1e-9,'Pitch radius violates the profile or feature-clearance envelope'),
        (c['pitch_radius']+c['lobe_radius']-c['casing_bore_radius']>=.4-1e-9,'Lobes need attachment to the casing'),
        (c['bearing_cup_depth']>=c['output_bearing']['depth']+2*c['bearing_endplay'],'Casing bearing cup too short'),
        (c['housing_radius']-c['bearing_seats']['output_casing']['seat_radius']>=c['casing_wall']-1e-9,'Casing bearing seats need the requested radial wall'),
        (c['casing_features']['front_6810_seat']['bottom']>=c['rotor_b_z']+c['rotor_thickness']+c['axial_clearance'],'Front bearing relief must be above the discs'),
        (c['post_pitch_radius']+c['post_radius']<=c['carrier_journal_radius'],'Integral posts must grow from the motor journal'),
        (0<c['motor_screw_length']-c['motor_plate_depth']<=2.5,'Invalid NEMA screw engagement'),
    ]
    for label in ('bottom','top'):
        local=c['bearing_seats']['cycloid_'+label]
        checks.extend([
            (c['rotor_thickness']>=local['seat_depth']+.8-1e-9,label+' bearing needs a 0.8 mm retaining lip'),
            (c['guide_pin_pitch_radius']-c['guide_hole_radius']-local['seat_radius']>=w-1e-9,label+' bearing and guide tracks need a connecting web'),
            (c['post_pitch_radius']-c['post_hole_radius']-local['seat_radius']>=w-1e-9,label+' bearing and post tracks need a connecting web'),
            (c['hub_key_radius']+c['hub_key_clearance']+e+1.4<=local['journal_radius'],label+' bearing bore leaves an eccentric key wall too thin'),
        ])
    for valid,message in checks:
        if not valid:raise ValueError(message)
    if c['direct_drive']:
        from gearbox_native.direct_drive import validate
        validate(c)
    if c['post_fasteners']:
        from gearbox_native.standoffs import validate
        validate(c)
    if c.get('split_output_casing'):
        from gearbox_native.split_casing import validate
        validate(c)
    for xy in c['post_positions']:
        if min(math.dist(xy,q) for q in c['guide_positions'])<c['post_hole_radius']+c['guide_hole_radius']+w:
            raise ValueError('Named post and guide orbit holes overlap or lack a web')


def motor_mount(c):
    from gearbox_native.captured import nut
    t=p.blank();top=c['rear_support_top'];plate=c['motor_plate_depth']
    p.add(t,'oobb_plate',width=c['housing_width'],height=c['housing_width'],depth=plate,holes=False)
    p.cylinder(t,c['carrier_journal_radius'],top)
    p.cylinder(t,c['rear_bearing_shoulder_radius'],c['rear_bearing_lift'],plate)
    for xy in c['post_positions']:
        if c['post_fasteners']:
            p.cylinder(t,c['post_radius'],c['front_support_bottom']-top,top,xy=xy)
            p.cylinder(t,c['post_register_radius'],c['post_register_depth'],c['front_support_bottom'],xy=xy)
        else:
            p.cylinder(t,c['post_radius'],c['front_support_bottom']+c['post_register_depth']-top,top,xy=xy)
    p.hole(t,c['motor_pilot_diameter']/2+c['motor_pilot_clearance'],plate+.05)
    p.hole(t,c['drive_flange_radius']+c['drive_flange_clearance'],top-plate+.05,z=plate)
    p.add(t,'oobb_holes','n',width=c['housing_width'],height=c['housing_width'],depth=plate,
          holes=['perimeter'],radius_name='m6',both_holes=True)
    p.through(t,c['motor_positions'],plate,countersink=True)
    for xy in c['motor_positions']:p.hole(t,3,top-plate+.1,xy,z=plate)
    for xy,a in zip(c['guide_positions'],c['guide_nut_rotations']):
        p.through(t,[xy],top,size=c['guide_bolt_radius_name'])
        nut(t,xy,c['guide_nut_top']+.1,c['guide_nut_top']+.2,c['guide_bolt_radius_name'],a)
    if c['post_fasteners']:
        from gearbox_native.standoffs import cut_mount
        cut_mount(t,c)
    for angle in ([] if c['base_grub'] else c['coupling_grub_angles']):
        # Flat-roof tool windows print as short bridges and keep the native
        # cylindrical walls trimmed only by straight, axial boundaries.
        window=p.blank();length=c['carrier_journal_radius']+1
        p.add(window,'oobb_cube',pos=[length/2,0,c['coupling_grub_z']-c['grub_access_radius']],
              size=[length,2*c['grub_access_radius'],2*c['grub_access_radius']],zz='bottom')
        p.group(t,window,rot=[0,0,angle],typ='n')
    return t


def front_carrier(c):
    t=p.blank();h=c['housing_depth']-c['front_support_bottom']
    p.cylinder(t,c['rear_bearing_shoulder_radius'],c['flange_web'])
    p.cylinder(t,c['carrier_journal_radius'],h)
    interfaces.cut_bearing(t,c['bearing_seats']['front_shaft'],top=h,through_depth=h)
    for xy in c['guide_positions']:
        p.add(t,'oobb_screw_socket_cap','n',pos=[*xy,c['guide_socket_floor']],radius_name=c['guide_bolt_radius_name'],
              depth=c['guide_bolt_length'],zz='none',nut_include=False,clearance='top',overhang=False)
        # OOBB extends socket-head access only in 3dpr. The nominal assembly
        # must also have an open entry path above the recessed head.
        p.hole(t,c['guide_socket_radius'],h-c['guide_socket_floor']+.1,xy,z=c['guide_socket_floor'])
    for xy in c['post_positions']:
        r=c['post_register_radius'] if c['post_fasteners'] else c['post_radius']
        p.hole(t,r+c['post_register_clearance'],c['post_register_depth']+.15,xy)
    if c['post_fasteners']:
        from gearbox_native.standoffs import cut_front
        cut_front(t,c,h)
    return t


def rotor(c,side):
    c=interfaces.for_disc(c,side)
    t=p.blank();h=c['rotor_thickness'];shape=lobe.shared_component(c,h)
    # The unrotated cycloid is symmetric about X. Mirroring the upper disc
    # therefore negates its phase; keep that transform separate from its math.
    shape['rot']=[0,0,c['disc_phase_degrees'][side]*(-1 if side else 1)]
    oobb.append_full(t,**shape);interfaces.cut_cycloid_holes(t,c,h)
    if side:
        for item in t['components']:
            if 'pos' in item:item['pos'][1]*=-1
            if 'points' in item:item['points']=[[x,-y] for x,y in item['points']][::-1]
    return t


def drive_and_lower_eccentric(c):
    if c['direct_drive']:
        from gearbox_native.direct_drive import lower
        return lower(c)
    from gearbox_native.captured import shaft,nut
    t=p.blank();h=c['drive_flange_depth']
    p.cylinder(t,c['drive_flange_radius'],h)
    p.group(t,shaft(c,key_socket=False),[0,0,h])
    nd=oobb.gv('nut_depth_m3','true');start=c['drive_start']
    nut(t,[0,0],c['hub_nut_bottom']+nd+.1-start,c['hub_nut_bottom']+nd+.2-start,'m3',30)
    p.hole(t,oobb.gv('hole_radius_m3','3dpr'),c['hub_split_z']-start+c['hub_key_depth']+.1)
    p.coupling_nut_pockets(t,c,c['drive_roof_top']-start)
    for xy in c['coupling_positions']:
        p.hole(t,oobb.gv('hole_radius_m3','3dpr'),c['cap_screw_head_z']+c['coupling_screw_length']-start+.2,xy)
    return t


def output_ring(c):
    """Open one-piece rotating ring with bearing seats at the two ends."""
    t=p.blank();base=c['casing_bottom_z'];h=c['housing_depth']-base
    f=c['casing_features'];shell=p.blank()
    p.cylinder(shell,c['housing_radius'],h)
    p.hole(shell,f['main_bore']['radius'],h);p.group(t,shell)
    # Round working faces with straight backs joined continuously to the shell.
    for xy in c['ring_positions']:
        p.cylinder(t,c['lobe_radius'],h,xy=xy)
        angle=math.degrees(math.atan2(xy[1],xy[0]));back=p.blank()
        length=c['housing_radius']-c['pitch_radius']-.1
        p.add(back,'oobb_cube',pos=[c['pitch_radius']+length/2,0,0],
              size=[length,2*c['lobe_radius'],h],zz='bottom')
        p.group(t,back,rot=[0,0,angle])
    # Outer-race abutments are named separately from the working lobe band.
    for start in (f['rear_6810_seat']['top'],f['front_6810_seat']['bottom']-f['bearing_lip']['depth']):
        lip=p.blank();p.cylinder(lip,c['housing_radius'],f['bearing_lip']['depth'])
        p.hole(lip,f['bearing_lip']['radius'],f['bearing_lip']['depth'])
        p.group(t,lip,[0,0,start-base])
    for name in ('rear_6810_seat','front_6810_seat'):
        seat=f[name];p.hole(t,seat['radius'],seat['top']-seat['bottom']+.02,z=seat['bottom']-base-.01)
    ramp=f['lobe_start_ramp'];depth=max(.01,ramp['depth'])
    # Coaxial ledges keep the native curves circular. A shortened transition
    # requires slicer support; the raised layout retains its 45-degree envelope.
    steps=max(1,math.ceil(depth/c['casing_ramp_layer_height']))
    for i in range(steps):
        z=i*depth/steps
        radius=ramp['radius_bottom']-(ramp['radius_bottom']-ramp['radius_top'])*i/steps
        p.hole(t,radius,depth/steps+.01,z=ramp['bottom']-base+z-.005)
    # Above the discs only the outer race may meet the front bearing's lip.
    p.hole(t,f['bearing_lip']['radius'],c['housing_depth']-c['front_support_bottom'],
           z=c['front_support_bottom']-base)
    return t


def build(c):
    from gearbox_native.captured import shaft
    result={}
    def put(name,thing,width,depth):result[name]=dict(thing=thing,width=width,depth=depth,quantity=1)
    cw=max(2*c['housing_radius'],2*c['housing_mount_offset']+2*c['housing_lug_radius'])
    put('motor_mount',motor_mount(c),max(cw,c['housing_width']*15-1),c['integrated_mount_depth'])
    if c.get('split_output_casing'):
        from gearbox_native.split_casing import pieces
        result.update(pieces(c))
    else:put('output_casing',output_ring(c),2*c['housing_radius'],c['housing_depth']-c['casing_bottom_z'])
    put('pin_front',front_carrier(c),2*c['rear_bearing_shoulder_radius'],c['housing_depth']-c['front_support_bottom'])
    for side,letter in enumerate(('a','b')):put('rotor_'+letter,rotor(c,side),2*c['pitch_radius'],c['rotor_thickness'])
    lower_interface=interfaces.for_disc(c,0)
    put('eccentric_hub_lower',drive_and_lower_eccentric(c),2*max(c['drive_flange_radius'],lower_interface['eccentric_shoulder_radius']+c['radius_offset']),c['hub_split_z']-c['drive_start']+c['hub_key_depth']+.02)
    if c['direct_drive']:
        from gearbox_native.direct_drive import upper
        upper_geometry=upper(c)
    else:upper_geometry=shaft(c,True)
    put('eccentric_hub_upper',upper_geometry,2*(interfaces.for_disc(c,1)['eccentric_shoulder_radius']+c['radius_offset']),c['hub_upper_end']-c['hub_split_z'])
    from gearbox_native.geometry import continuous_negative_sections,subtract_axial_sections
    for piece in result.values():
        continuous_negative_sections(piece['thing']);subtract_axial_sections(piece['thing'])
    if c['direct_drive']:
        # Print-clearance cuts can leave a redundant OCCT seam across the
        # radial window. Reparameterize only the coaxial circular surfaces;
        # a rotation about their own axis changes no material or dimensions.
        for item in result['motor_mount']['thing']['components']:
            if (item.get('inclusion')=='3dpr' and item.get('shape') in ('cylinder','revolved_profile')
                    and not any(item.get('pos',[0,0,0])[:2])):
                item['rot']=[0,0,c['direct_grub_angle']+90]
    return result


def assembly_parts(c):
    rows=[dict(name=n,translation=xyz,rotation_x=rx,explode=ex,member=member) for n,xyz,rx,ex,member in (
        ('motor_mount',[0,0,0],0,[0,0,-8],'fixed'),
        ('pin_front',[0,0,c['front_support_bottom']],0,[0,0,8],'fixed'),
        ('output_casing',[0,0,c['casing_bottom_z']],0,[8,0,0],'output'),
        ('rotor_a',[0,0,c['rotor_a_z']],0,[0,0,-2],'orbit_0'),
        ('rotor_b',[0,0,c['rotor_b_z']+c['rotor_thickness']],180,[0,0,3],'orbit_1'),
        ('eccentric_hub_lower',[0,0,c['drive_start']],0,[-7,0,-3],'input'),
        ('eccentric_hub_upper',[0,0,c['hub_split_z']],0,[-7,0,4],'input'),
    )]
    if c.get('split_output_casing'):
        from gearbox_native.split_casing import assembly_parts as casing_parts
        rows=[row for row in rows if row['name']!='output_casing']+casing_parts(c)
    return rows
