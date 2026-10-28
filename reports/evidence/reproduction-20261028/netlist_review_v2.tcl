# Read-only diagnostics, not an acceptance waiver. Outputs must be new.
# vivado -mode batch -source netlist_review.tcl -tclargs DCP OUT [CDC_PINS_TXT]
if {$argc < 2 || $argc > 3} { error "Expected DCP OUT optional-CDC_PINS_TXT" }
set checkpoint [file normalize [lindex $argv 0]]
set destination [file normalize [lindex $argv 1]]
if {![file isfile $checkpoint]} {error "Missing checkpoint: $checkpoint"}
if {[file exists $destination]} {error "Preserve existing output; select a new directory: $destination"}
file mkdir $destination
set_param general.maxThreads 4
open_checkpoint $checkpoint
report_utilization -file [file join $destination utilization_flat.txt]
proc exact_pin {name} {
    return [get_pins -hier -quiet -filter [format {NAME == "%s"} $name]]
}
proc describe {fd label objects properties} {
    puts $fd "$label count=[llength $objects]"
    foreach object $objects {
        puts $fd "  object=$object"
        set available [list_property $object]
        foreach property $properties {
            if {[lsearch -exact $available $property] >= 0} {
                puts $fd "    $property=[get_property $property $object]"
            }
        }
    }
}
set fd [open [file join $destination unused_hbm_pins.txt] w]
puts $fd "checkpoint=$checkpoint"
set count 0
for {set i 1} {$i < 16} {incr i} {
    foreach port {BREADY RREADY} {
        set name [format {dutDomain/ram_hbm/inst/ONE_STACK.u_hbm_top/ONE_STACK_HBM.hbm_one_stack_intf/HBM_SNGLBLI_INTF_AXI<%d>_INST/%s} $i $port]
        set pins [exact_pin $name]
        if {[llength $pins] != 1} { error "Expected exactly one $name" }
        incr count
        puts $fd "ENDPOINT $name"
        describe $fd pin $pins {DIRECTION REF_PIN_NAME IS_CONNECTED}
        set nets [get_nets -quiet -of_objects $pins]
        describe $fd net $nets {TYPE IS_GND IS_VCC IS_CONSTANT ROUTE_STATUS}
        set drivers [get_pins -quiet -of_objects $nets -filter {DIRECTION == OUT}]
        describe $fd drivers $drivers {DIRECTION REF_PIN_NAME}
        describe $fd driver_cells [get_cells -quiet -of_objects $drivers] {REF_NAME PRIMITIVE_TYPE}
        if {$port eq "BREADY"} {
            # check_timing classifies these endpoints as clocked by a constant.
            set owner [get_cells -quiet -of_objects $pins]
            set clocks {}
            foreach p [get_pins -quiet -of_objects $owner -filter {DIRECTION == IN}] {
                if {[regexp -nocase {clk|clock} [get_property REF_PIN_NAME $p]]} {lappend clocks $p}
            }
            describe $fd hbm_clock_pins $clocks {REF_PIN_NAME IS_CLOCK}
            set clock_nets [get_nets -quiet -of_objects $clocks]
            describe $fd hbm_clock_nets $clock_nets {TYPE IS_GND IS_VCC IS_CONSTANT}
            set clock_drivers [get_pins -quiet -of_objects $clock_nets -filter {DIRECTION == OUT}]
            describe $fd hbm_clock_drivers $clock_drivers {REF_PIN_NAME}
            describe $fd hbm_clock_driver_cells [get_cells -quiet -of_objects $clock_drivers] {REF_NAME PRIMITIVE_TYPE}
        }
        if {[catch {all_fanin -flat -startpoints_only -to $pins} fanin]} {
            puts $fd "fanin_query_error=$fanin"
        } else { describe $fd fanin $fanin {DIRECTION REF_PIN_NAME} }
    }
}
puts $fd "observed_endpoints=$count"
close $fd
set fd [open [file join $destination external_reset.txt] w]
set ports [get_ports -quiet prst_n]
describe $fd ports $ports {DIRECTION PACKAGE_PIN IOSTANDARD}
if {[llength $ports]} {
    set endpoints [all_fanout -flat -endpoints_only -from $ports]
    puts $fd "endpoint_count=[llength $endpoints]"
    describe $fd first_100_endpoints [lrange $endpoints 0 99] {DIRECTION REF_PIN_NAME}
}
close $fd
if {$argc == 3} {
    set input [open [lindex $argv 2] r]
    set names [split [string trim [read $input]] "\n"]
    close $input
    set fd [open [file join $destination cdc_endpoint_cones.txt] w]
    foreach name [lsort -unique $names] {
        set name [string trim $name]
        if {$name eq ""} {continue}
        puts $fd "ENDPOINT $name"
        set pins [exact_pin $name]
        if {[llength $pins] != 1} {error "Expected exactly one CDC pin $name"}
        describe $fd pins $pins {DIRECTION REF_PIN_NAME}
        set cells [get_cells -quiet -of_objects $pins]
        describe $fd cells $cells {REF_NAME ASYNC_REG DONT_TOUCH LOC BEL INIT}
        set cpins [get_pins -quiet -of_objects $cells -filter {IS_CLOCK == 1}]
        describe $fd clocks [get_clocks -quiet -of_objects $cpins] {PERIOD WAVEFORM IS_GENERATED MASTER_CLOCK}
        set starts [all_fanin -flat -startpoints_only -to $pins]
        describe $fd fanin $starts {DIRECTION REF_PIN_NAME}
        describe $fd fanin_cells [get_cells -quiet -of_objects $starts] {REF_NAME ASYNC_REG DONT_TOUCH LOC BEL INIT}
        foreach p [get_pins -quiet -of_objects $cells] {
            # foreach returns a Tcl name; resolve to a typed Vivado pin before querying.
            set pin_object [get_pins -quiet -of_objects $cells -filter [format {NAME == "%s"} $p]]
            if {[llength $pin_object] != 1} {error "Expected one pin in cell: $p"}
            describe $fd cell_pin $pin_object {DIRECTION REF_PIN_NAME}
            set nets [get_nets -quiet -of_objects $pin_object]
            describe $fd net $nets {TYPE IS_GND IS_VCC IS_CONSTANT ROUTE_STATUS}
            describe $fd net_drivers [get_pins -quiet -of_objects $nets -filter {DIRECTION == OUT}] {REF_PIN_NAME}
        }
    }
    close $fd
}
set fd [open [file join $destination exception_objects.txt] w]
for {set i 0} {$i < 8} {incr i} {
    puts $fd "CPLL_LANE $i"
    set starts [get_cells -hier -quiet -filter [format {NAME =~ *gen_cpll_cal_inst[%d].*U_TXOUTCLK_FREQ_COUNTER/testclk_cnt_reg*} $i]]
    set ends [get_cells -hier -quiet -filter [format {NAME =~ *gen_cpll_cal_inst[%d].*U_TXOUTCLK_FREQ_COUNTER/freq_cnt_o_reg*} $i]]
    describe $fd starts $starts {REF_NAME PRIMITIVE_TYPE ASYNC_REG LOC}
    describe $fd ends $ends {REF_NAME PRIMITIVE_TYPE ASYNC_REG LOC}
}
set old_addr [get_cells -hier -quiet -filter {NAME =~ *sram_accRAM_fullWrite_0_addr_REG*}]
set all_addr [get_cells -hier -quiet -filter {NAME =~ *sram_accRAM_fullWrite_0_addr*}]
describe $fd obsolete_addr_constraint_target $old_addr {REF_NAME MAX_FANOUT}
describe $fd actual_addr_cells $all_addr {REF_NAME MAX_FANOUT}
close $fd
set fd [open [file join $destination context.txt] w]
puts $fd "checkpoint=$checkpoint"
puts $fd "sha256=[lindex [exec sha256sum -- $checkpoint] 0]"
puts $fd "part=[get_property PART [current_design]]"
puts $fd "scope=read-only structural diagnostics; no acceptance verdict; no constraints changed"
close $fd
close_design
exit
