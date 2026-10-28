#!/usr/bin/env python3
"""Read original A110/APB55 and A120 reports; no synthesis or timing changes."""
import argparse,json
from pathlib import Path
import physical_summary_helpers as h

p=argparse.ArgumentParser()
p.add_argument('--baseline-root',type=Path,required=True)
p.add_argument('--candidate-build',type=Path,required=True)
p.add_argument('--diagnostics',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--reaudit',type=Path)
a=p.parse_args()
if a.output.exists():raise SystemExit('Refusing to overwrite comparison')
oldobj=a.baseline_root/'reaudit04/obj'
obj=a.candidate_build/'A120/fpga/chipyard.fpga.nm37.NM37FPGATestHarness.EmptyNM37Config/obj'
cap=oldobj/'report/utilization_flat.txt'
physical=a.candidate_build/'physical.passed.json'
if not physical.exists():physical=a.candidate_build/'physical.failed.json'
if a.reaudit:
 obj=a.reaudit/'obj'
 physical=a.reaudit/'acceptance/initial/reaudit.passed.json'
 assert physical.is_file(), 'Revised acceptance required'
old=h.extract('A110/APB55',oldobj,a.baseline_root/'reaudit04/acceptance/cdc-reviewed/reaudit.passed.json',cap,build=a.baseline_root/'build04/build.json',flat=cap)
new=h.extract('A120/APB60',obj,physical,cap,build=a.candidate_build/'build.json',flat=a.diagnostics/'utilization_flat.rpt',pulse=a.diagnostics/'pulse_width.rpt')
r={'scope':'Read-only extraction; acceptance is the separately bound physical decision. No board timing measurement.', 'script_sha256':h.sha(Path(__file__)), 'helper_sha256':h.sha(Path(h.__file__)), 'baseline':old,'candidate':new,'differences':h.differences(new,old)}
a.output.write_text(json.dumps(r,indent=2)+'\n')
for label,v in [('baseline',old),('candidate',new)]:
 print(label,{k:v[k].get('status') for k in ['timing_summary','dut_setup','dut_hold','resources','bus_skew','route','drc','cdc']})
