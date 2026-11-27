"""Materialize populate variants solely through exposed native CAD parameters."""
import argparse,hashlib,json,shutil,uuid,zipfile
from pathlib import Path
from gearbox_native.project import PROJECT,VERSION,require_editable
from gearbox_native.native_exports import export

NATIVE_NAME = 'native_v' + VERSION.split('_')[-1]
VERSION_LABEL = 'V' + VERSION.split('_')[-1]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def compact_print(part):
 """Pack the checked print-oriented meshes inside a 240 mm square."""
 import trimesh
 positions={'output_casing_lower':(40,40),'output_casing_lobes':(120,40),'output_casing_upper':(200,40),
  'motor_mount':(40,120),'bearing_baseplate':(40,120),'rotor_a':(112,115),'rotor_b':(180,115),
  'pin_front':(30,200),'eccentric_hub_lower':(78,200),'eccentric_hub_upper':(108,200),
  'motor_spacer':(153,200),'bearing_retainer':(153,200),'drive_sleeve':(202,200)}
 holder=(part/'native_parts/bearing_holder.stl').exists()
 if holder:positions.update(bearing_holder=(153,200),bearing_retainer=(230,200))
 split=(part/'native_parts/eccentric_hub_lower_a.stl').exists()
 if split:
  del positions['eccentric_hub_lower'],positions['eccentric_hub_upper']
  positions.update(eccentric_hub_lower_a=(78,212),eccentric_hub_lower_b=(108,183),
                   eccentric_hub_upper_a=(224,155),eccentric_hub_upper_b=(224,125))
 bodies=[]
 for name,(x,y) in positions.items():
  source=part/'native_parts'/(name+'.stl')
  if not source.exists():continue
  mesh=trimesh.load_mesh(source);assert mesh.is_volume and abs(mesh.bounds[0,2])<.01
  mesh.apply_translation([x,y,0]);bodies.append(mesh)
 assert len(bodies)==(14 if split else 12 if holder else 11)
 for i,a in enumerate(bodies):
  for b in bodies[i+1:]:
   assert any(a.bounds[1,j]<b.bounds[0,j] or b.bounds[1,j]<a.bounds[0,j] for j in (0,1)), 'Print footprints overlap'
 mesh=trimesh.util.concatenate(bodies)
 assert all(mesh.bounds[0,j]>=0 and mesh.bounds[1,j]<=240 for j in (0,1))
 folder=part/'compact_print';folder.mkdir(exist_ok=True);mesh.export(folder/'3dpr.stl')
 (folder/'README.md').write_text(f'Compact placement of the {len(bodies)} checked native STL parts, within 240 x 240 mm. Geometry and print orientations are unchanged. The parent native 3dpr file retains its wider editable layout. Individual parts are in ../native_parts/.\n',encoding='utf8')


def shaft_reprint(part):
 """Lay out the replacement kit from this preset's verified native exports."""
 import trimesh
 kit=part/'shaft_reprint'
 kit.mkdir(exist_ok=True)
 bodies=[]
 positions=[('eccentric_hub_lower',0,0),('eccentric_hub_upper',32,0),('motor_spacer',70,0)]
 if (part/'native_parts/drive_sleeve.stl').exists():
  positions=[('eccentric_hub_lower',0,0),('eccentric_hub_upper',32,0),('drive_sleeve',65,0),
             ('pin_front',115,0),('rotor_a',30,70),('rotor_b',100,70)]
 for name,x,y in positions:
  mesh=trimesh.load_mesh(part/'native_parts'/(name+'.stl'))
  assert mesh.is_volume and abs(mesh.bounds[0,2]) < .01
  mesh.apply_translation([x,y,0])
  bodies.append(mesh)

 plate=kit/'3dpr.stl'
 trimesh.util.concatenate(bodies).export(plate)
 shells=trimesh.load_mesh(plate).split(only_watertight=False)
 assert len(shells)==len(positions) and all(shell.is_volume for shell in shells)


def publish(part,source,views,overrides,source_sha):
 require_editable(part);part.mkdir(parents=True,exist_ok=True)
 export_record=json.loads((views/'export.json').read_text(encoding='utf-8'))
 assert export_record['status']=='native_export_checked'
 assert export_record['source_sha256']==sha(source),'Exports do not belong to this native source'
 values={p['name']:p['value'] for p in export_record['parameters']['parameters']}
 if 'output_nut_plate' in export_record['parts'] and 'connected_contact_ring' not in export_record['parts']:
  raise ValueError('Use the current master to populate the spacer-ring style. Export the earlier 35:1 master directly for standalone views.')
 if 'carrier_top_nut_tray' in export_record['parts']:
  from gearbox_native.version_11_outputs import publish as publish_v11
  return publish_v11(part,source,views,source_sha)
 if 'motor_inner_adapter' in export_record['parts']:
  from gearbox_native.nema17_outputs import publish as publish_motor
  return publish_motor(part,source,views,overrides,source_sha)
 if 'connected_contact_ring' in export_record['parts']:
  from gearbox_native.simple_double_bearing import profile
  from gearbox_native.verify_double_bearing import fits
  style_fits=fits(views/'parts',values,profile())
 shutil.copyfile(source,part/'gearbox_controls.solidcraft')
 for mode,target in [('assembled','true'),('exploded','exploded'),('3dpr','3dpr')]:
  for ext in ('solidcraft','step','stl','png'):shutil.copyfile(views/(mode+'.'+ext),part/(target+'.'+ext))
  for ext in ('stl','png'):shutil.copyfile(views/(mode+'.'+ext),part/(target+'_solidcraft.'+ext))
  style='simple_double_bearing_version_2' if 'output_nut_plate' in export_record['parts'] else VERSION
  record=dict(status='success',construction='native',native_only=True,version=style,external_piece_links=False,
   canonical_master=str(part/'gearbox_controls.solidcraft'),snapshot=True,geometry='manufacturing clearances',
   native_parameter_overrides=overrides,source_master_sha256=source_sha,source_sha256=sha(source),export_evidence='native_export_verification.json')
  (part/(target+'_solidcraft_manifest.json')).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
 (part/'native_parts').mkdir(exist_ok=True)
 for path in (views/'parts').iterdir():shutil.copyfile(path,part/'native_parts'/path.name)
 # Portable concise evidence; detailed face diagnostics stay in the build evidence.
 summary=dict(status=export_record['status'],source_sha256=export_record['source_sha256'],
   sampling=export_record['sampling'],parameters=values,part_names=list(export_record['parts']),
   print_mesh=export_record['print_mesh'],note=export_record['note'])
 (part/'native_export_verification.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
 if 'output_nut_plate' in export_record['parts']:
  from gearbox_native.double_bearing_outputs import publish_details
  publish_details(part,views,values,overrides,source_sha,style_fits)
  if 'shaft_end_lower' in export_record['parts']:
   from gearbox_native.simple_double_bearing import RETIRED_SHAFT
   for name in RETIRED_SHAFT:
    for ext in ('stl','step'):(part/'native_parts'/(name+'.'+ext)).unlink(missing_ok=True)
  return
 shutil.copyfile(PROJECT/f'NATIVE_{VERSION_LABEL}.md',part/'EDITING_PARAMETERS.md')
 bearing_guide=PROJECT/'parts/oobb_part_motor_gearbox_cycloidal_version_7_20_to_1_reduction/CASING_BEARINGS.md'
 bearing_text=bearing_guide.read_text(encoding='utf-8').replace('version_7',VERSION).replace('V7',VERSION_LABEL)
 bearing_text=bearing_text.replace('project-root `gearbox_controls.solidcraft`','`gearbox_controls.solidcraft` for your chosen variant')
 bearing_text=bearing_text.replace('from `6810`',f"from `{int(values['casing_bearing'])}`")
 bearing_text=bearing_text.replace('EDITING_PARAMETERS.md#automatic-oobb-tab-positions','EDITING_PARAMETERS.md#three-piece-casing-and-printing')
 if 'output_footprint_guard' in values:
  start=bearing_text.index('The selection drives')
  end=bearing_text.index('**`casing_fit_checks=0`**')
  bearing_text=bearing_text[:start]+('V9 is designed around **6808** casing bearings. Keep this selection for the checked 5Ã—5 design. '
   'Bearing seats, journals and axial dimensions remain linked, but the output outline and mounting positions stay fixed at 74Ã—74 mm. '
   'The catalogue below is retained for reference; other bearing combinations are unverified and may exceed the native footprint guards. '
   'See [the editing guide](EDITING_PARAMETERS.md#output-mounting-and-printing).\n\n')+bearing_text[end:]
 (part/'CASING_BEARINGS.md').write_text(bearing_text,encoding='utf-8',newline='\n')
 master_name='gearbox_bearing_controls.solidcraft' if part.name.endswith('_bearing_input') else 'gearbox_controls.solidcraft'
 (part/'native_configuration.json').write_text(json.dumps(dict(version=VERSION,source_master=master_name,
    source_master_sha256=source_sha,parameters=overrides,geometry_implementation='shared native feature graph',
    editable_master=str(part/'gearbox_controls.solidcraft')),indent=2)+'\n',encoding='utf-8',newline='\n')
 ratio=int(values['reduction'])
 (part/'README.md').write_text(f'''# Native {VERSION_LABEL} â€” {ratio}:1

Edit [gearbox_controls.solidcraft](gearbox_controls.solidcraft) in SolidCraft's
Parameters menu. [Editing instructions](EDITING_PARAMETERS.md) explain the
controls and print orientations. Presets of the same input arrangement share
their feature graph and differ through exposed parameter overrides only.

| Dimension | Value |
|---|---:|
| Contact radius | {values['contact_radius']:g} mm |
| Eccentricity | {values['eccentricity']:g} mm |
| Casing bearing | {values['casing_bearing']:g} |
| Minimum circular casing envelope | {2*values['casing_radius']:g} mm |
| OOBB grid | {values['tab_plate_size']:g} Ã— {values['tab_plate_size']:g} |
| Tab footprint | {2*(values['tab_radius']+7):g} Ã— {2*(values['tab_radius']+7):g} mm |
| Guide screws | {int(values['guide_count'])} Ã— M{2*values['guide_radius']:g} Ã— {values['guide_screw_length']:g} mm |
| Casing joining screws | 4 Ã— M3 socket cap Ã— {values['join_screw_length']:g} mm |

[Assembled](true.solidcraft) Â· [Exploded](exploded.solidcraft) Â·
[Print layout](3dpr.solidcraft) Â· [Print STL](3dpr.stl)

![Exploded printed components](exploded.png)

Individual print-oriented STEP/STL files are in `native_parts/`. The three
casing pieces print separately on their flat split/end faces. These view files
are independent snapshots. Native geometry and hardware clearance have been
checked; physical printing and load testing are still needed.
''',encoding='utf-8',newline='\n')
 if 'motor_spacer' in export_record['parts']:
  shaft_reprint(part)
  old_snapshot=part/'shaft_reprint/3dpr.solidcraft'
  if 'drive_sleeve' in export_record['parts'] and old_snapshot.exists():old_snapshot.unlink()
  with (part/'README.md').open('a',encoding='utf-8') as stream:
   stream.write('\n[Motor retrofit print plate](shaft_reprint/3dpr.stl) Â· [Hardware](HARDWARE.md)\n')
 if 'drive_sleeve' in export_record['parts']:
  compact_print(part)
  with (part/'README.md').open('a',encoding='utf-8') as stream:
   kind='Bearing-supported external input' if {'bearing_baseplate','bearing_holder'} & set(export_record['parts']) else 'NEMA17 input with external D-shaft sleeve'
   stream.write('\n'+kind+'. Both input arrangements use a 6702 front shaft bearing.\n')
   stream.write('\n[Compact 3dpr STL for a 240 mm bed](compact_print/3dpr.stl). The native print snapshot retains its wider layout.\n')
 if 'eccentric_hub_lower_a' in export_record['parts']:
  from gearbox_native.split_stack_outputs import make_outputs
  make_outputs(part,values)
 nav=PROJECT/'navigation_oobb/oobb/part/motor_gearbox/cycloidal'/VERSION/f'{ratio}_to_1_reduction'
 if part.name.endswith('_bearing_input'):nav=nav/'bearing_input'
 require_editable(nav);nav.mkdir(parents=True,exist_ok=True)
 (nav/'active_part.json').write_text(json.dumps(dict(version=VERSION,part_id=part.name,path=part.relative_to(PROJECT).as_posix()),indent=2)+'\n',encoding='utf-8')
 import os
 link=os.path.relpath(part/'README.md',nav).replace('\\','/')
 (nav/'README.md').write_text(f'# Native {VERSION_LABEL} â€” {ratio}:1\n\n[Parts and editing instructions]({link})\n',encoding='utf-8')


def main(output=None,evidence=None,style=None):
 import working_oomp_populate,working_oomp
 options=working_oomp_populate.get_options()
 if style:
  options=[o for o in options if o['style']==style]
  if not options:raise ValueError(f'Unknown catalogue style: {style}')
 for option in options:
  source=PROJECT/option.get('native_master','gearbox_controls.solidcraft')
  with zipfile.ZipFile(source) as z:document=json.loads(z.read('document.json'))
  favorites=set(document['favorites'])
  assert any(c.get('name') in ('output_casing_lobes','output_nut_plate') for c in document['components']),'Publish the native master first'
  unknown=set(option.get('native_parameters',{}))-favorites
  if unknown:raise ValueError(f'Variant changes non-exposed parameters: {unknown}')
 working_oomp_populate.main(style=style)
 for option in options:
  working_oomp.main(part_filter=working_oomp_populate.build_oomp_id(option),wait_for_completion=True)
 catalogue_label = options[0]['style'] if len({o['style'] for o in options})==1 else NATIVE_NAME
 folder=Path(output or PROJECT/f'outputs/{catalogue_label}/catalogue_{uuid.uuid4().hex[:8]}').resolve();folder.mkdir(parents=True,exist_ok=False)
 evidence=Path(evidence).resolve() if evidence else folder
 for option in options:
  part_id=working_oomp_populate.build_oomp_id(option);part=PROJECT/'parts'/part_id;require_editable(part)
  source=PROJECT/option.get('native_master','gearbox_controls.solidcraft');digest=sha(source)
  case=folder/part_id;case.mkdir();changes=option.get('native_parameters',{})
  native=case/'gearbox_controls.solidcraft'
  with zipfile.ZipFile(source) as archive:
   original={p['name']: p['expr'] for p in json.loads(archive.read('document.json'))['params']}
  if any(original.get(k)!=value for k,value in changes.items()):
   # Only source graphs are rewritten. Native evaluation and all export checks follow.
   with zipfile.ZipFile(source) as archive, zipfile.ZipFile(native,'w') as target:
    if set(archive.namelist()) != {'container.json','document.json'}:
     raise ValueError('Expected a source graph without cached evaluated solids')
    for entry in archive.infolist():
     data=archive.read(entry)
     if entry.filename=='document.json':
      document=json.loads(data)
      for param in document['params']:
       if param['name'] in changes:param['expr']=changes[param['name']]
      data=json.dumps(document).encode()
     target.writestr(entry,data)
  else:shutil.copyfile(source,native)
  views=case/'exports';export(native,views,None,evidence/part_id/'export')
  assert sha(source)==digest,'The working master changed; retain generated outputs without publishing over concurrent edits'
  publish(part,native,views,changes,digest)
 from gearbox_native.book.readmes import write_index
 write_index()
 print('Published populate variants:',[o['reduction'] for o in options],flush=True)


if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path);p.add_argument('--evidence-dir',type=Path);a=p.parse_args();main(a.output,a.evidence_dir)
