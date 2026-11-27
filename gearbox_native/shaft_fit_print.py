"""Build a quick shaft-only fit print using the same native features as the assembly."""
import argparse
from pathlib import Path
import shutil
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.registry import discover
from gearbox_native.acceptance import health_check,verify_mesh
from gearbox_native.simple_double_bearing import parameters
from gearbox_native import stacked_disc_shaft as shaft
from gearbox_native.project import PROJECT
from gearbox_native.verification import read_step
from gearbox_native.double_bearing_outputs import shaft_kit
def build(out):
    out.mkdir(parents=True,exist_ok=False)
    parts=out/'native_parts';parts.mkdir()
    with MCPClient(out/'author',allow_path=PROJECT,timeout=600) as c:
        d=discover().module('native_design').Design(c);parameters(d)
        canonical={}
        for name,kind,*_ in shaft.LAYERS:
            if kind in canonical:
                for ext in ('step','stl'):shutil.copyfile(parts/(canonical[kind]+'.'+ext),parts/(name+'.'+ext))
                continue
            shaft.part(d,name)
            for ext in ('step','stl'):
                require_ok(c.call('export',dict(path=str(parts/(name+'.'+ext)),bodies=[name])))
            verify_mesh(parts/(name+'.stl'),read_step(parts/(name+'.step')))
            canonical[kind]=name
        health_check(c,out/'health.json')
    shaft_kit(out,shaft.NAMES,{'middle_length':16})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);build(p.parse_args().folder.resolve())

