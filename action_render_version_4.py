"""One-command V4 HQ hardware generation and rendering. No AI/API keys needed.

python action_render_version_4.py            # hardware, PNG, MP4, GIF, .blend
python action_render_version_4.py --preview  # hardware, PNG and editable scene
python action_render_version_4.py --hardware-only
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

PROJECT=Path(__file__).resolve().parent


def main():
    config=json.loads((PROJECT/'solidcraft/config.json').read_text())
    # A normal Python install can launch this; CAD dependencies stay in the
    # already configured worker environment.
    if Path(sys.executable).resolve()!=Path(config['python']).resolve():
        raise SystemExit(subprocess.call([config['python'],str(Path(__file__).resolve()),*sys.argv[1:]],cwd=PROJECT))
    sys.path.insert(0,config['helper_root'])
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview',action='store_true')
    parser.add_argument('--hardware-only',action='store_true')
    parser.add_argument('--spacing',type=float,default=12)
    parser.add_argument('--mode',choices=['true'],default='true')
    args=parser.parse_args()
    if args.spacing<=0:parser.error('Spacing must be positive')
    from oobb_solidcraft.pipeline import output_lock
    state=PROJECT/'build/v4_presentation';state.mkdir(parents=True,exist_ok=True)
    with output_lock(state):
        run(args,state)


def run(args,state):
    from gearbox_native.presentation_version_4 import prepare
    from gearbox_native.high_quality_presentation import digest
    import render_solidcraft_exploded as media
    media.VERSION='version_4'
    job,path=prepare(PROJECT,args)
    path.write_text(json.dumps(job,indent=2)+'\n')
    if args.hardware_only:
        (state/'latest_run.json').write_text(json.dumps(dict(status='passed',stage='hardware',job=str(path)),indent=2)+'\n')
        print('V4 hardware generation complete:',path,flush=True);return
    blender=shutil.which('blender')
    if not blender:raise RuntimeError('Blender must be on PATH')
    out=Path(job['output'])
    with (out/'blender.log').open('w') as log:
        subprocess.run([blender,'--background','--factory-startup','--python',str(PROJECT/'gearbox_native/render_blender.py'),
                        '--',str(path)],stdout=log,stderr=subprocess.STDOUT,check=True)
    media.decorate(job)
    verification=None if args.preview else media.verify_media(job)
    report=dict(status='preview' if args.preview else 'passed',version='version_4',part_count=len(job['pieces']),
        hardware_count=len(job['hardware']),high_quality_hardware_count=job['high_quality_hardware_count'],
        verification=verification,hardware_geometry=job['hardware_geometry'],ai_required=False,scad_required=False,
        files={p.name:digest(p) for p in out.glob('solidcraft_exploded*') if p.suffix in ('.png','.mp4','.gif','.blend')})
    (out/'render_report.json').write_text(json.dumps(report,indent=2)+'\n')
    (state/'latest_run.json').write_text(json.dumps(dict(status='passed',stage='render',report=str(out/'render_report.json')),indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
