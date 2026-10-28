"""Exact analytic boundary comparison for dense imported rotor BReps.

Matching every trimmed analytic face avoids performing a second enormous CSG
cut on thousands of coincident polygon faces. Unsupported or changed topology
falls back to the helper's symmetric Boolean comparison, never to volume alone.
"""
import math
import hashlib
import json
import os
import uuid
from pathlib import Path
from collections import Counter
import numpy as np
from OCP.BRepAdaptor import BRepAdaptor_Surface,BRepAdaptor_Curve
from OCP.BRepTools import BRepTools
from OCP.GeomConvert import GeomConvert_CurveToAnaCurve
from OCP.Geom import Geom_Circle,Geom_Line
from OCP.Geom import Geom_BSplineSurface,Geom_CylindricalSurface
from OCP.GeomAdaptor import GeomAdaptor_Surface
from OCP.BRep import BRep_Tool
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.GeomAbs import GeomAbs_Plane,GeomAbs_Cylinder,GeomAbs_Cone,GeomAbs_Line,GeomAbs_Circle
from OCP.TopAbs import TopAbs_FACE,TopAbs_WIRE,TopAbs_EDGE,TopAbs_REVERSED
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS
from OCP.TopoDS import TopoDS_Shape
from OCP.BRep import BRep_Builder
from OCP.gp import gp_Pnt,gp_Vec,gp_Ax3
from oobb_solidcraft.validation import read_step as uncached_read_step,inspect_shape
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import OCP


def _sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def cache_shape(path,shape):
    """Cache parsing only; every acceptance still compares to its own reference."""
    sha=_sha(path);root=Path(__file__).resolve().parents[1]/'build/solidcraft/step_cache'
    root.mkdir(parents=True,exist_ok=True)
    key=sha+'_'+OCP.__version__;brep=root/(key+'.brep');meta=root/(key+'.json')
    temporary=root/(key+'.'+uuid.uuid4().hex+'.tmp')
    assert BRepTools.Write_s(shape,str(temporary))
    os.replace(temporary,brep)
    temporary.write_text(json.dumps(dict(step_sha256=sha,brep_sha256=_sha(brep),ocp_version=OCP.__version__)))
    os.replace(temporary,meta)


def read_step(path):
    sha=_sha(path);root=Path(__file__).resolve().parents[1]/'build/solidcraft/step_cache'
    key=sha+'_'+OCP.__version__;brep=root/(key+'.brep');meta=root/(key+'.json')
    if brep.is_file() and meta.is_file():
        data=json.loads(meta.read_text())
        if data==dict(step_sha256=sha,brep_sha256=_sha(brep),ocp_version=OCP.__version__):
            shape=TopoDS_Shape()
            if BRepTools.Read_s(shape,str(brep),BRep_Builder()):return shape
    shape=uncached_read_step(path)
    cache_shape(path,shape)
    return shape


def _values(values):
    return tuple(round(float(x),8) for x in values)


def _direction(values):
    values=np.asarray(values,dtype=float)
    for value in values:
        if abs(value)>1e-9:
            return values if value>0 else -values
    raise ValueError('Zero analytic direction')


def _circle_frame(axis):
    axis=np.array(axis)
    x=np.array([0.,1.,0.]) if abs(axis[0])>.9 else np.array([1.,0.,0.])
    x-=axis*(x@axis);x/=np.linalg.norm(x)
    return x,np.cross(axis,x)


def _merge_circle_arcs(edges,periodic):
    circles={};other=[]
    for item in edges:
        if item[0]!='circle':other.append(item);continue
        base=item[:4]; intervals=circles.setdefault(base,[])
        if item[4]=='closed':intervals.append((0.,2*math.pi));continue
        center=np.array(base[1]);x,y=_circle_frame(base[2])
        def angle(point):
            delta=np.array(point)-center
            return math.atan2(delta@y,delta@x)%(2*math.pi)
        start,end=map(angle,item[5]);middle=angle(item[6]);span=(end-start)%(2*math.pi)
        if (middle-start)%(2*math.pi)>span:
            start,end=end,start;span=2*math.pi-span
        finish=start+span
        if finish<=2*math.pi+1e-10:intervals.append((start,min(finish,2*math.pi)))
        else:intervals.extend(((start,2*math.pi),(0.,finish-2*math.pi)))
    for base,intervals in circles.items():
        merged=[]
        for start,end in sorted(intervals):
            if merged and start<=merged[-1][1]+1e-9:
                merged[-1]=(merged[-1][0],max(end,merged[-1][1]))
            else:merged.append((start,end))
        other.append(base+('ranges',tuple((round(a,9),round(b,9)) for a,b in merged)))
    if periodic:
        # A periodic face's seam occurs twice, in opposite directions, in the
        # same wire. Its arbitrary angular placement is not a trim boundary.
        counts=Counter(other)
        other=[edge for edge in other if not (edge[0]=='line' and counts[edge]==2)]
    return tuple(sorted(other))


def translated_circle_surface(face):
    """Recognize an exact rational circular extrusion without refitting it.

    Equal rational weights and a constant displacement between the two rows
    prove that every intermediate row is a translation of the same curve.
    Only an analytic circle and an axial displacement qualify as a cylinder.
    """
    surface=BRep_Tool.Surface_s(face)
    if not isinstance(surface,Geom_BSplineSurface) or surface.VDegree()!=1 or surface.NbVPoles()!=2:
        return None
    shifts=[]
    for i in range(1,surface.NbUPoles()+1):
        if abs(surface.Weight(i,1)-surface.Weight(i,2))>1e-12:return None
        shifts.append(np.array(surface.Pole(i,2).Coord())-surface.Pole(i,1).Coord())
    delta=shifts[0]
    if any(np.linalg.norm(shift-delta)>1e-9 for shift in shifts):return None
    u0,u1,v0,v1=surface.Bounds()
    circle=GeomConvert_CurveToAnaCurve.ComputeCurve_s(surface.VIso(v0),1e-9,u0,u1,0.,0.,0.)
    if not isinstance(circle,Geom_Circle):return None
    axis=np.array(circle.Axis().Direction().Coord())
    if np.linalg.norm(delta-axis*(delta@axis))>1e-9:return None
    return GeomAdaptor_Surface(Geom_CylindricalSurface(gp_Ax3(circle.Position()),circle.Radius()))


def analytic_boundary(shape):
    faces=Counter(); explorer=TopExp_Explorer(shape,TopAbs_FACE)
    while explorer.More():
        face=TopoDS.Face_s(explorer.Current()); surface=BRepAdaptor_Surface(face)
        reversed_face=face.Orientation()==TopAbs_REVERSED
        point=gp_Pnt();du=gp_Vec();dv=gp_Vec()
        surface.D1((surface.FirstUParameter()+surface.LastUParameter())/2,
                   (surface.FirstVParameter()+surface.LastVParameter())/2,point,du,dv)
        normal=np.array(du.Crossed(dv).Normalized().Coord())
        if reversed_face:normal=-normal
        if surface.GetType() not in (GeomAbs_Plane,GeomAbs_Cylinder,GeomAbs_Cone):
            surface=translated_circle_surface(face)
            if surface is None:return None
        if surface.GetType()==GeomAbs_Plane:
            # The complete boundary curves fix the plane's offset; retaining
            # a separately rounded offset introduces redundant numeric noise.
            support=('plane',_values(normal))
        elif surface.GetType()==GeomAbs_Cylinder:
            cylinder=surface.Cylinder(); axis=_direction(cylinder.Axis().Direction().Coord())
            origin=np.array(cylinder.Location().Coord()); origin-=axis*(origin@axis)
            radial=np.array(point.Coord())-origin;radial-=axis*(radial@axis)
            support=('cylinder',_values(axis),_values(origin),round(cylinder.Radius(),8),bool(normal@radial<0))
        elif surface.GetType()==GeomAbs_Cone:
            cone=surface.Cone();angle=cone.SemiAngle()
            axis=np.array(cone.Axis().Direction().Coord())*(1 if angle>0 else -1)
            apex=np.array(cone.Apex().Coord())
            radial=np.array(point.Coord())-apex;radial-=axis*(radial@axis)
            support=('cone',_values(axis),_values(apex),round(abs(angle),12),bool(normal@radial<0))
        else:return None
        outer=BRepTools.OuterWire_s(face); wires=[]
        wire_ex=TopExp_Explorer(face,TopAbs_WIRE)
        while wire_ex.More():
            wire=TopoDS.Wire_s(wire_ex.Current()); edges=[]
            edge_ex=TopExp_Explorer(wire,TopAbs_EDGE)
            while edge_ex.More():
                curve=BRepAdaptor_Curve(TopoDS.Edge_s(edge_ex.Current()))
                a,b=curve.FirstParameter(),curve.LastParameter()
                ends=tuple(sorted((_values(curve.Value(a).Coord()),_values(curve.Value(b).Coord()))))
                circle=None;line=curve.GetType()==GeomAbs_Line
                if curve.GetType()==GeomAbs_Circle:
                    circle=curve.Circle()
                elif not line:
                    converted=GeomConvert_CurveToAnaCurve.ComputeCurve_s(curve.Curve().Curve(),1e-9,a,b,0.,0.,0.)
                    if isinstance(converted,Geom_Circle):circle=converted.Circ()
                    elif isinstance(converted,Geom_Line):line=True
                    else:return None
                if line:
                    item=('line',ends)
                elif circle is not None:
                    axis=_direction(circle.Axis().Direction().Coord());center=np.array(circle.Location().Coord())
                    radius=circle.Radius()
                    base=('circle',_values(center),_values(axis),round(radius,8))
                    if np.linalg.norm(np.array(ends[0])-ends[1])<1e-8:
                        item=base+('closed',)
                    else:
                        # Rational spline and analytic-circle parameters differ.
                        # Use their common geometric arc midpoint, not the midpoint
                        # of the parameter interval, to identify the selected arc.
                        x,y=_circle_frame(axis)
                        def angle(point):
                            delta=np.array(point)-center
                            return math.atan2(delta@y,delta@x)
                        start,end=map(angle,ends);middle=angle(curve.Value((a+b)/2).Coord())
                        span=(end-start)%(2*math.pi)
                        theta=start+span/2 if (middle-start)%(2*math.pi)<=span else start-(2*math.pi-span)/2
                        midpoint=center+radius*(math.cos(theta)*x+math.sin(theta)*y)
                        item=base+('arc',ends,_values(midpoint))
                else:return None
                edges.append(item);edge_ex.Next()
            wires.append((wire.IsSame(outer),_merge_circle_arcs(edges,support[0] in ('cylinder','cone'))))
            wire_ex.Next()
        faces[(support,tuple(sorted(wires)))]+=1
        explorer.Next()
    return faces


def canonical_boundary(shape):
    unify=ShapeUpgrade_UnifySameDomain(shape,True,True,False)
    unify.SetSafeInputMode(True)
    unify.SetLinearTolerance(1e-9)
    unify.SetAngularTolerance(1e-12)
    unify.Build()
    result=unify.Shape()
    return analytic_boundary(result)


def verify_step(path,reference):
    shape=read_step(path)
    actual,expected=inspect_shape(shape),inspect_shape(reference)
    assert actual['valid'] and actual['solid_count']==expected['solid_count']
    assert np.max(np.abs(np.array(actual['bounds_mm'])-expected['bounds_mm']))<1e-5
    error=abs(actual['volume_mm3']-expected['volume_mm3'])
    assert error<max(1e-5,expected['volume_mm3']*1e-8),error
    boundary=canonical_boundary(reference)
    if boundary is not None and boundary==canonical_boundary(shape):
        return dict(validator='Open CASCADE '+OCP.__version__,actual=actual,expected=expected,
            comparison_method='identical_canonical_trimmed_analytic_boundary',face_count=sum(boundary.values()),
            canonicalization_linear_tolerance_mm=1e-9,canonicalization_angular_tolerance_rad=1e-12,
            coordinate_quantization_mm=1e-8,volume_error_mm3=error)
    difference=0.
    for first,second in ((shape,reference),(reference,shape)):
        cut=BRepAlgoAPI_Cut(first,second)
        assert cut.IsDone(),'Symmetric difference did not complete'
        properties=GProp_GProps()
        BRepGProp.VolumeProperties_s(cut.Shape(),properties,1e-10,True,False)
        difference+=abs(properties.Mass())
    assert difference<0.001,difference
    return dict(validator='Open CASCADE '+OCP.__version__,actual=actual,expected=expected,
        comparison_method='symmetric_boolean_difference',symmetric_difference_mm3=difference,volume_error_mm3=error)
