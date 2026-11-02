# original-u280 独立复现验收（2026-11-02）

结论：原始U280硬件完成独立编译、功能仿真、完整布局布线，修正工具的STA周期身份检查后已成功导出实验bit。未烧录、未板测，CDC/约束逐项审查未闭环。旧仓库、旧分支和旧构建不变。

## 固定来源与证据范围

- 整理起点：`3d1714de26aeaad172461bd96e6c8fc26e63109a`，旧FSA来源`50344530d2fa83f4a507789bf6d6508a3d494806`。
- 实际build/sim/elaborate/route源码：`c9b39717ec6bd5fc5ac98e998b7f9d6c95fef05f`。
- 实际恢复审计/导出工具：`b6fb959`；此后的报告和环境说明提交不冒充重新运行全部硬件流程。新加入export的bus-skew报告命令已通过独立同DCP审计验证，本次bit由b6fb959导出。
- 本地源码`/tmp/ict-u280-work`，结果`/tmp/ict-u280-run/build-attempt02`，阶段receipt在相邻`.ict-state/`。
- 172个锁定依赖恢复；355个文件和1个symlink共356项fpga/FSA/easyfloat历史来源哈希完全匹配。FSA U280补丁只有主机Python修复，无Scala算术改动、easyfloat改动、P0/P1/P2/P3。保留历史两个ILA及dbg_hub。
- 工具：JDK20.0.2、firtool1.75.0、Verilator5.022、Vivado2020.2_AR75986、GCC/G++13.3；入口Python3.10.14，算法Python3.13.14。依赖和下载缓存复制到独立目录，未复用旧JAR/RTL/DCP。

## 各阶段

| 阶段 | 结果 |
|---|---|
| doctor、两套uv frozen | 通过 |
| 原入口回归 | 25项通过 |
| 修复后入口+恢复负例 | 27项通过 |
| build | 成功，本次JAR生成 |
| sim4 seq4/seq8 | 两例均与PyEasyFloat逐位一致 |
| elaborate | 成功，板级16×16、fp16/fp32、单内存端口 |
| 完整综合/布局/布线 | 完成，post_route.dcp保留 |
| 原implement验收 | 在时钟身份精度检查失败，receipt原样保留 |
| 独立恢复审计/export | 严格时序/DRC通过，bit导出成功 |
| bus-skew补充审计 | 18条约束全部MET，最差+2.884ns |
| 板测 | 未执行 |

第一次build在沙箱中因sbt Unix socket权限失败，日志保留在build-attempt01.ict-state；允许本机通信后用新输出重建。sim与elaborate有并行执行差异，日志确认sim先生成共享tapeout.jar，elaborate报告up-to-date未重写；交付README要求串行，避免潜在竞争。

## 工具错误与修复

U280 MMCM实际参数为输入300 MHz、MULT=119.875、DIVCLK=30、CLKOUT=17.125，名义输出恰好70 MHz。历史输入时钟约束使用3.333 ns，STA推导周期3.333×30×17.125/119.875=14.284285714 ns，显示14.284ns/70.007MHz。旧工具与1000/70比较的0.001ns容差因此错误拒绝。

修复仅增加profile的已知STA周期元数据，并让审计检查使用该周期；容差仍0.001ns，所有setup/hold/pulse-width门槛仍为非负。未修改IP、XDC、RTL、频率或物理策略。报告频率不是板上晶振实测，性能换算仍应明确名义70MHz。

`export --build-source-commit`核验原source receipt、DCP/config哈希、祖先关系与严格工具变更白名单，只读取旧结果并写全新目录。原failed implement不改成成功。机器可读记录见[original-u280-validation.json](original-u280-validation.json)。

## 最终时序和资源

| 指标 | 结果 |
|---|---:|
| 全局/DUT WNS | +0.003ns |
| TNS / failing endpoints | 0 / 0 |
| 全局/DUT WHS | +0.010ns |
| THS / failing endpoints | 0 / 0 |
| 全局WPWS / TPWS | 0 / 0 |
| LUT | 381056 / 29.23% |
| FF | 72510 / 2.78% |
| DSP | 320 / 3.55% |
| BRAM tile | 81.5 / 4.04%（RAMB36=80，RAMB18=3） |

最差路径位于`clk_out1_harnessSysPLL`：`dutDomain/fsa/fsa/mxControl/fsm_list_1/accumTimer_reg[0]/C`到`dutDomain/fsa/fsa/accumulator/accUnit_1/reciprocal/reg_r_exp_reg[8]/D`。Data Path Delay13.830ns，其中logic4.731ns(34.208%)、route9.099ns(65.792%)，60逻辑级。裕量很小，不据此推导更高频率保证。

导出前DRC无Error/Critical Warning，保留1233普通Warnings/22Advisories；bitgen命令自身完成记录0 Critical Warnings/0 Errors。CDC、未约束端点和exceptions报告已保存，未将其等同于功能或CDC验收通过。

## 产物

- bit：`/tmp/ict-u280-run/bits-attempt01/U280_EXPERIMENTAL.bit`
- SHA256：`6bf687c68da923859f6196bab0c828dcba173362d4340335fbc2cc81a06a0832`
- 配套配置与报告：同目录`FSAConfig.json`、`experiment.json`、`timing.txt`、`utilization.txt`、`drc.txt`、`cdc.txt`、`dut_setup_top100.txt`等。
- bus skew：`/tmp/ict-u280-run/bus-skew.txt`；只读脚本`bus-skew-audit.tcl`和运行日志相邻。
- `sha256sum -c SHA256SUMS`通过。

补充Spike/FESVR从零安装流程已由独立工具验证`/tmp/ict-spike-baseline-validation/validation.json`通过（pin76858cc3、GCC13.3、双库/头文件/ldd）。该新安装没有用于上面已经完成的硬件构建，不混写证据。
