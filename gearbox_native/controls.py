"""One public control vocabulary for the explorer, saved CAD and recipe inputs.

This module is deliberately stdlib-only: populate uses the ordinary Python,
while native validation and generation use the configured CAD interpreter.
"""
import json
import math
from pathlib import Path
from gearbox_native.project import VERSION

ROOT = Path(__file__).resolve().parents[1]
VALUES_PATH = ROOT / 'gearbox_native' / 'control_values.json'

# name, default, unit, lower, upper, explorer name, recipe name, description
ROWS = [
    ('reduction',20,'',3,60,'ratio','reduction','Ring contacts; disc lobes = reduction - 1. Rebuild required.'),
    ('automatic_pitch',1,'',0,1,'auto','automatic_pitch','1 calculates the minimum usable pitch; 0 uses the manual radius.'),
    ('radius_buffer',0.,'mm',0,25,'radiusBuffer','pitch_radius_buffer','Extra radius above the calculated minimum; automatic mode only.'),
    ('contact_pitch_radius',31.15,'mm',10,150,'radius','pitch_radius','Centre to ring contact centre; used in manual mode.'),
    ('contact_radius',3.,'mm',.3,10,'roller','lobe_radius','Radius, not diameter, of each circular contact.'),
    ('eccentricity',1.4,'mm',.1,5,'eccentricity','radius_offset','Orbit radius; also drives all moving clearance holes.'),
    ('profile_clearance',.2,'mm',0,1,'clearance','lobe_clearance','Radial profile running clearance.'),
    ('casing_wall',2.,'mm',.8,6,'wall','casing_wall','Radial wall outside contacts and casing bearing seats.'),
    ('disc_thickness',5.,'mm',2,12,'thickness','rotor_thickness','Thickness of each disc; must retain its selected bearing.'),
    ('disc_gap',.5,'mm',.1,3,'gap','disc_gap','Axial gap between the opposed discs.'),
    ('standoff_radius',2.7,'mm',1.7,12,'postRadius','post_radius','Body radius of the three screw-reinforced standoffs.'),
    ('standoff_pitch_radius',18.55,'mm',3,70,'postPitch','post_pitch_radius','Centre to each standoff centre.'),
    ('guide_radius',1.5,'mm',1.5,3,'guideRadius',None,'Production guides use catalogue M3 or M6 socket screws, subject to fit checks.'),
    ('guide_pitch_radius',17.4,'mm',3,70,'guidePitch','guide_pin_pitch_radius','Centre to each of the six guide screws.'),
    ('reference_bearing',6810,'',6700,6812,'referenceBearing','reference_bearing','Display scale only; the actual casing bearings remain 6810.'),
    ('top_bearing',6703,'',6700,6812,'topBearing','bearing_eccentric_top','Purchased centre bearing in the upper disc.'),
    ('bottom_bearing',6703,'',6700,6812,'bottomBearing','bearing_eccentric_bottom','Purchased centre bearing in the lower disc.'),
    ('input_angle',0.,'deg',0,21600,None,None,'Assembly viewing position; not a manufacturing dimension.'),
    ('reference_underlay',1,'',0,1,None,None,'Display the reference bearing beneath the explorer discs.'),
    ('amber_clearance',.1,'mm',0,5,None,None,'Explorer warning threshold; does not add manufacturing clearance.'),
]
SPECS = {row[0]: dict(zip(('default','unit','min','max','explorer','recipe','description'),row[1:])) for row in ROWS}
BOOLEAN_NAMES = {'automatic_pitch','reference_underlay'}
BEARING_NAMES = {'reference_bearing','top_bearing','bottom_bearing'}
VIEW_NAMES = {'reference_bearing','input_angle','reference_underlay','amber_clearance'}


def defaults():
    return {name: spec['default'] for name,spec in SPECS.items()}


def validate(values, *, complete=True):
    if not isinstance(values,dict):raise ValueError('Controls must be a JSON object')
    unknown=set(values)-set(SPECS)
    if unknown:raise ValueError('Unknown controls: '+', '.join(sorted(unknown)))
    result=defaults() if complete else {}
    for name,value in values.items():
        if isinstance(value,str) and name in BEARING_NAMES and value.isdigit():value=int(value)
        if isinstance(value,bool) and name in BOOLEAN_NAMES:value=int(value)
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
            raise ValueError(f'{name} must be a finite number')
        spec=SPECS[name]
        if not spec['min']<=value<=spec['max']:
            raise ValueError(f"{name} must be between {spec['min']} and {spec['max']} {spec['unit']}")
        if name in BOOLEAN_NAMES|BEARING_NAMES|{'reduction'}:
            if int(value)!=value:raise ValueError(f'{name} must be a whole number')
            value=int(value)
        if name=='guide_radius' and value not in (1.5,3):
            raise ValueError('The installed OOBB socket-head catalogue supplies M3 and M6: use guide radius 1.5 or 3 mm. Other radii remain explorer studies.')
        if name in BEARING_NAMES and not (6700<=value<=6711 or 6800<=value<=6812):
            raise ValueError(f'{name}: choose a supported 6700- or 6800-series catalogue size')
        result[name]=value
    return result


def to_kwargs(values):
    values=validate(values,complete=False);result={}
    for name,value in values.items():
        target=SPECS[name]['recipe']
        if target:result[target]=str(value) if name in BEARING_NAMES else value
    if 'guide_radius' in values:
        diameter=2*values['guide_radius']
        result['guide_pin_diameter']=diameter
        result['guide_bolt_radius_name']='m'+format(diameter,'g')
    return result


def from_config(c):
    result=defaults()
    for name,spec in SPECS.items():
        if spec['recipe'] in c:
            value=c[spec['recipe']]
            if value is not None:result[name]=int(value) if name in BEARING_NAMES else value
    result.update(automatic_pitch=int(c['radius_calculation']['mode']=='automatic'),
                  guide_radius=c['guide_pin_diameter']/2,
                  contact_pitch_radius=c['pitch_radius'],
                  top_bearing=int(c.get('bearing_eccentric_top',c['bearing_eccentric'])),
                  bottom_bearing=int(c.get('bearing_eccentric_bottom',c['bearing_eccentric'])))
    return validate(result)


def from_explorer(values):
    if not isinstance(values,dict):raise ValueError('Explorer settings must be an object')
    mapping={spec['explorer']:name for name,spec in SPECS.items() if spec['explorer']}
    return validate({mapping[k]:v for k,v in values.items() if k in mapping})


def to_explorer(values):
    values=validate(values)
    return {spec['explorer']:(str(values[name]) if name in BEARING_NAMES else bool(values[name]) if name in BOOLEAN_NAMES else values[name])
            for name,spec in SPECS.items() if spec['explorer']}


def saved_overrides(path=VALUES_PATH):
    path=Path(path)
    if not path.exists():return {}
    data=json.loads(path.read_text(encoding='utf-8'))
    if data.get('version')!=VERSION:raise ValueError('Control settings belong to another design version')
    return validate(data['values'],complete=False)


def native_commands(values):
    values=validate(values)
    return [dict(command='parameters.add',params=dict(name=name,
        expression=f"{values[name]} {spec['unit']}".strip(),unit=spec['unit'],
        favorite=True,comment=spec['description'])) for name,spec in SPECS.items()]
