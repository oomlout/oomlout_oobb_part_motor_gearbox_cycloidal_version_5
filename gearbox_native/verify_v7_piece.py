import argparse,json,math
from pathlib import Path
from OCP.gp import gp_Trsf,gp_Vec,gp_Ax1,gp_Pnt,gp_Dir
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from oobb_solidcraft.compiler import compile_thing
from gearbox_native.configurator import recipe
from gearbox_native import controls,acceptance
from gearbox_native.exact_geometry import build_shape
from gearbox_native.simple import build


def reference(name,values=None):
    c=recipe(values or controls.defaults())[2]
    thing=dict(id='independent_'+name,mode='3dpr',**build(c)[name]['thing'])
    shape=build_shape(compile_thing(thing)['tree'])
    z=0
    if name=='eccentric_hub_lower':z=c['drive_start']
    if name=='eccentric_hub_upper':z=c['hub_split_z']
    if name.startswith('output_casing'):
        if name.endswith('lower'):
            tr=gp_Trsf();tr.SetRotation(gp_Ax1(gp_Pnt(0,0,0),gp_Dir(1,0,0)),math.pi)
            shape=BRepBuilderAPI_Transform(shape,tr,True).Shape()
        z=c['output_casing_split_z']
    if z:
        tr=gp_Trsf();tr.SetTranslation(gp_Vec(0,0,z));shape=BRepBuilderAPI_Transform(shape,tr,True).Shape()
    return shape


def verify(folder,name):
    folder=Path(folder).resolve();shape=reference(name)
    report={'piece':name,'step':acceptance.verify_step(folder/'gearbox.step',shape)}
    report['mesh']=acceptance.verify_mesh(folder/'gearbox.stl',shape)
    report['status']='passed'
    (folder/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(name,'passed',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');p.add_argument('name');a=p.parse_args();verify(a.folder,a.name)
