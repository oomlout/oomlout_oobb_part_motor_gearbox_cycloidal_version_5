// Generated via working_scad. Edit populate/builders, not this file.
$fn=96;
module eccentric_hub_upper(){
difference() {
	union() {
		cylinder(h = 24.950000000000003, r = 7.700000000000001);
		translate(v = [-1.85, 0, 0.0]) {
			cylinder(h = 5.849999999999999, r = 9.9);
		}
		translate(v = [-1.85, 0, 5.849999999999999]) {
			cylinder(h = 0.8, r1 = 9.9, r2 = 10.8);
		}
		translate(v = [0, 0, 5.85]) {
			cylinder(h = 1.9000000000000012, r1 = 8.05, r2 = 9.9);
		}
		translate(v = [0, 0, 7.75]) {
			cylinder(h = 17.200000000000003, r = 9.9);
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
		translate(v = [0, 0, 18.950000000000003]) {
			cylinder(h = 6.119999999999999, r = 6.05);
		}
		translate(v = [0, 0, -0.01]) {
			cylinder(h = 27.070000000000004, r = 3.25);
		}
	}
}

}
eccentric_hub_upper();
