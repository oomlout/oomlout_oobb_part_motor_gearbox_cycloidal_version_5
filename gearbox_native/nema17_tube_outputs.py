"""Publish the conversion geometry and link a matching checked assembly guide."""
import hashlib
import json
import shutil
from pathlib import Path

from gearbox_native.nema17_double_bearing import PROJECT, MASTER, PART_ID
from gearbox_native.nema17_end_caps_outputs import conversion_beds, verify_edit
from gearbox_native.nema17_end_caps_checks import verify, verify_core


def assembly_notice(part, digest):
    guide=Path(part)/'assembly_guide'
    if (guide/'verification.json').exists() and (guide/'assembly-guide.pdf').exists():
        record=json.loads((guide/'verification.json').read_text())
        if record.get('source_sha256')==digest:
            return ('[Full illustrated assembly guide](assembly_guide/README.md) · '
                    '[Printable PDF](assembly_guide/assembly-guide.pdf) · '
                    '[Hardware table](assembly_guide/hardware.csv)\n\n'
                    'The guide covers the base gearbox and motor conversion, including nut-loading and tool access. '
                    'Its insertion sequence is CAD checked; this revision has not been physically test assembled.')
    return ('No matching assembly guide has been generated for this geometry. '
            'CAD clearance and native save/reopen checks are recorded beside the model; '
            'this revision has not been physically test assembled.')


def publish(part, source, views, overrides=None, source_sha=None):
    part,source,views=map(Path,(part,source,views))
    report=json.loads((views/'export.json').read_text())
    cover=verify(views);core=verify_core(views)
    edit=verify_edit(source,views/'motor_depth_edit')
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest==report['source_sha256']
    values={p['name']:p['value'] for p in report['parameters']['parameters']}
    assert values['coupler_bolt_circle_diameter']==16 and values['coupler_mount_radius']==8
    part.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,part/'gearbox_controls.solidcraft')
    for mode,target in [('assembled','true'),('exploded','exploded'),('3dpr','3dpr')]:
        for ext in ('solidcraft','step','stl','png'):
            shutil.copyfile(views/(mode+'.'+ext),part/(target+'.'+ext))
        (part/(target+'_solidcraft_manifest.json')).write_text(json.dumps(dict(
            status='success',construction='native',native_only=True,source_sha256=digest,
            conversion_only=mode=='3dpr',canonical_master=str(part/'gearbox_controls.solidcraft')),indent=2))
    (part/'native_parts').mkdir(exist_ok=True)
    for path in (views/'parts').iterdir():shutil.copyfile(path,part/'native_parts'/path.name)
    (part/'3dpr.scad').write_text('// Conversion only: all unchanged base gearbox parts are excluded.\nimport("3dpr.stl", convexity=10);\n')
    summary=dict(status=report['status'],source_sha256=digest,sampling=report['sampling'],
                 parameters=values,part_names=list(report['parts']),print_mesh=report['print_mesh'],note=report['note'])
    for name,data in [('end_cover_verification',cover),('motor_fit_verification',core),
                      ('motor_depth_edit_verification',edit),('native_export_verification',summary),
                      ('native_export_details',report),('native_configuration',dict(
                          style='simple_double_bearing_version_2',input_variant='nema17_flange',
                          motor_depth=values['motor_depth'],parameters=overrides or {},source_master=MASTER,
                          source_master_sha256=source_sha or digest))]:
        (part/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    conversion_beds(part)
    shutil.copyfile(part/'3dpr.solidcraft',part/'nema3dpr.solidcraft')
    for name in ('geometry_preview.png','unchanged_core.json','new_support_printability.json'):
        if (views.parent/name).exists():shutil.copyfile(views.parent/name,part/name)
    (part/'EDITING_PARAMETERS.md').write_text('''# Native NEMA17 parameters

Open `gearbox_controls.solidcraft` and use the Parameters menu. Change
`motor_depth` to the motor body length, excluding its shaft. The black tube,
three identical joiners, rear ring and rear cover follow that value. The rear
black mounting face remains 1.5 mm proud of the teal ring.

`coupler_bolt_circle_diameter` is 16 mm. It controls the four M3 axes in both
motor-side 6704 inner pieces. `motor_tube_wall` is 3 mm.

The three joiners share `rear_joiner_height`, `rear_extension_post_radius`,
`rear_joiner_screw_pitch` and `rear_joiner_pitch`. Their stations are 120 degrees
apart. Keep the calculated height expression to retain motor-depth propagation.
Changing the radial placement or screw pitch requires another plate and OOBB
hole clearance check; the current checked values are 52.5 mm and 15 mm.

Set `print_layout=0`, `explode=0 mm` for the assembly. Increase `explode` for
the exploded view, or set `print_layout=1`, `explode=0 mm` for print placement.
The supplied STL files are snapshots and need exporting again after an edit.

To make a separate catalogue variant, set `motor_depth` in the verbose NEMA
entry in `working_oomp_populate.py`. Its depth becomes part of the catalogue ID
and is passed to the native master through `native_parameters`. Regenerate
through the existing populate/working_oomp/working_scad pipeline.
''',encoding='utf8')
    (part/'README.md').write_text(f'''# NEMA17 conversion — {values['motor_depth']:g} mm motor body

Geometry review revision: three identical, separate teal joiners, spaced 120 degrees apart, plus a
continuous 3 mm-wall black motor support tube with a peaked cable opening.
Each joiner uses two M3 x 10 countersunk screws at each end. The rear ring is a separate flat print. The matching output
plates now have six extension screw/access holes. Joining screws remain short.

This is an entirely AI-generated coding project. The generated files are
included as a starting point for modifications with your own AI tools.

![Current geometry preview](geometry_preview.png)

- [Conversion print](nema3dpr.scad): 18 extra or changed parts, arranged on three beds.
- [Bed 1](motor_conversion/bed_1/3dpr.scad) · [Bed 2](motor_conversion/bed_2/3dpr.scad) · [Bed 3](motor_conversion/bed_3/3dpr.scad)
- [Exact print inventory](motor_conversion/conversion_inventory.json)
- [Native parameter model](gearbox_controls.solidcraft)
- [Parameter editing](EDITING_PARAMETERS.md)
- [Native conversion-only print view](3dpr.solidcraft)
- [Individual parts](native_parts/)

The base gearbox's discs, cams, sleeves and unchanged bearing carriers are
reused. The two circular output plates replace the base plates. Optional square
and asymmetric replacements are in native_parts; print one matching pair.

The motor-side 6704 journal and nut carrier are **different from the base
gearbox**. Their four M3 axes lie on a **16 mm bolt circle**, radius 8 mm.
Print `coupler_6704_journal.stl` and `coupler_6704_nut_carrier.stl` when selecting
individual files. These are named copies of `shaft_end_lower` and
`shaft_mount_lower`, already included once each in the conversion print.
Do not print both aliases and original names.

`rear_output_joiner.stl` is the common joiner: print three. The conversion bed
already contains those three copies. `rear_output_ring.stl` is its separate
3 mm rear ring. Twelve M3 x 10 countersunk screws and twelve M3 nuts attach
the joiners, six at the gearbox end and six at the rear ring.

The 6810 socket-side cap is included because it has the overhang bridges absent
from the preserved manual base. Its mating nut-side cap is reused.

`motor_depth` is the motor body length, excluding the shaft. The current part
definition uses {values['motor_depth']:g} mm and includes that depth in its ID.
Edit the same setting in populate to create another depth in a separate folder,
or edit the native favourite to resize the current model. `motor_tube_wall`
and `coupler_bolt_circle_diameter` are also exposed native parameters.

{assembly_notice(part, digest)}
''',encoding='utf8')
    return cover
