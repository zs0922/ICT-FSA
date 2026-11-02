#!/usr/bin/env python3
"""Verify original upstream inputs; this does not certify a build or FPGA."""
import argparse,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--require-core-deps',action='store_true');a=p.parse_args()
def git(*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
meta=json.loads((root/'docs/baselines/original-provenance.json').read_text())
allowed={'README.md','docs/baselines/upstream-README.md','docs/baselines/original-provenance.json','docs/baselines/original-validation.md','scripts/verify-original.py','scripts/prepare-original-deps.py'}
changed=set(git('diff','--name-only',meta['upstream_commit'],'--',':(exclude)README.md').splitlines())
wrong=changed-allowed
for path in git('ls-files','--others','--exclude-standard').splitlines():
 if path not in allowed: wrong.add(path)
if wrong:sys.exit('ERROR: unexpected upstream input changes: '+', '.join(sorted(wrong)))
links={line.split('\t')[1]:line.split()[2] for line in git('ls-tree','-r','HEAD').splitlines() if line.startswith('160000')}
if links!=meta['root_gitlinks']:sys.exit('ERROR: upstream gitlink pins changed')
missing=[]
for name in ('generators/fsa','generators/easyfloat','fpga/fpga-shells'):
 d=root/name
 if not (d/'.git').exists():missing.append(name);continue
 actual=subprocess.check_output(['git','-C',str(d),'rev-parse','HEAD'],text=True).strip()
 dirty=subprocess.check_output(['git','-C',str(d),'status','--porcelain','--untracked-files=normal'],text=True).strip()
 if actual!=links[name] or dirty:sys.exit('ERROR: core dependency mismatch or edits: '+name)
if missing and a.require_core_deps:sys.exit('ERROR: initialize pinned core dependencies: '+', '.join(missing))
print('PASS: upstream tracked hardware and gitlink pins unchanged')
print('Core dependencies missing: '+(', '.join(missing) or 'none'))
print('This is source identity verification, not compilation, timing or board acceptance.')
