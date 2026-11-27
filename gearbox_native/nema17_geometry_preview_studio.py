"""Quick actual-CAD details for review, not assembly instructions."""
import sys
import os
from pathlib import Path
import bpy
from mathutils import Vector

out=Path(sys.argv[-1]).resolve();out.mkdir(exist_ok=True,parents=True)
scene=bpy.context.scene;scene.cycles.samples=24
objects={o.name:o for o in scene.objects if o.type=='MESH'}
camera=scene.camera
if os.environ.get('NEMA17_PREVIEW_MESHES'):
    import numpy as np
    with np.load(os.environ['NEMA17_PREVIEW_MESHES']) as data:
        for key in data.files:
            if not key.endswith('_v'):continue
            name=key[:-2]
            if name not in objects:
                obj=bpy.data.objects.new(name,bpy.data.meshes.new(name));scene.collection.objects.link(obj)
                objects[name]=obj
                material=objects['rear_output_extension'].data.materials[0]
            else:
                obj=objects[name];material=obj.data.materials[0]
            mesh=bpy.data.meshes.new(name+'_review')
            mesh.from_pydata(data[key].tolist(),[],data[name+'_f'].tolist());mesh.update()
            obj.data=mesh;obj.data.materials.append(material)
bpy.context.view_layer.update()


def render(name,placements,target,scale,offset):
    for n,o in objects.items():
        o.hide_render=n not in placements
        if n in placements:
            bounds=[Vector(v) for v in o.bound_box]
            centre=Vector(((min(p.x for p in bounds)+max(p.x for p in bounds))/2,
                           (min(p.y for p in bounds)+max(p.y for p in bounds))/2,
                           min(p.z for p in bounds)))
            o.location=Vector(placements[n])-centre
    camera.location=Vector(target)+Vector(offset)
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=scale
    scene.render.resolution_x=1600;scene.render.resolution_y=1100
    bpy.context.view_layer.update()
    points=[camera.matrix_world.inverted() @ o.matrix_world @ Vector(v)
            for n,o in objects.items() if n in placements for v in o.bound_box]
    left,right=min(p.x for p in points),max(p.x for p in points)
    bottom,top=min(p.y for p in points),max(p.y for p in points)
    camera.location += camera.rotation_euler.to_matrix() @ Vector(((left+right)/2,(bottom+top)/2,0))
    camera.data.ortho_scale=max(right-left,(top-bottom)*1600/1100)*1.18
    scene.render.filepath=str(out/(name+'.png'))
    bpy.ops.render.render(write_still=True)


render('supports',{'motor_cage':(-100,0,0),'rear_output_extension':(65,0,0),
                  'rear_output_joiner_1':(65,52.5,18),
                  'rear_output_joiner_2':(19.53,-26.25,18),
                  'rear_output_joiner_3':(110.47,-26.25,18)},
       (0,0,30),300,(180,-270,210))
render('coupler_inserts',{'shaft_end_lower':(-17,0,0),'shaft_mount_lower':(17,0,0)},
       (0,0,2),70,(0,-15,180))
