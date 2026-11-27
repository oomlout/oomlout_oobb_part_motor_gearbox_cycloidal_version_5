"""Check every offered bearing code using SolidCraft's own expression evaluator."""
import json
from pathlib import Path
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.registry import discover
from gearbox_native.native_v7 import parameters
from gearbox_native.project import PROJECT


def main():
    class Collector:
        def __init__(self):self.entries=[]
        def parameter(self,name,expression,**kwargs):self.entries.append((name,expression,kwargs))
    collector=Collector();parameters(collector)
    definitions={name:(expression,kwargs) for name,expression,kwargs in collector.entries}
    expected=json.loads((PROJECT/'solidcraft/casing_bearings.json').read_text())['options']
    folder=PROJECT/'build/native_v7/casing_selector';folder.mkdir(exist_ok=False)
    report={'options':{},'fit_checked':False}
    with MCPClient(folder/'session',allow_path=folder,timeout=120) as client:
        d=discover().module('native_design').Design(client)
        for name in ('casing_bearing','casing_bore_catalogue','casing_od','casing_width','casing_catalogue_guard'):
            expression,kwargs=definitions[name];d.parameter(name,expression,**kwargs)
        for code,spec in expected.items():
            require_ok(client.execute('parameters.change',changes={'casing_bearing':code}))
            values={p['name']:p['value'] for p in require_ok(client.execute('parameters.list',filter='user'))['parameters']}
            actual=dict(id=values['casing_bore_catalogue'],od=values['casing_od'],depth=values['casing_width'])
            assert actual==spec,(code,actual,spec)
            report['options'][code]=actual
        for invalid in ('6810.5','6799','9999'):
            rejected=False
            try:require_ok(client.execute('parameters.change',changes={'casing_bearing':invalid}))
            except Exception:rejected=True
            assert rejected,invalid
        require_ok(client.execute('parameters.change',changes={'casing_bearing':'6810'}))
        require_ok(client.call('save',dict(path=str(folder/'selector.solidcraft'))))
    report.update(status='passed',invalid_codes_rejected=['6810.5','6799','9999'])
    (folder/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Verified',len(expected),'native selector options and invalid code rejection')


if __name__=='__main__':main()
