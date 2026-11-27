$fn=96;
difference() {
	union() {
		cylinder(h = 2.0, r = 7.0);
		cylinder(h = 27.5, r = 4.8);
	}
	union() {
		translate(v = [0, 0, 67.0]) {
			rotate(a = [180, 0, 0]) {
				difference() {
					union() {
						translate(v = [0, 0, 42.0]) {
							rotate(a = [0, 0, 0]) {
								difference() {
									union() {
										translate(v = [0, 0, -35.0]) {
											cylinder(h = 35.0, r = 1.5);
										}
										cylinder(h = 253.2, r = 3.0);
										translate(v = [0, 0, -35.0]) {
											cylinder(h = 35.0, r = 1.8);
										}
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
		}
	}
}
