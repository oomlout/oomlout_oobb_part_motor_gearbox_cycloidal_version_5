"""Blender-only studio; inputs are meshes exported from checked native CAD."""
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

cache=Path(sys.argv[-1]);bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences
for backend in ('OPTIX','CUDA'):
    try:
        prefs.compute_device_type=backend;prefs.get_devices();gpu=[d for d in prefs.devices if d.type==backend]
        if gpu:
            for d in prefs.devices:d.use=d in gpu
            scene.cycles.device='GPU';break
    except TypeError:pass
scene.render.film_transparent=True;scene.view_settings.view_transform='AgX'
scene.world=bpy.data.worlds.new('Soft studio');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.8,.8,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5

def material(name,color,metal=0):
    rgb=[int(color[i:i+2],16)/255 for i in (0,2,4)]
    linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    m=bpy.data.materials.new(name);m.use_nodes=True;s=m.node_tree.nodes['Principled BSDF']
    s.inputs['Base Color'].default_value=(*linear,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=.38
    return m
teal=material('OOBB turquoise','00B1B7');black=material('OOBB black','121212');yellow=material('OOBB sunflower','FEC601')
steel=material('Steel','BFC5C9',.85);bolts=material('Screw steel','555D63',.8)
objects={}
with np.load(cache/'studio.npz') as data:
    for key in data.files:
        if not key.endswith('_v'):continue
        n=key[:-2];mesh=bpy.data.meshes.new(n);mesh.from_pydata(data[key].tolist(),[],data[n+'_f'].tolist());mesh.update()
        obj=bpy.data.objects.new(n,mesh);scene.collection.objects.link(obj);objects[n]=obj
        if n.startswith(('printed_','shaft_end_','rear_output_spacer_')):m=yellow
        elif n.startswith(('output_','circular_','asymmetric_','rotor_','shaft_mount_','rear_output_extension')):m=teal
        elif n=='hardware_NEMA17_motor':m=black
        elif n.startswith('hardware_'):m=steel if any(k in n for k in ('nut','washer','coupler','6810','6704')) else bolts
        else:m=black
        obj.data.materials.append(m)

cam_data=bpy.data.cameras.new('Orthographic');cam_data.type='ORTHO';cam_data.ortho_scale=220
cam=bpy.data.objects.new('Camera',cam_data);scene.collection.objects.link(cam);scene.camera=cam
target=Vector((0,0,-15));cam.location=target+Vector((180,-240,145));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
for offset,power,size in [((100,-80,200),420000,150),((-120,-60,90),280000,130),((40,160,80),350000,120)]:
    light=bpy.data.lights.new('Softbox','AREA');light.energy=power;light.shape='DISK';light.size=size
    obj=bpy.data.objects.new('Softbox',light);scene.collection.objects.link(obj);obj.location=target+Vector(offset)
    obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1400;scene.render.resolution_y=1120;scene.render.resolution_percentage=100
labels=('square','circular','asymmetric','rear') if 'asymmetric_top' in objects else ('square','circular','rear') if 'front_cover_face' in objects else ('square','circular')
for label in labels:
    look=Vector((0,-12,-15)) if label=='asymmetric' else target
    cam_data.ortho_scale=235 if label=='asymmetric' else 220
    cam.location=look+Vector((180,-240,-145 if label=='rear' else 145))
    cam.rotation_euler=(look-cam.location).to_track_quat('-Z','Y').to_euler()
    for n,obj in objects.items():
        variant='circular' if label=='rear' else label
        obj.hide_render=(n.startswith('circular_') and variant!='circular') or (n.startswith('asymmetric_') and variant!='asymmetric') or (n in ('output_cap_plate','output_nut_plate') and variant!='square')
    scene.render.filepath=str(cache/(label+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(cache/'motor_variant.blend'))
