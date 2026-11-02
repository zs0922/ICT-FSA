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
| seq_q=seq_kv=4 功能仿真 | PASS 完成，误差见下 |
| U55C 综合、布局布线、bitstream | 未运行；make bitstream命令已dry-run验证 |
| U55C 板测 | 未运行；本轮没有U55C板卡验收结果 |

仿真 FSA 与 Torch：MAE=9.6587464e-05，MSE=1.6099552e-08，
MaxErr=0.00030440092，RelErr=0.00019886618。
PyEasyFloat 与 Torch 打印指标相同；这不等于逐元素 bit-exact 证明。
FSA execTime=353 cycles，mxBubble=206，mxActive=71，dmaActive=22，rawInst=32；
整个 Verilator testbench 在4587周期结束。不要把testbench周期当FSA执行周期。
本次仅4×4功能回归，不作为16×16板卡性能数据。

## 环境与恢复

- Linux x86_64；JDK OpenJDK 20.0.2-internal；sbt 1.8.2（源码锁定）。
- firtool 1.75.0；Verilator 5.022（Conda发行）；最终C++编译和链接强制系统GCC/G++13.3.0。
- Python 3.13.14、uv 0.11.30、Torch 2.6.0；按上游uv.lock冻结安装。
- Spike/FESVR库来自既有 `/home/zhangsi/riscv`；未从零重建工具链。
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
