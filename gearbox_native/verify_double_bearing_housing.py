"""Inspect the actual drill pattern and bearing pocket in print coordinates."""
import math
import numpy as np
import trimesh
from shapely.geometry import Point, Polygon
from gearbox_native.double_bearing_housing import FOOT, CIRCLE, CYLINDERS, output_mounts,NUT_ENVELOPE,CLEARANCE


def section(mesh,z):
    paths=mesh.section(plane_origin=[0,0,z],plane_normal=[0,0,1])
    return sorted([Polygon(loop[:,:2]) for loop in paths.discrete],key=lambda p:-p.area)


def inspect_plate(mesh,name,ring_radius,pitch,count):
    expected=output_mounts(ring_radius,foot=name==FOOT)
    outline,*holes=section(mesh,.2)
    ring=[(pitch*math.cos(i*math.tau/count),pitch*math.sin(i*math.tau/count)) for i in range(count)]
    for size,points,radius in (('m6',expected['m6'],3.25),('m3',expected['m3'],1.8),('lobe',ring,1.7),('lip',[(0,0)],31.65)):
        for x,y in points:
            candidates=[p for p in holes if Point(x,y).distance(p.centroid)<.015]
            assert len(candidates)==1,(name,size,x,y)
            hole=candidates[0]
            assert abs(max(hole.bounds[2]-x,hole.bounds[3]-y)-radius)<.03,(name,size,x,y)
            holes.remove(hole)
    assert not holes,(name,'extra off-grid bores',len(holes))
    edge=15*math.ceil((ring_radius-6.5)/15)
    bbox=[-edge-7,-edge-(22 if name==FOOT else 7),edge+7,ring_radius if name==FOOT else edge+7]
    assert np.allclose(outline.bounds,bbox,atol=.04),(name,outline.bounds,bbox)
    return {size:len(points) for size,points in expected.items()}


def inspect_housing(part,v):
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from gearbox_native.verification import read_step
    from gearbox_native.verify_native_v8 import overlap, volume
    from gearbox_native.verify_v8_hardware import cylinder as round_stock
    from gearbox_native.split_stack import layer_audit
    # Compare all material inside the actual retainer footprint. This includes
    # both bearing shoulders and every lobe through-bore on the interchangeable face.
    footprint=round_stock(v['bearing_ring_radius'],v['mount_flange_depth'],[0,0,0])
    lands=[]
    circle=(part/(CIRCLE+'.step')).exists()
    for name in ('output_cap_plate',FOOT,*([CIRCLE] if circle else [])):
        clip=BRepAlgoAPI_Common(read_step(part/(name+'.step')),footprint)
        clip.Build()
        assert clip.IsDone()
        lands.append(clip.Shape())
    difference=max(abs(volume(lands[0])+volume(stock)-2*overlap(lands[0],stock)) for stock in lands[1:])
    assert abs(difference)<.01,('alternate plate clamp interface',difference)
    depths={}
    layer_checks={}
    for name in ('output_nut_plate','output_cap_plate',FOOT,*CYLINDERS,*([CIRCLE] if circle else [])):
        mesh=trimesh.load_mesh(part/(name+'.stl'))
        assert mesh.is_volume and abs(mesh.bounds[0,2])<.001
        h=mesh.extents[2]
        cylinder=name in CYLINDERS
        if cylinder:
            audit=layer_audit(mesh)
            assert audit['unsupported_islands']==0 and audit['maximum_lateral_reach_mm']<1.8,name
            layer_checks[name]=audit
        assert abs(h-(v['housing_cylinder_depth'] if cylinder else v['mount_flange_depth']))<.001
        # Bearing seats open upwards: follow the inner edge from the bed to the
        # open mouth, across every horizontal feature boundary in the STL.
        levels=np.unique(mesh.vertices[:,2].round(3))
        radii=[]
        section_starts=[]
        for lo,hi in zip(levels,levels[1:]):
            if hi-lo<.015:continue
            _,*holes=section(mesh,(lo+hi)/2)
            center=next(hole for hole in holes if hole.contains(Point(0,0)))
            section_starts.append(lo)
            radii.append(center.bounds[2])
        if cylinder:
            assert min(np.diff(radii))>-.02 and abs(radii[0]-31.65)<.03 and abs(radii[-1]-32.6)<.03,name
            shoulder=next(lo for lo,r in zip(section_starts,radii) if r>32.4)
            assert abs(h-shoulder-v['main_bearing_width']-v['housing_race_allowance'])<.002,name
        else:
            assert all(abs(r-31.65)<.03 for r in radii),(name,'plate bore has a step',radii)
        depths[name]=round(float(h),3)
    grids={name:inspect_plate(trimesh.load_mesh(part/(name+'.stl')),name,v['bearing_ring_radius'],v['pitch'],int(v['ring_count']))
           for name in ('output_nut_plate','output_cap_plate',FOOT)}
    if circle:grids[CIRCLE]=inspect_circle(trimesh.load_mesh(part/(CIRCLE+'.stl')),v)
    return dict(depths_mm=depths, grid_holes=grids, outer_race_stops_per_end=2,
                axial_race_clearance_mm=v['housing_race_allowance'], layer_checks=layer_checks,
                alternative_interface_difference_mm3=abs(difference))


def inspect_circle(mesh,v):
    """Check every real bore and constant thickness, including absence of countersinks."""
    expected={'m6':[],'m3':[]}
    for i in range(-12,13):
        for j in range(-12,13):
            size='m6' if not(i%2 or j%2) else 'm3';r=math.hypot(i*7.5,j*7.5)
            edge=NUT_ENVELOPE[size]+CLEARANCE
            if v['bearing_ring_radius']+edge<=r<=v['circle_plate_radius']-edge:
                expected[size].append((i*7.5,j*7.5))
    counts={size:len(xy) for size,xy in expected.items()}
    stations=[('m6',expected['m6'],v['m6_bore']),('m3',expected['m3'],v['m3_bore']),
              ('ring',[(v['pitch']*math.cos(i*math.tau/v['ring_count']),v['pitch']*math.sin(i*math.tau/v['ring_count'])) for i in range(int(v['ring_count']))],1.7),
              ('bearing lip',[(0,0)],v['main_bearing_od']/2-.85)]
    for z in (.2,v['mount_flange_depth']/2,v['mount_flange_depth']-.2):
        outline,*holes=section(mesh,z)
        assert np.allclose(outline.bounds,[-v['circle_plate_radius']]*2+[v['circle_plate_radius']]*2,atol=.03)
        for size,points,radius in stations:
            for x,y in points:
                match=[p for p in holes if Point(x,y).distance(p.centroid)<.015]
                assert len(match)==1,(size,x,y,z)
                hole=match[0];assert abs(max(hole.bounds[2]-x,hole.bounds[3]-y)-radius)<.03,(size,x,y,z)
                holes.remove(hole)
        assert not holes,('Unexpected circular plate hole',z,len(holes))
    return counts
