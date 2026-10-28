"""Bundle all runtime assets and the example PDF into one offline HTML file."""
import base64,re
from pathlib import Path
root=Path(__file__).resolve().parent
dist=root/'dist'
html=(dist/'index.html').read_text(encoding='utf-8')
css=(dist/'style.css').read_text(encoding='utf-8')
css=re.sub(r"@import url\([^\n]+\);\n",'',css)
html=html.replace('<link rel="stylesheet" href="style.css">','<style>'+css+'</style>')
for name in ('geometry.js','studies.js','diagram.js','app.js','cad_controls.js'):
    html=html.replace(f'<script defer src="{name}"></script>','')
script='\n'.join((dist/name).read_text(encoding='utf-8') for name in ('geometry.js','studies.js','diagram.js','app.js','cad_controls.js'))
html=html.replace('</body>','<script>'+script+'</script></body>')
pdf=base64.b64encode((dist/'cycloidal-examples.pdf').read_bytes()).decode('ascii')
html=html.replace('href="cycloidal-examples.pdf" download','href="data:application/pdf;base64,'+pdf+'" download="cycloidal-examples.pdf"')
out=root/'cycloidal-explorer.html';out.write_text(html,encoding='utf-8')
assert not re.search(r'<script[^>]+src=|<link[^>]+stylesheet|@import',html)
print(f'{out} ({out.stat().st_size:,} bytes; offline assets and PDF embedded)')
