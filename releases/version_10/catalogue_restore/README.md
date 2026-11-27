<!-- oobb-presentation:start -->
# OOBB cycloidal gearbox

AI-generated images and instructions. Errors possible.

## Summary

This project provides a 3D-printable cycloidal reduction gearbox for OOBB mechanisms. Fix the teal outer ring, drive the central shaft and take the reduced-speed output from the black middle ring. The repository includes printable parts, editable SolidCraft CAD and illustrated assembly instructions.

This is an entirely AI-generated coding project. The generated outputs are included and usually work, but the main purpose of publishing it is to give others a starting point for modifying the project with their own AI tools.

![AI-generated CAD render: OOBB gearbox with the teal outer ring fixed, yellow E input and black middle ring output](presentation/images/in-use.png)

## Details

The current build is **simple double-bearing V2**, shown with 104 x 104 x 3 mm square outer mounting plates. It uses two 6810 casing bearings, four 6704 bearings, twenty outer contacts and six inner guides. The standard sleeve length is 16 mm, eccentricity is 1.5 mm and the shaft has a 6.50 mm centre passage. Fix the teal outer ring and drive the yellow E journal. The black middle ring is the output; with twenty outer contacts and nineteen disc lobes, this arrangement gives a nominal **19:1 reduction**, opposite to the input direction.

![AI-generated CAD render: assembled printed gearbox parts with all purchased hardware hidden](presentation/images/printed-assembly.png)

Print the [gearbox plate](parts/oobb_part_motor_gearbox_cycloidal_simple_double_bearing_version_2_20_to_1_reduction/gearbox_plate/3dpr.stl), [disc and shaft plate](parts/oobb_part_motor_gearbox_cycloidal_simple_double_bearing_version_2_20_to_1_reduction/disc_plate/3dpr.stl) and [outer housing plate](parts/oobb_part_motor_gearbox_cycloidal_simple_double_bearing_version_2_20_to_1_reduction/outer_housing_plate/3dpr.stl). Select the two square plates and twenty loose contact sleeves for the illustrated build; the supplied layouts also contain the connected-ring and lower-row alternatives. Use either ring option, with six separate inner guide sleeves.

A [plain circular OOBB plate](parts/oobb_part_motor_gearbox_cycloidal_simple_double_bearing_version_2_20_to_1_reduction/circular_plate/3dpr.scad) is also available: 134 mm diameter, 3 mm thick, with M6/M3 mounting holes and no countersinks. One copy is included in the [main 3dpr layout](parts/oobb_part_motor_gearbox_cycloidal_simple_double_bearing_version_2_20_to_1_reduction/3dpr.scad); substitute it for either square plate, or print two for circular plates at both ends.

[Individual STLs](parts/oobb_part_motor_gearbox_cycloidal_simple_double_bearing_version_2_20_to_1_reduction/native_parts/) Â· [Editable master](simple_double_bearing_version_2.solidcraft) Â· [Assembly PDF](presentation/assembly-guide.pdf) Â· [Complete parts CSV](presentation/parts.csv) Â· [Build notes and older versions](presentation/README.md)

## Parts

![AI-generated CAD render: labelled exploded fixed outer ring, output carrier and discs, and eight-piece input shaft](presentation/images/exploded.png)

CAD render of the three coaxial groups. Teal: fixed outer housing, cycloids and N carriers. Black: output carriers and C cams. Yellow: all sleeves and E journals. Bearings and fasteners retain metal finishes.

Complete hardware list for **one square-flange gearbox with 16 mm sleeves and all captive mounting nuts installed**. External drive, frame, load and their attachment screws are excluded.

| Ref. | Part | Specification | Qty. | OOMP ID | Code |
| --- | --- | --- | ---: | --- | --- |
| H1 | [6810 bearing](https://github.com/oomlout/oomlout_oomp_version_1_messy/tree/main/parts/hardware_bearing_6800_series_6810_size_50_mm_id_65_mm_od_7_mm_depth) | 50 x 65 x 7 mm | 2 | [`hardware_bearing_6800_series_6810_size_50_mm_id_65_mm_od_7_mm_depth`](https://github.com/oomlout/oomlout_oomp_version_1_messy/tree/main/parts/hardware_bearing_6800_series_6810_size_50_mm_id_65_mm_od_7_mm_depth) | [7xku1](https://oom.lt/a/7xku1) |
| H2 | [6704 bearing](https://github.com/oomlout/oomlout_oomp_version_1_messy/tree/main/parts/hardware_bearing_6700_series_6704_size_20_mm_id_27_mm_od_4_mm_depth) | 20 x 27 x 4 mm | 4 | [`hardware_bearing_6700_series_6704_size_20_mm_id_27_mm_od_4_mm_depth`](https://github.com/oomlout/oomlout_oomp_version_1_messy/tree/main/parts/hardware_bearing_6700_series_6704_size_20_mm_id_27_mm_od_4_mm_depth) | [4y780](https://oom.lt/a/4y780) |
| H3 | [M3 x 30 socket-cap screw](https://github.com/oomlout/oomp_hardware_screw_version_5/tree/main/parts/hardware_screw_socket_cap_hex_head_black_m3_diameter_30_mm_length) | 20 outer ring screws; 2.5 mm hex key | 20 | [`hardware_screw_socket_cap_hex_head_black_m3_diameter_30_mm_length`](https://github.com/oomlout/oomp_hardware_screw_version_5/tree/main/parts/hardware_screw_socket_cap_hex_head_black_m3_diameter_30_mm_length) | [4x6wf](https://oom.lt/a/4x6wf) |
| H4 | [M3 x 35 socket-cap screw](https://github.com/oomlout/oomp_hardware_screw_version_5/tree/main/parts/hardware_screw_socket_cap_hex_head_black_m3_diameter_35_mm_length) | 6 guides and 2 shaft ties; 2.5 mm key | 8 | [`hardware_screw_socket_cap_hex_head_black_m3_diameter_35_mm_length`](https://github.com/oomlout/oomp_hardware_screw_version_5/tree/main/parts/hardware_screw_socket_cap_hex_head_black_m3_diameter_35_mm_length) | [22vya](https://oom.lt/a/22vya) |
| H5 | [M3 x 6 countersunk screw](https://github.com/oomlout/oomp_hardware_screw_version_5/tree/main/parts/hardware_screw_countersunk_hex_head_black_m3_diameter_6_mm_length) | 6 disc clamps; 2 mm hex key | 6 | [`hardware_screw_countersunk_hex_head_black_m3_diameter_6_mm_length`](https://github.com/oomlout/oomp_hardware_screw_version_5/tree/main/parts/hardware_screw_countersunk_hex_head_black_m3_diameter_6_mm_length) | [61zh8](https://oom.lt/a/61zh8) |
| H6 | [M3 hex nut](https://github.com/oomlout/oomlout_oomp_version_1_messy/tree/main/parts/hardware_nut_m3) | 20 ring + 6 guides + 2 ties + 6 discs + 16 carrier + 8 N | 58 | [`hardware_nut_m3`](https://github.com/oomlout/oomlout_oomp_version_1_messy/tree/main/parts/hardware_nut_m3) | [3vb5b](https://oom.lt/a/3vb5b) |

The 58 M3 nuts include eight optional N attachment nuts; omit only the attachment nuts you will not use. The 20 mm sleeve option needs twenty M3 x 35 outer screws in place of the M3 x 30 screws. Guide screws and shaft ties remain M3 x 35.

## Assembly

1. **Prepare both cycloids.** Capture one 6704 between each disc's halves. Fit three M3 nuts and three M3 x 6 countersunk screws per disc; seat the heads flush before stacking.

   [![AI-generated CAD illustration: prepare both cycloids](presentation/images/thumbnails/step-01.png)](presentation/images/step-01.png)

2. **Stand the screws upward.** Start with output_cap_cylinder, carrier_top_cap and yellow shaft_end_upper (E), flanges down. Fit 20 M3 x 30 ring screws, six M3 x 35 guides and two M3 x 35 shaft screws from underneath. One shaft head temporarily occupies E's empty hex pocket.

   [![AI-generated CAD illustration: stand the screws upward](presentation/images/thumbnails/step-02.png)](presentation/images/step-02.png)

3. **Seat the starting bearings.** Lower a 6810 over the large black journal and a centred 6704 over yellow E. Seat both on their shoulders.

   [![AI-generated CAD illustration: seat the starting bearings](presentation/images/thumbnails/step-03.png)](presentation/images/step-03.png)

4. **Close the starting layer.** Load eight M3 nuts into carrier_top and four into shaft_mount_upper (N). Retain the nuts with their pockets downward; lower the core, N and output_cap_plate. Support the plate with at least 50 mm access underneath.

   [![AI-generated CAD illustration: close the starting layer](presentation/images/thumbnails/step-04.png)](presentation/images/step-04.png)

5. **Fit the sleeves.** Slide six guide sleeves onto the inner screws and twenty contact sleeves onto the outer screws. The connected ring replaces the twenty outer sleeves only.

   [![AI-generated CAD illustration: fit the sleeves](presentation/images/thumbnails/step-05.png)](presentation/images/step-05.png)

6. **Fit the first cam and Disc B.** Lower shaft_cam_b_outer with its narrow journal up. Lower the closed Disc B with its screw heads down and its indexed clamp screw toward the wide guide gap.

   [![AI-generated CAD illustration: fit the first cam and disc b](presentation/images/thumbnails/step-06.png)](presentation/images/step-06.png)

7. **Close B and start A.** Fit shaft_cam_b_inner with its journal down, then shaft_cam_a_inner with its journal up. Set A's eccentric offset 180 degrees opposite B.

   [![AI-generated CAD illustration: close b and start a](presentation/images/thumbnails/step-07.png)](presentation/images/step-07.png)

8. **Fit Disc A and close its cam.** Lower Disc A with its heads up and index toward the same wide guide gap. Seat its bearing, then fit shaft_cam_a_outer with its journal down.

   [![AI-generated CAD illustration: fit disc a and close its cam](presentation/images/thumbnails/step-08.png)](presentation/images/step-08.png)

9. **Close the finishing inner layer.** Load eight nuts into carrier_bottom and four into shaft_mount_lower (N), pockets upward. Lower those pieces and output_nut_plate; seat the guide sleeves in the core sockets.

   [![AI-generated CAD illustration: close the finishing inner layer](presentation/images/thumbnails/step-09.png)](presentation/images/step-09.png)

10. **Seat the finishing bearings.** Lower the remaining 6810 onto the outer plate and carrier shoulder. Lower the remaining centred 6704 onto N.

    [![AI-generated CAD illustration: seat the finishing bearings](presentation/images/thumbnails/step-10.png)](presentation/images/step-10.png)

11. **Fit the finishing caps.** Lower output_nut_cylinder, carrier_bottom_cap and shaft_end_lower (E), flanges up. Match E's round socket to the temporary screw and its hex pocket to the retained screw.

    [![AI-generated CAD illustration: fit the finishing caps](presentation/images/thumbnails/step-11.png)](presentation/images/step-11.png)

12. **Reverse the temporary shaft screw.** Secure the correctly directed shaft tie and start the ring and guide nuts. Withdraw the temporary screw underneath. Load the vacated hex pocket with an M3 nut; reverse the same screw and insert it from above.

    [![AI-generated CAD illustration: reverse the temporary shaft screw](presentation/images/thumbnails/step-12.png)](presentation/images/step-12.png)

13. **Adjust the fasteners.** Snug the opposed shaft ties, then the six guides, then the twenty ring screws evenly. Hold the teal outer ring fixed and turn E by hand after each group. The black middle ring should turn freely. Reseat any bearing, sleeve or nut that binds.

    [![AI-generated CAD illustration: adjust the fasteners](presentation/images/thumbnails/step-13.png)](presentation/images/step-13.png)

14. **Install the gearbox.** Fix the teal outer ring through its OOBB mounting plates. Couple the drive to E; its face is recessed 0.8 mm behind the black middle ring. Attach the load to the black middle ring through its captive M3 mounting points. Keep the 6.50 mm centre passage clear and select mounting screws for the attached parts.

    [![AI-generated CAD illustration: install the gearbox](presentation/images/thumbnails/step-14.png)](presentation/images/step-14.png)
<!-- oobb-presentation:end -->


## Separate NEMA17 flange-coupler variant

The current manual-input part remains the default. The separate
[NEMA17 adaptation for a 40 mm motor body](parts/oobb_part_motor_gearbox_cycloidal_simple_double_bearing_version_2_20_to_1_reduction_nema17_flange_40_mm_motor_depth/README.md)
uses a 5 mm flange coupler and a configurable motor support. Both black end
covers stay fixed and contain captive M6/M3 mounting nuts. The teal outer
housing is the 20:1 output. Three identical, separate joiners sit 120 degrees
apart. Two M3 × 10 countersunk screws at each end attach each joiner to the
gearbox plate and the separate rear ring. Both teal flanges are 3 mm thick;
the fixed rear black cover projects 1.5 mm beyond the teal mounting face.
The motor support is a continuous tube with a cable opening. Its motor body
depth is part of the catalogue ID and an editable native parameter. Square,
circular and two-row asymmetric plate pairs are available. The three-bed
conversion print contains only added or changed parts. This revision provides
a geometry preview and a [complete 23-stage assembly guide](parts/oobb_part_motor_gearbox_cycloidal_simple_double_bearing_version_2_20_to_1_reduction_nema17_flange_40_mm_motor_depth/assembly_guide/README.md), with a [printable PDF](parts/oobb_part_motor_gearbox_cycloidal_simple_double_bearing_version_2_20_to_1_reduction_nema17_flange_40_mm_motor_depth/assembly_guide/assembly-guide.pdf) and hardware table. The guide checks nut-loading and tool access for the 40 mm motor version.
