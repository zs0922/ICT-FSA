# 三个原始基线：来源与独立复现记录

本轮目的为保存上游原貌、U280 初始移植、NM37-CIV 初始移植三个起点。不引入新性能优化，不推送远端，不修改既有分支和构建。集成文档位于新增 `codex/original-baselines` 分支；现有默认分支的工作树不切换。

## 上游与来源

真实 FSA/U55C 集成起点为 VCA-EPFL/chipyard-fsa `54671054fedcd2c1f65bb2dd6939abdaf8071814`，该提交合并 PR #22。Berkeley Chipyard 是框架上游，不能用其当前 HEAD 代替这个 FSA 起点。

`original` 导入上述历史与全部原始 gitlink，仅新增复现文档和两个辅助脚本。U280/NM37 从已有 ICT-FSA 物化提交建立，计算核心、板级源码与依赖锁保持来源一致；最终U280 profile仅补充已知STA周期元数据，审计工具修复见下文。父任务独立核对 Git tree ID；原始分支又逐项核验来源报告中的日志 SHA256。

证据：

- [原始分支变更范围与日志哈希核对](original-baselines-20261102/original-source-and-logs.json)
- [U280/NM37 构建源树核对](original-baselines-20261102/source-tree-audit.json)及[最终交付源树复核](original-baselines-20261102/final-source-audit.json)
- [生成器、仿真和板级展开阶段记录](original-baselines-20261102/functional-validation.json)

U280 源清单核验 356 项、NM37 358 项，无差异。NM37 相对初始 U280 的 `generators/fsa/src` 与 `generators/easyfloat` 没有差异。两者均为板上16×16、单内存端口、目标70MHz，并保留历史 ILA 调试逻辑；A70-P3 不是它们的别名。

## 已建立的本地分支与实际构建来源

| 分支 | 当前交付提交 | 实际硬件构建来源 |
|---|---|---|
| `original` | `474e92dc018df7a7a818aa329db967ebb829108c` | 上游 `54671054`，仅添加文档/辅助脚本 |
| `original-u280` | `ab28e170feb2c29d347dd476f45fd29456cf0d7b` | `c9b39717`；审计/导出工具 `b6fb9591` |
| `original-nm37-civ` | `87cd26500fc88f7051771e3cb1670001375c6b1f` | `eb16cafb`，本次独立 build-attempt02 |

U280/NM37 已完成独立完整布局布线，实际导出实验 bitstream。U55C 本轮没有运行完整物理实现。U280 初次 implement 在写出 DCP 后因周期身份检查误拒而标为失败；原记录保留，修复工具独立重新审计 DCP 并成功导出，不把旧 receipt 改为成功。

| 最终 routed 指标 | original-u280 | original-nm37-civ |
|---|---:|---:|
| 名义 DUT MHz | 70 | 70 |
| STA 显示周期 ns | 14.284 | 14.286 |
| 全局/DUT WNS ns | +0.003 | +0.001 |
| 全局/DUT WHS ns | +0.010 | +0.010 |
| TNS / THS / TPWS | 0 / 0 / 0 | 0 / 0 / 0 |
| WPWS ns | 0 | 0 |
| Bus-skew 检查 | 18项全部MET，最小+2.884ns | 18项全部MET，最小+2.389ns |
| LUT | 381056（29.23%） | 380891（29.22%） |
| FF | 72510（2.78%） | 72500（2.78%） |
| DSP | 320（3.55%） | 320（3.55%） |
| BRAM tiles | 81.5（4.04%） | 81.5（4.04%） |
| DRC Error / Critical Warning | 0 / 0 | 0 / 0 |
| 实验 bitstream | 已导出、哈希复核通过 | 已导出、哈希复核通过 |

时序裕量仅1～3ps，不代表额外提频余量。资源为整板总量，包含历史ILA，不是纯FSA。

U280 最差DUT setup：`mxControl/fsm_list_1/accumTimer_reg[0]` → `accumulator/accUnit_1/reciprocal/reg_r_exp_reg[8]`，60级，数据延迟13.830ns（逻辑4.731ns，布线9.099ns）。NM37：同类计时器 → `accRAM_sram/.../RAMG_D1/I`，53级，13.918ns（逻辑5.462ns，布线8.456ns）。具体完整层级及延迟以各分支报告为准，不能仅按起点命名解释为纯控制路径。

导出身份记录：[U280](original-baselines-20261102/u280-export.json)、[NM37](original-baselines-20261102/nm37-export.json)。主任务独立重新计算两个bit、配置及DCP哈希，均与记录一致。实际文件分别位于 `/tmp/ict-u280-run/bits-attempt01/U280_EXPERIMENTAL.bit` 和 `/tmp/ict-nm37-validation/bits-attempt01/NM37_EXPERIMENTAL.bit`。

CDC、exceptions及HBM未约束端点只归档、未逐项关闭；实验导出不等于正式CDC或实板验收。NM37 CDC仍有30 Critical/171 Warning，check_timing有30个HBM端点及1个缺input delay输入。

## 功能验证

两个移植分支各自恢复172个固定依赖；下载缓存独立复制，不复用旧JAR/RTL/仿真器/DCP。工具检查通过，Scala生成器真实编译、4×4固定仿真和16×16板级RTL展开通过。U280与NM37的seq4/seq8使用相同输入，输出哈希相同，且各自与PyEasyFloat逐位一致。

original恢复原始子模块并实际编译，完成U55C板级RTL展开和4×4 Verilator仿真。seq4/seq8的FSA与PyEasyFloat对Torch打印指标相同；这是上游main.py的数值对照，不宣称逐元素bit-exact。seq4 RelErr=0.00019886618，seq8 RelErr=0.00021823279。未运行U55C完整布局布线或板测。

三个分支本轮都没有实板验收，不能把仿真数据填为板卡性能数据。原始依赖从本地已锁定对象恢复，本轮没有逐一验证所有第三方公网服务的新机器下载；所有活动Git仓库解除对象alternates，分支不依赖旧仓库对象存续。

## 发现并修复的复现问题

1. 旧通用README混入后续优化版本命令。U280/NM37改为本分支独立执行清单，旧说明归档；初始NM37和U280均不误用尚不支持该profile的统一板测入口。
2. 原始Verilator文件列表仍引用Radiance/Vortex/fpnew，尽管FSA没有实例化该模块。原始依赖准备脚本补齐父gitlink锁定的嵌套依赖。
3. Conda Verilator内置编译器和链接器覆盖环境变量，不能链接系统Spike库。原始README在make命令行明确传入CC/CXX/LINK/AR，实际以系统G++13.3重编译、链接成功。
4. 双Python环境需要分别frozen sync。原始README还检查生成配置存在，防止Python默认配置回退，结果使用独立目录。
5. U280实际路由后发现名义70MHz的周期校验不匹配历史STA约束：输入300MHz写为3.333ns，经原始MMCM参数传播为约14.284ns，而不是理想14.285714ns。MMCM本身按300MHz输入对应70MHz；修复仅针对已知STA周期检查，不改变RTL、IP、XDC或非负slack要求。原失败receipt/DCP保留，独立恢复审计的工具提交与硬件构建提交分别绑定。
6. 执行沙箱禁止sbt创建Unix socket，U280/NM37第一次attempt未进入编译。保留失败日志，获准使用正常本机执行环境后新attempt成功；这是执行环境限制，没有因此修改RTL。

入口测试：U280最初25项、修复后27项通过，NM37 25项通过，集成分支30项通过。测试不能替代实际布局布线。

等待物理实现期间，另在 `/tmp/ict-spike-baseline-validation` 实际执行固定 `76858cc3` 的 Spike/FESVR 从源码 configure、make -j4、安装；系统 GCC/G++13.3、dtc1.7，三个安装产物与运行检查均通过，旧RISCV安装不变。见 [独立工具安装证据](original-baselines-20261102/spike-install-validation.json)。此前硬件构建使用已有RISCV安装，没有使用这个新安装重新构建；不能把独立工具验证说成整套硬件冷启动重跑。

## 保存与使用

新入口见 [基线README](../docs/baselines/README.md)。各分支详细记录另汇总为 [U280](original-baselines-20261102/u280-validation.json)、[NM37](original-baselines-20261102/nm37-validation.json)。

三个分支源码和本轮输出都在独立目录；旧FSA和既有ICT-FSA构建没有被清理、重置或覆盖。未创建验收tag，未push。构建源码commit与随后仅补记录的文档commit分别记载，不将文档提交自动当成一次新构建。

完整本机原始记录位于 `/tmp/ict-original-validation`、`/tmp/ict-u280-run`、`/tmp/ict-nm37-validation`。其中失败attempt与新成功attempt并存。长期交付应归档日志和哈希；下载缓存和生成产物不进入源码Git。
