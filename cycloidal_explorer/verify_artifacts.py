import base64,re
from pathlib import Path
from pypdf import PdfReader
root=Path(__file__).resolve().parent
pdf=(root/'dist/cycloidal-examples.pdf').read_bytes()
html=(root/'cycloidal-explorer.html').read_text(encoding='utf-8')
embedded=re.search(r'data:application/pdf;base64,([^"\s]+)',html).group(1)
assert base64.b64decode(embedded)==pdf
assert not re.search(r'<script[^>]+src=|<link[^>]+stylesheet|@import',html)
reader=PdfReader(root/'dist/cycloidal-examples.pdf')
assert len(reader.pages)==5
for page in reader.pages:
    assert '6810' in page.extract_text()
    assert abs(float(page.mediabox.width)-595.2756)<.01
    assert abs(float(page.mediabox.height)-841.8898)<.01
print(f'5 A4 pages; embedded PDF matches ({len(pdf):,} bytes); HTML has no external runtime assets.')
