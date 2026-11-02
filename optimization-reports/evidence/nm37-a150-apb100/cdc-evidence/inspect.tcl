set_param general.maxThreads 4
open_checkpoint [lindex $argv 0]
set out [lindex $argv 1]
set f [open "$out/routed-structure.txt" w]
set regs [get_cells -hier -filter {NAME =~ wrangler/debounced_debounce/reg_0_reg*}]
if {[llength $regs] != 14} {error "Expected 14 debounce registers"}
foreach c [lsort $regs] {
 puts $f "CELL $c REF=[get_property REF_NAME $c] INIT=[get_property INIT $c]"
 foreach p {C CE CLR} {
  set pin [get_pins "$c/$p"]
  puts $f "  $p NET=[get_nets -of_objects $pin] DRIVERS=[all_fanin -flat -startpoints_only -to $pin]"
 }
}
foreach pattern {wrangler/deglitched_deglitch/reg_0_reg wrangler/nodeOut_reset_catcher*/io_sync_reset_chain/output_chain/sync*} {
 foreach c [lsort [get_cells -hier -filter "NAME =~ $pattern"]] {
  puts $f "CHAIN $c REF=[get_property REF_NAME $c] ASYNC_REG=[get_property ASYNC_REG $c]"
  foreach p {C D CLR PRE} {
   set pin [get_pins -quiet "$c/$p"]
   if {[llength $pin]} {puts $f "  $p NET=[get_nets -of_objects $pin] DRIVERS=[all_fanin -flat -startpoints_only -to $pin]"}
  }
 }
}
close $f
close_design
exit
