// PRINT LAYOUT: all required pieces, flat on z=0. This is 3D geometry.
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

$fn=96;
translate([44.5, 44.5, 0]) housing_back();
translate([141.5, 44.5, 0]) housing_front();
translate([40.5, 137.5, 0]) bearing_retainer_front();
translate([127.0, 135.0, 0]) rotor_lower();
translate([38.0, 224.0, 0]) rotor_upper();
translate([112.0, 214.0, 0]) output_carrier_lower();
translate([176.0, 214.0, 0]) output_carrier_upper();
translate([24.0, 294.0, 0]) bearing_retainer_back();
translate([71.5, 285.5, 0]) eccentric_lower();
translate([110.5, 285.5, 0]) eccentric_upper();
translate([148.0, 284.0, 0]) input_hub_lower();
translate([184.0, 284.0, 0]) input_hub_upper();
translate([216.0, 280.0, 0]) input_shaft_spacer();
translate([5.0, 331.0, 0]) housing_spacer();
translate([23.0, 331.0, 0]) housing_spacer();
translate([41.0, 331.0, 0]) housing_spacer();
translate([59.0, 331.0, 0]) housing_spacer();
