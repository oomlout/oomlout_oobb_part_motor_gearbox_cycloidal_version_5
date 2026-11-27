# Editing and assembly

Open [gearbox_controls.solidcraft](gearbox_controls.solidcraft) and edit its favourite parameters. The ring holes, printed spacers, connected ring and cycloid profiles follow `reduction`. `contact_radius` is the spacer outside radius. The upper stationary carrier takes the screw heads and the lower one takes M3 nuts. Each 6810 outer race seats between a flat OOBB plate and a separate retaining cylinder. The lobe screws enter the upper cylinder and the nuts load from the lower cylinder. Print each piece flat with its bearing pocket opening upwards.

The rotating shaft now takes an attachment at either end using four M3 holes at 7.5 mm radius. Its nominal Ø6.50 mm central passage remains open. The eight discs make three shapes: E end journal, N mount nut carrier, C eccentric half. The C offsets follow eccentricity. At input angle zero the E mounting cross is 45 degrees to the housing; turn the input to -45 degrees to align the two grids. At the default Ø78 mm contact pitch change reduction and offset together for the checked 15:1 / 2 mm combination. Both sleeve sets and the connected ring use Ø7 mm contacts. Set middle_length to 16 mm (default) or 20 mm. The two 7 mm discs and their 0.5 mm running gap need more than 12 mm. The 16 mm setting leaves 0.75 mm end clearance on each side.

Follow the [layered assembly order](ASSEMBLY.md) and the two illustrated pages, [starting layers](assembly_lower.png) and [finishing layers](assembly_upper.png). Start with the native upper/socket-cap end facing down and all 28 long screws standing upward. The central E and large 6810 inner carrier share the first layer. Lower the bearings, concentric plates and spacers over the screws, then Disc B and Disc A around their split cams. Secure one shaft tie before withdrawing and reversing the temporary tie at the end.

Fit your drive to the rotating four-hole pattern. The rotating E face sits 0.80 mm below the stationary carrier face: use a central boss that reaches E and keeps the broad face of the attachment clear of the stationary plate. Measured from E, the bottom of the mounting nut pocket is 11.2 mm in, and the first cam is 11.7 mm in. Select the mounting screw length after allowing for your attachment thickness. Keep the M6 passage open and check the mechanism turns freely by hand before applying load.

The print plate includes both outer contact options. In the native assembly the loose sleeves are visible. To preview the alternative, show connected_contact_ring and hide the printed_contact_sleeve bodies. Keep the six printed_drive_sleeve bodies visible. The native print snapshot hides it and the print STL contains only plastic. To export a saved edit use `python action_export_native.py --design "<path to your saved master>"`. Use [the bearing and sleeve upgrade](bearing_reprint/README.md) when upgrading the preceding V2 assembly. The three shaft shapes print flat, with the E screw and nut mouths on the bed and the N pockets facing up. For the supplied default, print gearbox_plate/3dpr.stl, disc_plate/3dpr.stl and outer_housing_plate/3dpr.stl for a 240 mm bed. The four-piece outer_housing_reprint/3dpr.stl upgrades just the housing. The parent 3dpr.stl is the complete wide layout.

The default housing uses a 7 × 7 OOBB square on each end. The spare lower-row plate beside the stack fits either cylinder. Its upper half follows the ring and its bottom edge extends by one 15 mm row. Use the Alternative output plate browser group to toggle it. The 15 mm M6 grid and 7.5 mm M3 grid stay centered on the shaft, with M6 at shared positions. Both shapes omit stations that would foul a mounting nut against the bearing cylinder.

Edit `pitch` (ring screw center radius) or `contact_radius` (spacer radius) to change the ring diameter. The flange selects an odd OOBB size through 9 × 9. Mounting holes become available or drop out as the cylinder clears them, and the spare moves sideways with the plate size. The 6810 and the existing gear geometry also constrain the usable pitch.

Shaft controls in the native Parameters menu:

| Parameter | Meaning at the supplied setting |
|---|---|
| `eccentricity` | 1.50 mm journal offset. Both C pairs follow it in opposite directions. |
| `shaft_open_bore` | **Radius**, 3.25 mm; the continuous center passage is Ø6.50 mm. |
| `shaft_tie_pitch` | Radius to each opposed M3 tie, 6.52 mm. The two tie axes are 13.04 mm apart. |
| `shaft_tie_bore` | Tie clearance radius, 1.70 mm (Ø3.40 mm). |
| `shaft_head_depth` / `shaft_nut_depth` | 3.30 / 3.00 mm from each outside face. Changes affect nut engagement and the recess floor. |
| `shaft_tie_length` | 35 mm under the head. End depth adjusts with the spacer length to preserve the grip. |

The end journals, carrier lengths and cam shoulder depths are derived dimensions. With these shallow webs, check the sliced end journal and recheck fit after changing any of the shaft recesses, bore or tie pitch.

Each outer carrier cap pilots the full 7 mm width of the 6810. The flat carrier core meets the end of that journal at the bearing face and closes the inner race. The OOBB plate and the outside cylinder lip retain the outer race. Insert each E journal from the outside through its centered 6704 and seat its wide flange. N bears against the other side. Seat each sleeve in both shallow guide sockets. See the [installation drawing and fit gauge](bearing_reprint/README.md) before closing the gearbox.

The default guide pattern is three opposing pairs. To move a pair in the master, edit `guide_pair_a`, `guide_pair_b` or `guide_pair_c` in degrees; its opposite stays 180° away. The screw seats, shafts, sleeves and matching guide tracks follow. The OOBB mounting grid stays fixed. After an angle edit, check the webs to the nut pockets and the disc clamps before reprinting. The [fit report](fit_verification.json) records the measured webs for the supplied layout.

The plain circular OOBB plate is a third interchangeable option: **134 mm diameter x 3 mm thick**. It has the OOBB M6/M3 grid and straight lobe-screw bores, with no countersinks or NEMA17 joiner holes. One copy is included in the main 3dpr layout. Use it in place of either square plate; print twice for two circular ends. [Circular plate only](circular_plate/3dpr.scad) · [Individual STL](native_parts/output_circle_plate.stl) · [All options in 3dpr](3dpr.scad). It is parked beside the assembly in Alternative output plate. `circle_grid_radius` and `circle_plate_radius` follow the ring size through native expressions.

## Browser visibility

Click the eye beside **Hardware** to hide or show all purchased parts. Expand it for separate **Bearings** and **Fasteners** controls. Fasteners includes the screws, their socket heads and all nuts.

**Top plate and carrier** and **Bottom plate and carrier** each contain the corresponding OOBB output plate, 6810 retaining cylinder and both halves of its stationary carrier. **Alternative output plate** contains the lower-row flange and, in the current manual model, the plain circular OOBB plate parked beside the main assembly. Toggle either child individually. **Disc A** is the lower cycloid and **Disc B** is the upper one. Each contains its two printed halves. Their bearings and clamps are in Hardware.

**Input shaft stack** contains two identical E end journals, two N mount carriers and four C eccentric halves. **Inner guide sleeves** and **Outer ring contacts** control the printed spacers. Expand Outer ring contacts to switch between the loose sleeves and the optional connected ring. The loose sleeves are selected in the assembly. The print view includes both options.
