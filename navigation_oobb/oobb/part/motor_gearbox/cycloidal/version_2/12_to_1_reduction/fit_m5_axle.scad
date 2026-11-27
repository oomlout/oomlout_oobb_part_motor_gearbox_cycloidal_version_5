// Optional test print. Bearing seats left to right: radial allowance 0, 0.10, 0.20 mm.
$fn=96;
difference() {
	union() {
		cylinder(h = 8, r = 8);
	}
	union() {
		translate(v = [0, 0, -0.01]) {
			cylinder(h = 8.02, r = 2.75);
		}
	}
}
