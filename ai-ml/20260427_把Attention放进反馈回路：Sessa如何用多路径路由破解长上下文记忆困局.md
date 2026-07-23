# 把Attention放进反馈回路：Sessa如何用多路径路由破解长上下文记忆困局

**日期**: 2026-04-27

---

论文 : Sessa: Selective State Space Attention链接 : https://arxiv.org/abs/2604.18580Transformer的self-attention能任意访问历史token，但单次读取时信息容易被分散稀释；Mamba这类SSM通过循环状态累积信息，却又容易指数遗忘。长上下文建模就像走钢丝——两边都危险。
Sessa的解法很暴力： 把Attention塞进反馈回路里 。这不是简单的”Attention+SSM”拼接，而是一次架构视角的重新定义。
## 问题：为什么长上下文这么难？
Attention的稀释问题 ：当attention mass分散在大片上下文上时，单个token的贡献会变成O(1/|𝒲ₜ|)。论文里提到最坏情况能到O(1/T)——100万token的上下文里，某个token的影响几乎被稀释到忽略。
SSM的指数遗忘 ：Mamba用门控机制”冻结时间”，但在failed freeze-time regime下，累积的离散时间步∑Δᵣ有正下界，导致影响按e^(-λ·lag)指数衰减。
这两种衰减模式有个共同点： 都是单一路径的悲剧 。
- Transformer：一条直接边τ→t，权重被摊薄- Mamba：一条链式路径τ→…→t，每步都在衰减Sessa问了个问题： 能不能让一个token通过多条路径影响未来？
## 核心设计：多路径反馈路由Sessa的layer结构不复杂，但思路很清晰：
input → LayerNorm → 拆成gate+activator↓activator → Forward Attention → fₜ (one-hop direct read)
↓+ Feedback Attention → αᶠᵇₜ,ⱼ × γₜ → Bᶠᵇ矩阵↓解方程 (I - Bᶠᵇ)s = f → s (multi-hop solve)
↓s ⊙ gate → output关键区别 ：
- Forward Attention：标准causal attention，走一条直接路径- Feedback Attention：权重αᶠᵇₜ,ⱼ + 标量增益γₜ∈(-1,1)组成严格下三角矩阵Bᶠᵇ- 求解(I - Bᶠᵇ)s = f：这是一个递归替换过程，等价于s = f + Bᶠᵇf + (Bᶠᵇ)²f + …展开看就明白了：
sₜ = fₜ + γₜ·∑ⱼ₌₀ᵗ⁻¹ αᶠᵇₜ,ⱼ sⱼ递归代入后，sₜ变成 所有历史fⱼ的加权和，权重对应从j到t的所有可能路径的乘积 。
比如从τ到t：
- 1-hop：直接边 τ→t（权重αᶠᵇₜ,τ）
- 2-hop：τ→k→t（权重αᶠᵇₖ,τ·αᶠᵇₜ,ᵏ）
- k-hop：τ→…→t（k步路径权重乘积）
而Transformer只有1-hop，Mamba只有 唯一的一条链 （每个中间节点只有一个前驱）。Sessa的Bᶠᵇ是 稠密下三角矩阵 ，意味着 每对历史-未来节点间存在多条不同长度的路径 。
## 理论突破：幂律衰减尾巴论文最硬核的部分是证明了这种多路径结构能产生 幂律衰减（power-law）的长期影响尾巴 ：
定理8 ：在显式假设和匹配条件下，Sessa的记忆尾巴是O(ℓ⁻ᵝ)，其中0<β<1。
这意味着：
- Attention (diffuse regime)：单条边的影响≈O(1/|𝒲ₜ|) ≈ O(1/t)，对应β=1的边界- Mamba (failed freeze-time)：指数衰减，比任何幂律都快- Sessa：可以做到β<1，衰减比1/ℓ还慢举个例子：lag=1000时- Attention：影响≈1/1000 = 0.001- Mamba（假设κ=0.99）：≈0.99¹⁰⁰⁰ ≈ 4e-5- Sessa（β=0.5）：≈1/√1000 ≈ 0.032差了一个数量级以上。
定理12 进一步证明：在匹配regime下，Sessa是 唯一 能实现灵活选择性检索的模型，包括 不随距离衰减的影响档案 （non-decaying profiles）。这意味着理论上可以做到”无论多远，想取就取”。
## 实验数据：长上下文确实强论文做了matched experiments（控制变量对比），结果直接看表格：
基准测试 Context Length Sessa Transformer Mamba PG-19 8K 42.1 41.8 41.5 32K 40.2 41.3 41.0 128K 38.7 40.9 40.5 Proof-Pile 16K 29.4 29.2 29.0 64K 27.8 29.1 28.7（数据来自论文Table 1，PG-19是perplexity越低越好）
关键观察 ：
- 短上下文（8K）：Sessa 42.1 vs Transformer 41.8，基本打平，没有显著退化- 长上下文（32K-128K）：差距拉大，128K时Sessa 38.7比Transformer 40.9领先2.2个perplexity点——这在语言建模里是巨大优势- Mamba基线：在长上下文上同样被Sessa压制，但差距比Transformer小论文还提到在code、math任务上也有类似trend，但具体数字没全放正文。
## 工程启示：这玩意儿能用吗？
优点很明确 ：
- 长上下文优势明显：如果做文档分析、代码仓库理解、长对话，Sessa的理论优势能兑现成实际指标- 架构兼容性好：本质是个mixer模块，可以替换Transformer的self-attention或SSM的transition- 不用额外位置编码：反馈solve本身能产生绝对位置信号（Corollary I.8），这点很巧妙但代价也很实在 ：
- 计算复杂度仍是O(T²)：feedback attention要算所有历史对，全注意力。论文说可以用”windowed”或”sparse”变体，但性能会打折扣- 数值稳定性依赖条件：定理需要sup|γₜ|<1，论文通过tanh门控保证，但实践中会不会有near-1的边缘case存疑- 训练动态未知：多路径路由+递归solve，梯度会不会爆炸/消失？论文没细说训练细节落地场景推荐 ：
- ✅ 长文档理解：合同审阅、论文分析、代码库导航- ✅ Agent历史记忆：让agent真正记住几百轮对话的细节- ⚠️ 实时/流式应用：O(T²)复杂度在超长流上可能成瓶颈- ❌ 极致速度要求：相比linear-scaling的Mamba，Sessa的quadraticcost是硬伤## 局限与展望论文自己也承认几个边界：
- 理论分析假设较多：diffuse regime、smooth-routing bounds这些在真实数据上是否普遍成立？
- 实验规模有限：主要做language modeling，没见vision/speech任务，跨模态通用性未知- 超长上下文实测缺失：128K已经是论文极限，但实际应用动不动要1M+，Sessa的幂律尾巴在 Million-token尺度会不会变平？
开放问题 ：
- 能否设计稀疏Sessa保持幂律尾巴但降到near-linear复杂度？
- Feedback attention加RoPE会怎样？论文特意不加，但加了会不会破坏位置信号？
- 和Hybrid架构（如Transolver+Mamba）比，Sessa的单一模块优势是否还明显？
## 个人判断这是一篇有理论深度的架构创新 。把”多路径路由”这个视角注入序列建模，比单纯堆Attention或SSM更有解释力。 幂律尾巴的证明 是硬核加分项，不是heuristic。
但 工程落地有门槛 。quadratic cost在T>100K时会成为实际部署的障碍。如果要做产品，可能需要：
- 先验证64K-128K场景下的ROI是否足够高- 探索chunked+recurrent的混合方案，在关键层用Sessa- 看看能不能和FlashAttention技术结合，做近似求解推荐阅读人群 ：对long-context架构有研究的工程师、SSM/Transformer交叉领域的研究者。如果只是要个能跑的long-context模型，现在Mamba2或者Transformer with sliding window可能更省心。
一句话总结 ：Sessa证明了”多路径反馈”是比”单链循环”或”单次读取”更强大的长程记忆范式，但算力账单不低。
