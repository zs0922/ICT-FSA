#!/usr/bin/env python3
"""Build materialized historical sources; never applies patches or imports old outputs."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from ict_cli import ROOT, profile, sha, save, source_identity


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['build','verify','sim','elaborate','implement'])
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--array-size',type=int,default=16)
    a=parser.parse_args(); p=profile(); out=a.out.resolve(); stage=p['id']
    if stage not in ('U280','NM37','A70-P3'): parser.error('Historical backend used with modern profile')
    env=dict(os.environ,USE_CHISEL6='1',ICT_BUILD_OUT=str(out),ICT_DUT_MHZ=str(p['dut_mhz']))
    env['JAVA_TOOL_OPTIONS']=env.get('JAVA_TOOL_OPTIONS','')+' -Xmx16G -Xss8M -XX:ActiveProcessorCount=16 -Dsbt.supershell=false -Dsbt.server.autostart=false'
    env['PYTHONPATH']=str(ROOT/'generators/easyfloat')+':'+str(ROOT/'generators/fsa/python')
    board=p['board'].lower(); model=p.get('model',p['board']+'FPGATestHarness'); cfg=p.get('config','Empty'+p['board']+'Config')
    name=f'chipyard.fpga.{board}.{model}.{cfg}'
    build=out/p.get('build_label',stage)/'fpga'/name
    jar=out/'generator.jar'
    base=['make','-C',str(ROOT/'fpga'),'SUB_PROJECT='+board,'CONFIG='+cfg,'GENERATOR_CLASSPATH='+str(jar)]
    identity=source_identity(p)
    def run(cmd,cwd=ROOT):
        print('RUN:',json.dumps(cmd),flush=True);subprocess.run(cmd,cwd=cwd,env=env,check=True)
    def fresh(path):
        if path.exists(): raise ValueError(f'Existing artifact {path}; preserve and use a new build output')
    if a.phase=='build':
        fresh(out); out.mkdir(parents=True);(out/'logs').mkdir()
        shutil.copytree(ROOT/'fpga/fpga-shells',out/'shell',ignore=shutil.ignore_patterns('.git','target','__pycache__'))
        save(out/'build.json',{'source':str(ROOT),**identity,'status':'building'})
        run(base+[str(jar)])
        if not jar.is_file() or not jar.stat().st_size: raise ValueError('Assembly exited without a generator JAR')
        save(out/'build.json',{'source':str(ROOT),**identity,'status':'built','jar_sha256':sha(jar)})
        return
    record=json.loads((out/'build.json').read_text())
    if any(record.get(k)!=v for k,v in identity.items()) or record.get('jar_sha256')!=sha(jar): raise ValueError('Source/JAR differs from build receipt')
    if a.phase=='verify':
        if stage!='A70-P3': raise ValueError('Historical baseline has no inherited focused unit/formal suite; use its declared sim regression')
        fresh(out/'formal-rtl'); fresh(out/'formal')
        run(['java','-jar','scripts/sbt-launch.jar','-Dsbt.supershell=false',
             'set fsa / Test / sources := (fsa / Test / sources).value.filter(f => Set("A70AccumulatorVerification.scala", "A70LegacyExp2.scala", "A70LegacyReciprocal.scala", "A70LegacyFMA.scala").contains(f.getName))',
             'fsa/Test/runMain fsa.A70AccumulatorVerification',f'fsa/Test/runMain fsa.A70AccumulatorVerification emit {out}/formal-rtl'])
        run([sys.executable,str(ROOT/'scripts/ict/a70_verify/window_proof/run-proof.py'),'--rtl',str(out/'formal-rtl'),'--out',str(out/'formal')])
    elif a.phase=='sim':
        size=a.array_size
        if size not in p['array_sizes']: raise ValueError('Unsupported array size')
        config=p.get('sim_configs',{}).get(str(size),f'AXI4FSA{size}X{size}Fp16Config')
        sim=out/f'sim{size}'; fresh(sim);sim.mkdir()
        run(['make','-C',str(ROOT/'sims/verilator'),'-j'+os.environ.get('FSA_JOBS','8'),'CONFIG='+config,'CXX='+os.environ.get('CXX','g++'),'CC='+os.environ.get('CC','gcc'),'LINK='+os.environ.get('CXX','g++'),'GENERATOR_CLASSPATH='+str(jar),'-o',str(jar),'build_dir='+str(sim/'build'),'sim='+str(sim/'simulator'),'default'])
        for seq in (size,2*size):
            run([os.environ.get('FSA_PYTHON',sys.executable),str(ROOT/'scripts/ict/a70_verify/verify_sim.py'),'--source',str(ROOT),'--binary',str(sim/'simulator'),'--config',str(sim/'build'/f'chipyard.harness.TestHarness.{config}.FSAConfig.json'),'--out',str(sim/f'seq{seq}'),'--seq',str(seq)])
    elif a.phase=='elaborate':
        fresh(build)
        run(base+['-o',str(jar),'build_dir='+str(build),str(build/(name+'.vsrcs.f'))])
    elif a.phase=='implement':
        fresh(build/'obj')
        ip=sorted(str(f) for f in build.rglob('*.vivado.tcl'))
        run(['vivado','-mode','batch','-source',str(ROOT/'scripts/ict/implement.tcl'),'-tclargs','-top-module',model,'-F',str(build/(name+'.vsrcs.f')),'-board',board,'-ip-vivado-tcls',' '.join(ip)],cwd=build)
        if not (build/'obj/post_route.dcp').is_file(): raise ValueError('Implementation did not produce post_route.dcp')
    print('COMPLETE:',a.phase)

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.CalledProcessError) as exc:
        print('ERROR:',exc,file=sys.stderr);sys.exit(2)
