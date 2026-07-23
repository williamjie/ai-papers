# ⭐⭐⭐ 流式3D重建新范式：HorizonStream长程注意力机制解析

**日期**: 2026-05-27

---

论文 : HorizonStream: Long-Horizon Attention for Streaming 3D Reconstruction链接 : https://arxiv.org/abs/2605.23889做自动驾驶或具身智能的朋友都知道，在线 3D 重建（Online 3D Reconstruction）是个硬骨头。既要满足严格的因果性（Causality），又要受限于内存边界，还得在超长序列里保持位姿不飘、尺度不崩。这篇来自 Horizon Robotics 和 HKUST(GZ) 合作的论文 HorizonStream ，提供了一个非常优雅的解法：它不再盲目堆砌 KV Cache，而是把几何信息的传播形式化为一个“证据影响核”，通过显式的通道级衰减机制，实现了常数内存下的万帧级稳定重建。
### 痛点：为什么现有的流式方法会崩？
目前的流式 3D 重建架构在处理长序列时，往往陷入两种极端：
- 滑动窗口（Sliding Window）：如 Stream3R，强制遗忘旧信息。这导致几何证据被硬性截断，一旦关键特征移出窗口，位姿就会发生跳变或漂移。
- 无门控循环/因果注意力：如 TTT3R 或某些基于 KV Cache 的方法。它们试图保留所有历史信息，结果导致缓存饱和（Cache Saturation）和注意力汇聚（Attention Sinks）。早期的无关 Token 会干扰当前帧的推理，造成严重的几何失真和位姿抖动。
核心矛盾在于： 流式几何证据具有时间异质性（Temporally Heterogeneous） 。局部对应关系是短命的，而全局尺度和场景结构却是持久的。现有架构对所有证据采用统一的传播规则，这显然是不合逻辑的。
### 方法拆解：将“遗忘”变成一种能力HorizonStream 的核心 Insight 是将几何传播分解为空间和时间两个因子： K(t,i)=Kspatial(t,i)⋅Ktime(t,i)K(t, i) = K_{spatial}(t, i) \cdot K_{time}(t, i) K s p a t ia l ​ ( t , i ) ⋅ K t im e ​ ( t , i ) 。
1. 几何线性注意力（Geometric Linear Attention）：解决长程时间因子这是本文最精彩的设计。作者引入了一个有界的 O(1)O(1) 递归几何状态 StS_t ​ ，并设计了 通道级保留率（Channel-wise Retention Rates） γt\gamma^t 。
- 设计直觉：不同的几何特征需要不同的“寿命”。局部对应关系应该快速衰减，而全局结构应长期保留。
- 实现方式：通过学习每个通道的指数衰减率 γ∈(0,1)\gamma \in (0, 1)(0,1)，模型能够自动区分哪些信息是“噪音”（快速遗忘），哪些是“骨架”（长期记忆）。公式 St=diag(γt)St−1+ϕ(kt)vt⊤S_t = \text{diag}(\gamma^t) S_{t-1} + \phi(k_t)v_t^\top​=diag(γt)St−1​+ϕ(kt​)vt⊤​ 确保了状态更新是有界的，避免了传统 RNN 或 Transformer 中的误差无限累积。
2. 几何局部注意力（Geometric Local Attention）：解决短程空间因子在窗口内，模型使用带有**时空旋转位置编码（Spatiotemporal RoPE）**的局部注意力进行精细匹配。
- 防抖动设计：引入了 Head-wise 可靠性门控（Reliability Gating），过滤掉不可靠的注意力头，有效抑制了注意力汇聚现象。
3. 度量读出 Token（Metric Readout Tokens, MRT）
为了解决尺度漂移问题，MRT 直接从高保留率的递归状态中读取全局尺度信息，而不是依赖局部上下文的累积误差。这使得模型能在长序列中保持稳定的米制尺度和刚性位姿。
### 关键结果：短训练，长推理HorizonStream 的训练数据仅包含 48 帧 的片段，但它在测试时展现出了惊人的泛化能力，稳定支持超过 10,000 帧 的序列，且内存占用恒定，时间复杂度线性增长。
以下是 KITTI 数据集上的平均绝对轨迹误差（ATE）对比（单位：米，越低越好）：
方法 KITTI Avg. ATE 备注 HorizonStream (Ours) 19.75 本文方法 HorizonStream w/ LC 16.44 加入回环检测后更优 Lingbot-map 25.29 基线最强对手，但长序列抖动严重 LongStream 51.90 周期性刷新导致上下文丢失 TTT3R w/ refresh 72.86 刷新机制引入不连续性 STream3R 227.77 滑动窗口导致严重漂移在 VBR 数据集的超长序列测试中（最长超过 18,000 帧），HorizonStream 的平均 ATE 为 25.30 ，而基线方法如 CUT3R 和 TTT3R 均超过 60，部分方法甚至直接崩溃（OOM 或跟踪失败）。
### 工程启示与局限对工程师的价值：
- 内存可控：对于端侧部署（如机器人、车载芯片），O(1)O(1) 的递归状态意味着你不需要随着视频时长无限增加显存。
- 无需周期性刷新：现有的流式方法常通过定期重置状态来防止崩溃，但这会丢失长程上下文。HorizonStream 证明了通过“有界衰减”可以兼顾长期记忆和稳定性，简化了工程逻辑。
局限与展望：
论文也坦诚指出，固定大小的递归状态在极端长序列的重访场景中，可能会丢失细粒度的几何细节。此外，动态前景物体仍可能污染局部几何证据。目前的回环检测模块是独立参数化的，未来若能将其端到端集成，将进一步降低延迟并提升全局一致性。
总的来说，HorizonStream 通过重新思考“如何遗忘”，解决了流式 3D 重建中的长期依赖难题，是目前该领域最具工程落地潜力的方案之一。
## 📝 AI 点评点评时间：2026-05-27 01:19 ｜ reviewer: DeepSeek V4 Flash我们被要求根据原始论文和博文进行点评。原始论文是arXiv 2605.23889，关于HorizonStream: Long-Horizon Attention for Streaming 3D Reconstruction。博文是由Qwen3.6-27B根据它自动生成的中文技术博客。我们需要产出点评，包括核心贡献、亮点、挑刺、总评。
首先，理解原始论文的核心贡献。论文提出了一种新的流式3D重建方法HorizonStream，核心是形式化几何传播为证据影响核（evidence influence kernel），并分解为时空因子。对于长程时间因子，使用Geometric Linear Attention学习通道级衰减率，实现有界多时间尺度传播；对于短程空间因子，使用Geometric Local Attention with Spatiotemporal RoPE进行可靠3D匹配并抑制注意力汇聚；Metric Readout Tokens恢复稳定尺度和刚性位姿。关键贡献：训练仅48帧，泛化到超过10000帧，常数内存和线性时间，达到SOTA。
博文内容：标题“流式3D重建新范式：HorizonStream长程注意力机制解析”。内容大致介绍了痛点、方法拆解、关键结果、工程启示与局限。博文整体忠实于原文，但可能存在一些简化、遗漏或表述偏差。
现在按要求写点评。
核心贡献：提炼原文要解决什么，用了什么核心方法。以原始材料为准。原文解决在线流式3D重建中长序列的漂移、抖动、崩溃问题，归因于几何证据的时间异质性与现有架构统一传播规则之间的不匹配。核心方法是提出了证据影响核的形式化，并分解为时空因子：Geometric Linear Attention（通道级衰减率，有界递归状态）、Geometric Local Attention with Spatiotemporal RoPE（头级门控和时空位置编码）、Metric Readout Tokens（从高保持通道恢复尺度和位姿）。所以核心贡献可以概括为：形式化几何证据影响核，并提出HorizonStream，通过通道级衰减和局部注意力分解实现有界多时间尺度传播，仅训练48帧即可推广到万帧序列。
亮点：博文相对原文的提炼/取舍是否到位？原文里真正有工程价值或方法新意的点。博文准确抓住了核心洞察：流式几何证据的时间异质性，以及“将遗忘变成一种能力”。它提到了通道级保留率、Spationtemporal RoPE、MRT等关键设计。工程价值点：O(1)递归状态，无需周期性刷新，内存可控。博文在这些方面提炼到位。
挑刺：需要具体指出博文遗漏的关键约束/数字/条件、过度解读、术语错位、引用偏差等。每条必须引用原文或博文的具体片段或数据做依据。
仔细对比：
-博文说“现有的流式方法会崩？……滑动窗口（Sliding Window）：如Stream3R，强制遗忘旧信息。”原文中Stream3R确实使用滑动窗口，但博文可能过于简化。不过这不算是严重错误。
-博文在方法拆解中写道“几何线性注意力……这是本文最精彩的设计。作者引入了一个有界的O(1)递归几何状态S_t，并设计了通道级保留率（Channel-wise Retention Rates）γ^t。” 博文正确。
-博文在关键结果表格中给出了KITTI Avg. ATE，原文表1中HorizonStream平均ATE是19.75，博文正确。但博文表格中还有“HorizonStream w/ LC” 16.44，原文也是。但是博文遗漏了原文中更详细的对比：比如不同序列的ATE，以及VBR等数据集的结果。不过博文作为概要，可以理解。
-博文说“HorizonStream的训练数据仅包含48帧的片段”，原文说“trained on only 48-frame clips”，正确。
-博文在“工程启示与局限”中说“无需周期性刷新”，原文确实不需要周期性刷新，因为几何线性注意力有界。但原文中CUT3R、TTT3R等有refresh变体，博文提及了。但博文说“现有的流式方法常通过定期重置状态来防止崩溃，但这会丢失长程上下文。HorizonStream证明了通过“有界衰减”可以兼顾长期记忆和稳定性”，这基本正确。
需要找出具体的遗漏或错误。
可能的遗漏：
-原文中非常重要的理论分析：附录A和B详细证明了因果softmax注意力的稀释问题（Proposition 1）和零遗忘污染（Proposition 2）。博文完全没有提到这些理论证明，但这是论文的重要贡献之一，形式化了问题。不过博文作为技术博客，不要求涵盖所有理论细节，但亮点中提到了“形式化为一个‘证据影响核’”，博文确实提到了这个核，但没有深入证明。这不算严重遗漏。
-原文中有一个重要细节：Geometric Linear Attention的状态更新公式中，使用了ϕ(k_t)映射和ṽ_t，博文简化成了ϕ(k_t)v_t^T。原文公式(5)是S_t = γ_t S_{t-1} + ϕ(k_t)ṽ_t^⊤，博文写成了S_t = diag(γ^t) S_{t-1} + ϕ(k_t)v_t^⊤。这里ṽ_t与v_t可能不同？原文中ṽ_t是value update written into the state，但博文没有区分。不过这不是大问题。
-博文说“在KITTI数据集上的平均绝对轨迹误差（ATE）对比（单位：米，越低越好）”，然后给出了一个表格。但是原文中表1的ATE是“mean ATE”，但表1的数值是19.75，博文正确。但是博文表格中“Lingbot-map”是25.29，原文表1中Lingbot-map平均ATE是25.29，正确。“LongStream”是51.90，原文也是。但是博文表格中“TTT3R w/ refresh”是72.86，原文表1中TTT3R w/ refresh平均ATE是72.86？原文表1中TTT3R w/ refresh平均是72.86吗？原文表1最后一行是“Ours w/ LC 16.44”，上面一行是“Ours 19.75”。再上面有“Lingbot-map 25.29”，“LongStream 51.90”，“TTT3R w/ refresh”在表1中：TTT3R w/ refresh的均值是72.86吗？表1中TTT3R w/ refresh那一行：119.94, 99.59, 238.07, 16.83, 3.98, 36.38, 47.20, 11.62, 107.33, 86.96, 33.58, 平均？原文没有直接给出平均列，但表1最后一列是“Avg.”，对于TTT3R w/ refresh是72.86，正确。所以博文表格准确。
-博文说“在VBR数据集的超长序列测试中（最长超过18,000帧），HorizonStream的平均ATE为25.30，而基线方法如CUT3R和TTT3R均超过60”。原文表3中Ours平均ATE是25.30，CUT3R平均66.25，TTT3R平均64.99，正确。但博文说“部分方法甚至直接崩溃（OOM或跟踪失败）”，原文确实有“–”表示OOM或重复跟踪失败，比如InfiniteVGGT在ciampino_1是“–”。博文概括合理。
-博文“工程启示与局限”中提到“固定大小的递归状态在极端长序列的重访场景中，可能会丢失细粒度的几何细节”。原文讨论部分也提到“the fixed-size recurrent state still miss fine-grained details”。所以正确。
-博文“目前的回环检测模块是独立参数化的”，原文说“The optional loop-closure module is currently parameterized separately”，正确。
-博文没有提到“通道级保留率γ_t是通过sigmoid函数从输入特征中学习得到的”，原文公式(6)有σ(W_γ x_t + b_γ)。博文只说了“通过学习每个通道的指数衰减率”，没有具体说如何学习。这不算严重遗漏。
-博文说“Geometric Local Attention……引入了Head-wise可靠性门控”，原文公式(8)有g_h = σ(W_g x̄ + b_g)。博文提到“过滤掉不可靠的注意力头”，正确。
-博文提到“Spatiotemporal RoPE”扩展了三个轴（时间、高度、宽度），原文也是。
-博文说“MRT直接从高保留率的递归状态中读取全局尺度信息”，原文说“MRT participates in Geometric Linear Attention and reads metric scale from high-retention channels”。正确。
-博文“无需周期性刷新”是亮点，但原文中CUT3R、TTT3R、LoGeR都有refresh变体，博文提到“现有的流式方法常通过定期重置状态来防止崩溃”，正确。
现在找挑刺。可能需要更仔细地看博文是否有过度解读或术语错位。
博文开头：“它不再盲目堆砌 KV Cache，而是把几何信息的传播形式化为一个‘证据影响核’，通过显式的通道级衰减机制，实现了常数内存下的万帧级稳定重建。” 原文确实提出了证据影响核，但“不再盲目堆砌 KV Cache”是一种通俗说法，没有错误。
博文在“方法拆解”中写道：“设计直觉：不同的几何特征需要不同的‘寿命’。局部对应关系应该快速衰减，而全局结构应长期保留。” 这与原文一致。
博文公式写为“S_t = \text{diag}(\gamma^t) S_{t-1} + \phi(k_t)v_t^\top”，原文公式(6)是S_t = diag(γ_t) S_{t-1} + ϕ(k_t) ṽ_t^⊤。博文将γ_t写为γ^t，但原文γ_t是向量，上标t表示时间步，下标t表示时间。博文可能省略了下标，但意思正确。另外博文使用v_t而不是ṽ_t，这可能是一个小的不准确，因为原文中ṽ_t是value update，可能与v_t不同（可能经过投影）。但原文没有明确说ṽ_t = v_t，可能ṽ_t是经过处理的。不过这个细节不影响主要理解。
博文“关键结果”表格中，在“方法”列写了“HorizonStream (Ours)”和“HorizonStream w/ LC”，但原文表1中“Ours”和“Ours w/ LC”。博文用了“HorizonStream”名称，没问题。
博文“工程启示与局限”中说“对于端侧部署（如机器人、车载芯片），O(1)的递归状态意味着你不需要随着视频时长无限增加显存。” 原文确实提到constant memory。正确。
博文“局限与展望”中说“目前的回环检测模块是独立参数化的，未来若能将其端到端集成，将进一步降低延迟并提升全局一致性。” 原文说“The optional loop-closure module is currently parameterized separately, and its optimization settings could be further refined.” 博文表述合理。
可能存在的挑刺：
-博文没有提到论文中最重要的理论分析：几何注意力稀释（Geometric Attention Dilution）和零遗忘污染（Zero-Forgetting Contamination）的命题。虽然博文是技术博客，但作为“亮点”可能应该提及原文的理论贡献。但这不是“挑刺”必须的，因为博文已经概括了核心思想。
-博文在描述“几何线性注意力”时，说“公式 S_t = \text{diag}(\gamma^t) S_{t-1} + \phi(k_t)v_t^\top 确保了状态更新是有界的，避免了传统 RNN 或 Transformer 中的误差无限累积。” 原文证明了有界性，但博文没有提到原文Proposition 5的详细证明。但这不是错误。
-博文在“关键结果”中说“HorizonStream的训练数据仅包含48帧的片段”，但原文也提到训练分两阶段，Stage 1用48帧，Stage 2用更长片段？原文说“Training clips use temporal strides from 1 to 8”，以及“Stage 2 adds longer clips for long-horizon inference”。所以严格来说，训练数据不全是48帧？原文在贡献中说“trained on only 48-frame clips”，但方法部分说“each sample consists of 48 frames”，训练数据描述中有“Stage 2 adds longer clips”。这里可能有歧义：原文在Abstract和Introduction中明确说“trained on only 48-frame clips”，但在Implementation Details中说“each sample consists of 48 frames, processed sequentially in 21-frame chunks”。所以训练时每个样本是48帧，但Stage 2可能使用更长的序列？原文说“Stage 2 adds longer clips for long-horizon inference”，但没说具体长度。可能Stage 2也是48帧但采样策略不同。但博文说“仅包含48帧的片段”基本正确，因为训练样本是48帧。所以不算错误。
-博文在表格中比较了“Lingbot-map 25.29”和“HorizonStream 19.75”，但原文中表1的Lingbot-map平均ATE是25.29，正确。但博文没有提及Lingbot-map是最近的强基线，而原文在方法对比中提到了。不过这不是问题。
-博文说“HorizonStream证明了通过‘有界衰减’可以兼顾长期记忆和稳定性，简化了工程逻辑。” 原文确实证明了有界性。
-博文可能遗漏了“Geometric Local Attention”中的“Geometric Local Attention with Spatiotemporal RoPE”的具体细节：原文提到“periodically reset the temporal index to avoid unbounded positional growth”，博文没有提及这个重置细节。这是一个工程细节，但可能不是关键。
-博文在“方法拆解”中写道“几何局部注意力（Geometric Local Attention）：解决短程空间因子……引入了Head-wise可靠性门控（Reliability Gating），过滤掉不可靠的注意力头，有效抑制了注意力汇聚现象。” 原文中Head-wise gating确实是为了抑制注意力汇聚和噪声匹配。但博文说“有效抑制了注意力汇聚现象”，而原文提到“suppress attention sinks”，正确。
-博文“关键结果”表格中“方法”列写的是“HorizonStream (Ours)”，但原文表格中“Ours”和“Ours w/ LC”。博文在表格下方写了“本文方法”，没问题。但博文表格中“备注”列写了“本文方法”，可能有点冗余。
-博文“关键结果”中“在VBR数据集的超长序列测试中（最长超过18,000帧），HorizonStream的平均ATE为25.30，而基线方法如CUT3R和TTT3R均超过60，部分方法甚至直接崩溃（OOM或跟踪失败）。” 原文表3中CUT3R平均66.25，TTT3R平均64.99，确实超过60。但“部分方法甚至直接崩溃”可能指InfiniteVGGT在ciampino_1是“–”，博文没说具体哪个，但可以接受。
-博文“局限与展望”中说“目前的回环检测模块是独立参数化的，未来若能将其端到端集成，将进一步降低延迟并提升全局一致性。” 原文说“The optional loop-closure module is currently parameterized separately”，但原文没有说“降低延迟并提升全局一致性”是未来方向，只是说“its optimization settings could be further refined”。博文添加了“端到端集成”的建议，这属于合理推测，不算错误。
-博文没有提到原文中的“通道级保留率γ_t是通过sigmoid函数从窗口特征中学习得到的”，博文只说“通过学习每个通道的指数衰减率”。这不算错误，但可以更准确。
-博文在“痛点”部分说“滑动窗口（Sliding Window）：如Stream3R，强制遗忘旧信息。” 原文中Stream3R确实使用滑动窗口，但博文说“强制遗忘旧信息”可能有点绝对，原文描述为“sliding windows enforce hard cutoffs”。正确。
-博文说“无门控循环/因果注意力：如TTT3R或某些基于KV Cache的方法。” TTT3R是基于Test-Time Training，不是严格的无门控循环。原文中TTT3R使用的是“ungated recurrence”？原文在related work中描述TTT3R为“add persistent recurrent states”，但附录中提到了TTT without reset导致零遗忘污染。所以博文归类为“无门控循环/因果注意力”基本正确。
现在，我考虑是否有明显的术语错位或过度解读。博文整体质量较高，提炼准确。
可能的挑刺：博文在“方法拆解”中写道“公式 S_t = \text{diag}(\gamma^t) S_{t-1} + \phi(k_t)v_t^\top 确保了状态更新是有界的，避免了传统 RNN 或 Transformer 中的误差无限累积。” 原文中Proposition 5证明有界性，但博文没有提及需要γ̄<1的条件。但博文在直觉中说了“γ∈(0,1)”，所以隐含了。没问题。
博文“关键结果”中表格的备注列写了“本文方法”“加入回环检测后更优”等，但原文中“HorizonStream w/ LC”是16.44，博文正确。但博文没有提供原文中更细的ATE breakdown，比如不同序列的ATE。这不算遗漏，因为博文是总结。
博文最后说“是目前该领域最具工程落地潜力的方案之一。” 原文没有直接说“最具工程落地潜力”，但基于性能，可以这么说。
总体来看，博文忠实反映了原文的核心贡献和方法，没有严重错误。但为了挑刺，我可以指出一些细节：
-博文在“痛点”中说“早期的无关 Token 会干扰当前帧的推理，造成严重的几何失真和位姿抖动。” 原文中关于注意力汇聚的讨论更具体：softmax attention导致注意力集中在早期token（sink），而博文说“早期的无关Token”，但原文提到“spike-like attention sinks, which focus on irrelevant early tokens”，所以博文正确。
-博文在“方法拆解”中写“Geometric Linear Attention……公式 S_t = \text{diag}(\gamma^t) S_{t-1} + \phi(k_t)v_t^\top 确保了状态更新是有界的”，原文中状态更新公式是St = diag(γ_t) S_{t-1} + ϕ(k_t) ṽ_t^⊤。博文用v_t代替ṽ_t，可能忽略了ṽ_t是经过处理的（比如可能是v_t的某种变换）。原文没有明确说明ṽ_t和v_t的关系，但公式中写的是ṽ_t。不过博文没有引用原文，所以这个差异可能不算错误，但可以指出作为术语偏差：原文中的value update符号是ṽ_t，博文简化为v_t，可能丢失了细节。但这不是严重错误。
-博文在“关键结果”中给出了“HorizonStream (Ours) 19.75”和“HorizonStream w/ LC 16.44”，但原文表1中还有“Ours w/ LC 16.44”，但原文表1中“Ours”是19.75。博文正确。
-博文说“在VBR数据集的超长序列测试中（最长超过18,000帧），HorizonStream的平均ATE为25.30”，原文表3中“Ours”平均ATE是25.30，正确。但博文没有提到“Ours w/ LC”在VBR上的平均ATE是18.84，这可能是遗漏，但博文主要关注无LC版本。
-博文没有提到“Geometric Local Attention”中的“Geometric Local Attention with Spatiotemporal RoPE”的具体实现：原文说“For a patch at frame t and spatial location (y, x), we set π = (t+1, y+1, x+1), split query and key vectors into three parts, and rotate each part along one axis.” 博文只说了“扩展了三个轴”，没有提及split和rotate细节，但这是合理的简化。
-博文没有提到“Metric Readout Tokens (MRT) and relative pose fusion”中的“relative pose fusion”的具体细节：原文说“A transformer head jointly attends to these tokens and estimates a consensus relative pose for the current frame with respect to the window context.” 博文只说“直接从高保留率的递归状态中读取全局尺度信息”，没有提及pose fusion。但博文在方法拆解中提到了“MRT直接从高保留率的递归状态中读取全局尺度信息”，但未提pose。然而博文在“关键结果”中主要关注ATE，所以可以接受。
-博文“工程启示与局限”中说“无需周期性刷新”，但原文中CUT3R、TTT3R等有refresh变体，博文正确。但原文提到“HorizonStream avoids periodic refresh by discounting stale evidence”，博文说“无需周期性刷新”，正确。
-博文“局限与展望”中说“固定大小的递归状态在极端长序列的重访场景中，可能会丢失细粒度的几何细节。” 原文在Discussion中说“for extremely long sequences with repeated revisits, the fixed-size recurrent state still miss fine-grained details”，博文正确。
现在，我考虑一个可能更严重的遗漏：博文没有提及原文中关于“训练分两阶段”和“训练数据组成”的具体细节。但这不影响主要insight。
另一个可能的挑刺：博文在“关键结果”表格中，将“Lingbot-map”称为“基线最强对手，但长序列抖动严重”。原文中确实提到“Lingbot-map can achieve competitive ATE, but its pose becomes increasingly jittery over longer sequences”。博文正确。
综合来看，博文没有明显的错误，但有一些细节的简化。为了达到挑刺的要求，我可以指出：
-博文在描述“Geometric Linear Attention”时，将状态更新公式写为S_t = diag(γ^t) S_{t-1} + ϕ(k_t)v_t^⊤，而原文中ṽ_t可能不同于v_t（原文中ṽ_t是“value update written into the state”）。虽然不影响理解，但符号不精确。
-博文在“方法拆解”中说“公式 S_t = \text{diag}(\gamma^t) S_{t-1} + \phi(k_t)v_t^\top 确保了状态更新是有界的”，但原文中证明有界性需要γ̄<1，博文没有明确说明这个条件。
-博文没有提及原文中重要的理论结果，如Proposition 1（几何注意力稀释）和Proposition 2（零遗忘污染），这些是论文形式化贡献的一部分。博文虽然提到了“证据影响核”，但未深入其理论推导。不过这不是错误，而是取舍。
-博文在“痛点”中说“无门控循环/因果注意力：如TTT3R或某些基于KV Cache的方法。它们试图保留所有历史信息，结果导致缓存饱和（Cache Saturation）和注意力汇聚（Attention Sinks）。” 原文中TTT3R使用递归状态（不是因果softmax注意力），但原文提到“ungated recurrence [6,43]”导致heavy-tailed kernel，TTT3R正是使用ungated recurrence。所以博文正确。
-博文“关键结果”中“HorizonStream (Ours) 19.75”是KITTI平均ATE，但原文表1中“Ours”平均是19.75，但注意表1中还有“Ours w/ LC”是16.44。博文正确。
-博文没有提及原文中在Oxford Spires、ScanNet++等数据集上的详细结果，但这是合理的总结。
我认为博文整体质量高，没有严重事实错误。但根据评分标准，⭐⭐⭐是默认档（博文准确反映论文，论文是有意义的工作）。但这里博文不仅准确，而且很好地提炼了insight，并且有适当的工程启示。论文本身有显著创新（形式化核分解、通道级衰减、长序列泛化），博文也传达了核心insight。所以可以给⭐⭐⭐⭐？但需要谨慎：博文是否“精准呈现”？博文在方法部分描述清晰，关键结果准确，局限也提到。没有发现重大遗漏或错误。但可能缺少一些理论细节，不过作为技术博客已经足够。考虑到“HF Daily Papers已预筛过质量，blog只要忠实就到这一档”，但这里博文是自动生成的，且忠实度很高。我倾向于给4星，因为论文创新显著，博文准确传达了insight。但按照评分标准，⭐⭐⭐⭐需要“论文有显著创新或工程价值 + 博文准确传达 insight”，满足。所以可以给⭐⭐⭐⭐。
但也可以考虑给⭐⭐⭐½，因为博文在细节上有些简化（如公式符号），但整体准确。不过4星更合适。
现在撰写点评。
核心贡献：1-2句。原文解决流式3D重建在长序列中的漂移和崩溃问题，通过形式化几何证据影响核，并分解为时空因子，提出HorizonStream，包含通道级衰减的几何线性注意力、带时空RoPE的几何局部注意力和度量读出Token，实现仅训练48帧即可推广到万帧序列。
亮点：博文准确捕捉了核心洞察（证据时间异质性、通道级衰减），并强调了工程价值（O(1)内存、无需周期性刷新）。方法拆解清晰。
挑刺：具体指出遗漏或偏差。需要引用原文或博文片段。
可能的挑刺点：
- 博文在描述几何线性注意力状态更新时写“S_t = \text{diag}(\gamma^t) S_{t-1} + \phi(k_t)v_t^\top”，而原文为“S_t = diag(γ_t) S_{t-1} + ϕ(k_t)ṽ_t^⊤”。博文将γ_t写为γ^t（可能表示γ的t次方，但原文γ_t是向量），且ṽ_t简化为v_t。原文中ṽ_t是“value update written into the state”，与v_t可能有区别（例如经过投影）。虽然不影响主要思想，但符号不精确。
- 博文在“关键结果”中只给出了KITTI平均ATE，但未提及原文中更全面的对比，例如VBR、Oxford Spires等。不过作为博客，可以接受。
- 博文在“方法拆解”中未提及原文中关于“几何线性注意力与TTT的联系”（Proposition 6），但这不是必须。
- 博文在“痛点”中说“现有的流式方法会崩？……滑动窗口（Sliding Window）：如Stream3R，强制遗忘旧信息。” 原文中Stream3R是使用causal mask和sliding-window attention，但博文说“强制遗忘旧信息”可能过于简单，因为滑动窗口不是强制遗忘，而是硬截断。但基本正确。
更具体的挑刺：博文在“关键结果”表格中，将“Lingbot-map”的ATE列为25.29，并说“基线最强对手，但长序列抖动严重”。原文中Lingbot-map的ATE在KITTI平均是25.29，确实比LongStream等好。但博
