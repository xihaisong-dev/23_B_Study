# AI 辅助开发统一声明（D-011）

## 工具身份

- 工具名称：OpenAI Codex desktop。
- 版本/型号：GPT-5 系列桌面 Agent；宿主未披露精确部署版本号。
- 开发机构/公司：OpenAI。
- 版本发布日期：宿主未披露精确部署版本的发布日期；本项目不以推测日期代替事实，缺失情况同步记录于 `00_admin/AI_USE_LOG.md`。

## 本里程碑的 AI 辅助范围

AI 根据冻结的 `03_model/tournament_protocol.json`、D-005、D-007、D-011 和 `3coding-visual` 约束，辅助实现：冻结门禁、L0 数学/输入检查、q1--q5 确定性 baseline、稀疏因子持久化、独立复算、run manifest 与部分结果汇总。AI 未实现或运行挑战者，未选择最终胜者，未改写冻结协议。

任务输入的实质摘要为：仅在 `agent/compute` 独立 worktree 内，通过协议冻结校验后，为所有正式 Python 程序增加 AI 文件头，完成 L0 和全部确定性 baseline，使用新 run-id 保存完整谱系与失败记录；不运行挑战者，不把总状态写成 PASS。

## 后处理和人工复核要求

1. 所有 Python 文件头使用同一四项工具身份口径，并说明对应人工核验措施。
2. 正式运行前须同时通过 `workflow_guard.py verify-freeze --stage tournament_protocol` 和 `04_code/scripts/validate_protocol.py`。
3. 题面输入重新计算 SHA-256；目标的单位化、零基索引、Kronecker 定义、因子顺序、Pq、行支持、K/L/C 和支持下界由 L0 检查。
4. 每个 baseline 输出先写入独立因子文件，再由不导入搜索乘积/RMSE函数的路径重新加载并复算；搜索/复算 RMSE 差须不超过 `1e-10`。
5. 全部代码由单元测试、Python 编译检查和 `git diff --check` 验证；队长仍须审阅算法口径、失败记录及论文披露，AI 输出不能替代最终人工责任。

## 已知边界

当前目标来自 D-010 在 practice profile 授权的 `third_party_copy`，不是主办方服务器原始 ZIP/MD5。baseline 只建立 L1 参考线，不证明 q2--q5 全局最优；`metrics.json` 和 `tournament.json` 在挑战者、稳健性和消融完成前必须保持 `BLOCKED`。
