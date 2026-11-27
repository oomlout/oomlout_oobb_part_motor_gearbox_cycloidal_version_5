"""Publish the style's hardware list, editing guide, and section from checked print meshes."""
import json
import os
from pathlib import Path

import numpy as np
import trimesh
from gearbox_native.project import PROJECT
from gearbox_native.simple_double_bearing import MASTER,STYLE


def print_footprint(mesh):
    """Project top-facing STL triangles, preserving holes used for nested parts."""
    from shapely import polygons,union_all
    xy=mesh.triangles[mesh.face_normals[:,2]>1e-9,:,:2]
    footprint=union_all(polygons(xy),grid_size=.0001)
    assert footprint.is_valid and footprint.area>0
    return footprint


def write_beds(part,records):
    # Preserve the native print orientations on the individual 240 mm beds.
    # Use the checked, localized exports so bed selection does not rely on STL shell order.
    from gearbox_native.simple_double_bearing import POSITIONS,RING_PRINT,SECOND_BED,THIRD_BED
    from gearbox_native.double_bearing_housing import CIRCLE
    from itertools import combinations
    home=dict(POSITIONS,connected_contact_ring=RING_PRINT)
    beds=[('gearbox_plate',[n for n in records if n not in SECOND_BED|THIRD_BED|{CIRCLE}]),('disc_plate',sorted(SECOND_BED)),('outer_housing_plate',sorted(THIRD_BED)),('outer_housing_reprint',['output_nut_plate','output_cap_plate','output_nut_cylinder','output_cap_cylinder'])]
    if CIRCLE in records:beds.append(('circular_plate',[CIRCLE]))
    for bed,names in beds:
        meshes=[]
        for n in names:
            m=trimesh.load_mesh(part/'native_parts'/(n+'.stl'))
            if bed=='circular_plate':xy=(120,120)
            elif bed=='disc_plate':xy=(home[n][0]-244,home[n][1])
            elif bed=='outer_housing_plate':xy=(home[n][0]-488,home[n][1])
            elif bed=='outer_housing_reprint':xy=(54+108*(names.index(n)%2),54+104*(names.index(n)//2))
            elif n in home:xy=home[n]
            else:
                bounds=records[n]['mesh']['bounds_mm'];xy=np.mean(bounds,axis=0)[:2]
            m.apply_translation([*xy,0]);meshes.append(m)
        plate=trimesh.util.concatenate(meshes)
        assert max(plate.extents[:2])<=240,(bed,plate.extents)
        # Center each group on its own 240 mm bed, independent of the master layout origin.
        shift=120-np.mean(plate.bounds,axis=0)[:2]
        plate.apply_translation([*shift,0])
        assert min(plate.bounds[0,:2])>=0 and max(plate.bounds[1,:2])<=240
        outlines=[print_footprint(m) for m in meshes]
        assert all(a.distance(b)>1 for a,b in combinations(outlines,2))
        folder=part/bed;folder.mkdir(exist_ok=True);plate.export(folder/'3dpr.stl')
        (folder/'3dpr.scad').write_text('import("3dpr.stl", convexity=10);\n',encoding='utf8')
        shells=trimesh.load_mesh(folder/'3dpr.stl').split(only_watertight=False)
        assert len(shells)==len(names) and all(s.is_volume and abs(s.bounds[0,2])<.01 for s in shells)


def shaft_kit(part,names,v):
    from gearbox_native.split_stack import layer_audit
    from gearbox_native.stacked_disc_shaft import NAMES
    import shutil
    shaft_names=list(NAMES)
    assert set(shaft_names)<=set(names)
    audit={n:layer_audit(trimesh.load_mesh(part/'native_parts'/(n+'.stl'))) for n in shaft_names}
    for name,a in audit.items():
        assert a['unsupported_islands']==0,(name,a)
        if name.startswith('shaft_end'):
            # E prints with both pockets against the bed, using two short bridge layers.
            assert a['maximum_lateral_reach_mm']<1.8,(name,a)
            if a['maximum_lateral_reach_mm']>.35:
                assert 2.9 < a['at_print_z_mm'] < 4.2,(name,a)
        else:assert a['maximum_lateral_reach_mm']<.35,(name,a)

    (part/'shaft_printability.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf8')
    kit=part/'shaft_reprint';kit.mkdir(exist_ok=True)
    pieces=[];x=y=4.;row_height=0.
    for i,name in enumerate(shaft_names):
        m=trimesh.load_mesh(part/'native_parts'/(name+'.stl'))
        if i and i%3==0:
            x=4.;y+=row_height+4;row_height=0.
        m.apply_translation([x-m.bounds[0,0],y-m.bounds[0,1],0])
        x+=m.extents[0]+4;row_height=max(row_height,m.extents[1]);pieces.append(m)
    trimesh.util.concatenate(pieces).export(kit/'3dpr.stl')
    shells=trimesh.load_mesh(kit/'3dpr.stl').split(only_watertight=False)
    assert len(shells)==len(shaft_names) and all(s.is_volume and abs(s.bounds[0,2])<.01 for s in shells)
    for alias,name in [('E_end_journal','shaft_end_lower'),('N_mount_carrier','shaft_mount_lower'),('C_eccentric_half','shaft_cam_a_outer')]:
        for ext in ('step','stl'):shutil.copyfile(part/'native_parts'/(name+'.'+ext),kit/(alias+'.'+ext))
    (kit/'README.md').write_text(f"""# Shaft-only print: eight pieces, three shapes

Print [3dpr.stl](3dpr.stl) once, or print two [E end journals](E_end_journal.stl), two [N nut carriers](N_mount_carrier.stl) and four [C eccentric halves](C_eccentric_half.stl). For a first fit check, print one E: the nominal web beside the screw-head recess is only 0.27 mm. Check your slicer retains that wall and that an actual screw, nut and bearing seat without forcing.

Follow the [checked gearbox assembly order](../ASSEMBLY.md) when fitting these pieces around the bearings.

Order from either end: **E N C C C C N E**. The end recesses face out; the four N pockets face their E. Load the mounting nuts before closing E onto N. For each eccentric bearing, put two narrow C journals nose-to-nose in the inner race with shoulders outside. Turn the second pair 180 degrees about the gearbox axis. Flip the second E about the diagonal perpendicular to the tie line: each socket must sight through to a hex at the other end. Insert two M3 x 35 socket screws from opposite ends and seat them lightly into their nuts. The central 6.50 mm bore stays clear. The four OOBB mounting holes are blind to the inner cams; choose external screws that reach their embedded nuts without bottoming out. At the default 16 mm spacing, each rotating E face is recessed 0.8 mm behind the stationary carrier. Give a flat drive attachment a central boss or stand-off that reaches E and leaves the carrier clear.

This kit matches the {v['middle_length']:g} mm spacer stack. It includes the complete shaft stack for that length. The [layer check](../shaft_printability.json) measures sideways steps between successive 0.2 mm sections in these print orientations.
""",encoding='utf8')


def publish_details(part,views,v,overrides,digest,proof):
    (part/'3dpr.scad').write_text('// All current print options; choose the output plate shape to use.\nimport("3dpr.stl", convexity=10);\n',encoding='utf8')
    record=json.loads((views/'export.json').read_text())
    (part/'browser_groups_verification.json').write_text(json.dumps(dict(status='passed',
        view='reopened exploded assembly',source_sha256=record['source_sha256'],
        toggled_visible_bodies=record['browser_groups']),indent=2)+'\n',encoding='utf8')
    proof.update(outer_loose_sleeves=int(v['ring_count']),central_loose_sleeves=int(v['guide_count']),connected_ring_choices=1,source_sha256=record['source_sha256'],printable_parts=len(record['parts']),
                 hardware_reference_bodies=len(record['hardware_reference_bodies']),physical_fit_tested=False)
    (part/'fit_verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8')
    (part/'native_configuration.json').write_text(json.dumps(dict(style=STYLE,source_master=MASTER,
        source_master_sha256=digest,parameters=overrides),indent=2)+'\n',encoding='utf8')
    from gearbox_native.double_bearing_diagram import draw_exploded,draw_carrier_faces,draw_output_plates
    draw_output_plates(part,v)
    draw_carrier_faces(part)
    draw_exploded(part,views,v)
    from gearbox_native.stacked_shaft_drawing import draw
    draw(part,v)
    from gearbox_native.bearing_reprint import write_upgrade
    write_upgrade(part,v)
    write_beds(part,record['parts'])
    (part/'outer_housing_reprint/README.md').write_text(f"""# Outer housing reprint

Print [3dpr.stl](3dpr.stl) once for the two square plates and both bearing cylinders. To use the lower-row shape, substitute one [lower-row plate](../native_parts/output_lower_row_plate.stl) for each square plate you want to replace. All bearing pockets face upwards in the supplied print orientations.

Place a 6810 into each cylinder. Close each with a flat plate against the exposed outer race. Put the two plate faces against the ring spacers and align their lobe holes. Pass {int(v['ring_count'])} M3 × {v['join_length']:g} socket-cap screws from the cylinder with round recesses into the nuts in the opposite cylinder. The lobe screws clamp the whole assembly.

[Plate hole patterns](../output_plate_options.png) · [Exploded assembly](../exploded_labeled.png)
""",encoding='utf8')
    shaft_kit(part,record['parts'],v)
    carrier_kit=part/'carrier_reprint'
    carrier_kit.mkdir(exist_ok=True)
    carriers=[]
    for i,name in enumerate(('carrier_bottom','carrier_bottom_cap','carrier_top','carrier_top_cap')):
        mesh=trimesh.load_mesh(part/'native_parts'/(name+'.stl'))
        mesh.apply_translation([30+55*(i%2),30+55*(i//2),0])
        carriers.append(mesh)
    kit=trimesh.util.concatenate(carriers)
    assert len(kit.split())==4 and kit.is_volume
    kit.export(carrier_kit/'3dpr.stl')
    (carrier_kit/'README.md').write_text('''# Inner carrier reprint

Print the four pieces once in the supplied orientation. Load eight M3 nuts straight into each core from its flat mating face. Seat the 6704 in the cap and close it with the core. Use these four pieces with the matching revised disc halves. The cap with six hex recesses goes on the drive end and the cap with six round socket-head recesses goes on the top end. The six M3 × 35 screws clamp both carriers through the inner guide sleeves.

[Assembly and parameters](../EDITING_PARAMETERS.md) · [Labeled exploded view](../exploded_labeled.png)
''',encoding='utf8')
    # One bed for upgrading an assembled gearbox from the four-mount carriers.
    upgrade=part/'eight_mount_reprint'
    upgrade.mkdir(exist_ok=True)
    meshes=[]
    for i,name in enumerate(('rotor_a','rotor_a_cap','rotor_b','rotor_b_cap',
                             'carrier_top','carrier_top_cap','carrier_bottom','carrier_bottom_cap')):
        mesh=trimesh.load_mesh(part/'native_parts'/(name+'.stl'))
        xy=(40+79*(i%2),40+79*(i//2)) if i<4 else (188,28+55*(i-4))
        mesh.apply_translation([*xy,0])
        for other in meshes:
            assert any(mesh.bounds[0,j]>other.bounds[1,j]+1 or other.bounds[0,j]>mesh.bounds[1,j]+1 for j in (0,1))
        meshes.append(mesh)
    bed=trimesh.util.concatenate(meshes)
    assert len(bed.split())==8 and bed.is_volume and np.all(bed.bounds[0,:2]>=0) and np.all(bed.bounds[1,:2]<=240)
    bed.export(upgrade/'3dpr.stl')
    (upgrade/'README.md').write_text('''# Eight-mount carrier upgrade

Print [3dpr.stl](3dpr.stl) once. The four carrier pieces and four disc halves share the revised six-guide pattern; replace them as a set. Reuse the shaft stack, outer casing, bearings, sleeves and six M3 × 35 drive screws. A fully populated carrier pair needs 16 M3 mounting nuts (eight more than the earlier four-mount pair).

Load the nuts from the flat face of each carrier core, seat a 6704 in each cap, and close the carriers before tightening the six drive screws. See the [matching split faces](../carrier_split_faces.png) and the [full assembly order](../EDITING_PARAMETERS.md).
''',encoding='utf8')
    hardware=f"""# Hardware

| Part | Quantity | Location |
|---|---:|---|
| 6810 bearing, 50 × 65 × 7 mm | 2 | Between each output plate and its stationary carrier |
| 6704 bearing, 20 × 27 × 4 mm | 4 | Two centered shaft supports and one inside each cycloid |
| M3 × {v['join_length']:g} socket-cap screw and M3 nut | {int(v['ring_count'])} each | Outer ring contacts |
| M3 × 35 socket-cap screw and M3 nut | 6 each | All four stationary carrier pieces and six inner sleeves |
| M3 hex mounting nut | 16 | Eight at each carrier split, installed before closing |
| Printed round spacer, Ø{2*v['contact_radius']:g} × {v['middle_length']:g} mm, Ø{2*v['spacer_bore']:g} bore | {int(v['ring_count']+v['guide_count'])} on the plate | Six on the drive screws plus one per outer contact when using loose sleeves |
| Printed connected contact ring | 1 on the plate | Alternative to all outer loose sleeves. Use the same six loose sleeves on the drive screws with either option |
| M3 × 6 countersunk screw and M3 nut | 6 each | Three per clamshell disc. Ø6 mm heads seat flush; nominal nut engagement is 1.75 mm |
| M3 × 35 socket-cap screw and M3 nut | 2 each | Opposed shaft ties; one enters each E from the outside |
| M3 hex mounting nut | Up to 8 | Four in each rotating N disc; omit unused mounting points |

The six guide screws and the two shaft ties stay M3 × 35 at either spacer setting. Outer ring screws are M3 × 30 for 16 mm spacers and M3 × 35 for 20 mm spacers. The default square flange is 104 × 104 × 3 mm with 12 M6 and 28 M3 mounting bores. The lower-row flange has 13 M6 and 33 M3 mounting bores. The 20 lobe screws pass through both flanges and clamp their 8.5 mm bearing cylinders against the spacers. Each stationary carrier has eight M3 half-grid mounts at (±15, ±7.5) and (±7.5, ±15) mm in assembled coordinates. Load their nuts from the split face.
"""
    (part/'HARDWARE.md').write_text(hardware,encoding='utf8')
    guide=f"""# Editing and assembly

Open [gearbox_controls.solidcraft](gearbox_controls.solidcraft) and edit its favourite parameters. The ring holes, printed spacers, connected ring and cycloid profiles follow `reduction`. `contact_radius` is the spacer outside radius. The upper stationary carrier takes the screw heads and the lower one takes M3 nuts. Each 6810 outer race seats between a flat OOBB plate and a separate retaining cylinder. The lobe screws enter the upper cylinder and the nuts load from the lower cylinder. Print each piece flat with its bearing pocket opening upwards.

The rotating shaft now takes an attachment at either end using four M3 holes at 7.5 mm radius. Its nominal Ø6.50 mm central passage remains open. The eight discs make three shapes: E end journal, N mount nut carrier, C eccentric half. The C offsets follow eccentricity. At input angle zero the E mounting cross is 45 degrees to the housing; turn the input to -45 degrees to align the two grids. At the default Ø78 mm contact pitch change reduction and offset together for the checked 15:1 / 2 mm combination. Both sleeve sets and the connected ring use Ø7 mm contacts. Set middle_length to 16 mm (default) or 20 mm. The two 7 mm discs and their 0.5 mm running gap need more than 12 mm. The 16 mm setting leaves 0.75 mm end clearance on each side.

Follow the [layered assembly order](ASSEMBLY.md) and the two illustrated pages, [starting layers](assembly_lower.png) and [finishing layers](assembly_upper.png). Start with the native upper/socket-cap end facing down and all 28 long screws standing upward. The central E and large 6810 inner carrier share the first layer. Lower the bearings, concentric plates and spacers over the screws, then Disc B and Disc A around their split cams. Secure one shaft tie before withdrawing and reversing the temporary tie at the end.

Fit your drive to the rotating four-hole pattern. The rotating E face sits {v['carrier_extension']+v['shaft_face_z']:.2f} mm below the stationary carrier face: use a central boss that reaches E and keeps the broad face of the attachment clear of the stationary plate. Measured from E, the bottom of the mounting nut pocket is {v['shaft_end_depth']+v['shaft_nut_depth']:.1f} mm in, and the first cam is {v['shaft_end_depth']+v['shaft_mount_depth']:.1f} mm in. Select the mounting screw length after allowing for your attachment thickness. Keep the M6 passage open and check the mechanism turns freely by hand before applying load.

The print plate includes both outer contact options. In the native assembly the loose sleeves are visible. To preview the alternative, show connected_contact_ring and hide the printed_contact_sleeve bodies. Keep the six printed_drive_sleeve bodies visible. The native print snapshot hides it and the print STL contains only plastic. To export a saved edit use `python action_export_native.py --design "<path to your saved master>"`. Use [the bearing and sleeve upgrade](bearing_reprint/README.md) when upgrading the preceding V2 assembly. The three shaft shapes print flat, with the E screw and nut mouths on the bed and the N pockets facing up. For the supplied default, print gearbox_plate/3dpr.stl, disc_plate/3dpr.stl and outer_housing_plate/3dpr.stl for a 240 mm bed. The four-piece outer_housing_reprint/3dpr.stl upgrades just the housing. The parent 3dpr.stl is the complete wide layout.
"""
    guide+="""
The default housing uses a 7 × 7 OOBB square on each end. The spare lower-row plate beside the stack fits either cylinder. Its upper half follows the ring and its bottom edge extends by one 15 mm row. Use the Alternative output plate browser group to toggle it. The 15 mm M6 grid and 7.5 mm M3 grid stay centered on the shaft, with M6 at shared positions. Both shapes omit stations that would foul a mounting nut against the bearing cylinder.

Edit `pitch` (ring screw center radius) or `contact_radius` (spacer radius) to change the ring diameter. The flange selects an odd OOBB size through 9 × 9. Mounting holes become available or drop out as the cylinder clears them, and the spare moves sideways with the plate size. The 6810 and the existing gear geometry also constrain the usable pitch.
"""
    guide+='''
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
'''
    guide+='\nEach outer carrier cap pilots the full 7 mm width of the 6810. The flat carrier core meets the end of that journal at the bearing face and closes the inner race. The OOBB plate and the outside cylinder lip retain the outer race. Insert each E journal from the outside through its centered 6704 and seat its wide flange. N bears against the other side. Seat each sleeve in both shallow guide sockets. See the [installation drawing and fit gauge](bearing_reprint/README.md) before closing the gearbox.\n'
    guide+='\nThe default guide pattern is three opposing pairs. To move a pair in the master, edit `guide_pair_a`, `guide_pair_b` or `guide_pair_c` in degrees; its opposite stays 180° away. The screw seats, shafts, sleeves and matching guide tracks follow. The OOBB mounting grid stays fixed. After an angle edit, check the webs to the nut pockets and the disc clamps before reprinting. The [fit report](fit_verification.json) records the measured webs for the supplied layout.\n'
    from gearbox_native.double_bearing_groups import BROWSER_GUIDE
    circle_note=''
    if 'output_circle_plate' in record['parts']:
        circle_note=('\nThe plain circular OOBB plate is a third interchangeable option: '
                     f"**{2*v['circle_plate_radius']:g} mm diameter x {v['mount_flange_depth']:g} mm thick**. "
                     'It has the OOBB M6/M3 grid and straight lobe-screw bores, with no countersinks or NEMA17 joiner holes. '
                     'One copy is included in the main 3dpr layout. Use it in place of either square plate; print twice for two circular ends. '
                     '[Circular plate only](circular_plate/3dpr.scad) · [Individual STL](native_parts/output_circle_plate.stl) · [All options in 3dpr](3dpr.scad). '
                     'It is parked beside the assembly in Alternative output plate. '
                     '`circle_grid_radius` and `circle_plate_radius` follow the ring size through native expressions.\n')
        guide+=circle_note
    (part/'EDITING_PARAMETERS.md').write_text(guide+'\n'+BROWSER_GUIDE,encoding='utf8')
    studio_links = '[Rounded gearbox](render_assembled_rounded.png) · [Square gearbox](render_assembled_square.png) · [Exploded groups](render_exploded.png) · [Assembly instructions](ASSEMBLY.md) · [Twelve-step illustrated guide](render_installation.png)\n\n' if (part/'render_installation.png').is_file() else ''
    (part/'README.md').write_text(f"""# Simple double bearing · version 2 · {v['reduction']:g}:1

{studio_links}[Editable SolidCraft master](gearbox_controls.solidcraft) · [Gearbox print plate](gearbox_plate/3dpr.stl) · [Disc halves, carrier caps and split shaft parts](disc_plate/3dpr.stl) · [Cylinders and lower-row option](outer_housing_plate/3dpr.stl) · [Four-piece outer housing upgrade](outer_housing_reprint/3dpr.stl) · [Complete wide layout](3dpr.stl) · [Individual STEP/STL](native_parts/) · [Connected ring STL](native_parts/connected_contact_ring.stl) · [One Ø7 mm sleeve STL](native_parts/printed_contact_sleeve.stl) · [Exploded assembly with hardware](exploded.solidcraft)

[Bearing upgrade, installation drawing and fit gauge](bearing_reprint/README.md) · [Output plate hole patterns](output_plate_options.png) · [Labeled exploded diagram](exploded_labeled.png) · [Eight-piece upgrade print](eight_mount_reprint/3dpr.stl) · [Carrier split faces](carrier_split_faces.png) · [Four replacement carrier halves](carrier_reprint/3dpr.stl) · [Shaft names, diameters and OOBB grid (SVG)](shaft_reference.svg) · [Shaft-only reprint](shaft_reprint/3dpr.stl) · [Assembly and parameters](EDITING_PARAMETERS.md) · [Hardware list](HARDWARE.md) · [Fit checks](fit_verification.json)

{circle_note}
![Shaft stack and purchased hardware](shaft_stackup.png)
""",encoding='utf8')
    nav=PROJECT/'navigation_oobb/oobb/part/motor_gearbox/cycloidal'/STYLE/f"{int(v['reduction'])}_to_1_reduction"
    nav.mkdir(parents=True,exist_ok=True)
    (nav/'active_part.json').write_text(json.dumps(dict(style=STYLE,part_id=part.name,path=part.relative_to(PROJECT).as_posix()),indent=2))
    (nav/'README.md').write_text(f"[Parts and assembly]({os.path.relpath(part/'README.md',nav).replace(chr(92),'/')})\n",encoding='utf8')
