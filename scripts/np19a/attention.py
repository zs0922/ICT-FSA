#!/usr/bin/env python3
"""Explicit NP19A board experiment; a supplied bit filename is NOT programming evidence."""
import argparse,hashlib,json,re,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--config',type=Path,required=True);p.add_argument('--bit',type=Path,required=True)
 p.add_argument('--device',required=True);p.add_argument('--bdf',required=True)
 p.add_argument('--seq',type=int,default=16);p.add_argument('--seed',type=int,default=0)
 p.add_argument('--out',type=Path,required=True);p.add_argument('--dry-run',action='store_true')
 a=p.parse_args()
 if not re.fullmatch(r'xdma\d+',a.device) or not re.fullmatch(r'[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7]',a.bdf):p.error('Invalid XDMA device/BDF')
 c=json.loads(a.config.read_text())
 if (c['sa_rows'],c['sa_cols'],c['mem_base'],c['mem_size'],c['mem_align'])!=(16,16,0,1<<34,32):p.error('Not the generated NP19A baseline config')
 if a.seq<=0 or a.seq%16:p.error('seq must be a positive multiple of 16')
 if a.out.exists():p.error('Output exists; choose a new attempt')
 if not a.bit.is_file() or not a.bit.stat().st_size:p.error('Missing bitstream')
 meta={'profile':'NP19A','seq':a.seq,'seed':a.seed,'device':a.device,'bdf':a.bdf,'config_sha256':sha(a.config),'bit_sha256':sha(a.bit),'programming_identity':'operator supplied; not hardware verified','nominal_clock_mhz':70}
 if a.dry_run:print(json.dumps(meta,indent=2));print('DRY RUN: no hardware accessed');return
 # Check all three nodes identify the selected PCI function before opening hardware.
 for suffix in ['user','h2c_0','c2h_0']:
  node=Path('/sys/class/xdma')/(a.device+'_'+suffix)/'device'
  if not node.exists() or a.bdf.lower() not in str(node.resolve()).lower().split('/'):
   p.error(f'Cannot bind {node} to {a.bdf}; inspect sysfs mapping before testing')
 sys.path.insert(0,str(ROOT/'generators/fsa/python'));sys.path.insert(0,str(ROOT/'generators/easyfloat'))
 import numpy as np
 import fsa as F
 from main import scaled_dot_product_attention,ref_pyeasyfloat,ref_torch
 F.init(str(a.config.resolve()));a.out.mkdir(parents=True)
 meta['status']='running';(a.out/'result.json').write_text(json.dumps(meta,indent=2)+'\n')
 np.random.seed(a.seed);q,k,v=[np.random.rand(a.seq,16).astype(np.float16) for _ in range(3)]
 for n,x in [('q',q),('k',k),('v',v)]:np.save(a.out/(n+'.npy'),x)
 engine=F.FPGA(control_dev=f'/dev/{a.device}_user',mem_read_dev=f'/dev/{a.device}_c2h_0',mem_write_dev=f'/dev/{a.device}_h2c_0')
 t=time.monotonic();result=engine.execute(scaled_dot_product_attention(F.from_numpy(q),F.from_numpy(k),F.from_numpy(v.T),16,16));meta['host_execute_seconds']=time.monotonic()-t
 actual=np.ascontiguousarray(F.to_numpy(result).T);ref=np.ascontiguousarray(ref_pyeasyfloat(q,k,v,16,16,False));torch=ref_torch(q,k,v)
 for n,x in [('actual',actual),('pyeasyfloat',ref),('torch',torch)]:np.save(a.out/(n+'.npy'),x)
 meta['bitwise_equal_pyeasyfloat']=bool(np.array_equal(actual.view(np.uint32),ref.view(np.uint32)))
 d=actual-torch
 meta['errors_vs_torch']={'MAE':float(np.abs(d).mean()),'MSE':float((d*d).mean()),'MaxErr':float(np.abs(d).max()),'RelErr':float(np.mean(np.abs(d/(torch+1e-8))))}
 meta['relerr_definition']='mean(abs((actual-reference)/(reference+1e-8))); original fsa.utils definition'
 meta['counters']={n:int(engine.MMIO.dev_mmio_read(o)) for n,o in [('execTime',0xc),('mxBubble',0x10),('mxActive',0x14),('dmaActive',0x18),('rawInst',0x1c),('mxInst',0x20),('dmaInst',0x24),('fenceInst',0x28),('enq',0x2c),('deq',0x30)]}
 meta['status']='passed' if meta['bitwise_equal_pyeasyfloat'] else 'numerical_mismatch'
 (a.out/'result.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2))
 if not meta['bitwise_equal_pyeasyfloat']:raise SystemExit(1)
if __name__=='__main__':main()
