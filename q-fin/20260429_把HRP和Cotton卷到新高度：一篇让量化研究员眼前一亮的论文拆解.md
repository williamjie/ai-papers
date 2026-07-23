# 把 HRP 和 Cotton 卷到新高度：一篇让量化研究员眼前一亮的论文拆解

**日期**: 2026-04-29

---

论文 : Beyond De Prado and Cotton: Hierarchical and Iterative Methods for General Mean-Variance Portfolios链接 : https://arxiv.org/abs/2604.23833这篇论文戳中了量化组合构建里一个老痛点：HRP 和 Cotton 方法再流行，也只能做 最小方差（µ=1） ，压根不认你的 α 信号。就像一个只懂风控、不听策略的同事——在需要主动管理的场景下，简直是浪费信息。
作者甩出三个方法： HRP-µ、HRP-Σµ、CRISP 。它们都接收任意信号向量 µ，同时继承 HRP/Cotton 的正则化哲学，复杂度压到 O(N²)。最关键的是—— 在合成蒙特卡洛实验里，CRISP 在每个面板、每个样本量上都碾压所有基准 。
### 问题与动机：为什么我们要“信号敏感”的组合优化？
量化投资的本质是“信号→组合”。但现实是：
- HRP（López de Prado, 2016）：只依赖聚类树与逆方差，信号 blind- Cotton（2024）：用 Schur 补把 HRP 连到精确最小方差，但仍是 µ=1 的专属游戏，复杂度 O(N³/6)
- 直接 Markowitz：用样本协方差求逆？低特征值方向噪音被放大， Michaud 的“极端权重”问题免不了实际场景中，µ 可能是股票因子暴露、战术资产观点、Black–Litterman 混合后验，你不可能把它设成 1 然后假装无事发生。而每天滚动优化 N=1e3–1e4 的资产池，O(N³) 直接劝退。
作者的问题很干净： 能否把层次化+收缩的结构扩展到任意 µ，同时保留正则化红利？ 答案是三个方法，都由同一个收缩参数 γ∈[0,1] 控制，γ 越高，跨资产协方差信息越充分。
### 方法拆解：三个方法，一套哲学#### 1. CRISP：迭代 shrinkage 求解器（最强选手）
CRISP 的全称是 Correlation-Regularised Iterative Shrinkage Portfolios 。核心是个简单的 Gauss–Seidel 迭代：
解 Pγ w = µ，其中 Pγ = (1−γ)D + γΣ- D = diag(Σ)，只保留个体方差- Σ 是完整协方差- γ 在 [0,1] 连续插值：γ=0 时就是对角解（基于方差的符号加权），γ=1 时退化为精确 Markowitz收敛性保证 （Theorem 5.2）：对任意对称正定 Σ 和任意 γ∈[0,1]，Gauss–Seidel 无条件收敛。 不需要精细调参 。
收敛速度 （Theorem 5.3）是关键创新：迭代次数满足p = O( κ(D⁻¹Pγ) · log(1/ε) )
而κ(D⁻¹Pγ) = [(1−γ)+γλ₁(C)] / [(1−γ)+γλₙ(C)]注意到这里只有 相关系数矩阵 C 的条件数 κ(C) ，与 Σ 的波动率离散度完全无关。这是大杀器：
- 个股波动率差异再大，只要相关性结构良好，CRISP 一样快- κ(C) 在 equities 中通常远小于 κ(Σ)，所以收敛极快收敛后，CRISP 等价于对 shrunk covariance Pγ 做 Markowitz 。这意味着：
- 方差完全保留（D 不变）
- 只有相关性被收缩- γ 的目的是最大化样本外 Sharpe，而不是最小化协方差估计误差（Ledoit–Wolf 的典型目标）
#### 2. HRP-µ：透明、可审计的信号感知 HRPHRP-µ 走同一棵树，但在每个内部节点用 带符号的逆方差组合 作为簇代表：
ŵ_L,i ∝ sign(µ_i) / σ_ii²然后，子簇之间的预算分配仍然使用 Cotton 的 2×2 均值-方差系统。优点是：
- 保持 HRP 的树状可解释性：每片叶子权重 = 符号 × 根到叶路径上预算乘积- 复杂度 O(N²)，比 Cotton 的 O(N³) 低一个数量级- µ=1、γ=0 时精确还原经典 HRP#### 3. HRP-Σµ：在树上做递归 MVO（HRP-µ 的强化版）
HRP-Σµ 把簇代表升级为 在子树上递归计算的局部均值-方差最优解 ，用完整簇内协方差 Σ_LL。
技术细节是 归一化方式 ：简单 sum-to-one 会引发符号翻转病态（Appendix C 详细分析），而 L1 归一化α_k ← α_k^raw / (|α_L| + |α_R|)
是射线不变且保号的（Lemmas 4.5 & 4.6）。结果：
- 捕捉簇内对冲，比 HRP-µ 的逆方差代表信息更丰富- 复杂度仍是 O(N²)
- µ=1、γ=0 时与 HRP 余弦相似度达 0.992，树深度≤2 时精确一致（Proposition 4.8）
### 关键结果：表格与数字说话论文的 Table 2 展示了四种协方差结构（因子、块、尖峰、等相关）下，不同 T/N 比例（0.6–5）的样本外 Sharpe。
CRISP 表现 （Section 10.3）：
- γ ∈ [0.3, 0.7]，100 次迭代- 达到 oracle Sharpe 的 80–94%，在所有面板上一致压倒所有基准- 包括 1/N、HRP、Cotton（多 γ）、直接 Markowitz、线性/非线性 Ledoit–Wolf、HRP-µ、HRP-ΣµHRP-Σµ vs HRP-µ ：
- 随机信号：Sharpe 高 20–35%- 结构性-sector tilt 信号：最高高 180%- 整体可达 CRISP 的约 90%，但仍明显落后Cotton 的脆弱性 （Proposition 3.2）：在小样本 T 下，Cotton 的 γ 连续体表现出 Schur 补不稳定性，即使用真实协方差也一样。HRP-µ 在相同 γ 下更稳定。
速度 Reality Check （Remark 5.7）：
- 在 Apple M4 + Accelerate + Numba-JIT 环境下- N=500 时，直接 Cholesky 比 CRISP 快 48 倍- N∈[500,5000] 区间，Cholesky 仍快 9–48 倍- 按趋势外推， wall-clock 交叉点在 N≈45,000，远超现实组合规模CRISP 的真实卖点不是速度，是内存 ：因子流实现（Algorithm 3）让 Σ 永不实体化，内存从 O(N²) 降到 O(NK)。N=30,000、K=20 时：
- 稠密 Σ：7.2 GB- 因子流：4.8 MBCholesky 需要随机访问完整矩阵，无法利用这种压缩。
### 工程启示：这对实际系统意味着什么？
-主动管理场景的首选迭代器：如果你的策略需要把 α 信号（因子打分、观点向量）融入组合优化，CRISP 是目前唯一在实验中全面压倒 Markowitz 本身的方法。γ=0.5 默认值在 0.3–0.7 的平坦高原上很稳。
-记忆优于算力：对于 N>10,000 的资产池（如股票多因子、加密货币指数），CRISP 的因子流变体能在有限内存里跑完，而 Cholesky 的稠密分解直接内存爆炸。这在边缘设备或内存受限的回测环境里是决定性优势。
-可解释性的权衡：HRP-µ 保留了“根→叶预算乘积”的审计路径，适合合规或策略归因。HRP-Σµ 提升明显但牺牲可解释性。CRISP 完全黑箱，但在样本外 Sharpe 这个终极指标上最优——对以绩效为导向的量化基金，黑箱可以接受。
-正则化的三重通道（Remark 7.2）：
Channel 1：γ 控制的算子收缩（主力）
- Channel 2：有限迭代 slack（副作用）
- Channel 3：早停导致的谱截断（γ≈1 时有益，类似岭回归）
实践建议： γ≈0.5 + 100 次迭代 ，此时只有 Channel 1 显著作用，不要过早停止。
-诊断工具 dir() 的陷阱：论文提出的方向误差 dir(ŵ,w⋆) 对尺度不变，但对符号也不变（Equation 6）。这意味着如果一个方法稳定地输出反方向组合，dir 依然显示 0。好在 HRP/Cotton/CRISP 的符号由构造固定，但若你自创方法，要当心。
-不要迷信“小特征值放大”直觉：Lemma 2.3 说明：当 µ 是 C 的单特征向量时，所有收缩方法都在同一射线上，γ 变化不改变方向。真正的坏情况必须激发至少两个特征空间。设计 µ 时，要么对齐单因子（所有方法一致），要么故意制造多因子冲突来测试稳健性。
### 局限与开放问题论文自己也承认了几个边界：
- 仅限二次效用：框架是均值-方差，不能直接搬到 CVaR 或衍生品定价里的非二次目标。
- 无交易成本：权重再平衡的换手成本未纳入 Sharpe 计算，高频调仓场景可能需要额外约束。
- 线性约束已处理，非线性难：Section 9 用投影 CRISP 处理_long-only_、 sector cap 等线性约束，但若你的约束是多项式或分段（如期权 Delta 对冲），现有框架不直接支持。
- 依赖协方差平稳性：所有实验基于滚动窗口估计，未考虑协方差结构性断点（危机期相关性飙升），此时 κ(C) 可能骤升，收敛变慢。
- γ 的自适应公式仅供参考（Proposition 7.1）：
γ⋆ ≈ 1 / (1 + c·κ(C)²·N/(T·IC²))
校准显示样本外 Sharpe 曲面在 γ 上相当平坦（中值宽度 0.38），所以固定 γ=0.5 已经很强，公式更多是解释性而非处方性。
### 总结：三句话- CRISP 是当前最稳健的“信号敏感”组合迭代器，O(N²) 复杂度，收敛由 κ(C) 控制，实验全面胜出- HRP-µ/Σµ 是树解释性场景的自然延伸，适合需要归因与审计的主动组合，但 Sharpe 明显低一档- 核心洞察是“方差保留、仅收缩相关”：这让 shrinkage 不干扰单个资产的波动率估计（最可信的部分），只净化不可靠的 cross-asset 信号如果你在做因子投资、战术资产配置、或任何需要把明确的 α 向量转化为权重的场景，这篇 paper 的三个方法值得立刻在你回测框架里跑一遍。代码已开源，质量很高。
← 上一篇（更早） CNCF 项目 AI 使用报告：生产力提升与治理滞后的矛盾 下一篇（更新） → 用物理约束拯救LOB模型: ExsdHawkes的数学革命 ← 返回首页 © 2026 前沿研读 · Frontier Studies. All rights reserved.
📡 RSSfunction d(){const o=document.getElementById("article-toc");if(!o)return;const i=document.querySelectorAll(".prose h2, .prose h3");if(i.length {e.id||(e.id="h-"+c);const n=document.createElement("li");n.className=e.tagName.toLowerCase();const t=document.createElement("a");t.href="#"+e.id,t.textContent=(e.textContent||"").trim(),n.appendChild(t),s.appendChild(n),r.push({a:t,h:e})}),o.appendChild(s);const l=new IntersectionObserver(e=>{e.forEach(c=>{if(!c.isIntersecting)return;const n=r.find(t=>t.h===c.target);n&&(r.forEach(t=>t.a.classList.remove("active")),n.a.classList.add("active"))})},{rootMargin:"-80px 0px -70% 0px"});i.forEach(e=>l.observe(e))}d();
