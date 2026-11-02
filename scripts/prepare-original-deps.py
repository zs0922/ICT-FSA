#!/usr/bin/env python3
"""Initialize the original Scala/Verilator build dependencies at parent gitlink pins."""
import argparse,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--mirror-root',type=Path,help='Optional read-only existing Chipyard checkout; no source files copied');a=p.parse_args()
def run(args,**kw):return subprocess.check_output(args,text=True,**kw).strip()
links={l.split('\t')[1]:l.split()[2] for l in run(['git','-C',str(root),'ls-tree','-r','HEAD']).splitlines() if l.startswith('160000')}
paths=[n for n in links if n.startswith(('generators/','tools/','fpga/')) and n not in ['tools/circt','tools/axe','tools/torture','tools/install-circt']]+['sims/firesim']
base=['git','-c','url.https://github.com/.insteadOf=git@github.com:']
def prepare(parent,name,sha,relative):
 dest=parent/name
 if (dest/'.git').exists():
  actual=run(['git','-C',str(dest),'rev-parse','HEAD'])
  dirty=run(['git','-C',str(dest),'status','--porcelain','--untracked-files=normal'])
  if actual!=sha or dirty:raise RuntimeError(f'Preserve {dest}: checkout differs or has changes. Use a new clean source directory.')
 elif a.mirror_root:
  old=a.mirror_root.resolve();source=old/relative
  repo=Path(run(['git','-C',str(source),'rev-parse','--absolute-git-dir']))
  if repo==old/'.git':repo=old/'.git/modules'/relative
  if not repo.is_dir():raise RuntimeError('Missing mirror objects: '+str(repo))
  subprocess.run(['git','clone','--shared','--no-checkout',str(repo),str(dest)],check=True)
  subprocess.run(['git','-C',str(dest),'checkout','--detach',sha],check=True)
 else:
  subprocess.run(base+['-C',str(parent),'submodule','update','--init','--checkout','--',name],check=True)
 subprocess.run(base+['-C',str(parent),'submodule','init','--',name],check=True)
 subprocess.run(base+['-C',str(parent),'submodule','absorbgitdirs','--',name],check=True)
for name in paths:prepare(root,name,links[name],name)
rocket=root/'generators/rocket-chip'
for name in ['dependencies/cde','dependencies/chisel','dependencies/diplomacy','dependencies/hardfloat']:
 sha=run(['git','-C',str(rocket),'ls-tree','HEAD','--',name]).split()[2]
 prepare(rocket,name,sha,'generators/rocket-chip/'+name)
for parent_name,name in [('generators/radiance','src/main/resources/vsrc/vortex'),('generators/radiance/src/main/resources/vsrc/vortex','third_party/fpnew')]:
 parent=root/parent_name
 sha=run(['git','-C',str(parent),'ls-tree','HEAD','--',name]).split()[2]
 prepare(parent,name,sha,parent_name+'/'+name)
print('PASS: original Scala/Verilator dependencies initialized; software toolchains are separate prerequisites.')
