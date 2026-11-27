"""Exact recipe rewrites for native kernels; no mesh or tolerance relaxation."""
import copy
import math
from shapely.geometry import Polygon
from shapely.ops import unary_union


def continuous_negative_sections(thing):
    """Union coaxial bores, counterbores and tapers before subtracting material.

    Exact planar sections avoid both the Hole feature's drill semantics and
    separately cutting two tools that meet at the same blind-pocket plane.
    """
    def transform(sections, item):
        rx,ry,rz=item.get('rot',[0,0,0])
        if abs(rx % 180)>1e-9 or abs(ry % 180)>1e-9:
            return None
        sx,sy=round(math.cos(math.radians(ry))),round(math.cos(math.radians(rx)))
        sz=sx*sy
        c,s=math.cos(math.radians(rz)),math.sin(math.radians(rz))
        px,py,pz=item.get('pos',[0,0,0])
        return [(px+c*sx*x-s*sy*y,py+s*sx*x+c*sy*y,
                 [[r,pz+sz*z] for r,z in points]) for x,y,points in sections]
    def collect(item,mode):
        if isinstance(item,list):
            out=[]
            for child in item:
                result=collect(child,mode)
                if result is None:return None
                out.extend(result)
            return out
        if item.get('inclusion','all') not in ('all',mode):return []
        if item.get('intent',{}).get('shape')=='oobb_holes':return None
        if item.get('type')=='rotation':
            result=collect(item['objects'],mode)
            return None if result is None else transform(result,item)
        if item.get('shape')=='cylinder':
            h=item['h']; r=item.get('r',item.get('radius'))
            points=[[0,0],[item.get('r1',r),0],[item.get('r2',r),h],[0,h]]
        elif item.get('shape')=='revolved_profile':points=item['points']
        else:return None
        return transform([(0,0,points)],item)
    rest=[]
    groups={}
    for item in thing['components']:
        negative=item.get('typetype') in ('n','negative') if item.get('type')=='rotation' else item.get('type') in ('n','negative')
        if not negative:
            if item.get('type')=='rotation':
                continuous_negative_sections({'components':item['objects']})
            rest.append(item)
            continue
        modes={mode:collect(item,mode) for mode in ('laser','true','3dpr')}
        if any(value is None for value in modes.values()):
            rest.append(item)
            continue
        for mode,sections in modes.items():
            for x,y,points in sections:
                groups.setdefault((x,y,mode),[]).append(Polygon(points))
    for (x,y,mode),sections in groups.items():
        shape=unary_union(sections).simplify(1e-10,preserve_topology=True)
        for polygon in ([shape] if shape.geom_type=='Polygon' else shape.geoms):
            if polygon.interiors:raise ValueError('Unexpected axial cutter hole')
            rest.append(dict(type='negative',shape='revolved_profile',pos=[x,y,0],inclusion=mode,
                points=[list(p) for p in list(polygon.exterior.coords)[:-1]]))
    thing['components'][:]=rest
    return thing


def subtract_axial_sections(thing):
    """Resolve coaxial stock and bores in 2D when all stock shares one axis."""
    items = thing['components']
    positive = [item for item in items if item.get('type') in ('p', 'positive')]
    if not positive or any(item.get('shape') not in ('cylinder','revolved_profile')
                           or any(item.get('pos',[0,0,0])[:2])
                           or any(item.get('rot',[0,0,0])[:2]) for item in positive):
        return thing
    if any(item.get('type') == 'rotation' and item.get('typetype') in ('p','positive') for item in items):
        return thing
    negative = [item for item in items if item.get('type') in ('n','negative')
                and item.get('shape') == 'revolved_profile'
                and not any(item.get('pos',[0,0,0])[:2])
                and not any(item.get('rot',[0,0,0])[:2])]
    if not negative:
        return thing
    def section(item):
        z=item.get('pos',[0,0,0])[2]
        if item['shape']=='revolved_profile':
            return Polygon([(r,h+z) for r,h in item['points']])
        r=item.get('r',item.get('radius')); h=item['h']
        return Polygon([(0,z),(item.get('r1',r),z),(item.get('r2',r),z+h),(0,z+h)])
    replacement=[]
    for mode in ('laser','true','3dpr'):
        stock=unary_union([section(i) for i in positive if i.get('inclusion','all') in ('all',mode)])
        cuts=unary_union([section(i) for i in negative if i.get('inclusion','all') in ('all',mode)])
        material=stock.difference(cuts).simplify(1e-10,preserve_topology=True)
        for polygon in ([material] if material.geom_type=='Polygon' else material.geoms):
            if polygon.interiors:
                return thing
            replacement.append(dict(type='positive',shape='revolved_profile',inclusion=mode,pos=[0,0,0],
                                    points=[list(p) for p in list(polygon.exterior.coords)[:-1]]))
    selected={id(i) for i in positive+negative}
    thing['components'][:]=replacement+[i for i in items if id(i) not in selected]
    return thing


def continuous_positive_sections(thing):
    """Merge coaxial positive cylinders/tapers in their exact radius/Z plane."""
    groups = {}
    rest = []
    for leaf in thing['components']:
        if (leaf.get('type') not in ('positive', 'p') or leaf.get('shape') != 'cylinder'
                or any(leaf.get('rot', [0,0,0]))):
            rest.append(leaf)
            continue
        key = (*leaf['pos'][:2], leaf.get('inclusion', 'all'))
        groups.setdefault(key, []).append(leaf)
    for (x, y, mode), leaves in groups.items():
        if len(leaves) == 1:
            rest.extend(leaves)
            continue
        polygons=[]
        for leaf in leaves:
            z, h = leaf['pos'][2], leaf['h']
            r = leaf.get('r', leaf.get('radius'))
            polygons.append(Polygon([(0,z),(leaf.get('r1',r),z),
                                     (leaf.get('r2',r),z+h),(0,z+h)]))
        # Derived heights can differ by a few binary floating-point ULPs.
        # Remove only numerical slivers, far below the 0.0005 mm profile budget.
        section=unary_union(polygons).simplify(1e-10, preserve_topology=True)
        if section.geom_type != 'Polygon' or section.interiors:
            rest.extend(leaves)
            continue
        rest.append(dict(type='positive',shape='revolved_profile',pos=[x,y,0],inclusion=mode,
                         points=[list(p) for p in list(section.exterior.coords)[:-1]]))
    thing['components']=rest
    return thing


def continuous_countersinks(objects):
    """Revolve the exact union of the source's concentric shaft/head sections.

    The old screw expansion emits redundant shafts in multiple modes. Preserve
    their actual outer envelope, including the 1.8 mm shaft in true mode, rather
    than substituting an idealized screw or fusing coincident cones in 3D.
    """
    result = copy.deepcopy(objects)
    for group in result:
        if group.get('type') != 'rotation':
            raise ValueError('Expected a grouped countersunk screw')
        sections = []
        for mode in ('laser', 'true', '3dpr'):
            polygons = []
            for leaf in group['objects']:
                if leaf.get('inclusion', 'all') not in ('all', mode):
                    continue
                if leaf.get('shape') != 'cylinder' or any(leaf.get('rot', [0, 0, 0])) or any(leaf['pos'][:2]):
                    raise ValueError('Countersink rewrite requires coaxial cylinders/cones')
                z = leaf['pos'][2]
                h = leaf['h']
                bottom = leaf.get('r1', leaf.get('r'))
                top = leaf.get('r2', leaf.get('r'))
                polygons.append(Polygon([(0,z),(bottom,z),(top,z+h),(0,z+h)]))
            section = unary_union(polygons).simplify(0)
            if section.geom_type != 'Polygon' or section.interiors:
                raise ValueError('Countersink section must be one simple profile')
            sections.append(dict(type='positive', shape='revolved_profile', inclusion=mode,
                                 points=[list(point) for point in list(section.exterior.coords)[:-1]], pos=[0,0,0]))
        group['objects'] = sections
    return result
