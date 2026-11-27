"""Shared hardware patterns retain the actual OOBB nut and overhang prisms."""
from pathlib import Path
import pytest
from oobb_solidcraft.registry import discover

@pytest.mark.parametrize('name,depth',[('m3',2.5),('m6',5.5)])
def test_nut_prisms_include_both_exact_overhang_roofs(name,depth):
 module=discover().module('native_hardware_pattern')
 items=module.prisms(dict(radius_name=name,depth=depth,zz='bottom',overhang=True))
 assert len(items)==5
 assert sum(len(i['points'])==6 for i in items)==1
 assert sorted(round(i['z'],6) for i in items)==[-.6,-.3,0,depth,round(depth+.3,6)]
 assert sum(i['depth']==.3 for i in items)==4
