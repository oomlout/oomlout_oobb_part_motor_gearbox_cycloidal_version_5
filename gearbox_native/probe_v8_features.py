from pathlib import Path
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.registry import discover
from oobb_solidcraft.backend import require_ok
from gearbox_native.acceptance import health_check
folder=Path('D:/codex_builds/gearbox_v8_three_piece_20261028/probes')
with MCPClient(folder/'pattern_session_03',allow_path=Path.cwd(),timeout=600) as client:
 d=discover().module('native_design').Design(client)
 d.parameter('count','6',unit='');d.parameter('use_m6','0',unit='');d.component('plate');d.cylinder(30,10,operation='new')
 discover().module('native_hardware_pattern').cut(d,pitch='18 mm',count='count',z='2 mm',selector='use_m6')
 health_check(client,folder/'pattern_health.json')
 require_ok(client.execute('parameters.change',changes={'count':'4','use_m6':'1'}))
 health_check(client,folder/'pattern_edit_health.json')
 require_ok(client.call('save',dict(path=str(Path.cwd()/'build/native_v8/probe.solidcraft'))))
 print('Native OOBB nut count and size edit passed',flush=True)
