"""Open the V6 explorer connected to the native gearbox pipeline."""
import json,subprocess,time,urllib.request,webbrowser
from pathlib import Path
if __name__=='__main__':
    root=Path(__file__).resolve().parent;url='http://127.0.0.1:8766'
    try:urllib.request.urlopen(url+'/api/controls',timeout=1)
    except OSError:
        config=json.loads((root/'solidcraft/config.json').read_text(encoding='utf-8'))
        log=root/'outputs/gearbox_control_server.log';log.parent.mkdir(exist_ok=True)
        with log.open('w',encoding='utf-8') as stream:
            subprocess.Popen([config['python'],'-m','gearbox_native.control_server'],cwd=root,
                stdout=stream,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        for _ in range(30):
            try:urllib.request.urlopen(url+'/api/controls',timeout=1);break
            except OSError:time.sleep(.2)
        else:raise RuntimeError('Control server did not start; see '+str(log))
    webbrowser.open(url)
