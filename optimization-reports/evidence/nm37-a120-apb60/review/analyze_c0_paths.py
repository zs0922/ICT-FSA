#!/usr/bin/env python3
import argparse,collections,hashlib,json
from pathlib import Path
import path_analysis_helpers as h
p=argparse.ArgumentParser();p.add_argument('--reports',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise SystemExit('Refusing to overwrite analysis')
r={'scope':'Actual A120 routed checkpoint reports; no extrapolated Fmax or board measurements. SLR data covers reported SLICE sites, not every routing PIP.', 'reports':{}}
for name in ('dut_setup_top1000.rpt','from_pe_fma.rpt','from_accumulator.rpt','from_scratchpad.rpt','from_reset.rpt'):
 f=a.reports/name;paths=h.parse(f.read_text())
 if name=='dut_setup_top1000.rpt':
  assert len(paths)==1000
  assert all(x['path_type'].startswith('Setup') and abs(x['requirement_ns']-1000/120)<.001 for x in paths)
 groups={}
 for cat in sorted({x['category'] for x in paths}):
  rows=[x for x in paths if x['category']==cat];groups[cat]={'count':len(rows),'worst':min(rows,key=lambda x:x['slack_ns'])}
 r['reports'][name]={'source':str(f.resolve()),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'path_count':len(paths),'worst':min(paths,key=lambda x:x['slack_ns']),'categories':groups,'pe_counts':dict(collections.Counter(x['pe'] for x in paths if x['pe']))}
r['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
r['helper_sha256']=hashlib.sha256(Path(h.__file__).read_bytes()).hexdigest()
a.output.write_text(json.dumps(r,indent=2)+'\n')
for name,v in r['reports'].items():print(name,v['worst']['slack_ns'],{k:x['count'] for k,x in v['categories'].items()})
