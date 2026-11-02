# A150/APB100 迁入 ICT-FSA（2026-11-02）

## 迁移身份与范围

起点为 ICT-FSA `462a341eb250f74a3d0c7ca415ef765f693c1839`。迁入另一对话“优化FSA的频率”中已完成离线验收和 bitstream 导出的 A150/APB100 源码：

- 原实验仓库：`/home/zhangsi/tmp/FSA-m1/nm37-apb100-20261101/A150/src`。
- 原源码/记录提交：`338ca77682c2a8c84106cc9f7db98cca264867dd`。
- 原硬件实现提交：`32480c2630fea1073c7666ea0e4c2f75a49ac358`。
- 新 ICT-FSA 候选分支：`codex/nm37-a150-apb100`。迁移先完成本地提交，随后用户授权推送 A150 分支及默认分支 README。发布仅更新文档，不改变硬件或验收结论，不创建验收标签。

**本次完成的是源码迁移、工具测试、源文件锁核对和文档更新，没有重跑新 ICT-FSA 提交的 Scala 编译、硬件功能仿真、布局布线或板测，也没有为新提交导出 bit。** 历史报告和新候选的验收范围分别记录，不能把原实验 DCP/bit 当作本次重建结果。

## 相对 A120 的变化

| 项目 | A120/APB60 | A150/APB100 |
|---|---:|---:|
| DUT/FSA/HBM AXI MHz | 120 | 150 |
| HBM APB MHz | 60 | 100 |
| DUT:APB 频率比 | 2:1 | 3:2 |
| ResetWrangler 100µs 去抖计数 | 6000（13位） | 10000（14位） |
| PE/CMP 内部流水 | 1/1拍 | 1/1拍 |
| scratchpad/accumulator FMA 延迟 | 2/3拍 | 2/3拍 |

硬件源码仅迁入 NM37 `Configs.scala` 的频率集合和 `TestHarness.scala` 的 APB 选择变化，两文件与原实验最终版本一致。保留源实验允许的 130/140/160 数值，但本次没有为它们建立统一 profile 或声称它们时序通过；本分支只提供 A150/APB100。

FSA/easyfloat 共 89 个跟踪文件与迁移前 ICT-FSA 及原 A150 逐字节一致。HBM 启动 RTL、调度、PE 流水和复位复制策略没有新增修改。更紧频率约束可改变工具的映射、布局和复制结果，资源不保证相同。

原实验的 55 个 shell 运行输入中，ICT-FSA 仅 `xilinx/nm37/constraints/nm37-config.xdc` 因此前清除无效 MAX_FANOUT 而不同；此次保留该修复。shell 直接由主仓跟踪，不恢复 gitlink、不在构建时应用历史 patch。

## 统一构建入口

新增 `scripts/nm37-a150/`、A150 baseline 和 bitstream Tcl，更新当前 profile、依赖锁身份、维护工具、板测频率映射和 CLI 支持列表。依赖 pin 与 A120 相同。

相对原实验后端，仅 `check.py`、`prepare-shell.py` 适配 vendored shell，`run.sh` 适配源快照说明和现有明确错误提示；其余审计器/启动测试/验证器保持原实验最终字节。源锁重新绑定当前 Git 跟踪文件及模式，不用旧锁冒充新源码身份。

新的 HBM 时钟检查要求 150/100MHz、3:2 同源时钟，周期舍入界限为 `0.0005*(1+1.5)+1e-9 ns`；拒绝旧 APB75、错误 DUT120 等配置。启动回归的四组生产比例场景更新为 150:100。

根 README 增加 A150 本地 clone → 环境 → build → verify → sim4/8/16 → elaborate → implement → export；新环境补齐 Spike/FESVR 安装。A120 保留已发布的固定 `462a341` 入口，其他原分支不移动，不在已有构建中切换源码。

实验导出继续使用 `python3 scripts/fsa.py export`，不用严格后端 `run.sh bitstream`。统一入口不要求手写 CDC 审核 JSON 或 physical.passed.json；它绑定本次实现的 routed DCP/config 并重新检查目标 DUT150、整板 max/min/pulse 时序和 DRC。CDC 报告保留，不以实验导出关闭 CDC 问题。实现未生成 DCP、时序不通过或 DRC 阻塞时，导出仍应失败。

输出名为 `A150-APB100_EXPERIMENTAL.bit`，避免和历史 A150/APB75 的 `NM37_A150.bit` 混淆。

## 历史实现证据（不是新仓重建）

详细原报告：[NM37_A150_APB100](../optimization-reports/NM37_A150_APB100.md)。原证据逐字节保存在 [历史归档](../optimization-reports/evidence/nm37-a150-apb100/README.md)，包含原失败状态、后续 CDC 审核、最终验收和 bitstream 导出记录；大型 DCP/bit 不提交 Git。

| 指标 | 原实验 A150/APB100 |
|---|---:|
| DUT setup WNS | +0.049ns |
| 整板最差 Max / Hold | +0.047ns / +0.010ns |
| 最差脉宽裕量 | 0ns |
| LUT / FF | 364525 / 140546 |
| DSP / RAMB36 | 288 / 60 |
| 已布线网络 / 路由错误 | 497602 / 0 |
| CDC Critical / Warning | 25 / 173 |
| 实际板测 | 未执行 |

整板最差 Max 为 APB100→DUT150 复位 Recovery，不是普通数据 setup。裕量较小，不外推更高频率。周期数相同时 150/120=1.25 是理论加速比，不是板测结果。

原实验两条新增 CDC-15 来自去抖计数器增加的 bit13，经原 RTL、routed 连接和 24 组数字复位回归审核为既有结构扩展。原实验最终 `constrained_sta_passed=true`，`review_required=false`，但 `board_signoff=false`。继承的 ASYNC_REG 属性缺失、模拟亚稳态验证边界、30 个未使用 HBM 无约束端点和 prst_n 覆盖边界未被本次迁移修复。原 cdc-review.json 绑定旧 DCP，不复制到新 build 目录套用。

原 bitstream 文件位于旧构建 `build01/bitstream/NM37_A150.bit`，大小 84989293 字节，SHA256 为 `6f146b8cb0f0c14bf08f7b2ba2962a35725e08611f16cc1fb1e52413aace26c3`。该文件仍保留在旧构建；新仓需按 README 自行重建和导出。

## 本次实际验证

- 统一 CLI、离线依赖工具、源锁维护测试 30 项通过，包含 A120 和 A150 分派及输出环境；未运行真实 FPGA 构建。
- A150 Python 审计器测试 44 项通过，使用 Python 3.14.6（固定 AST 序列化指纹版本）。日常 FSA Python/形式工具仍为 Python 3.13。
- HBM Tcl 结构/比例正反例 34 项、reset/reaudit 实际频率门禁正反例 12 项通过。
- Bash 语法、A150 build/verify/sim 分派 dry-run、源文件内容/模式、55 个 shell 输入哈希检查通过。
- 169 个原归档文件 SHA256 及 gzip 可解压检查通过；归档 SHA256SUMS 自身 SHA256 为 `70c824b22b7716fd35330a474099b0a43cf0f695de37d498efa9f403f68f4a08`。
- 当前候选完整第三方依赖尚未在迁移 checkout 初始化；依赖计划检查不代表下载或编译完成。历史 24 组复位回归记录作为证据保留，本次没有重跑该历史 RTL 仿真。
