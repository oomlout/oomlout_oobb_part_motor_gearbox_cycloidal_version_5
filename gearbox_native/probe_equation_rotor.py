"""Verify one actual configured rotor in isolation before publishing equation parts."""
import cmath
import json
import uuid
import yaml
from oobb_solidcraft.compiler import compile_thing
from oobb_solidcraft.construction import build_thing
from oobb_solidcraft.runtime import write_json
from gearbox_native.project import PROJECT,active_part
from gearbox_native.equation_surfaces import context
from gearbox_native.export import render_piece


def main():
    part=active_part()
    thing=build_thing(yaml.safe_load((part/'working.yaml').read_text()),builder_path=PROJECT/'working_solidcraft.py',mode='true')
    local=dict(id=part.name+'__rotor_a',mode='true',**thing['gearbox']['pieces']['rotor_a']['thing'],
               sequential_unions=True,compound_cuts=True,dimensions=thing['dimensions'])
    plan=compile_thing(local);ctx=context(plan);g=ctx['geometry'];c=thing['gearbox']['config']
    # Separate complex-number evaluation establishes the configuration mapping.
    errors=[]
    for t,point in zip(g['stations'],g['points']):
        z=cmath.exp(1j*t);zn=cmath.exp(1j*c['ring_pin_count']*t)
        normal=c['pitch_radius']*z-c['ring_pin_count']*c['radius_offset']*zn
        result=c['pitch_radius']*z-c['radius_offset']*zn-(c['lobe_radius']+c['lobe_clearance'])*normal/abs(normal)
        errors.append(abs(complex(*point)-result))
    assert max(errors)<1e-10
    output=PROJECT/'build/equation_rotor'/uuid.uuid4().hex[:12];output.mkdir(parents=True)
    write_json(output/'plan.json',plan);write_json(output/'config.json',c)
    print('Isolated rotor:',output,flush=True)
    result=render_piece(local,plan,output,'native',True,True)
    if 'error' in result:raise RuntimeError(result['error'])
    report=dict(status='passed',output=str(output),config=c,verification=result['verification'],
                analytic_mapping_max_error_mm=max(errors),geometry=g['sampling']['max_sampled_chord_error_mm'])
    write_json(output/'report.json',report);write_json(PROJECT/'outputs/equation_rotor_probe.json',report)
    print('Isolated equation rotor passed',flush=True)


if __name__=='__main__':main()
