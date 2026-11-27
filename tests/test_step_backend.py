"""Exact-project CSG and acceptance checks, independent of SolidCraft processes."""
import math
import sys
from pathlib import Path
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gearbox_native.step_backend import build_shape
from oobb_solidcraft.compiler import compile_thing
from oobb_solidcraft.validation import inspect_shape,reference_shape,verify_step
from OCP.STEPControl import STEPControl_Writer,STEPControl_AsIs
from OCP.IFSelect import IFSelect_RetDone


def test_exact_multiple_overlapping_cuts_and_transforms(tmp_path):
    thing={'id':'exact','mode':'true','components':[
        dict(type='positive',shape='cube',size=[20,20,8],pos=[-10,-10,0]),
        dict(type='negative',shape='cylinder',r=3,h=10,pos=[0,0,-1]),
        dict(type='negative',shape='cylinder',r=3,h=10,pos=[3,0,-1]),
        dict(type='negative',shape='cylinder',r=1,h=30,pos=[0,-15,4],rot=[-90,0,0]),
    ]}
    plan=compile_thing(thing)
    shape=build_shape(plan['tree'])
    expected=reference_shape(plan['tree'])
    path=tmp_path/'exact.step'; writer=STEPControl_Writer()
    assert writer.Transfer(shape,STEPControl_AsIs)==IFSelect_RetDone
    assert writer.Write(str(path))==IFSelect_RetDone
    assert verify_step(path,expected)['symmetric_difference_mm3']<0.001


def test_yaml_parameter_change_changes_regenerated_exact_part():
    from gearbox_native.captured import resolve,front_hub
    from gearbox_native.geometry import continuous_negative_sections,subtract_axial_sections
    volumes=[]
    for radius in (24.9,25.1):
        c=resolve({}); c['carrier_journal_radius']=radius
        piece=front_hub(c)
        continuous_negative_sections(piece);subtract_axial_sections(piece)
        plan=compile_thing(dict(id='edited_hub',mode='3dpr',**piece))
        volumes.append(inspect_shape(build_shape(plan['tree']))['volume_mm3'])
    assert volumes[1]>volumes[0]
    h=c['housing_depth']-c['front_hub_bottom']
    assert volumes[1]-volumes[0]==pytest.approx(math.pi*(25.1**2-24.9**2)*h,abs=1e-6)


def test_boundary_comparison_detects_equal_volume_shifted_holes():
    from gearbox_native.verification import analytic_boundary
    signatures=[];volumes=[]
    for x in (2,3):
        plan=compile_thing(dict(id='shift',mode='true',components=[
            dict(type='positive',shape='cube',size=[20,20,5],pos=[-10,-10,0]),
            dict(type='negative',shape='cylinder',r=1,h=7,pos=[x,0,-1])]))
        shape=build_shape(plan['tree'])
        signatures.append(analytic_boundary(shape));volumes.append(inspect_shape(shape)['volume_mm3'])
    assert signatures[0] is not None and signatures[1] is not None
    assert volumes[0]==pytest.approx(volumes[1],abs=1e-8)
    assert signatures[0]!=signatures[1]


def test_geometry_cache_invalidates_a_changed_cut():
    from gearbox_native.export import geometry_digest
    plans=[]
    for identifier,x in [('first',2),('renamed',2),('changed',3)]:
        plans.append(compile_thing(dict(id=identifier,mode='true',components=[
            dict(type='positive',shape='cube',size=[20,20,5],pos=[-10,-10,0]),
            dict(type='negative',shape='cylinder',r=1,h=7,pos=[x,0,-1])])))
    assert geometry_digest(plans[0])==geometry_digest(plans[1])
    assert geometry_digest(plans[0])!=geometry_digest(plans[2])
