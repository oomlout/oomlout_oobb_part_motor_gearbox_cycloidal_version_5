use <motor_mount.scad>
use <output_casing.scad>
use <output_cover.scad>
use <pin_rear.scad>
use <pin_front.scad>
use <rotor_a.scad>
use <rotor_b.scad>
use <eccentric_hub_lower.scad>
use <eccentric_hub_upper.scad>
use <hardware.scad>
drive_start = -13.8;
drive_bearing_z = -12.0;
hub_upper_start = 17.8;
hub_upper_end = 46.2;
hub_nut_bottom = 17.9;
hub_bolt_head_z = 47.7;
coupling_positions = [[5.656854249492381, 5.656854249492381], [-5.6568542494923815, -5.65685424949238]];
coupling_nut_rotations = [225.0, 44.99999999999997];
coupling_nut_hex_rotation = 30.0;
coupling_flange_z = -2.0;
drive_roof_top = 6.0;
coupling_grub_z = 5.0;
coupling_grub_angles = [0, 90];
coupling_service_angle = 0.0;
coupling_barrel_radius = 5.0;
ratio = 20;
eccentricity = 1.75;
H = 46.0;
flange_depth = 10.0;
rotor_depth = 7;
rotor_z = [10.5, 28.5];
eccentric_bearing_z = [15.4, 33.4];
shaft_bearing_z = [3.1, 42.9];
output_bearing_z = [4.4, 41.6];
housing_positions = [[31.0, 31.0], [-31.0, 31.0], [-31.0, -31.0], [31.0, -31.0]];
motor_positions = [[15.5, 15.5], [-15.5, 15.5], [-15.5, -15.5], [15.5, -15.5]];
guide_positions = [[17.753520777580995, 10.249999999999998], [1.255262969126037e-15, 20.5], [-17.753520777580995, 10.249999999999998], [-17.75352077758099, -10.250000000000002], [-3.7657889073781105e-15, -20.5], [17.753520777580988, -10.250000000000009]];
motor_face = -14.0;
motor_plate_depth = 4.0;
coupling_z = -2.0;
coupling_depth = 12.0;
coupling_radius = 11.0;
washer_depth = 1.5;
retainer_depth = 2.0;
rear_retainer_depth = 4.0;
guide_nut_bottom = -4.0;
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
    if(side==0) rotor_a();
    else rotor_b();
}
module lower_hub() {translate([-3*E,0,drive_start-3.5*E]) rotate([0,0,input_angle]) eccentric_hub_lower();}
module upper_hub() {translate([-3*E,0,hub_upper_end+4.5*E]) rotate([0,0,input_angle]) rotate([180,0,0]) eccentric_hub_upper();}
module hub() {lower_hub();upper_hub();}
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
    } else if(kind==1) {
        if(side==1) translate([0,0,shaft_bearing_z[1]+7*E]) hardware_bearing_shaft();
        else translate([0,0,drive_bearing_z-9*E]) hardware_bearing_drive();
    }
    else translate([0,0,output_bearing_z[side]+(side==0?-4:5)*E]) hardware_bearing_output();
}
module sleeves() {
    for(p=guide_positions)
    translate([p[0],p[1],flange_depth+E]) hardware_sleeve();
}
module guide_fasteners() {
    for(p=guide_positions) {
        translate([p[0],p[1],H+8.5*E]) hardware_screw_guide();
        translate([p[0],p[1],guide_nut_bottom-11.5*E]) hardware_nut_m3();
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
module shaft_fasteners() {
    translate([-3*E,0,0]) rotate([0,0,input_angle]) {
        translate([0,0,hub_upper_end+8*E]) hardware_washer_m5();
        translate([0,0,hub_nut_bottom+E]) hardware_nut_m5();
        translate([0,0,hub_bolt_head_z+12*E]) hardware_screw_hub();
    }
}
module flange_nut(i, shift=0) {
    p=coupling_positions[i];
    a=coupling_nut_rotations[i];
    translate([-3*E,0,-3.5*E]) rotate([0,0,input_angle])
    translate([p[0]-shift*cos(a),p[1]-shift*sin(a),drive_roof_top-nut_depth_m3])
    rotate([0,0,a+coupling_nut_hex_rotation]) hardware_nut_m3();
}
module flange_fasteners() {
    rotate([0,0,input_angle]) for(p=coupling_positions) {
        translate([p[0],p[1],coupling_flange_z-7*E]) rotate([180,0,0]) hardware_screw_flange();
    }
    for(i=[0:len(coupling_positions)-1]) flange_nut(i,1.5*E);
}
module coupling() {translate([0,0,coupling_z-8*E]) rotate([0,0,input_angle]) hardware_coupling();}
module coupling_screws() {
    rotate([0,0,input_angle]) for(a=coupling_grub_angles)
    rotate([0,0,a]) translate([coupling_barrel_radius+0.55+2*E,0,coupling_grub_z-8*E]) rotate([0,90,0]) hardware_set_screw();
}
module motor() {translate([0,0,motor_face-12*E]) hardware_motor();}

// Full, assembled collision checks. Bearings are nominal annuli: intended race
// contacts are tangencies. Thread engagement within hardware is intentional;
// all hardware is checked against the printed bodies.
module moving(i) {
    if(i==0) disk(0);
    if(i==1) disk(1);
    if(i==2) {hub();shaft_fasteners();}
    if(i==3) {casing();cap();housing_fasteners();}
    if(i==4) {for(k=[0:2],s=[0:1]) bearing(k,s);}
    if(i==5) {coupling();flange_fasteners();coupling_screws();}
}
module fixed() {mount();carrier(0);carrier(1);sleeves();guide_fasteners();motor();motor_fasteners();}
module collision_pair(i,j) {
    // All separate moving groups include their fasteners; thread engagement
    // inside a group is checked separately against the printed bodies.
    intersection() {
        moving(i);
        if(j<0) fixed(); else moving(j);
    }
}
module internal_collisions() {
    intersection() {lower_hub();upper_hub();}
    intersection() {hub();shaft_fasteners();}
    intersection() {hub();flange_fasteners();}
    intersection() {mount();union(){motor_fasteners();guide_fasteners();}}
    intersection() {union(){carrier(0);carrier(1);} guide_fasteners();}
    intersection() {coupling();union(){flange_fasteners();coupling_screws();}}
    intersection() {union(){casing();cap();} housing_fasteners();}
}
module collisions() {
    if(!is_undef(fit_pair)) collision_pair(fit_pair[0],fit_pair[1]);
    else {
        internal_collisions();
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
        color("Silver") {sleeves();shaft_fasteners();coupling();coupling_screws();flange_fasteners();}
        color("SlateGray") {guide_fasteners();housing_fasteners();motor_fasteners();}
    }
    if(is_undef(show_motor)||show_motor) color("DarkSlateGray") motor();
}
module service_tools() {
    for(a=coupling_grub_angles) rotate([0,0,a+coupling_service_angle])
    translate([coupling_barrel_radius+0.1,0,coupling_grub_z]) rotate([0,90,0]) cylinder(r=0.9,h=35);
}
module drive_scene() {
    color("SteelBlue") mount();
    color("Gold") lower_hub();
    color("DimGray") bearing(1,0);
    color("Silver") {coupling();coupling_screws();flange_fasteners();motor_fasteners();}
    color("DarkSlateGray") motor();
}
if(!is_undef(flange_nut_installation_check)) color("Red") intersection() {
    union() {lower_hub();coupling();mount();}
    // The hull is the complete swept envelope of a translating hex nut.
    union() for(i=[0:len(coupling_positions)-1]) hull() {
        flange_nut(i,0);flange_nut(i,20);
    }
} else if(!is_undef(flange_nut_loading_view)) {
    color("Gold") lower_hub();
    color("Silver") coupling();
    color("SlateGray") for(i=[0:len(coupling_positions)-1]) flange_nut(i,12*(1-$t));
} else if(!is_undef(nut_installation_shift)) color("Red") intersection() {
    mount();
    translate([0,0,-nut_installation_shift]) for(p=guide_positions)
        translate([p[0],p[1],guide_nut_bottom]) hardware_nut_m3();
} else if(!is_undef(nut_loading_view)) {
    color("SteelBlue") mount();
    color("Silver") for(p=guide_positions)
        translate([p[0],p[1],motor_face-6]) hardware_nut_m3();
} else if(!is_undef(bearing_installation_shift)) color("Red") {
    intersection() {lower_hub();translate([0,0,bearing_installation_shift]) bearing(0,0);}
    intersection() {upper_hub();translate([0,0,bearing_installation_shift]) bearing(0,1);}
} else if(!is_undef(joint_installation_shift)) color("Red") intersection() {
    lower_hub();translate([0,0,joint_installation_shift]) upper_hub();
} else if(!is_undef(grub_access_check)) color("Red") intersection() {
    service_tools();
    union() {mount();lower_hub();bearing(1,0);}
} else if(!is_undef(drive_only)) {
    if(section_view) difference() {drive_scene();translate([0,-200,-200]) cube([200,400,500]);}
    else drive_scene();
} else if(!is_undef(installation_shift)) color("Red") intersection() {
    casing();
    translate([0,0,installation_shift]) {
        disk(0);disk(1);hub();carrier(0);carrier(1);sleeves();
        for(k=[0:2],s=[0:1]) if(k!=1 || s!=0) bearing(k,s);
    }
} else if(collision_view) color("Red") collisions();
else if(section_view) difference() {scene();translate([0,-200,-200]) cube([200,400,500]);}
else scene();
