"""Current catalogue documentation generated from the consolidated recipe."""
import json
from pathlib import Path
from gearbox_native.project import VERSION


def publish(folder,gearbox):
    folder=Path(folder);c=gearbox['config'];pieces=gearbox['pieces']
    if c.get('direct_drive'):
        from gearbox_native.documentation_direct import publish as direct
        return direct(folder,gearbox)
    fasteners=[dict(role=role,size='M3',length_mm=c[key],quantity=q,head=head) for role,key,q,head in (
        ('guides','guide_bolt_length',6,'socket cap'),('central hub','hub_bolt_length',1,'socket cap'),
        ('coupler flange','coupling_screw_length',2,'socket cap, installed upwards'),
        ('motor','motor_screw_length',4,'countersunk'))]
    record=dict(architecture=c['architecture'],parameters=c,
        pieces={name:{k:v for k,v in piece.items() if k!='thing'} for name,piece in pieces.items()},
        layout=gearbox['layout'],fasteners=fasteners,nuts=dict(size='M3',quantity=9,overhang=True),
        bearings=[dict(role=role,size=c['bearing_'+role],quantity=q,**c[role+'_bearing'])
                  for role,q in (('output',2),('eccentric',2),('shaft',1))],
        guide_smooth_shank_min_mm=c['guide_bolt_head_z']-c['rotor_a_z'])
    (folder/'native_gearbox.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    (folder/'cycloid_equation.json').write_text(json.dumps(c['cycloid_equation'],indent=2),encoding='utf-8')
    text=f'''# {VERSION.replace('_', ' ').title()} — seven-piece native cycloidal gearbox

**{2*c['housing_radius']:g} mm casing diameter; {c['housing_depth']:g} mm above the motor face; {c['reduction']}:1.**
The motor-side bearing remains **6810, 50×65×7 mm**. The second casing bearing
is also 6810. A {c['casing_wall']:g} mm radial wall plus seat clearance makes the
casing only {2*c['housing_radius']-65:g} mm larger than the bearings.
The square OOBB motor mounting plate is {c['housing_width']*15-1:g} mm across.

## Files

- [3dpr.solidcraft](3dpr.solidcraft): linked print layout of all seven pieces.
- [3dpr_solidcraft.stl](3dpr_solidcraft.stl): combined printable mesh.
- `solidcraft/3dpr/`: individual editable native documents and STEP/STL/PNG files.
- `true.solidcraft` / `solidcraft/true/`: nominal geometry.
- `fits/3dpr/`: small samples using the production bearing-seat and orbit-hole definitions.
- `solidcraft_renders/true/with_hardware/`: annotated view, MP4/GIF and editable Blender scene.
- [native_gearbox.json](native_gearbox.json): resolved parameters, named interfaces and BOM.
- [cycloid_equation.json](cycloid_equation.json): analytic cycloid definition.

## Seven printed parts

1. `motor_mount`: NEMA plate, rear 6810 journal, bottom nut pockets, rear guide support and three integral spacer posts.
2. `output_casing`: one open rotating lobe ring, with 6810 seats and outer-race shoulders at both ends.
3. `pin_front`: front guide carrier, front 6810 journal and central shaft-bearing seat in one piece.
4. `rotor_a`: lower, single-piece cycloid.
5. `rotor_b`: opposed upper cycloid; prints pocket-up and flips during assembly.
6. `eccentric_hub_lower`: lower eccentric and coupler drive flange in one piece.
7. `eccentric_hub_upper`: keyed opposed eccentric and front shaft journal.

There is no `pin_rear`, separate front bearing hub, coupling collar, casing base,
casing cover, purchased support post, or embedded guide bearing. The two central
disc bearings remain. The casing is captured axially between the two bearings;
the fixed front carrier is clamped to the motor mount by six M3 guide screws.

## Hardware

| Role | Quantity | Size | Head |
|---|---:|---|---|
'''
    for bolt in fasteners:text+=f"| {bolt['role']} | {bolt['quantity']} | M3 × {bolt['length_mm']:g} | {bolt['head']} |\n"
    text+=f'''
Use nine M3 nuts, two 6810 bearings, two **{c['bearing_eccentric']} ({c['eccentric_bearing']['id']:g}×{c['eccentric_bearing']['od']:g}×{c['eccentric_bearing']['depth']:g} mm)** eccentric bearings,
and one **{c['bearing_shaft']} ({c['shaft_bearing']['id']:g}×{c['shaft_bearing']['od']:g}×{c['shaft_bearing']['depth']:g} mm)** front shaft bearing.
The M5 flanged coupler and its two grub screws remain at the {c['motor_shaft_length']:g} mm shaft tip.
M3 guide screws are socket caps, at most 35 mm, with top-clearance recesses. Their
smooth shank should extend at least **{c['guide_bolt_head_z']-c['rotor_a_z']:.1f} mm below the head**.

## Assembly and printing

Print the motor mount plate-down, the front carrier flange-down, both cycloids
bearing-pocket-up, and the casing upright. The lower casing bearing stop has a
short {c['bearing_seats']['output_casing']['seat_radius']-c['bearing_seats']['output_casing']['through_radius']:.1f} mm radial lip;
the lobe undersides continue on {c['casing_ramp_layer_height']:g} mm steps along a 45-degree ramp. Test that lip with
the casing-seat sample before printing the full ring.

Load the six guide nuts from the bottom of the motor mount, then fit the mount
to the motor and slide on the rear 6810. Fit the two flange nuts from the sides
of the lower eccentric/drive and its centre nut from underneath. Bolt the
purchased coupler to this drive using the two upward-facing M3 socket screws
before lowering the assembly onto the motor shaft. Tighten the grub screws
through the motor mount's radial access holes.

Fit the lower bearing/disc and the keyed upper eccentric/bearing/disc, around
the integral posts. Lower the single casing over them onto the rear bearing,
aligned with the cycloid lobes. Finally lower the front carrier with its 6810
and shaft bearing, and tighten the six guide screws and centre hub screw.

## Parametric editing

Use the verbose `working_oomp_populate.py` for catalogue variants; its kwargs
flow into the recipe. `gearbox_native/design.yaml` can override those values.
Local defaults are in `simple_defaults.yaml`.
With `lobe_radius: null`, lobe radius scales as reference radius × reference
reduction / chosen reduction (1.65 × 20 / reduction by default). An explicit
radius from populate or the design overrides takes precedence. The pitch radius
then grows as needed to satisfy the named hole and lobe-envelope constraints.

`interfaces.py` defines shared
catalogue-based bearing seats and the named cycloid holes: `drive_bearing`,
`guide_orbit`, and `support_post_orbit`. Production parts and fit samples use
those same definitions.

The cycloid is defined by the shared `cycloidal_disc` mathematical component.
With N contacts, pitch radius R, eccentricity e, and a = lobe radius + clearance:

```text
u = R*cos(t) - N*e*cos(N*t)
v = R*sin(t) - N*e*sin(N*t)
s = sqrt(u*u + v*v)
x = R*cos(t) - e*cos(N*t) - a*u/s
y = R*sin(t) - e*sin(N*t) - a*v/s
```

The shared `parametric_profile` adapter preserves this formula in native coordinate
expressions on both caps and the outer wall, targeting {c['profile_tolerance']:g} mm
sampled chord tolerance. These remain line segments, not exact analytic curves.
Validate native edits against the fixed stations with `gearbox_native.check_equation_edit`;
regenerate when rejected. Coordinated gearbox edits are made in the recipe and
regenerated with `python action_make_solidcraft.py`.

The current eccentricity is {c['radius_offset']:g} mm, lobe radius {c['lobe_radius']:g} mm,
disc thickness {c['rotor_thickness']:g} mm and disc gap {c['disc_gap']:g} mm. Named guide
orbit holes are {2*c['guide_hole_radius']:g} mm diameter on a {2*c['guide_pin_pitch_radius']:g} mm pitch circle.
Plain sliding guides save parts and space but add friction and wear. The smaller
eccentricity also changes bearing/guide loads. Sampled CAD checks do not establish
load capacity; test the fit samples and then a low-load prototype.
'''
    (folder/'README.md').write_text(text,encoding='utf-8')
