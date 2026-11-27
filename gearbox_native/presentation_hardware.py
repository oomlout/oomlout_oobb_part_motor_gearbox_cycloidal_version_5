"""Parametric nominal hardware for presentation, independent of SCAD.

Purchased hardware is visualization geometry, not a native SolidCraft feature
history. Threads and rolling elements are omitted; bearing envelopes, fastener
sizes, holes, installed positions and motion follow the current native recipe.
"""
import math
from pathlib import Path


def build_hardware(c, folder, *, shape_cache=None):
    from oobb_solidcraft import api
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeCone, BRepPrimAPI_MakeBox, BRepPrimAPI_MakePrism
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.StlAPI import StlAPI_Writer
    from OCP.gp import gp_Pnt, gp_Vec, gp_Ax2, gp_Dir
    from OCP.BRepCheck import BRepCheck_Analyzer
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    steel=[.53,.58,.62,1]; dark=[.14,.18,.21,1]
    def cyl(r,h,z=0,xy=(0,0),direction=(0,0,1)):
        return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(*xy,z),gp_Dir(*direction)),r,h).Shape()
    def cut(a,b): return BRepAlgoAPI_Cut(a,b).Shape()
    def fuse(a,b): return BRepAlgoAPI_Fuse(a,b).Shape()
    def ring(ro,ri,h,z=0): return cut(cyl(ro,h,z),cyl(ri,h+.2,z-.1))
    def hexagon(radius,h,z=0):
        wire=BRepBuilderAPI_MakePolygon()
        for i in range(6):
            a=math.pi*i/3;wire.Add(gp_Pnt(radius*math.cos(a),radius*math.sin(a),z))
        wire.Close()
        return BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(wire.Wire()).Face(),gp_Vec(0,0,h)).Shape()
    models={}
    def save(name,shape,color=steel):
        assert BRepCheck_Analyzer(shape).IsValid(),name
        if shape_cache is not None:shape_cache[name]=shape
        BRepMesh_IncrementalMesh(shape,.03,False,.18,True).Perform()
        path=folder/(name+'.stl')
        writer=StlAPI_Writer();writer.ASCIIMode=False
        assert writer.Write(shape,str(path)),name
        asset=dict(stl=str(path),color=color)
        models[name]=[asset]
        return asset
    for kind in ('guide','eccentric','eccentric_top','eccentric_bottom','shaft','output'):
        if kind=='guide' and c.get('plain_guides'):continue
        spec=c['eccentric_bearings'][('bottom','top').index(kind.split('_')[1])] if kind.startswith('eccentric_') else c[kind+'_bearing'];ro,ri,h=spec['od']/2,spec['id']/2,spec['depth']
        shape=ring(ro,ri,h,-h/2)
        # Shallow recessed seal/race boundaries make the bearing readable.
        margin=(ro-ri)*.25
        for z in (-h/2,h/2-.16):
            shape=cut(shape,ring(ro-margin,ri+margin,.16,z))
        save('bearing_'+kind,shape)
    for size in sorted({'m3','m6',c['guide_bolt_radius_name']}):
        save('nut_'+size,cut(hexagon(api.gv('nut_radius_'+size,'true'),api.gv('nut_depth_'+size,'true')),
                            cyl(float(size[1:])/2,8,-1)))
    screw_defs=[('guide',c['guide_pin_diameter'],c['guide_bolt_length'],c.get('guide_screw_style','countersunk' if c.get('plain_guides') else 'hex')),
        ('hub',int(c['hub_bolt_radius_name'][1:]),c['hub_bolt_length'],'socket_cap' if c['hub_bolt_radius_name']=='m3' else 'hex'),
        ('housing',3,c['housing_screw_length'],c['housing_screw_style']),('flange',3,c['coupling_screw_length'],'socket_cap'),
        *[(n,3,c[k],'countersunk') for n,k in [('motor','motor_screw_length'),('disc','disc_join_length'),
            ('deck','deck_screw_length'),('post','post_screw_length'),('front_hub','front_hub_screw_length')]]]
    if c.get('post_fasteners'):
        screw_defs=[(n,d,length,'socket_cap' if n=='post' else style) for n,d,length,style in screw_defs]
    for name,d,length,style in screw_defs:
        shank=cyl(d/2,length,-length)
        if style=='hex': head=hexagon(api.gv('bolt_radius_m6','true'),api.gv('bolt_depth_m6','true'))
        elif style=='socket_cap':
            size='m'+format(d,'g');hr=api.gv('screw_socket_cap_radius_'+size,'true');hh=api.gv('screw_socket_cap_height_'+size,'true')
            head=cut(cyl(hr,hh),hexagon(d*.48,hh*.67,hh*.4))
        else:
            head=BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(0,0,-1.7),gp_Dir(0,0,1)),1.5,2.9,1.7).Shape()
            head=cut(head,hexagon(1.15,1.2,-.9))
        shape=fuse(shank,head)
        if style=='countersunk':shape=cut(shape,hexagon(1.15,1.2,-.9))
        save('screw_'+name,shape)
    save('post',ring(c['post_radius'],1.6,c['post_depth']))
    save('grub',cut(cyl(1.5,3,-3),hexagon(.85,1,-.8)))
    if c.get('direct_drive'):
        save('direct_grub',cut(cyl(1.5,c['direct_grub_length'],-c['direct_grub_length']),hexagon(.85,1,-.8)))
    h=c['coupling_length'];barrel=c['coupling_barrel_length']
    coupler=fuse(cyl(c['coupling_barrel_diameter']/2,barrel),cyl(c['coupling_diameter']/2,h-barrel,barrel))
    coupler=cut(coupler,cyl(2.55,h+.2,-.1))
    for xy in c['coupling_hole_positions']:
        coupler=cut(coupler,cyl(c['coupling_flange_hole_diameter']/2+.02,h-barrel+.2,barrel-.1,xy))
    for deg in c['coupling_grub_angles']:
        a=math.radians(deg)
        coupler=cut(coupler,cyl(1.52,c['coupling_barrel_diameter'],barrel-c['coupling_grub_from_barrel_top'],direction=(math.cos(a),math.sin(a),0)))
    save('coupler',coupler)
    w,d=c['motor_body_width'],c['motor_body_depth']
    body=BRepPrimAPI_MakeBox(gp_Pnt(-w/2,-w/2,-d+7),w,w,d-14).Shape()
    rear=BRepPrimAPI_MakeBox(gp_Pnt(-w/2,-w/2,-d),w,w,7).Shape()
    front=BRepPrimAPI_MakeBox(gp_Pnt(-w/2,-w/2,-7),w,w,7).Shape()
    for xy in c['motor_positions']:front=cut(front,cyl(1.5,3.1,-3,xy))
    front=fuse(front,cyl(c['motor_pilot_diameter']/2,c['motor_pilot_height']))
    shaft=cyl(2.5,c['motor_shaft_length'])
    models['motor']=[save('motor_body',body,dark),save('motor_rear',rear),save('motor_front',front),save('motor_shaft',shaft)]
    rows=[]
    def put(name,model,xyz,explode,member='fixed',rz=0,ry=0):
        rows.append(dict(name=name,assets=models[model],translation=xyz,explode=explode,member=member,
                         rotation_x=0,rotation_y=ry,rotation_z=rz,rotate_position=member in ('input','output'),
                         hardware=True,model=model))
    def array(prefix,model,positions,z,ex,member='fixed',rz=0):
        for i,xy in enumerate(positions):put(f'{prefix}_{i+1}',model,[*xy,z],ex,member,rz)
    for side in (0,1):
        ex=[0,0,-2.5 if side==0 else 3.5]
        if not c.get('plain_guides'):
            array(f'guide_bearing_{side}','bearing_guide',c['guide_positions'],c['guide_bearing_z'][side],ex,f'orbit_{side}')
        put(f'eccentric_bearing_{side}','bearing_eccentric_'+('bottom','top')[side],[0,0,c['eccentric_bearing_z'][side]],ex,f'orbit_{side}')
        put(f'output_bearing_{side}','bearing_output',[0,0,c['output_bearing_z'][side]],[0,0,-9 if side==0 else 12])
        z=c['rotor_a_z'] if side==0 else c['rotor_b_z']
        array(f'disc_screw_{side}','screw_disc',c['disc_join_positions'],z+c['disc_join_head_z'],[0,0,-.3 if side==0 else 5.7],f'orbit_{side}')
        array(f'disc_nut_{side}','nut_m3',c['disc_join_positions'],z+c['disc_join_nut_bottom'],[0,0,-4.7 if side==0 else 1.3],f'orbit_{side}')
    put('shaft_bearing','bearing_shaft',[0,0,c['shaft_bearing_z'][1]],[0,0,11])
    array('guide_bolt','screw_guide',c['guide_positions'],c['guide_bolt_head_z'],[0,0,8.8],rz=30)
    array('guide_nut','nut_'+c['guide_bolt_radius_name'],c['guide_positions'],c['guide_nut_bottom'],[0,0,-9.5 if c.get('simple_assembly') else -8],rz=30)
    for item,angle in zip(rows[-len(c['guide_positions']):],c['guide_nut_rotations']):item['rotation_z']=angle
    if not c.get('simple_assembly'):
        array('support_post','post',c['post_positions'],c['rear_support_top'],[0,0,6])
    for name,positions,head,nut,hexpl,nexpl in [
        ('post',c['post_positions'],c['post_screw_head_z'],c['post_nut_bottom'],8,-8),
        ('deck',c['deck_positions'],c['deck_screw_head_z'],.3,-6,-12),
        ('front_hub',c['deck_positions'],c['front_hub_screw_head_z'],c['front_hub_nut_bottom'],11.5,6.7)]:
        if c.get('simple_assembly') and not (name=='post' and c.get('post_fasteners')):continue
        array(name+'_screw','screw_'+name,positions,head,[0,0,hexpl])
        array(name+'_nut','nut_m3',positions,nut,[0,0,nexpl])
        if name=='post' and c.get('post_fasteners'):
            for row in rows[-len(positions):]:row['rotation_z']=c['post_fastener_nut_rotation']
    if not c.get('single_output_ring'):
        array('housing_screw','screw_housing',c['housing_positions'],c['case_screw_head_z'],[8 if c.get('split_output_casing') else 0,0,17],'output')
        array('housing_nut','nut_m3',c['housing_positions'],c['case_nut_bottom'],[8 if c.get('split_output_casing') else 10,0,-6],'output',rz=30 if c.get('split_output_casing') else 0)
    array('motor_screw','screw_motor',c['motor_positions'],c['motor_plate_depth'],[0,0,-10.5])
    put('motor','motor',[0,0,0],[0,0,-15])
    if c.get('direct_drive'):
        angle=c['direct_grub_angle'];a=math.radians(angle)
        for name,model,r in (('shaft_grub','direct_grub',c['direct_grub_outer_radius']),
                             ('shaft_grub_nut','nut_m3',c['direct_grub_nut_radius'])):
            put(name,model,[r*math.cos(a),r*math.sin(a),c['coupling_grub_z']],
                [-7+(2*math.cos(a) if name=='shaft_grub' else 0),2*math.sin(a),-3 if name=='shaft_grub' else -5],
                'input',angle,90)
    else:
        put('flanged_coupler','coupler',[0,0,c['coupling_z']],[-8,0,-10],'input')
        for i,deg in enumerate(c['coupling_grub_angles']):
            a=math.radians(deg);r=c['coupling_barrel_diameter']/2+.55
            put(f'grub_screw_{i+1}','grub',[r*math.cos(a),r*math.sin(a),c['coupling_grub_z']],
                [-8+.5*math.cos(a),.5*math.sin(a),-10],'input',deg,90)
        array('flange_screw','screw_flange',c['coupling_positions'],c['cap_screw_head_z'],[-8,0,-3.3],'input')
        if c.get('coupling_screw_up'):
            for item in rows[-len(c['coupling_positions']):]:item['rotation_x']=180
        for i,(xy,deg) in enumerate(zip(c['coupling_positions'],c['coupling_nut_rotations'])):
            a=math.radians(deg)
            put(f'flange_nut_{i+1}','nut_m3',[*xy,c['drive_roof_z']],[-8-math.cos(a),-math.sin(a),-7],'input',deg+c['coupling_nut_hex_rotation'])
    put('hub_bolt','screw_hub',[0,0,c['hub_bolt_head_z']],[-8,0,9],'input',30)
    put('hub_nut','nut_'+c['hub_bolt_radius_name'],[0,0,c['hub_nut_bottom']],[-8,0,-6],'input',30)
    return rows
