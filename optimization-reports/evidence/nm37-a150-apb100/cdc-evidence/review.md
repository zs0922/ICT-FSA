# A150/APB100 新增 CDC 审核（2026-11-02）

审核范围：仅 cdc-review.required.json 中两个 CDC-15 Warning；不覆盖其他路径或其他构建。
分类：equivalent_existing_structure，与已验收 A150/APB75 中计数器低 13 位同类。

ResetWrangler.scala 保持不变：slowTicks=ceil(100000 ns / slowPeriodNs)，slowBits=log2Ceil(slowTicks+1)。
APB75 是最慢输入，7500 拍、13 位；APB100 仍是最慢输入，10000 拍、14 位。
生成 RTL 比较表明：仅计数器宽度及终值变化；causes OR、递增/饱和使能、deglitch 寄存器和每域三级 ResetCatchAndSync 拓扑相同。
新增路径终点均是 bit13 的异步 CLR；不是跨域的多位业务数据，也不是新增 APB 启动握手路径。
comparison.json 保存原始报告哈希和全部基线 finding，精确差集只有这两项。

复位原因异步清零计数器并置位 deglitch。原因解除后在 APB 域计数到 10000，deglitch 寄存后送各时钟域三级复位释放链。
24 组实际生成 RTL 测试覆盖三种复位输入、八种释放偏移，以及计数中途再次复位。
检查复位有效期间与计数结束前不提前释放、三个域最终释放且不重新跳变。
这是数字协议验证，不模拟恢复/移除违例产生的模拟亚稳态；计数器直接异步复位是继承的既有结构，不能以计数延时宣称消除了所有亚稳态风险。
审核接受的是相对既有已审结构的新增位，不代表 CDC 报告清零或已完成板级签核。

布线后补充证据见 routed-structure.txt：检查全部 14 个 FDCE 的 C/CE/CLR 同源、deglitch 和复位输出链连接。
原始整板 setup/recovery、hold/removal、pulse-width 检查仍生效，无新增 false path、异步时钟组或时序豁免。
既有未使用 HBM AXI 端口及 prst_n 约束边界保持原验收范围。

审核器回归：原 AST 指纹测试生成于 Python 3.14；同版本运行 44 项全部通过。Python 3.10/系统 Python 的 AST 序列化不同，固定哈希测试失败，其余 43 项通过；此处没有修改测试期望或物理断言。复现该测试需 Python 3.14。物理验收使用构建环境自带 Python 3.10，实际报告检查与此测试序列化无关。

DCP 检查确认 14 个 FDCE 的 C/CE/CLR 同源；三域保留 sync_2→sync_1→sync_0 三级释放链。报告中这些寄存器的 ASYNC_REG 属性为空；不宣称存在该属性或工具已认证同步器 MTBF。本次分类基于既有结构等价性，未改变同步器结构/布局约束。
