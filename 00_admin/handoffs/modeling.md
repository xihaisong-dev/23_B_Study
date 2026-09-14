# 建模 Agent 交接

## 当前交接：`03_model/checks/` 来源审计与证书修订

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
