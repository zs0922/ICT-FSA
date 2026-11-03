# 环境准备

NP19A 使用以下工具环境：JDK 20.0.2、firtool 1.75.0、Verilator 5.022、Vivado 2024.2（安装 Virtex UltraScale+ xcvu19p 器件支持）。Python 使用源码自带 uv.lock 和 Python 3.13，Torch 2.6。NP19A 当前验证状态见根 README；历史 NM37 报告不是 NP19A 验收证据。

```bash
# 按机器实际安装位置修改这三行；不要原样使用示例路径。
export JAVA_HOME=/absolute/path/to/jdk-20.0.2
export RISCV=/absolute/path/to/riscv-toolchain
export PATH="$JAVA_HOME/bin:/absolute/path/to/circt/bin:/absolute/path/to/verilator/bin:$RISCV/bin:$PATH"
source /absolute/path/to/Vivado/2024.2/settings64.sh
export CC=/absolute/path/to/gcc-13.3.0
export CXX=/absolute/path/to/g++-13.3.0
export LD_LIBRARY_PATH="$RISCV/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CHISEL_FIRTOOL_PATH="$(dirname "$(command -v firtool)")"
export JAVA_TOOL_OPTIONS='-Dsbt.supershell=false -Dsbt.server.forcestart=false -Dsbt.server.autostart=false'
unset JDK_JAVA_OPTIONS _JAVA_OPTIONS
# 不要继承之前 A100/A110 实验的 -Dfsa.* 手动参数。
test -s "$RISCV/lib/libfesvr.a"
test -s "$RISCV/lib/libriscv.so"
"$CC" -dumpfullversion
"$CXX" -dumpfullversion
java -version
firtool --version
verilator --version
vivado -version
```

脚本中的 `JAVA_TOOL_OPTIONS` 只在子进程设置所需堆栈、内存和硬件配置。不要用宿主机默认的 JDK21/25 替代锁定 JDK20；旧 sbt/Scala 解析 JDK 类文件可能报 `bad constant pool index` 或 `Could not initialize class sbt.internal.parser.SbtParser`。

还需要 Python >=3.9（统一脚本入口）、GNU make、Git、uv、本机C/C++编译器及Vivado器件支持/许可证。FSA/EasyFloat使用Python3.13独立环境。本原始NM37基线不运行verify，不需要Yosys或formal-env。XDMA驱动和实际板卡连接仅在未来板测时需要。

`RISCV` 是 Chipyard make 的必需变量，即使目标设计不运行 RISC-V 指令也不能省略；Verilator 需要其中的 FESVR/Spike 头文件和库。若使用已有 Chipyard conda 环境，先激活对应环境，再检查其 `$RISCV/lib/libfesvr.a` 和 `libriscv.so`，不能只设置一个空目录。

`doctor` 检查可执行文件、四个主要工具版本、GCC/G++13.3、RISCV 库和遗留 JVM 参数；它不能提前证明板卡连接、Vivado 器件授权、硬件功能、许可证余量或完整布局布线可用。实际阶段产生的日志才是对应验收证据。

下载缓存可共用：Coursier/Ivy/Maven、uv 和 Git bundle。生成 JAR、RTL、仿真器及 DCP 不能直接从别的版本复制来冒充本次构建。首次下载失败应修复网络后重试，不要以清空所有缓存作为默认处理。

## 独立运行目录及可复用下载缓存

在根README设置WORK/SRC后，可使用以下块隔离本次下载与sbt运行目录。缓存可以预先从其他成功环境复制（不复制target、JAR、RTL、DCP）；首次下载需要网络。不要设置UV_OFFLINE=true，除非缓存已齐备。

```bash
mkdir -p "$WORK/cache" "$WORK/runtime"
chmod 700 "$WORK/runtime"
export XDG_CACHE_HOME="$WORK/cache"
export XDG_RUNTIME_DIR="$WORK/runtime"
export UV_CACHE_DIR="$WORK/cache/uv"
export COURSIER_CACHE="$WORK/cache/coursier/v1"
export ICT_SBT_CACHE="$WORK/cache/sbt"
export SBT_OPTS="-Dsbt.ivy.home=$ICT_SBT_CACHE/ivy2 -Dsbt.global.base=$ICT_SBT_CACHE/global -Dsbt.boot.directory=$ICT_SBT_CACHE/boot -Dsbt.supershell=false -Dsbt.server.forcestart=false"
export JAVA_TOOL_OPTIONS="-Dsbt.supershell=false -Dsbt.server.forcestart=false -Dsbt.server.autostart=false $SBT_OPTS"
export FSA_JOBS=4
export MAKEFLAGS=-j4
unset JDK_JAVA_OPTIONS _JAVA_OPTIONS
```

在限制本地Unix socket的执行沙箱里，sbt可能报`Operation not permitted`；应使用允许本地IPC的执行环境，保留失败日志并选择新的输出attempt。不要因此改硬件或伪造成功状态。

## 首次安装 Spike/FESVR库

本分支可以独立构建，无需先运行 A70-P3/A100/A110 等优化版本。`RISCV` 需要指向已安装 Spike/FESVR 头文件和主机库的前缀；只 export 一个空路径不会安装库。若 doctor 只有 `RISCV/libfesvr.a`、`RISCV/libriscv.so` 为 false，先检查是否已有完整安装；否则按以下步骤构建。这里不需要完整 RISC-V 交叉编译器。

先执行 `deps` 初始化锁定源码（该命令不依赖 doctor 成功），并安装本机 C/C++ 编译工具和 dtc：

```bash
cd "$SRC"
python3 scripts/fsa.py deps --report "$WORK/dependencies.json"
sudo apt-get update
sudo apt-get install build-essential device-tree-compiler

git -C "$SRC/toolchains/riscv-tools/riscv-isa-sim" rev-parse HEAD
# 当前 NM37 初始基线锁定值：76858cc3aa178446584eae52f82e0a933e71f8db
export SPIKE_SOURCE="$SRC/toolchains/riscv-tools/riscv-isa-sim"
export SPIKE_BUILD="$WORK/spike-build-attempt01"
export RISCV="$WORK/toolchain/spike-76858cc3"
mkdir -p "$SPIKE_BUILD"
cd "$SPIKE_BUILD"
"$SPIKE_SOURCE/configure" --prefix="$RISCV" \
  --with-boost=no --with-boost-asio=no --with-boost-regex=no
make -j4
make libfesvr.a
make install
install -m 644 libfesvr.a "$RISCV/lib/libfesvr.a"

export PATH="$RISCV/bin:$PATH"
export LD_LIBRARY_PATH="$RISCV/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
ls -lh "$RISCV/lib/libfesvr.a" "$RISCV/lib/libriscv.so"
ls -l "$RISCV/include/fesvr/htif.h"
cd "$SRC"
python3 scripts/fsa.py doctor
```

逐条成功后继续；不要把失败后的 make install 当作成功。安装目录在 WORK 下，无需 sudo make install，不修改已有 `$HOME/riscv`。编译目录放在源码外，避免触发源码未跟踪文件检查。后续新终端保留相同 RISCV/PATH/LD_LIBRARY_PATH。成功初始化的 deps 不必再下载；接着执行根 README 的两个 uv sync ；本基线无需形式验证工具。
