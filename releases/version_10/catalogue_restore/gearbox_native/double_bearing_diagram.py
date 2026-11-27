"""Draw the named double-bearing parts from the native exploded STL and its body bounds."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import trimesh


def draw_exploded(part, views, values):
    health = json.loads((views / 'exploded_health.json').read_text())
    shells = trimesh.load_mesh(part / 'exploded.stl').split(only_watertight=False)
    bounds = np.array([m.bounds for m in shells])
    bodies = {}
    for b in health['bodies']:
        if b['name'] == 'connected_contact_ring':
            continue
        box = np.array([b['bbox']['min'], b['bbox']['max']])
        error = np.abs(bounds - box).max(axis=(1, 2))
        assert error.min() < .08, b['name']
        bodies[b['name']] = shells[error.argmin()]
    assert len(set(map(id, bodies.values()))) == len(shells) == len(bodies)
    bodies['connected_contact_ring'] = trimesh.load_mesh(part / 'native_parts/connected_contact_ring.stl')

    paper = '#fffdf8'
    ink = '#203746'
    muted = '#4b6470'
    image = Image.new('RGB', (2990, 2050), paper)
    d = ImageDraw.Draw(image)
    def label(x, y, s, size=28, bold=False, color=ink):
        font = ImageFont.truetype('segoeuib.ttf' if bold else 'segoeui.ttf', size)
        d.text((x,y), s, font=font, fill=color, anchor='lt')

    def color(name):
        if name.startswith('hardware_'): return (139,154,163)
        if name.startswith(('output_', 'connected_', 'printed_contact')): return (53,150,173)
        if name.startswith(('carrier','printed_drive')): return (92,126,164)
        if name.startswith('rotor_a'): return (71,167,132)
        if name.startswith('rotor_b'): return (229,143,74)
        return (158,117,173)

    # Parallel projection; depth-sort CAD triangles so the near surfaces cover the far ones.
    right = np.array([.84,.54,0]); right /= np.linalg.norm(right)
    eye = np.array([right[1]*.94,-right[0]*.94,.342])
    up = np.cross(eye, right)
    def render(names, x, y, w, h):
        points=[]; depths=[]; colors=[]
        for name in names:
            m=bodies[name]; visible=(m.face_normals @ eye) > .0001
            t=m.triangles[visible]; n=m.face_normals[visible]
            points.append(np.stack((t @ right,-(t @ up)),axis=2))
            depths.append((t @ eye).mean(axis=1))
            light=np.clip(.68+.34*(n @ np.array([-.35,-.45,.82])),.43,1.05)
            colors.append((light[:,None]*color(name)).astype('uint8'))
        xy=np.concatenate(points); depth=np.concatenate(depths); rgb=np.concatenate(colors)
        lo=xy.min(axis=(0,1));hi=xy.max(axis=(0,1))
        xy=np.rint((xy-(lo+hi)/2)*min(w/(hi-lo)[0],h/(hi-lo)[1])+[x,y]).astype(int)
        for tri,c in zip(xy[np.argsort(depth)].reshape(-1,6).tolist(),rgb[np.argsort(depth)].tolist()):
            d.polygon(tri,fill=tuple(c))

    r=int(values['ring_count']); g=int(values['guide_count'])
    names = [
        ('Output and carriers', [
          ('O1c','Upper retaining cylinder','output_cap_cylinder'),('O1','Upper output plate','output_cap_plate'),('O2','Upper casing bearing / 6810','hardware_6810_top'),
          ('O3b','Upper carrier cap','carrier_top_cap'),('O3a','Upper carrier core','carrier_top'),
          ('O4a','Lower carrier core','carrier_bottom'),('O4b','Lower carrier cap','carrier_bottom_cap'),
          ('O5','Lower casing bearing / 6810','hardware_6810_bottom'),('O6','Lower output plate','output_nut_plate'),('O6c','Lower retaining cylinder','output_nut_cylinder'),('Alt','Lower-row OOBB plate','output_lower_row_plate')]),
        ('Cycloid clamshells', [
          ('B1','Disc B / screw half','rotor_b'),('B2','Disc B / 6704 bearing','hardware_6704_disc_b'),
          ('B3','Disc B / nut half','rotor_b_cap'),('A1','Disc A / nut half','rotor_a_cap'),
          ('A2','Disc A / 6704 bearing','hardware_6704_disc_a'),('A3','Disc A / screw half','rotor_a')]),
        ('Input shaft stack', [
          ('E2','Upper end journal','shaft_end_upper'),('R2','Upper support / 6704','hardware_6704_top'),
          ('N2','Upper OOBB nut carrier','shaft_mount_upper'),('C4','Bearing B / outer half','shaft_cam_b_outer'),
          ('C3','Bearing B / inner half','shaft_cam_b_inner'),('C2','Bearing A / inner half','shaft_cam_a_inner'),
          ('C1','Bearing A / outer half','shaft_cam_a_outer'),('N1','Lower OOBB nut carrier','shaft_mount_lower'),
          ('R1','Lower support / 6704','hardware_6704_base'),('E1','Lower end journal','shaft_end_lower')])]
    label(48,33,'MECHANICAL REFERENCE     /     SIMPLE DOUBLE BEARING     /     V2',24,True,muted)
    label(45,84,'Exploded gearbox and part names',65,True)
    label(49,178,'Either end accepts the same four-hole drive attachment. Use the callout or the native body name when specifying a change.',31)
    d.line((48,245,2940,245),fill='#9bacad',width=2)
    label(48,277,'Complete assembly',36,True)
    render([n for n in bodies if n not in ('connected_contact_ring','output_lower_row_plate','output_circle_plate')],295,842,500,930)
    label(48,1375,'Loose ring sleeves fitted',26,True)
    label(48,1416,'Hardware shown in grey.',24,color=muted)
    for j,(title,rows) in enumerate(names):
        left=581+j*785
        d.line((left-19,277,left-19,1464),fill='#d3d9d6',width=2)
        label(left,277,title,36,True)
        ys=np.linspace(420,1355,len(rows))
        d.line((left+109,365,left+109,1405),fill='#d4deda',width=2)
        for (ref,title,name),y in zip(rows,ys):
            y=int(y)
            render([name],left+109,y,202,76 if len(rows)>8 else 125)
            label(left+230,y-28,ref,25,True,'#37636c')
            label(left+298,y-29,title,29,True)
            label(left+298,y+12,name,23,color=muted)
    d.rectangle((0,1498,2990,2050),fill='#eff3f1')
    label(48,1526,'Sleeves and fasteners',39,True)
    label(520,1538,'Quantities are for one gearbox. The connected ring replaces all loose outer sleeves.',27,color=muted)
    length=int(values['join_length']); tie=int(values['shaft_tie_length'])
    items=[
     ('F1',f'Outer contact sleeve × {r}','printed_contact_sleeve', 'One on each ring screw.'),
     ('F2',f'Inner drive sleeve × {g}','printed_drive_sleeve','One on each fixed guide screw.'),
     ('F3','Connected contact ring × 1','connected_contact_ring','Optional substitute for F1.'),
     ('F4','M3 socket-cap screws','hardware_ring_cap_heads+hardware_ring_M3_shanks',f'{r} × {length} mm ring; {g} × 35 mm guide.'),
     ('F5',f'M3 hex nut × {r+g+6+16}','hardware_M3_ring_nuts',f'{r} ring, {g} guide, 6 disc, 16 mount.'),
     ('F6','M3 × 6 countersunk screw × 6','hardware_disc_a_M3x6_1','Three per cycloid clamshell.'),
     ('F7',f'M3 × {tie} shaft tie × 2','hardware_shaft_M3x35_lower','One screw enters from each end.'),
     ('F8','M3 shaft nuts × 10','hardware_shaft_tie_nut_lower','2 opposed ties; 8 drive mounts.') ]
    for i,(ref,title,name,note) in enumerate(items):
        x=48+(i%4)*739;y=1665+(i//4)*185
        render(name.split('+'),x+72,y+35,130,110)
        label(x+155,y-20,ref,24,True,'#37636c')
        label(x+155,y+15,title,28,True)
        label(x+155,y+58,note,24,color=muted)
    image.save(part/'exploded_labeled.png',optimize=True)

def draw_carrier_faces(part):
    """Show the two real split-face sections in the same assembled XY orientation."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    from shapely.geometry import Polygon as Outline

    fig,axes=plt.subplots(1,2,figsize=(11.2,6.2),facecolor='#fffefa')
    for ax,name,title,note in zip(axes,('carrier_top','carrier_top_cap'),
        ('Carrier core','Carrier cap'),('Eight hex pockets open onto the flat split.','The 6704 seats in the circular recess.')):
        mesh=trimesh.load_mesh(part/'native_parts'/(name+'.stl'))
        loops=mesh.section(plane_normal=[0,0,1],plane_origin=[0,0,(json.loads((part/'native_export_verification.json').read_text())['parameters']['carrier_cap_height'] if name.endswith('_cap') else mesh.bounds[1,2])-.1]).discrete
        for q in sorted((Outline(q[:,:2]) for q in loops),key=lambda q:-q.area):
            xy=np.array(q.exterior.coords)
            if name.endswith('_cap'):xy[:,1]*=-1
            radius=np.linalg.norm(q.centroid.coords[0])
            fill=('#e3e9e4' if q.area>1300 else '#fffefa' if radius<1 else
                  '#aed8df' if radius>18 else '#ffde9c')
            ax.add_patch(Polygon(xy,facecolor=fill,edgecolor='#294654',lw=1.2))
        ax.set(xlim=(-28,28),ylim=(-28,28),aspect='equal')
        ax.axis('off');ax.set_title(title,fontsize=18,color='#233e49')
        ax.text(.5,-.025,note,transform=ax.transAxes,ha='center',fontsize=11)
    fig.subplots_adjust(top=.78,bottom=.16,wspace=.1)
    fig.text(.5,.91,'Eight-mount inner carrier',ha='center',fontsize=26,weight='bold',color='#233e49')
    fig.text(.5,.84,'Top carrier at the mating plane, aligned in assembled coordinates',ha='center',fontsize=12)
    fig.text(.5,.055,'Amber: OOBB M3 mounts     •     Blue: six M3 × 35 guide screws     •     Cross-sections from the exported parts',ha='center',fontsize=11)
    for ext in ('svg','png'):
        fig.savefig(part/('carrier_split_faces.'+ext),dpi=170,facecolor=fig.get_facecolor())
    plt.close(fig)


def draw_output_plates(part,v):
    """Color each bore in the actual print sections, keeping both plates to scale."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Patch
    from gearbox_native.double_bearing_housing import FOOT
    from gearbox_native.verify_double_bearing_housing import section

    colors={'plate':'#d9e6e2','M6':'#ce9453','M3':'#447f91','Lobe screw':'#706d95'}
    choices=[('output_cap_plate','Square OOBB plate'),(FOOT,'Lower-row plate')]
    if (part/'native_parts/output_circle_plate.stl').exists():choices.append(('output_circle_plate','Circular OOBB plate'))
    fig,axes=plt.subplots(1,len(choices),figsize=(5*len(choices),6.1),facecolor='#fffefa')
    for ax,(name,title) in zip(axes,choices):
        mesh=trimesh.load_mesh(part/'native_parts'/(name+'.stl'))
        outline,*holes=section(mesh,.25)
        ax.add_patch(Polygon(list(outline.exterior.coords),facecolor=colors['plate'],edgecolor='#314d52',lw=1.2))
        for hole in holes:
            r=np.linalg.norm(hole.centroid.coords[0])
            kind=('Lobe screw' if abs(r-v['pitch'])<.04 else 'M6' if hole.area>20 else 'M3')
            fill='#fffefa' if r<.1 else colors[kind]
            ax.add_patch(Polygon(list(hole.exterior.coords),facecolor=fill,edgecolor='#314d52',lw=.6))
        edge=max(v['housing_plate_half'],v.get('circle_plate_radius',0))
        ax.set(xlim=(-edge-5,edge+5),ylim=(-edge-20,edge+5),aspect='equal')
        ax.set_title(title,color='#25434c',fontsize=15);ax.axis('off')
    fig.suptitle('Outer housing plates',fontsize=23,fontweight='bold',color='#25434c')
    keys=('M6','M3','Lobe screw')
    fig.legend([Patch(color=colors[k]) for k in keys],['M6 mounting hole','M3 mounting hole','M3 lobe screw'],loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,.04))
    fig.subplots_adjust(top=.86,bottom=.15,wspace=.06)
    fig.text(.02,.015,'AI-generated CAD section drawing. Errors possible.',fontsize=8,color='#59615f')
    fig.savefig(part/'output_plate_options.png',dpi=160,facecolor=fig.get_facecolor());plt.close(fig)
