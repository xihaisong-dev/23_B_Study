# 建模 Agent 交接

## 当前交接：Q5 高斯整数格全局不可行性证书

- 角色：M 建模 Agent
- 状态：数学证书与机器复核 `PASS`；结论限定于冻结注册实例
- 工作树/分支：`C:/Users/Lenovo/Desktop/华为杯-数模/23年B/worktrees/modeling`，`agent/modeling`
- 证书提交：`dcdb1319ce7338ca0a07b6a1457758cdd26f2836`（本交接记录为其后一独立提交）
- 输入版本/哈希：题面 DOCX `c71b8b1273f008d3d0dbee0cc91b351421ebcd2885945e3277488f692c064841`；冻结协议 `c253df797845cfff4f24cdcd7da579ed841e487c36bb678cc92a8ebd60457592`，与 `00_admin/freezes/tournament_protocol.json` 绑定值一致；语义依据为 D-005/D-007/D-012
- 命令/run-id：`python -X utf8 03_model/checks/verify_q5_gaussian_integer_infeasibility.py`；`workflow_guard.py verify-freeze --stage problem`；`workflow_guard.py verify-freeze --stage tournament_protocol`；`git diff --check`；run-id `N/A`（建模证书，非正式实验）
- 产物：
  - `03_model/Q5_GAUSSIAN_INTEGER_INFEASIBILITY.md`，SHA-256 `5969af3c6b7759c719a8fbbaf8f5d394d54187cf9a0c7ba462cff00b015c4313`
  - `03_model/checks/verify_q5_gaussian_integer_infeasibility.py`，纯标准库，SHA-256 `8ea7d6b55539426c44f13d5b5d43d27a3f19b388da5050984a65d5d6f1012143`
  - `03_model/checks/q5_gaussian_integer_infeasibility.json`，SHA-256 `6350a9b7c73bfadcb08f22fac79d616b2c595ceef94b3511aef316a41da9ea18`
- 证明结论：`P_q` 的实虚部均为整数，故任意有限因子乘积逐项属于高斯整数环 `Z[i]`，右置换只重排列，仍属于 `Z[i]`。单位化 DFT 每项模为 `1/sqrt(N)`，所以任一合法乘积满足 `RMSE >= d_N=min(1/sqrt(N),1-1/sqrt(N))`。冻结 `N=[2,4,8,16,32,64]` 的下界分别为约 `0.292893、0.5、0.353553、0.25、0.176777、0.125`，均严格大于 `0.1`；六个注册实例对任意 `q/K/候选/种子` 全局不可行。
- 机器验证：脚本从 DOCX XML 核对约束 2、Q5 和阈值原文，核对协议冻结哈希/大小，枚举 `q=1..4` 字母表的加乘闭包，执行 2×2 矩阵乘积/右置换 sanity check，并对六个 DFT 的全部 5,460 个元素枚举邻近高斯整数；输出 `status=PASS`、`failed_checks=[]`、最弱界 `0.125`。两级 freeze verify 与 `git diff --check` 均 `PASS`。
- 冻结边界：未修改 `01_problem/original`、`03_model/ANALYSIS_MODELING_REPORT.md`、`03_model/tournament_protocol.json` 或冻结清单；不替换协议冻结。证书属于 `modeling_certificate`、`formal_experiment=false`，不是 L1–L4 run。
- 适用限制：题面无限族不能全部判为不可行；`N>=128` 时本界不超过 `0.1`，且零乘积已有 `RMSE=1/sqrt(N)<=0.1`。因此论文只能称“冻结六尺寸的全局不可行”。
- 接口影响/下一步：主 Agent 应把 Q5 的正式赢家保持为 `null`，不得伪造可行 run。若要用此证书短路冻结协议要求的完整 Q5 搜索，或让当前门禁接受“经证明无可行赢家”，必须按正式变更流程更新运行/门禁规则并重走受影响冻结；本提交本身没有越权修改协议。接收人：主 Agent、计算 Agent、论文 Agent。

## 当前交接：下界证书审计（D-012 冻结后的只读复算）

- 角色：M 建模 Agent
- 状态：审计 `PASS`；结论为否定性（记录哪些下界不可用）
- 工作树/分支：`C:/Users/Lenovo/Desktop/华为杯-数模/23年B/worktrees/modeling`，`agent/modeling`
- 基线：`main` = `a8ad6cf`（`workflow: adopt AI proxy and freeze tournament protocol`，D-012 已把题面与协议冻结、`phase=PROTOCOL_FROZEN`）
- 前置裁决：D-005（`β=1`、单位化 DFT、`RMSE=‖F−P‖_F/N`）、D-007（`A1@…@AK`）、D-010/D-011（practice 题面与 AI 代理规则）、D-012（冻结）
- 命令/run-id：`python -X utf8 03_model/checks/{verify_row_bound,verify_row_bound_audit,verify_structural_bounds,verify_row_relaxation_bounds}.py`，四者退出码均为 0；run-id `N/A`（建模证书，非正式实验）
- 产物路径：
  - `03_model/BOUND_AVAILABILITY_AUDIT.md`（本轮主报告）
  - `03_model/checks/verify_row_bound_audit.py` + `row_bound_audit_results.json`：冻结清单哈希/大小/依赖与协议 `kbrefs` 行号的**只读**审计
  - `03_model/checks/verify_structural_bounds.py` + `structural_bounds_results.json`：结构不等式核验与证伪
  - `03_model/checks/verify_row_relaxation_bounds.py` + `row_relaxation_bounds.json`：下界可用性审计
  - `03_model/checks/README.md`（更新文件清单与证据边界）
- 验证：
  - 冻结完整性（独立复算）：`00_admin/freezes/{problem,tournament_protocol}.json` 为 `PASS`，全部文件 SHA-256 与大小与磁盘一致，依赖链一致，冻结清单确实绑定 `03_model/tournament_protocol.json`；协议 `PASS/frozen=true`、5 问 × 3 候选、25 条 `kbrefs` 全部行号未越界；检索清单 `PASS`、7 条 KB 路径全部存在
  - 冻结产物未被改动：`verify_row_bound.py`、`tournament_protocol.json`、`ANALYSIS_MODELING_REPORT.md`、`retrieval_manifest.json` 的哈希在冻结清单中仍为 `OK`
  - 四个脚本退出码 0；`git diff --check` 与 pre-commit 边界检查通过
- 关键结论：
  1. 行支持传播成立；经典支持下界 `sqrt(N − min(N,2^K))/N`（`β=1`）是本项目**唯一**非平凡的严格下界，`2^K ≥ N` 时退化为 0。
  2. **列支持传播被证伪**（`N=16, K=2` 实测列支持 12 > 曾猜的 cap 4）；计数式收紧与支持界同源，永不更强。
  3. **系数幅值证书平凡**：`cap2 = 2·m_q ≥ 2√2 > 1/√N`，在所有注册实例上不激活（`certificate_a_active_cases = []`）。
  4. 后果：q2 **没有任何下界**；q3/q4/q5 仅 `K ≤ 4`（`N=32`）与 `K ≤ 4`（`N=64`）被排除；`K ≥ log2(N)` 之后无证书，故论文的 q2–q5 结果只能是 `best_found`，问题 5 不得声称 `K*=5` 已证明。
- 限制：本审计只做下界可用性判定，未运行任何候选搜索；不改变冻结协议；未写入 `05_results/`；`tournament`/`model-results` 门禁不受影响（仍为 `FAIL`，等待对擂）。
- 接口影响：给计算 Agent 的可用剪枝是"`N=32` 的 q3/q4 与 `N=64` 的 q5 可跳过 `K ≤ 4`"；给论文 Agent 的措辞边界见报告第 6 节。
- 下一步/接收人：主 Agent 审核并集成本提交；计算 Agent 在此边界内执行 L0–L4；论文 Agent 在结果冻结前不得引用任何 `best_found` 之外的措辞。

## 历史交接：D-005 后对擂准备稿（协议草案 + 检索清单 + 分析报告）

- 角色：M 建模 Agent
- 状态：产物已提交；正式门禁仍 `BLOCKED`（协议 `PROPOSED`，未冻结）
- 工作树/分支：`C:/Users/Lenovo/Desktop/华为杯-数模/23年B/worktrees/modeling`，`agent/modeling`
- 语义依据：`00_admin/DECISIONS.md` D-005（固定 `β=1` 且不计入 `L`；Q5 先 `RMSE≤0.1` 再按 `(C,K,RMSE)` 字典序、`q` 非平局目标；式 (3) 单位化 DFT；`q∈Z≥1`、`P_q={0,±2^r}`、`L` 为逐层作用向量的非平凡乘法位置数且不共享；所有扩张支撑的 `N×N` 层计入 `K`、纯排列单列）与 D-006（题面文本交叉核验）
- 基线：`4d245919f2d835a25efe0fbd5909eac1334f137f`（已含 `main` = `ac89420`）
- 命令/run-id：仅执行文件读取、KB 路径解析检查、JSON 结构检查、`git diff --check` 与 pre-commit 边界检查；**未运行任何候选或评分命令**，run-id `NOT_RUN`
- 产物路径：
  - `03_model/tournament_protocol.json`（34,222 bytes）：`status=BLOCKED`、`proposal_status=PROPOSED`、`frozen=false`；`blocked_by` 列明四条；五问各 3 个候选（1 基线 + 2 挑战者），含实例网格、种子策略 17/43/71、分段预算 60/300/900/1800 s、统一平局与失败/回退规则、L0–L4 验证层级
  - `02_retrieval/retrieval_manifest.json`（14,398 bytes）：顶层 `status=PASS`、`kb=PASS`，五问各 3 篇文献
  - `02_retrieval/EVIDENCE_MATRIX.md`（4,938 bytes）
  - `02_retrieval/CANDIDATE_SPECS.md`（一致性更新）
  - `03_model/ANALYSIS_MODELING_REPORT.md`（7,915 bytes）：`DRAFT / BLOCKED`
- 验证：5 个路径全部落在建模授权范围内；`retrieval_manifest.json` 引用的所有 `knowledge_base/` 路径均可解析；JSON 均可解析；草案已吸收 `5992431` 的修正（明确要求"缩放后的 `L` 必须重新计，不能沿用未缩放链数字"），未残留已作废的 `K=t+1`/`β=1/√N` 归属声明
- 限制：本轮**未核验** `knowledge_base/` 论文与 `PROBLEM_STATEMENT_AUDIT.md` 中文献引用的语义一致性（仅验证路径与结构）；协议未冻结，不得作为对擂依据；`blocked_by` 中的四项阻断（`rules.json` 的 AI 政策、`input_manifest` 官方来源、`freezes/problem.json` 缺失、`rules.json` 顶层 `BLOCKED`）本轮未被解除
- 接口影响：计算 Agent 仍不得开始正式对擂；`04_code/` 只允许做冻结前的脚手架（见 `agent/compute` 的 `e1f4194`）
- 更正说明：本文件旧"当前交接"段落曾写"`L` 计数、正负共享、`β` 是否计复杂度仍待语义裁决"，该表述已被 D-005 取代——`β=1` 且不计入 `L`、`L` 按位置计数且不共享已由 D-005 固定；仅"物理乘法器共享口径"仍作为需重算 `C` 的前提记录在 `ROW_BOUND_THEORY.md` 第 3 节
- 下一步/接收人：主 Agent 审核并集成本提交；解阻 `rules.json`/`input_manifest`/`problem freeze` 后，由建模 Agent 冻结 `03_model/tournament_protocol.json`，之后计算 Agent 方可进入 L1–L4

## 历史交接：`03_model/checks/` 来源审计与证书修订

- 角色：M 建模 Agent
- 状态：建模复算 `PASS`；正式门禁仍 `BLOCKED / NOT_RUN`
- 工作树/分支：`C:/Users/Lenovo/Desktop/华为杯-数模/23年B/worktrees/modeling`，`agent/modeling`
- 来源：`03_model/checks/` 最初由提交 `80ec0bd8365f76aa8e035680140516de8c05b23d` 加入，确属 V6 材料相关的建模核验，不是临时残留；本轮基线为 `5ba5736a0cf4afec7ee478348a7529d93e048e19`
- 修订提交：`59924310c6a9e92a2522d4b43e7a337757f1094c`
- 命令/run-id：`python -X utf8 03_model/checks/verify_row_bound.py`；run-id `N/A`（建模证书，不是正式实验）
- 产物：`03_model/checks/README.md`、`verify_row_bound.py`、`row_bound_results.json`，以及一致性修订后的 `03_model/ROW_BOUND_THEORY.md`、`01_problem/PROBLEM_STATEMENT_AUDIT.md`、`02_retrieval/CANDIDATE_SPECS.md`
- 验证：退出码 0；12/12 检查 `PASS`；JSON `status=PASS`、`failed_checks=[]`；JSON 记录的脚本 SHA-256 与当前脚本一致；`git diff --check` 与 pre-commit 边界检查通过；没有 `__pycache__` 或 `*.pyc`
- 修订摘要：使用容差识别免费根，避免把近似 `±j` 误计入 `L`；不再对缩放后因子沿用未缩放 `L`；修正式 (5) 的 `A2` 转录并撤回秩亏结论；把比特反转吸收进首层后，非零精确 radix-2 构造为 `K=log2(N)`、`β=√N`，`N=2..64` 的 `L` 位置数为 `0,0,4,20,68,196`。
- 限制：`L` 位置计数、正负共享和 `β` 是否计复杂度仍待语义裁决；式 (5) 只核对提取稿印刷顺序；V5/V6 仍缺因子、源码和日志。JSON 是 `formal_experiment=false` 的建模检查，不是正式结果。
- 接口影响：旧提交 `80ec0bd` 与旧 handoff 中的 `K=t+1`、`β=1/√N`、`L=0,2,10,34,98,258`、式 (5) 秩亏/240 顺序枚举均已作废，不得引用。
- 下一步/接收人：主 Agent 合并 `5992431`；正式候选、协议和结果仍须等待语义裁决与检索门禁。

## 历史交接：行二稀疏 DFT 分解（已由 `5992431` 修订，以下旧数值不得引用）

- 角色：M 建模 Agent
- 状态：建模交付完成（可复算结论 `PASS`）；正式对擂协议仍 `BLOCKED / NOT_RUN`
- 工作树：`C:/Users/Lenovo/Desktop/华为杯-数模/23年B/worktrees/modeling`
- 分支：`agent/modeling`
- 主分支同步：本轮开始与结束时 `git merge main` 均为 `Already up to date`；同步时 `main` 为 `927a633de2b14f2d7ca1501378d265a175070c31`
- 输入版本与哈希：
  - 本轮基线提交 `3c586e0`（其内容提交为 `c3bd76de7c3288bd7695eb77997878fa0739a418`）
  - 题面 DOCX SHA-256 `c71b8b1273f008d3d0dbee0cc91b351421ebcd2885945e3277488f692c064841`
  - 用户 README SHA-256 `ba53f44660d951dbef5d0b1545e25e7449ca4f59e711aed83aba3b652a94fef8`
  - `03_model/tournament_protocol.json` 本轮**未修改**，保持 `status = "NOT_RUN"`、`problems = []`
- 内容提交哈希：`80ec0bd8365f76aa8e035680140516de8c05b23d`（已推送到 `origin/agent/modeling`；上游同步提交 `4edcc47cc88681bb2c4d16ca922bc6c6aa87f81b` 由主 Agent 侧产生并已随本次推送一并上远端）
- 前序交接提交：`3c586e0`（内容提交 `c3bd76de7c3288bd7695eb77997878fa0739a418`）
- 命令与 run-id：
  - `cd 03_model/checks && python verify_row_bound.py`（退出码 0；纯标准库，无第三方依赖）
  - `git merge main`、`git diff --check`、pre-commit 边界检查
  - run-id：`N/A`（本轮为建模证书与精确构造复算，未产生搜索/实验 run；计算 Agent 的正式 run-id 在协议冻结后由 `04_code/` 产出）
- 产物路径：
  - `03_model/ROW_BOUND_THEORY.md`（可证明结论与精确构造）
  - `03_model/checks/verify_row_bound.py`（证书与构造复算脚本，纯标准库）
  - `03_model/checks/row_bound_results.json`（全精度机器可读结果）
  - `01_problem/PROBLEM_STATEMENT_AUDIT.md`（题面可复算审计补充）
  - `02_retrieval/CANDIDATE_SPECS.md`（候选规格与对擂接口草案）
  - `00_admin/proposals/modeling/TOURNAMENT_PROTOCOL_FREEZE_PACKET.md`（冻结包准备件）

### 本轮可复算的主要结论

1. **精确构造（问题 1）**：对 `N = 2^t`，比特反转排列 + `t` 个 radix-2 蝶形层，每个因子整体除以常数后乘积恰为 `βF_N`，`β = 1/√N`。
   实测 `N = 2…64` 全部 `max|chain − βF_N| ≤ 1.0e-15`、`RMSE < 2e-16`、每行支持 2、`K = t+1`；
   `L = 0, 2, 10, 34, 98, 258`（保守位置计数），`C(q=16) = 0, 32, 160, 544, 1568, 4128`。
   因此问题 1 在 `N ≤ 64` 上的最小误差为 0（构造给出可行解）。
2. **支持下界（`β = 1`）**：`(1/N)‖F_N − B‖_F ≥ sqrt(N − min(N,2^K))/N`，逐行精确计算版本对 `F_N` 与 `F_4⊗F_8` 均适用。
   `N=64`：`K≤4` 时 `0.108253 > 0.1`，`K=5` 时 `0.088388`；`K≥6` 时该界退化为 0。
3. **尺度退化（新增复算证据）**：`(𝒜, β) → (c𝒜, cβ)` 使残差同比例缩放，故式 (6) 关于 `(𝒜, β)` 下确界为 0。
   结论：README 的 `K* = 5`、`C* = 0` 只在一个显式固定的 `β` 口径下才有定义。
4. **题面式 (5) 不是精确恒等式（新发现）**：对 240 种因子顺序/排列读法逐一复算，最优读法的逐元素最大绝对误差仍为 `1.7678`（目标元素模长 `0.3536`）。式 (5) 自身用了 `≈`，故不构成题面错误，但不能作为精确 radix-8 构造引用。
5. **`F_4⊗F_8 ≠ F_32`（数值确认）**：两者最大逐元素差 `0.3536`；`F_4⊗F_8` 仍为酉矩阵且行模值恒为 `1/√32`。问题 4 必须以 `F_4⊗F_8` 构造目标。
6. **`P_q` 两种读法**：`{0,±2^r}` 与 `{0,±1,…,±2^{q-1}}` 在 `q=1,2` 相同、在 `q ≥ 3` 分叉；题面 `q=3` 示例只支持前者。

### 测试与门禁

| 检查 | 结果 |
| --- | --- |
| `python verify_row_bound.py` | `PASS`（退出码 0，全部断言/复算通过） |
| 目标矩阵自检（列正交、式 (1)/(3) 关系、`F_4⊗F_8` 酉性） | `PASS` |
| 精确构造逐元素复算（`N=2…64`） | `PASS`（`≤ 1.0e-15`） |
| 行支持传播随机复算（`N=16`，K=1..4） | `PASS` |
| 秩传播规则随机复算 | `PASS`（无违例；同时更正了"行二稀疏蕴涵秩 ≤ 2^K"这一错误命题） |
| 尺度退化复算 | `PASS`（残差按 `c` 线性缩放） |
| `git diff --check` | `PASS`（无空白错误） |
| 分支写入边界（pre-commit hook） | `PASS`（hook 实际执行通过；见下方"环境阻断"） |
| 推送到 `origin/agent/modeling` | `PASS`（`4edcc47..80ec0bd`） |
| `03_model/tournament_protocol.json` 未被改动 | `PASS`（`git diff 3c586e0 80ec0bd -- 03_model/tournament_protocol.json` 为空） |
| `01_problem/original/` 未被改动 | `PASS`（同上 diff 路径为空） |
| 题面规则冻结 / 检索 / 协议冻结 / 对擂 / 结果冻结 | `BLOCKED` / `NOT_RUN` / `NOT_RUN` / `NOT_RUN` / `NOT_RUN` |

### 环境阻断（本轮遇到并已解决，需主 Agent 知晓）

本会话的初始文件沙箱为 `workspace-write`，在其中：

- `git commit` **无法执行 pre-commit hook**：hook 是 bash 脚本，Git for Windows 需要用 bash 解释器启动它，而受限沙箱不允许创建命名管道，bash 立即以 `fatal error - couldn't create signal pipe, Win32 error 5` 退出（`git commit` 随之返回 128）。
- `git push`/`git fetch` 失败于 `schannel: AcquireCredentialsHandle failed: SEC_E_NO_CREDENTIALS`，受限沙箱读不到 HTTPS 凭证。

两次操作在获得更宽权限后成功（`commit_exit=0`、`push_exit=0`）。**未使用 `--no-verify`**：边界检查是真实执行的，不是被绕过的。当前会话的文件策略已放宽为 `danger-full-access` 且审批提示已关闭，后续交接应当可以直接提交与推送。

### 脚本自查（本轮修复的自身缺陷，留档以防误引）

`03_model/checks/verify_row_bound.py` 初稿存在两类**会产生错误数值**的实现缺陷，已在最终版本修正，并写进代码注释：

1. 列表推导式变量遮蔽函数参数（`dft_matrix`、`matmul`、`residual` 三处）：导致目标矩阵、矩阵乘法与残差在部分调用路径上被静默算错。
2. 对**已缩放**的因子统计 `L`：归一化常数使所有元素不再等于豁免集合 `{0,±1,±j}`，会把 `L` 放大数倍。最终版本只对未缩放的整数/单位根因子计数。

因此本文件与 `ROW_BOUND_THEORY.md` 中的数字均来自最终版本的一次完整运行；`row_bound_results.json` 含每个条目的原始数值，可逐项复核。

### 已知限制

- 未做网络检索，官方题面/规则未核验（`00_admin/rules.json` 仍 `BLOCKED`）；本轮结论只针对仓库内只读副本与提取稿。
- 问题 2/3/4 的**最优性**未做：只给出可行基准（精确构造）与 `β=1` 支持下界，未给出与下界匹配的离散可行解。
- 问题 5 在 `L = 0` 类内**没有下界证书**：用户 README 的 `N=64, q=1, K=5, RMSE≈0.0905` 仍为 `UNVERIFIED`（无因子、无代码、无日志）。
- 未证明"`K = t` 可达"或"`K ≥ t+1` 必要"；`t` 只是本轮构造所用的值。
- 未执行任何第三方代码；未产生正式 `05_results/` 结果。

### 接口影响（对计算 Agent 与主 Agent）

- 计算 Agent 可直接使用的输入：`03_model/checks/verify_row_bound.py` 中的 `dft_matrix` / `kron` / `residual` 可作为独立复算参照；`row_bound_results.json` 的 `t4_exact_construction` 给出每个尺寸的 `K`、`β`、`L`、`C` 与精确性证据。
- 计算 Agent 不得在协议冻结前开展正式对擂；输出契约见 `02_retrieval/CANDIDATE_SPECS.md` 第 1 节。
- 需要在 `00_admin/DECISIONS.md` 落盘的裁决：`V6_SEMANTIC_DECISIONS.md` 的 D1–D5（尤其 D1 的 `β` 口径与 D4 的 `L`/`q` 口径），以及本轮新增的两条题面问题（式 (5) 精确性、`P_q` 读法）。

### 下一步与接收人

1. **主 Agent（接收人）**：审核本交接；把 D1–D5 裁决与式 (5)/`P_q` 的题面问题写入 `00_admin/DECISIONS.md`；裁决后通知建模 Agent 冻结 `03_model/tournament_protocol.json`（准备件见 `00_admin/proposals/modeling/TOURNAMENT_PROTOCOL_FREEZE_PACKET.md`）。
2. **用户**：对 `V6_SEMANTIC_DECISIONS.md` D1–D6 作出选择；若选 D6 选项 1，请提供 V5 NPZ 与 V1–V6 源码包。
3. **计算 Agent**：按 `02_retrieval/CANDIDATE_SPECS.md` 实现输出契约与候选 C1/C2/C3；用 `verify_row_bound.py` 做独立复算；在协议冻结前不写正式结果。
4. **建模 Agent（下一轮，仅在被授权后）**：冻结 `tournament_protocol.json`；为问题 2/3/4 补充分布式最优性下界（当前缺失）。

## 历史交接：用户 V6 模型材料审计

- 状态：审计交付已完成；语义与工程复现 `BLOCKED`
- 内容提交哈希：`c3bd76de7c3288bd7695eb77997878fa0739a418`
- 产物路径：`03_model/incoming/README_LATEST_V6.md`、`03_model/USER_MODEL_AUDIT.md`、`00_admin/proposals/modeling/V6_SEMANTIC_DECISIONS.md`
- 摘要：行二稀疏支持上界 `2^K`、`β=1` 下的 `√(N−2^K)/N` 下界、`N=64` 的 K=4/K=5 算术可复核；`C*=0`、`K*=5`、V4–V6 全部数值为 `UNVERIFIED`。
- 本轮更新：为该交接补上了尺度退化的**新复算证据**（残差按 `c` 线性缩放），并把"秩 ≤ 2^K"这一错误命题从建模结论中移除。

## 历史交接：题面启动审计

- 内容提交：`4c5baecdc3ae2aee86fd5ae69e0c1364b94022d3`
- Handoff 提交：`e161813446542e68c89798bc12285367ca2a85a0`
- 产物：`01_problem/PROBLEM_BRIEF.md`、`01_problem/DATA_AUDIT.md`
- 状态：已由主分支集成；官方题面来源与关键语义仍待核验。
