"""Check linked placements and publish a printable layout from accepted meshes."""
import argparse
import json
import os
from pathlib import Path
import shutil
import uuid
import sys
import numpy as np
import trimesh
import yaml
from oobb_solidcraft.construction import build_thing
from oobb_solidcraft.compiler import compile_thing
from oobb_solidcraft.runtime import digest,write_json
from oobb_solidcraft.validation import read_step,inspect_shape
from OCP.TopAbs import TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.STEPControl import STEPControl_Writer,STEPControl_AsIs
from OCP.IFSelect import IFSelect_RetDone

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))
from gearbox_native.project import active_part, require_editable
from gearbox_native.exact_geometry import build_shape,_move
from gearbox_native.acceptance import verify_step
PART=active_part(PROJECT)


def verify(modes,export_stl=True):
    require_editable(PART)
    results={}
    definition=yaml.safe_load((PART/'working.yaml').read_text())
    for mode in modes:
        manifest_path=PART/(mode+'_solidcraft_manifest.json')
        record=json.loads(manifest_path.read_text())
        thing=build_thing(definition,builder_path=PROJECT/'working_solidcraft.py',mode=mode)
        count=len(thing['gearbox']['layout'])
        assert record['status']=='success' and record['construction']=='native'
        assert record['body_count']==record['placement_count']==count and record['reopened']
        if not export_stl:
            results[mode]=dict(body_count=count,reopened=True);continue
        thing=build_thing(definition,builder_path=PROJECT/'working_solidcraft.py',mode=mode)
        meshes=[];source_files=[]
        for placement in thing['gearbox']['layout']:
            name=placement['part'];folder=PART/'solidcraft'/mode
            piece=json.loads((folder/(name+'_manifest.json')).read_text())
            assert piece['status']=='success' and piece['verification']['status']=='passed'
            path=folder/(name+'.stl')
            saved=next(f['sha256'] for f in piece['published_files'] if f['file']==path.name)
            assert digest(path)==saved
            mesh=trimesh.load_mesh(path,process=True)
            assert mesh.is_watertight and mesh.is_winding_consistent and mesh.is_volume
            mesh.apply_translation(placement['pos']);meshes.append(mesh)
            source_files.append(dict(file=str(path),sha256=saved,translation_mm=placement['pos']))
        attempt=Path(record['manifest']).parent
        measured=json.loads((attempt/'measurements.json').read_text())
        assert measured['body_count']==len(meshes)
        # Linked-component measure() can return a loose box from surface control
        # points (the casing is inflated by 0.9 mm on two sides). Verify actual
        # exported-solid boxes instead, with the original placement tolerance.
        # Modified equation rotors also receive the complete independent STEP
        # check. Other individual parts retain their existing accepted evidence.
        layout_step=PART/(mode+'.step')
        assert digest(layout_step)==next(f['sha256'] for f in record['published_files'] if f['file']==layout_step.name)
        solid=read_step(layout_step);ex=TopExp_Explorer(solid,TopAbs_SOLID);solids=[];actual_boxes=[]
        while ex.More():
            body=ex.Current();ex.Next();info=inspect_shape(body)
            assert info['valid'] and info['solid_count']==1
            solids.append(body);actual_boxes.append(np.array(info['bounds_mm']).reshape(2,3))
        assert len(solids)==count
        unmatched=list(range(len(actual_boxes)))
        step_checks=[]
        for placement,mesh in zip(thing['gearbox']['layout'],meshes):
            match=min(unmatched,key=lambda i:np.max(np.abs(actual_boxes[i]-mesh.bounds)))
            assert np.max(np.abs(actual_boxes[match]-mesh.bounds))<=0.1
            unmatched.remove(match)
            name=placement['part']
            local=dict(id=definition['id']+'__'+name,mode=mode,**thing['gearbox']['pieces'][name]['thing'],
                sequential_unions=True,compound_cuts=True,dimensions=thing['dimensions'])
            if name in ('rotor_a','rotor_b'):
                reference=_move(build_shape(compile_thing(local)['tree']),'translate',placement['pos'])
                path=attempt/(name+'_placed_check.step');writer=STEPControl_Writer()
                assert writer.Transfer(solids[match],STEPControl_AsIs)==IFSelect_RetDone
                assert writer.Write(str(path))==IFSelect_RetDone
                checked=verify_step(path,reference)
                step_checks.append(dict(part=name,valid=True,linear_tolerance_mm=checked['linear_tolerance_mm'],
                    bounds_error_mm=checked['bounds_error_mm'],volume_error_mm3=checked['volume_error_mm3'],
                    comparison_method=checked['comparison_method']))
        combined=trimesh.util.concatenate(meshes)
        for i,first in enumerate(meshes):
            for second in meshes[i+1:]:
                overlap=np.minimum(first.bounds[1,:2],second.bounds[1,:2])-np.maximum(first.bounds[0,:2],second.bounds[0,:2])
                assert not np.all(overlap>0),'Print-layout XY bounds overlap'
        assert combined.is_watertight and combined.is_winding_consistent and combined.is_volume
        assert len(combined.split())==count
        original=attempt/'generated.stl'
        if original.exists() and not (attempt/'generated_raw_native.stl').exists():
            shutil.copyfile(original,attempt/'generated_raw_native.stl')
        combined.export(original)
        destination=PART/(mode+'_solidcraft.stl')
        temporary=destination.with_name(destination.name+'.'+uuid.uuid4().hex+'.tmp')
        shutil.copyfile(original,temporary);os.replace(temporary,destination)
        for file in record['published_files']:
            if file['file']==destination.name:file['sha256']=digest(destination)
        record['layout_mesh_verification']=dict(body_count=count,watertight=True,placement_bounds_checked=True,
            method='exported STEP placement boxes, independent placed rotor geometry, and translated accepted native piece meshes',sources=source_files,
            placed_step_checks=step_checks,native_reported_boxes=[b['bbox'] for b in measured['bodies']])
        write_json(manifest_path,record);write_json(Path(record['manifest']),record)
        results[mode]=record['layout_mesh_verification']
    write_json(PROJECT/'solidcraft/layout_validation.json',dict(status='passed',results=results))
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--modes',nargs='+',default=['true','3dpr'])
    verify(parser.parse_args().modes)
