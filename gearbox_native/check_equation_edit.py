"""Check a proposed native edit against the actual published sample stations.

This validates sampling only. Regenerate the complete recipe for coordinated
changes to eccentric cams, hole clearances, casing and assembly placement.
"""
import argparse
import json
from pathlib import Path
from gearbox_native.project import active_part
from gearbox_native.equation_surfaces import profile_api


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--eccentricity',type=float,required=True)
    parser.add_argument('--mode',choices=['true','3dpr'],default='true')
    args=parser.parse_args();reports={}
    for name in ('rotor_a','rotor_b'):
        manifest=json.loads((active_part()/'solidcraft'/args.mode/(name+'_manifest.json')).read_text())
        geometry=json.loads((Path(manifest['verification_evidence'])/'equation_profile.json').read_text())
        result=profile_api().validate_edit(geometry,{'eccentricity':args.eccentricity})
        reports[name]={k:v for k,v in result.items() if k!='points'}
    print(json.dumps(reports,indent=2))


if __name__=='__main__':main()
