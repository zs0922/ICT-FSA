# NP19A single-SODIMM shell. Source: user schematic/XDC and pinned NEXST board example.
# No CPU, PCIe root ports, HBM or optimization-stage arithmetic changes.
if {$argc != 2} {error "usage: implement.tcl BUILD ROOT"}
lassign $argv build root
set_param general.maxThreads 8
set obj [file join $build obj]
if {[file exists $obj]} {error "Output exists: $obj; preserve it and choose a fresh attempt"}
file mkdir $obj
create_project np19a [file join $obj project] -part xcvu19p-fsva3824-2-e
set_property target_language Verilog [current_project]
set fd [open [lindex [glob $build/*.vsrcs.f] 0] r]
set sources [split [read $fd] \n];close $fd
foreach f $sources {if {[string trim $f] ne ""} {add_files -norecurse $f}}
add_files -norecurse [file join $build fsa_axi_wrapper.v]
create_bd_design np19a
set fsa [create_bd_cell -type module -reference fsa_axi_wrapper fsa]
set clk [create_bd_intf_port -mode Slave -vlnv xilinx.com:interface:diff_clock_rtl:1.0 ddr4_mig_sys_clk]
set_property CONFIG.FREQ_HZ 100000000 $clk
set ref [create_bd_intf_port -mode Slave -vlnv xilinx.com:interface:diff_clock_rtl:1.0 pcie_ep_gt_ref_clk]
set_property CONFIG.FREQ_HZ 100000000 $ref
create_bd_port -dir I -type rst pcie_ep_perstn
set_property CONFIG.POLARITY ACTIVE_LOW [get_bd_ports pcie_ep_perstn]
foreach n {rxn rxp} {create_bd_port -dir I -from 7 -to 0 pcie_ep_$n}
foreach n {txn txp} {create_bd_port -dir O -from 7 -to 0 pcie_ep_$n}
create_bd_intf_port -mode Master -vlnv xilinx.com:interface:ddr4_rtl:1.0 c0_ddr4
set sysbuf [create_bd_cell -type ip -vlnv xilinx.com:ip:util_ds_buf:2.2 sysbuf]
set_property CONFIG.C_BUF_TYPE IBUFDS $sysbuf
connect_bd_intf_net $clk [get_bd_intf_pins sysbuf/CLK_IN_D]
set gtbuf [create_bd_cell -type ip -vlnv xilinx.com:ip:util_ds_buf:2.2 gtbuf]
set_property CONFIG.C_BUF_TYPE IBUFDSGTE $gtbuf
connect_bd_intf_net $ref [get_bd_intf_pins gtbuf/CLK_IN_D]
set inv [create_bd_cell -type ip -vlnv xilinx.com:ip:util_vector_logic:2.0 perst_inv]
set_property -dict [list CONFIG.C_OPERATION not CONFIG.C_SIZE 1] $inv
connect_bd_net [get_bd_ports pcie_ep_perstn] [get_bd_pins perst_inv/Op1]
set mig [create_bd_cell -type ip -vlnv xilinx.com:ip:ddr4:2.2 ddr4_mig]
set_property -dict [list CONFIG.C0.DDR4_isCustom false CONFIG.C0.DDR4_AxiSelection true CONFIG.C0.DDR4_AxiAddressWidth 34 CONFIG.C0.DDR4_AxiDataWidth 512 CONFIG.C0.DDR4_Clamshell false CONFIG.C0.DDR4_DataMask DM_NO_DBI CONFIG.C0.DDR4_DataWidth 64 CONFIG.C0.DDR4_Ecc false CONFIG.C0.DDR4_InputClockPeriod 10005 CONFIG.C0.DDR4_TimePeriod 938 CONFIG.C0.DDR4_MemoryType SODIMMs CONFIG.C0.DDR4_MemoryPart MTA16ATF2G64HZ-2G3 CONFIG.C0.DDR4_CasLatency 15 CONFIG.C0.DDR4_AxiNarrowBurst true CONFIG.System_Clock No_Buffer] $mig
connect_bd_intf_net [get_bd_intf_ports c0_ddr4] [get_bd_intf_pins ddr4_mig/C0_DDR4]
connect_bd_net [get_bd_pins sysbuf/IBUF_OUT] [get_bd_pins ddr4_mig/c0_sys_clk_i]
connect_bd_net [get_bd_pins perst_inv/Res] [get_bd_pins ddr4_mig/sys_rst]
set pll [create_bd_cell -type ip -vlnv xilinx.com:ip:clk_wiz:6.0 harnessSysPLL]
set_property -dict [list CONFIG.PRIM_IN_FREQ 100 CONFIG.CLKOUT1_REQUESTED_OUT_FREQ 70 CONFIG.USE_RESET true] $pll
connect_bd_net [get_bd_pins sysbuf/IBUF_OUT] [get_bd_pins harnessSysPLL/clk_in1]
connect_bd_net [get_bd_pins perst_inv/Res] [get_bd_pins harnessSysPLL/reset]
set xd [create_bd_cell -type ip -vlnv xilinx.com:ip:xdma:4.1 xdma_ep]
set_property -dict [list CONFIG.functional_mode DMA CONFIG.mode_selection Advanced CONFIG.pcie_blk_locn PCIE4C_X0Y2 CONFIG.en_gt_selection true CONFIG.select_quad GTY_Quad_226 CONFIG.pl_link_cap_max_link_width X8 CONFIG.pl_link_cap_max_link_speed 8.0_GT/s CONFIG.xdma_axi_intf_mm AXI_Memory_Mapped CONFIG.axi_data_width 256_bit CONFIG.axilite_master_en true CONFIG.axilite_master_size 1 CONFIG.axilite_master_scale Megabytes CONFIG.pciebar2axibar_axil_master 0x00000000 CONFIG.axist_bypass_en false CONFIG.cfg_mgmt_if false CONFIG.xdma_rnum_chnl 1 CONFIG.xdma_wnum_chnl 1 CONFIG.pf0_base_class_menu Processing_accelerators CONFIG.pf0_sub_class_interface_menu Unknown] $xd
connect_bd_net [get_bd_pins gtbuf/IBUF_DS_ODIV2] [get_bd_pins xdma_ep/sys_clk]
connect_bd_net [get_bd_pins gtbuf/IBUF_OUT] [get_bd_pins xdma_ep/sys_clk_gt]
connect_bd_net [get_bd_ports pcie_ep_perstn] [get_bd_pins xdma_ep/sys_rst_n]
foreach n {rxn rxp txn txp} {connect_bd_net [get_bd_ports pcie_ep_$n] [get_bd_pins xdma_ep/pci_exp_$n]}
set zero [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 zero]
set_property CONFIG.CONST_VAL 0 $zero
set one [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 one]
set_property CONFIG.CONST_VAL 1 $one
foreach p {usr_irq_req} {if {[llength [get_bd_pins -quiet xdma_ep/$p]]} {connect_bd_net [get_bd_pins zero/dout] [get_bd_pins xdma_ep/$p]}}
# MIG calibration and XDMA reset readiness are asynchronous to the core;
# proc_sys_reset synchronizes release to each destination clock.
set ready [create_bd_cell -type ip -vlnv xilinx.com:ip:util_vector_logic:2.0 ready]
set_property -dict [list CONFIG.C_OPERATION and CONFIG.C_SIZE 1] $ready
connect_bd_net [get_bd_pins ddr4_mig/c0_init_calib_complete] [get_bd_pins ready/Op1]
connect_bd_net [get_bd_pins xdma_ep/axi_aresetn] [get_bd_pins ready/Op2]
set notready [create_bd_cell -type ip -vlnv xilinx.com:ip:util_vector_logic:2.0 notready]
set_property -dict [list CONFIG.C_OPERATION not CONFIG.C_SIZE 1] $notready
connect_bd_net [get_bd_pins ready/Res] [get_bd_pins notready/Op1]
foreach domain {core mig} {
 set rst [create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 ${domain}_reset]
 connect_bd_net [get_bd_pins one/dout] [get_bd_pins ${domain}_reset/aux_reset_in]
 connect_bd_net [get_bd_pins zero/dout] [get_bd_pins ${domain}_reset/mb_debug_sys_rst]
}
connect_bd_net [get_bd_pins harnessSysPLL/clk_out1] [get_bd_pins core_reset/slowest_sync_clk] [get_bd_pins fsa/aclk]
connect_bd_net [get_bd_pins harnessSysPLL/locked] [get_bd_pins core_reset/dcm_locked]
connect_bd_net [get_bd_pins notready/Res] [get_bd_pins core_reset/ext_reset_in]
connect_bd_net [get_bd_pins core_reset/peripheral_aresetn] [get_bd_pins fsa/aresetn]
connect_bd_net [get_bd_pins ddr4_mig/c0_ddr4_ui_clk] [get_bd_pins mig_reset/slowest_sync_clk]
connect_bd_net [get_bd_pins ddr4_mig/c0_init_calib_complete] [get_bd_pins mig_reset/dcm_locked]
connect_bd_net [get_bd_pins ddr4_mig/c0_ddr4_ui_clk_sync_rst] [get_bd_pins mig_reset/ext_reset_in]
connect_bd_net [get_bd_pins mig_reset/peripheral_aresetn] [get_bd_pins ddr4_mig/c0_ddr4_aresetn]
# SmartConnect converts widths/protocols and includes asynchronous AXI crossing.
set mem [create_bd_cell -type ip -vlnv xilinx.com:ip:smartconnect:1.0 memory]
set_property -dict [list CONFIG.NUM_SI 2 CONFIG.NUM_MI 1 CONFIG.NUM_CLKS 3] $mem
connect_bd_intf_net [get_bd_intf_pins xdma_ep/M_AXI] [get_bd_intf_pins memory/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins fsa/m_axi] [get_bd_intf_pins memory/S01_AXI]
connect_bd_intf_net [get_bd_intf_pins memory/M00_AXI] [get_bd_intf_pins ddr4_mig/C0_DDR4_S_AXI]
connect_bd_net [get_bd_pins ddr4_mig/c0_ddr4_ui_clk] [get_bd_pins memory/aclk]
connect_bd_net [get_bd_pins xdma_ep/axi_aclk] [get_bd_pins memory/aclk1]
connect_bd_net [get_bd_pins harnessSysPLL/clk_out1] [get_bd_pins memory/aclk2]
connect_bd_net [get_bd_pins core_reset/interconnect_aresetn] [get_bd_pins memory/aresetn]
set ctl [create_bd_cell -type ip -vlnv xilinx.com:ip:smartconnect:1.0 control]
set_property -dict [list CONFIG.NUM_SI 1 CONFIG.NUM_MI 1 CONFIG.NUM_CLKS 2] $ctl
connect_bd_intf_net [get_bd_intf_pins xdma_ep/M_AXI_LITE] [get_bd_intf_pins control/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins control/M00_AXI] [get_bd_intf_pins fsa/s_axi]
connect_bd_net [get_bd_pins harnessSysPLL/clk_out1] [get_bd_pins control/aclk]
connect_bd_net [get_bd_pins xdma_ep/axi_aclk] [get_bd_pins control/aclk1]
connect_bd_net [get_bd_pins core_reset/interconnect_aresetn] [get_bd_pins control/aresetn]
assign_bd_address -offset 0x00000000 -range 0x400000000 -target_address_space [get_bd_addr_spaces xdma_ep/M_AXI] [get_bd_addr_segs ddr4_mig/C0_DDR4_MEMORY_MAP/C0_DDR4_ADDRESS_BLOCK]
assign_bd_address -offset 0x00000000 -range 0x400000000 -target_address_space [get_bd_addr_spaces fsa/m_axi] [get_bd_addr_segs ddr4_mig/C0_DDR4_MEMORY_MAP/C0_DDR4_ADDRESS_BLOCK]
assign_bd_address -offset 0x00000000 -range 0x00001000 -target_address_space [get_bd_addr_spaces xdma_ep/M_AXI_LITE] [get_bd_addr_segs fsa/s_axi/reg0]
validate_bd_design
# Check propagated reset polarity rather than overriding read-only derived fields.
foreach domain {core mig} {
 if {[get_property CONFIG.C_EXT_RESET_HIGH [get_bd_cells ${domain}_reset]] != 1} {error "${domain} external reset must be active high"}
 if {[get_property CONFIG.C_AUX_RESET_HIGH [get_bd_cells ${domain}_reset]] != 0} {error "${domain} inactive aux reset must be high (active low)"}
}
set props [open [file join $obj board-properties.txt] w]
foreach cell {ddr4_mig harnessSysPLL xdma_ep core_reset mig_reset memory control} {
 puts $props "CELL $cell"
 foreach key [lsort [list_property [get_bd_cells $cell]]] {
  if {[string match CONFIG.* $key]} {puts $props "$key = [get_property $key [get_bd_cells $cell]]"}
 }
}
close $props
save_bd_design
set bd [get_files */np19a.bd]
set_property synth_checkpoint_mode None $bd
generate_target all $bd
add_files -norecurse [make_wrapper -files $bd -top]
set_property top np19a_wrapper [current_fileset]
add_files -fileset constrs_1 -norecurse [file join $root scripts/np19a/top.xdc]
update_compile_order -fileset sources_1
write_bd_tcl -force [file join $obj generated-bd.tcl]
if {[info exists ::env(NP19A_BD_ONLY)]} {exit}
launch_runs synth_1 -jobs 8
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "synthesis failed"}
launch_runs impl_1 -to_step route_design -jobs 8
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "implementation failed"}
open_run impl_1
write_checkpoint [file join $obj post_route.dcp]
file mkdir [file join $obj report]
foreach {cmd name} {report_timing_summary timing report_utilization utilization report_clocks clocks report_cdc cdc check_timing check_timing report_exceptions exceptions report_drc drc report_bus_skew bus_skew report_route_status route_status} {
 $cmd -file [file join $obj report ${name}.txt]
}
set dut [get_clocks -quiet *harnessSysPLL*]
if {[llength $dut] != 1 || abs([get_property PERIOD $dut]-1000.0/70)>0.001} {error "Expected one 70MHz FSA clock"}
set summary [report_timing_summary -return_string -max_paths 1]
if {![regexp {WNS\(ns\)[^\n]*\n\s*-+[^\n]*\n\s*([^\n]+)} $summary ignored row]} {error "Missing timing summary"}
set values [regexp -all -inline {\S+} $row]
foreach i {0 4 8} {if {[lindex $values $i]<0} {error "Negative setup/hold/pulse slack: $row"}}
foreach i {1 2 5 6 9 10} {if {[lindex $values $i]!=0} {error "Timing failure: $row"}}
if {[llength [get_drc_violations -quiet -filter {SEVERITY == Error || SEVERITY == {Critical Warning}}]]} {error "Blocking DRC"}
exit
