# original-u280 基线审查

本分支基于 ICT-FSA `3d1714de26aeaad172461bd96e6c8fc26e63109a`。新增内容只涉及复现说明/工具；硬件源码保留历史 U280 初始移植。

已检查来源清单：仅 `u280/fpga-shells-u280.patch` 与 `u280/fsa-u280.patch`，无 NM37 或 P0/P1/P2/P3 补丁。FSA 补丁不修改 Scala，easyfloat 无补丁；后续 NM37 算术、流水及复位优化不属于本分支。

独立验证进行中，完成情况以随后记录及外部构建 receipt 为准。当前不得据此宣称 U280 布局布线或板测通过。
