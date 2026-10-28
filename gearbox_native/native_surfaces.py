"""Native sketches and analytic surfaces for gearbox pieces with dense outlines.

Source geometry supplies the sketch boundaries, never an imported SolidCraft
body. Planar faces become sketch patches; straight circular walls become surface
extrusions; complete conical walls become surface revolutions. Stitching closes
the authored surfaces without asking the Boolean kernel to displace a cutter.
Unsupported trims fail explicitly. The full saved feature history remains native.
"""
import math
from pathlib import Path
import numpy as np
from OCP.BRep import BRep_Tool
from OCP.BRepTools import BRepTools,BRepTools_WireExplorer
from OCP.BRepAdaptor import BRepAdaptor_Curve,BRepAdaptor_Surface
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.BRepAlgoAPI import BRepAlgoAPI_Splitter
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.GeomAbs import GeomAbs_Line,GeomAbs_Circle,GeomAbs_Plane,GeomAbs_Cylinder,GeomAbs_Cone
from OCP.TopAbs import TopAbs_EDGE,TopAbs_VERTEX,TopAbs_FACE,TopAbs_WIRE,TopAbs_REVERSED
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS
from OCP.TopTools import TopTools_ListOfShape
from OCP.gp import gp_Pnt,gp_Trsf,gp_Pln,gp_Dir
from oobb_solidcraft.backend import require_ok
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.runtime import write_json,digest
from oobb_solidcraft.validation import inspect_shape
from gearbox_native.exact_geometry import build_shape
from gearbox_native.acceptance import health_check,verify_step,verify_mesh,verify_native_measurement,verify_edit


class UnsupportedSurface(ValueError):
    pass


def split_boundary_levels(shape):
    """Split only boundary faces at existing Z stations, adding no material.

    Stepped cylindrical trims then become exact axial rectangles. Splitting all
    incident faces together keeps their shared edge endpoints consistent for
    native stitching. The unsplit solid remains the acceptance reference.
    """
    levels=set();ex=TopExp_Explorer(shape,TopAbs_VERTEX)
    while ex.More():levels.add(round(BRep_Tool.Pnt_s(TopoDS.Vertex_s(ex.Current())).Z(),10));ex.Next()
    levels=sorted(levels)
    if len(levels)<3:return shape
    if len(levels)>64:raise UnsupportedSurface('Too many axial stations for native face splitting')
    arguments=TopTools_ListOfShape();ex=TopExp_Explorer(shape,TopAbs_FACE)
    while ex.More():arguments.Append(ex.Current());ex.Next()
    cutters=TopTools_ListOfShape()
    for level in levels[1:-1]:
        cutters.Append(BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(0,0,level),gp_Dir(0,0,1))).Face())
    splitter=BRepAlgoAPI_Splitter();splitter.SetArguments(arguments);splitter.SetTools(cutters)
    splitter.SetNonDestructive(True);splitter.Build()
    if not splitter.IsDone():raise UnsupportedSurface('Boundary station split failed')
    return splitter.Shape()


def plan_surfaces(shape, *, outline=None, height=None, equation=None):
    commands=[]
    # Give adjacent caps and walls identical arc partitions, even where one
    # station has an intersecting bore and another has a complete circle.
    def circle_frame(circle):
        axis=np.array(circle.Axis().Direction().Coord())
        for v in axis:
            if abs(v)>1e-9:
                if v<0:axis=-axis
                break
        seed=np.array([1.,0.,0.]) if abs(axis[0])<0.9 else np.array([0.,1.,0.])
        x=seed-axis*(seed@axis);x/=np.linalg.norm(x);y=np.cross(axis,x)
        center=np.array(circle.Location().Coord());line=center-axis*(center@axis)
        key=tuple(np.round(np.r_[axis,line,circle.Radius()],8))
        return center,x,y,key
    partitions={};edges=TopExp_Explorer(shape,TopAbs_EDGE)
    while edges.More():
        curve=BRepAdaptor_Curve(TopoDS.Edge_s(edges.Current()));edges.Next()
        if curve.GetType()!=GeomAbs_Circle:continue
        center,x,y,key=circle_frame(curve.Circle())
        angles=partitions.setdefault(key,[0.,2*math.pi/3,4*math.pi/3])
        for t in (curve.FirstParameter(),curve.LastParameter()):
            p=np.array(curve.Value(t).Coord())-center
            a=math.atan2(p@y,p@x)%(2*math.pi)
            if min(a,2*math.pi-a)<1e-9:a=0.
            if not any(abs(a-b)<1e-9 for b in angles):angles.append(a)
    # Remove redundant rim vertices only when every face using that circle
    # contains a complete circular boundary. This gives full cone revolutions
    # and neighbouring sketches the same three native arc spans.
    cone_keys=set();coverage={};faces=TopExp_Explorer(shape,TopAbs_FACE)
    while faces.More():
        face=TopoDS.Face_s(faces.Current());faces.Next()
        is_cone=BRepAdaptor_Surface(face).GetType()==GeomAbs_Cone
        rings={};edges=TopExp_Explorer(face,TopAbs_EDGE)
        while edges.More():
            curve=BRepAdaptor_Curve(TopoDS.Edge_s(edges.Current()));edges.Next()
            if curve.GetType()!=GeomAbs_Circle:continue
            circle=curve.Circle();center,_,_,key=circle_frame(circle)
            station=tuple(np.round(center,8));ring=(key,station)
            rings[ring]=rings.get(ring,0.)+curve.LastParameter()-curve.FirstParameter()
            if is_cone:cone_keys.add(key)
        for (key,_),sweep in rings.items():coverage.setdefault(key,[]).append(sweep)
    for key in cone_keys:
        if all(abs(sweep-2*math.pi)<1e-8 for sweep in coverage[key]):
            partitions[key]=[0.,2*math.pi/3,4*math.pi/3]
    def emit(command_id,**params):
        commands.append(dict(command=command_id,params=params))
    def scalar(value):return f'{float(value)!r} * profile_unit'
    def zscalar(value):
        if equation and 'rotor' in equation:
            from gearbox_native.equation_surfaces import z_expression
            return z_expression(equation,value)
        if equation and abs(abs(value)-height)<1e-8:
            return 'rotor_depth' if value>0 else '-rotor_depth'
        return scalar(value)
    def xy(point):
        value=np.array(point.Coord())
        if equation:
            from gearbox_native.equation_surfaces import projected_point
            expressions=projected_point(equation,value,(dx,dy))
            if expressions is not None:return expressions
        return [scalar(value@axis) for axis in (dx,dy)]
    def draw_curve(curve):
        a,b=curve.FirstParameter(),curve.LastParameter()
        if curve.GetType()==GeomAbs_Circle:
            circle=curve.Circle()
            center,x,y,key=circle_frame(circle)
            def point(angle):return gp_Pnt(*(center+circle.Radius()*(math.cos(angle)*x+math.sin(angle)*y)))
            angles=sorted(partitions[key]);angles.append(angles[0]+2*math.pi)
            original_x=np.array(circle.XAxis().Direction().Coord())
            original_y=np.array(circle.YAxis().Direction().Coord())
            for start,end in zip(angles,angles[1:]):
                delta=np.array(point((start+end)/2).Coord())-center
                t=math.atan2(delta@original_y,delta@original_x)
                if (t-a)%(2*math.pi)>=b-a-1e-10:continue
                emit('sketch.arc.three_point',start=xy(point(start)),end=xy(point(end)),through=xy(point((start+end)/2)),connect=False)
        elif curve.GetType()==GeomAbs_Line:
            emit('sketch.line',points=[xy(curve.Value(a)),xy(curve.Value(b))],infer=False,connect=False)
        else:raise UnsupportedSurface(f'Cannot author curve {curve.GetType()} exactly')
    def draw(wire):
        curves=[];walk=BRepTools_WireExplorer(wire)
        while walk.More():curves.append(BRepAdaptor_Curve(walk.Current()));walk.Next()
        if all(c.GetType()==GeomAbs_Line for c in curves):
            walk=BRepTools_WireExplorer(wire);points=[]
            while walk.More():points.append(xy(BRep_Tool.Pnt_s(walk.CurrentVertex())));walk.Next()
            emit('sketch.line',points=points,closed=True,infer=False,connect=False)
        else:
            for curve in curves:draw_curve(curve)
    def vertices(face):
        result=[];ex=TopExp_Explorer(face,TopAbs_VERTEX)
        while ex.More():result.append(np.array(BRep_Tool.Pnt_s(TopoDS.Vertex_s(ex.Current())).Coord()));ex.Next()
        return result
    emit('parameters.add',name='profile_unit',expression='1 mm',comment='Uniform native dimension scale; recipe dimensions remain in Python/YAML')
    if equation:
        commands.extend(equation['setup']['commands'])
        emit('parameters.add',name='rotor_depth',expression=equation.get('depth_expression',f'{height!r} mm'),comment='Shared cap offsets and wall heights')
    minimum_outline_radius=min(math.hypot(*p) for p in outline) if outline else None
    explorer=TopExp_Explorer(shape,TopAbs_FACE);index=0;outer_count=0
    while explorer.More():
        face=TopoDS.Face_s(explorer.Current());surface=BRepAdaptor_Surface(face);explorer.Next()
        name=f'boundary_{index:03d}'
        if surface.GetType()==GeomAbs_Plane:
            plane=surface.Plane()
            dx=np.array(plane.XAxis().Direction().Coord());dy=np.array(plane.YAxis().Direction().Coord())
            # Reflected source parts can have an indirect gp_Ax3 frame: its
            # stored Z direction differs from X cross Y. SolidCraft's custom
            # plane always uses X cross Y for its offset direction.
            normal=np.cross(dx,dy)
            points=vertices(face)
            if (outline and abs(normal[2])<1e-10
                    and all(np.linalg.norm(p[:2])>=minimum_outline_radius-1e-8 for p in points)
                    and all(min(abs(p[2]),abs(p[2]-height))<1e-8 for p in points)):
                outer_count+=1
                continue
            emit('sketch.create',plane={'x_dir':dx.tolist(),'y_dir':dy.tolist()},offset=zscalar(np.array(plane.Location().Coord())@normal),name=name+'_profile')
            wires=TopExp_Explorer(face,TopAbs_WIRE)
            while wires.More():
                wire=TopoDS.Wire_s(wires.Current());start=len(commands);draw(wire)
                if wire.IsSame(BRepTools.OuterWire_s(face)):
                    for entry in commands[start:]:entry['capture_outer']=True
                wires.Next()
            emit('sketch.solve');emit('sketch.finish')
            # Surface Patch's default selects and merges inner regions too.
            # Binding the outer wire preserves all holes in the selected face.
            emit('surface.patch',sketch=name+'_profile',profiles='OUTER_PROFILE',name=name,body_name=name)
            if face.Orientation()==TopAbs_REVERSED:emit('surface.reverse_normal',body=name)
        elif surface.GetType()==GeomAbs_Cylinder:
            cylinder=surface.Cylinder();axis=np.array(cylinder.Axis().Direction().Coord())
            dx=np.array(cylinder.XAxis().Direction().Coord());dy=np.cross(axis,dx)
            stations=[float(p@axis) for p in vertices(face)];lo,hi=min(stations),max(stations)
            if any(min(abs(z-lo),abs(z-hi))>1e-8 for z in stations):
                raise UnsupportedSurface('A cylindrical face has a stepped or curved trim')
            emit('sketch.create',plane={'x_dir':dx.tolist(),'y_dir':dy.tolist()},offset=zscalar(lo),name=name+'_profile')
            edges=TopExp_Explorer(face,TopAbs_EDGE);length=0.
            while edges.More():
                curve=BRepAdaptor_Curve(TopoDS.Edge_s(edges.Current()));edges.Next()
                if curve.GetType()==GeomAbs_Circle:
                    if abs(np.array(curve.Circle().Location().Coord())@axis-lo)<1e-8:
                        draw_curve(curve);length+=cylinder.Radius()*(curve.LastParameter()-curve.FirstParameter())
                elif curve.GetType()!=GeomAbs_Line:raise UnsupportedSurface('Cylindrical trim is not an axial rectangle')
            area=GProp_GProps();BRepGProp.SurfaceProperties_s(face,area,1e-10)
            if not length or abs(area.Mass()-length*(hi-lo))>1e-7:
                raise UnsupportedSurface('Cylindrical wall is not a complete extrusion of its lower boundary')
            emit('sketch.solve');emit('sketch.finish')
            distance=f'({zscalar(hi)}) - ({zscalar(lo)})' if equation else scalar(hi-lo)
            emit('surface.extrude',sketch=name+'_profile',curves='CURRENT_CURVES',distance=distance,name=name,body_name=name)
            emit('surface.reverse_normal',body=name)
        elif surface.GetType()==GeomAbs_Cone:
            cone=surface.Cone();axis=np.array(cone.Axis().Direction().Coord())
            edges=TopExp_Explorer(face,TopAbs_EDGE);rims=[]
            while edges.More():
                curve=BRepAdaptor_Curve(TopoDS.Edge_s(edges.Current()));edges.Next()
                if curve.GetType()==GeomAbs_Circle:
                    circle=curve.Circle();center=np.array(circle.Location().Coord())
                    # Axial face splitting may partition a complete rim into
                    # several arcs. Retain the full-cone restriction while
                    # recognising those exact, co-circular boundary segments.
                    group=next((rim for rim in rims if
                        np.linalg.norm(center-np.array(rim[0].Location().Coord()))<1e-7
                        and abs(circle.Radius()-rim[0].Radius())<1e-7),None)
                    if group is None:
                        group=[circle,0.];rims.append(group)
                    group[1]+=curve.LastParameter()-curve.FirstParameter()
                elif curve.GetType()!=GeomAbs_Line:raise UnsupportedSurface('Cone has a curved trim')
            if len(rims)!=2 or any(abs(sweep-2*math.pi)>1e-8 for _,sweep in rims):
                raise UnsupportedSurface('Cone must have two complete circular rims')
            circles=[rim[0] for rim in rims]
            area=GProp_GProps();BRepGProp.SurfaceProperties_s(face,area,1e-10)
            slant=math.hypot(circles[0].Location().Distance(circles[1].Location()),
                             circles[0].Radius()-circles[1].Radius())
            expected_area=math.pi*(circles[0].Radius()+circles[1].Radius())*slant
            if abs(area.Mass()-expected_area)>1e-7:
                raise UnsupportedSurface('Conical wall must cover the complete circular frustum')
            circles.sort(key=lambda c:np.array(c.Location().Coord())@axis)
            dx=circle_frame(circles[0])[1];dy=axis
            normal=np.cross(dx,dy);origin=np.array(circles[0].Location().Coord())
            emit('sketch.create',plane={'x_dir':dx.tolist(),'y_dir':dy.tolist()},offset=scalar(origin@normal),name=name+'_profile')
            points=[np.array(c.Location().Coord())+dx*c.Radius() for c in circles]
            emit('sketch.line',points=[[scalar(p@dx),scalar(p@dy)] for p in points],infer=False,connect=False)
            commands[-1]['capture_generatrix']=True
            emit('sketch.line',points=[[scalar(np.array(c.Location().Coord())@dx),scalar(np.array(c.Location().Coord())@dy)] for c in circles],construction=True,infer=False,connect=False)
            commands[-1]['capture_axis']=True
            emit('sketch.solve');emit('sketch.finish')
            emit('surface.revolve',sketch=name+'_profile',curves='GENERATRIX',axis='SKETCH_AXIS',angle='360 deg',name=name,body_name=name)
            emit('surface.reverse_normal',body=name)
        else:raise UnsupportedSurface(f'Unsupported surface: {surface.GetType()}')
        index+=1
    if outline:
        if outer_count!=len(outline):raise UnsupportedSurface('Cycloidal outer-wall count differs from the authored polygon')
        if equation:
            from gearbox_native.equation_surfaces import profile_api
            matrix=equation['matrix']
            wall=profile_api().sketch_plan(equation['geometry'],prefix='rotor',sketch_name='cycloidal_profile',
                plane={'x_dir':matrix[:,0].tolist(),'y_dir':matrix[:,1].tolist()},include_parameters=False)
            commands.extend(wall['commands'])
        else:
            emit('sketch.create',plane='XY',name='cycloidal_profile')
            emit('sketch.line',points=[[scalar(v) for v in p] for p in outline],closed=True,infer=False,connect=False)
            emit('sketch.solve');emit('sketch.finish')
        emit('surface.extrude',sketch='cycloidal_profile',distance='rotor_depth' if equation else scalar(height),name='cycloidal_wall',body_name='cycloidal_wall')
    return commands


def execute_plan(client,commands,*,stitch=True):
    curves=[];outer=[];generatrix=[];axis=[]
    for index,entry in enumerate(commands):
        if index%2000==0:
            print(f'  Native surface commands: {index}/{len(commands)}',flush=True)
        command=entry['command'];params=dict(entry['params'])
        if command=='sketch.create':curves=[];outer=[];generatrix=[];axis=[]
        if params.get('curves')=='CURRENT_CURVES':params['curves']=curves.copy()
        if params.get('curves')=='GENERATRIX':params['curves']=generatrix.copy()
        if params.get('axis')=='SKETCH_AXIS':params['axis']=axis[0]
        if params.get('profiles')=='OUTER_PROFILE':params['profiles']=[{'curves':outer.copy()}]
        reply=require_ok(client.call('execute',dict(command=command,params=params)))
        created=reply.get('created',{}).get('curves',[]);curves.extend(created)
        if entry.get('capture_outer'):outer.extend(created)
        if entry.get('capture_generatrix'):generatrix.extend(created)
        if entry.get('capture_axis'):axis.extend(created)
    if stitch:
        print(f'  Native surface commands: {len(commands)}/{len(commands)}; stitching',flush=True)
        state=require_ok(client.call('inspect_design'))
        names=[b['name'] for b in state['bodies']]
        require_ok(client.call('execute',dict(command='surface.stitch',params={'bodies':names,'tolerance':'0.0000001 mm'})))


def authoring_boundary(shape,part_id):
    """Merge redundant casing face divisions; keep the original acceptance reference."""
    if not part_id.endswith(('__output_casing_lower','__output_casing_upper',
                             '__fit_casing_clamp_lower','__fit_casing_clamp_upper','__fit_casing_OOBB_tab')):
        return shape
    from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
    merger=ShapeUpgrade_UnifySameDomain(shape,True,True,False)
    merger.Build()
    result=merger.Shape();info=inspect_shape(result)
    if not info['valid'] or info['solid_count']!=1:
        raise ValueError('Casing boundary merge must retain one valid solid')
    return result


def render(thing, *, plan,output_dir,export_stl=True,export_extras=True,verify_solidcraft=True):
    if not verify_solidcraft:raise ValueError('Native surfaces always require full verification')
    output=Path(output_dir);shape=build_shape(plan['tree'])
    source=inspect_shape(shape)
    if not source['valid'] or source['solid_count']!=1:raise ValueError('Expected one valid printed solid')
    from gearbox_native.equation_surfaces import context,edited_plan
    equation=context(plan,thing.get('rotor_interfaces'))
    outline=equation['geometry'] if equation else next((f['geometry'] for f in plan['features'] if f['geometry']['kind']=='polygon' and len(f['geometry']['points'])>256),None)
    boundary=authoring_boundary(shape,thing['id'])
    try:
        commands=plan_surfaces(boundary,outline=equation['points'] if equation else outline['points'] if outline else None,
                               height=outline['height'] if outline else None,equation=equation)
    except UnsupportedSurface:
        if outline:raise
        commands=plan_surfaces(split_boundary_levels(boundary))
    write_json(output/'native_surface_commands.json',{'commands':commands})
    checks={}
    with MCPClient(output/'session',allow_path=output,timeout=600) as client:
        version=client.initialized['serverInfo']['version']
        if version!='0.22.0':raise ValueError(f'Unvalidated SolidCraft version {version}')
        execute_plan(client,commands)
        original=health_check(client,output/'native_inspection.json')
        require_ok(client.call('save',{'path':str(output/'generated.solidcraft')}))
        require_ok(client.call('export',{'path':str(output/'generated.step')}))
        checks['native']=verify_native_measurement(require_ok(client.call('measure')),shape)
        require_ok(client.call('export',{'path':str(output/'generated.stl')}))
        if export_extras:require_ok(client.call('screenshot',{'source':'model','view':'iso','path':str(output/'native.png'),'width':1100,'height':760,'grid':False,'axes':False}))
    print('  Native surface history built; checking exported solid',flush=True)
    checks['step']=verify_step(output/'generated.step',shape)
    checks['stl']=verify_mesh(output/'generated.stl',shape)
    print('  Native geometry passed; checking saved parameter edit',flush=True)
    if equation:
        before=equation['geometry']['cycloidal_parameters']['eccentricity']
        after=max(0,before-.01)
        edited_reference,checks['edit_sampling']=edited_plan(plan,after,thing.get('rotor_interfaces'))
        edited=build_shape(edited_reference['tree'])
        edit_name='eccentricity' if thing.get('rotor_interfaces') else equation['setup']['parameters']['eccentricity']
        edit_value=f'{after!r} mm'
        checks['equation_edit']=dict(parameter=edit_name,before_mm=before,after_mm=after)
        write_json(output/'equation_profile.json',equation['geometry'])
        write_json(output/'edited_reference_plan.json',edited_reference)
    else:
        transform=gp_Trsf();transform.SetScale(gp_Pnt(0,0,0),1.001)
        edited=BRepBuilderAPI_Transform(shape,transform,True).Shape()
        edit_name='profile_unit';edit_value='1.001 mm'
    with MCPClient(output/'reopen',design=output/'generated.solidcraft',allow_path=output,timeout=600) as client:
        reopened=health_check(client,output/'reopened_inspection.json')
        if len(reopened['timeline'])!=len(original['timeline']):raise ValueError('Feature history changed on reopen')
        checks['reopened']=verify_native_measurement(require_ok(client.call('measure')),shape)
        require_ok(client.call('set_parameter',{'name':edit_name,'value':edit_value}))
        health_check(client,output/'edited_inspection.json')
        checks['edited_native']=verify_native_measurement(require_ok(client.call('measure')),edited)
        checks['edit_response']=verify_edit(checks['reopened'],checks['edited_native'])
        require_ok(client.call('save',{'path':str(output/'edited.solidcraft')}))
        require_ok(client.call('export',{'path':str(output/'edited.step')}))
        if equation:require_ok(client.call('export',{'path':str(output/'edited.stl')}))
    checks['edited_step']=verify_step(output/'edited.step',edited)
    if equation:checks['edited_stl']=verify_mesh(output/'edited.stl',edited)
    with MCPClient(output/'edited_reopen',design=output/'edited.solidcraft',allow_path=output,timeout=600) as client:
        health_check(client,output/'edited_reopened_inspection.json')
        checks['edited_reopened']=verify_native_measurement(require_ok(client.call('measure')),edited)
    write_json(output/'measurements.json',checks)
    write_json(output/'cad_structure.json',dict(construction='native',method='analytic_sketch_surfaces',
        native_feature_history=True,body_count=1,sketch_count=len(original['sketches']),
        profile_vertices_preserved=True,parameters=equation['setup']['parameters'] if equation else {'profile_unit':'uniform native dimension scale'},
        parameter_source='Shared equation coordinate expressions on all caps and walls; validate fixed stations before native edits' if equation else 'Recipe dimensions regenerate native sketch boundaries; each saved sketch and surface remains editable'))
    formats=['solidcraft']+(['step'] if export_extras else [])+(['stl'] if export_stl else [])
    return dict(construction='native',native_method='analytic_sketch_surfaces',backend_version=version,
        artifacts=[dict(path=str(output/('generated.'+ext)),sha256=digest(output/('generated.'+ext)),format=ext) for ext in formats],
        verification=dict(enabled=True,status='passed',native_feature_edit=f'{edit_name} -> {edit_value}; saved, reopened, exported solid checked'),
        measurements=str(output/'measurements.json'))
