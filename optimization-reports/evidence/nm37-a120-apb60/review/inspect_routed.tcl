# Read-only examination. No clock changes, optimization, routing or DCP writes.
if {$argc != 2} { error "usage: inspect_routed.tcl routed.dcp new-output-directory" }
set input [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
if {[file exists $out]} { error "output must be new" }
file mkdir $out
set_param general.maxThreads 8
open_checkpoint $input
set dut [get_clocks clk_out1_harnessSysPLL]
if {[llength $dut] != 1} { error "one DUT clock required" }
set paths [get_timing_paths -from $dut -to $dut -delay_type max -max_paths 1000 -nworst 1]
report_timing -from $dut -to $dut -delay_type max -max_paths 1000 -nworst 1 -input_pins -nets -file $out/dut_setup_top1000.rpt
report_timing_summary -delay_type min_max -max_paths 10 -report_unconstrained -file $out/timing_summary.rpt
report_clocks -file $out/clocks.rpt
report_utilization -file $out/utilization_flat.rpt
set apb_primitive [get_cells -quiet -hier -filter {REF_NAME == HBM_SNGLBLI_INTF_APB}]
if {[llength $apb_primitive] != 1} {error "Expected one HBM APB primitive"}
set apb_pin [get_pins -quiet -of_objects $apb_primitive -filter {REF_PIN_NAME == PCLK}]
if {[llength $apb_pin] != 1} {error "Expected one HBM APB PCLK"}
set apb_clock [get_clocks -quiet -of_objects $apb_pin]
if {[llength $apb_clock] != 1} {error "Expected one APB clock"}
report_pulse_width -clocks $apb_clock -limit 100 -significant_digits 3 -file $out/pulse_width.rpt $apb_pin
report_property [lindex $paths 0] -file $out/first_path_properties.rpt
set f [open $out/path_locations.tsv w]
puts $f "rank\tslack_ns\tstart\tend\tstart_loc\tend_loc\tendpoint_slrs"
set rank 0
foreach p $paths {
 incr rank
 set start [get_property STARTPOINT_PIN $p]
 set end [get_property ENDPOINT_PIN $p]
 set sc [get_cells -quiet -of_objects [get_pins -quiet $start]]
 set ec [get_cells -quiet -of_objects [get_pins -quiet $end]]
 set slrs [lsort -unique [get_slrs -quiet -of_objects [concat $sc $ec]]]
 puts $f "$rank\t[get_property SLACK $p]\t$start\t$end\t[get_property LOC $sc]\t[get_property LOC $ec]\t$slrs"
}
close $f
set r [open $out/dut_setup_top1000.rpt r]
set report [read $r]; close $r
set f [open $out/site_slrs.tsv w]
puts $f "site\tslr"
foreach site [lsort -unique [regexp -all -inline {SLICE_X[0-9]+Y[0-9]+} $report]] {
 puts $f "$site\t[get_slrs -quiet -of_objects [get_sites $site]]"
}
close $f
# Independent cones keep top1000 domination by one arithmetic cone from hiding others.
foreach {label pattern} {
 pe_fma *sa/mesh_*/macUnit/mulAddExp2/fma/*
 accumulator *accumulator*
 scratchpad *spRAM*
 reset *sync_0_reg_replica*
} {
 set cells [get_cells -quiet -hier -filter "NAME =~ $pattern && IS_SEQUENTIAL == 1"]
 if {[llength $cells]} {
  report_timing -from $cells -delay_type max -max_paths 20 -nworst 1 -input_pins -nets -file $out/from_${label}.rpt
 }
}
close_design
set f [open $out/complete.txt w]; puts $f "read-only diagnostics complete"; close $f
