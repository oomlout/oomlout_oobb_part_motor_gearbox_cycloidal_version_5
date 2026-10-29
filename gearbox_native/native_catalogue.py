"""Materialize populate variants solely through exposed native CAD parameters."""
import argparse,hashlib,json,shutil,uuid,zipfile
from pathlib import Path
from oobb_solidcraft.mcp import MCPClient
from oobb_solidcraft.backend import require_ok
from gearbox_native.project import PROJECT,VERSION,require_editable
from gearbox_native.native_exports import export


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def publish(part,source,views,overrides,source_sha):
 require_editable(part);part.mkdir(parents=True,exist_ok=True)
 export_record=json.loads((views/'export.json').read_text(encoding='utf-8'))
 assert export_record['status']=='native_export_checked'
 assert export_record['source_sha256']==sha(source),'Exports do not belong to this native source'
 shutil.copyfile(source,part/'gearbox_controls.solidcraft')
 for mode,target in [('assembled','true'),('exploded','exploded'),('3dpr','3dpr')]:
  for ext in ('solidcraft','step','stl','png'):shutil.copyfile(views/(mode+'.'+ext),part/(target+'.'+ext))
  for ext in ('stl','png'):shutil.copyfile(views/(mode+'.'+ext),part/(target+'_solidcraft.'+ext))
  record=dict(status='success',construction='native',native_only=True,version=VERSION,external_piece_links=False,
   canonical_master=str(part/'gearbox_controls.solidcraft'),snapshot=True,geometry='manufacturing clearances',
   native_parameter_overrides=overrides,source_master_sha256=source_sha,source_sha256=sha(source),export_evidence='native_export_verification.json')
  (part/(target+'_solidcraft_manifest.json')).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
 (part/'native_parts').mkdir(exist_ok=True)
 for path in (views/'parts').iterdir():shutil.copyfile(path,part/'native_parts'/path.name)
 # Portable concise evidence; detailed face diagnostics stay in the build evidence.
 values={p['name']:p['value'] for p in export_record['parameters']['parameters']}
 summary=dict(status=export_record['status'],source_sha256=export_record['source_sha256'],
   sampling=export_record['sampling'],parameters=values,part_names=list(export_record['parts']),
   print_mesh=export_record['print_mesh'],note=export_record['note'])
 (part/'native_export_verification.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
 shutil.copyfile(PROJECT/'NATIVE_V8.md',part/'EDITING_PARAMETERS.md')
 bearing_guide=PROJECT/'parts/oobb_part_motor_gearbox_cycloidal_version_7_20_to_1_reduction/CASING_BEARINGS.md'
 bearing_text=bearing_guide.read_text(encoding='utf-8').replace('version_7','version_8').replace('V7','V8')
 bearing_text=bearing_text.replace('project-root `gearbox_controls.solidcraft`','`gearbox_controls.solidcraft` for your chosen variant')
 bearing_text=bearing_text.replace('from `6810`',f"from `{int(values['casing_bearing'])}`")
 bearing_text=bearing_text.replace('EDITING_PARAMETERS.md#automatic-oobb-tab-positions','EDITING_PARAMETERS.md#three-piece-casing-and-printing')
 (part/'CASING_BEARINGS.md').write_text(bearing_text,encoding='utf-8',newline='\n')
 (part/'native_configuration.json').write_text(json.dumps(dict(version=VERSION,source_master='gearbox_controls.solidcraft',
    source_master_sha256=source_sha,parameters=overrides,geometry_implementation='shared native feature graph',
    editable_master=str(part/'gearbox_controls.solidcraft')),indent=2)+'\n',encoding='utf-8',newline='\n')
 ratio=int(values['reduction'])
 (part/'README.md').write_text(f'''# Native V8 — {ratio}:1

Edit [gearbox_controls.solidcraft](gearbox_controls.solidcraft) in SolidCraft's
Parameters menu. [Editing instructions](EDITING_PARAMETERS.md) explain the
controls and print orientations. This preset uses the same feature graph as
the other V8 presets, with exposed parameter overrides only.

| Dimension | Value |
|---|---:|
| Contact radius | {values['contact_radius']:g} mm |
| Eccentricity | {values['eccentricity']:g} mm |
| Casing bearing | {values['casing_bearing']:g} |
| Casing core diameter | {2*values['casing_radius']:g} mm |
| OOBB grid | {values['tab_plate_size']:g} × {values['tab_plate_size']:g} |
| Tab footprint | {2*(values['tab_radius']+7):g} × {2*(values['tab_radius']+7):g} mm |
| Guide screws | {int(values['guide_count'])} × M{2*values['guide_radius']:g} × {values['guide_screw_length']:g} mm |
| Casing joining screws | 4 × M3 socket cap × {values['join_screw_length']:g} mm |

[Assembled](true.solidcraft) · [Exploded](exploded.solidcraft) ·
[Print layout](3dpr.solidcraft) · [Print STL](3dpr.stl)

![Exploded printed components](exploded.png)

Individual print-oriented STEP/STL files are in `native_parts/`. The three
casing pieces print separately on their flat split/end faces. These view files
are independent snapshots. Native geometry and hardware clearance have been
checked; physical printing and load testing are still needed.
''',encoding='utf-8',newline='\n')
 nav=PROJECT/'navigation_oobb/oobb/part/motor_gearbox/cycloidal'/VERSION/f'{ratio}_to_1_reduction'
 require_editable(nav);nav.mkdir(parents=True,exist_ok=True)
 (nav/'active_part.json').write_text(json.dumps(dict(version=VERSION,part_id=part.name,path=part.relative_to(PROJECT).as_posix()),indent=2)+'\n',encoding='utf-8')
 (nav/'README.md').write_text(f'# Native V8 — {ratio}:1\n\n[Parts and editing instructions](../../../../../../../parts/{part.name}/README.md)\n',encoding='utf-8')


def main(output=None,evidence=None):
 import working_oomp_populate,working_oomp
 source=PROJECT/'gearbox_controls.solidcraft';digest=sha(source)
 with zipfile.ZipFile(source) as z:document=json.loads(z.read('document.json'))
 favorites=set(document['favorites'])
 assert any(c.get('name')=='output_casing_lobes' for c in document['components']),'V8 three-piece master must be published first'
 options=working_oomp_populate.get_options()
 for option in options:
  unknown=set(option.get('native_parameters',{}))-favorites
  if unknown:raise ValueError(f'Variant changes non-exposed parameters: {unknown}')
 working_oomp_populate.main()
 working_oomp.main(part_filter=f'cycloidal_{VERSION}_',wait_for_completion=True)
 folder=Path(output or PROJECT/f'outputs/native_v8/catalogue_{uuid.uuid4().hex[:8]}').resolve();folder.mkdir(parents=True,exist_ok=False)
 evidence=Path(evidence).resolve() if evidence else folder
 for option in options:
  part_id=working_oomp_populate.build_oomp_id(option);part=PROJECT/'parts'/part_id;require_editable(part)
  case=folder/part_id;case.mkdir();changes=option.get('native_parameters',{})
  native=case/'gearbox_controls.solidcraft'
  if changes:
   with MCPClient(evidence/part_id/'configure',design=source,allow_path=PROJECT,timeout=600) as client:
    require_ok(client.execute('parameters.change',changes=changes))
    require_ok(client.call('save',dict(path=str(native))))
  else:shutil.copyfile(source,native)
  views=case/'exports';export(native,views,PROJECT/'solidcraft/native_v8_profile.json',evidence/part_id/'export')
  assert sha(source)==digest,'The working master changed; retain generated outputs without publishing over concurrent edits'
  publish(part,native,views,changes,digest)
 print('Published populate variants:',[o['reduction'] for o in options],flush=True)


if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path);p.add_argument('--evidence-dir',type=Path);a=p.parse_args();main(a.output,a.evidence_dir)
