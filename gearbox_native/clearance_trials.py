"""Reproduce the native 35:1 running-clearance experiments and sampled motion checks."""
import json
import math
import numpy as np
from pathlib import Path
from shapely.geometry import Polygon,MultiPoint
from shapely.affinity import translate,rotate
from oobb_solidcraft.registry import discover
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from gearbox_native.native_v9_drive import parameters,PROJECT,common,base
from gearbox_native.acceptance import health_check,verify_mesh
from gearbox_native.verification import read_step
from oobb_solidcraft.validation import inspect_shape

def run(output=None):
    out=Path(output) if output else PROJECT / "build/native_v9/clearance_trials_01"
    out.mkdir(parents=True,exist_ok=True)
    geometry=base.profile_geometry()
    cases=[('original',.2,.2,.15),('balanced',.15,.1,.1),('close',.1,.05,.05)]
    report={}
    with MCPClient(out/'author',allow_path=PROJECT,timeout=600) as client:
        d=discover().module('native_design').Design(client);parameters(d)
        common.rotor(d,0,geometry);common.rotor(d,1,geometry)
        d.move(translate=[65,0,0])
        for name,profile,guide,post in cases:
            folder=out/name;folder.mkdir(exist_ok=True)
            require_ok(client.execute('parameters.change',changes={'profile_clearance':f'{profile} mm','guide_running_clearance':f'{guide} mm','post_running_clearance':f'{post} mm'}))
            health_check(client,folder/'health.json')
            params=require_ok(client.execute('parameters.list',filter='user'))
            v={p['name']:p['value'] for p in params['parameters']}
            validated=discover().module('cycloidal_pattern').validate_edit(geometry,dict(ring_pin_count=35,pitch_radius=v['pitch'],eccentricity=v['eccentricity'],roller_radius=v['contact_radius'],clearance=profile))
            require_ok(client.call('save',dict(path=str(folder/'3dpr.solidcraft'))))
            for ext in ('step','stl'):
                require_ok(client.call('export',dict(path=str(folder/('3dpr.'+ext)))))
            shape=read_step(folder/'3dpr.step')
            assert inspect_shape(shape)['valid']
            mesh=verify_mesh(folder/'3dpr.stl',shape)
            points=np.array(validated['points'])
            cycle=[]
            for i in range(34):
                a=i*2*math.pi/34
                mat=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
                cycle.extend(points[:-1]@mat.T)
            poly=Polygon(cycle)
            top=rotate(poly,-180/34,origin=(0,0))
            minima=[]
            N=int(v['ring_count']);e=v['eccentricity'];r=v['pitch']
            for angle in range(0,360,2):
                th=math.radians(angle)
                ring=MultiPoint([(r*math.cos(th/N+2*math.pi*i/N),r*math.sin(th/N+2*math.pi*i/N)) for i in range(N)])
                pa=translate(poly,e*math.cos(th),e*math.sin(th))
                pb=translate(top,-e*math.cos(th),-e*math.sin(th))
                minima.append(min(pa.distance(ring),pb.distance(ring))-v['contact_radius'])
            assert min(minima)>profile-.011,(name,min(minima))
            # Profile-only freedom with the input fixed. Running-track and bearing
            # movement are excluded, so this is a comparison, not measured backlash.
            pa=translate(poly,e,0);pb=translate(top,-e,0)
            def free(deg):
                th=math.radians(deg)
                ring=MultiPoint([(r*math.cos(th+2*math.pi*i/N),r*math.sin(th+2*math.pi*i/N)) for i in range(N)])
                return min(pa.distance(ring),pb.distance(ring))>=v['contact_radius']
            lo,hi=0,5
            for _ in range(30):
                mid=(lo+hi)/2
                if free(mid):lo=mid
                else:hi=mid
            report[name]=dict(profile_clearance=profile,guide_clearance=guide,post_clearance=post,
                              pitch=v['pitch'],guide_pitch=v['guide_pitch'],post_pitch=v['post_pitch'],
                              mesh=mesh,sampling_error_mm=validated['max_sampled_chord_error_mm'],
                              motion_samples=len(minima),minimum_contact_gap_mm=min(minima),
                              profile_only_deadband_deg=2*lo,status='passed')
            (out/'report.json').write_text(json.dumps(report,indent=2))
            print(name,report[name]['minimum_contact_gap_mm'],report[name]['profile_only_deadband_deg'],flush=True)
    for name,*_ in cases:
        folder=out/name
        with MCPClient(folder/'reopen',design=folder/'3dpr.solidcraft',allow_path=PROJECT,timeout=600) as client:
            health_check(client,folder/'reopened_health.json')
    print('Trials passed',flush=True)

if __name__ == "__main__":
    run()
