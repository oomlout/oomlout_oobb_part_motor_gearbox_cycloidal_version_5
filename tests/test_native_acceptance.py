import pytest
from gearbox_native.acceptance import health_check,verify_edit,LINEAR_MM,MESH_MM


def test_small_kernel_retry_is_recorded_but_large_retry_fails(tmp_path):
    event=dict(translation_mm=0.0000675,rotation_rad=2e-6,tolerance_mm=0.003)
    health={'timeline':[dict(warning='Boolean retry',boolean_diagnostics={'events':[event]})],
            'sketches':[dict(status='solved',dof=0)]}
    class Client:
        def call(self,*args):return health
    assert health_check(Client(),tmp_path/'health.json')==health
    event['translation_mm']=0.2
    with pytest.raises(ValueError,match='allowance'):health_check(Client(),tmp_path/'bad.json')


def test_edit_must_change_geometry_even_when_inside_geometry_tolerance():
    def measurement(native,expected):return dict(actual={'total':{'volume_mm3':native}},reference={'volume_mm3':expected})
    before=measurement(100,100)
    assert verify_edit(before,measurement(100.1,100.1))['changed']
    with pytest.raises(AssertionError):verify_edit(before,measurement(100,100.1))


def test_design_can_change_without_a_scad_reference():
    from gearbox_native.captured import resolve,build
    from oobb_solidcraft.compiler import compile_thing
    from gearbox_native.export import geometry_digest
    original=resolve({});modified=resolve({'rotor_thickness':7.2,'disc_gap':0.6})
    assert modified['rotor_b_z']!=original['rotor_b_z']
    keys=[]
    for config in (original,modified):
        piece=build(**config)['rotor_a_lower']['thing']
        keys.append(geometry_digest(compile_thing(dict(id='variant',mode='3dpr',**piece))))
    assert keys[0]!=keys[1]
    assert LINEAR_MM==0.05 and MESH_MM==0.1


def test_geometry_digest_ignores_only_empty_csg_operands():
    from gearbox_native.export import geometry_digest
    solid=dict(op='solid',value=dict(kind='cylinder',radius=5,depth=2))
    empty=dict(op='union',children=[])
    noop=dict(op='translate',value=[2,3,4],children=[dict(op='difference',children=[empty,empty])])
    original=dict(tree=dict(op='union',children=[noop,solid]))
    current=dict(tree=dict(op='union',children=[solid]))
    assert geometry_digest(original)==geometry_digest(current)
    assert geometry_digest(current)!=geometry_digest(dict(tree=empty))
    moved=dict(tree=dict(op='union',children=[dict(op='translate',value=[1,0,0],children=[solid])]))
    assert geometry_digest(moved)!=geometry_digest(current)
