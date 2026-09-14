# 最新建模工程交接说明（V6）

## 1. 当前可信结论

本工程针对 2023 华为杯 B 题“DFT 类矩阵的整数分解逼近”。

目前问题5在 `N=64` 下的**最佳可信可行解**仍来自 V5：

- `q = 1`
- `K = 5`
- `L = 0`
- `C = qL = 0`
- `RMSE = 0.09049305675445285`

严格 support 下界：

- `RMSE_LB = 0.08838834764831845`
- absolute gap = `0.002104709106134403`
- relative gap = `2.325823860548105%`

因此当前能够严格证明：

- `C* = 0`
- `K* = 5`
- 固定 `K=5` 时，RMSE 仍未证明全局最优；当前上界为 `0.09049305675445285`。

**重要：V6 已实现并测试更大的联合邻域，但尚未产生优于 V5 的可行 RMSE。**
所以交付包中把 V5 factors 标记为 `current_best`，V6 作为最新搜索算法与实验依据保留。

---

## 2. V1 -> V6 的模型演化

### V1：结构化基础模型
- Cooley-Tukey / radix-2 稀疏分解
- 离散整数投影
- 解析消去整体缩放
- epsilon-constraint 形式处理问题5

### V2：可变 XOR 蝶形 + Beam/DP
- XOR perfect matching topology
- Beam Search
- Pareto pruning
- stage complexity DP
- `C>=0` 下界与 `C=0` 最优证书

### V3：一般 Perfect Matching + K 下界
- 从 XOR 扩展到一般 perfect matching 候选
- bound-guided Beam/A*-like
- support/rank lower bound
- 把 permutation 吸收到最后一级
- 建立 `K` 的严格 support 下界

### V4：General row-2-sparse
- 相邻两级压缩，将 N=64 从 `K=6` 压到 `K=5`
- 不再局限 perfect matching
- general row-2-sparse coordinate descent
- 证明 N=64 下 `K*=5`
- V4 RMSE: `0.0908281665`

### V5：离散平台搜索
- top-M 单行候选
- neutral plateau walk
- strict row-2 polish
- RMSE 降至 `0.09049305675445285`
- 严格相对 gap 降至约 `2.3258%`

### V6：两行/两层联合块 + 支持重连 Branch-and-Bound
最新代码加入：
- adjacent two-layer block-coordinate update
- 对第一层 row-2 候选的完整离散枚举
- 对第二层采用连续松弛建立严格 block lower bound
- lower-bound 排序与剪枝
- tabu / ejection-chain
- 小幅近中性或微上坡结构重连后重新 strict polish

当前实验尚未得到比 V5 更低的可行 RMSE，因此不能把连续松弛或 oracle 数值当成最终解。

---

## 3. 当前推荐的论文主模型

建议正式论文把算法统一表述为：

**基于层级稀疏分解、一般行二稀疏结构优化与下界引导块搜索的 DFT 整数矩阵逼近模型**

问题5使用字典序 / epsilon-constraint：

1. 最小化 `C`
2. 在最小 `C` 下最小化 `K`
3. 在最小 `(C,K)` 下最小化 `RMSE`

即当前 N=64 主问题可写成：

`min RMSE  s.t. C=0, K=5, 每个因子每行<=2非零, 系数满足q=1免费集合`

---

## 4. 当前最优性证书

每个因子每行最多2个非零，因此 K 个因子相乘后每行支持数最多 `2^K`。

对于单位化 DFT，若 `2^K < N`，得到：

`RMSE_K >= sqrt(N - 2^K) / N`

N=64：

- K=4: `sqrt(48)/64 ≈ 0.108253 > 0.1`
- 因此满足 RMSE<=0.1 必须 `K>=5`
- 当前已有 `K=5, C=0, RMSE<0.1` 可行解
- 所以 `K*=5`
- 又因为 `C=qL>=0` 且已有 `C=0` 可行解，所以 `C*=0`

固定 K=5：

`RMSE >= sqrt(32)/64 = 0.08838834764831845`

当前：

`0.08838834764831845 <= RMSE* <= 0.09049305675445285`

---

## 5. V6 的正确使用方式

Windows：

双击：

`run_v6_windows.bat`

或命令行：

```bash
python code/dft_integer_factor_optimized_v6.py ^
  --parent-npz results/current_best/P5-V5_N64_factors.npz ^
  --seeds 17,43,71 ^
  --chain-len 3 ^
  --block-sample 50 ^
  --exact-blocks 4 ^
  --top-x 40 ^
  --top-y 8 ^
  --uphill-budget 8e-5 ^
  --polish-sweeps 2 ^
  --outdir results/v6_new
```

Linux：

```bash
bash run_v6_linux.sh
```

---

## 6. 目录

```text
DFT_latest_modeling_V6/
├─ README_LATEST_V6.md
├─ requirements.txt
├─ run_v6_windows.bat
├─ run_v6_linux.sh
├─ code/
│  ├─ dft_integer_factor_optimized.py
│  ├─ dft_integer_factor_optimized_v2.py
│  ├─ ...
│  └─ dft_integer_factor_optimized_v6.py
├─ docs/
│  └─ V1~V5 历史说明
├─ results/
│  ├─ current_best/       # 当前可信最优：V5
│  ├─ v6_block_bnb/       # V6 搜索结果与B&B证据
│  └─ validation/         # N=2~64验证与版本对比
├─ experiments/
│  └─ scripts/            # V6 辅助实验脚本
└─ references/
   ├─ 原赛题
   └─ 三篇参考论文
```

---

## 7. 下一阶段

当前不建议继续主要做 coefficient tuning。

更值得做的是针对最终 support pattern 的大邻域结构优化，例如：

- depth-2 / depth-3 subtree reconnect
- Boolean support factorization
- multi-block ejection chain
- support-targeted branch-and-bound

目标是在保持：

`C=0, K=5`

不变的条件下，把 RMSE 从 `0.090493...` 推入 `0.089x`。

同时应保持一个原则：

**连续松弛、oracle、lower bound 只能作为下界/诊断；只有重新满足全部离散约束并重新计算完整矩阵 RMSE 的结果，才能报告为可行解。**
