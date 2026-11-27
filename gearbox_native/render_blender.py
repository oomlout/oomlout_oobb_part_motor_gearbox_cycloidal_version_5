"""Background Blender scene builder; reads the native render job JSON."""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

job_path = Path(sys.argv[sys.argv.index('--')+1])
job = json.loads(job_path.read_text())
sys.path.insert(0, job['project'])
from gearbox_native.presentation import pose, motion

out = Path(job['output'])
out.mkdir(parents=True, exist_ok=True)
# This is a new background process with factory startup, never the user's scene.
scene = bpy.data.scenes.new(job.get('version', 'version_6').replace('version_', 'V')+' SolidCraft exploded presentation')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = .001
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.studio_light = 'paint.sl'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'BOTH'
scene.display.shading.curvature_ridge_factor = 1.15
scene.display.shading.curvature_valley_factor = 1.05
scene.display.shading.cavity_ridge_factor = 1.1
scene.display.shading.cavity_valley_factor = 1.05
scene.display.shading.show_object_outline = False
scene.display.shading.show_specular_highlight = True
scene.display.shading.background_type = 'WORLD'
world = bpy.data.worlds.new('Warm white studio')
world.color = (.87, .89, .91)
scene.world = world
scene.display.render_aa = '16'
scene.view_settings.view_transform = 'Standard'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent = True
scene.render.fps = job['fps']
scene.frame_start = 1
scene.frame_end = job['frames']

palette = {'fixed': (.13, .40, .51, 1), 'output': (.80, .24, .13, 1),
           'input': (.93, .61, .16, 1), 'orbit_0': (.76, .72, .59, 1),
           'orbit_1': (.25, .64, .79, 1)}
objects = {}
items=job['pieces']+job.get('hardware',[])
materials={}
def material(color):
    key=tuple(color)
    if key not in materials:
        mat=bpy.data.materials.new('Presentation '+str(len(materials)+1))
        mat.diffuse_color=color
        materials[key]=mat
    return materials[key]
for item in items:
    bpy.ops.object.select_all(action='DESELECT')
    assets=item.get('assets',[dict(stl=item.get('stl'),color=palette[item['member']])])
    imported=[]
    for asset in assets:
        bpy.ops.wm.stl_import(filepath=asset['stl'])
        obj=bpy.context.object
        obj.data.materials.append(material(asset['color']))
        imported.append(obj)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in imported:obj.select_set(True)
    bpy.context.view_layer.objects.active=imported[0]
    if len(imported)>1:bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = item['name']
    obj.color = palette[item['member']]
    obj['native_document'] = item.get('native_document','Nominal hardware presentation model')
    obj['native_mesh_sha256'] = item.get('stl_sha256','')
    obj['moving_member'] = item['member']
    objects[item['name']] = obj
    # Preserve facets at sharp transitions while smoothing the original mesh's
    # near-coplanar faces. No decimation, bevels or substituted CAD geometry.
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_auto_smooth() if hasattr(bpy.ops.object, 'shade_auto_smooth') else None
    obj.rotation_mode = 'XYZ'
    for frame in range(1, job['frames']+1):
        expansion, turns, _ = motion((frame-1)/job['fps'], job['config']['reduction'])
        obj.location, obj.rotation_euler = pose(item, job['config'], expansion, turns, job['spacing'])
        obj.keyframe_insert(data_path='location', frame=frame)
        obj.keyframe_insert(data_path='rotation_euler', frame=frame)

camera_data = bpy.data.cameras.new('Orthographic assembly camera')
camera = bpy.data.objects.new('Orthographic assembly camera', camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera_data.type = 'ORTHO'
camera_data.clip_end = 3000

def frame_camera():
    # Fit all exploded native bounds. Keep one fixed camera through the motion.
    for item in items:
        obj = objects[item['name']]
        obj.location, obj.rotation_euler = pose(item, job['config'], 1, 0, job['spacing'])
    bpy.context.view_layer.update()
    corners = [obj.matrix_world @ Vector(c) for obj in objects.values() for c in obj.bound_box]
    lower = Vector([min(p[i] for p in corners) for i in range(3)])
    upper = Vector([max(p[i] for p in corners) for i in range(3)])
    target = (lower+upper)/2
    camera.location = target + Vector((100, -900, 490))
    camera.rotation_euler = (target-camera.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    inv = camera.matrix_world.inverted()
    view = [inv @ p for p in corners]
    width = max(p.x for p in view)-min(p.x for p in view)
    height = max(p.y for p in view)-min(p.y for p in view)
    camera_data.ortho_scale = max(width, height)*1.30

frame_camera()
scene.frame_set(85)
scene.render.resolution_x = scene.render.resolution_y = job['still_size']
scene.render.resolution_percentage = 100
scene.render.filepath = str(out/'exploded_raw.png')
bpy.ops.render.render(write_still=True)
anchors = {}
for name, obj in objects.items():
    center = sum((Vector(c) for c in obj.bound_box), Vector())/8
    p = world_to_camera_view(scene, camera, obj.matrix_world @ center)
    anchors[name] = [p.x, 1-p.y]
(out/'anchors.json').write_text(json.dumps(anchors, indent=2))
scene.render.resolution_x = scene.render.resolution_y = job['video_size']
scene.render.filepath = str(out/'frames/frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'solidcraft_exploded.blend'))
if not job.get('preview_only'):
    (out/'frames').mkdir(exist_ok=True)
    bpy.ops.render.render(animation=True)
