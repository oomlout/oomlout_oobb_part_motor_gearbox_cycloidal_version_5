"""Render the latest native SolidCraft pieces; no SCAD dependency.

Run with the Python configured in solidcraft/config.json. Requires Blender and
ffmpeg on PATH. --preview makes only the still and editable scene.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

PROJECT = Path(__file__).resolve().parent
settings = json.loads((PROJECT/'solidcraft/config.json').read_text())
sys.path.insert(0, settings['helper_root'])
from gearbox_native.presentation import assembly_parts, motion
from gearbox_native.project import active_part, VERSION, require_editable


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(args):
    import yaml
    from oobb_solidcraft.construction import build_thing
    from oobb_solidcraft.compiler import compile_thing
    from gearbox_native.export import geometry_digest
    part_dir = active_part(PROJECT)
    require_editable(part_dir)
    part = yaml.safe_load((part_dir/'working.yaml').read_text())
    thing = build_thing(part, builder_path=PROJECT/'working_solidcraft.py', mode=args.mode)
    pieces = assembly_parts(thing['gearbox']['config'])
    for item in pieces:
        name = item['name']
        folder = part_dir/'solidcraft'/args.mode
        manifest = json.loads((folder/(name+'_manifest.json')).read_text())
        assert manifest['status'] == 'success' and manifest['construction'] == 'native'
        local = dict(id=part['id']+'__'+name, mode=args.mode, **thing['gearbox']['pieces'][name]['thing'],
                     sequential_unions=True, compound_cuts=True, dimensions=thing['dimensions'])
        assert geometry_digest(compile_thing(local)) == manifest['geometry_sha256'], f'Regenerate changed native part: {name}'
        files = {f['file']: f['sha256'] for f in manifest['published_files']}
        for suffix in ('.stl', '.solidcraft'):
            assert sha(folder/(name+suffix)) == files[name+suffix], f'Changed published artifact: {name+suffix}'
        item.update(stl=str(folder/(name+'.stl')), stl_sha256=files[name+'.stl'],
                    native_document=str(folder/(name+'.solidcraft')))
    output = part_dir/'solidcraft_renders'/args.mode
    if args.hardware: output=output/'with_hardware'
    output.mkdir(parents=True, exist_ok=True)
    hardware=[]
    if args.hardware:
        from gearbox_native.presentation_hardware import build_hardware
        hardware=build_hardware(thing['gearbox']['config'],output/'hardware_meshes')
        for item in hardware:
            for asset in item['assets']:asset['sha256']=sha(asset['stl'])
    job = dict(version=VERSION, project=str(PROJECT), output=str(output), mode=args.mode, pieces=pieces,
               config=thing['gearbox']['config'], spacing=args.spacing, fps=24, frames=360,
               still_size=2000, video_size=1200, preview_only=args.preview,
               geometry_source='verified native SolidCraft exports', hardware_included=args.hardware,
               hardware=hardware,hardware_geometry='parametric nominal envelopes; threads and rolling elements omitted')
    path = output/'render_job.json'
    return job, path


def decorate(job):
    from PIL import Image, ImageDraw, ImageFont
    out = Path(job['output'])
    display_version=job.get('version',VERSION).replace('version_', 'V')
    def font(size, bold=False):
        return ImageFont.truetype('C:/Windows/Fonts/'+('segoeuib.ttf' if bold else 'segoeui.ttf'), size)
    def canvas(path, title, subtitle):
        raw = Image.open(path).convert('RGBA')
        image = Image.new('RGB', raw.size, '#edf0f2')
        image.paste(raw, mask=raw.getchannel('A'))
        d = ImageDraw.Draw(image)
        s = image.width/2000
        d.text((70*s, 48*s), title, font=font(round(48*s), True), fill='#213640')
        d.text((72*s, 112*s), subtitle, font=font(round(25*s)), fill='#5a6d76')
        footer=(f"{len(job['pieces'])} NATIVE SOLIDCRAFT PARTS   /   {len(job['hardware'])} NOMINAL HARDWARE ITEMS" if job['hardware_included']
                else f"NATIVE SOLIDCRAFT GEOMETRY   /   {len(job['pieces'])} PRINTED COMPONENTS   /   HARDWARE OMITTED")
        d.text((72*s, image.height-66*s), footer,
               font=font(round(20*s)), fill='#5a6d76')
        return image
    height=job['config'].get('overall_height',job['config']['housing_depth']+job['config']['front_retainer_depth'])
    subtitle=f"{job['config']['reduction']}:1 · {height:g} mm above motor · Exploded assembly · {'Nominal' if job['mode']=='true' else 'Print-clearance'} parts"
    image = canvas(out/'exploded_raw.png', 'CYCLOIDAL GEARBOX / '+display_version, job.get('presentation_subtitle',subtitle))
    d = ImageDraw.Draw(image)
    anchors = json.loads((out/'anchors.json').read_text())
    # Numbered callouts avoid long labels crossing the mechanism. The legend is
    # below each column in a separate companion sheet generated from the same view.
    for index, item in enumerate(job['pieces'], 1):
        x,y = [v*image.width for v in anchors[item['name']]]
        dx = -78 if item['member']=='input' else 85 if item['member']=='output' else -120
        end = (x+dx, y)
        d.line([(x,y),end], fill='#647680', width=2)
        d.ellipse((end[0]-19,end[1]-19,end[0]+19,end[1]+19), fill='#ffffff', outline='#647680', width=2)
        d.text(end, str(index), font=font(19, True), anchor='mm', fill='#213640')
    # Keep the main still clean; the companion key lists editable component IDs.
    image.save(out/'solidcraft_exploded.png')
    key = Image.new('RGB',(2000,760 if job['hardware_included'] else 540),'#edf0f2')
    kd = ImageDraw.Draw(key)
    for i,item in enumerate(job['pieces']):
        col,row = divmod(i,5)
        kd.text((70+col*640,38+row*96), f'{i+1:02d}  '+item['name'].replace('_',' ').capitalize(), font=font(27), fill='#213640')
    if job['hardware_included']:
        from collections import Counter
        counts=Counter(i['model'] for i in job['hardware'])
        summary=' · '.join(f'{count} {name.replace("_"," ")}' for name,count in counts.items())
        import textwrap
        kd.text((70,545),job.get('hardware_caption','HARDWARE / NOMINAL PRESENTATION MODELS'),font=font(26,True),fill='#213640')
        for line,text in enumerate(textwrap.wrap(summary,125)):
            kd.text((70,590+line*35),text,font=font(22),fill='#5a6d76')
    sheet = Image.new('RGB',(2000,2000+key.height),'#edf0f2')
    sheet.paste(image,(0,0)); sheet.paste(key,(0,2000))
    sheet.save(out/'solidcraft_exploded_key.png')
    if job['preview_only']: return
    decorated = out/'video_frames'; decorated.mkdir(exist_ok=True)
    for frame in range(1,job['frames']+1):
        _,turns,state = motion((frame-1)/job['fps'],job['config']['reduction'])
        pic=canvas(out/f'frames/frame_{frame:04d}.png','CYCLOIDAL GEARBOX / '+display_version,f"{job['config']['reduction']}:1 · {height:g} mm above motor · {state}")
        draw=ImageDraw.Draw(pic)
        draw.line([(42,pic.height-65),(42+(pic.width-84)*(frame-1)/(job['frames']-1),pic.height-65)],fill='#36798d',width=4)
        pic.save(decorated/f'frame_{frame:04d}.png')
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg: raise RuntimeError('ffmpeg is required')
    base=[ffmpeg,'-y','-loglevel','error','-framerate',str(job['fps']),'-start_number','1','-i',str(decorated/'frame_%04d.png')]
    subprocess.run(base+['-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'solidcraft_exploded.mp4')],check=True)
    subprocess.run(base+['-filter_complex','fps=12,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse=dither=sierra2_4a','-loop','0',str(out/'solidcraft_exploded.gif')],check=True)


def verify_media(job):
    """Check actual encoded frames and create a decoded-frame review sheet."""
    from PIL import Image
    out = Path(job['output'])
    ffmpeg, ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
    if not ffprobe: raise RuntimeError('ffprobe is required to verify the video')
    result = subprocess.run([ffprobe,'-v','error','-count_frames','-select_streams','v:0',
        '-show_entries','stream=width,height,nb_read_frames,avg_frame_rate,duration',
        '-of','json',str(out/'solidcraft_exploded.mp4')],capture_output=True,text=True,check=True)
    stream = json.loads(result.stdout)['streams'][0]
    assert int(stream['nb_read_frames']) == job['frames']
    assert (stream['width'],stream['height']) == (job['video_size'],job['video_size'])
    assert abs(float(stream['duration'])-job['frames']/job['fps']) < .05
    frames = sorted((out/'frames').glob('frame_*.png'))
    assert len(frames) == job['frames']
    unique = len({sha(p) for p in frames})
    assert unique > 100, 'Animation did not move as expected'
    # Decode the final MP4, rather than reviewing only the pre-encode images.
    review = out/'review'; review.mkdir(exist_ok=True)
    subprocess.run([ffmpeg,'-y','-loglevel','error','-i',str(out/'solidcraft_exploded.mp4'),
        '-vf','select=eq(n\\,0)+eq(n\\,48)+eq(n\\,84)+eq(n\\,150)+eq(n\\,240)+eq(n\\,359),scale=600:600',
        '-fps_mode','vfr',str(review/'decoded_%02d.png')],check=True)
    sheet = Image.new('RGB',(1800,1200),'white')
    for i,path in enumerate(sorted(review.glob('decoded_*.png'))):
        with Image.open(path) as im: sheet.paste(im,((i%3)*600,(i//3)*600))
    sheet.save(out/'animation_review.png')
    with Image.open(out/'solidcraft_exploded.gif') as gif:
        assert gif.n_frames == 180
        gif_frames=gif.n_frames
    return dict(video=stream,unique_rendered_frames=unique,gif_frames=gif_frames,
                review_sheet='animation_review.png',status='passed')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['true','3dpr'],default='true')
    parser.add_argument('--spacing',type=float,default=12.)
    parser.add_argument('--preview',action='store_true')
    parser.add_argument('--hardware',action='store_true',help='Include parametric bearings, motor, coupler and all fasteners in a separate output folder.')
    parser.add_argument('--finish',action='store_true',help='Decorate and encode an already rendered job.')
    args=parser.parse_args()
    if args.spacing<=0: parser.error('--spacing must be positive')
    # Finishing a rendered job is only safe when its geometry and pose settings
    # still match. Do not silently encode stale frames after a design edit.
    previous_path=active_part(PROJECT)/'solidcraft_renders'/args.mode/'render_job.json'
    if args.hardware:previous_path=previous_path.parent/'with_hardware/render_job.json'
    previous=json.loads(previous_path.read_text()) if args.finish else None
    job,path=prepare(args)
    if previous:
        assert previous == job, 'Rendered job changed; rerun without --finish'
    path.write_text(json.dumps(job, indent=2)+'\n')
    if not args.finish:
        blender=shutil.which('blender')
        if not blender: raise RuntimeError('Blender is required on PATH')
        with (Path(job['output'])/'blender.log').open('w') as log:
            subprocess.run([blender,'--background','--factory-startup','--python',str(PROJECT/'gearbox_native/render_blender.py'),'--',str(path)],stdout=log,stderr=subprocess.STDOUT,check=True)
    decorate(job)
    out=Path(job['output'])
    verification=verify_media(job) if not args.preview else None
    report=dict(status='preview' if args.preview else 'rendered',frames=job['frames'] if not args.preview else 1,
                fps=job['fps'],duration_seconds=15 if not args.preview else 0,part_count=len(job['pieces']),
                source='verified native SolidCraft meshes',mode=args.mode,scad_required=False,
                hardware_count=len(job['hardware']),hardware_geometry=job['hardware_geometry'],
                animation='assembly separation, 20 input turns / 1 output turn while exploded, reassembly',
                verification=verification,
                files={p.name:sha(p) for p in out.glob('solidcraft_exploded*') if p.suffix in ('.png','.mp4','.gif','.blend')})
    (out/'render_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
