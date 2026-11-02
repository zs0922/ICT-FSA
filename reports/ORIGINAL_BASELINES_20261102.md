# 三个原始基线：来源与独立复现记录

本轮目的为保存上游原貌、U280 初始移植、NM37-CIV 初始移植三个起点。不引入新性能优化，不推送远端，不修改既有分支和构建。集成文档位于新增 `codex/original-baselines` 分支；现有默认分支的工作树不切换。

## 上游与来源

真实 FSA/U55C 集成起点为 VCA-EPFL/chipyard-fsa `54671054fedcd2c1f65bb2dd6939abdaf8071814`，该提交合并 PR #22。Berkeley Chipyard 是框架上游，不能用其当前 HEAD 代替这个 FSA 起点。

`original` 导入上述历史与全部原始 gitlink，仅新增复现文档和两个辅助脚本。U280/NM37 从已有 ICT-FSA 物化提交建立，所有计算核心、板级源码、依赖锁、配置及构建源树仍与对应来源一致。父任务独立核对 Git tree ID；原始分支又逐项核验来源报告中的日志 SHA256。

证据：

- [原始分支变更范围与日志哈希核对](original-baselines-20261102/original-source-and-logs.json)
- [U280/NM37 源树一致性核对](original-baselines-20261102/source-tree-audit.json)
- [生成器、仿真和板级展开阶段记录](original-baselines-20261102/functional-validation.json)

U280 源清单核验 356 项、NM37 358 项，无差异。NM37 相对初始 U280 的 `generators/fsa/src` 与 `generators/easyfloat` 没有差异。两者均为板上16×16、单内存端口、目标70MHz，并保留历史 ILA 调试逻辑；A70-P3 不是它们的别名。

## 已建立的本地分支与物理验证进度

| 分支 | 当前交付提交 | 实际硬件构建来源 |
|---|---|---|
| `original` | `98c0401a289e255ca00a7d5a7f70c47f223ab66b` | 上游 `54671054`，仅添加文档/辅助脚本 |
| `original-u280` | `c9b39717ec6bd5fc5ac98e998b7f9d6c95fef05f` | 同一提交，本次独立 build-attempt02 |
| `original-nm37-civ` | `eb16cafbc0ce4710e6c2e4f58a53f39c4e348a81` | 同一提交，本次独立 build-attempt02 |

本记录初次提交时，U280/NM37完整Vivado实现仍在运行，不能记为70MHz通过；后续物理终态会追加到本记录。U55C本轮没有运行完整物理实现。

## 功能验证

两个移植分支各自恢复172个固定依赖；下载缓存独立复制，不复用旧JAR/RTL/仿真器/DCP。工具检查通过，Scala生成器真实编译、4×4固定仿真和16×16板级RTL展开通过。U280与NM37的seq4/seq8使用相同输入，输出哈希相同，且各自与PyEasyFloat逐位一致。

original恢复原始子模块并实际编译，完成U55C板级RTL展开和4×4 Verilator仿真。seq4/seq8的FSA与PyEasyFloat对Torch打印指标相同；这是上游main.py的数值对照，不宣称逐元素bit-exact。seq4 RelErr=0.00019886618，seq8 RelErr=0.00021823279。未运行U55C完整布局布线或板测。

三个分支本轮都没有实板验收，不能把仿真数据填为板卡性能数据。原始依赖从本地已锁定对象恢复，本轮没有逐一验证所有第三方公网服务的新机器下载；所有活动Git仓库解除对象alternates，分支不依赖旧仓库对象存续。

## 发现并修复的复现问题

1. 旧通用README混入后续优化版本命令。U280/NM37改为本分支独立执行清单，旧说明归档；初始NM37和U280均不误用尚不支持该profile的统一板测入口。
2. 原始Verilator文件列表仍引用Radiance/Vortex/fpnew，尽管FSA没有实例化该模块。原始依赖准备脚本补齐父gitlink锁定的嵌套依赖。
3. Conda Verilator内置编译器和链接器覆盖环境变量，不能链接系统Spike库。原始README在make命令行明确传入CC/CXX/LINK/AR，实际以系统G++13.3重编译、链接成功。
4. 双Python环境需要分别frozen sync。原始README还检查生成配置存在，防止Python默认配置回退，结果使用独立目录。
5. 执行沙箱禁止sbt创建Unix socket，U280/NM37第一次attempt未进入编译。保留失败日志，获准使用正常本机执行环境后新attempt成功；这是执行环境限制，没有因此修改RTL。

入口测试：U280/NM37各25项通过，集成分支30项通过。测试不能替代实际布局布线。

## 保存与使用

新入口见 [基线README](../docs/baselines/README.md)。三个分支源码和本轮输出都在独立目录；旧FSA和既有ICT-FSA构建没有被清理、重置或覆盖。未创建验收tag，未push。构建源码commit与随后仅补记录的文档commit分别记载，不将文档提交自动当成一次新构建。

完整本机原始记录位于 `/tmp/ict-original-validation`、`/tmp/ict-u280-run`、`/tmp/ict-nm37-validation`。其中失败attempt与新成功attempt并存。长期交付应归档日志和哈希；下载缓存和生成产物不进入源码Git。
