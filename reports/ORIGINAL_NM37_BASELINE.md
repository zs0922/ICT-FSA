# original-nm37-civ 基线复现记录

## 输入与来源

本次真实构建源码提交为 `eb16cafbc0ce4710e6c2e4f58a53f39c4e348a81`；本报告及随后 README 的提交仅补充证据和操作说明，不属于本次已构建源码身份。`profiles/current.json` 保持历史 `NM37` 标识。

基线来自 ICT-FSA `00e021c635cd31d013cf00fd24cba687dc0b4be5`，旧 FSA `57344208e4b88e4eed87e3bf4e9dd9a790d06e84`。上游 FSA `f4051d9e6e1aac80b74fee9c9cff0096e19f7acf`、easyfloat `44e1c369659c2c397548d2aecfc4ded3a74a111e`、FPGA shells `d7c353201c61f1879afdb2fddf3c52283d450147`，依次只应用 U280 FSA/shell 与 NM37 FSA/shell 迁移补丁；详细哈希见 `docs/history/NM37/source-provenance.json`。

358 个自研核心和板级文件（含符号链接）与来源 manifest 逐文件 SHA256 一致。相对 U280 迁移提交 `3d1714de`，NM37 初始迁移的 `generators/fsa/src` 与 `generators/easyfloat` diff 为空。因此这里没有后续 P0/P1/P2/P3、ShiftRightJam、A100 流水或高频复位优化。

板级 `EmptyNM37Config` 为 16×16、fp16 输入/fp32 累加、单内存端口、70 MHz DUT。4×4 是固定 Verilator 回归阵列，不是板上阵列。生成的 harness PLL 输入请求100 MHz、输出请求70 MHz。

## 执行环境与结果

独立源码 `/tmp/ict-nm37-work`；输出 `/tmp/ict-nm37-validation/build-attempt02`，所有下载缓存独立复制，未复用旧 JAR、RTL、仿真器或 DCP。

- doctor通过：JDK20.0.2、firtool1.75.0、Verilator5.022、Vivado2020.2_AR75986、GCC/G++13.3。
- 172个固定第三方仓库按依赖锁完成本地恢复；FSA与easyfloat各自uv环境按冻结锁安装。
- `python3 -m unittest discover -s tests -p 'test_ict*.py'`：25项通过。
- Scala/JAR build：COMPLETE；JAR SHA256 `03bbf91e9520cdb8357a0e02604334bedd644db7463c2b07073c774a1cd1a8a6`。
- sim4 seq4与seq8：均与PyEasyFloat逐位相同，seed=0；simulator SHA256 `354d538853a63f50deeb0640d59c5f66e7e828dd6defd1c816467c7f482d46ab`。
- 板级elaborate：COMPLETE。

首次尝试在受限沙箱中因sbt Unix socket `Operation not permitted`失败；保留日志，使用新的输出attempt02在允许本地IPC的执行环境重跑。此错误不是原硬件或Scala功能错误。前置依赖恢复必须完成后再build；过早启动被源码完整性检查拦截，不可把依赖检查PASS当成构建完成。

## 验证边界

未运行实板测试；统一板测runtime尚未声明历史`NM37` profile。本报告不声称实板70MHz运行或CDC已经验收；静态时序结果见下文完整布局布线终态。未重新烧录的其他版本日志不能用作本基线实板性能。原始基线即使目标时序失败也保留，不为使其通过加入性能优化。

## 本次完整布局布线终态

`implement` 于2026-11-02 09:01:25 UTC完成，器件`xcvu37p_CIV-fsvh2892-2L-e`，真实DUT周期14.286ns。最终严格setup/hold/pulse检查全部通过；这里使用完整布线后报告，不使用综合或路由中间估算值。

| 指标 | 最终值 |
|---|---:|
| 全局及DUT WNS | +0.001 ns |
| 全局TNS / setup失败端点 | 0 / 0 |
| 全局及DUT WHS | +0.010 ns |
| 全局THS / hold失败端点 | 0 / 0 |
| WPWS / TPWS / pulse失败端点 | 0 / 0 / 0 |
| DRC Error / Critical Warning | 0 / 0 |
| DRC Warning / Advisory | 1234 / 24 |

`audit/bus_skew.txt`全表18项约束均MET，最小裕量2.389ns。

70 MHz本次实现通过，但1ps setup裕量非常小，不表示有额外提频余量，也不保证其他工具版本产生相同结果。全局最差setup路径位于DUT，起点`mxControl/fsm_list_1/accumTimer_reg[0]/C`，终点`accRAM_sram/banks_subBanks_sram_mem_1/banks_subBanks_sram_mem_1_0_ext/mem_0_0/ram_reg_0_31_238_251/RAMG_D1/I`。完整路径在`obj/audit/dut_setup_top100.txt`：53级，数据延迟13.918ns，其中逻辑5.462ns（39.244%），布线8.456ns（60.756%）。该路径包含DSP及进位逻辑，不能仅按起点名字解释成纯控制分发路径。

最差DUT hold为`sa/cmp_in_pipe_b_9_mantissa_reg[1]/C`到`sa/cmp_array_9/oldMax_mantissa_reg[1]/D`，数据延迟0.503ns（逻辑0.124ns、布线0.379ns），时钟偏斜0.432ns，最终裕量0.010ns。

| 整板资源 | 使用量 | 器件总量 | 使用比例 |
|---|---:|---:|---:|
| LUT | 380891 | 1303680 | 29.22% |
| FF | 72500 | 2607360 | 2.78% |
| DSP | 320 | 9024 | 3.55% |
| BRAM tiles | 81.5 | 2016 | 4.04% |
| URAM | 0 | 960 | 0% |

LUT细分：逻辑375522，分布式RAM3814，SRL1555。BRAM由80个RAMB36E2和3个RAMB18E2组成。以上包含PCIe/HBM/shell，不能当作纯FSA资源。原始NM37不等同于优化后的A70-P3。

CDC仍有30项Critical（CDC-7=12、CDC-10=2、CDC-11=16）、171项Warning（CDC-8=1、CDC-15=170）；这里只归档，没有逐项关闭。`check_timing`列出30个因常量时钟未约束的HBM BREADY/RREADY端点以及1个无input delay输入。原始exceptions也全部保留；这些未决项不被“时序通过”自动豁免。DRC Warning主要为DSP未配置输入/输出寄存器的性能建议，不为消除它们而更改原始设计。

完整产物根目录`/tmp/ict-nm37-validation/build-attempt02`；DCP SHA256为`091b3edfc332c8366346699445a3a2d2bfbd8aaed58ca82b62a66bc4a5cba565`。精简证据JSON包含报告哈希、阶段收据及来源核验。

独立Spike/FESVR首次安装配方另外用锁定`76858cc3`及GCC13.3实跑通过（configure、make、install、双库/头文件/ldd检查）。本次硬件构建使用原有`/home/zhangsi/riscv`安装，不能将工具安装验证写成整套硬件已做零缓存冷启动。

## 实验bit实际导出

在同一冻结源码上执行`python3 scripts/fsa.py export --out /tmp/ict-nm37-validation/build-attempt02 --result-out /tmp/ict-nm37-validation/bits-attempt01`，独立重开DCP、复查时序与DRC后，`write_bitstream`于2026-11-02 09:09:42 UTC成功完成。`sha256sum -c SHA256SUMS`中bit和配置两项均OK。

- bit：`/tmp/ict-nm37-validation/bits-attempt01/NM37_EXPERIMENTAL.bit`
- bit SHA256：`46df2586ff7622002f9d164966a4f8195f8981cc9c16847fea2b8611ac632d26`
- 配置 SHA256：`d8c3330d60ee335601401365e6fa4de774b53bb099dccc0afd464048b262a6ba`
- `experiment.json`状态为`exported`，用途`EXPERIMENTAL_BOARD_TEST`，`release_approved=false`、`cdc_review=not_closed_by_export`。

没有烧录，没有push。报告与文档在独立`/tmp/ict-nm37-docs`克隆提交；构建源码`/tmp/ict-nm37-work`始终保持实际验证提交`eb16caf`，所以其status/export身份绑定仍然有效。后续文档提交与eb16caf的差异不涉及硬件或构建脚本；重现本次精确构建可checkout该完整验证SHA，阅读最新分支README获取补充环境步骤。
