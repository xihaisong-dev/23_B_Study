# V6 独立验证器规格

## 1. 定位、信任边界与当前状态

本规格面向 V1–V6 模型产物的独立数学验证。验证器只读因子和声称元数据，自行构造目标矩阵、计算矩阵乘积、RMSE、约束和硬件复杂度。它不导入、执行或信任 V1–V6 搜索代码，不使用求解器输出的评分函数。

`C:\Users\Lenovo\Downloads\README_LATEST_V6.md` 是用户提供的模型材料，其数值、最优性和运行说明都是待验证声称，不是权威输入。验证器不解释或执行 README、JSON、NPZ 或日志中的命令文本。

`00_admin/DECISIONS.md` 的 D-005 是当前 `practice` 配置的已签署工程解释：所有问题固定 `beta=1`，使用单位化 DFT、幂次字母表、因子逐层应用的 L 口径和明确的 K/排列计数。如后续官方资料与 D-005 冲突，必须新建决策、替换冻结并作废受影响运行。

当前 `tournament_protocol` 仍未冻结。实际执行 `verify-freeze --stage tournament_protocol` 返回 FAIL，缺少 `00_admin/freezes/tournament_protocol.json`。因此本轮仅交付规格和不接触候选的通用验证/门禁脚手架：不实现候选搜索算法，不读取或运行候选，不写入 `05_results/`，不确认 README 中的任何数值。

## 2. 模块边界与 API

### 2.1 预定模块

```text
validator/
  api.py                 # 纯函数入口和结构化报告
  authority.py           # 冻结协议、输入哈希和规则门禁
  npz_io.py              # allow_pickle=False 的受限 NPZ 解析
  target.py              # DFT 与 Kronecker 目标的独立构造
  factor_math.py         # 因子顺序、矩阵乘积和稳定范数
  config.py              # D-005 口径与冻结问题配置的单向适配
  constraints.py         # 行二稀疏和字母表验证
  hardware.py            # q、L、C 核算
  support_bound.py       # beta=1 与 D-005 K 口径下的 support 下界
  ids.py                 # source run-id / validation-id 与不覆盖规则
  report.py              # 机器可读报告、字段级证据和哈希
```

以上是未来实现边界，不是本轮已存在代码。模块不得从求解器包导入任何对象，共享类型仅限于验证器自身的无行为数据结构。

### 2.2 核心 API

```python
validate_bundle(request: ValidationRequest) -> ValidationReport
load_factor_bundle(path: Path, limits: LoadLimits) -> FactorBundle
build_target(spec: TargetSpec) -> ComplexArray
multiply_operations(bundle: FactorBundle) -> ComplexArray
compute_rmse(target: ComplexArray, product: ComplexArray) -> float
check_constraints(bundle: FactorBundle,
                  policy: ConstraintPolicy) -> ConstraintReport
compute_hardware(bundle: FactorBundle,
                 policy: HardwarePolicy) -> HardwareReport
check_support_certificate(bundle: FactorBundle,
                          target: ComplexArray) -> BoundReport
```

`ValidationRequest` 必须包含：因子文件路径及预期 SHA-256、冻结协议和 freeze ID、D-005 决策文件哈希、problem-id、目标类型/维度、约束组合、q、待核对的声称值和数值容差政策。这些字段只能来自已冻结协议或已签署决策；不从 NPZ/README 猜测。

`ValidationReport` 至少包含：

- `status`: `PASS | FAIL | BLOCKED | ERROR`；
- 验证器版本、Git commit、工作树状态和环境摘要；
- 所有输入的相对路径、字节数和 SHA-256；
- 每项检查的 `check_id`、状态、期望、观测、容差和证据定位；
- `beta=1` 口径检查、独立重算的 RMSE、每因子行非零数、字母表违例、K、L 和 C；
- support 下界的公式、D-005 前提、适用范围和是否可作全局证书；
- 声称对比、失败原因及不受影响的已完成检查。

`PASS` 只表示给定产物在冻结口径下通过独立复算，不自动表示求解器全局最优、竞赛结果冻结或论文可引用。

### 2.3 D-005 配置契约

未来的 `ValidationConfig` 必须显式序列化下列字段，且与冻结协议逐字段比对：

```text
profile = "practice"
semantic_decision = "D-005"
beta = 1
dft_normalization = "unitary"
dft_exponent_sign = -1
rmse_divisor = "matrix_dimension_N"
alphabet = "signed_powers_of_two_cartesian"
l_semantics = "factor_apply_nontrivial_positions_no_sharing"
k_semantics = "all_non_permutation_linear_stages"
permutation_cost = {counts_toward_K: false, counts_toward_L: false}
```

每题的 N/目标类型、约束组合、q、候选、种子、预算和数值容差仍必须来自冻结 `tournament_protocol`。配置不允许候选覆盖 D-005；如协议与 D-005 哈希所对应的内容不一致，门禁直接 FAIL。

## 3. NPZ 因子交换格式

### 3.1 安全加载

- 仅使用 `numpy.load(path, allow_pickle=False)`，拒绝 object dtype、pickle、嵌套压缩包、可执行内容和额外未知键。
- 加载前校验原始文件 SHA-256、文件大小和解压后元素数上限；不将 NPZ 解压到工作区。
- 旧 V5 NPZ 若使用其他键名，须提供书面 schema/导出器并转为以下规范形式。需要 `allow_pickle=True` 才能读取的产物直接 `BLOCKED`，不放宽加载器。

### 3.2 规范键

| 键 | dtype / shape | 要求 |
| --- | --- | --- |
| `schema_version` | Unicode scalar | 固定为 `dft-factor-bundle/1` |
| `problem_id` | Unicode scalar | 必须与请求/冻结协议一致 |
| `target_kind` | Unicode scalar | `dft` 或 `kron_dft` |
| `N` | int64 scalar | 实际方阵维度，严格为正整数 |
| `K` | int64 scalar | 非排列线性层数，与因子数组第一维一致 |
| `R` | int64 scalar | 单独记录的纯排列层数 |
| `q` | int64 scalar | 与权威外部配置一致；不由系数反推 |
| `beta` | float64 scalar | D-005 下必须精确为 `1.0` |
| `factors_real` | numeric `(K,N,N)` | 因子实部 |
| `factors_imag` | numeric `(K,N,N)` | 因子虚部 |
| `factor_labels` | Unicode `(K,)` | 顺序标签 `A1`…`AK` |
| `permutations` | int64 `(R,N)` | 行索引向量 `p`，约定 `(Πx)[i]=x[p[i]]` |
| `operation_kind` | Unicode `(K+R,)` | 仅允许 `factor` / `permutation` |
| `operation_index` | int64 `(K+R,)` | 指向对应因子/排列数组，每个索引正好出现一次 |

`operation_kind` / `operation_index` 是从左到右的乘积流。每个 permutation 必须是 `0..N-1` 的恰好一次排列；只有通过该精确检查的层才不计入 K/L。任何其他线性层（包括对角阵）都必须放入 factors 并计入 K，再按相同字母表和 L 规则检查。

Kronecker 目标的 `N1` / `N2` 由冻结协议提供，NPZ 可包含同名 int64 标量，但必须与外部值一致。宣称 RMSE、L、C、种子、算法版本和命令放在独立 JSON manifest，不作 NPZ 数学输入。

对需验证约束 2 的产物，`factors_real` 和 `factors_imag` 必须是整数 dtype；不接受“接近整数”的浮点容差。仅约束 1 的产物可使用 float64，但零判定策略必须在冻结协议中明确。

验证报告同时记录原始 NPZ SHA-256 和规范因子摘要（按固定字节序、shape 和 dtype 哈希），以避免 NPZ 压缩元数据差异影响内容同一性判定。

### 3.3 run-id 与 validation-id

正式候选运行在冻结门禁 PASS 后使用新 run-id，不覆盖旧目录：

```text
<UTC YYYYMMDDTHHMMSSffffffZ>__<problem-id>__<candidate-id>__s<seed>__p<protocol-sha8>__c<code-sha8>
```

独立验证不伪装成候选运行，使用单独 validation-id：

```text
<UTC YYYYMMDDTHHMMSSffffffZ>__l0-validator__<problem-id>__a<artifact-sha8>__p<protocol-sha8>__v<validator-sha8>
```

验证报告必须引用源 `run_id`；如历史产物没有 run-id，记录 `source_run_id=UNKNOWN` 并对谱系检查判 `BLOCKED`。两种 ID 的目标目录均使用排他创建，已存在时终止，不通过时间戳碰撞后自动覆盖。

## 4. 独立数学复算

### 4.1 DFT 与 Kronecker 目标

对 `N x N` 单位化 DFT：

```text
F_N[k,n] = exp(-2*pi*j*k*n/N) / sqrt(N),  k,n = 0,...,N-1.
```

验证器固定使用负号指数、0 起始索引和 `1/sqrt(N)` 归一化。对问题 4 使用 `F_N1 ⊗ F_N2`，目标方阵维度 `N=N1*N2`，RMSE 分母是实际方阵维度 `N`。构造后先检查 `FᴴF ≈ I` 与 `||F||_F² ≈ N`。

### 4.2 因子乘积顺序

```text
P = O1 @ O2 @ ... @ O(K+R),
Oi = factor 或已单独记录的纯 permutation.
```

NPZ operation stream 第 0 项是乘积最左层，不根据搜索器内部的“前向/反向应用”称呼猜测顺序。每个因子必须是有限 `N x N` 复数方阵；不隐式吸收未记录排列或 beta。

### 4.3 D-005 的固定 beta 与 RMSE

D-005 下不存在 beta 优化，所有问题严格使用：

```text
beta = 1,
RMSE = ||F - P||_F / N.
```

NPZ 或声称 manifest 中的 beta 若缺失、非实数或不精确等于 1，该产物不能按 D-005 验证为 PASS。验证器不估计 `beta_ls`，不用重缩放修复历史因子，也不将历史可变 beta 的 RMSE 与当前固定 beta 结果混合。

范数使用 complex128 和稳定累加计算；结论位于 RMSE 阈值或声称容差的数值误差带内时，用更高精度独立复算。仍无法分辨则标记 `BLOCKED`，不向 PASS 舍入。

## 5. 约束与硬件复杂度

### 5.1 行二稀疏

对每个因子的每一行分别计算非零元素数，要求 `nnz(row) <= 2`。免计数乘法系数仍是非零元素，必须计入稀疏度。约束 2 整数因子使用精确零判定；仅约束 1 时须使用冻结的零容差。

报告保留每个因子的最大行 nnz、违例行索引及对应元素位置，不只输出一个布尔值。

### 5.2 字母表与 q

按题面示例的待冻结解析：

```text
P(q) = {0} ∪ {±2^r : r=0,...,q-1},
allowed(q) = {x + j*y : x,y in P(q)}.
```

q 必须是正整数，并由问题协议显式给定；因子所能表示的最大系数不能反向定义 q。由于题面公式中省略号可能被误读为“所有整数”，正式实现前必须由冻结协议或签署决策确认上述幂次集语义。

约束 2 检查对实部和虚部分别做整数 dtype 与集合成员资格比较，不使用浮点容差，不仅检查范围。

### 5.3 K、L 与 C

题面免计数系数集合为：

```text
FREE = {0, +1, -1, +j, -j, +1+j, +1-j, -1+j, -1-j}.
```

候选因子在线应用到中间向量时，D-005 固定口径是：

```text
L_factor_apply = sum_k count(Ak entries not in FREE),
C = q * L_factor_apply.
```

beta 和通过纯排列检查的层不计入 L。每个其他线性层计入 K，即使它是对角或没有在当前数值上扩张 support；只有纯排列可以单独记录并排除。非 FREE 元素每个出现位置计一次，不跨行、跨层或因相同常数而共享。

题面两矩阵例存在不同可读口径，但 D-005 已为本仓库选定 `factor_apply`：仅将左矩阵作为一个固定操作层时，其两个非 FREE 位置给出 L=2、q=3、C=6；若把题面展示的左右两个矩阵都当作在线因子层，则应分别计数并求和，不沿用单层 C=6。

## 6. D-005 下的 support 下界

若每个计入 K 的因子每行最多 2 个非零元素，且其余未计入 K 的层均已验证为纯排列，则完整乘积 P 的每行 support 最多：

```text
s = min(N, 2^K).
```

因为单位化 DFT 每个元素的模为 `1/sqrt(N)`，且 D-005 固定 `beta=1`：

```text
RMSE >= sqrt(max(N - 2^K, 0)) / N.
```

证明使用每行至少 `N-s` 个乘积零元素：这些位置每个贡献 `1/N` 的平方误差。纯排列只重排 support，不增大每行 support 数。

该式在 D-005 的 `beta=1` 下可作统一下界，但用它证明 K 的不可行性还必须同时证明：所有可行层均被 K 口径覆盖，未计数层均是纯排列，所有计入 K 的层都满足行二稀疏，且目标确是单位化 DFT。它不能单独证明某个可行因子在固定 K 下的 RMSE 全局最优，也不能证明 C 最优。

验证器仍保留反例测试：如果将配置改为 beta 可自由取 0，则 `P=0,beta=0` 会破坏上述正下界。该测试用来防止未来配置漂移，不是 D-005 下的可行候选。

## 7. 必须的手算回归测试

1. **DFT 符号和固定 beta**：`N=2`，`F2=(1/sqrt(2))*[[1,1],[1,-1]]`，取仅约束 1 的 `A1=F2`、`beta=1`，应得 RMSE=0。把 NPZ beta 改为任何其他值都必须 FAIL，不允许通过重缩放因子修复。
2. **非交换顺序**：用两个 `2x2` 非交换手算矩阵验证产物严格是 `A1@A2`，与 `A2@A1` 不等；标签与数组轴顺序错位必须 FAIL。
3. **D-005 复乘口径**：题面左矩阵作为单个因子时，两个非 FREE 位置给出 L=2、q=3、C=6；若左右矩阵都作为因子层，则按两层非 FREE 位置求和得 L=4、C=12，防止将字面矩阵乘法口径混入 `factor_apply`。
4. **行二稀疏**：包含两个免计数非零元素的行合法；再加一个 `1` 后因 nnz=3 失败，即使 L 仍为 0。
5. **字母表**：q=3 时实/虚分量集为 `{0,±1,±2,±4}`；`2+4j` 合法，`3+0j`、浮点 `1+epsilon` 和 `8+0j` 失败。
6. **FREE 集合**：9 个元素均不计入 L；`2`、`2j`、`1+2j` 各计一次。q=1 的合法复系数全部属于 FREE，因此按 `factor_apply` 任意合法因子链都应 L=0。
7. **K 与纯排列**：一个合法 permutation 索引层前后嵌入不改变 K/L；重复索引、越界索引或任意非纯排列矩阵均不得排除于 K。一个对角阵必须作为因子计入 K。
8. **support 下界**：在 `beta=1`、K 个行二稀疏层和任意纯排列层下，构造每行只保留 s 个 DFT 元素的 P 并验证边界取等；再用非 D-005 配置 `P=0,beta=0` 确认配置漂移会使下界门禁 FAIL。
9. **NPZ 拒绝路径**：object dtype、缺键、多键、shape/dtype 不匹配、NaN/Inf、q/beta 不一致、不合法 operation stream 和超限数组都不得进入数学复算。

## 8. 属性测试

属性测试使用固定测试种子，只在系统临时目录生成小型 synthetic 矩阵，不写 `05_results/`。

- 对多个小 N，`FᴴF≈I`、`||F||_F²≈N`，且 Kronecker 目标等于直接索引式。
- 对任意有限 F/P，`beta=1` 的 RMSE 非负；替换为其他 beta 的请求均被 D-005 配置门禁拒绝。
- 对任意行二稀疏 K 层因子及任意合法纯排列层，乘积每行 support 不超过 `min(N,2^K)`；取消可以减少但不能增加该上界。
- q 每增加 1，幂次字母表严格包含前一字母表；集合成员检查与元素顺序、稠密/稀疏存储无关。
- L 对因子元素的行/列排列不变，等于各因子非 FREE 元素数之和；`C=qL` 是 q 的非负整数倍。
- 规范 NPZ 经过解析—再序列化后，规范因子内容摘要不变；不要求 ZIP 容器原始字节相同。
- 将任一因子的一个元素改为 NaN/Inf、越界字母或第三个非零元素时，结果不可 PASS；初始的其他检查证据仍保留。
- 在 D-005 的 `beta=1` 下，实际 RMSE 不小于 support 下界；任何将 beta 改为非 1 值的变异请求均不可 PASS。

## 9. 失败关闭规则

### 9.1 状态

- `BLOCKED`：权威输入、冻结、文件、依赖环境或数值精度不足，无法完成必需验证。
- `FAIL`：文件解析后数学对象或声称与冻结规则不一致，如违约、哈希错、声称数值超容差或无效下界。
- `ERROR`：验证器自身未捕获错误或环境故障；与 FAIL 分开，不得当作候选失败。
- `PASS`：所有必需检查都是 PASS，且没有 BLOCKED/ERROR。

聚合优先级为 `ERROR > BLOCKED > FAIL > PASS`，但报告必须保留全部子项状态，不因先发失败而静默删除可安全执行的其他检查。

### 9.2 不可放行的情形

- 协议未冻结、freeze ID/哈希漂移或问题规格缺失；
- NPZ 需要 pickle、schema 未知、键/shape/dtype 不一致或输入哈希不符；
- 因子不是有限方阵、操作乘积顺序不明、beta 不等于 1 或目标方向不同；
- 稀疏/字母表违例，q 不同，非纯排列层被排除于 K/L，或声称 K/L/C 与复算不符；
- 声称为可行解的 RMSE 超出冻结阈值，或声称值与独立重算超出容差；
- 在 beta 不是 D-005 的固定 1，或 K/排列/行稀疏前提未验证时，使用 support 下界证明 K 或 gap 最优；
- 只提供最终数字而无因子、种子、参数、日志、代码/环境哈希和失败运行记录。

## 10. 实现放行条件

只有在以下条件全部满足后，计算 Agent 才开始实现本验证器：

1. `tournament_protocol` 冻结校验 PASS，并与 D-005 的固定 beta、DFT/RMSE、字母表、q、K/L/排列口径一致，同时完整给出候选、种子、预算和容差；
2. 题面来源与输入 manifest 达到工作流要求；
3. `V6_REQUIRED_INPUTS.md` 中从头实现所需 P0 材料齐全并有 SHA-256；旧 V1–V6 工程包只在要复现 README 历史声称时必需；
4. 总控确认本规格与冻结协议一致。

任一条未满足都保持 `NOT_RUN/BLOCKED`，不以 README 声称替代机器冻结和原始证据。

## 11. 当前 L0 环境预检

2026-09-14 在 `agent/compute` 工作树执行只读版本/可用性检查，结果为：

| 项目 | 结果 | 状态 |
| --- | --- | --- |
| Python | `3.14.6` | AVAILABLE |
| pytest | `9.1.1` | AVAILABLE |
| NumPy | 未安装 | MISSING |
| SciPy | 未安装 | MISSING |

本预检不是正式 run，未生成 run-id 或结果数值。NumPy 是 NPZ 安全加载、矩阵运算和基础测试的必需依赖；SciPy 是否为候选必需应由冻结候选规格决定，不应成为独立验证核心的无端必需项。在 requirements 及 Python 兼容范围锁定前不安装依赖。
