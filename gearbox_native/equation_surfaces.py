"""Map shared equation stations onto independently extracted rotor boundaries."""
import copy
import math
import numpy as np
from scipy.spatial import cKDTree
from oobb_solidcraft.registry import discover


def profile_api():
    return discover().module('parametric_profile')


def context(plan, rotor=None):
    found=[]
    def visit(node,matrix):
        op=node['op']
        if op=='rotate':
            rot=np.eye(4)
            for axis,degrees in enumerate(node['value']):
                a=math.radians(degrees);step=np.eye(4);i=(axis+1)%3;j=(axis+2)%3
                step[i,i]=step[j,j]=math.cos(a);step[i,j]=-math.sin(a);step[j,i]=math.sin(a)
                rot=step@rot
            matrix=matrix@rot
        elif op=='translate':
            move=np.eye(4);move[:3,3]=node['value'];matrix=matrix@move
        elif op=='solid' and node['value']['kind']=='parametric_profile':
            if not np.allclose(matrix[:3,3],0,atol=1e-10) or not np.allclose(matrix[2,:3],[0,0,1],atol=1e-10):
                raise ValueError('Equation surface rotor must be authored upright at its local origin')
            found.append((node['value'],matrix[:3,:3].copy()))
        for child in node.get('children',[]):visit(child,matrix)
    visit(plan['tree'],np.eye(4))
    if not found:return None
    if len(found)!=1:raise ValueError('Expected one equation outline per rotor')
    geometry,matrix=found[0]
    if geometry.get('z_offset',0):raise ValueError('Equation rotor must start at local Z=0')
    api=profile_api();setup=api.parameter_commands(geometry,prefix='rotor')
    points=np.asarray(geometry['points'])@matrix[:2,:2].T
    ctx=dict(geometry=geometry,matrix=matrix,points=points.tolist(),tree=cKDTree(points),
                expressions=api.coordinate_expressions(geometry,prefix='rotor'),setup=setup)
    if rotor:bind_interfaces(ctx,rotor)
    return ctx


def bind_interfaces(ctx,rotor):
    """Match every cap and cylindrical boundary to the same mechanical formula."""
    c=rotor['config'];side=rotor['side']
    from gearbox_native.interfaces import for_disc
    c=for_disc(c,side);seat=c['bearing_seats']['cycloid_drive']
    values={'contact_pitch_radius':c['pitch_radius'],'eccentricity':c['radius_offset'],
        'contact_radius':c['lobe_radius'],'profile_clearance':c['lobe_clearance'],
        'disc_thickness':c['rotor_thickness'],'guide_radius':c['guide_pin_diameter']/2,
        'guide_pitch_radius':c['guide_pin_pitch_radius'],'standoff_radius':c['post_radius'],
        'standoff_pitch_radius':c['post_pitch_radius'],
        'centre_bearing_od':c['eccentric_bearing']['od'],'centre_bearing_width':c['eccentric_bearing']['depth']}
    commands=[dict(command='parameters.add',params=dict(name=k,expression=f'{v!r} mm',unit='mm',favorite=True,
        comment='Local rotor dimension. Update gearbox from master controls to synchronize all parts and validate fits.')) for k,v in values.items()]
    aliases={'pitch_radius':'contact_pitch_radius','eccentricity':'eccentricity',
        'roller_radius':'contact_radius','clearance':'profile_clearance'}
    for command in ctx['setup']['commands']:
        for source,target in aliases.items():
            if command['params']['name']==ctx['setup']['parameters'][source]:command['params']['expression']=target
    ctx['setup']['commands']=commands+ctx['setup']['commands']
    ctx['depth_expression']='disc_thickness'
    ctx['floor']=c['rotor_thickness']-seat['seat_depth']
    ctx['floor_expression']=f"disc_thickness - centre_bearing_width - {2*c['bearing_endplay']!r} mm"
    ctx['circles']=[];ctx['rotor']=rotor
    for name,pitch,radius,expression in (
        ('guide',c['guide_pin_pitch_radius'],c['guide_hole_radius'],f"guide_radius + eccentricity + {c['guide_pin_clearance']!r} mm"),
        ('post',c['post_pitch_radius'],c['post_hole_radius'],f"standoff_radius + eccentricity + {c['post_clearance']!r} mm")):
        key='guide_pitch_radius' if name=='guide' else 'standoff_pitch_radius'
        for x,y in c[name+'_positions']:
            if side:y=-y
            ctx['circles'].append(dict(center=[x,y],radius=radius,
                expressions=[f'({x/pitch!r}) * {key}',f'({y/pitch!r}) * {key}'],radius_expression=expression))
    for radius,expression in ((seat['seat_radius'],f"centre_bearing_od / 2 + {c['bearing_seat_clearance']!r} mm"),
                              (seat['through_radius'],'centre_bearing_od / 2 - 0.8 mm')):
        ctx['circles'].append(dict(center=[0,0],radius=radius,expressions=['0 mm','0 mm'],radius_expression=expression))


def z_expression(ctx,value):
    if abs(abs(value)-ctx['geometry']['height'])<1e-8:
        return 'rotor_depth' if value>0 else '-rotor_depth'
    if 'floor' in ctx and abs(abs(value)-ctx['floor'])<1e-8:
        return ('-' if value<0 else '')+'('+ctx['floor_expression']+')'
    return f'{float(value)!r} * profile_unit'


def projected_point(ctx,point,axes):
    """Return formulas only for an actual station, never for a nearby hole."""
    distance,index=ctx['tree'].query(point[:2])
    if distance>1e-7:
        for circle in ctx.get('circles',[]):
            delta=np.asarray(point[:2])-circle['center']
            if abs(np.linalg.norm(delta)-circle['radius'])>1e-7:continue
            xyz=[f"({base}) + ({float(v/circle['radius'])!r}) * ({circle['radius_expression']})" for base,v in zip(circle['expressions'],delta)]
            xyz.append(z_expression(ctx,point[2]))
            return [' + '.join(f'({float(v)!r}) * ({expr})' for v,expr in zip(axis,xyz) if abs(v)>1e-12) or '0 mm' for axis in axes]
        return None
    result=[]
    for axis in axes:
        coefficients=np.asarray(axis)@ctx['matrix']
        terms=[f'({float(v)!r}) * ({expr})' for v,expr in zip(coefficients[:2],ctx['expressions'][index]) if abs(v)>1e-12]
        if abs(axis[2])>1e-12:
            z='rotor_depth' if abs(point[2]-ctx['geometry']['height'])<1e-7 else f'{float(point[2])!r} mm'
            terms.append(f'({float(axis[2])!r}) * ({z})')
        result.append(' + '.join(terms) or '0 mm')
    return result


def edited_plan(plan,value,rotor=None):
    """Independent OCCT reference uses fixed-station numeric points, not CAD output."""
    edited=copy.deepcopy(plan);checks=[]
    def visit(value_node):
        if isinstance(value_node,dict):
            if rotor and value_node.get('kind') in ('cylinder','revolved_profile'):
                c=rotor['config']
                for radius in (c['guide_hole_radius'],c['post_hole_radius']):
                    for key in ('radius','radius_1','radius_2'):
                        if key in value_node and abs(value_node[key]-radius)<1e-8:
                            value_node[key]+=value-c['radius_offset']
                    for point in value_node.get('points',[]):
                        if abs(point[0]-radius)<1e-8:point[0]+=value-c['radius_offset']
            if value_node.get('kind')=='parametric_profile':
                checked=profile_api().validate_edit(value_node,{'eccentricity':value})
                value_node['points']=checked['points']
                value_node['definition']['parameters']['eccentricity']['value']=value
                value_node['cycloidal_parameters']['eccentricity']=value
                checks.append({k:v for k,v in checked.items() if k!='points'})
                return
            for child in value_node.values():visit(child)
        elif isinstance(value_node,list):
            for child in value_node:visit(child)
    visit(edited)
    if not checks:raise ValueError('No equation profile to edit')
    return edited,checks[0]
