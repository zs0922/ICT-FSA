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

还需要 GNU make、C/C++ 编译器、Git、uv、器件支持/许可证、已安装的 XDMA 驱动（仅板测）以及证明工具。A70-P3 默认使用 `yowasp-yosys`，可以通过 `YOSYS=/absolute/path/to/yowasp-yosys` 指定；A100/A110 对照各自 `scripts/nm37-a100`、`scripts/nm37-a110` 验证器的实际需求。

用于定向形式验证的工具采用固定 Python 包版本；仓库含完整 requirements：

```bash
python3 -m venv "$WORK/formal-env"
"$WORK/formal-env/bin/pip" install -r "$SRC/scripts/ict/formal-requirements.txt"
export YOSYS="$WORK/formal-env/bin/yowasp-yosys"
"$YOSYS" -V
```

`RISCV` 是 Chipyard make 的必需变量，即使目标设计不运行 RISC-V 指令也不能省略；Verilator 需要其中的 FESVR/Spike 头文件和库。若使用已有 Chipyard conda 环境，先激活对应环境，再检查其 `$RISCV/lib/libfesvr.a` 和 `libriscv.so`，不能只设置一个空目录。

`doctor` 检查可执行文件、四个主要工具版本、GCC/G++13.3、RISCV 库和遗留 JVM 参数；它不能提前证明板卡连接、Vivado 器件授权、硬件功能、许可证余量或完整布局布线可用。实际阶段产生的日志才是对应验收证据。

下载缓存可共用：Coursier/Ivy/Maven、uv 和 Git bundle。生成 JAR、RTL、仿真器及 DCP 不能直接从别的版本复制来冒充本次构建。首次下载失败应修复网络后重试，不要以清空所有缓存作为默认处理。
