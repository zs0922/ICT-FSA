#!/usr/bin/env python3
"""Maintainer-only lock refresh after a reviewed source change.

This writes input identities, never test/implementation success. First stage
all intended input files in Git; commit the resulting lock in the same change.
Build/test commands only verify the lock and never regenerate it.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--profile', required=True, choices=['A100', 'A110-APB55', 'A120-APB60'])
p.add_argument('--write', action='store_true', help='Explicitly rewrite the reviewed source input lock')
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
short = {'A100': 'a100', 'A110-APB55': 'a110', 'A120-APB60': 'a120'}[a.profile]
path = root / ('scripts/nm37-' + short + '/check.py')
spec = importlib.util.spec_from_file_location('stagecheck', path)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)
modes = check.source_modes()
lock_path = root / ('fpga/baselines/nm37-' + short + '/source-lock.json')
lock = json.loads(lock_path.read_text())
lock['source_modes'] = modes
lock['source_hashes'] = {name: check.sha(root / name) for name in modes}
shell_prefix = 'fpga/fpga-shells/'
# The NM37 runtime snapshot contains the Xilinx shell subtree. Scala and
# other vendors remain covered by source_hashes, but are not copied into OUT/shell.
shell_paths = [name for name in modes if name.startswith(shell_prefix + 'xilinx/')]
if not shell_paths:
    raise RuntimeError('No tracked Xilinx shell inputs; stage the intended shell files first')
# The backend checks both the source tree and its frozen shell snapshot.
# Derive both identities from the same reviewed Git file set, including adds/removals.
lock['shell_hashes'] = {
    name[len(shell_prefix):]: lock['source_hashes'][name] for name in shell_paths
}
lock.pop('historical_generator_sha256', None)
lock['input_policy'] = 'ICT-FSA reviewed tracked inputs; shell is vendored; no runtime patching. Input lock is not a verification pass.'
if a.write:
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + '\n')
    print('Updated source input lock (not a test PASS):', lock_path)
else:
    assert lock == json.loads(lock_path.read_text()), 'Source lock stale; review the diff before an explicit --write'
    print('Source lock matches the Git index and working tree; dependency initialization was not checked.')
