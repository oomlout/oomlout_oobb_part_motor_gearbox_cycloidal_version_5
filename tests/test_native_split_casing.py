"""Split casing retains its working envelope and exposes printable clamp/tab fits."""
import pytest
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut,BRepAlgoAPI_Common,BRepAlgoAPI_Fuse
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from oobb_solidcraft.compiler import compile_thing
from oobb_solidcraft.validation import inspect_shape
from working_oomp_populate import get_options
from gearbox_native.captured import resolve,build
from gearbox_native.simple import output_ring
from gearbox_native.exact_geometry import build_shape,_move
from gearbox_native.split_casing import fit_samples


def volume(s):
    props=GProp_GProps();BRepGProp.VolumeProperties_s(s,props);return abs(props.Mass())


def shape(t):return build_shape(compile_thing(dict(id='split_test',mode='3dpr',**t))['tree'])


@pytest.fixture(scope='module')
def casing():
    c=resolve(get_options()[0]['oobb_details']);pieces=build(**c)
    halves=[shape(pieces['output_casing_'+side]['thing']) for side in ('lower','upper')]
    return c,pieces,halves


def test_seam_print_pose_and_original_working_volume(casing):
    c,pieces,halves=casing
    assert len(pieces)==8 and 'output_casing' not in pieces
    assert c['rotor_a_z']+c['rotor_thickness']<c['output_casing_split_z']<c['rotor_b_z']
    assert sum(c['casing_half_depths'])==pytest.approx(26.6)
    for half,h in zip(halves,c['casing_half_depths']):
        info=inspect_shape(half)
        assert info['valid'] and info['solid_count']==1
        assert info['bounds_mm'][2]==pytest.approx(0,abs=1e-7)
        assert info['bounds_mm'][5]==pytest.approx(h)
        from gearbox_native.native_surfaces import authoring_boundary
        merged=authoring_boundary(half,'test__output_casing_lower')
        assert volume(BRepAlgoAPI_Cut(half,merged).Shape())<1e-5
        assert volume(BRepAlgoAPI_Cut(merged,half).Shape())<1e-5
    lower=_move(_move(halves[0],'rotate',[180,0,0]),'translate',[0,0,c['casing_half_depths'][0]])
    upper=_move(halves[1],'translate',[0,0,c['casing_half_depths'][0]])
    joined=BRepAlgoAPI_Fuse(lower,upper).Shape()
    original=shape(output_ring(c))
    core=BRepPrimAPI_MakeCylinder(c['housing_radius']-.001,26.6).Shape()
    actual=BRepAlgoAPI_Common(joined,core).Shape()
    expected=BRepAlgoAPI_Common(original,core).Shape()
    assert volume(BRepAlgoAPI_Cut(actual,expected).Shape())<1e-5
    assert volume(BRepAlgoAPI_Cut(expected,actual).Shape())<1e-5


def test_tab_holes_are_clear_and_bearing_lands_have_full_wall_backing(casing):
    c,_,halves=casing
    assert c['casing_tab_depth']==3 and c['casing_tab_spacing']==15
    assert c['casing_tab_units']==3 and c['casing_tab_length']==44
    assert c['casing_tab_m6_offsets']==[-15,0,15]
    assert c['casing_tab_m3_offsets']==[-7.5,7.5]
    # A slightly smaller gauge traverses the complete height, not just the pad.
    for half in halves:
        for y,r in [(-15,3),(0,3),(15,3),(-7.5,1.5),(7.5,1.5)]:
            gauge=_move(BRepPrimAPI_MakeCylinder(r,20).Shape(),'translate',[45,y,-1])
            assert volume(BRepAlgoAPI_Common(half,gauge).Shape())<1e-6
        # The flat backing reaches the wall near both ends, not only the middle.
        import math
        for y in (-21,0,21):
            x=math.sqrt(c['housing_radius']**2-y*y)+.2
            gauge=_move(BRepPrimAPI_MakeCylinder(.1,2.8).Shape(),'translate',[x,y,.1])
            assert volume(BRepAlgoAPI_Cut(gauge,half).Shape())<1e-6
        old_lug=_move(BRepPrimAPI_MakeCylinder(2,3).Shape(),'translate',[40/2**.5,40/2**.5,0])
        assert volume(BRepAlgoAPI_Common(half,old_lug).Shape())<1e-6
    # A complete annulus, not just isolated lobe backs, supports each 6810 land.
    for half,height,seat in zip(halves,c['casing_half_depths'],('rear_6810_seat','front_6810_seat')):
        f=c['casing_features'][seat]
        bearing_depth=f['top']-f['bottom']
        # Seat cutters extend 0.03 mm past the nominal stop to avoid coincident faces.
        support_height=height-bearing_depth-.05
        annulus=BRepAlgoAPI_Cut(BRepPrimAPI_MakeCylinder(c['housing_radius']-.01,support_height).Shape(),
            BRepPrimAPI_MakeCylinder(c['casing_bearing_backing_radius']+.01,support_height).Shape()).Shape()
        assert volume(BRepAlgoAPI_Cut(annulus,half).Shape())<1e-5


def test_clamps_and_samples_use_requested_hardware(casing):
    c,_,halves=casing
    assert c['housing_screw_style']=='countersunk' and c['housing_screw_length']==6
    assert len(c['housing_positions'])==4
    assert c['housing_positions'][0]==[45,7.5]
    assert c['case_screw_head_z']-6<c['case_nut_bottom']
    samples=fit_samples(c)
    assert len(samples)==3
    def walk(items):
        for item in items:
            if isinstance(item,list):
                yield from walk(item)
                continue
            yield item
            yield from walk(item.get('objects',[]))
    nuts=[x for x in walk(samples['fit_casing_clamp_lower']['components']) if x.get('intent',{}).get('shape')=='oobb_nut']
    assert nuts and all(x['intent']['overhang'] for x in nuts)
    for name,t in samples.items():
        sample=shape(t)
        info=inspect_shape(sample);assert info['valid'] and info['solid_count']==1
        if name=='fit_casing_clamp_upper':
            from gearbox_native.native_surfaces import authoring_boundary,plan_surfaces
            commands=plan_surfaces(authoring_boundary(sample,'test__'+name))
            assert any(item['command']=='surface.revolve' for item in commands)
    # Splitting the actual print-tolerance casing at its axial stations can
    # divide one complete countersink rim into multiple co-circular arcs.
    from gearbox_native.native_surfaces import authoring_boundary,plan_surfaces,split_boundary_levels
    boundary=authoring_boundary(halves[1],'test__output_casing_upper')
    commands=plan_surfaces(split_boundary_levels(boundary))
    sectors=[item for item in commands if item['command']=='surface.revolve']
    assert len(sectors)==4
    assert sum(float(item['params']['angle'].split()[0]) for item in sectors)==pytest.approx(4*360)
