"""Render all guide stages from the current native-export mesh inventory."""
import sys,json,math,hashlib,os
from pathlib import Path
import numpy as np
import bpy
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from gearbox_native.nema17_depth40_guide import scenes,BUILD,PART
cache=Path(sys.argv[-1]).resolve()
sys.argv[-1]=str(cache)
setup=(ROOT/'gearbox_native/nema17_studio.py').read_text().split("labels=('square'")[0]
setup=setup.replace("'rear_output_extension'","'rear_output_extension','rear_output_joiner_'")
exec(compile(setup,'native_studio_setup','exec'))
scene.cycles.samples=24
data=json.loads((PART/'native_export_verification.json').read_text());v=data['parameters']
assert v['motor_depth']==40
source=objects['hardware_shaft_M3x35_lower']
points=np.array([p.co[:] for p in source.data.vertices])*[1,-1,-1]
points[:,1]-=2*v['shaft_tie_pitch']
points[:,2]+=v['shaft_face_z']+v['shaft_head_depth']+v['stack_height']-v['shaft_face_z']-v['shaft_nut_depth']
mesh=bpy.data.meshes.new('temporary_shaft_tie');mesh.from_pydata(points.tolist(),[],[list(p.vertices) for p in source.data.polygons]);mesh.update()
obj=bpy.data.objects.new('temporary_shaft_tie',mesh);scene.collection.objects.link(obj);obj.data.materials.append(bolts);objects[obj.name]=obj
records=scenes(objects)
final=next(r for r in records if r['key']=='finished')['parts']
overview={}
for n in final:
    delta=[0,0,0]
    if n.startswith(('front_cover_','hardware_endcap_front_')):delta=[0,0,65]
    elif n.startswith(('rear_output_joiner_','rear_output_extension','hardware_endcap_outer_')):delta=[160,0,-80]
    elif n.startswith(('rear_cover_','hardware_endcap_rear_')):delta=[0,0,-170]
    elif n.startswith(('motor_cage','hardware_cage_')):delta=[0,0,-125]
    elif n.startswith(('motor_inner_adapter','hardware_NEMA17_')):delta=[0,0,-60]
    elif n.startswith(('hardware_flange_','hardware_coupler_')):delta=[0,0,-25]
    overview[n]=delta
records.append(dict(key='overview',parts=overview,flip=False,look=(100,-300,100)))
lights=[(o,o.location.copy()-Vector((0,0,-15))) for o in scene.objects if o.type=='LIGHT']
all_anchors=json.loads((cache/'anchors.json').read_text()) if (cache/'anchors.json').exists() else {}
selected=set(filter(None,os.environ.get('NEMA_GUIDE_RENDER_ONLY','').split(',')))
for record in records:
    key=record['key'];visible=[]
    if selected and key not in selected:continue
    rot=Matrix.Rotation(math.pi,4,'X') if record['flip'] else Matrix.Identity(4)
    for n,obj in objects.items():
        obj.hide_render=n not in record['parts']
        if not obj.hide_render:
            obj.matrix_world=rot@Matrix.Translation(Vector(record['parts'][n]));visible.append(obj)
    bpy.context.view_layer.update()
    pts=[o.matrix_world@Vector(p) for o in visible for p in o.bound_box]
    lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)));hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    target=(lo+hi)/2;eye=Vector(record['look'])
    cam.location=target+eye.normalized()*800;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update();local=[cam.matrix_world.inverted()@p for p in pts]
    left,right=min(p.x for p in local),max(p.x for p in local);bottom,top=min(p.y for p in local),max(p.y for p in local)
    cam.location+=cam.rotation_euler.to_matrix()@Vector(((left+right)/2,(bottom+top)/2,0))
    width,height=(1500,1200) if key!='overview' else (1800,1400)
    cam_data.ortho_scale=max(right-left,(top-bottom)*width/height)*1.15
    for lamp,offset in lights:lamp.location=target+offset
    scene.render.resolution_x=width;scene.render.resolution_y=height
    scene.render.filepath=str(cache/(key+'.png'))
    bpy.context.view_layer.update();bpy.ops.render.render(write_still=True)
    anchors={}
    for o in visible:
        p=o.matrix_world@(sum((Vector(q) for q in o.bound_box),Vector())/8)
        uv=world_to_camera_view(scene,cam,p);anchors[o.name]=[float(uv.x*width),float((1-uv.y)*height)]
    all_anchors[key]=anchors
    (cache/'scenes.json').write_text(json.dumps(records,indent=2))
    (cache/'anchors.json').write_text(json.dumps(all_anchors,indent=2))
    print('GUIDE RENDER',key,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(cache/'nema17_depth40_assembly.blend'))
(cache/'render_info.json').write_text(json.dumps(dict(source_sha256=data['source_sha256'],blender=bpy.app.version_string,
    render_engine=scene.render.engine,samples=scene.cycles.samples,device=scene.cycles.device,rendered=[r['key'] for r in records]),indent=2))
