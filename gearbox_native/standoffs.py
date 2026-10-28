"""Slim screw-reinforced posts and matching locating sockets in the front carrier."""
from gearbox_native import parts as p
from oobb_solidcraft import api as oobb

def configure_early(c,kwargs):
    for key,default in (('post_radius','post_fastener_radius'),
                        ('post_pitch_radius','post_fastener_pitch_radius'),
                        ('post_register_radius','post_fastener_register_radius'),
                        ('post_register_depth','post_fastener_register_depth'),
                        ('post_screw_length','post_fastener_length')):
        c[key]=kwargs.get(key,c[default])

def configure(c,kwargs):
    c['post_screw_hole_radius']=1.5+c['post_fastener_screw_clearance']
    c['post_screw_head_z']=c['front_support_bottom']+c['post_fastener_socket_floor']
    c['post_nut_bottom']=kwargs.get('post_nut_bottom',c['post_screw_head_z']-c['post_screw_length']+.2)
    c['post_nut_top']=c['post_nut_bottom']+oobb.gv('nut_depth_m3','true')
    c['fastener_interfaces']['standoff_clamp']=dict(size='m3',head='socket_cap',
        length=c['post_screw_length'],head_z=c['post_screw_head_z'],nut_bottom=c['post_nut_bottom'],
        nut_rotation=c['post_fastener_nut_rotation'],positions=c['post_positions'],
        post_radius=c['post_radius'],bore_radius=c['post_screw_hole_radius'],
        register_radius=c['post_register_radius'],
        register_depth=c['post_register_depth'],register_clearance=c['post_register_clearance'])

def validate(c):
    checks=[
        (c['casing_lip_pass_clearance']>=.05-1e-9,'Discs must pass through the casing bearing lip during assembly'),
        (c['post_radius']-c['post_screw_hole_radius']>=c['post_fastener_min_wall']-1e-9,'Standoff screw bore leaves too little wall'),
        (c['post_register_radius']-c['post_screw_hole_radius']>=.5,'Locating peg screw bore leaves too little wall'),
        (c['post_radius']-c['post_register_radius']-c['post_register_clearance']>=.2,'Locating peg needs a seating shoulder'),
        (c['post_fastener_socket_floor']-c['post_register_depth']-c['post_register_clearance']>=.8,'Standoff socket head needs a roof above the locating peg'),
        (0<c['post_screw_length']<=35,'Standoff screws must be at most 35 mm'),
        (c['post_screw_head_z']-c['post_screw_length']>=.2,'Standoff screw tip must clear the motor face'),
        (c['post_nut_top']+.5<c['rear_support_top'],'Standoff nut needs a retaining roof'),
        (c['post_screw_head_z']+3<c['housing_depth'],'Standoff screw head must be recessed'),
        (c['post_pitch_radius']-c['post_hole_radius']-c['bearing_seats']['cycloid_drive']['seat_radius']>=c['minimum_wall'],'Standoff orbit hole approaches the eccentric bearing'),
    ]
    for good,message in checks:
        if not good:raise ValueError(message)

def cut_mount(t,c,positions=None):
    from gearbox_native.captured import nut
    for xy in c['post_positions'] if positions is None else positions:
        p.hole(t,c['post_screw_hole_radius'],c['integrated_mount_depth'],xy)
        nut(t,xy,c['post_nut_top']+.1,c['post_nut_top']+.2,'m3',c['post_fastener_nut_rotation'])

def cut_front(t,c,h,positions=None):
    for xy in c['post_positions'] if positions is None else positions:
        p.add(t,'oobb_screw_socket_cap','n',pos=[*xy,c['post_fastener_socket_floor']],
              radius_name='m3',depth=c['post_screw_length'],zz='none',nut_include=False,
              clearance='top',overhang=False)
        p.hole(t,oobb.gv('screw_socket_cap_radius_m3','3dpr'),h-c['post_fastener_socket_floor']+.1,
               xy,z=c['post_fastener_socket_floor'])

def fit_samples(c):
    lower=p.blank();h=c['rear_support_top']
    p.add(lower,'oobb_cube',size=[12,12,h],zz='bottom')
    p.cylinder(lower,c['post_radius'],c['front_support_bottom']-h,z=h)
    p.cylinder(lower,c['post_register_radius'],c['post_register_depth'],z=c['front_support_bottom'])
    cut_mount(lower,c,[[0,0]])
    upper=p.blank();h=c['housing_depth']-c['front_support_bottom']
    p.add(upper,'oobb_cube',size=[12,12,h],zz='bottom')
    p.hole(upper,c['post_register_radius']+c['post_register_clearance'],c['post_register_depth']+.15)
    cut_front(upper,c,h,[[0,0]])
    return dict(fit_M3_standoff_lower=lower,fit_M3_standoff_socket=upper)
