"""Rebuild the vector A4 example book from the exact browser geometry output."""
import json, math
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit

ROOT=Path(__file__).resolve().parent
DATA=json.loads((ROOT/'qa/examples.json').read_text())
OUT=ROOT/'dist/cycloidal-examples.pdf'
INK='#183d3b'; MUTED='#697571'; TEAL='#197f76'; PAPER='#f5f3ed'; LINE='#d7ddd5'
W,H=210*mm,297*mm
c=canvas.Canvas(str(OUT),pagesize=(W,H),pageCompression=1)
c.setTitle('Cycloidal V5 - geometry example book')
c.setAuthor('OOBB / Cycloidal geometry explorer')

def text(x,y,s,size=10,color=INK,bold=False):
    c.setFillColor(HexColor(color));c.setFont('Helvetica-Bold' if bold else 'Helvetica',size)
    c.drawString(x*mm,y*mm,s)

def para(x,y,s,width=180,size=9,color=MUTED,leading=4.5):
    for line in simpleSplit(s,'Helvetica',size,width*mm):
        text(x,y,line,size,color);y-=leading
    return y

def line(x1,y1,x2,y2,color=LINE,width=.5):
    c.setStrokeColor(HexColor(color));c.setLineWidth(width);c.line(x1*mm,y1*mm,x2*mm,y2*mm)

def base(page,label):
    c.setFillColor(HexColor(PAPER));c.rect(0,0,W,H,fill=1,stroke=0)
    text(15,282,'OOBB / MECHANISM STUDIES',10,INK,True)
    text(150,282,'V05  /  GEOMETRY LAB',8,MUTED)
    line(15,276,195,276)
    line(15,17,195,17)
    text(15,11,'Cycloidal V5  |  26 October 2026  |  Dimensions in mm',7,MUTED)
    text(160,11,f'{label}  /  {page:02d}',7,MUTED)

def circle(x,y,r,fill=None,stroke=INK,width=.5):
    c.setLineWidth(width);c.setStrokeColor(HexColor(stroke))
    if fill:c.setFillColor(HexColor(fill))
    c.circle(x*mm,y*mm,r*mm,fill=int(bool(fill)),stroke=1)

def dim(x1,x2,y,label):
    line(x1,y,x2,y,MUTED,.4);line(x1,y-1.2,x1,y+1.2,MUTED,.4);line(x2,y-1.2,x2,y+1.2,MUTED,.4)
    c.setFont('Helvetica',7);c.setFillColor(HexColor(MUTED));c.drawCentredString((x1+x2)/2*mm,(y+2)*mm,label)

def shape(points,cx,cy,fill,stroke=TEAL):
    path=c.beginPath()
    for i,(x,y) in enumerate(points):
        (path.moveTo if i==0 else path.lineTo)((cx+x)*mm,(cy+y)*mm)
    path.close();c.setStrokeColor(HexColor(stroke));c.setFillColor(HexColor(fill));c.setLineWidth(.65);c.drawPath(path,fill=1,stroke=1)

def diagram(m,cx=56,cy=196,bx=151):
    p=m['p'];r=m['casingRadius'];e=p['eccentricity']
    circle(cx,cy,r,'#ece6d8','#9b8a6c');circle(cx,cy,m['boreRadius'],PAPER,'#9b8a6c')
    c.setDash(2,2);circle(cx,cy,p['radius'],None,'#aeb5a7',.35);c.setDash()
    for i in range(m['n']):
        a=2*math.pi*i/m['n'];circle(cx+p['radius']*math.cos(a),cy+p['radius']*math.sin(a),p['roller'],'#d7ad6e','#8b7047',.4)
    shape(m['points'],cx+e,cy,'#c4ddd1' if m['profileValid'] else '#f3ccc0',TEAL if m['profileValid'] else '#b64a2d')
    for positions,key in [(m['guides'],'guideHole'),(m['posts'],'postHole')]:
        for x,y in positions:circle(cx+e+x,cy+y,m[key],PAPER,TEAL,.4)
    circle(cx+e,cy,11.6,PAPER,TEAL,.4);circle(cx+e,cy,11.5,'#dee5e6','#789097',.35);circle(cx+e,cy,8.5,PAPER,'#789097',.35)
    for x,y in m['guides']:circle(cx+x,cy+y,1.5,'#345852','#345852',.3)
    for x,y in m['posts']:circle(cx+x,cy+y,2.7,'#869d91','#526e62',.35);circle(cx+x,cy+y,1.5,PAPER,'#526e62',.3)
    line(cx-4,cy,cx+4,cy,MUTED,.3);line(cx,cy-4,cx,cy+4,MUTED,.3);line(cx,cy,cx+e,cy,'#dc6947',1.3)
    circle(bx,cy,32.5,'#dee5e6','#789097');circle(bx,cy,30.2,None,'#9dafb4',.3);circle(bx,cy,27.3,None,'#9dafb4',.3);circle(bx,cy,25,PAPER,'#789097')
    text(bx-9,cy+2,'6810',16,INK,True);text(bx-17,cy-4,'50 x 65 x 7 mm',9,MUTED)
    dim(cx-r,cx+r,cy+r+5,f'Casing diameter {2*r:.2f}')
    dim(bx-32.5,bx+32.5,cy+r+5,'Outside diameter 65.00')
    dim(bx-25,bx+25,cy-38,'Bore diameter 50.00')
    text(cx-r,cy-r-8,f'Pitch diameter {2*p["radius"]:.2f}  |  {m["lobes"]} disc lobes',8,MUTED)

def table(rows,y):
    for label,value in rows:
        line(15,y-2,195,y-2)
        text(15,y+1,label,9,MUTED)
        c.setFont('Helvetica-Bold',9);c.setFillColor(HexColor(INK));c.drawRightString(195*mm,(y+1)*mm,value)
        y-=7
    return y

for i,item in enumerate(DATA['examples'],1):
    m=item['model'];p=m['p'];base(i,'DESIGN STUDY')
    text(15,262,f'{p["ratio"]}:1 / {item["name"]}',24,INK,True)
    para(15,251,item['note'],size=9)
    diagram(m)
    rows=[
        ('Ring contacts / disc lobes / output direction',f'{m["n"]} / {m["lobes"]} / same as input'),
        ('Pitch radius / contact radius / eccentricity',f'{p["radius"]:.2f} / {p["roller"]:.2f} / {p["eccentricity"]:.2f}'),
        ('Radial profile clearance / casing wall',f'{p["clearance"]:.2f} / {p["wall"]:.2f}'),
        ('Disc root / tip diameter',f'{2*m["rootRadius"]:.2f} / {2*m["tipRadius"]:.2f}'),
        ('Disc swept envelope / casing diameter',f'{2*m["sweptRadius"]:.2f} / {2*m["casingRadius"]:.2f}'),
        ('Guide holes (6) / guide pitch circle',f'{2*m["guideHole"]:.2f} / 34.80'),
        ('Standoff holes (3) / standoff pitch circle',f'{2*m["postHole"]:.2f} / 37.10'),
        ('Disc thickness / gap / bearing-disc stack only',f'{p["thickness"]:.2f} / {p["gap"]:.2f} / {m["bearingStack"]:.2f}'),
        ('Minimum convex radius / offset used',f'{m["rho"]:.3f} / {p["roller"]+p["clearance"]:.3f}'),
    ]
    table(rows,140)
    text(15,69,'8/8 screening checks pass',10,TEAL,True)
    para(15,63,'The explorer checks radial envelopes, undercut, contact attachment, orbit-hole webs, casing-lip passage and eccentric-bearing retention. Explorations are not full CAD-validated assemblies.',size=8.5,leading=4)
    if i==1:
        para(15,49,'Current V5 reference: 32 mm overall height above the motor face; casing depth 26.6 mm; mounting plate 74 mm across. These heights are not extrapolated to changed designs.',size=8.5,leading=4)
    else:
        para(15,49,'Retains the fixed V5 radial interfaces and 6810 end bearings. Recalculate the axial stack and run the native CAD, assembly and motion checks before making parts.',size=8.5,leading=4)
    line(15,29,65,29,INK,1);line(15,27.5,15,30.5,INK,.6);line(65,27.5,65,30.5,INK,.6)
    text(74,28,'50 mm check bar. Diagrams 1:1 on A4 at 100% / Actual size.',8,MUTED)
    c.showPage()

base(5,'PROJECT LESSONS')
text(15,261,'Why the old pitch failed',25,INK,True)
para(15,250,'The project regression captures an important failure: increasing the contact radius without increasing the pitch radius creates an undercut profile.',size=10,leading=5)
old=DATA['rejected'];now=DATA['examples'][0]['model']
table([('Same inputs in both studies','20 contacts / e 1.40 / r 3.00 / clearance 0.20'),
       ('Old pitch radius / current pitch radius','30.15 / 31.15'),
       ('Old minimum convex radius',f'{old["rho"]:.6f}'),
       ('Required inward offset','3.200000'),
       ('Old undercut margin',f'{old["rho"]-3.2:.6f} - rejected'),
       ('Current minimum convex radius',f'{now["rho"]:.6f}'),
       ('Current undercut margin',f'{now["rho"]-3.2:.6f} - passes')],226)
y=165
for title,body in [
 ('01 / The ratio belongs to the output member', 'The V5 discs are prevented from spinning by fixed guides. They orbit on opposed eccentrics while the casing rotates in the input direction. N contacts and N-1 disc lobes give N:1 casing reduction. A fixed-ring, rotating-disc arrangement has a different ratio and direction.'),
 ('02 / Contact radius is not rotor radius', 'The adjustable lobe radius is the radius of each circular contact in the casing. Current contacts are solid printed features. A future M3 axle needs a 6 mm outside-diameter roller or sleeve to reproduce a 3 mm contact radius.'),
 ('03 / Bearings occupy a different axial region', '6810 means 50 mm bore, 65 mm outside diameter, 7 mm width. Two end bearings capture the casing. The disc plane lies between them. Guide holes are 3 + 2e + 0.40 mm; standoff holes are 5.4 + 2e + 0.30 mm. More eccentricity takes material out of both webs.'),
 ('04 / Geometry is the first gate', 'A passing radial study does not establish load capacity, backlash, wear or print fit. The current underside needs slicer supports. Test the shared fit coupons and smooth guide surfaces, and run the full native CAD and motion validation for any changed design.')]:
    text(15,y,title,11,INK,True);y=para(15,y-6,body,size=9,leading=4.5)-8
text(15,48,'Source trace',10,INK,True)
para(15,42,'Repository: README.md; working_oomp_populate.py; gearbox_native/cycloid_equation.py, captured.py, simple.py and interfaces.py; tests/test_native_three_mm_lobes.py. All four examples use the same geometry calculation as the HTML explorer.',size=8,leading=3.6)
text(15,25,'Bearing reference: NSK 6810 product dimensions (50 x 65 x 7 mm).',8,TEAL)
c.linkURL('https://www.nsk.com/engineering/products/bearings/ball-bearings/deep-groove-ball-bearings/single-row-deep-groove-ball-bearings/6810-apn.html',(15*mm,23*mm,180*mm,29*mm),relative=0)
c.save()
print(OUT)
