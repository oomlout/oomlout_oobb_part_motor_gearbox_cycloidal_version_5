"""Shaft sheet from the exported production meshes; bearings and fasteners at nominal size."""
import math
import numpy as np
import trimesh
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
from gearbox_native.stacked_disc_shaft import LAYERS, stations

def draw(part,v):
    from matplotlib import rc_context
    with rc_context({'font.family':'DejaVu Sans','svg.fonttype':'none'}):
        fig=plt.figure(figsize=(13.2,8),facecolor='#fffdf8')
        grid=fig.add_gridspec(2,3,left=.06,right=.95,bottom=.10,top=.83,hspace=.45,height_ratios=[1,.96])
        kinds={'E':('End journal',2,'#9ac7dc'),'N':('Mount nut carrier',2,'#ebc88a'),'C':('Eccentric half',4,'#9dc9ab')}
        fig.text(.06,.94,'Eight discs, three shaft parts',fontsize=26,weight='bold',color='#223b42')
        fig.text(.06,.895,'Simple double bearing V2   /   Production mesh sections   /   Dimensions in mm',fontsize=12)
        front=fig.add_subplot(grid[1,:])
        # Same section plane as the mesh cut; the two central bearings are offset in X.
        for z,x in [(v['race_end_gap'],0),(v['disc_a_z']+v['disc_lip'],v['eccentricity']),
                    (v['disc_b_z']+v['disc_lip'],-v['eccentricity']),
                    (v['stack_height']-v['race_end_gap']-v['shaft_race_width'],0)]:
            ri=(10**2-(x-.005)**2)**.5;ro=((v['shaft_race_od']/2)**2-(x-.005)**2)**.5
            for y in (ri,-ro):
                front.add_patch(Rectangle((z,y),v['shaft_race_width'],ro-ri,
                                 fc='#e8ebeb',ec='#758890',lw=.7,hatch='////',zorder=0))
        for i,(name,k,flip,reverse,station,level) in enumerate(LAYERS):
            mesh=trimesh.load_mesh(part/'native_parts'/(name+'.stl'))
            label,qty,col=kinds[k]
            if i in (0,1,2):
                ax=fig.add_subplot(grid[0,i])
                z=mesh.bounds[1,2]-.02
                for origin,style in ([(.02,'-'),(z,':')] if k=='E' else [(z,'-'),(.02,':')]):
                    path=mesh.section(plane_origin=[0,0,origin],plane_normal=[0,0,1])
                    for curve in path.discrete:ax.plot(curve[:,0],curve[:,1],style,lw=1.45,color='#21495a')
                for t in (-7.5,0,7.5):
                    ax.axvline(t,c='#aaa89c',lw=.55,zorder=-1);ax.axhline(t,c='#aaa89c',lw=.55,zorder=-1)
                ax.set(aspect='equal',xlim=(-13,13),ylim=(-13,13));ax.axis('off')
                ax.set_title(f'{k}   {label}  × {qty}',color='#223b42',weight='bold')
                ax.text(.5,-.08,['Head and nut on opposite diagonals','Four M3 pockets at radius 7.5','Ø19.90 journal, offset from the ties'][i],transform=ax.transAxes,ha='center',fontsize=10)
            def turn(angle,axis):mesh.apply_transform(trimesh.transformations.rotation_matrix(math.radians(angle),axis))
            if flip:turn(180,[1,0,0]);turn(-90,[0,0,1])
            turn(225 if reverse else 45,[0,0,1])
            z=stations(v)[name];mesh.apply_translation([0,0,z])
            path=mesh.section(plane_normal=[1,0,0],plane_origin=[.005,0,0])
            for curve in path.discrete:
                front.fill(curve[:,2],curve[:,1],color=col,ec='#25434c',lw=.7)
            front.text(mesh.bounds[:,2].mean(),14.0,k,ha='center',weight='bold',fontsize=11)
        h=v['stack_height'];p=v['shaft_tie_pitch'];face=v['shaft_face_z']
        for bottom in (True,False):
            s=face+v['shaft_head_depth'] if bottom else h-face-v['shaft_head_depth'];y=-p if bottom else p
            front.add_patch(Rectangle((s if bottom else s-v['shaft_tie_length'],y-1.5),v['shaft_tie_length'],3,color='#596f78'))
            front.add_patch(Rectangle((s-3 if bottom else s,y-2.75),3,5.5,color='#596f78'))
            nut= h-face-v['shaft_nut_depth'] if bottom else face+v['shaft_nut_depth']-2.5
            front.add_patch(Rectangle((nut,y-2.75),2.5,5.5,ec='#35444d',fc='none',lw=1.3))
        front.set(aspect='equal',xlim=(face-1,h-face+1),ylim=(-14.0,15.4))
        front.axis('off')
        front.text(-.34,.56,'Axial cut through both ties\n\nGrey: M3 × 35 screws\nOutline: M3 nuts\nHatching: 6704 bearings',transform=front.transAxes,ha='right',va='center',fontsize=12)
        front.text(1.04,.50,'Centre stays open: Ø6.50\nBoth end faces accept the same mount.\nTurn the second cam pair 180°.',transform=front.transAxes,va='center',fontsize=11)
        fig.text(.06,.075,'Face views: solid = mounting or journal face; dotted = opposite face. Grid spacing 7.5 mm. Mount holes Ø3.60; tie holes Ø3.40 on radius 6.52.',fontsize=10)
        fig.text(.06,.04,'Print broad face down. Load the four mount nuts before closing each E/N pair. The narrowest end-journal web is 0.27 mm at the default dimensions.',fontsize=10)
        for ext in ('svg','png'):fig.savefig(part/('shaft_reference.'+ext),dpi=155)
        import shutil
        shutil.copyfile(part/'shaft_reference.png',part/'shaft_stackup.png')
        plt.close(fig)
