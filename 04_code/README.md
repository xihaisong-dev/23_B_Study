# 04_code — 计算端骨架（协议已冻结）

当前已具备目标构造、RMSE/约束/复杂度计数、全部冻结候选、统一搜索预算、批次谱系、稳定分片/续跑和失败关闭聚合器。正式运行必须保留完整 run manifest，失败运行不得删除。

## 状态

- `03_model/tournament_protocol.json`：`PASS / APPROVED`，含 5 个问题、每题 3 个候选。
- `00_admin/freezes/tournament_protocol.json` 已验证；`scripts/validate_protocol.py` 退出码为 0。
- `scripts/run_tournament.py` 支持 L2/L3/L4 dry-run、非正式 smoke、问题/候选过滤、稳定 shard 与 resume；正式 1442-run 尚未执行。

## 环境

纯标准库，无第三方依赖。本轮验证环境为 CPython `3.14.6`；测试用 stdlib `unittest`，无需安装任何东西。

## 运行测试

```bash
cd 04_code
python -m unittest discover -s tests -p "test_*.py" -v
```

每个测试文件自行把 `src/` 加入 `sys.path`，因此从任意工作目录运行均可。

## 冻结后的 L0/L1 里程碑

所有 `04_code/**/*.py` 文件均在文件头按 D-011 记录 AI 辅助工具、型号、开发机构和版本日期披露边界。正式运行前依次执行：

```bash
python -X utf8 C:/Users/Lenovo/.codex/skills/1start-mathmodel/scripts/workflow_guard.py verify-freeze --workspace . --stage tournament_protocol
python -X utf8 04_code/scripts/validate_protocol.py
python -X utf8 04_code/scripts/run_l0.py
python -X utf8 04_code/scripts/run_baselines.py
```

`run_baselines.py` 只执行冻结协议登记的 q1--q5 确定性 baseline。每个 `(problem,N,K,q,candidate,seed)` 使用全新 run-id，因子以稀疏 JSON 保存并由独立路径重新加载复算。该里程碑把 `metrics.json` 与 `tournament.json` 保持为 `BLOCKED`，直到挑战者、稳健性和消融全部完成；不会提前选择最终胜者。

## 统一 runner

```bash
python 04_code/scripts/validate_protocol.py
python 04_code/scripts/run_tournament.py --dry-run --level L2
python 04_code/scripts/run_tournament.py --smoke --level L2
python 04_code/scripts/run_tournament.py --dry-run --level L2 --shard-index 0 --shard-count 3
python 04_code/scripts/run_tournament.py --dry-run --level L3
```

放行条件（全部满足才 `allowed=True`）：

1. `03_model/tournament_protocol.json` 的 `status == "PASS"`；
2. 该协议的 `problems` 非空；
3. `00_admin/freezes/tournament_protocol.json` 存在、元数据为 `status == "PASS"`/`stage == "tournament_protocol"`，并通过文件 SHA-256、大小及上游 `problem` 冻结依赖校验；
4. 冻结清单必须显式绑定当前 `03_model/tournament_protocol.json`。

`PASS` 是机器状态；“已冻结”由 `00_admin/freezes/tournament_protocol.json` 的可验证哈希清单证明，不使用 `FROZEN` 状态 token。该口径与 `workflow_guard.py verify-freeze --stage tournament_protocol` 一致。

## 模块

| 模块 | 职责 |
| --- | --- |
| `targets` | 式 (1)/(3) DFT、Kronecker、`product([A1,..,AK]) = A1@..@AK` |
| `metrics` | `RMSE = ||F - P||_F / N`（D-005 固定 `beta=1`） |
| `hardware` | `L`（非 FREE 位置计数）与 `C = q*L`，精确分类、失败关闭 |
| `constraints` | 约束 1 行稀疏、约束 2 字母表 `P_q`（实/虚分量精确成员） |
| `serialization` | 复数矩阵规范字节与内容哈希 |
| `hashing` | 文件/字节 SHA-256 |
| `contracts` | 协议适配只读数据对象 |
| `candidate_api` | 候选 `Protocol`、结构化 `FailureRecord`、fake 候选 |
| `provenance` | run-id、环境摘要、最小 manifest |
| `protocol_gate` | 失败关闭门禁 |
| `search_budget` | 循环内 wall/sweep/patience/tolerance 停止与轨迹 |
| `independent_search_score` | 不导入生产目标/指标模块的搜索接受与 patience 评分 |
| `formal_tournament_runner` | 批次、分片、续跑、manifest 与独立复算 |
| `aggregation` | 1442 tuple 双射、冻结排序、fallback 与 q5 frontier |
| `validation_runs` | L3/L4 parent/variant 子运行预登记与统计 |

L3/L4 正式执行必须通过 `--parent-batch-id` 指向已完成的真实 L2 批次；每个子运行绑定真实 `parent_run_id`。reverse initialization/update、tolerance、right-associated 独立计算和 boundary K/q 均改变实际执行，L4 四个 adapter 会真实禁用对应初始化、支持重连、离散润色或固定 Butterfly 支持。

Q5 的 Gaussian 整数格下界为 `min(1/sqrt(N),1-1/sqrt(N))`，冻结六个 N 均大于 0.1。`--q5-certificate-shortcut` 仅供 readiness 审计，默认关闭；在没有获批并冻结的协议变更请求时，正式运行会失败关闭，不能用证书悄悄替代冻结搜索。

## 口径（D-005）

- `beta` 固定为 1，不计入 `L`；`RMSE = ||F_N - P||_F / N`。
- 免计数集合精确为 `{0, ±1, ±j, ±1±j}`；近似值不四舍五入进免计数集合。
- `P_q = {0, ±2^r : r < q}` 作用于实部与虚部（笛卡尔积）；`q` 只读协议。
- `product` 按存储乘积顺序计算 `A1@A2@...@AK`；对列向量实际由 `AK` 先作用。纯排列右乘并单独记录。

## 尚未执行

- 正式 1442-run L2、L3 稳健性和 L4 消融均未运行；总状态必须保持 `BLOCKED`。
