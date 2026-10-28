# A70-P3 独立复现验收记录（2026-10-28）

本次从 ICT-FSA `8cc6b42536334892b88f6214f39d3afe5daa2504` 独立 clone，按交付手册运行新的生成器编译、验证、固定仿真、长序列仿真、板级展开和完整布局布线。所有原生阶段均已完成；新 A70-P3 的实际 routed 时序、资源和路由计数与旧 A70-P3 相同。没有修改该冻结源码，没有导出 bitstream、烧录或板测，没有 push。

## 输入和环境

- 成功源码：`/tmp/ict-fsa-reproduce-20261028/a70/source-attempt02`，HEAD 为上述完整 commit，Git 工作树无已跟踪改动。
- 成功输出：`/tmp/ict-fsa-reproduce-20261028/a70/build-attempt02`。
- 旧对照：`/home/zhangsi/nm37-git-reproduce-fresh/a70-p3-build-java20-20261025-020151`，只读。
- 初始执行手册：交付主分支 `4d85b90cefc6b5aa65151c285fe2873118939b84` 的 README 与环境/恢复文档；后续文档勘误由主 Agent 单独提交，不注入冻结硬件源码。
- 工具：JDK 20.0.2、firtool 1.75.0、Verilator 5.022、GCC/G++ 13.3.0、Vivado 2020.2_AR75986、Yosys 0.70。
- 独立恢复 172 个锁定依赖仓库，重建 FSA/EasyFloat 两个 Python 环境。只复制下载缓存；未复制旧生成器 JAR、RTL、仿真器、形式证明或 DCP。运行使用 CPU 0–7；Vivado maxThreads=4。

完整环境和命令在 `env.sh`、`commands.log`；原生阶段记录副本在 `evidence/receipts/`。这些证据副本不是补写构建成功标记。

## 已完成的阶段

| 阶段 | 实际结果 | 主要证据 |
|---|---|---|
| doctor / deps / Python | 工具检查通过，锁定依赖和两个 Python 环境恢复 | `evidence/logs/`、`dependencies-attempt02.json` |
| build | 新 JAR 编译完成，SHA256 `a126f6a625d357f23afd665747873e9834a4a45d2f1a01ee07f9d850213231ae` | `build-attempt02.ict-state/build-0.log`、`build.json` |
| verify | 累计器 24,394 个输出、倒数 525 次事务、三拍无输入约束 SAT 等价和证明驱动正反例通过 | `verify-0.log`、`evidence/formal-result.json` |
| sim4 | seq4/8 对 PyEasyFloat 逐位一致 | `sim4-0.log`、`sim-old-comparison.json` |
| sim16 | seq16/32 对 PyEasyFloat 逐位一致 | `sim16-0.log`、`simulation-counters.json` |
| sim-extra | 16×16、seq1024 对 PyEasyFloat 逐位一致 | `seq1024-attempt02/result.json`、`logs/sim-extra-1024-attempt02.log` |
| elaborate | 92 个板级 Verilog/SystemVerilog 文件与旧 A70 逐字节相同；配置 JSON、PLL/XDMA/HBM Tcl 相同 | `rtl-old-comparison.json`、`elaboration-old-comparison.json` |
| implement | 06:57:47 UTC 完成；全板/DUT setup、hold、脉宽严格检查通过 | `implement-0.log`、`implement.json`、`evidence/routed/` |

三拍形式证明的范围是累计器 MAC/EXP2 输出，不扩展成倒数或全系统调度形式证明。全部仿真用例的输入、配置、实际输出和参考输出哈希与旧对应 A70 结果相同。seq1024 的旧控制台计数日志未找到，因此只对其输入/输出/配置做旧新哈希核对，不宣称旧长序列计数已经核验。

## 仿真计数

前四行的全部 8 项 FSA 计数及仿真总周期与旧 A70 日志相同。最后一行为本次新增长序列日志的实际计数。

| 阵列 / 序列 | execTime | mxBubble | mxActive | dmaActive | 仿真总周期 |
|---|---:|---:|---:|---:|---:|
| 4×4 / 4 | 368 | 153 | 143 | 16 | 4,707 |
| 4×4 / 8 | 1,083 | 651 | 388 | 48 | 11,857 |
| 16×16 / 16 | 442 | 111 | 249 | 101 | 5,427 |
| 16×16 / 32 | 1,157 | 421 | 754 | 260 | 12,577 |
| 16×16 / 1024 | 775,909 | 382,899 | 532,032 | 150,734 | 7,760,097 |

seq1024：rawInst=70,529、mxInst=12,416、dmaInst=8,320、fence=1；实际/参考输出 SHA256 均为 `b7f9f8ec3d9d6efc5f38c1f79b58ce911bb65a00f0b03f1e28a54d8fb2e9f131`。

A70 的 16×16 固定仿真使用单路 256-bit AXI 和 `mm_magic_t` 功能内存；A100/A110 固定仿真使用 8 路 64-bit AXI。跨版本计数不能作为纯提频/流水加速比。仿真总周期也不是 FSA execTime；mxBubble 是矩阵指令入口 ready 且无 valid 的计数，不是 PE 空闲率，且不保证与 mxActive 互斥。

## 实际 routed 结果与旧 A70 对照

| 指标 | 旧 A70-P3 | 本次 A70-P3 | 差值 |
|---|---:|---:|---:|
| DUT 周期 | 14.286 ns | 14.286 ns | 0 |
| 全板 WNS / WHS | 0.047 / 0.010 ns | 0.047 / 0.010 ns | 0 |
| DUT WNS / WHS | 0.419 / 0.010 ns | 0.419 / 0.010 ns | 0 |
| TNS / THS / WPWS / TPWS | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 0 |
| LUT | 378,248 (29.01%) | 378,248 (29.01%) | 0 |
| Logic LUT | 372,342 (28.56%) | 372,342 (28.56%) | 0 |
| LUTRAM / SRL | 4,958 / 948 | 4,958 / 948 | 0 |
| FF | 71,330 (2.74%) | 71,330 (2.74%) | 0 |
| DSP | 288 (3.19%) | 288 (3.19%) | 0 |
| RAMB36 / RAMB18 | 52 (2.58%) / 0 | 52 (2.58%) / 0 | 0 |
| fully routed / routable nets | 477,602 / 477,602 | 477,602 / 477,602 | 0 |
| routing errors | 0 | 0 | 0 |

全板 setup/hold 检查端点均为 192,967，脉宽检查端点 81,055，全部失败端点数为 0。bus-skew 最小 slack=2.579 ns。DRC 无 Error/Critical；保留的 Warning 为 DPIP-2=544、DPOP-3=272、DPOP-4=288、REQP-1852=1、RTSTAT-10=1。完整原始表和实际 SHA256 在 `physical-old-comparison.json`。

新 DCP SHA256：`dcc05fd3cbcac572db83d743c3912a0747c59f530feb7512f72754557364215d`。

旧 DCP SHA256：`a6f02be1703015255da8e1861b453e93adae9ce9e0fdd453dcb288af0d6a4878`。

两个 DCP 文件 hash 不同，不影响上述实际 RTL/报告指标一致的结论，也不要求不同构建目录产生字节相同 DCP。

## CDC / 约束证据范围

`audit/cdc.txt`、`check_timing.txt`、`exceptions.txt`、`bus_skew.txt` 去掉日期/路径等报告头后，正文与旧 A70 完全相同。CDC 分类为 CDC-3 Info 77、CDC-7 Critical 12、CDC-8 Warning 1、CDC-9 Info 22、CDC-10 Critical 2、CDC-11 Critical 16、CDC-15 Warning 170。约束覆盖仍为 30 个 HBM internal endpoints、1 个 prst_n no_input_delay；其余 check_timing 类别为零。exceptions 中 Invalid startpoint 8 处、Non-existent path 10 处。这是没有新增发现的证据，不等同于自动批准全部 CDC。

本次 DCP 的只读网表诊断已完成 HBM 与外部复位部分，与旧 DCP 诊断结构相同：HBM 端口 1–15 的 15 个 ACLK net 均为 GROUND；每个 BREADY/RREADY 的 fanin 分别来自同一 HBM 宏的 BVALID_PIPE/RVALID_PIPE。**READY 本身不是常量。** prst_n 对应外部异步复位和 16 个 PCIe 异步复位端点。源码 ResetWrangler 将 reset causes 合并后作慢时钟去抖，ResetCatchAndSync 用三拍链对各域释放同步；这些源码事实仍需结合网表端点判断，不将整个 reset 网络默认为安全。

附加 CDC 全端点 typed-pin 诊断第一次运行在 Vivado Tcl 对象查询处失败；失败日志保留在 `logs/netlist-review.log`。主 Agent 告知用户后，在新目录 `netlist-review-attempt02` 用修复后的只读脚本重跑，07:38 UTC 完整 exit=0，182 个唯一 Warning/Critical 目的端点全部查询成功，并绑定本次 DCP SHA256。没有改变设计或时序约束。

网表独立确认，每个 CPLL lane 的旧 start 通配符匹配 18 个 FDCE 和 3 个 CARRY8，终点是 18 个 FDRE。组合 CARRY8 被混入起点集合可以解释 Invalid startpoint；不是合法寄存器不存在，也不是整个例外失效。实际 CDC 报告的 144 条 CPLL 捕获路径均显示 Exception=False Path。供应商 `gtwizard_ultrascale_v1_7_gtye4_cal_freqcnt.v` 通过两拍 testclk_en 同步、HOLD_STATE 等待后 UPDATE_STATE 捕获；该源码/网表结构事实不冒充所有启动时序的动态证明。

CDC-8 所报首级 `wrangler/nodeOut_reset_catcher_1/.../sync_2_reg` 在网表中为 FDCE，ASYNC_REG 为空；对应生成源码是三拍异步清零、同步移入 1，再反相输出的 reset 释放链。PCIe `user_lnk_up_cdc/arststages_ff_reg[0]` 和 `user_reset_cdc/arststages_ff_reg[0]` 的 ASYNC_REG=1。保留属性缺失作为后续物理实现改进项，本轮未扩大硬件改动范围。完整端点属性、时钟、fanin 和 selector 对象在 `netlist-review-attempt02`，机器摘要在 `netlist-review-summary.json`。

## 执行中发生的异常及处理

1. 第一次 build 在 sbt BootServerSocket 初始化时被代理沙箱拒绝本机 socket，未生成 JAR。保留 `source` / `build-attempt01` 和日志，重新独立 clone 为 `source-attempt02`、重新恢复依赖/两个 Python 环境，并使用新输出及允许本机 socket 的执行权限。没有改设计或降低验证门槛。
2. 成功 build 的原生 CLI 在 05:34:19 已输出 COMPLETE，原生 `build.json` 为 completed，sbt 正常完成 assembly。任务外部的临时监控 wrapper 因执行中被修改日志路径随后报 EOF；这是监控脚本故障，不是仓库 build 命令失败。该异常和原生日志都保留，后续所有阶段均校验本次 JAR，没有手写成功标记。
3. 附加网表诊断的 typed-pin API 错误独立保留，不覆盖失败产物，不重跑已成功的 P&R；只重试修复后的只读分析。

## 交付边界

本次证明 A70-P3 新入口能够重新生成与旧基线一致的功能、RTL 和实际布局布线结果。板测、bit 导出和全部 CDC/约束的最终签署不在本记录中冒充完成。最终报告由主 Agent 与 A100/A110 证据统一集成本地提交，冻结构建源码保持不变。
