# 计算 Agent 交接

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
