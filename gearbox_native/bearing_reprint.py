"""Upgrade beds and an orientation gauge made from the exported guide pattern."""
import math
from pathlib import Path
import numpy as np
import trimesh
from gearbox_native.guide_assembly_fit import track_wires
from gearbox_native.verification import read_step

def guide_gauge(folder,parts,v):
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeCone
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.StlAPI import StlAPI_Writer
    from gearbox_native.exact_geometry import _move,_boolean
    from gearbox_native.verify_v8_hardware import cylinder
    from matplotlib import pyplot as plt
    from matplotlib.patches import Circle
    faces=track_wires(read_step(parts/'rotor_a.step'),v['guide_track'])
    tracks=sorted([(math.atan2(xy[1],xy[0])%math.tau,r,xy) for r,xy in faces
                   if abs(r-v['guide_track'])<.001],key=lambda q:q[0])
    assert len(tracks)==6
    lead=v['guide_entry'];radius=v['guide_pitch']+v['guide_track']+lead+2
    gap_index=max(range(6),key=lambda i:(tracks[(i+1)%6][0]-tracks[i][0])%math.tau)
    a=tracks[gap_index][0];b=tracks[(gap_index+1)%6][0]
    mark=a+((b-a)%math.tau)/2
    depth=1.6
    tools=[cylinder(v['shaft_journal']+.1,depth+1,[0,0,-.5]),
           cylinder(1.3,depth+1,[radius*math.cos(mark),radius*math.sin(mark),-.5])]
    for _,r,(x,y) in tracks:
        tools.append(cylinder(r,depth+1,[x,y,-.5]))
        tools.append(_move(BRepPrimAPI_MakeCone(r+lead+.01,r-.02,lead+.03).Shape(),'translate',[x,y,-.01]))
    stock=_boolean('cut',cylinder(radius,depth,[0,0,0]),tools)
    BRepMesh_IncrementalMesh(stock,.012,False,.12,True).Perform()
    target=folder/'six_sleeve_gauge.stl'
    writer=StlAPI_Writer();writer.ASCIIMode=False;assert writer.Write(stock,str(target))
    m=trimesh.load_mesh(target);assert m.is_volume and len(m.split())==1 and abs(m.extents[2]-depth)<.001

    fig,axs=plt.subplots(1,2,figsize=(11,6),facecolor='#fffdf7')
    fig.subplots_adjust(left=.05,right=.95,top=.76,bottom=.19,wspace=.22)
    fig.suptitle('Fitting the cycloid over the six guide sleeves',weight='bold',fontsize=22,y=.96)
    fig.text(.5,.865,'View from the upper carrier end. The shaft is shown with the lower eccentric pointing right.',ha='center',fontsize=11)
    for ax in axs:
        ax.set(aspect='equal',xlim=(-30,30),ylim=(-30,30));ax.axis('off')
    ax,other=axs
    ax.set_title('Matched V2 disc and carrier',weight='bold')
    ax.add_patch(Circle((0,0),26.25,fill=False,ec='#a9b7b6'))
    e=v['eccentricity']
    ax.add_patch(Circle((e,0),10,fill=False,ec='#536779',lw=1.7))
    ax.plot(0,0,'+',color='black');ax.plot(e,0,'+',color='#bc6538')
    for _,r,(x,y) in tracks:
        ax.add_patch(Circle((x+e,y),r,fc='#fff2cf',ec='#a07930',lw=1.5))
        ax.add_patch(Circle((x,y),v['contact_radius'],fc='#5d96a2',ec='#285865'))
    def annotate_chord(axes,p1,p2):
        axes.plot(*np.stack([p1,p2]).T,color='#233e49',lw=1)
        mid=(p1+p2)/2
        axes.text(*mid,f'{np.linalg.norm(p1-p2):.1f}',ha='center',va='center',size=10,bbox=dict(fc='#fffdf7',ec='none',pad=.5))
    pts=[q[2] for q in tracks]
    for i in (0,1):annotate_chord(ax,pts[i],pts[i+1])
    clamp=math.radians(v['clamp_phase'])
    screw=np.array([e+v['clamp_pitch']*math.cos(clamp),v['clamp_pitch']*math.sin(clamp)])
    ax.plot(*screw,marker='D',ms=5,color='#9a4963')
    ax.text(0,-29,'Diamond = disc clamp screw in the wide gap.',ha='center',fontsize=10)
    other.set_title('Identify the generation on your bench',weight='bold')
    for j,(_,r,(x,y)) in enumerate(tracks):
        pre=math.radians(15+60*j)
        prior=np.array([20*math.cos(pre),20*math.sin(pre)])
        other.add_patch(Circle(prior,1.85,fill=False,ec='#b15943',lw=1.7,ls='--'))
        other.plot(x,y,'+',color='#285865',mew=2,ms=11)
    other.text(0,-29,'Dashed = earlier 60° pattern. Cross = eight-nut V2.',ha='center',fontsize=10)
    fig.text(.5,.115,'Point the clamp screw between two widely spaced tracks toward the same wide gap on both discs.',ha='center',fontsize=11)
    fig.text(.5,.06,'Install the disc over one exposed C journal, with the opposite C half removed. Its shoulder is larger than the bearing bore.',ha='center',fontsize=10)
    for ext in ('png','svg'):fig.savefig(folder/('guide_installation.'+ext),dpi=160)
    plt.close(fig)

def write_upgrade(part,v):
    folder=part/'bearing_reprint';folder.mkdir(exist_ok=True)
    native=part/'native_parts';guide_gauge(folder,native,v)
    draw_retention(part,v)
    bed=folder/'drive_and_carriers';bed.mkdir(exist_ok=True)
    positions={'rotor_a':(40,40),'rotor_a_cap':(119,40),'rotor_b':(40,119),'rotor_b_cap':(119,119),
               'carrier_bottom':(189,28),'carrier_bottom_cap':(189,84),
               'carrier_top':(189,140),'carrier_top_cap':(189,196),
               'shaft_end_lower':(22,186),'shaft_end_upper':(53,186),
               'shaft_mount_lower':(84,186),'shaft_mount_upper':(115,186)}
    pieces=[]
    for name,xy in positions.items():
        m=trimesh.load_mesh(native/(name+'.stl'));m.apply_translation([*xy,0])
        assert all(any(m.bounds[0,k]>other.bounds[1,k]+1 or other.bounds[0,k]>m.bounds[1,k]+1 for k in (0,1)) for other in pieces)
        pieces.append(m)
    combined=trimesh.util.concatenate(pieces);combined.export(bed/'3dpr.stl')
    assert min(combined.bounds[0,:2])>=0 and max(combined.bounds[1,:2])<=240
    assert all(m.is_volume and abs(m.bounds[0,2])<.01 for m in pieces) and len(combined.split())==12
    # From the previous V2, the nut-side rotor halves and four C halves can be reused.
    flat_kit=folder/'flat_carrier_update'
    flat_kit.mkdir(exist_ok=True)
    changed=[m for n,m in zip(positions,pieces) if n not in ('rotor_a_cap','rotor_b_cap')]
    changed_path=flat_kit/'3dpr.stl'
    trimesh.util.concatenate(changed).export(changed_path)
    shells=trimesh.load_mesh(changed_path).split(only_watertight=False)
    assert len(shells)==10 and all(m.is_volume and abs(m.bounds[0,2])<.01 for m in shells)
    (folder/'README.md').write_text("""# Fitting the V2 bearings and guide sleeves

Upgrading from the previous V2 with the stepped 6810 carrier joint? Print the [ten changed pieces](flat_carrier_update/3dpr.stl). Reuse the rotor nut halves, all four C halves, guide sleeves, casing and hardware.

Print the [1.6 mm fit gauge](six_sleeve_gauge.stl) first. Try it on the six sleeves of one open carrier, then over the exposed Ø19.90 mm eccentric journal with the other C half removed. The gauge has a Ø20.10 mm pilot and the working holes and entry tapers of Disc A. Its edge notch marks the midpoint of a wide pair. The [orientation drawing](guide_installation.png) shows the default pattern viewed from the upper end.

Follow the [layered assembly sequence](../ASSEMBLY.md). Start socket-cap end down with the screws standing upward. Install the small E journal and large 6810 inner carrier in the same starting layer, then both bearings. Lower the subsequent layers over the screws, install B before A, and reverse the temporary shaft screw at the end.

On the eight-nut V2 carrier, adjacent sleeve centres repeat 24.1, 17.8, 17.8 mm. Earlier regular carriers have six 20.0 mm centre distances. Measure corresponding edges of equal sleeves to identify the pattern. Both discs must match the carrier and point their indexed clamp screw toward the same wide gap.

The [bearing cross-section](bearing_retention.png) shows the lower end. The carrier cap runs through the full 6810 bore and meets the core at a flat split. Seat E from outside through the centred 6704. N closes the opposite side of its inner race.

Print the [four outer housing parts](../outer_housing_reprint/3dpr.stl) and [twelve internal parts](drive_and_carriers/3dpr.stl), one plate each. For the lower-row mounting option, substitute the [flat lower-row flange](../native_parts/output_lower_row_plate.stl) for a square flange. Reuse the four C halves, the Ø7 × 16 mm sleeves, the bearings and fasteners. For the flat 6810 split and flush rotor screws, use the matching four carrier pieces, two E end journals, two N nut carriers and both screw-side rotor halves. The earlier nut-side rotor halves can be reused. The twelve-piece bed includes both nut-side halves for a complete set.

The default has Ø10.30 mm working tracks and Ø11.50 mm entry mouths. The 0.60 mm lead-in on each end leaves 5.80 mm of straight track across the assembled disc. Each sleeve sits 0.45 mm into a carrier register at either end. The two seats preserve the 16 mm sleeve length.
""",encoding='utf8')
def draw_retention(part,v):
    """Radial cut through the lower production meshes. Upper end is its mirror."""
    from matplotlib import pyplot as plt
    from matplotlib.patches import Rectangle,PathPatch,Patch
    from matplotlib.path import Path as DrawingPath
    from shapely.geometry import Polygon,GeometryCollection,box
    from shapely.geometry.polygon import orient
    import trimesh
    from gearbox_native.stacked_disc_shaft import stations
    entries=[
        ('output_nut_cylinder',False,-v['housing_lip_depth'],'#538aaa','Outside cylinder'),
        ('output_nut_plate',True,v['middle_start'],'#9bc4d1','Flat OOBB plate'),
        ('carrier_bottom_cap',False,-v['carrier_extension'],'#66ab91','Carrier cap'),
        ('carrier_bottom',True,v['middle_start']+v['guide_socket_depth'],'#c6dfad','Carrier core'),
        ('shaft_end_lower',False,v['shaft_face_z'],'#de9f66','E end journal'),
        ('shaft_mount_lower',True,stations(v)['shaft_mount_lower'],'#e6c89f','N nut carrier')]
    fig,ax=plt.subplots(figsize=(12,5.6),facecolor='#fffdf7')
    fig.subplots_adjust(left=.08,right=.98,bottom=.24,top=.83)
    for name,flip,z,color,_ in entries:
        mesh=trimesh.load_mesh(part/'native_parts'/(name+'.stl'))
        # E and N's 45-degree assembled clocking is material at this section.
        if flip:mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0]))
        if name.startswith('shaft_'):
            angle=-45 if flip else 45
            mesh.apply_transform(trimesh.transformations.rotation_matrix(math.radians(angle),[0,0,1]))
        mesh.apply_translation([0,0,z])
        section=mesh.section(plane_normal=[0,1,0],plane_origin=[0,.015,0])
        solid=GeometryCollection()
        for loop in section.discrete:solid=solid.symmetric_difference(Polygon(loop[:,[0,2]]).buffer(0))
        solid=solid.intersection(box(0,-4,36,10))
        for island in getattr(solid,'geoms',[solid]):
            island=orient(island,sign=1)
            paths=[DrawingPath(np.asarray(r.coords)) for r in [island.exterior,*island.interiors]]
            ax.add_patch(PathPatch(DrawingPath.make_compound_path(*paths),facecolor=color,edgecolor='#334651',lw=.7))
    for caption,ri,ro,base,width in [('6704',10,13.5,v['race_end_gap'],4),('6810',25,32.5,v['main_outer_face'],7)]:
        ax.add_patch(Rectangle((ri,base),ro-ri,width,facecolor='#eeeae3',edgecolor='#596773',hatch='///',lw=.8))
        ax.text((ri+ro)/2,base+width/2,caption,ha='center',va='center',fontsize=10,weight='bold',
                bbox=dict(facecolor='#fffdf7',alpha=.9,edgecolor='none',pad=1))
    ax.set(xlim=(0,36),ylim=(-3.6,10),aspect='equal',xlabel='Radius from shaft centre (mm)',ylabel='Height (mm)')
    ax.set_title('Lower bearing seats in assembly',loc='left',fontsize=20,weight='bold')
    ax.legend(handles=[Patch(fc=c,label=l) for _,_,_,c,l in entries],loc='upper center',bbox_to_anchor=(.5,-.21),ncol=3,frameon=False)
    for ext in ('png','svg'):fig.savefig(part/'bearing_reprint'/('bearing_retention.'+ext),dpi=170)
    plt.close(fig)
