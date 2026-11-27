// Optional test print. Bearing seats left to right: radial allowance 0, 0.10, 0.20 mm.
$fn=96;
difference() {
	union() {
		translate(v = [-28.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 8.0, r = 13.0);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 8.02, r = 9.5);
						}
						translate(v = [0, 0, 1.7999999999999998]) {
							cylinder(h = 6.22, r = 11.0);
						}
					}
				}
			}
		}
		translate(v = [0.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 8.0, r = 13.0);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 8.02, r = 9.5);
						}
						translate(v = [0, 0, 1.7999999999999998]) {
							cylinder(h = 6.22, r = 11.1);
						}
					}
				}
			}
		}
		translate(v = [28.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 8.0, r = 13.0);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 8.02, r = 9.5);
						}
						translate(v = [0, 0, 1.7999999999999998]) {
							cylinder(h = 6.22, r = 11.2);
						}
					}
				}
			}
		}
	}
	union();
}
