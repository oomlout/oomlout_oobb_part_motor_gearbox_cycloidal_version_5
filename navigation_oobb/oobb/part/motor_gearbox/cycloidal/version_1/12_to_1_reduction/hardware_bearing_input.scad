module hardware_bearing_input() {
difference() {
	union() {
		translate(v = [0, 0, -2.0]) {
			union() {
				difference() {
					cylinder(h = 4.0, r = 16.0);
					cylinder(h = 4.0, r = 12.5);
				}
				difference() {
					translate(v = [0, 0, -50]) {
						cylinder(h = 100, r = 14.25);
					}
					translate(v = [0, 0, -50]) {
						cylinder(h = 100, r = 14.25);
					}
				}
			}
		}
	}
	union();
}

}
