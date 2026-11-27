"""Render every PDF page and check the guide's files, inventory and source hash."""
import hashlib,json,re
from pathlib import Path
import fitz
from PIL import Image,ImageDraw
from gearbox_native.nema17_depth40_guide import ROOT,BUILD,OUT,STEPS

def main():
    qa=BUILD/'pdf_qa';qa.mkdir(exist_ok=True)
    document=fitz.open(OUT/'assembly-guide.pdf');assert len(document)==32
    errors=[];images=[]
    for i,page in enumerate(document):
        for block in page.get_text('blocks'):
            if len(block)>6 and block[6]!=0:continue
            x0,y0,x1,y1=block[:4]
            if x0<0 or y0<0 or x1>page.rect.width+.1 or y1>page.rect.height+.1:errors.append((i+1,block))
        page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(qa/f'page-{i+1:02d}.png')
        images.append(qa/f'page-{i+1:02d}.png')
    assert not errors,errors
    for offset in range(0,len(images),8):
        sheet=Image.new('RGB',(1200,1880),'#c8cdcb');draw=ImageDraw.Draw(sheet)
        for n,p in enumerate(images[offset:offset+8]):
            im=Image.open(p);im.thumbnail((594,446));x=n%2*600;y=n//2*470
            sheet.paste(im,(x,y));draw.text((x+8,y+450),f'Page {offset+n+1}',fill='black')
        sheet.save(qa/f'contact-{offset//8+1}.png')
    text=(OUT/'README.md').read_text(encoding='utf8')
    for link in re.findall(r'\]\(([^)]+)\)',text):
        if '://' in link:continue
        assert (OUT/link).exists(),link
    render=json.loads((BUILD/'scenes.json').read_text())
    assert [x['key'] for x in render[:23]]==[x[0] for x in STEPS]
    core=next(s for s in render if s['key']=='start')['parts']
    assert len([n for n in core if n.startswith('hardware_guide_M3x35')])==3
    assert not any(n.startswith('hardware_guide_M3x40') for n in core)
    assert 'temporary_shaft_tie' in core
    end=next(s for s in render if s['key']=='finished')['parts'];assert 'temporary_shaft_tie' not in end
    source=ROOT/'simple_double_bearing_version_2_nema17_flange.solidcraft'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==json.loads((OUT/'verification.json').read_text())['source_sha256']
    report=dict(pdf_pages=len(document),page_bounds='passed',local_links='passed',stage_order='passed',
        starting_guide_inventory='passed',source_unchanged=True,pdf_sha256=hashlib.sha256((OUT/'assembly-guide.pdf').read_bytes()).hexdigest(),
        raster_pages=str(qa),visual_review='pending')
    (OUT/'document_qa.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
