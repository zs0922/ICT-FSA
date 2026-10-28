# 失败恢复与已有产物

统一入口的阶段记录在 `BUILD_OUT.ict-state`，后端日志/产物在 `BUILD_OUT`。先运行：

```bash
python3 scripts/fsa.py status --out "$BUILD_OUT"
rg -n 'ERROR|Error|Exception|failed|bad constant|OutOfMemory' "$BUILD_OUT.ict-state" "$BUILD_OUT/logs"
```

状态分为未开始、running、completed、failed_or_interrupted。终止或断电可能留下 running；不能把它当成功，也不能通过手工编辑为 completed 恢复。源验证的 PASS 只证明源输入，不能替代 assembly/仿真/布局布线成功。

- **参数不合法**：读取错误提示，检查 profile 中支持阵列列表。序列1024使用 `sim-extra --array-size 16 --seq 1024`。预检失败不会启动编译。
- **前置阶段缺失**：按提示先完成 build/verify/对应全部 sim/elaborate。勿补造 passed.json。
- **下载失败**：保留下载缓存，修复网络，重新执行 deps；有已有修改时先识别其来源，脚本不执行强制reset。需要独立重试时从相同 commit clone 新源码，缓存继续共用。
- **assembly 失败但存在 JAR**：JAR 可能不完整或来自旧输入；没有对应成功记录时不会将其晋升为可复用产物。检查 JDK/sbt/内存错误并修好环境；保留失败目录，在新的独立源码和 BUILD_OUT 重新 build。已完成的旧构建保留用于诊断。
- **已完成阶段再次执行**：明确报“已完成”，没有重复跑，也不会覆盖日志。继续下一阶段即可。
- **implementation 已路由但 CDC 末端审查失败**：保留 DCP 和所有报告，修复/审查真实问题。实验导出可以从该 DCP 独立执行时序和 DRC 检查，仍明确不宣称 CDC 验收通过。
- **设备 Permission denied**：使用与源码环境匹配的绝对 `FSA_PYTHON`，并按 README 的 sudo 命令运行，或由管理员配置 XDMA 用户组权限。不要递归 chmod 整个 `/dev`。
- **板测 timeout/队列不空**：保存该结果目录，确认没有并发访问，按板卡流程重新烧录/复位并产生新 receipt，再用新 attempt 运行。

这轮迁移不提供“任意失败阶段自动续写”功能。失败环境修复后采用新输出进行完整重试，下载缓存继续复用；已完成阶段结果保留且不会被破坏。以后若添加产物重用，必须先校验对应源码、工具、输出 hash 和完成证据，不能只因文件存在就略过编译。


## A110/APB55 已完成布线，但 CDC 审查缺失

如果日志已经完成 `route_design`、写出 `post_route.dcp` 并生成报告，最后错误为缺少本次 `cdc-review.json`，先保留 `physical.failed.json` 和 `*.ict-state`。这不是重新编译或重跑 P&R 的理由；也不能直接把 failure 改成 passed。下面只适用于 A110/APB55，使用实际执行该构建的源码目录：

```bash
export REAUDIT_OUT="$WORK/reaudit-$COMMIT-attempt01"
python3 "$SRC/scripts/nm37-a110/reaudit.py" run \
  --source "$SRC" --build "$BUILD_OUT" --out "$REAUDIT_OUT"
```

该命令重新打开已有 routed DCP，在独立目录生成新的时序、CDC、HBM 和复位复制报告，绑定原源码、生成器、IP、DCP 和原报告哈希。它不修改设计、不重新布局布线、不写原构建目录，也不是自动 CDC 放行。执行需要相同 Vivado 环境，输出目录必须为新目录。

之后可用独立 acceptance attempt 执行实际检查；缺失或不完整审查会写入本次 acceptance 的失败记录，并给出待审查项：

```bash
python3 "$SRC/scripts/nm37-a110/reaudit.py" accept \
  --out "$REAUDIT_OUT" --attempt check01
```

`cdc-review.required.json` 是待审查模板，不是成功证据。检查每条实际发现的源/目的网表、同步结构、时钟和复位关系后，才能形成与本次 DCP/CDC 报告绑定、包含证据哈希的 `cdc-review.json`；不允许复制旧 DCP 的结论或把真实缺陷填成工具误报。审查补齐后用新的 `--attempt check02`，保留 check01 失败记录。无法证明的条目保留待处理，不能为通过门槛扩大 false-path。

即使该独立复审通过，它仍保留 `board_signoff=false`；不代表实板测试或所有异步故障场景已验证。2026-10-28 的实际执行与边界见[复现记录](../../reports/ICT_FSA_REPRODUCTION_20261028.md)。如目的是实验板测，根 README 的独立 `export` 入口仍会重新检查时序和 DRC，并明确保留 CDC 未签核状态。
