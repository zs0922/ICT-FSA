# Board experiments: do not waive DRC or declare CDC/release acceptance.
if {$argc != 5} {error "Expected DCP NEW_EXPERIMENT_DIR DUT_MHZ BIT_PATH STA_DUT_PERIOD_NS"}
lassign $argv dcp out mhz bit expected_period
set_param general.maxThreads 4
open_checkpoint $dcp
report_timing_summary -file [file join $out timing.txt]
report_route_status -file [file join $out route-status.txt]
report_bus_skew -file [file join $out bus-skew.txt]
report_utilization -file [file join $out utilization.txt]
report_clocks -file [file join $out clocks.txt]
report_cdc -details -file [file join $out cdc.txt]
check_timing -verbose -file [file join $out check-timing.txt]
report_exceptions -file [file join $out exceptions.txt]
report_drc -file [file join $out drc.txt]
# Strict setup/hold guard for the DUT and every timed clock group.
set dut [get_clocks clk_out1_harnessSysPLL]
if {[llength $dut] != 1 || abs([get_property PERIOD $dut] - $expected_period) > 0.001} {
    error "Expected exactly one $mhz MHz DUT clock"
}
set fd [open [file join $out clock-observed.json] w]
puts $fd "\{"
puts $fd [format {"nominal_dut_mhz": %s, "sta_period_ns": %s, "sta_frequency_mhz": %s} $mhz [get_property PERIOD $dut] [expr {1000.0/[get_property PERIOD $dut]}]]
puts $fd "\}"
close $fd
report_timing -from $dut -to $dut -delay_type max -max_paths 100 -input_pins -nets -file [file join $out dut_setup_top100.txt]
report_timing -from $dut -to $dut -delay_type min -max_paths 100 -input_pins -nets -file [file join $out dut_hold_top100.txt]
foreach kind {max min} {
    set paths [get_timing_paths -delay_type $kind -max_paths 1]
    if {[llength $paths] == 0 || [get_property SLACK $paths] < 0} { error "Global $kind timing failed" }
    set paths [get_timing_paths -from $dut -to $dut -delay_type $kind -max_paths 1]
    if {[llength $paths] == 0 || [get_property SLACK $paths] < 0} { error "DUT $kind timing failed" }
}
# The primitive minimum-period and high/low pulse-width rules are independent
# of register-to-register setup/hold. This guard also protects direct DCP export.
set summary [report_timing_summary -return_string -max_paths 1]
if {![regexp {WNS\(ns\)[^\n]*\n\s*-+[^\n]*\n\s*([^\n]+)} $summary ignored row]} {
    error "Missing global timing summary including pulse-width checks"
}
set values [regexp -all -inline {\S+} $row]
if {[llength $values] != 12} {error "Unexpected timing summary: $row"}
foreach index {0 4 8} {
    set value [lindex $values $index]
    if {![string is double -strict $value] || $value < 0} {error "Global setup/hold/pulse-width violation: $row"}
}
foreach index {1 2 5 6 9 10} {
    if {[lindex $values $index] != 0} {error "Global timing failing endpoints: $row"}
}

set bad [get_drc_violations -quiet -filter {SEVERITY == Error || SEVERITY == {Critical Warning}}]
if {[llength $bad]} {error "DRC errors or critical warnings prohibit export: $bad"}
set_property BITSTREAM.Config.SPI_buswidth 8 [current_design]
write_bitstream $bit
close_design
exit
