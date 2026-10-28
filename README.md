# ICT-FSA：从源码到 FPGA 板测

这是整理后的源码候选仓库。每个里程碑提交包含自己的硬件、主机软件、依赖锁和工具入口；旧 FSA 仓库和既有构建保持独立。**整理及脚本测试通过不表示这个新提交已经完成 Vivado 重建、CDC 验收或实板验收。** 查看本提交 `profiles/current.json`、`docs/history/` 和 `reports/` 了解实际验证范围。当前不需要另一个 integration-tools checkout。

阶段为 U280 → NM37 初始迁移 → NM37 A70-P3 → NM37 A100 → NM37 A110/APB55。具体 commit 与已验证范围见 [本地迁移记录](reports/ICT_FSA_LOCAL_MIGRATION.md)（完整映射：`docs/history/migration-map.json`）；候选提交可切换，验收标签要等对应复现通过后再创建。下面命令在 Bash/tmux 中逐条执行；**不要在交互终端执行 `set -euo pipefail`**。

## 1. 获取指定版本（固定输入）

本手册是交付主分支 `codex/ict-fsa-integration` 的最新操作说明。切到固定里程碑后，源码里的历史 README 可能缺少本轮新增的离线环境预热说明；请继续参照本手册执行，命令仍使用各源码版本自己的脚本。

新远程仓库尚未创建或推送时，从本地整理仓库 clone；发布后只替换仓库地址。`COMMIT` 使用交付记录中的完整新 commit，不使用旧 FSA 的 hash。

```bash
export ICT_REPO=/absolute/path/to/local/ICT-FSA
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

A70-P3/A100/A110 先执行定向测试及等价证明；A110 还包括独立 APB 时钟域的 HBM 复位/启动验证：

```bash
python3 scripts/fsa.py verify --out "$BUILD_OUT"
```

U280 和初始 NM37 没有继承这些后来新增的证明套件，跳过该命令，执行其已有 4×4 仿真。每个版本必须运行自己 profile 中的全部阵列：

```bash
# 所有阶段都有 4×4。
python3 scripts/fsa.py sim --out "$BUILD_OUT" --array-size 4
# A100 和 A110/APB55 额外执行 8×8；U280/NM37/A70 不执行这一行。
python3 scripts/fsa.py sim --out "$BUILD_OUT" --array-size 8
# A70-P3、A100、A110/APB55 执行 16×16；U280/初始 NM37 不执行这一行。
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

比较仿真周期时还需核对内存拓扑：A70-P3 的 16×16 使用 `A70SinglePort16X16Fp16Config`（1 路、每拍 32 字节），A100/A110 固定回归使用 `AXI4FSA16X16Fp16Config`（8 路、每拍 8 字节）。两者均可用于各自功能回归，但其周期和 bubble 差异包含内存接口差异，不能作为纯提频/流水优化的加速比。公平的跨版本仿真性能比较需另外统一接口与内存模型；板上性能使用第 8–9 节的实际烧录测试。

## 5. 生成板级 RTL，然后完整布局布线

```bash
python3 scripts/fsa.py elaborate --out "$BUILD_OUT"
python3 scripts/fsa.py implement --out "$BUILD_OUT"
python3 scripts/fsa.py status --out "$BUILD_OUT"
```

`elaborate` 将 Chisel 配置展开成 RTL，包含板级时钟/IP 配置；`implement` 执行 Vivado 综合、优化、布局、布线和报告。报告主要位于 `post_route.dcp` 旁的 `report/`、`audit/`。检查真实时钟、全局及 DUT setup/hold、脉宽、DRC、CDC、未约束端点和 exceptions；WNS 非负不自动证明 CDC 正确。

A100/A110 后端仍保留严格发布审查门槛；布局布线成功而 CDC 新问题需要审查时，`implement` 可能最后报失败，但 DCP 和报告会保留。先检查日志，不能将工具错误当成通过，也不要手写成功 seal。需要实验板测时，下一节独立重新检查 routed DCP 的时序和 DRC；不会宣称 CDC/正式交付已通过。

## 6. 导出实验 bit（不是烧录）

```bash
export EXPORT_OUT="$WORK/bits-$COMMIT-attempt01"
python3 scripts/fsa.py export --out "$BUILD_OUT" --result-out "$EXPORT_OUT"
cat "$EXPORT_OUT/experiment.json"
(cd "$EXPORT_OUT" && sha256sum -c SHA256SUMS)
```

自动保存 bit、生成配置、SHA256、时钟/时序/资源/CDC/约束报告和源码身份。实验导出不要求手写 JSON，不降低 DRC 严重级别，也不关闭 CDC 验收问题。输出目录已存在则换新 attempt，旧记录保留。

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
