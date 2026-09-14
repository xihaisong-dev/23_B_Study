# 计算端启动实施计划

## 1. 目的与当前门禁

本文只定义计算 Agent 在对擂协议冻结前可搭建的工程骨架和候选统一接口，不实现或挑选任何候选模型，不产生正式实验数值。

当前 `03_model/tournament_protocol.json` 的状态是 `NOT_RUN`，且 `problems` 为空；`00_admin/workflow.json` 仍处于 `INIT`。因此：

- 允许：建立包结构、类型/协议适配层、纯函数计分器、运行记录器、合成小样例和单元测试。
- 禁止：执行正式候选对擂、调参、选胜、写入正式 `metrics.json` / `tournament.json`，或宣称任何 RMSE/复杂度改善。
- 放行条件：运行器必须验证协议状态、冻结清单及哈希，且候选、指标、种子、预算、约束和平局规则完整。任一项未通过时以非零退出码终止，不作降级运行。

## 2. 预定目录结构

```text
04_code/
  README.md                       # 环境、命令和状态语义
  pyproject.toml                  # 固定依赖与测试/格式化配置
  src/dft_integer_approx/
    contracts.py                  # 协议适配后的强类型对象
    protocol_gate.py              # 冻结、状态、完整性检查
    targets.py                    # 归一化 DFT / Kronecker 目标构造
    candidate_api.py              # 候选插件接口与注册表
    constraints.py                # 约束验证，不自行发明协议语义
    metrics.py                    # RMSE 等冻结指标的纯函数实现
    hardware.py                   # L 和 C=q*L 的精确计数
    hashing.py                    # 文件/配置/代码/输入 SHA-256
    provenance.py                 # run-id、环境和 run manifest
    runner.py                     # 同口径执行和错误分类
    serialization.py              # 整数/复数矩阵无歧义序列化
  tests/
    fixtures/                     # 仅小型 synthetic / hand-worked fixtures
    test_targets.py
    test_candidate_contract.py
    test_constraints.py
    test_metrics.py
    test_hardware.py
    test_protocol_gate.py
    test_provenance.py
    test_serialization.py
  scripts/
    validate_protocol.py
    run_tournament.py
    reproduce_run.py
05_results/
  runs/<run-id>/                  # 不可覆盖；每次尝试均有记录
```

目录只在实际需要时创建。冻结前的测试输出必须写入系统临时目录，不写入 `05_results/`。

## 3. 协议适配与统一候选接口

### 3.1 适配原则

`tournament_protocol.json` 冻结后由 `contracts.py` 做单向适配：原文件是权威输入，代码内部对象不反写协议。未知字段保留于原始快照，缺少必需字段则失败关闭。若冻结后接口仍无法无歧义映射，只在 `00_admin/proposals/compute/` 提交影响和迁移提案，不修改模型协议。

### 3.2 输入对象

```python
ProblemSpec(
    problem_id: str,
    target: TargetSpec,
    constraints: tuple[ConstraintSpec, ...],
    candidates: tuple[CandidateSpec, ...],
    metrics: MetricPolicy,
    budget: BudgetSpec,
    seeds: tuple[int, ...],
    tie_break: TieBreakPolicy,
)

CandidateContext(
    problem: ProblemSpec,
    candidate: CandidateSpec,
    seed: int,
    run_id: str,
    work_dir: Path,
    deadline_monotonic: float | None,
)
```

`TargetSpec` 只接受协议声明的归一化 DFT 或 Kronecker 目标。数组形状、复数类型、矩阵乘法顺序与维度在候选启动前检查。输入对象不向候选暴露其他候选的运行结果。

### 3.3 候选插件

```python
class Candidate(Protocol):
    candidate_id: str

    def solve(self, context: CandidateContext) -> CandidateOutput:
        ...

CandidateOutput(
    status: Literal["SUCCESS", "FAIL", "BLOCKED"],
    factors: tuple[ComplexMatrix, ...] | None,
    beta: float | None,
    diagnostics: Mapping[str, JsonValue],
    failure: FailureRecord | None,
)
```

候选只返回因子、实数 `beta`、诊断和结构化失败。候选不自行计算排名分数、复杂度或选胜结论；这些由共享验证/评分层在相同口径下计算。`SUCCESS` 必须有非空因子列表和有限实数 `beta`；`FAIL` / `BLOCKED` 必须有错误阶段、类型和消息，不得从候选表中删除。

### 3.4 共享输出与评分

验证层按 `A1 @ A2 @ ... @ AK` 构造乘积，核对每个因子的形状、有限性、约束和系数域。RMSE 严格按题面/冻结协议实现：

```text
RMSE = || beta * F - A1 @ A2 @ ... @ AK ||_F / N
```

目标构造使用题面的 `1/sqrt(N)` 归一化。指标计算不优化 `beta`；`beta` 的生成方式必须来自冻结候选规格。非有限值、违约或维度错误均标记失败，不转换为较差的有效分数。

## 4. 输入、输出与不可变运行

### 4.1 正式输入

每次运行先重算并比对：

- `00_admin/input_manifest.json` 声明的输入文件 SHA-256 和数据类别；
- `03_model/tournament_protocol.json` 与对应冻结清单中的 SHA-256；
- 当前 Git commit、工作树污染状态、配置和代码树哈希。

原始输入只读。数据类别不满足正式运行条件时，必须在记录中标为 `BLOCKED`，不伪装成官方结果。

### 4.2 run-id 与写入策略

run-id 由记录器生成，建议格式为：

```text
<UTC YYYYMMDDTHHMMSSffffffZ>__<problem-id>__<candidate-id>__s<seed>__p<protocol-sha8>__c<code-sha8>
```

时间戳使用 UTC 且包含微秒；标识组件仅允许安全字符。创建 `05_results/runs/<run-id>/` 必须使用排他式操作；目录已存在即失败，绝不覆盖。先写同目录临时文件，成功 `fsync` 后原子替换目标文件。

每个尝试至少保存：

```text
run_manifest.json
stdout.log
stderr.log
factors.npz              # SUCCESS 时存在
candidate_output.json
metric_output.json
```

`metrics.json` 和 `tournament.json` 是由所有单次运行记录汇总生成的派生产物；汇总器必须保留成功、失败、阻塞和未运行的全部候选。

### 4.3 `run_manifest.json` 最小字段

- schema version、run-id、状态与正式/合成标签；
- problem-id、candidate-id、seed、开始/结束 UTC、单调时钟耗时；
- 完整命令参数、工作目录、资源预算与终止原因；
- Python、操作系统、CPU/逻辑核、可用内存，以及参与计算的库版本；
- 线程数与确定性环境变量；
- Git commit/污染状态、协议/冻结 ID、配置/代码/输入 SHA-256；
- Python `random`、NumPy 及候选所用其他后端的实际种子；
- 产物相对路径、字节数和 SHA-256；
- 测试/门禁状态与结构化失败记录。

种子策略完全读取冻结协议。不使用隐式全局随机状态；候选获得由根种子确定派生的局部 RNG。同一问题的候选共用相同根种子列表和预算口径。

## 5. 硬件复杂度计数

### 5.1 单一事实源

`hardware.py` 是唯一复杂度计数实现。对因子链按题面定义累计非平凡复乘系数个数 `L`，再计算 `C = q * L`。免计数集合严格为：

```text
0, +1, -1, +j, -j, +1+j, +1-j, -1+j, -1-j
```

约束 2 的高斯整数系数使用整数实/虚部判定，不使用浮点容差将近似值误判为免计数元素。约束 1 下的一般复数如何进行精确/容差分类，必须由冻结协议或已签署决策指定；未指定时失败关闭。`q` 只读取协议/语义契约，不根据观测到的系数反推。

### 5.2 必须通过的单元测试

1. 上述 9 个免计数元素逐一返回 0，且零不因稀疏存储方式被重复计数。
2. `2+4j` 和 `1+2j` 各计一次；题面手算例中 `L=2`、`q=3`、`C=6`。该断言是定义回归测试，不是竞赛候选结果。
3. 多因子链的 `L` 等于各因子非平凡系数数量之和，改变因子顺序不改变计数，但不换序乘积本身。
4. 空因子列表、非方阵、NaN/Inf、不合法 `q`、非整数约束 2 系数以及超出冻结字母表均显式失败。
5. 约束 1 的逐行非零元素上限与复杂度计数分离测试：免计数非零元素仍计入行稀疏度。
6. 题 1 的 `q=16` 仅在问题语义确认后由协议注入；测试验证一个非平凡系数对应 `C=16`，防止默认值漂移。
7. 稠密与稀疏存储对同一小矩阵给出相同 `L` 和 `C`。

## 6. 其他测试与持续检查

- 目标矩阵：以手算的小型合成 fixture 验证归一化、元素符号、形状和 Kronecker 顺序。
- 候选契约：使用 fake candidate 验证完整输出、超时、异常、违约和非有限数处理。
- 指标：使用零误差、已知单元素偏差和输入不变性测试 RMSE；不把任何合成值写入正式结果。
- 协议门禁：覆盖未冻结、哈希漂移、字段缺失、重复 candidate-id、空种子/预算和未知指标。
- 谱系：验证相同输入和代码生成稳定哈希，run-id 唯一，已有目录不可覆盖，产物篡改可检测。
- 可复现：同一候选、种子、协议、代码和确定性环境必须产生逐字节相同的机器结果；如底层库无法保证，在 manifest 明示并按协议容差验证。

冻结前 CI/本地测试只允许使用 `synthetic` 或题面明示手算例，并设置禁止写入 `05_results/` 的环境开关。

## 7. 实施顺序

1. 先实现协议 schema 适配和失败关闭门禁；在协议冻结前只能测试门禁“拒绝运行”。
2. 实现目标矩阵、矩阵序列化、约束、RMSE 与硬件计数纯函数，用手算/合成 fixture 单元测试。
3. 实现候选插件契约、预算/超时包装和结构化错误，只接入 fake candidates。
4. 实现 run-id、环境快照、哈希和不可覆盖写入，在临时目录做端到端测试。
5. 协议冻结后同步最新 `main`，运行 `workflow_guard.py verify-freeze --stage tournament_protocol`；仅在 PASS 后映射真实候选并进入 L0–L4。
6. 在同一冻结协议下运行全部候选，完整保留成功/失败记录，再生成汇总产物。

## 8. 实施前待冻结的接口项

下列内容必须由建模 Agent 在协议中明确，计算 Agent 不作默认：

- 各题候选 ID、规格、假设、输入/输出、失败条件和文献依据；
- 主/次指标方向、可行性优先级、平局顺序与数值容差；
- 每题的 `N`、目标构造、约束组合、`q`、`K` 语义和搜索范围；
- 训练/评估或重启口径、种子列表、时间/迭代/内存预算；
- 压力、稳健性/敏感性和消融项及 `NOT_APPLICABLE` 条件；
- 约束 2 字母表的精确解析，以及约束 1 一般复数与免计数集合比较的容差政策；
- 题 5 的 `q` 合法域、RMSE 阈值可行性判定与复杂度平局规则。

上述任一项缺失都是协议门禁错误，不允许通过运行时猜测补齐。
