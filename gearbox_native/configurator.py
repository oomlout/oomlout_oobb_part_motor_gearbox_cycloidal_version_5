"""Validated explorer/native controls -> OOMP recipe -> native gearbox.

Each update is an isolated catalogue revision. Only a completely accepted build
and fit check changes the active pointer; old files remain available on failure.
"""
import argparse, json, os, shutil, subprocess, sys, uuid
from pathlib import Path
from gearbox_native import controls
from gearbox_native.project import PROJECT, VERSION, active_part


def recipe(values):
    from working_oomp_populate import get_options
    from gearbox_native.captured import resolve
    import yaml
    values=controls.validate(values)
    options=get_options([controls.to_kwargs(values)])
    raw=options[0]['oobb_details']
    overrides=yaml.safe_load((PROJECT/'gearbox_native/design.yaml').read_text(encoding='utf-8')).get('parameters',{})
    conflicts=set(overrides)&set(controls.to_kwargs(values))
    if conflicts:raise ValueError('Move these design.yaml overrides to shared controls first: '+', '.join(sorted(conflicts)))
    raw.update(overrides)
    c=resolve(raw)
    return values,options[0],c


def check(values):
    values,option,c=recipe(values)
    sampling={}
    from gearbox_native.equation_surfaces import profile_api
    for name in ('rotor_a','rotor_b'):
        path=active_part()/'solidcraft/true'/(name+'_manifest.json')
        if not path.exists():continue
        record=json.loads(path.read_text(encoding='utf-8'))
        profile=Path(record['verification_evidence'])/'equation_profile.json'
        if not profile.exists():continue
        geometry=json.loads(profile.read_text(encoding='utf-8'))
        if geometry['cycloidal_parameters']['ring_pin_count']!=c['reduction']:
            sampling[name]={'regenerate':True,'reason':'Ring count changes the equation and sampling topology'}
        else:
            try:
                result=profile_api().validate_edit(geometry,dict(pitch_radius=c['pitch_radius'],eccentricity=c['radius_offset'],
                    roller_radius=c['lobe_radius'],clearance=c['lobe_clearance']))
                sampling[name]={'regenerate':False,**{k:v for k,v in result.items() if k!='points'}}
            except ValueError as error:sampling[name]={'regenerate':True,'reason':str(error)}
    return dict(status='recipe_valid',values=values,resolved_values=controls.from_config(c),
        diameter_mm=2*c['housing_radius'],height_mm=c['overall_height'],
        pitch_sizing=c['radius_calculation'],sampling=sampling,
        note='Full native, assembly and installation checks run during Update gearbox. Fixed samples are regenerated on every update.')


def atomic_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.tmp');temp.write_text(json.dumps(data,indent=2),encoding='utf-8');os.replace(temp,path)


def read_native(path):
    from oobb_solidcraft.mcp import MCPClient
    from oobb_solidcraft.backend import require_ok
    folder=PROJECT/'build/parametric_v7/read_controls'/uuid.uuid4().hex[:10]
    with MCPClient(folder,design=Path(path).resolve(),allow_path=PROJECT,timeout=600) as client:
        result=require_ok(client.call('execute',dict(command='parameters.list',params={'filter':'user'})))
    rows=result['parameters']
    if isinstance(rows,dict):rows=[dict(name=k,**v) for k,v in rows.items()]
    values={r['name']:r['value'] for r in rows if r['name'] in controls.SPECS}
    missing=set(controls.SPECS)-set(values)
    if missing:raise ValueError('Not a gearbox control document; missing '+', '.join(sorted(missing)))
    return controls.validate(values)


def make_master(values,part=None,path=None):
    from gearbox_native.project import require_legacy_authoring
    require_legacy_authoring()
    from oobb_solidcraft.mcp import MCPClient
    from oobb_solidcraft.backend import require_ok
    from gearbox_native.acceptance import health_check
    part=Path(part or active_part());path=Path(path or PROJECT/'gearbox_controls.solidcraft')
    folder=PROJECT/'build/parametric_v7/master'/uuid.uuid4().hex[:10]
    with MCPClient(folder,design=part/'true.solidcraft',allow_path=PROJECT,timeout=600) as client:
        for entry in controls.native_commands(values):require_ok(client.call('execute',entry))
        require_ok(client.call('execute',dict(command='document.metadata.set',params={'key':'org.oomlout.gearbox.controls',
            'value':dict(version=VERSION,part_id=part.name,update='Run action_update_gearbox.py --from-native gearbox_controls.solidcraft after saving.',
                         behavior='Master controls require Update gearbox; source rotor dimensions are live locally.')})))
        health_check(client,folder/'health.json')
        require_ok(client.call('save',{'path':str(path)}))
    with MCPClient(folder/'reopen',design=path,allow_path=PROJECT,timeout=600) as client:
        health_check(client,folder/'reopened.json')
    return str(path)


def build(values,*,select=True,recipe_only=False):
    if not recipe_only:
        from gearbox_native.project import require_legacy_authoring
        require_legacy_authoring()
    report=check(values);values,option,c=recipe(values)
    revision='configuration_'+uuid.uuid4().hex[:8]
    option['taxonomy_7']=revision
    option['oobb_details']['taxonomy_7']=revision
    from working_oomp_populate import build_oomp_id
    part_id=build_oomp_id(option);part=PROJECT/'parts'/part_id
    attempt=PROJECT/'build/parametric_v7/updates'/revision;attempt.mkdir(parents=True)
    atomic_json(attempt/'request.json',dict(version=VERSION,values=values,option=option))
    atomic_json(attempt/'preflight.json',report)
    env=dict(os.environ,GEARBOX_ACTIVE_PART=part_id,GEARBOX_FIT_OUTPUT=str(attempt/'fit'),PYTHONIOENCODING='utf-8')
    ordinary=shutil.which('python')
    code="import json,sys;from oomp_populate_helper import write_extras;import working_oomp;d=json.load(open(sys.argv[1],encoding='utf-8'));write_extras([d['option']]);working_oomp.main(part_filter=sys.argv[2])"
    def run(args,label):
        print(label,flush=True)
        with (attempt/(label+'.log')).open('w',encoding='utf-8') as log:
            subprocess.run(args,cwd=PROJECT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    run([ordinary,'-c',code,str(attempt/'request.json'),part_id],'populate')
    run([sys.executable,'-m','gearbox_native.fit','--recipe'],'recipe_fit')
    if recipe_only:
        report.update(status='recipe_fit_passed',part_id=part_id,revision=revision,attempt=str(attempt),
            note='Diagnostic only: no new native CAD acceptance and no active-selection change.')
        atomic_json(part/'recipe_study.json',report)
        return report
    source=active_part()/'solidcraft'
    if source.exists():
        shutil.copytree(source,part/'solidcraft',dirs_exist_ok=True)
        for manifest in (part/'solidcraft').rglob('*_manifest.json'):
            data=json.loads(manifest.read_text(encoding='utf-8'));data['part_id']=part_id
            atomic_json(manifest,data)
    from gearbox_native.coupons import recipes
    seed=active_part()/'fits/3dpr';target=part/'fits/3dpr'
    if seed.exists():
        target.mkdir(parents=True,exist_ok=True)
        for name in recipes(c):
            for suffix in ('.solidcraft','.step','.stl','.png','_manifest.json','_structure.json'):
                if (seed/(name+suffix)).exists():shutil.copyfile(seed/(name+suffix),target/(name+suffix))
    run([sys.executable,'working_solidcraft.py','--worker','--filter',part_id,'--stl','--extras','--verify'],'native_build')
    run([sys.executable,'-m','gearbox_native.validate'],'native_validation')
    run([sys.executable,'-m','gearbox_native.fit'],'native_fit')
    run([sys.executable,'-m','gearbox_native.coupons'],'fit_samples')
    fit=attempt/'fit/native_fit.json'
    shutil.copyfile(fit,part/'parametric_fit.json')
    report.update(status='accepted',part_id=part_id,revision=revision,attempt=str(attempt))
    atomic_json(part/'control_build.json',report)
    master=make_master(values,part,path=part/'gearbox_controls.solidcraft')
    if select:
        atomic_json(controls.VALUES_PATH,dict(version=VERSION,values=values,revision=revision))
        atomic_json(PROJECT/'solidcraft/active_design.json',dict(version=VERSION,part_id=part_id,build=str(part/'control_build.json')))
        shutil.copyfile(master,PROJECT/'gearbox_controls.solidcraft')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings',type=Path)
    parser.add_argument('--from-native',type=Path)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--master',action='store_true')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--no-select',action='store_true',help='Validate a new example revision without selecting it as the working gearbox.')
    parser.add_argument('--recipe-only',action='store_true',help='Run the full recipe fit diagnostic in isolation, without generating or selecting native files.')
    args=parser.parse_args()
    if args.from_native:values=read_native(args.from_native)
    elif args.settings:
        data=json.loads(args.settings.read_text(encoding='utf-8'))
        values=controls.from_explorer(data['explorer']) if 'explorer' in data else data.get('values',data)
        if 'explorer' in data:values.update({k:data[k] for k in controls.VIEW_NAMES if k in data})
    else:values=controls.validate(controls.saved_overrides())
    result=check(values) if args.check else {'master':make_master(values)} if args.master else build(values,select=not args.no_select,recipe_only=args.recipe_only)
    if args.output:atomic_json(args.output,result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
