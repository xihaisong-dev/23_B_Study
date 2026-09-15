# Q5「无可行赢家」门禁裁决提案（提案）

- 角色：C 建模 Agent（`agent/modeling`）
- 状态：`PROPOSED`（非冻结；请集成者裁决后并入 `00_admin/DECISIONS.md`）
- 基线提交：`b7b53914d4e8cd17b7eb54a7fb207c5cd05a91ee`（分支 `agent/modeling`）。注意该分支当前落后 `main` 5 个提交：`main` 已含本角色 3 个提交的等价版本（`da5797e`、`3dd246f`、`b4c6f58`），而本分支另有 `d2ada25`、`b7b5391` 两个提交尚未进入 `main`；合并本提案时请留意同文件冲突。
- 关联：`03_model/Q5_GAUSSIAN_INTEGER_INFEASIBILITY.md`、`03_model/checks/q5_gaussian_integer_infeasibility.json`、`03_model/tournament_protocol.json`（冻结）、门禁 `workflow_guard.py check --gate tournament|model-results`

## 1. 事实：门禁子句与其所强制执行的冻结协议互相矛盾

以下三条**同时成立**，均为实测：

**(a) 冻结协议明文要求 Q5 的赢家为 `null`。** `03_model/tournament_protocol.json`（SHA-256 `c253df797845cfff4f24cdcd7da579ed841e487c36bb678cc92a8ebd60457592`）中 `problems[q5].failure_rule`：

> "Apply global failure rule. RMSE>0.1 is INFEASIBLE, not PASS. If no feasible run exists, **winner remains null** and best infeasible RMSE may be reported separately."

`global_fallback_rule` 同旨："For q5, if no run reaches RMSE<=0.1, report no feasible winner within budget."

**(b) 同一协议的 Q5 可行集可证为空。** `03_model/checks/q5_gaussian_integer_infeasibility.json`（`status = PASS`，`failed_checks = []`）的结论为：在 `beta = 1` 下，任意正整数 `q`、任意 `K`、任意右置换的容许乘积都取高斯整数值，因此在全部 6 个已注册 `N`（2, 4, 8, 16, 32, 64）上 `RMSE > 0.1`；`minimum_registered_rmse_lower_bound = 0.125`、`minimum_registered_margin_above_point_one = 0.025`。即 `d_64 = 1/8 = 0.125 > 0.1`。这是**证明**，不是搜索失败；且证书覆盖任意 `q`、任意 `K`，强于冻结网格所需。

**(c) 门禁要求一个「有可行 PASS run」的注册赢家。** `workflow_guard.py` 第 423–428 行：

```python
winner = str(outcome.get("winner_id", ""))
if winner not in expected:
    errors.append(f"{pid}: winner is not a registered candidate")
winner_runs = run_index.get((pid, winner), [])
if not any(r.get("status") == "PASS" and r.get("constraints_status") == "PASS" for r in winner_runs):
    errors.append(f"{pid}: winner has no feasible PASS run")
```

由 (a)+(b)，`winner_id` 只可能取两种值，**而两种都被拒**：

| q5 `winner_id` | 门禁结果（实测） |
| --- | --- |
| `"q5-b0-q1-butterfly"`（当前 `05_results/tournament.json` 的取值） | `FAIL`，1 条错误：`q5: winner has no feasible PASS run` |
| `null`（**协议要求**的取值） | `FAIL`，2 条错误：`q5: winner is not a registered candidate`、`q5: winner has no feasible PASS run` |

第二行的内因是 `str(outcome.get("winner_id", ""))`：JSON `null` 被转成字符串 `"None"`，而 `"None"` 不属于注册候选集，于是**协议要求的取值反而多出一条错误**。

**结论：这不是计算端的实现缺陷，而是门禁与其所强制执行的冻结产物（D-012 冻结的协议）不一致。** 按被冻结的协议，Q5 的正确答案就是「无可行赢家」，而当前门禁没有任何表达该合法终态的途径。因此 `tournament` 与 `model-results` 两个门禁在**遵守协议的前提下永远无法通过**；任何「让它变绿」的做法都必然要么违反协议、要么放宽阈值。

## 2. 影响面（实测）

- 现状 `05_results/tournament.json` 的 q5 记录：`threshold = 0.1`、`runs_total = 957`、`runs_eligible = 0`、`status_counts = {"INFEASIBLE": 957}`、`no_feasible_winner = true`、`winner_basis = "best_structurally_valid_but_rmse_above_threshold"`，并已单独记录 `best_infeasible`（`q5-b0-q1-butterfly`，`RMSE = 0.125`，`N=64, K=1, q=1, L=0, C=0`）。
- **受影响门禁**：`tournament` FAIL（1 错）；`model-results` 因 `check_model_results` 直接调用 `check_tournament`（`workflow_guard.py` 第 442 行）而**继承同一错误**，自身不新增错误。
- **不受影响**：`rules-problem`、`retrieval`、`protocol` 均 PASS；`check_paper`（第 466 行）**不调用** `check_tournament`，故 `paper` 门禁不被本冲突阻塞（`paper` freeze 只依赖 `model_results` freeze 清单的有效性，而该清单现已 `verify-freeze` PASS）。
- 由于本轮已把 `model_results` freeze 修到可移植（清单哈希 = 工作树字节 = 索引 blob，全新检出复测 PASS），**Q5 子句一旦获得裁决，两个门禁即可通过，无需重跑任何 run**。

## 3. 可选裁决

### A（推荐）：承认「无可行赢家」是合法终态，但保持失败关闭

把第 423–428 行改为按「本问题是否记录到任何可行 run」分支，判据取自 `05_results/metrics.json` 的**已记录 runs**，而非调用方声明：

```python
winner_raw = outcome.get("winner_id")            # 允许 null / 缺省
has_feasible = any(
    r.get("status") == "PASS" and r.get("constraints_status") == "PASS"
    for r in run_index_for(pid)                  # 仅本问题的 runs
)
if has_feasible:
    winner = str(winner_raw)                     # 保持现有强约束
    if winner not in expected: errors.append(f"{pid}: winner is not a registered candidate")
    if not any(r.get("status") == "PASS" and r.get("constraints_status") == "PASS"
               for r in run_index.get((pid, winner), [])):
        errors.append(f"{pid}: winner has no feasible PASS run")
else:
    if winner_raw is not None:
        errors.append(f"{pid}: winner must be null when no feasible run exists")
    if not outcome.get("no_feasible_winner"):
        errors.append(f"{pid}: missing no_feasible_winner flag")
    if not nonempty(outcome.get("winner_basis")):
        errors.append(f"{pid}: no feasible run but winner_basis is empty")
    if not outcome.get("best_infeasible"):
        errors.append(f"{pid}: no feasible run but best_infeasible evidence is missing")
```

要点：

- **仍然失败关闭**：无可行 run 时必须留下 `no_feasible_winner` + `winner_basis` + `best_infeasible` 三项证据，缺一即 FAIL。
- **不可被滥用**：只有当**实测 runs 中确实一条可行 run 都没有**时才走 null 分支；因此该放宽无法用来跳过本可解出的问题。存在可行 run 时仍沿用原强约束。
- **不引入放宽阈值或改状态名**：`RMSE > 0.1` 仍为 `INFEASIBLE`，`threshold` 不变。
- 代价与权限：需修改**仓库外**的共享工具 `workflow_guard.py`（见 §4），并在 `DECISIONS.md` 落盘；该改动影响全流程判定语义，属集成者/总控权限。

**A′（可选加强）**：上述判据无法区分「已证明不可行」与「只是没搜到」。若要保留这一区分，可在 null 分支追加要求：`outcome` 必须给出可落盘的不可行性依据路径（例如 `infeasibility_evidence`，指向 `03_model/checks/q5_gaussian_integer_infeasibility.json` 一类证书），且该路径必须存在于磁盘。Q5 已具备该证书；其他问题若走 null 分支则须显式声明「未证明，仅未搜到」。

### B：仅放宽为「允许 `winner_id` 为 null，不再要求赢家可行」

最小改动（删除第 427–428 行的 `any(...)` 检查）。**不建议**：这会让任何问题都用一个不可行赢家「通过」，等于取消该门禁的核心保障，并与仓库规则「`FAIL`、`BLOCKED`、`NOT_RUN` 均不得当作通过」直接冲突。

### C：把 Q5 改为「仅报告、不设赢家」并从该门禁的问题集排除

需**重冻协议**并重走受影响的冻结链（`tournament_protocol` → `model_results` → `paper`）。代价最大，但语义最干净：Q5 的定位本就与 q1–q4 不同（可行集可证为空）。若集成者希望保留「每个问题都必须有赢家」的强形式，选此项。

### D：不改门禁，接受两个门禁长期 FAIL，论文按「Q5 无可行解」表述

零改动、零越权，但违反「正式流程必须依次满足」的要求，最终验收将永久停在此处。**仅在集成者明确接受该终态时**可选。

## 4. 与仓库边界有关的现实约束（须由集成者处理）

- `workflow_guard.py` **不在本仓库内**（`git ls-files` 匹配计数为 0）。实际文件为
  `C:\Users\Lenovo\.codex\skills\1start-mathmodel\scripts\workflow_guard.py`（32611 字节，mtime 2026-09-12 15:01:01）。
  因此方案 A/A′/B/C **都无法由任一泳道 Agent 在仓库内完成**，必须由掌握该技能工具的一方实施。本提案未对该文件做任何改动，也未在其上尝试越权写入。
- 该工具对「替换已存在的冻结」提供的唯一正式途径是 `freeze --replace --change-request "<说明>"`（`workflow_guard.py` 第 589–592 行；替换时必须给出 `--change-request`），且要求依赖阶段的 freeze 校验为 `PASS`。方案 C 必须走这条路径，并在 freeze 清单的 `change_request` 字段留下说明。
- 建议在 `00_admin/DECISIONS.md` 新增条目（D-013）记录裁决，并注明 `workflow_guard.py` 的版本/位置与是否随之修改，以便日后复算。

## 5. 本提案明确未做的事

- 未修改 `03_model/tournament_protocol.json`、任何 freeze 清单、任何门禁代码或 `workflow_guard.py`。
- 未放宽阈值、未改状态名、未伪造可行 run；`05_results/tournament.json` 仍如实记录 `no_feasible_winner = true`，Q5 的赢家字段标注为「结构上最优但超阈值」，并把 `best_infeasible` 单独列出。
- §1 表格中 `winner_id = null` 一行是在 `05_results/tournament.json` 的临时副本上运行**真实门禁**得到的；测后已逐字节还原（`git checkout --`），sha256 `33672F7C11F9EEDEB87646238465B95200242A15E4A8E9F5CA28840B02140131` 前后一致，工作树 0 个未提交项。

## 6. 建议与接收人

- 接收人：主 Agent / 集成者（抄送计算 Agent、论文 Agent）。
- 建议顺序：(1) 采纳方案 A（如希望保留「已证明/未搜到」的区分，并入 A′）；(2) 由具备 `workflow_guard.py` 权限的一方实施并记录版本；(3) 在 `DECISIONS.md` 落盘 D-013；(4) 重跑 `check --gate tournament` 与 `--gate model-results` 确认 PASS；(5) 论文端按「Q5 无可行解（可证）」表述，量化结论引用 `best_infeasible = 0.125` 与 `d_64 = 1/8`。
- 补充提示：无论采纳哪个方案，都应保留 Q5 的 `best_infeasible` 与证书哈希，避免后续把「证明无解」误表述为「搜索失败」。
