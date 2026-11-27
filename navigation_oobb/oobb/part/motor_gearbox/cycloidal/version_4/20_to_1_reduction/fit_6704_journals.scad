$fn=96;
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 5, r = 10.0);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 5.02, r = 3.25);
						}
					}
				}
			}
		}
		translate(v = [22, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 5, r = 9.9);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 5.02, r = 3.25);
						}
					}
				}
			}
		}
		translate(v = [44, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 5, r = 9.8);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 5.02, r = 3.25);
						}
					}
				}
			}
		}
	}
	union();
}
