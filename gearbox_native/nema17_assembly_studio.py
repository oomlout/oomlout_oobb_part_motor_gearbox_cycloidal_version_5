"""Render assembly stages from the checked NEMA17 studio, without changing CAD.

blender -b <studio/motor_variant.blend> -P this_file -- <output-directory>
"""
import json
import math
import os
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

out = Path(sys.argv[-1]).resolve()
out.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.cycles.samples = 24
objects = {o.name: o for o in scene.objects if o.type == 'MESH'}


def group(n):
    if n.startswith(('asymmetric_',)) or n in ('output_cap_plate', 'output_nut_plate'):
        return 'omit'
    if n.startswith(('front_cover_', 'hardware_endcap_front_')):
        return 'front'
    if n.startswith(('rear_cover_', 'hardware_endcap_rear_')):
        return 'rear'
    if n.startswith(('rear_output_extension', 'hardware_endcap_outer_extension_')):
        return 'extension'
    if n.startswith(('rear_output_spacer_', 'hardware_endcap_spacer_')):
        return 'braces'
    if n.startswith(('motor_cage', 'hardware_cage_')):
        return 'cage'
    if n.startswith(('motor_inner_adapter', 'hardware_NEMA17_')):
        return 'motor'
    if n.startswith(('hardware_flange_', 'hardware_coupler_')):
        return 'coupler'
    if n.startswith('hardware_guide_M3x40') or n in ('hardware_guide_nut_1', 'hardware_guide_nut_3', 'hardware_guide_nut_5'):
        return 'late_guides'
    return 'core'


def render(label, groups, shifts=None, flip=True, select=None, individual=None,
           look=(180, -240, 170), width=1100, height=900):
    if os.environ.get('NEMA17_RENDER_ONLY') not in (None, label):
        return
    shifts = shifts or {}
    individual = individual or {}
    rotation = Matrix.Rotation(math.pi, 4, 'X') if flip else Matrix.Identity(4)
    visible = []
    for n, obj in objects.items():
        g = group(n)
        obj.hide_render = g not in groups or (select is not None and not select(n))
        delta = individual.get(n, shifts.get(g, (0, 0, 0)))
        obj.matrix_world = rotation @ Matrix.Translation(Vector(delta))
        if not obj.hide_render:
            visible.append(obj)
    bpy.context.view_layer.update()
    points = [o.matrix_world @ Vector(v) for o in visible for v in o.bound_box]
    lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    target = (lo + hi) / 2
    cam = scene.camera
    cam.location = target + Vector(look).normalized() * 700
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    local = [cam.matrix_world.inverted() @ p for p in points]
    sx = max(p.x for p in local) - min(p.x for p in local)
    sy = max(p.y for p in local) - min(p.y for p in local)
    midpoint = Vector(((max(p.x for p in local)+min(p.x for p in local))/2,
                       (max(p.y for p in local)+min(p.y for p in local))/2, 0))
    cam.location += cam.rotation_euler.to_matrix() @ midpoint
    aspect = width / height
    cam.data.ortho_scale = (max(sx, sy*aspect) if aspect >= 1 else max(sx/aspect, sy)) * 1.16
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(out / (label + '.png'))
    bpy.ops.render.render(write_still=True)
    anchors = {}
    for obj in visible:
        p = obj.matrix_world @ (sum((Vector(v) for v in obj.bound_box), Vector()) / 8)
        uv = world_to_camera_view(scene, cam, p)
        anchors[obj.name] = [round(uv.x * width, 2), round((1-uv.y) * height, 2)]
    (out / (label + '.json')).write_text(json.dumps(anchors, indent=2))


# Core opened at its two bearing layers; the two cycloids remain clamped.
split = {}
for n in objects:
    if group(n) != 'core':
        continue
    if n in ('output_cap_cylinder', 'carrier_top_cap', 'shaft_end_upper'):
        dz = 65
    elif n in ('hardware_6810_top', 'hardware_6704_top'):
        dz = 44
    elif n in ('circular_top', 'carrier_top', 'shaft_mount_upper') or 'mount_nut_upper' in n or 'carrier_top_mount_nut' in n:
        dz = 24
    elif n in ('output_nut_cylinder', 'carrier_bottom_cap', 'shaft_end_lower'):
        dz = -65
    elif n in ('hardware_6810_bottom', 'hardware_6704_base'):
        dz = -44
    elif n in ('circular_bottom', 'carrier_bottom', 'shaft_mount_lower') or 'mount_nut_lower' in n or 'carrier_bottom_mount_nut' in n:
        dz = -24
    else:
        dz = 0
    split[n] = (0, 0, dz)

render('01_core', {'core'}, individual=split,
       select=lambda n: not n.startswith(('hardware_ring_', 'hardware_guide_', 'hardware_shaft_M3', 'hardware_shaft_tie_')),
       look=(80, -260, 95))
render('02_coupler', {'core', 'coupler'}, shifts={'coupler': (0, 0, -24)},
       select=lambda n: group(n) == 'coupler' or n in ('shaft_end_lower', 'shaft_mount_lower') or n.startswith(('hardware_shaft_mount_nut_lower', 'hardware_shaft_M3', 'hardware_shaft_tie_')))
motor_offsets = {n: (0, 0, 22) for n in objects if n == 'motor_inner_adapter' or n.startswith('hardware_NEMA17_M3x8')}
render('03_motor', {'motor'}, individual=motor_offsets, flip=False)
render('04_mount', {'core', 'coupler', 'motor', 'late_guides'},
       shifts={'motor': (0, 0, -35)},
       individual={n: ((0, 0, 45) if 'M3x40' in n else (0, 0, -35)) for n in objects if group(n) == 'late_guides'})
base = {'core', 'coupler', 'motor', 'late_guides'}
render('05_cage', base | {'cage'}, shifts={'cage': (0, 0, -55)})
cover_offsets = {n: (0, 0, (55 if n == 'front_cover_face' else 35)) for n in objects if group(n) == 'front'}
cover_offsets.update({n: (0, 0, (-55 if n == 'rear_cover_face' else -35)) for n in objects if group(n) == 'rear'})
render('06_covers', base | {'cage', 'front', 'rear'}, individual=cover_offsets, flip=False)
render('07_extension', base | {'cage', 'front', 'rear', 'extension'}, shifts={'extension': (0, 0, -85)}, flip=False,
       individual={n: (0, 0, 35) for n in objects if n.startswith('hardware_endcap_outer_extension_screw_')})
render('08_finished', base | {'cage', 'front', 'rear', 'extension', 'braces'}, flip=False)

# A separate subsystem overview: offsets are illustrative, not a chronological step.
render('overview', base | {'cage', 'front', 'rear', 'extension'}, flip=False,
       shifts={'front': (0, 0, 65), 'coupler': (0, 0, -35), 'motor': (0, 0, -75),
               'cage': (0, 0, -150), 'rear': (0, 0, -205), 'extension': (165, 0, -100),
               'late_guides': (0, 0, 0)}, width=1400, height=1700, look=(100, -300, 100))
