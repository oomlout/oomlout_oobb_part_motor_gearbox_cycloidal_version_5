"""Plain technical sheets composed from production CAD renders."""
import json
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parents[1]
RAW = P / 'raw'
OUT = P / 'images'
INK = '#222625'
GREY = '#59615F'
TEAL = '#006D70'
WARM = '#FAF8F2'
NOTICE = 'AI-generated CAD illustration. Errors possible.'


def font(size, bold=False):
    return ImageFont.truetype(str(Path('C:/Windows/Fonts') / ('segoeuib.ttf' if bold else 'segoeui.ttf')), size)


def text(d, xy, value, size=28, bold=False, fill=INK):
    d.text(xy, value, font=font(size, bold), fill=fill, anchor='lt')


def wrap(d, xy, value, width, size=27, fill=GREY):
    x, y = xy
    line = ''
    for word in value.split():
        trial = (line + ' ' + word).strip()
        if d.textlength(trial, font=font(size)) > width and line:
            text(d, (x,y), line, size, fill=fill)
            y += size * 1.4
            line = word
        else:
            line = trial
    text(d, (x,y), line, size, fill=fill)
    return y + size * 1.4


def sheet(title, size=(1600,1360), subtitle=None):
    im = Image.new('RGB', size, 'white')
    d = ImageDraw.Draw(im)
    text(d, (48,32), title, 46, True)
    if subtitle:
        wrap(d, (50,99), subtitle, size[0]-100, 26)
    text(d, (48,size[1]-45), NOTICE, 22, fill=GREY)
    return im, d


def paste(page, key, box):
    raw = Image.open(RAW / (key+'.png')).convert('RGBA')
    x,y,w,h = box
    scale = min(w/raw.width,h/raw.height)
    raw = raw.resize((round(raw.width*scale),round(raw.height*scale)),Image.Resampling.LANCZOS)
    left,top = round(x+(w-raw.width)/2),round(y+(h-raw.height)/2)
    background = Image.new('RGB', (w,h), WARM)
    page.paste(background,(x,y))
    page.paste(raw, (left,top), raw)
    return lambda point: (left+point[0]*scale,top+point[1]*scale)


def leader(d, point, target, title, caption=None):
    x,y = target
    d.line([point,(x-16,point[1]),(x-8,y+10)],fill=TEAL,width=2)
    px,py=point
    d.ellipse((px-4,py-4,px+4,py+4),fill=TEAL)
    text(d,(x,y),title,26,True,TEAL)
    if caption:
        text(d,(x,y+35),caption,22,fill=GREY)


def palette(d,y):
    x=50
    for color,label in [('#00B1B7','Housing, discs, N'),('#121212','Carriers, C cams'),('#FEC601','Sleeves, E journals'),('#A1ABAF','Metal hardware')]:
        d.ellipse((x,y+5,x+18,y+23),fill=color)
        text(d,(x+29,y),label,23,fill=GREY)
        x += int(d.textlength(label,font=font(23)))+75


def publish(data):
    anchors=json.loads((RAW/'anchors.json').read_text())
    im,d=sheet('19:1 cycloidal gearbox',subtitle='Drive E. Fix the teal outer ring. Take the reduced-speed output from the black middle ring.')
    project=paste(im,'in_use',(45,160,1510,1080))
    # Leaders indicate the actual interfaces without inventing a drive or mounting hardware.
    leader(d,project(anchors['in_use']['shaft_end_upper']),(1110,210),'Input: E journal')
    leader(d,project(anchors['in_use']['carrier_top_cap']),(1110,290),'Output: black middle ring')
    leader(d,project(anchors['in_use']['output_cap_plate']),(1110,1020),'Fix the teal outer ring')
    text(d,(50,1250),'Operating arrangement; external motor, frame and load omitted.',25,fill=GREY)
    im.save(OUT/'in-use.png')
    for key,name,title,caption in [('printed','printed-assembly.png','Assembled printed parts','46 printed pieces. Purchased bearings, nuts and screws hidden.'),
                                   ('rounded','rounded.png','Lower-row mounting option','Replace both square plates with the lower-row flange; keep the same bearing interface.')]:
        im,d=sheet(title,subtitle=caption)
        paste(im,key,(45,160,1510,1080))
        palette(d,1250)
        im.save(OUT/name)

    im,d=sheet('Exploded gearbox groups',(2560,1780),
               'All groups share one axis in the finished gearbox. Read each column from bottom to top.')
    panels=[('housing','Fixed outer ring',[
        ('hardware_ring_cap_heads','20 ring screws','H3 / M3 x 30 socket cap'),
        ('output_cap_cylinder','Starting cylinder','P04 / 8.5 mm deep'),
        ('hardware_6810_top','2 casing bearings','H1 / 6810'),
        ('output_cap_plate','2 OOBB plates','P01 + P02 / 104 mm square'),
        ('printed_contact_sleeve','20 outer sleeves','P21 / diameter 7 x 16 mm'),
        ('output_nut_cylinder','Finishing cylinder','P03 / outer nut recesses')]),
        ('core','Output carrier and discs',[
        ('hardware_drive_caps','6 guide screws','H4 / M3 x 35 socket cap'),
        ('carrier_top_cap','Carrier caps and cores','P05-P08 / 16 captive nuts'),
        ('hardware_6704_top','4 shaft/disc bearings','H2 / 6704'),
        ('rotor_b','Disc B clamshell','P11 + P12 / heads toward top in native view'),
        ('printed_drive_sleeve','6 inner guides','P22 / diameter 7 x 16 mm'),
        ('rotor_a','Disc A clamshell','P09 + P10 / heads toward bottom'),
        ('carrier_bottom','Finishing carrier','8 captive M3 mounting nuts'),
        ('hardware_drive_nuts','6 guide nuts','H6 / recessed in carrier cap')]),
        ('shaft','Eight-piece input shaft',[
        ('hardware_shaft_M3x35_upper','2 opposed shaft ties','H4 / M3 x 35 socket cap'),
        ('shaft_end_upper','E: starting journal','P14 / yellow'),
        ('shaft_mount_upper','N: starting carrier','P16 / 4 attachment nuts'),
        ('shaft_cam_b_outer','B: two C cam halves','P19 + P20 / black'),
        ('shaft_cam_a_outer','A: two C cam halves','P17 + P18 / offset opposite B'),
        ('shaft_mount_lower','N: finishing carrier','P15 / 4 attachment nuts'),
        ('shaft_end_lower','E: finishing journal','P13 / 6.50 mm centre passage'),
        ('hardware_shaft_M3x35_lower','Opposite tie direction','One screw head at each end')])]
    for i,(key,title,callouts) in enumerate(panels):
        x=35+i*840
        text(d,(x+10,180),title,38,True)
        transform=paste(im,key,(x,250,540,1340))
        entries=sorted([(transform(anchors[key][n]),a,b) for n,a,b in callouts],key=lambda e:e[0][1])
        ys=[]
        for point,_,_ in entries:
            ys.append(max(point[1],ys[-1]+110 if ys else 290))
        for j in reversed(range(len(ys))):
            ys[j]=min(ys[j],ys[j+1]-110 if j+1<len(ys) else 1580)
        for (point,a,b),y in zip(entries,ys):
            # Compact labels avoid crossing into the next group.
            px,py=point;tx=x+515
            d.line([(px,py),(tx-26,py),(tx-12,y+9)],fill=TEAL,width=2)
            text(d,(tx,y),a,24,True)
            wrap(d,(tx,y+34),b,285,21)
    palette(d,1655)
    im.save(OUT/'exploded.png')

    for index,step in enumerate(data['readme']['assembly_steps'],1):
        im,d=sheet(f"{index}. {step['title']}")
        key=step['key']
        if key=='layer_start':
            paste(im,key,(430,135,1120,900))
            paste(im,'layer_start_face',(45,450,380,323))
            text(d,(60,795),'Starting E: underside',25,True)
            wrap(d,(60,840),'Round socket stays. Hex pocket holds the temporary head.',335,24)
        else:
            transform=paste(im,key,(60,130,1480,935))
            if key=='bench':
                leader(d,transform(anchors[key]['hardware_6704_disc_b']),
                       (1180,545),'H2: 6704 bearing')
            if key=='layer_reverse':
                leader(d,transform(anchors[key]['hardware_shaft_M3x35_lower']),
                       (1120,230),'2. Refit from above')
                leader(d,transform(anchors[key]['temporary_shaft_tie']),
                       (1120,900),'1. Withdraw below')
                text(d,(65,1015),'Same screw shown in two positions',24,True,TEAL)
        end=wrap(d,(50,1095),step['body'],1500,26)
        assert end<1300, ('Step caption overflow',index,end)
        im.save(OUT/step['image'])

    im,d=sheet('Load the carrier nuts before closing',subtitle='Starting carrier shown. Eight M3 mounting nuts sit in its flat split face.')
    paste(im,'nut_split',(60,145,1480,970))
    wrap(d,(50,1150),'Keep the pockets accessible until all eight nuts are seated. The finishing carrier uses the same arrangement, with its pockets facing upward during the build.',1500,29)
    im.save(OUT/'carrier-nuts.png')
    section(data)
    # Compatibility overview: readable close-ups remain available as individual steps.
    overview=Image.new('RGB',(1920,math.ceil(len(data['readme']['assembly_steps'])/3)*544),'white')
    for i,step in enumerate(data['readme']['assembly_steps']):
        thumb=Image.open(OUT/step['image']).resize((640,544),Image.Resampling.LANCZOS)
        overview.paste(thumb,((i%3)*640,(i//3)*544))
    overview.save(OUT/'assembly-overview.png')


def section(data):
    """Section the actual carrier and embedded nut meshes at a mounting-hole axis."""
    import numpy as np
    import trimesh
    models=np.load(RAW/'studio.npz')
    im,d=sheet('Carrier mounting nut section',(1600,1000),
               'Section through the production mesh at y = 7.5 mm. Mounting axis x = 15 mm.')
    # Native top carrier closes between z=24.55 and z=37; section shows x,z.
    x0,z0=8,23
    scale=45
    def xy(x,z):return (200+(x-x0)*scale,820-(z-z0)*scale)
    colors={'carrier_top':TEAL,'carrier_top_cap':'#222625'}
    names=['carrier_top','carrier_top_cap']
    for n in models.files:
        if n.endswith('_v') and n.startswith('hardware_carrier_top_mount_nut'):
            points=models[n]
            if abs(points[:,0].mean()-15)<1 and abs(points[:,1].mean()-7.5)<1:
                names.append(n[:-2])
    assert len(names)==3, 'Identify one actual nut at the section axis'
    paths=[]
    for n in names:
        mesh=trimesh.Trimesh(models[n+'_v'],models[n+'_f'],process=False)
        cut=mesh.section(plane_origin=[15,7.5,0],plane_normal=[0,1,0])
        assert cut is not None,n
        for loop in cut.discrete:
            # Keep the local nut area; off-page line segments are excluded.
            for a,b in zip(loop[:-1],loop[1:]):
                if 8<=a[0]<=22 and 8<=b[0]<=22 and 23<=a[2]<=38 and 23<=b[2]<=38:
                    d.line([xy(a[0],a[2]),xy(b[0],b[2])],fill=colors.get(n,'#8D6919'),width=4)
                    paths.append([n,a.tolist(),b.tolist()])
    assert paths
    d.line([xy(15,23),xy(15,38)],fill='#9AB2B0',width=2)
    text(d,(920,300),'Carrier cap',33,True)
    text(d,(920,365),'M3 nut at split',33,True,fill='#8D6919')
    text(d,(920,430),'Carrier core',33,True,fill=TEAL)
    wrap(d,(920,530),'Nominal nut: 5.5 mm across flats, 2.4 mm thick. Load it before fitting the cap.',575,28)
    wrap(d,(50,870),'Section drawing from the registered production meshes; no hidden hardware is implied by the exterior view.',1500,27)
    im.save(OUT/'carrier-section.png')
    im.crop((240,135,840,835)).save(RAW/'carrier-section-geometry.png')
    (P/'qa/section-paths.json').write_text(json.dumps(paths),encoding='utf8')
