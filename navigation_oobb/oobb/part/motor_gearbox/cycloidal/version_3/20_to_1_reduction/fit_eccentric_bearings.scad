// Optional test print. Bearing seats left to right: radial allowance 0, 0.10, 0.20 mm.
$fn=96;
difference() {
	union() {
		translate(v = [-33.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6.0, r = 15.5);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 12.0);
						}
						translate(v = [0, 0, 1.7999999999999998]) {
							cylinder(h = 4.22, r = 13.5);
						}
					}
				}
			}
		}
		translate(v = [0.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6.0, r = 15.5);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 12.0);
						}
						translate(v = [0, 0, 1.7999999999999998]) {
							cylinder(h = 4.22, r = 13.6);
						}
					}
				}
			}
		}
		translate(v = [33.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6.0, r = 15.5);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 12.0);
						}
						translate(v = [0, 0, 1.7999999999999998]) {
							cylinder(h = 4.22, r = 13.7);
						}
					}
				}
			}
		}
	}
	union();
}
