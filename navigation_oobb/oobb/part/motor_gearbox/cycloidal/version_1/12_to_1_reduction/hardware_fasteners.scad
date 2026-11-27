module hardware_screw_rotor() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -1.7]) {
							cylinder(h = 1.7, r1 = 1.5, r2 = 2.9);
						}
						translate(v = [0, 0, -10.0]) {
							cylinder(h = 10, r = 1.5);
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

module hardware_screw_eccentric() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -1.7]) {
							cylinder(h = 1.7, r1 = 1.5, r2 = 2.9);
						}
						translate(v = [0, 0, -10.0]) {
							cylinder(h = 10, r = 1.5);
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

module hardware_screw_hub() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -1.7]) {
							cylinder(h = 1.7, r1 = 1.5, r2 = 2.9);
						}
						translate(v = [0, 0, -13.0]) {
							cylinder(h = 13, r = 1.5);
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

module hardware_screw_carrier() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -1.7]) {
							cylinder(h = 1.7, r1 = 1.5, r2 = 2.9);
						}
						translate(v = [0, 0, -13.0]) {
							cylinder(h = 13, r = 1.5);
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
						translate(v = [0, 0, -43.0]) {
							cylinder(h = 43.0, r = 1.5);
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

module hardware_screw_output() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -0.75]) {
							cylinder(h = 0.75, r1 = 1.25, r2 = 2.25);
						}
						translate(v = [0, 0, -26.0]) {
							cylinder(h = 26.0, r = 1.25);
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

module hardware_nut_m2d5() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						linear_extrude(height = 1.9) {
							polygon(points = [[2.885, 0.0], [1.4425000000000001, 2.4984832899181053], [-1.4424999999999992, 2.4984832899181053], [-2.885, 3.5331060155401137e-16], [-1.4425000000000012, -2.498483289918105], [1.442499999999998, -2.4984832899181066]]);
						}
					}
					union();
				}
			}
		}
	}
	union() {
		translate(v = [0, 0, -1]) {
			cylinder(h = 3.92, r = 1.25);
		}
	}
}

}

module hardware_nut_m6() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						linear_extrude(height = 5) {
							polygon(points = [[5.77, 0.0], [2.8850000000000002, 4.996966579836211], [-2.8849999999999985, 4.996966579836211], [-5.77, 7.066212031080227e-16], [-2.8850000000000025, -4.99696657983621], [2.884999999999996, -4.996966579836213]]);
						}
					}
					union();
				}
			}
		}
	}
	union() {
		translate(v = [0, 0, -1]) {
			cylinder(h = 7.02, r = 3.0);
		}
	}
}

}

module hardware_washer_m6() {
difference() {
	union() {
		cylinder(h = 1.6, r = 6);
	}
	union() {
		translate(v = [0, 0, -1]) {
			cylinder(h = 3.62, r = 3.2);
		}
	}
}

}
