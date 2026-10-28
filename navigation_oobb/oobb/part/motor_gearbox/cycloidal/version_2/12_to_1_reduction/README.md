# Version 2: 12:1 opposed-disc gearbox

Generated through working_oomp_populate -> working_oomp -> working_scad.
Edit the Python source/populate options, then regenerate.

- 3dpr.scad / 3dpr.stl: eight printed pieces, one of each.
- Named SCAD/STL files: individual printable pieces. The outer casing is the output; the six guide sleeves and both pin supports are fixed to the motor mount.
- animation.gif / animation.mp4: rendered exploded motion with motor, coupling,
  six bearings, sleeves, screws, nuts and M5 input axle.
- animation.scad: interactive motion; View > Animate, FPS 12, Steps 192.
  Set explode=0 to assemble; show_housing=false exposes the working mechanism.
- exploded.scad, section.scad, assembly.scad: inspection examples.
- fit_check.scad: intersection-only moving fit check; a passing pose is empty.
- fit_*_bearings.scad: three seat allowances 0 / 0.10 / 0.20 mm radial.
- fit_m5_axle.scad, fit_nema17_mount.scad: small interface tests before the full print.
- gearbox.json: all resolved parameters, BOM, layout and coupon counts.
- validation.json: rendered mesh, bore and moving-clearance checks.

See the project README for assembly order and hardware assumptions. NEMA17 describes
face dimensions, not one universal shaft length: the default preview assumes a
24 mm shaft, 40 mm body and 25 mm-long 5-to-5 mm coupling. Check your motor drawing.
The M3x6 countersunk mount screws engage 2 mm past the 4 mm base.
The M5 axle uses a radial M3 set screw and captive nut in the central hub boss.
Printed rotating casing contacts replace loose metal ring rods. Grease and material
choice need physical testing; digital clearance does not establish torque or life.
