$fn=96;
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, 4]) {
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
						cylinder(h = 4, r = 9);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 7.02, r = 3.25);
						}
					}
				}
			}
		}
		translate(v = [24, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 4, r = 9);
					}
					union() {
						translate(v = [0, 0, 2]) {
							rotate(a = [0, 0, 0]) {
								difference() {
									union() {
										cylinder(h = 2.17, r = 5.050000000000001);
									}
									union() {
										translate(v = [4.449999999999999, -10.0, -0.01]) {
											cube(size = [20, 20, 2.1999999999999997]);
										}
									}
								}
							}
						}
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 7.02, r = 3.25);
						}
					}
				}
			}
		}
	}
	union();
}
