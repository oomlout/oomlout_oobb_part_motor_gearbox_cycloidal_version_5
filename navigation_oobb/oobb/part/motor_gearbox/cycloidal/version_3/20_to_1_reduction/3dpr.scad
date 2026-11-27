// Print one of each of the 9 pieces; all on z=0.
use <motor_mount.scad>
use <output_casing.scad>
use <output_cover.scad>
use <pin_rear.scad>
use <pin_front.scad>
use <rotor_a.scad>
use <rotor_b.scad>
use <eccentric_hub_lower.scad>
use <eccentric_hub_upper.scad>

$fn=96;
translate([44.5, 44.5, 0]) motor_mount();
translate([141.5, 44.5, 0]) output_casing();
translate([44.5, 141.5, 0]) output_cover();
translate([135.5, 135.5, 0]) rotor_a();
translate([38.5, 232.5, 0]) rotor_b();
translate([113.0, 222.0, 0]) pin_rear();
translate([177.0, 222.0, 0]) pin_front();
translate([15.700000000000001, 294.7, 0]) eccentric_hub_lower();
translate([52.150000000000006, 291.75, 0]) eccentric_hub_upper();
