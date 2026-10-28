$fn=96;
difference() {
	union() {
		translate(v = [-71.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 5.0, r = 34.5);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 5.02, r = 32.0);
						}
						translate(v = [0, 0, 1.4]) {
							cylinder(h = 3.62, r = 32.5);
						}
					}
				}
			}
		}
		translate(v = [0.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 5.0, r = 34.5);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 5.02, r = 32.0);
						}
						translate(v = [0, 0, 1.4]) {
							cylinder(h = 3.62, r = 32.6);
						}
					}
				}
			}
		}
		translate(v = [71.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 5.0, r = 34.5);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 5.02, r = 32.0);
						}
						translate(v = [0, 0, 1.4]) {
							cylinder(h = 3.62, r = 32.7);
						}
					}
				}
			}
		}
	}
	union();
}
