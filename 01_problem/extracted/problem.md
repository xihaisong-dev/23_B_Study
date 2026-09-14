2023年中国研究生数学建模竞赛B题（华为题目）

**DFT类矩阵的整数分解逼近**

## 一、问题背景

离散傅里叶变换（Discrete Fourier Transform，DFT）作为一种基本工具广泛应用于工程、科学以及数学领域。例如，通信信号处理中，常用DFT实现信号的正交频分复用（Orthogonal Frequency Division Multiplexing，OFDM）系统的时频域变换（见图1）。另外在信道估计中，也需要用到逆DFT（IDFT）和DFT以便对信道估计结果进行时域降噪（见图2）。

<img src="01_problem\extracted/media/image1.png" style="width:4.36806in;height:2.81885in" />

图1 OFDM系统流程

<img src="01_problem\extracted/media/image2.png" style="width:5.07826in;height:0.48693in" />

图2 信道估计处理流程

在芯片设计中，DFT计算的硬件复杂度与其算法复杂度和数据元素取值范围相关。算法复杂度越高、数据取值范围越大，其硬件复杂度就越大。目前在实际产品中，一般采用快速傅里叶变换（Fast Fourier Transform，FFT）算法来快速实现DFT，其利用DFT变换的各种性质，可以大幅降低DFT的计算复杂度（参见[\[1\]](#_Ref142986454)[\[2\]](#_Ref143019309)）。然而，随着无线通信技术的演进，天线阵面越来越大，通道数越来越多，通信带宽越来越大，对FFT的需求也越来越大，从而导致专用芯片上实现FFT的硬件开销也越大。为进一步降低芯片资源开销，一种可行的思路是将DFT矩阵分解成整数矩阵连乘的形式。

给定$`N`$点的时域一维复数信号$`x_{0},x_{1},\ldots,x_{N - 1}`$，DFT后得到的复数信号$`X_{k}`$（$`k = 0,1,\ldots,N - 1`$）由下式给出（其中*j*为虚数单位，下同）：

``` math
\begin{array}{r}
X_{k} = \sum_{n = 0}^{N - 1}{x_{n}*e^{- \frac{j2\pi nk}{N}}}\ \ ,k = 0,1,2,\ldots,N - 1\#(1)
\end{array}
```

写成矩阵形式为：

``` math
\begin{array}{r}
\mathbf{X}\mathbf{=}\mathbf{F}_{N}\mathbf{x}\mathbf{\#}(2)
\end{array}
```

其中**x**$`= {\lbrack x_{0}\ \ x_{1}\ \cdots\ \ x_{N - 1}\rbrack}^{T}`$为时域信号向量，$`\mathbf{X} = {\lbrack X_{0}\ \ X_{1}\ \cdots\ \ X_{N - 1}\rbrack}^{T}`$为变换后的频域信号向量，$`\mathbf{F}_{N}`$为DFT矩阵，形式如下：

``` math
\begin{array}{r}
\mathbf{F}_{N} = \frac{1}{\sqrt{N}}\begin{bmatrix}
1 & 1 & 1 & \cdots & 1 \\
1 & w & w^{2} & \cdots & w^{N - 1} \\
1 & w^{2} & w^{4} & \cdots & w^{2(N - 1)} \\
 \vdots & \vdots & \vdots & \ddots & \vdots \\
1 & w^{N - 1} & w^{2(N - 1)} & \cdots & w^{(N - 1)(N - 1)}
\end{bmatrix},w = e^{- \frac{j2\pi}{N}}\mathbf{\#}(3)
\end{array}
```

由于DFT矩阵的特殊结构，存在很多方法加速傅里叶变换的计算，其中，分治的策略以及蝶形计算单元的优化是DFT性能的关键。下面分别给出用FFT和矩阵连乘拟合近似计算DFT的具体思路。

**FFT思路**：FFT采用蝶形运算的思想，以radix-3蝶形计算为例，其计算过程可以表示为：

``` math
\begin{array}{r}
\begin{bmatrix}
X_{0} \\
X_{1} \\
X_{2}
\end{bmatrix} = \begin{bmatrix}
1 & 0 & 0 \\
1 & - 3 & - 1 \\
1 & - 3 & 1
\end{bmatrix}\begin{bmatrix}
1 & 1 & 0 \\
0 & \frac{1}{2} & 0 \\
0 & 0 & \frac{\sqrt{3}j}{2}
\end{bmatrix}\begin{bmatrix}
1 & 0 & 0 \\
0 & 1 & 1 \\
0 & 1 & - 1
\end{bmatrix}\begin{bmatrix}
x_{0} \\
x_{1} \\
x_{2}
\end{bmatrix}\#(4)
\end{array}
```

可以看到蝶形的设计相对于直接DFT矩阵乘积的形式大幅降低了复数乘法运算的次数。

**矩阵连乘拟合思路**：DFT可以用传统的蝶形计算方法精确实现，也可以用一种矩阵乘法拟合近似获得，其核心思想是将DFT矩阵近似表达为一连串稀疏的、元素取值有限的矩阵连乘形式。以radix-8蝶形计算为例（参见[\[3\]](#_Ref142571015)）：

``` math
\begin{array}{r}
\mathbf{F}_{8}\mathbf{\approx}\mathbf{P}\mathbf{A}_{4}\mathbf{D}\mathbf{A}_{3}\mathbf{A}_{2}\mathbf{A}_{1}\mathbf{\#}(5)
\end{array}
```

其中$`\mathbf{P} = \left\lbrack e_{0}\ e_{4\ }e_{2}\ e_{5}\ e_{1}\ e_{7}{\ e}_{3}\ e_{6} \right\rbrack`$为排列矩阵，$`\mathbf{D} = diag\left( \lbrack 1\ 1\ 1\ j\ 1\ j\ j\ 1\rbrack \right)`$为对角阵，$`\mathbf{A}_{1}`$~$`\mathbf{A}_{4}`$为稀疏矩阵，分别如下：

``` math
\mathbf{A}_{1} = \begin{bmatrix}
1 & & & & 1 & & & \\
 & 1 & & & & 1 & & \\
 & & 1 & & & & 1 & \\
 & & & 1 & & & & 1 \\
1 & & & & - 1 & & & \\
 & 1 & & & & - 1 & & \\
 & & 1 & & & & - 1 & \\
 & & & 1 & & & & - 1
\end{bmatrix}\mathbf{,\ A}_{2} = \begin{bmatrix}
1 & & 1 & & & & & \\
 & 1 & & 1 & & & & \\
1 & & - 1 & & & & & \\
 & 1 & & - 1 & & & & \\
 & & & & 1 & & & \\
 & & & & & 1 & & 1 \\
 & & & & & & 1 & \\
 & & & & & 1 & & - 1
\end{bmatrix}
```

``` math
\mathbf{A}_{3} = \begin{bmatrix}
1 & 1 & & & & & & \\
1 & - 1 & & & & & & \\
 & & 1 & & & & & \\
 & & & 1 & & & & \\
 & & & & 1 & & & 1 \\
 & & & & & 1 & 1 & \\
 & & & & & 1 & - 1 & \\
 & & & & 1 & & & - 1
\end{bmatrix}\mathbf{,\ A}_{4} = \begin{bmatrix}
1 & & & & & & & \\
 & 1 & & & & & & \\
 & & 1 & - 1 & & & & \\
 & & 1 & 1 & & & & \\
 & & & & 1 & - 1 & & \\
 & & & & 1 & 1 & & \\
 & & & & & & - 1 & 1 \\
 & & & & & & 1 & 1
\end{bmatrix}
```

可以看到在该方案中，分解后的矩阵元素均为整数，从而降低了每个乘法器的复杂度；另外$`\mathbf{A}_{1}`$~$`\mathbf{A}_{4}`$的稀疏特性可以减少乘法运算数量。可以看出，这其实是一种精度与硬件复杂度的折中方案，即损失了一定的计算精度，但是大幅降低了硬件复杂度。在对输出信噪比要求不高的情况下可以优先考虑此类方案。

## 二、建模描述

本题在不同约束条件下，研究DFT的低复杂度计算方案，目的是对目前芯片中利用FFT计算DFT的方法进行替代，以降低硬件复杂度。给定已知的*N*维DFT矩阵$`\mathbf{F}_{N}`$，设计*K*个矩阵$`\mathcal{A} = \{\mathbf{A}_{1}\mathbf{,}\mathbf{A}_{2}\mathbf{,\ldots,}\mathbf{A}_{K}\mathbf{\}}`$，使得矩阵$`\beta\mathbf{F}_{N}和\mathbf{A}_{1}\mathbf{A}_{2}\mathbf{\cdots}\mathbf{A}_{K}`$在Frobenius范数意义下尽可能接近，即：

``` math
\begin{array}{r}
\min_{\mathcal{A},\beta}{RMSE\left( \mathcal{A},\beta \right)} = \frac{1}{N}\ \sqrt{{\left\| \beta\mathbf{F}_{N}\mathbf{-}\mathbf{A}_{1}\mathbf{A}_{2}\mathbf{\cdots}\mathbf{A}_{K} \right\|_{F}}^{2}}\#(6)
\end{array}
```

其中$`\beta`$为实值矩阵缩放因子，可根据约束条件不同来设计。

相比于乘法，加法的硬件复杂度小得多，因此本题中只考虑乘法器的硬件复杂度：

``` math
C = q \times L
```

其中，*q*指示分解后的矩阵$`\mathbf{A}_{k}`$中元素的取值范围。在以下的问题2~5中，我们限制$`\mathbf{A}_{k}`$中元素实部和虚部的取值范围为$`\mathcal{P =}\left\{ 0, \pm 1, \pm 2,\ldots, \pm 2^{q - 1} \right\}`$。以$`\mathcal{P =}\left\{ 0, \pm 1, \pm 2, \pm 4 \right\}`$为例，此时$`q = 3`$。*L*表示复数乘法的次数，其中与0、$`\pm 1`$、$`\pm j`$或$`( \pm 1 \pm j)`$相乘时不计入复数乘法次数。例如：若$`\mathcal{P =}\left\{ 0, \pm 1, \pm 2, \pm 4 \right\}`$，则下列矩阵乘法的硬件复杂度$`C = 6`$（$`q = 3`$，$`L = 2`$）：

``` math
\begin{bmatrix}
1 & 2 + 4j \\
1 + 2j & 0
\end{bmatrix} \times \begin{bmatrix}
0 & 1 \\
2 + 4j & 2 - 4j
\end{bmatrix}
```

考虑以下两种约束条件：

**约束1**：限定$`\mathcal{A}`$中每个矩阵$`\mathbf{A}_{k}`$的每行至多只有2个非零元素。

**约束2**：限定$`\mathcal{A}`$中每个矩阵$`\mathbf{A}_{k}`$满足以下要求：

``` math
\mathbf{A}_{k}\lbrack l,m\rbrack \in \left\{ x + jy \middle| x,y \in \mathcal{P} \right\}\mathcal{,P =}\left\{ 0, \pm 1, \pm 2,\ldots, \pm 2^{q - 1} \right\},k = 1,2,\ldots,K；l,m = 1,2,\ldots,N
```

其中，$`\mathbf{A}_{k}\lbrack l,m\rbrack`$表示矩阵$`\mathbf{A}_{k}`$第$`l`$行第$`m`$列的元素。在问题2,3,4中，固定$`q = 3`$；在问题5中，$`需要寻找合适的q`$以满足精度要求，并且使得硬件复杂度*C*尽量低。

目前使用FFT进行DFT计算的方案硬件复杂度较高，因为我们希望研究一种替代方案来降低DFT计算的硬件复杂度，但同时我们对精度也有一定要求。请针对以下问题分别设计分解方法，既能最小化RMSE，同时又使得乘法器的数量尽量少。

$`\mathcal{A}`$中矩阵的个数*K*的取值并没有限制，也是优化的变量之一。但需要注意，一般情况下，*K*越小，硬件复杂度越低，但是如果增加矩阵的个数可以使得矩阵中包含更多的简单元素（0、$`\pm 1`$、$`\pm j`$或$`( \pm 1 \pm j)`$），硬件复杂度也可能会降低，因此，需要根据硬件复杂度*C*的定义合理的设计*K*。

问题1：首先通过减少乘法器个数来降低硬件复杂度。由于仅在非零元素相乘时需要使用乘法器，若$`\mathbf{A}_{k}`$矩阵中大部分元素均为0，则可减少乘法器的个数，因此希望$`\mathbf{A}_{k}`$为稀疏矩阵。对于$`N = 2^{t},t = 1,2,3,\ldots`$的DFT矩阵$`\mathbf{F}_{N}`$，请在满足**约束1**的条件下，对最优化问题(6)中的变量$`\mathcal{A}`$和$`\beta`$进行优化，并计算最小误差（ 即(6)的目标函数，下同）和方案的硬件复杂度$`C`$（由于本题中没有限定$`\mathbf{A}_{k}`$元素的取值范围，因此在计算硬件复杂度时可默认$`q = 16`$）。

问题2：讨论通过限制$`\mathbf{A}_{k}`$中元素实部和虚部取值范围的方式来减少硬件复杂度的方案。对于$`N = 2^{t},t = 1,2,3,4,5`$的DFT矩阵$`\mathbf{F}_{N}`$，请在满足**约束2**的条件下，对$`\mathcal{A}`$和$`\beta`$进行优化，并计算最小误差和方案的硬件复杂度$`C`$。

问题3：同时限制$`\mathbf{A}_{k}`$的稀疏性和取值范围。对于$`N = 2^{t},t = 1,2,3,4,5`$的DFT矩阵$`\mathbf{F}_{N}`$，请在**同时满足约束1和2**的条件下，对$`\mathcal{A}`$和$`\beta`$进行优化，并计算最小误差和方案的硬件复杂度$`C`$。

问题4：进一步研究对其它矩阵的分解方案。考虑矩阵$`\mathbf{F}_{N}\mathbf{=}\mathbf{F}_{N1} \otimes \mathbf{F}_{N2}`$，其中$`\mathbf{F}_{N1}和\mathbf{F}_{N2}`$分别是$`N_{1}`$和$`N_{2}`$维的DFT矩阵，⊗表示Kronecker积（注意$`\mathbf{F}_{N}`$非DFT矩阵）。当$`N_{1} = 4`$, $`N_{2} = 8`$时，请在**同时满足约束1和2**的条件下，对$`\mathcal{A}`$和$`\beta`$进行优化，并计算最小误差和方案的硬件复杂度$`C`$。

问题5：在问题3的基础上加上精度的限制来研究矩阵分解方案。要求将精度限制在0.1以内，即RMSE≤0.1。对于$`N = 2^{t},t = 1,2,3\ldots`$的DFT矩阵$`\mathbf{F}_{N}`$，请在**同时满足约束1和2**的条件下，对$`\mathcal{A}`$和$`\beta\mathbf{,}\mathcal{P}`$进行优化，并计算方案的硬件复杂度$`C`$。

## 参考文献

1.  <span id="_Ref143019309" class="anchor"></span>James W. Cooley and John W. Tukey, An Algorithm for the Machine Calculation of Complex Fourier Series, Mathematics of Computation, vol. 19, no. 90, pp. 297-301, 1965. DOI:10.2307/2003354.

2.  <span id="_Ref142571015" class="anchor"></span>K. R. Rao, D. N. Kim, and J. J. Hwang, Fast Fourier Transform: Algorithms and Applications, Springer, 2010. （中译本：快速傅里叶变换：算法与应用，万帅，杨付正译，机械工业出版社，2012.）

3.  Viduneth Ariyarathna, Arjuna Madanayake, Xinyao Tang, Diego Coelho, et al, Analog Approximate-FFT 8/16-Beam Algorithms, Architectures and CMOS Circuits for 5G Beamforming MIMO Transceivers, IEEE Journal on Emerging and Selected Topics in Circuits and Systems, vol. 8, no. 3, pp. 466-479, 2018. DOI: 10.1109/JETCAS.2018.2832177.

## 附录一：名词解释

- 复数乘法次数/复乘次数：进行复数乘法的次数，例如($`1 + 2j`$)×($`2 + 2j`$)为一次复乘。

- 硬件复杂度：本题中，仅考虑乘法器带来的硬件复杂度，硬件复杂度仅与乘法器个数和每个乘法器的复杂度相关

- 乘法器个数：本题中，乘法器个数即为复乘次数

- 单个乘法器的复杂度：单个乘法器的复杂度与乘法器的设计方法和输入数据的位宽等因素相关。在本题中，将乘法器的复杂度简化为仅与输入数据的取值范围相关。对于复数g$`\in \left\{ x + jy \middle| x,y \in \mathcal{P} \right\}\mathcal{,P =}\left\{ 0, \pm 1, \pm 2,\ldots, \pm 2^{q - 1} \right\},`$其与任意复数z相乘的复杂度为q。
