"""Read-only core insertion and motor-tube driver audit for the guide."""
import json,math
import numpy as np
from gearbox_native.nema17_depth40_guide import ROOT,PART,BUILD
from gearbox_native.nema17_end_caps_checks import named_shapes
from gearbox_native.nema17_outputs import MotorAudit,overlap
from gearbox_native.verify_assembly_sequence import bounds,intersect_boxes
from gearbox_native.exact_geometry import _move,_polygon


def main():
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder,BRepPrimAPI_MakePrism
    from OCP.gp import gp_Ax2,gp_Pnt,gp_Dir,gp_Vec
    views=ROOT/'build/nema17_separate_joiners_r2/views'
    report=json.loads((PART/'native_export_verification.json').read_text());v=report['parameters']
    health=json.loads((views/'assembled_health.json').read_text())
    shapes=named_shapes(PART/'true.step',health)
    for alias,original in [('circular_top','output_circle_plate'),('circular_bottom','output_circle_rear_plate')]:
        b=bounds(shapes[original]);shapes[alias]=_move(shapes[original],'translate',[-(b[0]+b[3])/2,0,0])
    a=MotorAudit.__new__(MotorAudit);a.shapes=shapes;a.boxes={n:bounds(s) for n,s in shapes.items()}
    a.cache={};a.records=[];a.boolean_checks=0;a.slivers=[];a.bore_exclusions=[];a.through_bores={}
    # Physical tool envelope: 2.5 mm AF short leg, 8 mm insertion-end length;
    # round radial arm is a conservative 2.9 mm diameter outside the socket.
    keys=[]
    keep=[n for n in shapes if n not in ('output_circle_plate','output_circle_rear_plate','output_lower_row_plate','output_lower_row_rear_plate','output_plain_circle_plate')
          and not n.startswith(('front_cover_','rear_cover_','rear_output_','hardware_endcap_'))]
    for i in (0,2,4):
        name=f'hardware_cage_M3x16_{i}';b=a.boxes[name];x,y=(b[:2]+b[3:5])/2;z=b[5]-1.2
        phase=0
        pts=[(1.25/math.cos(math.pi/6)*math.cos(phase+j*math.pi/3),1.25/math.cos(math.pi/6)*math.sin(phase+j*math.pi/3)) for j in range(6)]
        leg=BRepPrimAPI_MakePrism(_polygon(pts),gp_Vec(0,0,8)).Shape();leg=_move(leg,'translate',[x,y,z])
        radial=np.array([x,y,0.]);radial/=np.linalg.norm(radial)
        arm=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z+7),gp_Dir(*radial)),1.45,45).Shape()
        hits=[]
        for tool in (leg,arm):
            bb=bounds(tool)
            for other in keep:
                if not intersect_boxes(bb,a.boxes[other]):continue
                amount=overlap(tool,shapes[other])
                if amount>.03:hits.append(dict(part=other,volume=amount))
        keys.append(dict(screw=name,short_leg_mm=8,across_flats_mm=2.5,clear=not hits,blocked=hits,axis_mm=[float(x),float(y),float(z)]))
    (BUILD/'tube_tool_access.json').write_text(json.dumps(keys,indent=2))
    assert all(k['clear'] for k in keys),keys
    print('SHORT MOTOR TUBE KEY ACCESS PASSED',flush=True)
    # Retain the full source's geometry, but only build the pre-motor core here.
    temp=_move(shapes['hardware_shaft_M3x35_lower'],'rotate',[180,0,0])
    temp=_move(temp,'translate',[0,-2*v['shaft_tie_pitch'],v['shaft_head_depth']+v['stack_height']-v['shaft_nut_depth']])
    shapes['temporary_shaft_tie']=temp;a.boxes['temporary_shaft_tie']=bounds(temp)
    installed=[]
    family=lambda *prefix:[n for n in shapes if n.startswith(prefix)]
    def add(title,names,dz=-60):installed.extend(a.path(title,names,installed,dz))
    add('Starting nested cylinders and journals',['output_cap_cylinder','carrier_top_cap','shaft_end_upper'])
    add('Twenty standing ring screws',family('hardware_ring_M3_shanks','hardware_ring_cap_heads'),60)
    add('Only three short guide screws',family('hardware_guide_M3x35'),60)
    add('Two standing shaft ties',['hardware_shaft_M3x35_upper','temporary_shaft_tie'],60)
    add('First concentric bearing pair',['hardware_6810_top','hardware_6704_top'])
    add('Starting inner layer and captured nuts',['circular_top','carrier_top','shaft_mount_upper']+family('hardware_carrier_top_mount_nut','hardware_shaft_mount_nut_upper'))
    add('Six guide sleeves and twenty contacts',family('printed_drive_sleeve','printed_contact_sleeve'))
    add('First B outer cam',['shaft_cam_b_outer'])
    add('Closed disc B',family('rotor_b','hardware_disc_b','hardware_6704_disc_b'))
    add('Opposed middle cam halves',['shaft_cam_b_inner','shaft_cam_a_inner'])
    add('Closed disc A',family('rotor_a','hardware_disc_a','hardware_6704_disc_a'))
    add('Last A outer cam',['shaft_cam_a_outer'])
    add('Motor-side plate and modified nut carrier',['circular_bottom','carrier_bottom','shaft_mount_lower']+family('hardware_carrier_bottom_mount_nut','hardware_shaft_mount_nut_lower'))
    add('Finishing bearing pair',['hardware_6810_bottom','hardware_6704_base'])
    add('Finishing caps and modified E',['output_nut_cylinder','carrier_bottom_cap','shaft_end_lower'])
    add('Ring nuts, three guide nuts and retained shaft nut',family('hardware_M3_ring_nuts','hardware_guide_nut_2','hardware_guide_nut_4','hardware_guide_nut_6','hardware_shaft_tie_nut_lower'))
    a.path('Withdraw temporary tie',['temporary_shaft_tie'],installed,60);installed.remove('temporary_shaft_tie')
    add('Fill vacated hex pocket',['hardware_shaft_tie_nut_upper'],60)
    add('Reversed final shaft tie',['hardware_shaft_M3x35_lower'])
    proof=dict(status='passed',source_sha256=report['source_sha256'],steps=a.records,boolean_checks=a.boolean_checks,
               tool_access=keys,conservative_sweeps=a.slivers,printed_fit_tested=False,
               later_stage_evidence=['motor_fit_verification.json','end_cover_verification.json'])
    (BUILD/'full_core_access.json').write_text(json.dumps(proof,indent=2))
    print('NEMA CORE LAYER ORDER PASSED',flush=True)

if __name__=='__main__':main()
