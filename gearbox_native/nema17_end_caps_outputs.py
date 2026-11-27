"""Checked publication and three practical print beds for the fixed end covers."""
import hashlib
import json
import math
import shutil
from pathlib import Path
import numpy as np
import trimesh
from gearbox_native.nema17_end_caps import PROJECT,PART_ID,MASTER,mount_layout
from gearbox_native.nema17_end_caps_checks import verify,verify_core


def verify_edit(source,folder):
    from gearbox_native.nema17_outputs import verify_edit as motor_edit
    result=motor_edit(source,folder,additional_changes={'input_angle':'360 deg'})
    states={name:json.loads((folder/(file+'.json')).read_text(encoding='utf8')) for name,file in [('before','before'),('after','after'),('reopened','reopened')]}
    def box(state,name):
        b=next(b for b in states[state]['bodies'] if b['name']==name)
        return np.array([b['bbox']['min'],b['bbox']['max']])
    for name in ('rear_cover_face','rear_cover_nuts'):
        assert np.max(abs(box('after',name)[:,2]-box('before',name)[:,2]+8))<.001
    assert abs(box('after','rear_output_extension')[0,2]-box('before','rear_output_extension')[0,2]+8)<.001
    assert abs(box('after','rear_output_extension')[1,2]-box('before','rear_output_extension')[1,2]+8)<.001
    for i in range(1,4):
        name=f'rear_output_joiner_{i}'
        assert abs(box('after',name)[0,2]-box('before',name)[0,2]+8)<.001
        assert abs(box('after',name)[1,2]-box('before',name)[1,2])<.001
    assert abs(box('after','rear_output_extension')[0,2]-box('after','rear_cover_face')[0,2]-1.5)<.001
    for name in ('front_cover_face','front_cover_nuts','front_cover_spacer'):
        assert np.max(abs(box('after',name)-box('before',name)))<.001
    for name in ('front_cover_face','rear_cover_face','rear_output_extension'):
        assert np.max(abs(box('after',name)-box('reopened',name)))<.001
    moving='hardware_endcap_outer_extension_screw_0'
    old=box('before',moving).mean(axis=0);new=box('after',moving).mean(axis=0)
    angle=math.radians(18)
    expected=np.array([old[0]*math.cos(angle)-old[1]*math.sin(angle),old[0]*math.sin(angle)+old[1]*math.cos(angle)])
    assert np.max(abs(expected-new[:2]))<.001
    fixed='hardware_endcap_front_join_screw_0'
    assert np.max(abs(box('after',fixed)-box('before',fixed)))<.001
    result.update(rear_cover_and_output_follow_motor_depth=True,rear_holder_proud_mm=1.5,rear_offset_preserved=True,
                  stationary_front_cover_unchanged=True,input_edit_degrees=360,rear_output_rotation_degrees=18,
                  fixed_cover_motion_checked=True)
    (folder/'cover_report.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    return result


def conversion_beds(part):
    from gearbox_native.nema17_print_set import CONVERSION_PARTS
    beds=[[
        ('motor_inner_adapter',(44,44)),('motor_cage',(162,71)),
        ('shaft_end_lower',(20,120)),('shaft_mount_lower',(49,120)),('front_cover_spacer',(90,157)),
        ('carrier_top_cap',(170,180)),
        *[(f'rear_output_spacer_{i+1}',xy) for i,xy in enumerate([(20,160),(35,160)])],
        *[(f'rear_output_joiner_{i+1}',xy) for i,xy in enumerate([(35,205),(75,205),(115,205)])],
    ],[
        ('rear_output_extension',(71,71)),('front_cover_face',(190,45)),('front_cover_nuts',(190,132)),
        ('rear_cover_face',(45,190)),('rear_cover_nuts',(132,196)),
    ],[('output_circle_plate',(71,71)),('output_circle_rear_plate',(169,169))]]
    kit=part/'motor_conversion';kit.mkdir(exist_ok=True);all_meshes=[];record=[]
    assert {n for rows in beds for n,xy in rows}==set(CONVERSION_PARTS)
    from shapely.geometry import box
    for i,rows in enumerate(beds,1):
        folder=kit/f'bed_{i}';folder.mkdir(exist_ok=True);meshes=[];footprints=[]
        for name,xy in rows:
            mesh=trimesh.load_mesh(part/'native_parts'/(name+'.stl'));assert mesh.is_volume
            mesh.apply_translation([*xy,0]);meshes.append(mesh)
            assert min(mesh.bounds[0,:2])>=0 and max(mesh.bounds[1,:2])<240
            assert abs(mesh.bounds[0,2])<.001
            # Convex XY hull is conservative even for annular or drilled parts.
            from shapely.geometry import MultiPoint
            footprint=MultiPoint(mesh.vertices[:,:2]).convex_hull
            assert all(footprint.distance(old)>.5 for old in footprints),(i,name)
            footprints.append(footprint)
        combined=trimesh.util.concatenate(meshes);combined.export(folder/'3dpr.stl')
        (folder/'3dpr.scad').write_text('import("3dpr.stl", convexity=10);\n',encoding='utf8')
        combined.apply_translation([260*(i-1),0,0]);all_meshes.append(combined)
        record.append(dict(bed=i,parts=[n for n,xy in rows],printer_area_mm=[240,240]))
    trimesh.util.concatenate(all_meshes).export(kit/'3dpr.stl')
    (kit/'3dpr.scad').write_text('// Complete conversion kit, arranged as three 240 mm beds.\n// Print bed_1, bed_2 and bed_3/3dpr.scad individually.\n// Bed 3 contains the circular front/rear plate pair; square and asymmetric pairs are optional native_parts files.\nimport("3dpr.stl", convexity=10);\n',encoding='utf8')
    (kit/'print_manifest.json').write_text(json.dumps(record,indent=2),encoding='utf8')
    (kit/'conversion_inventory.json').write_text(json.dumps(CONVERSION_PARTS,indent=2)+'\n',encoding='utf8')
    # Friendly entry point: this is the conversion, never a second base gearbox.
    shutil.copyfile(kit/'3dpr.stl',part/'nema3dpr.stl')
    (part/'nema3dpr.scad').write_text('// NEMA additions and changed parts only; three 240 mm print beds.\nimport("nema3dpr.stl", convexity=10);\n',encoding='utf8')
    for old,new in [('shaft_end_lower','coupler_6704_journal'),('shaft_mount_lower','coupler_6704_nut_carrier'),
                    ('rear_output_extension','rear_output_ring'),('rear_output_joiner_1','rear_output_joiner')]:
        for ext in ('step','stl'):shutil.copyfile(part/'native_parts'/(old+'.'+ext),part/'native_parts'/(new+'.'+ext))
    return record


def publish(part,source,views,overrides=None,source_sha=None):
    from gearbox_native.nema17_outputs import publish as motor_publish
    part=Path(part);source=Path(source);views=Path(views)
    parameters=json.loads((views/'export.json').read_text(encoding='utf8'))['parameters']['parameters']
    if any(p['name']=='motor_tube_wall' for p in parameters):
        from gearbox_native.nema17_tube_outputs import publish as publish_tube
        return publish_tube(part,source,views,overrides,source_sha)
    covers=verify(views);core=verify_core(views);edit=verify_edit(source,views/'motor_depth_edit')
    core['end_covers_checked']=True
    core['end_cover_verification']='end_cover_verification.json'
    motor_publish(part,source,views,overrides,source_sha,_checks=(core,edit))
    (part/'end_cover_verification.json').write_text(json.dumps(covers,indent=2),encoding='utf8')
    conversion_beds(part)
    # Remove only the two superseded generated sleeve copies; the checked
    # previous native model is preserved separately in solidcraft/.
    for i in (3,4):
        for ext in ('step','stl'):
            (part/'native_parts'/f'rear_output_spacer_{i}.{ext}').unlink(missing_ok=True)
    (part/'ASSEMBLY.md').write_text("""# Lower-plate extension attachment

[Full illustrated NEMA17 assembly guide](assembly_guide/README.md) ·
[Named exploded view](assembly_guide/exploded_overview.png) ·
[Core and motor steps](assembly_guide/01_motor_assembly.png) ·
[Covers and output steps](assembly_guide/02_covers_and_output.png)

Both black covers stay fixed. The fixed rear black mounting face projects
**1.5 mm** beyond the rotating teal rear face. Both teal flanges are 3 mm thick.

1. Assemble the gearbox using one matched pair of outer plates: square,
   circular, or asymmetric. All three pairs have the same four lower-plate
   attachment axes, two offset brace axes and front screw-access holes.
2. Fit the motor adapter and coupler as before. Load the three deeper side
   nuts at the gearbox end of `motor_cage`, then attach it with M3 × 16 socket
   caps. The motor-cover end still uses its original three M3 × 16 countersunk
   screws. Tighten the coupler grub screws before closing the covers.
3. Fit `front_cover_spacer` and the two front cover halves with four M3 × 25
   countersunk screws into the existing carrier nuts. Load the chosen M6/M3
   mounting nuts at the split before fitting each cover's face plate.
4. Load the three rear-cover M3 nuts and fit its two halves with three M3 × 16
   countersunk screws. Route the motor cable through the 8 mm rear passage.
5. Slide four M3 nuts into the side slots near the ends of the teal extension
   posts. Bring the extension up from behind; its posts seat against the
   motor-side outer plate.
6. Drop four M3 × 10 countersunk screws through the 6.4 mm access holes in the
   front plate. Seat their heads in the MOTOR-SIDE plate and tighten into the
   extension nuts using a straight hex key through those same access holes.
7. Slide the two Ø7 × 16 mm printed braces between the plates at the offset
   axes. Load an M3 nut beneath each motor-side plate hole, between the nearby
   extension posts. Insert two M3 × 25 countersunk screws from the front plate
   through the braces and tighten against these nuts. These screws do not
   attach the rear extension.
8. Turn the input by hand. Both covers must remain fixed, with the teal output
   clear of the motor cable and fixed support throughout its rotation.

The asymmetric pair has a round upper edge at the bearing-holder radius and
**two complete M6/M3 OOBB rows at 75 and 90 mm below centre**. The lower rows
are beyond the extension posts so their mounting fasteners have room.

Print the three files under `motor_conversion/bed_1`, `bed_2` and `bed_3`.
Each folder has `3dpr.scad` and `3dpr.stl` for a 240 × 240 mm bed. Bed 3 contains
the circular plate pair. Substitute the square pair (`output_cap_plate` and
`output_nut_plate`) or asymmetric pair (`output_lower_row_plate` and
`output_lower_row_rear_plate`) from `native_parts` if preferred.

Keep external mounting screws within 2 mm of either black cover's inner face.
The cover nut pockets use OOBB primitives with overhang enabled. Unused mounting
nuts may be omitted. Replace the rear extension, motor cage, both outer plates
and the two extra braces when upgrading from the long-through-screw version.
The 6810 socket-side insert `carrier_top_cap` is included on bed 1 with the
OOBB overhang bridge layers. Its matching nut-side insert already has them.
""",encoding='utf8')
    (part/'HARDWARE_END_COVERS.md').write_text("""# Conversion joining hardware

| Hardware | Quantity | Location |
|---|---:|---|
| M3 × 25 countersunk | 4 | Fixed front cover, into existing carrier nuts |
| M3 × 16 countersunk | 3 | Fixed rear cover |
| M3 × 10 countersunk | 4 | Motor-side outer plate into teal extension |
| M3 × 25 countersunk | 2 | Offset Ø7 × 16 mm brace sleeves between plates |
| M3 × 16 socket cap | 3 | Black motor cage to motor bracket; replaces M3 × 10 |
| M3 hex nut | 3 | Deeper motor-cage pockets; reuse the existing nuts |
| M3 hex nut | 7 | Three rear-cover and four extension side pockets |
| M3 hex nut | 2 | Exposed nuts below the offset brace screws |
| M6 hex nut | Up to 34 | 15 front and 19 rear black-cover mounting pockets |
| M3 hex nut | Up to 31 | 16 front and 15 rear black-cover mounting pockets |
| Printed Ø7 × 16 mm brace sleeve, M3 bore | 2 | Included in the print kit |

Countersunk screw lengths include the head. Existing gearbox, motor and coupler
hardware is retained. The original three motor-cage M3 × 10 socket caps are
replaced by M3 × 16; the four former M3 × 30 extension socket caps are removed.
See [HARDWARE_CHANGES.md](HARDWARE_CHANGES.md) for the original motor conversion;
this table supersedes its cage screw length. Socket caps remain at most 40 mm.
""",encoding='utf8')
    editing=part/'EDITING_PARAMETERS.md'
    text=editing.read_text(encoding='utf8')
    text=text.replace('three separate 10 mm screws','three separate 16 mm screws')
    text=text.replace('Both output and rear circular flanges are 3 mm thick.',
                      'Both output and rear circular flanges are 3 mm thick.')
    text=text.replace('Square, lower-row, extended circular, and plain circular output plates are\ninterchangeable options. The two circular options are parked',
                      'Use a matched square, extended circular or asymmetric plate pair with the rear extension.\nThe plain circular option lacks its attachment points. Alternative plates are parked')
    text += """

## Short rear attachment and offset braces

`rear_holder_proud=1.5 mm` makes the fixed rear black cover project beyond the
teal rear flange. `rear_extension_base` and the post heights follow this and
`motor_depth`. Both faces preserve their 1.5 mm offset after a motor-depth edit.

Four M3 × 10 countersunk screws attach only the motor-side plate to the rear
extension. The front plate's `rear_access_radius=3.2 mm` holes admit both the
screw heads and a straight hex key. The two extra braces have their own M3 × 25
countersunk screws and nuts at clocked positions, clear of those access axes.
The Ø13 mm extension posts are all on the lower half so the asymmetric bracket
can keep its upper outline at the bearing-holder radius.

`cage_join_length=16 mm` and `cage_nut_inset=11.3 mm` move the motor-cage joining
nuts 6 mm deeper than before. The rear cover's joining nuts stay in place.
The front cover retains its 4.3 mm spacer and M3 × 25 countersunk joining screws.

`bracket_full_row_start` selects the first complete 15 mm OOBB row beyond both
the ring and the extension fasteners. The second row is 15 mm farther out.
Default full rows are at −75 and −90 mm; `bracket_lower_edge=97 mm` includes the
outer edge margin. The square option keeps its 7×7 grid and extends its lower
edge to `rear_square_edge=59.5 mm` for full support around the attachment holes.
The circular pair remains Ø134 mm.

The 8 mm rear cable passage is unchanged. The mounting-nut layout is checked
for the current 81 mm black covers; changing their radius needs a new fit check.
"""
    editing.write_text(text,encoding='utf8')
    (part/'README.md').write_text("""# NEMA17 gearbox with accessible rear-extension screws

AI-generated CAD images and instructions. Errors possible.

## Summary

Both black mounting covers stay fixed while the teal output rotates. Short
countersunk screws attach the rear extension directly to the motor-side plate;
front access holes allow tightening without screws running through both plates.
Two offset braces support the plate spacing. The fixed rear cover projects
1.5 mm beyond the 3 mm teal rear flange.

This is an entirely AI-generated coding project. The generated outputs are
included as a starting point for modifications with your own AI tools.
This revision has not been physically assembled.

## Details

![AI-generated CAD render of the circular version](render_circular.png)

- [Editable SolidCraft model](gearbox_controls.solidcraft) · [Parameters](EDITING_PARAMETERS.md)
- [Complete print kit](motor_conversion/3dpr.scad): print its three beds separately
- [Bed 1](motor_conversion/bed_1/3dpr.scad) · [Bed 2](motor_conversion/bed_2/3dpr.scad) · [Bed 3](motor_conversion/bed_3/3dpr.scad)
- [Individual STEP/STL files](native_parts/) · [Native exploded view](exploded.solidcraft)
- [Square version](render_square.png) · [Asymmetric bracket](render_asymmetric.png) · [Rear view](render_rear.png)

The circular plate pair is on bed 3. Matched square and asymmetric pairs are
provided as individual files. The asymmetric upper edge follows the bearing
holder; two full OOBB rows extend below the attachment region.

## Parts

See the [joining hardware table](HARDWARE_END_COVERS.md). The front black cover
accepts up to 15 M6 and 16 M3 mounting nuts; the rear accepts 19 M6 and 15 M3.
The motor cage now uses M3 × 16 socket caps into deeper captive nuts. All new
outer-plate and rear-extension joining screws are countersunk.

## Assembly

Follow the [assembly sequence](ASSEMBLY.md). Fit the extension with four M3 × 10
screws through the front access holes, then fit the two offset braces with their
own M3 × 25 screws and nuts. Keep the motor cable within the fixed support.
""",encoding='utf8')
    from gearbox_native.carrier_overhang import publish_reprint
    publish_reprint(part)
    return covers
