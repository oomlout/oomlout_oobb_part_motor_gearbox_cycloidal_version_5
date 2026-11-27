"""Audit the six actual sleeve axes and disc tracks from the assembled STEP."""
from pathlib import Path
import json
import math
import numpy as np
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder
from OCP.TopAbs import TopAbs_FACE, TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS
from gearbox_native.verification import read_step

def cylinders(solid):
    faces=TopExp_Explorer(solid,TopAbs_FACE)
    result=[]
    while faces.More():
        surface=BRepAdaptor_Surface(TopoDS.Face_s(faces.Current()))
        if surface.GetType()==GeomAbs_Cylinder:
            c=surface.Cylinder()
            if abs(c.Axis().Direction().Z())>.99999:
                result.append((c.Radius(),np.array(c.Location().Coord()[:2])))
        faces.Next()
    return result

def track_wires(solid,expected_radius):
    """Measure circular hole boundaries even when STEP represents a cylinder as two splines."""
    from OCP.BRep import BRep_Tool
    from OCP.BRepTools import BRepTools_WireExplorer
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.GeomAbs import GeomAbs_Plane
    from OCP.TopAbs import TopAbs_WIRE
    faces=TopExp_Explorer(solid,TopAbs_FACE)
    result=[]
    while faces.More():
        face=TopoDS.Face_s(faces.Current());sf=BRepAdaptor_Surface(face);faces.Next()
        if sf.GetType()!=GeomAbs_Plane or abs(sf.Plane().Axis().Direction().Z())<.99999:continue
        wires=TopExp_Explorer(face,TopAbs_WIRE)
        while wires.More():
            wire=TopoDS.Wire_s(wires.Current());wires.Next()
            bounds=Bnd_Box();BRepBndLib.AddOptimal_s(wire,bounds,False,False)
            x0,y0,_,x1,y1,_=bounds.Get()
            if max(abs(x1-x0-2*expected_radius),abs(y1-y0-2*expected_radius))>.02:continue
            edges=BRepTools_WireExplorer(wire);points=[]
            while edges.More():
                curve=BRepAdaptor_Curve(edges.Current());edges.Next()
                for t in np.linspace(curve.FirstParameter(),curve.LastParameter(),16):
                    points.append(curve.Value(t).Coord()[:2])
            xy=np.array(points);x,y=xy.T
            cx,cy,k=np.linalg.lstsq(np.column_stack((2*x,2*y,np.ones(len(x)))),x*x+y*y,rcond=None)[0]
            center=np.array([cx,cy]);r=math.sqrt(k+cx*cx+cy*cy)
            assert np.max(np.abs(np.linalg.norm(xy-center,axis=1)-r))<.002
            if all(np.linalg.norm(center-q[1])>.002 for q in result):result.append((r,center))
    assert len(result)==6,(expected_radius,result)
    return result

def rotor_boundary(solid):
    """Sample the actual outside wire on the largest horizontal disc face."""
    from OCP.BRep import BRep_Tool
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    from OCP.GeomAbs import GeomAbs_Plane,GeomAbs_Line
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.BRepTools import BRepTools,BRepTools_WireExplorer
    faces=TopExp_Explorer(solid,TopAbs_FACE)
    largest=0.
    while faces.More():
        face=TopoDS.Face_s(faces.Current());surface=BRepAdaptor_Surface(face)
        if surface.GetType()==GeomAbs_Plane and abs(surface.Plane().Axis().Direction().Z())>.99999:
            props=GProp_GProps();BRepGProp.SurfaceProperties_s(face,props)
            if props.Mass()>largest:
                largest=props.Mass();outer=BRepTools.OuterWire_s(face)
        faces.Next()
    edges=BRepTools_WireExplorer(outer);points=[]
    while edges.More():
        assert BRepAdaptor_Curve(edges.Current()).GetType()==GeomAbs_Line
        points.append(BRep_Tool.Pnt_s(edges.CurrentVertex()).Coord()[:2]);edges.Next()
    assert len(points)>100
    return np.array(points)

def guide_fit(step,health,v):
    tree=json.loads(Path(health).read_text(encoding='utf8'))['bodies']
    selected={b['name']:np.array(b['bbox']['min']+b['bbox']['max']) for b in tree
              if b['name'].startswith(('rotor_','printed_drive_sleeve','printed_contact_sleeve','hardware_drive_shanks','carrier_'))}
    solids=TopExp_Explorer(read_step(step),TopAbs_SOLID)
    matches={};outlines={};contacts=[];sockets=[]
    while solids.More():
        solid=solids.Current()
        box=Bnd_Box();BRepBndLib.AddOptimal_s(solid,box,False,False)
        for name,bounds in selected.items():
            if max(abs(np.array(box.Get())-bounds))<.04:
                assert name not in matches,name
                matches[name]=cylinders(solid)
                if name in ('carrier_bottom','carrier_top') and 'guide_socket_fit' in v:
                    # STEP may split a cylindrical socket into two faces along its seam.
                    # Measure each complete circular mouth once, as for the rotor tracks.
                    sockets.append(track_wires(solid,v['contact_radius']+v['guide_socket_fit']))
                if name.startswith('rotor_'):
                    outlines[name]=rotor_boundary(solid)
                    matches[name]=[(r,xy) for r,xy in matches[name] if abs(r-v['guide_track'])>=.001]
                    matches[name].extend(track_wires(solid,v['guide_track']))
        solids.Next()
    assert matches.keys()==selected.keys(),selected.keys()-matches.keys()
    sleeves=[]; screws=[]; carriers=[]; discs={}
    for name,faces in matches.items():
        if name.startswith('printed_drive'):
            radii=sorted(faces,key=lambda q:q[0])
            assert len(radii)==2 and np.linalg.norm(radii[0][1]-radii[1][1])<.001
            sleeves.append((radii[1][1],radii[1][0],radii[0][0]))
        if name.startswith('printed_contact_sleeve'):contacts.append(max(faces,key=lambda q:q[0]))
        if name.startswith('hardware_drive_shanks'):
            assert len(faces)==1
            screws.append(faces[0])
        if name.startswith('rotor_'):
            center=next(xy for r,xy in faces if abs(r-v['shaft_race_od']/2-v['seat_fit'])<.001)
            tracks=[(xy-center,r) for r,xy in faces if abs(r-v['guide_track'])<.001]
            assert len(tracks)==6
            discs[name]=(center,tracks)
        if name.startswith('carrier_'):
            holes=[]
            for r,xy in faces:
                if abs(r-1.7)<.001 and all(np.linalg.norm(xy-other)>.002 for other in holes):
                    holes.append(xy)
            assert len(holes)==6,(name,len(holes))
            carriers.append(holes)

    assert len(sleeves)==len(screws)==6 and len(carriers)==len(discs)==4
    minimum=float('inf');worst_alignment=0;float_gap=float('inf')
    for axis,od,id_radius in sleeves:
        screw_r,screw_xy=min(screws,key=lambda q:np.linalg.norm(q[1]-axis))
        worst_alignment=max(worst_alignment,np.linalg.norm(screw_xy-axis),
                            *(min(np.linalg.norm(p-axis) for p in holes) for holes in carriers))
        for center,tracks in discs.values():
            orbit=np.linalg.norm(center)
            assert abs(orbit-v['eccentricity'])<.001
            local,track=min(tracks,key=lambda q:np.linalg.norm(q[0]-axis))
            alignment=np.linalg.norm(local-axis)
            worst_alignment=max(worst_alignment,alignment)
            # Exact worst direction of a circular orbit, including between sampled angles.
            clearance=track-od-orbit-alignment
            minimum=min(minimum,clearance)
            float_gap=min(float_gap,clearance-(id_radius-screw_r))
    assert minimum>.149 and worst_alignment<.001,(minimum,worst_alignment)
    located_gap=None
    if 'guide_socket_fit' in v:
        assert len(sockets)==2 and all(len(row)==6 for row in sockets)
        slack=0.
        for axis,od,_ in sleeves:
            for row in sockets:
                r,xy=min(row,key=lambda q:np.linalg.norm(q[1]-axis))
                slack=max(slack,r-od+np.linalg.norm(xy-axis))
        located_gap=round(float(minimum-slack),4)
        assert located_gap>=.069
    # At every input position find the first sleeve contact for disc twist in
    # either direction. This checks that the fixed sleeves can react torque.
    max_takeup=0.
    for center,tracks in discs.values():
        vectors=[]; limits=[]
        axes=np.array([entry[0] for entry in sleeves])
        for axis,outer,_ in sleeves:
            local,radius=min(tracks,key=lambda q:np.linalg.norm(q[0]-axis))
            vectors.append(local);limits.append(radius-outer)
        vectors=np.array(vectors);limits=np.array(limits)
        tangent=np.column_stack((-vectors[:,1],vectors[:,0]))
        for phase in np.deg2rad(np.arange(360)):
            offset=np.linalg.norm(center)*np.array([np.cos(phase),np.sin(phase)])
            for sign in (-1,1):
                def contact(a):
                    shifted=offset+np.cos(a)*vectors+sign*np.sin(a)*tangent
                    return np.any(np.linalg.norm(shifted-axes,axis=1)>=limits)
                lo,hi=0.,np.deg2rad(3)
                assert contact(hi),'guide sleeve cannot react disc twist'
                for _ in range(16):
                    mid=(lo+hi)/2
                    if contact(mid):hi=mid
                    else:lo=mid
                max_takeup=max(max_takeup,np.rad2deg(hi))
    from shapely.geometry import LinearRing
    from shapely import points as point_array, distance as planar_distance
    ring_axes=np.array([xy for r,xy in contacts])
    assert len(contacts)==int(v['ring_count'])
    ring_radii=np.array([r for r,xy in contacts])
    min_mesh=float('inf')
    for name,(center,_) in discs.items():
        outline=LinearRing(outlines[name]-center)
        for phi in np.deg2rad(np.arange(360)):
            theta=phi/v['ring_count']
            rot=np.array([[np.cos(theta),np.sin(theta)],[-np.sin(theta),np.cos(theta)]])
            orbit=np.array([center[0]*np.cos(phi)-center[1]*np.sin(phi),center[0]*np.sin(phi)+center[1]*np.cos(phi)])
            gap=planar_distance(outline,point_array(ring_axes@rot-orbit))-ring_radii
            min_mesh=min(min_mesh,float(gap.min()))
    assert min_mesh>v['profile_clearance']-.008,(min_mesh,'assembled ring phasing')
    return dict(measured_profile_min_ring_gap_mm=round(min_mesh,4),input_positions=360,max_disc_twist_to_sleeve_contact_deg=round(float(max_takeup),3),tested_torque_directions=2,
                located_full_orbit_gap_mm=located_gap,sleeves=6,disc_halves=4,track_paths=24,max_axis_error_mm=round(float(worst_alignment),6),
                full_orbit_min_radial_gap_mm=round(float(minimum),4),
                gap_with_sleeve_at_bore_limit_mm=round(float(float_gap),4),
                track_diameter_mm=round(2*track,3),sleeve_od_mm=round(2*od,3),sleeve_id_mm=round(2*id_radius,3))
