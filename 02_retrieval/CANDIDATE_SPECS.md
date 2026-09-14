# 候选模型规格与对擂接口（草案）

- 角色：M 建模 Agent（`agent/modeling`）
- 状态：**`PROPOSED`（未冻结）**。冻结前置条件见第 5 节；在冻结前，计算 Agent 不得据此开展正式对擂。
- 依据：`03_model/ROW_BOUND_THEORY.md`（本文的可证明结论）、`01_problem/PROBLEM_STATEMENT_AUDIT.md`（待裁决语义）。
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
  "q": 16, "K": 6, "beta": 8.0,
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

1. `rmse_recompute_independent` 必须由**与搜索代码无关**的复算路径产生（本仓库可用 `03_model/checks/verify_row_bound.py` 中的 `dft_matrix/residual` 作为独立参照）。
2. 未计算的量写 `null`，不得写 0。
3. `optimality_claim` 必须逐条命名；"最小误差"在无证明时只能写 `best_found`，并同时给出可用的下界（若存在）。
4. 每个候选都要报告**约束 1/2 的逐元素检查结果**，不能只报 `feasible: true`。

## 2. 候选清单（至少 3 个；`minimum_candidates` 的门槛值由 `00_admin/workflow.json` 的集成者字段裁定，本文件不复制该字段）

### C1 `exact-radix2-chain`（问题 1 的非零精确基准）

- 来源：本题建模结论，`03_model/ROW_BOUND_THEORY.md` 第 3 节（已数值复算精确）。
- 构造：把比特反转排列吸收到第一个 radix-2 蝶形层，得到 `K=t=log2(N)` 个行二稀疏因子，乘积等于 `√N F_N`；取 `β=√N`，`RMSE=0`。支持下界同时证明任何 `β≠0` 的非零精确分解都有 `K≥t`。
- 实测（`N≤64`）：`K=1..6`，`L=0,0,4,20,68,196`（位置计数），`C(q=16)=0,0,64,320,1088,3136`。
- 适用范围：问题 1 的非零精确基准。问题 2–5 可借用其拓扑作搜索初值，但原始扭因子不满足离散集合，不能直接称为可行解。
- 已知限制：扭因子层含非豁免系数，故 `L > 0`；`q = 1` 时需要把扭因子离散化，误差需重新计算。
- **精确性证据**：`N≤64` 的每个尺寸都给出逐元素复算（浮点最大误差 `≤6.4e-14`），并给出 `K`、`L`、`C`；见 `03_model/checks/row_bound_results.json` 的 `t3_exact_radix2`。

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

## 5. 冻结前置条件（`BLOCKED` 项）

`03_model/tournament_protocol.json` 在以下条件全部满足前保持 `NOT_RUN`：

1. `00_admin/rules.json` 不再为 `BLOCKED`（官方题面/规则核验）；
2. `00_admin/DECISIONS.md` 已裁决 `V6_SEMANTIC_DECISIONS.md` 的 D1–D5，特别是：
   - **D1** `β` 归一化（本轮证明它是 `K*`/`C*` 是否有定义的前提，见审计 A7）；
   - **D2** 问题 5 的目标顺序与平局规则；
   - **D3** 采用式 (3) 还是式 (1) 归一化（影响阈值 `0.1` 的绝对含义，见审计 A6）；
   - **D4** `L` 的计数口径与 `q` 的整数域（见审计 A3/A4，直接改变 `C`）；
   - **D5** 计入 `K` 的层类别；
3. `02_retrieval/` 的检索门禁与候选规格齐备（见 `02_retrieval/retrieval_manifest.json` 与 `02_retrieval/CANDIDATE_SPECS.md`）。

在这五项完成前，本文件是**草案**，不得作为冻结协议使用。
