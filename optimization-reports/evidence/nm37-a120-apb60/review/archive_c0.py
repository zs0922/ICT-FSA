#!/usr/bin/env python3
"""Archive selected reproducibility evidence with source and stored-byte hashes."""
import argparse,datetime,gzip,hashlib,json
from pathlib import Path

def sha(data):return hashlib.sha256(data).hexdigest()
p=argparse.ArgumentParser()
p.add_argument('--build',type=Path,required=True)
p.add_argument('--source',type=Path,required=True)
p.add_argument('--review',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--diagnostics',type=Path,required=True)
p.add_argument('--reaudit',type=Path)
a=p.parse_args()
assert not a.output.exists(),'Archive must be new'
assert (a.build/'physical.passed.json').exists() or (a.build/'physical.failed.json').exists(),'Physical decision required'
files={}
def add(path,name):
 if path.is_file():
  assert name not in files,name
  files[name]=path
if a.reaudit:
 assert (a.reaudit/'acceptance/initial/reaudit.passed.json').is_file(), 'Revised acceptance required'
 for path in a.reaudit.rglob('*'):
  if '__pycache__' not in path.parts:add(path,'reaudit/'+str(path.relative_to(a.reaudit)))
for path in a.build.glob('*.json'):add(path,'build/'+path.name)
for dirname in ('logs','formal','hbm-startup/rtl','shell'):
 for path in (a.build/dirname).rglob('*'):
  if path.is_file():add(path,'build/'+str(path.relative_to(a.build)))
for name in ('results.json','simulation.log','emission.log','verilator-build.log'):
 add(a.build/'hbm-startup'/name,'build/hbm-startup/'+name)
for size in (4,8,16):
 sim=a.build/f'sim{size}'
 add(sim/'build.log','build/'+str((sim/'build.log').relative_to(a.build)))
 for seq in (size,size*2):
  for path in (sim/f'seq{seq}').iterdir():add(path,'build/'+str(path.relative_to(a.build)))
 for path in (sim/'generated-src').glob('*/*.FSAConfig.json'):add(path,'build/'+str(path.relative_to(a.build)))
board=a.build/'A120/fpga/chipyard.fpga.nm37.NM37FPGATestHarness.EmptyNM37Config'
for dirname in ('report','audit','hbm_audit','reset_replication_audit'):
 for path in (board/'obj'/dirname).rglob('*'):add(path,'build/'+str(path.relative_to(a.build)))
for pattern in ('*.vivado.tcl','*.sdc','*.xdc','*.FSAConfig.json','obj/ip/*/*.xci'):
 for path in board.glob(pattern):add(path,'build/'+str(path.relative_to(a.build)))
for name in ('implementation.log','elaboration.log'):
 add(a.build/'A120'/name,'build/A120/'+name)
for path in (a.source/'scripts/nm37-a120').iterdir():add(path,'current-source-drivers/'+path.name)
for name in ('source-lock.json','FSAConfig.json','fpga-shells.patch','a110-apb55-cdc.txt.gz'):
 add(a.source/'fpga/baselines/nm37-a120'/name,'baseline/'+name)
for name in ('compare_c0.py','comparison_helpers.py','c0-build02-comparison.json','compare_physical.py','physical_summary_helpers.py','c0-build02-physical.json','analyze_c0_paths.py','path_analysis_helpers.py','c0-build02-paths.json','c0-routed-preacceptance.json','inspect_routed.tcl','archive_c0.py','original-workspace-preservation.json'):
 add(a.review/name,'review/'+name)
for name in ('c0-build02-comparison.json','c0-build02-physical.json','c0-build02-paths.json'):
 assert (a.review/name).is_file(),name
assert (a.diagnostics/'complete.txt').is_file()
for path in a.diagnostics.iterdir():add(path,'diagnostics/'+path.name)
experiment=a.build.parent
for name in ('src-restore.json','driver-tests-fixed.log','hbm-audit-tests-fixed.log','clock-guard-fixed.log','hbm-rounding-tests.log','reaudit-rounding-tests.log','reaudit01-driver.log','reaudit01.exit','environment-build02.sh','run-build02.sh','run-reaudit01.sh','start-reaudit01.sh','c0-build02-original-physical.log','implementation-attempt02-failure.json','c0-build02-audit-failure.json','diagnostics-c0-build02-input.sha256','diagnostics-c0-build02.exit','c0-build02.exit','c0-build02-driver.log','diagnostics-c0-build02.log','diagnostics-c0-build02-vivado.log'):
 add(experiment/name,'execution/'+name)
add(experiment/'interrupted-physical-attempt01/interruption.json','history/interruption.json')
a.output.mkdir(parents=True)
manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'build':str(a.build.resolve()),'script_sha256':sha(Path(__file__).read_bytes()),'note':'Raw reports and selected verification inputs/outputs; generator, simulators and DCP are bound by seals/hashes but not embedded. Source commit plus dependency locks define source inputs. current-source-drivers are the corrected rerun entry; exact original executed drivers are under reaudit/implementation-drivers and the revised auditor is under reaudit/auditor.','files':[]}
manifest['hardware_execution_commit']=json.loads((a.build/'build.json').read_text())['root_commit']
if a.reaudit:
 manifest['reaudit_inputs_sha256']=sha((a.reaudit/'inputs.json').read_bytes())
 manifest['revised_acceptance_sha256']=sha((a.reaudit/'acceptance/initial/reaudit.passed.json').read_bytes())
for name,path in sorted(files.items()):
 raw=path.read_bytes()
 compress=path.suffix in ('.log','.txt','.rpt','.sv','.v','.dict','.tsv') or len(raw)>150000
 data=gzip.compress(raw,mtime=0) if compress else raw
 rel=name+('.gz' if compress else '')
 dest=a.output/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 manifest['files'].append({'source':str(path.resolve()),'archive':rel,'raw_sha256':sha(raw),'stored_sha256':sha(data),'raw_bytes':len(raw),'stored_bytes':len(data),'compression':'gzip' if compress else 'none'})
(a.output/'inventory.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in manifest['files']:
 stored=(a.output/row['archive']).read_bytes();assert sha(stored)==row['stored_sha256']
 raw=gzip.decompress(stored) if row['compression']=='gzip' else stored
 assert sha(raw)==row['raw_sha256']
print('Archived and rehashed',len(files),'files')
