# A100 本次新 DCP 的 CDC / 约束审查记录

这是结构核对记录，不是 CDC 全量放行或实板验收。原提交 `f8650f9576bf681bfae38a2ab40718fc2ace4262` 的本次 DCP SHA256 为 `5420a3f09a23b726ad749f158d8b138440884022b3d3709b4b17aff59ff3874d`；来源 `build-attempt02/A100/fpga/chipyard.fpga.nm37.NM37FPGATestHarness.EmptyNM37Config/obj/post_route.dcp`。布局布线正常 exit0，`physical.passed.json` 明确 `constrained_sta_passed=true`、`board_signoff=false`、`cdc_review_required=true`。

本记录所有相对路径均相对于本任务根。报告hash在`build-attempt02-physical-evidence/summary.json`。下述比较使用旧A100作为只读参考，没有复制任何旧review或成功标记。

## 已确认的范围

| 项目 | 本次实际证据 | 结论与限制 |
|---|---|---|
| 全板及DUT时序 | 全板WNS0.049ns / WHS0.010ns / WPWS0；DUT10ns setup0.534ns / hold0.010ns；TNS/THS/TPWS均0 | 受约束的时序通过 |
| 路由、DRC、bus skew | 497497/497497 routable nets完整布线，routing error0；DRC无Error/Critical；最小bus-skew slack3.142ns | 本次路由质量检查通过 |
| HBM30未约束端点 | `check_timing.txt`明确为constant clock；`netlist-review-original-attempt02/unused_hbm_pins.txt`逐项30端点，AXI1..15的15个ACLK网络均TYPE=GROUND；30个BREADY/RREADY的all_fanin分别来自同macro的BVALID_PIPE/RVALID_PIPE | 可以作为未使用HBM端口的局部例外接受；**数据端点不是全部接地**，不得扩展到使用中的AXI00。完整v2 probe成功；首次API失败输出也保留 |
| `prst_n` no_input_delay | 本次网表BF5/LVCMOS18输入，扇出端点16个，均在PCIe内部的CLR/PRE；生成shell.sdc第18行是`set_false_path -through [get_ports {prst_n}]` | 属异步复位输入，不应虚构同步数据input delay来消提示；接受无同步数据接口延迟的解释，并不等于复位释放全部签核 |
| 与旧A100比较 | 全302条CDC detail行，以及8条Invalid startpoint/10条Non-existent path记录与旧A100归一空白后相同 | 证明没有新增这些报告项，不能单凭“旧版也有”放行 |

## CDC 分类

本次共99 Info、173 Warning、30 Critical。`cdc-groups-original.json`保存规则、层次归属、数量及示例：

- CDC-3：77，CDC-9：22，主要为PCIe和AXI/AXI-Lite clock converter的工具识别同步器。
- CDC-7：12，其中PCIe10、ResetWrangler2；实际查完6个唯一目的cell，均是FDCE/FDPE的CLR/PRE。PCIe一侧fan-in为POR、prst_n、PCIE4CE4 CORECLK；Wrangler的deglitched PRE fan-in为PCIe user_reset、POR和PLL LOCKED。确认属于既有异步复位控制网络，未把它们认作同步数据路径；未证明任意复位源抖动/失锁/释放顺序的所有动态情形。
- CDC-8：1，`wrangler/deglitched_deglitch/reg_0_reg/C` → `wrangler/nodeOut_reset_catcher_1/io_sync_reset_chain/output_chain/sync_2_reg/CLR`，报告识别三拍链但缺ASYNC_REG。源码`ResetCatchAndSync.scala`/`SynchronizerReg.scala`存在三拍异步置位/同步释放结构。本次网表首级为FDCE、D/CE接VCC，clock为4ns PCIe AXI时钟，CLR来自deglitched；ASYNC_REG为空，LOC=SLICE_X162Y63。释放结构存在但属性缺口是真实的，保留物理CDC后续项。
- CDC-10：2，POR进入PCIe `user_lnk_up_cdc`/`user_reset_cdc`同步器前有组合逻辑。实际查完两个目的端点：分别FDCE/FDPE、ASYNC_REG=1、PCIe AXI 4ns时钟，工具报告depth3；fan-in为POR、prst_n及PCIe硬核CORECLK。确认同步器存在、警告指向其前方组合复位源；本轮没有针对所有组合复位源相对时序做时域故障注入或实板冷启动测试。
- CDC-11：16，PCIe phy_rate/as_mac_in_detect各向8 lane分发，工具标出多目的同步扇出。实际查完16个目的端点，均FDRE、ASYNC_REG=1、目标xdma_ref_clk=10ns，工具报告depth4；两个launch链分别向8个lane同步器分发。确认是vendor PHY控制的多个同步目的，而非本次新增FSA数据CDC；未证明8lane解除控制的周期一致性，未以ASYNC_REG=1替代vendor协议的动态验收。
- CDC-15：172，其中PCIe CPLL频率计数捕获144、ResetWrangler debounce复位28。该规则表示CE控制的跨域捕获等结构，不能直接解释成172个未同步普通FSA数据总线。

以上Warning/Critical目的层次均为`pcie`或`wrangler`，没有以PE/FSA数据寄存器为目的的新增CDC行。已完成上述实际新DCP的Warning/Critical端点结构归类，详见`cdc-structural-summary-original.json`及完整170端点raw probe。其边界是结构与既有行为对照；并未完成所有异步复位动态场景、vendor多lane协议及MTBF的独立证明。本次未创建全量CDC放行JSON。

## Exceptions 与已修正的无效历史约束

`exceptions.txt`的8条Invalid startpoint来自生成的GT Wizard XDC中每lane的`U_TXOUTCLK_FREQ_COUNTER/testclk_cnt_reg*` → `freq_cnt_o_reg*` false-path命令。10条Non-existent path已对照报告的具体对象：position92/93为`xdma_ref_clk`与lane27/channel3 `GTYE4_CHANNEL_PRIM_INST/TXOUTCLK`的两向重复组；94/95为`xdma_ref_clk`到`bufg_gt_intclk/O`；96/97为`pipe_clk`与该intclk的两向重复组。对应的是本次网表没有实际时序路径的这些clock-group关系；例如position95反向那一行没有Non-existent标记，不能连同其它有效跨域路径一概忽略。clock_interaction中的有效pipe↔xdma_ref关系仍记录Asynchronous Groups，而pipe→AXI/TxOUTCLK等相关时钟路径仍Timed。保留vendor约束，不为消提示增加或扩大false path。不能仅根据字符串把前者全部认定为“寄存器不存在”：CDC报告仍列出了相应计数寄存器，本次精确查询证实：每个lane的start通配符匹配21个对象，包含18个FDCE计数寄存器及3个CARRY8组合单元；end匹配18个FDRE。非时序CARRY8被纳入start集合解释Invalid startpoint，而对应144条CDC计数捕获行Exception列仍为False Path。可接受对这8条vendor选择器提示的局部解释，不应把命令整体描述为无效或把寄存器说成不存在。原始对象见`netlist-review-original-attempt02/exception_objects.txt`。

与上述vendor exceptions不同，历史`nm37-config.xdc`的`MAX_FANOUT 128`针对`*sram_accRAM_fullWrite_0_addr_REG*`，在本次综合中明确匹配零个cell，产生Common17-55。先向用户报告后，修复提交`9b8911f4e9e5c6af49fe6b6287e9c88ee1031352`只删除该无效命令与过时说明，并同步输入锁。未改PE流水、未改时钟、未把限制重新施加到新的地址寄存器。修复版独立完整布局布线已exit0：全板WNS0.073ns、DUT WNS0.642ns，hold0.010ns、所有总负裕量0；新DCP SHA256 `1e1fc9f7fbf88035fae084cbf21c935c0f8d9b6d2be9bf36a1beeb8036f9592e`，Common17-55消失。

## 分析脚本自身问题

共享只读`netlist_review.tcl`首次运行完整输出HBM/资源/外部复位小节后，在CDC cell-pin循环中把字符串交给`list_property`导致Common17-58。这不是硬件或implement失败。保留`netlist-review-original`及exit1日志；单独副本`netlist_review_fixed_api.tcl`重取typed pin，输出新目录`netlist-review-original-attempt02`，同时追加CPLL exception和失效MAX_FANOUT的精确对象查询。v2最终exit0，完整记录170个选定CDC端点；`context.txt`再次记录实际DCP SHA。此辅助脚本修复不改变设计、约束、DCP或任何构建成功标记。

## CPLL计数器捕获源码证据

本次生成IP的`obj/ip/nm37_xdma/ip_0/ip_0/hdl/gtwizard_ultrascale_v1_7_gtye4_cal_freqcnt.v`中，testclk_en经过两拍ASYNC_REG同步后控制test域计数；ref域状态机结束MEASURE后进入HOLD，等待hold_clk到0xF再进入UPDATE捕获18bit testclk_cnt。这解释每lane18条、共144条CDC-15的CE/稳定窗口设计。该结构解释不是所有时钟比/上电场景的完整证明；当前报告不以它替代vendor启动条件和复位释放审查。

## 修复候选新DCP最终复核

`netlist-review-fixed`完整exit0，其context绑定上述修复DCP。新DCP逐项查完170个CDC目的端点；HBM15个unused ACLK为GROUND、30个ready为同macro VALID_PIPE反馈；prst_n还是同16个PCIe异步置位/复位端点；8 lane的CPLL selector各18 FDCE+3 CARRY8→18 FDRE；无效MAX_FANOUT旧selector为0，实际新命名地址cell为10。原/修复两套结果忽略实际布局LOC/BEL变化后，所查CDC目的cell类型、ASYNC_REG、时钟和fan-in结构全部一致。

修复版CDC-8首级仍为FDCE、ASYNC_REG为空，LOC为SLICE_X157Y54；该既有物理属性缺口未被本轮隐藏或改写。30个Critical和173个Warning的结构已经归类，本记录保留未独立证明的动态复位、多lane协议和MTBF范围，不制造完整board_signoff。详见`netlist-review-summary-original.json`、`netlist-review-summary-fixed.json`、`netlist-comparison.json`。
