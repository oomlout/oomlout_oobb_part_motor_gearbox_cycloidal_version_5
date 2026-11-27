"""Exercise native parameter guards on an isolated unsaved session."""
import json
from pathlib import Path
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from gearbox_native.project import PROJECT
from gearbox_native.acceptance import health_check


def main():
    root=PROJECT/'build/native_v7/assembly_03';out=root/'guard_checks';out.mkdir(exist_ok=True)
    results=[]
    with MCPClient(out/'session',design=root/'gearbox.solidcraft',allow_path=PROJECT,timeout=600) as client:
        health_check(client,out/'opened_health.json')
        original=require_ok(client.execute('parameters.list',filter='user'))
        expressions={p['name']:p['expression'] for p in original['parameters']}
        for name,value in [('reduction','16.5'),('bottom_bearing','9999'),('eccentricity','3 mm'),('guide_radius','2 mm')]:
            result=client.execute('parameters.change',changes={name:value})
            rejected=False
            try:require_ok(result)
            except Exception:rejected=True
            now=require_ok(client.execute('parameters.list',filter='user'))
            errors=[{'name':p['name'],'error':p['error']} for p in now['parameters'] if p.get('error')]
            assert rejected or errors,f'Unsafe edit was silently accepted: {name}'
            changed={p['name']:p['expression'] for p in now['parameters']}
            rollback=all(changed[k]==v for k,v in expressions.items())
            results.append(dict(parameter=name,attempt=value,rejected=rejected,parameter_errors=errors,atomic_rollback=rollback))
            if not rollback:require_ok(client.execute('parameters.change',changes={name:expressions[name]}))
            health_check(client,out/(name+'_recovered_health.json'))
            print(name,'guard passed; atomic rollback:',rollback,flush=True)
    (out/'guards.json').write_text(json.dumps(dict(status='passed',checks=results),indent=2),encoding='utf-8')


if __name__=='__main__':main()
