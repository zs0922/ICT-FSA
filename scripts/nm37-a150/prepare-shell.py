#!/usr/bin/env python3
"""Compatibility preflight: verify vendored shell, never mutate sources."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[2]
short = Path(__file__).resolve().parent.name
lock = json.loads((root / 'fpga/baselines' / short / 'source-lock.json').read_text())
for name, expected in lock['shell_hashes'].items():
    path = root / 'fpga/fpga-shells' / name
    assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected, 'Vendored shell mismatch: ' + name
print('PASS: vendored shell input hashes; no files changed')
