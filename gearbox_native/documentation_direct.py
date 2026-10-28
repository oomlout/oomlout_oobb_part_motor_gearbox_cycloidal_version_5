"""Generated guide for the direct captured-nut shaft connection."""
import json
from pathlib import Path
from gearbox_native.project import VERSION


def publish(folder,gearbox):
    folder=Path(folder);c=gearbox['config'];pieces=gearbox['pieces']
    bolts=[dict(role=role,size='M3',length_mm=c[key],quantity=q,head=head) for role,key,q,head in (
        ('guides','guide_bolt_length',c['guide_pin_count'],'socket cap'),
        ('central hub','hub_bolt_length',1,'socket cap'),
        ('motor shaft','direct_grub_length',1,'grub / set screw'),
        ('motor','motor_screw_length',4,'countersunk'))]
    post_count=len(c['post_positions']) if c['post_fasteners'] else 0
    nut_count=c['guide_pin_count']+2+post_count
    if c.get('split_output_casing'):
        nut_count+=len(c['housing_positions'])
        bolts.append(dict(role='casing halves',size='M3',length_mm=c['housing_screw_length'],quantity=len(c['housing_positions']),head='countersunk'))
    if post_count:
        bolts.append(dict(role='standoffs',size='M3',length_mm=c['post_screw_length'],quantity=post_count,head='socket cap'))
    bolts[0]['size']=c['guide_bolt_radius_name'].upper()
    bearing_rows=[dict(role=role,size=c['bearing_'+role],quantity=q,**c[role+'_bearing']) for role,q in (('output',2),('shaft',1))]
    for side,label in enumerate(('bottom','top')):
        bearing_rows.append(dict(role=label+' eccentric',size=c['bearing_eccentric_'+label],quantity=1,**c['eccentric_bearings'][side]))
    record=dict(architecture=c['architecture'],drive_connection=c['drive_connection'],parameters=c,
        pieces={name:{k:v for k,v in piece.items() if k!='thing'} for name,piece in pieces.items()},
        layout=gearbox['layout'],fasteners=bolts,nuts=dict(size='M3',quantity=nut_count,overhang=True),
        bearings=bearing_rows,
        guide_smooth_shank_min_mm=c['guide_bolt_head_z']-c['rotor_a_z'])
    record['nut_groups']=[dict(size='M3',quantity=nut_count-c['guide_pin_count'],overhang=True),
                          dict(size=c['guide_bolt_radius_name'].upper(),quantity=c['guide_pin_count'],overhang=True)]
    if c['guide_bolt_radius_name']!='m3':record['nuts']=record['nut_groups']
    (folder/'native_gearbox.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    (folder/'cycloid_equation.json').write_text(json.dumps(c['cycloid_equation'],indent=2),encoding='utf-8')
    text=f'''# {VERSION.replace('_', ' ').title()} — direct grub-screw drive

**{2*c['housing_radius']:g} mm casing diameter, {c['housing_depth']:g} mm above the motor face, {c['reduction']}:1.**
{len(pieces)} printed pieces. The square OOBB motor plate is {c['housing_width']*15-1:g} mm across.
The previous 50 mm flanged-coupler design and sources are preserved in
`outputs/v5_flanged_50mm/` at the project root.

## Direct shaft connection

One **M3 × {c['direct_grub_length']:g} grub screw** passes through a captured M3 hex nut
and presses radially against the **5 mm motor shaft**. The nut loads from the
bottom of the lower eccentric hub; its threaded axis is radial. The OOBB nut
cutter uses `overhang=True`. The hub has a {2*c['direct_shaft_bore_radius']:g} mm shaft bore.
The printed passage is clearance only: the metal nut supplies the thread.

The hub begins at {c['drive_start']:g} mm above the motor face. Its long hollow
keyed stem surrounds the motor shaft and extends above its {c['motor_shaft_length']:g} mm tip.
A second M3 nut loads into the top of that stem at {c['hub_nut_bottom']:g} mm.
The **M3 × {c['hub_bolt_length']:g} socket screw** retains the upper eccentric,
without entering the motor shaft's space. The key fixes the opposed cam phase.

The first disc now starts at {c['rotor_a_z']:g} mm instead of 28 mm. There is no
purchased flanged coupler, pair of flange screws, or pair of flange nuts.

## Assembly order

1. Print and test `fits/3dpr/fit_M3_grub_and_5mm_shaft.stl` on the actual shaft.
   Check nut loading, sliding fit and gripping before printing the full gearbox.
2. Load six guide nuts into the motor mount from underneath, then attach the
   mount with the four countersunk motor screws.
3. Load the radial M3 nut into the lower hub from its bottom and the axial M3
   joining nut from its top. Start the grub screw without projecting into the bore.
4. Slide the lower hub onto the shaft. Align the top of its cylindrical base
   with the motor mount's top annular face, both {c['drive_flange_top']:g} mm above
   the motor face; use a straightedge across the exposed rims. Hold that position
   while tightening the grub through the radial tool window. Tighten against the
   shaft flat if it has one. Remove the straightedge and check free rotation.
5. **Fit the rear 6810 after tightening the grub screw.** It blocks that tool
   window once installed. Slide it over the posts onto the motor journal.
6. Fit the lower disc/bearing, then the upper disc/bearing and keyed upper cam.
7. Lower the casing over the discs, then fit the front carrier, front 6810 and
   shaft bearing. Tighten the six guide screws and the central joining screw.

To retighten the grub screw, remove the casing/discs and lift the rear 6810.
The access check is for this assembly order, not access through the bearing.

## Hardware

| Role | Quantity | Size | Head |
|---|---:|---|---|
'''
    for b in bolts:text+=f"| {b['role']} | {b['quantity']} | {b['size']} × {b['length_mm']:g} | {b['head']} |\n"
    text+=f'''
Use {nut_count-c['guide_pin_count']} M3 nuts and {c['guide_pin_count']} {c['guide_bolt_radius_name'].upper()} guide nuts.
The casing uses two 6810 bearings. The lower disc uses {c['bearing_eccentric_bottom']},
the upper disc uses {c['bearing_eccentric_top']}, and the front shaft uses {c['bearing_shaft']}.
Guide screws are below the 35 mm maximum. The discs contact {c['guide_bolt_head_z']-c['rotor_a_z']:g} mm
of the guide length below the head: prefer a smooth {c['guide_pin_diameter']:g} mm guide surface there.
Ordinary short fully threaded screws can increase plastic wear; their threads
are not represented in the nominal fit model.

## Printed parts and files

1. `motor_mount`: NEMA plate, rear bearing journal, guide nuts and integral posts.
2. `output_casing`: one rotating ring with lobes and two 6810 seats.
3. `pin_front`: fixed front carrier and bearing seats.
4. `rotor_a`: lower single-piece cycloid.
5. `rotor_b`: opposed upper single-piece cycloid, flipped after printing.
6. `eccentric_hub_lower`: direct shaft hub, radial nut slot and long hollow key.
7. `eccentric_hub_upper`: opposed eccentric and front shaft journal.

- [3dpr.solidcraft](3dpr.solidcraft): editable linked print layout.
- [3dpr_solidcraft.stl](3dpr_solidcraft.stl): combined printable mesh.
- `solidcraft/3dpr/`: individual native documents, STEP/STL and previews.
- `true.solidcraft` and `solidcraft/true/`: nominal geometry.
- `fits/3dpr/`: bearing/orbit-hole samples and the new direct-drive sample.
- `solidcraft_renders/true/with_hardware/`: annotated exploded view, MP4/GIF and Blender scene.
- `native_gearbox.json`: resolved dimensions, named interfaces and hardware.
- [direct_grub_section.png](direct_grub_section.png): section through the grub screw and captured nut.

Print both cams base-down, both discs bearing-pocket-up, the motor plate flat,
the front carrier flange-down, and the casing upright. The lower hub's shaft
bore has a short printed ceiling below the axial nut; confirm it admits the
full motor shaft and clear any bridge strands before assembly.

## Editing and checks

Keep catalogue variants in the verbose `working_oomp_populate.py`. Defaults live
near their mechanism in `simple_defaults.yaml`; kwargs and `design.yaml`
overrides propagate into the native recipe. Use `drive_connection: grub_nut`
for this design or `flanged_coupler` for the previous connection. Direct-drive
dimensions have `direct_` names so the two arrangements stay independently editable.

`interfaces.py` provides the shared bearing seats and named cycloid holes.
The shared `cycloidal_disc` component supplies a `parametric_profile` whose
coordinate formulas remain linked to native parameters on both caps and the wall.
These are sampled line segments, not exact analytic CAD curves. The shared
`rotor_depth` controls cap offsets and wall heights. Before a scripted eccentricity
edit, or after a manual edit before publication, run
`python -m gearbox_native.check_equation_edit --eccentricity 1.39` from the project.
This checks the published file's fixed stations; regenerate if rejected. Changing
the gearbox eccentricity also requires coordinated cam, clearance and assembly
updates through populate. Changing ring count always requires regeneration.
A null lobe radius scales with reduction;
an explicit radius overrides that rule. Generate with `python action_make_solidcraft.py`.

CAD checks cover nominal fit, sampled motion, staged bearing installation,
bottom nut loading and grub-tool access. They do not establish grip torque,
plastic creep, wear or fatigue. Tighten only enough to prevent slipping and
test initially at low load; a metal hub remains the stronger upgrade if needed.
'''
    if c['base_grub']:
        text=text.replace(f"{c['housing_depth']:g} mm above the motor face",
                          f"{c['housing_depth']-c['casing_bottom_z']:g} mm casing depth, {c['overall_height']:g} mm maximum above the motor face")
        text=text.replace('## Assembly order',f'''## Axial package

Two {c['output_bearing']['depth']:g} mm 6810 bearings + two {c['rotor_thickness']:g} mm cycloids
+ {c['disc_gap']:g} mm disc gap = {2*c['output_bearing']['depth']+2*c['rotor_thickness']+c['disc_gap']:g} mm of main components.
The casing is {c['housing_depth']-c['casing_bottom_z']:g} mm deep after clearances and bearing shoulders.
Its top is {c['housing_depth']:g} mm above the motor face. The small central hub reaches
{c['overall_height']:g} mm, retaining an uncut {c['motor_shaft_length']:g} mm motor shaft and an M3 × {c['hub_bolt_length']:g} socket screw.
The 6701 shaft bearing sits radially inside the upper 6810 and shares its axial region.
See [axial_stack_section.png](axial_stack_section.png) for the dimensioned section.

The previous 36 mm direct-drive version is preserved in `outputs/v5_direct_36mm/`.

## Assembly order''')
        start=text.index('1. Print and test');end=text.index('## Hardware',start)
        text=text[:start]+f'''1. Print and test `fits/3dpr/fit_M3_grub_and_5mm_shaft.stl` on the actual shaft.
2. Load the radial nut from underneath the lower hub and the joining nut from
   its top. Start the M3 × {c['direct_grub_length']:g} grub screw without projecting into the bore.
3. **Secure the lower hub to the motor before fitting the motor plate.**
   Put a {c['direct_base_clearance']:g} mm feeler gauge between the hub underside and the raised
   motor pilot. Tighten the grub against the shaft flat if present, then remove
   the gauge and check free rotation. The hub underside is {c['drive_start']:g} mm above
   the motor face; the grub axis is at {c['coupling_grub_z']:g} mm.
4. Load six guide nuts into the motor mount from below. Lower the motor mount
   over the already-secured hub and attach it with the four countersunk screws.
   Its central opening clears the hub and recessed grub screw.
5. Fit the rear 6810 over the posts onto its journal.
6. Fit the lower disc/bearing, then the upper disc/bearing and keyed upper cam.
7. Lower the casing over the discs. Fit the front carrier, upper 6810 and 6701
   shaft bearing, then the six M3 × {c['guide_bolt_length']:g} guide screws and central M3 × {c['hub_bolt_length']:g} socket screw.

To retighten the grub, remove the motor plate from over the hub. There is no
assembled side-access window. The fit check tests this installation order,
including the plate passing over the secured hub, nut and grub screw.

''' + text[end:]
        text=text.replace('the front carrier flange-down, and the casing upright.',
            f'''the front carrier flange-down, and the casing upright. **Use slicer supports
under the casing's internal lobe transition:** it rises only {c['direct_base_ramp_depth']:g} mm to save height.
Remove those supports and check the lobe faces before assembly. The discs retain
their full {c['rotor_thickness']:g} mm working thickness above the transition.''')
        text=text.replace('for this design or `flanged_coupler` for the previous connection.',
            'with `direct_stack_layout: base_grub` for this design. Use `raised` for the\nprevious 36 mm stack, or `flanged_coupler` for the earlier metal coupling.')
    if post_count:
        text=text.replace('4. Load six guide nuts into the motor mount from below.',
            '4. Load six guide nuts and three standoff nuts into the motor mount from below.')
        text=text.replace(f"shaft bearing, then the six M3 × {c['guide_bolt_length']:g} guide screws and central M3 × {c['hub_bolt_length']:g} socket screw.",
            f"shaft bearing, then the six M3 × {c['guide_bolt_length']:g} guide screws, three M3 × {c['post_screw_length']:g}\n   standoff socket screws and central M3 × {c['hub_bolt_length']:g} socket screw.")
        text=text.replace('## Printed parts and files',f'''## Eccentricity and reinforced standoffs

Eccentricity is {c['radius_offset']:g} mm. The automatically sized pitch radius is
{c['pitch_radius']:g} mm using {c['pitch_radius_increment']:g} mm increments and a profile coefficient limit of
{c['lobe_eccentricity_ratio']:g}. The guide-orbit holes are {2*c['guide_hole_radius']:g} mm and standoff-orbit
holes {2*c['post_hole_radius']:g} mm. Casing diameter is {2*c['housing_radius']:g} mm and maximum height is {c['overall_height']:g} mm.
The printed casing contacts have radius {c['lobe_radius']:g} mm (diameter {2*c['lobe_radius']:g} mm).
Changing to M3-mounted rollers later still requires axle mounts and a matching roller outside diameter;
these parts retain solid printed contacts.
The previous 1.25 mm version is preserved in `outputs/v5_eccentric_1_25/`.

Three {2*c['post_radius']:g} mm diameter posts sit on a {2*c['post_pitch_radius']:g} mm pitch circle.
Each has a {2*c['post_screw_hole_radius']:g} mm clearance bore for an M3 × {c['post_screw_length']:g} socket screw,
with its nut loaded from below the motor plate. All nut cutters use `overhang=True`.
The {2*c['post_register_radius']:g} mm diameter locating pegs project {c['post_register_depth']:g} mm into matching
{2*(c['post_register_radius']+c['post_register_clearance']):g} mm carrier sockets. Their shoulders support the
carrier face; the screw heads are recessed above the sockets. The carrier is the
printed part inside the front 6810, named `pin_front`.

Print `fits/3dpr/fit_M3_standoff_lower.stl` and `fit_M3_standoff_socket.stl` together
to check the peg, shoulder and screw fit before printing the full parts. The
small peg walls and printed shoulders need physical clamping/load tests.

## Printed parts and files''')
    if c.get('split_output_casing'):
        start=text.index('1. `motor_mount`:');end=text.index('- [3dpr.solidcraft]',start)
        text=text[:start]+'''1. `motor_mount`: NEMA plate, rear bearing journal, guide nuts and integral posts.
2. `pin_front`: fixed front carrier and bearing seats.
3. `rotor_a`: lower single-piece cycloid.
4. `rotor_b`: opposed upper single-piece cycloid, flipped after printing.
5. `eccentric_hub_lower`: direct shaft hub, radial nut slot and long hollow key.
6. `eccentric_hub_upper`: opposed eccentric and front shaft journal.
7. `output_casing_lower`: lower rotating casing half, 6810 seat and middle nut tabs.
8. `output_casing_upper`: upper rotating casing half, 6810 seat and countersunk middle tabs.

'''+text[end:]
        start=text.index('7. Lower the casing over the discs.')
        end=text.index('\n\nTo retighten',start)
        text=text[:start]+f'''7. Load four M3 nuts into the outside face of the lower casing's middle joining tabs **before installing it**.
   Lower that half over the discs onto the rear 6810. Add `output_casing_upper`,
   aligning the OOBB tabs, their selected M3 joining holes and the continuous lobe band.
   Join with four M3 × {c['housing_screw_length']:g} countersunk screws through the upper middle tabs.
8. Fit the front carrier, upper 6810 and 6701 shaft bearing. Install the six guide screws,
   three standoff screws and central hub screw. Check free rotation before loading.'''+text[end:]
        start=text.index('the front carrier flange-down, and the casing upright.')
        end=text.index(' The lower hub',start)
        text=text[:start]+'''the front carrier flange-down, and **both casing halves split-face down**.
The bearing seats face upward. Do not flip the casings onto their bearing faces;
that would recreate the internal lobe overhang.'''+text[end:]
        text+='''
## Split casing and OOBB output tabs

The split is in the gap between cycloids. Internal geometry and gearbox height
are unchanged. One M3 midpoint hole in each OOBB tab joins the halves; the separate
round joining lugs have been removed. Screws remain clear of the working lobes.
All four captive-nut cutters use OOBB `overhang=True`; load these nuts before the
lower casing meets the motor mount. The countersunk screw heads finish flush.

Each half has four 3 mm-deep, three-unit (44 mm-long) OOBB tabs at the middle split.
Each tab has three M6 holes on 15 mm centres and two midpoint M3 holes (7.5 mm offset).
One M3 hole carries the countersunk joining screw and captive nut; the other remains
available for mounting. A full-length backing joins each tab to the curved casing wall
without entering the working bore. The tabs and
joining flanges sit flat on the bed with the middle joining face. The matched
halves make a 6 mm-thick mounting flange when assembled, with aligned through-holes.
The continuous annular casing wall supports the complete circumference of both
6810 bearing lands; no isolated lobe bridges are needed. Test the tab and nut-pocket
coupons first. These tabs rotate with
the output casing; keep the full rotating envelope clear of surrounding mounts.
'''
        text+=f"\nCore diameter remains {2*c['housing_radius']:g} mm; the tabs span {c['casing_print_width']:g} mm across. "
        text+=f"Half depths are {c['casing_half_depths'][0]:g} and {c['casing_half_depths'][1]:g} mm.\n"
        text+='Print `fit_casing_clamp_lower`, `fit_casing_clamp_upper` and `fit_casing_OOBB_tab` before the full parts.\n'
    if not (folder/'solidcraft_renders').exists():
        text=text.replace('- `solidcraft_renders/true/with_hardware/`: annotated exploded view, MP4/GIF and Blender scene.',
            '- To create fresh presentation media for the selected revision, run `render_solidcraft_exploded.py --hardware` with the configured CAD Python.')
    if not (folder/'direct_grub_section.png').exists():
        text=text.replace('- [direct_grub_section.png](direct_grub_section.png): section through the grub screw and captured nut.',
            '- `gearbox_native.render_direct_section` can generate the selected revision\'s grub-screw section.')
    text+='''
## Shared version 6 controls

Run `python action_gearbox_controls.py` at the project root to open the connected
explorer. Check gearbox screens the complete recipe; Update gearbox generates
and validates a separate catalogue revision before selecting it.

Alternatively, edit and save `gearbox_controls.solidcraft` at the project root,
then run `python action_update_gearbox.py --from-native gearbox_controls.solidcraft`.
The master controls require this update action. Rotor source documents also have
live local dimensions: eccentricity updates both the outline and orbit holes;
disc thickness updates the caps, walls and bearing-seat floor. Local part edits
do not automatically propagate to linked parts. Regenerate the complete gearbox
before manufacturing a changed design. See `PARAMETRIC_CONTROLS.md` at the root.
'''
    (folder/'README.md').write_text(text,encoding='utf-8')
