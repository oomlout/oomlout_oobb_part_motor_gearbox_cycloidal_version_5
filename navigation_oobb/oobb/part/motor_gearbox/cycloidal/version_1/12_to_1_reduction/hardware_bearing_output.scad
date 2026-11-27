module hardware_bearing_output() {
difference() {
	union() {
		translate(v = [0, 0, -3.5]) {
			union() {
				difference() {
					cylinder(h = 7.0, r = 32.5);
					cylinder(h = 7.0, r = 25.0);
				}
				difference() {
					translate(v = [0, 0, -50]) {
						cylinder(h = 100, r = 28.75);
					}
					translate(v = [0, 0, -50]) {
						cylinder(h = 100, r = 28.75);
					}
				}
			}
		}
	}
	union();
}

}
