"""Build current native pieces, then a linked SolidCraft print-layout assembly.

Private headless sessions and immutable attempts follow the plate migration.
The single OOMP catalogue item and all existing SCAD files are preserved.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import traceback
import uuid
from concurrent.futures import ProcessPoolExecutor,as_completed

import yaml
from oobb_solidcraft.backend import render_thing, require_ok, health_check
from oobb_solidcraft.compiler import compile_thing
from oobb_solidcraft.construction import build_thing
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.pipeline import output_lock
from oobb_solidcraft.runtime import write_json, digest
from oobb_solidcraft.build_policy import enabled
from oobb_solidcraft._loader import ROOT, COMPONENTS_ROOT
from gearbox_native.project import VERSION


def geometry_digest(plan):
    def clean(value):
        if isinstance(value,list):return [clean(v) for v in value]
        if isinstance(value,dict):
            result={k:clean(v) for k,v in value.items() if k not in ('source_id','logical_id','intent','cad_name')}
            # Shared compiler revisions may omit transforms of empty geometry.
            # Normalize those no-ops without ignoring any material or dimensions.
            children=result.get('children',[])
            empty=lambda n:n.get('op')=='union' and not n.get('children')
            op=result.get('op')
            if op=='union':
                result['children']=[n for n in children if not empty(n)]
            elif op in ('translate','rotate') and len(children)==1 and empty(children[0]):
                return {'op':'union','children':[]}
            elif op=='difference' and children and empty(children[0]):
                return {'op':'union','children':[]}
            return result
        return value
    return hashlib.sha256(json.dumps(clean(plan['tree']),sort_keys=True).encode()).hexdigest()


def render_piece(local,plan,attempt,construction,export_stl,export_extras):
    """Prefer editable native dimensions; dense rotors use native surfaces."""
    from gearbox_native import acceptance
    from gearbox_native.native_surfaces import render as surface_renderer
    if construction != 'native':raise ValueError('Only native construction is published')
    dense=any(f['geometry']['kind'] in ('polygon','parametric_profile') and len(f['geometry']['points'])>256 for f in plan['features'])
    # These profiles are much quicker and more reliable as native surfaces;
    # their coordinated dimensions remain editable in the recipe.
    surface_first=dense or local['id'].endswith(('__motor_mount','__output_casing','__output_casing_lower','__output_casing_upper','__eccentric_hub_lower',
        '__fit_casing_clamp_lower','__fit_casing_clamp_upper','__fit_casing_OOBB_tab'))
    strategies=(['surfaces'] if dense else ['surfaces','features']) if surface_first else ['features','surfaces']
    errors={}
    for strategy in strategies:
        folder=Path(attempt)/strategy;folder.mkdir(parents=True,exist_ok=True)
        try:
            if strategy=='features':
                outcome=render_thing(local,plan=plan,output_dir=folder,export_stl=True,
                    export_extras=True,verify_solidcraft=True,verification_policy=acceptance)
            else:
                outcome=surface_renderer(local,plan=plan,output_dir=folder,export_stl=export_stl,
                    export_extras=export_extras,verify_solidcraft=True)
            for name in ('generated.solidcraft','generated.step','generated.stl','cad_structure.json','native.png','measurements.json'):
                if (folder/name).is_file():shutil.copyfile(folder/name,Path(attempt)/name)
            for artifact in outcome.get('artifacts',[]):
                artifact['path']=str(Path(attempt)/Path(artifact['path']).name)
            outcome.update(construction='native',native_method=strategy,verification_policy=acceptance.POLICY_VERSION,
                strategy_attempts=errors,verification_evidence=str(folder),native_feature_history=True)
            return outcome
        except Exception as error:
            (folder/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8')
            errors[strategy]=str(error)
    (Path(attempt)/'failure.txt').write_text(json.dumps(errors,indent=2),encoding='utf-8')
    return {'error':errors}


def publish_files(source, destination, names):
    destination.mkdir(parents=True, exist_ok=True)
    published=[]
    for old, new in names.items():
        path=source/old
        temporary=destination/(new+'.'+uuid.uuid4().hex+'.tmp')
        shutil.copyfile(path, temporary)
        os.replace(temporary,destination/new)
        published.append(dict(file=new,sha256=digest(destination/new)))
    return published


def assembly(output, pieces, placements, *, mode, export_stl, export_extras):
    with MCPClient(output/'session',allow_path=output.parents[3],timeout=600) as client:
        for item in placements:
            require_ok(client.call('execute',{'command':'component.insert_design','params':{
                'path':str(pieces[item['part']]),'name':item['part'], 'translate':item['pos'], 'reuse':True}}))
        health=health_check(client,output/'native_inspection.json')
        measure=require_ok(client.call('measure'))
        write_json(output/'measurements.json',measure)
        require_ok(client.call('save',{'path':str(output/'generated.solidcraft')}))
        for ext in (['step'] if export_extras else [])+(['stl'] if export_stl else []):
            require_ok(client.call('export',{'path':str(output/('generated.'+ext))}))
        if export_extras:
            require_ok(client.call('screenshot',{'source':'model','view':'iso','path':str(output/'native.png'),
                'width':1400,'height':1000,'grid':False,'axes':False}))
    with MCPClient(output/'reopen',design=output/'generated.solidcraft',allow_path=output.parents[3],timeout=600) as client:
        reopened=health_check(client,output/'reopened_inspection.json')
        after=require_ok(client.call('measure'))
        if after != measure:
            # Exact JSON can differ in irrelevant display metadata. Require the
            # physical body count and total volume to remain the same.
            write_json(output/'reopened_measurements.json',after)
        if len(reopened['bodies']) != len(health['bodies']):
            raise ValueError('Linked assembly body count changed on reopen')
        if abs(after['total']['volume_mm3']-measure['total']['volume_mm3']) > 1e-6:
            raise ValueError('Linked assembly volume changed on reopen')
    return dict(body_count=len(health['bodies']),placement_count=len(placements),reopened=True)


def run(project,part_filter,modes,*,export_stl=False,export_extras=False,verify_solidcraft=False):
    project=Path(project).resolve()
    config=json.loads((project/'solidcraft/config.json').read_text(encoding='utf-8'))
    construction=config.get('construction','native')
    if construction != 'native':
        raise ValueError('Deliverables require fully native features; STEP-backed construction is diagnostic only')
    workers=config.get('workers',1)
    if type(workers) is not int or workers not in (1,2):raise ValueError('workers must be 1 or 2')
    root=project/'build/solidcraft'
    root.mkdir(parents=True,exist_ok=True)
    results=[]
    # Cache validity includes native recipe, helpers and catalogue resources.
    sources={}
    for base in (project/'gearbox_native', ROOT/'oobb_solidcraft',COMPONENTS_ROOT,ROOT/'catalog'):
        for path in sorted(base.rglob('*')):
            if path.is_file() and path.suffix in ('.py','.yaml') and '__pycache__' not in path.parts:
                sources[str(path)]=digest(path)
    with output_lock(root):
        def summary(*, completed=False):
            status='running'
            if completed:
                status='success' if results and all(r['status'] in ('success','skipped') for r in results) else 'failed'
            value=dict(status=status,results=results)
            write_json(root/'latest_run.json',value)
            return value
        write_json(root/'latest_run.json',dict(status='running',results=[]))
        for part_path in sorted((project/'parts').glob('*/working.yaml')):
            if (part_path.parent/'SEALED.json').exists():
                continue
            part=yaml.safe_load(part_path.read_text(encoding='utf-8'))
            if part_filter and part_filter not in part['id']:
                continue
            details=part.get('oobb_details',{})
            if not enabled(details,'solidcraft'):
                results.append(dict(part_id=part['id'],status='skipped',reason='run_solidcraft is false'))
                continue
            if details.get('architecture') not in ('captured_6810', 'compact_6810', 'simple_6810') or details.get('oobb_name') != VERSION:
                raise ValueError('Only the current captured_6810 native version is editable')
            for mode in modes:
                thing=build_thing(part,builder_path=project/'working_solidcraft.py',mode=mode)
                gearbox=thing['gearbox']
                published={}
                failed=False
                executor=ProcessPoolExecutor(max_workers=workers)
                pending={}
                for name,piece in gearbox['pieces'].items():
                    local=dict(id=part['id']+'__'+name,mode=mode,**copy.deepcopy(piece['thing']),
                               sequential_unions=True,compound_cuts=True,dimensions=thing['dimensions'])
                    contract='coupled_rotor_interfaces_v1' if name in ('rotor_a','rotor_b') else None
                    if contract:local['rotor_interfaces']=dict(config=gearbox['config'],side=int(name=='rotor_b'))
                    plan=compile_thing(local)
                    key=hashlib.sha256(json.dumps(dict(thing=local,plan=plan,sources=sources,construction=construction,
                        stl=export_stl,extras=export_extras,verify=verify_solidcraft),sort_keys=True).encode()).hexdigest()
                    destination=part_path.parent/'solidcraft'/mode
                    manifest_path=destination/(name+'_manifest.json')
                    cached=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
                    same_geometry=False
                    from gearbox_native.acceptance import POLICY_VERSION
                    # A directly dimensioned part can be identical in both
                    # modes. Reuse only verified native artifacts whose exact
                    # CSG digest and complete file hashes match; retain evidence.
                    if cached.get('geometry_sha256')!=geometry_digest(plan):
                        for sibling in ('true','3dpr'):
                            if sibling==mode:continue
                            candidate_path=part_path.parent/'solidcraft'/sibling/(name+'_manifest.json')
                            if not candidate_path.is_file():continue
                            candidate=json.loads(candidate_path.read_text())
                            if (candidate.get('geometry_sha256')!=geometry_digest(plan)
                                or candidate.get('parameter_contract')!=contract
                                or candidate.get('construction')!='native'
                                or candidate.get('verification_policy')!=POLICY_VERSION
                                or not candidate.get('native_feature_history')
                                or candidate.get('status')!='success'
                                or candidate.get('verification',{}).get('status')!='passed'):continue
                            files=candidate.get('published_files',[])
                            if not files or not all((candidate_path.parent/f['file']).is_file()
                                and digest(candidate_path.parent/f['file'])==f['sha256'] for f in files):continue
                            destination.mkdir(parents=True,exist_ok=True)
                            for f in files:shutil.copyfile(candidate_path.parent/f['file'],destination/f['file'])
                            cached=copy.deepcopy(candidate);cached['mode']=mode
                            cached['identical_geometry_reused_from']=str(candidate_path)
                            write_json(manifest_path,cached)
                            break
                    if cached.get('construction')=='native' and cached.get('verification_policy')==POLICY_VERSION and cached.get('native_feature_history'):
                        previous_plan=Path(cached.get('manifest','')).parent/'plan.json'
                        old_geometry=cached.get('geometry_sha256')
                        if not old_geometry and previous_plan.is_file():old_geometry=geometry_digest(json.loads(previous_plan.read_text()))
                        same_geometry=old_geometry==geometry_digest(plan) and cached.get('parameter_contract')==contract
                    required={name+'.solidcraft',name+'_structure.json'}
                    if export_stl:required.add(name+'.stl')
                    if export_extras:required.update((name+'.step',name+'.png'))
                    if (cached.get('build_key')==key or same_geometry) and cached.get('status')=='success' and cached.get('verification',{}).get('status')=='passed' and required<={f['file'] for f in cached.get('published_files',[])} and all(
                            (destination/f['file']).is_file() and digest(destination/f['file'])==f['sha256']
                            for f in cached.get('published_files',[])):
                        print(f'{mode} {name}: current',flush=True)
                        if same_geometry:
                            cached['reuse_check']=dict(build_key=key,geometry_sha256=geometry_digest(plan),sources=sources)
                            write_json(manifest_path,cached)
                        published[name]=destination/(name+'.solidcraft')
                        results.append(dict(part_id=part['id'],piece=name,mode=mode,status='success',cached=True,manifest=str(manifest_path)))
                        continue
                    attempt=root/'attempts'/uuid.uuid4().hex[:12]
                    attempt.mkdir(parents=True)
                    record=dict(part_id=part['id'],piece=name,mode=mode,status='failed',build_key=key,construction=construction,
                                parameter_contract=contract,
                                geometry_sha256=geometry_digest(plan),
                                sources=sources,manifest=str(attempt/'build_manifest.json'))
                    print(f'Building {mode} {name}: {attempt.name}',flush=True)
                    write_json(attempt/'definition.json',local)
                    write_json(attempt/'plan.json',plan)
                    future=executor.submit(render_piece,local,plan,attempt,construction,export_stl,export_extras)
                    pending[future]=(name,attempt,record,manifest_path,destination)
                for future in as_completed(pending):
                    name,attempt,record,manifest_path,destination=pending[future]
                    try:
                        outcome=future.result()
                        if 'error' in outcome:raise RuntimeError(outcome['error'])
                        record.update(outcome)
                        names={'generated.solidcraft':name+'.solidcraft','cad_structure.json':name+'_structure.json'}
                        if construction=='step_backed':names['source.step']=name+'_source.step'
                        if export_stl: names['generated.stl']=name+'.stl'
                        if export_extras: names.update({'generated.step':name+'.step','native.png':name+'.png'})
                        record['published_files']=publish_files(attempt,destination,names)
                        record['status']='success'
                        write_json(manifest_path,record)
                        published[name]=destination/(name+'.solidcraft')
                    except Exception as error:
                        failed=True
                        record['error']=str(error)
                        if not (attempt/'failure.txt').exists():
                            (attempt/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8')
                    write_json(attempt/'build_manifest.json',record)
                    results.append({k:record[k] for k in ('part_id','piece','mode','status','manifest')})
                    summary()
                    print(f'{mode} {name}: {record["status"]}',flush=True)
                executor.shutdown(wait=True)
                if not failed:
                    attempt=root/'attempts'/uuid.uuid4().hex[:12]
                    attempt.mkdir(parents=True)
                    record=dict(part_id=part['id'],mode=mode,piece='print_layout',status='failed',construction=construction,manifest=str(attempt/'build_manifest.json'))
                    try:
                        record.update(assembly(attempt,published,gearbox['layout'],mode=mode,export_stl=export_stl,export_extras=export_extras))
                        names={'generated.solidcraft':mode+'.solidcraft','measurements.json':mode+'_solidcraft_measurements.json'}
                        if export_stl: names['generated.stl']=mode+'_solidcraft.stl'
                        if export_extras: names.update({'generated.step':mode+'.step','native.png':mode+'_solidcraft.png'})
                        record['published_files']=publish_files(attempt,part_path.parent,names)
                        record['piece_links']={n:str(p) for n,p in published.items()}
                        record['status']='success'
                        write_json(part_path.parent/(mode+'_solidcraft_manifest.json'),record)
                        from gearbox_native.documentation import publish as publish_documentation
                        publish_documentation(part_path.parent,gearbox)
                    except Exception as error:
                        record['error']=str(error)
                        (attempt/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8')
                    write_json(attempt/'build_manifest.json',record)
                    results.append({k:record[k] for k in ('part_id','piece','mode','status','manifest')})
                    summary()
        final=summary(completed=True)
        if final['status']=='success': write_json(root/'latest_success.json',final)
    if final['status']!='success':
        raise RuntimeError(f'Native build incomplete; inspect {root / "latest_run.json"}')
    return final
