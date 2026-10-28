"""Experimental export, explicit programming, and receipt-bound numerical tests."""
import csv
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import socket
import statistics
import subprocess
import sys
import time
from ict_cli import sha, save, source_identity, bind
from . import runtime


def fresh(path):
    if path.exists() or path.is_symlink(): raise ValueError(f'Output exists: {path}; select a new attempt directory')

def load_export(directory, p):
    directory=directory.resolve()
    m=json.loads((directory/'experiment.json').read_text())
    if m.get('status')!='exported' or m.get('profile')!=p['id'] or m.get('clock_mhz')!=p['dut_mhz']:
        raise ValueError('Export/profile mismatch or export incomplete')
    for kind in ('bitstream','config'):
        path=(directory/m[kind]['path']).resolve()
        if not path.is_relative_to(directory) or not path.is_file() or sha(path)!=m[kind]['sha256']:
            raise ValueError(kind+' export hash/path mismatch')
    return m, directory/m['bitstream']['path'], directory/m['config']['path']

def routed_inputs(build,state):
    record=state/'implement.json'
    if not record.is_file():raise ValueError('No implementation attempt receipt; use implement before export')
    artifacts=json.loads(record.read_text()).get('routed_artifacts')
    if not artifacts:raise ValueError('Implementation has no recorded routed DCP/config; inspect its failure logs')
    dcps=list(build.rglob('post_route.dcp'))
    if len(dcps)!=1:raise ValueError('Expected one routed checkpoint from this implementation')
    configs=list(dcps[0].parent.parent.glob('*.FSAConfig.json'))
    if len(configs)!=1:raise ValueError('Expected one generated config')
    expected={str(f.relative_to(build)):sha(f) for f in [dcps[0],configs[0]]}
    if expected!=artifacts:raise ValueError('Routed DCP/config changed after implementation; preserve mixed artifacts and rebuild in a new output')
    return dcps[0],configs[0]

def export(a,p,root):
    build=a.out.resolve(); state=bind(build,p)
    routed_inputs(build,state)
    dcps=list(build.rglob('post_route.dcp'))
    if len(dcps)!=1: raise ValueError(f'Expected exactly one routed DCP, found {len(dcps)}; complete implementation first')
    dcp=dcps[0]; configs=list(dcp.parent.parent.glob('*.FSAConfig.json'))
    if len(configs)!=1: raise ValueError('Expected one generated FSAConfig.json adjacent to routed design')
    out=a.result_out.resolve();fresh(out)
    exe=shutil.which(a.vivado)
    if not exe: raise ValueError('Vivado missing; load settings64.sh')
    identity=source_identity(p);out.mkdir(parents=True)
    shutil.copy2(configs[0],out/'FSAConfig.json')
    bit=out/(p['id']+'_EXPERIMENTAL.bit')
    manifest={'schema_version':1,'profile':p['id'],'clock_mhz':p['dut_mhz'],'source':identity,
              'purpose':'EXPERIMENTAL_BOARD_TEST','release_approved':False,'cdc_review':'not_closed_by_export',
              'dcp_sha256':sha(dcp),'dcp':str(dcp),'status':'running','created_utc':datetime.now(timezone.utc).isoformat(),
              'config':{'path':'FSAConfig.json','sha256':sha(out/'FSAConfig.json')}}
    save(out/'experiment.json',manifest)
    script=root/'scripts/ict/export.tcl';shutil.copy2(script,out/'export.tcl')
    try:
        with (out/'console.log').open('x') as log:
            subprocess.run([exe,'-mode','batch','-source',str(out/'export.tcl'),'-log',str(out/'vivado.log'),'-journal',str(out/'vivado.jou'),'-tclargs',str(dcp),str(out),str(p['dut_mhz']),str(bit)],cwd=out,stdout=log,stderr=subprocess.STDOUT,check=True)
        if not bit.is_file() or not bit.stat().st_size or sha(dcp)!=manifest['dcp_sha256']: raise ValueError('Missing bitstream or changed DCP')
        manifest.update(status='exported',bitstream={'path':bit.name,'sha256':sha(bit)})
        (out/'SHA256SUMS').write_text(f'{sha(bit)}  {bit.name}\n{sha(out/"FSAConfig.json")}  FSAConfig.json\n')
    except BaseException as exc:
        manifest.update(status='failed_or_interrupted',error=str(exc));raise
    finally:save(out/'experiment.json',manifest)
    print('EXPORTED:',bit,'\nExperiment only; no handwritten review JSON required. CDC acceptance remains separate.')

def validate_receipt(receipt,manifest,bdf):
    r=json.loads(receipt.read_text())
    if r.get('status')!='programmed' or r.get('profile')!=manifest['profile'] or r.get('bitstream_sha256')!=manifest['bitstream']['sha256']:
        raise ValueError('Successful programming receipt does not match this exported image. Changing profile/variables does not program FPGA.')
    if r.get('bdf_operator_mapping')!=bdf: raise ValueError('PCI BDF differs from programming receipt; re-identify target rather than guessing device number')
    return r

def program(a,p,root):
    manifest,bit,_=load_export(a.export_dir,p)
    if not re.fullmatch(r'[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]',a.bdf): raise ValueError('Expected lowercase full PCI BDF')
    if any(ch in a.hw_target+a.hw_device for ch in '*?[]\n\r'): raise ValueError('Explicit exact target/device names required; no wildcard')
    out=a.out.resolve();fresh(out)
    cmd=[a.vivado,'-mode','batch','-source',str(root/'scripts/ict/program.tcl'),'-tclargs',a.server,a.hw_target,a.hw_device,str(bit),p.get('jtag_part','')]
    if a.dry_run: print(json.dumps({'command':cmd,'hardware_programmed':False},indent=2));return
    if not shutil.which(a.vivado):raise ValueError('Vivado missing')
    out.mkdir(parents=True)
    receipt={'schema_version':1,'status':'programming','profile':p['id'],'bitstream_sha256':sha(bit),'bitstream':str(bit),
             'identity_kind':'successful_programming_operation_not_hardware_identity_readback',
             'jtag_target':a.hw_target,'jtag_device':a.hw_device,'hw_server':a.server,'bdf_operator_mapping':a.bdf,
             'created_utc':datetime.now(timezone.utc).isoformat(),'host':socket.gethostname()}
    save(out/'program.json',receipt)
    try:
        with (out/'console.log').open('x') as log:
            subprocess.run(cmd,cwd=out,stdout=log,stderr=subprocess.STDOUT,check=True)
        if 'ICT_FSA_PROGRAM_COMMAND_COMPLETED' not in (out/'console.log').read_text():raise ValueError('Programming completion marker missing')
        if sha(bit)!=receipt['bitstream_sha256']:raise ValueError('Bitstream changed during programming')
        receipt['status']='programmed'
    except BaseException as exc:
        receipt.update(status='failed_or_interrupted',error=str(exc));raise
    finally:save(out/'program.json',receipt)
    print('PROGRAMMED; receipt:',out/'program.json','\nRe-enumerate PCIe/reload xdma if necessary, then re-check BDF/device. Receipt is an operation record, not live hardware identity readback.')

def test(a,p,root):
    if p['board']!='NM37': raise ValueError('U280 source/build retained; board tester currently validates NM37 XDMA ID 10ee:9038. U280 device mapping requires separate validation.')
    manifest,bit,config=load_export(a.export_dir,p)
    receipt=validate_receipt(a.receipt.resolve(),manifest,a.bdf)
    identity=source_identity(p)
    if identity!=manifest['source']:raise ValueError('Current source differs from image source. Use matching milestone checkout for this baseline test.')
    if not re.fullmatch(r'xdma\d+',a.device) or a.seq<=0 or a.seq%16 or not 0<=a.seed<2**32 or a.repeat<1 or a.warmup<0:raise ValueError('Invalid device/seq/seed/repeat/warmup')
    cfg=json.loads(config.read_text())
    if (cfg.get('sa_rows'),cfg.get('sa_cols'),cfg.get('e_type'),cfg.get('a_type'))!=(16,16,'fp16','fp32'):raise ValueError('Expected 16x16 fp16/fp32 generated config')
    out=a.out.resolve();fresh(out)
    if a.dry_run: print('INPUTS OK; no MMIO access, programming or numerical test performed');return
    paths={'software':root/'generators/fsa/python','easyfloat':root/'generators/easyfloat','config':config}
    metadata={'schema_version':1,'profile':p['id'],'clock_mhz_assumed':p['dut_mhz'],'source':identity,'export':manifest,
              'program_receipt':receipt,'program_receipt_sha256':sha(a.receipt),'seq':a.seq,'seed':a.seed,
              'device':a.device,'bdf':a.bdf,'repeat':a.repeat,'warmup':a.warmup,'status':'started',
              'hardware_identity_kind':receipt['identity_kind'],'python':sys.version,'host':socket.gethostname(),
              'software_files':runtime.software_files(paths['software']),'easyfloat_files':runtime.software_files(paths['easyfloat']),
              'counter_note':'mxBubble is matrix ready&&!valid, not PE idle; counters may overlap. enq/deq are cumulative uint32; per-run deltas are checked.'}
    runtime.probe_device(a.device,a.bdf)
    out.mkdir(parents=True);save(out/'run.json',metadata)
    backend=None
    console=(out/'console.log').open('x'); saved_stdout=sys.stdout; saved_stderr=sys.stderr
    class Tee:
        def __init__(self, stream): self.stream=stream
        def write(self,text): self.stream.write(text);console.write(text);self.flush();return len(text)
        def flush(self): self.stream.flush();console.flush()
    sys.stdout=Tee(saved_stdout);sys.stderr=Tee(saved_stderr)
    try:
        with open('/tmp/ict-fsa-board-'+a.bdf+'.lock','a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            backend=runtime.Runtime(paths,a)
            if not Path(backend.F.__file__).resolve().is_relative_to(paths['software']):raise ValueError('Wrong FSA Python module imported')
            metadata['workload']=backend.prepare(out)
            # Preserve the exact original fp16 Torch reference used in earlier logs.
            from main import ref_torch
            torch_ref=ref_torch(backend.q,backend.k,backend.v)
            backend.np.save(out/'torch-reference.npy',torch_ref)
            backend.open_device();results=[]
            for i in range(a.warmup+a.repeat):
                sub=out/f'run-{i:03d}';sub.mkdir();r=backend.execute(sub,p['dut_mhz'])
                actual=backend.np.load(sub/'actual.npy')
                def metrics(arr):
                    np=backend.np;delta=arr-torch_ref
                    return {'MAE':float(np.mean(np.abs(delta))),'MSE':float(np.mean(delta**2)),'MaxErr':float(np.max(np.abs(delta))),'RelErr':float(np.mean(np.abs(delta/(torch_ref+1e-8))))}
                r.update(warmup=i<a.warmup,errors_vs_torch=metrics(actual),pyeasyfloat_errors_vs_torch=metrics(backend.ref))
                save(sub/'result.json',r);results.append(r)
                print('FSA vs Torch:',r['errors_vs_torch'],'FSA vs PyEasyFloat bit mismatches:',r['bit_mismatches'],flush=True)
                if not r['passed']:raise RuntimeError('Numerical/instruction-delta failure in '+str(sub))
            measured=results[a.warmup:]
            summary={'passed':True,'runs':results,'exec_us_median':statistics.median(r['exec_us'] for r in measured),'exec_us_min':min(r['exec_us'] for r in measured),'exec_us_max':max(r['exec_us'] for r in measured),'host_execute_ms_median':statistics.median(r['host_execute_ms'] for r in measured)}
            save(out/'result.json',summary);metadata['status']='completed'
    except BaseException as exc:
        metadata.update(status='failed_or_interrupted',error=str(exc));raise
    finally:
        if backend is not None:backend.close()
        save(out/'run.json',metadata)
        sys.stdout=saved_stdout;sys.stderr=saved_stderr;console.close()
    print('COMPLETE: saved inputs, instructions, actual/reference arrays, per-run counters and direct bit comparison at',out)

def summarize(a,p,root):
    fresh(a.out);rows=[]; groups={}
    for path in a.results:
        m=json.loads((path/'run.json').read_text());s=json.loads((path/'result.json').read_text())
        if m.get('status')!='completed' or not s.get('passed') or m.get('hardware_identity_kind')!='successful_programming_operation_not_hardware_identity_readback':raise ValueError('Unverified/incomplete test result: '+str(path))
        validate_receipt_data=m['program_receipt']
        if validate_receipt_data.get('status')!='programmed' or validate_receipt_data.get('bitstream_sha256')!=m['export']['bitstream']['sha256']:raise ValueError('Result has inconsistent programming provenance')
        measured=[r for r in s['runs'] if not r['warmup']]
        row={'profile':m['profile'],'seq':m['seq'],'seed':m['seed'],'runs':len(measured),'clock_mhz_assumed':m['clock_mhz_assumed'],'exec_ms_median':s['exec_us_median']/1000,'exec_ms_min':s['exec_us_min']/1000,'exec_ms_max':s['exec_us_max']/1000,'host_ms_median':s['host_execute_ms_median'],'bubble_pct_median':statistics.median(100*r['counters']['mxBubble']/r['counters']['execTime'] for r in measured),'RelErr':measured[0]['errors_vs_torch']['RelErr'],'speedup_vs_A70':None,'source_commit':m['source']['commit'],'input_identity':json.dumps(m['workload']['inputs'],sort_keys=True),'result':str(path.resolve())}
        # Profiles retain historical host differences. Never claim these ratios isolate clocks.
        rows.append(row);groups.setdefault((m['seq'],m['seed'],row['input_identity']),[]).append(row)
    for group in groups.values():
        bases=[r for r in group if r['profile']=='A70-P3']
        if len(bases)==1:
            for r in group:r['speedup_vs_A70']=bases[0]['exec_ms_median']/r['exec_ms_median']
    a.out.mkdir(parents=True)
    with (a.out/'results.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    save(a.out/'results.json',rows)
    lines=['# ICT-FSA 板测汇总','','时钟来自对应导出配置，烧录身份来自操作记录，没有硬件身份寄存器回读。各阶段原配主机软件可能不同；加速比是完整系统差异，不是纯提频收益。bubble 不是 PE 空闲率。','','| Profile | Seq | 次数 | 执行中位数 ms | 范围 ms | bubble % | RelErr | 相对 A70 |','|---|---:|---:|---:|---|---:|---:|---:|']
    for r in rows:lines.append(f"| {r['profile']} | {r['seq']} | {r['runs']} | {r['exec_ms_median']:.6f} | {r['exec_ms_min']:.6f}–{r['exec_ms_max']:.6f} | {r['bubble_pct_median']:.3f} | {r['RelErr']:.8g} | {r['speedup_vs_A70'] if r['speedup_vs_A70'] else '—'} |")
    (a.out/'README.md').write_text('\n'.join(lines)+'\n');print('SAVED:',a.out/'README.md')
