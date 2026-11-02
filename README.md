# original-nm37-civ：NM37-CIV 初始移植基线

本分支从 ICT-FSA `00e021c635cd31d013cf00fd24cba687dc0b4be5` 建立，硬件来源为旧 FSA `57344208e4b88e4eed87e3bf4e9dd9a790d06e84`。这里只包含 U280 与 NM37 的板级迁移及历史正确性修复；**没有加入后续 P0/P1/P2/P3、ShiftRightJam 或 A100 流水优化**。70 MHz 是目标频率，不代表已完成本分支时序验收。

本分支保留自己的 FSA、easyfloat、FPGA shell 和依赖锁，不从优化分支拷贝 JAR/RTL/DCP。来源及补丁哈希见 [NM37 来源清单](docs/history/NM37/source-provenance.json)。本次整理不修改硬件目录。

## 本分支的最短完整流程

仅在本地交付时使用本地 ICT-FSA 路径；本分支尚未 push，不要假定远端已有它。发布后可将 `ICT_REPO` 换为 GitHub URL。

```bash
export ICT_REPO=/absolute/path/to/ICT-FSA
export WORK="$HOME/ict-fsa-original-nm37-civ"
mkdir -p "$WORK"
git clone --no-hardlinks --branch original-nm37-civ "$ICT_REPO" "$WORK/source"
export SRC="$WORK/source"
cd "$SRC"
git rev-parse HEAD | tee "$WORK/source-commit.txt"
export BUILD_OUT="$WORK/build-attempt01"
```

先按[环境说明](docs/reproduction/environment.md)安装并加载工具，然后逐条执行。不要在交互式 tmux shell 中开启 `set -e`。

```bash
# 检查工具版本；不编译。
python3 scripts/fsa.py doctor
# 准备锁定的第三方源码；必须完成后再启动 build。
python3 scripts/fsa.py deps --report "$WORK/dependencies.json"
# 可选离线替代：deps --local-source /absolute/path/to/compatible/source --report ...
# 准备与本分支匹配的 Python 与 EasyFloat，不继承其他源码的 PYTHONPATH。
uv sync --frozen --python 3.13 --project "$SRC/generators/easyfloat"
uv sync --frozen --python 3.13 --project "$SRC/generators/fsa/python"
export FSA_PYTHON="$SRC/generators/fsa/python/.venv/bin/python"
# 编译 Scala/Chisel 生成器 JAR。
python3 scripts/fsa.py build --out "$BUILD_OUT"
# 编译 4x4 Verilator 仿真器，执行 seq4/seq8 并逐位比对 PyEasyFloat。
python3 scripts/fsa.py sim --out "$BUILD_OUT" --array-size 4
# 展开板上 16x16 设计及 IP 描述。
python3 scripts/fsa.py elaborate --out "$BUILD_OUT"
# 执行完整综合、布局布线，记录真实时序与资源。
python3 scripts/fsa.py implement --out "$BUILD_OUT"
python3 scripts/fsa.py status --out "$BUILD_OUT"
# 在实际时序与 DRC 满足导出条件时生成实验 bit，尚未烧录。
export EXPORT_OUT="$WORK/bits-attempt01"
python3 scripts/fsa.py export --out "$BUILD_OUT" --result-out "$EXPORT_OUT"
(cd "$EXPORT_OUT" && sha256sum -c SHA256SUMS)
```

本基线仅恢复 4x4 的固定仿真入口；板上 16x16 与仿真 4x4 不应混淆。没有后续版本的定向证明套件，因此不执行 `verify`、sim8 或 sim16。失败时保留输出和日志；用新的 attempt 输出重试，不手工补写成功记录。`implement` 的时序失败不表示源码构建失败，但不能据此宣称 70 MHz 通过。

## 验收范围与失败恢复

本次流程止于源码构建、固定仿真、板级展开和完整布局布线。只有布局布线时序与 DRC 满足要求时才能导出实验 bit。板测入口 `scripts/ict/runtime.py` 尚未声明 `NM37` profile，不能直接照搬 A70-P3/A100 的板测命令；本分支尚无新实板验收证据。

运行记录在 `$BUILD_OUT.ict-state/`，详细产物在 `$BUILD_OUT/`。检查 `status` 和阶段日志；完整通过看明确 `COMPLETE`，不能把 doctor/source 的 PASS 当成阶段通过。出现失败不要清空依赖缓存，不覆盖已有日志、不手写 seal；参考[恢复说明](docs/reproduction/recovery.md)，用新的输出 attempt 重新执行必要阶段。切换版本必须使用独立源码与输出。

[归档的通用说明](docs/reproduction/historical-common-readme.md)仅供查阅工具历史，不是本分支的执行清单。
