# Agent 仓库规则

## 唯一事实源

`00_admin/workflow.json` 是机器状态源。题面、规则、模型协议、实验结果和论文必须沿既定目录传递，禁止另建同义副本。

## 分支和写入边界

- `agent/modeling` 只写 `01_problem/`、`02_retrieval/`、`03_model/`，以及自己的 handoff/proposals。
- `agent/compute` 只写 `04_code/`、`05_results/`，以及自己的 handoff/proposals。
- `agent/paper` 只写 `06_paper/`、`07_review/`，以及自己的 handoff/proposals。
- 同一角色的临时分支只能使用 `agent/modeling-*`、`agent/compute-*` 或 `agent/paper-*`；它们继承对应角色的相同写入边界。其他未知 `agent/*` 分支拒绝提交。
- `main` 只用于集成。工作 Agent 不得直接提交到 `main`。
- `01_problem/original/` 只读，任何角色都不得修改。

仓库的 `.githooks/pre-commit` 会检查上述边界，包括删除操作。不要使用 `--no-verify` 绕过；需要跨目录改变接口时，在自己的 proposals 目录提交提案，由集成者裁决。

## 交接和证据

每次交接必须写明角色、分支、提交哈希、输入版本/哈希、命令、run-id、产物路径、测试与门禁结果、限制、接口影响、下一步和接收人。没有实际运行就不能报告数值改善。

正式流程必须依次满足题面规则冻结、检索、协议冻结、候选对擂、结果冻结、论文冻结和最终验收；`FAIL`、`BLOCKED`、`NOT_RUN` 均不得当作通过。
