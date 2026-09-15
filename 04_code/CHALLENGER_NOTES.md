# 挑战者实现与对擂执行（agent/compute-tournament）

- 角色：E 计算 Agent
- 分支 / worktree：`agent/compute-tournament` / `worktrees/compute-tournament`
- 基线：`origin/agent/compute` = `6d1d2691bc3fb3728d6ba5c6ec3733d906007455`
- 状态：框架已提交并可复算；全量挑战者对擂在后台执行中，结果以 `05_results/challenger_runs.json` 为准
- 隔离说明：本 worktree 是**新建的干净工作树**，与并发会话使用的 `worktrees/compute` 以及另一会话使用中的 `worktrees/compute-challengers` **完全分离**，本分支不改动它们的任何文件。

## 1. 交付内容

| 文件 | 职责 |
| --- | --- |
| `04_code/src/dft_integer_approx/challenger_core.py` | 高效核心：`sparse_row_update`（含行上限的解析支撑更新）、`exact_factor_update`（无上限）、`continuous_factor_update`（松弛+自适应格点投影）、`descend`（只接受实测改善的块坐标下降，带 deadline 守卫） |
| `04_code/src/dft_integer_approx/challengers.py` | 冻结协议注册的 10 个挑战者，按问题约束选择优化器 |
| `04_code/src/dft_integer_approx/formal_challenger_runner.py` | L2 执行器：与基线执行器一致的 gate、产物布局、约束检查、独立复算与 manifest 字段 |
| `04_code/scripts/run_challengers.py` | 命令行入口（支持 `--dry-run`、`--problem`、`--max-n`、`--candidate`、`--limit`） |

## 2. 两个容易写错、且已实测确认的设计点

### 2.1 优化器必须按问题类别选择（错误的选择会毁掉精确解）

- **问题 1 的精确链首层是稠密的**（`1/sqrt(N)` 的折入使其如此）。对它施加"每行至多 2 个非零"的**约束式**更新会把目标从精确值破坏到 `O(1/sqrt(N))` 量级（实测 N=8、K=3 从 0 变成 0.2286）。
  因此 q1 使用**无上限**的精确更新，行上限只作为结果的**检查**，不作为搜索约束。
- **问题 3/4/5** 才有真正的行上限约束，使用 `sparse_row_update`：它直接求解受限问题，并让每行最多保留 `row_cap` 个非零，因此 `L`（进而 `C`）不会因为因子稠密化而虚高。

### 2.2 排序与评分的乘积约定

评分为 `approximate_matrix(factors, permutation) = product(factors) @ P`，`P = bit_reversal_permutation(n)`。实测：`N=8` 时带 `P` 误差 `3.1e-16`，不带 `P` 误差 `0.878`。所有从蝶形出发的挑战者都携带该排列。搜索内部使用的目标函数也必须带 `P`，否则优化的是另一个矩阵。

## 3. 性能修正

上一版用"试探-重算全乘积"的支撑交换，复杂度 `O(N^4)`，`N=32` 单次运行需 40–80 秒。现在全部更新为 `O(K N^3)`：

| 规模 | 单次 1 sweep | 
| --- | --- |
| N=32, K=5 | 0.08 s |
| N=64, K=6 (q1) | 0.78 s |
| N=64, K=5 (q5) | 1.72 s |

## 4. 已完成的 q1 结果

`--problem q1` 全量 36 runs（6 尺寸 × 2 挑战者 × 种子 {17,43,71}）：**36/36 PASS**。

| 候选 | RMSE | L |
| --- | --- | --- |
| `q1-b0-scaled-radix2`（基线） | `3.1e-16` … `1.3e-15` | 48 (N=8) … 768 (N=64) |
| `q1-c1-palm-row2` | 同上 | 同上 |
| `q1-c2-structure-reconnect` | 同上 | 同上 |

即 **q1 的挑战者只是追平基线，没有改进**：问题 1 在 `K = log2(N)` 已有精确解且 `L` 相同，所以挑战者在该问题上是等价的，`(C,K,RMSE)` 排序下不产生替换。这一点按仓库规则如实记录，不作改进声明。

## 5. 已知限制

- q1 之外的问题尚未跑完（后台执行中）；本文件不预写任何结论。
- q2 无行约束且字母表为整数格 `P_3`，量化会把 `1/sqrt(N)` 量级的目标清零；目前 q2 挑战者只能追平 `K=1` 的量化基线（0.353553 at N=8），未见改进。
- `deadline` 守卫只保证单次 sweep 不超时，尚未接入协议的完整分段预算（`N≤16` 300 s、`N=32` 900 s、`N=64` 1800 s）的强制中止。
- 未实现 L3（种子/初始化次序/浮点容差/乘法结合顺序稳健性）与 L4（消融）。

## 6. 复现

```bash
python -X utf8 04_code/scripts/run_challengers.py --dry-run        # 计划
python -X utf8 04_code/scripts/run_challengers.py --problem q1     # 单问题
python -X utf8 04_code/scripts/run_challengers.py                  # 全量
python -X utf8 -m unittest discover -s 04_code/tests -p "test_*.py"
```

必须在仓库根执行（门禁使用相对路径）。每个 run 写入 `05_results/runs/<run-id>/`（`factors.json`、`run_manifest.json`、`stdout.txt`、`stderr.txt`），不覆盖、不删除；汇总写入 `05_results/challenger_runs.json`。
