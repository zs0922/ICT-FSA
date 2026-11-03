# original-np19a 迁移验证记录

## 来源与实际构建版本

实际验证源码提交：`bcaa1c76`（完整 SHA 见证据 JSON）。源码在 `/tmp/ict-np19a-work`，本次正式输出在 `/tmp/ict-np19a-validation/build-attempt03`。报告与 README 的后续提交只整理证据，不冒充本次构建源码身份。

父基线为 `original-nm37-civ` 的 `87cd26500fc88f7051771e3cb1670001375c6b1f`。`generators/fsa` 与 `generators/easyfloat` 相对该版本无差异；没有引入 P3、ShiftRightJam 优化或 PE 流水改变。原始 NM37 的来源核验见其历史报告。NP19A 增加独立 AXI 顶层及 DDR4/PCIe shell，不能用 NM37 的 routed 结果替代本板结果。

器件由用户指定为 `xcvu19p-fsva3824-2-e`。板级约束筛选了用户 XDC 的130条语句，保留的语句未改变引脚或电平值。参考附件和 NEXST 固定版本哈希见 `docs/history/NP19A/source-provenance.json`。

## 已完成的验证

- JDK20.0.2、firtool1.75.0、Verilator5.022、GCC/G++13.3、Vivado2024.2环境检查通过。
- 172个锁定依赖按本地来源独立恢复，使用本分支的Python环境与锁文件。
- 统一入口build完成，生成本次输出目录中的非空JAR。
- 统一入口sim4完成；seed0下seq4/seq8与PyEasyFloat逐位一致。
- 统一入口elaborate完成，生成16×16 fp16/fp32设计、16GB地址空间与256位访存接口。
- Vivado BD校验通过；MIG型号MTA16ATF2G64HZ-2G3，AXI512位/地址34位，窄突发已开启。
- 复位派生极性检查通过；Clock Wizard输入为No_buffer，生成RTL中不再插入第二个IBUF。
- 开发工程RTL端口/约束检查通过：0 Error、0 Critical Warning，无未匹配时钟端口。
- 现有复现工具25项单元测试在最终代码上通过；构建缓存修复由attempt03实际生成新JAR验证。

4×4计算回归不覆盖整个PCIe/DDR板级系统，也不代表16×16已上板通过。尚无本次NP19A实板数据，运行时间、bubble及DDR有效带宽不能填写为实测值。

## 复现中发现并修复的问题

| 问题 | 修复/处理 |
|---|---|
| 独立顶层没有EmptyChipTop，模型与DUT同名又影响内存层次拆分 | 模型为NP19AFSACore，DUT为AXI4FSA |
| AXI UserYanker要求明确flight cap | 沿用原板级每ID cap8 |
| XDMA BAR translation拒绝0x8000（需64KB对齐） | BAR从0开始，包装层将控制地址映射到内部0x8000；计算核心和软件偏移不变 |
| proc_sys_reset辅助复位低有效 | 接常数1，自动检查派生极性 |
| 差分输入已缓冲，Clock Wizard仍默认添加IBUF | PLL设置PRIM_SOURCE=No_buffer |
| sbt-assembly换输出目录返回旧JAR路径，touch又可能生成空JAR | 禁用assembly输出缓存，保留下载/编译缓存；用非空检查替代touch |

attempt01在完成build/sim/elaborate后，因发现重复时钟输入缓冲主动停止综合；不是时序验收结果。attempt02被非空JAR检查拦截，没有进入仿真或实现。两次输出和日志都保留。attempt03按新提交、新输出重新执行，未复制旧JAR、RTL或DCP冒充新结果。

## 物理实现与实板边界

Vivado2024.2完整布局布线通过，539,620条可布线网络全部完成，布线错误0。`report_bus_skew`列出的20条汇总记录最小slack为+3.203ns，没有VIOLATED。全局所有已约束setup/hold/pulse-width检查通过：

| 指标 | 结果 |
|---|---:|
| FSA频率 / 周期 | 70MHz / 14.286ns |
| 全局WNS / TNS | +0.058ns / 0 |
| 全局WHS / THS | +0.010ns / 0 |
| 全局WPWS / TPWS | 0.000ns / 0 |
| FSA域WNS / WHS | +0.142ns / +0.013ns |
| 内部未约束端点 | 0 |
| DRC Error / Critical Warning | 0 / 0 |

| 整板资源 | 使用 | 器件总量 | 占用 |
|---|---:|---:|---:|
| CLB LUT | 402,192 | 4,085,760 | 9.84% |
| CLB registers | 100,142 | 8,171,520 | 1.23% |
| DSP | 323 | 3,840 | 8.41% |
| BRAM tiles | 83.5 | 2,160 | 3.87% |
| URAM | 0 | 320 | 0% |

CLB registers包括100,141 FF和1个AND/OR寄存单元；BRAM为83个RAMB36E2和1个RAMB18E2。以上包含DDR/PCIe基础设施，不是FSA核心独占资源。DRC仍有1252条Warning（含DSP流水建议等），没有修改原始计算流水来消除这些建议，也没有降低DRC严重性。

未运行JTAG烧录或板测；未push。DDR校准、PCIe枚举、DMA访存、attention逐位结果及实际性能仍须在NP19A上验证。


## CDC与启动边界

导出阶段的详细`cdc.txt`报告CDC-3 Info272条、CDC-9 Info17条、CDC-12 Critical2条、CDC-15 Warning2729条。DRC的0 Critical不代表CDC的0 Critical，两种检查不可混用。

两条CDC-12均落到同一四级同步器：

- `np19a_i/ddr4_mig/inst/u_ddr4_mem_intfc/u_ddr_cal_top/calDone_gated_reg/C`
- `np19a_i/xdma_ep/inst/pcie4c_ip_i/inst/user_reset_reg/C`
- 共同终点：`np19a_i/core_reset/U0/EXT_LPF/ACTIVE_HIGH_EXT.ACT_HI_EXT/GENERATE_LEVEL_P_S_CDC.SINGLE_BIT.CROSS_PLEVEL_IN2SCNDRY_IN_cdc_to/D`

`implement.tcl`先将校准完成与XDMA复位释放相与、取反，送入`core_reset/ext_reset_in`。厂商`proc_sys_reset_v5_0_vh_rfs.vhd`中该输入进入`cdc_sync`（C_SINGLE_BIT=1、C_MTBF_STAGES=4），之后经过复位滤波和释放序列；不是异步信号直接驱动FSA数据寄存器。告警原因是同步器前存在来自两个时钟域的组合扇入。

本实验使用“上电→PLL锁定→DDR校准/PCIe就绪→释放核心→主机发任务”的启动约定；就绪信号稳定后才开始计算。运行期热复位/掉锁/校准丢失不支持保留在途任务，须重新初始化。当前保留这两条结构告警及全部CDC-15记录，没有新增全局false path或填造豁免报告。尚未完成所有CDC-15逐条释放审查，不能把这次导出称为CDC发布验收完成。后续如要求运行中独立复位和自动恢复，应拆分同步就绪信号、设计停机/清空协议并重新验证实现。


`check_timing -verbose`中no_input_delay的唯一端口为`pcie_ep_perstn`，no_output_delay的唯一端口为`c0_ddr4_reset_n`。二者属于外部复位，不是遗漏的同步计算数据总线；普通单周期input/output delay不能证明复位脉宽、上电顺序或DDR初始化协议。保持厂商复位结构及IP约束，实板需确认PERST、DDR初始化和校准。no_clock、multiple_clock、generated_clock问题及组合环均为0；不以虚构delay数值掩盖这两个提示。


## 实验比特流与复现入口

导出完成，`sha256sum -c SHA256SUMS`验证bit/config均为OK。

- 本次已构建源码：`bcaa1c761794445c6a6e70caec07a5842a06a217`。
- 比特流：`/tmp/ict-np19a-validation/bits-attempt01/NP19A_EXPERIMENTAL.bit`。
- bit SHA256：`eebe2bb9ca279463c5e5ca263d0e21bada851c325712eba904c050b7eb949f66`。
- 配套配置：`/tmp/ict-np19a-validation/bits-attempt01/FSAConfig.json`。
- DCP SHA256：`97968c42c5c0112ecf213c4ae290968b9a19622a692d6e2d0b3a9a2d8cd5b96c`。
- 阶段收据、报告哈希及导出清单见[证据JSON](original-np19a-evidence.json)。

根目录[README](../README.md)提供独立clone、依赖恢复、环境检查、build/sim/elaborate/implement/export，以及烧录和attention命令。后续文档提交不改变本次硬件源码；重新从该文档提交构建时使用新的输出目录。这里的`/tmp`是本次验收暂存位置，交付时应保留bit、配置、清单、校验和及报告，勿依赖临时目录永久存在。未push，未声称实板或完整CDC发布验收通过。
