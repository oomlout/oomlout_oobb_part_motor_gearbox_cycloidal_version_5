"""Explicit V4 presentation source; never resolves the active V5 recipe."""
import json
from pathlib import Path


def prepare(project, args):
    from gearbox_native.presentation import assembly_parts
    from gearbox_native.presentation_hardware import build_hardware
    from gearbox_native.high_quality_presentation import upgrade,digest
    part=Path(project)/'parts/oobb_part_motor_gearbox_cycloidal_version_4_20_to_1_reduction'
    source=part/'solidcraft_renders'/args.mode/'render_job.json'
    # Saved V4 configuration is independent of active V5 defaults. The user
    # explicitly authorized updating V4's hardware and presentation outputs.
    saved=json.loads(source.read_text())
    c=dict(saved['config']);c.setdefault('hub_bolt_radius_name','m6')
    if c.get('plain_guides'):raise ValueError('Expected the captured-bearing V4 design')
    pieces=assembly_parts(c)
    for item in pieces:
        folder=part/'solidcraft'/args.mode;name=item['name']
        manifest=json.loads((folder/(name+'_manifest.json')).read_text())
        if manifest['construction']!='native' or manifest['status']!='success':raise ValueError(name)
        hashes={f['file']:f['sha256'] for f in manifest['published_files']}
        for ext in ('.stl','.solidcraft'):
            if digest(folder/(name+ext))!=hashes[name+ext]:raise ValueError(f'Changed V4 source: {name+ext}')
        item.update(stl=str(folder/(name+'.stl')),stl_sha256=hashes[name+'.stl'],native_document=str(folder/(name+'.solidcraft')))
    output=part/'solidcraft_renders'/args.mode/'with_high_quality_hardware';output.mkdir(parents=True,exist_ok=True)
    rows=build_hardware(c,output/'accessory_meshes')
    rows=upgrade(rows,c,part/'solidcraft/high_quality_hardware')
    for item in rows:
        for asset in item['assets']:asset['sha256']=digest(asset['stl'])
    job=dict(project=str(project),output=str(output),version='version_4',mode=args.mode,pieces=pieces,config=c,
        spacing=args.spacing,fps=24,frames=360,still_size=2000,video_size=1200,preview_only=args.preview,
        geometry_source='verified V4 native SolidCraft exports',hardware_included=True,hardware=rows,
        hardware_geometry='shared high_quality_hardware native models: helical threads, races, balls and cages; parametric motor, coupler and posts',
        source_configuration=str(source),source_configuration_sha256=digest(source),
        presentation_subtitle='20:1 reduction · High-quality hardware · Modeled threads and rolling elements',
        hardware_caption='HARDWARE / MODELED THREADS & ROLLING ELEMENTS',
        high_quality_hardware_count=sum(i['hardware_quality']=='high_quality_hardware' for i in rows))
    return job,output/'render_job.json'
