# ICT-FSA original：FSA/U55C 上游原始基线

这是移植 U280/NM37 之前的原始基线，硬件、Python 主机软件和 gitlink 保持
[VCA-EPFL/chipyard-fsa `54671054fedcd2c1f65bb2dd6939abdaf8071814`](https://github.com/VCA-EPFL/chipyard-fsa/commit/54671054fedcd2c1f65bb2dd6939abdaf8071814)
原貌。该提交于 2025-07-24 合并 FSA/U55C PR #22。Berkeley Chipyard 是框架上游，
不是本项目 FSA/U55C 的直接移植起点。原 Chipyard README 见
[upstream-README.md](docs/baselines/upstream-README.md)。

本分支只添加来源记录、README 和源一致性检查工具；不包含 U280/NM37 移植、P0～P3、
ShiftRightJam、A100 流水、复位复制或 APB 分频等后续修改。
`EmptyU55CConfig` 是 16×16、70MHz、单内存端口配置；仿真 `FSA4X4Fp16Config` 为 4×4，
不是板卡配置。它们的运行时间不能直接比较。

| 输入 | 固定版本 |
|---|---|
| Chipyard/FSA 集成 | `54671054fedcd2c1f65bb2dd6939abdaf8071814` |
| generators/fsa | `f4051d9e6e1aac80b74fee9c9cff0096e19f7acf` |
| generators/easyfloat | `44e1c369659c2c397548d2aecfc4ded3a74a111e` |
| fpga/fpga-shells | `d7c353201c61f1879afdb2fddf3c52283d450147` |

其余顶层依赖已由 gitlink 锁定，完整清单见
[original-provenance.json](docs/baselines/original-provenance.json)。嵌套依赖使用各父仓库的 gitlink，
不能使用 `git submodule update --remote`。这条历史分支仍然使用子模块，与新优化分支的
FSA/easyfloat 直接跟踪方式不同。

## 1. 创建独立源码目录

目前分支仅在本地，尚未 push。当前开发服务器可执行：

```bash
export ORIGINAL_WORK="$HOME/ict-fsa-original-reproduce"
mkdir -p "$ORIGINAL_WORK"
git clone --branch original --single-branch /home/zhangsi/tmp/ICT-FSA "$ORIGINAL_WORK/source"
cd "$ORIGINAL_WORK/source"
git rev-parse HEAD
python3 scripts/verify-original.py
```

发布后可把 clone 的仓库地址替换为 `https://github.com/zs0922/ICT-FSA.git`；正式交付应再
`git switch --detach <交付记录中的完整commit>`，不要把随时可能变化的分支名当作固定版本。
不要复用 A70/A100 的源码目录或生成目录。

## 2. 准备依赖和工具环境

主路径使用已有工具安装，不要求先运行任何优化版本。所需版本：JDK 20.0.2、
CIRCT firtool 1.75.0、Verilator 5.022、GCC/G++ 13.3.0、Python 3.13（由 uv 管理），
以及包含 `libfesvr.a` 和 `libriscv.so` 的 RISC-V/Spike 安装。sbt 1.8.2 已在源码锁定。
准备 Git、make、uv；以下路径必须替换为当前机器对应安装位置，不能指向不存在的目录。

```bash
export JAVA_HOME=/path/to/jdk-20.0.2
export RISCV=/path/to/riscv
export CHISEL_FIRTOOL_PATH=/path/to/circt/bin
export VERILATOR_BIN=/path/to/verilator/bin
export PATH="$JAVA_HOME/bin:$CHISEL_FIRTOOL_PATH:$VERILATOR_BIN:$PATH"
export CC=/usr/bin/gcc CXX=/usr/bin/g++
export USE_CHISEL6=1
export LD_LIBRARY_PATH="$RISCV/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export XDG_RUNTIME_DIR="$ORIGINAL_WORK/runtime"
export COURSIER_CACHE="$ORIGINAL_WORK/download-cache/coursier/v1"
export SBT_OPTS="-Dsbt.ivy.home=$ORIGINAL_WORK/download-cache/sbt/ivy2 -Dsbt.global.base=$ORIGINAL_WORK/download-cache/sbt/global -Dsbt.boot.directory=$ORIGINAL_WORK/download-cache/sbt/boot"
export JAVA_TOOL_OPTIONS="-Dsbt.supershell=false -Dsbt.server.forcestart=false -Dsbt.server.autostart=false $SBT_OPTS"
mkdir -p "$XDG_RUNTIME_DIR"
java -version
verilator --version
firtool --version
"$CXX" --version
ls "$RISCV/lib/libfesvr.a" "$RISCV/lib/libriscv.so"

cd "$ORIGINAL_WORK/source"
python3 scripts/prepare-original-deps.py
python3 scripts/verify-original.py --require-core-deps
uv sync --project generators/easyfloat --frozen
uv sync --project generators/fsa/python --frozen
```

依赖工具只获取当前编译涉及的顶层模块、Rocket 的四个 Scala 依赖和 Verilator 文件列表引用的 Vortex/fpnew 嵌套依赖，按各父 gitlink 固定
commit；它不下载与 FSA 编译无关的完整 Linux/FireSim 软件树，也不安装 RISC-V 工具链。
默认通过 `.gitmodules` 下载，仅本次 Git 命令把 GitHub SSH URL 转为 HTTPS。
本机已有完整历史对象时可使用 `--mirror-root /path/to/old-chipyard`，只读旧 Git 对象，
创建新的依赖工作树；该本地加速模式依赖旧对象存续，不可把它直接作为独立交付包。
本轮采用此加速路径，不能声称已对每个公网仓库完成全新网络下载。

源检查工具检查全部顶层 gitlink 的固定值、根仓库文件差异，以及三个核心依赖的工作树；
它不等价于所有依赖递归完整性审计。实际验证环境和结果见
[original-validation.md](docs/baselines/original-validation.md)。

上游替代环境准备方式是安装 Conda 后运行：

```bash
bash build-setup.sh --skip-ctags --skip-firesim --skip-marshal --skip-clean
source env.sh
```

该替代方式本轮没有从空机器完整执行，不作为已验证主路径。脚本下载范围较大，
固定源码不代表所有外部下载服务一直可用。网络中断保存日志并重试依赖准备；不要清空
下载缓存或把 gitlink 改到新版。

## 3. 编译 Verilator 仿真器

```bash
cd "$ORIGINAL_WORK/source/sims/verilator"
make -j8 CONFIG=FSA4X4Fp16Config CXX="$CXX" CC="$CC" LINK="$CXX" AR=/usr/bin/ar
```

这一步编译 Scala、生成 RTL，再编译 4×4 PE 阵列的 Verilator 仿真器。
命令行显式传入编译器，防止 Conda Verilator 的内置 CXX/LINK 覆盖环境变量，导致它与系统编译的
RISC-V 库产生 `__isoc23_*@GLIBC_2.38` 链接错误。
保存完整终端日志；出现任何失败先停止，不能只依据前面的来源 PASS 判断构建完成。

## 4. 运行 attention 功能仿真

安装 uv 后执行（原始 Python 项目要求 Python ≥3.13，uv 会按项目要求准备环境）；下面先确认生成的配置存在，避免原始 Python 入口回退到默认配置。

```bash
cd "$ORIGINAL_WORK/source/generators/fsa/python"
test -s ../../../sims/verilator/generated-src/chipyard.harness.TestHarness.FSA4X4Fp16Config/chipyard.harness.TestHarness.FSA4X4Fp16Config.FSAConfig.json
mkdir "$ORIGINAL_WORK/sim-seq4-attempt01"
uv run main.py --seq_q 4 --seq_kv 4 --config FSA4X4Fp16Config --diff --max_cycles 10000000 --output_dir "$ORIGINAL_WORK/sim-seq4-attempt01"
```

追加一个分块计算输入（同一个4×4 PE阵列，不需重编译）：

```bash
mkdir "$ORIGINAL_WORK/sim-seq8-attempt01"
uv run main.py --seq_q 8 --seq_kv 8 --config FSA4X4Fp16Config --diff --max_cycles 10000000 --output_dir "$ORIGINAL_WORK/sim-seq8-attempt01"
```

检查仿真正常结束以及 FSA/PyEasyFloat 对 Torch 的 MAE、MSE、MaxErr、RelErr。
`--seq_q/--seq_kv` 是输入序列长度，不是 PE 阵列尺寸。记录生成配置、输入规模和误差；
程序完成不自动代表达到某个数值验收阈值。

## 5. 生成 U55C RTL 和 bitstream

先加载支持 U55C 的 Vivado 环境并检查许可证；下面以本机可用的 2020.2_AR75986 为路径示例，原始 U55C 的完整实现尚未验收。这是 **U55C** 构建，不能烧到 U280/NM37。

```bash
source /path/to/Xilinx/Vivado/2020.2/settings64.sh
cd "$ORIGINAL_WORK/source/fpga"
make SUB_PROJECT=u55c CONFIG=EmptyU55CConfig TOP=EmptyChipTop bitstream
```

该上游命令串行执行 Scala/RTL 生成、综合、布局布线和 bitstream 导出。目标文件是：

```text
fpga/generated-src/chipyard.fpga.u55c.U55CFPGATestHarness.EmptyU55CConfig/obj/U55CFPGATestHarness.bit
```

检查完整实现日志、实际约束时钟、setup/hold 的 WNS/TNS、DRC 和导出日志；文件存在不能
代替验收。本分支没有引入手写 CDC 审查文件作为实验导出的前置条件。
保存 routed DCP、时序/资源报告、生成的 FSAConfig.json、bitstream 和 SHA256。
不要将后续 NM37 的已验证 Vivado 版本自动视为原始 U55C 的已验证工具版本。

## 6. U55C 上板小输入测试

使用 Vivado Hardware Manager 选择正确 U55C 设备并烧录上述 bitstream，保存烧录记录。
重新枚举正确的 PCIe 设备并加载 XDMA 驱动，检查设备节点访问权限；不要照抄其他机器的 BDF。
原始主机程序默认使用 `/dev/xdma0_*`，存在多块板时必须核对设备身份。

```bash
cd "$ORIGINAL_WORK/source/generators/fsa/python"
test -s ../../../fpga/generated-src/chipyard.fpga.u55c.U55CFPGATestHarness.EmptyU55CConfig/chipyard.fpga.u55c.U55CFPGATestHarness.EmptyU55CConfig.FSAConfig.json
uv run main.py --seq_q 16 --seq_kv 16 --config EmptyU55CConfig --engine FPGA --diff
```

保留 RelErr 等指标和性能计数器，但不要将原始主机软件多次执行行为默认视为已经修复。
U280 之后的历史正确性修复不在此分支；这是保留原貌的参考起点。

## 验证状态

以[original-validation.md](docs/baselines/original-validation.md)为准。来源核验、make dry-run、
编译、仿真、布局布线、板测是不同层次，不能相互替代。
