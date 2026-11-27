"""Native purchased-hardware references for the double-bearing style."""
import argparse
import math
from pathlib import Path
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.registry import discover
from gearbox_native.project import PROJECT
from gearbox_native.simple_double_bearing import guide_angles
from gearbox_native.acceptance import health_check


def hardware(d):
    def plane(z,level):
        return f'({z}) + ({level}) * explode + 150 mm * print_layout'

    def batch(name,z,h,level,radius,*,pitch,count,angle,bore=None,hexagon=False,socket=False,printed=False):
        d.component(('printed_' if printed else 'hardware_')+name)
        def section(r,hex_shape,operation,height,offset):
            if printed:
                outer=name=='contact_sleeve'
                cx,cy=(54,54) if outer else (162,54)
                center=[f'{cx} mm * layout_scale * print_layout',f'{cy} mm * layout_scale * print_layout']
                radius_pitch=f'({pitch}) * (1 - print_layout) + {26.5 if outer else 16} mm * print_layout'
                offset=f'(({z}) + ({level}) * explode) * (1 - print_layout)'
            else:
                center=['0 mm','0 mm'];radius_pitch=pitch
            sketch=d.sketch(name+'_'+operation,offset)
            for phase in guide_angles() if count=='guide_count' else (angle,):
                if hex_shape:
                    curves=d.line([[f'({pitch}) * cos({phase}) + ({r}) * cos({phase} + {i*60} deg)',
                                    f'({pitch}) * sin({phase}) + ({r}) * sin({phase} + {i*60} deg)'] for i in range(6)])
                else:
                    curves=d.circle(r,[f'({center[0]}) + ({radius_pitch}) * cos({phase})',
                                       f'({center[1]}) + ({radius_pitch}) * sin({phase})'])
                if count!='guide_count':
                    d.pattern(curves,count,center=center)
            if operation=='new':d.extrude(sketch,height,'new',all_profiles=True)
            else:
                # With no explicit targets the native feature cuts every intersected member
                # of the variable-count pattern, including new members after a ratio edit.
                d.finish()
                d.do('solid.extrude',sketch=sketch,distance=height,operation='cut',profiles='all')
        # Construct pierced reference stock before the screw shanks are present.
        section(radius,hexagon,'new',h,plane(z,level))
        if bore:section(bore,False,'cut',h,plane(z,level))
        if socket:section('1.45 mm',True,'cut','1.5 mm',plane(z if socket=='bottom' else f'({z}) + ({h}) - 1.5 mm',level))

    row=dict(pitch='pitch',count='ring_count',angle='output_angle')
    guides=dict(pitch='guide_pitch',count='guide_count',angle=None)
    batch('contact_sleeve','middle_start','middle_length',5,'contact_radius',bore='spacer_bore',printed=True,**row)
    batch('M3_ring_nuts','0 mm','2.4 mm',-1,'3.17543 mm',bore='1.55 mm',hexagon=True,**row)
    batch('drive_sleeve','middle_start','middle_length',5,'contact_radius',bore='spacer_bore',printed=True,**guides)
    batch('ring_cap_heads','join_length','3 mm',11,'2.75 mm',socket=True,**row)
    batch('ring_M3_shanks','0 mm','join_length',11,'1.50 mm',**row)
    batch('drive_nuts','drive_tip','2.4 mm',-1,'3.17543 mm',bore='1.55 mm',hexagon=True,**guides)
    batch('drive_caps','drive_tip + carrier_drive_length','3 mm',10,'2.75 mm',socket=True,**guides)
    batch('drive_shanks','drive_tip','carrier_drive_length',10,'1.5 mm',**guides)

    def ring(name,ri,ro,h,z,level,offset='0 mm'):
        d.component('hardware_'+name)
        xy=[f'({offset}) * cos(input_angle)',f'({offset}) * sin(input_angle)']
        d.cylinder(ro,h,z=plane(z,level),xy=xy,inner=ri,operation='new',name='nominal_race_envelope')

    for tag,z,level in [('bottom','main_outer_face',.5),('top','stack_height - main_inner_face',9.5)]:
        ring('6810_'+tag,'main_bearing_bore / 2','main_bearing_od / 2','main_bearing_width',z,level)
    for tag,z,level,e in [('base','race_end_gap',1.5,'0 mm'),('disc_a','disc_a_z + disc_lip',4,'eccentricity'),
                          ('disc_b','disc_b_z + disc_lip',7,'-eccentricity'),('top','stack_height - shaft_race_width - race_end_gap',8.5,'0 mm')]:
        ring('6704_'+tag,'10 mm','shaft_race_od / 2','shaft_race_width',z,level,e)
    # Each clamshell closes on its outer bearing race. Fasteners follow the orbital
    # translation of the disc while retaining the orientation of its fixed guide tracks.
    for side in ('a','b'):
        bottom=side=='a'
        base='disc_a_z' if bottom else 'disc_b_z + disc_thickness'
        for i in range(3):
            angle=f'(clamp_phase + {i*120} deg)'
            sign='' if bottom else '-'
            xy=[f'clamp_pitch * cos({angle}) + {sign}eccentricity * cos(input_angle)',
                f'clamp_pitch * sin({angle}) + {sign}eccentricity * sin(input_angle)']
            d.component(f'hardware_disc_{side}_M3x6_{i+1}')
            d.revolve([[0,0],[3,0],[1.5,1.5],[1.5,6],[0,6]],operation='new',name='countersunk_screw')
            d.polygon([[1.155*math.cos(j*math.pi/3),1.155*math.sin(j*math.pi/3)] for j in range(6)],
                      1.01,z=-.01,operation='cut',name='hex_socket')
            if not bottom:d.move(axis=[1,0,0],angle='180 deg')
            d.move(translate=[*xy,plane(base,4 if bottom else 7)])
            d.component(f'hardware_disc_{side}_nut_{i+1}')
            d.polygon([[3.17543*math.cos(j*math.pi/3),3.17543*math.sin(j*math.pi/3)] for j in range(6)],
                      2.4,z=4.25,operation='new',name='M3_nut')
            d.holes(1.55,2.4,z=4.25,name='nominal_thread')
            if not bottom:d.move(axis=[1,0,0],angle='180 deg')
            d.move(translate=[*xy,plane(base,4.55 if bottom else 6.45)])
    from gearbox_native.simple_double_bearing import carrier_mounts
    for side in ('bottom','top'):
        for i,(x,y) in enumerate(carrier_mounts(),1):
            ang=math.atan2(y,x)+math.pi/6
            d.component(f'hardware_carrier_{side}_mount_nut_{i}')
            z='carrier_split + 0.1 mm' if side=='bottom' else 'stack_height - carrier_split - 2.5 mm'
            z=plane(z,.8 if side=='bottom' else 9.2)
            points=[[x+3.17543*math.cos(ang+j*math.pi/3),y+3.17543*math.sin(ang+j*math.pi/3)] for j in range(6)]
            d.polygon(points,2.4,z=z,operation='new',name='embedded_mount_nut')
            d.holes(1.55,2.4,z=z,positions=[(x,y)],name='nominal_thread')
    from gearbox_native.stacked_disc_shaft import hardware as shaft_hardware
    shaft_hardware(d,plane)


def append(source,target,evidence):
    with MCPClient(evidence,design=source,allow_path=PROJECT,timeout=600) as client:
        cls=discover().module('native_design').Design
        # The source already owns native_unit, so resume its graph.
        d=cls.__new__(cls);d.client=client;d.commands=[];d.index=1000
        hardware(d)
        from gearbox_native.double_bearing_groups import group_components
        group_components(client)
        health_check(client,evidence/'hardware_health.json')
        require_ok(client.call('save',dict(path=str(target))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path)
    folder=p.parse_args().folder.resolve()
    append(folder/'gearbox_controls.solidcraft',folder/'complete.solidcraft',folder/'hardware')
