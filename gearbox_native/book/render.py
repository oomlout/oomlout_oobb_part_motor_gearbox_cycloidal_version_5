"""Blender entry point. Render the cumulative build and inventory from native solids."""
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

job = Path(sys.argv[-1])
plan = json.loads((job / "scenes.json").read_text())
out = Path(plan["output"])
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 8
scene.cycles.use_denoising = True
prefs = bpy.context.preferences.addons["cycles"].preferences
for backend in ["OPTIX", "CUDA", "HIP", "METAL"]:
    try:
        prefs.compute_device_type = backend
        prefs.get_devices()
        devices = [d for d in prefs.devices if d.type == backend]
        if devices:
            for d in prefs.devices:
                d.use = d in devices
            scene.cycles.device = "GPU"
            break
    except TypeError:
        continue
scene.world = bpy.data.worlds.new("Soft studio")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.8, 0.8, 0.8, 1)
scene.render.film_transparent = True
scene.view_settings.view_transform = "AgX"
scene.render.image_settings.color_mode = "RGBA"
scene.render.resolution_percentage = 100

def material(name, colour, metallic):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    srgb = [int(colour[j:j+2],16)/255 for j in (0,2,4)]
    bsdf.inputs["Base Color"].default_value = [((v+.055)/1.055)**2.4 if v>.04045 else v/12.92 for v in srgb]+[1]
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = .32 if metallic else .4
    return m

mats = {k: material(k, colour, metallic) for k, colour, metallic in [
    ("teal","00B1B7",0),("black","181818",0),("yellow","FEC601",0),
    ("steel","CED3D8",.78),("screw","535961",.65)]}
objects = {}
corners = {}
for name, colour in plan["materials"].items():
    bpy.ops.wm.stl_import(filepath=str(job / (name + ".stl")))
    obj = bpy.context.object
    obj.name = name
    # The socket end is native upper. Flip about X to build from the bench.
    obj.rotation_euler.x = 3.141592653589793
    obj.data.materials.append(mats[colour])
    corners[name] = [Vector((x,-y,-z)) for x,y,z in obj.bound_box]
    objects[name] = obj
cam = bpy.data.objects.new("Orthographic camera",bpy.data.cameras.new("Lens"))
scene.collection.objects.link(cam)
scene.camera = cam
cam.data.type = "ORTHO"
cam.data.clip_end = 3000
lights = []
for delta,power,size in [((110,-110,175),430000,120),((-100,-70,105),240000,100),((0,130,120),360000,95)]:
    light = bpy.data.lights.new("Softbox","AREA")
    light.energy = power
    light.shape = "DISK"
    light.size = size
    o = bpy.data.objects.new("Softbox",light)
    scene.collection.objects.link(o)
    off = Vector(delta)
    o.rotation_euler = (-off).to_track_quat("-Z","Y").to_euler()
    lights.append((o,off))
for view in plan["views"]:
    positions = view["offsets"]
    eye = Vector(view.get("eye", [.85,-1.45,1.02])).normalized()
    rotation = eye.to_track_quat("Z","Y")
    coords = []
    for name,obj in objects.items():
        obj.hide_render = name not in positions
        if not obj.hide_render:
            obj.location.z = positions[name]
            coords.extend(rotation.inverted() @ (p+obj.location) for p in corners[name])
    low = Vector([min(p[i] for p in coords) for i in range(3)])
    high = Vector([max(p[i] for p in coords) for i in range(3)])
    target = rotation @ ((low+high)/2)
    w,h = view["size"]
    scene.render.resolution_x,scene.render.resolution_y = w,h
    cam.data.ortho_scale = max((high.x-low.x)*max(1,h/w),(high.y-low.y)*max(1,w/h))*1.02
    cam.rotation_euler = rotation.to_euler()
    cam.location = target + eye*700
    for light,off in lights:
        light.location = target+off
    scene.render.filepath = str(out/(view["key"]+".png"))
    bpy.ops.render.render(write_still=True)

