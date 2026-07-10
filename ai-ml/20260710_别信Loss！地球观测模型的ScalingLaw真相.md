# ⭐⭐⭐⭐ 别信 Loss！地球观测模型的Scaling Law真相

**日期**: 2026-07-10

---

论文 : TESSERA v2: Scaling Pixel-wise Earth Foundation Models链接 : https://arxiv.org/abs/2607.03949在 NLP 和 CV 领域，我们习惯了盯着预训练 Loss 看，以为它越低模型越好。但在地球观测（Earth Observation, EO）领域，这个直觉彻底失效了。这篇论文通过 395 次大规模实验，揭示了 EO 基础模型的 Scaling Law 真相： Loss 与下游性能几乎无关 。
对于工程师来说，这意味着如果你还在用 Loss 来挑选 EO 模型，你可能白白浪费了 254% 的计算资源。
### 痛点：为什么 EO 模型这么难搞？
现有的遥感基础模型（如 SatMAE, SkySense）大多沿用自然图像的 Scaling Law，即“Loss 下降 = 性能提升”。但 EO 数据有其特殊性：
- 数据极度不规则：Sentinel-2 经常有云遮挡，Sentinel-1 和 Sentinel-2 的重访周期不同步。
- 标签稀缺且地域性强：很难像 ImageNet 那样有统一、高质量的标注。
- 部署成本高：用户需要处理原始影像、校准辐射、去云，计算负担极重。
目前的方案要么只发布模型权重（让用户自己跑推理），要么发布固定维度的 Embedding（无法灵活调整存储和精度）。TESSERA v2 的目标是提供一个**“Embeddings-as-Data”**的产品化方案：预计算好的全球像素级特征，开箱即用。
### 核心 Insight：Scaling Law 的颠覆性发现作者团队在 1,024 张 GH200 GPU 上进行了受控实验，固定架构（Barlow Twins），扫描 Encoder 大小、Projector 大小和数据量。结果有两个反直觉的发现：
⚠️ 发现 1：预训练 Loss 是下游性能的糟糕预测器Pearson 相关系数仅为 -0.18。这是因为云和轨道采样主导了输入方差，而冗余减少目标（Redundancy Reduction）可以通过对下游任务无用的不变性来最小化 Loss。 用 Loss 选模型比用下游性能选模型多浪费约 254% 的算力。
⚠️ 发现 2：Projector 不需要 Scaling随着计算预算增加， Encoder 容量和数据量应共同增长 （指数约为 0.36 和 0.63），而 Projector 的大小应保持固定 （指数接近 0）。
这意味着，正确的做法是： 训练一个巨大的 Encoder，搭配适量的数据，但保持 Projector 小而精。 然后通过蒸馏（Distillation）将知识传递给小型学生模型。
### 方法拆解：Matryoshka 蒸馏策略基于上述 Scaling Law，TESSERA v2 设计了“教师-学生”架构：
- 教师模型：1B 参数的双分支 Transformer Encoder，处理 Sentinel-1/2 时间序列。它不直接部署，而是作为“表示分布”的生成器。
- 学生模型家族：通过蒸馏得到 N (1M), S (7M), M (21M), L (44M) 四个尺寸的学生模型。
- Matryoshka Embeddings（套娃嵌入）：这是工程亮点。每个像素生成一个 128 维向量，但前 16、32、64 维分别是独立的低维表示。用户可以根据存储带宽需求，直接截断维度，无需重新训练。
为什么蒸馏能做 Matryoshka，而预训练不行？
自监督学习（如 Barlow Twins）只能确定子空间，无法确定坐标顺序。前缀损失会导致梯度不平衡。而蒸馏针对固定的教师 Embedding 进行监督，强行赋予了维度顺序，使得低维前缀具有实际语义信息。
### 关键结果：小模型吊打大巨头在包含 29 个任务的全套测试中（15 个 AlphaEarth 基准 + 14 个保留集），TESSERA v2 的表现令人印象深刻：
模型 参数量 复合得分 (Composite Score) 备注 TESSERA v2-1B-M 21M 0.611 最佳，开源 TESSERA v1 - 0.576 前代版本 AlphaEarth - 0.574 闭源权重，仅开放 Embedding OlmoEarth-L - 0.562 强基线工程效率优势：
- 存储灵活性：16 维前缀保留了 92% 的 128 维性能，但存储空间仅为 1/8。
- 推理成本：学生模型的全局年度推理成本比教师模型低两个数量级（0.04-2 H100-years vs 50 H100-years）。
- 去伪影能力：相比 v1，v2 显著减少了 Sentinel 获取几何导致的条纹伪影，年际稳定性更高。
### 工程启示- 不要迷信 Loss：在 EO、医疗等数据分布复杂、噪声大的领域，预训练 Loss 可能完全失真。必须建立下游任务驱动的评估闭环。
- Embeddings-as-Data 是趋势：对于大多数应用，用户不需要微调 Backbone。提供预计算的、可截断的 Embedding 数据集，能极大降低使用门槛。
- 蒸馏优于直接小模型训练：在资源有限时，先训练大教师模型再蒸馏，比直接训练小模型效果更好，尤其是需要多粒度（Matryoshka）输出时。
### 局限与展望- Scaling Law 的适用范围：目前仅验证于 Sentinel-1/2 像素级编码器，其他传感器或架构需重新验证。
- 计算门槛：训练 1B 教师模型仍需巨大算力（512 GPUs），中小团队难以复现预训练阶段，但可以直接使用蒸馏后的学生模型。
这篇论文不仅提供了一个 SOTA 的 EO 模型，更提供了一套 经过实证检验的 EO 模型研发方法论 。对于从事遥感 AI 的工程团队来说，这是一份值得反复研读的“避坑指南”。
## 📝 AI 点评点评时间：2026-07-10 05:05 ｜ reviewer: DeepSeek V4 Flash核心贡献:
论文通过395次受控实验，在固定BARLOW TWINS架构下系统研究了像素级地球观测基础模型的缩放规律，发现预训练损失与下游性能几乎无关（|Pearson r|<0.2），并给出了计算资源分配规则：编码器容量和训练数据应随预算同步增长，而投影器保持固定。基于此规则训练了1B教师模型，并通过蒸馏得到可部署的学生模型家族，在29任务综合套件上取得领先性能。
亮点:
- 博文准确提炼了最关键的反直觉发现——预训练损失不能预测下游性能，并引用具体相关系数（-0.18）和254%的额外计算代价，抓住了论文的核心工程价值。
- 对Matryoshka嵌入（嵌套前缀）的解释到位，明确指出“蒸馏赋予维度顺序而自监督无法做到”，并给出了16维保留92%性能、存储1/8的具体数字，清晰传达了方法新意。
- 将论文中的“embedding-as-data”理念和产品化思路（学生模型尺寸、存储-精度权衡）用通俗语言呈现，使非遥感读者也能理解部署优势。
挑刺:
-过度推广至医疗领域博文在“工程启示”中写道：“在EO、医疗等数据分布复杂、噪声大的领域，预训练Loss可能完全失真”。原文仅讨论地球观测（EO）数据，并未涉及医疗或其他领域，这一扩展缺乏原文依据，属于不当的跨领域推断。
引用：原文“EO breaks this assumption: selecting models by the loss wastes roughly a factor of three in compute.” 仅针对EO。
-遗漏原文中缩放定律的关键限定条件博文未提及原文明确指出的缩放定律仅适用于“像素级Sentinel-1/2编码器、BARLOW TWINS目标和15任务评估套件”（原文Section 6 Limitations）。这导致读者可能误以为结论可无条件推广到所有EO模型。
引用：原文“First, the scaling laws are empirical and apply only to pixel-wise Sentinel-1/2 encoders, one self-supervised objective, and one 15-task evaluation suite.”
-复合得分未区分任务套件可能引发误解博文表格将TESSERA v2-1B-M的复合得分列为0.611，但未在表内标注这是29-task全套件的得分。原文中该模型在15-task AlphaEarth套件上得分为0.581，两者差异明显。虽然前文已说明“29个任务”，但表格缺乏明确标注，容易让快速浏览的读者误以为0.611是AlphaEarth套件上的结果。
引用：原文“On the full 29-task suite TESSERA v2-1B-M has the best composite score of any system, 0.611” vs “On the 15 AlphaEarth suite tasks alone … M … at 0.581”.
总评: ⭐⭐⭐⭐博文准确传达了论文的核心颠覆性发现和工程创新，关键数字与原文一致，Matryoshka蒸馏机制解释到位。虽有一处过度推广和一处限定条件遗漏，但整体忠实且insight清晰，值得推荐给EO领域工程师阅读。