use <motor_mount.scad>
use <output_casing.scad>
use <output_cover.scad>
use <pin_rear.scad>
use <pin_front.scad>
use <rotor_a.scad>
use <rotor_b.scad>
use <eccentric_hub.scad>
use <hardware.scad>
ratio = 12;
eccentricity = 1.5;
H = 48.0;
flange_depth = 13.0;
rotor_depth = 7;
rotor_z = [13.5, 27.5];
eccentric_bearing_z = [16.1, 31.9];
shaft_bearing_z = [3.1, 44.9];
output_bearing_z = [4.4, 43.6];
hub_start = 0.3;
clamp_z = 24.0;
housing_positions = [[30.0, 30.0], [-30.0, 30.0], [-30.0, -30.0], [30.0, -30.0]];
motor_positions = [[15.5, 15.5], [-15.5, 15.5], [-15.5, -15.5], [15.5, -15.5]];
guide_positions = [[16.454482671904337, 9.499999999999998], [1.1634144591899855e-15, 19.0], [-16.454482671904337, 9.499999999999998], [-16.454482671904334, -9.500000000000002], [-3.4902433775699565e-15, -19.0], [16.45448267190433, -9.500000000000009]];
motor_face = -45.0;
motor_plate_depth = 4.0;
coupling_z = -31.0;
coupling_depth = 25.0;
coupling_radius = 9.5;
input_axle_start = -16.0;
input_axle_end = 55.5;
washer_depth = 1.5;
retainer_depth = 2.0;
rear_retainer_depth = 4.0;
guide_nut_bottom = -5.5;
nut_depth_m3 = 2.5;
nut_depth_m5 = 4;
// Controls affect pose/visibility only; generated dimensions are in gearbox.json.
$fn=96;
turns=is_undef(input_turns)?0:input_turns;
E=is_undef(explode)?0:explode;
section_view=is_undef(cutaway)?false:cutaway;
collision_view=is_undef(fit_only)?false:fit_only;
input_angle=360*turns;
output_angle=input_angle/ratio;
module disk(side) {
    sign=side==0?1:-1;
    translate([sign*eccentricity*cos(input_angle),sign*eccentricity*sin(input_angle),rotor_z[side]+(side==0?-2:3)*E])
    if(side==0) translate([0,0,rotor_depth]) rotate([180,0,0]) rotor_a();
    else rotor_b();
}
module hub() {translate([-3*E,0,hub_start]) rotate([0,0,input_angle]) eccentric_hub();}
module carrier(side) {
    if(side==0) translate([0,0,flange_depth-5*E]) rotate([180,0,0]) pin_rear();
    else translate([0,0,H-flange_depth+6*E]) pin_front();
}
module casing() {translate([9*E,0,-rear_retainer_depth]) rotate([0,0,output_angle]) output_casing();}
module mount() {translate([0,0,motor_face-10*E]) motor_mount();}
module cap() {translate([0,0,H+retainer_depth+10*E]) rotate([0,0,output_angle]) rotate([180,0,0]) output_cover();}
module bearing(kind,side) {
    if(kind==0) {
        s=side==0?1:-1;
        translate([s*eccentricity*cos(input_angle),s*eccentricity*sin(input_angle),eccentric_bearing_z[side]+(side==0?-3:4)*E]) hardware_bearing_eccentric();
    } else if(kind==1) translate([0,0,shaft_bearing_z[side]+(side==0?-6:7)*E]) hardware_bearing_shaft();
    else translate([0,0,output_bearing_z[side]+(side==0?-4:5)*E]) hardware_bearing_output();
}
module sleeves() {
    for(p=guide_positions)
    translate([p[0],p[1],flange_depth+E]) hardware_sleeve();
}
module guide_fasteners() {
    for(p=guide_positions) {
        translate([p[0],p[1],H+8.5*E]) hardware_screw_guide();
        translate([p[0],p[1],guide_nut_bottom-7.2*E]) hardware_nut_m3();
    }
}
module housing_fasteners() {
    rotate([0,0,output_angle]) for(p=housing_positions) {
        translate([p[0],p[1],H+retainer_depth+11*E]) hardware_screw_housing();
        translate([p[0],p[1],-rear_retainer_depth+.01-8.7*E]) hardware_nut_m3();
    }
}
module motor_fasteners() {
    for(p=motor_positions) translate([p[0],p[1],motor_face+motor_plate_depth-9.5*E]) hardware_screw_motor();
}
module axle() {translate([-3*E,0,input_axle_start]) rotate([0,0,input_angle]) hardware_axle();}
module shaft_fasteners() {
    translate([-3*E,0,0]) rotate([0,0,input_angle]) {
        translate([0,0,-washer_depth-7*E]) hardware_washer_m5();
        translate([0,0,-washer_depth-nut_depth_m5-7.8*E]) hardware_nut_m5();
        translate([0,0,H+8*E]) hardware_washer_m5();
        translate([0,0,H+washer_depth+9*E]) hardware_nut_m5();
        translate([8+1.5*E,0,clamp_z]) rotate([0,90,0]) translate([0,0,-nut_depth_m3]) hardware_nut_m3();
        translate([8.5+3*E,0,clamp_z]) rotate([0,90,0]) hardware_set_screw();
    }
}
module coupling() {translate([0,0,coupling_z-8*E]) rotate([0,0,input_angle]) hardware_coupling();}
module coupling_screws() {
    rotate([0,0,input_angle]) for(z=[coupling_z+5,coupling_z+coupling_depth-5])
    translate([8.5+2*E,0,z-8*E]) rotate([0,90,0]) hardware_set_screw();
}
module motor() {translate([0,0,motor_face-12*E]) hardware_motor();}

// Full, assembled collision checks. Bearings are nominal annuli: intended race
// contacts are tangencies. Thread engagement and the hub clamp are excluded.
module moving(i) {
    if(i==0) disk(0);
    if(i==1) disk(1);
    if(i==2) {hub();shaft_fasteners();}
    if(i==3) {casing();cap();housing_fasteners();}
    if(i==4) {for(k=[0:2],s=[0:1]) bearing(k,s);}
    if(i==5) {axle();coupling();}
}
module fixed() {mount();carrier(0);carrier(1);sleeves();guide_fasteners();motor();motor_fasteners();}
module collision_pair(i,j) {
    // M5 nut-to-axle thread engagement is intentional, so test the hub body
    // against the axle here; other pairs include all shaft clamping hardware.
    intersection() {
        if(i==2 && j==5) hub(); else moving(i);
        if(j<0) fixed(); else moving(j);
    }
}
module collisions() {
    if(!is_undef(fit_pair)) collision_pair(fit_pair[0],fit_pair[1]);
    else {
        for(i=[0:5]) collision_pair(i,-1);
        for(i=[0:4],j=[i+1:5]) collision_pair(i,j);
    }
}
module scene() {
    if(is_undef(show_housing)||show_housing) {
        color("SteelBlue") mount();
        color("Tomato") casing();
    }
    if(is_undef(show_retainers)||show_retainers) color("Tomato") cap();
    if(is_undef(show_carrier)||show_carrier) color("SteelBlue") {carrier(0);carrier(1);}
    color("Ivory") disk(0);
    color("LightSkyBlue") disk(1);
    color("Gold") hub();
    if(is_undef(show_bearings)||show_bearings) color("DimGray") for(k=[0:2],s=[0:1]) bearing(k,s);
    if(is_undef(show_hardware)||show_hardware) {
        color("Silver") {sleeves();axle();shaft_fasteners();coupling();coupling_screws();}
        color("SlateGray") {guide_fasteners();housing_fasteners();motor_fasteners();}
    }
    if(is_undef(show_motor)||show_motor) color("DarkSlateGray") motor();
}
if(!is_undef(installation_shift)) color("Red") intersection() {
    casing();
    translate([0,0,installation_shift]) {
        disk(0);disk(1);hub();carrier(0);carrier(1);sleeves();
        for(k=[0:2],s=[0:1]) bearing(k,s);
    }
} else if(collision_view) color("Red") collisions();
else if(section_view) difference() {scene();translate([0,-200,-200]) cube([200,400,500]);}
else scene();
