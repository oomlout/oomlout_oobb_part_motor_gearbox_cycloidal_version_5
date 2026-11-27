"""Combine disjoint checks of the same saved native source after all complete."""
import hashlib
import json
from pathlib import Path
from gearbox_native.project import PROJECT
from gearbox_native.verify_v7_assembly import CASES


def main():
    root=PROJECT/'build/native_v7/assembly_03'
    main_path=root/'assembly_verification.json'
    initial=root/'assembly_verification_initial_run.json'
    if not initial.exists():initial.write_bytes(main_path.read_bytes())
    digest=hashlib.sha256((root/'gearbox.solidcraft').read_bytes()).hexdigest()
    result={'status':'passed','native_only_edits':True,'native_sha256':digest,'cases':{},'source_reports':{}}
    for name in (initial.name,'manual_verification.json','m6_verification.json','views_verification.json'):
        file=root/name;data=json.loads(file.read_text())
        assert data['native_sha256']==digest
        if name!=initial.name:assert data['status']=='passed'
        result['source_reports'][name]=hashlib.sha256(file.read_bytes()).hexdigest()
        for case,row in data['cases'].items():
            assert row['status']=='passed' and row['changes']==CASES[case]
            assert case not in result['cases']
            result['cases'][case]=row
    assert set(result['cases'])==set(CASES)
    main_path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Collected',len(result['cases']),'native parameter cases')


if __name__=='__main__':main()
