// Generated via working_scad. Edit populate/builders, not this file.
$fn=96;
module output_cover(){
difference() {
	union() {
		cylinder(h = 2.0, r = 46.1);
		translate(v = [35.5, 35.5, 0.0]) {
			cylinder(h = 2.0, r = 7.0);
		}
		translate(v = [-35.5, 35.5, 0.0]) {
			cylinder(h = 2.0, r = 7.0);
		}
		translate(v = [-35.5, -35.5, 0.0]) {
			cylinder(h = 2.0, r = 7.0);
		}
		translate(v = [35.5, -35.5, 0.0]) {
			cylinder(h = 2.0, r = 7.0);
		}
		translate(v = [0, 0, 2.0]) {
			cylinder(h = 10.4, r = 34.6);
		}
		translate(v = [35.5, 35.5, 2.0]) {
			cylinder(h = 25.5, r = 4.8);
		}
		translate(v = [-35.5, 35.5, 2.0]) {
			cylinder(h = 25.5, r = 4.8);
		}
		translate(v = [-35.5, -35.5, 2.0]) {
			cylinder(h = 25.5, r = 4.8);
		}
		translate(v = [35.5, -35.5, 2.0]) {
			cylinder(h = 25.5, r = 4.8);
		}
	}
	union() {
		translate(v = [0, 0, 67.0]) {
			rotate(a = [180, 0, 0]) {
				difference() {
					union() {
						translate(v = [35.5, 35.5, 42.0]) {
							rotate(a = [0, 0, 0]) {
								difference() {
									union() {
										translate(v = [0, 0, -35.0]) {
											cylinder(h = 35.0, r = 1.5);
										}
										cylinder(h = 253.2, r = 3.0);
										translate(v = [0, 0, -35.0]) {
											cylinder(h = 35.0, r = 1.8);
										}
										translate(v = [0, 0, -35.0]) {
											cylinder(h = 35.0, r = 1.5);
										}
									}
									union();
								}
							}
						}
						translate(v = [-35.5, 35.5, 42.0]) {
							rotate(a = [0, 0, 0]) {
								difference() {
									union() {
										translate(v = [0, 0, -35.0]) {
											cylinder(h = 35.0, r = 1.5);
										}
										cylinder(h = 253.2, r = 3.0);
										translate(v = [0, 0, -35.0]) {
											cylinder(h = 35.0, r = 1.8);
										}
										translate(v = [0, 0, -35.0]) {
											cylinder(h = 35.0, r = 1.5);
										}
									}
									union();
								}
							}
						}
						translate(v = [-35.5, -35.5, 42.0]) {
							rotate(a = [0, 0, 0]) {
								difference() {
									union() {
										translate(v = [0, 0, -35.0]) {
											cylinder(h = 35.0, r = 1.5);
										}
										cylinder(h = 253.2, r = 3.0);
										translate(v = [0, 0, -35.0]) {
											cylinder(h = 35.0, r = 1.8);
										}
										translate(v = [0, 0, -35.0]) {
											cylinder(h = 35.0, r = 1.5);
										}
									}
									union();
								}
							}
						}
						translate(v = [35.5, -35.5, 42.0]) {
							rotate(a = [0, 0, 0]) {
								difference() {
									union() {
										translate(v = [0, 0, -35.0]) {
											cylinder(h = 35.0, r = 1.5);
										}
										cylinder(h = 253.2, r = 3.0);
										translate(v = [0, 0, -35.0]) {
											cylinder(h = 35.0, r = 1.8);
										}
										translate(v = [0, 0, -35.0]) {
											cylinder(h = 35.0, r = 1.5);
										}
									}
									union();
								}
							}
						}
					}
					union();
				}
			}
		}
		translate(v = [0, 0, -0.01]) {
			cylinder(h = 12.42, r = 28.5);
		}
		translate(v = [0, 0, 5.0]) {
			cylinder(h = 7.42, r = 32.6);
		}
	}
}

}
output_cover();
