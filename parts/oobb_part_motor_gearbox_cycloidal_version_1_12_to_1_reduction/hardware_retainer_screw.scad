module hardware_retainer_screw() {
difference() {
	union() {
		translate(v = [0, 0, 0]) {
			rotate(a = [0, 0, 0]) {
				difference() {
					union() {
						cylinder(h = 3, r = 2.9);
						translate(v = [0, 0, -16.5]) {
							cylinder(h = 16.5, r = 1.5);
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
