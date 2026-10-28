"""Source geometry evaluator for native sketch planning and independent diagnostics.

No SolidCraft import or export occurs here. The native surface path uses this
geometry to author constrained sketches and native extrusion/revolution features.
"""
import math
from pathlib import Path

from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon, BRepBuilderAPI_Transform
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeCone, BRepPrimAPI_MakePrism, BRepPrimAPI_MakeRevol
from OCP.TopTools import TopTools_ListOfShape
from OCP.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Dir, gp_Ax1

def _move(shape, kind, values):
    operations = [(None,values)] if kind=='translate' else list(enumerate(values))
    for axis,value in operations:
        transform=gp_Trsf()
        if axis is None:
            transform.SetTranslation(gp_Vec(*value))
        else:
            if not value: continue
            vector=[0,0,0]; vector[axis]=1
            transform.SetRotation(gp_Ax1(gp_Pnt(0,0,0),gp_Dir(*vector)),math.radians(value))
        shape=BRepBuilderAPI_Transform(shape,transform,True).Shape()
    return shape


def _boolean(kind, stock, tools):
    if not tools:return stock
    arguments=TopTools_ListOfShape(); arguments.Append(stock)
    cutters=TopTools_ListOfShape()
    for shape in tools:cutters.Append(shape)
    operation=(BRepAlgoAPI_Cut if kind=='cut' else BRepAlgoAPI_Fuse)()
    operation.SetArguments(arguments); operation.SetTools(cutters)
    operation.SetNonDestructive(True)
    operation.Build()
    if not operation.IsDone():raise RuntimeError(f'Exact {kind} failed')
    shape=operation.Shape()
    if not BRepCheck_Analyzer(shape).IsValid():raise RuntimeError(f'Exact {kind} produced an invalid BRep')
    return shape


def _polygon(points, vertical=False):
    wire=BRepBuilderAPI_MakePolygon()
    for x,y in points:wire.Add(gp_Pnt(x,0,y) if vertical else gp_Pnt(x,y,0))
    wire.Close()
    return BRepBuilderAPI_MakeFace(wire.Wire()).Face()


def build_shape(node):
    """Project-owned OCCT construction, separate from the validation oracle."""
    op=node['op']
    if op in ('translate','rotate'):
        shape=build_shape(node['children'][0])
        return None if shape is None else _move(shape,op,node['value'])
    if op=='union':
        shapes=[build_shape(child) for child in node['children']]
        shapes=[s for s in shapes if s is not None]
        return _boolean('join',shapes[0],shapes[1:]) if shapes else None
    if op=='difference':
        stock=build_shape(node['children'][0])
        # Multiple independent tools avoid a huge intermediate union and retain
        # the exact semantics A minus (B union C).
        negatives=node['children'][1]
        tools=[build_shape(child) for child in negatives['children']] if negatives['op']=='union' else [build_shape(negatives)]
        return _boolean('cut',stock,[s for s in tools if s is not None])
    if op!='solid':raise ValueError(f'Unsupported exact operation: {op}')
    g=node['value']; kind=g['kind']
    if kind=='cube':return BRepPrimAPI_MakeBox(*g['size']).Shape()
    if kind=='cylinder':shape=BRepPrimAPI_MakeCylinder(g['radius'],g['height']).Shape()
    elif kind=='cone':shape=BRepPrimAPI_MakeCone(g['radius_bottom'],g['radius'],g['height']).Shape()
    elif kind=='revolved_profile':
        return BRepPrimAPI_MakeRevol(_polygon(g['points'],True),gp_Ax1(gp_Pnt(0,0,0),gp_Dir(0,0,1))).Shape()
    elif kind in ('polygon','parametric_profile','polyg'):
        points=g['points'] if kind in ('polygon','parametric_profile') else [(g['radius']*math.cos(i*2*math.pi/g['sides']),g['radius']*math.sin(i*2*math.pi/g['sides'])) for i in range(g['sides'])]
        shape=BRepPrimAPI_MakePrism(_polygon(points),gp_Vec(0,0,g['height'])).Shape()
    else:raise ValueError(f'Unsupported exact primitive: {kind}')
    return _move(shape,'translate',[0,0,g.get('z_offset',0)])


