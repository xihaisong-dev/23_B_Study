# V6 独立验证所需输入提案

## 1. 提案目的

本清单定义开始 V6 验证器实现、历史谱系审计和正式复现前需要的原始材料。用户提供的 `C:\Users\Lenovo\Downloads\README_LATEST_V6.md` 仅是索引和待验证声称；其中的命令不执行，其列出的目录不视为文件已提供。

当前仓库未包含 V1–V6 源码、V5 factors NPZ、V6 原始日志或依赖文件，且 `tournament_protocol` 冻结校验失败。因此正式状态保持 `BLOCKED/NOT_RUN`。

## 2. 优先级定义

- **P0—正式门禁**：缺失则不能开始正式验证实现或任何数值复现。
- **P1—V5/V6 核验核心**：缺失则不能独立核验当前因子、RMSE、约束或 V6 搜索证据。
- **P2—谱系与比较**：缺失不一定阻断单个 V5 因子的纯数学核算，但阻断 V1→V6 演化、改善幅度和算法复现声称。

## 3. P0：权威语义和冻结输入

| 需要材料 | 最小内容 | 完整性/哈希要求 | 缺失影响 |
| --- | --- | --- | --- |
| 有效的 `tournament_protocol` 冻结 | 问题 1–5 候选、目标、约束、beta 域、q、L 语义、种子、预算、容差、平局和失败规则 | freeze ID、递归 SHA-256 清单与 `verify-freeze` PASS | 不能实现权威口径；所有验证/experiment 继续 `BLOCKED` |
| 已核验题面与 input manifest | 官方来源、数据类别、本地路径和 SHA-256 | 来源、获取时间、文件大小、SHA-256 | 只能做非正式结构检查，不能冻结比赛结论 |
| beta 定义/归一化裁决 | 明确是 `beta*F-P`，beta 是否允许 0、符号/区间/归一化条件以及是否优化 | 写入协议或签署 `DECISIONS.md`，并纳入冻结 | RMSE 可退化为 `P=0,beta=0`；support/K 下界和最优性证书无法成立 |
| 字母表与 L 计数裁决 | `P(q)` 是幂次集还是整数区间；`l_semantics`；beta/排列/对角因子是否计费 | 书面算法、手算 fixture、协议哈希 | 无法对 q/L/C 作 PASS/FAIL 判定 |

## 4. P1：V5 当前因子与产生证据

| 需要材料 | 最小内容 | 完整性/哈希要求 | 缺失影响 |
| --- | --- | --- | --- |
| V5 factors NPZ | README 指向的 `results/current_best/P5-V5_N64_factors.npz` 原文件 | 文件大小、SHA-256、NPZ 键/shape/dtype/schema；必须可用 `allow_pickle=False` 读取 | 无法复算因子乘积、beta、RMSE、行稀疏、字母表、L 或 C |
| V5 源码 | 主脚本、导入的本地模块、配置、产物导出代码和测试 | 最好提供 Git commit/tag；否则提供只读归档及递归 SHA-256 manifest | 可能核验 NPZ 数学性质，但不能复现其生成、排查隐藏投影/修复或确认版本 |
| V5 原始运行记录 | 命令参数、所有种子/重启、stdout/stderr、开结束时间、失败运行、候选汇总 | 记录文件 SHA-256，与 NPZ 及源码提交双向引用 | 无法确认 NPZ 来历、选择偏差、种子覆盖或运行失败 |
| V5 声称 manifest | problem-id、N/K/q、beta、RMSE、L/C、约束、评分方向、容差、因子顺序 | JSON schema、SHA-256，每个声称指向源文件/日志 | 验证器可计算数字，但不知要核对的精确声称与口径 |

NPZ 若是旧 schema，还需要一份无歧义的键映射说明和安全转换脚本。不接受仅截图、仅打印的矩阵或需要 pickle 才可读的产物。

## 5. P1：V6 源码、配置与日志

| 需要材料 | 最小内容 | 完整性/哈希要求 | 缺失影响 |
| --- | --- | --- | --- |
| V6 源码 | `dft_integer_factor_optimized_v6.py`、全部本地导入、共用 V1–V5 模块、辅助实验脚本和测试 | Git commit/tag 或递归 SHA-256 manifest；保留原始目录结构 | 无法审计 block lower bound、剪枝安全性、tabu/ejection 流程、约束修复和评分口径 |
| 启动器与配置 | README 指向的 Windows/Linux 脚本、配置文件和默认值来源 | 只作文本审计；命令不执行；记录 SHA-256 | 无法确认 README 命令是否等价于实际运行或是否遗漏隐式默认值 |
| V6 全部原始日志 | 每个种子/重启的 stdout/stderr、返回码、时间/内存、候选接受/拒绝、剪枝统计、下界记录、最终因子及失败运行 | 不覆盖原始日志；文件级 SHA-256；与 run-id/代码/NPZ 对应 | 无法核验“V6 未优于 V5”是完整实验结论，也无法审计 B&B 证据是下界还是 oracle/连续松弛 |
| 精确参数 | 除 README 中的 seeds、chain-len、block-sample、exact-blocks、top-x、top-y、uphill-budget、polish-sweeps 外，还要求所有默认值、预算、超时、重启、剪枝容差和停机条件 | 与每个 run-id 绑定的规范 JSON 及 SHA-256 | 无法等口径复现，也无法排除结果后调参 |
| 随机性记录 | 根种子、每轮派生种子、Python/NumPy/其他后端 RNG、候选枚举顺序与并行调度设置 | 每个 run-id 独立记录，不仅在 README 列出三个数字 | 无法逐运行复现，并行非确定性可能被误归因为算法改善 |

## 6. 依赖和环境

| 需要材料 | 最小内容 | 完整性/哈希要求 | 缺失影响 |
| --- | --- | --- | --- |
| `requirements.txt` 与锁定信息 | 所有直接/间接包的精确版本，最好包含 wheel 哈希 | 原文件 SHA-256；若只有范围版本，追加实际 `pip freeze` | 无法重建数值环境，也无法判断 API/算子版本漂移 |
| Python/平台 | Python 完整版本、OS/build、CPU 型号、逻辑核、RAM | 来自原运行环境的机器可读快照 | 无法核对性能预算或硬件相关数值差异 |
| 数值后端 | NumPy/SciPy/优化器版本，BLAS/LAPACK vendor 与版本 | 环境快照与运行日志关联 | 连续松弛、排序/剪枝和近阈值结果可不可复现 |
| 确定性设置 | OMP/MKL/OpenBLAS 线程数、hash seed、GPU/CUDA 确定性开关（如适用） | 实际值，不只是建议值 | 同种子也可能分歧，不能声称逐字节复现 |

不以直接在当前机器安装未知依赖的方式反推环境。用户材料先以只读归档进入隔离审计，待协议冻结和依赖确认后再建立可复现环境。

## 7. P2：V1–V4 与历史谱系

对 V1、V2、V3、V4 每一版都需要：

- 完整源码、本地导入、配置、测试和可读运行入口；
- 版本间父子关系（Git commit/tag 或书面 mapping）；
- 该版本所用的输入因子、输出因子、参数/种子、原始日志和失败运行；
- 版本声称的 RMSE/K/q/L/C 及其原始机器产物；
- 递归文件 manifest，至少记录相对路径、字节数和 SHA-256。

缺失 V1–V4 不阻断对已提供 V5 NPZ 的静态数学验证，但会阻断：

- README 中 V1→V6 演化路径的事实核对；
- 任何“比前版改善”或消融归因；
- 判断 V5/V6 是否继承了口径变更、未记录修复或结果后调参。

## 8. V6 下界和 B&B 专项证据

README 明示 V6 使用连续松弛和 block lower bound。要审核其下界或剪枝正确性，还需要：

- 松弛问题的完整数学定义、原问题到松弛的包含关系证明；
- 每个 block 的输入状态、计算下界、incumbent、剪枝差额和精度容差；
- 在下界非精确时的保守舍入方向和求解器状态；
- oracle/连续解、重新离散化后解和最终可行因子的不同 ID，严禁混用；
- 被剪枝节点和完整枚举节点的可追溯计数。

缺失上述材料时，最多只能验证最终因子是否可行，不能将连续松弛数值或搜索日志当作全局最优性证书。

## 9. 接收格式与最小交付包

建议由总控在一个只读交付目录中提供：

```text
V6_SOURCE_PACKAGE/
  MANIFEST.sha256.json
  README_LATEST_V6.md
  requirements.txt
  environment.json
  code/v1/ ... code/v6/
  tests/
  configs/
  artifacts/v5/current_best_factors.npz
  artifacts/v5/claim_manifest.json
  logs/v1/ ... logs/v6/
  runs/<run-id>/run_manifest.json
  docs/beta_and_cost_semantics.md
  docs/v6_relaxation_and_bnb_proof.md
```

`MANIFEST.sha256.json` 至少对每个文件记录相对路径、字节数、SHA-256、版本和数据类别。压缩包只作传输容器；解包后重算文件哈希，不信任容器中的绝对路径、链接或脚本。

在 P0 和 P1 材料齐全之前，计算 Agent 不创建正式代码、不运行 README 命令、不安装未锁定依赖，也不为 README 数值生成任何 PASS 记录。
