"""The named style survives populate, native parameter edits and hardware-only views."""
import hashlib
import json
import zipfile

from gearbox_native.project import PROJECT
from working_oomp_populate import get_options,build_oomp_id


def test_double_bearing_catalogue_and_checked_print():
    style='simple_double_bearing_version_2'
    index=json.loads((PROJECT/'solidcraft'/(style+'.json')).read_text())
    option=next(o for o in get_options() if o['style']==style)
    assert index['part_id']==build_oomp_id(option)
    part=PROJECT/'parts'/index['part_id']
    for path in (PROJECT/option['native_master'],part/'gearbox_controls.solidcraft'):
        assert hashlib.sha256(path.read_bytes()).hexdigest()==index['master_sha256']
    assert hashlib.sha256((part/'3dpr.stl').read_bytes()).hexdigest()==index['print_plate_sha256']
    export=json.loads((part/'native_export_verification.json').read_text())
    assert len(export['part_names'])==export['print_mesh']['body_count']==49
    assert 'output_circle_plate' in export['part_names']
    assert (part/'3dpr.scad').exists() and (part/'circular_plate/3dpr.stl').exists()
    circular=json.loads((part/'circular_plate_verification.json').read_text())
    assert circular['source_sha256']==index['master_sha256']
    assert circular['grid_holes']=={'m6':12,'m3':72}
    assert circular['no_countersinks'] and circular['interchangeable_interface_difference_mm3']<.01
    assert circular['edit_save_reopen'] and circular['edited_diameter_mm']==164
    assert sum(n.startswith('printed_contact_sleeve') for n in export['part_names'])==20
    assert sum(n.startswith('printed_drive_sleeve') for n in export['part_names'])==6
    assert export['parameters']['eccentricity']==1.5 and export['parameters']['contact_radius']==3.5
    assert export['parameters']['middle_length']==16 and export['parameters']['disc_half']==3.5
    assert export['parameters']['mount_flange_depth']==3
    assert {'rotor_a_cap','rotor_b_cap'}<=set(export['part_names'])
    assert all((part/bed/'3dpr.stl').is_file() for bed in ('disc_plate','gearbox_plate','outer_housing_plate'))
    audit=json.loads((part/'shaft_printability.json').read_text())
    assert len(audit)==8 and all(a['unsupported_islands']==0 for a in audit.values())
    assert not any(n.startswith('hardware_') for n in export['part_names'])
    with zipfile.ZipFile(part/'gearbox_controls.solidcraft') as z:
        names={c['name'] for c in json.loads(z.read('document.json'))['components']}
    assert {'printed_contact_sleeve','printed_drive_sleeve','connected_contact_ring','hardware_6810_bottom','hardware_6704_disc_a'}<=names
    fit=json.loads((PROJECT/index['fit_verification']).read_text())
    assert fit['confirmed_bearing_stops_per_carrier']==2 and fit['carrier_grid_mounts_per_end']==8
    assert (fit['shaft_unique_blanks'],fit['shaft_stack_parts'],fit['shaft_open_bore_mm'])==(3,8,6.5)
    assert fit['shaft_nut_engagement_mm']==2.5 and {'hardware_shaft_M3x35_lower','hardware_shaft_M3x35_upper'}<=names
    assert .26 < fit['shaft_sections']['end_face_minimum_web_mm'] < .29
    assert fit['shaft_sections']['support_to_drive_face_recess_mm']==.8
    assert fit['flat_carrier_split_mm']==export['parameters']['main_inner_face']
    assert len(fit['rotor_clamps'])==6
    assert all(row['head_face_error_mm']<.002 and row['nut_engagement_mm']==1.75
               for row in fit['rotor_clamps'].values())
    assert (part/'bearing_reprint/flat_carrier_update/3dpr.stl').is_file()
    contacts=fit['race_contacts']
    assert len(contacts)==6 and all(len(c)==4 for c in contacts.values())
    assert contacts['6810_lower']['inner_low']=='carrier_bottom_cap'
    assert contacts['6704_upper']['inner_high']=='shaft_end_upper'
    drive=fit['assembled_guide_sweep']
    assert drive['track_paths']==24 and drive['max_axis_error_mm']<.001
    assert drive['track_diameter_mm']==10.30 and drive['located_full_orbit_gap_mm']>=.069
    assert drive['max_disc_twist_to_sleeve_contact_deg']<1.
    assert (part/'bearing_reprint/drive_and_carriers/3dpr.stl').is_file()
    assert (part/'bearing_reprint/six_sleeve_gauge.stl').is_file()
    housing=fit['output_housing']
    assert housing['outer_race_stops_per_end']==2
    assert housing['axial_race_clearance_mm']==0 and housing['alternative_interface_difference_mm3']<.01
    assert housing['grid_holes']['output_cap_plate']=={'m6':12,'m3':28}
    assert housing['grid_holes']['output_lower_row_plate']=={'m6':13,'m3':33}
    assert fit['guide_screw_mm']==35 and export['parameters']['carrier_extension']==3
    assert (part/'eight_mount_reprint/3dpr.stl').is_file()
    assert fit['maximum_hex_pocket_profile_error_mm']<.03
    assert fit['maximum_overlap_mm3']<.03 and fit['motion']['minimum_ring_gap_mm']>.14
    edited=json.loads((PROJECT/index['eccentricity_edit']).read_text())
    assert edited['reopened'] and edited['ratio']==edited['round_spacers']==15
    assert edited['housing_grid_size']==9 and edited['housing_plate_width_mm']==134
    assert edited['eccentricity_mm']==2 and edited['minimum_cam_to_tie_web_mm']>=1
    assert edited['mesh_watertight'] and edited['motion']['input_positions']==360

def test_double_bearing_release_and_successor():
    from pathlib import Path
    import pytest
    from gearbox_native.project import active_part, require_editable
    old = 'simple_double_bearing_version_1'
    release = PROJECT/'releases'/old
    record = json.loads((release/'release.json').read_text())
    with (release/record['archive']).open('rb') as stream:
        assert hashlib.file_digest(stream,'sha256').hexdigest() == record['archive_sha256']
    for folder in ('parts','parts_source'):
        with pytest.raises(ValueError, match='Sealed'):
            require_editable(PROJECT/folder/record['primary_part_id'])
    with pytest.raises(ValueError, match='sealed'):
        get_options([dict(style=old)])
    current = active_part()
    assert record['next_editable_version'] in current.name
    require_editable(current)
    assert (current/'exploded_labeled.png').read_bytes().startswith(b'\x89PNG')

def test_v2_groups_follow_component_placements_in_every_view():
    from gearbox_native.double_bearing_groups import component_group
    from gearbox_native.project import active_part
    part = active_part()
    for name in ('gearbox_controls', 'true', 'exploded', '3dpr'):
        with zipfile.ZipFile(part / (name + '.solidcraft')) as archive:
            doc = json.loads(archive.read('document.json'))
        components = {c['id']: c for c in doc['components']}
        parents = {c['id']: c['parent'] for c in components.values()}
        parent_ids = set(parents.values())
        for placement in doc['occurrences']:
            cid = placement['component']
            assert placement['parent'] == parents[cid]
            component = components[cid]['name']
            if cid not in parent_ids:
                assert components[parents[cid]]['name'] == component_group(component)
            elif component in ('Fasteners', 'Bearings'):
                assert components[parents[cid]]['name'] == 'Hardware'
            else:
                assert parents[cid] == 0
