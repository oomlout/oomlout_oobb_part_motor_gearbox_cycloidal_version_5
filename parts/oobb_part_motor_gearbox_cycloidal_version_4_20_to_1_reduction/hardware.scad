module hardware_screw_housing() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 3, r = 2.9);
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

module hardware_screw_flange() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 3, r = 2.9);
						translate(v = [0, 0, -12.0]) {
							cylinder(h = 12.0, r = 1.5);
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

module hardware_screw_guide() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 30.0]) {
				difference() {
					union() {
						linear_extrude(height = 4) {
							polygon(points = [[5.77, 0.0], [2.8850000000000002, 4.996966579836211], [-2.8849999999999985, 4.996966579836211], [-5.77, 7.066212031080227e-16], [-2.8850000000000025, -4.99696657983621], [2.884999999999996, -4.996966579836213]]);
						}
					}
					union();
				}
			}
		}
		translate(v = [0, 0, -40.0]) {
			cylinder(h = 40, r = 3.0);
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

module hardware_nut_guide() {
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

module hardware_set_screw() {
difference() {
	union() {
		translate(v = [0, 0, -3.0]) {
			cylinder(h = 3, r = 1.5);
		}
	}
	union();
}

}

module hardware_bearing_eccentric() {
difference() {
	union() {
		translate(v = [0, 0, -2.0]) {
			cylinder(h = 4.0, r = 13.5);
		}
	}
	union() {
		translate(v = [0, 0, -2.0]) {
			cylinder(h = 4.02, r = 10.0);
		}
	}
}

}

module hardware_bearing_shaft() {
difference() {
	union() {
		translate(v = [0, 0, -2.0]) {
			cylinder(h = 4.0, r = 13.5);
		}
	}
	union() {
		translate(v = [0, 0, -2.0]) {
			cylinder(h = 4.02, r = 10.0);
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

module hardware_bearing_guide() {
difference() {
	union() {
		translate(v = [0, 0, -2.0]) {
			cylinder(h = 4.0, r = 7.5);
		}
	}
	union() {
		translate(v = [0, 0, -2.0]) {
			cylinder(h = 4.02, r = 5.0);
		}
	}
}

}

module hardware_coupling() {
difference() {
	union() {
		translate(v = [0, 0, 10.0]) {
			cylinder(h = 2.0, r = 11.0);
		}
		cylinder(h = 10.0, r = 5.0);
	}
	union() {
		translate(v = [0.0, 0.0, 5.0]) {
			rotate(a = [0, 90, 45]) {
				difference() {
					union() {
						cylinder(h = 10.0, r = 1.52);
					}
					union();
				}
			}
		}
		translate(v = [-0.0, 0.0, 5.0]) {
			rotate(a = [0, 90, 135]) {
				difference() {
					union() {
						cylinder(h = 10.0, r = 1.52);
					}
					union();
				}
			}
		}
		translate(v = [0, 0, -0.01]) {
			cylinder(h = 12.02, r = 2.55);
		}
		translate(v = [8.0, 0.0, 10.0]) {
			cylinder(h = 2.02, r = 1.52);
		}
		translate(v = [4.898587196589413e-16, 8.0, 10.0]) {
			cylinder(h = 2.02, r = 1.52);
		}
		translate(v = [-8.0, 9.797174393178826e-16, 10.0]) {
			cylinder(h = 2.02, r = 1.52);
		}
		translate(v = [-1.4695761589768238e-15, -8.0, 10.0]) {
			cylinder(h = 2.02, r = 1.52);
		}
	}
}

}

module hardware_motor() {
difference() {
	union() {
		translate(v = [-21.0, -21.0, -40.0]) {
			cube(size = [42.0, 42.0, 40.0]);
		}
		cylinder(h = 2.0, r = 11.0);
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
module hardware_screw_disc() {
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
							cylinder(h = 6.0, r = 1.5);
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

module hardware_screw_deck() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -1.7]) {
							cylinder(h = 1.7, r1 = 1.5, r2 = 2.9);
						}
						translate(v = [0, 0, -25.0]) {
							cylinder(h = 25.0, r = 1.5);
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

module hardware_screw_post() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -1.7]) {
							cylinder(h = 1.7, r1 = 1.5, r2 = 2.9);
						}
						translate(v = [0, 0, -25.0]) {
							cylinder(h = 25.0, r = 1.5);
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

module hardware_screw_front_hub() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, -1.7]) {
							cylinder(h = 1.7, r1 = 1.5, r2 = 2.9);
						}
						translate(v = [0, 0, -16.0]) {
							cylinder(h = 16.0, r = 1.5);
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
			rotate(a = [0, 0, 30]) {
				difference() {
					union() {
						linear_extrude(height = 4) {
							polygon(points = [[5.77, 0.0], [2.8850000000000002, 4.996966579836211], [-2.8849999999999985, 4.996966579836211], [-5.77, 7.066212031080227e-16], [-2.8850000000000025, -4.99696657983621], [2.884999999999996, -4.996966579836213]]);
						}
					}
					union();
				}
			}
		}
		translate(v = [0, 0, -35.0]) {
			cylinder(h = 35.0, r = 3);
		}
	}
	union();
}

}

module hardware_post() {
difference() {
	union() {
		cylinder(h = 15.5, r = 3.0);
	}
	union() {
		translate(v = [0, 0, -0.01]) {
			cylinder(h = 15.52, r = 1.6);
		}
	}
}

}
