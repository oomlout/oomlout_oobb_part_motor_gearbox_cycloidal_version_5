"""Loopback-only bridge between the existing explorer and the native pipeline."""
import argparse,json,subprocess,sys,threading,uuid
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from gearbox_native import controls
from gearbox_native.configurator import check,read_native,atomic_json
from gearbox_native.project import PROJECT,active_part,VERSION

job=None
guard=threading.Lock()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(PROJECT/'cycloidal_explorer/dist'),**kwargs)
    def reply(self,data,status=200):
        body=json.dumps(data).encode();self.send_response(status)
        self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store')
        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def do_GET(self):
        if self.headers.get('Host') not in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'):
            return self.reply({'error':'Use the local loopback URL'},403)
        if self.path=='/api/controls':
            values=controls.validate(controls.saved_overrides())
            return self.reply(dict(values=values,explorer=controls.to_explorer(values),schema=controls.SPECS,
                part=str(active_part()),master=str(PROJECT/'gearbox_controls.solidcraft')))
        if self.path=='/api/status':
            if not job:return self.reply(dict(status='idle'))
            code=job['process'].poll();status='running' if code is None else 'accepted' if code==0 else 'failed'
            log=job['log'].read_text(encoding='utf-8',errors='replace')[-6000:]
            return self.reply(dict(status=status,log=log,part=str(active_part()),log_path=str(job['log'])))
        super().do_GET()
    def do_POST(self):
        global job
        if self.headers.get('Host') not in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'):
            return self.reply({'error':'Use the local loopback URL'},403)
        # A browser page from another origin cannot trigger local writes.
        if self.headers.get('X-Gearbox-Control')!='version_6':return self.reply({'error':'Local control header required'},403)
        origin=self.headers.get('Origin')
        if origin and urlsplit(origin).netloc!=self.headers.get('Host'):return self.reply({'error':'Origin mismatch'},403)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=32768:raise ValueError('Invalid request size')
            data=json.loads(self.rfile.read(size))
            if self.path=='/api/read-native':
                if job and job['process'].poll() is None:raise ValueError('Wait for the active build before reading native controls')
                values=read_native(PROJECT/'gearbox_controls.solidcraft')
                return self.reply(dict(values=values,explorer=controls.to_explorer(values)))
            values=controls.from_explorer(data['explorer'])
            values.update({k:data[k] for k in controls.VIEW_NAMES if k in data})
            values=controls.validate(values)
            if self.path=='/api/check':return self.reply(check(values))
            if self.path!='/api/build':return self.reply({'error':'Unknown action'},404)
            with guard:
                if job and job['process'].poll() is None:raise ValueError('A gearbox update is already running')
                report=check(values)
                folder=PROJECT/'build/parametric_v7/web'/uuid.uuid4().hex[:10];folder.mkdir(parents=True)
                request=folder/'controls.json';atomic_json(request,dict(version=VERSION,values=values))
                path=folder/'build.log'
                with path.open('w',encoding='utf-8') as log:
                    process=subprocess.Popen([sys.executable,'-m','gearbox_native.configurator','--settings',str(request)],
                        cwd=PROJECT,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                job=dict(process=process,log=path)
            return self.reply(dict(status='running',preflight=report),202)
        except Exception as error:self.reply(dict(error=str(error)),400)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8766);args=parser.parse_args()
    print(f'Gearbox controls: http://127.0.0.1:{args.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()


if __name__=='__main__':main()
