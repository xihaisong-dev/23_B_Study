# 挑战者实现记录（进行中）与一处基线自洽性问题

- 角色：E 计算 Agent（独立 worktree，避免与并发会话冲突）
- 分支 / worktree：`agent/compute-challengers` / `worktrees/compute-challengers`
- 基线：`agent/compute` = `6d1d2691bc3fb3728d6ba5c6ec3733d906007455`
- 状态：**代码已就位但挑战者尚不具竞争力**；本文只记录已实测的事实与一个待澄清的基线自洽性问题，不作任何改进声明。

## 1. 已实现的挑战者

`04_code/src/dft_integer_approx/challengers.py` 按 `baselines.py` 的既有约定（`BaselineSolution(factors, permutation, masks, diagnostics)`，评分为 `approximate_matrix(factors, permutation) = product(factors) @ P`）实现了冻结协议注册的 10 个挑战者：

| 协议 id | 初始化 | 局部搜索 |
| --- | --- | --- |
| `q1-c1-palm-row2` | 精确 radix-2 链 | 无约束逐因子精确块更新（4 轮） |
| `q1-c2-structure-reconnect` | 同上 | 块更新 + 单点支撑交换 |
| `q2-c1-sp2-recursive` | 量化蝶形 + 单位层 | 贪心右因子 + 离散润色 |
| `q2-c2-relax-project-polish` | 同上 | 连续松弛 → 自适应缩放投影 → 离散润色 |
| `q3-c1-discrete-coordinate` | 量化蝶形（含排列） | 精确离散块更新 + 支撑交换 |
| `q3-c2-hierarchical-reconnect` | 同上 | 块更新 + 2 轮支撑交换 |
| `q4-c1-generic-discrete` | 随机 ±1 行二 | 块更新 + 支撑交换 |
| `q4-c2-kron-reconnect` | `(F4 层) ⊗ (F8 层)` 提升 | 块更新 + 跨块支撑交换 |
| `q5-c1-lexicographic-grid` | 量化蝶形（含排列） | 3 轮块更新 + 支撑交换 |
| `q5-c2-large-neighborhood` | 同上 | 块更新 + 3 轮支撑交换 |

共享算子：`exact_factor_update`（固定其余因子时逐项精确最优，含行上限与改进守卫）、`continuous_factor_update`（最小二乘解 + 幂次缩放的格点投影）、`support_swap_sweep`（单点支撑交换，仅接受目标改善）。

## 2. 本轮修掉的四个自身缺陷（均实测）

1. **丢掉外部排列**：`radix2_unitary_factors` 的链需要右乘比特反转排列才是 `F_N`；早稿用单位排列评分为 0.354，与该会话基线同为 0.354 却误以为"追平"。实测：`N=8` 时 `approx(raw, perm)` 误差 `3.1e-16`，`approx(raw, identity)` 误差 `0.878`。
2. **目标函数漏掉排列**：搜索优化的是 `product(factors)`，评分却是 `product(factors) @ P`，两者在 `N=8` 相差 0.354。已把 `permutation` 贯穿到 `_objective`、`_polish`、`support_swap_sweep` 与 `exact_factor_update`。
3. **无条件接受更新**：`_polish` 曾无条件接受单因子精确解，而带行上限后的候选**不是**该受限集合上的最小化者（上限会丢掉无约束解想要的项），于是一遍润色就把精确解破坏成 `1/sqrt(N)` 量级。已加改进守卫（只在完全复算的目标下降时才接受）。
4. **量化起点把目标清零**：把单位化目标直接投影到整数格 `P_q` 会全变 0（`N=64` 时目标模长 0.125 < 格距 1）；改为从**已按 `1/sqrt(2)` 缩放的量化蝶形层**起步。

## 3. 待澄清：`exact_q1_baseline` 无法由其自身助手函数复现

这是本轮最值得上报的问题，全部为实测值：

| 构造 | RMSE vs `F_N` |
| --- | --- |
| `exact_q1_baseline(8)`（`approximate_matrix(factors, permutation)`） | `3.14e-16`（精确） |
| `radix2_unitary_factors(8)` 原样 + `bit_reversal_permutation(8)` | `3.14e-16`（精确） |
| 同上，但把第一层乘 `1/sqrt(N)`（`beta=1`） | `2.29e-01` |
| 同上，把第一层乘 `sqrt(N)` | 更差 |

即：`radix2_unitary_factors` 的原样链配排列就已等于 `F_N`（说明每层的 `1/sqrt(2)` 已经承担了全部缩放），但 `exact_q1_baseline` 报告的 `L` 明显小于该原样链（`N=8` 时基线 `L=48`，原样链 `L=192`），而 `L` 由 `count_nontrivial_positions(solution.factors)` 直接统计。**两者不可能同时成立**，除非 `exact_q1_baseline` 使用了另一条尚未在本 worktree 中呈现的因子构造。

- 影响：`C=qL` 是问题 1 的次要指标，`L` 的口径又直接进入 `(C,K,RMSE)` 排序，因此这一问题会影响 q1 的名次与论文中的复杂度数字。
- 建议：由 `agent/compute` 的所属会话确认 `exact_q1_baseline` 的因子来源（是否与 `radix2_unitary_factors` 相同、`L=48` 对应的具体因子矩阵），并让 `L0` 检查直接断言 `L` 与该构造的一致性。

## 4. 当前实测（不作为结论）

`N=8`、`K=3`（q4 用 `N=32`、`K=3`）、`seed=17`：

| 候选 | RMSE | L |
| --- | --- | --- |
| `q1-b0-scaled-radix2` | `3.1e-16` | 48 |
| `q1-c1-palm-row2` | `2.29e-01` | 48 |
| `q1-c2-structure-reconnect` | `3.54e-01` | 20 |
| `q3-b0-quantized-butterfly` | `3.54e-01` | 0 |
| `q3-c1/c2`、`q5-c1/c2` | `3.54e-01` | 0 |
| `q2-b0-onefactor-quantize` | `3.54e-01` | 0 |
| `q4-c1/c2` | `1.77e-01` | 0…52 |

**没有挑战者优于基线**，且 `q1` 挑战者目前比精确基线差一个数量级。因此本 worktree 不发布任何对擂结论，也不写 `05_results/`。

## 5. 已知性能问题

`q4` 挑战者在 `N=32, K=3` 单次 `seed` 耗时 40–80 秒（支撑交换每步重算全乘积，`O(N^4)` 量级）。按协议的全网格与 3 个种子，q4 一个候选约需 30–60 分钟，需要先做增量目标更新才能纳入正式预算。

## 6. 下一步

1. 先解决第 3 节的基线自洽性问题（阻塞 q1 的 C/K 排序）；
2. 把支撑交换改成增量目标更新（缓存 `product(factors)` 与前缀/后缀积），目标是把 `q4`/`q5` 的 `N=32/64` 拉进协议预算；
3. 在挑战者至少追平基线后再执行 L2，并按协议种子 `{17,43,71}` 与确定性种子 `0` 写入 `05_results/runs/`。
