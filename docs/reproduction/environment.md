# 环境准备

本次候选沿用已有 NM37 验证环境：JDK 20.0.2、firtool 1.75.0、Verilator 5.022、Vivado 2020.2 + AR75986。Python 使用源码自带 uv.lock 和 Python 3.13，Torch 2.6。U280/初始 NM37 使用这一环境的全流程重建尚待验证，不能把 NM37 旧记录当作 U280 证据。

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
# 不要继承之前 A100/A110/A120/A150 实验的 -Dfsa.* 手动参数。
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

还需要 GNU make、C/C++ 编译器、Git、uv、器件支持/许可证、已安装的 XDMA 驱动（仅板测）以及证明工具。A70-P3 默认使用 `yowasp-yosys`，可以通过 `YOSYS=/absolute/path/to/yowasp-yosys` 指定；A100/A110/A120/A150 对照各自 `scripts/nm37-a100`、`scripts/nm37-a110`、`scripts/nm37-a120`、`scripts/nm37-a150` 验证器的实际需求。

用于定向形式验证的工具采用固定 Python 包版本和 Python 3.13；仓库含完整 requirements。不要用未指定版本的 `python3 -m venv`：Chipyard conda 环境可能提供 Python 3.10，与这些固定包的 Python 要求不兼容。创建独立环境：

```bash
uv venv --python 3.13 "$WORK/formal-env"
uv pip install --python "$WORK/formal-env/bin/python" \
  -r "$SRC/scripts/ict/formal-requirements.txt"
export YOSYS="$WORK/formal-env/bin/yowasp-yosys"
"$YOSYS" -V
```

`RISCV` 是 Chipyard make 的必需变量，即使目标设计不运行 RISC-V 指令也不能省略；Verilator 需要其中的 FESVR/Spike 头文件和库。若使用已有 Chipyard conda 环境，先激活对应环境，再检查其 `$RISCV/lib/libfesvr.a` 和 `libriscv.so`，不能只设置一个空目录。

`doctor` 检查可执行文件、四个主要工具版本、GCC/G++13.3、RISCV 库和遗留 JVM 参数；它不能提前证明板卡连接、Vivado 器件授权、硬件功能、许可证余量或完整布局布线可用。实际阶段产生的日志才是对应验收证据。

下载缓存可共用：Coursier/Ivy/Maven、uv 和 Git bundle。生成 JAR、RTL、仿真器及 DCP 不能直接从别的版本复制来冒充本次构建。首次下载失败应修复网络后重试，不要以清空所有缓存作为默认处理。

## sbt 下载缓存的位置

`variables.mk` 默认用当前源码内的 `.sbt`、`.sbt/boot` 和 `.ivy2`。只在 `JAVA_TOOL_OPTIONS` 中指定共享目录可能被 make 后面的 `SBT_OPTS` 覆盖；日志中应核对实际命令。需要跨独立 checkout 共用下载缓存时，在首次 build 前明确设置：

```bash
export ICT_SBT_CACHE="$WORK/download-cache/sbt"
mkdir -p "$ICT_SBT_CACHE/boot" "$ICT_SBT_CACHE/global" "$ICT_SBT_CACHE/ivy2"
# 缓存路径避免空格；仅复用下载缓存，不复制 target、生成器 JAR 或 RTL。
export SBT_OPTS="-Dsbt.ivy.home=$ICT_SBT_CACHE/ivy2 -Dsbt.global.base=$ICT_SBT_CACHE/global -Dsbt.boot.directory=$ICT_SBT_CACHE/boot -Dsbt.supershell=false -Dsbt.server.forcestart=false"
# verify 的部分定向测试直接执行 java，不经过 make，也需同样的缓存路径。
export JAVA_TOOL_OPTIONS="$JAVA_TOOL_OPTIONS $SBT_OPTS"
```

并发构建尽量使用各自缓存副本，避免旧 sbt 缓存锁相互等待。首次联网下载仍是必需的，除非已有对应版本的完整缓存。

## 首次安装 Spike/FESVR库

可以独立构建 A120/A150，无需先运行其他硬件版本。`RISCV` 需要指向已安装 Spike/FESVR 头文件和主机库的前缀；只 export 一个空路径不会安装库。若 doctor 只有 `RISCV/libfesvr.a`、`RISCV/libriscv.so` 为 false，先检查是否已有完整安装；否则按以下步骤构建。这里不需要完整 RISC-V 交叉编译器。

先执行 `deps` 初始化锁定源码（该命令不依赖 doctor 成功），并安装本机 C/C++ 编译工具和 dtc：

```bash
cd "$SRC"
python3 scripts/fsa.py deps --report "$WORK/deps-$COMMIT.json"
sudo apt-get update
sudo apt-get install build-essential device-tree-compiler

git -C "$SRC/toolchains/riscv-tools/riscv-isa-sim" rev-parse HEAD
# 当前 A120/A150 锁定值：76858cc3aa178446584eae52f82e0a933e71f8db
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

逐条成功后继续；不要把失败后的 make install 当作成功。安装目录在 WORK 下，无需 sudo make install，不修改已有 `$HOME/riscv`。编译目录放在源码外，避免触发源码未跟踪文件检查。后续新终端保留相同 RISCV/PATH/LD_LIBRARY_PATH。成功初始化的 deps 不必再下载；接着执行根 README 的两个 uv sync 和本页的形式验证工具准备。

A150 审计器开发测试中的固定 AST 序列化指纹由 Python 3.14 生成；运行 `python3 -m unittest discover -s scripts/nm37-a150 -p 'test_*.py'` 时使用 Python 3.14。此项是审计器自身开发回归，不是日常 `fsa.py verify` 的新增前置条件，FSA/EasyFloat 和形式工具环境仍使用前述 Python 3.13。
