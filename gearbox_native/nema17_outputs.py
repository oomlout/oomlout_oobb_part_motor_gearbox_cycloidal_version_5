"""Validate and publish the motor adaptation, without rewriting the manual part."""
import argparse
import hashlib
import itertools
import json
import shutil
from pathlib import Path

import numpy as np
import trimesh
from OCP.TopAbs import TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.mcp import MCPClient
from gearbox_native.project import PROJECT
from gearbox_native.acceptance import health_check,verify_mesh
from gearbox_native.verification import read_step
from gearbox_native.verify_assembly_sequence import bounds,intersect_boxes,Audit
from gearbox_native.verify_native_v8 import overlap as exact_overlap,volume
from gearbox_native.nema17_double_bearing import BASE,MASTER,PART_ID,POSITIONS

BOOLEAN_RETRIES=[]


class MotorAudit(Audit):
    """Continuous insertion; bound non-prismatic native spline faces conservatively."""
    def sweep(self,name,delta):
        from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
        from OCP.BRepCheck import BRepCheck_Analyzer
        from OCP.TopoDS import TopoDS
        from OCP.TopAbs import TopAbs_FACE
        from OCP.gp import gp_Vec
        from gearbox_native.exact_geometry import _move
        key=name,tuple(delta)
        if key not in self.cache:
            solid=self.shapes[name];pieces=[solid,_move(solid,'translate',delta)]
            faces=TopExp_Explorer(solid,TopAbs_FACE)
            while faces.More():
                face=TopoDS.Face_s(faces.Current());faces.Next()
                prism=BRepPrimAPI_MakePrism(face,gp_Vec(*delta),False,True).Shape()
                amount=abs(volume(prism))
                if amount<1e-7:continue
                if not BRepCheck_Analyzer(prism).IsValid():
                    # Sweeping a warped cylindrical spline can fold over itself.
                    # Test an OUTER convex envelope instead of ignoring that face.
                    # Native Z bounds retain exact end stops; the XY hull has a
                    # 5-micron outward margin over a 1-micron face tessellation.
                    assert delta[0]==delta[1]==0
                    from OCP.BRepMesh import BRepMesh_IncrementalMesh
                    from OCP.BRep import BRep_Tool
                    from OCP.TopLoc import TopLoc_Location
                    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon,BRepBuilderAPI_MakeFace
                    from OCP.gp import gp_Pnt
                    from shapely.geometry import MultiPoint
                    BRepMesh_IncrementalMesh(face,.001,False,.03,False).Perform()
                    location=TopLoc_Location();mesh=BRep_Tool.Triangulation_s(face,location)
                    xy=[mesh.Node(i).Transformed(location.Transformation()).Coord()[:2] for i in range(1,mesh.NbNodes()+1)]
                    hull=MultiPoint(xy).convex_hull.buffer(.005,join_style=2)
                    bb=bounds(face);low=bb[2]+min(0,delta[2]);high=bb[5]+max(0,delta[2])
                    wire=BRepBuilderAPI_MakePolygon()
                    for x,y in list(hull.exterior.coords)[:-1]:wire.Add(gp_Pnt(x,y,low))
                    wire.Close();cap=BRepBuilderAPI_MakeFace(wire.Wire()).Face()
                    prism=BRepPrimAPI_MakePrism(cap,gp_Vec(0,0,high-low)).Shape()
                    # Preserve an independently checked, axis-aligned through
                    # bore. A Z translation cannot sweep material into that bore;
                    # filling it with a convex hull would be a false collision.
                    if name in self.through_bores:
                        from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
                        from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
                        from OCP.gp import gp_Ax2,gp_Dir
                        r=self.through_bores[name]
                        check=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,0,self.boxes[name][2]-1),gp_Dir(0,0,1)),r,self.boxes[name][5]-self.boxes[name][2]+2).Shape()
                        assert overlap(solid,check)<.03,('Unverified through bore',name,r)
                        bore=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,0,low-1),gp_Dir(0,0,1)),r,high-low+2).Shape()
                        cut=BRepAlgoAPI_Cut(prism,bore);cut.Build();assert cut.IsDone();prism=cut.Shape()
                    assert BRepCheck_Analyzer(prism).IsValid()
                    self.slivers.append(dict(body=name,delta_mm=delta,method='conservative convex envelope',
                                             tessellation_mm=.001,outward_xy_margin_mm=.005,
                                             verified_through_bore_radius_mm=self.through_bores.get(name)))
                pieces.append(prism)
            self.cache[key]=[(p,bounds(p)) for p in pieces]
        return self.cache[key]

    def path(self,title,moving,installed,dz,required=True):
        moving=list(moving);obstacles=set(installed)-set(moving);failures=[];pairs=0
        for name in moving:
            box=self.boxes[name].copy();box[2]+=min(0,dz);box[5]+=max(0,dz)
            for other in (n for n in obstacles if intersect_boxes(box,self.boxes[n])):
                pairs+=1;largest=0.
                if name in self.through_bores:
                    # Exact sufficient condition: an obstacle wholly inside a
                    # verified through bore stays clear for every Z translation.
                    from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
                    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
                    from OCP.gp import gp_Ax2,gp_Pnt,gp_Dir
                    low=min(box[2],self.boxes[other][2])-1
                    high=max(box[5],self.boxes[other][5])+1
                    bore=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,0,low),gp_Dir(0,0,1)),self.through_bores[name],high-low).Shape()
                    assert overlap(self.shapes[name],bore)<1e-6,('Through bore not clear',name)
                    outside=BRepAlgoAPI_Cut(self.shapes[other],bore);outside.Build();assert outside.IsDone()
                    if abs(volume(outside.Shape()))<1e-6:
                        self.bore_exclusions.append(dict(moving=name,obstacle=other,radius_mm=self.through_bores[name]))
                        continue
                for swept,swept_box in self.sweep(name,[0,0,dz]):
                    if not intersect_boxes(swept_box,self.boxes[other]):continue
                    self.boolean_checks+=1;largest=max(largest,overlap(swept,self.shapes[other]))
                    if largest>.03:break
                if largest>.03:failures.append(dict(moving=name,obstacle=other,overlap_mm3=largest))
        self.records.append(dict(step=title,moving=moving,approach_offset_mm=dz,installed=list(installed),
                                 candidate_pairs=pairs,clear=not failures,blocked=failures))
        print(title,'PASS' if not failures else failures,flush=True)
        if required:assert not failures,title
        return moving


def overlap(a,b):
    """Retry coincident nut/roof faces within the existing acceptance allowance."""
    try:return exact_overlap(a,b)
    except AssertionError:
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
        from OCP.TopTools import TopTools_ListOfShape
        aa=TopTools_ListOfShape();aa.Append(a);bb=TopTools_ListOfShape();bb.Append(b)
        for tolerance in (1e-6,1e-5,1e-4,.001):
            op=BRepAlgoAPI_Common();op.SetArguments(aa);op.SetTools(bb);op.SetFuzzyValue(tolerance);op.Build()
            if op.IsDone():
                BOOLEAN_RETRIES.append(dict(fuzzy_tolerance_mm=tolerance))
                return max(0,volume(op.Shape()))
        raise


def verify(views):
    BOOLEAN_RETRIES.clear()
    report=json.loads((views/'export.json').read_text(encoding='utf8'))
    v={p['name']:p['value'] for p in report['parameters']['parameters']}
    baseline_id=PART_ID.split('_nema17_flange',1)[0]
    baseline=json.loads((PROJECT/'parts'/baseline_id/'native_export_verification.json').read_text(encoding='utf8'))
    unchanged=('reduction','pitch','eccentricity','contact_radius','profile_clearance','middle_length','disc_thickness',
               'disc_gap','guide_pitch','guide_track','shaft_race_od','main_bearing_od','main_bearing_width')
    assert all(v[k]==baseline['parameters'][k] for k in unchanged),'This adapter proof is for the accepted gearbox dimensions'
    states=json.loads((views/'assembled_health.json').read_text(encoding='utf8'))['bodies']
    declared={r['name']:np.array(r['bbox']['min']+r['bbox']['max']) for r in states if r['name']!='connected_contact_ring'}
    shapes={};boxes={}
    exp=TopExp_Explorer(read_step(views/'assembled.step'),TopAbs_SOLID)
    while exp.More():
        solid=exp.Current();box=bounds(solid)
        names=[n for n,b in declared.items() if np.max(abs(b-box))<.04]
        assert len(names)==1,('Body identification',names,box)
        shapes[names[0]]=solid;boxes[names[0]]=box;exp.Next()
    assert shapes.keys()==declared.keys()
    changed=set(POSITIONS)|{'shaft_end_lower','shaft_mount_lower'}
    changed.update(n for n in shapes if n.startswith(('hardware_guide_','hardware_coupler_','hardware_NEMA17_','hardware_flange_','hardware_cage_','hardware_shaft_mount_nut_lower')))
    clashes=[];checks=0;maximum=0.
    for a,b in itertools.combinations(shapes,2):
        if not ({a,b}&changed) or not intersect_boxes(boxes[a],boxes[b]):continue
        amount=overlap(shapes[a],shapes[b]);checks+=1;maximum=max(maximum,amount)
        if amount>.03:clashes.append(dict(a=a,b=b,overlap_mm3=amount))
    proof=dict(source_sha256=report['source_sha256'],checks=checks,maximum_overlap_mm3=maximum,clashes=clashes,
               motor_depth_mm=v['motor_depth'],motor_shaft_mm=v['motor_shaft_length'],
               guide_screw_lengths_mm=[40,35,40,35,40,35],
               circular_plate_diameter_mm=2*v['circle_plate_radius'],
               original_master_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),physical_fit_tested=False)
    proof['unchanged_gearbox_dimensions']={k:v[k] for k in unchanged}
    (views/'motor_fit.json').write_text(json.dumps(proof,indent=2),encoding='utf8')
    assert not clashes,clashes
    assert v['motor_guide_length']<=40
    assert -v['carrier_extension']-(v['drive_tip']-v['motor_guide_extension']+2.4)>=.8, 'Insufficient guide-nut roof for this sleeve stack'
    assert abs(v['motor_cage_height']-v['motor_depth']-v['motor_rear_gap']-3)<1e-7
    assert round((2*v['circle_plate_radius']+1)/15)%2==1
    # Full nut engagement and clearance before the following eccentric piece.
    tip=v['shaft_face_z']-2.5+14
    nut_floor=v['shaft_end_station']+v['shaft_nut_depth']
    assert tip>=nut_floor and tip<v['stack_height']/2-2*v['shaft_cam_depth']
    proof['coupler_nut_engagement_mm']=2.5
    proof['coupler_screw_tip_clearance_mm']=v['stack_height']/2-2*v['shaft_cam_depth']-tip
    # Only additions need new path checks; the unchanged rotor/guide stack keeps
    # its prior accepted sweep. Verify installing motor before the surround.
    audit=MotorAudit.__new__(MotorAudit);audit.shapes=shapes;audit.boxes=boxes;audit.cache={};audit.records=[];audit.boolean_checks=0;audit.slivers=[]
    audit.through_bores={'motor_inner_adapter':14.95,'motor_cage':v['motor_clear_radius']-.05}
    audit.bore_exclusions=[]
    long_names={f'hardware_guide_M3x40_{i}' for i in (1,3,5)}
    gear=[n for n in shapes if n not in POSITIONS and not n.startswith(('hardware_NEMA17_','hardware_cage_'))
          and n not in long_names and n not in {f'hardware_guide_nut_{i}' for i in (1,3,5)}]
    motor_group=['motor_inner_adapter','hardware_NEMA17_motor']+[n for n in shapes if n.startswith('hardware_NEMA17_M3')]
    audit.path('Attach motor and adapter subassembly after fitting coupler',motor_group,gear,-80)
    placed=gear+motor_group+[f'hardware_guide_nut_{i}' for i in (1,3,5)]
    audit.path('Insert three M3x40 guides from the original socket-cap end',long_names,placed,80)
    placed+=list(long_names)
    audit.path('Lower the rear surround over the installed motor',['motor_cage'],placed,-80)
    # Nuts must slide in before the three long screws: a screw already crossing
    # the pocket would block radial loading. Check the swept nut, not just its OD.
    radial=[]
    for i,angle in [(1,v['guide_pair_a']),(3,v['guide_pair_c']),(5,v['guide_pair_b']+180)]:
        import math
        delta=[12*math.cos(math.radians(angle)),12*math.sin(math.radians(angle)),0]
        name=f'hardware_guide_nut_{i}';largest=0.
        for swept,box in audit.sweep(name,delta):
            for other in motor_group:
                if intersect_boxes(box,boxes[other]):largest=max(largest,overlap(swept,shapes[other]))
        assert largest<.03,(name,'radial loading',largest)
        radial.append(dict(nut=name,overlap_mm3=largest))
    proof['radial_nut_loading']=radial
    from gearbox_native.exact_geometry import _move
    stops=[]
    for name,target in [(f'hardware_guide_nut_{i}','motor_inner_adapter') for i in (1,3,5)]+[(f'hardware_cage_nut_{i}','motor_cage') for i in (0,2,4)]:
        # Tightening pulls these nuts toward +Z. A real roof must stop them.
        amount=overlap(_move(shapes[name],'translate',[0,0,.05]),shapes[target])
        assert amount>.05,('Nut has no clamping roof',name,amount)
        stops.append(dict(nut=name,retainer=target,blocked_upward_move_mm=.05,overlap_mm3=amount))
    proof['nut_clamping_roofs']=stops
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
    from OCP.gp import gp_Ax2,gp_Pnt,gp_Dir
    access=[]
    for axis in [(1,0,0),(0,1,0),(-1,0,0),(0,-1,0)]:
        tool=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(5*axis[0],5*axis[1],v['shaft_face_z']-7),gp_Dir(*axis)),1.0,35).Shape()
        amount=overlap(tool,shapes['motor_inner_adapter'])
        assert amount<.03,('grub access',axis,amount)
        access.append(dict(direction=axis,tool_diameter_mm=2,overlap_mm3=amount))
    proof['grub_key_access']=access
    proof['insertion_paths']=audit.records
    proof['conservative_sweep_envelopes']=audit.slivers
    proof['continuous_through_bore_clearances']=audit.bore_exclusions
    # Printability of the tall surround and adapter is checked from real sections.
    from gearbox_native.split_stack import layer_audit
    proof['printability']={name:layer_audit(trimesh.load_mesh(views/'parts'/(name+'.stl'))) for name in ('motor_inner_adapter','motor_cage')}
    assert all(r['unsupported_islands']==0 for r in proof['printability'].values())
    proof['status']='passed'
    proof['boolean_retries']=list(BOOLEAN_RETRIES)
    (views/'motor_fit.json').write_text(json.dumps(proof,indent=2),encoding='utf8')
    return proof


def verify_edit(source,folder,additional_changes=None):
    folder.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256(Path(source).read_bytes()).hexdigest()
    if (folder/'report.json').exists():
        cached=json.loads((folder/'report.json').read_text(encoding='utf8'))
        if cached.get('source_sha256')==digest and cached.get('status')=='passed' and cached.get('additional_changes',{})==(additional_changes or {}):return cached
    with MCPClient(folder/'edit',design=source,allow_path=PROJECT,timeout=1800) as client:
        before=health_check(client,folder/'before.json')
        params=require_ok(client.execute('parameters.list',filter='user'))
        original={p['name']:p['value'] for p in params['parameters']}
        depth=original['motor_depth']+8
        require_ok(client.execute('parameters.change',changes={'motor_depth':f'{depth} mm',**(additional_changes or {})}))
        after=health_check(client,folder/'after.json')
        for ext in ('step','stl'):
            require_ok(client.call('export',dict(bodies=['motor_cage'],path=str(folder/('cage48.'+ext)))))
        from gearbox_native.nema17_mesh import verify_print_mesh
        mesh=verify_print_mesh(folder/'cage48.stl',read_step(folder/'cage48.step'))
        require_ok(client.call('save',dict(path=str(folder/'depth48.solidcraft'))))
    with MCPClient(folder/'reopen',design=folder/'depth48.solidcraft',allow_path=PROJECT,timeout=1800) as client:
        reopened=health_check(client,folder/'reopened.json')
        params=require_ok(client.execute('parameters.list',filter='user'))
        v={p['name']:p['value'] for p in params['parameters']}
        assert v['motor_depth']==depth and v['motor_cage_height']==depth+original['motor_rear_gap']+3 and v['motor_guide_length']<=40
        require_ok(client.call('save',dict(path=str(folder/'depth48_reopened.solidcraft'))))
    def box(h,n):return next(b['bbox'] for b in h['bodies'] if b['name']==n)
    assert abs(box(after,'motor_cage')['min'][2]-box(before,'motor_cage')['min'][2]+8)<.001
    assert np.max(abs(np.array(box(after,'motor_cage')['min'])-box(reopened,'motor_cage')['min']))<.001
    result=dict(status='passed',source_sha256=digest,native_edit=f'motor_depth: {original["motor_depth"]:g} to {depth:g} mm',rear_flange_shift_mm=-8,guide_screw_mm=40,save_reopen=True,mesh=mesh,additional_changes=additional_changes or {})
    (folder/'report.json').write_text(json.dumps(result,indent=2),encoding='utf8');return result


def publish(part,source,views,overrides=None,source_sha=None,_checks=None):
    part=Path(part);views=Path(views);source=Path(source)
    report=json.loads((views/'export.json').read_text(encoding='utf8'))
    if any(p['name']=='motor_tube_wall' for p in report['parameters']['parameters']):
        from gearbox_native.nema17_tube_outputs import publish as publish_tube
        return publish_tube(part,source,views,overrides,source_sha)
    if 'front_cover_spacer' in report['parts'] and _checks is None:
        from gearbox_native.nema17_end_caps_outputs import publish as publish_covers
        return publish_covers(part,source,views,overrides,source_sha)
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    if _checks is None:
        proof=json.loads((views/'motor_fit.json').read_text(encoding='utf8')) if (views/'motor_fit.json').exists() else {}
        if proof.get('status')!='passed' or proof.get('source_sha256')!=digest:proof=verify(views)
        edit=verify_edit(source,views/'motor_depth_edit')
    else:proof,edit=_checks
    v={p['name']:p['value'] for p in report['parameters']['parameters']}
    part.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,part/'gearbox_controls.solidcraft')
    for mode,target in [('assembled','true'),('exploded','exploded'),('3dpr','3dpr')]:
        for ext in ('solidcraft','step','stl','png'):shutil.copyfile(views/(mode+'.'+ext),part/(target+'.'+ext))
        for ext in ('stl','png'):shutil.copyfile(views/(mode+'.'+ext),part/(target+'_solidcraft.'+ext))
        manifest=dict(status='success',construction='native',native_only=True,version='simple_double_bearing_version_2',
                      input_variant='nema17_flange',canonical_master=str(part/'gearbox_controls.solidcraft'),snapshot=True,
                      external_piece_links=False,source_sha256=report['source_sha256'],export_evidence='native_export_verification.json')
        (part/(target+'_solidcraft_manifest.json')).write_text(json.dumps(manifest,indent=2),encoding='utf8')
    (part/'native_parts').mkdir(exist_ok=True)
    for path in (views/'parts').iterdir():shutil.copyfile(path,part/'native_parts'/path.name)
    summary=dict(status=report['status'],source_sha256=report['source_sha256'],sampling=report['sampling'],parameters=v,
                 part_names=list(report['parts']),print_mesh=report['print_mesh'],note=report['note'])
    for name,data in [('motor_fit_verification',proof),('motor_depth_edit_verification',edit),('native_export_verification',summary),('native_export_details',report),
                      ('native_configuration',dict(style='simple_double_bearing_version_2',input_variant='nema17_flange',source_master=MASTER,parameters=overrides or {},source_master_sha256=source_sha))]:
        (part/(name+'.json')).write_text(json.dumps(data,indent=2),encoding='utf8')
    # Compact conversion bed. Both circular plates remain individual optional prints.
    kit=part/'motor_conversion';kit.mkdir(exist_ok=True);meshes=[]
    for name,xy in [('motor_inner_adapter',(44,44)),('motor_cage',(162,71)),('shaft_end_lower',(20,120)),('shaft_mount_lower',(49,120))]:
        m=trimesh.load_mesh(part/'native_parts'/(name+'.stl'));m.apply_translation([*xy,0]);meshes.append(m)
    bed=trimesh.util.concatenate(meshes);assert max(bed.bounds[1,:2])<240 and min(bed.bounds[0,:2])>=0
    bed.export(kit/'3dpr.stl')
    (kit/'3dpr.scad').write_text('import("3dpr.stl", convexity=10);\n',encoding='utf8')
    (part/'3dpr.scad').write_text('// Native SolidCraft print-layout export. Edit gearbox_controls.solidcraft.\nimport("3dpr.stl", convexity=10);\n',encoding='utf8')
    (part/'EDITING_PARAMETERS.md').write_text('''# Editing the motor variant

Open `gearbox_controls.solidcraft`. In Parameters, edit the favourite `motor_depth`
(default 40 mm). This is the motor body only. The rear OOBB flange and three
surround posts move together, leaving `motor_rear_gap` (3 mm). `motor_shaft_length`
is the shaft projection (24 mm); it changes the motor reference. The 5 mm shaft
can enter the open 6.5 mm bore in the gearbox stack.

The existing reduction, profile, eccentricity, sleeve and print/explode controls
remain native. This motor conversion is checked with the current 16 mm spacer
stack; a 20 mm stack needs a revised guide-nut seat to keep the 40 mm limit.
Set `print_layout=1`, `explode=0 mm` for printing. Hardware is
parked above the print bed; export only the printed groups. `explode=12 mm`,
`print_layout=0` makes the exploded view from this same master.

The four coupler holes use `coupler_mount_radius=8 mm`. Change only for a measured
coupler: this variant is for the project's Ø22 × 12 mm flange coupler, 5 mm bore,
four M3 holes on Ø16 mm PCD. It does not mean all 5 mm couplers are interchangeable.

The motor mounts are standard 31 mm square, clocked 18.5° to keep the guide
fasteners clear. Three guides are 40 mm, three 35 mm. The rear surround uses
three separate 10 mm screws; increasing motor depth never increases these lengths.

`circle_plate_radius` follows the next suitable odd OOBB diameter (currently
134 mm, nominal 9 units). Both output and rear circular flanges are 3 mm thick.
Square, lower-row, extended circular, and plain circular output plates are
interchangeable options. The two circular options are parked to the left of
the main stack in the native drawing; they are not additional installed layers.

The original manual-input catalogue part and its native master are unchanged.
''',encoding='utf8')
    (part/'ASSEMBLY.md').write_text('''# Motor variant assembly

Use the original gearbox's screws-first layered sequence, socket-cap end down.
For this motor variant, the rear motor flange and black inner carrier are fixed;
the teal outer housing is the output (20:1, in the input's direction). Follow the
mechanical stacking steps from the manual guide, but use this mounting arrangement.
Replace only the motor-end E journal and N nut carrier with this variant's
`shaft_end_lower` and `shaft_mount_lower`. Their four holes now match the coupler.
Keep the opposite E/N, both cycloids, four C halves and all bearing seats.

1. Start the original 20 outer screws and both opposed shaft ties. For the six
   inner guides, keep the 35 mm screws at 82°, 188° and 315°. Set aside three
   40 mm screws for 8°, 135° and 262° until the motor is fitted. All heads remain
   at the original socket-cap end. Build the bearing
   and rotor layers as before. Reverse the temporary shaft tie at the end.
2. Preload the four M3 coupler nuts in the modified N carrier before closing E.
   Finish the shaft ties before fitting the coupler: its flange covers them.
3. Attach the Ø22 mm coupler flange to E using four M3 × 14 socket caps and one
   Ø6 × 0.5 mm M3 washer under each head. The washers keep the screw tips clear of
   the next C half. The narrow barrel faces the motor; the flange faces E.
4. On the bench, seat the motor against `motor_inner_adapter`. Use four M3 × 8
   socket caps through the front access bores (4 mm nominal motor thread
   engagement). Tighten these now: the gearbox carrier covers the access bores.
5. Slide the motor-and-adapter subassembly over the coupler and onto the gearbox.
   Slide three M3 nuts radially into the side slots, flats parallel to the slot.
   Insert the three M3 × 40 guide screws from the opposite socket-cap end and
   tighten them into these nuts. The remaining three 35 mm guides retain their
   original nuts. Support the gearbox so that both ends remain accessible.
6. Tighten the coupler grub screws through the four roofed access windows before
   installing the rear surround. Rotate the input to align a grub with a window.
7. Slide three M3 nuts into the radial slots near the tops of the surround posts. Slide `motor_cage` over
   the motor from its rear and attach it with three M3 × 10 socket caps through
   the outer holes of the motor adapter. Route the cable through an open side.
8. Fix the rear circular flange using its OOBB holes; attach the load to the teal
   outer housing. Keep the outer housing free to rotate. For a circular output,
   substitute the extended or plain circular plate for a square plate; use the
   same lobe screws and 6810 cylinders. Turn the input by hand before powering.

Print the conversion bed once. The adapter prints motor-face down; the surround
prints rear-flange down. The circular output plates print flat. The 40 mm body
envelope excludes a connector: check its position in one of the open sectors.
''',encoding='utf8')
    (part/'HARDWARE_CHANGES.md').write_text('''# Hardware changes from the current manual gearbox

| Hardware | Quantity | Use |
|---|---:|---|
| 5 mm shaft flange coupler, Ø22 flange, 12 mm high, Ø16 PCD | 1 | Motor to modified E/N stack |
| NEMA17 motor, 31 mm mounting square, 24 mm shaft projection | 1 | Default body depth 40 mm |
| M3 × 40 socket cap | 3 | Replace three M3 × 35 guide screws; reuse their nuts |
| M3 × 14 socket cap | 4 | Coupler flange to the four existing mounting nuts |
| M3 washer, Ø6 mm OD × 0.5 mm thick | 4 | Under coupler screw heads |
| M3 hex nut | 4 | Captured in the modified N carrier; reuse the optional old mounting nuts if fitted |
| M3 × 8 socket cap | 4 | Adapter to motor face |
| M3 × 10 socket cap and M3 nut | 3 each | Rear surround to motor adapter |

All other gearbox hardware stays unchanged. Maximum socket-cap length: 40 mm.
Coupler grub screws are the coupler's supplied hardware. The two mounted
circular flanges are options for external mounting; their application bolts
are not included in this conversion list.
''',encoding='utf8')
    (part/'README.md').write_text('''# Double-bearing gearbox — NEMA17 flange-coupler variant

Separate adaptation of the current manual-input gearbox. The original part is
retained. The native file contains the complete gearbox, motor adapter, motor
surround, rear circular flange and parked circular output-plate options.

Fix the rear motor flange. The black inner carrier is stationary and the teal
outer housing provides the 20:1 output, rotating in the input's direction.

This is an entirely AI-generated coding project. Generated outputs are included
as a starting point for modifications with your own AI tools. Digital fit checks
are recorded here; the motor conversion has not been physically assembled.

- [Native editable master](gearbox_controls.solidcraft)
- [Motor conversion print bed](motor_conversion/3dpr.stl) — four new/replacement pieces
- [All printable parts](3dpr.stl), including alternative plates and contact ring
- [Extended circular output plate](native_parts/output_circle_plate.stl)
- [Plain circular output plate](native_parts/output_plain_circle_plate.stl)
- [Assembly](ASSEMBLY.md) · [Parameters](EDITING_PARAMETERS.md) · [Hardware changes](HARDWARE_CHANGES.md)
- [Assembled view](true.png) · [Exploded native model](exploded.solidcraft)
- [Circular-flange render](render_circular.png) · [Square-plate render](render_square.png)
''',encoding='utf8')
    return proof


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('views',type=Path);p.add_argument('--verify-only',action='store_true');a=p.parse_args()
    if a.verify_only:verify(a.views)
    else:publish(PROJECT/'parts'/PART_ID,a.source,a.views,source_sha=hashlib.sha256(a.source.read_bytes()).hexdigest())
