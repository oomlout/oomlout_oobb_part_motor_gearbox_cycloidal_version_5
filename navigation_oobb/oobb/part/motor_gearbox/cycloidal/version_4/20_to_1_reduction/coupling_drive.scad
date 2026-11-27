// Generated via working_scad. Edit populate/builders, not this file.
$fn=96;
module coupling_drive(){
difference() {
	union() {
		translate(v = [0, 0, 8.5]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 2.02, r = 4.9);
					}
					union() {
						translate(v = [4.300000000000001, -10.0, -0.01]) {
							cube(size = [20, 20, 2.05]);
						}
					}
				}
			}
		}
		cylinder(h = 8.5, r = 13.5);
	}
	union() {
		translate(v = [0, 0, 5.300000000000001]) {
			rotate(a = [0, 0, 30]) {
				difference() {
					union() {
						translate(v = [-2.875, -5.0, -5.699999999999998]) {
							cube(size = [5.75, 10, 0.3]);
						}
						translate(v = [-2.875, -2.875, -5.999999999999998]) {
							cube(size = [5.75, 5.75, 0.3]);
						}
						translate(v = [-2.875, -5.0, 0.0]) {
							cube(size = [5.75, 10, 0.3]);
						}
						translate(v = [-2.875, -2.875, 0.3]) {
							cube(size = [5.75, 5.75, 0.3]);
						}
						translate(v = [0, 0, -5.399999999999999]) {
							linear_extrude(height = 5.399999999999999) {
								polygon(points = [[5.914249999999999, 0.0], [2.957125, 5.1218907443321156], [-2.9571249999999982, 5.1218907443321156], [-5.914249999999999, 7.242867331857232e-16], [-2.9571250000000022, -5.121890744332115], [2.9571249999999956, -5.121890744332118]]);
							}
						}
						translate(v = [-2.875, -5.0, -5.699999999999998]) {
							cube(size = [5.75, 10, 0.3]);
						}
						translate(v = [-2.875, -2.875, -5.999999999999998]) {
							cube(size = [5.75, 5.75, 0.3]);
						}
						translate(v = [-2.875, -5.0, 0.0]) {
							cube(size = [5.75, 10, 0.3]);
						}
						translate(v = [-2.875, -2.875, 0.3]) {
							cube(size = [5.75, 5.75, 0.3]);
						}
						translate(v = [-2.875, -5.0, -5.699999999999998]) {
							cube(size = [5.75, 10, 0.3]);
						}
						translate(v = [-2.875, -2.875, -5.999999999999998]) {
							cube(size = [5.75, 5.75, 0.3]);
						}
						translate(v = [-2.875, -5.0, 0.0]) {
							cube(size = [5.75, 10, 0.3]);
						}
						translate(v = [-2.875, -2.875, 0.3]) {
							cube(size = [5.75, 5.75, 0.3]);
						}
					}
					union();
				}
			}
		}
		translate(v = [4.898587196589413e-16, 8.0, -0.01]) {
			cylinder(h = 8.52, r = 1.8);
		}
		translate(v = [-1.4695761589768238e-15, -8.0, -0.01]) {
			cylinder(h = 8.52, r = 1.8);
		}
		translate(v = [4.898587196589413e-16, 8.0, 5.5]) {
			cylinder(h = 8.52, r = 3.05);
		}
		translate(v = [-1.4695761589768238e-15, -8.0, 5.5]) {
			cylinder(h = 8.52, r = 3.05);
		}
		translate(v = [0, 0, -0.01]) {
			cylinder(h = 10.62, r = 3.25);
		}
	}
}

}
coupling_drive();
