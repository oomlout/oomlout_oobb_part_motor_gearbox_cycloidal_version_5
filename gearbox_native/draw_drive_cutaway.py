"""Label the revised drive using sections of the published native STL exports."""
import argparse
import json
from pathlib import Path
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from matplotlib.path import Path as Outline


def draw(part):
    v = json.loads((part/'native_export_verification.json').read_text(encoding='utf8'))['parameters']
    if (part/'native_parts/eccentric_hub_lower_a.stl').is_file():
        from gearbox_native.split_stack_outputs import draw as split_stack
        return split_stack(part,v)
    holder = (part/'native_parts/bearing_holder.stl').exists()
    bearing = holder or (part/'native_parts/bearing_baseplate.stl').exists()
    fig, ax = plt.subplots(figsize=(13, 10), facecolor='white')
    fig.subplots_adjust(left=.02, right=.98, bottom=.13, top=.84)
    ax.set_aspect('equal'); ax.axis('off')
    ax.set(xlim=(-49, 56), ylim=(-11, 57))
    ink='#203945'; steel='#a4bacb'; brass='#f3cd69'
    def polygon(points, color, z=3):
        patch=Polygon(points, closed=True, facecolor=color, edgecolor=ink, lw=.7, zorder=z)
        ax.add_patch(patch)
        return patch
    def rect(x,z,w,h,color,layer=4):
        return polygon([(x,z),(x+w,z),(x+w,z+h),(x,z+h)],color,layer)
    def section(name,dz,color,crop=False):
        mesh=trimesh.load_mesh(part/'native_parts'/(name+'.stl'))
        cut=mesh.section(plane_normal=[0,1,0],plane_origin=[0,.0001,0])
        contours=[q[:,[0,2]]+[0,dz] for q in cut.discrete]
        def area(q): return abs(np.sum(q[:-1,0]*q[1:,1]-q[1:,0]*q[:-1,1]))
        drawn=[]
        for q in sorted(contours,key=area,reverse=True):
            level=sum(Outline(prior).contains_point(q[0]) for prior in drawn)
            patch=polygon(q,'white' if level%2 else color,2)
            if crop:
                patch.set_clip_path(Rectangle((-12,-12),24,80,transform=ax.transData))
            drawn.append(q)
    def ring(x,z):
        for side in (-1,1):
            rect(x+(-10.5 if side<0 else 7.5),z,3,4,steel)
    if bearing:
        if holder:
            section('motor_mount',0,'#d8e0e6',True)
            section('bearing_holder',-v['bearing_holder_depth'],'#bfcedd',True)
        else:section('bearing_baseplate',0,'#d8e0e6',True)
        section('bearing_retainer',v['wiggle_join_head_seat'],'#a69ac5')
        ring(0,v.get('bearing_holder_bearing_z',.1))
    else:
        section('motor_spacer',-v['motor_spacer_depth'],'#d8e0e6')
    section('eccentric_hub_lower',v['lower_support_bottom'] if bearing else v['drive_base_bottom'],'#51aaa0')
    section('eccentric_hub_upper',v['seam_z'],'#e7a260')
    section('drive_sleeve',v['drive_sleeve_bottom'],'#849ecb')
    for x,z in ((v['eccentricity'],v['bottom_journal_z']+.1),(-v['eccentricity'],v['rotor_b_z']+.1),(0,v['housing_top']-4.1)):
        ring(x,z)
    seat=v['wiggle_join_head_seat']
    rect(-1.25,seat,2.5,35 if bearing else 12,steel)
    rect(-2.25,seat-2.5,4.5,2.5,steel)
    rect(-2.5,v['wiggle_join_nut_bottom'],5,2,brass)
    z=v['drive_clamp_z']; tip=v['drive_clamp_tip']
    rect(tip,z-1.5,6,3,steel); rect(tip+6,z-2.75,3,5.5,steel)
    rect(5.8,z-2.75,2.4,5.5,brass)
    if not bearing:
        rect(-2.5,-v['motor_spacer_depth'],5,v['motor_shaft_end']+v['motor_spacer_depth'],steel)
        z=v['wiggle_grub_z']
        polygon([(2.5,z-1.5),(8.64,z-1.5),(10.5,z-3.36),(10.5,z+3.36),(8.64,z+1.5),(2.5,z+1.5)],steel,4)
        rect(5,z-2.75,2.4,5.5,brass)
    def call(x,z,tx,tz,title,detail,color='#506c7d'):
        sign=1 if tx>x else -1
        ax.plot([x,tx-2*sign,tx-.5*sign],[z,tz,tz],color=color,lw=.85,zorder=8)
        ax.scatter([x],[z],s=9,c=color,zorder=9)
        ha='left' if sign==1 else 'right'
        ax.text(tx,tz+.4,title,ha=ha,va='bottom',fontsize=10.5,weight='bold',color=ink)
        ax.text(tx,tz-.3,detail,ha=ha,va='top',fontsize=9,color='#536672')
    call(5,49,18,51,'External D input','12 mm exposed; round diameter 14.90 mm')
    call(-8.6,40,-19,43,'Drive sleeve','drive_sleeve; removable keyed coupling')
    call(10.5,37.3,20,39,'Sleeve clamp','M3 x 6 socket cap + side-loaded M3 nut')
    call(2,v['wiggle_join_nut_bottom']+1,20,32,'Upper joining nut','M2.5; load before fitting sleeve')
    call(-9,29,-19,34,'Front shaft bearing','6702: 15 x 21 x 4 mm')
    call(-4,25,-19,27,'Upper hub','eccentric_hub_upper')
    call(3,21,20,24,'Hub-to-hub D joint','Short internal key; 0.05 mm allowance')
    call(9,19,20,17,'Cycloid centre bearings','2 x 6702; centres offset by +/- eccentricity')
    call(-7,10,-19,14,'Lower hub','eccentric_hub_lower')
    if bearing:
        call(-9,v.get('bearing_holder_bearing_z',.1)+2,-19,6,'Bottom support bearing','6702; separate cup below shared motor plate' if holder else '6702; bearing_baseplate shown cropped')
        call(7,v['wiggle_join_head_seat']+1,-19,-2,'Retaining washer','bearing_retainer')
        call(1,seat-1.2,20,1,'Upward joining screw','M2.5 x 35; head below the bearing cup' if holder else 'M2.5 x 35; head extends 5 mm below base')
        if holder:call(11,-5,20,8,'Separate bearing holder','bearing_holder; four NEMA17 mounting screws')
    else:
        call(1,17.2,20,10,'Upward joining screw','M2.5 x 12; fits above 24 mm motor shaft')
        call(9,-2.8,22,0,'Motor clamp','M3 x 8 countersunk; tighten through window')
        call(-17,-5,-24,-4,'Motor spacer','8 mm with full-height access gap')
    fig.text(.06,.94,'V9  /  '+('BEARING INPUT' if bearing else 'NEMA17 INPUT'),fontsize=12,weight='bold',color='#536672')
    fig.text(.06,.895,'Wiggle shaft and external drive',fontsize=26,weight='bold',color=ink)
    fig.text(.06,.86,'Actual printed profiles in axial section; nominal hardware shown without threads.',fontsize=12,color='#536672')
    fig.text(.06,.085,'The external D-shaft drives the input. The outer casing remains the reduced-speed output.',fontsize=11,color=ink)
    fig.text(.06,.055,'Tighten the axial join first, then fit and clamp the sleeve. See HARDWARE.md and EDITING_PARAMETERS.md.',fontsize=10,color=ink)
    temp=part/'shaft_cutaway_new.png'
    fig.savefig(temp,dpi=180)
    temp.replace(part/'wiggle_shaft_assembled_cutaway.png')
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('part',type=Path);a=p.parse_args();draw(a.part)
