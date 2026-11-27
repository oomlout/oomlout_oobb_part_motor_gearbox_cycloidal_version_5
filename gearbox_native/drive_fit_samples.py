"""Printable gauges for the 6702 journals and shared D-drive socket."""
import json
from gearbox_native.native_v9_drive import PROJECT,parameters,d_profile
from oobb_solidcraft.registry import discover
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from gearbox_native.acceptance import health_check,verify_mesh
from gearbox_native.verification import read_step

def run():
    out=PROJECT/'build/native_v9/drive_fit_samples_01';out.mkdir(parents=True,exist_ok=True)
    with MCPClient(out/'author',allow_path=PROJECT,timeout=600) as client:
        d=discover().module('native_design').Design(client);parameters(d)
        samples=[]
        for index,clearance in enumerate((.075,.05,.025)):
            name=f'journal_sample_{index+1}'
            d.component(name)
            d.cylinder(10,2,operation='new',name='label_base')
            d.cylinder(7.5-clearance,5,z=2,name='6702_fit')
            d.holes(.65,1,z=1,positions=[(-2+j*2,8.5) for j in range(index+1)],name='sample_number')
            d.move(translate=[index*25,0,0])
            samples.append(dict(name=name,radial_clearance_mm=clearance,diameter_mm=15-2*clearance))
        d.component('D_key_gauge');d.cylinder(7,2,operation='new')
        d_profile(d,'drive_key_radius','drive_key_flat','7 mm','2 mm','join')
        d.move(translate=[0,25,0])
        for index,clearance in enumerate((.1,.05,.025)):
            name=f'D_socket_sample_{index+1}';d.component(name)
            d.cylinder(9,6,operation='new')
            d_profile(d,f'drive_key_radius + {clearance} mm',f'drive_key_flat + {clearance} mm','6.02 mm','-0.01 mm','cut')
            d.holes(.65,1,z=5,positions=[(-2+j*2,7.2) for j in range(index+1)],name='sample_number')
            d.move(translate=[(index+1)*22,25,0])
            samples.append(dict(name=name,radial_clearance_mm=clearance))
        health_check(client,out/'health.json')
        require_ok(client.call('save',dict(path=str(out/'3dpr.solidcraft'))))
        for ext in ('step','stl'):
            require_ok(client.call('export',dict(path=str(out/('3dpr.'+ext)))))
        mesh=verify_mesh(out/'3dpr.stl',read_step(out/'3dpr.step'))
        (out/'samples.json').write_text(json.dumps(dict(samples=samples,mesh=mesh),indent=2))
    print('Fit samples ready',flush=True)

if __name__=='__main__':run()
