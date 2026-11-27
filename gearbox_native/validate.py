"""Audit current native deliverables. No SCAD files or snapshots are required."""
import argparse
import json
from pathlib import Path
import traceback
import yaml
from oobb_solidcraft.compiler import compile_thing
from oobb_solidcraft.construction import build_thing
from oobb_solidcraft.runtime import write_json,digest
from gearbox_native.export import geometry_digest
from gearbox_native.exact_geometry import build_shape
from gearbox_native.acceptance import verify_step,verify_mesh,POLICY_VERSION

PROJECT=Path(__file__).resolve().parents[1]
from gearbox_native.project import active_part, require_editable
PART=active_part(PROJECT)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modes',nargs='+',default=['true','3dpr'])
    parser.add_argument('--filter',default='')
    parser.add_argument('--deep',action='store_true',help='Repeat STEP and mesh geometry checks; normally audit saved acceptance evidence and hashes.')
    args=parser.parse_args();report=dict(results={},reference='current_native_recipe',policy_version=POLICY_VERSION,
        requested_modes=args.modes,selection_filter=args.filter,coverage_complete=False)
    part=yaml.safe_load((PART/'working.yaml').read_text());missing=[];expected_count=0
    for mode in args.modes:
        thing=build_thing(part,builder_path=PROJECT/'working_solidcraft.py',mode=mode)
        expected_count+=len(thing['gearbox']['pieces'])
        for name,piece in thing['gearbox']['pieces'].items():
            if args.filter and args.filter not in name:continue
            key=mode+'/'+name;folder=PART/'solidcraft'/mode;path=folder/(name+'_manifest.json')
            if not path.exists():missing.append(key);continue
            item=dict(status='failed',manifest=str(path));print('Checking',key,flush=True)
            try:
                manifest=json.loads(path.read_text())
                assert manifest['status']=='success' and manifest['construction']=='native'
                assert manifest['verification']['status']=='passed' and manifest['verification_policy']==POLICY_VERSION
                assert manifest['native_feature_history']
                local=dict(id=part['id']+'__'+name,mode=mode,**piece['thing'],
                    sequential_unions=True,compound_cuts=True,dimensions=thing['dimensions'])
                plan=compile_thing(local)
                assert geometry_digest(plan)==manifest['geometry_sha256'],'Recipe changed: regenerate this part'
                assert manifest['published_files']
                for file in manifest['published_files']:
                    assert digest(folder/file['file'])==file['sha256'],file['file']
                evidence=Path(manifest['verification_evidence'])
                measurements=json.loads((evidence/'measurements.json').read_text())
                assert measurements.get('edit_response',{}).get('changed'),'Missing effective native edit check'
                inspection=json.loads((evidence/'native_inspection.json').read_text())
                feature_types=[f['type'] for f in inspection['timeline']]
                assert inspection['sketches'],'Missing native sketch history'
                assert not any('import' in t.lower() or 'mesh' in t.lower() for t in feature_types),'Imported geometry in a native piece'
                item['native_feature_count']=len(feature_types)
                item['native_sketch_count']=len(inspection['sketches'])
                item['imported_geometry']=False
                if args.deep:
                    expected=build_shape(plan['tree'])
                    item['step']=verify_step(folder/(name+'.step'),expected)
                    item['stl']=verify_mesh(folder/(name+'.stl'),expected)
                item.update(status='passed',native_method=manifest['native_method'],edit_response=measurements['edit_response'])
            except Exception as error:
                item.update(error=str(error),traceback=traceback.format_exc())
            report['results'][key]=item
    report['missing']=missing
    report['coverage_complete']=not args.filter and set(args.modes)=={'true','3dpr'} and len(report['results'])==expected_count and not missing
    report['status']='failed' if any(i['status']=='failed' for i in report['results'].values()) else ('incomplete' if missing else 'passed')
    write_json(PROJECT/'solidcraft/validation.json',report)
    if report['status']!='passed':raise SystemExit(1)


if __name__=='__main__':main()
