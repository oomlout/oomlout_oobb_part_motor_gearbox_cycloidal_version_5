// Generated via working_scad. Edit populate/builders, not this file.
$fn=96;
module eccentric_hub_lower(){
difference() {
	union() {
		translate(v = [0, 0, 7.75]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 2.02, r = 4.9);
					}
					union() {
						translate(v = [4.300000000000001, -10.0, -0.01]) {
							cube(size = [20, 20, 2.05]);
						}
					}
				}
			}
		}
		cylinder(h = 7.75, r = 7.700000000000001);
		translate(v = [1.85, 0, 1.8999999999999986]) {
			cylinder(h = 4.2, r = 9.9);
		}
		translate(v = [1.85, 0, 0.0]) {
			cylinder(h = 1.8999999999999986, r = 10.8);
		}
	}
	union() {
		translate(v = [0, 0, -0.01]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 2.17, r = 5.050000000000001);
					}
					union() {
						translate(v = [4.449999999999999, -10.0, -0.01]) {
							cube(size = [20, 20, 2.1999999999999997]);
						}
					}
				}
			}
		}
		translate(v = [4.898587196589413e-16, 8.0, -0.01]) {
			cylinder(h = 0.27, r = 3.05);
		}
		translate(v = [-1.4695761589768238e-15, -8.0, -0.01]) {
			cylinder(h = 0.27, r = 3.05);
		}
		translate(v = [0, 0, -0.01]) {
			cylinder(h = 9.87, r = 3.25);
		}
	}
}

}
eccentric_hub_lower();
