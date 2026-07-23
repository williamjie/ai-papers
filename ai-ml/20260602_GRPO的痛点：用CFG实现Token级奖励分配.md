# ⭐⭐⭐½ GRPO的痛点：用CFG实现Token级奖励分配

**日期**: 2026-06-02

---

论文 : Guidance Contrastive Token Credit Assignment for Discrete Policy Optimization链接 : https://arxiv.org/abs/2605.29198GRPO 和 DAPO 这类 Group-Relative Policy Optimization 方法最近很火，它们省去了 Value Model，靠组内相对奖励来优化策略。但有个硬伤： 奖励是样本级的（Sample-level），却均匀广播给所有 Token 。
这意味着，在一个数学推理链中，关键的推导步骤和无关的标点符号，拿到的梯度信号是一模一样的。这篇论文提出了 GCPO (Guidance Contrastive Policy Optimization) ，核心思路很巧妙： 借图像生成里的 Classifier-Free Guidance (CFG) 思想，给每个 Token 算出“重要性权重”，实现细粒度的信用分配。
### 为什么需要 Token 级奖励？
直觉上，不是所有 Token 都同等重要。
- 在 CoT 推理中：数学计算步骤是核心，连接词是填充物。
- 在文生图中：描述主体的区域是关键，背景噪音权重应低。
现有的 GRPO 把整个序列的奖励平均分摊给每个 Token，这显然浪费了信息。之前的工作（如 VPPO）尝试过基于视觉依赖或置信度加权，但往往局限于特定领域或需要复杂的启发式规则。GCPO 的核心 Insight 是： 如果一个 Token 在“正向提示”和“负向提示”下的预测分布差异巨大，说明这个 Token 对任务至关重要。
### 方法拆解：CFG 的逆向工程GCPO 并不改变推理过程，它只在训练时做文章。
-对比引导（Contrastive Guidance）：
对于生成的每个 Token yi,ty_{i,t}​，模型分别计算在正向提示 xx 和负向提示 x−x^- 下的概率分布。然后计算两者的 KL 散度 ηi,t=DKL(πθ(y∣x)∣∣πθ(y∣x−))\eta_{i,t} = D_{KL}(\pi_\theta(y|x) || \pi_\theta(y|x^-))​=DKL​(πθ​(y∣x)∣∣πθ​(y∣x−))。
直觉：如果去掉提示或改变提示，模型对某个 Token 的预测变化不大，说明这个 Token 跟任务关系不大（比如背景或废话）；如果变化巨大，说明它是核心内容。
-负向提示的设计（关键 Trick）：
文生图：直接用空字符串作为负向提示，这是 CFG 的标准做法。
- 多模态推理：LLM 不接受空指令。作者发现，直接在原问题后加一句 “please generate a wrong answer” 效果最好。这利用了贝叶斯解释：模型在“生成正确答案”和“故意生成错误答案”之间的分布差异，能精准定位出那些区分对错的关键 Token。
-直方图均衡化归一化：
KL 散度的绝对值范围很大且不稳定，直接用 Softmax 或 Min-Max 会导致权重集中在极少数 Token（通常是第一个 Token）。作者采用 Rank-based Normalization（基于排名的归一化），相当于对每个序列的 KL 分布做直方图均衡化。这确保了无论序列长短或任务类型，权重的分布形态是一致的，训练更稳定。
### 实验结果：全面碾压基线作者在文生图和多模态推理两个领域进行了验证，数据非常扎实。
1. 文生图 (GenEval Benchmark)
基于 Janus-Pro-7B 模型，GCPO 在整体得分上达到了 0.89 ，显著优于 GRPO 的 0.85 。
- Counting（计数）：从 0.56 提升到 0.84 (+28 pts)。
- Color Attribution（颜色属性）：从 0.66 提升到 0.83 (+17 pts)。
这说明 GCPO 让模型更关注提示词中具体的实体和属性，而不是泛泛地生成图像。
2. 多模态推理 (Qwen2.5/3-VL)
在 MathVerse、MM12k 等数据集上，GCPO 基于 DAPO 基线进一步提升：
- MathVerse：从 DAPO 的 68.3 提升到 71.7。
- MM12k：从 DAPO 的 82.1 提升到 83.1。
- LogicVista：从 DAPO 的 46.8 提升到 49.7。
特别值得注意的是，GCPO 在通用视觉推理任务（如 LogicVista）上比专门针对视觉依赖设计的 VPPO 表现更好。这证明： 不仅要看图，逻辑推导步骤的 Token 同样需要高权重。
⚠️ 反直觉发现 ：
即使 LLM 在推理时不使用 CFG，这种“假设性”的对比信号依然能有效指导策略优化。这说明 CFG 的价值不仅在于推理时的采样控制，更在于它揭示了模型内部对条件信息的敏感度分布。
### 工程启示- 无需额外网络：GCPO 不需要训练 Value Model，也不需要复杂的梯度分解，只需要在 RL 步骤中多前向传播一次（带负向提示）。计算开销增加有限，但收益显著。
- 即插即用：可以无缝集成到现有的 GRPO/DAPO 训练流程中。只需修改 Advantage 的计算方式，乘以归一化后的 KL 权重即可。
- 负向提示工程：对于非图像任务，设计好的负向提示是关键。“Generate a wrong answer” 是一个简单但高效的通用负向指令，值得在其他对比学习场景中尝试。
### 局限与展望- 计算成本：虽然省去了 Value Model，但每个 Token 需要两次前向传播（正向+负向），显存占用和训练时间会增加约一倍。
- 归一化敏感性：虽然直方图均衡化解决了分布问题，但在极短序列或极度不平衡的奖励分布下，仍可能需要微调温度系数。
这篇论文提供了一个优雅的视角： 用对比学习解决信用分配问题 。对于正在做 RLHF 或 GRPO 训练的工程师来说，这是一个低成本、高回报的改进方向。
## 📝 AI 点评点评时间：2026-06-02 06:12 ｜ reviewer: DeepSeek V4 Flash核心贡献：
针对GRPO/DAPO将样本级奖励均匀广播给所有token而忽略token级贡献差异的问题，提出GCPO（Guidance Contrastive Policy Optimization），利用Classifier-Free Guidance思想，通过对比正负提示下每个token预测分布的KL散度得到重要性权重，经直方图均衡化归一化后乘以样本级优势，实现token级信用分配。
亮点：
- 博文精准抓住了GCPO的核心洞察——CFG差异反映token重要性，并用“逆向工程”的比喻清晰解释了对比引导机制。
- 对负向提示的设计（“generate a wrong answer”）及其贝叶斯解释提炼到位，点出了这一关键trick的工程价值。
- 直方图均衡化归一化的必要性被正确强调，并指出其避免了softmax/min-max的分布集中问题，体现了方法新意。
- 博文还总结了“即插即用”“无需额外网络”等工程启示，方便读者快速评估落地成本。
挑刺：
- 计数指标数值错误：博文称“Counting（计数）：从0.56提升到0.84”，但原文Table 1中Janus-Pro-7B base的Counting为0.59，GRPO为0.81，GCPO为0.84，0.56无出处，属于引用偏差。
- 归一化敏感性表述与原文矛盾：博文在“局限与展望”中写道“在极短序列或极度不平衡的奖励分布下，仍可能需要微调温度系数”，而原文第3.2节明确指出直方图均衡化“removes the need of task-specific hyperparameter tuning”，博文说法与原文意图不符，构成过度解读。
- 遗漏关键实验结果：博文在多模态推理部分仅列出Qwen2.5-VL的结果，而原文Table 2同时包含Qwen3-VL-Instruct的完整结果（如MathVerse: GCPO 84.1 vs DAPO 76.5），这一遗漏使读者无法全面评估GCPO在不同规模模型上的泛化能力。
总评：⭐⭐⭐½ 博文准确传达了GCPO的核心思路和主要结论，但在数字引用和细节表述上存在两处明显偏差，整体仍是一篇有价值的解读。
