# original / U55C 验证记录（2026-11-02）

来源：VCA-EPFL/chipyard-fsa `54671054fedcd2c1f65bb2dd6939abdaf8071814`。
在线 GitHub commit 页确认 PR #22 合并及两父提交；本地旧 FSA 历史拥有同一对象。
ICT-FSA 原有整理历史未包含该对象，本次 original 分支导入该历史，未修改原始硬件。

## 实际结果

| 检查 | 结果 |
|---|---|
| 原始 tracked 源码/gitlinks | PASS，只有文档及辅助脚本不同 |
| 三个核心子模块 | PASS，原始 commit、无工作树改动 |
| 依赖准备 | PASS，从只读本地 Git 对象准备；未逐一验证公网全新下载 |
| Python easyfloat/FSA frozen sync | PASS |
| FPGA Scala assembly | PASS，实际从源码编译 |
| U55C EmptyU55CConfig RTL生成 | PASS，16×16/70MHz，未进行物理实现 |
| FSA4X4Fp16Config Verilator 编译 | PASS，实际编译并链接 |
| seq_q=seq_kv=4 / 8 功能仿真 | 两者 PASS 完成，误差见下 |
| U55C 综合、布局布线、bitstream | 未运行；make bitstream命令已dry-run验证 |
| U55C 板测 | 未运行；本轮没有U55C板卡验收结果 |

仿真 FSA 与 Torch：MAE=9.6587464e-05，MSE=1.6099552e-08，
MaxErr=0.00030440092，RelErr=0.00019886618。
PyEasyFloat 与 Torch 打印指标相同；这不等于逐元素 bit-exact 证明。
FSA execTime=353 cycles，mxBubble=206，mxActive=71，dmaActive=22，rawInst=32；
整个 Verilator testbench 在4587周期结束。不要把testbench周期当FSA执行周期。
同一4×4仿真器追加seq8分块回归：MAE=9.252038e-05，MSE=1.30638265e-08，
MaxErr=0.00027418137，RelErr=0.00021823279；PyEasyFloat打印指标相同。
execTime=1068，mxBubble=780，mxActive=232，dmaActive=68，rawInst=97；testbench=11737周期。
本次仅4×4功能回归，不作为16×16板卡性能数据。

## 环境与恢复

- Linux x86_64；JDK OpenJDK 20.0.2-internal；sbt 1.8.2（源码锁定）。
- firtool 1.75.0；Verilator 5.022（Conda发行）；最终C++编译和链接强制系统GCC/G++13.3.0。
- Python 3.13.14、uv 0.11.30、Torch 2.6.0；按上游uv.lock冻结安装。
- 先前硬件编译使用的Spike/FESVR库来自既有 `/home/zhangsi/riscv`；后续独立安装验证见文末。
- Scala/Maven下载缓存复制到独立目录，未改旧构建缓存；源码依赖从本地对象取得，
  之后实际仓库全部repack解除alternates，原始分支不依赖旧FSA对象目录。
- `XDG_RUNTIME_DIR` 指定可写独立目录，sbt需要本地socket；受限sandbox下需允许socket。

发现并修复的是复现工具/命令问题，不是原始RTL：

1. Verilator公共文件列表引用Radiance/Vortex/fpnew，即使本配置不实例化它也必须获取；
   `prepare-original-deps.py`已补齐这两个父gitlink锁定的嵌套依赖。
2. Conda Verilator硬编码CXX和LINK，单独export CXX不足以覆盖；原命令会与系统Spike库
   出现 `__isoc23_*@GLIBC_2.38` 链接失败。README同时传入CC/CXX/LINK/AR。
   失败的Conda生成目录已移至独立诊断目录保留；最终对象由系统G++重新编译。
3. 原README中的bitstream路径漏掉`obj/`，已按Makefile纠正。
4. 原Python配置缺失会默认回退，README在仿真/板测前显式检查配置文件存在。
5. 原Python默认输出/tmp，README改为每次独立结果目录，避免并行实验覆盖。

上游 `build-setup.sh` 完整Conda/工具链安装未执行，README将它明确列为替代方式。
主路径的工具环境、依赖、frozen Python安装、编译及仿真已实际执行；网络全新安装
和U55C完整物理实现仍须后续验收，不能称为全流程板卡复现已通过。

## 留存证据

本地源码 `/tmp/ict-original-work`；日志 `/tmp/ict-original-validation`。
下表为本次日志SHA256；日志未作为大文件加入仓库，交付时应连同该目录归档。

| 文件 | SHA256 |
|---|---|
| `dependencies-attempt03.log` | `de330973e4ca3b618881a627adf8a0ecbedf1e1a7a90efd06c8ca11ee2d973e3` |
| `assembly-attempt04.log` | `1f9e4530e6e5dc5fc4b57c6cd9858e82bcc1301609677bd46d1dc69b259bf169` |
| `elaborate-u55c.log` | `0051f1d4f907a0046b8d487fdf0d1a0a70791c6fb22ebaae1a9b21fe5afc90e7` |
| `sim-build-attempt04.log` | `3e8ca30c3237525db0ba1aa58a333387a868e9207a485fe230783c317b2adc54` |
| `sim-seq4-attempt02.log` | `e75afc1e969580bddfce86fc0e28f95de8e9564f18adedcec08ed8ddb93f1fef` |
| `uv-easyfloat.log` | `a1673e153034267fc58cf4756c0c6ac81a5ac08a711b4b97d46e91642a127fc2` |
| `uv-fsa.log` | `a541b6882c5286f9e1f2eaafaa8f97e5ccb480cff54a62537978116e85e78c1d` |
| `sim-seq8-attempt01.log` | `dcb74fb9bee21dc02f1c7e4db5be073a21ce35109234a4ff4d2f1e373f3ed091` |


## Spike/FESVR 首次安装文档补充

README新增固定 `76858cc3aa178446584eae52f82e0a933e71f8db` 的独立工具构建步骤。
本轮只检查该提交的 `configure --help`、`Makefile.in`、`fesvr/fesvr.mk.in` 和
`riscv/riscv.mk.in`：支持 `--prefix` 及三个禁用 Boost 选项，提供静态 FESVR 和动态
RISC-V 库安装规则。configure帮助输出在 `spike-configure-help.log`。
该文档补充提交时尚未执行另一套工具链编译；随后实际安装结果见下一节。已有仿真验收仍使用原记录中的既有库。


## Spike/FESVR 独立安装实际验收（2026-11-02）

在 `/tmp/ict-spike-baseline-validation` 新建 `source`、`build` 和 `install`，
从只读本地Git对象独立clone固定 `76858cc3aa178446584eae52f82e0a933e71f8db`。
没有共享alternates，没有修改 `/home/zhangsi/riscv`；源码工作树保持干净。
CC=/usr/bin/gcc、CXX=/usr/bin/g++，均13.3.0；dtc版本为DTC 1.7.0。

| 操作 | 结果 |
|---|---|
| configure，独立prefix，三个with-boost选项均no | exit 0 |
| make -j4 | exit 0 |
| make libfesvr.a | exit 0 |
| make install，用户可写prefix | exit 0 |
| 安装libfesvr.a到prefix/lib | exit 0 |
| 双库及fesvr/htif.h存在且非空 | 通过 |
| 新安装spike --help | exit 0，1.1.1-dev |
| 新安装libriscv.so动态依赖解析 | 无not found |

先前本分支Scala/RTL/Verilator验收仍使用旧安装。本节只验证独立工具构建安装流程，
没有据此宣称硬件又用新库重建了一遍，也没有执行完整RISC-V交叉编译器构建。
公网源码下载没有重新执行；本地对象只是源码获取加速，编译和安装产物均本次重新生成。

| 新安装产物 | 字节数 | SHA256 |
|---|---:|---|
| `lib/libfesvr.a` | 6651522 | `6bdc33518a3b873a0d546a8b64857df0f83519bc86c500ca39e29ed33781d4dd` |
| `lib/libriscv.so` | 180559904 | `cf57970c6b9228ea6299fd38359c79c754948939c13c6a2f098cf4036dd59472` |
| `include/fesvr/htif.h` | 5965 | `5aec4e8516d1ccc72941af7a728556027a9da88d199978c9434e0996e55be608` |

本地完整记录：`/tmp/ict-spike-baseline-validation/validation.json`。日志哈希：

| 日志 | SHA256 |
|---|---|
| `configure.log` | `874c36a26ee4cef9355462e09c64cc0933cce2c722d3c10592a447b53a17fb02` |
| `make.log` | `b3a720dc636a697a6da1048ed7a848e741272c86c66a5046bd857ff1c3b210d0` |
| `libfesvr-confirm.log` | `292facd041a91cdeec3249613fd0e7250cc514861c1cb3230865295832c8495f` |
| `install-confirm.log` | `691ca15ab3cc12c515c33476cdb1bdcb0105500c6244a18bdecf0c948dee7744` |
| `archive-install-confirm.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `spike-help.log` | `c5573d08c9380e48fe3fca1042a02857ba6e265e996bd31c0953fc0f644dc98c` |
| `validation.json` | `4bc00b272fe11566cdc37fef54e2fef9ddfbb3822015faf60125fd7e0e61595b` |
