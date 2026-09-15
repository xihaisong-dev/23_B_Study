# 本地知识库证据矩阵

- 状态：`PASS`（仅指本地知识库检索覆盖）；上游 `rules-problem` 仍 `FAIL`。
- 检索时间：2026-09-14 23:53 +08:00。
- 范围：只检索 `knowledge_base/`，未开展网络检索。三份可检索原文均阅读机械提取稿并回查 PDF；扫描版 Cooley–Tukey 只作背景，不计入三篇可检索文献门槛。
- 语义基准：D-005，固定 `beta=1`；单位化 DFT；`P_q`、`L`、`K` 和 q5 字典序均按 `00_admin/semantic_contract.json`。

## 1. 文献与可迁移边界

| KBREF | 可抽象结论 | 可用于 | 不可迁移/风险 |
| --- | --- | --- | --- |
| `KB-BFLY-2019::knowledge_base/papers/dao_butterfly_2019.txt#L166-L223`（PDF pp.3–4） | radix-2 DFT 可写成蝶形因子链与比特反转排列 | q1 结构基线；q3/q4 初始化 | 连续复系数、特定拓扑；不直接给本题固定 `beta=1` 的 `L` 或最优性 |
| `KB-BFLY-2019::knowledge_base/papers/dao_butterfly_2019.txt#L240-L372`（PDF pp.5–7） | Butterfly 参数化与可学习排列；参数族包含 FFT | 支持图/排列挑战者 | 固定 Butterfly 类可能排除更优行二稀疏图 |
| `KB-BFLY-2019::knowledge_base/papers/dao_butterfly_2019.txt#L419-L454`（PDF p.8） | 同总稀疏预算比较，明确 RMSE、优化器、调参与停止规则 | q1–q5 公平验证设计 | 论文稀疏预算不是 `C=qL`，论文阈值和结果不能移植 |
| `KB-MLSA-2016::knowledge_base/papers/le_magoarou_multilayer_sparse_2016.txt#L136-L152`（PDF p.3） | 用 Frobenius 目标拟合多层稀疏乘积 | q1–q5 共用目标框架 | 文中约束集为连续实值框架 |
| `KB-MLSA-2016::knowledge_base/papers/le_magoarou_multilayer_sparse_2016.txt#L268-L365`（PDF pp.4–5） | PALM/投影交替更新，尺度歧义通过归一化因子和标量处理，收敛只到驻点 | 连续松弛、块坐标更新 | D-005 固定 `beta=1`，不可沿用文中自由尺度；离散投影后需独立复算 |
| `KB-MLSA-2016::knowledge_base/papers/le_magoarou_multilayer_sparse_2016.txt#L378-L467`（PDF p.5） | 分层二因子初始化后全局润色可缓解直接多因子局部点 | q1–q5 层次挑战者 | 是启发式初始化，不是全局最优证书 |
| `KB-MLSA-2016::knowledge_base/papers/le_magoarou_multilayer_sparse_2016.txt#L927-L952` | 非凸问题存在坏局部极小，层次方案只是经验上较好 | 多种子、失败留档、消融 | 不能从论文实验推出本题最优值 |
| `KB-SP2-2020::knowledge_base/papers/muller_sparse_power_of_2_2020.txt#L65-L102`（PDF p.2） | 稀疏有符号二次幂因子与递归稀疏恢复 | q2/q3/q5 离散因子挑战者 | 实数/矩形设定；本题复数实虚部分别投影至 `P_q` |
| `KB-SP2-2020::knowledge_base/papers/muller_sparse_power_of_2_2020.txt#L94-L125`（PDF p.2） | 该优化 NP-hard，算法为贪心近似且作者不声称最优 | `best_found` 口径、失败规则 | 实验为随机高斯矩阵，数值不能用于 DFT/Kronecker 目标 |

## 2. 五问覆盖

| 问题 | Domain 查询结论 | Method 查询结论 | Validation 查询结论 | 证据覆盖与缺口 |
| --- | --- | --- | --- | --- |
| q1 | DFT 蝶形与比特反转提供合法结构族 | 连续行二投影 + 层次初始化 + 结构重连 | 同预算/同种子；独立 RMSE、约束与 `L` 复算 | 三篇覆盖。固定 `beta=1` 后的缩放会改变 `L`，必须从头计数 |
| q2 | 有符号二次幂因子对应有限系数域 | 单因子量化基线；递归贪心；连续松弛后 P3 离散润色 | NP-hard，仅称 `best_found`；所有 P3 元素逐项验合法 | 三篇覆盖。没有针对单位化 DFT、复数 P3 的现成结果 |
| q3 | 行二稀疏与 P3 是组合离散约束 | Butterfly 初值、交替离散更新、支持重连 | 多种子并保留超时/约束失败；做支持/系数消融 | 三篇覆盖。没有全局最优算法或 q3 数值证据 |
| q4 | 目标是 `F4⊗F8`，不是 `F32` | 分量结构初始化与通用多层稀疏搜索对照 | 直接生成目标并独立重构；不可借用随机矩阵结果 | 三篇覆盖但无论文直接处理该目标；方法属于有证据约束下的原创组合 |
| q5 | 离散系数、行二支撑与实现代价存在折衷 | 对 `(q,K)` 网格执行阈值约束和 `(C,K,RMSE)` 字典序 | 相同预算、多种子、L0–L4；无可行解时不得指定赢家 | 三篇覆盖。`q=1/K=5/RMSE≈0.0905` 等 V6 数值仍无代码、因子或日志，不能继承 |

## 3. 采用与拒绝

采用：Butterfly 结构基线、层次初始化、投影/块坐标框架、有限系数递归贪心，以及同预算/多种子/失败留档原则。

拒绝直接继承：三篇论文的任何 RMSE、复杂度或最优性数值；用户 V4–V6 的数值；自由尺度标量；随机高斯矩阵上的性能；与 D-005 不同的复杂度定义。

完整查询字符串、KBREF、适用对象与风险见 `02_retrieval/retrieval_manifest.json`。
