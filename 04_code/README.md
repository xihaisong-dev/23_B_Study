# 04_code — 计算端骨架（协议冻结前）

计算 Agent 在对擂协议冻结前可搭建的工程骨架：目标构造、RMSE/约束/复杂度计数的纯函数、候选插件契约、谱系与失败关闭门禁。**不实现或挑选任何候选，不产生正式实验数值。**

## 状态

- `03_model/tournament_protocol.json`：`NOT_RUN`（`problems` 为空），冻结文件 `00_admin/freezes/tournament_protocol.json` 缺失。
- 因此 `scripts/validate_protocol.py` 与 `scripts/run_tournament.py` 均**失败关闭**（退出码 1），拒绝正式对擂。
- 冻结前测试输出写入系统临时目录，**不写 `05_results/`**。

## 环境

纯标准库，无第三方依赖。本机 `Python 3.12.10`、`numpy 2.5.0`（已装但未作为锁定依赖使用）、`pytest` 未装。测试用 stdlib `unittest`，无需安装任何东西。

## 运行测试

```bash
cd 04_code
python -m unittest discover -s tests -p "test_*.py" -v
```

每个测试文件自行把 `src/` 加入 `sys.path`，因此从任意工作目录运行均可。

## 失败关闭门禁

```bash
cd 04_code
python scripts/validate_protocol.py     # 当前应打印 reasons 并以退出码 1 拒绝
python scripts/run_tournament.py        # 当前应拒绝
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
| `runner` | 门禁优先的候选执行唯一入口 |

## 口径（D-005）

- `beta` 固定为 1，不计入 `L`；`RMSE = ||F_N - P||_F / N`。
- 免计数集合精确为 `{0, ±1, ±j, ±1±j}`；近似值不四舍五入进免计数集合。
- `P_q = {0, ±2^r : r < q}` 作用于实部与虚部（笛卡尔积）；`q` 只读协议。
- `product` 采用题面式 (6) 的左起优先顺序 `A1 A2 ... AK`；建模层 `03_model/checks/verify_row_bound.py` 使用相反的应用顺序 `chain`，作为独立复算路径保留。

## 尚未实现（冻结后）

- NPZ 安全加载（需锁定 NumPy）、真实候选映射、L0–L4 执行、`05_results/runs/<run-id>/` 不可覆盖写入与汇总器。
