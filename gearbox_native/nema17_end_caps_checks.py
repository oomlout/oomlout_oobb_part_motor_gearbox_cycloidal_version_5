"""Actual native-solid clearances for the stationary covers and rear output."""
import json
import itertools
import math
import hashlib
import shutil
from pathlib import Path
import numpy as np
from OCP.TopAbs import TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from gearbox_native.verification import read_step
from gearbox_native.verify_assembly_sequence import bounds,intersect_boxes
from gearbox_native.nema17_outputs import overlap
from gearbox_native.nema17_end_caps import PROJECT,PART_ID,BUILDERS
from gearbox_native.exact_geometry import _move


def named_shapes(step,health):
    declared={b['name']:np.array(b['bbox']['min']+b['bbox']['max']) for b in health['bodies'] if b['name']!='connected_contact_ring'}
    shapes={};it=TopExp_Explorer(read_step(step),TopAbs_SOLID)
    while it.More():
        s=it.Current();it.Next();bb=bounds(s)
        matches=[n for n,b in declared.items() if np.max(abs(b-bb))<.04]
        assert len(matches)==1,(matches,bb)
        shapes[matches[0]]=s
    return shapes


def check_pairs(shapes,changed):
    boxes={n:bounds(s) for n,s in shapes.items()};clashes=[];count=0;maximum=0
    for a,b in itertools.combinations(shapes,2):
        if not ({a,b}&set(changed)) or not intersect_boxes(boxes[a],boxes[b]):continue
        amount=overlap(shapes[a],shapes[b]);count+=1;maximum=max(maximum,amount)
        if amount>.03:clashes.append(dict(a=a,b=b,overlap_mm3=amount))
    return dict(checks=count,maximum_overlap_mm3=maximum,clashes=clashes)


def preflight(parts,old_views):
    old=json.loads((old_views/'assembled_health.json').read_text(encoding='utf8'))
    shapes=named_shapes(old_views/'assembled.step',old);shapes.pop('motor_cage')
    poses={'motor_cage':(False,-68),'front_cover_spacer':(False,37),
           'front_cover_nuts':(False,45),'front_cover_face':(True,54),
           'rear_cover_nuts':(True,-68),'rear_cover_face':(False,-77),'rear_output_extension':(False,-77)}
    for name,(flip,z) in poses.items():
        s=read_step(parts/(name+'.step'))
        if flip:s=_move(s,'rotate',[180,0,0])
        shapes[name]=_move(s,'translate',[0,0,z])
    result=check_pairs(shapes,poses)
    (parts.parent/'preflight.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    assert not result['clashes'],result['clashes']
    print('STATIC PREFLIGHT PASSED',result['checks'],flush=True)
    return shapes,result


def write_compound(shapes,path):
    from OCP.BRep import BRep_Builder
    from OCP.TopoDS import TopoDS_Compound
    from OCP.STEPControl import STEPControl_Writer,STEPControl_AsIs
    from OCP.IFSelect import IFSelect_RetDone
    builder=BRep_Builder();compound=TopoDS_Compound();builder.MakeCompound(compound)
    for shape in shapes:builder.Add(compound,shape)
    writer=STEPControl_Writer();writer.Transfer(compound,STEPControl_AsIs)
    assert writer.Write(str(path))==IFSelect_RetDone


def verify_core(views):
    """Repeat the accepted motor assembly audit before fitting the new covers."""
    from gearbox_native.nema17_outputs import verify
    report=json.loads((views/'export.json').read_text(encoding='utf8'))
    folder=views/'motor_core_check';folder.mkdir(exist_ok=True)
    cached=folder/'motor_fit.json'
    if cached.exists():
        r=json.loads(cached.read_text(encoding='utf8'))
        if r.get('status')=='passed' and r.get('source_sha256')==report['source_sha256']:return r
    health=json.loads((views/'assembled_health.json').read_text(encoding='utf8'))
    shapes=named_shapes(views/'assembled.step',health)
    from gearbox_native.nema17_end_caps import REVISED_PLATES
    extra=set(BUILDERS)-{'motor_cage'}-REVISED_PLATES
    keep={n:s for n,s in shapes.items() if n not in extra and not n.startswith('hardware_endcap_')}
    health['bodies']=[b for b in health['bodies'] if b['name'] in keep]
    write_compound(keep.values(),folder/'assembled.step')
    (folder/'assembled_health.json').write_text(json.dumps(health),encoding='utf8')
    (folder/'export.json').write_text(json.dumps(report),encoding='utf8')
    (folder/'parts').mkdir(exist_ok=True)
    for name in ('motor_cage','motor_inner_adapter'):shutil.copyfile(views/'parts'/(name+'.stl'),folder/'parts'/(name+'.stl'))
    result=verify(folder);result['scope']='Motor and gearbox core before installing the stationary covers and rear output extension'
    return result


def verify(views):
    from gearbox_native.nema17_outputs import MotorAudit
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
    from OCP.gp import gp_Ax2,gp_Pnt,gp_Dir
    from gearbox_native.nema17_end_caps import EXTENSION_JOINS,EXTENSION_POSTS,JOINER_ANGLES,SPACER_JOINS,mount_layout
    report=json.loads((views/'export.json').read_text(encoding='utf8'));v={p['name']:p['value'] for p in report['parameters']['parameters']}
    cached=views/'end_cover_fit.json'
    if cached.exists():
        r=json.loads(cached.read_text(encoding='utf8'))
        if r.get('status')=='passed' and r.get('source_sha256')==report['source_sha256']:
            if 'captured_mounting_nuts' not in r:
                health=json.loads((views/'assembled_health.json').read_text(encoding='utf8'))
                r['captured_mounting_nuts']=verify_captive_mounts(named_shapes(views/'assembled.step',health))
                cached.write_text(json.dumps(r,indent=2),encoding='utf8')
            if 'printability' not in r and all((views/'parts'/(n+'.stl')).exists() for n in BUILDERS):
                from gearbox_native.split_stack import layer_audit
                import trimesh
                r['printability']={n:layer_audit(trimesh.load_mesh(views/'parts'/(n+'.stl'))) for n in BUILDERS}
                assert all(v['unsupported_islands']==0 for v in r['printability'].values())
                cached.write_text(json.dumps(r,indent=2),encoding='utf8')
            return r
    health=json.loads((views/'assembled_health.json').read_text(encoding='utf8'))
    shapes=named_shapes(views/'assembled.step',health)
    changed=set(BUILDERS)|{n for n in shapes if n.startswith('hardware_endcap_')}
    result=check_pairs(shapes,changed)
    result.update(source_sha256=report['source_sha256'],physical_fit_tested=False)
    cached.write_text(json.dumps(result,indent=2),encoding='utf8')
    assert not result['clashes'],result['clashes']
    boxes={n:bounds(s) for n,s in shapes.items()}
    if 'motor_tube_wall' in v:
        # Physical material probes prove the new parts are a tube and three
        # connected oblong posts, not just renamed collections of cylinders.
        probes=[]
        for angle in range(0,360,45):
            r=v['motor_clear_radius']+v['motor_tube_wall']/2
            x,y=r*math.cos(math.radians(angle)),r*math.sin(math.radians(angle))
            z=v['motor_cage_base']+v['motor_cage_height']/2
            probe=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(0,0,1)),.25,.5).Shape()
            amount=overlap(probe,shapes['motor_cage'])
            assert amount>math.pi*.25**2*.5-.0001,('Tube wall missing',angle,amount)
            probes.append(dict(angle=angle,material_mm3=amount))
        webs=[]
        for i,pair in enumerate(EXTENSION_POSTS):
            x,y=np.mean(pair,axis=0);z=v['rear_extension_base']+v['rear_extension_height']/2
            probe=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(0,0,1)),.25,.5).Shape()
            amount=overlap(probe,shapes[f'rear_output_joiner_{i+1}'])
            assert amount>math.pi*.25**2*.5-.0001,('Post web missing',pair,amount)
            webs.append(dict(screw_axes=pair,material_mm3=amount))
        coupler=[]
        for angle in (45,135,225,315):
            x,y=8*math.cos(math.radians(angle)),8*math.sin(math.radians(angle))
            for name in ('shaft_end_lower','shaft_mount_lower'):
                z=boxes[name][2];height=boxes[name][5]-z
                probe=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(0,0,1)),1.5,height).Shape()
                amount=overlap(probe,shapes[name]);assert amount<.03,(name,angle,'Coupler bore mismatch',amount)
                coupler.append(dict(part=name,angle=angle,bolt_circle_diameter_mm=16,overlap_mm3=amount))
        result['continuous_tube_probes']=probes
        result['paired_post_web_probes']=webs
        result['coupler_6704_bolt_circle_checks']=coupler
    # Actual head envelopes must finish below the mounting faces, with full
    # engagement of the receiving nuts. These checks include changed hardware.
    from gearbox_native.nema17_end_caps import FRONT_JOINS,REAR_JOINS,REVISED_PLATES
    assert v['outer_connection_depth']==3 and v['rear_extension_flange_depth']==3
    assert v['rear_extension_post_radius']>=6.5
    flush=[]
    for i in range(len(FRONT_JOINS)):
        name=f'hardware_endcap_front_join_screw_{i}'
        assert abs(boxes[name][5]-v['front_cover_face_z'])<.001
        assert boxes[name][2]<=v['middle_end']+.5
        stop=overlap(_move(shapes[name],'translate',[0,0,-.3]),shapes['front_cover_face'])
        assert stop>.03,('Missing front countersink seat',name,stop)
        flush.append(dict(screw=name,style='countersunk',face_clearance_mm=v['front_cover_face_z']-boxes[name][5],seat_stop_mm3=stop))
    for i in range(len(REAR_JOINS)):
        name=f'hardware_endcap_rear_join_M3x16_{i}';nut=f'hardware_endcap_rear_join_nut_{i}'
        assert abs(boxes[name][2]-v['rear_cover_face_z'])<.001
        assert boxes[name][5]>=boxes[nut][5]
        stop=overlap(_move(shapes[name],'translate',[0,0,.3]),shapes['rear_cover_face'])
        assert stop>.03,('Missing rear countersink seat',name,stop)
        flush.append(dict(screw=name,style='countersunk',face_clearance_mm=boxes[name][2]-v['rear_cover_face_z'],seat_stop_mm3=stop))
    for i in range(len(EXTENSION_JOINS)):
        name=f'hardware_endcap_outer_extension_screw_{i}';nut=f'hardware_endcap_outer_extension_nut_{i}'
        clearance=v['middle_start']-boxes[name][5]
        assert abs(clearance)<.001 and boxes[name][2]<=boxes[nut][2]
        stop=overlap(_move(shapes[name],'translate',[0,0,-.3]),shapes['output_nut_plate'])
        assert stop>.03,('Missing rear countersink seat',name,stop)
        flush.append(dict(screw=name,style='countersunk',face_clearance_mm=clearance,seat_stop_mm3=stop))
    for i in range(len(EXTENSION_JOINS)):
        name=f'hardware_endcap_outer_ring_screw_{i}';nut=f'hardware_endcap_outer_ring_nut_{i}'
        clearance=boxes[name][2]-v['rear_extension_base']
        assert abs(clearance)<.001 and boxes[name][5]>=boxes[nut][5]
        stop=overlap(_move(shapes[name],'translate',[0,0,.3]),shapes['rear_output_extension'])
        assert stop>.03,('Missing ring countersink seat',name,stop)
        flush.append(dict(screw=name,style='countersunk',face_clearance_mm=clearance,seat_stop_mm3=stop))
    for i in range(len(SPACER_JOINS)):
        name=f'hardware_endcap_spacer_screw_{i}';nut=f'hardware_endcap_spacer_nut_{i}'
        clearance=v['middle_end']+v['mount_flange_depth']-boxes[name][5]
        assert abs(clearance)<.001 and boxes[name][2]<=boxes[nut][2]
        stop=overlap(_move(shapes[name],'translate',[0,0,-.3]),shapes['output_cap_plate'])
        assert stop>.03,('Missing brace countersink seat',name,stop)
        flush.append(dict(screw=name,style='countersunk',face_clearance_mm=clearance,seat_stop_mm3=stop))
    result['flush_joining_heads']=flush
    result['outer_connection_depth_mm']=v['outer_connection_depth']
    result['rear_flange_depth_mm']=v['rear_extension_flange_depth']
    result['rear_post_diameter_mm']=2*v['rear_extension_post_radius']
    result['extension_post_count']=len(EXTENSION_POSTS)
    result['extension_join_count']=len(EXTENSION_JOINS)
    result['motor_tube_wall_mm']=v.get('motor_tube_wall',0)
    # All four access holes and lower countersinks need a complete material
    # rim, including those nearest the square plate's extended lower edge.
    support=[]
    for name in ('output_cap_plate','output_nut_plate','output_circle_plate','output_circle_rear_plate',
                 'output_lower_row_plate','output_lower_row_rear_plate'):
        cx=(boxes[name][0]+boxes[name][3])/2
        for x,y in EXTENSION_JOINS:
            axis=gp_Ax2(gp_Pnt(cx+x,y,boxes[name][5]-.4),gp_Dir(0,0,1))
            outer=BRepPrimAPI_MakeCylinder(axis,4.1,.3).Shape()
            inner=BRepPrimAPI_MakeCylinder(axis,3.4,.3).Shape()
            rim=BRepAlgoAPI_Cut(outer,inner);rim.Build();assert rim.IsDone()
            expected=math.pi*(4.1**2-3.4**2)*.3
            material=overlap(rim.Shape(),shapes[name])
            assert material>=expected-.001,(name,'Incomplete attachment rim',x,y,material,expected)
            support.append(dict(plate=name,xy_mm=[x,y],complete_material_rim=True))
    result['complete_attachment_rims']=support
    # Substitute both optional plates in their working positions.
    for label,front,rear in [('circular','output_circle_plate','output_circle_rear_plate'),
                             ('asymmetric','output_lower_row_plate','output_lower_row_rear_plate')]:
        variant=dict(shapes);del variant['output_cap_plate'];del variant['output_nut_plate']
        for name in (front,rear):
            center=(boxes[name][0]+boxes[name][3])/2
            variant[name]=_move(variant[name],'translate',[-center,0,0])
        proof=check_pairs(variant,{front,rear});assert not proof['clashes'],(label,proof)
        result[label+'_plate_pair_fit']=proof
    proud=boxes['rear_output_extension'][2]-boxes['rear_cover_face'][2]
    assert abs(proud-v['rear_holder_proud'])<.001 and abs(proud-1.5)<.001
    assert v['rear_extension_screw_length']==10 and v['cage_join_length']==16
    assert abs(v['rear_extension_height']-(v['main_inner_face']-v['rear_extension_base']))<.001
    result['rear_holder_proud_mm']=proud
    result['extension_join_screw_mm']=v['rear_extension_screw_length']
    result['brace_screw_mm']=v['outer_spacer_screw_length']
    result['cage_join_screw_mm']=v['cage_join_length']
    result['bracket_full_rows_y_mm']=[-v['bracket_full_row_start'],-v['bracket_full_row_start']-15]
    result['fixed_rear_flange_radial_clearance_mm']=v['rear_extension_inner']-v['cover_radius']-.3
    result['front_shaft_axial_clearance_mm']=v['front_cover_inner']-boxes['shaft_end_upper'][5]
    result['front_carrier_axial_clearance_mm']=v['front_cover_inner']-boxes['carrier_top_cap'][5]
    result['rear_cover_motor_clearance_mm']=boxes['hardware_NEMA17_motor'][2]-boxes['rear_cover_nuts'][5]
    assert min(result[k] for k in ('fixed_rear_flange_radial_clearance_mm','front_shaft_axial_clearance_mm','rear_cover_motor_clearance_mm'))>=1.19

    # Continuous 360-degree sweep: a conservative annulus contains every post
    # and its fastener; a second annulus contains the entire rotating flange.
    def ring(inner,outer,z,height):
        axis=gp_Ax2(gp_Pnt(0,0,z),gp_Dir(0,0,1))
        a=BRepPrimAPI_MakeCylinder(axis,outer,height).Shape();b=BRepPrimAPI_MakeCylinder(axis,inner,height).Shape()
        cut=BRepAlgoAPI_Cut(a,b);cut.Build();assert cut.IsDone();return cut.Shape()
    from shapely.geometry import LineString,Point
    radii=[math.hypot(*p) for p in EXTENSION_JOINS]
    minimum_post_radius=min(LineString(pair).distance(Point(0,0)) for pair in EXTENSION_POSTS)
    sweeps=[ring(v['rear_extension_inner'],v['circle_plate_radius'],v['rear_extension_base'],v['rear_extension_flange_depth']),
            ring(minimum_post_radius-v['rear_extension_post_radius'],max(radii)+v['rear_extension_post_radius'],v['rear_extension_base'],
                 v['middle_end']+v['mount_flange_depth']+3-v['rear_extension_base'])]
    moving=lambda n:n.startswith(('output_','rear_output_','hardware_endcap_outer_extension','hardware_endcap_outer_ring','hardware_endcap_spacer'))
    wing_radius=math.hypot(v['housing_plate_half'],v['bracket_lower_edge'])
    sweeps += [ring(v['bearing_ring_radius'],wing_radius,z,v['mount_flange_depth']) for z in (v['main_inner_face'],v['middle_end'])]
    sweep_checks=[]
    for i,sweep in enumerate(sweeps):
        bb=bounds(sweep)
        for n,s in shapes.items():
            if moving(n) or not intersect_boxes(bb,boxes[n]):continue
            amount=overlap(sweep,s)
            assert amount<.03,('Rear output sweep',n,amount)
            sweep_checks.append(dict(envelope=i,part=n,overlap_mm3=amount))
    result['continuous_360_degree_rotation']=dict(clear=True,checks=sweep_checks)

    audit=MotorAudit.__new__(MotorAudit)
    audit.shapes=shapes;audit.boxes=boxes;audit.cache={};audit.records=[];audit.boolean_checks=0;audit.slivers=[];audit.bore_exclusions=[]
    audit.through_bores={'front_cover_spacer':v['front_cover_shaft_clearance']-.05,'rear_output_extension':v['rear_extension_inner']-.05}
    base=[n for n in shapes if n not in set(BUILDERS)-{'motor_cage'}-REVISED_PLATES and not n.startswith('hardware_endcap_')]
    rear_nuts=[n for n in shapes if n.startswith('hardware_endcap_rear_join_nut')]
    extension_nuts=[n for n in shapes if n.startswith('hardware_endcap_outer_extension_nut')]
    installed=base+rear_nuts
    installed+=audit.path('Seat fixed front standoff on the unchanged black carrier',['front_cover_spacer'],installed,60)
    for end,dz in [('front',80),('rear',-80)]:
        mountnuts=[n for n in shapes if n.startswith('hardware_endcap_'+end+'_m') and '_mount_nut_' in n]
        cap=[end+'_cover_face',end+'_cover_nuts']+mountnuts
        installed+=audit.path('Fit '+end+' stationary cover sandwich',cap,installed,dz)
        screws=[n for n in shapes if n.startswith('hardware_endcap_'+end+'_join_') and 'nut' not in n]
        installed+=audit.path('Seat '+end+' cover countersunk screws',screws,installed,dz)
    ring_nuts=[n for n in shapes if n.startswith('hardware_endcap_outer_ring_nut')]
    installed+=audit.path('Slide three independent joiners onto the gearbox attachment face',
                          [f'rear_output_joiner_{i}' for i in range(1,4)]+extension_nuts+ring_nuts,installed,-120)
    installed+=audit.path('Seat separate rear output ring against all three joiners',
                          ['rear_output_extension'],installed,-120)
    ring_screws=[n for n in shapes if n.startswith('hardware_endcap_outer_ring_screw')]
    installed+=audit.path('Seat rear ring countersunk screws',ring_screws,installed,-60)
    # Sleeves enter radially between the two existing outer plates before bolts.
    # Their solid outer cylinder swept along the line is an exact conservative
    # envelope; filling the empty screw bore cannot conceal a collision.
    from shapely.geometry import LineString
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon,BRepBuilderAPI_MakeFace
    from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
    from OCP.gp import gp_Vec
    sleeve_paths=[]
    for i,(x,y) in enumerate(SPACER_JOINS):
        name=f'rear_output_spacer_{i+1}';r=math.hypot(x,y);dx,dy=40*x/r,40*y/r
        outline=LineString([(x,y),(x+dx,y+dy)]).buffer(v['contact_radius']+.002,quad_segs=64)
        wire=BRepBuilderAPI_MakePolygon()
        for a,b in list(outline.exterior.coords)[:-1]:wire.Add(gp_Pnt(a,b,v['middle_start']))
        wire.Close();sweep=BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(wire.Wire()).Face(),gp_Vec(0,0,v['middle_length'])).Shape()
        bb=bounds(sweep);maximum=0
        for n in installed:
            if intersect_boxes(bb,boxes[n]):maximum=max(maximum,overlap(sweep,shapes[n]))
        assert maximum<.03,(name,maximum)
        sleeve_paths.append(dict(part=name,maximum_overlap_mm3=maximum,clear=True));installed.append(name)
    screws=[n for n in shapes if n.startswith('hardware_endcap_outer_extension_screw')]
    installed+=audit.path('Insert rear-extension screws from the accessible front face',screws,installed,60)
    # Separate brace nuts remain reachable from the side, between the posts.
    brace_nuts=[n for n in shapes if n.startswith('hardware_endcap_spacer_nut_')]
    brace_entries=[]
    for name in brace_nuts:
        xy=(boxes[name][:2]+boxes[name][3:5])/2;r=float(np.linalg.norm(xy));delta=[25*xy[0]/r,25*xy[1]/r,0]
        maximum=0
        for swept,bb in audit.sweep(name,delta):
            for other in installed:
                if intersect_boxes(bb,boxes[other]):maximum=max(maximum,overlap(swept,shapes[other]))
        assert maximum<.03,(name,'brace nut access',maximum)
        stop=overlap(_move(shapes[name],'translate',[0,0,.05]),shapes['output_nut_plate'])
        assert stop>.05,(name,'brace nut stop',stop)
        brace_entries.append(dict(nut=name,clear=True,maximum_overlap_mm3=maximum,clamping_stop_mm3=stop))
        installed.append(name)
    brace_screws=[n for n in shapes if n.startswith('hardware_endcap_spacer_screw_')]
    installed+=audit.path('Insert countersunk brace screws through the clocked sleeves',brace_screws,installed,60)
    result['brace_nut_loading']=brace_entries
    # A physical screw and a straight 2.5 mm driver must pass through the
    # front access hole all the way down to each lower attachment head.
    access=[]
    for x,y in EXTENSION_JOINS:
        tool=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,v['middle_start']),gp_Dir(0,0,1)),1.25,70).Shape()
        maximum=max(overlap(tool,shapes[n]) for n in installed if not n.startswith('hardware_endcap_outer_extension'))
        assert maximum<.03,('Screwdriver access',x,y,maximum)
        access.append(dict(xy_mm=[x,y],driver_diameter_mm=2.5,maximum_overlap_mm3=maximum,clear=True))
    result['extension_driver_access']=access
    result['insertion_paths']=audit.records;result['radial_sleeve_paths']=sleeve_paths

    # Prove side-loading entry directions and real clamping stops, not just a
    # generous empty hex cavity. Rear nuts pull downward; front/outer nuts upward.
    joins=[]
    for prefix,body,sign in [('rear_join_nut','motor_cage',-1),('outer_extension_nut',None,1),('outer_ring_nut',None,-1)]:
        for n in [n for n in shapes if n.startswith('hardware_endcap_'+prefix)]:
            center=(boxes[n][:2]+boxes[n][3:5])/2;r=float(np.linalg.norm(center));delta=[20*center[0]/r,20*center[1]/r,0]
            target=body
            if target is None:
                i=int(n.rsplit('_',1)[1])//2
                target=f'rear_output_joiner_{i+1}'
                angle=math.radians(JOINER_ANGLES[i]);delta=[20*math.cos(angle),20*math.sin(angle),0]
            maximum=0
            for swept,bb in audit.sweep(n,delta):
                if intersect_boxes(bb,boxes[target]):maximum=max(maximum,overlap(swept,shapes[target]))
            assert maximum<.03,(n,'side loading',maximum)
            stop=overlap(_move(shapes[n],'translate',[0,0,.05*sign]),shapes[target])
            assert stop>.05,(n,'missing clamping stop',stop)
            joins.append(dict(nut=n,body=target,entry_overlap_mm3=maximum,clamping_stop_mm3=stop))
    result['side_loaded_clamp_nuts']=joins
    result['mounting_nut_counts']={end:{size:sum(r['size']==size for r in mount_layout(end)) for size in ('m6','m3')} for end in ('front','rear')}
    result['maximum_socket_cap_length_mm']=max(40,v['rear_extension_screw_length'])
    result['captured_mounting_nuts']=verify_captive_mounts(shapes)
    result['conservative_sweep_envelopes']=audit.slivers
    result['status']='passed';cached.write_text(json.dumps(result,indent=2),encoding='utf8')
    print('END COVERS AND REAR OUTPUT PASSED',flush=True);return result


def verify_captive_mounts(shapes):
    result=[]
    for end in ('front','rear'):
        for name,nut in shapes.items():
            if not name.startswith('hardware_endcap_'+end+'_m') or '_mount_nut_' not in name:continue
            stops=[]
            for delta in (-.5,.5):
                moved=_move(nut,'translate',[0,0,delta])
                stop=sum(overlap(moved,shapes[end+'_cover_'+half]) for half in ('face','nuts'))
                assert stop>.05,('Mounting nut is not captured',name,delta,stop)
                stops.append(stop)
            result.append(dict(nut=name,axial_escape_blocked_both_directions=True,stop_volumes_mm3=stops))
    assert len(result)==65
    return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('views',type=Path)
    args=parser.parse_args();verify(args.views.resolve());verify_core(args.views.resolve())
