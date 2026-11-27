"""Export and publish the additive manual circular-plate revision."""
import argparse,hashlib,json,shutil
from pathlib import Path
import trimesh
from itertools import combinations
from gearbox_native.project import PROJECT,require_editable
from gearbox_native.simple_double_bearing import MASTER,STYLE,PROFILE
from gearbox_native.native_exports import export
from gearbox_native.native_catalogue import publish,sha
from gearbox_native.double_bearing_outputs import print_footprint


def run(build):
    source=build/'complete.solidcraft';views=build/'views'
    motor=json.loads((PROJECT/'solidcraft/simple_double_bearing_version_2_nema17_flange.json').read_text())
    assert sha(PROJECT/motor['master'])==motor['master_sha256']
    if (views/'export.json').exists():
        record=json.loads((views/'export.json').read_text())
        assert record['source_sha256']==sha(source) and record['status']=='native_export_checked'
    else:record=export(source,views,PROFILE)
    assert record['print_mesh']['body_count']==49 and record['print_mesh']['watertight']
    from working_oomp_populate import get_options,build_oomp_id
    option=next(o for o in get_options() if o['style']==STYLE and 'input_variant' not in o)
    part=PROJECT/'parts'/build_oomp_id(option);require_editable(part)
    mesh=trimesh.load_mesh(views/'3dpr.stl');shells=mesh.split(only_watertight=False)
    assert len(shells)==49 and all(s.is_volume and abs(s.bounds[0,2])<.01 for s in shells)
    outlines=[print_footprint(s) for s in shells]
    gap=min(a.distance(b) for a,b in combinations(outlines,2));assert gap>1
    publish(part,source,views,option['native_parameters'],sha(source))
    proof=json.loads((build/'option_verification.json').read_text())
    for filename,diameter in [('after_health.json',134),('reopened_edit_health.json',164)]:
        body=next(b for b in json.loads((build/filename).read_text())['bodies'] if b['name']=='output_circle_plate')
        assert abs(body['bbox']['max'][0]-body['bbox']['min'][0]-diameter)<.001
        assert abs(body['bbox']['max'][2]-body['bbox']['min'][2]-3)<.001
        assert set(body['face_types'])=={'cylinder','plane'},body['face_types']
    fit=json.loads((part/'fit_verification.json').read_text())
    proof.update(source_sha256=sha(source),minimum_print_gap_mm=gap,
        grid_holes=fit['output_housing']['grid_holes']['output_circle_plate'],
        interchangeable_interface_difference_mm3=fit['output_housing']['alternative_interface_difference_mm3'],
        no_countersinks=True,straight_through_sections_mm=[.2,1.5,2.8],measured_native_diameters_mm=[134,164],
        print_mesh_bodies=49,existing_nema_master_unchanged=True,nema_master_sha256=sha(PROJECT/motor['master']))
    (part/'circular_plate_verification.json').write_text(json.dumps(proof,indent=2))
    shutil.copy2(source,PROJECT/MASTER);shutil.copy2(source,part/'gearbox_controls_copy.solidcraft')
    path=PROJECT/'solidcraft'/(STYLE+'.json');index=json.loads(path.read_text())
    index.update(master_sha256=sha(source),print_plate_sha256=sha(part/'3dpr.stl'),
        print_plate_size_mm=mesh.extents.tolist(),minimum_print_gap_mm=gap,
        circular_plate_verification=(part/'circular_plate_verification.json').relative_to(PROJECT).as_posix())
    path.write_text(json.dumps(index,indent=2)+'\n')
    assert sha(PROJECT/motor['master'])==motor['master_sha256']
    print('PUBLISHED CIRCULAR OPTION',json.dumps(proof),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);run(p.parse_args().folder.resolve())
