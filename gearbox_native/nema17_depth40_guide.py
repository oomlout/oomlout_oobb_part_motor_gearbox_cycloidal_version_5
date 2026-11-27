"""Assembly content and scene inventory for the checked, separate-joiner NEMA17."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
PART_ID=json.loads((ROOT/'solidcraft/simple_double_bearing_version_2_nema17_flange.json').read_text())['part_id']
PART=ROOT/'parts'/PART_ID
BUILD=ROOT/'build/nema17_depth40_guide'
OUT=PART/'assembly_guide'

# The build starts at the native 'upper' face, turned down onto an open support.
# 'Top/bottom' filenames are native CAD names, not the builder's gravity direction.
STEPS=[
 ('discs','Prepare both cycloids',
  'Capture one 6704 bearing between each matching pair of disc halves. Load three M3 nuts into each cap, then join with three M3 x 6 countersunk screws. Seat the heads flush. Disc B will enter the stack first, heads down; Disc A follows, heads up.',
  'Do not mix A and B halves. Keep their indexed clamp screw facing the wide guide gap during stacking.'),
 ('start','Stand the first layer and screws',
  'Place output_cap_cylinder, carrier_top_cap and yellow shaft_end_upper (E) flanges down. Insert twenty M3 x 30 ring screws, only the three M3 x 35 guide screws, and both M3 x 35 shaft ties from beneath. One shaft tie temporarily occupies E\'s vacant hex pocket.',
  'Use an open support with at least 50 mm access underneath. Leave the three M3 x 40 guides out.'),
 ('bearings_start','Seat the first bearing pair',
  'Lower the first 6810 over the large black inner journal and the first centred 6704 over yellow E. Seat both against their shoulders. Keep these two bearing layers together; neither inner journal is fitted later through a closed bearing.',
  'Both bearings should sit square before the next layer.'),
 ('inner_start','Close the starting inner layer',
  'Load eight M3 nuts into carrier_top and four into shaft_mount_upper (N). Retain them while lowering the pieces with their pockets down. Add the front circular plate, output_circle_plate. The standing screws keep the layers aligned.',
  'The four front-cover screws will use carrier nuts installed here. They cannot be added after this split closes.'),
 ('sleeves','Fit the contact and guide sleeves',
  'Fit twenty yellow outer contact sleeves and all six yellow inner guide sleeves, OD 7 x 16 mm. Three inner sleeves have screws through them; locate the other three in their carrier sockets and keep the build upright. Their long screws are fitted after the motor adapter.',
  'Use either the twenty loose outer contacts or one connected contact ring, never both. Keep six separate inner sleeves.'),
 ('disc_b','Fit cam B and Disc B',
  'Lower shaft_cam_b_outer with its narrow bearing journal up. Lower the closed Disc B over the sleeves and standing screws, screw heads down. Align its indexed clamp screw toward the wide guide gap and seat the bearing on the cam journal.',
  'Rotate gently to find alignment. Do not enlarge the disc tracks or force a misclocked disc over the sleeves.'),
 ('cams','Close B and start the opposite cam',
  'Fit shaft_cam_b_inner with its journal down into B\'s bearing. Then fit shaft_cam_a_inner with its journal up. Keep the two shaft tie holes aligned and place A\'s eccentric offset 180 degrees opposite B.',
  'The opposed offsets are essential. These are the two centre cam halves, not the outer end halves.'),
 ('disc_a','Fit Disc A and close its cam',
  'Lower the closed Disc A with its countersunk heads up. Its indexed clamp screw faces the same wide guide gap used for B. Seat the bearing on A\'s lower cam half, then fit shaft_cam_a_outer with its journal down.',
  'Keep the bearing seated and the six guide sleeves inside their matching tracks.'),
 ('inner_finish','Close the motor-side inner layer',
  'Load eight M3 nuts into carrier_bottom and four into the modified shaft_mount_lower (N). Lower these with their pockets up, together with output_circle_rear_plate. Seat all six guide sleeve ends in the carrier sockets.',
  'Use the N piece with the 16 mm coupler bolt circle. Its four nuts must be installed before the next bearing and E cap.'),
 ('bearings_finish','Seat the finishing bearing pair',
  'Lower the second 6810 onto its carrier shoulder and circular-plate layer. Lower the remaining centred 6704 onto the motor-side N journal. Check that both bearings are fully seated and their inner and outer supports are aligned.',
  'This completes two 6810 and four 6704 bearings in the gearbox, including the two disc bearings.'),
 ('caps','Fit the finishing caps',
  'Lower output_nut_cylinder, carrier_bottom_cap and the modified yellow shaft_end_lower (E), flanges up. The E piece has four coupler holes on a 16 mm bolt circle. Match its round socket to the temporary tie and its hex pocket to the retained tie.',
  'The 6810 sits entirely in its cylinder. Both bearing rims are captured by the adjoining parts.'),
 ('reverse','Reverse the temporary shaft tie',
  'Start the twenty ring nuts and the three short-guide nuts. Secure the correctly directed shaft tie. Withdraw the temporary tie downward through the starting face; place an M3 nut in the vacated hex pocket, then reverse that same screw and insert it from the motor side.',
  'Finish with two opposed M3 x 35 shaft ties. Snug ties, three guides and ring screws evenly; check free input motion before adding the coupler.'),
 ('coupler','Attach the flange coupler',
  'Place the 5 mm shaft coupler\'s wide flange against the modified yellow E face, barrel toward the motor. Fit four M3 x 14 socket caps, each with a 0.5 mm M3 washer, into the four captive nuts in N. Tighten while this face is still open.',
  'Finish both shaft ties first: the coupler covers their tool access. Coupler flange: OD 22 mm, 16 mm screw PCD, 12 mm overall height.'),
 ('motor','Bolt the motor to its adapter',
  'On the bench, fasten the 40 mm-body NEMA17 to motor_inner_adapter using four M3 x 8 socket caps. This build uses a 5 mm shaft with 24 mm projection and a 31 mm mounting square. Tighten all four screws before offering it to the gearbox.',
  'The gearbox blocks these screw access bores after installation. The render shows the adapter separated to reveal them.'),
 ('tube','Fit the motor tube on the bench',
  'Load three M3 cage-joining nuts near the tube\'s gearbox end and three rear-cover nuts near its rear end. Slide the tube over the motor from behind, feeding the cable through the peaked opening. Join it to the adapter with three M3 x 16 socket caps, tightened from the open gearbox-facing side.',
  'Do this before mounting the motor assembly. The tube screws are fully accessible here. Check the cable connector can pass before seating the tube.'),
 ('mount','Seat the motor and secure the long guides',
  'Slide the complete motor, adapter and tube onto the coupler. Seat the adapter. Slide its three M3 guide nuts into their radial slots BEFORE inserting the three M3 x 40 guide screws from the front/starting side. Tighten evenly. Align a coupler grub with an adapter window and tighten; rotate the input to reach the other grub.',
  'The tube ends below the grub windows, so both remain reachable. Tighten both supplied grubs before covers and teal joiners.'),
 ('front_cover','Close the fixed front cover',
  'Fit front_cover_spacer over the front shaft end. Load the chosen captive nuts into front_cover_nuts: up to 15 M6 and 16 M3. Close with front_cover_face and four M3 x 25 countersunk screws into the carrier nuts loaded at step 4.',
  'The shaft ties must already be adjusted. Load mounting nuts before closing the split; keep them out of the shaft clearance.'),
 ('rear_cover','Route the cable and close the rear cover',
  'Load rear_cover_nuts with the chosen mounting nuts: up to 19 M6 and 15 M3. Route the motor cable through the fixed tube opening and rear-cover passage, clear of the rotating output. Close with rear_cover_face and three M3 x 16 countersunk screws into the tube\'s preloaded nuts.',
  'Both black covers stay fixed. The rear black face projects 1.5 mm beyond the teal rear ring.'),
 ('joiner_nuts','Prepare three identical joiners',
  'Slide four M3 nuts into each teal rear_output_joiner: two near each end, twelve nuts total. Align all hex flats with their slots. The two screw axes are 15 mm apart; each joiner is 78.5 mm tall in the 40 mm-motor build.',
  'All three pieces are identical. Orient their side-loading slots outward when fitted at the three 120-degree stations.'),
 ('joiners','Attach the joiners to the gearbox',
  'Bring the three joiners in from the motor/rear side until their ends meet the motor-side circular plate. Pass six M3 x 10 countersunk screws through the access holes in the front plate. Their heads seat in the MOTOR-SIDE plate and engage the joiners\' upper nuts.',
  'Use a straight 2 mm hex key through the six 6.4 mm access holes. The front plate is a tool passage, not the screw seat.'),
 ('rear_ring','Attach the separate rear output ring',
  'Bring rear_output_ring (native name rear_output_extension) onto the free ends of the three joiners from behind the motor. Align its six attachment holes. Fit six M3 x 10 countersunk screws from the rear face into the lower joiner nuts.',
  'The flat 3 mm ring and joiners rotate with the gearbox\'s teal casing. They do not fasten to either black cover.'),
 ('braces','Fit the two extra plate braces',
  'Slide the two yellow rear_output_spacer sleeves radially between the circular plates at the offset brace holes. Load an M3 nut beneath each motor-side hole, then insert an M3 x 25 countersunk screw from the front through each sleeve.',
  'These OD 7 x 16 mm braces have their own screws. They do not replace or share the twelve joiner screws.'),
 ('finished','Mount and check the complete gearbox',
  'Attach the stationary frame to the black covers; attach the load to the teal output plates or rear ring. Select external fasteners so they project no more than 2 mm inside either black cover. Keep the cable inside the fixed assembly and clear of all rotating teal parts.',
  'Start slowly with no load and the motor driver set for the motor. Stop and reseat any layer that binds. The fixed-carrier arrangement gives 20:1 output reduction.'),
]


def scenes(names):
    names=set(names)
    def pick(*prefix):return {n:[0,0,0] for n in names if n.startswith(prefix)}
    def lifted(group,z):return {n:[0,0,z] for n in group}
    result=[]
    def add(key,parts,flip=True,look=(180,-250,210)):
        result.append(dict(key=key,parts=parts.copy(),flip=flip,look=look))
    def disc(s):return pick('rotor_'+s,'hardware_disc_'+s,'hardware_6704_disc_'+s)
    bench={}
    for side,dx in [('a',-38),('b',38)]:
        for n in disc(side):
            # Local station offset puts both complete clamshells on one bench.
            z=0 if side=='b' else 8.5
            z+=-14 if n=='rotor_'+side or 'M3x6' in n else 20 if n=='rotor_'+side+'_cap' or '_nut_' in n else 4
            bench[n]=[dx,0,z]
    add('discs',bench,False)
    first={n:[0,0,0] for n in ('output_cap_cylinder','carrier_top_cap','shaft_end_upper','hardware_shaft_M3x35_upper','temporary_shaft_tie')}
    first.update(pick('hardware_ring_M3_shanks','hardware_ring_cap_heads','hardware_guide_M3x35'))
    add('start',first)
    bearing=pick('hardware_6810_top','hardware_6704_top')
    add('bearings_start',first|lifted(bearing,-20));first.update(bearing)
    closing=pick('carrier_top','hardware_carrier_top_mount_nut','shaft_mount_upper','hardware_shaft_mount_nut_upper')
    closing.pop('carrier_top_cap');closing['circular_top']=[0,0,0]
    add('inner_start',first|lifted(closing,-22));first.update(closing)
    sleeves=pick('printed_drive_sleeve','printed_contact_sleeve')
    add('sleeves',first|lifted(sleeves,-22));first.update(sleeves)
    add('disc_b',first|{'shaft_cam_b_outer':[0,0,-14]}|lifted(disc('b'),-36),look=(200,-100,280))
    first['shaft_cam_b_outer']=[0,0,0];first.update(disc('b'))
    add('cams',first|{'shaft_cam_b_inner':[0,0,-15],'shaft_cam_a_inner':[0,0,-33]},look=(200,-100,280))
    first.update({n:[0,0,0] for n in ('shaft_cam_b_inner','shaft_cam_a_inner')})
    add('disc_a',first|lifted(disc('a'),-28)|{'shaft_cam_a_outer':[0,0,-45]},look=(200,-100,280))
    first.update(disc('a'));first['shaft_cam_a_outer']=[0,0,0]
    closing=pick('carrier_bottom','hardware_carrier_bottom_mount_nut','shaft_mount_lower','hardware_shaft_mount_nut_lower')
    closing.pop('carrier_bottom_cap');closing['circular_bottom']=[0,0,0]
    add('inner_finish',first|lifted(closing,-24));first.update(closing)
    bearing=pick('hardware_6810_bottom','hardware_6704_base')
    add('bearings_finish',first|lifted(bearing,-20));first.update(bearing)
    caps=pick('output_nut_cylinder','carrier_bottom_cap','shaft_end_lower')
    add('caps',first|lifted(caps,-22));first.update(caps)
    first.update(pick('hardware_M3_ring_nuts','hardware_guide_nut_2','hardware_guide_nut_4','hardware_guide_nut_6','hardware_shaft_tie_nut_lower'))
    add('reverse',first|{'temporary_shaft_tie':[0,0,45],'hardware_shaft_M3x35_lower':[0,0,-45],'hardware_shaft_tie_nut_upper':[0,0,10]},look=(170,-270,130))
    first.pop('temporary_shaft_tie');first.update(pick('hardware_shaft_M3x35_lower','hardware_shaft_tie_nut_upper'))
    coupler=pick('hardware_coupler_','hardware_flange_')
    # Show the open coupling face at useful scale, with the rest of the core omitted.
    add('coupler',pick('shaft_end_lower','shaft_mount_lower','hardware_shaft_mount_nut_lower')|lifted(coupler,-25))
    first.update(coupler)
    motor=pick('motor_inner_adapter','hardware_NEMA17_')
    add('motor',motor|lifted(pick('motor_inner_adapter','hardware_NEMA17_M3x8'),22),False)
    cage=pick('motor_cage','hardware_cage_','hardware_endcap_rear_join_nut_')
    add('tube',motor|lifted(cage,-45),False,look=(180,-250,180))
    late=pick('hardware_guide_M3x40','hardware_guide_nut_1','hardware_guide_nut_3','hardware_guide_nut_5')
    add('mount',first|lifted(motor|cage,-35)|{n:[0,0,35 if 'M3x40' in n else -35] for n in late})
    first.update(motor);first.update(cage);first.update(late)
    front=pick('front_cover_','hardware_endcap_front_')
    detail={n:[0,0,40 if n=='front_cover_face' or 'front_join_screw' in n else 18 if n!='front_cover_spacer' else 0] for n in front}
    add('front_cover',detail|pick('carrier_top_cap','shaft_end_upper'),False)
    first.update(front)
    rear=pick('rear_cover_','hardware_endcap_rear_join_M3x16')
    rear.update(pick('hardware_endcap_rear_m'))
    add('rear_cover',pick('motor_cage','hardware_endcap_rear_join_nut_')|{n:[0,0,-38 if n=='rear_cover_face' or 'M3x16' in n else -17] for n in rear},False,look=(180,-240,-170))
    first.update(rear)
    joiners=pick('rear_output_joiner_','hardware_endcap_outer_extension_nut_','hardware_endcap_outer_ring_nut_')
    detail={'rear_output_joiner_1':[0,0,0]}
    for n in joiners:
        if n.startswith('hardware_') and n.rsplit('_',1)[1] in ('0','1'):detail[n]=[0,18,0]
    add('joiner_nuts',detail,False,look=(140,230,80))
    top_screws=pick('hardware_endcap_outer_extension_screw_')
    add('joiners',first|lifted(joiners,-38)|lifted(top_screws,40),False)
    first.update(joiners);first.update(top_screws)
    ring=pick('rear_output_extension','hardware_endcap_outer_ring_screw_')
    add('rear_ring',first|lifted(ring,-32),False,look=(180,-240,-170));first.update(ring)
    brace=pick('rear_output_spacer_','hardware_endcap_spacer_')
    shifts={}
    for n in brace:
        if 'spacer_screw_' in n:shifts[n]=[0,0,35]
        elif 'spacer_nut_' in n:shifts[n]=[0,0,-12]
        else:shifts[n]=[-18 if n.endswith('_1') else 18,-20,0]
    add('braces',first|shifts,False);first.update(brace)
    add('finished',first,False)
    # Extra details are intentionally not chronological assembly frames.
    add('starting_ties',pick('shaft_end_upper','hardware_shaft_M3x35_upper')|{'temporary_shaft_tie':[0,0,0]},True,look=(1,-1,-300))
    add('grub_access',pick('motor_inner_adapter','motor_cage','hardware_NEMA17_motor','hardware_flange_','hardware_coupler_','shaft_end_lower'),False,look=(20,-300,10))
    add('tube_access',pick('motor_inner_adapter','motor_cage','hardware_cage_','output_nut_cylinder','circular_bottom'),False,look=(120,-280,-20))
    assert [s['key'] for s in result[:len(STEPS)]]==[s[0] for s in STEPS]
    return result
