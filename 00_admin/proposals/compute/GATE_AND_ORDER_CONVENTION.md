# 计算端失败关闭门禁与乘积顺序约定（提案）

- 角色：E 计算 Agent（`agent/compute`）
- 状态：`PROPOSED`（非冻结；请集成者裁决后并入 `00_admin/DECISIONS.md`）
- 关联：`04_code/src/dft_integer_approx/protocol_gate.py`、`04_code/src/dft_integer_approx/targets.py`

## 1. 失败关闭门禁的冻结前置条件

`protocol_gate.check_frozen` 仅当以下三条**同时**满足才 `allowed=True`，否则返回非零退出码拒绝，绝不降级运行：

1. `03_model/tournament_protocol.json` 的 `status == "FROZEN"`；
2. 该协议的 `problems` 非空；
3. `00_admin/freezes/tournament_protocol.json` 存在且其 `status == "FROZEN"`。

**来源**：`FROZEN` token 出自 `00_admin/proposals/modeling/TOURNAMENT_PROTOCOL_FREEZE_PACKET.md`（"status（冻结时为 FROZEN）"）；冻结文件路径出自先前 compute 交接中 `workflow_guard.py verify-freeze --stage tournament_protocol` 的失败信息（"唯一错误为缺少 `00_admin/freezes/tournament_protocol.json`"）。

**请求裁决**：门禁目前不校验「协议与冻结文件哈希一致」，也不校验 `problems` 内部 schema（候选/种子/预算/容差/平局）。这两项是否必须由计算端门禁在放行前自行校验，还是由集成者的 `verify-freeze` 统一负责，需在 `DECISIONS.md` 落盘。在裁决前，门禁只做上述三条保守检查，其余交给上游冻结门禁。

## 2. 乘积顺序约定（可能静默出错的跨泳道接口）

题面式 (6) 写作 `A_1 A_2 ... A_K`，即**左起优先**矩阵乘积。本仓库存在两种读法，且会得到不同的数值结果：

| 读法 | 定义 | 当前使用者 |
| --- | --- | --- |
| 左起优先 | `product([A1,..,AK]) = A1 @ A2 @ ... @ AK` | 本题面式 (6)、`V6_VALIDATOR_SPEC.md` §4.2、本包 `targets.product` |
| 应用顺序 | `chain([A1,..,AK]) = AK @ ... @ A1`（A1 先作用于向量） | `03_model/checks/verify_row_bound.py` 的 `chain` |

两者在 `K ≥ 2` 且因子不可交换时结果不同。当前两者各自一致（建模证书用 `chain`，验证层规格用左起优先），但**一旦用建模脚本的 `chain` 结果去校验验证层按 `product` 复算的 RMSE，会系统性不一致**。

**请求裁决**：在冻结协议中显式声明 `product_order = "leftmost_first" | "application_order"`，并规定独立复算路径与验证层必须使用同一约定（或显式声明换算关系）。在裁决前，本包 `targets.product` 采用左起优先，建模脚本 `chain` 保持应用顺序，二者不得互作校验基准；`rmse_recompute_independent` 必须与主 RMSE 同序。

## 3. 建议

- 在 `DECISIONS.md` 新增条目（如 D-007）记录上述两项裁决。
- 冻结 `tournament_protocol.json` 时加入 `product_order` 字段，计算端 `contracts`/`runner` 读取该字段而非硬编码。
