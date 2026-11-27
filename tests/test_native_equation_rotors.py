"""Shared equation mapping, complete boundary links and fixed-station edit limits."""
import math
import pytest
from shapely.geometry import Polygon
from shapely.affinity import rotate,scale
from oobb_solidcraft.compiler import compile_thing
from oobb_solidcraft.registry import discover
from working_oomp_populate import get_options
from gearbox_native.captured import resolve,build
from gearbox_native.lobe import component,shared_component
from gearbox_native.equation_surfaces import context,profile_api,edited_plan
from gearbox_native.exact_geometry import build_shape
from gearbox_native.native_surfaces import plan_surfaces


@pytest.fixture(scope='module')
def configuration():return resolve(get_options()[0]['oobb_details'])


@pytest.mark.parametrize('side',[0,1])
def test_actual_rotors_preserve_phase_dimensions_and_link_every_boundary(configuration,side):
    c=configuration;piece=build(**c)['rotor_'+('a','b')[side]]['thing']
    for mode in ('true','3dpr'):
        plan=compile_thing(dict(id='equation_test',mode=mode,**piece))
        ctx=context(plan);g=ctx['geometry']
        assert g['kind']=='parametric_profile'
        assert g['cycloidal_parameters']['ring_pin_count']==20
        for name,key in [('pitch_radius','pitch_radius'),('eccentricity','radius_offset'),('roller_radius','lobe_radius'),('clearance','lobe_clearance')]:
            assert g['definition']['parameters'][name]['value']==c[key]
        old=Polygon(component(c,c['rotor_thickness'])['points'])
        old=rotate(old,c['disc_phase_degrees'][side],origin=(0,0))
        if side:old=scale(old,xfact=1,yfact=-1,origin=(0,0))
        actual=Polygon(ctx['points'])
        assert actual.is_valid and actual.hausdorff_distance(old)<c['profile_tolerance']*2
        commands=plan_surfaces(build_shape(plan['tree']),outline=ctx['points'],height=g['height'],equation=ctx)
        boundaries=[item for item in commands if item['command']=='sketch.line' and len(item['params']['points'])==len(g['points'])]
        assert len(boundaries)==3 # bottom cap, top cap, wall; includes extracted ordering.
        for boundary in boundaries:
            assert all('rotor_parameter_eccentricity' in coordinate for point in boundary['params']['points'] for coordinate in point)
        assert any(item['command']=='sketch.create' and 'rotor_depth' in str(item['params'].get('offset')) for item in commands)
        wall=next(item for item in commands if item['params'].get('name')=='cycloidal_wall')
        assert wall['params']['distance']=='rotor_depth'


def test_fixed_sampling_failure_requires_regeneration(configuration):
    request=shared_component(configuration,configuration['rotor_thickness'])
    cycloid=discover().module('cycloidal_disc');g=cycloid.profile(request)
    assert profile_api().validate_edit(g,{'eccentricity':1.39})['max_sampled_chord_error_mm']<=.005
    with pytest.raises(ValueError,match='regenerate'):
        profile_api().validate_edit(g,{'eccentricity':1.3})
    regenerated=cycloid.profile(dict(request,eccentricity=1.3))
    assert regenerated['stations']!=g['stations']
    assert profile_api().validate_edit(regenerated)['max_sampled_chord_error_mm']<=.005
    with pytest.raises(ValueError,match='self-intersections'):
        profile_api().validate_edit(g,{'eccentricity':1.42})
