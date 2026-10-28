"""Per-part output switches; stdlib-only for the legacy project launcher."""
FLAGS = {'scad': 'run_scad', 'solidcraft': 'run_solidcraft'}

COMPONENT = {
    'name': 'build_policy', 'name_long': 'Per-part build switches', 'category': 'Integration',
    'description': 'Select SCAD and SolidCraft independently using boolean flags in oobb_details.',
    'kind': 'service', 'shape_aliases': [], 'entry_point': 'enabled',
    'returns': 'True when the selected output route is enabled for this part.',
    'variables': [
        {'name': 'details', 'type': 'dict', 'default': 'required', 'description': 'The part oobb_details mapping.'},
        {'name': 'backend', 'type': 'scad or solidcraft', 'default': 'required', 'description': 'Output route being selected.'},
        {'name': 'oobb_type', 'type': 'type name in details', 'default': 'legacy name when absent', 'description': 'plate selects get_plate; new types select their matching get_<type> routine.'},
        {'name': 'run_scad', 'type': 'boolean in details', 'default': True, 'description': 'Allow this part through the SCAD output route.'},
        {'name': 'run_solidcraft', 'type': 'boolean in details', 'default': True, 'description': 'Allow this part through the native output route.'},
    ],
}


def describe():
    import copy
    return copy.deepcopy(COMPONENT)


define = describe


def validate(details):
    if not isinstance(details, dict):
        raise ValueError('oobb_details must be a dictionary')
    for key in FLAGS.values():
        if key in details and type(details[key]) is not bool:
            raise ValueError(f'oobb_details.{key} must be true or false (a boolean, not text or a number)')
    if 'oobb_type' in details:
        value = details['oobb_type']
        if not isinstance(value, str) or not value.isidentifier() or value.startswith('_'):
            raise ValueError('oobb_details.oobb_type must be a type name such as plate or bracket')


def enabled(details, backend):
    validate(details)
    if backend not in FLAGS:
        raise ValueError(f'Unknown output backend: {backend!r}')
    return details.get(FLAGS[backend], True)


def geometry_parameters(parameters):
    """Keep orchestration flags out of builders and primitive dictionaries."""
    return {key: value for key, value in parameters.items() if key not in (*FLAGS.values(), 'oobb_type')}


def builder_name(part):
    """Explicit type selects get_<type>; untyped legacy parts retain name dispatch."""
    details = part.get('oobb_details', {})
    validate(details)
    typ = details.get('oobb_type', part.get('oobb_name', details.get('oobb_name', 'default')))
    if not isinstance(typ, str) or not typ.isidentifier() or typ.startswith('_'):
        raise ValueError(f'Invalid OOBB builder type/name: {typ!r}')
    return 'get_' + typ


def resolve_builder(module, part, *, legacy_fallback=False):
    name = builder_name(part)
    function = getattr(module, name, None)
    if callable(function):
        return function
    if legacy_fallback and 'oobb_type' not in part.get('oobb_details', {}):
        fallback = getattr(module, 'get_base', None)
        if callable(fallback):
            return fallback
    raise ValueError(f'Missing builder {name} in {getattr(module, "__file__", module)}')


def default_builder(project, backend='solidcraft'):
    """Choose the project's native recipe module, or its legacy shared builder."""
    import ast
    from pathlib import Path
    project = Path(project)
    native = project / 'working_solidcraft.py'
    if backend == 'solidcraft' and native.is_file():
        if any(isinstance(node, ast.FunctionDef) and node.name.startswith('get_')
               for node in ast.parse(native.read_text(encoding='utf-8')).body):
            return native
    return project / 'working_scad.py'


action = enabled
