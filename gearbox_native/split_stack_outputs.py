"""Build the two retrofit plates and the assembly card from accepted native exports."""
import json
import shutil
import numpy as np
import trimesh

from gearbox_native.split_stack import HALVES, STACK, layer_audit


def load(part,name):
    return trimesh.load_mesh(part/'native_parts'/(name+'.stl'))


def plate(part,folder,names):
    out=part/folder;out.mkdir(exist_ok=True)
    bodies=[];x=y=4.;row=0.
    for i,name in enumerate(names):
        m=load(part,name)
        assert m.is_volume and abs(m.bounds[0,2])<.01,name
        if i and i%3==0:
            x=4.;y+=row+5;row=0.
        m.apply_translation([x-m.bounds[0,0],y-m.bounds[0,1],0])
        x+=m.extents[0]+5;row=max(row,m.extents[1]);bodies.append(m)
    target=out/'3dpr.stl'
    trimesh.util.concatenate(bodies).export(target)
    shells=trimesh.load_mesh(target).split(only_watertight=False)
    assert len(shells)==len(names) and all(s.is_volume for s in shells)


def assembled(part,name,v):
    m=load(part,name)
    if name in HALVES:
        angle=-90 if name.endswith('_a') else 90
        m.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(angle),[1,0,0]))
    elif name=='bearing_retainer':
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi,[1,0,0]))
        m.apply_translation([0,0,v['lower_support_bottom']])
    elif name=='drive_sleeve':m.apply_translation([0,0,v['drive_sleeve_bottom']])
    return m


def draw(part,v):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import to_rgb
    from matplotlib.patches import Polygon,Rectangle
    from matplotlib.path import Path as Outline
    ink='#183843';grey='#4d626b';steel='#a8beca';gold='#e6b349'
    colors=['#ad91c3','#47a799','#47a799','#e5a766','#e5a766','#6f90bd']
    fig=plt.figure(figsize=(12.6,9),facecolor='white')
    fig.text(.05,.945,'Wiggle shaft  /  bearing input',size=26,weight='bold',color=ink)
    fig.text(.051,.908,f"V9  •  {v['reduction']:g}:1 gearbox     |     Six printed pieces. One M3 × 35 socket cap ties the eccentric hubs to the washer.",size=12,color=grey)
    ax=fig.add_axes([.05,.13,.40,.73]);ax.set_aspect('equal');ax.axis('off')
    ax.set(xlim=(-34,34),ylim=(-21,103),title='Exploded printed parts')
    # Orthographic projection of real native meshes. Only explode their placement.
    u=np.array([.80,.60,0]);w=np.array([-.24,.32,.9165]);eye=np.cross(u,w)
    for name,c in zip(STACK,colors):
        m=assembled(part,name,v)
        level=0 if name=='bearing_retainer' else 1 if '_lower_' in name else 2 if '_upper_' in name else 3
        side=1 if name.endswith('_a') else -1 if name.endswith('_b') else 0
        m.apply_translation([0,side*13,(-8,4,22,47)[level]])
        indices=np.flatnonzero(m.face_normals@eye>1e-6)
        order=indices[np.argsort(m.triangles_center[indices]@eye)]
        tri=m.triangles[order]
        polys=np.stack((tri@u,tri@w),axis=-1)
        light=.63+.33*np.maximum(0,m.face_normals[order]@np.array([-.35,-.55,.75]))
        fill=np.clip(light[:,None]*to_rgb(c),0,1)
        ax.add_collection(PolyCollection(polys,facecolors=fill,edgecolors=fill,linewidths=.18,antialiaseds=False))
    for z,label in [(-15,'1'),(11,'2'),(45,'3'),(82,'4')]:
        ax.text(-28,z,label,ha='center',va='center',size=11,color='white',weight='bold',
                bbox=dict(boxstyle='circle,pad=.32',fc=ink,ec='none'))
    ax=fig.add_axes([.44,.13,.54,.73]);ax.set_aspect('equal');ax.axis('off')
    ax.set(xlim=(-13,59),ylim=(-13,59),title='Assembled axial section')
    def rect(x,z,w,h,c):
        ax.add_patch(Rectangle((x,z),w,h,fc=c,ec=ink,lw=.65))
    for i in (0,1,3,5):
        m=assembled(part,STACK[i],v)
        cut=m.section(plane_origin=[0,.005,0],plane_normal=[0,1,0])
        sections=[q[:,[0,2]] for q in cut.discrete]
        drawn=[]
        for q in sorted(sections,key=lambda q:abs(np.sum(q[:-1,0]*q[1:,1]-q[1:,0]*q[:-1,1])),reverse=True):
            inside=sum(Outline(prev).contains_point(q[0]) for prev in drawn)
            ax.add_patch(Polygon(q,fc='white' if inside%2 else colors[i],ec=ink,lw=.65))
            drawn.append(q)
    for x,z in [(0,v['bearing_holder_bearing_z']),(v['eccentricity'],v['bottom_journal_z']+.1),
                (-v['eccentricity'],v['rotor_b_z']+.1),(0,v['housing_top']-4.1)]:
        for a in (-10.5,7.5):rect(x+a,z,3,4,steel)
    seat=v['wiggle_join_head_seat'];nut=v['wiggle_join_nut_bottom'];clamp=v['drive_clamp_z']
    rect(-1.5,seat,3,35,steel);rect(-2.75,seat-3,5.5,3,steel)
    for x in (-2.75,1.5):rect(x,nut,1.25,2.4,gold)
    rect(v['drive_clamp_tip'],clamp-1.5,6,3,steel);rect(v['drive_clamp_tip']+6,clamp-2.75,3,5.5,steel)
    for z in (clamp-2.75,clamp+1.5):rect(5.8,z,2.4,1.25,gold)
    labels=[(5,v['drive_extension_top']-4,52,'4   External D-sleeve','Slide onto the keyed stem after tightening the tie.'),
            (v['drive_clamp_tip']+7.5,clamp,44,'Radial sleeve clamp','M3 × 6 socket cap and its own M3 nut.'),
            (2.25,nut+1,36,'Captive axial M3 nut','Load sideways before fitting the sleeve.'),
            (5.3,21,28,'3   Upper eccentric hub · A + B','The asymmetric key sets the disc phase.'),
            (5.6,10,17,'2   Lower eccentric hub · A + B','The 6702 inner races locate the halves.'),
            (1.3,2.5,6,'M3 × 35 axial screw','35 mm under the head; enters from below.'),
            (4,-7,-5,'1   Retaining washer','Wide face against the lower inner race.')]
    for x,z,ty,a,b in labels:
        ax.plot([x,13.8,15],[z,ty,ty],color=grey,lw=.75);ax.scatter([x],[z],s=7,color=ink,zorder=8)
        ax.text(16,ty+.55,a,fontsize=10,weight='bold',color=ink)
        ax.text(16,ty-.42,b,fontsize=8.6,color=grey,va='top')
    fig.text(.051,.083,'PRINT   Lay the four hub halves on their flat split faces. The supplied STL is already oriented.',fontsize=11,weight='bold',color=ink)
    fig.text(.051,.048,'ASSEMBLY   Match each A/B pair, load the upper nut, tighten the axial screw, then fit and clamp the sleeve. Steel hardware shown without threads.',fontsize=10,color=grey)
    target=part/'shaft_stackup.png';fig.savefig(target,dpi=155);plt.close(fig)
    shutil.copyfile(target,part/'wiggle_shaft_assembled_cutaway.png')


def make_outputs(part,values):
    from gearbox_native.publish_native_drive import hardware
    plate(part,'shaft_reprint',STACK)
    plate(part,'bearing_conversion',('bearing_holder',*STACK))
    results={n:layer_audit(load(part,n)) for n in STACK}
    assert all(r['unsupported_islands']==0 for r in results.values()),results
    (part/'shaft_reprint/printability.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf8')
    hardware(part,values,True);draw(part,values)
    instructions="""The lower and upper eccentric hubs each have two longitudinal halves. Print them on the supplied flat faces. Print the retainer wide face down and the open D-sleeve upright. Keep the A/B pairs together. Seat the lower pair inside the lower 6702 races. Engage the upper pair on the asymmetric key, load the M3 nut across the upper split, and capture the journals in their bearing races. Fit the retainer with its wide face against the bottom inner race. Insert one M3 × 35 socket cap from below and tighten into the nut. Slide on the D-sleeve; fit its separate M3 nut and M3 × 6 radial clamp. Allow 3.5 mm beneath the cup for the retaining collar.

Both axial fastener cutouts use OOBB overhang relief. The shaft is printed; the screw clamps it axially. The bearing races and keyed drive sleeve hold the split halves radially. Use the [stack-up graphic](../shaft_stackup.png) and [hardware list](../HARDWARE.md).
"""
    audit='\nThe [0.2 mm layer check](printability.json) compares successive sections of each print-oriented STL. No part starts a disconnected island. The longest horizontal step between layers is '+f"{max(r['maximum_lateral_reach_mm'] for r in results.values()):.2f} mm"+' at a small fastener relief. This is a geometric check; bridging and fit still depend on the printer.\n'
    (part/'shaft_reprint/README.md').write_text('# Shaft-only reprint · six pieces\n\nPrint [3dpr.stl](3dpr.stl). Reuse the existing detachable cup, bearings, gearbox and motor plate.\n\n'+instructions+audit,encoding='utf8')
    (part/'bearing_conversion/README.md').write_text('# Stepper to bearing input · seven pieces\n\nPrint [3dpr.stl](3dpr.stl). Includes the detachable 6702 cup and all six shaft pieces. Reuse the shared motor plate, front carrier, two rotors and three casing pieces.\n\n'+instructions,encoding='utf8')
    with (part/'README.md').open('a',encoding='utf8') as stream:
        stream.write('\n[Shaft-only reprint (6 pieces)](shaft_reprint/3dpr.stl) · [Bearing conversion with cup (7 pieces)](bearing_conversion/3dpr.stl) · [Stack-up drawing](shaft_stackup.png) · [Assembly order](shaft_reprint/README.md) · [Hardware](HARDWARE.md)\n')
