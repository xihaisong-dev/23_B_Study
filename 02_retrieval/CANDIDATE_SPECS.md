# 候选模型规格与对擂接口

- 角色：M 建模 Agent（`agent/modeling`）
- 状态：**`PASS / FROZEN`**。机器依据为 `00_admin/freezes/tournament_protocol.json`；计算 Agent 可据此实现候选并开展 L0--L4，任何协议改动必须走替换冻结流程。
- 依据：D-005、`00_admin/semantic_contract.json`、`03_model/ROW_BOUND_THEORY.md` 与 `02_retrieval/EVIDENCE_MATRIX.md`。D-005 已取代本文历史版本中的自由 `β` 口径。
- 目的：把"五个问题要比较哪些候选"写成可执行规格，使计算 Agent 能在协议冻结后立即实现，而无需再猜题意。

## 1. 共享输出契约（每个候选、每个尺寸、每次运行都必须给出）

与 `01_problem/PROBLEM_BRIEF.md` 第 6 节一致，此处给出机器可读字段名，供计算 Agent 直接落地：

```json
{
  "run_id": "string",
  "problem": "q1|q2|q3|q4|q5",
  "candidate_id": "string",
  "N": 64,
  "target": {"kind": "dft|kron", "definition": "式(3)单位化|F4xF8",
             "sha256_of_matrix_bytes": "string"},
  "q": 16, "K": 6, "beta": 1.0,
  "factors": [{"layer": 1, "row_support_max": 2, "nonzeros": 32,
               "entries_sha256": "string"}],
  "constraint1_row_support_max": 2,
  "constraint2_allowed_set": "{0,±1,...}",
  "constraint2_violations": 0,
  "rmse": 0.0,
  "rmse_recompute_independent": 0.0,
  "L": 196, "C": 3136,
  "seed": 17, "budget": "string", "wall_clock_s": 0.0,
  "feasible": true,
  "optimality_claim": "exact|lower_bound|best_found|heuristic"
}
```

硬性要求：

1. 因子按 `[A1,...,AK]` 存储，乘积固定为 `A1 @ A2 @ ... @ AK`；对列向量作用时 `AK` 最先作用。搜索代码与独立复算不得采用相反顺序。
2. `rmse_recompute_independent` 必须由**与搜索代码无关**的复算路径产生（本仓库可用 `03_model/checks/verify_row_bound.py` 中的 `dft_matrix/residual` 作为独立参照）。
3. 未计算的量写 `null`，不得写 0。
4. `optimality_claim` 必须逐条命名；"最小误差"在无证明时只能写 `best_found`，并同时给出可用的下界（若存在）。
5. 每个候选都要报告**约束 1/2 的逐元素检查结果**，不能只报 `feasible: true`。

## 2. 候选清单（至少 3 个；`minimum_candidates` 的门槛值由 `00_admin/workflow.json` 的集成者字段裁定，本文件不复制该字段）

### C1 `exact-radix2-chain`（问题 1 的非零精确基准）

- 来源：本题建模结论，`03_model/ROW_BOUND_THEORY.md` 第 3 节（已数值复算精确）。
- 构造：把比特反转排列吸收到第一个 radix-2 蝶形层，得到 `K=t=log2(N)` 个行二稀疏因子。历史证书的未缩放乘积为 `√N F_N`；D-005 固定 `β=1`，因此正式基线必须把 `1/√N` 吸收到某个计入 `K` 的因子，使乘积等于 `F_N`，并对**缩放后的全部因子重新计数** `L`。支持下界只证明非零精确分解须有 `K≥t`。
- 已有证书（仅结构/精确性）：`N≤64` 的未缩放链为 `K=1..6` 且精确。历史 `L=0,0,4,20,68,196` 是未缩放链的位置计数，**不得**作为 D-005 固定 `β=1` 基线的复杂度；正式 `L,C` 等计算 Agent 从头复算后再填。
- 适用范围：问题 1 的非零精确基准。问题 2–5 可借用其拓扑作搜索初值，但原始扭因子不满足离散集合，不能直接称为可行解。
- 已知限制：扭因子层含非豁免系数，故 `L > 0`；`q = 1` 时需要把扭因子离散化，误差需重新计算。
- **精确性证据**：`N≤64` 的每个尺寸都给出未缩放链的逐元素复算（浮点最大误差 `≤6.4e-14`）；见 `03_model/checks/row_bound_results.json` 的 `t3_exact_radix2`。固定 `β=1` 版本需由计算 Agent 独立复算缩放链及其 `L,C`。

### C2 `support-optimal-discrete`（问题 2/3 的主候选）

- 思路：固定 `q`（问题 2/3 为 `q=3`），在"每行至多 `M = min(N, 2^K)` 个非零"的支撑结构上，先用 C1 的支撑图作为初值，再做离散系数投影 + 支撑重连的局部搜索。
- 目标：在给定 `K` 下最小 `RMSE`；同时报告 `L`、`C = qL`。
- 必须报告的对照量：`03_model/ROW_BOUND_THEORY.md` 第 4 节的 `β=1` 支持下界（`q` 无关），用于判断是否还有改进空间。
- 已知限制：该下界在 `M = N` 时退化为 0，因此对较大 `K` 不提供可证最优性。

### C3 `budget-first-q1`（问题 5 的主候选）

- 思路：问题 5 的目标顺序先最小化 `C = qL`。由于 `q=1` 时全部允许系数落在豁免集合内，任何**只含**豁免系数的因子链都有 `L = 0`、`C = 0`。因此问题 5 的第一层问题是：
  > 在"每行至多 2 个非零、系数 `∈ {0,±1,±j,±1±j}`、`L = 0`"的约束下，`N = 2^t` 能达到的最小 `RMSE` 是多少，以及达到 `RMSE ≤ 0.1` 所需的最小 `K`。
- 本仓库已知：该问题目前**没有下界证书**（`ROW_BOUND_THEORY.md` 第 7 节）。用户 README 声称 `N=64, K=5, L=0, RMSE≈0.0905`，但因子、代码与日志均未提供，故为 `UNVERIFIED`。
- 需要计算 Agent 提供：可行解（若有）、搜索预算、失败/超时记录、以及在 `L=0` 类内逐 `K` 的最好值。
- 已知限制：若 `L=0` 类在某个尺寸上不可行，必须明确报告"该类无可行解或未找到"，不能以"近似为 0"代替。

### C4（可选）`user-v5-replication`（第三方材料的独立复现）

- 触发条件：用户按 `V6_SEMANTIC_DECISIONS.md` D6 选项 1 提供完整工程包。
- 要求：计算 Agent 用**自己**的代码独立复算 V5 因子链的 `RMSE`、`L`、约束 1/2 与 `C`，并给出 run-id 与产物哈希。
- 在此之前，V5/V6 的任何数字保持 `UNVERIFIED`，不得进入 `05_results/` 或论文。

## 3. 每个问题的推荐候选与判据

| 问题 | 候选 | 判据（必须同时给出） |
| --- | --- | --- |
| 1 | C1 为主，C2（不限系数）为对照 | `RMSE`（C1 应为 0）、`K`、`L`、`C = 16L` |
| 2 | C2 | 每个 `N ∈ {2,4,8,16,32}` 的 `RMSE`、`C = 3L`、约束 2 逐元素检查 |
| 3 | C2（同时施加约束 1 与 2） | 同上，另加约束 1 逐行检查 |
| 4 | C2（目标换为 `F_4⊗F_8`） | 必须以 `F_4⊗F_8` 构造目标（见审计 A5），`C = 3L` |
| 5 | C3 为主，C1/C2 作对照 | `q`、`K`、`RMSE ≤ 0.1` 的可行性证据、`C = qL`、在 `L=0` 类内是否可行 |

## 4. 对照与证据要求

1. **同一预算**：所有候选在每个 `(问题, N, K)` 上使用相同的时间/迭代预算，预算值写入协议。
2. **失败也算结果**：超时、不可行、约束违反的运行必须留档；只保留"较好"的种子视为无效。
3. **下界并列**：每个候选旁必须列出该 `(问题, N, K)` 可用的严格下界（本仓库目前只有 `03_model/ROW_BOUND_THEORY.md` 第 4 节的 `β=1` 支持下界）。
4. **独立性**：`rmse` 与 `rmse_recompute_independent` 必须来自不同代码路径。
5. **冻结**：候选结果只能由计算 Agent 写入 `05_results/`，建模 Agent 不写正式结果。

## 5. 冻结状态

1. `rules-problem`、`retrieval` 与 `protocol` 门禁均已由主 Agent 运行并记录为 `PASS`。
2. D-005/D-007 的 `β`、q5 目标、DFT/RMSE、`P_q/L`、`K` 和因子顺序与 `semantic_contract.json` 保持一致。
3. `00_admin/freezes/tournament_protocol.json` 已递归绑定 problem 冻结和本协议输入；计算前仍须运行 `verify-freeze --stage tournament_protocol`，出现任何哈希漂移立即停止。

本文件是冻结协议的人类接口说明；机器权威内容以已冻结的 `03_model/tournament_protocol.json` 为准。
