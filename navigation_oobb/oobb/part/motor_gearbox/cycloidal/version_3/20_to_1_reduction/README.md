# Version 3: 20:1 opposed-disc gearbox

Generated through working_oomp_populate -> working_oomp -> working_scad.
Edit the Python source/populate options, then regenerate.

- 3dpr.scad / 3dpr.stl: 9 printed pieces, one of each.
- Named SCAD/STL files: individual printable pieces. The outer casing is the output; the six guide sleeves and both pin supports are fixed to the motor mount.
- animation.gif / animation.mp4: rendered exploded motion with motor, coupling,
  six bearings, sleeves, screws, nuts and the M5 hub joining bolt.
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
24 mm shaft, 40 mm body and 12 mm-long flanged 5 mm coupling. Check your motor drawing.
The M3x6 countersunk mount screws engage 2 mm past the 4 mm base.
Load the six guide nuts from the underside of the motor faceplate before the bearing and motor.
The hexagonal loading pockets retain the nuts against rotation.
The 6706 drive bearing sits on the motor face, retained by the mount lip.
The wide flange faces downward, with the narrow barrel ending at the motor shaft tip. Two opposite vertical M3x8 socket screws fasten it
into captive nuts in the lower printed hub. Slide both nuts straight inward through the radial
side slots before fitting the flange screws. The pockets use OOBB clearance="right" facing outward;
the hex is rotated independently to keep a flat toward the barrel. flange_nut_loading.scad shows insertion;
flange_nut_installation_check.scad checks the complete swept paths. The split hub has a one-way D key
and an M5x30 joining bolt. Before installing the rear pin carrier and casing, rotate the input 0 degrees
from the assembly index to use the two radial access holes. Grub-screw access is an assembly-stage operation; remove the casing and rear carrier for later service.
Print fit_coupling_flange.scad, fit_drive_bearings.scad and fit_hub_key.scad first.
motor_drive.scad shows the compact interface; grub_access_check.scad tests tool access.
Printed rotating casing contacts replace loose metal ring rods. Grease and material
choice need physical testing; digital clearance does not establish torque or life.
