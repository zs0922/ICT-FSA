#!/usr/bin/env python3
"""Compare sealed A110/APB55 and A120/APB60 outputs without editing either build."""
import argparse
import json
from pathlib import Path
import comparison_helpers as h


def compare(old, new):
    h.scanner_selftest()
    report = {'method': 'Exact bytes for inputs/configuration; exact FP32 payloads and all eight counters; RTL removes only CIRCT source location line comments.',
              'script_sha256': h.file_sha(Path(__file__)),
              'helpers_sha256': h.file_sha(Path(h.__file__)), 'builds': {}, 'rtl': {}, 'cases': []}
    manifests = {}
    for key, build in [('A110', old), ('A120', new)]:
        report['builds'][key], manifests[key] = h.verify_new_stage_seals(build)
    board_name = 'chipyard.fpga.nm37.NM37FPGATestHarness.EmptyNM37Config'
    sim_name = 'chipyard.harness.TestHarness.AXI4FSA16X16Fp16Config'
    dirs = {}
    for key, build in [('A110', old), ('A120', new)]:
        board = build/key/'fpga'/board_name/'gen-collateral'
        sim = build/'sim16'/'generated-src'/sim_name/'gen-collateral'
        h.verify_comparison_coverage(build, manifests[key], board, sim)
        dirs[key] = {'board': board, 'sim16': sim}
    for kind in ('board', 'sim16'):
        files = {key: {p.name:p for p in dirs[key][kind].glob('*.sv')} for key in dirs}
        h.require_equal(set(files['A110']), set(files['A120']), kind+' file set')
        rows = []
        for name in sorted(files['A110']):
            core = any(name[:-3] == p or name.startswith(p+'_') for p in h.CORE_PREFIXES)
            hashes = {key: h.sha(h.normalize_source_locations(files[key][name].read_bytes())[0]) for key in files}
            equal = hashes['A110'] == hashes['A120']
            if core or kind == 'sim16':
                h.require_equal(equal, True, kind+'/'+name)
            if kind == 'board' and not equal:
                h.require_equal(name, 'ResetWrangler.sv', 'Only frequency-dependent debounce RTL may differ')
                a = h.normalize_source_locations(files['A110'][name].read_bytes())[0]
                b = h.normalize_source_locations(files['A120'][name].read_bytes())[0]
                h.require_equal(a.count(b"13'h157C"), 1, 'A110 debounce constant count')
                h.require_equal(a.replace(b"13'h157C", b"13'h1770"), b, 'Exact 5500 -> 6000 APB debounce ticks change')
                report['reset_debounce'] = {'baseline_ticks':5500, 'candidate_ticks':6000, 'baseline_MHz':55, 'candidate_MHz':60, 'time_us':100, 'note':'ResetWrangler uses its slowest input clock; no pipeline stage changed.'}
            rows.append({'name':name, 'core':core, 'normalized_sha256':hashes, 'equal':equal})
        report['rtl'][kind] = rows
    for size in (4,8,16):
        for seq in (size,size*2):
            rel = Path(f'sim{size}/seq{seq}')
            cases = {key:build/rel for key,build in [('A110',old),('A120',new)]}
            for name in ('inst.bin','mem.elf'):
                h.require_equal(h.file_sha(cases['A110']/name),h.file_sha(cases['A120']/name),str(rel/name))
            cfg = f'chipyard.harness.TestHarness.AXI4FSA{size}X{size}Fp16Config'
            cfgpath = Path(f'sim{size}/generated-src/{cfg}/{cfg}.FSAConfig.json')
            h.require_equal(h.file_sha(old/cfgpath),h.file_sha(new/cfgpath),'config')
            counts = {}
            payloads = {}
            for key,case in cases.items():
                counts[key] = h.log_counters((case/'test.log').read_text(),str(case))
                actual = h.npy_float32(case/'actual.npy')
                expected = h.npy_float32(case/'expected.npy')
                h.require_equal(actual,expected,'bitwise result '+key)
                result = h.unique_json(case/'result.json')
                h.require_equal(result['bitwise_equal'],True,'result PASS')
                h.require_equal(result['actual_sha256'],h.sha(actual[1]),'actual hash')
                h.require_equal(result['expected_sha256'],h.sha(expected[1]),'expected hash')
                payloads[key] = h.sha(actual[1])
            h.require_equal(counts['A110'],counts['A120'],'counters and TB cycles')
            h.require_equal(payloads['A110'],payloads['A120'],'output bits across builds')
            counters, tb = counts['A120']
            report['cases'].append({'case':str(rel),'counters':counters,'testbench_cycles':tb,'output_sha256':payloads['A120'],
                'exec_us_A110':counters['execTime']/110,'exec_us_A120':counters['execTime']/120,
                'speedup':120/110,'mxBubble_fraction_of_execTime':counters['mxBubble']/counters['execTime'] if counters['execTime'] else None})
    report['status']='pass'
    report['performance_scope']='Simulation counters; microseconds are cycles/frequency, not board measurements. mxBubble is the hardware counter, not every idle cycle.'
    return report

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    for name in ('baseline','candidate','output'): p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    if a.output.exists(): raise SystemExit('Refusing to overwrite comparison')
    a.output.write_text(json.dumps(compare(a.baseline,a.candidate),indent=2)+'\n')
