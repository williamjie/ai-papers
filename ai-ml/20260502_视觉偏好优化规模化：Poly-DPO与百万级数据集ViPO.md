# 视觉偏好优化规模化：Poly-DPO与百万级数据集ViPO

**日期**: 2026-05-02

---

论文 : ViPO: Visual Preference Optimization at Scale链接 : https://arxiv.org/abs/2604.24953这篇论文干了两件大事：一是发现现有视觉偏好数据集全是”坑”，二是给出了真正的解决方案。
## 问题出在哪？
视觉生成模型的偏好优化（类似RLHF）在LLM上玩得转，但在图像/视频生成上一直Scale不动。原因很现实—— 数据质量太差 。
看Table 1的对比就知道差距：
数据集 图像对数量 分辨率 构建方式 生成模型 Pick-a-pic v2 58,960 512-768px 随机收集 SD2.1, SDXL HPD v3 202,274 256-1024px 随机收集 多模型混杂 ViPO ( ours ) 1,000,000 1024px统一 分类构建 FLUX, Qwen-Image等SOTA **问题有三个层面：
第一，冲突偏好（conflicting patterns） 。论文里测试了Pick-a-Pic V2，用5个不同的奖励模型（PickScore、ImageReward、HPSv2、Aesthetic、CLIP）同时打分，结果只有**20.79%**的图像对能在所有维度上保持一致的胜负关系。这意味着模型学到的是互相矛盾的信号——某个图像在美学上赢，但在文本对齐上输。这种数据喂出来的模型，根本不知道该学什么。
第二，数据质量低下 。现有数据集分辨率普遍512-768px，而ViPO统一1024px。更重要的是，它们用着过时的生成模型（SD1.4/SD2.x），这些模型本身就有缺陷，产生的”偏好”本身就不靠谱。
第三，分布严重失衡 。随机收集导致某些简单模式（比如清晰度） dominates，而关键的构图、文本渲染等维度样本不足。
## Poly-DPO：一行代码的自信调节核心发现是： 现有Diffusion-DPO把冲突数据当二分类问题硬学，梯度更新不加区分，结果被噪声带偏 。
Poly-DPO的改进在Equation (9)：
LPoly-DPO=−log⁡pw>l+α⋅(1−pw>l)L_{\text{Poly-DPO}} = -\log p_{w>l} + \alpha \cdot (1 - p_{w>l}) ​ = − lo g p w > l ​ + α ⋅ ( 1 − p w > l ​ )
就是给标准DPO Loss加了一项 α⋅(1−pw>l)\alpha \cdot (1 - p_{w>l}) ( 1 − p w > l ​ ) 。看起来简单，但** α\alpha 的符号决定了整个学习 dynamics**：
- α>0\alpha > 00（论文用 α=8\alpha=88）：给低置信度样本（p≈0.5p \approx 0.50.5）上权重，高置信度样本（p≈0p \approx 00 或 11）下权重。这适合冲突数据——模型在模糊样本上反而能学到有用的区分信号。
- α<0\alpha < 00：反过来，压制高置信度样本的梯度。这是防止模型在”过于简单”的数据上过拟合（比如随机打乱loser的合成数据）。
- α≈0\alpha \approx 00：退化成标准DPO。这说明数据够干净时，复杂算法反而是累赘。
关键insight ：算法复杂度应该与数据质量成反比。垃圾数据需要鲁棒算法来”洗干净”，干净数据只需要最朴素的优化。
## ViPO：花了心思的数据工程ViPO不是简单堆量，而是 用SOTA模型生成 + 多维分类 + VLM过滤 的三重保障。
图像部分（1M对，1024px）分成5个维度，每个20万对：
- Aesthetics（美学）
- Text-Image Alignment（文本对齐）
- Text Rendering（文字渲染）
- Portrait Quality（人脸质量）
- Composition（构图）
视频部分（300K对，720p+）3个维度：
- Motion Quality（动态质量）
- Video-Text Alignment（视频文本对齐）
- Visual Quality（视觉质量）
用FLUX、Qwen-Image、WanVideo等最新生成器，确保偏好信号本身是高质量的。论文还特意说明：因为商业模型许可限制，开源版本用FLUX.2-dev和Wan2.2替换了 proprietary 模型，但效果验证过基本持平。
## 关键结果：数字不说谎Table 2：Pick-a-Pic V2训练，SD1.5测试方法 范式 PickScore ↑ HPSv2.1 ↑ ImageReward ↑ SD1.5 baseline - 20.57 25.02 0.085 Diffusion-DPO Off 20.95 (+1.8%) 26.12 (+4.4%) 0.297 (+0.212) Poly-DPO Off 21.48 (+4.4%) 28.30 (+13.1%) 0.679 (+0.594)
注意ImageReward的差距：Poly-DPO比Diffusion-DPO多出 +0.382 的绝对提升。这个指标对文本-图像对齐敏感，说明Poly-DPO真的学会了处理冲突信号。
Table 3：GenEval compositional benchmarksSD1.5在 Attribute Binding （属性绑定）这项难任务上：
- Diffusion-DPO: 3.75- Poly-DPO: 14.00（+273%）
SDXL同样任务：
- Diffusion-DPO: 18.50- Poly-DPO: 31.00（+67.6%）
这说明Poly-DPO学到的不只是表面的美学偏好，而是真正理解多实体、多属性的复杂关系。
Table 4：ViPO数据集上的跨模型提升SD3.5-Medium在GenEval整体分数：
- +SFT: 0.80- +SFT & Poly-DPO: 0.83FLUX.1-dev:
- +SFT: 0.75- +SFT & Poly-DPO: 0.79Table 5：文本对齐（DPG-Bench）
SD3.5-Medium在 Relation （关系理解）维度：
- baseline: 92.21- +SFT & Poly-DPO: 94.81FLUX.1-dev整体分数从83.84 → 87.31 ，超过GPT-Image 1的85.15。
Table 7：视频生成（VBench-2.0）
Wan2.1在 Dynamic Spatial Relationship （动态空间关系）：
- baseline: 24.64- +Poly-DPO: 33.82（+37.4%）
这些数字说明： ViPO的数据质量真的高，Poly-DPO在冲突数据上的优势也真的明显 。
## 最妙的发现：算法自动简化论文Figure 4(c)显示，在ViPO全量数据上，最优的 α\alpha 收敛到0 。这意味着：
- 数据质量 > 算法调参。当偏好信号干净、平衡、无冲突时，标准DPO就是最优解。
- Poly-DPO的adaptive nature。它可以自动”降级”成标准DPO，说明设计是合理的——复杂机制只在需要时才启用。
- 互为验证。ViPO数据集的质量让算法选择变简单，而Poly-DPO的收敛反过来证明数据确实没噪声。
这个发现直接回答了标题的”at scale”： 规模化不是无脑堆数据，而是数据质量达到阈值后，算法可以回归朴素 。
## 工程启示第一，数据质量永远是第一位 。与其折腾复杂的loss函数，不如先确保：
- 分辨率统一（ViPO强制1024px）
- 多维度平衡（5个类别各20万）
- 模型SOTA（用FLUX/Qwen-Image/WanVideo）
第二，算法要有”自适应”能力 。Poly-DPO就一个超参 α\alpha ，但能自动适应三种数据分布（冲突/过简/干净）。工程上，这意味着 同一个代码库可以通吃不同质量的数据集 ，不用为每个场景重写训练逻辑。
第三，冲突数据不是废数据，而是需要特殊处理 。Pick-a-Pic V2这种”脏数据”其实代表了真实用户反馈的常态——用户就是会在美学和文本对齐上有矛盾。Poly-DPO的 α>0\alpha>0 0 配置（论文用8）就是专门對付这种场景的”解毒剂”。
第四，规模化要走”质量优先”路线 。ViPO用1M数据把SD3.5-Medium的GenEval从0.69提到0.83，接近HiDream-I1-Full（0.83）——后者是专门为compositional generation设计的模型。这说明 高质量的偏好数据能让通用模型逼近专用模型性能 。
## 局限与边界论文没明说但值得注意的几点：
- ViPO的构建成本高。用FLUX、Qwen-Image、WanVideo这些SOTA模型生成，算力开销巨大。开源版本用替代模型，质量”可比”但没给具体数字对比。
- Poly-DPO的α\alpha 仍需调参。虽然能自适应，但α=8\alpha=88这个值是在Pick-a-Pic V2上调出来的，换个冲突数据集可能要重调。
- 评估依赖自动指标。GenEval、DPG-Bench、VBench都是proxy metrics，真正的用户偏好可能需要更长期的A/B测试。
后续方向 很明确：继续堆更高质量的时序偏好数据（视频方向），以及把Poly-DPO的思路扩展到其他off-policy算法（如KTO）。
## 一句话总结视觉偏好优化的规模化瓶颈不在算法复杂度的堆砌，而在数据的干净程度；当你用1M高质量偏好对把SD3.5-Medium的GenEval从0.69推到0.83时，算法本身 simplifies 到标准DPO——这才是”规模”的真正含义：数据质量达标后，最朴素的优化就是最优的。
