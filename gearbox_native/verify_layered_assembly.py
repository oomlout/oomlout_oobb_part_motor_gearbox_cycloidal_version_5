"""Verify assembly from the socket-cap end, using installed screws as guide rods."""
import json

from gearbox_native.exact_geometry import _move
from gearbox_native.verification import read_step
from gearbox_native.verify_assembly_sequence import Audit, PART, bounds


def run():
    audit=Audit()
    family=audit.family
    final_names=set(audit.shapes)
    values=json.loads((PART/'native_export_verification.json').read_text())['parameters']
    source_underside=values['shaft_face_z']+values['shaft_head_depth']
    temporary_underside=values['stack_height']-values['shaft_face_z']-values['shaft_nut_depth']
    installed=[]

    # Reverse the lower tie, retaining its original XY axis, to stand it beside
    # the upper tie in the upper E's vacant hex pocket during upside-down assembly.
    # Native lower tie is +Z from head underside 1.1; the temporary tie is -Z
    # from head underside 33.2. Rotation about X reflects Y as well.
    temp=_move(audit.shapes['hardware_shaft_M3x35_lower'],'rotate',[180,0,0])
    temp=_move(temp,'translate',[0,-2*values['shaft_tie_pitch'],temporary_underside+source_underside])
    audit.shapes['temporary_reversed_shaft_tie']=temp
    audit.boxes['temporary_reversed_shaft_tie']=bounds(temp)

    def add(title,moving,dz=-60):
        installed.extend(audit.path(title,moving,installed,dz))

    # First concentric layer. The small and large inner journals are installed together.
    add('01 First layer: outside cylinder, 6810 inner journal and 6704 E',
        ['output_cap_cylinder','carrier_top_cap','shaft_end_upper'])
    add('02 Twenty ring screws from beneath',family('hardware_ring_M3_shanks','hardware_ring_cap_heads'),60)
    add('03 Six guide screws from beneath',family('hardware_drive_shanks','hardware_drive_caps'),60)
    add('04 Both shaft screws from beneath',['hardware_shaft_M3x35_upper','temporary_reversed_shaft_tie'],60)
    add('05 Bearing layer: 6810 and centred 6704',['hardware_6810_top','hardware_6704_top'])

    core=['carrier_top']
    core.extend(audit.path('Bench first carrier core nuts',family('hardware_carrier_top_mount_nut'),core,60))
    nutcarrier=['shaft_mount_upper']
    nutcarrier.extend(audit.path('Bench first N nuts',family('hardware_shaft_mount_nut_upper'),nutcarrier,60))
    add('06 Closing layer: OOBB plate, carrier core and N',['output_cap_plate']+core+nutcarrier)
    add('07 Sleeve layer: inner guides and twenty outer contacts',family('printed_drive_sleeve','printed_contact_sleeve'))
    add('08 First C for B',['shaft_cam_b_outer'])

    def rotor(side):
        direction=60 if side=='a' else -60
        screw_half='rotor_'+side
        nut_half=screw_half+'_cap'
        group=[screw_half]
        group.extend(audit.path('Bench rotor bearing '+side,['hardware_6704_disc_'+side],group,direction))
        nuts=family('hardware_disc_'+side+'_nut')
        audit.path('Bench rotor nuts '+side,nuts,[nut_half],direction)
        group.extend(audit.path('Bench rotor nut half '+side,[nut_half]+nuts,group,direction))
        group.extend(audit.path('Bench rotor screws '+side,family('hardware_disc_'+side+'_M3x6'),group,-direction))
        return group

    add('09 First disc B over standing screws and sleeves',rotor('b'))
    add('10 Close B and start opposite cam A',['shaft_cam_b_inner','shaft_cam_a_inner'])
    add('11 Second disc A over standing screws and sleeves',rotor('a'))
    add('12 Close A',['shaft_cam_a_outer'])

    core=['carrier_bottom']
    core.extend(audit.path('Bench closing carrier core nuts',family('hardware_carrier_bottom_mount_nut'),core,-60))
    nutcarrier=['shaft_mount_lower']
    nutcarrier.extend(audit.path('Bench closing N nuts',family('hardware_shaft_mount_nut_lower'),nutcarrier,-60))
    add('13 Closing layer: flat plate, carrier core and N',['output_nut_plate']+core+nutcarrier)

    add('14a Finishing bearing layer: centred 6704 and 6810',
        ['hardware_6704_base','hardware_6810_bottom'])
    add('14b Finishing cap layer: cylinder, 6810 journal and E',
        ['carrier_bottom_cap','shaft_end_lower','output_nut_cylinder'])

    add('15 Secure the correctly directed shaft screw',['hardware_shaft_tie_nut_lower'],-60)
    add('16 Guide and ring nuts at the finishing face',family('hardware_drive_nuts','hardware_M3_ring_nuts'),-60)
    audit.path('17 Withdraw temporary tie through the starting face',
               ['temporary_reversed_shaft_tie'],installed,60)
    installed.remove('temporary_reversed_shaft_tie')
    add('18 Load the vacated starting-face shaft nut',['hardware_shaft_tie_nut_upper'],60)
    add('19 Reverse the withdrawn screw and insert from the finishing face',
        ['hardware_shaft_M3x35_lower'],-60)
    assert set(installed)==final_names and len(installed)==len(final_names)==170

    # Explicitly verify the upper 6704 and outer 6810 innards shared the first layer.
    assert set(audit.records[0]['moving'])=={'output_cap_cylinder','carrier_top_cap','shaft_end_upper'}
    result=dict(
        master_sha256=json.loads((PART/'native_export_verification.json').read_text())['source_sha256'],
        method='Continuous axial boundary-face sweeps of native STEP solids',
        build_direction='From original upper socket-cap face towards original lower nut face',
        native_approach_mm=-60,
        temporary_shaft_tie=dict(name='temporary_reversed_shaft_tie',bbox=audit.boxes['temporary_reversed_shaft_tie'].tolist(),
                                head_underside_native_z_mm=temporary_underside,
                                withdraw_direction='Starting face, underneath the build',
                                reinstall_direction='Finishing face, above the build'),
        maximum_allowed_overlap_mm3=.03,boolean_checks=audit.boolean_checks,
        bodies_installed=len(installed),steps=list(audit.records),
        note='Nominal CAD solids and smooth thread envelopes. Printed fit, support of loose layers, and driver handles require a bench check.')
    # Reuse the source-matched tool audit for the completed assembly.
    sleeve_state=next(r for r in result['steps'] if r['step'].startswith('07 Sleeve'))
    connected=_move(read_step(PART/'native_parts/connected_contact_ring.step'),
                    'translate',[0,0,values['middle_start']])
    audit.shapes['connected_contact_ring']=connected
    audit.boxes['connected_contact_ring']=bounds(connected)
    audit.path('Alternative connected ring onto standing screws',
               ['connected_contact_ring'],sleeve_state['installed']+family('printed_drive_sleeve'),-60)
    result['optional_connected_ring']=audit.records[-1]
    previous=json.loads((PART/'assembly_sequence_verification.json').read_text())
    assert previous['master_sha256']==result['master_sha256']
    result['tool_access']=previous['tool_access']
    result['tool_scope']=previous['tool_scope']
    result['tool_access_source']='Existing verified final assembly, identical native master hash'
    (PART/'layered_assembly_verification.json').write_text(json.dumps(result,indent=2),encoding='utf8')


if __name__=='__main__':
    run()
