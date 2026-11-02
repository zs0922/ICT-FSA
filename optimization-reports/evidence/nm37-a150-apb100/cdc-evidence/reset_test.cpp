#include "VResetWrangler.h"
#include "verilated.h"
#include <cstdio>
#include <cstdlib>
int main(int argc,char**argv) {
 Verilated::commandArgs(argc,argv);
 unsigned scenarios=0;
 for(int source=0;source<3;source++) for(int phase=0;phase<8;phase++) {
  VResetWrangler d;
  int ticks=0; bool prev_apb=false; bool released[3]={};
  // Reset once, interrupt debounce at 4000 time units, then release again.
  const int release1=121+phase, assert2=4001+phase, release2=4121+phase;
  for(int t=0;t<305000;t++) {
   bool rst=t<release1 || (t>=assert2 && t<release2);
   d.auto_in_0_clock=(t/10)%2; d.auto_in_1_clock=(t/15)%2; d.auto_in_2_clock=(t/6)%2;
   d.auto_in_0_reset=rst && source==0;
   d.auto_in_1_reset=rst && source==1;
   d.auto_in_2_reset=rst && source==2;
   bool rise=d.auto_in_1_clock&&!prev_apb; prev_apb=d.auto_in_1_clock;
   if(rst) {ticks=0;for(auto &x:released)x=false;} else if(rise)ticks++;
   d.eval();
   bool outputs[]={bool(d.auto_out_0_reset),bool(d.auto_out_1_reset),bool(d.auto_out_2_reset)};
   for(int i=0;i<3;i++) {
    if((rst || ticks<=10000) && !outputs[i]) {std::fprintf(stderr,"early release source=%d phase=%d t=%d ticks=%d domain=%d\n",source,phase,t,ticks,i);return 1;}
    if(!outputs[i])released[i]=true;
    if(released[i] && outputs[i] && !rst) return 2;
   }
   if(t==304999)for(bool x:released)if(!x)return 3;
  }
  scenarios++;
 }
 std::printf("PASS: %u reset source/phase scenarios, interrupted debounce restart, no early release, all three domains release and remain released. Digital RTL only; no metastability model.\n",scenarios);
}
