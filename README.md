# ICT-FSA：从源码到 FPGA 板测

这是整理后的源码候选仓库。每个里程碑提交包含自己的硬件、主机软件、依赖锁和工具入口；旧 FSA 仓库和既有构建保持独立。**整理及脚本测试通过不表示这个新提交已经完成 Vivado 重建、CDC 验收或实板验收。** 查看本提交 `profiles/current.json`、`docs/history/` 和 `reports/` 了解实际验证范围。当前不需要另一个 integration-tools checkout。

阶段为 U280 → NM37 初始迁移 → NM37 A70-P3 → NM37 A100 → NM37 A110/APB55 → NM37 A120/APB60 → NM37 A150/APB100。具体 commit 与已验证范围见 [本地迁移记录](reports/ICT_FSA_LOCAL_MIGRATION.md)（完整映射：`docs/history/migration-map.json`）；候选提交可切换，验收标签要等对应复现通过后再创建。下面命令在 Bash/tmux 中逐条执行；**不要在交互终端执行 `set -euo pipefail`**。

## 原始核心与未优化板卡移植基线

需要从原始 FSA 移植新板卡时，请先读 [三个原始基线的来源、选择与复现](docs/baselines/README.md)。`original` 保存 VCA-EPFL FSA/U55C 的历史核心；`original-u280`、`original-nm37-civ` 保存初始板卡适配及必要正确性修复，不含后续 P0～P3、A100 流水或 A110/A150 修改。A70-P3 是优化配置，不是原始基线。

三个基线通过 ICT-FSA 的 `original`、`original-u280`、`original-nm37-civ` 分支交付。GitHub 拉取、固定提交与151服务器操作命令见上述基线说明。既有硬件里程碑分支及其构建不变。每个基线使用独立 checkout 和输出目录；该基线自己的 README 是其命令入口，不要在原始分支照抄下方 A150 命令。实际验证范围与固定提交见上述基线说明。

## NP19A 原始核心迁移入口

无HBM的NP19A使用独立分支 **`original-np19a`**，固定交付提交 **`8407bdd8d4bd6d0aae56a1a549353f8c35f2124f`**。请按[该版本完整README](https://github.com/zs0922/ICT-FSA/blob/8407bdd8d4bd6d0aae56a1a549353f8c35f2124f/README.md)执行，不使用下方NM37命令。

器件`xcvu19p-fsva3824-2-e`、Vivado2024.2、原始16×16 FSA 70MHz、PCIe Gen3×8和单通道DDR4（配置MTA16ATF2G64HZ-2G3）。原始FSA/easyfloat保持不变。已完成源码编译、4×4 seq4/seq8逐位仿真、16×16完整布局布线及实验bit导出；全局WNS+0.058ns、WHS+0.010ns。尚未NP19A实板验收；两条复位启动相关CDC Critical和其他CDC告警的范围见[构建记录](https://github.com/zs0922/ICT-FSA/blob/8407bdd8d4bd6d0aae56a1a549353f8c35f2124f/reports/ORIGINAL_NP19A_BASELINE.md)。

```bash
export WORK="$HOME/ict-fsa-original-np19a-8407bdd8"
mkdir -p "$WORK"
git clone --branch original-np19a https://github.com/zs0922/ICT-FSA.git "$WORK/source"
export SRC="$WORK/source"
git -C "$SRC" checkout --detach 8407bdd8d4bd6d0aae56a1a549353f8c35f2124f
cd "$SRC"
# 从本分支README第2节开始：环境/依赖 → build → sim → elaborate → implement → export → program → attention。
```

无需先构建NM37/U280或优化版本。先核对板卡实际SO-DIMM型号，再构建；实际安装与配置不同不能直接烧录。原有分支和结果保持独立。

## 本次 A150/APB100 从哪里开始

当前集成版本为 **A150-APB100：DUT/FSA/HBM AXI 150MHz，HBM APB 100MHz**，分支 `codex/nm37-a150-apb100`。可以直接从这个版本开始，不必先构建 A70/A100/A110/A120。A150 分支与默认分支 `codex/ict-fsa-integration` 通过 GitHub 同步交付。硬件迁移提交为 `dae09729028da1d6ba0319c91fa946ae1916a97a`，本次发布提交只更新文档。构建时使用交付的固定提交，不在已有构建中途 pull 或切换版本。

PE/CMP/scratchpad/accumulator 流水保持 1/1/2/3 拍；DUT:APB 从 A120 的 2:1 改为 3:2，两个时钟仍由同一 MMCM 产生。旧实验已导出 bit，DUT setup +0.049ns、整板最差 Max（Recovery）+0.047ns、Hold +0.010ns，但尚未板测。**迁入 ICT-FSA 后尚未完整重建；上述数字不是新提交的实现结果。** 具体差异和验证边界见 [A150 迁移记录](reports/ICT_FSA_A150_MIGRATION.md)。

```bash
export ICT_REPO=https://github.com/zs0922/ICT-FSA.git
export WORK="$HOME/ict-fsa-a150-reproduce"
mkdir -p "$WORK"
git clone --no-hardlinks --branch codex/nm37-a150-apb100 "$ICT_REPO" "$WORK/a150-source"
export SRC="$WORK/a150-source"
export COMMIT="$(git -C "$SRC" rev-parse HEAD)"
git -C "$SRC" checkout --detach "$COMMIT"
cd "$SRC"
cat profiles/current.json  # 必须显示 A150-APB100 / 150 / 100
export BUILD_OUT="$WORK/a150-build-attempt01"
export EXPORT_OUT="$WORK/a150-bits-attempt01"
```

如果目录已存在，请换新的 WORK，不覆盖已有构建。然后执行下方第 2 节的工具、固定依赖、两个 Python 环境和形式验证工具准备。首次安装若 `doctor` 只有 `libfesvr.a` / `libriscv.so` 缺失，按[首次安装 Spike/FESVR](docs/reproduction/environment.md#首次安装-spikefesvr库)补齐；不需要构建前面的硬件版本。

完成环境准备后，在这个 checkout 内依次执行：

```bash
python3 scripts/fsa.py build --out "$BUILD_OUT"
python3 scripts/fsa.py verify --out "$BUILD_OUT"
python3 scripts/fsa.py sim --out "$BUILD_OUT" --array-size 4
python3 scripts/fsa.py sim --out "$BUILD_OUT" --array-size 8
python3 scripts/fsa.py sim --out "$BUILD_OUT" --array-size 16
python3 scripts/fsa.py elaborate --out "$BUILD_OUT"
python3 scripts/fsa.py implement --out "$BUILD_OUT"
python3 scripts/fsa.py status --out "$BUILD_OUT"

# implement 不会自动写出 bit；完成布局布线后单独执行 export。
python3 scripts/fsa.py export --out "$BUILD_OUT" --result-out "$EXPORT_OUT"
cat "$EXPORT_OUT/experiment.json"
(cd "$EXPORT_OUT" && sha256sum -c SHA256SUMS)
ls -lh "$EXPORT_OUT/A150-APB100_EXPERIMENTAL.bit"
```

第 4 节的 seq1024 可作为追加回归；4/8/16 固定回归是必需项。实验导出沿用统一 `export`：重新检查 DUT150 及整板 max/min/pulse 时序和 DRC，**不要求手写 CDC 审核 JSON 或 physical.passed.json**。如果 implement 仅因 CDC 待审核退出，但已完成布局布线并记录 routed DCP/config，仍可执行 export；实际综合、布线或时序失败须先修复。保留 CDC 等报告供之后分析，不将实验导出声明为完整板级验收。

成功后如需烧录、运行 attention 和查看 RelErr，继续第 7–9 节；使用同一次构建生成的 config、bit 和实际烧录记录。旧实验的 `NM37_A150.bit` 文件名没有 APB 后缀，本次使用明确的 `A150-APB100_EXPERIMENTAL.bit`，避免与历史 APB75 混淆。

## 已发布的 A120/APB60 从哪里开始

当前 A120 分支 `codex/nm37-a120-apb60` 对应 DUT/HBM AXI **120MHz**、HBM APB **60MHz**，PE 流水深度不变。详细来源、历史实现结果和本次迁移验证范围见 [A120 迁移记录](reports/ICT_FSA_A120_MIGRATION.md)。该分支通过 GitHub 仓库交付；默认分支 `codex/ict-fsa-integration` 同步提供本版 README。硬件迁移提交为 `f8d4748a8b1ce627103d81da591e4b5faa150109`，其后的本次发布提交只更新文档。请记录并固定本次交付的完整 commit，构建中途不要 pull 或 checkout。

在 151 或其他构建服务器上使用新的目录，从 GitHub clone 后固定提交。不要修改已有 A70/A100/A110 源码或输出目录；如果下面目录已存在，改用新的 WORK，不要删除原结果：

```bash
export ICT_REPO=https://github.com/zs0922/ICT-FSA.git
export WORK="$HOME/ict-fsa-a120-reproduce"
mkdir -p "$WORK"
git clone --no-hardlinks --branch codex/nm37-a120-apb60 "$ICT_REPO" "$WORK/a120-source"
export SRC="$WORK/a120-source"
export COMMIT=462a341eb250f74a3d0c7ca415ef765f693c1839
# A120 固定使用该已发布提交；不要在 A150 checkout 中修改 profile 来切换。
printf 'Source commit: %s\n' "$COMMIT"
git -C "$SRC" checkout --detach "$COMMIT"
cd "$SRC"
cat profiles/current.json  # 必须显示 A120-APB60 / 120 / 60
export BUILD_OUT="$WORK/a120-build-attempt01"
```

随后**跳过第 1 节重复 clone，依次执行第 2–6 节**：工具/依赖/Python → build → verify → sim 4/8/16 → elaborate → implement → export。第 4 节 seq1024 是可选追加测试；固定 4/8/16 回归是必须项。导出的文件为 `$EXPORT_OUT/A120-APB60_EXPERIMENTAL.bit`。生成 bit 不烧录板卡；要上板时再执行第 7–9 节。

旧 FSA A120 实验已完成完整布局布线：DUT setup +0.235ns、全局 WNS +0.041ns、WHS +0.010ns；这是旧实现的证据，**不是当前 ICT-FSA 提交已完成重建/板测的证明**。本次不复用旧 JAR、仿真器或 DCP。CDC 继承告警及已记录的复位同步器属性问题仍待独立验收；实验导出不会将其标为已关闭。

## 1. 获取指定版本（固定输入）

本手册是交付主分支 `codex/ict-fsa-integration` 的最新操作说明。切到固定里程碑后，源码里的历史 README 可能缺少本轮新增的离线环境预热说明；请继续参照本手册执行，命令仍使用各源码版本自己的脚本。

2026-10-28 独立复现的输入如下；实际完成范围和原始报告见[本轮复现记录](reports/ICT_FSA_REPRODUCTION_20261028.md)。A100/A110 候选只清除了不匹配任何网表对象的历史 `MAX_FANOUT` 约束，原始里程碑仍保留。

| 配置 | 本轮源码 commit | 本地分支 |
|---|---|---|
| A70-P3 | `8cc6b42536334892b88f6214f39d3afe5daa2504` | `codex/nm37-a70-p3` |
| A100，清理无效约束 | `9b8911f4e9e5c6af49fe6b6287e9c88ee1031352` | `codex/a100-reproduction-fix` |
| A110/APB55，清理无效约束 | `7deb8e3e9416f2f3d25df9d45a5f65fc38302cda` | `codex/a110-reproduction-fix` |

例如复现 A70 时，将下方 `COMMIT` 设为表中 A70 的完整值。主分支另含操作说明、审查记录和维护工具修复；上表记录真正执行硬件构建的提交。冻结 profile 中的 `validation_status` 是创建候选时的状态，不会随外部构建自动更新；验收结论以对应提交的复现记录为准。

A70/A100/A110/A120 的交付提交均从 `https://github.com/zs0922/ICT-FSA.git` 获取。A120 按上面的专用步骤开始。`COMMIT` 使用交付记录中的完整新 commit，不使用旧 FSA 的 hash。

```bash
export ICT_REPO=https://github.com/zs0922/ICT-FSA.git
export COMMIT=填写本次要复现的新提交
export WORK="$HOME/ict-fsa-reproduce"
mkdir -p "$WORK"
git clone --no-hardlinks "$ICT_REPO" "$WORK/source-$COMMIT"
export SRC="$WORK/source-$COMMIT"
git -C "$SRC" checkout --detach "$COMMIT"
cd "$SRC"
cat profiles/current.json
export BUILD_OUT="$WORK/build-$COMMIT-attempt01"
```

每个硬件版本使用独立源码和输出目录。不要在已有构建中途 checkout 另一个版本。输出、仿真器、DCP 和 bit 不提交进源码 Git；下载缓存可以复用。sbt 自身仍会在源码下写入忽略的 `target`/classpath 缓存，主构建产物位于指定输出目录。

## 2. 准备工具、固定依赖和 Python（不编译硬件）

先安装 [环境说明](docs/reproduction/environment.md)要求的 JDK20、firtool、Verilator、Vivado、GCC/G++13.3、RISCV/FESVR 库，按其中步骤配置路径和形式验证环境，再运行：

```bash
python3 scripts/fsa.py doctor
python3 scripts/fsa.py deps --plan
python3 scripts/fsa.py deps --report "$WORK/deps-$COMMIT.json"
uv sync --frozen --python 3.13 --project "$SRC/generators/fsa/python"
# Chisel 展开会调用 EasyFloat 的 Python 常量生成器，它有独立环境。
uv sync --frozen --python 3.13 --project "$SRC/generators/easyfloat"
export FSA_PYTHON="$SRC/generators/fsa/python/.venv/bin/python"
"$FSA_PYTHON" -c 'import numpy, torch, pyeasyfloat; print("Python dependencies imported")'
```

`deps` 按本提交的锁定 gitlink 获取所需第三方代码，不修改三个直接跟踪的自研/板级目录，也不在构建时打历史补丁。断网时可使用已准备的依赖 bundle：`deps --offline-dir /absolute/path/to/migration-source-deps`。网络失败不要删除 Maven、Coursier、uv 缓存；保持日志，修好网络后重试依赖步骤。锁定 commit 错误或目录有改动时不会强制重置。

## 3. 编译生成器（产生本次 JAR）

```bash
python3 scripts/fsa.py build --out "$BUILD_OUT"
python3 scripts/fsa.py status --out "$BUILD_OUT"
```

这个阶段生成 Scala/Chisel 生成器 JAR，尚未进行 FPGA 综合。日志和阶段状态保存在 `$BUILD_OUT.ict-state/`；阶段内部的细节日志也会留在构建目录中。只有明确 `COMPLETE` 才是该命令完成，源文件检查的 `PASS` 不是整个阶段完成。

## 4. 定向验证与 Verilator 功能回归

A70-P3/A100/A110/A120/A150 先执行定向测试及等价证明；A110/A120/A150 还包括独立 APB 时钟域的 HBM 复位/启动验证：

```bash
python3 scripts/fsa.py verify --out "$BUILD_OUT"
```

U280 和初始 NM37 没有继承这些后来新增的证明套件，跳过该命令，执行其已有 4×4 仿真。每个版本必须运行自己 profile 中的全部阵列：

```bash
# 所有阶段都有 4×4。
python3 scripts/fsa.py sim --out "$BUILD_OUT" --array-size 4
# A100、A110/APB55、A120/APB60 和 A150/APB100 额外执行 8×8；U280/NM37/A70 不执行这一行。
python3 scripts/fsa.py sim --out "$BUILD_OUT" --array-size 8
# A70-P3、A100、A110/APB55、A120/APB60、A150/APB100 执行 16×16；U280/初始 NM37 不执行这一行。
python3 scripts/fsa.py sim --out "$BUILD_OUT" --array-size 16
```

`--array-size 16` 是 **16×16 PE 阵列**。固定回归分别计算 seq=16/32 等小输入，并对 PyEasyFloat 做直接逐位检查。1024 是序列长度，不是 PE 阵列大小。已有 16×16 仿真器后可增加长序列测试：

```bash
timeout --signal=TERM --kill-after=10s 7200s \
  python3 scripts/fsa.py sim-extra --out "$BUILD_OUT" \
  --array-size 16 --seq 1024 --max-cycles 10000000 \
  --result-out "$WORK/seq1024-$COMMIT-attempt01"
```

额外测试不替代固定回归。U280/初始 NM37 当前只承诺已恢复的 4×4 仿真入口；这不表示其板上阵列是 4×4。

比较仿真周期时还需核对内存拓扑：A70-P3 的 16×16 使用 `A70SinglePort16X16Fp16Config`（1 路、每拍 32 字节），A100/A110/A120/A150 固定回归使用 `AXI4FSA16X16Fp16Config`（8 路、每路每拍 8 字节）。两者均可用于各自功能回归，但其周期和 bubble 差异包含内存接口差异，不能作为纯提频/流水优化的加速比。这些固定回归默认使用 `mm_magic_t` 功能内存模型，未启用 DRAMSim，也不模拟真实 HBM 延迟。公平的跨版本仿真性能比较需另外统一接口与内存模型；板上性能使用第 8–9 节的实际烧录测试。

## 5. 生成板级 RTL，然后完整布局布线

```bash
python3 scripts/fsa.py elaborate --out "$BUILD_OUT"
python3 scripts/fsa.py implement --out "$BUILD_OUT"
python3 scripts/fsa.py status --out "$BUILD_OUT"
```

`elaborate` 将 Chisel 配置展开成 RTL，包含板级时钟/IP 配置；`implement` 执行 Vivado 综合、优化、布局、布线和报告。报告主要位于 `post_route.dcp` 旁的 `report/`、`audit/`。检查真实时钟、全局及 DUT setup/hold、脉宽、DRC、CDC、未约束端点和 exceptions；WNS 非负不自动证明 CDC 正确。

A100/A110/A120/A150 后端仍保留严格发布审查门槛；布局布线成功而 CDC 新问题需要审查时，`implement` 可能最后报失败，但 DCP 和报告会保留。先检查日志，不能将工具错误当成通过，也不要手写成功 seal。A110 可按[恢复说明的独立复审入口](docs/reproduction/recovery.md#a110apb55-已完成布线但-cdc-审查缺失)对已有 DCP 重新生成审查报告，保留原失败状态。需要实验板测时，下一节独立重新检查 routed DCP 的时序和 DRC；不会宣称 CDC/正式交付已通过。

## 6. 导出实验 bit（不是烧录）

```bash
export EXPORT_OUT="$WORK/bits-$COMMIT-attempt01"
python3 scripts/fsa.py export --out "$BUILD_OUT" --result-out "$EXPORT_OUT"
cat "$EXPORT_OUT/experiment.json"
(cd "$EXPORT_OUT" && sha256sum -c SHA256SUMS)
```

自动保存 bit、生成配置、SHA256、时钟/时序/资源/CDC/约束报告和源码身份。实验导出不要求手写 JSON，不降低 DRC 严重级别，也不关闭 CDC 验收问题。输出目录已存在则换新 attempt，旧记录保留。A120 导出文件名为 `A120-APB60_EXPERIMENTAL.bit`，A150 为 `A150-APB100_EXPERIMENTAL.bit`。若 implement 仅因 CDC 待审查退出，且已留下完整 routed DCP，可继续实验导出；若是综合/布线/时序/DRC 失败，则先解决实际失败，不能用导出跳过。

## 7. 实际烧录对应 bit（切换变量不等于烧录）

在连接 NM37 的机器配置 Vivado Hardware Manager/hw_server，查看 `get_hw_targets` 和 `get_hw_devices`，确认唯一目标和器件。`--hw-target`、`--hw-device` 必须填写实际完整名称，不能复制别人的板卡序列号。确认没有其他任务在使用这块 FPGA。

```bash
export HW_TARGET=填写HardwareManager中的完整目标名称
export HW_DEVICE=填写对应FPGA器件名称
export BDF=0000:18:00.0  # 示例，必须根据本机 lspci 重新确认
export PROGRAM_OUT="$WORK/program-$COMMIT-attempt01"
python3 scripts/fsa.py program --export "$EXPORT_OUT" \
  --hw-target "$HW_TARGET" --hw-device "$HW_DEVICE" --bdf "$BDF" \
  --out "$PROGRAM_OUT" --dry-run
python3 scripts/fsa.py program --export "$EXPORT_OUT" \
  --hw-target "$HW_TARGET" --hw-device "$HW_DEVICE" --bdf "$BDF" \
  --out "$PROGRAM_OUT"
```

第二条真正调用 `program_hw_devices`，仅配置 FPGA SRAM，不烧写 flash。成功生成 `program.json` 和 Vivado 日志。它是**实际烧录操作记录，不是硬件身份寄存器回读**。以后若又烧录其他镜像，旧 receipt 不再代表板上当前状态；操作者必须保持独占和操作顺序。

重配置后按本机 XDMA 部署方式恢复 PCIe 枚举/驱动，可能需要重启；重新执行 `lspci -Dnn | rg '10ee|Xilinx'` 和 `ls -l /dev/xdma*`。不要对未确认的 PCIe BDF 自动执行 remove/reset。若 BDF 发生变化，先确认板卡映射，再使用新 BDF 重新产生本次烧录记录。

## 8. 上板 attention、RelErr、逐位比较和计数器

下面板测入口当前支持 NM37 的 XDMA `10ee:9038`；U280 构建来源保留，U280 实板设备识别与板测尚待单独验证。

```bash
export DEVICE=xdma0  # 根据烧录后的实际 sysfs/BDF 对应关系确认
export RESULT="$WORK/board-$COMMIT/seq16-attempt01"
"$FSA_PYTHON" scripts/fsa.py test --export "$EXPORT_OUT" \
  --receipt "$PROGRAM_OUT/program.json" --device "$DEVICE" --bdf "$BDF" \
  --seq 16 --repeat 5 --warmup 1 --out "$RESULT" --dry-run
sudo timeout --signal=TERM --kill-after=10s 600s \
  "$FSA_PYTHON" -u "$SRC/scripts/fsa.py" test --export "$EXPORT_OUT" \
  --receipt "$PROGRAM_OUT/program.json" --device "$DEVICE" --bdf "$BDF" \
  --seq 16 --repeat 5 --warmup 1 --out "$RESULT"
```

sudo 后面的绝对路径和变量由当前 shell 展开，无需 `sudo -E`。若设备权限已配置好，可去掉 sudo。dry-run 只查文件和参数，不访问硬件、不创建结果目录。程序拒绝不匹配的 profile/config/bit/烧录记录，检查设备 BDF 和队列空闲，保存 Q/K/V、指令、实际输出、PyEasyFloat/Torch 参考值，以及每次计数器前后值。

seq16 通过后依次测 seq64、128、256、512、1024；每次把 `--seq` 和 `RESULT` 都改为新值，长序列 timeout 可设 7200s。脚本打印 MAE/MSE/MaxErr/RelErr，同时要求 FSA 对 PyEasyFloat 逐位一致、指令入队/出队增量匹配。执行时间按配置频率换算；`mxBubble` 是矩阵指令接口 ready 且无 valid 的计数，不能直接当成 PE 空闲率，active/bubble 也不一定互斥。

## 9. 汇总对比、恢复及交付

```bash
python3 scripts/fsa.py summarize \
  "$WORK/board-A70的新commit/seq1024-attempt01" \
  "$WORK/board-A100的新commit/seq1024-attempt01" \
  "$WORK/board-A110的新commit/seq1024-attempt01" \
  --out "$WORK/comparison-attempt01"
```

汇总输出 CSV、JSON、Markdown，按相同输入/seed 匹配 A70 基线，报告运行时间中位数/范围、主机耗时、bubble、RelErr 和系统加速比。历史各阶段的主机 MMIO 实现也有变化，不能把原配软件组的加速全部归因于提频。统一主机下发实现的公平对比要单独开展并记录来源。

失败恢复详见 [恢复说明](docs/reproduction/recovery.md)。保留源码 commit、profile、依赖报告、工具版本、`*.ict-state`、构建报告、bit/config/manifest、烧录记录、每次板测目录。不同生成环境不要求 bit 字节完全一致；每个实际 bit 都有自己的 hash。

新仓尚未完成验收的项目必须明确标为待验证；不要移动验收标签，也不要把旧 FSA 未重新烧录的 A100/A110 软件诊断数据当作新仓实板通过记录。
