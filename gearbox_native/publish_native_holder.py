"""Publish the verified detachable lower bearing cup without rebuilding stepper presets."""
import argparse
import json
import shutil
from pathlib import Path
import trimesh
from gearbox_native.project import PROJECT, require_editable
from gearbox_native.native_catalogue import publish, sha
from gearbox_native.publish_native_drive import read, write, hardware
from gearbox_native.draw_drive_cutaway import draw
from gearbox_native.verification import read_step
from oobb_solidcraft.validation import inspect_shape


def run(build, edit):
    import working_oomp_populate as populate
    source=build/'gearbox.solidcraft'; views=build/'views'
    record=read(views/'export.json'); mechanical=read(views/'mechanical.json')
    assert record['status']=='native_export_checked' and mechanical['status']=='passed'
    assert record['source_sha256']==mechanical['source_sha256']==sha(source)
    assert len(record['parts'])==12 and record['print_mesh']['body_count']==12
    assert all(r['native_shape']['valid'] and r['native_shape']['solid_count']==1 and r['mesh']['watertight'] for r in record['parts'].values())
    edited=read(edit/'verification.json');assert edited['status']=='passed'
    index_path=PROJECT/'solidcraft/native_v9.json';index=read(index_path)
    assert index['acceptance_sha256']==sha(PROJECT/'gearbox_native/acceptance.py')
    stepper=PROJECT/'parts'/index['variants']['35']['part_id']
    # Compare actual native exports for every shared printed component.
    shared={}
    for name in set(record['parts'])-{'bearing_holder','bearing_retainer','eccentric_hub_lower','eccentric_hub_upper'}:
        a=inspect_shape(read_step(stepper/'native_parts'/(name+'.step')))
        b=record['parts'][name]['native_shape']
        dv=abs(a['volume_mm3']-b['volume_mm3'])
        # Export record bounds include XY layout offsets; local STEP is authoritative.
        local=inspect_shape(read_step(views/'parts'/(name+'.step')))
        db=max(abs(x-y) for x,y in zip(a['bounds_mm'],local['bounds_mm']))
        assert dv<.001 and db<.001,(name,dv,db)
        shared[name]=dict(volume_delta_mm3=dv,maximum_bound_change_mm=db)
    option=next(o for o in populate.get_options() if o.get('input_variant')=='bearing_input')
    part=PROJECT/'parts'/populate.build_oomp_id(option);require_editable(part)
    # Remove only the explicitly superseded generated baseplate exports.
    archive=build/'superseded';archive.mkdir(exist_ok=True)
    for ext in ('step','stl'):
        old=part/'native_parts'/('bearing_baseplate.'+ext)
        if old.exists():shutil.copyfile(old,archive/old.name);old.unlink()
    shutil.copyfile(source,PROJECT/'gearbox_bearing_controls.solidcraft')
    publish(part,source,views,option['native_parameters'],sha(source))
    hardware(part,mechanical['parameters'],True)
    draw(part)
    kit=part/'bearing_conversion';kit.mkdir(exist_ok=True)
    pieces=[]
    for name,x,y in [('bearing_holder',24,24),('eccentric_hub_lower',62,24),('eccentric_hub_upper',88,24),('bearing_retainer',112,24)]:
        mesh=trimesh.load_mesh(part/'native_parts'/(name+'.stl'))
        assert mesh.is_volume and abs(mesh.bounds[0,2])<.01
        mesh.apply_translation([x,y,0]);pieces.append(mesh)
    plate=trimesh.util.concatenate(pieces);plate.export(kit/'3dpr.stl')
    assert len(plate.split())==4
    (kit/'README.md').write_text('''# Bearing conversion parts

`3dpr.stl` contains the separate bearing holder, revised lower and upper hubs,
and retaining washer. Reuse the stepper version's `motor_mount`, front carrier,
drive sleeve, cycloids and three casing pieces. The old motor spacer is omitted.
If replacing the former integrated bearing baseplate, also print the common
`../native_parts/motor_mount.stl`. The retaining washer has the same geometry as before.

Fit the 6702 into the upward-open cup. Load guide/standoff nuts into the common
motor plate before fitting the holder. Four M3 x 10 countersunk screws and M3
nuts fasten the cup using the 31 mm square NEMA17 pattern. All nut pockets have
overhang enabled. The shaft still uses an upward M2.5 x 35 socket-cap screw;
its top nut is lower in the revised upper hub. Allow 2.7 mm below the cup for
the axial screw head. Tighten this join before attaching the external D-sleeve.
''',encoding='utf8')
    with (part/'README.md').open('a',encoding='utf8') as stream:
        stream.write('\n[Four-piece bearing conversion](bearing_conversion/3dpr.stl) · [Hardware and assembly](HARDWARE.md) · [Shaft cutaway](wiggle_shaft_assembled_cutaway.png)\n\nThe separate cup prints bearing-opening upward. The motor plate is shared with the stepper variant.\n')
    previous=read(PROJECT/index['verification'])
    mechanical['native_parts']={n:dict(valid=r['native_shape']['valid'],mesh=r['mesh']) for n,r in mechanical['native_parts'].items()}
    mechanical.update(print_parts=12,native_body_count=12)
    previous['variants']['35_bearing']=mechanical
    previous.update(holder_edit=edited,shared_stepper_parts=shared,holder_revision='Separate upward-open 6702 cup on the shared NEMA17 motor plate')
    write(PROJECT/'solidcraft/native_v9_holder_verification.json',previous)
    index['previous_drive_verification']=index['verification']
    index['verification']='solidcraft/native_v9_holder_verification.json'
    index['bearing_master_sha256']=sha(source)
    index['variants']['35_bearing'].update(master_sha256=sha(source),source_master_sha256=sha(source),component_count=12)
    for key in ('35','10'):index['variants'][key]['component_count']=11
    index['revision']='Detachable upward-open bearing cup, shared stepper motor plate and lower bearing-input shaft journal'
    write(index_path,index)
    print('Published detachable bearing holder; shared parts:',', '.join(sorted(shared)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('build',type=Path);p.add_argument('edit',type=Path)
    a=p.parse_args();run(a.build.resolve(),a.edit.resolve())
