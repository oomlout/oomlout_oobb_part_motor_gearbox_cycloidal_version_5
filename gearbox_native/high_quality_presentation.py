"""Generate/cache gearbox-sized native assets using the shared HQ library.

Explicit Python authoring, no AI or SCAD. This extends the library's authoring
recipes; normal renders reuse the saved, verified native files and their meshes.
"""
import copy
import hashlib
import importlib
import json
import math
from pathlib import Path
import shutil
import uuid


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def specifications(c):
    from oobb_solidcraft._loader import load
    root=load('high_quality_hardware')
    families=importlib.import_module(root.__name__+'.families')
    builder=importlib.import_module(root.__name__+'.build')
    result={}
    def screw(model,family,d,length):
        if family=='countersunk':p=copy.deepcopy(builder.PARAMETERS)
        else:p=copy.deepcopy(families.SPECS['socket_cap_m3_25mm_hex' if family=='socket_cap' else 'bolt_m3_25mm_hex_head']['parameters'])
        p.update(diameter=d,length=length)
        if d==6:
            p.update(head_af=10,head_height=4,bevel=.4,tip_chamfer=.4,runout=.8)
        if 'thread_length' in p:p['thread_length']=min(18,length-(p['head_height']+.5 if family=='countersunk' else .5))
        if p.get('thread_length',1)<=0:raise ValueError('Fastener is too short for its detailed head')
        result[model]=dict(family=family,parameters=p,designation=f'M{d:g}x{.5 if d==3 else 1:g}',pitch=.5 if d==3 else 1)
    screw('screw_guide','bolt',6,c['guide_bolt_length'])
    # Keep threads below the lower guide bearing; its inner race runs on the
    # bolt's smooth shank. Threading the whole shaft would misrepresent V4.
    smooth=c['guide_bolt_head_z']-c['guide_bearing_z'][0]+c['guide_bearing']['depth']/2
    result['screw_guide']['parameters']['thread_length']=min(18,c['guide_bolt_length']-smooth-.5)
    if result['screw_guide']['parameters']['thread_length']<=0:raise ValueError('Guide bolt needs a longer smooth shank')
    screw('screw_hub','bolt',6,c['hub_bolt_length'])
    screw('screw_housing',c['housing_screw_style'],3,c['housing_screw_length'])
    screw('screw_flange','socket_cap',3,c['coupling_screw_length'])
    for name,key in [('motor','motor_screw_length'),('disc','disc_join_length'),('deck','deck_screw_length'),
                     ('post','post_screw_length'),('front_hub','front_hub_screw_length')]:screw('screw_'+name,'countersunk',3,c[key])
    result['nut_m3']=copy.deepcopy(families.SPECS['nut_m3_hex'])
    result['nut_m3'].update(existing_asset='nut_m3_hex',pitch=.5,designation='M3x0.5')
    result['nut_m6']=dict(family='nut',designation='M6x1',pitch=1,
        parameters=dict(diameter=6,tap_diameter=5,head_af=10,height=5,bevel=.4,mouth_radius=3.25))
    for kind in ('guide','eccentric','shaft','output'):
        s=c[kind+'_bearing'];ro,ri,h=s['od']/2,s['id']/2,s['depth']
        pitch=(ro+ri)/2;ball=min((ro-ri)*.28,h*.28)
        count=max(7,min(32,int(2*math.pi*pitch/(2.6*ball))))
        result['bearing_'+kind]=dict(family='bearing',closure='open',ball_count=count,
            detail=dict(cage_scale=ball/1.98,window_encloses_relief=True),parameters=dict(bore=s['id'],outside=s['od'],width=h,
            edge=min(.3,h*.05),pitch_radius=pitch,ball_radius=ball,groove_radius=ball*1.025,
            inner_shoulder=pitch-ball*.65,outer_shoulder=pitch+ball*.65))
    result['grub']=dict(family='grub',designation='M3x0.5',pitch=.5,
        parameters=dict(length=3,diameter=3,hex_af=1.5,hex_depth=1,tip_chamfer=.15,thread_length=2.7))
    return result


def check_mesh(path,spec):
    import numpy as np
    import trimesh
    from oobb_solidcraft._loader import load
    validation=importlib.import_module(load('high_quality_hardware').__name__+'.validation')
    mesh=trimesh.load(path,force='mesh');p=spec['parameters'];family=spec['family']
    count=spec['ball_count']+4 if family=='bearing' else 1
    if not mesh.is_watertight or not mesh.is_winding_consistent or not mesh.is_volume or mesh.body_count!=count:
        raise ValueError(f'{family}: invalid presentation mesh: {mesh.body_count} bodies; expected {count}')
    result=dict(status='passed',watertight=True,body_count=mesh.body_count,triangles=len(mesh.faces),bounds_mm=mesh.bounds.tolist())
    if family=='bearing':
        expected=[[-p['outside']/2,-p['outside']/2,-p['width']/2],[p['outside']/2,p['outside']/2,p['width']/2]]
        if np.max(np.abs(mesh.bounds-expected))>.05:raise ValueError('Bearing envelope changed')
        balls=[m for m in mesh.split() if np.max(np.abs(m.extents-2*p['ball_radius']))<.05]
        if len(balls)!=spec['ball_count']:raise ValueError('Missing bearing rolling elements')
        result.update(rolling_elements=len(balls),bore_mm=p['bore'],outside_mm=p['outside'],width_mm=p['width'])
    else:
        pitch=spec['pitch'];length=p.get('length',p.get('height'))
        z0,z1=(0,p['height']) if family=='nut' else (-length,p['head_height'] if family in ('socket_cap','bolt') else 0)
        if np.max(np.abs(mesh.bounds[:,2]-[z0,z1]))>.05:raise ValueError('Fastener length changed')
        start=.7*pitch if family=='nut' else -length+max(.65,1.5*pitch)
        zs=np.linspace(start,start+pitch,41)
        a=validation.radial_hits(mesh,zs,0);b=validation.radial_hits(mesh,zs+pitch/2,math.pi)
        other=validation.radial_hits(mesh,zs,math.pi)
        phase=float(np.max(np.abs(a-b)))
        if phase>.06 or np.ptp(a)<pitch*.22 or np.max(np.abs(a-other))<pitch*.15:
            raise ValueError(f'Missing/incorrect modeled helix: phase={phase}, range={np.ptp(a)}')
        result.update(thread_pitch_mm=pitch,thread_half_turn_error_mm=phase,radius_range_mm=[float(a.min()),float(a.max())])
    return result


def author_grub(client,spec,families):
    a=families.Author(client)
    for name,value in spec['parameters'].items():a.run('parameters.add',name=name,expression=f'{value} mm')
    a.revolve('screw',[[0,'-length'],['diameter/2-tip_chamfer','-length'],['diameter/2','-length+tip_chamfer'],
        ['diameter/2','-tip_chamfer'],['diameter/2-tip_chamfer',0],[0,0]])
    a.hex('grub_socket','hex_af','-hex_depth','hex_depth+.1 mm','cut','screw')
    a.run('solid.thread',face=[1.5,0,-2],designation=spec['designation'],length='thread_length',modeled=True)
    a.metal(['screw'])


def ensure_asset(model,spec,folder):
    from oobb_solidcraft._loader import load
    from oobb_solidcraft.mcp import MCPClient
    from oobb_solidcraft.backend import require_ok
    from gearbox_native.acceptance import health_check
    root=load('high_quality_hardware')
    families=importlib.import_module(root.__name__+'.families')
    builder=importlib.import_module(root.__name__+'.build')
    source=[Path(__file__),Path(families.__file__),Path(builder.__file__)]
    fingerprint=hashlib.sha256(json.dumps(dict(spec=spec,sources={str(p):digest(p) for p in source}),sort_keys=True).encode()).hexdigest()
    # Same size shared by different mechanical roles is generated only once.
    folder=Path(folder)/fingerprint[:16];folder.mkdir(parents=True,exist_ok=True)
    manifest=folder/'manifest.json'
    if manifest.exists():
        record=json.loads(manifest.read_text())
        if record['fingerprint']==fingerprint and all(digest(folder/f)==h for f,h in record['hashes'].items()):
            print('Reusing HQ',model,flush=True);return record,folder
    # A helper source update need not rebuild unchanged, validated geometry.
    # Only reuse an identical parameter specification with intact native/STL
    # hashes, and repeat the current independent presentation checks.
    for prior in folder.parent.glob('*/manifest.json'):
        old=json.loads(prior.read_text())
        if old.get('status')!='passed' or old.get('spec')!=spec:continue
        if not all((prior.parent/f).is_file() and digest(prior.parent/f)==h for f,h in old['hashes'].items()):continue
        checked=check_mesh(prior.parent/'hardware.stl',spec)
        for name in ('hardware.solidcraft','hardware.stl','preview.png'):
            if (prior.parent/name).is_file():shutil.copyfile(prior.parent/name,folder/name)
        record=copy.deepcopy(old)
        record.update(fingerprint=fingerprint,validation=checked,revalidated_from=str(prior))
        manifest.write_text(json.dumps(record,indent=2)+'\n')
        print('Revalidated HQ',model,flush=True)
        return record,folder
    print('Generating HQ',model,spec['family'],spec['parameters'],flush=True)
    native,mesh=folder/'hardware.solidcraft',folder/'hardware.stl'
    attempt=folder/('attempt_'+uuid.uuid4().hex[:8]);attempt.mkdir()
    if spec.get('existing_asset'):
        paths,record=root.verified_asset(spec['existing_asset'])
        shutil.copyfile(paths['solidcraft'],native);shutil.copyfile(paths['stl'],mesh)
        checked=check_mesh(mesh,spec)
        method='verified saved high-quality library item'
    else:
        with MCPClient(attempt/'author',allow_path=folder,timeout=600) as client:
            if spec['family']=='countersunk':builder.author(client,spec['parameters'],designation=spec['designation'])
            elif spec['family']=='grub':author_grub(client,spec,families)
            else:families.author(client,spec)
            health_check(client,attempt/'native_health.json')
            require_ok(client.call('save',{'path':str(native)}))
        with MCPClient(attempt/'reopen',design=native,allow_path=folder,timeout=600) as client:
            health_check(client,attempt/'reopened_health.json')
            require_ok(client.call('export',{'path':str(mesh)}))
            require_ok(client.call('screenshot',{'path':str(folder/'preview.png'),'source':'model','view':'iso',
                       'width':1000,'height':800,'grid':False,'axes':False}))
        checked=check_mesh(mesh,spec)
        method='shared high_quality_hardware native authoring recipes'
    record=dict(status='passed',fingerprint=fingerprint,spec=spec,validation=checked,method=method,
        hashes={p.name:digest(p) for p in (native,mesh)},scope='native editable presentation and STL; not certified STEP',
        bearing_internals='illustrative internals, not a bearing-manufacturer reconstruction')
    manifest.write_text(json.dumps(record,indent=2)+'\n')
    return record,folder


def upgrade(rows,c,folder):
    specs=specifications(c);resolved={};manifest=[]
    named=Path(folder)/'named';named.mkdir(parents=True,exist_ok=True)
    for model in dict.fromkeys(row['model'] for row in rows):
        if model not in specs:continue
        record,path=ensure_asset(model,specs[model],folder)
        for ext in ('.solidcraft','.stl'):
            shutil.copyfile(path/('hardware'+ext),named/(model+ext))
        (named/(model+'.json')).write_text(json.dumps(dict(model=model,cache=str(path),**record),indent=2)+'\n')
        resolved[model]=(record,path);manifest.append(dict(model=model,path=str(path),named_native=str(named/(model+'.solidcraft')),**record))
    for row in rows:
        if row['model'] in resolved:
            record,path=resolved[row['model']]
            row['assets']=[dict(stl=str(named/(row['model']+'.stl')),color=[.53,.58,.62,1],sha256=digest(path/'hardware.stl'))]
            row['native_document']=str(named/(row['model']+'.solidcraft'))
            row['hardware_quality']='high_quality_hardware'
            row['hardware_spec']=record['spec']
        else:row['hardware_quality']='parametric accessory'
    (Path(folder)/'library_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return rows
