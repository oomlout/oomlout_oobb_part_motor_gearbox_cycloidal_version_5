"""Read the socket-head bridge geometry from the shared OOBB v5 primitive."""
from oobb_solidcraft import api
from oobb_solidcraft.compiler import compile_thing


def socket_roof_layers():
    thing=dict(id='carrier_socket_overhang',mode='3dpr',components=[])
    api.append_full(thing,shape='oobb_screw_socket_cap',type='p',radius_name='m3',
                    depth=10,zz='top',nut_include=False,overhang=True)
    cubes=[];heads=[]
    def visit(node,offset=(0,0,0)):
        op=node['op'];children=node.get('children',[])
        if op=='translate':visit(children[0],tuple(a+b for a,b in zip(offset,node['value'])))
        elif op=='rotate':
            assert all(abs(v)<1e-12 for v in node['value'])
            visit(children[0],offset)
        elif op=='difference':
            assert all(not c.get('children') for c in children[1:])
            visit(children[0],offset)
        elif op=='union':
            for child in children:visit(child,offset)
        elif op=='solid':
            shape=node['value']
            if shape['kind']=='cube':cubes.append((offset,shape['size']))
            elif shape['kind']=='cylinder':heads.append((shape['radius'],offset[2]))
            else:raise ValueError(shape['kind'])
        else:raise ValueError(op)
    visit(compile_thing(thing)['tree'])
    seat=max(heads)[1]
    result=[]
    for (x,y,z),(w,h,depth) in cubes:
        # Reflect the top-facing catalogue seat into this bed-facing recess.
        # 0.02 mm overlap avoids coincident Boolean cut faces; nominal layer
        # widths and the existing round head clearance remain unchanged.
        result.append(dict(points=[(x,-y),(x+w,-y),(x+w,-y-h),(x,-y-h)],
                           z=round(seat-z-depth,8)-.02,depth=depth+.04))
    assert len(result)==2
    return sorted(result,key=lambda r:r['z'])


def publish_reprint(part):
    """One-piece replacement plate; the already-bridged nut insert is reusable."""
    from pathlib import Path
    import trimesh
    part=Path(part);folder=part/'bearing_insert_reprint';folder.mkdir(exist_ok=True)
    mesh=trimesh.load_mesh(part/'native_parts/carrier_top_cap.stl')
    assert mesh.is_volume and abs(mesh.bounds[0,2])<.001
    mesh.apply_translation([30,30,0])
    assert mesh.bounds[0,:2].min()>0 and mesh.bounds[1,:2].max()<240
    mesh.export(folder/'3dpr.stl')
    (folder/'3dpr.scad').write_text('import("3dpr.stl", convexity=10);\n',encoding='utf8')
    (folder/'README.md').write_text('''# 6810 insert overhang update

Print `3dpr.scad` or `3dpr.stl` for one replacement `carrier_top_cap`.
The six M3 socket-cap recesses now use the OOBB v5 `overhang=True` bridge
geometry: two 0.3 mm transitions from the head recess to the screw bore.
The existing round head clearance and screw seating height are unchanged.

`carrier_bottom_cap` already has `overhang=True` on its six nut pockets and
can be reused. The embedded mounting nuts in the carrier cores also retain
their existing overhang geometry. No hardware lengths or bearing fits change.
''',encoding='utf8')
    guide=part/'README.md'
    if guide.exists():
        text=guide.read_text(encoding='utf8')
        if 'bearing_insert_reprint/3dpr.scad' not in text:
            text+='\n[6810 socket-side insert replacement print](bearing_insert_reprint/3dpr.scad): OOBB overhang bridges enabled; reuse the existing nut-side insert.\n'
            guide.write_text(text,encoding='utf8')
    return folder
