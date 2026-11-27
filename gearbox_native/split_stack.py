"""Print features for the bearing-input M3 tie-bolt stack. Dimensions are in mm."""
from oobb_solidcraft import api as oobb

HALVES = tuple(f'eccentric_hub_{level}_{side}' for level in ('lower','upper') for side in ('a','b'))
STACK = ('bearing_retainer', *HALVES, 'drive_sleeve')
PRINT = dict(zip(HALVES, ((78,215),(98,215),(266,218),(288,202))))


def socket_cap(d):
    # OOBB's unanchored socket cap starts at the underside of the head.
    # Reverse it so the nominal 35 mm shank runs upward along the gearbox axis.
    d.oobb_cut('oobb_screw_socket_cap',position=[0,0,'wiggle_join_head_seat'],
               rotation=[180,0,0],radius_name='m3',depth=35,zz='none',
               nut_include=False,overhang=True)


def channel(d):
    # When the Y=0 split face rests on the bed these inclined roofs close at
    # 45 degrees. The diamond circumscribes the round catalogue clearance.
    r=oobb.gv('hole_radius_m3','3dpr')*2**.5
    d.polygon([[-r,0],[0,-r],[r,0],[0,r]],35.15,z='wiggle_join_head_seat',
              operation='cut',name='support_free_M3_bore')


def clock_key(d,z,depth,socket=False):
    # One clipped corner makes the two 180-degree eccentric phases unambiguous.
    r='wiggle_key_radius' if not socket else '(wiggle_key_radius + sqrt(2) * wiggle_key_clearance)'
    f='wiggle_key_flat' if not socket else '(wiggle_key_flat + wiggle_key_clearance)'
    points=[[f,f'({r}) - ({f})'],[0,r],[f'-({r})',0],[0,f'-({r})'],[f,f'({f}) - ({r})']]
    d.polygon(points,depth,z=z,operation='cut' if socket else 'join',name='asymmetric_clocking_key')


def split(d,name):
    y0,y1=(-20,0) if name.endswith('_a') else (0,20)
    d.box(-25,25,y0,y1,82,z=-20,operation='cut',name='longitudinal_print_face')


def nut(d):
    d.oobb_cut('oobb_nut',position=[0,0,'wiggle_join_nut_bottom'],radius_name='m3',
               depth=2.8,zz='bottom',rot=[0,0,30],overhang=True)
    # Parallel walls retain the flats. Open along Y so neither half has a
    # pocket roof in its print direction. The fitted drive sleeve retains it.
    w=oobb.gv('nut_radius_m3','3dpr')*3**.5/2+.035
    d.box(-w,w,-12,12,2.86,z='wiggle_join_nut_bottom - 0.03 mm',operation='cut',name='M3_nut_split_face_loading')


def relief(d,points,depth,axis,xyz,name):
    target=d.body; d.index+=1; tool=f'{target}_{name}_{d.index}';d.body=tool
    d.polygon(points,depth,operation='new',name=name)
    d.move(axis=axis,angle='90 deg');d.move(translate=xyz);d.body=target
    d.do('solid.combine',target=target,tools=[tool],operation='cut')


def sleeve_roofs(d):
    # The nut insertion tunnel runs in Y, the clamp shank in X. Roof both
    # directions independently; leave the socket head accessible from above.
    relief(d,[[5.33,1.15],[8.70,1.15],[8.70,3.60],[7.015,5.285],[5.33,3.60]],
           19.2,[1,0,0],[0,15,'drive_clamp_z'],'nut_tunnel_roof')

def sleeve_throat(d):
    relief(d,[[1.93,-1.93],[1.93,1.93],[-1.93,1.93],[-3.86,0],[-1.93,-1.93]],
           14,[0,1,0],[3.77,0,'drive_clamp_z'],'socket_throat_roof')


def layer_audit(mesh, layer=.2):
    """Maximum lateral reach to the preceding layer, including hardware pockets."""
    import numpy as np
    from shapely.geometry import Polygon
    from shapely import GeometryCollection
    def section(z):
        path=mesh.section(plane_origin=[0,0,z],plane_normal=[0,0,1])
        result=GeometryCollection()
        if path:
            for loop in path.discrete:
                if len(loop)>=4:
                    poly=Polygon(loop[:,:2]).buffer(0)
                    if poly.area>1e-8:result=result.symmetric_difference(poly)
        return result
    bottom,top=mesh.bounds[:,2]
    zs=list(np.arange(bottom+.001,top-.001,layer))+[top-.001]
    previous=section(zs[0]);worst=0;worst_z=0;islands=0
    for z in zs[1:]:
        current=section(z)
        if current.is_empty: continue
        for g in getattr(current,'geoms',[current]):
            if g.area>.002 and not g.intersects(previous):islands+=1
        lo,hi=0.,20.
        for _ in range(13):
            mid=(lo+hi)/2
            if current.difference(previous.buffer(mid,quad_segs=12)).area<.0001:hi=mid
            else:lo=mid
        if hi>worst:worst=hi;worst_z=z-bottom
        previous=current
    return dict(layer_height_mm=layer,levels=len(zs),unsupported_islands=islands,
                maximum_lateral_reach_mm=round(worst,3),at_print_z_mm=round(worst_z,3))
