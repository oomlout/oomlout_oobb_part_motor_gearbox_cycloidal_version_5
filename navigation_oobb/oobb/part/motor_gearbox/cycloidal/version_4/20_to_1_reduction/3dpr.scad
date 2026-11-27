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
$fn=96;
translate([52.0, 52.0, 0]) motor_mount();
translate([158.1, 46.1, 0]) output_base();
translate([46.1, 158.1, 0]) output_casing();
translate([146.3, 158.1, 0]) output_cover();
translate([41.0, 253.2, 0]) rotor_a_lower();
translate([131.0, 253.2, 0]) rotor_a_upper();
translate([41.0, 343.2, 0]) rotor_b_lower();
translate([131.0, 343.2, 0]) rotor_b_upper();
translate([34.0, 426.2, 0]) pin_rear();
translate([110.0, 426.2, 0]) pin_front();
translate([176.9, 417.09999999999997, 0]) front_bearing_hub();
translate([223.3, 405.7, 0]) coupling_collar();
translate([13.5, 481.7, 0]) coupling_drive();
translate([48.5, 481.7, 0]) eccentric_hub_lower();
translate([82.65, 480.84999999999997, 0]) eccentric_hub_upper();