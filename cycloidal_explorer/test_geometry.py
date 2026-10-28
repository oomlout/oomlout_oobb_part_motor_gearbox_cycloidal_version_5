"""Independent comparisons with native formula, polygon topology and contact motion."""
import json,math,sys,subprocess
from pathlib import Path
from shapely.geometry import Polygon,Point
from shapely.affinity import translate,rotate
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from gearbox_native.cycloid_equation import CycloidEquation
from gearbox_native.lobe import profile_points

subprocess.run(['node','export_data.js'],cwd=ROOT,check=True)
data=json.loads((ROOT/'qa/examples.json').read_text())
for item in data['examples']:
    m=item['model'];p=m['p'];points=m['points'];n=m['n']
    native=CycloidEquation(n,p['radius'],p['eccentricity'],p['roller'],p['clearance'])
    assert abs(native.minimum_convex_radius()-m['rho'])<1e-10
    expected=profile_points(n-1,p['radius'],p['eccentricity'],p['roller'],p['clearance'],samples_per_lobe=24)
    assert len(points)==len(expected)
    for i in range(0,len(points),17):
        assert math.dist(expected[i],points[i])<1e-10
    poly=Polygon(points)
    assert poly.is_valid and poly.area>0
    for key,radius in [('guides',m['guideHole']),('posts',m['postHole'])]:
        for xy in m[key]:
            assert poly.contains(Point(xy))
            assert poly.boundary.distance(Point(xy))-radius>=2-.005
    minimum=math.inf
    for side in (0,1):
        base=rotate(poly,-side*180/(n-1),origin=(0,0))
        for angle in range(0,360*n,37):
            phase=math.radians(angle+side*180)
            moved=translate(base,p['eccentricity']*math.cos(phase),p['eccentricity']*math.sin(phase))
            for i in range(n):
                a=math.tau*i/n+math.radians(angle/n)
                centre=Point(p['radius']*math.cos(a),p['radius']*math.sin(a))
                minimum=min(minimum,moved.distance(centre)-p['roller'])
    assert p['clearance']-.005<minimum<p['clearance']+.005,minimum
    print(f'{item["name"]}: native equation match; valid polygon; hole webs; opposed-disc motion clearance {minimum:.6f} mm')
old=data['rejected']
assert not old['profileValid'] and not old['valid']
assert abs(old['rho']-2.6316239485)<1e-9
baseline=data['examples'][0]['model']
assert baseline['p']['radius']==31.15
assert abs(2*baseline['casingRadius']-72.3)<1e-10
assert abs(2*baseline['guideHole']-6.2)<1e-10
assert abs(2*baseline['postHole']-8.5)<1e-10
print('Baseline dimensions and historical undercut regression pass.')
