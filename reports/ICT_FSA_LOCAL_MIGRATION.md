# ICT-FSA 本地迁移及集成验收记录

日期：2026-10-28。范围：独立源码整理、工具集成、本地提交与迁移正确性检查。**尚未完成新仓五阶段的全流程硬件验收；未创建远程、未 push、未创建验收标签。**

本文保留迁移阶段当时的验收范围。随后 A70-P3/A100/A110 的独立完整重建和修复另见[2026-10-28 复现记录](ICT_FSA_REPRODUCTION_20261028.md)；下文“未执行/待验证”是迁移提交时的历史状态。

## 1. 当前交付及版本映射

本地仓库：`/home/zhangsi/tmp/ICT-FSA`。主整理分支：`codex/ict-fsa-integration`。这是独立 Git 对象库，无 alternates，也不依赖旧 FSA 的 `.git/objects`。各阶段可独立 checkout；阶段分支用于定位候选，不代表已经通过实板验收。

| 阶段 | ICT-FSA commit | 本地分支 | 旧 FSA 来源 |
|---|---|---|---|
| U280 | `3d1714de26aeaad172461bd96e6c8fc26e63109a` | `codex/u280-port` | `50344530d2fa` |
| NM37 | `00e021c635cd31d013cf00fd24cba687dc0b4be5` | `codex/nm37-port` | `57344208e4b8` |
| A70-P3 | `8cc6b42536334892b88f6214f39d3afe5daa2504` | `codex/nm37-a70-p3` | `45d859c1c1bd` |
| host-mmio | `2cf6d2da1cbd1fc143f7218d58bc588babc3eb17` | `（独立主机软件提交）` | `0a3a2656df66` |
| A100 | `f8650f9576bf681bfae38a2ab40718fc2ace4262` | `codex/nm37-a100` | `0a3a2656df66` |
| A110-APB55 | `b595900e91bda33925f059ff585771ae5ecddfcd` | `codex/nm37-a110-apb55` | `25673838e66d` |

完整机器可读映射：[migration-map.json](../docs/history/migration-map.json)。每阶段的补丁顺序、来源 hash、原 README 和输入指纹在 `docs/history/<stage>/`。末尾文档验收提交位于 A110 之上，硬件里程碑分支不会随报告更新而移动。**操作以交付主分支最新 README/环境说明为准**：固定里程碑中的工具接口相同，但当时 README 尚无本轮补充的 EasyFloat 独立环境预热和 sbt 离线缓存说明。源码 checkout 后仍使用交付手册的步骤；无需另一个工具仓。

A70-P3 已把历史 P0/P1、NM37、P2/P3 补丁按实际成功构建使用的顺序展开为源码；不再依赖 make 在编译时临时打补丁。A100/A110 对照既有输入锁导出，保留原实现。三个目录 `generators/fsa`、`generators/easyfloat`、`fpga/fpga-shells` 均由主仓直接跟踪，保留上游许可证和来源。其余 54 个根级 gitlink 仍锁定；本次 A110 所需递归依赖 172 个均已在独立验证目录恢复。

`2cf6d2da` 单独保留持久 MMIO 映射和批量队列写入改动，避免把主机下发优化混入 A100 的硬件改动解释。A70 原配主机软件和 A100/A110 原配软件不同，因此其运行时间差是系统差异，不能直接声称为纯提频收益。

## 2. 统一操作入口

每个阶段均包含 `scripts/fsa.py`、当前 profile、依赖锁、环境与恢复说明。按根 [README](../README.md) 执行：

`doctor → deps → Python 环境 → build → verify（适用阶段） → sim → elaborate → implement → export → program → test → summarize`。

- build 是 Scala/Chisel 生成器编译；sim 是 Verilator 功能测试；elaborate 是 RTL 展开；implement 才是 Vivado 完整布局布线。
- 参数、前置阶段、失败日志和成功状态都有明确提示；源码校验 PASS 不当成阶段完成。
- 新输出绑定源码 commit/profile；失败日志不覆盖，不伪造或手填成功标记。
- 实验 bit 导出绑定本次 DCP/config 指纹，并独立检查时序和 DRC；仍保留 CDC/约束待审查状态。
- program 真正执行 SRAM 配置并生成操作记录；test 要求匹配 bit/config/profile/烧录记录、BDF 和设备节点。操作记录不能替代硬件身份寄存器回读，重新烧录后旧记录不再代表当前镜像。
- 板测保存输入、指令、输出、两种参考结果、逐位检查与误差、计数器前后值；汇总按相同输入比较中位数和范围。bubble 接口计数不能简单等同 PE 空闲率。

## 3. 已完成的迁移验收

| 检查 | 结果 | 范围 |
|---|---|---|
| 五阶段独立 clone/checkout | 通过 | 均为独立对象，工作区测试前后干净 |
| 硬件/板级源码逐文件比对 | 通过 | U280 440、NM37 449、A70 455、A100 452、A110 454 个文件；字节、符号链接和 Git 可执行位一致 |
| gitlinks / 来源档案范围 | 通过 | 每阶段 54 个根 gitlink 正确，不混入未来阶段档案 |
| 统一工作流与依赖工具测试 | 通过 | 每阶段 25 项，共执行 125 项；不是 125 项不同硬件测试 |
| A110 审查工具测试 | 通过 | 44 项解析、约束及审查保护测试 |
| CLI / 依赖计划 / 构建命令检查 | 通过 | 所有阶段 build/elaborate/支持阵列的 sim dry-run；dry-run 不编译硬件 |
| A110 真实依赖恢复 | 通过 | 172 个固定依赖，从离线 bundle 恢复 |
| A110 真实生成器 assembly | 通过 | 新源码真实编译，产出新的 generator.jar；未复用旧 FSA JAR |
| A110 离线软件准备 | 通过 | seq16 输入、32 条指令及 PyEasyFloat 参考生成；不访问板卡 |
| A110 实际 Verilator 仿真 | 通过 | 4×4 阵列，seq4/8 与 PyEasyFloat 逐位一致 |
| 新仓完整 Vivado / bit / 实板测试 | 未执行 | 五阶段全部待后续验收，不能继承旧 DCP/板测的通过状态 |

逐项证据见 [evidence/local-migration-20261028](evidence/local-migration-20261028/)。其中绝对路径是本机当次执行位置，迁移到其他机器后不要求路径相同。源码交付 Git 不包含仿真器、JAR、DCP、bit 和下载缓存。

## 4. 本次真实构建与恢复记录

验证源码：`/tmp/ict-fsa-migration-20261028/validation/a110-source`，固定 `b595900e91bda33925f059ff585771ae5ecddfcd`。使用 JDK20.0.2、firtool1.75.0、Verilator5.022、GCC/G++13.3.0；读取既有工具安装，但构建和 Python 环境均在独立目录。

首次 assembly 因新源码内 sbt 缓存为空且当前网络受限而失败；保留 attempt01，复制已下载 sbt/Ivy/Coursier 缓存后，在 attempt02 真实编译成功。没有复制旧 FSA 的目标 JAR、RTL、仿真器或 DCP。

首次 sim4 在 Chisel 调用 EasyFloat Python 常量生成器时尝试联网解析 setuptools 而失败。FSA Python 环境与 EasyFloat 常量生成环境是两个独立环境；已用下载缓存离线安装后者并设置 `UV_OFFLINE=true`，用新输出 attempt03 重试。README 增补两处环境准备，失败产物均保留。

attempt03 的 4×4 Verilator 编译及 seq4/8 回归已通过，两组 `bitwise_equal=true`。生成器沿用同一独立源码在 attempt02 真正编译的产物，并经 prepare/输入指纹检查；未使用旧 FSA 构建结果。仿真器 SHA256：`2ad31855a3d4c1c6e04a3e8d5aebc1139f44ac8979d06b47991c0257107b16d4`。本次未补做 8×8/16×16、完整形式证明、板级 RTL/Vivado 或实板验收。

## 5. 后续验收顺序

1. 优先 A70-P3：独立 clone 固定提交，完整定向证明、4/16 阵列回归、RTL 和 Vivado 实现，审查 CDC/约束后导出本次 bit。
2. A100、A110/APB55 各自独立执行同样流程；补齐 8/16 阵列回归，A110 检查 APB55 复位和启动关系，PE 流水深度沿用原版本。
3. 每次换版本必须实际烧录并保存记录。在同一 NM37、同一 Q/K/V/seed 下跑 seq16/64/128/256/512/1024，每组 warmup1、repeat5；保存 bit/config/hash、频率、计数器及误差。
4. 汇总资源、真实时序、运行时间、bubble；分别分析原配软件系统比较与统一主机下发实现的硬件比较。旧的“只换环境变量、没重新烧录”的 A100/A110 数据只能用于主机软件诊断，不能作为对应硬件验收。
5. U280/初始 NM37 的完整重建另外验收；U280 当前统一板测器未验证设备识别，不能直接使用 NM37 的设备ID假设。
6. 五阶段按各自实际完成情况记录通过后再创建不可移动的验收标签；新 GitHub ICT-FSA 的创建及 push 留待后续指令。旧 FSA 与旧构建继续保留。

## 6. 旧工程保留与本地交付

本轮所有修改均在新工作区中完成。旧根仓及旧 integration-tools 工作区 HEAD 与 `git status --porcelain=v1` 与开始时一致；记录见 `preservation.json`。旧构建目录只作为来源核对及缓存读取，没有运行清理、重新构建或覆盖导出。

新仓源码 bundle 仅包含主仓及所有本地候选分支，不包含第三方子模块对象或下载缓存；接收端仍须执行 deps，或准备相同离线依赖 bundle。不要将旧主仓工作树直接覆盖到新仓，也不要将本地候选称为已验收发布。
