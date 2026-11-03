# original-np19a：NP19A 原始 FSA 迁移

本分支将原始 16×16 FSA 接到 NP19A 的 PCIe/XDMA 和 DDR4，目标器件 **xcvu19p-fsva3824-2-e**、Vivado **2024.2**、FSA **70 MHz**。不包含 P3、A100、A150 算术/流水优化；`generators/fsa` 和 `generators/easyfloat` 相对 `original-nm37-civ` 未修改。独立 AXI 顶层也可作为后续计算模块封装的起点。

**已完成源码编译、4×4计算回归与16×16完整布局布线；尚未完成 NP19A 实板验收。** 历史 NM37 报告不证明 NP19A 可用。70MHz下全局WNS为+0.058ns，FSA域WNS为+0.142ns。验证证据见 [本次构建记录](reports/ORIGINAL_NP19A_BASELINE.md)，板级配置见 [NP19A 迁移说明](docs/reproduction/np19a.md)。通过 `original-np19a` 分支交付；报告中的“未 push”描述的是当时本地验收状态。

## 1. 独立取得源码

```bash
export ICT_REPO=https://github.com/zs0922/ICT-FSA.git
export WORK="$HOME/ict-fsa-original-np19a"
mkdir -p "$WORK"
git clone --no-hardlinks --branch original-np19a "$ICT_REPO" "$WORK/source"
export SRC="$WORK/source"
export COMMIT="$(git -C "$SRC" rev-parse HEAD)"
git -C "$SRC" checkout --detach "$COMMIT"
cd "$SRC"
git rev-parse HEAD | tee "$WORK/source-commit.txt"
export BUILD_OUT="$WORK/build-attempt01"
```

发布说明提供固定完整 commit；如按指定版本复现，在开始 deps/build 前将 COMMIT 设置为该值并 checkout --detach。构建中途不要 pull 或切换版本。不要覆盖已有 NM37、U280 构建或复制其 JAR/RTL/DCP。交互式终端不要启用 `set -e`；每一步成功后才继续。

## 2. 准备环境和依赖

按 [环境说明](docs/reproduction/environment.md) 安装 JDK20.0.2、firtool1.75、Verilator5.022、GCC13.3、Spike/FESVR 库、uv，以及带 **xcvu19p 器件支持和实现许可证** 的 Vivado2024.2。无需先构建其他板卡/优化版本。

```bash
# 将下面安装路径改成当前服务器实际位置。
source /absolute/path/to/Vivado/2024.2/settings64.sh
export JAVA_HOME=/absolute/path/to/jdk-20.0.2
export RISCV=/absolute/path/to/spike-prefix
export PATH="$JAVA_HOME/bin:/absolute/path/to/circt/bin:/absolute/path/to/verilator/bin:$RISCV/bin:$PATH"
export CC=/usr/bin/gcc
export CXX=/usr/bin/g++  # doctor要求13.3.0
export LD_LIBRARY_PATH="$RISCV/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CHISEL_FIRTOOL_PATH="$(dirname "$(command -v firtool)")"
export JAVA_TOOL_OPTIONS='-Dsbt.supershell=false -Dsbt.server.forcestart=false -Dsbt.server.autostart=false'
unset JDK_JAVA_OPTIONS _JAVA_OPTIONS
export FSA_JOBS=4
export MAKEFLAGS=-j4
python3 scripts/fsa.py deps --report "$WORK/dependencies.json"
python3 scripts/fsa.py doctor
uv sync --frozen --python 3.13 --project "$SRC/generators/easyfloat"
uv sync --frozen --python 3.13 --project "$SRC/generators/fsa/python"
export FSA_PYTHON="$SRC/generators/fsa/python/.venv/bin/python"
```

`deps` 下载锁定源码；`doctor` 检查工具而不编译。仅缺 Spike/FESVR 时可按环境文档从本分支锁定源码安装，不要把 RISCV 指向空目录。

## 3. 编译、仿真、展开与布局布线

```bash
# 编译本次 Scala/Chisel 生成器。
python3 scripts/fsa.py build --out "$BUILD_OUT"
# 构建 4×4 仿真器，运行 seq4/seq8，与 PyEasyFloat 逐位比较。
python3 scripts/fsa.py sim --out "$BUILD_OUT" --array-size 4
# 展开板上 16×16 FSA、外露 AXI 接口并生成端口映射包装层。
python3 scripts/fsa.py elaborate --out "$BUILD_OUT"
# 创建 DDR4/PCIe BD，验证地址/时钟连接，再综合和完整布局布线。
python3 scripts/fsa.py implement --out "$BUILD_OUT"
python3 scripts/fsa.py status --out "$BUILD_OUT"
```

4×4 仿真检查原始计算/调度；不等价于板级 DDR4/PCIe 仿真，更不代替实板验证。本原始分支没有优化版本的 `verify` 套件，不执行该阶段。布局布线报告位于 `$BUILD_OUT/NP19A/fpga/chipyard.fpga.np19a.NP19AFSACore.EmptyNP19AConfig/obj/report/`。

## 4. 导出实验 bitstream

```bash
export EXPORT_OUT="$WORK/bits-attempt01"
python3 scripts/fsa.py export --out "$BUILD_OUT" --result-out "$EXPORT_OUT"
(cd "$EXPORT_OUT" && sha256sum -c SHA256SUMS)
```

导出检查实际器件、70MHz 时钟、全局 setup/hold/pulse-width 与 DRC，不需要手写审查 JSON。成功产物是 `$EXPORT_OUT/NP19A_EXPERIMENTAL.bit` 和配套 `FSAConfig.json`。它们不是实板通过的声明。CDC/未约束路径仍需结合报告检查。

## 5. 烧录与上板 attention

先通过 Vivado Hardware Manager 确定准确 JTAG target/device 和本板 PCI BDF。下列值需按实际板卡填写；不得复制 NM37 的设备号。首次无 PCI 枚举时，应先在 Hardware Manager 烧录，再保持板卡供电进行主机软重启，使 PCIe 枚举，记录烧录日志与 bit SHA256。

```bash
export HW_TARGET='actual/exact/target'
export HW_DEVICE='xcvu19p_0'
export BDF='0000:18:00.0'  # 示例，必须核对实际 NP19A
python3 scripts/fsa.py program --export "$EXPORT_OUT" \
  --hw-target "$HW_TARGET" --hw-device "$HW_DEVICE" --bdf "$BDF" \
  --out "$WORK/program-attempt01" --dry-run
# 确认目标无误后执行真实 SRAM 烧录；不写配置 flash。
python3 scripts/fsa.py program --export "$EXPORT_OUT" \
  --hw-target "$HW_TARGET" --hw-device "$HW_DEVICE" --bdf "$BDF" \
  --out "$WORK/program-attempt01"
```

烧录后等待 DDR 校准、确认 PCIe 枚举与 XDMA 驱动设备；必要时保持板卡供电进行主机软重启；SRAM 烧录不写 flash，板卡断电会丢失此配置。**更换环境变量不会更换 FPGA 电路。** 对照 sysfs 确认 `/dev/xdmaN_*` 对应选定 BDF。

```bash
lspci -Dnn
ls -l /dev/xdma*
export DEVICE=xdma0  # 示例，按 sysfs 映射核对
readlink -f "/sys/class/xdma/${DEVICE}_user/device"
export RESULT="$WORK/board/seq16-attempt01"
"$FSA_PYTHON" scripts/np19a/attention.py \
  --config "$EXPORT_OUT/FSAConfig.json" --bit "$EXPORT_OUT/NP19A_EXPERIMENTAL.bit" \
  --device "$DEVICE" --bdf "$BDF" --seq 16 --out "$RESULT" --dry-run
sudo timeout --signal=TERM --kill-after=10s 600s "$FSA_PYTHON" -u \
  "$SRC/scripts/np19a/attention.py" \
  --config "$EXPORT_OUT/FSAConfig.json" --bit "$EXPORT_OUT/NP19A_EXPERIMENTAL.bit" \
  --device "$DEVICE" --bdf "$BDF" --seq 16 --out "$RESULT"
```

只有存在真实烧录记录、板卡映射正确且 seq16 通过后，才以新结果目录改跑 seq64/128/256/512/1024（1024 建议 timeout7200s）。保存输入/输出 `.npy`、`result.json`、终端输出、烧录记录、bit/config SHA256，以及 `$WORK/source-commit.txt`、依赖报告和工具版本输出。`RelErr` 与原始软件定义一致：`mean(abs((FSA−torch)/(torch+1e-8)))`；是否逐位符合 PyEasyFloat 独立记录。`execTime/70e6` 是按目标频率换算的计数器时间，不是整段 Python 墙钟时间。

## 6. 失败恢复

检查 `$BUILD_OUT.ict-state/` 与阶段日志。阶段失败时保留输出、依赖缓存和日志；修复代码后本地提交，选新源码/新输出 attempt。不要手写成功标记、删除日志伪装首次运行，或直接用旧时序结果覆盖新工程。板测超时后先核对 DDR 校准、PCIe、复位状态和地址映射，不要据此修改原始计算算法。

## 7. 追加seq1024并读取结果

seq16逐位比较成功后，在同一次烧录下执行：

```bash
export RESULT="$WORK/board/seq1024-attempt01"
sudo timeout --signal=TERM --kill-after=10s 7200s "$FSA_PYTHON" -u \
  "$SRC/scripts/np19a/attention.py" \
  --config "$EXPORT_OUT/FSAConfig.json" --bit "$EXPORT_OUT/NP19A_EXPERIMENTAL.bit" \
  --device "$DEVICE" --bdf "$BDF" --seq 1024 --seed 0 --out "$RESULT"
sudo python3 - "$RESULT/result.json" <<'PYRESULT'
import json, sys
r = json.load(open(sys.argv[1]))
print("status:", r["status"])
print("bitwise_equal_pyeasyfloat:", r["bitwise_equal_pyeasyfloat"])
print("errors_vs_torch:", r["errors_vs_torch"])
c = r["counters"]
print("execution_ms (nominal 70MHz):", c["execTime"] / 70000)
print("mxBubble / execTime (%):", 100 * c["mxBubble"] / c["execTime"] if c["execTime"] else None)
PYRESULT
```

`errors_vs_torch.RelErr`是相对Torch的误差；`bitwise_equal_pyeasyfloat`是与同精度模型的逐位比较，二者不是同一指标。bubble计数比不直接等于PE空闲率。sudo前的变量由当前shell展开，不需要sudo -E；使用venv Python的绝对路径。每次重跑都换新的结果目录。XDMA驱动需要预先安装并与当前内核匹配；`lspci -Dnnk -s "$BDF"`应显示xdma驱动，三个字符设备必须存在，否则先解决驱动/枚举，不继续发任务。
