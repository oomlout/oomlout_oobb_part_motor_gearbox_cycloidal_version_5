$fn=96;
difference() {
	union() {
		translate(v = [-33.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 3.5, r = 15.5);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 3.52, r = 13.0);
						}
						translate(v = [0, 0, 1.4]) {
							cylinder(h = 2.12, r = 13.5);
						}
					}
				}
			}
		}
		translate(v = [0.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 3.5, r = 15.5);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 3.52, r = 13.0);
						}
						translate(v = [0, 0, 1.4]) {
							cylinder(h = 2.12, r = 13.6);
						}
					}
				}
			}
		}
		translate(v = [33.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 3.5, r = 15.5);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 3.52, r = 13.0);
						}
						translate(v = [0, 0, 1.4]) {
							cylinder(h = 2.12, r = 13.7);
						}
					}
				}
			}
		}
	}
	union();
}
