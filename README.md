# ICT-FSA original-u280：U280 初始移植基线

本分支保存 U280 初始移植及运行必需的正确性修复，不包含 NM37 后续 P0/P1/P2/P3、ShiftRightJam、PE/CMP 流水或复位复制优化。它是板卡移植起点，不是新的性能优化版本。

## 来源与范围

- ICT-FSA 整理起点：`3d1714de26aeaad172461bd96e6c8fc26e63109a`。
- 旧 FSA 源码：`50344530d2fa83f4a507789bf6d6508a3d494806`。
- 上游 Chipyard/FSA 集成祖先：`54671054fedcd2c1f65bb2dd6939abdaf8071814`。这里的 original 指 VCA-EPFL 的 FSA/U55C 集成，不是今天 Berkeley Chipyard 的主分支。
- 固定依赖和补丁：[来源清单](docs/history/U280/source-provenance.json)、[原始文件哈希](docs/history/U280/source-files.json)、[历史补丁](docs/history/U280/patches/u280)。补丁已经体现在源码中，构建时不要再次应用。
- 板上配置：`EmptyU280Config`，16×16 PE、单内存端口、DUT 70 MHz；器件 `xcu280-fsvh2892-2L-e`。
- 本入口的功能回归只提供 4×4 阵列、seq=4/8。这不表示板上阵列是 4×4，也不能用这个功能模型预测 HBM 带宽。

FSA 历史补丁只修改 Python `engine.py`、`xdma_mmio.py` 和 `main.py`：按 PCI 设备查找 XDMA、允许 done 状态再次启动、准确获取 libc 错误以及选择 U280 配置。easyfloat 和 FSA Scala 算术核心未被 U280 补丁修改。板级 shell 补丁增加器件、约束及实现脚本。为未来比较性能，仍需固定 Python 主机软件；不能把不同主机软件的差异全部归于硬件。

## 1. 独立获取源码

当前仅本地提交，尚未推送。下面 `ICT_REPO` 指向包含本分支的本地仓库；发布后可改为远程 URL。

```bash
export ICT_REPO=/absolute/path/to/ICT-FSA
export WORK="$HOME/ict-fsa-original-u280"
mkdir -p "$WORK"
git clone --no-hardlinks --branch original-u280 "$ICT_REPO" "$WORK/source"
export SRC="$WORK/source"
cd "$SRC"
git rev-parse HEAD | tee "$WORK/source-commit.txt"
export BUILD_OUT="$WORK/build-attempt01"
```

对外交付时按验收记录固定完整 commit，使用 `git checkout --detach <commit>`；不要在已有构建源码中切换版本。不要在交互式 tmux 中设置 `set -euo pipefail`。

## 2. 检查工具并获取锁定依赖

先按[环境说明](docs/reproduction/environment.md)设置 JDK20.0.2、firtool1.75.0、Verilator5.022、Vivado2020.2_AR75986、GCC/G++13.3 和 RISCV/FESVR。不需要先运行 A70/A100/A110；本分支没有后续形式验证套件，不必安装该说明中的 Yosys。

```bash
python3 scripts/fsa.py doctor
python3 scripts/fsa.py deps --plan
python3 scripts/fsa.py deps --report "$WORK/dependencies.json"
uv sync --frozen --python 3.13 --project "$SRC/generators/fsa/python"
uv sync --frozen --python 3.13 --project "$SRC/generators/easyfloat"
export FSA_PYTHON="$SRC/generators/fsa/python/.venv/bin/python"
"$FSA_PYTHON" -c 'import numpy, torch, pyeasyfloat; print("Python imports OK")'
```

已有本机依赖可将第三条替换为 `python3 scripts/fsa.py deps --local-source /absolute/path/to/complete-source --report "$WORK/dependencies.json"`。只复制固定版本的第三方源码，不复制 JAR、RTL、仿真器或 DCP。依赖下载中断后保留缓存重试；现有目标若版本不符，先保留现场并使用新源码目录。

## 3. 编译与功能仿真

```bash
python3 scripts/fsa.py build --out "$BUILD_OUT"
python3 scripts/fsa.py sim --out "$BUILD_OUT" --array-size 4
python3 scripts/fsa.py status --out "$BUILD_OUT"
```

`build` 生成本次 Scala/Chisel JAR。`sim` 编译 Verilator 仿真器并运行 seq=4、8 的 PyEasyFloat 对照；只有阶段完成记录与数值检查通过才能记为功能回归通过。此基线不执行 `verify`、8×8 或16×16回归入口。

## 4. 板级 RTL 与布局布线

```bash
python3 scripts/fsa.py elaborate --out "$BUILD_OUT"
python3 scripts/fsa.py implement --out "$BUILD_OUT"
python3 scripts/fsa.py status --out "$BUILD_OUT"
```

`elaborate` 生成 U280 的16×16板级 RTL/IP；`implement` 完整运行 Vivado，保留 routed DCP、资源与时序报告。查看输出中的 `report/`、`audit/`，特别是实际 DUT70 MHz、setup/hold、脉宽和 DRC。脚本入口存在不等于布局布线已通过。

## 5. 导出 bitstream

```bash
export EXPORT_OUT="$WORK/bits-attempt01"
python3 scripts/fsa.py export --out "$BUILD_OUT" --result-out "$EXPORT_OUT"
cat "$EXPORT_OUT/experiment.json"
(cd "$EXPORT_OUT" && sha256sum -c SHA256SUMS)
```

导出会重新检查实际 DCP 的时序和 DRC，不需要手写 CDC 审查 JSON。成功才生成 `U280_EXPERIMENTAL.bit`；这一步不烧录，也不证明板上数值正确。CDC/约束的未决项应与实验记录一起保留。

统一 `test` 命令目前只验证 NM37 的设备映射，会拒绝 U280；不能照抄 NM37 BDF/设备 ID 来声称完成 U280 板测。U280 烧录和主机运行需根据实际设备单独验收，历史操作见[原迁移 README](docs/history/U280/original-README.md)。本阶段重点恢复源码、编译、仿真和实现入口。

## 失败恢复与结果保留

查看 `$BUILD_OUT.ict-state/` 中对应阶段日志和 receipt。前一阶段成功不代表后一阶段成功；不要补写成功标记。工具或依赖错误先修环境，已有失败阶段保留，使用新的输出目录重新开始；源码发生改变时使用新 checkout 和新输出。下载缓存可以复制/复用，既有构建结果不得覆盖。

本次独立验证状态见[验收记录](reports/ORIGINAL_U280_BASELINE.md)。
