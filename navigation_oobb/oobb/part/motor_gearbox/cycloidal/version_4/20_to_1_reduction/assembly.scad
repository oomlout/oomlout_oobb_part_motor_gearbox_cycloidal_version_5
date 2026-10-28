use <motor_mount.scad>
use <pin_rear.scad>
use <output_base.scad>
use <output_casing.scad>
use <output_cover.scad>
use <pin_front.scad>
use <front_bearing_hub.scad>
use <rotor_a_lower.scad>
use <rotor_a_upper.scad>
use <rotor_b_lower.scad>
use <rotor_b_upper.scad>
use <coupling_collar.scad>
use <coupling_drive.scad>
use <eccentric_hub_lower.scad>
use <eccentric_hub_upper.scad>
use <hardware.scad>
reduction=20;
radius_offset=1.85;
lobe_radius=2.1;
lobe_eccentricity_ratio=0.91;
bearing_eccentric="6704";
bearing_shaft="6704";
bearing_output="6810";
bearing_guide="6700";
guide_bolt_radius_name="m6";
guide_spacer_radius=3.425;
guide_spacer_bore=3.1;
guide_head_depth=4.0;
guide_head_clearance=0.2;
rotor_thickness=7;
disc_gap=0.5;
axial_clearance=0.5;
flange_depth=17.0;
flange_web=6.5;
guide_pin_diameter=6;
guide_pin_pitch_radius=21.1;
guide_head_wall=1.0;
guide_pin_count=6;
guide_pin_clearance=0.15;
bearing_seat_clearance=0.1;
bearing_endplay=0.1;
journal_clearance=0.1;
lobe_clearance=0.2;
minimum_wall=2.0;
motor_plate_depth=4.0;
motor_hole_pitch=31;
motor_pilot_diameter=22.0;
motor_pilot_clearance=0.2;
motor_shaft_length=24.0;
motor_body_depth=40.0;
motor_screw_length=6;
shaft_radius_name="m5";
coupling_diameter=22.0;
coupling_barrel_diameter=10.0;
coupling_length=12.0;
coupling_barrel_length=10.0;
coupling_pitch_diameter=16.0;
coupling_flange_hole_diameter=3.0;
coupling_face_clearance=0.2;
motor_pilot_height=2.0;
coupling_grub_from_barrel_top=5.0;
coupling_grub_angles=[45, 135];
coupling_service_angle=0.0;
coupling_screw_length=12.0;
coupling_nut_rotation_offset=180.0;
coupling_nut_hex_rotation=30.0;
coupling_nut_side_clearance=0.1;
drive_roof_depth=2.0;
drive_flange_clearance=0.2;
drive_cavity_clearance=0.3;
rear_bearing_lift=0.3;
casing_bottom_clearance=0.5;
case_nut_plate_clearance=3.0;
grub_access_radius=1.7;
samples_per_lobe=240;
profile_tolerance=0.0005;
front_retainer_depth=2.0;
rotor_central_wall=1.5;
motor_body_width=42.0;
motor_body_clearance=0.4;
guide_thread_allowance=18.0;
architecture="captured_6810";
allow_shared_bearing_pockets=true;
bearing_outer_race_gap_min=0.05;
disc_join_radius=30.0;
disc_join_count=3;
disc_join_phase=60;
disc_join_length=6.0;
disc_join_nut_depth=2.4;
guide_lip_radius=7.0;
eccentric_lip_radius=12.7;
housing_lug_radius=7.0;
case_cover_post_radius=4.8;
case_cover_post_clearance=0.2;
case_cover_post_floor=2.5;
housing_screw_style="socket_cap";
housing_screw_max_length=35.0;
deck_bottom=14.0;
deck_radius=34.0;
deck_bore=13.7;
deck_screw_radius=16.5;
deck_screw_head_z=26.0;
deck_screw_length=25.0;
post_pitch_radius=29.0;
post_radius=3.0;
post_clearance=0.15;
post_screw_length=25.0;
post_nut_bottom=27.0;
drive_flange_radius=13.5;
drive_flange_depth=8.5;
hub_key_radius=4.9;
hub_key_flat=4.3;
hub_key_depth=2.0;
hub_key_clearance=0.15;
hub_bolt_length=35.0;
hub_nut_bottom=24.2;
collar_bottom=16.0;
guide_bolt_length=40.0;
guide_nut_bottom=14.2;
front_hub_screw_length=16.0;
animation_explode=12;
animation_camera_distance=1600;
animation_size=[960, 1600];
print_width=240;
filter="";
save_type="none";
navigation=true;
overwrite=true;
modes=["3dpr"];
oomp_run=false;
oomp_mode="project";
oobb_name="version_4";
reduction_text="20_to_1";
style="version_4";
taxonomy_1="oobb";
taxonomy_2="part";
taxonomy_3="motor_gearbox";
taxonomy_4="cycloidal";
taxonomy_5="version_4";
taxonomy_6="20_to_1_reduction";
type="default_version_4";
output_member="outer_casing";
output_direction="same_as_input";
eccentric_phase_degrees=[0, 180];
coupling_orientation="flange_up_at_motor_shaft_tip";
ring_pin_count=20;
disc_lobes=19;
disc_phase_degrees=[0, -9.473684210526315];
guide_strategy="outer_races_captured_in_split_discs_inner_races_orbit_M6";
guide_hole_radius=7.6;
guide_running_clearance=0.1499999999999999;
guide_positions=[[18.27313601985166, 10.549999999999999], [1.2920023731004577e-15, 21.1], [-18.27313601985166, 10.549999999999999], [-18.273136019851655, -10.550000000000002], [-3.876007119301373e-15, -21.1], [18.273136019851652, -10.55000000000001]];
post_positions=[[29.0, 0.0], [-14.499999999999993, 25.114736709748723], [-14.500000000000012, -25.114736709748716]];
post_hole_radius=5.0;
disc_join_positions=[[15.000000000000004, 25.980762113533157], [-30.0, 3.67394039744206e-15], [15.000000000000004, -25.980762113533157]];
deck_positions=[[16.5, 0.0], [-8.249999999999996, 14.289419162443238], [-8.250000000000007, -14.289419162443235]];
guide_nut_rotations=[30.0, 30.0, 30.0, 30.0, 30.0, 30.0];
pitch_radius=41.0;
ring_positions=[[41.0, 0.0], [38.99331716810129, 12.669696769372843], [33.16969676937285, 24.099195343991397], [24.099195343991397, 33.16969676937285], [12.669696769372845, 38.99331716810129], [2.510525938252074e-15, 41.0], [-12.669696769372841, 38.9933171681013], [-24.099195343991394, 33.16969676937285], [-33.16969676937284, 24.099195343991404], [-38.99331716810129, 12.669696769372848], [-41.0, 5.021051876504148e-15], [-38.9933171681013, -12.66969676937284], [-33.16969676937285, -24.099195343991394], [-24.099195343991404, -33.16969676937284], [-12.66969676937285, -38.99331716810129], [-7.531577814756221e-15, -41.0], [12.669696769372836, -38.9933171681013], [24.09919534399139, -33.16969676937285], [33.16969676937284, -24.099195343991408], [38.99331716810129, -12.669696769372855]];
casing_bore_radius=42.6;
housing_radius=46.1;
housing_width=7;
housing_mount_offset=35.5;
housing_positions=[[35.5, 35.5], [-35.5, 35.5], [-35.5, -35.5], [35.5, -35.5]];
motor_positions=[[15.5, 15.5], [-15.5, 15.5], [-15.5, -15.5], [15.5, -15.5]];
carrier_journal_radius=24.9;
carrier_radius=28.0;
bearing_pass_radius=28.5;
bearing_cup_radius=34.6;
bearing_cup_depth=10.4;
guide_heads_nested=false;
motor_face_z=0.0;
mount_bottom_z=0.0;
motor_plate_top=4.0;
mount_rim_top=4.0;
rear_bearing_bottom=4.3;
rear_bearing_top=11.3;
rear_bearing_shoulder_radius=26.5;
casing_bottom_z=4.5;
rear_retainer_depth=-4.5;
integrated_mount_depth=14.0;
coupling_top=24.0;
coupling_flange_top=24.0;
coupling_z=12.0;
coupling_flange_z=22.0;
coupling_grub_z=17.0;
coupling_hole_positions=[[8.0, 0.0], [4.898587196589413e-16, 8.0], [-8.0, 9.797174393178826e-16], [-1.4695761589768238e-15, -8.0]];
coupling_positions=[[4.898587196589413e-16, 8.0], [-1.4695761589768238e-15, -8.0]];
coupling_nut_rotations=[270.0, 89.99999999999999];
drive_roof_top=20.5;
drive_roof_z=18.0;
drive_start=24.0;
drive_flange_top=32.5;
cap_screw_head_z=29.5;
rotor_a_z=33.0;
rotor_b_z=40.5;
rear_support_top=32.5;
front_support_bottom=48.0;
housing_depth=65.0;
output_bearing_z=[7.800000000000001, 58.1];
shaft_bearing_z=[0, 62.900000000000006];
eccentric_bearing_z=[36.5, 44.0];
guide_bearing_z=[36.5, 44.0];
eccentric_journal_depth=4.2;
eccentric_journal_z=[34.4, 41.9];
eccentric_journal_radius=9.9;
eccentric_shoulder_radius=10.8;
shaft_journal_radius=9.9;
shaft_exit_radius=12.0;
hub_split_z=40.25;
hub_upper_start=40.25;
hub_upper_end=65.2;
hub_bolt_head_z=59.2;
guide_bolt_head_z=50.2;
guide_nut_top=19.2;
guide_spacer_depths=[];
guide_spacer_z=[];
post_depth=15.5;
post_screw_head_z=50.0;
front_hub_bottom=54.5;
front_hub_screw_head_z=64.8;
front_hub_nut_bottom=49.0;
case_nut_bottom=7.0;
housing_screw_length=35.0;
case_screw_head_z=42.0;
case_cover_post_bottom=39.5;
case_cover_depth=27.5;
case_split_z=13.4;
case_base_depth=8.9;
case_ring_depth=51.6;
central_to_guide_race_gap=0.10000000000000142;
gap=65.0;
thickness_outer_rotor=17.0;
disc_half_depth=3.5;
disc_join_head_z=6.7;
disc_join_nut_bottom=0.7000000000000002;
// Dimensions above come from populate -> working_scad. Controls below affect pose only.
$fn=96;
E=is_undef(explode)?0:explode;
turns=is_undef(input_turns)?0:input_turns;
a=360*turns; out=a/reduction;
function orbit(side)=[(side==0?1:-1)*radius_offset*cos(a),(side==0?1:-1)*radius_offset*sin(a),0];
function rz(side)=side==0?rotor_a_z:rotor_b_z;
function de(side,half)=side==0?(half==0?-4:-1):(half==0?2:5);
module mount(){translate([0,0,-11*E]) motor_mount();}
module deck(){translate([0,0,deck_bottom-7*E]) pin_rear();}
module front(){translate([0,0,front_support_bottom+7*E]) pin_front();}
module front_hub(){translate([0,0,front_hub_bottom+9*E]) front_bearing_hub();}
module casing_base(){translate([10*E,0,case_split_z-4*E])rotate([0,0,out])rotate([180,0,0])output_base();}
module casing_ring(){translate([10*E,0,case_split_z])rotate([0,0,out])output_casing();}
module casing(){casing_base();casing_ring();}
module cover(){translate([0,0,housing_depth+front_retainer_depth+12*E]) rotate([0,0,out]) rotate([180,0,0]) output_cover();}
module drive(){translate([-7*E,0,drive_start-5*E])rotate([0,0,a])coupling_drive();}
module lower_hub(){translate([-7*E,0,drive_flange_top-3*E]) rotate([0,0,a]) eccentric_hub_lower();}
module upper_hub(){translate([-7*E,0,hub_split_z+5*E]) rotate([0,0,a]) eccentric_hub_upper();}
module collar(){translate([-7*E,0,collar_bottom-7*E]) rotate([0,0,a]) coupling_collar();}
module disc_half(side,half){
    translate(orbit(side)) translate([0,0,rz(side)+(half==0?0:rotor_thickness)+de(side,half)*E])
    rotate([half==0?0:180,0,0]) {
        if(side==0&&half==0)rotor_a_lower();
        if(side==0&&half==1)rotor_a_upper();
        if(side==1&&half==0)rotor_b_lower();
        if(side==1&&half==1)rotor_b_upper();
    }
}
module disk(side){disc_half(side,0);disc_half(side,1);}
module guide_bearings(side){translate(orbit(side)) for(p=guide_positions) translate([p[0],p[1],guide_bearing_z[side]+(side==0?-2.5:3.5)*E]) hardware_bearing_guide();}
module eccentric_bearing(side){translate(orbit(side)) translate([0,0,eccentric_bearing_z[side]+(side==0?-2.5:3.5)*E]) hardware_bearing_eccentric();}
module shaft_bearing(){translate([0,0,shaft_bearing_z[1]+9.8*E]) hardware_bearing_shaft();}
module output_bearing(side){translate([0,0,output_bearing_z[side]+(side==0?-9:10)*E]) hardware_bearing_output();}
module bearings(){for(i=[0:1]){guide_bearings(i);eccentric_bearing(i);output_bearing(i);}shaft_bearing();}
module guide_bolts(){for(p=guide_positions) translate([p[0],p[1],guide_bolt_head_z+11*E]) hardware_screw_guide();}
module guide_nuts(){for(i=[0:len(guide_positions)-1]) translate([guide_positions[i][0],guide_positions[i][1],guide_nut_bottom-8*E]) rotate([0,0,guide_nut_rotations[i]]) hardware_nut_guide();}
module posts(){for(p=post_positions)translate([p[0],p[1],rear_support_top+6*E]) hardware_post();}
module post_screws(){for(p=post_positions)translate([p[0],p[1],post_screw_head_z+8*E]) hardware_screw_post();}
module post_nuts(){for(p=post_positions)translate([p[0],p[1],post_nut_bottom-8*E]) hardware_nut_m3();}
module deck_screws(){for(p=deck_positions)translate([p[0],p[1],deck_screw_head_z-6*E]) hardware_screw_deck();}
module deck_nuts(){for(p=deck_positions)translate([p[0],p[1],.3-12*E]) hardware_nut_m3();}
module front_hub_screws(){for(p=deck_positions)translate([p[0],p[1],front_hub_screw_head_z+10.5*E]) hardware_screw_front_hub();}
module front_hub_nuts(){for(p=deck_positions)translate([p[0],p[1],front_hub_nut_bottom+6.7*E]) hardware_nut_m3();}
module disc_screws(side){translate(orbit(side))for(p=disc_join_positions)translate([p[0],p[1],rz(side)+disc_join_head_z+(de(side,1)+.7)*E]) hardware_screw_disc();}
module disc_nuts(side){translate(orbit(side))for(p=disc_join_positions)translate([p[0],p[1],rz(side)+disc_join_nut_bottom+(de(side,0)-.7)*E]) hardware_nut_m3();}
module housing_screws(){rotate([0,0,out])for(p=housing_positions)translate([p[0],p[1],case_screw_head_z+15*E])hardware_screw_housing();}
module housing_nuts(){translate([10*E,0,0])rotate([0,0,out])for(p=housing_positions)translate([p[0],p[1],case_nut_bottom-6*E])hardware_nut_m3();}
module motor(){translate([0,0,-13*E])hardware_motor();}
module motor_screws(){for(p=motor_positions)translate([p[0],p[1],motor_plate_depth-10.5*E])hardware_screw_motor();}
module coupling(){translate([0,0,coupling_z-8*E])rotate([0,0,a])hardware_coupling();}
module grub_screws(){rotate([0,0,a])for(ang=coupling_grub_angles)rotate([0,0,ang])translate([coupling_barrel_diameter/2+.55+E,0,coupling_grub_z-8*E])rotate([0,90,0])hardware_set_screw();}
module flange_screws(){translate([-7*E,0,-4.5*E])rotate([0,0,a])for(p=coupling_positions)translate([p[0],p[1],cap_screw_head_z])hardware_screw_flange();}
module flange_nut(i,shift=0){p=coupling_positions[i];ang=coupling_nut_rotations[i];translate([-7*E,0,-7*E])rotate([0,0,a])translate([p[0]-shift*cos(ang),p[1]-shift*sin(ang),drive_roof_z])rotate([0,0,ang+coupling_nut_hex_rotation])hardware_nut_m3();}
module flange_nuts(){for(i=[0:1])flange_nut(i,E);}
module hub_bolt(){translate([-7*E,0,hub_bolt_head_z+7*E])rotate([0,0,a])hardware_screw_hub();}
module hub_nut(){translate([-7*E,0,hub_nut_bottom-6*E])rotate([0,0,a+30])hardware_nut_guide();}
module hardware(){guide_bolts();guide_nuts();posts();post_screws();post_nuts();deck_screws();deck_nuts();front_hub_screws();front_hub_nuts();for(s=[0:1]){disc_screws(s);disc_nuts(s);}housing_screws();housing_nuts();motor_screws();coupling();grub_screws();flange_screws();flange_nuts();hub_bolt();hub_nut();}
// Groups contain different rigid/moving members. All hardware is checked against
// printed geometry. Hardware-to-hardware thread engagements are intentional.
module member(i){
    if(i==0){mount();deck();front();front_hub();}
    if(i==1){casing();cover();}
    if(i==2){drive();lower_hub();upper_hub();collar();}
    if(i==3)disk(0);
    if(i==4)disk(1);
    if(i==5)bearings();
    if(i==6){hardware();motor();}
}
module internal_piece(i){
    if(i==0)intersection(){lower_hub();upper_hub();}
    if(i==1)intersection(){front();front_hub();}
    if(i==2)intersection(){mount();deck();}
    if(i==3||i==4)intersection(){disc_half(i-3,0);disc_half(i-3,1);}
    // Motor screw thread engagement and grub-to-shaft contact are intentional.
    if(i==5)intersection(){motor();union(){guide_bolts();deck_screws();hub_bolt();posts();}}
    if(i==6)intersection(){drive();lower_hub();}
    if(i==7)intersection(){casing_base();casing_ring();}
    if(i==8)intersection(){casing();cover();}
}
module internal(){for(i=[0:8])internal_piece(i);}
module collisions(){
    if(!is_undef(fit_internal))internal_piece(fit_internal);
    else if(!is_undef(fit_pair))intersection(){member(fit_pair[0]);member(fit_pair[1]);}
    else {for(i=[0:5],j=[i+1:6])intersection(){member(i);member(j);}internal();}
}
module scene(){
    color("SteelBlue"){mount();deck();front();front_hub();}
    color("Tomato"){casing();cover();}
    color("Ivory")disk(0);color("LightSkyBlue")disk(1);
    color("Gold"){drive();lower_hub();upper_hub();collar();}
    color("DimGray")bearings();color("Silver")hardware();color("DarkSlateGray")motor();
}
module tools(){for(ang=coupling_grub_angles)rotate([0,0,ang+coupling_service_angle])translate([coupling_barrel_diameter/2+.1,0,coupling_grub_z])rotate([0,90,0])cylinder(r=.9,h=40);}
module service(){mount();collar();output_bearing(0);motor();}
module checks(kind,shift){
    if(kind=="grub")intersection(){tools();service();}
    if(kind=="rear_bearing")intersection(){mount();translate([0,0,shift])output_bearing(0);}
    if(kind=="deck")intersection(){union(){mount();output_bearing(0);casing();coupling();collar();}translate([0,0,shift])deck();}
    if(kind=="casing")intersection(){union(){mount();output_bearing(0);motor();collar();coupling();}translate([0,0,shift])casing();}
    if(kind=="casing_base")intersection(){union(){mount();output_bearing(0);motor();collar();coupling();}translate([0,0,shift])casing_base();}
    if(kind=="casing_ring")intersection(){union(){casing_base();member(0);member(2);member(3);member(4);bearings();guide_bolts();posts();}translate([0,0,shift])casing_ring();}
    if(kind=="lower_disc")intersection(){union(){lower_hub();deck();coupling();}translate([0,0,shift]){disk(0);eccentric_bearing(0);guide_bearings(0);}}
    if(kind=="upper_unit")intersection(){union(){lower_hub();deck();disk(0);}translate([0,0,shift]){upper_hub();disk(1);eccentric_bearing(1);guide_bearings(1);}}
    if(kind=="lower_shaft")intersection(){union(){drive();flange_screws();deck();}translate([0,0,shift])lower_hub();}
    if(kind=="drive")intersection(){union(){coupling();collar();deck();}translate([0,0,shift])drive();}
    if(kind=="upper_disc_bench")intersection(){upper_hub();translate([0,0,-shift]){disk(1);eccentric_bearing(1);guide_bearings(1);}}
    if(kind=="guide_bearing")for(s=[0:1])intersection(){disc_half(s,0);translate([0,0,shift]){guide_bearings(s);eccentric_bearing(s);}}
    if(kind=="disc_upper")for(s=[0:1])intersection(){union(){disc_half(s,0);guide_bearings(s);eccentric_bearing(s);}translate([0,0,shift])disc_half(s,1);}
    if(kind=="guide_bolt")intersection(){union(){mount();deck();front();disk(0);disk(1);guide_bearings(0);guide_bearings(1);posts();}translate([0,0,shift])guide_bolts();}
    if(kind=="front_plate")intersection(){union(){upper_hub();disk(1);posts();}translate([0,0,shift])front();}
    if(kind=="front_hub")intersection(){union(){upper_hub();front();guide_bolts();hub_bolt();}translate([0,0,shift]){front_hub();shaft_bearing();}}
    if(kind=="front_bearing")intersection(){union(){front();front_hub();front_hub_screws();guide_bolts();}translate([0,0,shift])output_bearing(1);}
    if(kind=="cover")intersection(){union(){front();front_hub();output_bearing(1);casing();}translate([0,0,shift])cover();}
    if(kind=="casing_screws")intersection(){union(){cover();casing();}translate([0,0,shift])housing_screws();}
    if(kind=="nuts"){
        intersection(){deck();translate([0,0,-shift]){guide_nuts();post_nuts();}}
        intersection(){mount();translate([0,0,-shift])deck_nuts();}
        intersection(){front();translate([0,0,-shift])front_hub_nuts();}
        intersection(){casing();translate([0,0,-shift])housing_nuts();}
        for(s=[0:1])intersection(){disc_half(s,0);translate([0,0,-shift])disc_nuts(s);}
    }
    if(kind=="hub_nut")intersection(){drive();translate([0,0,-shift])hub_nut();}
    if(kind=="flange_nuts")intersection(){collar();union()for(i=[0:1])hull(){flange_nut(i,0);flange_nut(i,20);}}
    // Positive interference is REQUIRED here: wrong-phase shaft assembly is blocked.
    if(kind=="wrong_phase")intersection(){lower_hub();rotate([0,0,180])upper_hub();}
}
if(!is_undef(check_kind))color("Red")checks(check_kind,is_undef(installation_shift)?0:installation_shift);
else if(!is_undef(fit_only)&&fit_only)color("Red")collisions();
else if(!is_undef(grub_access_view)){
    color("SteelBlue")mount();color("Gold")collar();color("Silver")coupling();color("DimGray")output_bearing(0);color("DarkSlateGray")motor();color("OrangeRed")tools();
}else if(!is_undef(guide_only)){
    color("Ivory")disk(0);color("LightSkyBlue")disk(1);color("DimGray"){guide_bearings(0);guide_bearings(1);}color("Silver"){guide_bolts();posts();}
}else if(!is_undef(flange_nut_loading_view)){
    color("Gold")collar();color("Silver")for(i=[0:1])flange_nut(i,12*(1-$t));
}else if(!is_undef(nut_loading_view)){
    color("SteelBlue")deck();color("Silver")translate([0,0,-8]){guide_nuts();post_nuts();}
}else if(!is_undef(drive_only)){
    difference(){union(){color("Gold"){drive();lower_hub();upper_hub();collar();}color("Silver"){coupling();flange_screws();hub_bolt();}color("SteelBlue"){mount();deck();}}translate([0,-100,-10])cube([100,200,120]);}
}else if(!is_undef(cutaway)&&cutaway)difference(){scene();translate([0,-200,-200])cube([200,400,700]);}
else scene();
