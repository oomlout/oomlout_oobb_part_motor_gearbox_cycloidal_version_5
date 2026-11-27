"""Publish the 40 mm NEMA17 guide from actual CAD stage renders and fit proofs."""
from pathlib import Path
import csv,hashlib,json,re,shutil,sys
from xml.sax.saxutils import escape
from PIL import Image,ImageDraw,ImageFont
from gearbox_native.nema17_depth40_guide import ROOT,PART,BUILD,OUT,STEPS
sys.path.insert(0,str(ROOT/'presentation/scripts/lib'))
from manual_layout import Manual

HARDWARE=[
 ('6810 bearing',2,'50 bore x 65 OD x 7 mm; outer casing supports'),
 ('6704 bearing',4,'20 bore x 27 OD x 4 mm; two centred, two eccentric'),
 ('M3 x 30 socket cap',20,'Outer ring contacts'),
 ('M3 x 35 socket cap',5,'Three short guides + two opposed shaft ties'),
 ('M3 x 40 socket cap',3,'Late-installed guides into motor adapter'),
 ('M3 x 6 countersunk',6,'Three per cycloid clamshell'),
 ('M3 x 14 socket cap',4,'Coupler; use one 0.5 mm washer per screw'),
 ('M3 washer',4,'6 mm OD, 0.5 mm thick; coupler'),
 ('M3 x 8 socket cap',4,'NEMA17 motor to adapter'),
 ('M3 x 16 socket cap',3,'Motor tube to adapter'),
 ('M3 x 25 countersunk',6,'Four front-cover screws + two plate braces'),
 ('M3 x 16 countersunk',3,'Rear cover to tube'),
 ('M3 x 10 countersunk',12,'Six at each end of the three teal joiners'),
 ('M3 hex nut',109,'Full fitted inventory; breakdown on next page'),
 ('M6 hex nut',34,'15 front-cover + 19 rear-cover mounting pockets'),
 ('NEMA17 motor',1,'40 mm body; 5 mm shaft, 24 mm projection; 31 mm mounting square'),
 ('5 mm flange coupler',1,'22 mm flange OD; 16 mm screw PCD; 12 mm tall'),
 ('Coupler supplied grub screws',2,'Use the screws and matching key supplied with your coupler; omitted from CAD'),
]
NUTS=[('Outer contact ring',20,'Before completing core'),('Six guide screws',6,'Three early; three side-loaded before the long screws'),
 ('Cycloid clamshells',6,'Three in each disc before closing'),('Opposed shaft ties',2,'One late, when reversing the temporary tie'),
 ('Inner 6810 carrier mounts',16,'Eight per carrier, before closing each split'),('6704 N nut carriers',8,'Four per end; motor-side four used by coupler'),
 ('Motor tube joins',3,'Before fastening tube to adapter'),('Rear-cover joins',3,'In tube before rear cover'),
 ('Three teal joiners',12,'Four per joiner before installation'),('Two extra plate braces',2,'At brace installation'),
 ('Front/rear OOBB mounts',31,'16 front + 15 rear before closing covers')]
PRINTED=[
 ('Circular output plates',2,'output_circle_plate; output_circle_rear_plate'),
 ('6810 bearing cylinders',2,'output_cap_cylinder; output_nut_cylinder'),
 ('6810 inner carrier halves',4,'carrier_top; carrier_top_cap; carrier_bottom; carrier_bottom_cap'),
 ('Centred shaft ends E',2,'shaft_end_upper; shaft_end_lower (modified for coupler)'),
 ('Centred shaft nut carriers N',2,'shaft_mount_upper; shaft_mount_lower (modified for coupler)'),
 ('Eccentric cam halves',4,'shaft_cam_a_inner/outer; shaft_cam_b_inner/outer'),
 ('Cycloid halves',4,'rotor_a; rotor_a_cap; rotor_b; rotor_b_cap'),
 ('Outer contact sleeves',20,'printed_contact_sleeve; OD 7 x 16 mm'),
 ('Inner guide sleeves',6,'printed_drive_sleeve; OD 7 x 16 mm'),
 ('Motor adapter and tube',2,'motor_inner_adapter; motor_cage'),
 ('Fixed front cover pieces',3,'front_cover_spacer; front_cover_nuts; front_cover_face'),
 ('Fixed rear cover pieces',2,'rear_cover_nuts; rear_cover_face'),
 ('Identical teal joiners',3,'rear_output_joiner_1/2/3; common alias rear_output_joiner'),
 ('Rear output ring',1,'rear_output_extension; alias rear_output_ring'),
 ('Extra plate braces',2,'rear_output_spacer_1/2; OD 7 x 16 mm'),
]
AI='AI-generated images and instructions. Errors possible.'
PREP='Use the current 40 mm-depth conversion print plus the unchanged base gearbox parts. The conversion print contains 18 extra or replacement pieces, not a complete second gearbox. The illustrated circular-plate assembly contains 59 printed pieces with loose outer contacts. A connected outer ring replaces twenty loose contacts; do not install both.'
ORIENT='Front means the fixed black cover opposite the motor. Rear means the motor end. Build the core front-face down on an open support: native top/upper parts go in first and native bottom/lower parts go in last. Turn the assembly as needed after closing the core. In the illustrations, incoming layers are separated to show their order; those display gaps are not assembly dimensions.'
TOOLS='Use a 2.5 mm hex key for M3 socket caps, a straight 2 mm hex key for countersunk screws, the coupler\'s matching grub key, tweezers for nuts, and an open support that leaves at least 50 mm access beneath the front face. Check actual screw heads against your tools. Clean print bridges and test-fit each bearing and nut before stacking.'

def raw(key):return BUILD/(key+'.png')
def font(size,bold=False):return ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf',size)
def png(key,title,subtitle=''):
    im=Image.open(raw(key)).convert('RGBA');paper=Image.new('RGBA',im.size,'#faf8f2');paper.alpha_composite(im)
    out=Image.new('RGB',(im.width,im.height+150),'white');out.paste(paper.convert('RGB'),(0,105));d=ImageDraw.Draw(out)
    d.text((38,18),title,font=font(32,True),fill='#222625')
    if subtitle:d.text((38,64),subtitle,font=font(21),fill='#59615f')
    d.text((38,out.height-35),'AI-generated CAD illustration. Errors possible.',font=font(20),fill='#59615f')
    out.save(OUT/'images'/(key+'.png'))
    thumb=out.copy();thumb.thumbnail((480,480));thumb.save(OUT/'images'/(key+'-thumb.png'))
    return out

def catalogues():
    import yaml
    refs=[]
    for name,qty,spec in HARDWARE:
        match=re.match(r'M3 x (\d+) (socket cap|countersunk)$',name)
        url='';alpha='';status='Dimension specified by current native design; no exact catalogue record linked.'
        if match:
            length,kind=match.groups();head='socket_cap' if kind=='socket cap' else 'countersunk'
            ident=f'hardware_screw_{head}_hex_head_black_m3_diameter_{length}_mm_length'
            path=Path('C:/gh/oomp_hardware_screw_version_5/parts')/ident/'working.yaml'
            if path.exists():
                item=yaml.safe_load(path.read_text(encoding='utf8'));alpha=item.get('md5_6_alpha','');url=f'https://github.com/oomlout/oomp_hardware_screw_version_5/tree/main/parts/{ident}'
                status='Identity checked against local OOMP catalogue: '+str(path)
        refs.append(dict(item=name,quantity=qty,specification=spec,oomp_code=alpha,url=url,verification=status))
    base=json.loads((ROOT/'presentation/project.json').read_text())
    for target in refs:
        for item in base['hardware']:
            if (target['item'].startswith('6810') and '6810' in item['name']) or (target['item'].startswith('6704') and '6704' in item['name']) or (target['item']=='M3 hex nut' and 'M3' in item['name'] and 'nut' in item['name'].lower()):
                target.update(oomp_code=item['md5_6_alpha'],url=item['url'],verification='Existing verified base-project catalogue reference')
    return refs

def labeled_overview():
    image=Image.open(raw('overview')).convert('RGBA');paper=Image.new('RGBA',image.size,'#faf8f2');paper.alpha_composite(image)
    d=ImageDraw.Draw(paper);a=json.loads((BUILD/'anchors.json').read_text())['overview']
    labels=[('Fixed front cover','front_cover_face',70,100),('Gearbox core','circular_top',70,300),
      ('5 mm coupler','hardware_flange_coupler_5mm',70,460),('Motor + adapter','motor_inner_adapter',70,650),
      ('Fixed motor tube','motor_cage',70,880),('Fixed rear cover','rear_cover_face',70,1170),
      ('3 identical\nrotating joiners','rear_output_joiner_1',1350,620),('Separate rear ring\nRotating output','rear_output_extension',1320,1190)]
    for label,n,x,y in labels:
        p=a[n];end=(x+360 if x<500 else x-15,y+16)
        d.line((p[0],p[1],*end),fill='#006d70',width=3);d.ellipse((p[0]-5,p[1]-5,p[0]+5,p[1]+5),fill='#006d70')
        d.text((x,y),label,fill='#222625',font=font(28,True))
    d.text((38,image.height-35),'AI-generated CAD illustration. Errors possible.',fill='#59615f',font=font(20))
    paper.convert('RGB').save(OUT/'images/overview_labeled.png')

def md(refs,proof):
    lines=['# NEMA17 gearbox assembly - 40 mm motor body','',AI,'',
      '[Printable illustrated PDF](assembly-guide.pdf) | [Hardware CSV](hardware.csv) | [Printed inventory CSV](printed-parts.csv)','',
      '![Finished gearbox](images/finished.png)','',PREP,'',
      '**Configuration:** 20:1 rotating outer casing; 40 mm motor; 1.5 mm eccentricity; 7 mm split discs; 16 mm sleeves; two 6810 and four 6704 bearings. Both black covers remain fixed.','',
      '## Before you start','',ORIENT,'',TOOLS,'',
      'Keep screws loose until each layer is seated, then snug them evenly. If turning gets tight, loosen the last fasteners and reseat the layer. Do not use a screw to pull an unseated bearing into place.','',
      '![Named assembly overview](images/overview_labeled.png)','',
      '## Printed inventory','',
      'Use [nema3dpr.scad](../nema3dpr.scad) for the conversion-only kit and the base gearbox prints for reused parts. Current individual files are in [native_parts](../native_parts/). Use the conversion versions of `carrier_top_cap`, `shaft_end_lower`, `shaft_mount_lower` and both circular output plates. The coupler aliases duplicate E/N: do not print them twice.','',
      '| Part group | Qty | Native names / size |','|---|---:|---|']
    lines += [f'| {n} | {q} | {s} |' for n,q,s in PRINTED]
    lines += ['', '## Hardware','', 'Quantities include all captive mounting nuts. External frame/load fasteners are excluded. Optional unused mounting pockets may be left empty; leave every assembly nut in place.','', '| Item | Qty | Purpose / specification |','|---|---:|---|']
    for r in refs:
        name=f"[{r['item']}]({r['url']})" if r['url'] else r['item']
        lines.append(f"| {name} | {r['quantity']} | {r['specification']} |")
    lines += ['','Socket-cap length is measured under the head; countersunk length includes the head. Do not substitute longer screws at the coupler without checking shaft clearance. M3 x 14 is the model requirement; an exact OOMP catalogue entry was not found.','',
      '### Where the 109 M3 nuts go','', '| Location | Qty | Load them when |','|---|---:|---|']
    lines += [f'| {n} | {q} | {s} |' for n,q,s in NUTS]
    lines += ['','## Full assembly sequence','']
    for i,(key,title,body,access) in enumerate(STEPS,1):
        lines += [f'### {i:02d}. {title}','',body,'',f'**Access check:** {access}','',f'[![Stage {i}: {title}](images/{key}-thumb.png)](images/{key}.png)','']
    lines += ['## Access details','',
      '![Two starting ties](images/starting_ties.png)','',
      'One standing shaft screw begins in a hex nut pocket only as a temporary assembly aid. At stage 12 remove it, load the nut, and reinsert that same screw from the opposite end. Do this before the coupler covers the end.','',
      '![Coupler access](images/grub_access.png)','',
      'Align the two coupler grubs one at a time with the adapter windows by rotating the input. The bench-built tube remains below the windows. Tighten both before fitting covers and the surrounding teal joiners.','',
      '## Verification and limits','',
      'Illustrations use the current native STEP/STL geometry. The CAD checks cover the full core insertion sequence, the preassembled motor/tube approach, side-loading the three late guide nuts, and straight 2 mm-diameter grub-tool paths. Existing current-source checks cover cover insertion, joiner nuts, screw seats and the rotating output sweep. See [verification.json](verification.json).','',
      'These are geometric checks, not a physical assembly or load test. Cable connectors, print tolerances and the exact purchased coupler still need checking on the bench. Recheck after changing native parameters; this guide is for the recorded 40 mm configuration.','',
      f"Native source SHA256: `{proof['source_sha256']}`.",'']
    (OUT/'README.md').write_text('\n'.join(lines),encoding='utf8')

def pdf(refs,proof):
    m=Manual(OUT/'assembly-guide.pdf','NEMA17 cycloidal gearbox - 40 mm motor assembly')
    m.page('NEMA17 gearbox assembly','40 mm motor body | Simple double-bearing V2 adaptation | 20:1 rotating outer casing')
    m.image(raw('finished'),42,115,540,425)
    m.paragraph(612,135,'<b>Both black covers stay fixed.</b><br/>The teal casing, three joiners and rear ring turn together.',235,14)
    m.paragraph(612,255,'Two 6810 bearings<br/>Four 6704 bearings<br/>1.5 mm eccentricity<br/>7 mm split cycloids<br/>16 mm sleeves<br/>5 mm motor shaft',235,12)
    m.paragraph(42,553,PREP,816,11)
    m.finish()
    m.page('Names and assembly groups','Exploded spacing is illustrative. Parts retain their native CAD geometry.')
    m.image(OUT/'images/overview_labeled.png',42,108,816,505);m.finish()
    m.page('Orientation, tools and access')
    y=m.paragraph(42,113,ORIENT,816,12)
    y=m.paragraph(42,y+25,TOOLS,816,12)
    y=m.paragraph(42,y+25,'<b>Access order:</b> capture nuts before closing split parts; reverse the temporary shaft tie before the coupler; tighten motor and tube fasteners on the bench; load the three adapter guide nuts before their long screws; tighten both grubs before covers and teal joiners.',816,12)
    m.image(raw('starting_ties'),42,350,320,250)
    m.paragraph(395,393,'<b>Two ties stand upward at first.</b><br/><br/>One is deliberately temporary, sitting in a hex pocket. At stage 12, withdraw it, insert its nut and reverse the screw. The finished pair points in opposite directions.',420,12)
    m.finish()
    m.page('Printed parts','59 pieces for this circular-plate build. The conversion-only print contains 18 of these.')
    for i,(name,q,spec) in enumerate(PRINTED):
        col=i//8;row=i%8;x=42+col*418;y=120+row*59
        m.text(x,y,f'{name}  x{q}',11,True)
        m.paragraph(x,y+19,escape(spec),393,9.5)
    m.finish()
    for page,items in enumerate((refs[:10],refs[10:]),1):
        m.page(f'Hardware {page}/2','Complete inventory, including optional captive mounting nuts. External attachment screws excluded.')
        for i,r in enumerate(items):
            y=118+i*44;m.text(42,y,r['item'],11,True);m.text(303,y,r['quantity'],11,True)
            m.paragraph(352,y,escape(r['specification']),505,10.5)
            if r['url']:
                m.canvas.linkURL(r['url'],(42,m.height-y-15,290,m.height-y+2),relative=0)
        if page==2:
            m.paragraph(42,500,'M3 x 14 is the CAD requirement; no exact OOMP catalogue record was found. Each uses a 0.5 mm washer. Socket-cap length excludes the head; countersunk length includes it. Do not substitute longer coupler screws without checking clearance.',816,11)
        m.finish()
    m.page('Captive nuts: load before closing','109 M3 nuts and 34 M6 nuts with every mounting pocket populated.')
    for i,(name,q,when) in enumerate(NUTS):
        y=118+i*36;m.text(42,y,name,11,True);m.text(292,y,q,11,True);m.paragraph(340,y,escape(when),515,10.5)
    m.paragraph(42,546,'M6: 15 in the front cover and 19 in the rear cover. Unused external mounting pockets may remain empty. Keep all joining, shaft, guide and coupler nuts. The four front-cover screws use four of the carrier nuts; they are not another four loose nuts.',816,11)
    m.finish()
    for i,(key,title,body,access) in enumerate(STEPS,1):
        m.page(f'{i:02d}. {title}','Incoming layers are separated in the illustration; seat them fully in the finished assembly.')
        m.image(raw(key),32,120,540,450)
        y=m.paragraph(598,125,escape(body),260,12)
        y=m.paragraph(598,y+28,'<b>Access check</b><br/>'+escape(access),260,11)
        assert y<610,(key,y)
        if key in ('discs','inner_start','inner_finish','caps','coupler','front_cover','rear_cover','joiner_nuts'):
            m.text(42,600,'Match the native part names in the printed inventory and Markdown guide.',10,color='#59615F')
        m.finish()
    m.page('Coupler access and first run')
    m.image(raw('grub_access'),42,120,510,390)
    m.paragraph(585,120,'Rotate the input to bring each supplied grub screw to an adapter window. The tube is already fitted below these openings. Tighten both grubs before adding the covers and rotating joiners.',270,12)
    m.paragraph(585,285,'Turn the input by hand first. If a layer binds, back off the last fasteners and reseat it. Check the cable is clear through a full output turn. Then run slowly with no load using the motor\'s appropriate driver settings.',270,12)
    m.paragraph(42,540,'Frame mounts attach to the fixed black parts. Loads attach to the rotating teal parts. Keep external mounting screws to at most 2 mm projection inside the covers so they cannot enter the moving shaft clearance.',816,12)
    m.finish()
    m.page('Checks and source files','This guide describes the recorded 40 mm configuration; native edits require a new check.')
    m.paragraph(42,118,'The guide uses actual current native-export meshes. The full core stacking path, temporary shaft-tie withdrawal/reinsertion, bench-built motor/tube insertion, three late guide nut paths and four radial grub-tool paths passed CAD checks. Existing current-source checks cover screw seats, cover installation, rotating clearance and native parameter save/reopen.',816,12)
    m.paragraph(42,235,'<b>Not physically test assembled.</b> Cable connectors, printer tolerances and the exact supplied coupler still need checking at the bench. Geometric clearance checks do not establish load capacity or bearing life.',816,12)
    m.paragraph(42,325,'Files alongside this PDF:<br/>README.md - all illustrated stages and individual-part references<br/>hardware.csv / printed-parts.csv - complete inventory<br/>verification.json and proofs/ - traceable CAD checks<br/>images/ - individual assembly illustrations',816,12)
    m.paragraph(42,455,'Native source: simple_double_bearing_version_2_nema17_flange.solidcraft<br/>SHA256: '+proof['source_sha256'],816,10)
    m.paragraph(42,526,'This is an entirely AI-generated coding project. The files are included as a starting point for modifications with your own AI tools. Illustrations use the OOBB teal, black and yellow render guide.',816,11)
    m.finish();m.save()
    return m.page_number

def main():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'images').mkdir(exist_ok=True);(OUT/'proofs').mkdir(exist_ok=True)
    source=ROOT/'simple_double_bearing_version_2_nema17_flange.solidcraft';sha=hashlib.sha256(source.read_bytes()).hexdigest()
    checks={}
    for name,path in [('core',BUILD/'full_core_access.json'),('motor',BUILD/'bench_motor_access.json'),
        ('covers',PART/'end_cover_verification.json'),('native',PART/'native_export_verification.json')]:
        data=json.loads(path.read_text());assert data.get('source_sha256')==sha,(name,'source changed')
        shutil.copy2(path,OUT/'proofs'/path.name);checks[name]='proofs/'+path.name
    for key,title,*_ in STEPS:png(key,title,'NEMA17 / 40 mm motor body')
    png('starting_ties','Starting shaft ties','One temporary screw is reversed at stage 12')
    png('grub_access','Coupler grub access','Reach both grubs before covers and teal joiners')
    labeled_overview()
    final=next(s for s in json.loads((BUILD/'scenes.json').read_text()) if s['key']=='finished')['parts']
    assert len(final)==300
    printed=[n for n in final if not n.startswith('hardware_')];assert len(printed)==sum(p[1] for p in PRINTED)==59
    assert sum(n[1] for n in NUTS)==109
    assert sum(h[1] for h in HARDWARE)==223 # 221 modelled physical pieces + 2 supplied grubs
    proof=dict(source_sha256=sha,configuration='40 mm motor; circular plates; loose contacts; all mounting nuts',
        stage_count=len(STEPS),printed_pieces=59,hardware_model_pieces=221,hardware_mesh_bodies=241,
        additional_unmodelled_grub_screws=2,checks=checks,physical_test=False,geometry_changed_by_guide=False)
    refs=catalogues()
    with (OUT/'hardware.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(refs[0]));w.writeheader();w.writerows(refs)
    with (OUT/'printed-parts.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['name','quantity','native_names_or_size']);w.writerows(PRINTED)
    md(refs,proof);proof['pdf_pages']=pdf(refs,proof)
    (OUT/'verification.json').write_text(json.dumps(proof,indent=2))
    print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
