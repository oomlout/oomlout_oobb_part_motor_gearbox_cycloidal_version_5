"""Measure the three real print cross sections at the most crowded levels."""
import math
import trimesh
from shapely.geometry import Polygon,Point

def shaft_sections(parts,v):
    def loops(name,z):
        mesh=trimesh.load_mesh(parts/(name+'.stl'))
        p=mesh.section(plane_origin=[0,0,z],plane_normal=[0,0,1])
        return sorted((Polygon(path[:,:2]) for path in p.discrete),key=lambda p:-p.area)
    end,*holes=loops('shaft_end_lower',.05)
    assert len(holes)==7
    def web(out,holes):
        return min([out.exterior.distance(h) for h in holes]+[a.distance(b) for i,a in enumerate(holes) for b in holes[i+1:]])
    e=web(end,holes)
    # STL polygons approximate the circular arcs. Independent nominal head/bore web.
    nominal=v['shaft_tie_pitch']-3-v['shaft_open_bore']
    assert abs(e-nominal)<.02 and e>.24,('end web',e,nominal)
    mount,*holes=loops('shaft_mount_lower',v['shaft_mount_depth']-.05)
    assert len(holes)==7
    n=web(mount,holes);assert n>.34,n
    cam,*holes=loops('shaft_cam_a_outer',v['shaft_cam_depth']-.05)
    assert len(holes)==3
    ties=[h for h in holes if h.centroid.distance(Point(0,0))>1]
    c=min(cam.exterior.distance(h) for h in ties)
    assert abs(c-(v['shaft_journal']-math.hypot(v['eccentricity'],v['shaft_tie_pitch'])-v['shaft_tie_bore']))<.025
    assert all(abs(h.centroid.distance(Point(0,0)))<.01 for h in holes if h not in ties)
    return dict(end_face_minimum_web_mm=round(e,3),end_face_nominal_web_mm=round(nominal,3),
                mounting_carrier_minimum_web_mm=round(n,3),eccentric_journal_to_tie_mm=round(c,3),
                support_to_drive_face_recess_mm=round(v['carrier_extension']+v['shaft_face_z'],3))
