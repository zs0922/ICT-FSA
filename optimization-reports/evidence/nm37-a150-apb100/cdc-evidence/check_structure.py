from pathlib import Path
import re
p=Path(__file__).resolve().parent
s=(p/'routed-structure.txt').read_text()
blocks=re.findall(r'^CELL ([^\n]+)\n(.*?)(?=^CELL |^CHAIN |\Z)',s,re.M|re.S)
assert len(blocks)==14
for header,body in blocks:
 assert "REF=FDCE INIT=1'b0" in header
 for pin in ('C','CE','CLR'):
  assert re.search(r'^  '+pin+r' .*$',body,re.M).group()==re.search(r'^  '+pin+r' .*$',blocks[0][1],re.M).group()
for suffix in ('','_1','_2'):
 root='wrangler/nodeOut_reset_catcher'+suffix+'/io_sync_reset_chain/output_chain/'
 for bit in range(3):
  match=re.search(r'^CHAIN '+re.escape(root+f'sync_{bit}_reg')+r' [^\n]*\n(.*?)(?=^CHAIN |\Z)',s,re.M|re.S)
  assert match
  b=match[1]
  assert 'CLR ' in b and 'DRIVERS=wrangler/deglitched_deglitch/reg_0_reg/C' in b
  if bit<2: assert root+f'sync_{bit+1}_reg/C' in b
  else: assert '<const1>' in b
print('PASS: 14 FDCEs share clock/enable/async-clear; three output domains retain three-stage release chains.')
