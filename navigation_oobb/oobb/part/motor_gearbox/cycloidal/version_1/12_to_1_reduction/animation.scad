// Exploded working assembly: 12 input turns / one output turn.
// View > Animate: FPS 12, Steps 192. Set explode=0 to assemble.
input_turns = 12*$t;
explode = 20;
show_housing = true;
show_carrier = true;
show_retainers = true;
show_bearings = true;
show_hardware = true;
$vpt = [0, 0, 42.0];
$vpr = [65, 0, 25];
$vpd = 1359.36;
include <assembly.scad>
