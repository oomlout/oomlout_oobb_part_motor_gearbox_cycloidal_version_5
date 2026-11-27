"""Draw a section from accepted native/nominal meshes at the grub screw axis."""
import json
import hashlib
import math
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
    part=active_part();folder=part/'solidcraft_renders/true/with_hardware'
    job=json.loads((folder/'render_job.json').read_text());c=job['config']
    assert c['direct_drive']
    fig,ax=plt.subplots(figsize=(10,8),facecolor='#edf0f2')
    ax.set_facecolor('#edf0f2')
    selected=[next(p for p in job['pieces'] if p['name']=='eccentric_hub_lower')]
    selected.extend(p for p in job['hardware'] if p['name'] in ('motor','shaft_grub_nut','shaft_grub'))
    colors={'eccentric_hub_lower':'#ca9d42','motor':'#8796a1','shaft_grub_nut':'#a9b5bd','shaft_grub':'#5c707e'}
    for item in selected:
        assets=[dict(stl=item['stl'],sha256=item['stl_sha256'])] if 'stl' in item else item['assets']
        position,angles=pose(item,c)
        transform=trimesh.transformations.euler_matrix(*angles);transform[:3,3]=position
        for asset in assets:
            path=asset['stl']
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==asset['sha256'],'Regenerate the current animation before this section'
            mesh=trimesh.load_mesh(path,process=True);mesh.apply_transform(transform)
            section=mesh.section(plane_origin=[0,0,c['coupling_grub_z']],plane_normal=[0,0,1])
            if section is None:continue
            contours=[Polygon(points[:,:2]) for points in section.discrete]
            contours=[p for p in contours if p.is_valid and p.area>1e-8]
            for polygon in sorted(contours,key=lambda p:-p.area):
                depth=sum(other.contains(Point(polygon.exterior.coords[0])) for other in contours if other is not polygon)
                ax.add_patch(Patch(list(polygon.exterior.coords),facecolor='#edf0f2' if depth%2 else colors[item['name']],
                                  edgecolor='#31434d',linewidth=1.2))
    angle=math.radians(c['direct_grub_angle'])
    def polar(r):return (r*math.cos(angle),r*math.sin(angle))
    for label,xy,xytext in (
        ('5 mm motor shaft',(0,0),(-17,11)),
        ('Captured M3 nut\nloads from underneath',
         ((c['direct_grub_nut_radius']+1.25)*math.cos(angle)-2.3*math.sin(angle),
          (c['direct_grub_nut_radius']+1.25)*math.sin(angle)+2.3*math.cos(angle)),(11,12)),
        (f"M3 × {c['direct_grub_length']:g} grub screw",polar(c['direct_grub_outer_radius']-1),(12,-10)),
        ('Printed eccentric hub',(-7,-5),(-19,-12)),
    ):
        ax.annotate(label,xy=xy,xytext=xytext,fontsize=11,color='#213640',
                    arrowprops=dict(arrowstyle='-',color='#526973',connectionstyle='angle3'),
                    bbox=dict(boxstyle='round,pad=.4',fc='#edf0f2',ec='none'))
    ax.set_aspect('equal');ax.set_xlim(-21,25);ax.set_ylim(-16,17);ax.axis('off')
    fig.suptitle('DIRECT SHAFT CONNECTION / '+VERSION.replace('version_', 'V'),x=.08,ha='left',fontsize=18,fontweight='bold',color='#213640')
    fig.text(.08,.91,f"Grub axis {c['coupling_grub_z']:g} mm above motor · {c['overall_height']:g} mm overall height",fontsize=11,color='#526973')
    access='motor plate' if c.get('base_grub') else 'rear 6810'
    fig.text(.08,.07,f'Tighten before fitting the {access}. The metal nut supplies the thread.\n'
             'Section uses native hub geometry and nominal hardware; screw threads are omitted.',fontsize=10,color='#526973')
    for ext in ('png','svg'):fig.savefig(part/('direct_grub_section.'+ext),dpi=180,facecolor=fig.get_facecolor())
    plt.close(fig)
    print(part/'direct_grub_section.png')


if __name__=='__main__':main()
