// OPTIONAL bearing fit coupons; left to right radial clearance 0, 0.10, 0.20 mm.
$fn=96;
difference() {
	union() {
		translate(v = [0.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6, r = 20.0);
					}
					union() {
						translate(v = [0, 0, 4]) {
							translate(v = [0, 0, -2.0]) {
								union() {
									difference() {
										cylinder(h = 4.0, r = 16.0);
										cylinder(h = 4.0, r = 12.5);
									}
									difference() {
										translate(v = [0, 0, -50]) {
											cylinder(h = 100, r = 15.0);
										}
										translate(v = [0, 0, -50]) {
											cylinder(h = 100, r = 13.5);
										}
									}
								}
							}
						}
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 15.0);
						}
						translate(v = [0, 0, 1.85]) {
							cylinder(h = 4.17, r = 16.0);
						}
					}
				}
			}
		}
		translate(v = [44.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6, r = 20.0);
					}
					union() {
						translate(v = [0, 0, 4]) {
							translate(v = [0, 0, -2.0]) {
								union() {
									difference() {
										cylinder(h = 4.0, r = 16.0);
										cylinder(h = 4.0, r = 12.5);
									}
									difference() {
										translate(v = [0, 0, -50]) {
											cylinder(h = 100, r = 15.0);
										}
										translate(v = [0, 0, -50]) {
											cylinder(h = 100, r = 13.5);
										}
									}
								}
							}
						}
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 15.0);
						}
						translate(v = [0, 0, 1.85]) {
							cylinder(h = 4.17, r = 16.1);
						}
					}
				}
			}
		}
		translate(v = [88.0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6, r = 20.0);
					}
					union() {
						translate(v = [0, 0, 4]) {
							translate(v = [0, 0, -2.0]) {
								union() {
									difference() {
										cylinder(h = 4.0, r = 16.0);
										cylinder(h = 4.0, r = 12.5);
									}
									difference() {
										translate(v = [0, 0, -50]) {
											cylinder(h = 100, r = 15.0);
										}
										translate(v = [0, 0, -50]) {
											cylinder(h = 100, r = 13.5);
										}
									}
								}
							}
						}
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 15.0);
						}
						translate(v = [0, 0, 1.85]) {
							cylinder(h = 4.17, r = 16.2);
						}
					}
				}
			}
		}
	}
	union();
}
