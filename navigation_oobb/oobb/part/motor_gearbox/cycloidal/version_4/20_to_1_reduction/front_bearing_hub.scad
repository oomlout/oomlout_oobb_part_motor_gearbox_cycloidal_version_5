// Generated via working_scad. Edit populate/builders, not this file.
$fn=96;
module front_bearing_hub(){
difference() {
	union() {
		cylinder(h = 10.5, r = 24.9);
	}
	union() {
		translate(v = [16.5, 0.0, 10.3]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -10.32]) {
							cylinder(h = 10.32, r = 1.5);
						}
						translate(v = [0, 0, -1.9]) {
							cylinder(h = 1.9, r1 = 1.8, r2 = 3.6);
						}
						translate(v = [0, 0, -10.32]) {
							cylinder(h = 10.32, r = 1.8);
						}
						translate(v = [0, 0, -10.32]) {
							cylinder(h = 10.32, r = 1.5);
						}
					}
					union();
				}
			}
		}
		translate(v = [-8.249999999999996, 14.289419162443238, 10.3]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -10.32]) {
							cylinder(h = 10.32, r = 1.5);
						}
						translate(v = [0, 0, -1.9]) {
							cylinder(h = 1.9, r1 = 1.8, r2 = 3.6);
						}
						translate(v = [0, 0, -10.32]) {
							cylinder(h = 10.32, r = 1.8);
						}
						translate(v = [0, 0, -10.32]) {
							cylinder(h = 10.32, r = 1.5);
						}
					}
					union();
				}
			}
		}
		translate(v = [-8.250000000000007, -14.289419162443235, 10.3]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -10.32]) {
							cylinder(h = 10.32, r = 1.5);
						}
						translate(v = [0, 0, -1.9]) {
							cylinder(h = 1.9, r1 = 1.8, r2 = 3.6);
						}
						translate(v = [0, 0, -10.32]) {
							cylinder(h = 10.32, r = 1.8);
						}
						translate(v = [0, 0, -10.32]) {
							cylinder(h = 10.32, r = 1.5);
						}
					}
					union();
				}
			}
		}
		translate(v = [0, 0, -0.01]) {
			cylinder(h = 10.52, r = 12.0);
		}
		translate(v = [0, 0, -0.01]) {
			cylinder(h = 1.17, r = 13.15);
		}
		translate(v = [0, 0, 6.3]) {
			cylinder(h = 4.22, r = 13.6);
		}
		translate(v = [16.5, 0.0, 10.3]) {
			cylinder(h = 0.32, r = 3);
		}
		translate(v = [-8.249999999999996, 14.289419162443238, 10.3]) {
			cylinder(h = 0.32, r = 3);
		}
		translate(v = [-8.250000000000007, -14.289419162443235, 10.3]) {
			cylinder(h = 0.32, r = 3);
		}
	}
}

}
front_bearing_hub();
