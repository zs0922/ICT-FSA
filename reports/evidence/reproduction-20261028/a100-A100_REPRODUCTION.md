# ICT-FSA A100 独立复现记录（2026-10-28）

源码固定为 `f8650f9576bf681bfae38a2ab40718fc2ace4262`，工作分支 `codex/ict-reproduce-a100`。操作依据是交付主分支手册快照 `/tmp/ict-fsa-reproduce-20261028/handbook/README.md`，校验和见 `handbook.sha256`。当前干净源码位于 `source-attempt02`，输出 `build-attempt02`，日志状态在同级 `build-attempt02.ict-state`；所有路径相对本报告所在任务根。

没有复制旧 JAR、RTL、仿真器、DCP 或正式验收标记。只复用了下载缓存的独立副本与已安装工具；两个源码 Python 环境和固定形式环境重新创建。172 个依赖从离线 bundle 按固定锁恢复。旧 FSA 源码及既有构建仅作只读对照。

## 已执行的阶段

- doctor 检查 JDK20.0.2、firtool1.75.0、Verilator5.022、Vivado2020.2_AR75986、GCC/G++13.3.0、RISCV/FESVR 库通过。
- 独立工具回归 25 项通过。
- build 成功生成本次约 1.1GB 的 Scala/Chisel JAR。sbt assembly实际编译193秒；完整阶段含输入校验，05:37:03–05:41:25 UTC。
- verify：FPMac 延迟等价14,394例、CMP max/diff20,169例、PE EXP2扫描90例；五种矩形/方阵调度验证；5项控制信号测试全部通过。
- 形式等价：CMP最大值组合SAT、CMP减法流水归纳、MAC流水归纳全部通过。后两者证明从任意初态经过一个流水转换后的全部周期，不是完整PE协议的形式证明。
- fresh Verilator 4×4 seq4/8、8×8 seq8/16、16×16 seq16/32共6项，实际输出与PyEasyFloat逐位一致。
- NM37板级RTL展开通过；16×16 seq1024额外仿真已逐位通过；原版与修复版完整Vivado implement均exit0，通过受约束STA、DRC、routing和bus-skew检查。

## 发现与处理

1. **R001 文档环境缺口**：交付环境将conda Python3.10置于PATH前端，而文档用`python3 -m venv`创建形式环境；固定`platformdirs==4.13.0`要求Python≥3.11。安装失败日志已保存；改用独立`uv venv --python 3.13`环境，5个固定包及Yosys版本验证成功。问题先报告root，由root告知用户并统一修正文档，本固定源码未修改。
2. **R002 执行沙箱限制**：首次build在sbt BootServerSocket绑定本地Unix socket时被沙箱拒绝，尚未开始Scala编译。保留`source`、`build-attempt01`及日志；重新clone与恢复依赖、环境至`source-attempt02`，用新输出在允许本地socket的环境完整重跑。未关闭验证、未补写seal。
3. **R003 比较模型差异**：A100固定sim16生成8路64-bit DMA，旧A70-P3固定sim16为1路256-bit，跨版本仿真周期不能解释为纯提频/流水优化收益。A100板级RTL仍是1路256-bit。实际生成证据见`sim16-topology-evidence.json`与`board-rtl-evidence.json`。

4. **R004 无效历史约束**：`nm37-config.xdc:10` 的 `MAX_FANOUT 128` 目标 `*sram_accRAM_fullWrite_0_addr_REG*` 匹配零个cell，产生`Common 17-55`。同警告已存在于旧A100日志，实际RTL使用新的`addr_r...r_3`链。先向root报告，由root告知用户后，只移除无效命令及过时说明，没有将约束改套至新寄存器、没有修改PE流水/时钟/RTL。修复提交`9b8911f4e9e5c6af49fe6b6287e9c88ee1031352`保存在`fix-repo`的`codex/a100-reproduction-fix`分支；`source-fixed`从该提交独立clone，输出`build-fixed-attempt01`。原冻结run完整保留。
5. **R005 锁维护工具**：刷新输入锁时发现维护脚本仅更新`source_hashes`、不更新既有`shell_hashes`，导致修改后的XDC二重校验不一致。先报告root，由root告知用户并单独修复维护工具；上述A100修复提交明确同步同一XDC的两个hash。构建用修复提交保持冻结，未混入维护工具提交。

## 硬件身份与旧版本对照

实际板级RTL显示PE的`downMacD/downBypassD`、CMP的`bypassD/useBypassD`、PE MAC调用链中的`RawFloat_FMA_16.adderOutAbs`时钟寄存，以及InputDelayer输出后的`r_0..r_15`一级寄存。PLL请求100MHz。不能仅用FSAConfig JSON的hash证明流水深度，详细文件hash、行号与参数日志已保存于`board-rtl-evidence.json`。

本次板级gen-collateral全部92个`.sv/.v`与旧A100原始字节一致，没有归一化注释或路径，见`generated-rtl-vs-legacy-a100.json`。旧A100同拓扑16阵列固定回归的输出hash及exec/bubble/active计数也与本次一致。

| 仿真阵列/序列 | execTime | mxBubble | mxActive | dmaActive | 逐位结果 |
|---|---:|---:|---:|---:|---|
| 4×4 / 4 | 368 | 153 | 162 | 16 | 通过 |
| 4×4 / 8 | 1,083 | 646 | 464 | 48 | 通过 |
| 8×8 / 8 | 385 | 134 | 210 | 40 | 通过 |
| 8×8 / 16 | 1,100 | 535 | 642 | 116 | 通过 |
| 16×16 / 16 | 437 | 103 | 267 | 76 | 通过 |
| 16×16 / 32 | 1,152 | 295 | 824 | 220 | 通过 |
| 16×16 / 1024 | 775,904 | 219,217 | 601,728 | 141,952 | 通过 |

以上是DUT原生FSA printf计数，不是TestDriver总模拟周期、主机执行时间或实板时间。`AXI4FSA.scala:176`起规定：状态active期间execTime逐拍递增；首条矩阵指令fire后，矩阵指令接口ready且无valid时增加mxBubble；fsa.io.busy时增加mxActive。二者并非互斥分类，mxBubble不等于PE空闲率。

修复版重新执行build、verify、sim4/8/16、elaborate与额外seq1024全部通过。六项固定回归输出hash及八项原生计数均与原run和旧A100一致；seq1024亦与原run逐位结果/计数一致（输出SHA256 `b7f9f8ec3d9d6efc5f38c1f79b58ce911bb65a00f0b03f1e28a54d8fb2e9f131`）。修复版92个板级RTL与原run完全相同；正式P&R仍从本次新JAR和新RTL开始，未复用原run DCP。

## 完整布局布线与旧结果对照

原run为`build-attempt02`，P&R于05:53:47–07:04:36 UTC完成；修复run为`build-fixed-attempt01`，06:24:16–07:33:00 UTC完成。均从本次JAR重新生成RTL/IP并从头综合、布局、布线，没有从旧DCP继续。两个最终`physical.passed.json`均为`constrained_sta_passed=true`、`board_signoff=false`、`cdc_review_required=true`。

这里指定旧A70-P3对照为`/home/zhangsi/nm37-git-reproduce-fresh/a70-p3-build-java20-20261025-020151`，不是早期其它A70候选。旧A100为`/home/zhangsi/nm37-git-reproduce-fresh/a100-build`。旧报告hash见`legacy-report-hashes.json`。

| 指标 | 旧A70-P3 | 旧A100 | 新A100原提交 | 新A100修复提交 |
|---|---:|---:|---:|---:|
| DUT周期/ns | 14.286 | 10.000 | 10.000 | 10.000 |
| DUT setup WNS/ns | 0.419 | 0.534 | 0.534 | 0.642 |
| DUT hold WHS/ns | 0.010 | 0.010 | 0.010 | 0.010 |
| 全板WNS/ns | 0.047 | 0.049 | 0.049 | 0.073 |
| 全板WHS/ns | 0.010 | 0.010 | 0.010 | 0.010 |
| 全板WPWS/ns | 0.000 | 0.000 | 0.000 | 0.000 |
| 最差bus-skew slack/ns | 2.579 | 3.142 | 3.142 | 3.284 |
| 完全路由net数 | 477,602 | 497,497 | 497,497 | 497,468 |
| routing error | 0 | 0 | 0 | 0 |

四列TNS/THS/TPWS和对应失败端点数均为0。新原提交的全板/局部时序、路由数、bus skew与旧A100完全相同。修复版产生略有差异的物理优化/布线结果；仅删除不匹配的旧约束，不将这点裕量变化描述为新的功能或流水优化收益。

| 资源 | 旧A70-P3 | 旧A100 / 新原提交 | 新修复提交 | 器件容量 |
|---|---:|---:|---:|---:|
| 总LUT | 378,248（29.01%） | 355,692（27.28%） | 355,683（27.28%） | 1,303,680 |
| Logic LUT | 372,342 | 350,958 | 350,949 | — |
| LUTRAM | 4,958 | 3,774 | 3,774 | — |
| SRL | 948 | 960 | 960 | — |
| FF | 71,330（2.74%） | 140,263（5.38%） | 140,257（5.38%） | 2,607,360 |
| RAMB36 | 52（2.58%） | 60（2.98%） | 60（2.98%） | 2,016 |
| DSP | 288（3.19%） | 288（3.19%） | 288（3.19%） | 9,024 |

以上为全板资源。旧A70与新A100的不同包含此前已有流水、存储映射和算术优化组合，不能归因为本轮删除一条无效约束。本轮修复相较新原提交只差9 LUT/6 FF，RTL92个文件及所有功能回归保持一致。生成的8个SDC/XDC/IP配置Tcl也全部逐字节相同；锁中唯一改变的build输入是失效命令所在XDC，原run实际routed selector也确认为0个对象，见`constraints-comparison.json`。

新原提交DUT最差setup为reset catcher replica到CMP valid寄存器，9.082ns数据延迟中8.907ns是布线（98.073%，1级LUT）。修复版最差setup仍由同reset catcher replica到`sa/mesh_1_6/expIndex_reg[0]/R`，8.794ns中8.663ns是布线（98.510%，1级LUT）。这与A100已知复位分发瓶颈一致，未恢复成PE长组合链。

## CDC / 约束审查范围

原版和修复版均有99 Info、173 Warning、30 Critical，302条CDC detail与旧A100逐行一致。两者均保留30个unused HBM constant-clock端点和1个`prst_n`输入延迟提示；8条Invalid startpoint、10条Non-existent path也相同。实际新DCP审查见`CDC_CONSTRAINT_REVIEW.md`，不复制旧审查或制造全板放行标记。

原DCP只读probe已完整exit0：15个unused HBM AXI1..15 ACLK均GROUND，30个ready数据端点来自各自macro VALID_PIPE反馈；CPLL每lane旧exception start选择器实际匹配18 FDCE+3 CARRY8，解释Invalid startpoint而非寄存器缺失；CDC7/10/11的真实cell、属性、fan-in已分类。既有ResetWrangler同步器首级缺ASYNC_REG是真实属性缺口，作为后续CDC改进记录。未做所有复位动态/多lane协议/MTBF或实板冷启动的独立证明。

修复版独立新DCP的相同probe亦完整exit0：同样查完170个CDC目的、30个HBM端点及15个常量时钟，CPLL选择器和prst_n端点集相同。忽略允许变化的LOC/BEL后，所查CDC cell类型、ASYNC_REG、时钟和fan-in结构与原run一致，见`netlist-comparison.json`及两份`netlist-review-summary-*.json`。布局布线通过不自动代表实板通过。

修复版Common17-55已消失；实现日志仍记录既有两条IP重复导入`Vivado12-1504`及两条`report_timing -nets`过时选项`Vivado12-1569`。这些不等于DRC Error/Critical；本轮按已告知范围保留，不擅改vendor IP或放宽时序。

## 交付证据

- `commands.txt`：实际命令；`env.sh`和`env-fixed.sh`：独立环境；`dependencies-attempt02.json`和`dependencies-fixed.json`：172个依赖固定恢复记录。
- `run-summary.json`/`run-summary-fixed.json`：阶段与形式/仿真结果；`sim-extra-1024-summary.json`/`sim-extra-1024-fixed-summary.json`：额外1024验证和原生计数。
- `board-rtl-evidence.json`/`sim16-topology-evidence.json`：真实生成RTL的流水、接口、JVM参数和PLL证据；`fixed-vs-original.json`、`generated-rtl-vs-legacy-a100.json`、`sim-vs-legacy-a100.json`：语义与旧输出对照。
- `build-attempt02-physical-evidence/summary.json`和`build-fixed-attempt01-physical-evidence/summary.json`：实际报告hash/资源/CDC/约束/最差路径；`physical-comparison.json`：新旧实测差异。
- 原版新DCP SHA256：`5420a3f09a23b726ad749f158d8b138440884022b3d3709b4b17aff59ff3874d`。
- 修复版新DCP SHA256：`1e1fc9f7fbf88035fae084cbf21c935c0f8d9b6d2be9bf36a1beeb8036f9592e`。
- 修复commit：`9b8911f4e9e5c6af49fe6b6287e9c88ee1031352`，可从任务根`fix-repo`读取；源/输出和第一次环境失败输出全部保留。

本任务未导出bitstream、未烧板、未push、未打验收标签。根Agent统一验收、归档与本地提交报告，不在已构建源码中追加报告commit改变源码身份。
