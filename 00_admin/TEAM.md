# 三 Agent 协作与仓库隔离

`main` 是唯一集成分支，由当前主控或仓库所有者执行合并；它不是第四个工作 Agent。三个工作 Agent 必须在各自的 worktree 和分支中工作，不得直接切换到其他 Agent 分支，也不得跨目录写入。

| Agent | 分支 | 本地 worktree | 独占范围 | 当前职责 |
| --- | --- | --- | --- | --- |
| M 建模 | `agent/modeling` | `../worktrees/modeling` | `01_problem/`、`02_retrieval/`、`03_model/` | 题意审计、证据检索、候选模型、对擂协议 |
| E 计算 | `agent/compute` | `../worktrees/compute` | `04_code/`、`05_results/` | 公平实现候选、测试、实验谱系、指标与图表数据 |
| W 论文验收 | `agent/paper` | `../worktrees/paper` | `06_paper/`、`07_review/` | 论文、引用、复现检查、编译和逐页验收 |

## 共享区规则

- `00_admin/` 只由集成者维护；每个 Agent 只能修改自己的 `00_admin/handoffs/<role>.md` 和 `00_admin/proposals/<role>/`。
- `01_problem/original/` 永远只读。发现题面问题时写提案，不直接改原文。
- 建模 Agent 冻结 `tournament_protocol.json` 后，计算 Agent 才能进行正式对擂。
- 模型结果冻结后，论文 Agent 才能引用正式数值；未冻结结果只能标为探索性结果。
- Agent 完成一个交接单元后提交并推送自己的分支，随后在交接文件中给出提交哈希。只有集成者可以合并到 `main`。

## 合并顺序

1. `agent/modeling`：先合并题意、检索和冻结的对擂协议。
2. `agent/compute`：在同步最新 `main` 后运行并提交代码、测试与结果。
3. `agent/paper`：在同步冻结结果后完成论文和验收。

禁止三个 Agent 互相 cherry-pick 未经集成的提交。共享接口变化先写入各自 proposals，由集成者记录到 `DECISIONS.md` 后统一落盘。
