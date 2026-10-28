"""Two seam-down casing halves with flat 3 mm OOBB and clamp tabs at the seam."""
import math
from gearbox_native import parts as p
from oobb_solidcraft import api as oobb


def configure(c,kwargs):
    defaults=dict(casing_tab_depth=3.,casing_tab_radius=45.,casing_tab_units=3,
                  casing_join_screw_length=6.,casing_join_nut_setback=.1,
                  casing_tab_wall_overlap=.8,casing_tab_join_offset=oobb.gv('osp')/2)
    for key,value in defaults.items():c[key]=kwargs.get(key,value)
    c['output_casing_split_z']=kwargs.get('output_casing_split_z',c['rotor_a_z']+c['rotor_thickness']+c['disc_gap']/2)
    c['casing_half_depths']=[c['output_casing_split_z']-c['casing_bottom_z'],c['housing_depth']-c['output_casing_split_z']]
    c['casing_tab_angles']=[0,90,180,270]
    c['housing_positions']=[tab_point(c,angle,c['casing_tab_join_offset']) for angle in c['casing_tab_angles']]
    c['housing_screw_length']=c['casing_join_screw_length'];c['housing_screw_style']='countersunk'
    c['case_screw_head_z']=c['output_casing_split_z']+c['casing_tab_depth']
    c['case_cover_post_bottom']=c['case_screw_head_z']-c['case_cover_post_floor']
    c['case_cover_depth']=max(c['front_retainer_depth']+c['bearing_cup_depth'],
        c['housing_depth']+c['front_retainer_depth']-c['case_cover_post_bottom'])
    c['case_nut_bottom']=c['output_casing_split_z']-c['casing_tab_depth']+c['casing_join_nut_setback']
    c['case_nut_top']=c['case_nut_bottom']+oobb.gv('nut_depth_m3','true')
    c['single_output_ring']=False;c['casing_requires_lobe_support']=False
    c['casing_print_orientation']='split_face_down'
    c['casing_tab_spacing']=oobb.gv('osp')
    c['casing_tab_width']=c['casing_tab_spacing']-1
    c['casing_tab_length']=c['casing_tab_units']*c['casing_tab_spacing']-1
    c['casing_tab_m6_offsets']=[(i-(c['casing_tab_units']-1)/2)*c['casing_tab_spacing'] for i in range(c['casing_tab_units'])]
    c['casing_tab_m3_offsets']=[(a+b)/2 for a,b in zip(c['casing_tab_m6_offsets'],c['casing_tab_m6_offsets'][1:])]
    c['casing_print_width']=2*(c['casing_tab_radius']+c['casing_tab_width']/2)
    # The existing continuous wall lies outside this radius below both seats.
    # Keep that complete annulus as the bearing-run backing, independent of lobes.
    c['casing_bearing_backing_radius']=c['casing_features']['bearing_lip']['radius']
    c['fastener_interfaces']['casing_clamp']=dict(size='m3',head='countersunk',length=c['housing_screw_length'],
        positions=c['housing_positions'],head_z=c['case_screw_head_z'],nut_bottom=c['case_nut_bottom'],nut_overhang=True)


def validate(c):
    seam=c['output_casing_split_z']
    assert c['rotor_a_z']+c['rotor_thickness']<=seam<=c['rotor_b_z'],'Casing split must remain between the discs'
    assert min(c['casing_half_depths'])>c['casing_tab_depth']
    assert c['casing_tab_units']>=2 and isinstance(c['casing_tab_units'],int)
    assert c['casing_tab_length']/2<c['housing_radius']-c['casing_tab_wall_overlap'],'Tab must fit a continuous curved root'
    assert c['casing_tab_join_offset'] in c['casing_tab_m3_offsets'],'Clamp must use an OOBB M3 midpoint hole'
    assert min(math.hypot(*xy) for xy in c['housing_positions'])-oobb.gv('nut_radius_m3','3dpr')>c['housing_radius'],'Clamp cuts must remain outside the casing'
    assert 0<c['housing_screw_length']<=35
    tip=c['case_screw_head_z']-c['housing_screw_length']
    assert seam-c['casing_tab_depth']<=tip<c['case_nut_bottom'],'Clamp screws must engage the full nut without protruding'
    assert c['case_nut_top']<seam-.2,'Keep a printable roof above each nut'
    assert c['casing_bore_radius']<=c['casing_bearing_backing_radius'],'Bearing lands need continuous wall backing'


def tab_point(c,angle,offset):
    a=math.radians(angle);r=c['casing_tab_radius']
    return [r*math.cos(a)-offset*math.sin(a),r*math.sin(a)+offset*math.cos(a)]


def tabs(t,c,height):
    spacing=c['casing_tab_spacing'];radius=c['casing_tab_radius'];bottom=0
    for angle in c['casing_tab_angles']:
        tab=p.blank()
        p.add(tab,'oobb_plate',pos=[radius,0,bottom],width=1,height=c['casing_tab_units'],depth=c['casing_tab_depth'],holes=False,zz='bottom')
        # Full tangential length joins the curved outer wall. A local circular
        # relief keeps this backing outside the working casing bore.
        inner=math.sqrt(c['housing_radius']**2-(c['casing_tab_length']/2)**2)-c['casing_tab_wall_overlap']
        neck=p.blank()
        p.add(neck,'oobb_cube',pos=[(inner+radius)/2,0,0],size=[radius-inner,c['casing_tab_length'],c['casing_tab_depth']],zz='bottom')
        p.hole(neck,c['housing_radius']-c['casing_tab_wall_overlap'],c['casing_tab_depth'])
        p.group(tab,neck)
        for y,size in [(v,'m6') for v in c['casing_tab_m6_offsets']]+[(v,'m3') for v in c['casing_tab_m3_offsets']]:
            p.add(tab,'oobb_hole','n',pos=[radius,y,bottom-.01],radius_name=size,depth=c['casing_tab_depth']+.02)
        p.group(t,tab,rot=[0,0,angle])


def pieces(c):
    from gearbox_native.simple import output_ring
    full=output_ring(c);lower_h,upper_h=c['casing_half_depths'];result={}
    extent=c['casing_print_width']*2
    for side,height in enumerate((lower_h,upper_h)):
        clipped=p.blank();p.group(clipped,full)
        if side==0:
            p.add(clipped,'oobb_cube','n',pos=[0,0,height],size=[extent,extent,upper_h+1],zz='bottom')
            t=p.blank();p.group(t,clipped,pos=[0,0,height],rot=[180,0,0])
        else:
            p.add(clipped,'oobb_cube','n',pos=[0,0,-1],size=[extent,extent,lower_h+1],zz='bottom')
            t=p.blank();p.group(t,clipped,pos=[0,0,-lower_h])
        tabs(t,c,height)
        for xy in c['housing_positions']:
            # Lower half prints flipped: mirror the selected M3 holes so both
            # halves meet at the same four world-space clamp positions.
            xy=xy if side else [xy[0],-xy[1]]
            if side:
                p.through(t,[xy],c['casing_tab_depth'],countersink=True)
            else:
                p.through(t,[xy],c['casing_tab_depth'])
                p.add(t,'oobb_nut','n',pos=[*xy,c['casing_tab_depth']+.1],radius_name='m3',
                    depth=oobb.gv('nut_depth_m3','true')+c['casing_join_nut_setback']+.1,zz='top',rot=[0,0,30],overhang=True)
        result['output_casing_'+('lower','upper')[side]]=dict(thing=t,width=c['casing_print_width'],depth=height,quantity=1)
    return result


def assembly_parts(c):
    return [dict(name='output_casing_lower',translation=[0,0,c['output_casing_split_z']],rotation_x=180,explode=[8,0,-2],member='output'),
            dict(name='output_casing_upper',translation=[0,0,c['output_casing_split_z']],rotation_x=0,explode=[8,0,5],member='output')]


def fit_samples(c):
    """Actual seam clamp flanges and one flat OOBB tab in their print poses."""
    result={}
    for side in (0,1):
        height=c['casing_tab_depth']
        t=p.blank()
        p.add(t,'oobb_plate',width=1,height=c['casing_tab_units'],depth=height,holes=False,zz='bottom')
        for y in c['casing_tab_m6_offsets']:p.through(t,[[0,y]],height,size='m6')
        for y in c['casing_tab_m3_offsets']:p.through(t,[[0,y]],height)
        selected=c['casing_tab_join_offset']*(1 if side else -1)
        if side:p.through(t,[[0,selected]],height,countersink=True)
        if not side:
            p.add(t,'oobb_nut','n',pos=[0,selected,height+.1],radius_name='m3',
                  depth=oobb.gv('nut_depth_m3','true')+c['casing_join_nut_setback']+.1,zz='top',rot=[0,0,30],overhang=True)
        result['fit_casing_clamp_'+('lower','upper')[side]]=t
    t=p.blank();height=min(c['casing_half_depths'])
    tabs(t,dict(c,casing_tab_angles=[0]),height)
    wall=p.blank();p.cylinder(wall,c['housing_radius'],height)
    p.hole(wall,c['housing_radius']-2,height)
    p.add(wall,'oobb_cube','n',pos=[-50,0,0],size=[150,150,height],zz='bottom')
    p.group(t,wall)
    result['fit_casing_OOBB_tab']=t
    return result
