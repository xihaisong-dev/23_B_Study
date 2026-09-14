# 2023 华为杯 B 题协作仓库

本仓库用于研究“DFT 类矩阵的整数分解逼近”。工作流采用三个独立 Agent 工作树，主分支只负责集成。

## 三条工作泳道

| Agent | 分支 | 独占目录 |
| --- | --- | --- |
| 建模 | `agent/modeling` | `01_problem/`、`02_retrieval/`、`03_model/` |
| 计算 | `agent/compute` | `04_code/`、`05_results/` |
| 论文验收 | `agent/paper` | `06_paper/`、`07_review/` |

协作规则、交接格式和物理路径见 `00_admin/TEAM.md`。任何进入论文的数值都必须追溯到冻结结果，不能在论文分支手工改写。
