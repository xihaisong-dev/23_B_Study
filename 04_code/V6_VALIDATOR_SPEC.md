# V6 独立验证器规格

## 1. 定位、信任边界与当前状态

本规格面向 V1–V6 模型产物的独立数学验证。验证器只读因子和声称元数据，自行构造目标矩阵、计算矩阵乘积、RMSE、约束和硬件复杂度。它不导入、执行或信任 V1–V6 搜索代码，不使用求解器输出的评分函数。

`C:\Users\Lenovo\Downloads\README_LATEST_V6.md` 是用户提供的模型材料，其数值、最优性和运行说明都是待验证声称，不是权威输入。验证器不解释或执行 README、JSON、NPZ 或日志中的命令文本。

当前 `tournament_protocol` 未冻结且冻结校验失败。因此本轮仅交付规格：不创建验证代码，不读取或运行候选，不写入 `05_results/`，不确认 README 中的任何数值。

## 2. 模块边界与 API

### 2.1 预定模块

```text
validator/
  api.py                 # 纯函数入口和结构化报告
  authority.py           # 冻结协议、输入哈希和规则门禁
  npz_io.py              # allow_pickle=False 的受限 NPZ 解析
  target.py              # DFT 与 Kronecker 目标的独立构造
  factor_math.py         # 因子顺序、矩阵乘积和稳定范数
  beta.py                # 实数 beta 的校验与独立解析解
  constraints.py         # 行二稀疏和字母表验证
  hardware.py            # q、L、C 核算
  support_bound.py       # 带 beta 前提的 support 下界
  report.py              # 机器可读报告、字段级证据和哈希
```

以上是未来实现边界，不是本轮已存在代码。模块不得从求解器包导入任何对象，共享类型仅限于验证器自身的无行为数据结构。

### 2.2 核心 API

```python
validate_bundle(request: ValidationRequest) -> ValidationReport
load_factor_bundle(path: Path, limits: LoadLimits) -> FactorBundle
build_target(spec: TargetSpec) -> ComplexArray
multiply_factors(factors: Sequence[ComplexArray]) -> ComplexArray
optimal_real_beta(target: ComplexArray, product: ComplexArray,
                  domain: BetaDomain) -> float
compute_rmse(target: ComplexArray, product: ComplexArray,
             beta: float) -> float
check_constraints(bundle: FactorBundle,
                  policy: ConstraintPolicy) -> ConstraintReport
compute_hardware(bundle: FactorBundle,
                 policy: HardwarePolicy) -> HardwareReport
check_support_certificate(bundle: FactorBundle, target: ComplexArray,
                          beta_policy: BetaPolicy) -> BoundReport
```

`ValidationRequest` 必须包含：因子文件路径及预期 SHA-256、冻结协议和 freeze ID、problem-id、目标类型/维度、约束组合、beta 域与声称类型、q/L 语义、待核对的声称值和数值容差政策。这些字段只能来自已冻结协议或已签署决策；不从 NPZ/README 猜测。

`ValidationReport` 至少包含：

- `status`: `PASS | FAIL | BLOCKED | ERROR`；
- 验证器版本、Git commit、工作树状态和环境摘要；
- 所有输入的相对路径、字节数和 SHA-256；
- 每项检查的 `check_id`、状态、期望、观测、容差和证据定位；
- 独立重算的 beta、RMSE、每因子行非零数、字母表违例、L 和 C；
- support 下界的公式、beta 前提、适用范围和是否可作全局证书；
- 声称对比、失败原因及不受影响的已完成检查。

`PASS` 只表示给定产物在冻结口径下通过独立复算，不自动表示求解器全局最优、竞赛结果冻结或论文可引用。

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
| `K` | int64 scalar | 因子数，与数组第一维一致 |
| `q` | int64 scalar | 与权威外部配置一致；不由系数反推 |
| `beta` | float64 scalar | 有限实数；复数 beta 拒绝 |
| `factors_real` | numeric `(K,N,N)` | 因子实部 |
| `factors_imag` | numeric `(K,N,N)` | 因子虚部 |
| `factor_labels` | Unicode `(K,)` | 顺序标签 `A1`…`AK` |

Kronecker 目标的 `N1` / `N2` 由冻结协议提供，NPZ 可包含同名 int64 标量，但必须与外部值一致。宣称 RMSE、L、C、种子、算法版本和命令放在独立 JSON manifest，不作 NPZ 数学输入。

对需验证约束 2 的产物，`factors_real` 和 `factors_imag` 必须是整数 dtype；不接受“接近整数”的浮点容差。仅约束 1 的产物可使用 float64，但零判定策略必须在冻结协议中明确。

验证报告同时记录原始 NPZ SHA-256 和规范因子摘要（按固定字节序、shape 和 dtype 哈希），以避免 NPZ 压缩元数据差异影响内容同一性判定。

## 4. 独立数学复算

### 4.1 DFT 与 Kronecker 目标

对 `N x N` 单位化 DFT：

```text
F_N[k,n] = exp(-2*pi*j*k*n/N) / sqrt(N),  k,n = 0,...,N-1.
```

验证器固定使用负号指数、0 起始索引和 `1/sqrt(N)` 归一化。对问题 4 使用 `F_N1 ⊗ F_N2`，目标方阵维度 `N=N1*N2`，RMSE 分母是实际方阵维度 `N`。构造后先检查 `FᴴF ≈ I` 与 `||F||_F² ≈ N`。

### 4.2 因子乘积顺序

```text
P = A1 @ A2 @ ... @ AK
```

NPZ 第 0 层是 `A1`，不根据搜索器内部的“前向/反向应用”称呼猜测顺序。每个因子必须是有限 `N x N` 复数方阵；不在因子链内隐式吸收排列、对角阵或 beta。

### 4.3 beta 与 RMSE

题面方向固定为：

```text
RMSE(beta) = || beta*F - P ||_F / N,
```

其中 beta 是实数。若 beta 在全体实数上自由，独立解析最优解为：

```text
beta_ls = Re(<F,P>_F) / ||F||_F^2,
<F,P>_F = sum(conj(F[k,n]) * P[k,n]).
```

如 beta 域是已冻结闭区间或离散集，则在该域上对 `beta_ls` 投影/枚举；未冻结的符号、下界或归一化约束不可由验证器补齐。

验证分为两层：

1. 使用 NPZ 声称 beta 独立计算 RMSE，与日志/报告声称值比较。
2. 仅当声称为“beta 已最优化”时，按冻结 beta 域重算 `beta_ls`，并检查目标值不大于同域可比值。

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

### 5.3 L 与 C

题面免计数系数集合为：

```text
FREE = {0, +1, -1, +j, -j, +1+j, +1-j, -1+j, -1-j}.
```

候选因子在线应用到中间向量时，推荐口径是：

```text
L_factor_apply = sum_k count(Ak entries not in FREE),
C = q * L_factor_apply.
```

beta 不计入 C，因为题面的 C 仅对因子矩阵定义；如后续权威决策要求计入 beta，必须更改协议并重走冻结。

题面的两矩阵手算例按“当前矩阵乘法中实际非平凡标量乘法”可得 L=2，它与“固定因子对未知向量的运行时成本”不是显然同一的计数对象。因此正式验证前，冻结协议必须声明 `l_semantics`。若为 `factor_apply`，使用上述按因子元素累加的定义；若为其他口径，必须提供逐项算法和手算 fixture。缺失 `l_semantics` 时复杂度结论 `BLOCKED`，不默认挑选有利口径。

## 6. support 下界与 beta 的必要前提

若每个因子每行最多 2 个非零元素，则 K 个因子乘积 P 的每行 support 最多：

```text
s = min(N, 2^K).
```

因为单位化 DFT 每个元素的模为 `1/sqrt(N)`，对一个固定 beta：

```text
RMSE(beta) >= |beta| * sqrt(max(N - 2^K, 0)) / N.
```

证明使用每行至少 `N-s` 个乘积零元素：这些位置每个贡献 `|beta|²/N` 的平方误差。

因此，README 中不含 beta 的形式

```text
sqrt(N - 2^K) / N
```

只有在下列条件下才能按其声称的强度成立：

- `|beta| = 1` 时精确得到该形式；或
- 对所有可行解都有已冻结且可证明的 `|beta| >= 1`，则它是一个较弱但有效的统一下界。

更一般地，若对全部可行解仅能证明 `|beta| >= beta_min > 0`，则统一下界必须乘以 `beta_min`。一个已知产物的 `beta_hat` 只能给出该产物的事后下界；除非 `|beta_hat|` 同时是全部可行解的统一下界，否则不能用于证明 K 全局最小。

若 beta 是可自由优化的实数并允许 0，则取 `P=0, beta=0` 已使题面 RMSE 为 0，任何正的、不含 beta 的 support 下界都不成立。即使只排除 beta=0 但允许 `|beta|` 任意接近 0，也不存在正的统一 support 下界。

所以，验证器在 beta 域/归一化条件未由权威输入冻结时，必须对任何 `K*`、support gap 或由此导出的最优性证书判为 `BLOCKED`。

## 7. 必须的手算回归测试

1. **DFT 符号和 beta 方向**：`N=2`，`F2=(1/sqrt(2))*[[1,1],[1,-1]]`，取 `A1=[[1,1],[1,-1]]`、`beta=sqrt(2)`，应得 RMSE=0。`A1` 每行 nnz=2；当 q=1 且字母表为幂次集时，字母表合法且按 `factor_apply` 得 L=0、C=0。
2. **非交换顺序**：用两个 `2x2` 非交换手算矩阵验证产物严格是 `A1@A2`，与 `A2@A1` 不等；标签与数组轴顺序错位必须 FAIL。
3. **题面复乘例**：对题面给定的两矩阵按“实际标量乘法”手算口径得 L=2、q=3、C=6；另单独测试 `factor_apply` 口径，防止两种语义在代码中混合。
4. **行二稀疏**：包含两个免计数非零元素的行合法；再加一个 `1` 后因 nnz=3 失败，即使 L 仍为 0。
5. **字母表**：q=3 时实/虚分量集为 `{0,±1,±2,±4}`；`2+4j` 合法，`3+0j`、浮点 `1+epsilon` 和 `8+0j` 失败。
6. **FREE 集合**：9 个元素均不计入 L；`2`、`2j`、`1+2j` 各计一次。q=1 的合法复系数全部属于 FREE，因此按 `factor_apply` 任意合法因子链都应 L=0。
7. **实数 beta 解析解**：对小型复数 F/P 手算 `Re(<F,P>)/||F||²`，验证残差对 beta 的实内积为 0，且 beta 左右小扰动不降低目标。
8. **support 下界**：固定 `|beta|=1` 时构造每行只保留 s 个 DFT 元素的 P，验证边界取等；再用 `P=0,beta=0` 验证不含 beta 的正下界必须被拒绝。
9. **NPZ 拒绝路径**：object dtype、缺键、多键、shape/dtype 不匹配、NaN/Inf、q 不一致和超限数组都不得进入数学复算。

## 8. 属性测试

属性测试使用固定测试种子，只在系统临时目录生成小型 synthetic 矩阵，不写 `05_results/`。

- 对多个小 N，`FᴴF≈I`、`||F||_F²≈N`，且 Kronecker 目标等于直接索引式。
- 对任意有限 F/P，RMSE 非负，`beta_ls` 不劣于同域中的随机 beta；无约束情况满足一阶正交条件。
- 对任意行二稀疏 K 层因子，乘积每行 support 不超过 `min(N,2^K)`；取消可以减少但不能增加该上界。
- q 每增加 1，幂次字母表严格包含前一字母表；集合成员检查与元素顺序、稠密/稀疏存储无关。
- L 对因子元素的行/列排列不变，等于各因子非 FREE 元素数之和；`C=qL` 是 q 的非负整数倍。
- 规范 NPZ 经过解析—再序列化后，规范因子内容摘要不变；不要求 ZIP 容器原始字节相同。
- 将任一因子的一个元素改为 NaN/Inf、越界字母或第三个非零元素时，结果不可 PASS；初始的其他检查证据仍保留。
- 对任意固定 beta，实际 RMSE 不小于带 `|beta|` 的 support 下界；将 beta 缩放为 a 倍时，下界也按 `|a|` 缩放。

## 9. 失败关闭规则

### 9.1 状态

- `BLOCKED`：权威输入、冻结、beta/q/L 语义、文件或数值精度不足，无法完成必需验证。
- `FAIL`：文件解析后数学对象或声称与冻结规则不一致，如违约、哈希错、声称数值超容差或无效下界。
- `ERROR`：验证器自身未捕获错误或环境故障；与 FAIL 分开，不得当作候选失败。
- `PASS`：所有必需检查都是 PASS，且没有 BLOCKED/ERROR。

聚合优先级为 `ERROR > BLOCKED > FAIL > PASS`，但报告必须保留全部子项状态，不因先发失败而静默删除可安全执行的其他检查。

### 9.2 不可放行的情形

- 协议未冻结、freeze ID/哈希漂移或问题规格缺失；
- NPZ 需要 pickle、schema 未知、键/shape/dtype 不一致或输入哈希不符；
- 因子不是有限方阵、乘法顺序不明、beta 非实数或目标方向不同；
- 稀疏/字母表违例，q 或 l_semantics 未权威固定，或声称 L/C 与复算不符；
- 声称为可行解的 RMSE 超出冻结阈值，或声称值与独立重算超出容差；
- 在没有统一 beta 下界时用不含 beta 的 support 下界证明 K 或 gap 最优；
- 只提供最终数字而无因子、种子、参数、日志、代码/环境哈希和失败运行记录。

## 10. 实现放行条件

只有在以下条件全部满足后，计算 Agent 才开始实现本验证器：

1. `tournament_protocol` 冻结校验 PASS，并明确 beta 域/归一化、字母表、q、L 口径和容差；
2. 题面来源与输入 manifest 达到工作流要求；
3. `V6_REQUIRED_INPUTS.md` 中 P0/P1 材料齐全并有 SHA-256；
4. 总控确认本规格与冻结协议一致。

任一条未满足都保持 `NOT_RUN/BLOCKED`，不以 README 声称替代机器冻结和原始证据。
