"""Offline A4 page viewer generated from the same pages and links as the PDF."""
import base64
import copy
import hashlib
import html
import json
from pathlib import Path
import fitz


def publish(**kwargs):
    kwargs = copy.deepcopy(kwargs)
    output = Path(kwargs['output'])
    data = kwargs['data']
    book = data['book']
    if not book.get('viewer_enabled', True):
        return
    assert book['viewer_layout'] == 'a4-landscape-four-step'
    per_page = data['style']['columns'] * data['style']['rows']
    assert per_page == 4 and data['style']['page_mm'] == [297, 210]
    images, slides = {}, []
    with fitz.open(output/'assembly_instructions.pdf') as pdf:
        for index, (spec, page) in enumerate(zip(data['book_pages'], pdf), 1):
            key = f'page-{index:02d}'
            kind = spec['kind']
            numbers = []
            if kind == 'instructions':
                first = spec['group'] * per_page + 1
                last = min(first + per_page - 1, len(data['steps']))
                numbers = list(range(first, last + 1))
                label = f'Steps {first}-{last}'
            elif kind == 'summary':
                label = 'Completed assembly'
            else:
                label = {'cover':'Cover', 'details':'Project details', 'parts':'Parts list', 'back':'Back cover', 'spacer':'Blank page'}[kind]
            image = output/'pages'/f'page_{index:02d}.png'
            images[key] = 'data:image/png;base64,' + base64.b64encode(image.read_bytes()).decode('ascii')
            links = []
            for link in page.get_links():
                if link.get('uri', '').startswith('https://'):
                    rect = link['from']
                    links.append(dict(url=link['uri'], rect=[rect.x0/page.rect.width, rect.y0/page.rect.height, rect.width/page.rect.width, rect.height/page.rect.height]))
            slides.append(dict(id=key, label=label, image=key, number=index, kind=kind, steps=numbers, links=links))
    assert len(slides) == len(data['book_pages'])
    payload = dict(slides=slides, images=images, start=book['viewer_start'], layout=book['viewer_layout'], paper_mm=[297,210], step_count=len(data['steps']))
    template = Path(__file__).with_name('assembly_viewer.html').read_text(encoding='utf-8')
    result = template.replace('__TITLE__', html.escape(data['configuration_title']+' | Assembly instructions'))
    result = result.replace('__PROJECT_URL__', html.escape(book['project_url'], quote=True))
    result = result.replace('__DATA__', json.dumps(payload, separators=(',', ':')).replace('<', '\\u003c'))
    target = output/'assembly_instructions.html'
    target.write_text(result, encoding='utf-8')
    report_path = output/'validation.json'
    report = json.loads(report_path.read_text())
    report.update(html_sha256=hashlib.sha256(target.read_bytes()).hexdigest(), html_slides=len(slides), html_steps=len(data['steps']), html_self_contained=True, html_layout=book['viewer_layout'], html_instruction_page_steps=[s['steps'] for s in slides if s['kind']=='instructions'])
    report_path.write_text(json.dumps(report, indent=2))
