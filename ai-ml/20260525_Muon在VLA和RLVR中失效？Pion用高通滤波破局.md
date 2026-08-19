# ⭐⭐⭐½ Muon在VLA和RLVR中失效？Pion用高通滤波破局

**日期**: 2026-05-25

---

论文 : Rethinking Muon Beyond Pretraining: Spectral Failures and High-Pass Remedies for VLA and RLVR链接 : https://arxiv.org/abs/2605.19282Muon（MomentUm Orthogonalized by Newton–Schulz）作为 LLM 预训练中的明星优化器，通过矩阵感知的谱归一化大幅提升了训练效率。但如果你直接把它搬到视觉语言动作（Vision-Language-Action, VLA）模型或基于可验证奖励的强化学习（RLVR）中，可能会发现模型不仅不收敛，甚至直接崩溃。这篇论文给出了一个反直觉的结论：Muon 在预训练中有效的“全谱白化”，在低秩或低信噪比场景下恰恰是毒药。
### 为什么 Muon 在非预训练场景中失效？
Muon 的核心机制是通过 Newton–Schulz (NS) 迭代，将动量矩阵的所有奇异值推向 1（即 msignmsign 操作）。这在 LLM 预训练中能有效增强探索性。然而，论文指出了两个致命场景：
- VLA 训练中的低秩梯度：在 VLA 模型中，动作头（Action Head）的梯度具有极低的本征维度（Effective Rank, erank）。例如在 LIBERO Object 任务中，视觉模块 erank 约 300，语言模块约 50，而动作模块仅为 4-6。Muon 强行将所有奇异值白化为 1，导致原本微不足道的噪声方向被放大到与有效信号同等量级，严重干扰了低秩的动作更新。
- RLVR 中的低信噪比（SNR）：在 RLVR（如 GRPO）中，梯度是轨迹级别的稀疏奖励信号，而非 SFT 中的 Token 级监督。这导致梯度 SNR 极低。Muon 的均匀白化会将这些高方差噪声同等放大，导致策略迅速崩溃（Accuracy 跌至接近 0）。
### Pion：引入谱域的高通滤波为了解决上述问题，作者提出了 Pion (sPectral hIgh-pass Optimization on momeNtum)。其核心 Insight 非常清晰： 不要均匀白化，而要保留头部有效信号，抑制尾部噪声。
Pion 没有引入昂贵的 SVD 计算，而是重新设计了 NS 迭代的多项式系数，将其拆分为两个阶段：
- 提升阶段 (Promotion)：使用多项式 fp(σ)f_p(\sigma)​(σ) 放大所有奇异值，确保主导方向被充分激活。
- 抑制阶段 (Suppression)：使用多项式 fs(σ)f_s(\sigma)​(σ) 将较小的奇异值推向 0，同时保持大奇异值在 1 附近。
这种“先提后抑”的组合形成了一个 谱域高通滤波器 。此外，针对 RLVR 中注意力头（Attention Head）的异构性，Pion 支持 Per-Head 模式 ，即在重塑矩阵后对每个 Head 独立进行 NS 迭代，以保留预训练阶段形成的 Head 特异性。
### 关键实验结果论文在 VLA 和 RLVR 两个领域进行了详尽对比，数据极具说服力：
1. VLA 仿真与真机测试在 LIBERO 基准上，Pion 显著优于 Muon 和 AdamW：
- LIBERO Object (1,500 steps): Pion 达到 100% 成功率，Muon 为 97.0%，AdamW 仅为 32.2%。
- VLANeXt (Flow-matching): 在更具挑战性的 LIBERO-Plus 上，Pion 平均成功率达 75.93%，远超 Muon (72.34%) 和 AdamW (64.57%)。特别是在语言扰动下，Pion 领先 Muon 近 10%。
- 真机 Franka Robot: 在 DROID 设置的抓取放置任务中，Pion 平均成功率高达 85.6%，而 Muon 仅为 38.9%，AdamW 为 31.1%。
2. RLVR 后训练在使用 Qwen3-1.7B/4B 进行 GRPO/GMPO 训练时：
- Muon 彻底失效：在 MATH 和 GSM8K 任务上，Muon 的准确率迅速下降并收敛至接近 0。
- Pion 稳定领先：Pion (Per-Head) 在所有设置下均优于 AdamW，且避免了 Muon 的崩溃问题。例如在 Qwen3-1.7B + GRPO + MATH 设置中，Pion 保持了稳定的上升曲线，而 Muon 直接崩盘。
### 工程启示- 优化器不能“一招鲜”：Muon 并非万能钥匙。在处理低秩数据（如机器人动作、图像生成）或高噪声信号（如 RL 奖励）时，均匀谱归一化是有害的。
- 低成本改进可行：Pion 仅通过修改 NS 迭代的多项式系数就实现了性能跃升，且计算开销与 Muon 完全一致。这意味着你可以轻松在现有代码库中替换 Muon 为 Pion，无需额外硬件支持。
- 关注梯度结构：在调试训练不收敛问题时，不妨检查一下梯度的 Effective Rank 或 SNR。如果数据本身低秩，尝试使用具有谱抑制能力的优化器可能比调整学习率更有效。
### 局限与展望Pion 目前主要验证于 VLA 和 RLVR 场景，其在大规模多模态预训练（如 LLaVA 类模型的全量预训练）中的表现尚待探索。此外，Per-Head 模式虽然有效，但增加了实现复杂度，对于非 Transformer 架构可能需要适配。
总之，如果你正在做机器人学习或强化学习微调，别再用默认的 Muon 了，试试 Pion 的高通滤波策略，效果可能出乎意料。
## 📝 AI 点评点评时间：2026-05-25 18:06 ｜ reviewer: DeepSeek V4 Flash核心贡献: 本文首次识别出Muon优化器在VLA训练（低秩梯度）和RLVR后训练（低信噪比梯度）中的根本缺陷——均匀谱白化会放大噪声方向，并提出了Pion，一种通过两阶段（提升+抑制）高通过滤的Newton–Schulz迭代替代Muon的方法，在保持相同计算开销的同时实现稳定训练。
亮点: 博文准确提炼了Muon失效的两大核心机制（低秩与低信噪比），并清晰解释了Pion通过“先提后抑”实现高通滤波的设计思路，对实验数据（LIBERO、RLVR准确率等）的引用忠实且具体，突出了Pion在VLA和RLVR场景下的显著优势。
挑刺: 1. 博文未提及Pion的per-head模式在RLVR中的关键动机——原文Fig.4及其分析表明，per-head模式用于保留预训练注意力头的异构性（cross-head variance），这是Pion在RLVR中成功的重要设计，博文仅简单提到“支持Per-Head模式”而未解释为何需要。2. 博文称“Per-Head模式虽然有效，但增加了实现复杂度”，但原文明确说明该模式仅通过reshape操作实现，incurring no additional cost，此表述与原文不符。3. 博文未引用原文中的反向消融实验（Low-pass Muon, Fig.8），该实验严格证明了Pion的增益来源于高通滤波而非其他结构变化，属于关键证据的遗漏。
总评: ⭐⭐⭐½ 博文准确反映了论文的核心发现和实验结果，但遗漏了per-head模式的动机解释和反向消融实验，导致关键insight传递不够完整。
