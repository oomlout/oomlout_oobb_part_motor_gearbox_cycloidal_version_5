"""Hollow eccentric drive with one captured M3 nut and radial set screw.

The nut loads from the print's bottom, with its threaded axis radial. The long
keyed stem surrounds the motor shaft and carries the axial joining nut above
the shaft tip. No purchased flange coupling is required.
"""
import math
from gearbox_native import parts as p
from oobb_solidcraft import api as oobb


def configure(c):
    c['motor_shaft_radius']=2.5
    c['direct_shaft_bore_radius']=c['motor_shaft_radius']+c['direct_shaft_clearance']
    c['direct_grub_outer_radius']=c['motor_shaft_radius']+c['direct_grub_length']
    c['direct_grub_bore_radius']=oobb.gv('hole_radius_m3','3dpr')
    c['direct_nut_depth']=oobb.gv('nut_depth_m3','true')+2*c['direct_nut_clearance']
    c['direct_grub_nut_radius']=c['direct_nut_inner_radius']+c['direct_nut_clearance']
    c['fastener_interfaces'].pop('coupler_flange')
    c['fastener_interfaces']['shaft_grub']=dict(size='m3',length=c['direct_grub_length'],
        angle=c['direct_grub_angle'],height=c['coupling_grub_z'],nut_loading='bottom',
        nut_inner_radius=c['direct_nut_inner_radius'],nut_depth=c['direct_nut_depth'],
        overhang=True,access='before fitting motor plate' if c['base_grub'] else 'before fitting rear 6810')


def validate(c):
    checks=[
        (c['direct_stack_layout'] in ('raised','base_grub'),'Unknown direct stack layout'),
        (not c['base_grub'] or c['drive_flange_radius']+.1<=c['motor_pilot_diameter']/2+c['motor_pilot_clearance'],'Motor plate must pass over the installed hub'),
        (not c['base_grub'] or c['drive_start']>=c['motor_pilot_height']+.2,'Hub must clear the motor pilot'),
        (c['direct_grub_outer_radius']<=c['drive_flange_radius'],'Grub screw must fit within the rotating hub envelope'),
        (c['direct_nut_inner_radius']-c['direct_shaft_bore_radius']>=1.4,'Nut requires a retaining wall toward the shaft'),
        (c['direct_nut_inner_radius']+c['direct_nut_depth']+1.4<c['drive_flange_radius'],'Nut requires an outer retaining wall'),
        (c['direct_grub_height']>oobb.gv('nut_radius_m3','3dpr')+.3,'Nut pocket must be above the hub base'),
        (c['direct_grub_height']+oobb.gv('nut_radius_m3','3dpr')+.8<c['drive_flange_depth'],'Nut requires a roof below the eccentric bearing'),
        (c['hub_nut_bottom']>=c['motor_shaft_length']+c['direct_shaft_endplay']+.5,'Axial nut must clear the motor shaft tip'),
        (c['hub_key_depth']>2,'Hollow keyed stem must reach the upper joining nut'),
        (c['hub_key_radius']-c['direct_shaft_bore_radius']>=2,'Hollow key wall is too thin'),
        (c['shaft_journal_radius']-c['hub_key_radius']-c['hub_key_clearance']>=.8,'Upper key socket wall is too thin'),
        (c['hub_bolt_head_z']+3<=c['hub_upper_end'],'Axial socket screw must remain recessed'),
        (c['hub_bolt_head_z']-(c['hub_split_z']+c['hub_key_depth']+c['hub_key_clearance']+.02)>=.8,'Axial socket screw needs a retaining roof above the key'),
        (c['rotor_a_z']>=c['casing_features']['lobe_start_ramp']['bottom']+
            c['casing_features']['lobe_start_ramp']['depth']-1e-9,'Discs must start above the lobe entry ramp'),
    ]
    for valid,message in checks:
        if not valid:raise ValueError(message)


def radial_nut_and_screw_cut(t,c):
    """OOBB nut clearance left becomes a downward loading slot after rotation."""
    cutter=p.blank();z=c['direct_grub_height']
    p.add(cutter,'oobb_nut','n',pos=[c['direct_nut_inner_radius'],0,z],radius_name='m3',
          depth=c['direct_nut_depth'],zz='bottom',rot=[0,90,0],
          clearance='left',clearance_tightness=c['direct_nut_clearance'],overhang=True)
    # The metal nut supplies the thread. A square printed passage is easy to
    # bridge and leaves exact axial/planar surfaces in the native CAD history.
    length=c['drive_flange_radius']+1;r=c['direct_grub_bore_radius']
    p.add(cutter,'oobb_cube','n',pos=[length/2,0,z-r],size=[length,2*r,2*r],zz='bottom')
    p.cut_group(t,cutter,[0,0,0],[0,0,c['direct_grub_angle']])


def hub_sample(c):
    t=p.blank();hub_stock(t,c)
    p.hole(t,c['direct_shaft_bore_radius'],c['drive_flange_depth'])
    radial_nut_and_screw_cut(t,c)
    return t


def hub_stock(t,c):
    # Move the circular surface's parametric seam away from the radial slot.
    # This changes no material, but avoids an OCCT seam spanning a removed face.
    stock=p.blank();p.cylinder(stock,c['drive_flange_radius'],c['drive_flange_depth'])
    p.group(t,stock,rot=[0,0,c['direct_grub_angle']+90])


def lower(c):
    from gearbox_native.captured import shaft
    t=p.blank();start=c['drive_start'];h=c['drive_flange_depth']
    hub_stock(t,c)
    p.group(t,shaft(c,key_socket=False),[0,0,h])
    p.hole(t,c['direct_shaft_bore_radius'],c['motor_shaft_length']+c['direct_shaft_endplay']-start)
    p.add(t,'oobb_nut','n',pos=[0,0,c['hub_nut_bottom']-start],radius_name='m3',
          depth=oobb.gv('nut_depth_m3','true')+c['direct_key_roof_clearance']+.2,
          zz='bottom',rot=[0,0,30],overhang=True)
    radial_nut_and_screw_cut(t,c)
    return t


def upper(c):
    from gearbox_native.captured import shaft
    # The keyed socket surrounds the hollow lower stem. Above that socket the
    # existing M3 bore/head recess accepts the short joining screw.
    return shaft(c,True)
