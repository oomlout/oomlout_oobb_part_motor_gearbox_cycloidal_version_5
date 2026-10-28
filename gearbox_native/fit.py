"""Sample assembled native meshes against each other and nominal purchased hardware.

This is a clearance check, not a strength, wear, or continuous-motion proof.
Use --recipe for early diagnostics from the current OCCT recipe before native
publication; the normal run requires accepted current native exports.
"""
import argparse
import os
import json
import math
from pathlib import Path
import numpy as np
import trimesh
import yaml
import manifold3d as mf
from oobb_solidcraft.construction import build_thing
from oobb_solidcraft.compiler import compile_thing
from gearbox_native.export import geometry_digest
from gearbox_native.project import PROJECT, active_part, VERSION
from gearbox_native.presentation import assembly_parts, pose
from gearbox_native.presentation_hardware import build_hardware


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recipe', action='store_true')
    parser.add_argument('--frames', type=int, default=73)
    parser.add_argument('--native-case',type=Path,help='Validated native-only V7 export manifest; no recipe geometry is generated.')
    parser.add_argument('--profile-eccentricity',type=float,help='Recipe diagnostic: edit only fixed-station rotor outlines; keep holes, cams and assembly poses unchanged.')
    args=parser.parse_args()
    if args.profile_eccentricity is not None and not args.recipe:
        parser.error('--profile-eccentricity requires --recipe')
    part=active_part(); out=Path(os.environ.get('GEARBOX_FIT_OUTPUT',str(PROJECT/'outputs'/f'{VERSION}_fit')));out.mkdir(parents=True,exist_ok=True)
    native_case=None
    if args.native_case:
        if args.recipe or args.profile_eccentricity is not None:parser.error('--native-case cannot be combined with recipe geometry')
        native_case=json.loads(args.native_case.read_text(encoding='utf-8'))
        assert native_case['status']=='geometry_verified'
        thing={'gearbox':{'config':native_case['config'],'pieces':{name:{} for name in native_case['parts']}}}
    else:
        thing=build_thing(yaml.safe_load((part/'working.yaml').read_text()),
                          builder_path=PROJECT/'working_solidcraft.py',mode='true')
    c=thing['gearbox']['config'];items=assembly_parts(c);exact_shapes={};native_steps={}
    for item in items:
        name=item['name']
        if native_case:
            from oobb_solidcraft.runtime import digest
            record=native_case['parts'][name]
            for ext in ('step','stl'):assert digest(Path(record[ext]['path']))==record[ext]['sha256']
            native_steps[name]=Path(record['step']['path'])
            item['assets']=[dict(stl=record['stl']['path'])]
            continue
        local=dict(id=part.name+'__'+name,mode='true',
            **thing['gearbox']['pieces'][name]['thing'], sequential_unions=True,
            compound_cuts=True,dimensions=thing['dimensions'])
        plan=compile_thing(local)
        if args.profile_eccentricity is not None and name in ('rotor_a','rotor_b'):
            from gearbox_native.equation_surfaces import edited_plan
            plan,_=edited_plan(plan,args.profile_eccentricity)
        path=part/'solidcraft/true'/f'{name}.stl'
        if args.recipe:
            from gearbox_native.exact_geometry import build_shape
            from OCP.BRepMesh import BRepMesh_IncrementalMesh
            from OCP.StlAPI import StlAPI_Writer
            shape=build_shape(plan['tree']);BRepMesh_IncrementalMesh(shape,.02,False,.12,True).Perform()
            exact_shapes[name]=shape
            path=out/(name+'.stl');writer=StlAPI_Writer();writer.ASCIIMode=False
            assert writer.Write(shape,str(path))
        else:
            from oobb_solidcraft.runtime import digest
            record=json.loads(path.with_name(name+'_manifest.json').read_text())
            assert record['geometry_sha256']==geometry_digest(plan),f'Stale native part: {name}'
            assert record['status']=='success' and record['verification']['status']=='passed'
            assert digest(path)==next(f['sha256'] for f in record['published_files'] if f['file']==path.name)
            step=path.with_suffix('.step')
            assert digest(step)==next(f['sha256'] for f in record['published_files'] if f['file']==step.name)
            native_steps[name]=step
        item['assets']=[dict(stl=str(path))]
    hardware_shapes={}
    hardware=build_hardware(c,out/'hardware',shape_cache=hardware_shapes)
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Common
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    from gearbox_native.exact_geometry import _move
    from gearbox_native.verification import read_step
    for item in hardware:
        parts=[hardware_shapes[Path(a['stl']).stem] for a in item['assets']]
        shape=parts[0]
        for part_shape in parts[1:]:shape=BRepAlgoAPI_Fuse(shape,part_shape).Shape()
        exact_shapes[item['name']]=shape
    items+=hardware
    by_name={item['name']:item for item in items};facet_contacts=[]

    def exact_at(name,turn=0,lift=0):
        if name not in exact_shapes:exact_shapes[name]=read_step(native_steps[name])
        position,angles=pose(by_name[name],c,input_turns=turn);position[2]+=lift
        return _move(_move(exact_shapes[name],'rotate',[math.degrees(v) for v in angles]),'translate',position)

    def exact_volume(a,b,turn=0,lift=0):
        common=BRepAlgoAPI_Common(exact_at(a,turn,lift),exact_at(b,turn))
        assert common.IsDone(),f'Exact collision test failed: {a}, {b}'
        props=GProp_GProps();BRepGProp.VolumeProperties_s(common.Shape(),props)
        return abs(props.Mass())
    shapes={}
    for item in items:
        meshes=[trimesh.load_mesh(a['stl'],process=True) for a in item['assets']]
        components=[]
        for mesh in meshes:
            assert mesh.is_volume,item['name']
            m=mf.Manifold(mf.Mesh64(np.asarray(mesh.vertices,dtype=np.float64),
                                    np.asarray(mesh.faces,dtype=np.uint64)))
            assert m.status()==mf.Error.NoError,item['name']
            components.append(m)
        shape=components[0]
        for component in components[1:]:shape=shape+component
        shapes[item['name']]=shape
    collisions=[];tested=0;same_member=set()
    turns=sorted(set(np.linspace(0,1,args.frames).tolist()+np.linspace(0,c['reduction'],args.frames).tolist()))
    for frame,turn in enumerate(turns):
        moved={};boxes={}
        for item in items:
            position,angles=pose(item,c,input_turns=turn)
            matrix=trimesh.transformations.euler_matrix(*angles);matrix[:3,3]=position
            shape=shapes[item['name']].transform(matrix[:3,:4])
            moved[item['name']]=shape;boxes[item['name']]=np.array(shape.bounding_box()).reshape(2,3)
        for i,a in enumerate(items):
            for b in items[i+1:]:
                key=(a['name'],b['name'])
                if key in same_member:continue
                if a['member']==b['member']:same_member.add(key)
                aa,bb=boxes[a['name']],boxes[b['name']]
                if np.any(np.minimum(aa[1],bb[1])-np.maximum(aa[0],bb[0])<=.001):continue
                tested+=1;volume=(moved[a['name']] ^ moved[b['name']]).volume()
                if volume>.03:
                    exact=exact_volume(*key,turn=turn)
                    detail=dict(parts=list(key),input_turns=turn,mesh_volume_mm3=volume,exact_volume_mm3=exact)
                    if exact>1e-5:collisions.append(detail)
                    else:facet_contacts.append(detail)
        if frame%12==0:print(f'Fit pose {frame+1}/{len(turns)}; {len(collisions)} overlaps',flush=True)
    # Explicit axial installation stages, with only hardware already fitted at
    # that stage. The rear casing base cannot be fitted over the finished discs.
    initial={}
    for item in items:
        position,angles=pose(item,c)
        matrix=trimesh.transformations.euler_matrix(*angles);matrix[:3,3]=position
        initial[item['name']]=shapes[item['name']].transform(matrix[:3,:4])
    installed=['motor_mount','output_bearing_0','motor']
    stages=[
        ('rear_base',['output_base']),
        ('coupler_and_collar',['flanged_coupler','coupling_collar']),
        ('rear_carrier',['pin_rear']),
        ('coupling_drive',['coupling_drive']),
        ('lower_eccentric',['eccentric_hub_lower']),
        ('lower_disc_and_bearing',['rotor_a','eccentric_bearing_0']),
        ('upper_disc_bearing_and_eccentric',['rotor_b','eccentric_bearing_1','eccentric_hub_upper']),
        ('front_carrier',['pin_front']),
        ('front_hub_and_shaft_bearing',['front_bearing_hub','shaft_bearing']),
        ('lobe_ring',['output_casing']),
        ('front_cover_and_bearing',['output_cover','output_bearing_1']),
    ]
    if c.get('simple_assembly'):
        stages=[
            ('preassembled_coupler_and_lower_drive',['flanged_coupler','eccentric_hub_lower']),
            ('lower_disc_and_bearing',['rotor_a','eccentric_bearing_0']),
            ('upper_disc_bearing_and_eccentric',['rotor_b','eccentric_bearing_1','eccentric_hub_upper']),
            ('lobe_ring',['output_casing']),
            ('front_carrier_and_bearings',['pin_front','shaft_bearing','output_bearing_1']),
        ]
        if c.get('direct_drive'):
            installed=['motor_mount','motor']
            stages[0:1]=[
                ('direct_drive_before_grub_tightening',['eccentric_hub_lower']),
                ('rear_6810_after_grub_tightening',['output_bearing_0']),
            ]
            if c.get('base_grub'):
                installed=['motor']
                stages[0:1]=[
                    ('direct_drive_secured_before_motor_plate',
                     ['eccentric_hub_lower','shaft_grub','shaft_grub_nut']),
                    ('motor_plate_over_secured_drive',['motor_mount']),
                ]
    if c.get('split_output_casing'):
        revised=[]
        for stage,moving in stages:
            if 'output_casing' in moving:
                revised.extend([
                    ('lower_casing_with_preloaded_nuts',['output_casing_lower']+[f'housing_nut_{i+1}' for i in range(len(c['housing_positions']))]),
                    ('upper_casing',['output_casing_upper'])])
            else:revised.append((stage,moving))
        stages=revised
    installations=[]
    for stage,moving in stages:
        if any(name not in initial for name in moving):continue
        for lift in np.linspace(60,0,25):
            for name in moving:
                shifted=initial[name].translate([0,0,lift])
                aa=np.array(shifted.bounding_box()).reshape(2,3)
                for other in installed:
                    bb=np.array(initial[other].bounding_box()).reshape(2,3)
                    if np.any(np.minimum(aa[1],bb[1])-np.maximum(aa[0],bb[0])<=.001):continue
                    volume=(shifted ^ initial[other]).volume()
                    if volume>.03:
                        exact=exact_volume(name,other,lift=float(lift))
                        if exact>1e-5:
                            installations.append(dict(stage=stage,parts=[name,other],lift_mm=float(lift),exact_volume_mm3=exact))
        installed+=moving
    print('Installation overlaps:',len(installations),flush=True)
    access_collisions=[];access_tests=0
    if c.get('simple_assembly'):
        # Load nuts before mounting the motor; insert guide screws after the
        # fixed front carrier. Check the actual printed geometry along both paths.
        printed=list(thing['gearbox']['pieces'])
        for prefix,lifts,targets in (
            ('guide_nut_',np.linspace(-20,0,25),['motor_mount']),
            ('guide_bolt_',np.linspace(40,0,25),printed),
            ('post_nut_',np.linspace(-20,0,25),['motor_mount']) if c.get('post_fasteners') else ('unused',[],[]),
            ('post_screw_',np.linspace(40,0,25),printed) if c.get('post_fasteners') else ('unused',[],[]),
            ('housing_nut_',np.linspace(-20,0,25),['output_casing_lower']) if c.get('split_output_casing') else ('unused',[],[]),
            ('housing_screw_',np.linspace(40,0,25),printed) if c.get('split_output_casing') else ('unused',[],[]),
            ('shaft_grub_nut',np.linspace(-15,0,25),['eccentric_hub_lower']) if c.get('direct_drive') else ('unused',[],[]),
        ):
            for name in initial:
                if not name.startswith(prefix):continue
                for lift in lifts:
                    shifted=initial[name].translate([0,0,lift])
                    aa=np.array(shifted.bounding_box()).reshape(2,3)
                    for other in targets:
                        bb=np.array(initial[other].bounding_box()).reshape(2,3)
                        if np.any(np.minimum(aa[1],bb[1])-np.maximum(aa[0],bb[0])<=.001):continue
                        access_tests+=1
                        if (shifted ^ initial[other]).volume()>.03:
                            volume=exact_volume(name,other,lift=float(lift))
                            if volume>1e-5:access_collisions.append(dict(parts=[name,other],lift_mm=float(lift),volume_mm3=volume))
        # A 2 mm diameter driver envelope reaches each grub screw before the
        # upper disc and casing are fitted. Stop at the outside of the coupler.
        from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
        from OCP.gp import gp_Ax2,gp_Pnt,gp_Dir
        for angle in c['coupling_grub_angles']:
            a=math.radians(angle);r=c['direct_grub_outer_radius']+.1 if c.get('direct_drive') else c['coupling_barrel_diameter']/2+.6
            tool=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(r*math.cos(a),r*math.sin(a),c['coupling_grub_z']),
                gp_Dir(math.cos(a),math.sin(a),0)),1,c['carrier_journal_radius']+5-r).Shape()
            targets=('motor','eccentric_hub_lower') if c.get('base_grub') else ('motor_mount','eccentric_hub_lower','rotor_a')
            for other in targets:
                common=BRepAlgoAPI_Common(tool,exact_at(other));assert common.IsDone()
                props=GProp_GProps();BRepGProp.VolumeProperties_s(common.Shape(),props)
                volume=abs(props.Mass());access_tests+=1
                if volume>1e-5:access_collisions.append(dict(tool='grub_driver',angle=angle,part=other,volume_mm3=volume))
    print('Fastener access overlaps:',len(access_collisions),flush=True)
    report=dict(status='failed' if collisions or installations or access_collisions else 'passed',
        source='recipe OCCT diagnostic' if args.recipe else 'verified native STL and nominal hardware envelopes',
        printed_parts=len(thing['gearbox']['pieces']),hardware_items=len(items)-len(thing['gearbox']['pieces']),
        sampled_poses=len(turns),intersection_tests=tested,volume_threshold_mm3=.03,
        collisions=collisions,continuous_motion_proof=False,physical_test_required=True,
        mesh_contacts_cleared_by_exact_native_STEP=facet_contacts,exact_volume_threshold_mm3=1e-5,
        axial_installation_stages=len(stages),axial_installation_poses=len(stages)*25,
        installation_collisions=installations,
        fastener_access_tests=access_tests,fastener_access_collisions=access_collisions,
        grub_driver_envelope_diameter_mm=2 if c.get('simple_assembly') else None,
        required_guide_smooth_length_mm=c['guide_bolt_head_z']-c['rotor_a_z'],
        config=c)
    report['rotor_profile_eccentricity_override_mm']=args.profile_eccentricity
    dest=out/('edited_profile_fit.json' if args.profile_eccentricity is not None else 'recipe_fit.json' if args.recipe else 'native_fit.json')
    dest.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(report['status'],dest,flush=True)
    if collisions or installations or access_collisions:raise SystemExit(1)


if __name__=='__main__':main()
