$fn=96;
difference() {
	union() {
		hull() {
			translate(v = [-17.0, 17.0, 0]) {
				cylinder(h = 4.0, r = 5);
			}
			translate(v = [17.0, 17.0, 0]) {
				cylinder(h = 4.0, r = 5);
			}
			translate(v = [-17.0, -17.0, 0]) {
				cylinder(h = 4.0, r = 5);
			}
			translate(v = [17.0, -17.0, 0]) {
				cylinder(h = 4.0, r = 5);
			}
		}
	}
	union() {
		translate(v = [15.5, 15.5, 4.0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -4.02]) {
							cylinder(h = 4.02, r = 1.5);
						}
						translate(v = [0, 0, -1.9]) {
							cylinder(h = 1.9, r1 = 1.8, r2 = 3.6);
						}
						translate(v = [0, 0, -4.02]) {
							cylinder(h = 4.02, r = 1.8);
						}
						translate(v = [0, 0, -4.02]) {
							cylinder(h = 4.02, r = 1.5);
						}
					}
					union();
				}
			}
		}
		translate(v = [-15.5, 15.5, 4.0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -4.02]) {
							cylinder(h = 4.02, r = 1.5);
						}
						translate(v = [0, 0, -1.9]) {
							cylinder(h = 1.9, r1 = 1.8, r2 = 3.6);
						}
						translate(v = [0, 0, -4.02]) {
							cylinder(h = 4.02, r = 1.8);
						}
						translate(v = [0, 0, -4.02]) {
							cylinder(h = 4.02, r = 1.5);
						}
					}
					union();
				}
			}
		}
		translate(v = [-15.5, -15.5, 4.0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -4.02]) {
							cylinder(h = 4.02, r = 1.5);
						}
						translate(v = [0, 0, -1.9]) {
							cylinder(h = 1.9, r1 = 1.8, r2 = 3.6);
						}
						translate(v = [0, 0, -4.02]) {
							cylinder(h = 4.02, r = 1.8);
						}
						translate(v = [0, 0, -4.02]) {
							cylinder(h = 4.02, r = 1.5);
						}
					}
					union();
				}
			}
		}
		translate(v = [15.5, -15.5, 4.0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -4.02]) {
							cylinder(h = 4.02, r = 1.5);
						}
						translate(v = [0, 0, -1.9]) {
							cylinder(h = 1.9, r1 = 1.8, r2 = 3.6);
						}
						translate(v = [0, 0, -4.02]) {
							cylinder(h = 4.02, r = 1.8);
						}
						translate(v = [0, 0, -4.02]) {
							cylinder(h = 4.02, r = 1.5);
						}
					}
					union();
				}
			}
		}
		translate(v = [0, 0, -0.01]) {
			cylinder(h = 4.02, r = 11.2);
		}
	}
}
