# A120/APB60 迁入 ICT-FSA

## 范围与来源

本次从另一对话“优化FSA的频率”的实际源码和归档迁入 A120-C0：旧 FSA 提交 `04b31f054d698eb1075be6a82de52cba603ca976`，包含 `f577b977` 的 120MHz 审计修正及 `b6fbf163` 的 Vivado 周期舍入修正。ICT-FSA 起点为 `bac930f0751bd128487f3f5b75f5709313653f5d`，新候选分支为 `codex/nm37-a120-apb60`。本次仅本地提交，没有 push，不创建验收标签，不修改旧 FSA 或旧构建结果。

本提交是移植后的待重建候选。**本次没有执行 Scala 全量编译、Verilator 硬件功能回归、Vivado 全量布局布线、bitstream 导出或板测。** 用户将在独立目录按 README 完整重建。下列旧实现数字不能作为新提交的验收结果。

## 代码变化

- `fpga/src/main/scala/nm37/Configs.scala` 允许 `fsa.nm37MHz=120`；`TestHarness.scala` 在此配置下选择 APB60，其余配置保留 APB55。DUT/HBM AXI=120MHz、APB=60MHz、HBM reference=100MHz。
- PE/CMP 内部一拍、scratchpad 读边界两拍、accumulator FMA 三拍不变；FSA/easyfloat 89 个跟踪文件与历史 A120 逐字节一致，与移植前 ICT-FSA 也一致。
- 保留 ICT-FSA 的直接跟踪 shell 和此前无效 MAX_FANOUT 清理。历史 A120 的 55 个运行 shell 输入中仅 `xilinx/nm37/constraints/nm37-config.xdc` 因该清理不同；不重新应用旧 patch。
- 迁入 `scripts/nm37-a120/` 后，仅适配 `check.py`、`run.sh`、`prepare-shell.py` 的 vendored shell 校验、输入快照及明确错误提示。其余审计器、验证器与历史最终源码相同；保留周期舍入上界 0.0015ns + 1e-9ns，独立绝对频率检查仍在。
- `profiles/current.json`、依赖锁、源文件锁、统一 CLI 和维护工具支持 A120-APB60。第三方依赖 pin 与 A110 相同；只更新 profile 身份。脚本仍要求先完成 verify、4/8/16 固定仿真及 elaborate，才能 implement。
- 旧 A70/A100/A110 分支不移动。切到其他里程碑必须使用对应完整提交，不能在已有构建中途替换 profile。

## 历史实现证据（不是本次新仓重建）

完整历史报告：[NM37_A120_APB60](../optimization-reports/NM37_A120_APB60.md)。归档保持原始内容，包括原失败记录及其后的独立复审，不覆盖失败标记。

| 指标 | 历史 A120/APB60 |
|---|---:|
| DUT setup WNS | +0.235ns |
| 全局 WNS / WHS | +0.041ns / +0.010ns |
| setup / hold / pulse 失败端点 | 0 / 0 / 0 |
| LUT / FF | 356,619 / 140,554 |
| DSP / RAMB36 | 288 / 60 |
| routed / routable nets | 497,809 / 497,809 |
| 新比特流 / 新板测 | 未执行 |

历史六组固定仿真输出和周期与 A110 相同；周期不变时按 110→120MHz 换算得到 1.0909 倍加速，仅是理论时间换算，不是板测结果。

历史 `board_signoff=false`。CDC 25 Critical / 171 Warning / 98 Info 与其旧 A110 基线一致，只表示未新增差异，不表示这些告警全部正确；30 个未使用 HBM 端点和 `prst_n` 覆盖边界仍在。ICT-FSA 复现中记录的 PCIe 复位同步器 ASYNC_REG 缺失及热复位/链路重启验证范围没有在本次频率迁移中修复。新实现仍须检查自己的报告，不能复制旧 review JSON 当作通过证据。

## 本次实际完成的检查

- 统一工具、离线依赖恢复和源锁维护测试：29 项通过，包括新增 A120 分派/输出环境测试。
- A120 审计器 Python 测试：44 项通过。
- HBM Tcl 结构/周期检查：34 个正反例通过；包含 8.333/16.667ns 舍入值，拒绝错误 110/55MHz、错误 APB55、超出舍入界限等。
- 实际 reset/reaudit Tcl 频率门禁：12 个正反例通过。
- Bash 语法、A120 源锁内容/模式和 55 个 vendored shell 输入哈希通过；CLI build dry-run 指向 A120 后端。这些是工具检查，不是硬件仿真。
- 历史归档 435 个文件逐文件校验存储及解压 SHA256，通过。inventory SHA256 为 `e9e75d420541d015462bdc05e6d541be8076d09bdbf1bdece8cc8a3f8a9131db`。
- 本次未初始化完整第三方依赖；`deps --plan` 仅检查锁定获取计划，不代表依赖下载完成。

## 用户重建与导出

按根 README 的“A120/APB60 从哪里开始”建立新 checkout，然后执行第 2–6 节，使用该 checkout 自己的 `scripts/fsa.py`。无需另一个 integration-tools 仓库，也不运行历史 patch/prepare-shell 修改源码。

完整顺序为 `doctor → deps → 两个 uv sync → build → verify → sim 4/8/16 → elaborate → implement → export`；工具和形式验证环境先按环境文档配置。额外 seq1024 不代替固定回归。

`implement` 的真实失败原因以日志为准。如果只剩 CDC 审查未完成且实际布局布线成功、routed DCP/config 已记录，可用统一 `export` 做实验导出；它重新检查 DCP 的 DUT120、整板 setup/hold/pulse 和 DRC。不会关闭 CDC 问题，不要求手写 JSON。综合/布线失败或时序不通过时不能导出。导出前也要从本次 `hbm_audit/properties.txt` 核对 APB 周期约 16.667ns 和 AXI 周期约 8.333ns，并检查 HBM/reset 审计错误；通用实验导出并不替代这些结构审查。

成功输出 `$EXPORT_OUT/A120-APB60_EXPERIMENTAL.bit`、FSAConfig、experiment.json 和 SHA256SUMS。保留完整构建及 `.ict-state`。要上板再执行 README 第 7–9 节，必须真正烧录并使用本次烧录 receipt，不能只切换环境变量。
