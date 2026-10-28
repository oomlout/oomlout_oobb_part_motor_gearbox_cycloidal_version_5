"""Read the preserved current SCAD recipe; store definitions for migration QA."""
import json
from pathlib import Path
import sys
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))
import yaml
from gearbox.parts import resolve,build
part=yaml.safe_load((PROJECT/'parts/oobb_part_motor_gearbox_cycloidal_version_4_20_to_1_reduction/working.yaml').read_text())
c=resolve(part['oobb_details'])
data=dict(config=c,pieces=build(**c))
path=PROJECT/'solidcraft/scad_reference.json'
path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print(path)
