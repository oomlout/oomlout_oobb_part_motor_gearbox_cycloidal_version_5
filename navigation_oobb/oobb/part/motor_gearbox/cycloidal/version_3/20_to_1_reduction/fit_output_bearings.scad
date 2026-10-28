// Optional test print. Bearing seats left to right: radial allowance 0, 0.10, 0.20 mm.
$fn=96;
difference() {
	union() {
		translate(v = [-71.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 9.0, r = 34.5);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 9.02, r = 31.0);
						}
						translate(v = [0, 0, 1.7999999999999998]) {
							cylinder(h = 7.22, r = 32.5);
						}
					}
				}
			}
		}
		translate(v = [0.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 9.0, r = 34.5);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 9.02, r = 31.0);
						}
						translate(v = [0, 0, 1.7999999999999998]) {
							cylinder(h = 7.22, r = 32.6);
						}
					}
				}
			}
		}
		translate(v = [71.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 9.0, r = 34.5);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 9.02, r = 31.0);
						}
						translate(v = [0, 0, 1.7999999999999998]) {
							cylinder(h = 7.22, r = 32.7);
						}
					}
				}
			}
		}
	}
	union();
}
