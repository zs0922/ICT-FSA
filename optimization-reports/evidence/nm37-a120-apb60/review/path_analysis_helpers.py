#!/usr/bin/env python3
"""Summarize routed reports. Frequency estimates freeze delays/skew/jitter; NOT STA at new frequency."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re


def parse(text):
    paths = []
    for block in re.split(r'(?=Slack \()', text)[1:]:
        def get(pattern):
            m = re.search(pattern, block, re.M)
            if not m:
                raise ValueError('Missing timing field: ' + pattern)
            return m
        delay = get(r'Data Path Delay:\s*([\d.]+)ns\s*\(logic ([\d.]+)ns .*?route ([\d.]+)ns')
        path = dict(slack_ns=float(get(r'Slack .*?:\s*([-\d.]+)ns')[1]),
            start=get(r'^  Source:\s*(.+)')[1], end=get(r'^  Destination:\s*(.+)')[1],
            requirement_ns=float(get(r'Requirement:\s*([-\d.]+)ns')[1]),
            data_ns=float(delay[1]), logic_ns=float(delay[2]), route_ns=float(delay[3]),
            logic_levels=int(get(r'Logic Levels:\s*(\d+)')[1]),
            path_type=get(r'^  Path Type:\s*(.+)')[1])
        path['route_pct'] = 100 * path['route_ns'] / path['data_ns']
        pe = re.search(r'/mesh_(\d+)_(\d+)/', path['end'])
        path['pe'] = f'{pe[1]},{pe[2]}' if pe else None
        path['category'] = ('pe_before_add_register' if pe and '/fma/adderOutAbs_reg' in path['end'] else
                            'pe_other' if pe else 'cmp_internal' if '/cmp_array_' in path['end'] else
                            'cmp_output_link' if '/cmp_out_pipe_' in path['end'] else
                            'instruction_counter' if '/deqInstCnt_reg' in path['end'] else 'reset' if 'reset' in (path['start'] + path['end']).lower() else 'other')
        paths.append(path)
    if not paths:
        raise ValueError('No timing paths')
    return paths


def summarize(paths):
    categories = {}
    for category in sorted({p['category'] for p in paths}):
        group = [p for p in paths if p['category'] == category]
        categories[category] = dict(count=len(group), worst=min(group, key=lambda p: p['slack_ns']))
    worst = min(paths, key=lambda p: p['slack_ns'])
    # Only a same-DUT, one-period setup path can use this elementary estimate.
    if any(not p['path_type'].startswith('Setup') or abs(p['requirement_ns']-1000/110) > 0.001 for p in paths):
        raise ValueError('Expected only one-period 110 MHz DUT setup paths')
    baseline_period = 1000 / 110
    return dict(path_count=len(paths), categories=categories,
        endpoint_pe_counts=dict(collections.Counter(p['pe'] for p in paths if p['pe'])),
        worst=worst, fixed_delay_dut_ceiling_mhz=1000/(baseline_period-worst['slack_ns']),
        scope='Same-DUT setup paths only. Fixed route/skew/uncertainty estimate; excludes other domains and is not new-frequency implementation/STA.',
        screening=[dict(dut_mhz=f, apb_mhz=f/2, period_ns=1000/f,
                        estimated_dut_slack_ns=worst['slack_ns']+1000/f-baseline_period,
                        requested_2_to_1_apb_integer=(f % 2 == 0),
                        ideal_active_speedup_vs_a110=f/110) for f in (110,115,116,118,120,124,125,128,130)])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    paths=parse(a.report.read_text())
    result=summarize(paths)
    result.update(report=str(a.report.resolve()), report_sha256=hashlib.sha256(a.report.read_bytes()).hexdigest(), paths=paths)
    with a.out.open('x') as f: json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='paths'},indent=2))

if __name__=='__main__': main()
