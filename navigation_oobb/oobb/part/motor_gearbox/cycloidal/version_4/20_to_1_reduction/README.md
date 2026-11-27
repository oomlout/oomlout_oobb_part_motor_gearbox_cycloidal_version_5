# Version 4: captured 6700 bearings / raised 6810 casing

Generated through working_oomp_populate -> working_oomp -> working_scad.
Edit populate overrides or gearbox/captured.py; defaults accept **kwargs.

20:1, 19 lobes, eccentricity 1.85 mm.
Casing outside diameter 92.2 mm; cover height 67 mm above motor face.
The flange remains UP at the 24 mm shaft tip. Rear 6810 sits above the motor.

15 printed parts. Each disc has two 3.5 mm halves capturing six
6700 bearings (10 x 15 x 4). Their outer races move with the disc; their inner
bores orbit smooth M6 shanks, leaving 0.15 mm radial clearance.
The two eccentric bearings and the front shaft bearing are 6704 (20 x 27 x 4).
Both casing bearings are 6810 (50 x 65 x 7).
The central and guide-bearing outer races have 0.10 mm nominal
radial separation. Their seat pockets merge; no plastic wall separates them at
the bearing midplane. The retaining lips on the two disc faces hold the bearing pack.

Four M3x35 SOCKET CAP screws close the casing. The nuts remain
at the bottom (7 mm above motor face). Screw heads sit at
42 mm, inside long cover bosses with OOBB clearance="top".
Use a straight hex key down the top channels. The maximum specified casing
screw length is 35 mm; the cover's bosses descend into matching casing sockets
so the recessed heads still clamp the cover. Overall cover height is unchanged.

The output casing has THREE pieces: output_base, output_casing (the lobe ring),
and output_cover. The joint is at 13.4 mm above the motor face.
The 8.9 mm base prints joint-face down with its rear-bearing
pocket upward; flip it for assembly. The 51.6 mm lobe ring
prints upright. The four existing M3x35 screws pass through all three parts,
with the captive nuts retained in the base. No additional fasteners are needed.
The flat joint is located by the four screw holes and clamped between the bearing
holder and cover; keep the ring concentric while tightening the screws evenly.

The six M6x40 guides need smooth shanks at least
15.7 mm long below the head.
Use partially threaded bolts; threads must not enter either bearing bore.
Three steel spacers, 6 OD x 3.2 ID x 15.5 mm, maintain carrier spacing.
They pass through separate oversized orbit-clearance holes, not the 6700 bores.
No inner-race spacers clamp the moving guide bearings.

Assembly:
1. Print fit coupons first: 6700 seats, sandwich lips, 6704 journals/seats,
   6810 seats, NEMA mount, coupling collar and shaft key.
2. Load the three motor-faceplate M3 nuts underneath. Fix faceplate to motor
   with four M3x6 countersunk screws. Fit rear 6810 from above.
3. Load the collar's TWO M3 nuts through its straight outward-facing slots.
   Put collar and flange-up coupling on the shaft. Tighten grub screws now,
   with the rear deck and casing absent (grub_access.scad shows the tools).
4. Load casing-base nuts from below, lower the base onto the rear 6810,
   then lower the lobe ring onto its flat joint face, aligning all four screw holes.
   Load rear-carrier M6 and post M3 nuts from underneath, then fit the rear
   carrier with three M3x25 screws. Its central bore clears the coupling/collar.
5. Load the central M6 nut underneath the coupling drive plate; place it on the
   coupling flange and install two M3x12 socket screws into the collar nuts.
   Lower the lower wiggle shaft onto the drive plate's key. Its uninterrupted
   bearing journal has no coupling-screw access slots through it.
6. Assemble each disc around six 6700s and one 6704 on the bench. Use three
   M3x6 countersunk screws/nuts per disc; upper halves print pocket-up and flip
   for assembly. Keep the matching A/B half pairs and common XY orientation.
7. Lower disc A over the lower shaft from above. Fit disc B onto the upper
   shaft from below, then lower that unit onto the keyed lower shaft.
8. Insert three steel carrier spacers through their separate tracks. Fit front
   carrier, three M3x25 post screws and six M6x40 guide bolts. Fit the M6x35
   central shaft bolt; its head is recessed inside the front journal.
9. Load the front bearing hub's three nuts into the underside of the front
   carrier BEFORE step 8. Fit hub and front 6704 with three M3x16 screws.
   Lower the front 6810 over the hub, then fit the output cover and four
   M3x35 socket-cap casing screws through the deep top-access channels.
   Turn by hand before motor power.

3dpr.scad/.stl contains all printed pieces. Individual files use the part names
in part_names.md. exploded.scad/.png is annotated; animation.scad/.gif/.mp4 shows
the two orbiting bearing rows and all hardware. *_installation_check.scad files
render only interference along the stated assembly sequence.

This is a narrower, taller alternative to the preserved 6814 layout. CAD checks
verify nominal geometry; printed tolerances, bearing retention and load capacity
still need the supplied coupons and a physical prototype. The 6700 retaining
lips overlap the outermost 0.5 mm of the bearing; confirm they clear the shields
of your actual bearings. Do not clamp a shield or inner race with the disc halves.
