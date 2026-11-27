"""Check continuous straight insertion paths against the published native STEP bodies.

A translated solid sweeps its starting volume and the prisms swept by its boundary
faces. Check those individually against installed bodies, avoiding a fragile union.
The current design has planar faces, axial cylinders and cones with monotone
normals along the tested vertical paths.
"""
import argparse
import math
import json
from pathlib import Path

import numpy as np
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.GProp import GProp_GProps
from OCP.TopAbs import TopAbs_SOLID, TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS
from OCP.gp import gp_Vec

from gearbox_native.exact_geometry import _move
from gearbox_native.project import PROJECT, active_part
from gearbox_native.verification import read_step
from gearbox_native.verify_native_v8 import overlap

PART = active_part()
VIEWS = PROJECT / 'build/flat_6810/views'


def bounds(shape):
    box = Bnd_Box()
    BRepBndLib.AddOptimal_s(shape, box, False, False)
    return np.array(box.Get())


def volume(shape):
    prop = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, prop)
    return abs(prop.Mass())


def intersect_boxes(a, b):
    return all(a[i+3] > b[i]+1e-6 and b[i+3] > a[i]+1e-6 for i in range(3))


class Audit:
    def __init__(self):
        health = json.loads((VIEWS/'assembled_health.json').read_text())
        declared = {r['name']: np.array(r['bbox']['min']+r['bbox']['max'])
                    for r in health['bodies']
                    if r['name'] != 'connected_contact_ring'}
        self.shapes = {}
        self.boxes = {}
        solids = TopExp_Explorer(read_step(PART/'true.step'), TopAbs_SOLID)
        while solids.More():
            solid = solids.Current()
            box = bounds(solid)
            names = [n for n, b in declared.items() if np.max(abs(b-box)) < .04]
            if len(names) != 1:
                raise ValueError(('Ambiguous native body', names, box.tolist()))
            n = names[0]
            self.shapes[n], self.boxes[n] = solid, box
            solids.Next()
        assert self.shapes.keys() == declared.keys()
        self.shapes.pop('output_lower_row_plate')
        self.boxes.pop('output_lower_row_plate')
        self.shapes.pop('output_circle_plate',None)
        self.boxes.pop('output_circle_plate',None)
        published=json.loads((PART/'native_export_verification.json').read_text())
        export=json.loads((VIEWS/'export.json').read_text())
        assert published['source_sha256']==export['source_sha256']
        self.cache = {}
        self.records = []
        self.boolean_checks = 0

    def family(self, *prefixes):
        return [n for n in self.shapes if n.startswith(prefixes)]

    def sweep(self, name, delta):
        key = name, tuple(delta)
        if key not in self.cache:
            solid = self.shapes[name]
            pieces = [solid, _move(solid,'translate',delta)]
            faces = TopExp_Explorer(solid, TopAbs_FACE)
            while faces.More():
                face = TopoDS.Face_s(faces.Current())
                faces.Next()
                prism = BRepPrimAPI_MakePrism(face,gp_Vec(*delta),False,True).Shape()
                if volume(prism) < 1e-7:
                    continue
                if not BRepCheck_Analyzer(prism).IsValid():
                    raise ValueError(('Invalid swept boundary',name,delta))
                pieces.append(prism)
            self.cache[key] = [(p,bounds(p)) for p in pieces]
        return self.cache[key]

    def path(self, title, moving, installed, dz, required=True):
        moving = list(moving)
        obstacles = set(installed)-set(moving)
        failures = []
        candidates = 0
        for name in moving:
            box = self.boxes[name].copy()
            box[2] += min(0,dz)
            box[5] += max(0,dz)
            nearby = [n for n in obstacles if intersect_boxes(box,self.boxes[n])]
            if not nearby:
                continue
            for n in nearby:
                candidates += 1
                largest = 0.
                for swept, swept_box in self.sweep(name,[0,0,dz]):
                    if not intersect_boxes(swept_box,self.boxes[n]):
                        continue
                    self.boolean_checks += 1
                    amount = overlap(swept,self.shapes[n])
                    largest = max(largest,amount)
                    if amount > .03:
                        break
                if largest > .03:
                    failures.append(dict(moving=name,obstacle=n,overlap_mm3=round(largest,4)))
        row=dict(step=title,moving=moving,approach_offset_mm=dz,installed=list(installed),
                 candidate_pairs=candidates,clear=not failures,blocked=failures)
        self.records.append(row)
        print(title,'PASS' if not failures else failures,flush=True)
        if required and failures:
            raise ValueError(title)
        return moving



def access_checks(a, report):
    from gearbox_native.exact_geometry import _polygon
    values=json.loads((PART/'native_export_verification.json').read_text())['parameters']
    rows=[]
    def probe(title, shape, targets, required=True):
        box=bounds(shape)
        clashes=[]
        for name in targets:
            if intersect_boxes(box,a.boxes[name]):
                amount=overlap(shape,a.shapes[name])
                if amount>.03:
                    clashes.append(dict(part=name,overlap_mm3=round(amount,4)))
        row=dict(check=title,clear=not clashes,blocked=clashes)
        rows.append(row)
        print(title,'PASS' if not clashes else clashes,flush=True)
        if required and clashes:raise ValueError(title)

    def hex_tool(x,y,z0,z1,across_flats,angle):
        radius=across_flats/math.sqrt(3)
        points=[(radius*math.cos(angle+j*math.pi/3),
                 radius*math.sin(angle+j*math.pi/3)) for j in range(6)]
        solid=BRepPrimAPI_MakePrism(_polygon(points),gp_Vec(0,0,z1-z0)).Shape()
        return _move(solid,'translate',[x,y,z0])

    for name in a.family('hardware_drive_caps','hardware_ring_cap_heads','hardware_shaft_M3x35'):
        box=a.boxes[name]
        x,y=(box[:2]+box[3:5])/2
        shaft='shaft_' in name
        below=name.endswith('M3x35_lower')
        if below:z0,z1=box[2]-60,box[2]+1.2
        else:z0,z1=box[5]-1.2,box[5]+60
        phase=0 if shaft else math.atan2(y,x)
        tool=hex_tool(x,y,z0,z1,2.5,phase)
        probe('2.5 mm key access '+name,tool,a.shapes)

    for side in ('a','b'):
        group=a.family('rotor_'+side,'hardware_disc_'+side,'hardware_6704_disc_'+side)
        for name in a.family('hardware_disc_'+side+'_M3x6'):
            box=a.boxes[name]
            x,y=(box[:2]+box[3:5])/2
            if side=='a':z0,z1=box[2]-60,box[2]+.8
            else:z0,z1=box[5]-.8,box[5]+60
            tool=hex_tool(x,y,z0,z1,2,0)
            probe('2 mm rotor key on bench '+name,tool,group)
            probe('Blocked rotor key after casing closure '+name,tool,a.shapes,False)
            assert not rows[-1]['clear']

    # Use the current printed alternative in its final assembly position.
    ring='connected_contact_ring'
    a.shapes[ring]=_move(read_step(PART/'native_parts'/f'{ring}.step'),'translate',[0,0,values['middle_start']])
    a.boxes[ring]=bounds(a.shapes[ring])
    state=next(r['installed'] for r in report['steps'] if r['step']=='18 Twenty loose outer contacts')
    a.path('Alternative connected ring before upper unit',[ring],state,60)
    report['optional_connected_ring']=a.records[-1]
    report['tool_access']=rows
    report['tool_scope']='Straight 2.5 mm hex shanks for socket caps; straight 2 mm hex shanks for disc clamps. Driver handles and printed tolerances require a bench check.'


def run(output):
    a = Audit()
    F = a.family
    lower = []
    def add(title, moving, dz=60):
        lower.extend(a.path(title,moving,lower,dz))

    add('01 Lower cylinder',['output_nut_cylinder'])
    add('02 Lower 6810 into open cylinder',['hardware_6810_bottom'])
    add('03 Lower carrier cap from outside',['carrier_bottom_cap'],-60)
    add('04 Lower output plate',['output_nut_plate'])
    add('05 Lower support 6704',['hardware_6704_base'])
    add('06 Lower E from outside',['shaft_end_lower'],-60)

    core = ['carrier_bottom']
    core.extend(a.path('Bench lower core nuts',F('hardware_carrier_bottom_mount_nut'),core,-60))
    add('07 Lower core with captive nuts',core)
    nutcarrier = ['shaft_mount_lower']
    nutcarrier.extend(a.path('Bench lower N nuts',F('hardware_shaft_mount_nut_lower'),nutcarrier,-60))
    add('08 Lower N with captive nuts',nutcarrier)
    add('09 Six guide sleeves',F('printed_drive_sleeve'))
    add('10 First cam half A',['shaft_cam_a_outer'])

    def rotor(side):
        # Screw-side half and bearing are assembled on the bench in native coordinates.
        screw_half = 'rotor_'+side
        nut_half = screw_half+'_cap'
        direction = 60 if side=='a' else -60
        group = [screw_half]
        group.extend(a.path('Bench bearing '+side,['hardware_6704_disc_'+side],group,direction))
        nuts = F('hardware_disc_'+side+'_nut')
        a.path('Bench rotor nuts '+side,nuts,[nut_half],direction)
        group.extend(a.path('Bench nut half '+side,[nut_half]+nuts,group,direction))
        screws = F('hardware_disc_'+side+'_M3x6')
        group.extend(a.path('Bench countersunk screws '+side,screws,group,-direction))
        return group

    add('11 Complete disc A on one open cam',rotor('a'))
    add('12 Close cam A',['shaft_cam_a_inner'])
    add('13 First cam half B, reversed',['shaft_cam_b_inner'])
    add('14 Complete disc B on one open cam',rotor('b'))
    add('15 Close cam B',['shaft_cam_b_outer'])
    nutcarrier = ['shaft_mount_upper']
    nutcarrier.extend(a.path('Bench upper N nuts',F('hardware_shaft_mount_nut_upper'),nutcarrier,60))
    add('16 Upper N with captive nuts',nutcarrier)
    core = ['carrier_top']
    core.extend(a.path('Bench upper core nuts',F('hardware_carrier_top_mount_nut'),core,60))
    add('17 Upper core onto guides',core)
    add('18 Twenty loose outer contacts',F('printed_contact_sleeve'))

    upper = ['output_cap_cylinder']
    upper.extend(a.path('Bench upper 6810',['hardware_6810_top'],upper,-60))
    upper.extend(a.path('Bench upper carrier cap',['carrier_top_cap'],upper,60))
    upper.extend(a.path('Bench upper support 6704',['hardware_6704_top'],upper,-60))
    upper.extend(a.path('Bench upper E from outside',['shaft_end_upper'],upper,60))
    upper.extend(a.path('Bench upper output plate',['output_cap_plate'],upper,-60))
    add('19 Complete upper bearing unit',upper)

    add('20 Lower shaft tie nut',F('hardware_shaft_tie_nut_lower'),-60)
    add('21 Upper shaft tie nut',F('hardware_shaft_tie_nut_upper'),60)
    # Thread engagement is represented by nominal smooth bores in the reference nuts.
    add('22 Lower shaft tie screw',F('hardware_shaft_M3x35_lower'),-60)
    add('23 Upper shaft tie screw',F('hardware_shaft_M3x35_upper'),60)
    add('24 Lower guide nuts',F('hardware_drive_nuts'),-60)
    add('25 Guide screws',F('hardware_drive_shanks','hardware_drive_caps'),60)
    add('26 Lower outer-ring nuts',F('hardware_M3_ring_nuts'),-60)
    add('27 Outer-ring screws',F('hardware_ring_M3_shanks','hardware_ring_cap_heads'),60)
    assert len(set(lower)) == len(a.shapes) == len(lower)

    # Record why the tempting alternative orders fail.
    a.path('Blocked: upper bearing over already fitted E',
           ['hardware_6704_top'],['shaft_end_upper'],60,False)
    a.path('Blocked: disc A over both cam shoulders',
           ['hardware_6704_disc_a'],['shaft_cam_a_outer','shaft_cam_a_inner'],60,False)
    a.path('Blocked: outer contact through closed upper plate',
           ['printed_contact_sleeve'],['output_cap_plate'],60,False)
    assert all(not r['clear'] for r in a.records if r['step'].startswith('Blocked:'))
    report=dict(master_sha256=json.loads((PART/'native_export_verification.json').read_text())['source_sha256'],
                method='Continuous axial boundary-face sweeps of native STEP solids',
                maximum_allowed_overlap_mm3=.03,boolean_checks=a.boolean_checks,
                bodies_installed=len(lower),steps=list(a.records),
                note='Nominal CAD solids. Thread envelopes are smooth. Printed fits and hand/tool grip require physical confirmation.')
    access_checks(a,report)
    output.write_text(json.dumps(report,indent=2),encoding='utf8')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,default=PART/'assembly_sequence_verification.json')
    p.add_argument('--access-only',action='store_true')
    args=p.parse_args()
    if args.access_only:
        report=json.loads(args.output.read_text())
        access_checks(Audit(),report)
        args.output.write_text(json.dumps(report,indent=2),encoding='utf8')
    else:
        run(args.output)
