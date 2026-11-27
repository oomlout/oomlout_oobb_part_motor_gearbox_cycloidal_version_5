"""Check the actual native edit, printed solids, hardware and swept cycloid clearance."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import LinearRing, MultiPoint
from shapely.affinity import rotate
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.registry import discover
from oobb_solidcraft.validation import inspect_shape
from gearbox_native.acceptance import health_check,verify_mesh
from gearbox_native.verification import read_step
from gearbox_native.project import PROJECT
from gearbox_native.simple_double_bearing import POSITIONS
from gearbox_native.exact_geometry import _move
from gearbox_native.verify_native_v8 import overlap
from gearbox_native.verify_v8_hardware import cylinder,hexagon


def swept(v,profile):
    n=int(v['ring_count']);e=v['eccentricity'];pitch=v['pitch'];r=v['contact_radius']
    params=dict(ring_pin_count=n,pitch_radius=pitch,eccentricity=e,roller_radius=r,clearance=v['profile_clearance'])
    api=discover().module('cycloidal_pattern')
    sampling=api.validate_edit(profile,params)
    assert sampling['max_sampled_chord_error_mm']<=.005
    outline=LinearRing(api.full_points(profile,params))
    opposite=rotate(outline,-180/(n-1),origin=(0,0))
    # Global rotor orientation is fixed. Only the disc centres orbit.
    least=float('inf')
    for i in range(360):
        a=math.radians(i);cx=e*math.cos(a);cy=e*math.sin(a)
        t=a/n+np.arange(n)*2*math.pi/n
        x=pitch*np.cos(t);y=pitch*np.sin(t)
        for path,side in ((outline,1),(opposite,-1)):
            centers=MultiPoint(np.column_stack([x-side*cx,y-side*cy]))
            least=min(least,path.distance(centers)-r)
    assert least>v['profile_clearance']-.008,(least,params)
    wall_inner=pitch+r-.5
    # Triangle inequality gives a lower bound for every angle, including between samples.
    maximum_radius=max(math.hypot(x,y) for x,y in outline.coords) + e + sampling['max_sampled_chord_error_mm']
    assert wall_inner>maximum_radius
    return dict(input_positions=360,discs=2,minimum_ring_gap_mm=least,minimum_wall_gap_bound_mm=wall_inner-maximum_radius,chord_error_mm=sampling['max_sampled_chord_error_mm'])


def edit(build):
    source=build/'complete.solidcraft';folder=build/'edit';folder.mkdir(exist_ok=False)
    with MCPClient(folder/'change',design=source,allow_path=PROJECT,timeout=600) as c:
        require_ok(c.execute('parameters.change',changes={'reduction':'15','eccentricity':'2 mm','middle_length':'20 mm','pitch':'48 mm'}))
        health_check(c,folder/'edit_health.json')
        require_ok(c.call('save',dict(path=str(folder/'edited.solidcraft'))))
    with MCPClient(folder/'reopen',design=folder/'edited.solidcraft',allow_path=PROJECT,timeout=600) as c:
        h=health_check(c,folder/'reopened_health.json')
        v={r['name']:r['value'] for r in require_ok(c.execute('parameters.list',filter='user'))['parameters']}
        assert v['reduction']==15 and abs(v['eccentricity']-2)<1e-9 and v['middle_length']==20 and v['disc_thickness']==7
        pins=[b for b in h['bodies'] if b['name'].startswith(('printed_contact_sleeve','hardware_round_M3_spacers'))]
        assert len(pins)==15
        for ext in ('step','stl'):require_ok(c.call('export',dict(path=str(folder/('cam.'+ext)),bodies=['shaft_cam_a_outer'])))
        from gearbox_native.verify_double_bearing_housing import inspect_plate
        from gearbox_native.double_bearing_housing import FOOT
        import trimesh
        assert v['housing_grid_radius']==60 and v['housing_plate_half']==67
        for name in ('output_cap_plate',FOOT):
            path=folder/(name+'.stl')
            require_ok(c.call('export',dict(path=str(path),bodies=[name])))
            mesh=trimesh.load_mesh(path)
            mesh.apply_translation([-v['housing_preview_x'] if name==FOOT else 0,0,-v['middle_end']])
            inspect_plate(mesh,name,v['bearing_ring_radius'],v['pitch'],int(v['ring_count']))
    return measure_edit(build,v,len(pins))


def measure_edit(build,v,pin_count):
    folder=build/'edit'
    sh=read_step(folder/'cam.step');info=inspect_shape(sh);mesh=verify_mesh(folder/'cam.stl',sh)
    assert info['valid'] and info['solid_count']==1
    # Measure the outer journal in the BRep, not just its parameter entry.
    journals=[a for a in info['cylindrical_faces'] if abs(a['radius_mm']-v['shaft_journal'])<.001]
    assert journals and any(abs(a['axis_origin_mm'][0]-2)<.001 for a in journals),journals
    wall=v['shaft_journal']-math.hypot(v['shaft_tie_pitch'],v['eccentricity'])-v['shaft_tie_bore']
    assert wall>=1
    assert v['join_length']==35 and v['shaft_tie_length']==35
    evidence=dict(housing_grid_size=9,housing_plate_width_mm=2*v['housing_plate_half'],pitch_mm=v['pitch'],ratio=15,eccentricity_mm=2,spacer_length_mm=v['middle_length'],join_screw_mm=v['join_length'],
                  axial_tie_mm=v['shaft_tie_length'],round_spacers=pin_count,minimum_cam_to_tie_web_mm=wall,
                  reopened=True,mesh_watertight=mesh['watertight'],motion=swept(v,json.loads((build/'profile.json').read_text())))
    (folder/'verification.json').write_text(json.dumps(evidence,indent=2))
    return evidence


def fits(part,v,profile):
    # Reassemble the individual published print-oriented STEP files, and test actual BReps.
    z={
        'output_nut_plate':v['middle_start'],'output_cap_plate':v['middle_end'],
        'carrier_bottom':v['middle_start']+v['guide_socket_depth'],'carrier_top':v['middle_end']-v['guide_socket_depth'],
        'carrier_bottom_cap':-v['carrier_extension'],'carrier_top_cap':v['stack_height']+v['carrier_extension'],
        'rotor_a':v['disc_a_z'],'rotor_b':v['disc_b_z']+v['disc_thickness'],
        'rotor_a_cap':v['disc_a_z']+v['disc_thickness'],'rotor_b_cap':v['disc_b_z'],

    }
    from gearbox_native.double_bearing_housing import CYLINDERS, FOOT, output_mounts
    from gearbox_native.verify_double_bearing_housing import inspect_housing
    housing_report=inspect_housing(part,v)
    z.update(output_nut_cylinder=-v['housing_lip_depth'],output_cap_cylinder=v['stack_height']+v['housing_lip_depth'])
    from gearbox_native.stacked_disc_shaft import NAMES, stations
    shaft_z=stations(v)
    shapes={}
    for name in POSITIONS:
        if name in (FOOT,'output_circle_plate'):continue
        s=read_step(part/(name+'.step'))
        if name in NAMES:
            _,_,flip,reverse,station,_=NAMES[name]
            if flip:
                s=_move(s,'rotate',[180,0,0])
                s=_move(s,'rotate',[0,0,-90])
            s=_move(s,'rotate',[0,0,225 if reverse else 45])
            z[name]=shaft_z[name]
        if name in ('output_nut_plate','output_cap_cylinder','carrier_bottom','carrier_top_cap','rotor_b','rotor_a_cap','round_shim_bottom','shaft_bush_bottom','eccentric_spacer_a'):
            s=_move(s,'rotate',[180,0,0])
        x={'rotor_a':v['eccentricity'],'rotor_b':-v['eccentricity'],'rotor_a_cap':v['eccentricity'],'rotor_b_cap':-v['eccentricity']}.get(name,0)
        shapes[name]=_move(s,'translate',[x,0,z[name]])
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    def bounds(shape):
        box=Bnd_Box();BRepBndLib.Add_s(shape,box);return box.Get()
    boxes={name:bounds(s) for name,s in shapes.items()}
    checks=0;max_overlap=0.
    def clear(label,s,names):
        nonlocal checks,max_overlap
        a=bounds(s)
        for n in names:
            b=boxes[n];checks+=1
            if any(a[i+3]<b[i] or b[i+3]<a[i] for i in range(3)):continue
            delta=overlap(s,shapes[n]);assert delta<.03,(label,n,delta)
            max_overlap=max(max_overlap,delta)
    names=list(shapes)
    for i,n in enumerate(names):clear(n,shapes[n],names[i+1:])
    height=v['stack_height']
    face=v['shaft_face_z']; pitch=v['shaft_tie_pitch']; length=v['shaft_tie_length']
    clear('open_diameter_6_50',cylinder(v['shaft_open_bore']-.001,height-2*face+2,[0,0,face-1]),names)
    for bottom in (True,False):
        side='lower' if bottom else 'upper'; y=-pitch if bottom else pitch
        seat=face+v['shaft_head_depth'] if bottom else height-face-v['shaft_head_depth']
        clear('shaft_M3x35',cylinder(1.5,length,[0,y,seat if bottom else seat-length]),names)
        clear('shaft_socket',cylinder(2.75,3,[0,y,seat-3 if bottom else seat]),names)
        nut_z=face+v['shaft_nut_depth']-2.5 if bottom else height-face-v['shaft_nut_depth']
        clear('shaft_tie_nut',hexagon('m3',2.5,[0,-y,nut_z],0),names)
        for i in range(4):
            theta=math.radians(i*90+45)
            x,y2=7.5*math.cos(theta),7.5*math.sin(theta)
            z0=v['shaft_end_station']+v['shaft_nut_depth']-2.5 if bottom else height-v['shaft_end_station']-v['shaft_nut_depth']
            clear('shaft_mount_nut',hexagon('m3',2.5,[x,y2,z0],75+i*90),names)
            clear('shaft_mount_shank',cylinder(1.5,v['shaft_end_depth']+v['shaft_mount_depth'],[x,y2,face if bottom else height-face-v['shaft_end_depth']-v['shaft_mount_depth']]),names)
    engagement=length-(height-2*face-v['shaft_head_depth']-v['shaft_nut_depth'])
    assert 2.5<=engagement<=v['shaft_nut_depth']
    # The STEP shapes are localized in print coordinates; check every repeated blank.
    canonical={}
    for name,(_,kind,*_) in NAMES.items():
        sh=read_step(part/(name+'.step'))
        if kind not in canonical:canonical[kind]=sh
        else:
            from OCP.BRepGProp import BRepGProp
            from OCP.GProp import GProp_GProps
            props=GProp_GProps();BRepGProp.VolumeProperties_s(sh,props)
            assert abs(props.Mass()-overlap(sh,canonical[kind]))<.01,(name,kind)

    for i in range(int(v['ring_count'])):
        a=i*math.tau/v['ring_count'];x=v['pitch']*math.cos(a);y=v['pitch']*math.sin(a)
        clear('M3_contact_screw',cylinder(1.5,v['join_length'],[x,y,0]),['output_cap_plate','output_nut_plate',*CYLINDERS])
        clear('M3_contact_cap',cylinder(2.75,3,[x,y,v['join_length']]),[CYLINDERS[1]])
        clear('M3_contact_nut',hexagon('m3',2.4,[x,y,0],math.degrees(a)),[CYLINDERS[0]])
    # Verify the ring screws bear on each cylinder and both flange lands touch.
    for name,z_land in [('output_nut_cylinder',2.65+.65),('output_cap_cylinder',v['join_length']-.01)]:
        land=cylinder(2.75,.15,[v['pitch'],0,z_land if name==CYLINDERS[0] else z_land-.15])
        # The first printable bridge leaves two lands under a socket head.
        assert overlap(land,shapes[name]) / .15 > 5,('missing clamp land',name)

    pairs=[v['guide_pair_'+key] for key in 'abc']
    guide_degrees=pairs+[a+180 for a in pairs]
    expected_axes=[np.array([math.cos(math.radians(a)),math.sin(math.radians(a))])*v['guide_pitch'] for a in guide_degrees]
    # The tracks translate in a circle while the guide sleeves remain stationary.
    # Measure the actual printed tracks, including the mirrored halves, in disc coordinates.
    min_motion_gap=float('inf')
    for name in ('rotor_a','rotor_a_cap','rotor_b','rotor_b_cap'):
        from gearbox_native.guide_assembly_fit import track_wires
        import trimesh
        from shapely.geometry import Polygon
        shape=read_step(part/(name+'.step'))
        working=track_wires(shape,v['guide_track'])
        entry=track_wires(shape,v['guide_track']+v['guide_entry'])
        tracks=[dict(axis_origin_mm=xy,radius_mm=r) for r,xy in working]
        for r,xy in working:assert min(np.linalg.norm(xy-c) for _,c in entry)<.002
        # Check the axial shape in the production tessellation too, including the
        # transition at the end of the lead-in and the full-depth working bore.
        mesh=trimesh.load_mesh(part/(name+'.stl'))
        for level in (.04,v['guide_entry']/2,v['guide_entry']+.03,v['disc_half']/2,v['disc_half']-.04):
            path=mesh.section(plane_normal=[0,0,1],plane_origin=[0,0,level])
            loops=[Polygon(curve[:,:2]) for curve in path.discrete]
            radius=v['guide_track']+max(0,v['guide_entry']-level)
            for _,xy in working:
                hole=min(loops,key=lambda q:np.linalg.norm(np.array(q.centroid.coords[0])-xy))
                boundary=np.array(hole.exterior.coords)
                assert max(abs(np.linalg.norm(boundary-xy,axis=1)-radius))<.04,(name,level)
        mirror=-1 if name in ('rotor_a_cap','rotor_b') else 1
        for axis in expected_axes:
            err,f=min(((np.linalg.norm(axis-np.array(t['axis_origin_mm'][:2])*[1,mirror]),t) for t in tracks),key=lambda pair:pair[0])
            assert err<.001,(name,axis,err)
            min_motion_gap=min(min_motion_gap,f['radius_mm']-err-v['eccentricity']-v['contact_radius'])
    assert min_motion_gap>.149
    for angle in guide_degrees:
        a=math.radians(angle)
        x=v['guide_pitch']*math.cos(a);y=v['guide_pitch']*math.sin(a)
        clear('round_drive_sleeve',cylinder(v['contact_radius'],v['middle_length'],[x,y,v['middle_start']]),['rotor_a','rotor_a_cap','rotor_b','rotor_b_cap','carrier_bottom','carrier_top'])
        tip=v['drive_tip'];length=v['carrier_drive_length']
        assert length==35
        clear('drive_M3_join',cylinder(1.5,length,[x,y,tip]),names)
        clear('drive_cap',cylinder(2.75,3,[x,y,tip+length]),names)
        clear('drive_nut',hexagon('m3',2.4,[x,y,tip],math.degrees(a)),names)
        for sign,label,stock,z0,radius in ((1,'nut','carrier_bottom_cap',tip+2.4,2.7),
                                           (-1,'head','carrier_top_cap',tip+length,2.75)):
            land=cylinder(radius,.2,[x,y,z0+.65 if sign==1 else z0-.2])
            assert overlap(land,shapes[stock])>1, ('missing clamp land',label)
    for size,points in output_mounts(v['bearing_ring_radius']).items():
        length=5 if size=='m6' else 2.4
        for x,y in points:
            for name,z0 in [('output_cap_plate',v['middle_end']+v['mount_flange_depth']),('output_nut_plate',v['middle_start']-v['mount_flange_depth']-length)]:
                clear('external_nut_loading',hexagon(size,length,[x,y,z0],0),[name,*CYLINDERS])
                clear('mount_shank',cylinder(3 if size=='m6' else 1.5,height,[x,y,0]),[name])
    for n,zflat,zclear in [('output_cap_plate',v['middle_end'],v['middle_end']+3),
                           ('output_nut_plate',v['middle_start']-3,0)]:
        assert overlap(cylinder(.5,3,[38,40,zflat]),shapes[n])>2.35
        clear('mount_flange_depth',cylinder(.5,6,[38,40,zclear]),[n])
    from gearbox_native.simple_double_bearing import carrier_mounts
    # Check the full mating planes and the actual pocket mouths on both production meshes.
    from shapely.geometry import Polygon
    import trimesh
    from oobb_solidcraft import api as oobb
    pocket_error=0.
    # Measure material between neighboring recesses, including the OOBB bridge
    # layers. Use the middle of each distinct axial interval in the printed mesh.
    recess_webs={}
    for base in ('carrier_bottom','carrier_top','rotor_a','rotor_b'):
        for name in (base,base+'_cap'):
            mesh=trimesh.load_mesh(part/(name+'.stl'))
            levels=np.unique(np.round(mesh.vertices[:,2],3))
            carrier=name.startswith('carrier')
            mounts=carrier_mounts() if carrier else None
            pitch=math.hypot(*mounts[0]) if carrier else v['clamp_pitch']
            smallest=float('inf')
            for lo,hi in zip(levels,levels[1:]):
                if hi-lo<.015:continue
                section=mesh.section(plane_normal=[0,0,1],plane_origin=[0,0,(lo+hi)/2])
                loops=[Polygon(q[:,:2]) for q in section.discrete]
                def at_radius(r):
                    return [p for p in loops if abs(math.hypot(p.centroid.x,p.centroid.y)-r)<.2]
                holes,guides=at_radius(pitch),at_radius(v['guide_pitch'])
                assert len(holes)==(8 if carrier else 3) and len(guides)==6,(name,lo,hi)
                smallest=min(smallest,min(p.distance(q) for p in holes for q in guides))
            assert 0<smallest<float('inf'),name
            recess_webs[name]=round(smallest,3)
    for bottom in (True,False):
        name='carrier_bottom' if bottom else 'carrier_top'
        plane=v['carrier_split'] if bottom else height-v['carrier_split']
        assert abs(boxes[name][2 if bottom else 5]-plane)<.001
        rim_end=v['main_inner_face'] if bottom else height-v['main_inner_face']
        assert abs(boxes[name+'_cap'][5 if bottom else 2]-rim_end)<.001
        assert abs(plane-rim_end)<.001, (name,'split must be flat at 6810 inner face')
        mesh=trimesh.load_mesh(part/(name+'.stl'))
        section=mesh.section(plane_normal=[0,0,1],plane_origin=[0,0,v['carrier_core']-.1])
        loops=[Polygon(q[:,:2]) for q in section.discrete]
        for x,y in carrier_mounts():
            if bottom:y=-y
            angle=math.atan2(y,x)+math.pi/6
            radius=oobb.gv('nut_radius_m3','3dpr')
            expected=Polygon([(x+radius*math.cos(angle+j*math.pi/3),y+radius*math.sin(angle+j*math.pi/3)) for j in range(6)])
            pocket_error=max(pocket_error,min(expected.hausdorff_distance(poly) for poly in loops))
    assert pocket_error<.03,('mount nut pocket differs from the plain OOBB hex',pocket_error)
    for x,y in carrier_mounts():
        angle=math.degrees(math.atan2(y,x))+30
        for side in ('bottom','top'):
            n='carrier_'+side
            split=v['carrier_split']
            base=split+.1 if side=='bottom' else height-split-2.5
            clear('embedded_grid_nut',hexagon('m3',2.4,[x,y,base],angle),[n,n+'_cap'])
            low=-v['carrier_extension'] if side=='bottom' else v['middle_end']
            clear('grid_through',cylinder(1.5,v['plate_height']+v['carrier_extension'],[x,y,low]),[n,n+'_cap'])
            # Load the nut through the open flat split before closing the cap.
            start=base-4 if side=='bottom' else base
            clear('grid_nut_loading',hexagon('m3',6.4,[x,y,start],angle),[n])
            assert overlap(hexagon('m3',.25,[x,y,split-.25 if side=='bottom' else height-split],angle),shapes[n+'_cap'])>1
    alternative=_move(read_step(part/'connected_contact_ring.step'),'translate',[0,0,v['middle_start']])
    clear('connected_ring',alternative,names)
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeCone
    assembled_health=json.loads((part.parent/'assembled_health.json').read_text())
    native_boxes={b['name']:b['bbox'] for b in assembled_health['bodies']}
    rotor_clamps={}
    for side in ('a','b'):
        base=v['disc_a_z'] if side=='a' else v['disc_b_z']+v['disc_thickness']
        for i in range(3):
            angle=math.radians(v['clamp_phase']+i*120)
            x=v['clamp_pitch']*math.cos(angle)+(v['eccentricity'] if side=='a' else -v['eccentricity'])
            y=v['clamp_pitch']*math.sin(angle)
            screw_name=f'hardware_disc_{side}_M3x6_{i+1}'
            fastener=native_boxes[screw_name]
            nut=native_boxes[f'hardware_disc_{side}_nut_{i+1}']
            exterior='min' if side=='a' else 'max'
            head_error=abs(fastener[exterior][2]-native_boxes['rotor_'+side][exterior][2])
            engaged=min(nut['max'][2],fastener['max'][2])-max(nut['min'][2],fastener['min'][2])
            assert head_error<.002 and abs(engaged-1.75)<.002,(screw_name,head_error,engaged)
            rotor_clamps[screw_name]=dict(head_face_error_mm=round(head_error,4),nut_engagement_mm=round(engaged,4))
            tools=[('flush_countersink',BRepPrimAPI_MakeCone(3.,1.5,1.5).Shape()),
                   ('disc_screw',cylinder(1.5,4.5,[0,0,1.5])),('disc_nut',hexagon('m3',2.4,[0,0,4.25],0))]
            # A seated Ø6 head clears at the disc surface but cannot sink another 0.2 mm.
            sink=_move(tools[0][1],'translate',[0,0,.2])
            if side=='b':sink=_move(sink,'rotate',[180,0,0])
            assert overlap(_move(sink,'translate',[x,y,base]),shapes['rotor_'+side])>.1
            for label,tool in tools:
                if side=='b':tool=_move(tool,'rotate',[180,0,0])
                clear(label,_move(tool,'translate',[x,y,base]),names)
    from gearbox_native.exact_geometry import _boolean
    def band(r1,r2,z,depth,x=0):
        return _boolean('cut',cylinder(r2,depth,[x,0,z]),[cylinder(r1,depth+.02,[x,0,z-.01])])

    # Each row names both inner supports and both outer supports, low-Z end first.
    races=[]
    for lower in (True,False):
        core='carrier_bottom' if lower else 'carrier_top'
        end='lower' if lower else 'upper'
        cap=core+'_cap'
        outside=CYLINDERS[0 if lower else 1]
        plate='output_nut_plate' if lower else 'output_cap_plate'
        def order(a,b):return (a,b) if lower else (b,a)
        races.append(('6810_'+end,25,32.5,7,0,v['main_outer_face'] if lower else height-v['main_inner_face'],
                      order(cap,core),order(outside,plate)))
        races.append(('6704_'+end,10,13.5,4,0,v['race_end_gap'] if lower else height-v['race_end_gap']-4,
                      order('shaft_end_'+end,'shaft_mount_'+end),order(cap,core)))
    for side,sign in [('a',1),('b',-1)]:
        pair=('outer','inner') if sign==1 else ('inner','outer')
        rotor='rotor_'+side
        races.append(('6704_disc_'+side,10,13.5,4,sign*v['eccentricity'],v['disc_'+side+'_z']+v['disc_lip'],
                      ['shaft_cam_'+side+'_'+member for member in pair],
                      (rotor,rotor+'_cap') if sign==1 else (rotor+'_cap',rotor)))
    lands={};pilots={};insertion={}
    for label,ri,ro,width,x,z0,inner,outer in races:
        clear(label,band(ri,ro,z0,width,x),names)
        large=ri==25
        pilot=band(ri-.18,ri-.10,z0,width,x)
        from gearbox_native.verify_native_v8 import volume
        owners=[inner[0] if label=='6810_lower' else inner[1]] if large else set(inner)
        coverage=sum(overlap(pilot,shapes[n]) for n in owners)/volume(pilot)
        assert coverage>.999,(label,'interrupted journal',coverage)
        pilots[label]=round(coverage,5)
        inner_strip=(25.35,26.0) if large else (10.24,10.65)
        outer_strip=(31.9,32.18) if large else (12.92,13.25)
        seal_strip=(27.0,30.5) if large else (11.15,12.45)
        faces={}
        for i,side in enumerate(('low','high')):
            depth=.16
            z=z0-depth if i==0 else z0+width
            for race,strip,owner in [('inner',inner_strip,inner[i]),('outer',outer_strip,outer[i])]:
                probe=z
                if large and race=='outer' and owner in CYLINDERS:
                    probe+=(-1 if i==0 else 1)*v['housing_race_allowance']
                contact=overlap(band(*strip,probe,depth,x),shapes[owner])
                assert contact>1,(label,race,side,owner,contact)
                faces[race+'_'+side]=owner
            clear(label+'_seal_face',band(*seal_strip,z,depth,x),names)
        if label.startswith('6704_disc'):
            # The entire swept volume of the moving bearing when lowered straight
            # onto the first C journal. The opposite C half is fitted afterwards.
            approach=band(ri,ro,z0,width+v['middle_length'],x)
            clear(label+'_insertion_with_one_cam',approach,[inner[0]])
            blocked=overlap(approach,shapes[inner[1]])
            assert blocked>1,(label,'second shoulder should capture the bearing')
            insertion[label]=dict(fit_first=inner[0],fit_after_disc=inner[1],closed_pair_obstruction_mm3=round(blocked,3))
        lands[label]=faces
    from gearbox_native.guide_assembly_fit import guide_fit
    drive=guide_fit(part.parent/'assembled.step',part.parent/'assembled_health.json',v)
    from gearbox_native.shaft_sections import shaft_sections
    return dict(rotor_clamps=rotor_clamps,flat_carrier_split_mm=v['carrier_split'],disc_insertion_from_upper_end=insertion,journal_width_coverage=pilots,race_contacts=lands,assembled_guide_sweep=drive,shaft_sections=shaft_sections(part,v),shaft_unique_blanks=len(canonical),shaft_stack_parts=len(NAMES),shaft_open_bore_mm=2*v['shaft_open_bore'],shaft_nut_engagement_mm=min(2.5,engagement),shaft_screw_past_nut_mm=engagement-2.5,output_housing=housing_report,clearance_checks=checks,maximum_overlap_mm3=max_overlap,
                guide_to_mount_or_disc_clamp_web_mm=recess_webs,
                confirmed_bearing_stops_per_carrier=2,maximum_hex_pocket_profile_error_mm=pocket_error,min_orbit_guide_clearance_mm=min_motion_gap,carrier_grid_mounts_per_end=len(carrier_mounts()),guide_screw_mm=v['carrier_drive_length'],confirmed_bearing_stops_per_disc=2,disc_half_thickness_mm=v['disc_half'],
                mount_flange_thickness_mm=v['mount_flange_depth'],motion=swept(v,profile))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);args=p.parse_args()
    print(edit(args.folder.resolve()))
