# ICT-FSA：版本选择与统一构建流程

**以original-nm37为例：选择版本 → 设置环境 → 恢复依赖 → 编译/验证/仿真 → 布局布线 → 导出bitstream。** U280、NP19A及NM37优化版本沿用这条流程，具体替换项见第2节。`original`（U55C）仍使用上游make入口，请单独按[original README](https://github.com/zs0922/ICT-FSA/blob/474e92dc018df7a7a818aa329db967ebb829108c/README.md)执行，不使用下方统一入口。

## 1. 版本与commit对照表

| 版本 | Git分支 | 应切换到的完整commit | 对应完整流程 |
|---|---|---|---|
| **original** | `original` | `474e92dc018df7a7a818aa329db967ebb829108c` | [README](https://github.com/zs0922/ICT-FSA/blob/474e92dc018df7a7a818aa329db967ebb829108c/README.md) |
| **original-nm37** | `original-nm37-civ` | `87cd26500fc88f7051771e3cb1670001375c6b1f` | [README](https://github.com/zs0922/ICT-FSA/blob/87cd26500fc88f7051771e3cb1670001375c6b1f/README.md) |
| **original-u280** | `original-u280` | `ab28e170feb2c29d347dd476f45fd29456cf0d7b` | [README](https://github.com/zs0922/ICT-FSA/blob/ab28e170feb2c29d347dd476f45fd29456cf0d7b/README.md) |
| **original-np19a** | `original-np19a` | `8407bdd8d4bd6d0aae56a1a549353f8c35f2124f` | [README](https://github.com/zs0922/ICT-FSA/blob/8407bdd8d4bd6d0aae56a1a549353f8c35f2124f/README.md) |
| **nm37-A70-P3** | `codex/nm37-a70-p3` | `8cc6b42536334892b88f6214f39d3afe5daa2504` | [README](https://github.com/zs0922/ICT-FSA/blob/8cc6b42536334892b88f6214f39d3afe5daa2504/README.md) |
| **nm37-A100** | `codex/a100-reproduction-fix` | `9b8911f4e9e5c6af49fe6b6287e9c88ee1031352` | [README](https://github.com/zs0922/ICT-FSA/blob/9b8911f4e9e5c6af49fe6b6287e9c88ee1031352/README.md) |
| **nm37-a110** | `codex/a110-reproduction-fix` | `7deb8e3e9416f2f3d25df9d45a5f65fc38302cda` | [README](https://github.com/zs0922/ICT-FSA/blob/7deb8e3e9416f2f3d25df9d45a5f65fc38302cda/README.md) |
| **nm37-a120** | `codex/nm37-a120-apb60` | `462a341eb250f74a3d0c7ca415ef765f693c1839` | [README](https://github.com/zs0922/ICT-FSA/blob/462a341eb250f74a3d0c7ca415ef765f693c1839/README.md) |
| **nm37-a150** | `codex/nm37-a150-apb100` | `1e07e6b09422435ce2914cbbb8a34bf793df708b` | [README](https://github.com/zs0922/ICT-FSA/blob/1e07e6b09422435ce2914cbbb8a34bf793df708b/README.md) |

- `original`是FSA/U55C原始基线；`original-nm37`的实际分支名为`original-nm37-civ`。
- A100/A110选择已独立复现的修复分支；原始迁移里程碑仍保留。A110/A120/A150分别为APB55/APB60/APB100。
- 默认分支只作为总入口，其硬件配置不是original-nm37；必须先切换。无需先构建其他版本。

## 2. 换版本时改哪些内容

| 选择的版本 | Vivado | RUN_VERIFY | SIM_SIZES | 生成bit文件名 |
|---|---|---:|---|---|
| original-nm37（本文示例） | 2020.2_AR75986 | 0 | `4` | NM37_EXPERIMENTAL.bit |
| original-u280 | 按该分支环境说明 | 0 | `4` | U280_EXPERIMENTAL.bit |
| original-np19a | 2024.2，安装VU19P支持 | 0 | `4` | NP19A_EXPERIMENTAL.bit |
| nm37-A70-P3 | 2020.2_AR75986 | 1 | `4 16` | A70-P3_EXPERIMENTAL.bit |
| nm37-A100 | 2020.2_AR75986 | 1 | `4 8 16` | A100_EXPERIMENTAL.bit |
| nm37-a110 | 2020.2_AR75986 | 1 | `4 8 16` | A110-APB55_EXPERIMENTAL.bit |
| nm37-a120 | 2020.2_AR75986 | 1 | `4 8 16` | A120-APB60_EXPERIMENTAL.bit |
| nm37-a150 | 2020.2_AR75986 | 1 | `4 8 16` | A150-APB100_EXPERIMENTAL.bit |

换版本时：修改下面的`VERSION`、`BRANCH`、`COMMIT`、`RUN_VERIFY`、`SIM_SIZES`，并选择对应Vivado安装路径。**频率、APB、板卡型号和PE流水由该commit的profile/源码决定，不手动设置频率环境变量。** 输出路径由VERSION自动区分。

每个版本使用独立源码目录，下载来源与缓存共用；当前deps不会自动重置已初始化到其他commit的子模块，所以不要在已构建目录原地切换。重新选择版本后从第3节开始，不覆盖旧输出。

## 3. original-nm37示例：下载和切换commit

```bash
export VERSION=original-nm37
export BRANCH=original-nm37-civ
export COMMIT=87cd26500fc88f7051771e3cb1670001375c6b1f
export RUN_VERIFY=0
export SIM_SIZES='4'
export WORK="$HOME/ict-fsa-$VERSION-attempt01"
mkdir "$WORK"
git clone --branch "$BRANCH" https://github.com/zs0922/ICT-FSA.git "$WORK/source"
export SRC="$WORK/source"
cd "$SRC"
git checkout --detach "$COMMIT"
git rev-parse HEAD | tee "$WORK/source-commit.txt"
cat profiles/current.json
export BUILD_OUT="$WORK/build-attempt01"
export EXPORT_OUT="$WORK/bits-attempt01"
```

例如改跑A100，只需先改为以下五个值，再执行上面从`export WORK=...`开始的命令，后续流程相同：

```bash
export VERSION=nm37-A100
export BRANCH=codex/a100-reproduction-fix
export COMMIT=9b8911f4e9e5c6af49fe6b6287e9c88ee1031352
export RUN_VERIFY=1
export SIM_SIZES='4 8 16'
```

如果WORK已存在，换attempt02。Bash/tmux中逐步执行，失败后停止检查，不要在交互终端设置`set -euo pipefail`。后面的循环会在失败时退出循环，不代表可以继续后续阶段。

## 4. 环境与依赖

按当前checkout的`docs/reproduction/environment.md`准备工具。下面安装路径必须替换成实际路径；NP19A将Vivado改为2024.2。首次缺少Spike/FESVR双库时按该环境文档的安装步骤补齐，无需先构建其他版本。

```bash
source /absolute/path/to/Vivado/2020.2/settings64.sh
export JAVA_HOME=/absolute/path/to/jdk-20.0.2
export RISCV=/absolute/path/to/spike-prefix
export CHISEL_FIRTOOL_PATH=/absolute/path/to/circt/bin
export PATH="$JAVA_HOME/bin:$CHISEL_FIRTOOL_PATH:/absolute/path/to/verilator/bin:$RISCV/bin:$PATH"
export CC=/usr/bin/gcc
export CXX=/usr/bin/g++
export LD_LIBRARY_PATH="$RISCV/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export FSA_JOBS=4
export MAKEFLAGS=-j4
unset JDK_JAVA_OPTIONS _JAVA_OPTIONS

# 所有版本可共享下载缓存；生成结果仍独立。
export ICT_CACHE="$HOME/.cache/ict-fsa-downloads"
export UV_CACHE_DIR="$ICT_CACHE/uv"
export COURSIER_CACHE="$ICT_CACHE/coursier/v1"
export SBT_OPTS="-Dsbt.ivy.home=$ICT_CACHE/sbt/ivy2 -Dsbt.boot.directory=$ICT_CACHE/sbt/boot -Dsbt.global.base=$WORK/sbt-global"
export JAVA_TOOL_OPTIONS="-Dsbt.supershell=false -Dsbt.server.forcestart=false -Dsbt.server.autostart=false $SBT_OPTS"
cd "$SRC"
```

源码依赖二选一，报告文件不要重复使用：

```bash
# 已有下载齐全的源码：推荐复用，不重新联网下载。
export DEPS_SOURCE=/absolute/path/to/existing-source
python3 scripts/fsa.py deps --local-source "$DEPS_SOURCE" --report "$WORK/dependencies.json"
```

```bash
# 首次没有可复用源码时，改用这一条。
python3 scripts/fsa.py deps --report "$WORK/dependencies.json"
```

本地来源必须包含目标版本的Git对象；脚本独立复制依赖并核对pin，不修改旧源码，也不依赖旧目录永久存在。节省网络下载但仍占独立磁盘空间。不要软链接共享依赖源码。

随后检查工具并创建Python环境：

```bash
python3 scripts/fsa.py doctor
uv sync --frozen --python 3.13 --project "$SRC/generators/easyfloat"
uv sync --frozen --python 3.13 --project "$SRC/generators/fsa/python"
export FSA_PYTHON="$SRC/generators/fsa/python/.venv/bin/python"
"$FSA_PYTHON" -c 'import numpy, torch, pyeasyfloat; print("Python imports OK")'
```

doctor检查JDK20.0.2、firtool1.75、Verilator5.022、GCC/G++13.3和对应Vivado等；工具存在不代表构建通过。`RUN_VERIFY=1`的优化版还需按所选分支环境文档准备形式验证工具；original-nm37不需要这套工具。

## 5. 编译、验证和仿真

```bash
# Scala/Chisel生成器编译，不是FPGA综合。
python3 scripts/fsa.py build --out "$BUILD_OUT"
```

```bash
# original-nm37的RUN_VERIFY=0，自动跳过；优化版为1。
if [ "$RUN_VERIFY" = 1 ]; then
  python3 scripts/fsa.py verify --out "$BUILD_OUT"
fi
```

```bash
# 根据第2节设置的规模逐个执行，任一失败即停止循环。
for N in $SIM_SIZES; do
  python3 scripts/fsa.py sim --out "$BUILD_OUT" --array-size "$N" || break
done
python3 scripts/fsa.py status --out "$BUILD_OUT"
```

确认所有要求的阶段均完成后继续。原始NM37固定仿真是4×4，板上仍为16×16；seq1024是序列长度，不是1024×1024 PE阵列。优化版已完成sim16后可追加下面测试，原始三种板卡迁移基线跳过：

```bash
timeout --signal=TERM --kill-after=10s 7200s \
  python3 scripts/fsa.py sim-extra --out "$BUILD_OUT" \
  --array-size 16 --seq 1024 --max-cycles 10000000 \
  --result-out "$WORK/sim-seq1024-attempt01"
```

## 6. 展开RTL、完整布局布线、导出bitstream

```bash
python3 scripts/fsa.py elaborate --out "$BUILD_OUT"
python3 scripts/fsa.py implement --out "$BUILD_OUT"
python3 scripts/fsa.py status --out "$BUILD_OUT"
```

implement执行综合、布局布线并保存时序/资源等报告，不自动导出bit。成功后：

```bash
python3 scripts/fsa.py export --out "$BUILD_OUT" --result-out "$EXPORT_OUT"
(cd "$EXPORT_OUT" && sha256sum -c SHA256SUMS)
cat "$EXPORT_OUT/experiment.json"
ls -lh "$EXPORT_OUT"/*.bit
```

original-nm37结果为`NM37_EXPERIMENTAL.bit`和配套`FSAConfig.json`；其他名称见第2节。export检查实际时序/DRC，不要求手写CDC审查JSON。A110等若仅CDC审查待完成，但实际routed产物已被记录，可按对应文档执行实验export；不能绕过真正的综合/布线/时序失败。

## 7. 烧录与attention：此处区分版本

**从源码到bit的入口基本相同，板测尚未完全统一。** original-nm37和original-u280当前没有已验收的统一attention入口，不能照抄优化NM37的test命令。其源码、sim4、完整实现及实验bit导出已有记录，实板仍待验证。

对提供program入口的版本，先在Hardware Manager确认实际JTAG目标/器件、PCI BDF及XDMA映射，再执行：

```bash
export HW_TARGET='实际完整JTAG target'
export HW_DEVICE='实际FPGA器件名'
export BDF='0000:18:00.0'  # 示例，按实际设备修改
export PROGRAM_OUT="$WORK/program-attempt01"
python3 scripts/fsa.py program --export "$EXPORT_OUT" \
  --hw-target "$HW_TARGET" --hw-device "$HW_DEVICE" --bdf "$BDF" \
  --out "$PROGRAM_OUT" --dry-run
python3 scripts/fsa.py program --export "$EXPORT_OUT" \
  --hw-target "$HW_TARGET" --hw-device "$HW_DEVICE" --bdf "$BDF" \
  --out "$PROGRAM_OUT"
```

这是SRAM烧录，不写flash。首次PCIe未枚举时先在Hardware Manager烧录，再保持板卡供电软重启，重新确认BDF并加载XDMA驱动。换环境变量不等于换FPGA镜像。

### NM37优化版（A70-P3至A150）

```bash
export DEVICE=xdma0  # 核对本机BDF映射
export RESULT="$WORK/board/seq16-attempt01"
sudo timeout --signal=TERM --kill-after=10s 600s \
  "$FSA_PYTHON" -u "$SRC/scripts/fsa.py" test --export "$EXPORT_OUT" \
  --receipt "$PROGRAM_OUT/program.json" --device "$DEVICE" --bdf "$BDF" \
  --seq 16 --repeat 5 --warmup 1 --out "$RESULT"
```

### NP19A

先核对实装DDR4与配置MTA16ATF2G64HZ-2G3一致。NP19A改用独立脚本：

```bash
export DEVICE=xdma0  # 核对本机BDF映射
export RESULT="$WORK/board/seq16-attempt01"
sudo timeout --signal=TERM --kill-after=10s 600s \
  "$FSA_PYTHON" -u "$SRC/scripts/np19a/attention.py" \
  --config "$EXPORT_OUT/FSAConfig.json" --bit "$EXPORT_OUT/NP19A_EXPERIMENTAL.bit" \
  --device "$DEVICE" --bdf "$BDF" --seq 16 --seed 0 --out "$RESULT"
```

两者都打印/保存Torch误差和PyEasyFloat比较。seq16通过后改`--seq 1024`、timeout7200s，并换新RESULT目录。sudo使用绝对Python路径，不必sudo -E。NP19A的bit路径不是实时硬件身份回读，必须保留真实烧录记录。

## 补充说明

- original/U55C使用独立[README](https://github.com/zs0922/ICT-FSA/blob/474e92dc018df7a7a818aa329db967ebb829108c/README.md)，不执行本文`scripts/fsa.py`流程；其中旧“未push”描述是历史状态，现在已发布。
- 当前实际证据：原始NM37/U280/NP19A已完成实现和实验bit导出，未实板验收；A70及A100/A110推荐提交完成独立回归和约束时序验证，CDC/板级验收仍有限制；A120/A150旧实验有实现证据，不等于迁入后所有提交均已完整重建。
- 完整历史分支、来源与缓存说明见[补充指南](docs/reproduction/all-versions.md)，NM37计数器与性能汇总见[详细流程](docs/reproduction/nm37-optimized-workflow.md)。
- 失败保留源码commit、依赖/工具记录、日志、配置、时序/资源/CDC报告、bit校验和、烧录记录和板测结果。用新attempt重试，不清空下载缓存、不复制旧JAR/RTL/DCP冒充重建、不补写成功标记。
- RelErr与PyEasyFloat逐位一致是不同指标；bubble不直接等于PE空闲率。不同版本的仿真内存接口及主机实现可能不同，不能把所有性能差异都归因于提频。
