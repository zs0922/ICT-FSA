#!/usr/bin/env python3
"""Read actual routed reports. This collects evidence, not CDC acceptance."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def metrics(obj, flat_path=None):
    obj = obj.resolve()
    required = ['report/timing.txt', 'report/utilization.txt',
                'report/clocks.txt',
                'report/route_status.txt', 'report/drc.txt',
                'audit/run_properties.txt', 'audit/cdc.txt',
                'audit/check_timing.txt', 'audit/exceptions.txt']
    for name in required:
        if not (obj / name).is_file():
            raise ValueError('Missing report: ' + str(obj / name))
    content = (obj / 'report/timing.txt').read_text()
    match = re.search(r'WNS\(ns\).*?\n\s*-+[^\n]*\n\s*([^\n]+)', content, re.S)
    values = list(map(float, match[1].split()))
    if len(values) != 12:
        raise ValueError('Unexpected timing summary columns')
    timing_keys = ['wns_ns', 'tns_ns', 'setup_failing', 'setup_total',
                   'whs_ns', 'ths_ns', 'hold_failing', 'hold_total',
                   'wpws_ns', 'tpws_ns', 'pulse_failing', 'pulse_total']
    hierarchy = (obj / 'report/utilization.txt').read_text().splitlines()
    header = next(line for line in hierarchy if '| Total LUTs ' in line)
    top = next(line for line in hierarchy if re.match(r'\| NM37FPGATestHarness\s+\|', line))
    keys = [v.strip() for v in header.split('|')[3:-1]]
    numbers = [int(v.strip()) for v in top.split('|')[3:-1]]
    if len(keys) != len(numbers):
        raise ValueError('Unexpected hierarchical resource columns')
    resources = dict(zip(keys, numbers))
    flat_path = flat_path or obj / 'report/utilization_flat.txt'
    flat = flat_path.read_text().splitlines() if flat_path.is_file() else []
    utilization = {}
    for label in ('CLB LUTs', 'CLB Registers', 'Block RAM Tile', 'DSPs'):
        if not flat:
            continue
        line = next(line for line in flat if re.match(r'\|\s*' + re.escape(label) + r'\s*\|', line))
        cols = [v.strip() for v in line.split('|')[1:-1]]
        if len(cols) != 5:
            raise ValueError('Unexpected flat resource columns: ' + line)
        utilization[label] = dict(used=float(cols[1]), available=float(cols[3]), percent=float(cols[4]))
    if utilization:
        comparisons = {'CLB LUTs': resources['Total LUTs'],
                       'CLB Registers': resources['FFs'],
                       'Block RAM Tile': resources['RAMB36'] + resources['RAMB18'] / 2,
                       'DSPs': resources['DSP Blocks']}
        for label, expected in comparisons.items():
            if utilization[label]['used'] != expected:
                raise ValueError('Flat/hierarchical resource disagreement: ' + label)
    props = dict(line.split('=', 1) for line in (obj / 'audit/run_properties.txt').read_text().splitlines())
    coverage = dict((key, int(count)) for key, count in re.findall(
        r'^\d+\. checking (\w+) \((\d+)\)', (obj / 'audit/check_timing.txt').read_text(), re.M))
    cdc = dict((kind, dict(severity=severity, count=int(count))) for kind, severity, count in re.findall(
        r'^(CDC-\d+)\s+(Critical|Warning|Info)\s+(\d+)\s', (obj / 'audit/cdc.txt').read_text(), re.M))
    route_text = (obj / 'report/route_status.txt').read_text()
    route = {key: int(re.search(re.escape(key) + r'\.+\s*:\s*(\d+)', route_text)[1])
             for key in ('# of routable nets', '# of fully routed nets', '# of nets with routing errors')}
    dcp = obj / 'post_route.dcp'
    hashes = {name: sha(obj / name) for name in required}
    if flat:
        hashes[str(flat_path.resolve())] = sha(flat_path)
    return dict(obj=str(obj), checkpoint_sha256=sha(dcp),
                timing=dict(zip(timing_keys, values)), dut=props,
                resources=resources, utilization=utilization,
                constraint_coverage=coverage, cdc_counts=cdc, route=route,
                drc_error_or_critical=bool(re.search(r'\|\s*(?:Error|Critical Warning)\s*\|', (obj / 'report/drc.txt').read_text())),
                flat_utilization_source=str(flat_path.resolve()) if flat else None,
                evidence_sha256=hashes,
                scope='Actual routed reports; does not declare CDC or board acceptance')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('obj', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--flat', type=Path, help='Optional read-only flat utilization report for the same checkpoint')
    args = parser.parse_args()
    result = metrics(args.obj, args.flat)
    with args.out.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({key: result[key] for key in ('timing', 'resources', 'cdc_counts')}))
