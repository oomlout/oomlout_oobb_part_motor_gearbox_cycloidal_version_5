"""Validate saved V7 parameters without regenerating any native geometry."""
import argparse,json,math,hashlib
from pathlib import Path
import numpy as np
import trimesh
from OCP.STEPControl import STEPControl_Writer,STEPControl_AsIs
from OCP.IFSelect import IFSelect_RetDone
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.compiler import compile_thing
from oobb_solidcraft.registry import discover
from gearbox_native import acceptance,controls
from gearbox_native.configurator import recipe
from gearbox_native.exact_geometry import build_shape,_move
from gearbox_native.verification import read_step
from gearbox_native.presentation import assembly_parts,pose
from gearbox_native.simple import build
from gearbox_native.native_v7 import PRINT_POSITIONS

CASES={
    'baseline':{},
    'reduction_16':{'reduction':16},
    'dimensions':{'eccentricity':1.35,'contact_radius':2.9,'profile_clearance':.22,
        'disc_thickness':5.2,'disc_gap':.6,'casing_wall':2.1,'radius_buffer':.05,
        'guide_pitch_radius':17.45,'standoff_pitch_radius':18.6,'standoff_radius':2.65},
    'different_bearings':{'disc_thickness':6,'eccentricity':1.,'guide_pitch_radius':18.2,
        'standoff_pitch_radius':19.5,'bottom_bearing':6803},
    'M6_guides':{'guide_radius':3,'eccentricity':.5,'guide_pitch_radius':18.2,'standoff_pitch_radius':20},
    'motion':{'input_angle':75},
    'print_layout':{'print_layout':1},
    'manual_pitch':{'automatic_pitch':0,'contact_pitch_radius':29.6,'top_bearing':6803,
        'disc_thickness':6,'eccentricity':1.,'guide_pitch_radius':18.2,'standoff_pitch_radius':19.5},
}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def references(values,print_layout=False):
    c=recipe(values)[2];pieces=build(c);items={i['name']:i for i in assembly_parts(c)}
    shapes={};transforms={}
    for name,piece in pieces.items():
        thing=dict(id='independent_'+name,mode='3dpr',**piece['thing'])
        local=build_shape(compile_thing(thing)['tree'])
        if print_layout:location=[*PRINT_POSITIONS[name],0];angles=[0,0,0]
        else:location,angles=pose(items[name],c,input_turns=values['input_angle']/360)
        shape=_move(_move(local,'rotate',[math.degrees(a) for a in angles]),'translate',location)
        shapes[name]=shape;transforms[name]=(location,angles)
    return c,shapes,transforms


def localize(step,stl,where,transform):
    location,angles=transform
    local=_move(read_step(step),'translate',[-v for v in location])
    for i in (2,1,0):
        rotation=[0,0,0];rotation[i]=-math.degrees(angles[i]);local=_move(local,'rotate',rotation)
    writer=STEPControl_Writer();writer.Transfer(local,STEPControl_AsIs)
    assert writer.Write(str(where.with_suffix('.step')))==IFSelect_RetDone
    mesh=trimesh.load_mesh(stl);matrix=trimesh.transformations.euler_matrix(*angles);matrix[:3,3]=location
    mesh.apply_transform(np.linalg.inv(matrix));mesh.export(where.with_suffix('.stl'))


def verify(folder,cases,report_name='assembly_verification.json'):
    folder=Path(folder).resolve();native=folder/'gearbox.solidcraft'
    geometry=json.loads((folder/'profile.json').read_text(encoding='utf-8'))
    report_path=folder/report_name
    report=json.loads(report_path.read_text()) if report_path.exists() else {'native_only_edits':True,'native_sha256':sha(native),'cases':{}}
    assert report['native_sha256']==sha(native),'Evidence belongs to a different native source'
    report['status']='running'
    for name in cases:
        changes=CASES[name];values=dict(controls.defaults(),**{k:v for k,v in changes.items() if k in controls.SPECS})
        c,refs,transforms=references(values,bool(changes.get('print_layout')))
        path=folder/'verification'/name;path.mkdir(parents=True,exist_ok=True)
        sampling=discover().module('cycloidal_pattern').validate_edit(geometry,dict(ring_pin_count=c['ring_pin_count'],
            pitch_radius=c['pitch_radius'],eccentricity=c['radius_offset'],roller_radius=c['lobe_radius'],clearance=c['lobe_clearance']))
        row={'changes':changes,'sampling':{k:v for k,v in sampling.items() if k!='points'},'parts':{}}
        with MCPClient(path/'session',design=native,allow_path=folder,timeout=600) as client:
            acceptance.health_check(client,path/'opened_health.json')
            if changes:
                expressions={k:f"{v} {controls.SPECS[k]['unit'] if k in controls.SPECS else ''}".strip() for k,v in changes.items()}
                row['edit']=require_ok(client.execute('parameters.change',changes=expressions))
            acceptance.health_check(client,path/'edited_health.json')
            row['parameters']=require_ok(client.execute('parameters.list',filter='user'))
            measurement=require_ok(client.call('measure'));assert measurement['body_count']==8,measurement['body_count']
            require_ok(client.call('save',dict(path=str(path/'edited.solidcraft'))))
            for part,reference in refs.items():
                row['parts'][part]={'measurement':acceptance.verify_native_measurement(require_ok(client.call('measure',dict(body=part))),reference)}
                for ext in ('step','stl'):require_ok(client.call('export',dict(bodies=[part],path=str(path/f'{part}.{ext}'))))
            require_ok(client.call('screenshot',dict(source='model',path=str(path/'model.png'),view='iso',width=1200,height=900,grid=False,axes=False)))
        print(name,'native edit/export passed',flush=True)
        for part,reference in refs.items():
            partrow=row['parts'][part]
            partrow['step']=acceptance.verify_step(path/f'{part}.step',reference)
            partrow['mesh']=acceptance.verify_mesh(path/f'{part}.stl',reference)
            print(name,part,'geometry passed',flush=True)
        with MCPClient(path/'reopen',design=path/'edited.solidcraft',allow_path=folder,timeout=600) as client:
            acceptance.health_check(client,path/'reopened_health.json')
            for part,reference in refs.items():
                row['parts'][part]['reopen']=acceptance.verify_native_measurement(require_ok(client.call('measure',dict(body=part))),reference)
            require_ok(client.call('save',dict(path=str(path/'reopened.solidcraft'))))
        with MCPClient(path/'second_reopen',design=path/'reopened.solidcraft',allow_path=folder,timeout=600) as client:
            acceptance.health_check(client,path/'second_reopen_health.json')
            row['second_reopen_body_count']=require_ok(client.call('measure'))['body_count'];assert row['second_reopen_body_count']==8
        # Native exports are brought back into each part's print coordinates for
        # the existing motion, installation and hardware access acceptance suite.
        local=path/'local';local.mkdir(exist_ok=True);files={}
        for part in refs:
            localize(path/f'{part}.step',path/f'{part}.stl',local/part,transforms[part])
            files[part]={ext:{'path':str(local/f'{part}.{ext}'),'sha256':sha(local/f'{part}.{ext}')} for ext in ('step','stl')}
        (path/'native_case.json').write_text(json.dumps(dict(status='geometry_verified',config=c,parts=files),indent=2),encoding='utf-8')
        row['status']='passed';report['cases'][name]=row
        report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(name,'passed, including two reopen checks',flush=True)
    report['status']='passed'
    report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');p.add_argument('--cases',nargs='+',choices=list(CASES),default=list(CASES));p.add_argument('--report',default='assembly_verification.json');a=p.parse_args();verify(a.folder,a.cases,a.report)
