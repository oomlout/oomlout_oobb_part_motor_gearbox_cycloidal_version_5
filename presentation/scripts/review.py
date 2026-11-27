"""Render manual pages and a local CommonMark README preview for visual QA."""
import json
from pathlib import Path
import shutil
import subprocess
from PIL import Image,ImageDraw,ImageFont
from markdown_it import MarkdownIt

P=Path(__file__).resolve().parents[1]
ROOT=P.parent


def main():
    subprocess.run(['pdftoppm','-r','120','-png',str(P/'assembly-guide.pdf'),str(P/'qa/manual')],check=True)
    pages=sorted((P/'qa').glob('manual-[0-9]*.png'))
    tile_w,tile_h=600,475
    contact=Image.new('RGB',(tile_w*3,tile_h*((len(pages)+2)//3)),'#DDDDDD')
    draw=ImageDraw.Draw(contact)
    for i,path in enumerate(pages):
        im=Image.open(path).convert('RGB');im.thumbnail((600,450))
        x=(i%3)*tile_w;y=(i//3)*tile_h
        contact.paste(im,(x,y));draw.text((x+12,y+450),f'Page {i+1}',fill='black')
    contact.save(P/'qa/manual-contact-sheet.png')
    md=MarkdownIt('commonmark').enable('table')
    content=md.render((ROOT/'README.md').read_text(encoding='utf8'))
    html='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>OOBB README preview</title><base href="'''+ROOT.as_uri()+'''/"><style>
*{box-sizing:border-box}body{margin:0;color:#1f2328;font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#fff}
main{max-width:1012px;margin:32px auto;padding:32px;border:1px solid #d1d9e0;border-radius:6px}
h1{font-size:32px}h2{font-size:24px;border-bottom:1px solid #d1d9e0;padding-bottom:.3em;margin-top:28px}
img{max-width:100%;height:auto}a{color:#0969da;text-decoration:none}a:hover{text-decoration:underline}
table{display:block;max-width:100%;overflow-x:auto;border-spacing:0;border-collapse:collapse;font-size:14px}
td,th{padding:6px 13px;border:1px solid #d1d9e0}th{white-space:nowrap}td code{white-space:nowrap}
tr:nth-child(2n){background:#f6f8fa}code{background:#eff1f3;padding:2px 4px;font-size:85%}li{padding:2px 0}li p{margin:8px 0}
@media(max-width:700px){main{margin:0;border:0;padding:20px}h1{font-size:27px}ol{padding-left:24px}}
</style><main>'''+content+'</main>'
    (P/'qa/readme-preview.html').write_text(html,encoding='utf8')
    print('Rendered',len(pages),'manual pages and README preview.')


if __name__=='__main__':main()
