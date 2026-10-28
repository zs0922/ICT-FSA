# Execute the actual reset/reaudit frequency guards with mocked Vivado queries.
set here [file dirname [file normalize [info script]]]
source $here/reset_audit.tcl
set dutclk clk_out1_harnessSysPLL
set clock_result $dutclk
set period [expr {1000.0/120.0}]
proc get_clocks {args} {return $::clock_result}
proc get_property {property object} {
 if {$property ne {PERIOD}} {error "unexpected property $property"}
 return $::period
}
proc get_cells {args} {return {wrangler/dut/io_sync_reset_chain/output_chain/sync_2_reg}}
proc get_pins {args} {return {wrangler/dut/io_sync_reset_chain/output_chain/sync_2_reg/C}}
set f [open $here/reaudit.tcl r]
set code [read $f];close $f
set start [string first {set dut [get_clocks -quiet clk_out1_harnessSysPLL]} $code]
set stop [string first {report_bus_skew} $code $start]
if {$start < 0 || $stop < $start} {error "Could not isolate actual reaudit clock guard"}
set reaudit_guard [string range $code $start [expr {$stop-1}]]
set count 0
foreach mode {reset reaudit} {
 foreach {freq expected} {120 1 110 0 100 0 60 0} {
  set period [expr {1000.0/$freq}]
  set clock_result $dutclk
  set reset_audit::stem {}
  if {$mode eq {reset}} {set failed [catch {reset_audit::select_dut} message]} else {set failed [catch {eval $reaudit_guard} message]}
  if {!$failed != $expected} {error "$mode $freq MHz: expected acceptance=$expected, got $message"}
  if {$failed && ![string match {*120 MHz*} $message]} {error "Unexpected rejection: $message"}
  incr count
 }
 foreach clocks [list {} [list $dutclk another_clock]] {
  set clock_result $clocks
  set period [expr {1000.0/120.0}]
  set reset_audit::stem {}
  if {$mode eq {reset}} {set failed [catch {reset_audit::select_dut} message]} else {set failed [catch {eval $reaudit_guard} message]}
  if {!$failed} {error "$mode accepted missing/ambiguous clock"}
  incr count
 }
}
puts "PASS: $count actual A120 clock guard positive/negative cases"
