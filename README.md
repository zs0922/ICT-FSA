# ICT-FSA：全部板卡与版本的复现入口

本README是默认分支`codex/ict-fsa-integration`的统一导航。先选择板卡/配置，再到固定commit的独立源码目录构建；**默认分支当前代码是NM37 A150配置，不是任意板卡通用硬件配置**。不需要依次构建A70→A100→A150，也不需要旧FSA仓库或另一套integration-tools。

## 1. 选择分支与固定版本

“支持”表示提供对应源码和入口，验证程度以表中证据为准；源码可用、时序通过、bit导出、实板通过是不同阶段。所有分支尚不能一概视为完整板级发布验收完成。

| 分支 | 板卡 / 配置 | 固定commit及该版本README | 验证范围 / 建议 |
|---|---|---|---|
| `original` | U55C原始上游 | [`474e92dc018df7a7a818aa329db967ebb829108c`](https://github.com/zs0922/ICT-FSA/blob/474e92dc018df7a7a818aa329db967ebb829108c/README.md) | 编译、sim4、RTL通过；完整实现未验证 |
| `original-u280` | U280未优化，70MHz | [`ab28e170feb2c29d347dd476f45fd29456cf0d7b`](https://github.com/zs0922/ICT-FSA/blob/ab28e170feb2c29d347dd476f45fd29456cf0d7b/README.md) | 编译、sim4、完整实现及bit导出通过；未实板验收 |
| `original-nm37-civ` | NM37未优化，70MHz | [`87cd26500fc88f7051771e3cb1670001375c6b1f`](https://github.com/zs0922/ICT-FSA/blob/87cd26500fc88f7051771e3cb1670001375c6b1f/README.md) | 编译、sim4、完整实现及bit导出通过；未实板验收 |
| `original-np19a` | NP19A未优化，70MHz，DDR4 | [`8407bdd8d4bd6d0aae56a1a549353f8c35f2124f`](https://github.com/zs0922/ICT-FSA/blob/8407bdd8d4bd6d0aae56a1a549353f8c35f2124f/README.md) | 编译、sim4、完整实现及bit导出通过；未实板验收 |
| `codex/nm37-a70-p3` | NM37 A70-P3 | [`8cc6b42536334892b88f6214f39d3afe5daa2504`](https://github.com/zs0922/ICT-FSA/blob/8cc6b42536334892b88f6214f39d3afe5daa2504/README.md) | 固定回归、seq1024及约束时序通过；非完整板级验收 |
| `codex/a100-reproduction-fix` | NM37 A100，推荐复现 | [`9b8911f4e9e5c6af49fe6b6287e9c88ee1031352`](https://github.com/zs0922/ICT-FSA/blob/9b8911f4e9e5c6af49fe6b6287e9c88ee1031352/README.md) | 固定回归、seq1024及约束时序通过；非完整板级验收 |
| `codex/a110-reproduction-fix` | NM37 A110/APB55，推荐复现 | [`7deb8e3e9416f2f3d25df9d45a5f65fc38302cda`](https://github.com/zs0922/ICT-FSA/blob/7deb8e3e9416f2f3d25df9d45a5f65fc38302cda/README.md) | 固定回归、seq1024及约束时序通过；CDC未完全闭合 |
| `codex/nm37-a120-apb60` | NM37 A120/APB60 | [`462a341eb250f74a3d0c7ca415ef765f693c1839`](https://github.com/zs0922/ICT-FSA/blob/462a341eb250f74a3d0c7ca415ef765f693c1839/README.md) | 迁入源码；旧实验有实现证据，本仓独立全流程未验收 |
| `codex/nm37-a150-apb100` | NM37 A150/APB100 | [`1e07e6b09422435ce2914cbbb8a34bf793df708b`](https://github.com/zs0922/ICT-FSA/blob/1e07e6b09422435ce2914cbbb8a34bf793df708b/README.md) | 迁入源码；旧实验有实现证据，本仓独立全流程未验收 |
| `codex/u280-port` | 历史U280迁移里程碑 | [`3d1714de26aeaad172461bd96e6c8fc26e63109a`](https://github.com/zs0922/ICT-FSA/blob/3d1714de26aeaad172461bd96e6c8fc26e63109a/README.md) | 保留来源；新复现优先original-u280 |
| `codex/nm37-port` | 历史NM37迁移里程碑 | [`00e021c635cd31d013cf00fd24cba687dc0b4be5`](https://github.com/zs0922/ICT-FSA/blob/00e021c635cd31d013cf00fd24cba687dc0b4be5/README.md) | 保留来源；新复现优先original-nm37-civ |
| `codex/nm37-a100` | 原A100迁移里程碑 | [`f8650f9576bf681bfae38a2ab40718fc2ace4262`](https://github.com/zs0922/ICT-FSA/blob/f8650f9576bf681bfae38a2ab40718fc2ace4262/README.md) | 保留原提交；推荐上面的复现修复分支 |
| `codex/nm37-a110-apb55` | 原A110/APB55迁移里程碑 | [`b595900e91bda33925f059ff585771ae5ecddfcd`](https://github.com/zs0922/ICT-FSA/blob/b595900e91bda33925f059ff585771ae5ecddfcd/README.md) | 保留原提交；推荐上面的复现修复分支 |

其他分支：`codex/ict-fsa-integration`是当前总入口；`codex/original-baselines`保存早期三个原始基线的整理记录。远端`dependabot/*`是自动依赖更新提议，不是支持/验收配置。仅本地的`codex/ict-fsa-reproduction`是复现报告整理分支，不是单独板卡配置。

原始FSA/U55C集成来自VCA-EPFL/chipyard-fsa，Berkeley Chipyard是框架上游。来源见[原始基线说明](docs/baselines/README.md)。A70-P3已经包含优化，不属于“original”。A100/A110修复分支清理了无效历史约束并更新复现记录，不代表原FSA算法错误。证据见[独立复现记录](reports/ICT_FSA_REPRODUCTION_20261028.md)、[原始基线记录](reports/ORIGINAL_BASELINES_20261102.md)。NP19A验收报告在其固定分支的`reports/ORIGINAL_NP19A_BASELINE.md`。

## 2. 独立拉取与切换

以下用NP19A示例；选择其他版本时，把BRANCH和COMMIT同时替换为表中同一行。目录已存在时换attempt02，不删除旧结果。交互终端不要启用`set -euo pipefail`；每条成功后再继续。

```bash
export BRANCH=original-np19a
export COMMIT=8407bdd8d4bd6d0aae56a1a549353f8c35f2124f
export WORK="$HOME/ict-fsa-${BRANCH//\//-}-${COMMIT:0:8}-attempt01"
mkdir "$WORK"
git clone --branch "$BRANCH" https://github.com/zs0922/ICT-FSA.git "$WORK/source"
export SRC="$WORK/source"
git -C "$SRC" checkout --detach "$COMMIT"
cd "$SRC"
git rev-parse HEAD | tee "$WORK/source-commit.txt"
export BUILD_OUT="$WORK/build-attempt01"
export EXPORT_OUT="$WORK/bits-attempt01"
```

构建期间不pull/checkout。`original`使用上游make流程，直接按其README配置`ORIGINAL_WORK`并执行；不能运行下面的统一`scripts/fsa.py`入口。

## 3. 环境、依赖和共享缓存

首先读取**所选checkout自身**的`docs/reproduction/environment.md`和README。NP19A要求Vivado2024.2和VU19P支持；NM37优化流程使用Vivado2020.2_AR75986；其他板卡按各自文档。不能全仓统一替换Vivado版本。还需指定版本的JDK20.0.2、firtool1.75、Verilator5.022、GCC/G++13.3、RISCV/FESVR和uv；原始上游的具体环境以其README为准。

先设置真实工具路径、JAVA_HOME、RISCV、CC/CXX、CHISEL_FIRTOOL_PATH和LD_LIBRARY_PATH，避免继承旧实验的`-Dfsa.*`参数。缺Spike/FESVR时按所选分支环境文档安装，不能把RISCV指向空目录。

### Git依赖：优先复用已有本地下载

同一commit不必重复联网下载，但每个分支仍按自己的`locks/dependencies.json`取版本。以下三种方式**选择一种**，报告文件须为新路径、位于源码外。

```bash
# 推荐：已有其他版本下载齐全的源码根目录；不是build目录。
export DEPS_SOURCE=/absolute/path/to/existing-source
python3 scripts/fsa.py deps --local-source "$DEPS_SOURCE" \
  --report "$WORK/dependencies.json"
```

```bash
# 没有可复用依赖时，首次从网络初始化。
python3 scripts/fsa.py deps --report "$WORK/dependencies.json"
```

```bash
# 已有符合脚本manifest格式的离线Git bundle包时。
python3 scripts/fsa.py deps --offline-dir /absolute/path/to/dependency-bundles \
  --report "$WORK/dependencies.json"
```

`--local-source`不修改旧仓库，按目标pin独立复制Git仓库，不使用软链接、alternates或硬链接。因此节省重复网络下载，但仍占独立磁盘空间；删除旧源码不会破坏新构建。来源缺少所需commit时会报错，不会偷偷使用错误版本。当前脚本不会自动搜索其他工程缓存，也不会自动重置已有错误HEAD；检查报错后保留原目录并选新checkout。原始`original`的子模块初始化按其自身README执行。

### 软件包缓存可以共用，构建产物独立

在uv sync或build之前设置（新终端需重新设置）：

```bash
export ICT_DOWNLOAD_CACHE="$HOME/.cache/ict-fsa-downloads"
mkdir -p "$ICT_DOWNLOAD_CACHE"
export UV_CACHE_DIR="$ICT_DOWNLOAD_CACHE/uv"
export COURSIER_CACHE="$ICT_DOWNLOAD_CACHE/coursier/v1"
export SBT_OPTS="-Dsbt.ivy.home=$ICT_DOWNLOAD_CACHE/sbt/ivy2 -Dsbt.boot.directory=$ICT_DOWNLOAD_CACHE/sbt/boot -Dsbt.supershell=false -Dsbt.server.forcestart=false"
export JAVA_TOOL_OPTIONS="-Dsbt.supershell=false -Dsbt.server.forcestart=false -Dsbt.server.autostart=false $SBT_OPTS"
unset JDK_JAVA_OPTIONS _JAVA_OPTIONS
python3 scripts/fsa.py doctor
uv sync --frozen --python 3.13 --project "$SRC/generators/easyfloat"
uv sync --frozen --python 3.13 --project "$SRC/generators/fsa/python"
export FSA_PYTHON="$SRC/generators/fsa/python/.venv/bin/python"
```

Coursier/Ivy/uv缓存可复用；`.venv`、target、JAR、RTL、仿真器、DCP、bit按版本独立。不要将旧产物复制到新目录冒充重新构建。优化版本的`verify`还需要按对应环境文档安装形式验证工具。

## 4. 编译、验证与仿真

适用于统一入口的分支：

```bash
python3 scripts/fsa.py build --out "$BUILD_OUT"
```

按下表选择命令，不要把全部命令无条件运行：

| 配置 | verify | 固定sim阵列 |
|---|---|---|
| original-u280 / original-nm37-civ / original-np19a、历史U280/NM37迁移 | 跳过 | 4 |
| A70-P3 | 执行 | 4、16 |
| A100 / A110 / A120 / A150及复现修复版 | 执行 | 4、8、16 |
| original U55C | 上游README流程 | 上游README流程 |

```bash
# 仅优化配置执行
python3 scripts/fsa.py verify --out "$BUILD_OUT"
# 按上表逐个执行支持的规模
python3 scripts/fsa.py sim --out "$BUILD_OUT" --array-size 4
# 支持8/16的配置再执行：
# python3 scripts/fsa.py sim --out "$BUILD_OUT" --array-size 8
# python3 scripts/fsa.py sim --out "$BUILD_OUT" --array-size 16
```

`array-size`是PE阵列规模，seq1024是序列长度，二者不同。原始迁移的sim4不表示板上阵列只有4×4；板上为16×16。优化配置已有sim16后可追加：

```bash
timeout --signal=TERM --kill-after=10s 7200s \
  python3 scripts/fsa.py sim-extra --out "$BUILD_OUT" \
  --array-size 16 --seq 1024 --max-cycles 10000000 \
  --result-out "$WORK/sim-seq1024-attempt01"
```

此命令不适用于仅恢复sim4的原始基线。A70与后续版本仿真的内存端口/带宽不同，周期不能直接当作纯提频收益，详见[NM37详细说明](docs/reproduction/nm37-optimized-workflow.md)。

## 5. RTL、布局布线与bitstream

```bash
python3 scripts/fsa.py elaborate --out "$BUILD_OUT"
python3 scripts/fsa.py implement --out "$BUILD_OUT"
python3 scripts/fsa.py status --out "$BUILD_OUT"
python3 scripts/fsa.py export --out "$BUILD_OUT" --result-out "$EXPORT_OUT"
(cd "$EXPORT_OUT" && sha256sum -c SHA256SUMS)
cat "$EXPORT_OUT/experiment.json"
```

elaborate生成RTL；implement综合并完整布局布线；export单独生成bit。不能把source PASS当成阶段成功。实验导出检查实际时序、器件/时钟及阻断性DRC，不要求手写CDC审查JSON；时序通过不代表CDC全部闭合或已经上板。A110等若仅CDC审查门阻塞、实际routed产物已记录，可按其文档执行实验export；综合/布线/时序失败不可绕过。

bit名称按profile确定，例如NP19A为`NP19A_EXPERIMENTAL.bit`，A150为`A150-APB100_EXPERIMENTAL.bit`；以experiment.json为准，勿猜测文件名。U55C original使用自身README的make bitstream流程；本轮未验证U55C完整实现。

## 6. 实际烧录与板测入口

先核对实际板卡、内存配置、JTAG target/device和PCI BDF。NP19A目前使用MTA16ATF2G64HZ-2G3 16GB DDR4；实装不符须调整配置再构建。更改环境变量不等于烧录。

对于提供统一program入口的版本，参考以下模板（实际硬件名称必须修改）：

```bash
export HW_TARGET='实际完整JTAG target'
export HW_DEVICE='实际器件名称'
export BDF='0000:18:00.0'  # 示例，按本机确认
export PROGRAM_OUT="$WORK/program-attempt01"
python3 scripts/fsa.py program --export "$EXPORT_OUT" \
  --hw-target "$HW_TARGET" --hw-device "$HW_DEVICE" --bdf "$BDF" \
  --out "$PROGRAM_OUT" --dry-run
python3 scripts/fsa.py program --export "$EXPORT_OUT" \
  --hw-target "$HW_TARGET" --hw-device "$HW_DEVICE" --bdf "$BDF" \
  --out "$PROGRAM_OUT"
```

program配置SRAM，不写flash。首次未枚举时先通过Hardware Manager烧录，保持板卡供电进行主机软重启，再确认BDF。需要匹配内核的XDMA驱动；不自动卸载/复位其他板卡。

```bash
lspci -Dnnk -s "$BDF"
ls -l /dev/xdma*
export DEVICE=xdma0  # 核对实际映射
readlink -f "/sys/class/xdma/${DEVICE}_user/device"
export RESULT="$WORK/board/seq16-attempt01"
```

### NM37优化版本 A70-P3/A100/A110/A120/A150

使用对应源码、配套config/bit和本次真实烧录记录，完整命令见[NM37板测流程](docs/reproduction/nm37-optimized-workflow.md)：

```bash
sudo timeout --signal=TERM --kill-after=10s 600s \
  "$FSA_PYTHON" -u "$SRC/scripts/fsa.py" test --export "$EXPORT_OUT" \
  --receipt "$PROGRAM_OUT/program.json" --device "$DEVICE" --bdf "$BDF" \
  --seq 16 --repeat 5 --warmup 1 --out "$RESULT"
```

### NP19A

使用该分支独立板测脚本；不要调用NM37统一test：

```bash
sudo timeout --signal=TERM --kill-after=10s 600s \
  "$FSA_PYTHON" -u "$SRC/scripts/np19a/attention.py" \
  --config "$EXPORT_OUT/FSAConfig.json" --bit "$EXPORT_OUT/NP19A_EXPERIMENTAL.bit" \
  --device "$DEVICE" --bdf "$BDF" --seq 16 --seed 0 --out "$RESULT"
sudo python3 -m json.tool "$RESULT/result.json"
```

关注`bitwise_equal_pyeasyfloat`、`errors_vs_torch.RelErr`及counters。该脚本中的bit路径不是实时硬件身份回读，须保留真实烧录记录。seq16通过后换新RESULT、改`--seq 1024`和timeout7200s再测。完整NP19A命令见上表固定README。

### 原始U55C、U280、NM37迁移基线

使用各自README的板级说明。U280统一test会拒绝设备映射；original-nm37-civ的runtime未声明原始NM37 profile；U55C使用原始软件流程。这些版本的源码/实现入口可复现，但尚不能承诺一组已验收的统一attention命令。不要把优化NM37或NP19A脚本套上去声称板测通过。

## 7. 结果、性能比较与失败恢复

保存源码commit、profile、依赖报告、工具版本、阶段日志/收据、时序/资源/CDC/约束报告、bit/config/manifest/校验和、烧录日志及完整板测结果目录。NM37优化版可用`scripts/fsa.py summarize`汇总，详见详细流程；NP19A的result.json格式不同，当前不能直接混入该汇总器。

RelErr是对Torch的相对误差，PyEasyFloat逐位一致是另一项检验。execTime按实际配置频率换算；bubble计数比不直接等于PE空闲率。跨板卡比较必须固定输入、seed、精度、主机软件和测试方式，DDR与HBM差异也会影响性能。没有重新烧录的历史A100/A110数据不能作为对应硬件验收证据。

发生失败先查看`$BUILD_OUT.ict-state/`与阶段日志，保留失败产物和下载缓存。修复后使用独立源码/新输出，不手工制造成功标记，不覆盖已有结果。详细见[恢复说明](docs/reproduction/recovery.md)。正式验收标签应在对应源码复现和实板通过后再创建。
