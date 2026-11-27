"""Short assembly manual with one task per landscape page."""
from pathlib import Path
from xml.sax.saxutils import escape
import re
from manual_layout import Manual

P=Path(__file__).resolve().parents[1]


def build_manual(data):
    m=Manual(P/'assembly-guide.pdf',data['title'])
    m.page('OOBB cycloidal gearbox',data['revision']+' | '+data['date'])
    m.image(P/'raw/in_use.png',42,115,530,410)
    m.paragraph(600,145,'A printable gearbox for OOBB mechanisms. Fix the teal outer ring, drive E and connect the load to the black middle ring.',255,13)
    m.paragraph(600,255,'<b>19:1 nominal reduction</b><br/>Two 6810 bearings<br/>Four 6704 bearings<br/>104 mm square plates<br/>6.50 mm centre passage',255,12)
    m.paragraph(600,395,'Square flanges, 16 mm loose sleeves and all captive attachment nuts are shown. External motor, frame, load and their screws are application-specific.',255,11)
    m.paragraph(42,520,escape(data['ai_project_statement']),816,10.5)
    m.paragraph(42,590,'Use the three print plates linked in the repository README. Select either twenty loose outer contacts or one connected ring, and keep six separate inner guide sleeves. The shared layouts include alternative parts.',816,11)
    m.finish()

    m.page('Printed parts','Complete inventory for the illustrated square-flange assembly: 46 printed pieces.')
    for i,p in enumerate(data['printed_parts']):
        col=i//11;row=i%11;x=42+col*418;y=130+row*43
        m.text(x,y,p['ref'],10,True)
        m.text(x+35,y,p['name'],10.5,True)
        m.text(x+365,y,p['quantity'],10.5,True)
        m.paragraph(x+35,y+17,escape(p['spec']),350,9.5)
    m.finish()

    m.page('Hardware','Complete inventory for one gearbox, including all 24 captive attachment nuts. External attachment screws are excluded.')
    for i,p in enumerate(data['hardware']):
        y=135+i*67
        m.text(42,y,p['ref'],12,True)
        m.text(85,y,p['name'],12,True)
        m.text(790,y,'Qty. '+str(p['quantity']),11,True)
        m.paragraph(85,y+23,escape(p['spec']),690,10.5)
        code=p['md5_6_alpha']
        m.text(85,y+43,'OOMP code: '+code,9.5,color='#006D70')
        m.canvas.linkURL(p['url'],(85,m.height-y-57,280,m.height-y-40),relative=0)
    m.paragraph(42,565,'Tools: 2.5 mm hex key for socket caps and 2 mm hex key for the countersunk disc screws. Use 20 ring screws of M3 x 35 for the 20 mm sleeve option; the six guides and two shaft ties remain M3 x 35.',816,10.5)
    m.finish()

    steps=data['readme']['assembly_steps']
    for start in range(0,len(steps),2):
        pair=steps[start:start+2]
        title=['Prepare the parts','Seat and close the starting bearings','Fit the contacts and first disc',
               'Close the cams and second disc','Close the finishing bearings','Fit the caps and reverse the screw',
               'Adjustment and installation'][start//2]
        m.page(title)
        for col,s in enumerate(pair):
            x=42+col*418
            m.paragraph(x,116,f"<b>{start+col+1}. {escape(s['title'])}</b>",392,13)
            m.image(P/'raw'/(s['key']+'.png'),x,165,392,285)
            m.paragraph(x,475,escape(s['body']),392,11)
            if s['key']=='layer_start':
                m.image(P/'raw/layer_start_face.png',x+290,328,95,81)
            if s['key']=='layer_reverse':
                m.text(x,452,'Same screw shown before and after reversal',9.5,color='#006D70')
        m.finish()

    m.page('Captive carrier nuts','Load each set of eight carrier nuts before the flat split closes.')
    m.image(P/'raw/nut_split.png',42,135,480,360)
    m.image(P/'raw/carrier-section-geometry.png',535,145,190,315)
    m.text(735,220,'Carrier cap',11,True)
    m.text(735,290,'M3 nut',11,True,color='#8D6919')
    m.text(735,355,'Carrier core',11,True,color='#006D70')
    m.paragraph(42,525,'At the starting end, retain the eight nuts while lowering the carrier core with its pockets downward. At the finishing end the pockets face upward. The N discs carry four additional attachment nuts each.',816,12)
    m.caption(535,475,'Section drawing.','Production mesh cut through one mounting-hole axis. Nominal nut: 5.5 mm across flats, 2.4 mm thick.',320)
    m.finish()
    m.save()
