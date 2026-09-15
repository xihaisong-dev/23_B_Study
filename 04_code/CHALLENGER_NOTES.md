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

当前已用统一 `SearchBudget/StopState` 在搜索循环内执行 wall deadline、sweep cap、50-sweep patience 与 `1e-10` 改善阈值，并记录完整 sweep/proposal 摘要；beam、best-two、单行/多行 reconnect、cross-block reconnect 与 permutation swap 均实际构造候选并按目标接受。runner 固定批次 plan/config，支持稳定 tuple hash 的 shard/resume；严格聚合器只有在 1442 tuple 双射闭合后才会输出 L2 汇总。

在正式 1442-run 前仍必须：

1. 独立审阅者复核预算、候选实现、批次谱系、分片互斥和续跑行为；
2. 完成一次受控的多 shard 扩展 MVT，确认 N=32/64 性能不会使正式批次失控；
3. 正式 L2 完成后，从该批次选择真实 parent 并执行预登记的 L3/L4 子运行；四类消融 adapter 已实现作用性测试，但 L3/L4 当前仍为 `NOT_RUN`；
4. 只有 L2/L3/L4 均闭合后才能生成最终 winner 与 model-results freeze。

搜索接受与完整 sweep 的 patience 更新现由 `independent_search_score` 独立稠密路径完成，不调用生产 `_objective`。q2-c1 在每个右到左递归深度实际展开并保留 8 个 chain states。

Q5 的精确 Gaussian 整数格证书使用正确下界 `min(r,1-r)`、`r=1/sqrt(N)`。证书短路是默认关闭的 readiness-only 开关；正式入口在缺少冻结协议变更时直接拒绝。因此当前冻结正式计划仍保留全部 825 个 Q5 tuple/seed，并不擅自用证明替换候选运行。

因此本里程碑的 smoke 数值只能证明接口、约束、持久化和独立复算链路可工作，不能用于论文中的模型优胜结论。
