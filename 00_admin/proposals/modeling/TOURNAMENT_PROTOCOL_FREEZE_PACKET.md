# 对擂协议冻结包（未被授权冻结）

## 状态

- 提案状态：`PROPOSED / BLOCKED`
- 依据：`02_retrieval/CANDIDATE_SPECS.md`（候选规格草案）、`03_model/ROW_BOUND_THEORY.md`（可证明结论）、`01_problem/PROBLEM_STATEMENT_AUDIT.md`（待裁决语义）
- 目标文件：`03_model/tournament_protocol.json`（当前为 `status = "BLOCKED"`、`proposal_status = "PROPOSED"`，含 5 个问题、每题 3 个候选）

## 为什么本轮没有冻结协议

`AGENTS.md` 要求"正式流程必须依次满足题面规则冻结、检索、协议冻结、候选对擂、结果冻结、论文冻结和最终验收"。当前：

| 前置门禁 | 状态 | 阻断原因 |
| --- | --- | --- |
| 题面规则冻结 | `BLOCKED` | practice 题面输入、模板和提交要求已 PASS；`00_admin/rules.json.ai_policy` 仍未核验 |
| 检索 | `PASS` | `02_retrieval/retrieval_manifest.json` 已含五问三组检索和证据条目 |
| 语义裁决 D1–D5 | `PASS` | D-005 与 D-007 已落盘 |
| 候选规格 | `PROPOSED` | 五问各 3 个候选，等待规则门禁和协议冻结 |

建模 Agent 无权替集成者裁决语义，也无权自行把门禁置为通过，因此本文件是**冻结包的准备件**，不是冻结协议。

## 冻结包的必需内容（供主 Agent 落盘时使用）

一旦 `rules-problem` 门禁通过，冻结前应再次核对 `03_model/tournament_protocol.json` 至少包含：

1. `schema_version`、`status`（冻结时为 `FROZEN`）、`frozen_at`、`frozen_by`、`decision_ref`（指向 `00_admin/DECISIONS.md` 的条目号）。
2. `problems`：`q1`…`q5`，每个条目含
   - `targets`：尺寸与目标矩阵定义（`F_N` 用式 (3) 还是式 (1)；`q4` 固定为 `F_4⊗F_8`）；
   - `constraints`：约束 1/2 的精确形式，含 `P_q` 定义与 `q` 的整数域；
   - `metrics`：`RMSE` 定义、`L` 的计数口径、`C = qL` 的 `q` 取值；
   - `objective_order`：`(C, K, RMSE)` 等次序与平局规则；
   - `beta_convention`：`β` 的归一化（含是否计入 `L`）；
   - `bounds`：每个 `(N, K)` 可用的严格下界（本仓库目前为 `β=1` 支持下界）；
   - `candidates`：`CANDIDATE_SPECS.md` 第 2 节的候选 ID 与超参搜索范围；
   - `budget`：每个候选的迭代/时间预算与随机种子清单；
   - `evidence_required`：第 1 节的字段契约（含独立复算路径）。
3. `non_goals`：明确"不声称全局最优"的项与"只报 best_found"的项。

## 建模 Agent 建议的默认取值（需主 Agent 裁决后才生效）

| 项 | 建议 | 理由 |
| --- | --- | --- |
| D1 `β` 口径 | 固定 `β = 1` | 与题面式 (3) 单位化一致，并是 README 支持论证所用的口径；尺度退化必须显式排除 |
| D2 问题 5 次序 | 先 `RMSE ≤ 0.1` 可行，再最小 `C`，再最小 `K`，最后最小 `RMSE` | 题面明确"满足精度并使 `C` 尽量低"，`K` 作为第二层需要显式声明 |
| D3 DFT 归一化 | 采用式 (3) | 与 `00_admin/semantic_contract.json` 现有假设一致；改式 (1) 需重算全部阈值 |
| D4 `L` 口径 | 逐层作用于向量时的非平凡常数乘法位置数；`β` 与纯排列不计入 `L` | 与附录一"乘法器个数即复乘次数"最贴近；同时要求报告"共享取负"计数作为敏感性 |
| D4 `q` 域 | `q ∈ Z_{≥1}`，`P_q = {0, ±2^r : r<q}` | 与题面 `q=3` 示例一致；`q=0` 会引入零解 |
| D5 `K` 层边界 | 所有可能扩张支撑的 `N×N` 线性层计入 `K`；纯排列单独记录 | 否则 `2^K` 支持上界失效 |
| D6 V5/V6 | 只保留为候选思路材料，直到提供完整工程包 | 当前无因子、代码、日志，全部为 `UNVERIFIED` |

## 移交

- 接收人：主 Agent（集成者），随后为计算 Agent。
- 需要主 Agent 的动作：裁决 D1–D5 并写入 `00_admin/DECISIONS.md`；随后通知建模 Agent 冻结 `03_model/tournament_protocol.json`。
- 需要计算 Agent 的动作：在协议冻结前**不得**开展正式对擂；可先按 `CANDIDATE_SPECS.md` 第 1 节实现输出契约。
- 需要用户的动作：对 `V6_SEMANTIC_DECISIONS.md` 的 D1–D6 作出选择；若选 D6 选项 1，请提供 V5 NPZ 与 V1–V6 源码包。
