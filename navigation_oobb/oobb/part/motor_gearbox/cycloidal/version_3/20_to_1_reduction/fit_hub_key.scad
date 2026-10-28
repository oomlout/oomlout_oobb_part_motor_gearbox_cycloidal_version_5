// Optional test print. Bearing seats left to right: radial allowance 0, 0.10, 0.20 mm.
$fn=96;
difference() {
	union() {
		translate(v = [-12, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 3.0, r = 6.0);
						translate(v = [0, 0, 3.0]) {
							cylinder(h = 2, r = 8);
						}
					}
					union() {
						translate(v = [5.0, -12.0, -0.01]) {
							cube(size = [12.0, 24.0, 3.02]);
						}
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 5.02, r = 2.75);
						}
					}
				}
			}
		}
		translate(v = [12, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 5.0, r = 8);
					}
					union() {
						translate(v = [0, 0, 2]) {
							rotate(a = [0, 0, 0]) {
								difference() {
									union() {
										cylinder(h = 3.02, r = 6.199999999999999);
									}
									union() {
										translate(v = [5.199999999999999, -12.399999999999999, -0.01]) {
											cube(size = [12.399999999999999, 24.799999999999997, 3.04]);
										}
									}
								}
							}
						}
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 5.02, r = 2.75);
						}
					}
				}
			}
		}
	}
	union();
}
