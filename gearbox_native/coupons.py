"""Print small native fit samples before committing to the compact gearbox."""
import json
from pathlib import Path
import uuid
import yaml
from oobb_solidcraft.compiler import compile_thing
from oobb_solidcraft.construction import build_thing
from gearbox_native import parts as p, interfaces
from gearbox_native.export import render_piece, publish_files, geometry_digest
from gearbox_native.project import PROJECT, active_part


def recipes(c):
    width=2*(c['guide_pin_pitch_radius']+c['guide_hole_radius']+4)
    u=p.blank();h=5.2
    p.add(u,'oobb_cube',size=[28,28,h],zz='bottom')
    interfaces.cut_bearing(u,c['bearing_seats']['front_shaft'],top=h,through_depth=h)
    v=p.blank();seat=c['bearing_seats']['output_casing'];h=seat['seat_depth']+c['minimum_wall']
    p.cylinder(v,c['housing_radius'],h)
    p.hole(v,seat['through_radius'],h)
    p.hole(v,seat['seat_radius'],seat['seat_depth'])
    result={f"fit_{c['bearing_shaft']}_shaft":u,'fit_6810_case_lip':v}
    # Keep baseline coupon names stable; add each genuinely different disc seat.
    for side in (0,1):
        local=interfaces.for_disc(c,side);sample=p.blank();h=c['rotor_thickness']
        p.add(sample,'oobb_cube',size=[width,local['eccentric_bearing']['od']+6,h],zz='bottom')
        interfaces.cut_bearing(sample,local['bearing_seats']['cycloid_drive'],top=h,through_depth=h)
        p.hole(sample,c['guide_hole_radius'],h,[c['guide_pin_pitch_radius'],0])
        result[f"fit_{local['bearing_eccentric']}_and_{c['guide_bolt_radius_name'].upper()}_orbit"]=sample
    if c.get('direct_drive'):
        from gearbox_native.direct_drive import hub_sample
        result['fit_M3_grub_and_5mm_shaft']=hub_sample(c)
    if c.get('post_fasteners'):
        from gearbox_native.standoffs import fit_samples
        result.update(fit_samples(c))
    if c.get('split_output_casing'):
        from gearbox_native.split_casing import fit_samples
        result.update(fit_samples(c))
    return result


def main():
    part=active_part();definition=yaml.safe_load((part/'working.yaml').read_text())
    thing=build_thing(definition,builder_path=PROJECT/'working_solidcraft.py',mode='3dpr')
    c=thing['gearbox']['config'];dest=part/'fits/3dpr';dest.mkdir(parents=True,exist_ok=True)
    records={}
    for name,geometry in recipes(c).items():
        local=dict(id=part.name+'__'+name,mode='3dpr',**geometry,
                   sequential_unions=True,compound_cuts=True,dimensions=thing['dimensions'])
        plan=compile_thing(local);key=geometry_digest(plan)
        manifest=dest/(name+'_manifest.json')
        if manifest.exists():
            old=json.loads(manifest.read_text())
            from oobb_solidcraft.runtime import digest
            if old.get('geometry_sha256')==key and old.get('status')=='success' and all(
                (dest/f['file']).is_file() and digest(dest/f['file'])==f['sha256'] for f in old['published_files']):
                records[name]=old;continue
        attempt=PROJECT/'build/solidcraft/attempts'/uuid.uuid4().hex[:12];attempt.mkdir(parents=True)
        print('Building fit sample',name,flush=True)
        (attempt/'plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
        record=render_piece(local,plan,attempt,'native',True,True)
        if 'error' in record:raise RuntimeError(record['error'])
        record.update(status='success',geometry_sha256=key,config=c,
            manifest=str(attempt/'build_manifest.json'),published_files=publish_files(attempt,dest,{
                'generated.solidcraft':name+'.solidcraft','generated.step':name+'.step',
                'generated.stl':name+'.stl','native.png':name+'.png',
                'cad_structure.json':name+'_structure.json'}))
        text=json.dumps(record,indent=2);manifest.write_text(text,encoding='utf-8')
        (attempt/'build_manifest.json').write_text(text,encoding='utf-8');records[name]=record
    (dest.parent/'README.txt').write_text(
        'Print these 3dpr samples using the intended material and layer height.\n'
        f"{c['bearing_eccentric_bottom']} / {c['bearing_eccentric_top']} samples: check each selected central bearing and outer-race lip.\n"
        f"The adjacent guide orbit hole is {2*c['guide_hole_radius']:.2f} mm for a {c['guide_pin_diameter']:g} mm smooth pin, {c['radius_offset']:g} mm orbit,\n"
        f"and {c['guide_pin_clearance']:g} mm radial clearance. This is an orbit hole, not a fastener fit hole.\n"
        '6701 sample: check the replacement front shaft bearing seat and supporting lip.\n'
        '6810 ring: print open seat up; test the bearing fit and outer-race stop.\n'
        'Split casing samples: clamp their bed faces together with an M3x6 countersunk screw and M3 nut. Load the nut from the outside of the lower seam flange.\n'
        'The clamp samples use the actual three-M6/two-M3 tab pattern. Flip the lower sample so its captive nut aligns with the upper countersink.\n'
        'OOBB tab sample: print flat with no slicer support; check its M6/M3 through-holes before printing the full casings.\n'
        'Direct-drive sample, if present: load the M3 nut from underneath; insert an M3x8 grub screw from the side.\n'
        'Test on the actual 5 mm motor shaft. The screw presses on the shaft; avoid crushing the printed nut pocket.\n'
        'Standoff samples, if present: fit the socket over the peg until its face sits on the shoulder; fasten with an M3x25 socket screw and bottom-loaded M3 nut.\n'
        'There are no guide bearings or split-disc screws. Prototype loading and wear remain untested.\n',encoding='utf-8')
    print('Native fit samples verified:',list(records),flush=True)


if __name__=='__main__':main()
