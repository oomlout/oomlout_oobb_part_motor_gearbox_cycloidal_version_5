$fn=96;
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 3.5, r = 12);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 3.52, r = 7.0);
						}
						translate(v = [0, 0, 1.4]) {
							cylinder(h = 2.12, r = 7.6);
						}
					}
				}
			}
		}
		translate(v = [28, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 3.5, r = 12);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 3.52, r = 7.0);
						}
						translate(v = [0, 0, 1.4]) {
							cylinder(h = 2.12, r = 7.6);
						}
					}
				}
			}
		}
	}
	union();
}
