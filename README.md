# ICT-FSA：选择版本与复现

**先从表中选择版本并固定commit，再执行该版本的流程。** 本文以`original`完整演示从源码到仿真、bitstream和上板测试。其他版本的独立README直接点击表格最后一列；它们的构建入口与original不同。

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
- 默认分支只作为总入口，其硬件配置不是original；必须先切换。无需先构建其他版本。

## 2. original：下载并固定源码

以下在Bash中逐块执行，每步成功后再继续。路径已存在时换attempt02，不删除旧构建；不要在交互终端设置`set -euo pipefail`。

```bash
export ORIGINAL_WORK="$HOME/ict-fsa-original-attempt01"
mkdir "$ORIGINAL_WORK"
git clone --branch original --single-branch \
  https://github.com/zs0922/ICT-FSA.git "$ORIGINAL_WORK/source"
export SRC="$ORIGINAL_WORK/source"
cd "$SRC"
git checkout --detach 474e92dc018df7a7a818aa329db967ebb829108c
git rev-parse HEAD | tee "$ORIGINAL_WORK/source-commit.txt"
python3 scripts/verify-original.py
```

这个original保留VCA-EPFL/chipyard-fsa的FSA/U55C集成原貌，不含后续板卡迁移和性能优化。板上配置为16×16、70MHz；下面的功能仿真使用4×4阵列。

## 3. original：环境与依赖

需先安装Git、make、uv、JDK20.0.2、firtool1.75.0、Verilator5.022、GCC/G++13.3.0，以及Spike/FESVR头文件和库。Python3.13由uv准备。下面的`/path/to/...`必须改为实际路径。

```bash
export JAVA_HOME=/path/to/jdk-20.0.2
export RISCV=/path/to/riscv
export CHISEL_FIRTOOL_PATH=/path/to/circt/bin
export VERILATOR_BIN=/path/to/verilator/bin
export PATH="$JAVA_HOME/bin:$CHISEL_FIRTOOL_PATH:$VERILATOR_BIN:$RISCV/bin:$PATH"
export CC=/usr/bin/gcc
export CXX=/usr/bin/g++
export USE_CHISEL6=1
export LD_LIBRARY_PATH="$RISCV/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export XDG_RUNTIME_DIR="$ORIGINAL_WORK/runtime"
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

# 各版本可以共用这些下载缓存。
export ICT_CACHE="$HOME/.cache/ict-fsa-downloads"
export COURSIER_CACHE="$ICT_CACHE/coursier/v1"
export UV_CACHE_DIR="$ICT_CACHE/uv"
export SBT_OPTS="-Dsbt.ivy.home=$ICT_CACHE/sbt/ivy2 -Dsbt.boot.directory=$ICT_CACHE/sbt/boot -Dsbt.global.base=$ORIGINAL_WORK/sbt-global"
export JAVA_TOOL_OPTIONS="-Dsbt.supershell=false -Dsbt.server.forcestart=false -Dsbt.server.autostart=false $SBT_OPTS"
unset JDK_JAVA_OPTIONS _JAVA_OPTIONS

java -version
firtool --version
verilator --version
"$CXX" --version
ls -lh "$RISCV/lib/libfesvr.a" "$RISCV/lib/libriscv.so"
```

若最后两个库不存在，先执行文末“首次安装Spike/FESVR”，然后继续；不需要构建A70等版本。

下载锁定的源码依赖，并建立两个Python环境：

```bash
cd "$SRC"
python3 scripts/prepare-original-deps.py
python3 scripts/verify-original.py --require-core-deps
uv sync --project generators/easyfloat --frozen --python 3.13
uv sync --project generators/fsa/python --frozen --python 3.13
```

已有完整依赖时，用以下命令**替代**上面的prepare命令，避免重复联网下载：

```bash
python3 scripts/prepare-original-deps.py --mirror-root /absolute/path/to/existing-chipyard-source
```

来源必须包含目标gitlink所需对象。不要使用`git submodule update --remote`改变固定版本。

## 4. original：编译并运行功能仿真

编译Scala/Chisel生成器、RTL和4×4 Verilator仿真器：

```bash
cd "$SRC/sims/verilator"
make -j8 CONFIG=FSA4X4Fp16Config \
  CXX="$CXX" CC="$CC" LINK="$CXX" AR=/usr/bin/ar
```

先确认生成配置存在，再运行seq4：

```bash
cd "$SRC/generators/fsa/python"
test -s ../../../sims/verilator/generated-src/chipyard.harness.TestHarness.FSA4X4Fp16Config/chipyard.harness.TestHarness.FSA4X4Fp16Config.FSAConfig.json
mkdir "$ORIGINAL_WORK/sim-seq4-attempt01"
uv run main.py --seq_q 4 --seq_kv 4 --config FSA4X4Fp16Config \
  --diff --max_cycles 10000000 --output_dir "$ORIGINAL_WORK/sim-seq4-attempt01"
```

同一个4×4仿真器追加seq8分块计算，无需重新编译：

```bash
mkdir "$ORIGINAL_WORK/sim-seq8-attempt01"
uv run main.py --seq_q 8 --seq_kv 8 --config FSA4X4Fp16Config \
  --diff --max_cycles 10000000 --output_dir "$ORIGINAL_WORK/sim-seq8-attempt01"
```

观察运行完成及FSA/PyEasyFloat相对Torch的MAE、MSE、MaxErr、RelErr，保留输出。序列长度与PE阵列规模不同；程序退出成功不自动代表满足数值验收阈值。

## 5. original：生成U55C bitstream

加载安装了U55C器件支持和许可证的Vivado。下面2020.2路径是环境示例；**本轮已验证original编译、仿真和RTL展开，尚未完成U55C完整布局布线及实板验收**，不能把NM37的工具验收直接算到U55C上。

```bash
source /path/to/Xilinx/Vivado/2020.2/settings64.sh
cd "$SRC/fpga"
make SUB_PROJECT=u55c CONFIG=EmptyU55CConfig TOP=EmptyChipTop bitstream
```

该命令依次执行板级RTL生成、综合、布局布线和bit导出。成功后的目标文件：

```text
fpga/generated-src/chipyard.fpga.u55c.U55CFPGATestHarness.EmptyU55CConfig/obj/U55CFPGATestHarness.bit
```

检查实际setup/hold时序、DRC和导出日志。保留routed DCP、时序/资源报告及同次生成的FSAConfig.json；不能只看bit文件是否存在。

```bash
export U55C_BUILD="$SRC/fpga/generated-src/chipyard.fpga.u55c.U55CFPGATestHarness.EmptyU55CConfig"
sha256sum "$U55C_BUILD/obj/U55CFPGATestHarness.bit" \
  "$U55C_BUILD/chipyard.fpga.u55c.U55CFPGATestHarness.EmptyU55CConfig.FSAConfig.json" \
  | tee "$ORIGINAL_WORK/u55c-sha256.txt"
```

## 6. original：烧录后运行attention、查看RelErr

在Vivado Hardware Manager中连接**实际U55C**，选择上述bit并执行Program Device，保存烧录日志。这是U55C镜像，不能烧到U280/NM37/NP19A。更换环境变量不等于烧录。

烧录后恢复PCIe枚举并加载匹配内核的XDMA驱动。必要时保持板卡供电进行主机软重启。原始软件默认使用`/dev/xdma0_*`，多卡机器先核对设备身份。

```bash
lspci -Dnnk
ls -l /dev/xdma0_*
readlink -f /sys/class/xdma/xdma0_user/device
cd "$SRC/generators/fsa/python"
test -s "$U55C_BUILD/chipyard.fpga.u55c.U55CFPGATestHarness.EmptyU55CConfig.FSAConfig.json"
uv run main.py --seq_q 16 --seq_kv 16 \
  --config EmptyU55CConfig --engine FPGA --diff
```

如设备访问权限不足，使用已准备好的venv Python绝对路径运行：

```bash
sudo "$SRC/generators/fsa/python/.venv/bin/python" -u main.py \
  --seq_q 16 --seq_kv 16 --config EmptyU55CConfig --engine FPGA --diff
```

查看终端打印的RelErr等数值及性能计数器，保存完整终端日志。original保留上游软件原貌，后续板卡分支的多次启动正确性修复不在本分支，不能假定重复运行已验收。

## 补充A：其他版本怎么复现

表格最后一列是各固定版本的完整README。其他版本通常使用以下入口，**不能把它替换进上面的original流程**：

```bash
python3 scripts/fsa.py deps --local-source /absolute/path/to/existing-source --report "$WORK/dependencies.json"
python3 scripts/fsa.py doctor
python3 scripts/fsa.py build --out "$BUILD_OUT"
# 优化版本再执行verify；sim规模按该版本README选择。
python3 scripts/fsa.py sim --out "$BUILD_OUT" --array-size 4
python3 scripts/fsa.py elaborate --out "$BUILD_OUT"
python3 scripts/fsa.py implement --out "$BUILD_OUT"
python3 scripts/fsa.py export --out "$BUILD_OUT" --result-out "$EXPORT_OUT"
```

此处是入口概览，WORK/BUILD_OUT/EXPORT_OUT、工具环境和Python准备必须按对应README设置。原始U280/NM37/NP19A仅固定sim4；A70-P3为sim4/16；A100及以后为sim4/8/16。NM37优化版板测用统一test；NP19A用独立attention.py；原始U280/NM37板测尚不能套用这两种入口。

NP19A使用Vivado2024.2、xcvu19p-fsva3824-2-e和指定DDR4；NM37优化版使用Vivado2020.2_AR75986。板卡内存、工具版本和时钟配置不能混用。详细分支状态、历史里程碑、缓存与板测差异保留在[补充指南](docs/reproduction/all-versions.md)。

## 补充B：首次安装Spike/FESVR（已有双库可跳过）

先准备GCC/G++13.3、make及dtc；Ubuntu缺少dtc时安装device-tree-compiler。这里安装主机库，不需要完整RISC-V交叉编译器。

```bash
command -v dtc
cd "$SRC"
git -c url.https://github.com/.insteadOf=git@github.com: \
  submodule update --init --checkout -- toolchains/riscv-tools/riscv-isa-sim
export SPIKE_SOURCE="$SRC/toolchains/riscv-tools/riscv-isa-sim"
test "$(git -C "$SPIKE_SOURCE" rev-parse HEAD)" = 76858cc3aa178446584eae52f82e0a933e71f8db
export SPIKE_BUILD="$ORIGINAL_WORK/spike-build-attempt01"
export RISCV="$ORIGINAL_WORK/toolchain/spike-76858cc3"
mkdir "$SPIKE_BUILD"
cd "$SPIKE_BUILD"
CC=/usr/bin/gcc CXX=/usr/bin/g++ "$SPIKE_SOURCE/configure" \
  --prefix="$RISCV" --with-boost=no --with-boost-asio=no --with-boost-regex=no
make -j4
make libfesvr.a
make install
install -m 644 libfesvr.a "$RISCV/lib/libfesvr.a"
export PATH="$RISCV/bin:$PATH"
export LD_LIBRARY_PATH="$RISCV/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
test -s "$RISCV/lib/libfesvr.a"
test -s "$RISCV/lib/libriscv.so"
test -s "$RISCV/include/fesvr/htif.h"
cd "$SRC"
```

成功后返回第3节的源码依赖准备步骤，保留这里设置的RISCV，不要再覆盖成示例路径。

## 补充C：结果保留与失败恢复

下载缓存可以共用，依赖源码按各版本pin独立恢复；不要软链接共享可变源码。JAR、RTL、仿真器、DCP和bit不得混用。固定源码与输入后才能比较运行时间；bubble不直接等于PE空闲率。

每一步失败先看完整日志，保留源码commit、工具版本、依赖记录、生成配置、报告、bit校验和和板测输出。修复后使用新的attempt，不删除缓存或制造成功标记。不要在构建期间切换commit。旧FSA仓库和已有结果继续保留。
