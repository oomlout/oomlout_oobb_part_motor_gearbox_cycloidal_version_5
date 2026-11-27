"""Promote a verified style build and select it for the normal native exporter."""
import argparse
import json
import shutil
from pathlib import Path
import trimesh
from gearbox_native.project import PROJECT,require_editable
from gearbox_native.native_catalogue import publish,sha
from gearbox_native.simple_double_bearing import MASTER,STYLE,PROFILE,POSITIONS


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def save(path,record):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(record,indent=2)+'\n',encoding='utf8');tmp.replace(path)


def run(build):
    import working_oomp_populate as pop
    source=build/'complete.solidcraft';views=build/'views';record=read(views/'export.json')
    assert record['source_sha256']==sha(source) and record['status']=='native_export_checked'
    config={p['name']:p['value'] for p in record['parameters']['parameters']}
    assert config['housing_race_allowance']==0
    assert config['housing_preview_x']-(1+2**.5)*config['housing_plate_half']>14.99
    assert set(POSITIONS)<=set(record['parts']) and 'connected_contact_ring' in record['parts']
    assert sum(n.startswith('printed_contact_sleeve') for n in record['parts'])==20
    assert sum(n.startswith('printed_drive_sleeve') for n in record['parts'])==6
    assert all(row['native_shape']['valid'] and row['native_shape']['solid_count']==1 and row['mesh']['watertight'] for row in record['parts'].values())
    assert record['print_mesh']['body_count']==49 and record['print_mesh']['watertight']
    assert len(record['hardware_reference_bodies'])==124
    from oobb_solidcraft.validation import inspect_shape
    from gearbox_native.verification import read_step
    for name in ('printed_contact_sleeve','printed_drive_sleeve'):
        sleeve=inspect_shape(read_step(views/'parts'/(name+'.step')))
        radii={round(f['radius_mm'],4) for f in sleeve['cylindrical_faces']}
        assert radii=={1.65,3.5} and abs(sleeve['bounds_mm'][5]-sleeve['bounds_mm'][2]-16)<.001
    edited=read(build/'edit/verification.json')
    assert edited['ratio']==15 and edited['spacer_length_mm']==20 and edited['round_spacers']==15 and edited['reopened'] and edited['minimum_cam_to_tie_web_mm']>=1
    assert sha(PROJECT/'gearbox_native/acceptance.py')==read(PROJECT/'solidcraft/native_v9.json')['acceptance_sha256']
    # Hardware has its own native features. At the assembled position its operations must
    # leave the existing printed bodies intact.
    original=read(build/'health.json')['bodies'];with_hw={b['name']:b for b in read(build/'hardware/hardware_health.json')['bodies']}
    assert all(abs(b['volume_mm3']-with_hw[b['name']]['volume_mm3'])<.001 for b in original)
    import math
    expected=[(20*math.cos(math.radians(a)),20*math.sin(math.radians(a))) for a in (8,82,135,188,262,315)]
    for family in ('printed_drive_sleeve','hardware_drive_shanks','hardware_drive_caps','hardware_drive_nuts'):
        centers=[b['center_of_mass'][:2] for n,b in with_hw.items() if n==family or n.startswith(family+' (')]
        assert len(centers)==6 and all(min(math.dist(xy,c) for c in centers)<.001 for xy in expected),family
    mesh=trimesh.load_mesh(views/'3dpr.stl');shells=mesh.split(only_watertight=False)
    assert len(shells)==49 and all(s.is_volume and abs(s.bounds[0,2])<.01 for s in shells)
    assert min(mesh.bounds[0,:2])>=0  # Individual 240 mm beds are checked during publication.
    from itertools import combinations
    from gearbox_native.double_bearing_outputs import print_footprint
    footprints=[print_footprint(s) for s in shells]
    print_gap=min(a.distance(b) for a,b in combinations(footprints,2))
    assert print_gap>1, f'Print bodies are too close: {print_gap:.2f} mm'
    option=next(o for o in pop.get_options() if o['style']==STYLE)
    part=PROJECT/'parts'/pop.build_oomp_id(option);require_editable(part)
    publish(part,source,views,option['native_parameters'],sha(source))
    proof=read(part/'fit_verification.json')
    assert proof['maximum_overlap_mm3']<.03
    save(part/'offset_edit_verification.json',edited)
    shutil.copyfile(source,PROJECT/MASTER);shutil.copyfile(build/'profile.json',PROFILE)
    shutil.copyfile(source,part/'gearbox_controls_copy.solidcraft')
    index=dict(style=STYLE,version=2,state='native-only',part_id=part.name,master=MASTER,
               master_sha256=sha(source),profile=PROFILE.relative_to(PROJECT).as_posix(),minimum_print_gap_mm=print_gap,
               print_plate_sha256=sha(part/'3dpr.stl'),print_plate_size_mm=mesh.extents.tolist(),
               acceptance_sha256=sha(PROJECT/'gearbox_native/acceptance.py'),
               fit_verification=(part/'fit_verification.json').relative_to(PROJECT).as_posix(),
               eccentricity_edit=(part/'offset_edit_verification.json').relative_to(PROJECT).as_posix())
    index['browser_verification']=(part/'browser_groups_verification.json').relative_to(PROJECT).as_posix()
    index['baseline_release']='releases/simple_double_bearing_version_1/release.json'
    ip=PROJECT/'solidcraft'/(STYLE+'.json');save(ip,index)
    save(PROJECT/'solidcraft/active_design.json',dict(version=STYLE,style=STYLE,part_id=part.name,state='native-only',
         master=MASTER,verification=ip.relative_to(PROJECT).as_posix()))
    print('Published',part,proof,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('build',type=Path)
    run(parser.parse_args().build.resolve())
