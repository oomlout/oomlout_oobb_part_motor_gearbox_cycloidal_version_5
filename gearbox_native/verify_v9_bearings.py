"""Place all five nominal purchased bearings at their actual shoulder/seat datums."""
import argparse
import json
from gearbox_native.project import PROJECT
from gearbox_native.verify_v8_hardware import cylinder
from gearbox_native.exact_geometry import _boolean
from gearbox_native.verify_native_v8 import overlap
from gearbox_native.verification import read_step


def main(name, case):
    folder=PROJECT/'build/native_v9'/name
    report=json.loads((folder/'verification.json').read_text())
    row=report['cases'][case];v=row['parameters']
    shapes={part:read_step(folder/case/(part+'.step')) for part in row['parts']}
    bearings=[('rear_6808',20,26,7,0,v['motor_plate_depth']+.3),
              ('front_6808',20,26,7,0,v['front_seat_bottom']),
              ('bottom_6702',7.5,10.5,4,v['eccentricity'],v['bottom_journal_z']+v['endplay']),
              ('top_6702',7.5,10.5,4,-v['eccentricity'],v['rotor_b_z']+v['endplay']),
              ('shaft_6701',6,9,4,0,v['housing_top']-4.1)]
    checks=[]
    for label,inside,outside,depth,x,z in bearings:
        ring=_boolean('cut',cylinder(outside,depth,[x,0,z]),[cylinder(inside,depth+.02,[x,0,z-.01])])
        for part,shape in shapes.items():
            amount=overlap(ring,shape)
            checks.append(dict(bearing=label,part=part,z=z,overlap_mm3=amount))
            assert amount<.03,(label,part,amount)
    result=dict(status='passed',checks=checks,maximum_overlap_mm3=max(c['overlap_mm3'] for c in checks))
    (folder/case/'bearing_fit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(case,'all five purchased bearing fits passed',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--case',required=True)
    a=p.parse_args();main(a.name,a.case)
