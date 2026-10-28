use <rotor_lower.scad>
use <eccentric_lower.scad>
use <input_hub_lower.scad>
use <output_carrier_lower.scad>
use <rotor_upper.scad>
use <eccentric_upper.scad>
use <input_hub_upper.scad>
use <output_carrier_upper.scad>
use <housing_back.scad>
use <bearing_retainer_back.scad>
use <housing_front.scad>
use <bearing_retainer_front.scad>
use <housing_spacer.scad>
use <input_shaft_spacer.scad>
use <hardware_bearing_input.scad>
use <hardware_bearing_output.scad>
use <hardware_retainer_screw.scad>
use <hardware_fasteners.scad>
ratio = 12;
eccentricity = 1.5;
rotor_depth = 9;
cover_depth = 12;
gap = 18.0;
axial_gap = 4.5;
ring_positions = [[38.0, 0.0], [33.647328974821974, 17.659480537663207], [21.586460375783922, 31.273386903958947], [4.580393849702274, 37.72293721572605], [-13.474985707616355, 35.53061722204576], [-28.443408430501833, 25.198661013150225], [-36.89578906218998, 9.093995242927193], [-36.895789062189984, -9.093995242927182], [-28.443408430501837, -25.198661013150222], [-13.474985707616364, -35.53061722204576], [4.580393849702248, -37.722937215726056], [21.586460375783936, -31.27338690395893], [33.64732897482198, -17.6594805376632]];
ring_radius = 3.0;
output_positions = [[15.0, 15.0], [-15.0, 15.0], [-15.0, -15.0], [15.0, -15.0]];
output_radius = 1.25;
input_radius = 3.0;
back_retainer_screws = [[19.904307257234066, 4.905971117894934], [-11.645327307988692, 16.871169250819957], [-11.645327307988696, -16.871169250819957]];
front_retainer_screws = [[35.924847244763924, -8.854679578639637], [-21.018395629052762, -30.45040303806529], [-21.01839562905277, 30.450403038065286]];
housing_positions = [[37.5, 37.5], [-37.5, 37.5], [-37.5, -37.5], [37.5, -37.5]];
rotor_screws = [[26.0, 0.0], [1.592040838891559e-15, 26.0], [-26.0, 3.184081677783118e-15], [-4.776122516674677e-15, -26.0]];
shaft_screws = [[7.5, 0.0], [4.592425496802575e-16, 7.5], [-7.5, 9.18485099360515e-16], [-1.3777276490407722e-15, -7.5]];
carrier_screws = [[18.477590650225736, 7.653668647301796], [-7.653668647301794, 18.477590650225736], [-18.477590650225736, -7.653668647301793], [7.6536686473018, -18.477590650225732]];
nut_depth_m3 = 2.5;
nut_depth_m2d5 = 1.9;
nut_depth_m6 = 5;
shaft_washer_depth = 1.6;
input_bearing_depth = 4.0;
output_bearing_depth = 7.0;
// Generated geometry is fixed; these controls change only pose and visibility.
$fn = 96;
turns = is_undef(input_turns) ? 0 : input_turns;
explosion = is_undef(explode) ? 0 : explode;
display_housing = is_undef(show_housing) ? true : show_housing;
display_carrier = is_undef(show_carrier) ? true : show_carrier;
display_retainers = is_undef(show_retainers) ? true : show_retainers;
display_bearings = is_undef(show_bearings) ? true : show_bearings;
display_hardware = is_undef(show_hardware) ? true : show_hardware;
section_view = is_undef(cutaway) ? false : cutaway;
collision_view = is_undef(fit_only) ? false : fit_only;
input_angle = turns*360;
output_angle = -input_angle/ratio;

// Exploded layers run from -6 (back cover) to +9 (front cover).
// Every displacement vanishes at explode=0, preserving the physical fit pose.
module rotor_pair() {
    translate([eccentricity*cos(input_angle),eccentricity*sin(input_angle),axial_gap])
    rotate([0,0,output_angle]) {
        rotor_lower();
        translate([0,0,rotor_depth+explosion*4]) rotate([180,0,0]) rotor_upper();
    }
}
module eccentric_pair() {
    translate([0,0,axial_gap]) rotate([0,0,input_angle]) {
        translate([0,0,explosion]) eccentric_lower();
        translate([0,0,rotor_depth+explosion*3]) rotate([180,0,0]) eccentric_upper();
    }
}
module input_hub_pair() {
    rotate([0,0,input_angle]) {
        translate([0,0,-explosion]) input_shaft_spacer();
        translate([0,0,-cover_depth-explosion*5]) input_hub_lower();
        translate([0,0,-explosion*3]) rotate([180,0,0]) input_hub_upper();
    }
}
module carrier_pair() {
    rotate([0,0,output_angle]) {
        translate([0,0,gap+explosion*6]) output_carrier_lower();
        translate([0,0,gap+cover_depth+explosion*8]) rotate([180,0,0]) output_carrier_upper();
    }
}
module ring_pins() {
    for (p=ring_positions) translate([p[0],p[1],-cover_depth])
        cylinder(r=ring_radius,h=gap+2*cover_depth);
}
module retained_ring_rods() {
    for (p=ring_positions) {
        translate([p[0],p[1],-cover_depth-nut_depth_m6-1])
            cylinder(r=ring_radius,h=gap+2*cover_depth+2*(nut_depth_m6+1));
        translate([p[0],p[1],-cover_depth-nut_depth_m6-explosion*6.8]) hardware_nut_m6();
        translate([p[0],p[1],gap+cover_depth+explosion*9.8]) hardware_nut_m6();
    }
}
module output_pins() {
    rotate([0,0,output_angle]) for (p=output_positions)
        translate([p[0],p[1],axial_gap-0.5+explosion*6])
            cylinder(r=output_radius,h=gap+cover_depth-axial_gap+0.5);
}
module housings() {
    translate([0,0,-cover_depth-explosion*6]) housing_back();
    translate([0,0,gap+cover_depth+explosion*9]) rotate([180,0,0]) housing_front();
    for(p=housing_positions) translate([p[0],p[1],0]) housing_spacer();
}
module retainers() {
    translate([0,0,1-explosion*2]) rotate([180,0,0]) bearing_retainer_back();
    translate([0,0,gap-1+explosion*5]) bearing_retainer_front();
}
module retainer_bolts() {
    for (p=back_retainer_screws) translate([p[0],p[1],1-explosion*1.35]) hardware_retainer_screw();
    for (p=front_retainer_screws) translate([p[0],p[1],gap-1+explosion*4.35])
        rotate([180,0,0]) hardware_retainer_screw();
}
module retainer_nuts() {
    for(p=back_retainer_screws)
        translate([p[0],p[1],-cover_depth-nut_depth_m3-explosion*6.4]) hardware_nut_m3();
    for(p=front_retainer_screws)
        translate([p[0],p[1],gap+cover_depth+explosion*9.4]) hardware_nut_m3();
}
module joining_fasteners() {
    // Rotor fasteners orbit with the rotor; eccentric and hub fasteners follow input.
    translate([eccentricity*cos(input_angle),eccentricity*sin(input_angle),axial_gap])
    rotate([0,0,output_angle]) for(p=rotor_screws) {
        translate([p[0],p[1],-explosion*0.8]) rotate([180,0,0]) hardware_screw_rotor();
        translate([p[0],p[1],rotor_depth-nut_depth_m3+0.02+explosion*4.6]) hardware_nut_m3();
    }
    rotate([0,0,input_angle]) for(p=shaft_screws) {
        translate([p[0],p[1],axial_gap+explosion*0.5]) rotate([180,0,0]) hardware_screw_eccentric();
        translate([p[0],p[1],axial_gap+rotor_depth-nut_depth_m3+0.02+explosion*3.6]) hardware_nut_m3();
        translate([p[0],p[1],-cover_depth-explosion*5.65]) rotate([180,0,0]) hardware_screw_hub();
        translate([p[0],p[1],-nut_depth_m3+0.02-explosion*2.4]) hardware_nut_m3();
    }
    rotate([0,0,output_angle]) {
        for(p=carrier_screws) {
            translate([p[0],p[1],gap+cover_depth+explosion*8.65]) hardware_screw_carrier();
            translate([p[0],p[1],gap+explosion*5.4]) hardware_nut_m3();
        }
        for(p=output_positions) {
            translate([p[0],p[1],gap+cover_depth+explosion*9.5]) hardware_screw_output();
            translate([p[0],p[1],gap+explosion*5.4]) hardware_nut_m2d5();
        }
    }
    for(p=housing_positions) {
        translate([p[0],p[1],gap+cover_depth+explosion*11.5]) hardware_screw_housing();
        translate([p[0],p[1],-cover_depth-explosion*6.6]) hardware_nut_m3();
    }
}
module input_axle_and_clamp() {
    rotate([0,0,input_angle]) {
        translate([0,0,-cover_depth-shaft_washer_depth-nut_depth_m6-2-explosion*8.2])
            cylinder(r=input_radius,h=cover_depth+rotor_depth+axial_gap+2*(shaft_washer_depth+nut_depth_m6+2));
        translate([0,0,-cover_depth-shaft_washer_depth-explosion*6.6]) hardware_washer_m6();
        translate([0,0,-cover_depth-shaft_washer_depth-nut_depth_m6-explosion*7]) hardware_nut_m6();
        translate([0,0,axial_gap+rotor_depth+explosion*3.4]) hardware_washer_m6();
        translate([0,0,axial_gap+rotor_depth+shaft_washer_depth+explosion*3.7]) hardware_nut_m6();
    }
}
module bearings() {
    translate([0,0,-cover_depth/2-explosion*4]) hardware_bearing_input();
    translate([eccentricity*cos(input_angle),eccentricity*sin(input_angle),axial_gap+rotor_depth/2+explosion*2]) hardware_bearing_input();
    translate([0,0,gap+cover_depth/2+explosion*7]) hardware_bearing_output();
}
module assembly() {
    if(display_housing) color([0.50,0.58,0.67]) housings();
    if(display_retainers) color([0.55,0.62,0.70]) retainers();
    color([0.95,0.59,0.17]) rotor_pair();
    color([0.32,0.65,0.84]) eccentric_pair();
    color([0.32,0.65,0.84]) input_hub_pair();
    if(display_carrier) color([0.32,0.72,0.48]) carrier_pair();
    if(display_hardware) color([0.75,0.76,0.79]) {
        retained_ring_rods();
        if(display_bearings) bearings();
        if(display_retainers) { retainer_bolts(); retainer_nuts(); }
        joining_fasteners();
        input_axle_and_clamp();
    }
}
module collisions() {
    color("red") intersection() {
        rotor_pair();
        union() { retained_ring_rods(); output_pins(); eccentric_pair(); carrier_pair(); housings(); retainers(); retainer_bolts(); retainer_nuts(); joining_fasteners(); input_axle_and_clamp(); }
    }
}
if(collision_view) collisions();
else if(section_view) difference() {
    assembly();
    translate([-200,-200,-100]) cube([400,200,300]);
}
else assembly();
