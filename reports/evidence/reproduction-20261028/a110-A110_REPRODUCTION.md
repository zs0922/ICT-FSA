# ICT-FSA A110/APB55 独立复现记录（完整复现已结束，CDC 未签核）

执行基线为 `b595900e91bda33925f059ff585771ae5ecddfcd`，修复候选为 `7deb8e3e9416f2f3d25df9d45a5f65fc38302cda`。两套均从独立无硬链接 clone 执行完整流程；未复制旧 JAR、RTL、Verilator 模型或 DCP。旧 FSA 及原构建保持只读。没有 push、打标签、导出 bitstream 或上板操作。

## 输入、环境和命令

- 原始执行源码：`source-attempt02`，输出 `build-attempt02`。
- 修复候选源码：`source-fixed`，输出 `build-fixed-attempt01`。
- 每套输出与源码身份、锁文件、生成器 JAR、各阶段 seal 绑定；构建完不修改源码 HEAD。
- JDK 20.0.2、firtool 1.75.0、Verilator 5.022、Vivado 2020.2_AR75986、GCC 13.3、Python 3.13.14。环境详见 `env.sh`、`env-fixed.sh`、各构建的 `logs/environment.json`。
- 172 个锁定依赖独立恢复，只复用下载缓存或锁定 Git 对象；FSA、easyfloat 两个 uv 环境均重新建立。
- 全程绑定 CPU 16–23，编译至多 8 线程，每个 Vivado maxThreads=4。具体命令保存在 `evidence/commands.txt`。
- 按交付 README 顺序执行 doctor、deps、build、verify、sim4/8/16、elaborate、implement；附加 16×16 seq1024 仿真独立输出。

## 已完成的功能验收

两套均完成本次生成器编译、定向验证、形式证明、HBM 启动验证、全部固定回归和额外 seq1024 仿真。

- FPMac 14394、CMP 20169、PE EXP2 扫描 90，五种阵列调度组合及 ControlSignalTest 5 项通过。
- 三项 SAT/时序归纳证明通过。
- HBM 复位启动涵盖 8 种异步时钟场景、32768 门控向量、3362863 次数字逻辑检查。这不是模拟亚稳态或 HBM PHY 证明。
- 六项固定回归逐位匹配 PyEasyFloat；原始、修复候选及旧 A110 同拓扑回归输出 hash 和全部计数器相同。

| 阵列 / seq | execTime 周期 | mxBubble 周期 |
|---|---:|---:|
| 4×4 / 4 | 368 | 153 |
| 4×4 / 8 | 1083 | 646 |
| 8×8 / 8 | 385 | 134 |
| 8×8 / 16 | 1100 | 535 |
| 16×16 / 16 | 437 | 103 |
| 16×16 / 32 | 1152 | 295 |
| 16×16 / 1024 | 775904 | 219217 |

额外 seq1024 的 mxActive=601728、dmaActive=141952、rawInst=70529；原始和修复候选输入、输出及全部计数相同。输出 SHA256 为 `b7f9f8ec3d9d6efc5f38c1f79b58ce911bb65a00f0b03f1e28a54d8fb2e9f131`。TestDriver 总周期 7760097 与 FSA execTime 不是同一计数口径。

板级原始与修复候选的 97 个生成 Verilog/SystemVerilog 文件、FSAConfig 和 PLL Tcl 逐字节相同。实际 RTL 确认 PE after-add、写回/旁路、CMP 和 InputDelayer 后 16 行寄存结构；PLL 请求 DUT110MHz/APB55MHz。FSAConfig 不编码流水深度，不能用它单独证明流水配置。

### 与旧 A70-P3 的实际资源/时序对照

| 指标 | 旧 A70-P3 | 本次 A110/APB55 原始 | 差异 |
|---|---:|---:|---:|
| DUT 周期 | 14.286 ns | 9.091 ns | 70 → 110 MHz |
| DUT WNS | 0.419 ns | 0.802 ns | +0.383 ns |
| 全板 WNS（含 Recovery） | 0.047 ns | 0.114 ns | +0.067 ns |
| LUT | 378248 | 355981 | −22267 |
| Logic LUT | 372342 | 351247 | −21095 |
| LUTRAM / SRL | 4958 / 948 | 3774 / 960 | −1184 / +12 |
| FF | 71330 | 140324 | +68994 |
| RAMB36 / DSP | 52 / 288 | 60 / 288 | +8 / 0 |

这是不同硬件实现的报告对照，不是单个 R004 删除无效约束的收益。旧报告路径及文件 hash 见 `evidence/legacy-reference.json`。

### 仿真比较范围

A110 固定 sim16 为 8×64-bit AXI、8 个功能内存模型；默认不启用 DRAMSim，使用 mm_magic_t，不模拟真实 HBM 延迟。旧 A70-P3 固定 sim16 为单路 256-bit，因此跨版本周期不能直接归为纯提频/流水收益。SimDRAM 的 CLOCK_HZ=100000000 仅用于未启用的 DRAMSim 分支，不是板级 PLL 配置。

mxBubble 表示矩阵指令接口 ready 且无 valid 的计数，不等于 PE 空闲率。mxActive 与 mxBubble 不是互斥分区，不应相加解释总执行周期。这里没有新的实板运行时间或 RelErr 测量。

## 已发现并保留的问题

1. R002：首次 `build-attempt01` 因沙箱禁止 sbt BootServerSocket Unix socket 失败。保留日志和目录，使用独立 `source-attempt02` / `build-attempt02`，以宿主权限完成；未补成功标记。
2. R004：原始 XDC 对 `*sram_accRAM_fullWrite_0_addr_REG*` 的 MAX_FANOUT 设置没有匹配对象，产生 Common17-55 Critical Warning。实际地址寄存器已改为 `_r` 等。告知用户后只删除失效约束及过时说明，更新该 XDC 的 source/shell 锁定哈希；不改 RTL、PE 流水、有效约束、CDC 例外或 DRC 等级。修复本地提交 `7deb8e3`，全新构建已完成编译、全部验证/仿真和完整布局布线，Common17-55归零。
3. 两套完整 P&R 均已完成，但各自 native implement 最后因缺少本次已接受的 CDC review 失败。两套 `physical.failed.json` 与 `.ict-state/implement.json` 原样保留；原始版本的独立 `reaudit-original-attempt01` 重新读取相同 routed DCP 并生成新报告，不把原失败改为成功。
4. 现有重复 read_ip 的 Vivado12-1504 警告记录为重复导入已在 fileset 的 IP；本轮未混入 unrelated 修复。

## 两套完整 P&R 的实际结果

| 指标 | 本次 b595900e / 修复 7deb8e3（相同） | 旧 A110/APB55 |
|---|---:|---:|
| 全板 WNS（含 Recovery） | 0.114 ns | 0.114 ns |
| 全板 WHS | 0.010 ns | 0.010 ns |
| DUT WNS | 0.802 ns | 0.802 ns |
| DUT WHS | 0.010 ns | 0.010 ns |
| TNS / THS | 0 / 0 | 0 / 0 |
| LUT | 355981 (27.31%) | 355981 |
| Logic LUT / LUTRAM / SRL | 351247 / 3774 / 960 | 相同 |
| FF | 140324 (5.38%) | 140324 |
| RAMB36 | 60 (2.98%) | 60 |
| DSP | 288 (3.19%) | 288 |

全板 WNS 对应 PCIe reset Recovery：`pcieResetControl/releaseSync/sync_reg[2]/C` → `as_mac_in_detect_user/PRE` 或 `speed_change_in_progress/CLR`，两级 LUT，数据延迟约 1.272 ns，其中布线约 86.8%。该正裕量是 Vivado 当前约束下的结果，不能独立证明异步复位释放安全；需要结合 vendor reset 协议/结构审查。

DUT 最差 setup 为 PE `reg_exp_reg[0]` → 同 PE FMA `adderOutAbs_reg[20]`，28 级逻辑，数据延迟 8.071 ns（logic 2.509 / route 5.562 ns）。

复位复制由 2 个原寄存器变为 21 个等价复制寄存器；实际 D/CLR 的 max/min 共 84 项检查覆盖完整，最差裕量 0.259 ns，不增加流水阶段。HBM APB55 / AXI110 / ref100 实际结构检查通过，相关最差时序 0.066 ns。

## CDC、HBM 与约束复审结果

两套本次 CDC 均为 25 Critical / 171 Warning；相对冻结分类列表有 36 项需要本次证据。已完成本次 332 个 Warning/Critical 源/目的 pin 的属性和连接采集，不将旧 review 复制为新审查。

实际 DCP 已确认：

- 未使用的 HBM AXI1–15 的 ACLK 均为 GROUND；30 个 BREADY/RREADY 分别是本 primitive BVALID_PIPE/RVALID_PIPE 的反馈，不能写成 READY 为常量。仅 AXI0 为活跃业务接口。
- 外部 prst_n 仅有三个端点：`pcieResetControl/releaseSync/sync_reg[0..2]/CLR`，不同于 A70/A100 直接复位多个原边界寄存器的 16 端点结构。
- 原生 HBM 审计确认三条三级同步链、PCIe releaseSync、10000 周期资格计数、无 reset 反馈；HBM traffic gating 只在完成同步启动后放行。
- CDC-15 的 26 个新增路径进入 APB55 域 ResetWrangler debounce 复位端；ResetWrangler 选择最慢时钟，再以 ResetCatchAndSync 向各目标域释放。需要结合实际同步链和网表确认，不能当普通多位数据 CDC。
- 实际 CDC-8 目的 `wrangler/nodeOut_reset_catcher_2/.../sync_2_reg` 的 ASYNC_REG 属性为空，保持待处理，不接受为误报。28 条 reset qualifier、2 条 XPM async reset、5 条 vendor reset sink 已做结构解释，但全部仍 pending；10000 周期资格计数只涵盖新增 fundamental-reset 上游，不覆盖 IP 内部 hot-reset/link-down 等运行时原因。A70 agent 已独立校验条目集合、证据及源码 hash，并审读分类边界。
- 其他 vendor CDC 的源协议和本次 IP 文件 hash 已记录在 `evidence/cdc-source-provenance.json`；逐组结构结论与边界见 `A110_CDC_CONSTRAINT_REVIEW.md`。

原始独立 reaudit 的 Vivado 只读报告生成 exit=0，113 个报告/证据文件与原 DCP 绑定；initial acceptance 因缺 CDC review 保持失败，且已确认 CDC-8 未解决，因此不补写 accepted review 或成功 seal。

`board_signoff=false` 始终明确保留。数字回归、STA 和有限结构审查不等价于实板验证、模拟 MTBF 证明或所有运行时恢复场景的系统签核。

机器状态见 `progress.json`。原始实际报告位于 `build-attempt02/A110/fpga/chipyard.fpga.nm37.NM37FPGATestHarness.EmptyNM37Config/obj/`；修复候选同构目录位于 `build-fixed-attempt01`。证据在 `evidence/`，网表只读诊断在 `netlist-original-review/`、`netlist-fixed-review/`。最终机器摘要为 `final-summary.json`。

修复候选的独立只读 probe 也已 exit=0，重新读取自己的 DCP（SHA256 `ee2a49e1a8b8a99e4d4028d43cc3ac3b6f90d75d0a19d1ac33f6f9a25e4fb794`），完成332个CDC端点、HBM、prst_n和exceptions对象取证。实际CDC-8属性仍为空；其记录为 `evidence/cdc-review.fixed.draft.json`，全部36项仍pending。原始A70 agent交叉审阅只适用于原始draft，未自动移用为修复候选的接受。root另行检查了修复DCP身份、332pin与属性缺口。

两套源码最终tracked worktree/gitlinks干净，HEAD分别保持原始和修复提交；没有为了报告更换构建源码身份。修复在 `fix-author` 的本地 `codex/a110-reproduction-fix` 分支，只有删除无效XDC及对应锁文件更新。报告由root在集成仓统一提交。严格CDC acceptance、board_signoff、bitstream导出和上板均未宣称通过。
