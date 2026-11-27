// Optional test print. Bearing seats left to right: radial allowance 0, 0.10, 0.20 mm.
$fn=96;
difference() {
	union() {
		translate(v = [-22, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6, r = 7.5);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 2.75);
						}
					}
				}
			}
		}
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6, r = 7.4);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 2.75);
						}
					}
				}
			}
		}
		translate(v = [22, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6, r = 7.3);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 2.75);
						}
					}
				}
			}
		}
		translate(v = [-22, 22, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6, r = 5.0);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 2.75);
						}
					}
				}
			}
		}
		translate(v = [0, 22, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6, r = 4.9);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 2.75);
						}
					}
				}
			}
		}
		translate(v = [22, 22, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6, r = 4.8);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 2.75);
						}
					}
				}
			}
		}
	}
	union();
}
