"""Native expressions for the smallest usable odd OOBB plate footprint.

The two outer M6 holes on each three-wide tab are at y=+-15 mm.
Both the casing and the head/nut envelope must fit; no gearbox fit is inferred.
"""
from oobb_solidcraft import api as oobb


def tab_parameters():
    pitch=oobb.gv('osp')
    inset=oobb.gv('osp_minus')
    envelope=max(oobb.gv('screw_socket_cap_radius_m6','3dpr'),oobb.gv('nut_radius_m6','3dpr'))
    return [
        ('tab_oobb_pitch',f'{pitch} mm','mm'),
        ('tab_oobb_inset',f'{inset} mm','mm'),
        ('tab_m6_envelope_radius',f'{envelope} mm','mm'),
        ('tab_m6_clearance','0.5 mm','mm'),
        ('tab_required_radius','max(casing_radius - (tab_oobb_pitch - tab_oobb_inset) / 2, sqrt(max((0 mm)^2, (casing_radius + tab_m6_envelope_radius + tab_m6_clearance)^2 - tab_oobb_pitch^2)))','mm'),
        ('tab_plate_size','2 * max(1, ceil(tab_required_radius / tab_oobb_pitch)) + 1',''),
        ('tab_plate_width','tab_plate_size * tab_oobb_pitch - tab_oobb_inset','mm'),
        ('tab_outer_bolt_gap','sqrt(((tab_plate_size - 1) * tab_oobb_pitch / 2)^2 + tab_oobb_pitch^2) - casing_radius - tab_m6_envelope_radius','mm'),
    ]


TAB_RADIUS='(tab_plate_size - 1) * tab_oobb_pitch / 2'
