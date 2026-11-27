"""Publish the verified three-piece revision and its native-only populate presets."""
import hashlib,json,shutil,zipfile
from pathlib import Path
from gearbox_native.project import PROJECT
from gearbox_native.native_v8 import SCRATCH
from gearbox_native.native_catalogue import publish


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
 Path(path).parent.mkdir(parents=True,exist_ok=True)
 Path(path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')


def main():
 import working_oomp_populate,working_oomp
 folder=PROJECT/'build/native_v8/assembly_06'
 report=read(SCRATCH/'verification/report.json');assert report['status']=='passed'
 assert report['cases']['compact_10']['changes']['casing_bearing']=='6808'
 compact=folder/'compact_probe.solidcraft';source=folder/'gearbox.solidcraft'
 baseline=read(PROJECT/'solidcraft/version_8_baseline.json')
 assert sha(PROJECT/'gearbox_controls.solidcraft') in (baseline['master_sha256'],sha(source)),'Working master changed; review before publishing'
 hardware={n:read(folder/n/'hardware_verification.json') for n in ('baseline','compact_10')}
 assert all(v['status']=='passed' for v in hardware.values())
 long_clamp=read(folder/'long_clamp/report.json');assert long_clamp['status']=='passed'
 for name,native in [('20',source),('10',compact)]:
  views=read(folder/('views_'+name)/'export.json')
  assert views['status']=='native_export_checked' and views['source_sha256']==sha(native)
 # The old working master is byte-identical to sealed V7 and remains in its archive.
 shutil.copyfile(source,PROJECT/'gearbox_controls.solidcraft')
 shutil.copyfile(folder/'profile.json',PROJECT/'solidcraft/native_v8_profile.json')
 working_oomp_populate.main()
 working_oomp.main(part_filter='cycloidal_version_8_',wait_for_completion=True)
 variants={}
 for option in working_oomp_populate.get_options():
  ratio=option['reduction'];part_id=working_oomp_populate.build_oomp_id(option);part=PROJECT/'parts'/part_id
  native=source if ratio==20 else compact;views=folder/f'views_{ratio}'
  publish(part,native,views,option['native_parameters'],sha(source))
  variants[str(ratio)]=dict(part_id=part_id,master_sha256=sha(native),native_parameters=option['native_parameters'])
 # Preserve a portable snapshot of the new shared helper, which is not needed
 # at runtime when editing an already-authored SolidCraft document.
 helper=Path(read(PROJECT/'solidcraft/config.json')['helper_root'])/'components/native_hardware_pattern'
 dest=PROJECT/'solidcraft/shared_components/native_hardware_pattern';dest.mkdir(parents=True,exist_ok=True)
 for name in ('working.py','notes.md','test_working.py'):shutil.copyfile(helper/name,dest/name)
 evidence=PROJECT/'solidcraft/evidence/v8_three_piece.zip';evidence.parent.mkdir(exist_ok=True)
 with zipfile.ZipFile(evidence,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  # Full diagnostics are retained without placing many duplicate large JSON
  # files in the catalogue. Only evidence for the successful candidate is used.
  for root,prefix in [(SCRATCH/'assembly_06','native'),(folder,'exports')]:
   for path in root.rglob('*.json'):
    if any(p.startswith('session') or p=='author' or 'rejected' in p for p in path.parts):continue
    z.write(path,f'{prefix}/{path.relative_to(root).as_posix()}')
  z.write(SCRATCH/'verification/report.json','verification/report.json')
  z.write(SCRATCH/'isolated_verification.json','verification/isolated_verification.json')
  for path in dest.iterdir():z.write(path,'shared_components/native_hardware_pattern/'+path.name)
 summary=dict(status='passed',master_sha256=sha(source),cases={},hardware={},long_clamp=long_clamp,variants=variants,
              evidence_archive=evidence.relative_to(PROJECT).as_posix(),evidence_sha256=sha(evidence),
              acceptance_sha256=sha(PROJECT/'gearbox_native/acceptance.py'),physical_print_load_tested=False)
 for name,row in report['cases'].items():
  item={k:row[k] for k in ('status','changes','dimensions','sampling')}
  item['parts']={n:dict(valid=p['shape']['valid'],watertight=p['mesh']['watertight'],maximum_sample_distance_mm=p['mesh']['maximum_sample_distance_mm']) for n,p in row['parts'].items()}
  if name in hardware:
   item.update(reopens=row['reopens'],maximum_intersection_mm3=max(v['volume'] for v in row['intersections']),maximum_motion_overlap_mm3=max(v['volume'] for v in row['motion']))
  summary['cases'][name]=item
 for name,row in hardware.items():summary['hardware'][name]=dict(status=row['status'],check_count=len(row['checks']),maximum_overlap_mm3=max(c['overlap_mm3'] for c in row['checks']))
 write(PROJECT/'solidcraft/native_v8_three_piece_verification.json',summary)
 index=read(PROJECT/'solidcraft/native_v8.json');index.update(master_sha256=sha(source),revision='three-piece casing and native compact preset',
   verification='solidcraft/native_v8_three_piece_verification.json',variants=variants,component_count=9,acceptance_sha256=summary['acceptance_sha256'])
 write(PROJECT/'solidcraft/native_v8.json',index)
 print('Published both native V8 presets and portable verification evidence',flush=True)


if __name__=='__main__':main()
