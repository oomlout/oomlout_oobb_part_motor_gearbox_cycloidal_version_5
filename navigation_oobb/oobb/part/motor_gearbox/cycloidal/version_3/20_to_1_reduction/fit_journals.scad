// Optional test print. Bearing seats left to right: radial allowance 0, 0.10, 0.20 mm.
$fn=96;
difference() {
	union() {
		translate(v = [-36, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6, r = 10.0);
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
						cylinder(h = 6, r = 9.9);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 2.75);
						}
					}
				}
			}
		}
		translate(v = [36, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6, r = 9.8);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 2.75);
						}
					}
				}
			}
		}
		translate(v = [-36, 36, 0]) {
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
		translate(v = [0, 36, 0]) {
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
		translate(v = [36, 36, 0]) {
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
		translate(v = [-36, 72, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6, r = 15.0);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 2.75);
						}
					}
				}
			}
		}
		translate(v = [0, 72, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6, r = 14.9);
					}
					union() {
						translate(v = [0, 0, -0.01]) {
							cylinder(h = 6.02, r = 2.75);
						}
					}
				}
			}
		}
		translate(v = [36, 72, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 6, r = 14.8);
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
