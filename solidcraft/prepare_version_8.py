"""Prepare V8 from the sealed native release; no CAD geometry is regenerated."""
import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8',newline='\n')
def edit(p,pairs):
 s=p.read_text(encoding='utf-8')
 for a,b in pairs:
  assert a in s,(str(p),a)
  s=s.replace(a,b)
 p.write_text(s,encoding='utf-8',newline='\n')
r=read(root/'releases/version_7/release.json');oldid=r['primary_part_id'];newid=oldid.replace('version_7','version_8')
old=root/'parts'/oldid;new=root/'parts'/newid
assert r['status']=='sealed' and not new.exists()
assert sha(root/'gearbox_controls.solidcraft')==r['master_sha256']
new.mkdir();inherited={}
names=['gearbox_controls.solidcraft']+[m+'.'+e for m in ('true','exploded','3dpr') for e in ('solidcraft','step','stl','png')]
names += [p.relative_to(old).as_posix() for p in (old/'native_parts').iterdir() if p.is_file()]
for name in names:
 p=new/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/name,p);inherited[name]=sha(p)
for m in ('true','exploded','3dpr'):
 d=read(old/(m+'_solidcraft_manifest.json'));d.update(version='version_8',part_id=newid,inherited_from='releases/version_7/release.json',verification_evidence='releases/version_7/evidence_index.json',export_evidence='releases/version_7/version_7.zip!build/native_v7/odd_oobb_tabs_views_01/export.json');write(new/(m+'_solidcraft_manifest.json'),d)
for name in ('EDITING_PARAMETERS.md','CASING_BEARINGS.md','working.yaml'):
 s=(old/name).read_text(encoding='utf-8').replace('version_7','version_8').replace('V7','V8').replace('native_v7','native_v8')
 (new/name).write_text(s,encoding='utf-8',newline='\n')
source=root/'parts_source'/newid;source.mkdir()
for p in (root/'parts_source'/oldid).iterdir():
 if p.is_file() and p.name!='SEALED.json':
  (source/p.name).write_text(p.read_text(encoding='utf-8').replace('version_7','version_8'),encoding='utf-8',newline='\n')
write(root/'solidcraft/version_8_baseline.json',dict(version='version_8',part_id=newid,parent_part_id=oldid,parent_release='releases/version_7/release.json',mechanical_changes=False,master_sha256=r['master_sha256'],inherited_files_sha256=inherited,acceptance_sha256=r['acceptance_sha256']))
shutil.copyfile(root/'solidcraft/native_v7_profile.json',root/'solidcraft/native_v8_profile.json')
write(root/'solidcraft/native_v8.json',dict(version='version_8',state='native-only',master='gearbox_controls.solidcraft',initial_sha256=r['master_sha256'],part_id=newid,profile='solidcraft/native_v8_profile.json',baseline='solidcraft/version_8_baseline.json',parent_release='releases/version_7/release.json',inherited_verification='releases/version_7/evidence_index.json'))
write(root/'solidcraft/active_design.json',dict(version='version_8',part_id=newid,state='native-only',baseline='solidcraft/version_8_baseline.json',master='gearbox_controls.solidcraft',verification='solidcraft/native_v8.json'))
edit(root/'gearbox_native/project.py', [('VERSION = "version_7"','VERSION = "version_8"'),('The marker is installed only after the one-document V7 is verified.','The active native marker protects the master.'),("PROJECT / 'solidcraft/native_v7.json'","PROJECT / f'solidcraft/native_v{VERSION.split(\"_\")[-1]}.json'"),("raise ValueError('V7 is native-only.","raise ValueError(f'{VERSION} is native-only.")])
edit(root/'working_oomp_populate.py',[('native V7','native V8'),('Versions 1–6 are sealed in releases/. Version 7','Versions 1–7 are sealed in releases/. Version 8'),('option["style"] = "version_7"','option["style"] = "version_8"'),('"version_5", "version_6")','"version_5", "version_6", "version_7")'),('use version_7 for new designs','use version_8 for new designs'),('option.get(value_name, "version_7")','option.get(value_name, "version_8")')])
edit(root/'working_solidcraft.py',[('use version_7','use version_8'),('if kwargs.get("style", "version_7") != "version_7":','# V7 remains readable for reference tests; main blocks legacy writes.\n    if kwargs.get("style", "version_8") not in ("version_7", "version_8"):'),('Only editable version_7 is supported; earlier versions are sealed','Only V7 reference and V8 recipes are supported; earlier versions are sealed')])
edit(root/'working_scad.py',[('use version_7','use version_8')])
d=read(root/'gearbox_native/control_values.json');d['version']='version_8';write(root/'gearbox_native/control_values.json',d)
edit(root/'action_export_native.py',[('Export the saved native V7','Export the saved active native design')])
edit(root/'gearbox_native/native_exports.py',[('Export a saved native V7 design.','Export a saved native design.'),('from gearbox_native.project import PROJECT','from gearbox_native.project import PROJECT, VERSION'),("PROJECT/'solidcraft/native_v7_profile.json'","PROJECT/f'solidcraft/native_v{VERSION.split(\"_\")[-1]}_profile.json'"),("PROJECT/'outputs/native_v7'","PROJECT/f'outputs/native_v{VERSION.split(\"_\")[-1]}'")])
edit(root/'solidcraft/verify_preservation.py',[('V1–V6','V1–V7'),('for number in (1, 2, 3, 4, 5, 6):','for number in (1, 2, 3, 4, 5, 6, 7):')])
edit(root/'tests/test_native_version_7.py',[('from gearbox_native.project import PROJECT,VERSION,active_part','from gearbox_native.project import PROJECT\n\ndef active_part():\n    return PROJECT/"parts/oobb_part_motor_gearbox_cycloidal_version_7_20_to_1_reduction"'),("assert VERSION=='version_7' and len(baseline['inherited_documents'])==16","assert len(baseline['inherited_documents'])==16"),("assert not (active_part()/'SEALED.json').exists()","assert (active_part()/'SEALED.json').exists()")])
for name in ('README.md','NATIVE_V7.md'):
 s=(root/name).read_text(encoding='utf-8').replace('version_7','version_8').replace('V7','V8').replace('native_v7','native_v8').replace('V1–V6','V1–V7').replace('V6 sealed release','V7 sealed release').replace('releases/version_6/README.md','releases/version_7/README.md').replace('VERSION_7_DEVELOPMENT.md','VERSION_8_DEVELOPMENT.md')
 if name=='README.md':s=s.replace('The starting design remains','V7 is sealed. V8 starts with identical geometry and parameters.\n\nThe starting design remains')
 else:s=s.replace('Old `solidcraft/true`, `solidcraft/3dpr` and fit coupons are retained\nas labelled V6 inheritance evidence, not live dependencies of this master.','Historical native parts and fit coupons remain in sealed V7; they are not live\ndependencies of this master.').replace('Verification records are indexed by','V8 inherits V7 verification records, indexed by')
 (root/('NATIVE_V8.md' if name=='NATIVE_V7.md' else name)).write_text(s,encoding='utf-8',newline='\n')
(root/'VERSION_8_DEVELOPMENT.md').write_text('# Version 8 — editable native baseline\n\nV7 is sealed. V8 starts with identical native model, parameters, views and eight manufacturing exports. No geometry or acceptance-policy changes were made.\n\nEdit the root gearbox_controls.solidcraft using SolidCraft Parameters. The 40 casing-bearing choices and automatic odd OOBB footprint formulas are retained. The default is 20:1, 6810 casing bearings, 3 mm contact radius, 1.4 mm eccentricity, 5 mm discs, 0.5 mm gap and a 7 × 7 mounting footprint.\n\nSee [parameter instructions](NATIVE_V8.md), [baseline hashes](solidcraft/version_8_baseline.json), and [sealed V7](releases/version_7/README.md). Its verification evidence is preserved in the archive. No new physical fit or print/load certification is claimed. Exports now go to outputs/native_v8.\n',encoding='utf-8',newline='\n')
(new/'README.md').write_text('# Native V8 snapshots\n\nEdit [the root master](../../gearbox_controls.solidcraft) in SolidCraft. See [editing instructions](EDITING_PARAMETERS.md) and [V8 notes](../../VERSION_8_DEVELOPMENT.md).\n\nThe local master and assembled/exploded/print views are independent initial snapshots. Individual STEP/STL files are in native_parts/. Historical source parts and fit coupons remain in sealed V7.\n',encoding='utf-8',newline='\n')
nav=root/'navigation_oobb/oobb/part/motor_gearbox/cycloidal/version_8/20_to_1_reduction';nav.mkdir(parents=True)
write(nav/'active_part.json',dict(version='version_8',part_id=newid,path='parts/'+newid))
(nav/'README.md').write_text('# Version 8\n\n[Parts and editing instructions](../../../../../../../parts/'+newid+'/README.md)\n',encoding='utf-8',newline='\n')
assert all(sha(new/n)==h for n,h in inherited.items())
print('Prepared V8:',len(inherited),'byte-identical files')
