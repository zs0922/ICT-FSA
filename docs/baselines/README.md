# 原始 FSA 与板卡移植基线

这里管理可追溯的原始起点，不替换既有 A70-P3/A100/A110/A120/A150 分支。三个基线通过同名 GitHub 分支交付，尚未创建验收标签；历史验收报告中的“未 push”指验证完成时的状态。分支具体提交与实测范围见 [本轮记录](../../reports/ORIGINAL_BASELINES_20261102.md)。

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

## 在151服务器获取固定源码

仓库地址为 `https://github.com/zs0922/ICT-FSA.git`，默认分支 `codex/ict-fsa-integration` 提供本入口。三个基线固定为：

| 分支 | 固定提交 | README 已实际验证范围 |
|---|---|---|
| original | `474e92dc018df7a7a818aa329db967ebb829108c` | 编译、4×4仿真、U55C RTL展开；未执行U55C完整布局布线 |
| original-u280 | `ab28e170feb2c29d347dd476f45fd29456cf0d7b` | 编译、4×4仿真、16×16完整实现及实验bit导出 |
| original-nm37-civ | `87cd26500fc88f7051771e3cb1670001375c6b1f` | 编译、4×4仿真、16×16完整实现及实验bit导出 |

在151的Bash/tmux终端逐条执行。每个版本使用新目录，不在已有构建目录中 pull/checkout，不必先运行优化版本。

```bash
export ICT_REPO=https://github.com/zs0922/ICT-FSA.git
export BASELINE=original-nm37-civ  # 三选一：original / original-u280 / original-nm37-civ
case "$BASELINE" in
  original) export COMMIT=474e92dc018df7a7a818aa329db967ebb829108c ;;
  original-u280) export COMMIT=ab28e170feb2c29d347dd476f45fd29456cf0d7b ;;
  original-nm37-civ) export COMMIT=87cd26500fc88f7051771e3cb1670001375c6b1f ;;
  *) echo 'BASELINE错误：请重新选择，不要继续' ;;
esac
export WORK="$HOME/ict-fsa-$BASELINE-reproduce-attempt01"
mkdir "$WORK"  # 已存在时改用attempt02；不删除原目录
git clone --branch "$BASELINE" --single-branch "$ICT_REPO" "$WORK/source"
export SRC="$WORK/source"
git -C "$SRC" checkout --detach "$COMMIT"
git -C "$SRC" rev-parse HEAD  # 应与上表完整commit一致
printf '%s\n' "$COMMIT" > "$WORK/source-commit.txt"
cd "$SRC"
```

每条命令成功后再继续。基线README中“本地尚未发布”是验证时保留的历史描述；上面的GitHub获取与固定commit步骤替代各README第1节，之后直接从第2节准备环境，不要再次clone。

**original-u280 / original-nm37-civ：** 先按本分支 `docs/reproduction/environment.md` 设置真实工具路径（含RISCV/FESVR），再执行本分支README第2～5节：

```bash
export BUILD_OUT="$WORK/build-attempt01"
export EXPORT_OUT="$WORK/bits-attempt01"
python3 scripts/fsa.py doctor
python3 scripts/fsa.py deps --plan
python3 scripts/fsa.py deps --report "$WORK/dependencies.json"
uv sync --frozen --python 3.13 --project "$SRC/generators/fsa/python"
uv sync --frozen --python 3.13 --project "$SRC/generators/easyfloat"
export FSA_PYTHON="$SRC/generators/fsa/python/.venv/bin/python"
"$FSA_PYTHON" -c 'import numpy, torch, pyeasyfloat; print("Python imports OK")'
python3 scripts/fsa.py build --out "$BUILD_OUT"
python3 scripts/fsa.py sim --out "$BUILD_OUT" --array-size 4
python3 scripts/fsa.py elaborate --out "$BUILD_OUT"
python3 scripts/fsa.py implement --out "$BUILD_OUT"
python3 scripts/fsa.py export --out "$BUILD_OUT" --result-out "$EXPORT_OUT"
python3 scripts/fsa.py status --out "$BUILD_OUT"
(cd "$EXPORT_OUT" && sha256sum -c SHA256SUMS)
```

串行执行；任一步失败就查看该阶段日志，不继续后续阶段。正常全新U280构建无需使用历史DCP恢复参数 `--build-source-commit`。两个版本均为名义70MHz、板上16×16，仿真4×4并非板上规模。两者尚未实板验收，历史profile不能直接套用优化版统一板测命令。

**original（U55C）：** 使用其原始make入口，不能运行上面的 `scripts/fsa.py`。先设置 `export ORIGINAL_WORK="$WORK"`，然后从该分支README第2节配置工具、初始化固定子模块及两个Python环境，依次执行第3节编译、第4节seq4/seq8仿真、第5节U55C实现。第5节命令为：

```bash
cd "$ORIGINAL_WORK/source/fpga"
make SUB_PROJECT=u55c CONFIG=EmptyU55CConfig TOP=EmptyChipTop bitstream
```

原始U55C完整实现尚未在本轮运行，此命令不代表已有U55C时序通过证据。U55C/U280 bit不能烧到NM37。所有版本都需先读对应README的环境要求，不能将此汇总替代工具安装步骤。

下载缓存可复用，生成的JAR/RTL/仿真器/DCP/bit使用独立目录。已有本地完整依赖时可按各分支README使用只读本地依赖来源；公网下载受网络和上游服务可用性影响。

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
