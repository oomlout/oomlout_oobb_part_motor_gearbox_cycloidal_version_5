"""Blender studio for the double-bearing V2. Coordinates are in native CAD millimetres."""
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

cache = Path(sys.argv[-1])
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
prefs = bpy.context.preferences.addons['cycles'].preferences
for backend in ('OPTIX', 'CUDA', 'HIP', 'METAL'):
    try:
        prefs.compute_device_type = backend
        prefs.get_devices()
        gpu = [d for d in prefs.devices if d.type == backend]
        if gpu:
            for d in prefs.devices:
                d.use = d in gpu
            scene.cycles.device = 'GPU'
            break
    except TypeError:
        continue

scene.render.film_transparent = True
scene.view_settings.view_transform = 'AgX'
scene.world = bpy.data.worlds.new('Softbox surroundings')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.77, .79, .81, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .48


def finish(name, color, roughness, metallic=0):
    rgb = [int(color[i:i+2], 16) / 255 for i in (0, 2, 4)]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (*linear, 1)
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = roughness
    return mat


teal = finish('Turquoise 10605', '00B1B7', .40)
black = finish('Black 10101', '121212', .39)
yellow = finish('Sunflower 10402', 'FEC601', .4)
steel = finish('Bearing and nut steel', 'BFC5C9', .26, .88)
bolt = finish('Oxidised screw steel', '575D63', .31, .81)


def material(n):
    if n.startswith(('printed_drive_sleeve', 'printed_contact_sleeve', 'connected_contact_ring', 'shaft_end_')):
        return yellow
    if n.startswith('shaft_mount_'):
        return teal
    if n.startswith('hardware_'):
        return steel if 'nut' in n.lower() or n.startswith(('hardware_67', 'hardware_68')) else bolt
    return teal if n.startswith(('output_', 'rounded_', 'rotor_')) else black


objects = {}
geometry = {}
with np.load(cache / 'studio.npz') as models:
    for key in models.files:
        if not key.endswith('_v'):
            continue
        name = key[:-2]
        points = models[key]
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(points.tolist(), [], models[name + '_f'].tolist())
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        scene.collection.objects.link(obj)
        obj.data.materials.append(material(name))
        objects[name] = obj
        geometry[name] = points

cam_data = bpy.data.cameras.new('Orthographic')
cam_data.type = 'ORTHO'
cam_data.clip_end = 3000
cam = bpy.data.objects.new('Studio camera', cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

lights = []
for offset, power, size in [((70, 25, 185), 370000, 130), ((-100, 60, 95), 190000, 110),
                            ((10, -140, 105), 300000, 95), ((135, 160, 35), 110000, 140)]:
    light = bpy.data.lights.new('Softbox', 'AREA')
    light.energy, light.shape, light.size = power, 'DISK', size
    lamp = bpy.data.objects.new('Softbox', light)
    scene.collection.objects.link(lamp)
    lamp.rotation_euler = (-Vector(offset)).to_track_quat('-Z', 'Y').to_euler()
    lights.append((lamp, Vector(offset)))

anchors = {}


def shoot(key, places, size, eye=(.86, 1.4, .87)):
    # The framing is taken from the triangles themselves, including partial flanges.
    rot = Vector(eye).to_track_quat('Z', 'Y')
    axes = np.array(rot.to_matrix())
    samples = []
    for n, o in objects.items():
        o.hide_render = n not in places
        if not o.hide_render:
            o.location.z = places[n]
            samples.append(geometry[n] + [0, 0, places[n]])
    coords = np.concatenate(samples) @ axes
    lo, hi = coords.min(axis=0), coords.max(axis=0)
    target = Vector(axes @ ((lo + hi) / 2))
    w, h = size
    span = hi - lo
    scale = max(span[0] * max(1, h/w), span[1] * max(1, w/h)) * 1.08
    cam_data.ortho_scale = scale
    cam.rotation_euler = rot.to_euler()
    cam.location = target + Vector(eye).normalized() * 800
    for lamp, off in lights:
        lamp.location = target + off
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(cache / (key + '.png'))
    bpy.ops.render.render(write_still=True)
    # Save a projected visible point on the right-hand silhouette of every named part.
    anchors[key] = {}
    for n, z in places.items():
        xy = (geometry[n] + [0, 0, z]) @ axes
        p = xy[np.argmax(xy[:, 0])]
        delta = (p - (lo+hi)/2) * max(size) / scale
        anchors[key][n] = [w/2 + delta[0], h/2 - delta[1]]
    (cache / 'anchors.json').write_text(json.dumps(anchors))


square = {n: 0 for n in objects if not n.startswith('rounded_')}
rounded = {n: 0 for n in objects if n not in ('output_cap_plate', 'output_nut_plate')}
shoot('square', square, (1510, 1080))
shoot('rounded', rounded, (1510, 1080))

# Separate coaxial subsystems to show parts normally hidden inside a larger bearing.
housing, core, shaft = {}, {}, {}
for n in square:
    if n.startswith(('output_', 'hardware_6810', 'hardware_ring', 'hardware_M3_ring', 'printed_contact')):
        if n.startswith('hardware_ring'):
            z = 103
        elif n.startswith('hardware_M3_ring'):
            z = -92
        else:
            z = {'output_cap_cylinder': 75, 'hardware_6810_top': 53, 'output_cap_plate': 36,
                 'output_nut_plate': -33, 'hardware_6810_bottom': -52,
                 'output_nut_cylinder': -71}.get(n, 0)
        housing[n] = z
    elif n.startswith(('shaft_', 'hardware_shaft')):
        if n.startswith('hardware_shaft_M3'):
            z = -70 if 'lower' in n else 70
        elif 'tie_nut' in n:
            z = -50 if 'lower' in n else 50
        elif 'mount_nut' in n:
            z = -32 if 'lower' in n else 32
        else:
            z = {'shaft_end_lower': -42, 'shaft_mount_lower': -25, 'shaft_cam_a_outer': -14,
                 'shaft_cam_a_inner': -5, 'shaft_cam_b_inner': 5, 'shaft_cam_b_outer': 14,
                 'shaft_mount_upper': 25, 'shaft_end_upper': 42}[n]
        shaft[n] = z
    else:
        if n.startswith(('hardware_drive_caps', 'hardware_drive_shanks')):
            z = 108
        elif n.startswith('hardware_drive_nuts'):
            z = -90
        elif 'carrier' in n or n in ('hardware_6704_base', 'hardware_6704_top'):
            upper = 'top' in n
            distance = 80 if 'cap' in n else 62 if 'nut' in n or '6704' in n else 46
            z = distance if upper else -distance
        elif 'disc_' in n or n.startswith('rotor'):
            upper = '_b' in n
            distance = 32 if n in ('rotor_a', 'rotor_b') or 'M3x6' in n else 23 if '6704' in n else 14
            z = distance if upper else -distance
        else:
            z = 0
        core[n] = z

assert set(housing) | set(core) | set(shaft) == set(square)
for key, layer in [('housing', housing), ('core', core), ('shaft', shaft)]:
    shoot(key, layer, (560, 1280), eye=(.45, 1.4, .48))

def subset(*prefixes):
    return {n: 0 for n in square if n.startswith(prefixes)}



# Assembly starts with the native upper face on the bench. Rotate every mesh,
# including its hardware, so the pictures follow the physical build direction.
values = json.loads((cache / 'native_parameters.json').read_text())
native_screw = geometry['hardware_shaft_M3x35_lower']
temporary = native_screw * [1, -1, -1]
temporary[:, 1] -= 2 * values['shaft_tie_pitch']
temporary[:, 2] += (values['shaft_face_z'] + values['shaft_head_depth']
                   + values['stack_height'] - values['shaft_face_z'] - values['shaft_nut_depth'])
mesh = bpy.data.meshes.new('Temporary shaft screw')
mesh.from_pydata(temporary.tolist(), [], [list(f.vertices) for f in objects['hardware_shaft_M3x35_lower'].data.polygons])
mesh.update()
temp = bpy.data.objects.new('temporary_shaft_tie', mesh)
scene.collection.objects.link(temp)
temp.data.materials.append(bolt)
objects[temp.name] = temp
geometry[temp.name] = temporary
for name, obj in objects.items():
    obj.rotation_euler.x = np.pi
    geometry[name] = geometry[name] * [1, -1, -1]

first = {'output_cap_cylinder': 0, 'carrier_top_cap': 0, 'shaft_end_upper': 0,
         'hardware_shaft_M3x35_upper': 0, 'temporary_shaft_tie': 0}
first.update(subset('hardware_ring_M3_shanks','hardware_ring_cap_heads',
                    'hardware_drive_shanks','hardware_drive_caps'))
shoot('layer_start',first,(690,490),eye=(1.0,1.4,1.1))
bearing = {'hardware_6810_top': 20,'hardware_6704_top': 20}
shoot('layer_bearings',first | bearing,(690,490),eye=(1.0,1.4,1.1))
first.update({n:0 for n in bearing})
closing = subset('carrier_top','hardware_carrier_top_mount_nut',
                 'shaft_mount_upper','hardware_shaft_mount_nut_upper')
closing.pop('carrier_top_cap')
closing['rounded_top'] = 0
shoot('layer_inner',first | {n:21 for n in closing},(690,490),eye=(1.0,1.4,1.15))
first.update(closing)
sleeves = subset('printed_drive_sleeve','printed_contact_sleeve')
shoot('layer_sleeves',first | {n:20 for n in sleeves},(690,490),eye=(1.0,1.4,1.15))
first.update(sleeves)

def disc(letter):
    return subset('rotor_'+letter, 'hardware_disc_'+letter, 'hardware_6704_disc_'+letter)

first['shaft_cam_b_outer'] = 0
b = disc('b')
shoot('layer_disc_b',first | {n:29 for n in b},(690,490),eye=(1.4,.55,1.45))
first.update(b)
shoot('layer_cams',first | {'shaft_cam_b_inner':14,'shaft_cam_a_inner':29},
      (690,490),eye=(1.4,.55,1.45))
first.update({'shaft_cam_b_inner':0,'shaft_cam_a_inner':0})
a = disc('a')
shoot('layer_disc_a',first | {n:27 for n in a} | {'shaft_cam_a_outer':43},
      (690,490),eye=(1.4,.55,1.45))
first.update(a)
first['shaft_cam_a_outer'] = 0

closing = subset('carrier_bottom','hardware_carrier_bottom_mount_nut',
                 'shaft_mount_lower','hardware_shaft_mount_nut_lower')
closing.pop('carrier_bottom_cap')
closing['rounded_bottom'] = 0
shoot('layer_finish_inner',first | {n:21 for n in closing},(690,490),eye=(1.0,1.4,1.15))
first.update(closing)
bearing = {'hardware_6810_bottom':20,'hardware_6704_base':20}
shoot('layer_finish_bearings',first | bearing,(690,490),eye=(1.0,1.4,1.1))
first.update({n:0 for n in bearing})
caps = {'output_nut_cylinder':20,'carrier_bottom_cap':20,'shaft_end_lower':20}
shoot('layer_finish_caps',first | caps,(690,490),eye=(1.0,1.4,1.15))
first.update({n:0 for n in caps})

first.update(subset('hardware_drive_nuts','hardware_M3_ring_nuts','hardware_shaft_tie_nut_lower'))
reversal = first | {'temporary_shaft_tie':-43, 'hardware_shaft_M3x35_lower':43,
                    'hardware_shaft_tie_nut_upper':-9}
shoot('layer_reverse',reversal,(690,490),eye=(.6,1.4,.55))
shoot('layer_end',rounded,(690,490))
# A near-axial view of the starting E shows which screw head occupies the hex pocket.
shoot('layer_start_face', {'shaft_end_upper':0, 'hardware_shaft_M3x35_upper':0,
                          'temporary_shaft_tie':0}, (400,340), eye=(.08,.08,-1))
