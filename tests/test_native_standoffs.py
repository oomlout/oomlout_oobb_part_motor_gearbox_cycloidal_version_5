"""Reinforced posts retain nut access, wall thickness and a real socket-head roof."""
import pytest
from gearbox_native.captured import resolve,build
from gearbox_native.standoffs import fit_samples
from oobb_solidcraft.compiler import compile_thing

def config(**kw):
    return resolve(dict(architecture='simple_6810',drive_connection='grub_nut',
        direct_stack_layout='base_grub',post_fasteners=True,radius_offset=1.4,
        pitch_radius_increment=.05,lobe_eccentricity_ratio=.93,**kw))

def test_slim_posts_and_taller_interlock_keep_socket_heads_and_tips_recessed():
    c=config();assert c==resolve(c)
    assert c['post_radius']==2.7 and c['post_register_depth']==1.6
    assert c['post_register_radius']==2.3
    assert c['post_radius']-c['post_register_radius']-c['post_register_clearance']>=.2
    assert c['post_screw_length']==25 and c['post_screw_hole_radius']==1.7
    assert c['post_screw_head_z']==25.6 and c['post_nut_bottom']==pytest.approx(.8)
    assert c['post_nut_top']==pytest.approx(3.3)
    assert c['post_screw_head_z']+3<c['housing_depth']
    assert c['post_fastener_socket_floor']-c['post_register_depth']-c['post_register_clearance']>=.8
    assert c['fastener_interfaces']['standoff_clamp']['positions']==c['post_positions']

def test_post_wall_and_socket_roof_constraints_reject_unusable_changes():
    with pytest.raises(ValueError,match='wall'):
        config(post_radius=2.2)
    with pytest.raises(ValueError,match='roof'):
        config(post_register_depth=3)
    with pytest.raises(ValueError,match='motor face'):
        config(post_screw_length=30)

def test_matching_standoff_fit_samples_compile_as_individual_parts():
    c=config();samples=fit_samples(c);assert len(samples)==2
    for name,sample in samples.items():
        assert compile_thing(dict(id=name,mode='3dpr',**sample))['result_bodies']
    # Check the actual solids: the socket seats without collision, then stops
    # on the shoulder if pushed another 0.05 mm, rather than bottoming on the peg.
    from gearbox_native.exact_geometry import build_shape,_move
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    shapes={name:build_shape(compile_thing(dict(id=name,mode='true',**sample))['tree'])
            for name,sample in samples.items()}
    def overlap(z):
        common=BRepAlgoAPI_Common(shapes['fit_M3_standoff_lower'],
            _move(shapes['fit_M3_standoff_socket'],'translate',[0,0,z]))
        assert common.IsDone()
        props=GProp_GProps();BRepGProp.VolumeProperties_s(common.Shape(),props)
        return abs(props.Mass())
    assert overlap(c['front_support_bottom'])<1e-7
    assert overlap(c['front_support_bottom']-.05)>.1

def test_print_clearance_nut_pockets_preserve_native_countersink_surfaces():
    # Regression: the taller screw seat let a print-clearance nut pocket clip
    # a NEMA countersink, producing conical trims the native exporter cannot author.
    from gearbox_native.exact_geometry import build_shape
    from gearbox_native.native_surfaces import plan_surfaces,split_boundary_levels
    part=build(**config())['motor_mount']['thing']
    plan=compile_thing(dict(id='standoff_mount',mode='3dpr',**part,
                            sequential_unions=True,compound_cuts=True))
    assert plan_surfaces(split_boundary_levels(build_shape(plan['tree'])))
