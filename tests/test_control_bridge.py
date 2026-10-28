"""Exercise the local HTTP boundary without triggering CAD builds."""
import json,threading,urllib.request,urllib.error
import pytest
from http.server import ThreadingHTTPServer
from gearbox_native.control_server import Handler
from gearbox_native.controls import defaults,to_explorer


@pytest.fixture(scope='module')
def service():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    yield 'http://127.0.0.1:'+str(server.server_port)
    server.shutdown();server.server_close();thread.join()


def post(url,data,headers=None):
    request=urllib.request.Request(url,data=json.dumps(data).encode(),headers=headers or {
        'Content-Type':'application/json','X-Gearbox-Control':'version_6'})
    return json.load(urllib.request.urlopen(request))


def test_serves_actual_controls_and_production_preflight(service):
    saved=json.load(urllib.request.urlopen(service+'/api/controls'))
    assert saved['values']['reduction']==20 and 'gearbox_controls.solidcraft' in saved['master']
    report=post(service+'/api/check',{'explorer':to_explorer(defaults())})
    assert report['status']=='recipe_valid' and report['diameter_mm']==72.3
    assert report['resolved_values']['contact_pitch_radius']==31.15
    html=urllib.request.urlopen(service).read().decode()
    assert 'cad_controls.js' in html


def test_invalid_dimensions_and_cross_origin_requests_rejected(service):
    values=defaults();values['eccentricity']=4
    with pytest.raises(urllib.error.HTTPError) as error:
        post(service+'/api/check',{'explorer':to_explorer(values)})
    assert error.value.code==400
    with pytest.raises(urllib.error.HTTPError) as error:
        post(service+'/api/build',{},headers={'Content-Type':'application/json'})
    assert error.value.code==403
    with pytest.raises(urllib.error.HTTPError) as error:
        post(service+'/api/check',{'explorer':to_explorer(defaults())},headers={
            'X-Gearbox-Control':'version_6','Origin':'https://unrelated.example'})
    assert error.value.code==403
