"""Geometry-sensitive planning checks; native acceptance is recorded per build."""
import math
import pytest
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder,BRepPrimAPI_MakeBox
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.gp import gp_Pnt,gp_Trsf,gp_Ax2,gp_Dir
from gearbox_native.native_surfaces import plan_surfaces,split_boundary_levels


def test_patches_bind_outer_wire_to_keep_holes():
    stock=BRepPrimAPI_MakeBox(20,20,5).Shape()
    hole=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(10,10,-1),gp_Dir(0,0,1)),2,7).Shape()
    commands=plan_surfaces(BRepAlgoAPI_Cut(stock,hole).Shape())
    patches=[c for c in commands if c['command']=='surface.patch']
    assert patches and all(c['params']['profiles']=='OUTER_PROFILE' for c in patches)
    assert any(c.get('capture_outer') for c in commands)
    assert all(not c['command'].startswith(('file.','component.insert')) for c in commands)


def test_reflected_plane_offset_follows_authored_frame():
    source=BRepPrimAPI_MakeBox(gp_Pnt(-2,-3,1),4,6,2).Shape()
    transform=gp_Trsf();transform.SetMirror(gp_Ax2(gp_Pnt(0,0,0),gp_Dir(0,1,0)))
    mirrored=BRepBuilderAPI_Transform(source,transform,True).Shape()
    commands=plan_surfaces(mirrored)
    heights=[]
    for command in commands:
        if command['command']!='sketch.create':continue
        plane=command['params']['plane'];x,y=plane['x_dir'],plane['y_dir']
        normal_z=x[0]*y[1]-x[1]*y[0]
        if abs(normal_z)>0.99:
            offset=float(command['params']['offset'].split(' * ')[0])
            heights.append(round(offset*normal_z,8))
    assert sorted(heights)==[1,3]


def test_axial_boundary_split_adds_no_internal_cap_faces():
    stock=BRepPrimAPI_MakeBox(20,20,8).Shape()
    hole=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(10,10,4),gp_Dir(0,0,1)),3,5).Shape()
    source=BRepAlgoAPI_Cut(stock,hole).Shape()
    split=split_boundary_levels(source)
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    areas=[]
    for shape in (source,split):
        props=GProp_GProps();BRepGProp.SurfaceProperties_s(shape,props,1e-10);areas.append(props.Mass())
    assert areas[0]==pytest.approx(areas[1],abs=1e-8)
    assert plan_surfaces(split)
