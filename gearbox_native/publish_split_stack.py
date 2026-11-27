"""Publish only the accepted split-shaft bearing-input revision of V9."""
import argparse
import shutil
from pathlib import Path
import trimesh
from oobb_solidcraft.validation import inspect_shape
from gearbox_native.native_catalogue import publish,sha
from gearbox_native.project import PROJECT,require_editable
from gearbox_native.publish_native_drive import read,write
from gearbox_native.split_stack import STACK
from gearbox_native.verification import read_step


def compare_shared(build):
    """Check exact exported geometry before publishing; bind evidence to both STEP files."""
    stepper=PROJECT/'parts'/read(PROJECT/'solidcraft/native_v9.json')['variants']['35']['part_id']/'native_parts'
    paths=sorted(p for p in (build/'views/parts').glob('*.step') if p.stem not in {'bearing_holder',*STACK})
    assert len(paths)==7
    inputs={p.stem:[sha(p),sha(stepper/p.name)] for p in paths}
    cache=build/'shared_comparison.json'
    if cache.exists():
        old=read(cache)
        if old['inputs']==inputs:return old['results']
    results={}
    for p in paths:
        a,b=[inspect_shape(read_step(path)) for path in (stepper/p.name,p)]
        dv=abs(a['volume_mm3']-b['volume_mm3']);db=max(abs(x-y) for x,y in zip(a['bounds_mm'],b['bounds_mm']))
        assert dv<.001 and db<.001,p.stem
        results[p.stem]=dict(volume_delta_mm3=dv,maximum_bound_change_mm=db)
    write(cache,dict(inputs=inputs,results=results))
    return results


def run(build,edit):
    import working_oomp_populate as populate
    source=build/'gearbox.solidcraft';views=build/'views';digest=sha(source)
    rec=read(views/'export.json');mech=read(views/'mechanical.json');changed=read(edit/'verification.json')
    ip=PROJECT/'solidcraft/native_v9.json';idx=read(ip)
    assert idx['acceptance_sha256']==sha(PROJECT/'gearbox_native/acceptance.py')
    assert rec['source_sha256']==mech['source_sha256']==digest
    assert rec['status']=='native_export_checked' and mech['status']=='passed'
    assert changed['status']=='passed' and changed['reopens']==2 and abs(changed['height_change_mm']-4)<.001
    names=set(rec['parts'])
    assert set(STACK)<=names and len(names)==rec['print_mesh']['body_count']==14
    assert all(r['native_shape']['valid'] and r['native_shape']['solid_count']==1 and r['mesh']['watertight'] for r in rec['parts'].values())
    shared=compare_shared(build)
    option=next(o for o in populate.get_options() if o.get('input_variant')=='bearing_input')
    part=PROJECT/'parts'/populate.build_oomp_id(option);require_editable(part)
    # Keep an exact backup of the four obsolete generated exports outside the catalogue.
    removed=build/'superseded';removed.mkdir(exist_ok=True)
    for n in ('eccentric_hub_lower','eccentric_hub_upper'):
        for ext in ('step','stl'):
            old=part/'native_parts'/(n+'.'+ext)
            if old.exists():shutil.copyfile(old,removed/old.name);old.unlink()
    publish(part,source,views,option['native_parameters'],digest)
    plates={}
    for file,count in [('3dpr.stl',14),('compact_print/3dpr.stl',14),('shaft_reprint/3dpr.stl',6),('bearing_conversion/3dpr.stl',7)]:
        m=trimesh.load_mesh(part/file);shells=m.split(only_watertight=False)
        assert len(shells)==count and all(s.is_volume and abs(s.bounds[0,2])<.01 for s in shells),file
        plates[file]=dict(parts=count,size_mm=m.extents.tolist(),sha256=sha(part/file))
    shutil.copyfile(source,PROJECT/idx['bearing_master'])
    mech['native_parts']={n:dict(valid=r['native_shape']['valid'],mesh=r['mesh']) for n,r in rec['parts'].items()}
    mech.update(print_parts=14,native_body_count=14,reprint_sha256=plates['shaft_reprint/3dpr.stl']['sha256'])
    proof=read(PROJECT/'solidcraft/native_v9_holder_verification.json')
    audit=read(part/'shaft_reprint/printability.json')
    proof['variants']['35_bearing']=mech
    proof.update(split_sleeve_edit=changed,shared_stepper_parts=shared,split_stack_printability=audit)
    verify='solidcraft/native_v9_split_verification.json';validation='solidcraft/version_9_split_validation.json'
    write(PROJECT/verify,proof)
    stats=dict(status='passed',source_sha256=digest,bearing_input_fit_checks=len(mech['checks']),
               maximum_overlap_mm3=mech['maximum_overlap_mm3'],shared_stepper_parts=shared,
               hardware='Axial M3 x 35 socket cap, M3 captive nut; OOBB overhang enabled for both.',
               print_plates=plates,layer_checks=audit,native_sleeve_edit='passed',physical_fit_tested=False)
    if (build/'previous_print_audit.json').exists():stats['previous_layer_checks']=read(build/'previous_print_audit.json')
    write(PROJECT/validation,stats)
    idx.update(verification=verify,revision_validation=validation,previous_holder_verification='solidcraft/native_v9_holder_verification.json',
               previous_holder_validation='solidcraft/version_9_holder_validation.json',bearing_master_sha256=digest,
               revision='Four flat-print eccentric hub halves and M3 x 35 axial tie in the 35:1 bearing input')
    idx['variants']['35_bearing'].update(master_sha256=digest,source_master_sha256=digest,component_count=14)
    write(ip,idx)
    print(f'Published {part.name}: {len(mech["checks"])} fit checks; six-piece shaft plate.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('build',type=Path);p.add_argument('edit',type=Path)
    args=p.parse_args();run(args.build.resolve(),args.edit.resolve())
