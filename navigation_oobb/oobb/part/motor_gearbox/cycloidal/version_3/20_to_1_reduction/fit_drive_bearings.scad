// Optional test print. Bearing seats left to right: radial allowance 0, 0.10, 0.20 mm.
$fn=96;
difference() {
	union() {
		translate(v = [-43.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6.0, r = 20.5);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 17.0);
						}
						translate(v = [0, 0, 1.7999999999999998]) {
							cylinder(h = 4.22, r = 18.5);
						}
					}
				}
			}
		}
		translate(v = [0.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6.0, r = 20.5);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 17.0);
						}
						translate(v = [0, 0, 1.7999999999999998]) {
							cylinder(h = 4.22, r = 18.6);
						}
					}
				}
			}
		}
		translate(v = [43.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6.0, r = 20.5);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 17.0);
						}
						translate(v = [0, 0, 1.7999999999999998]) {
							cylinder(h = 4.22, r = 18.7);
						}
					}
				}
			}
		}
	}
	union();
}
