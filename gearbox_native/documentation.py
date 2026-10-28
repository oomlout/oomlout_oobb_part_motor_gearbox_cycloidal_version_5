"""Generate a current native parts manifest and assembly guide from the recipe."""
import json
from pathlib import Path
from gearbox_native.project import VERSION


def publish(folder, gearbox):
    from gearbox_native.project import require_editable
    folder=Path(folder);require_editable(folder)
    c=gearbox['config'];pieces=gearbox['pieces']
    if c.get('simple_assembly'):
        from gearbox_native.documentation_simple import publish as publish_simple
        return publish_simple(folder,gearbox)
    if not c.get('plain_guides'):return
    height=c['housing_depth']+c['front_retainer_depth']
    bearings=[dict(size=c['bearing_output'],quantity=2,**c['output_bearing']),
              dict(size=c['bearing_eccentric'],quantity=2,**c['eccentric_bearing']),
              dict(size=c['bearing_shaft'],quantity=1,**c['shaft_bearing'])]
    bolts=[dict(role=role,size=size,length_mm=c[key],quantity=q,head=head) for role,size,key,q,head in (
        ('guides','M3','guide_bolt_length',6,'countersunk, smooth shank'),
        ('central hub','M3','hub_bolt_length',1,'socket cap'),
        ('casing','M3','housing_screw_length',4,'socket cap'),
        ('coupler flange','M3','coupling_screw_length',2,'socket cap'),
        ('motor','M3','motor_screw_length',4,'countersunk'),
        ('rear carrier','M3','deck_screw_length',3,'countersunk'),
        ('support posts','M3','post_screw_length',3,'countersunk'),
        ('front bearing hub','M3','front_hub_screw_length',3,'countersunk'))]
    record=dict(architecture=c['architecture'],parameters=c,
        pieces={name:{k:v for k,v in p.items() if k!='thing'} for name,p in pieces.items()},
        layout=gearbox['layout'],bearings=bearings,fasteners=bolts,
        nuts=dict(size='M3',quantity=22,overhang=True),
        support_posts=dict(quantity=3,od_mm=2*c['post_radius'],bore_mm=3.2,length_mm=c['post_depth']),
        guide_required_smooth_reach_below_head_top_mm=c['guide_bolt_head_z']-c['rotor_a_z'])
    (folder/'native_gearbox.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    text=f'''# Compact native {VERSION.replace('_', ' ')} — {c['reduction']}:1

Height above motor face: **{height:g} mm**. Round casing diameter:
**{2*c['housing_radius']:g} mm**. {len(pieces)} printed pieces and five bearings.
The motor-side 6810 is fixed; the coupler flange remains at the {c['motor_shaft_length']:g} mm shaft tip.

## Open and print

- [3dpr.solidcraft](3dpr.solidcraft): complete linked printable layout.
- [3dpr_solidcraft.stl](3dpr_solidcraft.stl): combined print layout mesh.
- `solidcraft/3dpr/`: individual editable documents and STEP/STL/PNG exports.
- `true.solidcraft` and `solidcraft/true/`: nominal geometry.
- `fits/3dpr/`: two small samples for the 6704/plain guide and 6701 seats.
- `solidcraft_renders/true/with_hardware/`: annotated still/key, animation and Blender scene.
- [native_gearbox.json](native_gearbox.json): dimensions, current part list and hardware.

## What changed

Two single-piece {c['rotor_thickness']:g} mm cycloids replace four split halves.
The twelve guide bearings and six disc-joining screw/nut sets are removed.
Six M3 guides run in {2*c['guide_hole_radius']:.2f} mm plain holes, allowing the
{c['radius_offset']:g} mm eccentric orbit plus {c['guide_pin_clearance']:g} mm radial clearance.
The two central 6704 bearings remain, with outer-race retaining lips; the upper
disc prints pocket-up and flips for assembly. The front shaft uses a 6701.
Both casing bearings are 6810. The central keyed hub fastener is now M3.

## Hardware

| Role | Quantity | Size | Head |
|---|---:|---|---|
'''
    for bolt in bolts:
        text+=f"| {bolt['role']} | {bolt['quantity']} | {bolt['size']} × {bolt['length_mm']:g} | {bolt['head']} |\n"
    text+=f'''
Use 22 M3 nuts, three 6 mm OD / 3.2 mm bore posts of {c['post_depth']:g} mm length,
two 6810 bearings (50×65×7), two 6704 (20×27×4), and one 6701 (12×18×4).
The M5 flanged coupler, its two grub screws and the NEMA 17 are unchanged.
Guide screws need a measured smooth section reaching **{c['guide_bolt_head_z']-c['rotor_a_z']:.1f} mm
below the top of the countersunk head**. Do not substitute fully threaded guide
screws without accepting thread contact against the printed tracks.

## Assembly and fit

Print the small fit samples first. Check bearing fit and smooth guide motion
with the actual screws. Fit the motor mount, rear 6810 and casing base first;
preload the base's bottom nuts before lowering it onto the bearing. Fit the
collar onto the coupler before mounting them together on the shaft. Load the
rear carrier nuts from underneath before installing that part. Tighten the
coupler grubs before sliding the rear carrier over the collar/coupler; its
centre bore passes over them. Install the drive,
lower eccentric/disc, keyed opposed upper eccentric/disc, support posts and front
carrier. Load the front hub nuts from the carrier underside. Fit the front hub
and its shaft bearing, then the separate lobe ring and cover.
Four recessed M3 socket screws clamp all three casing pieces to bottom nuts.

Plain sliding guides trade fewer parts and height for friction, wear and lower
pin stiffness. Sampled CAD clearance does not establish load capacity; test the
printed assembly under gradually increasing load.

Edit [design overrides](../../gearbox_native/design.yaml) or verbose populate
options; local compact defaults are in `gearbox_native/compact_defaults.yaml`.
Run `python action_make_solidcraft.py` from the project root. Generated documents
are replaced on regeneration; keep manual edits in separate copies.
'''
    (folder/'README.md').write_text(text,encoding='utf-8')
