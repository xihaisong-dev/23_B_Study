# `03_model/checks/` 来源与复算说明

## 来源

本目录最初由 `agent/modeling` 的提交 `80ec0bd8365f76aa8e035680140516de8c05b23d`（2026-09-14）加入，用于核验 V6 材料涉及的行支持下界、尺度退化和 DFT 构造。它属于建模 Agent 的 `03_model/` 写入范围，不是外部 V5/V6 工程包，也不是计算 Agent 的正式实验。

后续审计确认该方向有价值，但初版存在三类实质问题：

1. 用复数浮点值精确比较免费集合，误把数值近似的 `±j` 计入 `L`；
2. 把因子整体缩放后仍沿用未缩放因子的 `L`，而缩放会改变系数是否免费；
3. 式 (5) 的 `A2` 后四行转录错位，并据此产生错误的秩亏解释。

当前版本已修正这些问题，并把比特反转排列吸收到第一个蝶形层，使问题 1 的非零精确构造使用 `K=log2(N)`、`β=√N`，且不改变原始扭因子系数。

## 文件

- `verify_row_bound.py`：纯标准库复算程序；含确定性断言，任一强制检查失败时退出码为 1。
- `row_bound_results.json`：脚本生成的机器可读证据；`artifact_class=modeling_check`、`formal_experiment=false`。

## 运行

```powershell
python -X utf8 03_model/checks/verify_row_bound.py
```

脚本从任意当前目录运行都把 JSON 写回本目录。成功标准：退出码 0、顶层 `status` 为 `PASS`、`failed_checks` 为空。

## 证据边界

- 可核验：单位化 DFT 与 Kronecker 目标、支持/秩传播、问题 1 的 radix-2 非零精确构造、固定 `β` 的支持下界、尺度退化、提取稿式 (5) 的印刷顺序复算。
- 不可核验：用户 README 中的 V4–V6 搜索值及 `current_best`；本目录没有 V5 因子、NPZ、搜索源码或日志。
- `row_bound_results.json` 不是 `05_results/` 正式结果，不得用它跳过题面、检索、协议和对擂门禁。
- `__pycache__/`、`*.pyc`、临时日志均为可再生缓存，不得提交。
