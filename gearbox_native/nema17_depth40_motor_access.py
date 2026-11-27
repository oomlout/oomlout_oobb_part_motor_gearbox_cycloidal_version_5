"""Check the bench-built motor/tube sequence without changing the design."""
import json, math
from gearbox_native.nema17_depth40_access import *
from gearbox_native.exact_geometry import _move

def main():
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
    from OCP.gp import gp_Ax2,gp_Pnt,gp_Dir
    report=json.loads((PART/'native_export_verification.json').read_text());v=report['parameters']
    health=json.loads((ROOT/'build/nema17_separate_joiners_r2/views/assembled_health.json').read_text())
    shapes=named_shapes(PART/'true.step',health)
    for alias,original in [('circular_top','output_circle_plate'),('circular_bottom','output_circle_rear_plate')]:
        b=bounds(shapes[original]);shapes[alias]=_move(shapes[original],'translate',[-(b[0]+b[3])/2,0,0])
    a=MotorAudit.__new__(MotorAudit);a.shapes=shapes;a.boxes={n:bounds(s) for n,s in shapes.items()}
    a.cache={};a.records=[];a.boolean_checks=0;a.slivers=[];a.bore_exclusions=[]
    # Reuse the production proof's exact, independently verified through bores.
    # A convex envelope of a curved face must not fill these empty cylinders.
    a.through_bores={'motor_inner_adapter':14.95,'motor_cage':v['motor_clear_radius']-.05}
    family=lambda *prefix:[n for n in shapes if n.startswith(prefix)]
    motor=['motor_inner_adapter','motor_cage']+family('hardware_NEMA17_','hardware_cage_','hardware_endcap_rear_join_nut_')
    from gearbox_native.nema17_depth40_guide import scenes
    core=list(next(s for s in scenes(list(shapes)+['temporary_shaft_tie']) if s['key']=='reverse')['parts'])
    core.remove('temporary_shaft_tie')
    core+=family('hardware_coupler_','hardware_flange_')
    a.path('Install complete bench-built motor adapter and tube',motor,core,-100)
    radial=[]
    for i,angle in [(1,v['guide_pair_a']),(3,v['guide_pair_c']),(5,v['guide_pair_b']+180)]:
        delta=[12*math.cos(math.radians(angle)),12*math.sin(math.radians(angle)),0]
        name=f'hardware_guide_nut_{i}';hits=[]
        for swept,box in a.sweep(name,delta):
            for other in motor+core:
                if intersect_boxes(box,a.boxes[other]):
                    amount=overlap(swept,shapes[other])
                    if amount>.03:hits.append(dict(part=other,volume_mm3=amount))
        radial.append(dict(nut=name,clear=not hits,blocked=hits))
    assert all(p['clear'] for p in radial),radial
    print('Three guide nuts remain side-loadable with tube fitted PASS',flush=True)
    guides=family('hardware_guide_M3x40');nuts=[f'hardware_guide_nut_{i}' for i in (1,3,5)]
    a.path('Insert three long guides after side-loading nuts',guides,core+motor+nuts,100)
    access=[]
    for axis in [(1,0,0),(0,1,0),(-1,0,0),(0,-1,0)]:
        tool=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(5*axis[0],5*axis[1],v['shaft_face_z']-7),gp_Dir(*axis)),1,35).Shape()
        hits=[]
        for other in motor+core+guides+nuts:
            if other.startswith(('hardware_flange_','hardware_coupler_')):continue
            if intersect_boxes(bounds(tool),a.boxes[other]):
                amount=overlap(tool,shapes[other])
                if amount>.03:hits.append(dict(part=other,volume_mm3=amount))
        access.append(dict(direction=axis,tool_diameter_mm=2,clear=not hits,blocked=hits))
    assert all(p['clear'] for p in access),access
    print('All four grub windows clear with motor tube fitted PASS',flush=True)
    proof=dict(status='passed',source_sha256=report['source_sha256'],steps=a.records,boolean_checks=a.boolean_checks,
               radial_guide_nut_loading=radial,grub_key_access=access,printed_fit_tested=False,
               conservative_sweeps=a.slivers,continuous_through_bores=a.bore_exclusions)
    (BUILD/'bench_motor_access.json').write_text(json.dumps(proof,indent=2))

if __name__=='__main__':main()
