# V7 — fresh editable baseline

Inherited unchanged from sealed V6. The next task is direct whole-gearbox propagation from SolidCraft's Parameters menu. That redesign has not started. See [development brief](VERSION_7_DEVELOPMENT.md). The inherited mechanism guide follows.

# Version 7 — direct grub-screw drive

**72.3 mm casing diameter, 26.6 mm casing depth, 32 mm maximum above the motor face, 20:1.**
8 printed pieces. The square OOBB motor plate is 74 mm across.
The previous 50 mm flanged-coupler design and sources are preserved in
`outputs/v5_flanged_50mm/` at the project root.

## Direct shaft connection

One **M3 × 8 grub screw** passes through a captured M3 hex nut
and presses radially against the **5 mm motor shaft**. The nut loads from the
bottom of the lower eccentric hub; its threaded axis is radial. The OOBB nut
cutter uses `overhang=True`. The hub has a 5.1 mm shaft bore.
The printed passage is clearance only: the metal nut supplies the thread.

The hub begins at 2.5 mm above the motor face. Its long hollow
keyed stem surrounds the motor shaft and extends above its 24 mm tip.
A second M3 nut loads into the top of that stem at 24.8 mm.
The **M3 × 4 socket screw** retains the upper eccentric,
without entering the motor shaft's space. The key fixes the opposed cam phase.

The first disc now starts at 12 mm instead of 28 mm. There is no
purchased flanged coupler, pair of flange screws, or pair of flange nuts.

## Axial package

Two 7 mm 6810 bearings + two 5 mm cycloids
+ 0.5 mm disc gap = 24.5 mm of main components.
The casing is 26.6 mm deep after clearances and bearing shoulders.
Its top is 31.1 mm above the motor face. The small central hub reaches
32 mm, retaining an uncut 24 mm motor shaft and an M3 × 4 socket screw.
The 6701 shaft bearing sits radially inside the upper 6810 and shares its axial region.
See [axial_stack_section.png](axial_stack_section.png) for the dimensioned section.

The previous 36 mm direct-drive version is preserved in `outputs/v5_direct_36mm/`.

## Assembly order

1. Print and test `fits/3dpr/fit_M3_grub_and_5mm_shaft.stl` on the actual shaft.
2. Load the radial nut from underneath the lower hub and the joining nut from
   its top. Start the M3 × 8 grub screw without projecting into the bore.
3. **Secure the lower hub to the motor before fitting the motor plate.**
   Put a 0.5 mm feeler gauge between the hub underside and the raised
   motor pilot. Tighten the grub against the shaft flat if present, then remove
   the gauge and check free rotation. The hub underside is 2.5 mm above
   the motor face; the grub axis is at 6.5 mm.
4. Load six guide nuts and three standoff nuts into the motor mount from below. Lower the motor mount
   over the already-secured hub and attach it with the four countersunk screws.
   Its central opening clears the hub and recessed grub screw.
5. Fit the rear 6810 over the posts onto its journal.
6. Fit the lower disc/bearing, then the upper disc/bearing and keyed upper cam.
7. Load four M3 nuts into the outside face of the lower casing's middle joining tabs **before installing it**.
   Lower that half over the discs onto the rear 6810. Add `output_casing_upper`,
   aligning the OOBB tabs, their selected M3 joining holes and the continuous lobe band.
   Join with four M3 × 6 countersunk screws through the upper middle tabs.
8. Fit the front carrier, upper 6810 and 6701 shaft bearing. Install the six guide screws,
   three standoff screws and central hub screw. Check free rotation before loading.

To retighten the grub, remove the motor plate from over the hub. There is no
assembled side-access window. The fit check tests this installation order,
including the plate passing over the secured hub, nut and grub screw.

## Hardware

| Role | Quantity | Size | Head |
|---|---:|---|---|
| guides | 6 | M3 × 20 | socket cap |
| central hub | 1 | M3 × 4 | socket cap |
| motor shaft | 1 | M3 × 8 | grub / set screw |
| motor | 4 | M3 × 6 | countersunk |
| casing halves | 4 | M3 × 6 | countersunk |
| standoffs | 3 | M3 × 25 | socket cap |

Use 9 M3 nuts and 6 M3 guide nuts.
The casing uses two 6810 bearings. The lower disc uses 6703,
the upper disc uses 6703, and the front shaft uses 6701.
Guide screws are below the 35 mm maximum. The discs contact 12.4 mm
of the guide length below the head: prefer a smooth 3 mm guide surface there.
Ordinary short fully threaded screws can increase plastic wear; their threads
are not represented in the nominal fit model.

## Eccentricity and reinforced standoffs

Eccentricity is 1.4 mm. The automatically sized pitch radius is
31.15 mm using 0.05 mm increments and a profile coefficient limit of
0.9. The guide-orbit holes are 6.2 mm and standoff-orbit
holes 8.5 mm. Casing diameter is 72.3 mm and maximum height is 32 mm.
The printed casing contacts have radius 3 mm (diameter 6 mm).
Changing to M3-mounted rollers later still requires axle mounts and a matching roller outside diameter;
these parts retain solid printed contacts.
The previous 1.25 mm version is preserved in `outputs/v5_eccentric_1_25/`.

Three 5.4 mm diameter posts sit on a 37.1 mm pitch circle.
Each has a 3.4 mm clearance bore for an M3 × 25 socket screw,
with its nut loaded from below the motor plate. All nut cutters use `overhang=True`.
The 4.6 mm diameter locating pegs project 1.6 mm into matching
4.9 mm carrier sockets. Their shoulders support the
carrier face; the screw heads are recessed above the sockets. The carrier is the
printed part inside the front 6810, named `pin_front`.

Print `fits/3dpr/fit_M3_standoff_lower.stl` and `fit_M3_standoff_socket.stl` together
to check the peg, shoulder and screw fit before printing the full parts. The
small peg walls and printed shoulders need physical clamping/load tests.

## Printed parts and files

1. `motor_mount`: NEMA plate, rear bearing journal, guide nuts and integral posts.
2. `pin_front`: fixed front carrier and bearing seats.
3. `rotor_a`: lower single-piece cycloid.
4. `rotor_b`: opposed upper single-piece cycloid, flipped after printing.
5. `eccentric_hub_lower`: direct shaft hub, radial nut slot and long hollow key.
6. `eccentric_hub_upper`: opposed eccentric and front shaft journal.
7. `output_casing_lower`: lower rotating casing half, 6810 seat and middle nut tabs.
8. `output_casing_upper`: upper rotating casing half, 6810 seat and countersunk middle tabs.

- [3dpr.solidcraft](3dpr.solidcraft): editable linked print layout.
- [3dpr_solidcraft.stl](3dpr_solidcraft.stl): combined printable mesh.
- `solidcraft/3dpr/`: individual native documents, STEP/STL and previews.
- `true.solidcraft` and `solidcraft/true/`: nominal geometry.
- `fits/3dpr/`: bearing/orbit-hole samples and the new direct-drive sample.
- `solidcraft_renders/true/with_hardware/`: annotated exploded view, MP4/GIF and Blender scene.
- `native_gearbox.json`: resolved dimensions, named interfaces and hardware.
- [direct_grub_section.png](direct_grub_section.png): section through the grub screw and captured nut.

Print both cams base-down, both discs bearing-pocket-up, the motor plate flat,
the front carrier flange-down, and **both casing halves split-face down**.
The bearing seats face upward. Do not flip the casings onto their bearing faces;
that would recreate the internal lobe overhang. The lower hub's shaft
bore has a short printed ceiling below the axial nut; confirm it admits the
full motor shaft and clear any bridge strands before assembly.

## Editing and checks

Keep catalogue variants in the verbose `working_oomp_populate.py`. Defaults live
near their mechanism in `simple_defaults.yaml`; kwargs and `design.yaml`
overrides propagate into the native recipe. Use `drive_connection: grub_nut`
with `direct_stack_layout: base_grub` for this design. Use `raised` for the
previous 36 mm stack, or `flanged_coupler` for the earlier metal coupling. Direct-drive
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

Core diameter remains 72.3 mm; the tabs span 104 mm across. Half depths are 12.75 and 13.85 mm.
Print `fit_casing_clamp_lower`, `fit_casing_clamp_upper` and `fit_casing_OOBB_tab` before the full parts.

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
