// Optional test print. Bearing seats left to right: radial allowance 0, 0.10, 0.20 mm.
$fn=96;
difference() {
	union() {
		translate(v = [-30.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 7.0, r = 14.0);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 7.02, r = 10.5);
						}
						translate(v = [0, 0, 1.7999999999999998]) {
							cylinder(h = 5.22, r = 12.0);
						}
					}
				}
			}
		}
		translate(v = [0.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 7.0, r = 14.0);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 7.02, r = 10.5);
						}
						translate(v = [0, 0, 1.7999999999999998]) {
							cylinder(h = 5.22, r = 12.1);
						}
					}
				}
			}
		}
		translate(v = [30.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 7.0, r = 14.0);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 7.02, r = 10.5);
						}
						translate(v = [0, 0, 1.7999999999999998]) {
							cylinder(h = 5.22, r = 12.2);
						}
					}
				}
			}
		}
	}
	union();
}
