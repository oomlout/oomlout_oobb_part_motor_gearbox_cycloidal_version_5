"""Compare native tab sizing with an independent enumeration of odd plates."""
import json
import math
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.registry import discover
from gearbox_native.project import PROJECT
from gearbox_native.native_tabs import tab_parameters, TAB_RADIUS


def smallest_plate(radius,envelope,gap,pitch=15,inset=1):
    for n in range(3,101,2):
        if n*pitch-inset < 2*radius-1e-8:continue
        if math.hypot((n-1)*pitch/2,pitch)-radius-envelope < gap-1e-8:continue
        return n
    raise ValueError('No candidate in verification range')


def main():
    folder=PROJECT/'build/native_v7/odd_oobb_tab_rule';folder.mkdir(parents=True,exist_ok=False)
    results=[]
    with MCPClient(folder/'session',allow_path=folder,timeout=120) as client:
        d=discover().module('native_design').Design(client)
        d.parameter('casing_radius','36.15 mm')
        for name,expression,unit in tab_parameters():d.parameter(name,expression,unit=unit)
        d.parameter('tab_radius',TAB_RADIUS)
        rows=require_ok(client.execute('parameters.list',filter='user'))['parameters']
        values={p['name']:p['value'] for p in rows};envelope=values['tab_m6_envelope_radius'];gap=values['tab_m6_clearance']
        radii=[10,20,25,30,36.15,38.1,41.1,47.1,60,100]
        for n in (3,5,7,9,11):
            boundary=math.hypot((n-1)*15/2,15)-envelope-gap
            radii.extend([boundary-1e-5,boundary+1e-5])
        for radius in radii:
            require_ok(client.execute('parameters.change',changes={'casing_radius':f'{radius} mm'}))
            values={p['name']:p['value'] for p in require_ok(client.execute('parameters.list',filter='user'))['parameters']}
            expected=smallest_plate(radius,envelope,gap)
            assert values['tab_plate_size']==expected,(radius,values,expected)
            assert values['tab_radius']==(expected-1)*15/2
            assert values['tab_outer_bolt_gap']>=gap-1e-8
            results.append(dict(casing_radius=radius,plate_size=expected,tab_radius=values['tab_radius'],outer_bolt_gap=values['tab_outer_bolt_gap']))
        require_ok(client.execute('parameters.change',changes={'casing_radius':'36.15 mm'}))
        require_ok(client.call('save',dict(path=str(folder/'sizing.solidcraft'))))
    (folder/'verification.json').write_text(json.dumps(dict(status='passed',cases=results),indent=2),encoding='utf-8')
    print('Native odd-plate rule passed',len(results),'independent size and boundary cases')


if __name__=='__main__':main()
