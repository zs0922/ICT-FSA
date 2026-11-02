# 原始 FSA 与板卡移植基线

这里管理可追溯的原始起点，不替换既有 A70-P3/A100/A110/A120/A150 分支。本轮只本地提交，未 push，未创建验收标签。分支具体提交与实测范围见 [本轮记录](../../reports/ORIGINAL_BASELINES_20261102.md)。

## 选择正确的起点

| 分支 | 硬件来源 | 用途 |
|---|---|---|
| `original` | VCA-EPFL/chipyard-fsa `54671054fedcd2c1f65bb2dd6939abdaf8071814`，FSA/U55C 集成 | 保留上游核心、原始 gitlink，作为新板卡移植来源 |
| `original-u280` | ICT-FSA `3d1714de26aeaad172461bd96e6c8fc26e63109a`，旧 FSA `50344530d2fa83f4a507789bf6d6508a3d494806` | U280 初始移植及必要正确性修复 |
| `original-nm37-civ` | ICT-FSA `00e021c635cd31d013cf00fd24cba687dc0b4be5`，旧 FSA `57344208e4b88e4eed87e3bf4e9dd9a790d06e84` | NM37-CIV 初始移植，不含 P0～P3 |

`ucb-bar/chipyard` 是框架上游。这里的 FSA/U55C 集成来源是 [VCA-EPFL/chipyard-fsa](https://github.com/VCA-EPFL/chipyard-fsa)，并非今天的 Berkeley Chipyard 主分支。FSA 项目的 [上游说明](https://github.com/VCA-EPFL/FSA) 也指向该集成仓库。

原始集成的三个核心依赖锁定为：

| 路径 | 原始 gitlink |
|---|---|
| `generators/fsa` | `f4051d9e6e1aac80b74fee9c9cff0096e19f7acf` |
| `generators/easyfloat` | `44e1c369659c2c397548d2aecfc4ded3a74a111e` |
| `fpga/fpga-shells` | `d7c353201c61f1879afdb2fddf3c52283d450147` |

U280/NM37 基线沿用 ICT-FSA 已物化、由主仓直接跟踪的核心；补丁来源见各自 `docs/history/<profile>/source-provenance.json`。构建时不再向核心应用旧补丁。original 则保留上游的子模块结构，不能把两个流程混用。

历史结构也不同：`original` 导入上游历史，原有 ICT-FSA 物化历史从 U280 提交开始，两者没有共同 Git 祖先。这里保留来源映射而不改写已有历史；不要直接 merge 两条无关历史来移植板卡。未来新板卡应选定一种源码组织作为起点，按来源清单提取必要板级适配。

“未优化”允许板级必需适配和历史正确性修复，例如 XDMA 设备访问与完成后再次启动。不包含后来的主机 MMIO 映射复用性能提交，也不包含 ShiftRightJam、PE/CMP/scratchpad 流水或 HBM 独立 APB 优化。各分支具体保留内容以源码差异和来源报告为准。

## 从本地仓库获取独立源码

以下是尚未发布时的操作。`ICT_REPO` 必须指向已经包含三个新分支的本地 ICT-FSA 仓库。未来发布后才能换为 GitHub 地址。

```bash
export ICT_REPO=/absolute/path/to/ICT-FSA
export BASELINE=original-nm37-civ  # 可换为 original 或 original-u280
export WORK="$HOME/ict-fsa-$BASELINE-attempt01"
mkdir -p "$WORK"
git clone --no-hardlinks --branch "$BASELINE" "$ICT_REPO" "$WORK/source"
export SRC="$WORK/source"
export COMMIT="$(git -C "$SRC" rev-parse HEAD)"
git -C "$SRC" checkout --detach "$COMMIT"
printf '%s\n' "$COMMIT" > "$WORK/source-commit.txt"
cd "$SRC"
```

然后执行**这个 checkout 的 README**。每个基线有自己的环境、依赖和构建步骤。不要继续执行集成分支 README 中的 A150 流程，也不要在已有构建中途 checkout 新版本。若 source 或输出目录已存在，改用新的 WORK；不要删除旧结果。

U280/NM37 使用 `scripts/fsa.py`：deps → doctor/Python 环境 → build → sim4 → elaborate → implement → export。original 保留上游结构，使用其 README 所述原始 make 入口。固定 4×4 仿真并不表示板上阵列为 4×4；U280/NM37 板级配置为 16×16。

## 每一步证明什么

| 步骤 | 产生的证据 | 不代表什么 |
|---|---|---|
| 来源核验 | 上游 commit、子模块 pin、补丁清单和核心目录树 ID | 不证明硬件功能 |
| 依赖准备和 doctor | 指定依赖可恢复、工具版本可用 | 不证明 Scala 或 RTL 能编译 |
| build | 本次源码新生成的生成器 JAR 和编译日志 | 不是 FPGA 综合 |
| sim4 | 新 Verilator 仿真器、小序列输出与参考值的比较 | 不证明板上 16×16 性能 |
| elaborate | 板级 RTL、IP 参数和生成配置 | 不证明布局布线时序 |
| implement | 新综合/布局布线、时序、资源和检查报告 | 非负 WNS 不等于 CDC 全部正确 |
| export | 对应 DCP 经时序/DRC检查后导出的 bit 和哈希 | 不等于已烧录或板测通过 |

实验导出不要求为了普通板测手写 CDC 审查 JSON；它仍必须满足目标时序和阻断性 DRC 条件。若原始实现本身不满足目标频率，保留失败报告，不在“original”基线里偷偷加入性能优化来让时序通过。

下载缓存可复用；JAR、RTL、仿真器、DCP、bit 不从旧构建复制。本轮验证记录区分实际构建 commit 与随后增加报告的文档提交；文档提交没有自动获得新的一次完整构建证明。

## 后续扩展边界

本轮不创建 NP19A/VP1902 分支，不做板卡×优化配置重构，也不将 NEXST 合入。先让这三个起点具有清晰来源与可执行入口。后续性能矩阵需要另外固定内存模型、主机软件、实际时钟和输入，并记录真实烧录身份。
