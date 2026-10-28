# A110-APB55 来源与本轮状态

本阶段硬件源码来自 export.json 所列旧提交和实际 shell 输入，硬件字节一致性见 adaptation.json。源码迁移不能代替新构建验收；本轮尚未重新编译、仿真、证明、布局布线或板测。

FSA/easyfloat/fpga-shells 作为普通目录维护；原有许可/版权保留，没有独立 LICENSE 的核心目录不推断新的授权。其他依赖固定 commit 见 root-gitlinks.json。

host-mmio.patch 单独记录主机 MMIO 映射缓存优化，应与硬件提频分开统计。旧仓未重新烧录的 A100/A110 日志不是这些硬件版本的板测通过证据。
