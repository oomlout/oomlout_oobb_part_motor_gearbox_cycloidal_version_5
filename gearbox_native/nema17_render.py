"""Render the exported motor variant, keeping native body placements and colours."""
import argparse
import json
import subprocess
from pathlib import Path
import numpy as np
import trimesh
from gearbox_native.nema17_double_bearing import PROJECT,PART_ID


def stage(views,cache):
    cache.mkdir(parents=True,exist_ok=True)
    states={label:{r['name']:np.array([r['bbox']['min'],r['bbox']['max']]) for r in
                   json.loads((views/(label+'_health.json')).read_text(encoding='utf8'))['bodies']}
            for label in ('assembled','exploded')}
    meshes=trimesh.load_mesh(views/'exploded.stl').split(only_watertight=False)
    boxes=np.array([m.bounds for m in meshes]);models={};assigned=set();circles={}
    for name,box in states['exploded'].items():
        if name=='connected_contact_ring':continue
        error=abs(boxes-box).max(axis=(1,2));i=int(error.argmin())
        assert error[i]<.08 and i not in assigned,(name,error[i]);assigned.add(i)
        if name in ('output_circle_plate','output_circle_rear_plate','output_lower_row_plate','output_lower_row_rear_plate'):
            circle=meshes[i].copy()
            circle.apply_translation([-box[:,0].mean(),0 if name.startswith('output_lower_row') else -box[:,1].mean(),-box[0,2]])
            circles[name]=circle
        if name in ('output_lower_row_plate','output_circle_plate','output_circle_rear_plate','output_plain_circle_plate','output_lower_row_rear_plate'):continue
        mesh=meshes[i].copy();mesh.apply_translation((states['assembled'][name]-box).mean(axis=0))
        models[name+'_v']=np.array(mesh.vertices,dtype='float32');models[name+'_f']=np.array(mesh.faces,dtype='int32')
    for tag,name in [('top','output_cap_plate'),('bottom','output_nut_plate')]:
        key='output_circle_rear_plate' if tag=='bottom' and 'output_circle_rear_plate' in circles else 'output_circle_plate'
        mesh=circles[key].copy()
        mesh.apply_translation([0,0,states['assembled'][name][0,2]])
        models['circular_'+tag+'_v']=np.array(mesh.vertices,dtype='float32')
        models['circular_'+tag+'_f']=np.array(mesh.faces,dtype='int32')
    if 'output_lower_row_rear_plate' in circles:
        for tag,source,target in [('top','output_lower_row_plate','output_cap_plate'),('bottom','output_lower_row_rear_plate','output_nut_plate')]:
            mesh=circles[source].copy();mesh.apply_translation([0,0,states['assembled'][target][0,2]])
            models['asymmetric_'+tag+'_v']=np.array(mesh.vertices,dtype='float32')
            models['asymmetric_'+tag+'_f']=np.array(mesh.faces,dtype='int32')
    np.savez(cache/'studio.npz',**models)


def main(views,part=None):
    views=Path(views).resolve()
    parameters=json.loads((views/'export.json').read_text(encoding='utf8'))['parameters']['parameters']
    motor_depth=next(p['value'] for p in parameters if p['name']=='motor_depth')
    cache=views.parent/'studio';stage(views,cache)
    subprocess.run(['blender','--background','--python',str(PROJECT/'gearbox_native/nema17_studio.py'),'--',str(cache)],check=True)
    from PIL import Image,ImageDraw,ImageFont
    part=Path(part) if part else PROJECT/'parts'/PART_ID
    part.mkdir(parents=True,exist_ok=True)
    labels=[('square','NEMA17 adapter — square output plates'),('circular','NEMA17 adapter — matching circular OOBB flanges')]
    if (cache/'asymmetric.png').exists():labels.append(('asymmetric','Compact upper bracket — two full OOBB mounting rows'))
    if (cache/'rear.png').exists():labels.append(('rear','Rear mounting faces — black fixed, teal rotating'))
    for tag,title in labels:
        raw=Image.open(cache/(tag+'.png')).convert('RGBA')
        page=Image.new('RGB',(1400,1280),'#faf8f4');page.paste(raw,(0,60),raw)
        draw=ImageDraw.Draw(page);font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',30)
        draw.text((36,22),title,font=font,fill='#202323')
        draw.text((36,1200),f'{motor_depth:g} mm motor body • 5 mm flange coupler • M3 socket caps ≤ 40 mm',font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',23),fill='#202323')
        draw.text((36,1240),'AI-generated CAD illustration. Errors possible. Motor connector and supplied grub screws omitted.',font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',17),fill='#555555')
        page.save(part/('render_'+tag+'.png'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('views',type=Path);p.add_argument('--destination',type=Path)
    args=p.parse_args();main(args.views,args.destination)
