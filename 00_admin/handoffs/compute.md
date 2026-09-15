# 计算 Agent 交接

## 当前交接：对擂结果聚合与 `model_results` 冻结（隔离分支）

- 角色：E 计算 Agent（本轮为「聚合 + 冻结」阶段，由总控/用户授权在隔离分支执行）
- 状态：聚合与冻结已完成、已提交、已推送；门禁 `tournament` / `model-results` 仍为 `FAIL`，唯一错误是**已证明的数学冲突**，需集成者裁决（见「阻塞项」）。本轮**不主张任何改进**。
- 分支 / 提交：`agent/compute-tournament` = `adf187e6490af2f9a5f4a63021bab2a5aeaab31d`（父提交 `72e2df0`），已推送 `origin/agent/compute-tournament`
- 输入版本与哈希：
  - `03_model/tournament_protocol.json` SHA-256 `c253df797845cfff4f24cdcd7da579ed841e487c36bb678cc92a8ebd60457592`（本分支未改动）
  - `00_admin/freezes/tournament_protocol.json` SHA-256 `b97a9a31e36cea7d58ee9559c7dd90ac7f97fa9b0359594844e781cec5ba8b48`（作为 `model_results` freeze 的依赖写入）
  - 输入 run manifests：`05_results/runs/` 共 **1480** 个 run 目录（250 基线 + 1230 挑战者），全部已在库中（`git ls-files` 计数 5920 = 1480 × 4）
- 命令与 run-id：
  - `python -X utf8 04_code/scripts/normalise_line_endings.py`
  - `python -X utf8 04_code/scripts/freeze_model_results.py`
  - `python -X utf8 -m pytest 04_code -q` → `61 passed`
  - 门禁：`workflow_guard.py verify-freeze --workspace . --stage {problem,tournament_protocol,model_results}`；`workflow_guard.py check --workspace . --gate {rules-problem,retrieval,protocol,tournament,model-results}`
  - 本轮**不产生新 run-id**（只对已提交的 run manifests 做聚合，`metrics.run_count = 1480`）
- 产物路径：
  - `04_code/src/dft_integer_approx/aggregate_results.py`（折叠 run manifests → `metrics.json` + `tournament.json`）
  - `04_code/src/dft_integer_approx/robustness_ablation.py`（L3/L4）
  - `04_code/scripts/freeze_model_results.py`、`04_code/scripts/normalise_line_endings.py`
  - `05_results/metrics.json`、`05_results/tournament.json`、`05_results/l3_robustness.json`、`05_results/l4_ablation.json`、`05_results/RESULTS_REPORT.md`
  - `00_admin/freezes/model_results.json`（15 个文件绑定 + `tournament_protocol` 依赖）
- 聚合结果（`metrics.status = PASS`，`tournament.status = PASS`，逐问题 `robustness = PASS`、`ablation = PASS`）：
  - 状态分布：`PASS 764` / `INFEASIBLE 792` / `CONSTRAINT_FAIL 0`
  - q1 赢家 `q1-b0-scaled-radix2`，`RMSE 4.329780281177466e-17`（`N=2, K=1, q=16, L=4, C=64`）
  - q2 `q2-b0-onefactor-quantize` `0.17677669529663687`（`N=32, K=1, q=3`）
  - q3 `q3-b0-quantized-butterfly` `0.17677669529663687`（`N=32, K=5, q=3`）
  - q4 `q4-c1-generic-discrete` `0.18410230570528574`（`N=32, K=7, q=3`）
  - q5 `q5-b0-q1-butterfly` `0.125`（`N=64, K=1, q=1`），`winner_basis = best_structurally_valid_but_rmse_above_threshold`
- L3/L4 边界（状态取自**实测文件** `l3_robustness.json` / `l4_ablation.json`，非声明）：
  - L3：在**已记录**的三种子（17/43/71）run 上度量种子覆盖率、best/median/worst 离散度、因子结合顺序检查（`ASSOC_TOL = 1e-9`）；**未新增种子**
  - L4：组件开关级重跑（`no_hierarchical_init`、`no_support_reconnect`、`no_discrete_polish`、`fixed_butterfly_vs_reconnectable`），受 `--ablation-instances`（默认每问题 3 个）限制，**非全量覆盖**
- 本轮修复的自身缺陷（两处，均实测验证）：
  1. `io.open(..., newline="\n")` **不会**去掉文本中已存在的 `\r`——它只抑制写入时 `\n → os.linesep` 的转换。首版 `normalise_line_endings.py` 因此把 1236 个文件**按字节原样重写**，却汇报「已归一化 1236 个文件」。已改为按字节 `\r\n → \n` 重写并加幂等自检。修正后实际转换 1236 个文件，`git add` 后**未产生任何 blob 变更**（暂存 10 个交付文件，而非 1236 个）。
  2. `freeze_model_results.py` 原用 `Path.write_text(...)` 的默认换行写出，使 freeze 清单自身成为 CRLF。已改为 `newline="\n"`。
  - 实质影响：`workflow_guard.sha256()` 对**原始字节**取哈希（`path.open("rb")`），因此「按 CRLF 工作树字节算出」的清单在**全新检出**（等价地：本分支并入 `main` 后 git 以 `eol=lf` 写出文件）会哈希不匹配、`verify-freeze` 失败。修正后实测：用全新 worktree 检出 `adf187e`，绑定集合 CRLF 字节 = 0，`verify-freeze --stage model_results` = `PASS`，`check --gate tournament` 复现同一单错，1480 个 run manifest 全部在盘上（`missing = 0`）。
- 测试与门禁结果：
  - 单测 `61 passed`；`git diff --cached --check` 退出 0；暂存区无删除项
  - `verify-freeze`：`problem` `PASS`、`tournament_protocol` `PASS`、`model_results` `PASS`（且全新检出复测 `PASS`）
  - `check --gate`：`rules-problem` `PASS`、`retrieval` `PASS`、`protocol` `PASS`、`tournament` **`FAIL`（1 错）**、`model-results` **`FAIL`（同 1 错）**
- 已知限制：L3 未补新种子、L4 非全量覆盖；除 q5 外 q2–q5 均无已证明下界，只能按 `best_found` 表述；本轮未改动任何 run 产物与冻结协议
- 接口影响：`03_model/`、`05_results/runs/` 内既有产物均未修改，新增文件性变更全部在 compute 边界内。**唯一越界项**：`00_admin/freezes/model_results.json` 不在 `.githooks/pre-commit` 的 `compute:` 白名单内（白名单仅 `04_code/*`、`05_results/*`、`00_admin/handoffs/compute.md`、`00_admin/proposals/compute/*`）；该文件由 `workflow_guard` 的冻结流程产出。另注该钩子的 `case` 只识别 `agent/modeling|agent/compute|agent/paper` 三个规范分支名，对 `agent/compute-*` 临时分支一律 `exit 0`，即临时分支上写入边界**不被强制**。请集成者决定是否把 `00_admin/freezes/*` 纳入白名单。
- 阻塞项（需集成者裁决；我未做任何规避）：
  - `workflow_guard.check_tournament` 要求注册的 `winner_id` 存在 `status == "PASS"` **且** `constraints_status == "PASS"` 的 run；但 q5 在全部 6 个冻结实例上**可证不可行**（系数为高斯整数 ⇒ `RMSE ≥ d_64 = 1/8 = 0.125 > 0.1`），该子句因此**不可满足**。
  - 我**没有**放宽阈值、改状态名或伪造成可行解；`tournament.json` 对 q5 明确记录 `winner_basis = best_structurally_valid_but_rmse_above_threshold`。
  - 两个可选裁决：(a) 修改门禁语义，允许 q5 在「已证明不可行」时以文档化形式登记赢家；(b) 集成者明确接受「无可行赢家」，使 `check_tournament` 跳过该子句。二者均属跨目录接口变更，需由集成者/总控落盘到 `DECISIONS.md`。
- 下一步与接收人：接收人 = 总控/集成者。建议顺序：(1) 先裁决 q5 门禁语义；(2) 合并时注意 `00_admin/handoffs/compute.md` 与 `agent/compute-challengers`（`c8500b5`，13:02）在本文件顶部各有新增小节，可能产生冲突，需人工合并；(3) 合并后重跑 `verify-freeze` 与全部门禁，确认 `PASS`。

## 历史交接：L2 挑战者对擂执行完毕（隔离分支）

- 角色：E 计算 Agent
- 状态：对擂已执行（1230 runs）；结论为**挑战者在多数问题上未优于基线**，见下文；正式结果冻结仍由集成者执行
- 工作树 / 分支：`worktrees/compute-tournament` / `agent/compute-tournament`（从 `origin/agent/compute` 新建的**隔离**工作树，不改动并发会话正在使用的 `worktrees/compute` 与 `worktrees/compute-challengers`）
- 内容提交：`e50965b`（框架）、`4cbe36a`（设计记录）、`0854b83`（约束违规修复）、`90c2971`（对擂结果与报告）
- 基线提交：`origin/agent/compute` = `6d1d2691bc3fb3728d6ba5c6ec3733d906007455`
- 输入版本与哈希：
  - `03_model/tournament_protocol.json` SHA-256 `c253df797845cfff4f24cdcd7da579ed841e487c36bb678cc92a8ebd60457592`
  - `00_admin/freezes/tournament_protocol.json` SHA-256 `b97a9a31e36cea7d58ee9559c7dd90ac7f97fa9b0359594844e781cec5ba8b48`
  - 代码树 SHA-256 `c063379367cf248dc02668c13d6fa594628f33eaf451724fd956bc1edd52160a`
- 命令与 run-id：
  - `python -X utf8 04_code/scripts/run_challengers.py`（仓库根执行，门禁放行后才运行）
  - run-id 形如 `<UTC>__<问题>__<候选>__s<种子>__p<协议哈希8>__c<代码哈希8>`
- 产物路径：
  - `04_code/src/dft_integer_approx/challenger_core.py`、`challengers.py`、`formal_challenger_runner.py`
  - `04_code/scripts/run_challengers.py`、`04_code/CHALLENGER_NOTES.md`
  - `05_results/TOURNAMENT_REPORT.md`、`05_results/challenger_runs.json`
  - `05_results/runs/`：**1480** 个 run 目录（250 个基线保持原样 + 1230 个新增挑战者）
- 测试与门禁：
  - 门禁 `PASS`；单测 61/61 `OK`；`git diff --check` `PASS`；分支边界检查 `PASS`（全部改动落在 `04_code/` 与 `05_results/`）
  - 每个 run 都做独立复算：目标哈希、因子哈希、`L`/`C` 一致、`RMSE` 差 ≤ `1e-10`；约束 1/2 逐项检查
  - 状态分布：`PASS 438`、`INFEASIBLE 792`、`CONSTRAINT_FAIL 0`；墙钟 343 秒
- 结果摘要（与 `origin/agent/compute` 基线在同一 `(N,K,q)` 上比较）：
  - q1：6/6 **打平**（`RMSE ≤ 1.4e-15` 且 `L` 完全相同；该问题已有精确解，无改进空间）
  - q2：5/5 **打平**（整数格 `P_3` 与 `1/sqrt(N)` 量级目标使多因子无益）
  - q3：**更差 3/5**（0.353553→0.587086、0.250000→0.306186、0.176777→0.197328）
  - q4：**更好 1/1**（0.718391→0.188418，L 均为 0）——仅单实例，不作一般结论
  - q5：两侧均**无 `RMSE ≤ 0.1` 可行解**（基线最好 `0.125`、挑战者最好 `0.127178`），赢家为 `null`。
    主分支 `3dd246f` 的 `03_model/Q5_GAUSSIAN_INTEGER_INFEASIBILITY.md` 已证明冻结实例上 `RMSE ≥ d_N`，
    且 `d_64 = 1/8 = 0.125 > 0.1`。本分支**独立复算**了 `d_N`，并对高斯整数格在 `[-3,3]^2` 上暴力枚举最近格点，
    两者在小数第 10 位一致（`N=64` 均为 `0.1250000000`）。基线的最好值 `0.125000` **恰好等于** `d_64`（由全零乘积达到，`L=C=0`），
    因此 **q5 不存在改进空间**——`INFEASIBLE` 是定理的数值体现，不是搜索失败。
    边界：该证书只覆盖冻结的有限实例，**不外推到无限尺寸族**（`d_128 = 0.0884 < 0.1`），且依赖 D-005 固定 `beta = 1`。
  - **不主张任何改进**；论文引用须按 `best_found`/「无可行解」表述
- 本轮修复的自身缺陷：首次全量出现 714 个 `CONSTRAINT_FAIL`，源于 `_solve_row_support` 与 `continuous_factor_update` 在「格点投影塌缩为 0」时**回退返回未投影连续解**，把非格点值写入因子。已改为塌缩为 0（调用方只接受目标下降的更新，故合规且不退化），含非法因子的首批产物整体删除后从头重跑（提交 `0854b83`）。
- 已知限制：q3/q5 的搜索策略需重做（当前"解析支撑 + 块下降"不如基线的固定顺序坐标轮）；协议分段预算未强制中止；L3/L4 未实现；q2–q5 在 `K ≥ log2(N)` 后不存在已证明下界。
- 接口影响：仅新增文件，未修改冻结的 `03_model/` 与 `05_results/runs/` 中的基线产物；`05_results/runs/` 为纯新增（staged deletions = 0）。
- 下一步与接收人：主 Agent 审核并决定集成方式（建议：先取 `challengers.py`/`challenger_core.py` 与 `TOURNAMENT_REPORT.md`，挑战者搜索策略重做后再跑正式 L3/L4）；论文 Agent 只能引用 q1 精确值、q2/q3/q4 的 `best_found` 与 q5 的「无可行解」。

## 历史交接：启动计划

- 角色：E 计算 Agent
- 状态：启动计划已完成；正式对擂 `NOT_RUN`
- 工作树：`worktrees/compute`
- 分支：`agent/compute`
- 内容提交：`0b33f3ad6790ae79463162160c620b607e5927d9`
- 输入版本与哈希：
  - `00_admin/input_manifest.json` SHA-256 `4f7188fbdfb198f4c048c7d09575ade769ea99f4af2c03657f8217ec63142636`；其记录的题面 SHA-256 为 `c71b8b1273f008d3d0dbee0cc91b351421ebcd2885945e3277488f692c064841`，数据类别 `third_party_copy`、来源未核验。
  - `00_admin/semantic_contract.json` SHA-256 `495d256e6407cded994a59ebc52303c6295a59e67438b26debc0fe6ad40de3f7`，状态 `PASS`。
  - `03_model/tournament_protocol.json` SHA-256 `167635df24be6afdf40042345f2cd38995d03d5cde98047f29fc831bea302398`，状态 `NOT_RUN`、`problems` 为空。
- 命令与 run-id：仅执行文件读取、SHA-256 计算、`git diff --check` 和 Git 提交；未执行候选或评分命令，run-id 为 `NOT_RUN`。
- 产物路径：`04_code/IMPLEMENTATION_PLAN.md`，SHA-256 `b22f867f9ada007e34e3110583cbada99e74a177d6e29c73c6afb6c80600c1df`。
- 测试与门禁：`git diff --check` PASS；分支 pre-commit 写入边界检查 PASS。协议冻结门禁未运行，因当前协议尚未冻结；正式计算仍被阻断。
- 已知限制：本轮只交付实施计划，未创建候选实现、未运行测试套件、未产生或声称任何正式数值；题面官方来源仍未核验，协议仍未定义候选、指标、种子和预算。
- 接口影响：无现有机器接口变更；新文档仅约定未来的单向协议适配、统一候选输入/输出、谱系和复杂度测试要求，未修改 `03_model/tournament_protocol.json`。
- 下一步与接收人：交给总控/集成者审核并合并本启动产物。建模 Agent 完成候选协议冻结后，计算 Agent 应先同步最新 `main`、验证冻结哈希，再实现候选和运行对擂。

## V6 独立验证规格交接

- 角色/分支/工作树：E 计算 Agent；`agent/compute`；`worktrees/compute`。
- 同步状态：执行 `git merge --no-edit main` 返回 `Already up to date`；当前分支包含 `main` 提交 `927a633de2b14f2d7ca1501378d265a175070c31`。
- 内容提交：`66ecb3bd29adb92b46a27e8206fec3e5694eb4b2`。
- 输入版本与哈希：
  - 用户材料 `C:\Users\Lenovo\Downloads\README_LATEST_V6.md`，5,044 bytes，SHA-256 `ba53f44660d951dbef5d0b1545e25e7449ca4f59e711aed83aba3b652a94fef8`；仅作待验证模型材料，未执行其命令，未接受其数值声称。
  - `03_model/tournament_protocol.json` SHA-256 `167635df24be6afdf40042345f2cd38995d03d5cde98047f29fc831bea302398`；状态 `NOT_RUN`、`problems` 为空，且已知 freeze 校验失败。
  - `00_admin/input_manifest.json` SHA-256 `4f7188fbdfb198f4c048c7d09575ade769ea99f4af2c03657f8217ec63142636`；题面仍为未核验 `third_party_copy`。
  - `00_admin/semantic_contract.json` SHA-256 `495d256e6407cded994a59ebc52303c6295a59e67438b26debc0fe6ad40de3f7`。
- 命令与 run-id：仅执行 Git 同步/提交、文本只读审计、SHA-256 计算和 `git diff --check`；未运行 README 命令、候选、验证器或评分器，run-id 为 `NOT_RUN`。
- 产物：
  - `04_code/V6_VALIDATOR_SPEC.md`，SHA-256 `695400ab45962769c27aaef4388bcc2662e4a49f5928673b9beac536006528a6`。
  - `00_admin/proposals/compute/V6_REQUIRED_INPUTS.md`，SHA-256 `6fb42f008cf8c5c76296d41bee7cb3ac884d16b930c6438e1b524a233a3dd258`。
- 测试与门禁：`git diff --check` PASS；pre-commit 分支边界检查 PASS。已知协议 freeze 校验失败，因此正式实现/运行门禁为 `BLOCKED`，未将其当作 PASS。
- 已知限制：仓库中没有 V1–V6 源码、锁定 requirements、V5 factors NPZ、V6 原始日志/运行 manifest、完整种子/参数/环境。本轮未创建正式代码或任何 `05_results/` 产物，未生成或确认数值。
- 关键数学阻塞：不含 beta 的 `sqrt(N-2^K)/N` support 下界只在 `|beta|=1` 时精确成立，或在对全部可行解有 `|beta|>=1` 的权威统一约束时作为较弱下界；若 beta 可自由取 0，则正的 support 统一下界不成立。
- 接口影响：无现有代码/协议变更。新规格建议安全 NPZ schema、独立验证 API、beta/q/L 失败关闭和输入交付包；须由总控核对冻结协议后才能实施。
- 下一步与接收人：总控/集成者审核并合并本提交，收集 `V6_REQUIRED_INPUTS.md` 中 P0/P1 材料，交由建模 Agent 冻结 beta 域、字母表和 `l_semantics`。只有 freeze 校验 PASS 后才能返回计算 Agent 实现。

## D-005 接口对齐与 freeze 失败交接

- 角色/分支/工作树：E 计算 Agent；`agent/compute`；`worktrees/compute`。
- 同步：本轮开始时 `git merge --no-edit main` 已是最新；工作期间 `main` 追加 D-006 题面交叉核验后，再合并 `ac894208d23b93765c1b6212fa7767fd9c7c1628`，同步合并提交为 `8fc571e365d23a5d31c4a13a87aebcd87ef621d3`。
- 内容提交：`94eb06c2e5c41c3b23901181b9f9bd5968077fa0`。
- 输入版本与哈希：
  - `00_admin/DECISIONS.md` SHA-256 `4d34a5ce8e48161dff0dfb39fcbf506cbb084f0409ef7e56473652b489031679`；D-005 固定 beta/DFT/RMSE/q/K/L/排列口径并授权从头复现，D-006 仅提供题面内容交叉佐证。
  - `00_admin/semantic_contract.json` SHA-256 `bdbe1b5a454e1ba56d47201ff942f94844165e5550755cc4195af50da6f0cb62`。
  - `00_admin/input_manifest.json` SHA-256 `ff1d0a58ba424a53885980d0a91a734d984336c6c53f04bfea0ef9b191337875`；内容交叉佐证 PASS，但官方 ZIP/MD5 仍缺失，总状态仍 `BLOCKED`。
  - `03_model/tournament_protocol.json` SHA-256 `167635df24be6afdf40042345f2cd38995d03d5cde98047f29fc831bea302398`；状态 `NOT_RUN`、`problems` 为空。
- 门禁命令：`python -X utf8 C:\Users\Lenovo\.codex\skills\1start-mathmodel\scripts\workflow_guard.py verify-freeze --workspace . --stage tournament_protocol`。
- 门禁结果：`FAIL`，退出码 1，`checked_at=2026-09-14T15:49:55+00:00`，唯一错误为缺少 `00_admin/freezes/tournament_protocol.json`。依 `3coding-visual` 已停止正式实现和 runs。
- L0 环境预检：Python `3.14.6` AVAILABLE；pytest `9.1.1` AVAILABLE；NumPy MISSING；SciPy MISSING。未安装任何依赖，未执行矩阵/候选测试。
- 命令与 run-id：除 freeze 验证外，仅执行 Git 同步/提交、文本审计、环境版本可用性检查、SHA-256 和 `git diff --check`；无候选或正式运行，run-id 为 `NOT_RUN`。
- 产物：
  - `04_code/V6_VALIDATOR_SPEC.md`，SHA-256 `f9a7764e1698e17f58f6a2180f301284133b00ff4999690e12c6119df3898e01`；已按 D-005 替换可变 beta 接口，增加冻结配置、固定 beta=1、操作流 NPZ、run-id/validation-id、K/排列和对齐测试。
  - `00_admin/proposals/compute/V6_REQUIRED_INPUTS.md`，SHA-256 `abefce2cf0120a3afd3634c854f4527980d8366f1bfe7f811a6ba237bb761a39`；已将旧 V1–V6 包降为历史声称复现输入，不再作为从头实现前置。
- 测试：文档 `git diff --check` PASS；D-005 覆盖字段自检 PASS；pre-commit 边界检查 PASS。未运行 pytest，因为本轮无代码且 NumPy/SciPy 未安装。
- 结果边界：未创建/修改任何 `05_results/` 产物，未生成或声称任何候选 RMSE、改善、胜者或最优性数值。
- 接口影响：未改机器协议或现有代码。未来验证器以 D-005 为配置契约，只接受 beta=1；NPZ 用 factor/permutation operation stream 精确复原乘积，只有纯排列不计 K/L。
- 下一步与接收人：总控/建模 Agent 需完成候选、种子、预算、容差和失败规则，生成并验证 `tournament_protocol` freeze；总控同时需批准 Python 兼容范围和锁定依赖。只有 verify-freeze PASS 后才返回计算 Agent 开始正式实现。

## 预冻结计算端骨架与失败关闭门禁交接

- 角色/分支/工作树：E 计算 Agent；`agent/compute`；`D:/研究生资料/学习资料/数模/17`（本轮工作目录，非独立 worktree）。
- 同步：`git merge --no-edit main` 返回 `Already up to date`（`main` 已在分支历史内）。
- 内容提交：`e1f41946e061466979bbcaeaabd0597ce7e4dccb`。
- 基线：`7111a5af0f0619af4d2f81e1deabcebbaa8a8306`。
- 输入版本与哈希：
  - `03_model/tournament_protocol.json` SHA-256 `167635df24be6afdf40042345f2cd38995d03d5cde98047f29fc831bea302398`；状态 `NOT_RUN`、`problems` 为空，本轮未改动。
  - `00_admin/freezes/tournament_protocol.json` 缺失（本轮与先前 `verify-freeze` 门禁失败原因一致）。
  - `00_admin/semantic_contract.json`、`00_admin/DECISIONS.md`（含 D-005 固定 beta=1/单位化 DFT/RMSE/q/K/L 口径）作为已签署口径只读引用。
- 命令与 run-id：
  - `python -m unittest discover -s 04_code/tests -p "test_*.py"`：退出码 0，**49/49 PASS**。
  - `python 04_code/scripts/validate_protocol.py`：退出码 1，`allowed=false`，三条原因（status `NOT_RUN`、`problems` 空、缺 freeze 文件）。
  - `python 04_code/scripts/run_tournament.py`：退出码 1，拒绝运行。
  - `git diff --check`：PASS；pre-commit 边界检查：PASS（`core.hooksPath=.githooks`，未用 `--no-verify`）。
  - run-id：`NOT_RUN`（本轮无候选或正式实验）。
- 产物路径（`04_code/`，纯标准库、无第三方依赖）：
  - `README.md`、`pyproject.toml`；
  - `src/dft_integer_approx/`：`targets`（式 (1)/(3) DFT、Kronecker、左起优先 `product`）、`metrics`（`RMSE=||F-P||_F/N`，D-005 `beta=1`）、`hardware`（`L`/`C=qL`，精确免计数集合、失败关闭）、`constraints`（约束 1 行稀疏、约束 2 字母表 `P_q` 精确成员）、`serialization`/`hashing`（规范字节与内容哈希）、`contracts`（协议适配只读对象）、`candidate_api`（候选 Protocol + 结构化失败 + fake）、`provenance`（run-id/环境/manifest）、`protocol_gate`（失败关闭门禁）、`runner`（门禁优先唯一入口）；
  - `scripts/validate_protocol.py`、`scripts/run_tournament.py`；
  - `tests/`：7 文件 49 用例，覆盖题面手算例 `[[1,2+4j],[1+2j,0]]` 的 L=2/C=6、字母表、行稀疏、Kronecker `F4⊗F8≠F32`、乘积顺序、非有限值/非方阵失败、门禁放行/拒绝；
  - `00_admin/proposals/compute/GATE_AND_ORDER_CONVENTION.md`：记录门禁三条前置与「左起优先 vs 应用顺序」乘积约定，请集成者裁决。
- 测试与门禁：unittest 49/49 PASS；`git diff --check` PASS；pre-commit 边界 PASS；协议冻结门禁 `FAIL`（`NOT_RUN`，缺 `00_admin/freezes/tournament_protocol.json`），未当作通过。
- 结果边界：未创建/修改 `05_results/` 任何产物（`git diff main HEAD -- 05_results/` 为空）；未改动 `03_model/`；未生成或声称任何候选 RMSE、复杂度、胜者或最优性数值；测试输出仅写入系统临时目录。
- 接口影响：未改机器协议或现有代码。新增 `targets.product`（左起优先 `A1@..@AK`）与 `protocol_gate` 的 `FROZEN` token/冻结路径，均出自冻结包准备件与先前 `verify-freeze` 失败信息，但仍需集成者在 `DECISIONS.md` 落盘（见提案）。
- 已知限制：NPZ 安全加载（需锁定 NumPy）、真实候选映射、L0–L4 执行、`05_results/runs/<run-id>/` 不可覆盖写入与汇总器尚未实现，留待协议冻结后；本机 `pytest` 未装，测试用 stdlib `unittest`。
- 下一步与接收人：
  1. **集成者/主 Agent**：审核 `e1f4194` 与本提案；裁决 `FROZEN` 门禁与 `product_order` 约定并写入 `DECISIONS.md`；推动题面规则冻结、检索与 `tournament_protocol` 冻结。
  2. **计算 Agent（下一轮）**：冻结校验 PASS 后同步最新 `main`，验证冻结哈希，映射真实候选（C1/C2/C3）并实现 NPZ/runner/汇总器，进入 L0–L4。

## 对擂协议门禁接口修正交接

- 角色/分支/工作树：E 计算 Agent；`agent/compute`；`C:/Users/Lenovo/Desktop/华为杯-数模/23年B/worktrees/compute`。
- 内容提交：`2595bf019ae8730c26070f6a5a1943bfd2a6800d`。
- 输入版本与哈希：
  - `00_admin/workflow.json` SHA-256 `486ba2eaa9b2e48a294735e77ea2fa77d4509406e3054e5558970d666d1ea672`；机器状态契约只有明确 `PASS` 才放行。
  - `03_model/tournament_protocol.json` SHA-256 `167635df24be6afdf40042345f2cd38995d03d5cde98047f29fc831bea302398`；本工作树仍为 `NOT_RUN`，只用于确认门禁继续失败关闭。
  - `workflow_guard.py` 的 `verify_freeze`/`freeze` 实现作为接口事实源：冻结清单自身为 `status=PASS`、`stage=tournament_protocol`，并绑定文件 SHA-256/大小及 `problem` 冻结依赖。
- 改动与接口影响：
  - `04_code/src/dft_integer_approx/protocol_gate.py` 改为只接受协议 `status=PASS`，明确拒绝 `FROZEN` token；递归验证 `tournament_protocol`/`problem` 冻结元数据、依赖 manifest SHA-256、冻结文件 SHA-256/大小和工作区路径边界，并要求清单显式包含当前协议。文件 SHA-256 `e40412880a72c4b435c0ac2bfe2b5b4bc9334727a4e1583f6a9563f39ba3d27b`。
  - `04_code/tests/test_protocol_gate.py` 增加合法放行、`FROZEN` token 拒绝、缺冻结、协议哈希漂移、依赖哈希漂移等测试。文件 SHA-256 `161b9b09071f7f254798b0dd716447f56919b2dda67e8a09cbbe52d07bead1d3`。
  - `04_code/README.md` 与 `scripts/validate_protocol.py` 同步机器口径；未修改 `03_model/` 或 `05_results/`。
- 测试与门禁：
  - `python -m unittest discover -s 04_code/tests -p 'test_*.py' -v`：退出码 0，**52/52 PASS**。
  - `python 04_code/scripts/validate_protocol.py`：退出码 1，原因是协议 `NOT_RUN`、`problems` 为空、缺冻结清单；按预期拒绝。
  - `python 04_code/scripts/run_tournament.py`：退出码 1，按预期拒绝；没有启动候选或正式 tournament。
  - `git diff --check`：PASS；pre-commit 分支写入边界检查：PASS。
- run-id 与结果边界：`NOT_RUN`；没有创建、修改或覆盖任何 `05_results/` 文件，没有生成数值、排名或胜者。
- 已知限制：本提交只修正冻结门禁接口；真实候选映射和 L0–L4 仍须等待上游规则/题面、检索、协议及冻结链全部 PASS。
- 下一步与接收人：交给主 Agent 审核并合并；合并后以主工作树执行 `workflow_guard.py verify-freeze --stage tournament_protocol` 和本地 `validate_protocol.py` 双重校验，任何一项失败都不得进入正式运行。

## 协议冻结后 L0/L1 确定性基线交接

- 角色/分支/工作树：E 计算 Agent；`agent/compute`；`C:/Users/Lenovo/Desktop/华为杯-数模/23年B/worktrees/compute`。
- 同步与内容提交：开始时已确认 `HEAD=origin/main=a8ad6cfb6ec49acb7da70b4e3e127b29e745c873`；L0/L1 代码与结果提交为 `6aeddd1514e50bd2be8d17e6e72a525344627a8d`。
- 冻结输入与哈希：
  - `00_admin/input_manifest.json` SHA-256 `dfc1ed4ec5e939ea4e0613adf3414f979ed15b791c403fa203e38604b6920680`；L0 重算题面文件 SHA-256 与清单一致，数据类别保持 `third_party_copy`。
  - `03_model/tournament_protocol.json` SHA-256 `c253df797845cfff4f24cdcd7da579ed841e487c36bb678cc92a8ebd60457592`。
  - `00_admin/freezes/problem.json` SHA-256 `fcb77412c24bf8b0b8e491b2ae4a84a9988b0ca985af195500ce5b597aa5b0a1`。
  - `00_admin/freezes/tournament_protocol.json` SHA-256 `b97a9a31e36cea7d58ee9559c7dd90ac7f97fa9b0359594844e781cec5ba8b48`；正式运行前两次执行 `workflow_guard.py verify-freeze --stage tournament_protocol` 均为 PASS，本地 `validate_protocol.py` 也为 PASS。
- D-011 披露：所有 31 个 `04_code/**/*.py` 均有统一 AI 辅助文件头；`04_code/AI_ASSISTED_DEVELOPMENT.md`（SHA-256 `046bad06d491094557520e32404272b939768af623fa478997499fb1c7ebb1d6`）集中记录工具/型号、开发机构、精确版本日期未披露边界、任务输入摘要、后处理和人工复核要求。
- 实现范围：
  - L0：题面输入哈希、单位化/正交性、零基索引、F2 手算、`F4 tensor F8 != F32`、因子顺序、行支持、Pq、K/L/C、支持下界、N=8 精确 radix-2 构造；`05_results/l0_checks.json` 状态 PASS，SHA-256 `bf91c0f84b752c0591273f56ccba7854fccc3b6eff0660791fca8e57b7aa3890`。
  - L1：q1 精确缩放 radix-2、q2 单因子 P3 投影、q3 P3 量化 Butterfly＋固定顺序一次坐标润色、q4 Kronecker 提升量化 Butterfly、q5 q=1 全登记 K 网格基线。
  - 每个实例保存稀疏 `factors.json`、`stdout.txt`、`stderr.txt` 与完整 `run_manifest.json`；独立复算路径重新加载持久化因子，不导入搜索侧乘积/RMSE函数。所有文本产物固定 LF；`05_results/.gitattributes` 固定 `.txt eol=lf`，避免 checkout 后哈希漂移。
- 实际命令：
  - `python -m compileall -q 04_code`：PASS。
  - `python -m unittest discover -s 04_code/tests -p 'test_*.py'`：**61/61 PASS**。
  - `python -X utf8 C:/Users/Lenovo/.codex/skills/1start-mathmodel/scripts/workflow_guard.py verify-freeze --workspace . --stage tournament_protocol`：PASS。
  - `python -X utf8 04_code/scripts/validate_protocol.py`：PASS。
  - `python -X utf8 04_code/scripts/run_l0.py`：PASS。
  - `python -X utf8 04_code/scripts/run_baselines.py`：最终批次退出码 0，50 个实例均完成；最大单实例墙钟约 0.792119 秒，未触及 60 秒上限。
  - `workflow_guard.py check --gate tournament`：按预期 FAIL，原因仅为挑战者、最终 winner、L3 稳健性和 L4 消融仍未完成，未把本里程碑伪装成对擂 PASS。
- 当前正式证据批次与 run-id：`05_results/metrics.json.latest_batch_run_ids` 完整登记 50 个 run-id（首个 `20260915T021254422985Z__q1__q1-b0-scaled-radix2__s0__pc253df79__c8c947602`，末个 `20260915T021258909558Z__q5__q5-b0-q1-butterfly__s0__pc253df79__c8c947602`）；字段内 50 项是本提交代码树 SHA-256 `8c9476026d7536ac5befa9acce8bce1aaea6d50d9adff11a6d883245f8167935` 对应的当前证据集。搜索侧与独立复算 RMSE 最大绝对差为 0，全部产物哈希复核无误。
- 当前批次结果（不作最终胜者结论）：
  - q1：6/6 PASS；N=2/4/8/16/32/64 的 RMSE 分别约为 `4.33e-17/1.49e-16/3.14e-16/6.90e-16/9.76e-16/1.32e-15`，对应 `(L,C)` 为 `(4,64)/(16,256)/(48,768)/(128,2048)/(320,5120)/(768,12288)`。
  - q2：5/5 PASS；N=2/4/8/16/32 的 RMSE 为 `0.292893/0.5/0.353553/0.25/0.176777`，本基线均 `L=C=0`。
  - q3：5/5 PASS；同尺寸 RMSE 为 `0.292893/0.5/0.353553/0.25/0.176777`，本基线均 `L=C=0`。
  - q4：1/1 PASS；N=32、K=5、q=3，RMSE `0.7183905324091097`，`L=C=0`。
  - q5：33/33 为 `INFEASIBLE` 而非运行失败；所有 q=1/K 网格因子合法且 `L=C=0`，但 N=2/4/8/16/32/64 的最好 RMSE 仍为 `0.292893/0.5/0.353553/0.25/0.176777/0.125`，均未达到 0.1，因此 winner 保持 null。
- 机器汇总：`05_results/metrics.json` SHA-256 `ade19f68217307cdd06250f64bce0ae7a517d3cb1b556c7a99ff8045747f4902`、`05_results/tournament.json` SHA-256 `8a4957bd8c5744d37234f277ead56dff86dfd7714be1684b668a93a0254e4c02` 均保持 `BLOCKED`；`05_results/RESULTS_REPORT.md` SHA-256 `17ebced19b274d0d06363217d5273dcf782ddddbc3bf5dc6bff4d952ed934d94`。
- 历史失败保留：开发期首批 q4 曾因稀疏 JSON 未保存 IEEE-754 负零符号而触发因子字节哈希不一致；该 `CONSTRAINT_FAIL` run 及后续重跑批次均按不可删除原则保留。最终 `metrics.json` 共含 250 个历史/当前 run，其中 `latest_batch_run_ids` 的 50 项才是当前代码树证据集。
- 结果边界：未实现或运行任何 c1/c2 挑战者；未选择最终 winner；未写 `PASS` 总状态；未执行 L2/L3/L4；未修改任何冻结文件。
- 下一步与接收人：主 Agent 审核并合并本提交；随后计算 Agent 在同一冻结协议和预算下实现并运行全部挑战者，保留所有失败，完成 L2 后再做 L3/L4。论文 Agent 当前只能引用“基线阶段证据”，不得写最终赢家或最优性结论。
