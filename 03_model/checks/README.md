# `03_model/checks/` 来源与复算说明

## 来源

本目录最初由 `agent/modeling` 的提交 `80ec0bd8365f76aa8e035680140516de8c05b23d`（2026-09-14）加入，用于核验 V6 材料涉及的行支持下界、尺度退化和 DFT 构造。它属于建模 Agent 的 `03_model/` 写入范围，不是外部 V5/V6 工程包，也不是计算 Agent 的正式实验。

后续审计确认该方向有价值，但初版存在三类实质问题：

1. 用复数浮点值精确比较免费集合，误把数值近似的 `±j` 计入 `L`；
2. 把因子整体缩放后仍沿用未缩放因子的 `L`，而缩放会改变系数是否免费；
3. 式 (5) 的 `A2` 后四行转录错位，并据此产生错误的秩亏解释。

`5992431` 已修正这些问题，并把比特反转排列吸收到第一个蝶形层，使问题 1 的非零精确构造使用 `K=log2(N)`、`β=√N`，且不改变原始扭因子系数。

## 文件

| 文件 | 说明 |
| --- | --- |
| `verify_row_bound.py` | 冻结基线复算程序；含确定性断言，任一强制检查失败时退出码为 1。**已被 `00_admin/freezes/tournament_protocol.json` 的 SHA-256 绑定，D-012 冻结后不得修改。** |
| `row_bound_results.json` | 上者生成的机器可读证据；`artifact_class=modeling_check`、`formal_experiment=false`。 |
| `verify_row_bound_audit.py` | 冻结协议的**只读**一致性审计器（哈希/大小/依赖/引用行号自检），不修改任何冻结文件。 |
| `row_bound_audit_results.json` | 上者的输出。 |
| `verify_structural_bounds.py` | 结构不等式的核验与**证伪**记录（行支持传播成立、列支持传播与计数式收紧均被证伪）。 |
| `structural_bounds_results.json` | 上者的输出。 |
| `verify_row_relaxation_bounds.py` | 下界可用性审计：证明在冻结语义下 `K >= 2` 时经典支持下界是唯一非平凡证书。 |
| `row_relaxation_bounds.json` | 上者的输出。 |

## 运行

```powershell
python -X utf8 03_model/checks/verify_row_bound.py
python -X utf8 03_model/checks/verify_structural_bounds.py
python -X utf8 03_model/checks/verify_row_relaxation_bounds.py
```

三者都从任意当前目录运行并把 JSON 写回本目录。成功标准：退出码 0、顶层 `status` 为 `PASS`、`failed_checks` 为空。

## 证据边界

- 可核验：单位化 DFT 与 Kronecker 目标、行支持传播、问题 1 的 radix-2 非零精确构造、固定 `β` 的支持下界、尺度退化、提取稿式 (5) 的印刷顺序复算、冻结清单哈希与协议引用行号。
- **已验证的下界只有一个**：`RMSE >= sqrt(N - min(N,2^K))/N`（`β=1`）。它在 `2^K >= N` 时退化为 0。其他候选证书（列支持传播、计数式收紧、系数幅值上限）已在本目录被证明无效或平凡，见 `structural_bounds_results.json` 的 `falsified` 字段与 `row_relaxation_bounds.json` 的 `headline`。
- 不可核验：用户 README 中的 V4–V6 搜索值及 `current_best`；本目录没有 V5 因子、NPZ、搜索源码或日志。
- 本目录的 JSON 都不是 `05_results/` 正式结果，不得用它们跳过题面、检索、协议与对擂门禁。
- `__pycache__/`、`*.pyc`、临时日志均为可再生缓存，不得提交。
