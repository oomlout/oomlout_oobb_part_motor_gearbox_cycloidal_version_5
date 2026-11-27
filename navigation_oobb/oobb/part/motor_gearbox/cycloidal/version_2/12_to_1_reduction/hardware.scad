module hardware_screw_guide() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -1.7]) {
							cylinder(h = 1.7, r1 = 1.5, r2 = 2.9);
						}
						translate(v = [0, 0, -55.0]) {
							cylinder(h = 55, r = 1.5);
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

module hardware_screw_housing() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -1.7]) {
							cylinder(h = 1.7, r1 = 1.5, r2 = 2.9);
						}
						translate(v = [0, 0, -55.0]) {
							cylinder(h = 55, r = 1.5);
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

module hardware_screw_motor() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -1.7]) {
							cylinder(h = 1.7, r1 = 1.5, r2 = 2.9);
						}
						translate(v = [0, 0, -6.0]) {
							cylinder(h = 6, r = 1.5);
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

module hardware_nut_m3() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						linear_extrude(height = 2.5) {
							polygon(points = [[3.1734999999999998, 0.0], [1.5867500000000003, 2.7483316189099156], [-1.5867499999999992, 2.748331618909916], [-3.1734999999999998, 3.886416617094125e-16], [-1.5867500000000012, -2.748331618909915], [1.5867499999999977, -2.748331618909917]]);
						}
					}
					union();
				}
			}
		}
	}
	union() {
		translate(v = [0, 0, -1]) {
			cylinder(h = 4.52, r = 1.5);
		}
	}
}

}

module hardware_nut_m5() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						linear_extrude(height = 4) {
							polygon(points = [[4.616, 0.0], [2.3080000000000003, 3.997573263868968], [-2.307999999999999, 3.997573263868969], [-4.616, 5.652969624864182e-16], [-2.308000000000002, -3.9975732638689676], [2.3079999999999967, -3.9975732638689703]]);
						}
					}
					union();
				}
			}
		}
	}
	union() {
		translate(v = [0, 0, -1]) {
			cylinder(h = 6.02, r = 2.5);
		}
	}
}

}

module hardware_washer_m5() {
difference() {
	union() {
		cylinder(h = 1.5, r = 6.0);
	}
	union() {
		translate(v = [0, 0, -1]) {
			cylinder(h = 3.52, r = 2.7);
		}
	}
}

}

module hardware_sleeve() {
difference() {
	union() {
		cylinder(h = 22.0, r = 3.0);
	}
	union() {
		translate(v = [0, 0, -0.01]) {
			cylinder(h = 22.02, r = 1.6);
		}
	}
}

}

module hardware_axle() {
difference() {
	union() {
		cylinder(h = 71.5, r = 2.5);
	}
	union();
}

}

module hardware_set_screw() {
difference() {
	union() {
		translate(v = [0, 0, -6.0]) {
			cylinder(h = 6, r = 1.5);
		}
	}
	union();
}

}

module hardware_bearing_eccentric() {
difference() {
	union() {
		translate(v = [0, 0, -2.5]) {
			cylinder(h = 5.0, r = 12.0);
		}
	}
	union() {
		translate(v = [0, 0, -2.5]) {
			cylinder(h = 5.02, r = 7.5);
		}
	}
}

}

module hardware_bearing_shaft() {
difference() {
	union() {
		translate(v = [0, 0, -3.0]) {
			cylinder(h = 6.0, r = 11.0);
		}
	}
	union() {
		translate(v = [0, 0, -3.0]) {
			cylinder(h = 6.02, r = 5.0);
		}
	}
}

}

module hardware_bearing_output() {
difference() {
	union() {
		translate(v = [0, 0, -3.5]) {
			cylinder(h = 7.0, r = 32.5);
		}
	}
	union() {
		translate(v = [0, 0, -3.5]) {
			cylinder(h = 7.02, r = 25.0);
		}
	}
}

}

module hardware_coupling() {
difference() {
	union() {
		cylinder(h = 25.0, r = 9.5);
	}
	union() {
		translate(v = [0, 0, -0.01]) {
			cylinder(h = 25.02, r = 2.55);
		}
	}
}

}

module hardware_motor() {
difference() {
	union() {
		translate(v = [-21.0, -21.0, -40.0]) {
			cube(size = [42, 42, 40.0]);
		}
		cylinder(h = 2, r = 11);
		cylinder(h = 24.0, r = 2.5);
	}
	union() {
		translate(v = [15.5, 15.5, -3]) {
			cylinder(h = 3.02, r = 1.5);
		}
		translate(v = [-15.5, 15.5, -3]) {
			cylinder(h = 3.02, r = 1.5);
		}
		translate(v = [-15.5, -15.5, -3]) {
			cylinder(h = 3.02, r = 1.5);
		}
		translate(v = [15.5, -15.5, -3]) {
			cylinder(h = 3.02, r = 1.5);
		}
	}
}

}
