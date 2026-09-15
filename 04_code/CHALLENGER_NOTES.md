# 挑战者代码里程碑（仅 smoke，不是正式对擂结论）

- 分支 / worktree：`agent/compute-challengers` / `worktrees/compute-challengers`
- 冻结协议：`03_model/tournament_protocol.json` SHA-256 `c253df797845cfff4f24cdcd7da579ed841e487c36bb678cc92a8ebd60457592`
- 当前状态：`BLOCKED`；只完成最小可行性与统一 runner 框架，未运行正式 1442-run L2，也未运行 L3/L4。

## 已修正的语义与缺陷

1. q1 精确 radix-2 构造仅在一个 counted factor 吸收 `1/sqrt(N)`；N=8 的 L0 直接断言 `L=20,C=320`。旧正式 run 不删除，但其 q1 L/C 已被新口径取代。
2. q1 挑战者不再对精确起点重复缩放。
3. q4 generic 候选使用明确定义的单位排列，不再引用未定义 `perm`。
4. support swap 的每次接受判断都使用与评分相同的右置纯排列。
5. 离散候选即使最近格点全为零也不回退连续解，保证 q2–q5 的最终系数严格属于 `P_q`。
6. 种子实际驱动初始化、因子更新顺序和支持提议顺序；诊断记录 `seed_trace`。

## 已接通范围

- 10 个冻结 challenger id 均有最小可行实现；5 个 baseline 与 10 个 challenger 统一经 `run_tournament.py` 调度。
- `--dry-run` 展开完整冻结 L2 网格；当前契约为 1442 个互异 `(problem,candidate,N,K,q,seed)` tuple。
- `--problem`、`--candidate` 可组合筛选；`--smoke` 每个候选运行一个小实例；`--execute-full` 是正式批次入口。
- 每次执行只创建新的 run-id 目录，保留 PASS、INFEASIBLE、TIMEOUT、CRASH 和 CONSTRAINT_FAIL；manifest 绑定协议/冻结/代码树/目标/因子/批次/单 run 配置哈希以及独立复算结果。
- `validation_plan.json` 明确 L1 q1 旧结果被取代、L2 仅 smoke、L3/L4 未运行；winner 始终为 null。

## 正式批次前的阻塞项

当前非 smoke 路径仍是固定 pass 的参考实现，diagnostics 明确标注
`fixed_pass_reference_pending_frozen_budget_control`。在正式 1442-run 前必须：

1. 把冻结 wall-clock、sweep cap 与 patience 传入各搜索循环，并在循环内截止，不只事后判 TIMEOUT；
2. 将协议声明的 beam / 多行 reconnect / best-two support 等操作变成真实候选状态搜索，而不是仅在 diagnostics 中记录参数；
3. 实现并执行真实 L3 稳健性轴与 L4 消融，生成完整汇总后再选择 winner；
4. 由独立审阅者复核 runner、manifest 谱系与完整 1442 tuple，再授权正式批次。

因此本里程碑的 smoke 数值只能证明接口、约束、持久化和独立复算链路可工作，不能用于论文中的模型优胜结论。
