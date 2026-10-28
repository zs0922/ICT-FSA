# ICT-FSA A70-P3 / A100 / A110-APB55 独立复现记录

本轮任务开始并完成于 2026-10-28。三个独立任务按交付文档 commit `4d85b90cefc6b5aa65151c285fe2873118939b84` 的根 README 和环境/恢复说明执行。工具修复先报告用户再实施；不修改旧 FSA 源码或构建，不 push，不操作实板。

## 固定输入和隔离

| 配置 | 起始源码 commit | 独立工作目录 | 编译 CPU |
|---|---|---|---|
| A70-P3 | `8cc6b42536334892b88f6214f39d3afe5daa2504` | `/tmp/ict-fsa-reproduce-20261028/a70` | 0–7 |
| A100 | `f8650f9576bf681bfae38a2ab40718fc2ace4262` | `/tmp/ict-fsa-reproduce-20261028/a100` | 8–15 |
| A110/APB55 | `b595900e91bda33925f059ff585771ae5ecddfcd` | `/tmp/ict-fsa-reproduce-20261028/a110` | 16–23 |

使用相同安装版本的 JDK20.0.2、firtool1.75.0、Verilator5.022、GCC/G++13.3.0、Vivado2020.2_AR75986。每组独立 clone、依赖恢复、下载缓存和 Python 环境；下载缓存可复制，生成器 JAR、RTL、仿真器、形式证明及 DCP 必须由本次源码重新生成。Vivado 各自 maxThreads=4。

## 发现并修复的问题

- **R001，形式环境 Python 版本未固定。** 手册原用 `python3 -m venv`，Chipyard conda PATH 可能选中 Python3.10，而固定依赖要求更新的 Python。向用户说明后改为 `uv venv --python 3.13` 和指定解释器的 `uv pip install`。A100 任务独立安装五个锁定包并运行 Yosys0.70 成功，旧失败环境保留。文档修复 commit `898fc58`。

- **R002，代理沙箱拒绝 sbt 本机 socket。** A70/A100/A110 首次 build 在 Scala 编译前出现 `BootServerSocket / Operation not permitted`。向用户说明后保留失败目录，改用独立源码及新输出，并以允许创建本机 socket 的执行权限重试。这属于本轮代理执行环境限制，不修改 FPGA 设计，不降低任何验证门槛。

- **R003，跨版本固定仿真内存拓扑不同。** 源码与生成配置确认 A70 16×16 使用 1×256-bit 直接 AXI，A100/A110 使用 8×64-bit。先告知用户，再补 README；保留各版本历史固定回归用于复现，跨版本周期/bubble 只按各自模型记录，不报告纯提频加速比。固定回归默认 `dram_sim=False`，C++ 后端选择 `mm_magic_t` 功能内存模型；不模拟真实 HBM 时延。A110 仿真 RTL 的 `CLOCK_HZ=100000000` 只供未启用的 DRAMSim 分支使用，不是板级 PLL 配错。板级实际均应另行检查单端口 HBM 接入。文档修复 commit `ad73bba`。

- **R004，现代配置继承了无匹配对象的扇出约束。** A100/A110 的 `nm37-config.xdc` 仍对 `*sram_accRAM_fullWrite_0_addr_REG*` 设置 `MAX_FANOUT=128`，而实际生成地址链名称是 `_r`/`_r_1`/`_r_2`/`_r_3`。Vivado 报 `Common 17-55`；旧版也存在此警告，该约束没有实际生效。先告知用户后，两个配置分别提交最小修复，只删除空操作和过时说明，不重新匹配新寄存器，不引入新的扇出优化。原运行保留，修复版在新源码/输出目录完整重跑。A70 没有该约束，保持原里程碑。

| 修复候选 | 源码 commit | 本地分支 | 当前状态 |
|---|---|---|---|
| A100 | `9b8911f4e9e5c6af49fe6b6287e9c88ee1031352` | `codex/a100-reproduction-fix` | 完整布局布线和结构审查完成；未宣称全板签核 |
| A110/APB55 | `7deb8e3e9416f2f3d25df9d45a5f65fc38302cda` | `codex/a110-reproduction-fix` | 完整布局布线通过；严格 CDC 未签核 |

- **R005，维护工具没有同步 shell 输入指纹。** 原 `ict-source-manifest.py --write` 只刷新 `source_hashes`，改 XDC 后独立的 `shell_hashes` 仍旧，后端因此会拒绝构建。两组 R004 修复提交分别正确更新同一 XDC 的两处哈希。主分支维护工具另以 `9d5c700` 修正，同步 Xilinx 运行时 shell 文件集合及指纹，保持现有快照范围。三项隔离 Git 测试通过，包括两个 profile 的同步、检查模式不写入、已跟踪文件增删、空 shell 拒绝；不生成任何阶段成功标记。该维护工具改动与硬件候选提交分别记录。

- **R006，临时监控包装器退出异常。** A70 的原生 build 已在 05:34:19 UTC 返回 `COMPLETE`，临时 shell 监控脚本因执行过程中修改自身日志路径随后报 EOF。主 Agent 核验原生 `build.json` 为 `completed`、sbt 正常生成 JAR、assembly 日志无失败，后续验证继续校验此 JAR。这不是仓库构建入口失败；原生记录与监控异常说明均保留，未补写任何成功标记。

- **R007，只读网表诊断的 Vivado 对象查询。** 首版辅助脚本在枚举部分 PCIe 引脚时发生 `Common 17-58`，已保留失败输出。故障在附加 CDC 诊断段，原生布局布线/STA 结果未受影响；修复脚本通过精确重取引脚对象后在新目录执行，不修改约束或成功记录。实际通过范围在下方审查记录中说明。

三组 IP 导入阶段还有 `Vivado 12-1504`：`create_ip` 已注册 PLL/XDMA IP，随后历史 `synth.tcl` 第 4 行 `read_ip` 再次读取同一路径，工具报告不再添加。它不等于缺少 IP 或 STA 违例，作为继承的重复导入提示保留；验收仍核对实际 IP、时钟和时序。综合步骤内部显示的“0 Critical Warnings”不能代替整份 Vivado 日志审查。

## 对照来源

旧 A70-P3 对照固定为 `/home/zhangsi/nm37-git-reproduce-fresh/a70-p3-build-java20-20261025-020151`，routed 报告日期 2026-10-25；对应 SHA256 在证据记录中。不能混用早期 A70/ShiftRightJam 实验或历史 P2/P3 构建顺序修复前的报告。

| 指标 | 旧 A70-P3 |
|---|---:|
| DUT 频率 | 70MHz |
| 全板 WNS / WHS | 0.047ns / 0.010ns |
| DUT WNS / WHS | 0.419ns / 0.010ns |
| Total LUT / Logic LUT | 378,248 / 372,342 |
| LUTRAM / SRL | 4,958 / 948 |
| FF | 71,330 |
| RAMB36 / RAMB18 / DSP | 52 / 0 / 288 |

新 A70 对旧 A70 用于检查迁移复现差异；新 A100/A110 对旧 A70 用于比较不同硬件配置。仿真周期与按频率换算的模型时间不代表板上端到端运行时间；此次不把过去未重新烧录的 A100/A110 软件测试当作硬件实测。

## 执行结果

A70-P3 已完成本次完整布局布线：全板 WNS=0.047ns、WHS=0.010ns、WPWS=0，DUT WNS=0.419ns、WHS=0.010ns，所有失败端点数为零。主 Agent 独立解析最终报告，确认时序 12 项、资源及占比、路由计数、约束覆盖和 CDC 分类数量与旧 A70-P3 完全一致。新 DCP SHA256 为 `dcc05fd3cbcac572db83d743c3912a0747c59f530feb7512f72754557364215d`。A100、A110 的原始及修复版也均已生成本次完整布局布线结果；A110 原生 CDC 末端门槛仍未通过，具体范围见下文。以下功能证据与受约束时序结论分别记录。

- A70-P3：新的生成器编译、累计器 24,394 个输出检查、倒数 525 次事务检查、三拍无输入约束形式等价及证明驱动正反例均通过。4×4 的 seq4/8、16×16 的 seq16/32 逐位通过；输入、配置、输出和全部 8 项 FSA 计数均与旧 A70-P3 相同。
- A100：新的生成器编译、PE/CMP 定向及调度验证、5 个 ControlSignalTest、3 项形式证明均通过。
- A110/APB55：上述生成器/PE/CMP/调度/形式验证通过，另有 HBM 独立时钟启动测试通过：8 种异步时钟场景、32,768 门控向量、3,362,863 项检查。
- A70 板级展开的 92 个 Verilog/SystemVerilog 文件逐字节等于旧 A70-P3，配置 JSON 和 PLL/XDMA/HBM Tcl 也相同。此结果证明本次展开未引入 RTL 变化，不能代替本次布局布线验收。

| A70 回归 | 旧/新 FSA execTime | 旧/新 mxBubble | 旧/新 mxActive | 旧/新仿真总周期 |
|---|---:|---:|---:|---:|
| 4×4, seq4 | 368 | 153 | 143 | 4,707 |
| 4×4, seq8 | 1,083 | 651 | 388 | 11,857 |
| 16×16, seq16 | 442 | 111 | 249 | 5,427 |
| 16×16, seq32 | 1,157 | 421 | 754 | 12,577 |

表中“旧/新”表示两个实际日志的数值完全相同。仿真总周期包含初始化和总线交互，不能作为 FSA `execTime`。`mxBubble` 在矩阵指令入口 ready 且无 valid 时计数；它不是 PE 空闲率，也不保证与 `mxActive` 互斥。


## 16×16 长序列功能回归

原始三个里程碑的 seq1024 均逐位通过，Q/K/V 三个输入哈希相同，实际与参考输出哈希均为 `b7f9f8ec3d9d6efc5f38c1f79b58ce911bb65a00f0b03f1e28a54d8fb2e9f131`。

| 配置（原始里程碑） | 内存端口 | FSA execTime | mxBubble | mxActive | dmaActive |
|---|---|---:|---:|---:|---:|
| A70-P3 | 1×256-bit | 775,909 | 382,899 | 532,032 | 150,734 |
| A100 | 8×64-bit | 775,904 | 219,217 | 601,728 | 141,952 |
| A110/APB55 | 8×64-bit | 775,904 | 219,217 | 601,728 | 141,952 |

三组原始指令均为 70,529，矩阵指令 12,416、DMA 指令 8,320、fence 1；仿真总周期均为 7,760,097。此表只比较各自固定功能模型中的计数，不提供实板运行时间或纯提频加速比。两个修复候选的 seq1024 也逐位通过，输出哈希和全部 8 项计数器均与对应原始里程碑本轮运行一致。A100 修复前后 92 个板级 RTL、A110 修复前后 97 个板级 RTL 逐字节相同；A110 的 FSAConfig 与 PLL Tcl 也相同。两个修复候选的编译、定向/形式、全部固定仿真和板级展开均已完成；主 Agent 独立复算各阶段记录列出的文件 SHA256 与 build 绑定，全部一致。


## 实际物理实现对比

下表来自本轮实际 routed 报告；原始 A100/A110 的时序、资源、路由计数与对应旧版本相同。清理无效约束的 A100 重新布局后有小幅结果变化，RTL 未变，不能将该差异当成新算术优化的收益。

| 实际运行 | 全板 WNS / WHS (ns) | DUT WNS / WHS (ns) | LUT | FF | RAMB36 | DSP |
|---|---:|---:|---:|---:|---:|---:|
| 旧 A70-P3 | 0.047 / 0.010 | 0.419 / 0.010 | 378,248 | 71,330 | 52 | 288 |
| 新 A70-P3 `8cc6b42` | 0.047 / 0.010 | 0.419 / 0.010 | 378,248 | 71,330 | 52 | 288 |
| 新 A100 原始 `f8650f9` | 0.049 / 0.010 | 0.534 / 0.010 | 355,692 | 140,263 | 60 | 288 |
| 新 A100 修复 `9b8911f` | 0.073 / 0.010 | 0.642 / 0.010 | 355,683 | 140,257 | 60 | 288 |
| 新 A110 原始 `b595900` | 0.114 / 0.010 | 0.802 / 0.010 | 355,981 | 140,324 | 60 | 288 |
| 新 A110 修复 `7deb8e3` | 0.114 / 0.010 | 0.802 / 0.010 | 355,981 | 140,324 | 60 | 288 |

A110 原始及修复版全板最差 WNS=0.114ns 属于 PCIe 复位 Recovery 检查：100MHz releaseSync 输出到 250MHz PCIe 寄存器 CLR/PRE，数据路径约 1.27ns。它不是 PE 普通 setup 路径，也不能单独证明所有异步复位释放安全；DUT 最差路径另报 0.802ns。

按器件实际可用资源 LUT 1,303,680、FF 2,607,360、RAMB36 2,016、DSP 9,024 计算：

| 本轮候选 | LUT 占用 | FF 占用 | BRAM 占用 | DSP 占用 |
|---|---:|---:|---:|---:|
| A70-P3 | 29.01% | 2.74% | 2.58% | 3.19% |
| A100 修复 | 27.28% | 5.38% | 2.98% | 3.19% |
| A110/APB55 修复 | 27.31% | 5.38% | 2.98% | 3.19% |

与旧 A70-P3 相比，A100 修复版 LUT 减少 22,565、FF 增加 68,927、RAMB36 增加 8；A110 修复版 LUT 减少 22,267、FF 增加 68,994、RAMB36 增加 8，DSP 均不变。这是完整版本的资源对照，不能把差异仅归因于某一个流水寄存器或本轮无效约束清理。

上述完成运行的 TNS、THS、TPWS 和失败端点计数均为零，DRC 无 Error/Critical，路由错误为零。A110 的 DUT 为 110MHz、HBM APB 为 55MHz；这些数字不能外推为未经实现验证的最高频率。

## CDC / 约束审查的范围

受约束 STA 通过与全板 CDC 正式签核分别记录。A100 原生 `physical.passed.json` 明确保留 `board_signoff=false` 和 `cdc_review_required=true`。A110 原始运行完成完整布局布线后，因没有本次 `cdc-review.json` 被原生后端拒绝；两次 A110 的 `physical.failed.json` 和外层失败状态原样保留。后端在审查异常时把该文件的 `constrained_sta_passed` 也设为 false；本报告“受约束时序通过”专指独立读取实际 WNS/WHS/失败计数、路由、DRC 的结论，并非声称原生整体验收 passed。后续审查在独立目录进行，不能把旧 DCP 审查或手工成功标记补到原构建中。原始 A110 的独立只读复审已正常完成，主 Agent 复算 113 份新报告、118 份原报告及 DCP 绑定，原产物未变。

- 30 个 HBM 未约束端点均限于未使用的 AXI1..15：15 个 ACLK 为 GROUND；BREADY/RREADY 的 fan-in 分别为同一 macro 的 BVALID_PIPE/RVALID_PIPE。READY 数据网络不是常量。该解释不覆盖实际使用的 AXI00。
- 8 条 `Invalid startpoint`：每 lane 的 vendor 通配符匹配 18 个 FDCE 和 3 个 CARRY8；组合 CARRY8 被选为起点导致提示。18 个目的 FDRE 存在，对应捕获路径仍有 false-path。不能把整个约束说成无效。
- `Non-existent path` 提示逐项与 clock interaction 对照；保留 vendor 时钟组，不新增 false-path 消提示。
- PCIe CPLL 的 144 条 CDC-15 是受控计数捕获：testclk_en 经两拍同步、ref 域 HOLD 等待到 0xF 后 UPDATE 捕获。结构核对不能替代 vendor 启动条件的动态验证。
- ResetWrangler 的 CDC-8 有三拍异步断言/同步释放链，但实际所报首级 ASYNC_REG 属性缺失。这是保留的物理实现改进项；本轮不扩大硬件改动，也不以“旧版也有”宣称 MTBF 或所有异步释放情形已证明。
- `prst_n` 是异步复位输入；A70/A100 实际进入 PCIe 内部的 16 个 CLR/PRE，A110 经新增释放同步链进入 3 个 CLR。缺少同步数据 input-delay 的解释不等于完整复位签核。

A110 相对原生 CDC baseline 的 36 条新增项已逐条归类：28 条 ResetWrangler 资格/去抖复位、2 条 vendor 同步器前组合复位、5 条 vendor 冷复位目的、1 条缺失 ASYNC_REG 的 CDC-8。35 条结构解释不是安全放行，全部 disposition 仍为 pending。另一位 Agent 核对原始 A110 本次 332 个唯一源/目的 pin、发现集合和证据哈希后确认该边界；该复核仅绑定原始 DCP，不能移用为修复版 DCP 的审查。修复版另完成自身 DCP 的 332 个唯一源/目的 pin 取证；主 Agent 独立校验 DCP 哈希、pin 数量和所报首级缺失 ASYNC_REG 的属性，见 `a110-fixed-root-structural-check.json`。两版严格 CDC 验收均未通过。冷复位 10000 周期资格延时仅限制新增 fundamental-reset 上游，不能推广到 vendor hot-reset、link-down 等运行时事件。

逐项结构记录和本次 DCP 哈希绑定见各配置审查证据。此次任务未执行新实板测试，未导出 bit，未创建发布标签。


## 文件保存与旧工程保护

持久产物归档目录为 `/home/zhangsi/tmp/ICT-FSA-reproduction-20261028`，按 `a70/`、`a100/`、`a110/` 保存实际构建、失败尝试、阶段状态、仿真结果、DCP、原始报告和只读诊断。Git 只收录源码、说明及小型审查证据，不提交 JAR/DCP 等大产物。归档是证据副本；其中原生记录仍绑定执行时的 `/tmp/ict-fsa-reproduce-20261028/...` 路径，不篡改路径或成功标记来伪装成在新位置构建。原工作区保留。已复算五次运行共 163 个 JAR/DCP/构建记录/阶段证据/报告文件，归档副本与实际执行产物哈希完全相同，见 `archive-core-checksums.json`。

详细配置记录中的相对证据路径以归档中对应 `a70/`、`a100/`、`a110/` 为基准。复现应使用 README 的新 clone 和新输出目录，不能把归档目录直接当作已迁移的可续跑工作区。

旧 A70/A100/A110 的 DCP 与关键报告哈希再次校验未变。旧 FSA 的 HEAD 和原有状态条目保留；任务期间观察到两个新增未跟踪板测目录 `nm37-a100-programmed-board-tests-20261028/`、`nm37-a110-programmed-board-tests-20261028/`，未修改它们，也未将其作为本轮复现证据，不推断创建者。因此不宣称旧工作区的整个 `git status` 字节不变。另一个旧工具仓的 HEAD/状态均未变。


## 分配置详细记录

- [A70-P3 复现与旧基线对照](evidence/reproduction-20261028/a70-REPRODUCTION.md)，[机器验收摘要](evidence/reproduction-20261028/a70-acceptance.json)。
- [A100 原始/修复版完整复现](evidence/reproduction-20261028/a100-A100_REPRODUCTION.md)，[CDC/约束结构审查](evidence/reproduction-20261028/a100-CDC_CONSTRAINT_REVIEW.md)，[机器汇总](evidence/reproduction-20261028/a100-FINAL_SUMMARY.json)。
- [A110 原始/修复版完整复现](evidence/reproduction-20261028/a110-A110_REPRODUCTION.md)，[CDC/HBM/约束审查](evidence/reproduction-20261028/a110-A110_CDC_CONSTRAINT_REVIEW.md)，[机器汇总](evidence/reproduction-20261028/a110-final-summary.json)。

## 本轮验收结论

三组独立任务完成实际源码编译、定向/形式验证、固定仿真、seq1024 和完整布局布线；A100/A110 清理无效约束后另外以独立源码和新输出完整重跑，共五次物理实现。A70 与旧 A70-P3 的功能、RTL、时序、资源一致。A100/A110 原始候选也复现了各自旧结果；修复候选的实际数字见上表。

保留两组约束清理提交，操作说明与维护工具修复进入交付主分支。原始里程碑不移动；未 push、未打标签、未导出 bit、未在本轮执行实板测试。**这不是三组严格 CDC/整板发布签核均通过的结论**：A110 原生整体门槛仍失败，实际同步器属性缺口和运行时复位协议范围作为后续硬件验收项保留，不能使用旧 review 或编写 accepted 消除。

主 Agent 复算阶段证据文件哈希、全部 routed 核心指标及持久归档；维护工具三项隔离 Git 测试通过，主分支 A110 输入锁检查通过。新增 README/恢复命令经 `bash -n` 语法检查，实际 A110 只读复审入口已运行生成报告，未声明其 CDC 接受通过。
