# Explicit volatile SRAM programming, no flash erase/program operations.
if {$argc != 5} {error "Expected SERVER EXACT_TARGET EXACT_DEVICE BIT_PATH EXPECTED_PART"}
lassign $argv server targetName deviceName bit expectedPart
open_hw_manager
connect_hw_server -url $server
set matches {}
foreach target [get_hw_targets] {
    if {[get_property NAME $target] eq $targetName} {lappend matches $target}
}
if {[llength $matches] != 1} {error "Exact JTAG target not found once; use Hardware Manager to identify it"}
current_hw_target [lindex $matches 0]
open_hw_target
set matches {}
foreach dev [get_hw_devices] {
    if {[get_property NAME $dev] eq $deviceName} {lappend matches $dev}
}
if {[llength $matches] != 1} {error "Exact device not found once on selected JTAG target"}
set dev [lindex $matches 0]
if {$expectedPart ne "" && [get_property PART $dev] ne $expectedPart} {error "Unexpected FPGA part"}
set_property PROGRAM.FILE $bit $dev
program_hw_devices $dev
refresh_hw_device $dev
puts "ICT_FSA_PROGRAM_COMMAND_COMPLETED"
close_hw_target
disconnect_hw_server
close_hw_manager
