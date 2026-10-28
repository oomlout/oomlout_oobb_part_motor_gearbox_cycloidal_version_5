"""Dimensioned axial section from the verified native animation assets."""
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
from shapely.geometry import Polygon,Point
import trimesh
from gearbox_native.project import active_part, VERSION
from gearbox_native.presentation import pose

def main():
    part=active_part()
    job=json.loads((part/'solidcraft_renders/true/with_hardware/render_job.json').read_text())
    c=job['config'];assert c['base_grub']
    fig,ax=plt.subplots(figsize=(13,7),facecolor='#edf0f2')
    ax.set_facecolor('#edf0f2')
    colors={'motor_mount':'#aac3d0','pin_front':'#aac3d0','output_casing':'#dd9674','output_casing_lower':'#dd9674','output_casing_upper':'#e4a788',
            'rotor_a':'#b9bf83','rotor_b':'#c2acd2',
            'eccentric_hub_lower':'#d7b563','eccentric_hub_upper':'#d7b563'}
    selected=job['pieces']+[i for i in job['hardware'] if i['name'].startswith(('post_screw_','post_nut_')) or i['name'] in
        ('motor','output_bearing_0','output_bearing_1','shaft_bearing',
         'eccentric_bearing_0','eccentric_bearing_1','shaft_grub','shaft_grub_nut','hub_bolt','hub_nut')]
    for item in selected:
        assets=[dict(stl=item['stl'],sha256=item['stl_sha256'])] if 'stl' in item else item['assets']
        position,angles=pose(item,c)
        matrix=trimesh.transformations.euler_matrix(*angles);matrix[:3,3]=position
        for asset in assets:
            path=Path(asset['stl']);assert hashlib.sha256(path.read_bytes()).hexdigest()==asset['sha256']
            mesh=trimesh.load_mesh(path,process=True);mesh.apply_transform(matrix)
            cut=mesh.section(plane_origin=[0,0,0],plane_normal=[0,1,0])
            if cut is None:continue
            polygons=[Polygon(points[:,[0,2]]) for points in cut.discrete]
            polygons=[p for p in polygons if p.is_valid and p.area>1e-8]
            for polygon in sorted(polygons,key=lambda p:-p.area):
                depth=sum(other.contains(Point(polygon.exterior.coords[0])) for other in polygons if other is not polygon)
                ax.add_patch(Patch(list(polygon.exterior.coords),
                    facecolor='#edf0f2' if depth%2 else colors.get(item['name'],'#8999a4'),
                    edgecolor='#384954',linewidth=.65))
    def dimension(x,lo,hi,label):
        ax.annotate('',xy=(x,lo),xytext=(x,hi),arrowprops=dict(arrowstyle='<->',color='#31434d'))
        ax.text(x-1,(lo+hi)/2,label,rotation=90,ha='right',va='center',fontsize=10,color='#213640')
    side=14 if c.get('split_output_casing') else 0
    dimension(-39-side,c['casing_bottom_z'],c['housing_depth'],f"{c['housing_depth']-c['casing_bottom_z']:g} mm casing")
    dimension(-47-side,0,c['overall_height'],f"{c['overall_height']:g} mm overall above motor")
    for label,xy,target in (
        (f"{c['bearing_shaft']} shaft bearing nested inside upper 6810",(8,c['shaft_bearing_z'][1]),(48,37)),
        (f"Upper 6810 · {c['output_bearing']['depth']:g} mm",(29,c['output_bearing_z'][1]),(48,29)),
        (f"Upper cycloid · {c['rotor_thickness']:g} mm",(28,c['rotor_b_z']+c['rotor_thickness']/2),(48,22)),
        (f"{c['disc_gap']:g} mm gap / opposed eccentric discs",(14,c['rotor_b_z']-c['disc_gap']/2),(48,17)),
        (f"Lower cycloid · {c['rotor_thickness']:g} mm",(28,c['rotor_a_z']+c['rotor_thickness']/2),(48,12)),
        (f"Rear 6810 · {c['output_bearing']['depth']:g} mm",(29,c['output_bearing_z'][0]),(48,6)),
        ('Grub tightened before fitting motor plate',(8,c['coupling_grub_z']),(48,-1)),
    ):
        ax.annotate(label,xy=xy,xytext=(target[0]+side,target[1]),fontsize=9,color='#213640',
                    arrowprops=dict(arrowstyle='-',color='#627783',connectionstyle='angle3'),va='center')
    ax.axhline(0,color='#627783',linewidth=.6,linestyle='--',xmin=.04,xmax=.58)
    ax.set_aspect('equal');ax.set_xlim(-51-side,112+side);ax.set_ylim(-5,42);ax.axis('off')
    fig.suptitle(VERSION.replace('version_', 'V')+' / COMPRESSED BEARING STACK',x=.06,ha='left',fontsize=19,fontweight='bold',color='#213640')
    ideal=2*c['output_bearing']['depth']+2*c['rotor_thickness']+c['disc_gap']
    fig.text(.06,.88,f"Two 6810s + two cycloids + gap = {ideal:g} mm; casing including shoulders and clearances = {c['housing_depth']-c['casing_bottom_z']:g} mm.",fontsize=11,color='#526973')
    fig.text(.06,.11,f"Casing top: {c['housing_depth']:g} mm above motor. Central hub top: {c['overall_height']:g} mm. Motor shaft remains {c['motor_shaft_length']:g} mm long.\n"+
             ('Print casing halves split-face down; 3 mm tabs sit flat on the bed. Section uses verified meshes; threads omitted.' if c.get('split_output_casing') else
              'Use slicer supports beneath the shortened internal casing transition. Section uses verified meshes; threads omitted.'),
             fontsize=10,color='#526973')
    for ext in ('png','svg'):fig.savefig(part/('axial_stack_section.'+ext),dpi=170,facecolor=fig.get_facecolor())
    plt.close(fig)
    print(part/'axial_stack_section.png')

if __name__=='__main__':main()
