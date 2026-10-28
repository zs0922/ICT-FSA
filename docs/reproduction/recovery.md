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
