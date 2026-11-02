# U280 基线环境准备

统一入口 `python3` 需要 Python >=3.9；本轮实际使用3.10.14。算法/uv环境使用3.13.14。此版本没有后续NM37形式证明套件，不需要安装Yosys。

本次候选沿用已有 NM37 验证环境：JDK 20.0.2、firtool 1.75.0、Verilator 5.022、Vivado 2020.2 + AR75986。Python 使用源码自带 uv.lock 和 Python 3.13，Torch 2.6。本次U280编译、仿真、布局布线和恢复导出已独立验证，详见基线报告；不能把NM37旧记录当作U280证据。

```bash
# 按机器实际安装位置修改这三行；不要原样使用示例路径。
export JAVA_HOME=/absolute/path/to/jdk-20.0.2
export RISCV=/absolute/path/to/riscv-toolchain
export PATH="$JAVA_HOME/bin:/absolute/path/to/circt/bin:/absolute/path/to/verilator/bin:$RISCV/bin:$PATH"
source /absolute/path/to/Vivado/2020.2/settings64.sh
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

还需要 GNU make、C/C++ 编译器、Git、uv、器件支持/许可证、已安装的 XDMA 驱动（仅板测）。本分支不需要后续NM37定向形式验证工具。

`RISCV` 是 Chipyard make 的必需变量，即使目标设计不运行 RISC-V 指令也不能省略；Verilator 需要其中的 FESVR/Spike 头文件和库。若使用已有 Chipyard conda 环境，先激活对应环境，再检查其 `$RISCV/lib/libfesvr.a` 和 `libriscv.so`，不能只设置一个空目录。

`doctor` 检查可执行文件、四个主要工具版本、GCC/G++13.3、RISCV 库和遗留 JVM 参数；它不能提前证明板卡连接、Vivado 器件授权、硬件功能、许可证余量或完整布局布线可用。实际阶段产生的日志才是对应验收证据。

下载缓存可共用：Coursier/Ivy/Maven、uv 和 Git bundle。生成 JAR、RTL、仿真器及 DCP 不能直接从别的版本复制来冒充本次构建。首次下载失败应修复网络后重试，不要以清空所有缓存作为默认处理。

## 独立缓存与运行目录

在配置完上面的工具路径后、第一次 build 前执行。首次联网下载或完整缓存副本是必需的；缓存可复用，生成JAR/RTL/DCP不能复用。

```bash
export XDG_CACHE_HOME="$WORK/download-cache"
export XDG_RUNTIME_DIR="$WORK/runtime"
mkdir -p "$XDG_CACHE_HOME" "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
export UV_CACHE_DIR="$XDG_CACHE_HOME/uv"
export COURSIER_CACHE="$XDG_CACHE_HOME/coursier/v1"
export ICT_SBT_CACHE="$XDG_CACHE_HOME/sbt"
mkdir -p "$ICT_SBT_CACHE/boot" "$ICT_SBT_CACHE/global" "$ICT_SBT_CACHE/ivy2"
export SBT_OPTS="-Dsbt.ivy.home=$ICT_SBT_CACHE/ivy2 -Dsbt.global.base=$ICT_SBT_CACHE/global -Dsbt.boot.directory=$ICT_SBT_CACHE/boot -Dsbt.supershell=false -Dsbt.server.forcestart=false"
export JAVA_TOOL_OPTIONS="-Dsbt.supershell=false -Dsbt.server.forcestart=false -Dsbt.server.autostart=false $SBT_OPTS"
unset JDK_JAVA_OPTIONS _JAVA_OPTIONS
```

并发的独立源码构建建议使用不同缓存副本；同一个源码内build/sim/elaborate按README串行运行。若执行环境禁止Unix domain socket，sbt会报Operation not permitted；应在允许本机进程通信的正常终端构建，不是删除依赖或修改硬件。

## 首次安装 Spike/FESVR库

可以独立构建 U280，无需先运行其他硬件版本。`RISCV` 需要指向已安装 Spike/FESVR 头文件和主机库的前缀；只 export 一个空路径不会安装库。若 doctor 只有 `RISCV/libfesvr.a`、`RISCV/libriscv.so` 为 false，先检查是否已有完整安装；否则按以下步骤构建。这里不需要完整 RISC-V 交叉编译器。

先执行 `deps` 初始化锁定源码（该命令不依赖 doctor 成功），并安装本机 C/C++ 编译工具和 dtc：

```bash
cd "$SRC"
python3 scripts/fsa.py deps --report "$WORK/dependencies.json"
sudo apt-get update
sudo apt-get install build-essential device-tree-compiler

git -C "$SRC/toolchains/riscv-tools/riscv-isa-sim" rev-parse HEAD
# 当前 U280 锁定值：76858cc3aa178446584eae52f82e0a933e71f8db
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

逐条成功后继续；不要把失败后的 make install 当作成功。安装目录在 WORK 下，无需 sudo make install，不修改已有 `$HOME/riscv`。编译目录放在源码外，避免触发源码未跟踪文件检查。后续新终端保留相同 RISCV/PATH/LD_LIBRARY_PATH。成功初始化的 deps 不必再下载；接着执行根 README 的两个 uv sync；U280不需要形式验证工具。

