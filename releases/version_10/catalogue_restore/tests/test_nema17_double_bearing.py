"""The motor conversion stays separate and publishes actual fit/edit evidence."""
import hashlib
import json
import zipfile
from gearbox_native.nema17_double_bearing import BASE,MASTER,PART_ID,PROJECT
from working_oomp_populate import get_options,build_oomp_id


def test_separate_motor_catalogue_and_unchanged_baseline():
    options=get_options()
    motor=next(o for o in options if o.get('input_variant')=='nema17_flange')
    manual=next(o for o in options if o['style']=='simple_double_bearing_version_2' and 'input_variant' not in o)
    assert build_oomp_id(motor)==PART_ID
    assert build_oomp_id(manual)!=PART_ID and manual['native_master']!=MASTER
    accepted=json.loads((PROJECT/'solidcraft/simple_double_bearing_version_2.json').read_text(encoding='utf8'))
    assert hashlib.sha256(BASE.read_bytes()).hexdigest()==accepted['master_sha256']
    assert motor['native_parameters']['motor_depth']=='40 mm'


def test_motor_native_fit_edit_and_conversion_bed():
    part=PROJECT/'parts'/PART_ID
    fit=json.loads((part/'motor_fit_verification.json').read_text(encoding='utf8'))
    assert fit['status']=='passed' and not fit['clashes']
    assert fit['guide_screw_lengths_mm']==[40,35,40,35,40,35]
    assert fit['maximum_overlap_mm3']<.03
    assert fit['coupler_nut_engagement_mm']==2.5 and fit['coupler_screw_tip_clearance_mm']>.19
    assert len(fit['insertion_paths'])==3 and all(r['clear'] for r in fit['insertion_paths'])
    assert len(fit['radial_nut_loading'])==3 and len(fit['grub_key_access'])==4
    assert fit['circular_plate_diameter_mm']==134
    edit=json.loads((part/'motor_depth_edit_verification.json').read_text(encoding='utf8'))
    assert edit['status']=='passed' and edit['save_reopen'] and edit['rear_flange_shift_mm']==-8
    with zipfile.ZipFile(part/'gearbox_controls.solidcraft') as z:doc=json.loads(z.read('document.json'))
    assert {'motor_depth','motor_shaft_length'}<=set(doc['favorites'])
    parameters={p['name']:p['expr'] for p in doc['params']}
    assert 'motor_depth' in parameters['motor_cage_height']
    assert 'circle_grid_radius' in parameters['circle_plate_radius']
    import trimesh
    pieces=trimesh.load_mesh(part/'motor_conversion/3dpr.stl').split(only_watertight=False)
    assert len(pieces)==18 and all(p.is_volume for p in pieces)
    assert (part/'native_parts/output_circle_plate.stl').is_file()
    assert (part/'native_parts/output_plain_circle_plate.stl').is_file()


def test_fixed_covers_captive_nuts_and_proud_rear_holder():
    part=PROJECT/'parts'/PART_ID
    proof=json.loads((part/'end_cover_verification.json').read_text(encoding='utf8'))
    digest=hashlib.sha256((part/'gearbox_controls.solidcraft').read_bytes()).hexdigest()
    assert proof['source_sha256']==digest and proof['status']=='passed'
    assert not proof['clashes'] and proof['continuous_360_degree_rotation']['clear']
    assert abs(proof['rear_holder_proud_mm']-1.5)<.001
    assert proof['front_shaft_axial_clearance_mm']>3.2
    assert proof['rear_cover_motor_clearance_mm']>5.9
    assert len(proof['side_loaded_clamp_nuts'])==15
    assert len(proof['captured_mounting_nuts'])==65
    assert all(r['clear'] for r in proof['insertion_paths']+proof['radial_sleeve_paths'])
    edit=json.loads((part/'motor_depth_edit_verification.json').read_text(encoding='utf8'))
    assert edit['fixed_cover_motion_checked'] and edit['rear_offset_preserved']
    assert edit['rear_output_rotation_degrees']==18 and edit['stationary_front_cover_unchanged']
    manifests=json.loads((part/'motor_conversion/print_manifest.json').read_text(encoding='utf8'))
    assert [len(b['parts']) for b in manifests]==[11,5,2]
    import trimesh
    for i in (1,2,3):
        mesh=trimesh.load_mesh(part/f'motor_conversion/bed_{i}/3dpr.stl')
        assert mesh.bounds[0,:2].min()>=0 and mesh.bounds[1,:2].max()<240
        assert mesh.is_volume


def test_accessible_countersunk_outer_connections_and_cover_joins():
    part=PROJECT/'parts'/PART_ID
    proof=json.loads((part/'end_cover_verification.json').read_text(encoding='utf8'))
    assert proof['outer_connection_depth_mm']==3
    assert proof['rear_flange_depth_mm']==3
    assert proof['rear_post_diameter_mm']==13
    assert not proof['circular_plate_pair_fit']['clashes']
    heads=proof['flush_joining_heads']
    assert len(heads)==21
    assert sum(h['style']=='countersunk' for h in heads)==21
    assert all(h['face_clearance_mm']>-.001 for h in heads)
    assert all(h['style']=='countersunk' for h in heads)
    assert not proof['asymmetric_plate_pair_fit']['clashes']
    assert proof['bracket_full_rows_y_mm']==[-75,-90]
    assert proof['extension_join_screw_mm']==10 and proof['cage_join_screw_mm']==16
    assert len(proof['extension_driver_access'])==6 and all(r['clear'] for r in proof['extension_driver_access'])
    assert len(proof['brace_nut_loading'])==2 and all(r['clear'] for r in proof['brace_nut_loading'])
    assert len(proof['complete_attachment_rims'])==36
    assert (part/'native_parts/output_circle_rear_plate.stl').is_file()


def test_6810_insert_bridge_material_and_reprint():
    # This proof belongs to the unchanged, preserved preceding revision.
    part=PROJECT/'parts'/PART_ID.replace('_40_mm_motor_depth','')
    proof=json.loads((part/'carrier_overhang_verification.json').read_text(encoding='utf8'))
    assert proof['status']=='passed' and proof['socket_overhang'] and proof['nut_overhang']
    assert proof['source_sha256']==hashlib.sha256((part/'gearbox_controls.solidcraft').read_bytes()).hexdigest()
    assert len(proof['material_checks'])==36 and all(r['passed'] for r in proof['material_checks'])
    assert proof['nut_insert_unchanged'] and proof['maximum_other_body_volume_difference_mm3']<.001
    assert all(r['unsupported_islands']==0 for r in proof['printability'].values())
    assert proof['carrier_extension_edit']['bridge_planes_follow'] and proof['carrier_extension_edit']['save_reopen']
    import trimesh
    mesh=trimesh.load_mesh(part/'bearing_insert_reprint/3dpr.stl')
    assert mesh.is_volume and len(mesh.split())==1


def test_depth_catalogue_and_conversion_only_print():
    from gearbox_native.nema17_print_set import CONVERSION_PARTS
    from gearbox_native.nema17_tube_revision import CHANGED
    variant=get_options([dict(input_variant='nema17_flange',motor_depth=48)])[0]
    assert build_oomp_id(variant).endswith('nema17_flange_48_mm_motor_depth')
    assert variant['native_parameters']['motor_depth']=='48 mm'
    assert variant['native_master']==MASTER
    part=PROJECT/'parts'/PART_ID
    inventory=json.loads((part/'motor_conversion/conversion_inventory.json').read_text())
    assert inventory==CONVERSION_PARTS and len(inventory)==18
    import trimesh
    assert len(trimesh.load_mesh(part/'3dpr.stl').split())==18
    assert len(trimesh.load_mesh(part/'nema3dpr.stl').split())==18
    with zipfile.ZipFile(part/'gearbox_controls.solidcraft') as z:current=json.loads(z.read('document.json'))
    with zipfile.ZipFile(PROJECT/'solidcraft/nema17_flange_before_tube_revision.solidcraft') as z:before=json.loads(z.read('document.json'))
    ids={c['id'] for c in before['components'] if c['name'] in ('carrier_top_cap','carrier_bottom_cap','shaft_end_lower','shaft_mount_lower')}
    assert [f for f in current['features'] if f.get('component') in ids]==[f for f in before['features'] if f.get('component') in ids]
    assert 'coupler_bolt_circle_diameter' in current['favorites']
    proof=json.loads((part/'end_cover_verification.json').read_text())
    assert proof['extension_post_count']==3 and proof['extension_join_count']==6
    assert proof['motor_tube_wall_mm']==3
    # The requested 40 mm assembly guide now supersedes the geometry-only review.
    assert (part/'ASSEMBLY.md').exists()
    guide=json.loads((part/'assembly_guide/verification.json').read_text())
    assert guide['source_sha256']==proof['source_sha256'] and guide['stage_count']==23
    repeated=json.loads((part/'new_support_printability.json').read_text())
    assert repeated['identical_joiners'] and repeated['spacing_degrees']==120
    assert repeated['screws_per_end_per_joiner']==2
    assert all(p['unsupported_islands']==0 for p in repeated['printability'].values())
