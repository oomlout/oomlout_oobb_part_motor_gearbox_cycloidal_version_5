// Generated via working_scad. Edit populate/builders, not this file.
$fn=96;
module motor_mount(){
difference() {
	union() {
		hull() {
			translate(v = [-47.0, 47.0, 0]) {
				cylinder(h = 4.0, r = 5);
			}
			translate(v = [47.0, 47.0, 0]) {
				cylinder(h = 4.0, r = 5);
			}
			translate(v = [-47.0, -47.0, 0]) {
				cylinder(h = 4.0, r = 5);
			}
			translate(v = [47.0, -47.0, 0]) {
				cylinder(h = 4.0, r = 5);
			}
		}
		cylinder(h = 14.0, r = 24.9);
		translate(v = [0, 0, 4.0]) {
			cylinder(h = 0.3, r = 26.5);
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
		translate(v = [16.5, 0.0, 2.8]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [-1.75, -3.25, -3.1999999999999997]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, -3.4999999999999996]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
						translate(v = [-1.75, -3.25, 0.0]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, 0.3]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
						translate(v = [0, 0, -2.9]) {
							linear_extrude(height = 2.9) {
								polygon(points = [[3.4619999999999997, 0.0], [1.7310000000000003, 2.9981799479017264], [-1.7309999999999992, 2.9981799479017264], [-3.4619999999999997, 4.2397272186481365e-16], [-1.7310000000000014, -2.998179947901726], [1.7309999999999977, -2.9981799479017277]]);
							}
						}
						translate(v = [-1.75, -3.25, -3.1999999999999997]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, -3.4999999999999996]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
						translate(v = [-1.75, -3.25, 0.0]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, 0.3]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
						translate(v = [-1.75, -3.25, -3.1999999999999997]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, -3.4999999999999996]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
						translate(v = [-1.75, -3.25, 0.0]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, 0.3]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
					}
					union();
				}
			}
		}
		translate(v = [-8.249999999999996, 14.289419162443238, 2.8]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [-1.75, -3.25, -3.1999999999999997]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, -3.4999999999999996]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
						translate(v = [-1.75, -3.25, 0.0]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, 0.3]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
						translate(v = [0, 0, -2.9]) {
							linear_extrude(height = 2.9) {
								polygon(points = [[3.4619999999999997, 0.0], [1.7310000000000003, 2.9981799479017264], [-1.7309999999999992, 2.9981799479017264], [-3.4619999999999997, 4.2397272186481365e-16], [-1.7310000000000014, -2.998179947901726], [1.7309999999999977, -2.9981799479017277]]);
							}
						}
						translate(v = [-1.75, -3.25, -3.1999999999999997]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, -3.4999999999999996]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
						translate(v = [-1.75, -3.25, 0.0]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, 0.3]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
						translate(v = [-1.75, -3.25, -3.1999999999999997]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, -3.4999999999999996]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
						translate(v = [-1.75, -3.25, 0.0]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, 0.3]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
					}
					union();
				}
			}
		}
		translate(v = [-8.250000000000007, -14.289419162443235, 2.8]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [-1.75, -3.25, -3.1999999999999997]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, -3.4999999999999996]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
						translate(v = [-1.75, -3.25, 0.0]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, 0.3]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
						translate(v = [0, 0, -2.9]) {
							linear_extrude(height = 2.9) {
								polygon(points = [[3.4619999999999997, 0.0], [1.7310000000000003, 2.9981799479017264], [-1.7309999999999992, 2.9981799479017264], [-3.4619999999999997, 4.2397272186481365e-16], [-1.7310000000000014, -2.998179947901726], [1.7309999999999977, -2.9981799479017277]]);
							}
						}
						translate(v = [-1.75, -3.25, -3.1999999999999997]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, -3.4999999999999996]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
						translate(v = [-1.75, -3.25, 0.0]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, 0.3]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
						translate(v = [-1.75, -3.25, -3.1999999999999997]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, -3.4999999999999996]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
						translate(v = [-1.75, -3.25, 0.0]) {
							cube(size = [3.5, 6.5, 0.3]);
						}
						translate(v = [-1.75, -1.75, 0.3]) {
							cube(size = [3.5, 3.5, 0.3]);
						}
					}
					union();
				}
			}
		}
		translate(v = [0, 0, -0.01]) {
			cylinder(h = 14.02, r = 11.2);
		}
		translate(v = [-45.0, -45.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [-45.0, -30.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [-45.0, -15.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [-45.0, 0.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [-45.0, 15.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [-45.0, 30.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [-45.0, 45.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [-30.0, -45.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [-30.0, 45.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [-15.0, -45.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [-15.0, 45.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [0.0, -45.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [0.0, 45.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [15.0, -45.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [15.0, 45.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [30.0, -45.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [30.0, 45.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [45.0, -45.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [45.0, -30.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [45.0, -15.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [45.0, 0.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [45.0, 15.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [45.0, 30.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [45.0, 45.0, -100.0]) {
			cylinder(h = 200, r = 3.25);
		}
		translate(v = [-45.0, -45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-45.0, -37.5, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-45.0, -30.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-45.0, -22.5, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-45.0, -15.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-45.0, -7.5, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-45.0, 0.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-45.0, 7.5, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-45.0, 15.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-45.0, 22.5, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-45.0, 30.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-45.0, 37.5, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-45.0, 45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-37.5, -45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-37.5, 45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-30.0, -45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-30.0, 45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-22.5, -45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-22.5, 45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-15.0, -45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-15.0, 45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-7.5, -45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [-7.5, 45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [0.0, -45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [0.0, 45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [7.5, -45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [7.5, 45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [15.0, -45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [15.0, 45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [22.5, -45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [22.5, 45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [30.0, -45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [30.0, 45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [37.5, -45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [37.5, 45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [45.0, -45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [45.0, -37.5, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [45.0, -30.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [45.0, -22.5, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [45.0, -15.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [45.0, -7.5, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [45.0, 0.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [45.0, 7.5, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [45.0, 15.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [45.0, 22.5, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [45.0, 30.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [45.0, 37.5, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [45.0, 45.0, -100.0]) {
			cylinder(h = 200, r = 1.8);
		}
		translate(v = [15.5, 15.5, 4.0]) {
			cylinder(h = 10.12, r = 3);
		}
		translate(v = [-15.5, 15.5, 4.0]) {
			cylinder(h = 10.12, r = 3);
		}
		translate(v = [-15.5, -15.5, 4.0]) {
			cylinder(h = 10.12, r = 3);
		}
		translate(v = [15.5, -15.5, 4.0]) {
			cylinder(h = 10.12, r = 3);
		}
		translate(v = [16.5, 0.0, -0.01]) {
			cylinder(h = 14.02, r = 1.8);
		}
		translate(v = [-8.249999999999996, 14.289419162443238, -0.01]) {
			cylinder(h = 14.02, r = 1.8);
		}
		translate(v = [-8.250000000000007, -14.289419162443235, -0.01]) {
			cylinder(h = 14.02, r = 1.8);
		}
		translate(v = [18.27313601985166, 10.549999999999999, 9.900000000000002]) {
			cylinder(h = 4.219999999999997, r = 3.25);
		}
		translate(v = [1.2920023731004577e-15, 21.1, 9.900000000000002]) {
			cylinder(h = 4.219999999999997, r = 3.25);
		}
		translate(v = [-18.27313601985166, 10.549999999999999, 9.900000000000002]) {
			cylinder(h = 4.219999999999997, r = 3.25);
		}
		translate(v = [-18.273136019851655, -10.550000000000002, 9.900000000000002]) {
			cylinder(h = 4.219999999999997, r = 3.25);
		}
		translate(v = [-3.876007119301373e-15, -21.1, 9.900000000000002]) {
			cylinder(h = 4.219999999999997, r = 3.25);
		}
		translate(v = [18.273136019851652, -10.55000000000001, 9.900000000000002]) {
			cylinder(h = 4.219999999999997, r = 3.25);
		}
	}
}

}
motor_mount();
