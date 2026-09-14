# DFT 稀疏分解本地知识库

本目录只保存论文原文及机械提取文本，供 `02_retrieval/retrieval_manifest.json` 建立可追溯 KBREF。论文中的算法、参数和数值不能直接当作本题结果。

| ID | 论文 | 原始来源 | PDF SHA-256 | 主要用途 |
| --- | --- | --- | --- | --- |
| `KB-FFT-1965` | Cooley & Tukey, *An Algorithm for the Machine Calculation of Complex Fourier Series* | `https://web.stanford.edu/class/cme324/classics/cooley-tukey.pdf` | `b4fa04410bcbf324eca035ab9d94818f075cee2f2ae38e99ebb0e2348e64654a` | radix 分解、蝶形基线；PDF 为扫描件，文本提取不可用 |
| `KB-SP2-2020` | Müller, Gäde & Bereyhi, *Efficient Matrix Multiplication: The Sparse Power-of-2 Factorization* | `https://arxiv.org/pdf/2002.04002` | `a02d6794d3be302b42708df120e60a254f131b33c8f0b6812ab93d5cf412278d` | 二次幂离散系数与稀疏因子 |
| `KB-MLSA-2016` | Le Magoarou & Gribonval, *Flexible Multi-layer Sparse Approximations of Matrices and Applications* | `https://arxiv.org/pdf/1506.07300` | `92cb10524d7dd1d447460d805d852b731c5bb1b54d8254b43ce8eda81bb68c40` | 多层稀疏矩阵交替优化 |
| `KB-BFLY-2019` | Dao et al., *Learning Fast Algorithms for Linear Transforms Using Butterfly Factorizations* | `https://arxiv.org/pdf/1903.05895` | `eb245fa1bb8073ab830def648538e0eb2389ba54e5fe059c2f63f9fbf7970d1d` | Butterfly 参数化与 FFT 可表示性 |

除 Cooley–Tukey 扫描件外，每份 PDF 均有同名 `.txt` 机械提取稿。引用与判断必须回查 PDF 上下文。
