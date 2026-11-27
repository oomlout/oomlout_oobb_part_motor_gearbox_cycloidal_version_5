"""Validate a generated presentation package, without accessing the network.

Checks data paths, quantities, README links, image presence and PDF text bounds.
Hardware identity and physical fit still need review. Requires Pillow and PyMuPDF.
"""
import argparse,json,re
from pathlib import Path
from urllib.parse import unquote,urlsplit
from PIL import Image
import fitz

def validate(root):
    root=Path(root).resolve();p=root/'presentation'
    data=json.loads((p/'project.json').read_text(encoding='utf-8'))
    errors=[];refs=set();count=0
    for part in data['printed_parts']+data['hardware']:
        if part['ref'] in refs:errors.append('Duplicate reference: '+part['ref'])
        refs.add(part['ref'])
        if not isinstance(part['quantity'],int) or part['quantity']<1:errors.append('Invalid quantity: '+part['ref'])
        if 'stl' in part:
            if not (root/part['stl']).is_file():errors.append('Missing STL: '+part['stl'])
            count+=part['quantity']
        elif part.get('oomp_id') and not part.get('url'):errors.append('Missing catalogue URL: '+part['ref'])
    readme=root/data.get('readme_filename','README.md')
    md=readme.read_text(encoding='utf-8')
    if 'AI-generated' not in md:errors.append('Missing README AI notice')
    links=re.findall(r'\]\(([^)]+)\)',md)
    checked=0
    for link in links:
        if urlsplit(link).scheme or link.startswith('#'):continue
        path=unquote(link.split('#',1)[0])
        if not (readme.parent/path).exists():errors.append('Missing README target: '+path)
        checked+=1
    for image in (p/'images').rglob('*.png'):
        with Image.open(image) as im:im.verify()
    if data.get('readme',{}).get('layout') == 'four-section':
        if re.findall(r'^## (.+)$',md,re.M) != ['Summary','Details','Parts','Assembly']:
            errors.append('README headings differ from the four-section format')
        for i,step in enumerate(data['readme']['assembly_steps'],1):
            thumb=p/'images/thumbnails'/f'step-{i:02d}.png'
            if not thumb.is_file():
                errors.append('Missing assembly thumbnail: '+str(thumb))
            else:
                with Image.open(thumb) as im:
                    if max(im.size)>480:errors.append('Oversized thumbnail: '+str(thumb))
            full='presentation/images/'+step['image']
            if f']({full})' not in md:errors.append('Missing full-size image link: '+full)
    doc=fitz.open(p/'assembly-guide.pdf')
    for i,page in enumerate(doc):
        if 'AI-generated' not in page.get_text():errors.append(f'Missing AI footer: PDF page {i+1}')
        for word in page.get_text('words'):
            x0,y0,x1,y1=word[:4]
            if min(x0,y0)<0 or x1>page.rect.width+.2 or y1>page.rect.height+.2:
                errors.append(f'Text outside page {i+1}: {word[4]}')
    expected=data.get('geometry',{}).get('printed_count')
    if expected is not None and count!=expected:errors.append('Printed total differs from geometry manifest')
    report={'status':'PASS' if not errors else 'FAIL','printed_parts':count,'hardware_pieces':sum(x['quantity'] for x in data['hardware']),
            'pdf_pages':len(doc),'local_readme_links_checked':checked,'published_images':len(list((p/'images').glob('*.png'))),'errors':errors,
            'scope':'Digital consistency only. External link identity requires source inspection; physical build is untested.'}
    (p/'qa').mkdir(exist_ok=True)
    (p/'qa/validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('project',type=Path)
    result=validate(parser.parse_args().project)
    print(json.dumps(result,indent=2))
    raise SystemExit(bool(result['errors']))
