# A110/APB55 本次 routed CDC / HBM / 约束审查记录

本记录是独立复现取证与结构审阅，不是 CDC 接受记录。两套 native implement 均完整产生 routed DCP 和报告，末端严格检查因缺本次已接受 review 而失败；失败文件保持原样。全部 36 项新增审查条目保持 pending，`board_signoff=false`。其中 CDC-8 有实际 ASYNC_REG 缺口，不能用旧基线记录、正 WNS 或源码中存在三级链来解除。

## 绑定的实现

| 项目 | 原始 | 删除失效约束后的候选 |
|---|---|---|
| 源码提交 | b595900e91bda33925f059ff585771ae5ecddfcd | 7deb8e3e9416f2f3d25df9d45a5f65fc38302cda |
| 构建输出 | build-attempt02 | build-fixed-attempt01 |
| DCP SHA256 | 1d7cf7221b7785d45afb98ac49588efbeb0a1b2635d4590c4591d7e2db6e3268 | ee2a49e1a8b8a99e4d4028d43cc3ac3b6f90d75d0a19d1ac33f6f9a25e4fb794 |

相对路径均以 `/tmp/ict-fsa-reproduce-20261028/a110` 为根。原始独立 `reaudit-original-attempt01` 的 Vivado exit=0，生成 113 个报告/证据；`acceptance/initial/reaudit.failed.json` 仍失败。修复候选用本次 native 报告和独立只读网表探针取证，没有为已知不能接受的 CDC 条目重复执行整个 reaudit。

## CDC 分类与实际证据

两套本次 `report_cdc -details` 的 294 条详细行逐项相同：CDC-3 Info77、CDC-9 Info21、CDC-8 Warning1、CDC-7 Critical7、CDC-10 Critical2、CDC-15 Warning170、CDC-11 Critical16。Warning/Critical 合计196条，共332个唯一源/目的pin；不能将 Critical 数量下降视为审查通过。

| 组 | 数量 | 本次结构证据与解释 | 状态 |
|---|---:|---|---|
| 新增 CDC-15 debounce + CDC-7 deglitch | 26+2 | APB55 域13位 FDCE CLR/FDPE PRE，fanin 包括 PCIe user_reset、power-on reset、PLL LOCKED；ResetWrangler 以最慢55MHz计5500周期，经deglitch和逐域ResetCatchAndSync释放。是异步reset资格链，包含运行时原因；不是业务多位数据传输。 | 结构解释建议，pending |
| 新增 CDC-10 vendor XPM reset | 2 | 实际首级FDCE/FDPE的 ASYNC_REG=1；vendor xpm_cdc_async_rst DEST_SYNC_FF=2，复位前组合逻辑来自sys_rst_n与链路/热复位状态。 | 结构解释建议，pending |
| 新增 CDC-7 vendor reset sinks | 5 | user_lnk_up 的D由同步后的信号驱动，但异步clear仍受PHY链路状态影响；其余寄存器使用sys_or_hot_rst。实际fanin与本次生成PCIe源码一致。 | 结构解释建议，pending |
| 新增 CDC-8 | 1 | `wrangler/nodeOut_reset_catcher_2/.../sync_2_reg/CLR` 为实际FDCE，PCIe AXI250MHz，**ASYNC_REG为空**；上游是APB55 deglitch。 | **不接受，需后续设计处理** |
| 原有 CDC-11 vendor lane fanout | 16 | 8lane×2个单bit（rate[1]和MAC detect）扇出到各lane同步器；报告深度4，首级实际ASYNC_REG=1；生成sync_cell参数STAGE=3但数组[STAGE:0]，因此4级。 | 记录协议/结构边界，不构成全系统证明 |
| 原有 CDC-15 CPLL counter | 144 | 8lane×18bit；生成IP先关闭测试时钟计数使能，经HOLD等待后UPDATE采样，属于受控采样协议；本次CDC将144条标为False Path。 | 记录vendor协议与约束，不等同逐bit普通同步器 |

10000个sys_clock周期的资格计数仅覆盖新增的上游 fundamental-reset 原因，不覆盖vendor内部hot-reset、link-down、PHY状态和ds_pulse。对正Recovery裕量不作异步复位协议安全或MTBF证明。`evidence/cdc-review.original.draft.json` 有36条完整原始finding、限定理由和hash；A70 agent 独立核对集合、332pin、全部证据/源码hash，并收紧运行时原因的表述。全部 disposition 保留 pending。

## 未约束端点

- 本次 check_timing 的30个 unconstrained_internal_endpoints 恰为未使用HBM AXI1–15的BREADY/RREADY；15个ACLK均为GROUND。本次primitive的BREADY/RREADY分别反馈自身BVALID_PIPE/RVALID_PIPE，**不是READY常量**。这说明当前不活动端口为何不属于有效时钟下的业务STA。若启用更多AXI端口，应重新检查，而非继承此解释。
- 唯一 no_input_delay 是外部异步 prst_n。实际扇出只有releaseSync的3个CLR端点；该输入是复位原因，不能附会为同步数据输入延迟。与A70/A100的16端点直接输入复位结构不同。
- 其余 no_clock、constant_clock、multiple_clock、loops、no_output_delay 等检查为0；这里的constant_clock计数为0与30个内部端点的实际ACLK常量证据不矛盾，应分别阅读报告类别。

## Exceptions 与无效约束

8条 Invalid startpoint 对应vendor GT CPLL宽泛 `testclk_cnt_reg*` 选择器。每lane实际匹配18个FDCE以及3个CARRY8，而目的端为18个FDRE；并非寄存器不存在。144条真正寄存器CDC路径仍在report_cdc中标记False Path。本轮不改vendor生成约束、不扩展false path。

10条 Non-existent path 来自vendor clock-group例外在本次实现没有相应路径的组合。作为冗余约束状态记录；不把该提示等同真实有效路径未约束。

与这些vendor条目不同，R004是自研XDC中对 `*sram_accRAM_fullWrite_0_addr_REG*` 设置MAX_FANOUT的目标完全为空。本次原始DCP验证 count=0，生成RTL为新的_r地址寄存结构；修复提交删除失效语句，不改到新的目标。修复候选完整实现的Common17-55归零，RTL、有效实现行为及最终时序资源未变化。

## 复位复制和HBM边界

实际复位复制2→21，原生审计核对FDCE签名、驱动和完整sink并集等价，21个终端D/CLR各max/min共84项均覆盖，最差0.259ns；不增加PE流水阶段。HBM APB55、AXI110、ref100，三条三级同步链、启动完成同步和AXI全通道门控均通过本轮原生结构审计，相关最差时序0.066ns。数字HBM回归覆盖3362863次检查，但不证明模拟亚稳态、HBM PHY或所有PCIe运行时复位场景。

全板WNS=0.114ns为PCIe reset Recovery，DUT setup WNS=0.802ns、hold0.010ns；TNS/THS及失败端点为0。这些是当前约束下的STA数值，不能替代本记录保留的CDC签核缺口。

## 后续工作边界

若要把本次候选升为严格发布签核版本，需要另立设计变更：明确ResetCatchAndSync全部同步级的属性/保留策略与复制关系，验证同步链布局及恢复/移除检查，覆盖PCIe hot-reset/link-down等原因的跨域释放协议，再做对应完整P&R与审查。不能仅在JSON填写accepted或把缺失属性解释为误报。本轮没有修改该复位设计，没有导出bitstream或执行实板测试。

两套只读网表probe均 exit=0；修复候选独立采样的332pin、HBM/复位/例外对象内容与原始观察一致，并单独绑定自己的DCP。修复候选的 `evidence/cdc-review.fixed.draft.json` 仅记录这些本次观察，全部pending，不继承原始交叉审阅的接受。`evidence/fixed-original-netlist-comparison.json` 记录两次探针文件hash及比较范围。
