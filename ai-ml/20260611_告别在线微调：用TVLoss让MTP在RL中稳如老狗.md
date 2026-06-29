# ⭐⭐⭐ 告别在线微调：用 TV Loss 让 MTP 在 RL 中稳如老狗

**日期**: 2026-06-11

---

论文 : Breaking Entropy Bounds: Accelerating RL Training via MTP with Rejection Sampling链接 : https://arxiv.org/abs/2606.12370RL 训练太贵了， rollout（推理采样）阶段占了大半壁江山。大家都想上多 token 预测（MTP）来加速，但现实很骨感：一旦进入 RL 阶段，MTP 的接受率就会断崖式下跌，加速效果直接归零。阿里 Qwen 团队这篇论文不仅指出了病灶，还给出了一个无需在线更新 MTP 的优雅解法。
### 痛点：为什么 MTP 在 RL 里会“失灵”？
常规认知认为，RL 训练时模型权重在变，导致 Draft 模型和 Target 模型分布不匹配（Mismatch），所以接受率下降。但论文通过拆解发现， 真正的元凶是熵（Entropy） 。
⚠️ 反直觉发现 ：在 RL 训练中，MTP 接受率的下降主要归因于策略模型熵值的波动，而非权重更新带来的分布不匹配。
RL 为了鼓励探索，策略模型的熵值通常会升高或剧烈波动。对于传统的 Target-Only 采样，接受率上限被 max⁡p(y)\max p(y) 锁死，熵越高，峰值概率越低，接受率必然线性下降。即使换成 Rejection Sampling，如果使用常规的交叉熵（CE）损失训练 Draft，其梯度更新是均匀的，导致在高熵状态下 TV 距离依然累积变大，接受率照样随熵值升高而下跌。
### 核心解法：端到端 TV Loss + 拒绝采样论文提出的 Bebop 方案包含两个关键设计：
-改用拒绝采样（Rejection Sampling）：
其接受率取决于分布重叠度 ∑min⁡(p,q)\sum \min(p, q)，对熵值的敏感度远低于 Target-Only 采样。这打破了“熵高必死”的物理限制。
-提出端到端 TV Loss（End-to-End TV Loss）：
这是最精彩的 Insight。CE/KL 损失优化的是分布距离的上界，并不直接对应 Rejection Sampling 的接受率（由 TV 距离决定）。
TV Loss 梯度特性：∂LTV∂zj∝qj\frac{\partial L_{TV}}{\partial z_j} \propto q_j​∂LTV​​∝qj​。这意味着梯度与 Draft 输出的概率成正比。
- 工程意义：它会自动抑制长尾噪声，将优化资源集中在高概率 token 上。这种“概率比例误差”使得 TV 距离不再随熵值指数级恶化，从而实现了接受率对熵值的解耦。
### 实验数据：拒绝在线更新的诱惑论文在 Qwen3.5/3.6/3.7 系列模型上进行了大规模验证。核心结论是： 只需要在 SFT 阶段用 TV Loss 预训练一次 MTP，后续 RL 全程冻结即可。
任务类型 CE Loss (Baseline) e2e TV Loss (Ours) 提升幅度 Math 75.0% 78.0% +3.0% Code 71.3% 74.6% +3.3% SWE-Bench 75.1% 83.1% +8.0% Agent 90.3% 97.0% +6.7%数据来源：Table 2，Rejection Sampling, γ=3\gamma=3 3更令人惊喜的是稳定性。在 RL 训练过程中，CE Loss 训练的 MTP 接受率随熵值波动剧烈下降；而 TV Loss 训练的 MTP 接受率几乎是一条直线，全程维持在高位。这直接带来了 1.8x 的端到端 RL 训练加速 ，且省去了在线更新 MTP 带来的巨大显存和计算开销。
### 工程启示对于正在落地 RL 微调的团队，这篇论文提供了明确的避坑指南：
- 别在 RL 里死磕 MTP 在线更新：除非你使用 Target-Only 采样，否则 Rejection Sampling + TV Loss 预训练足以覆盖整个 RL 周期。
- Loss 函数要匹配采样策略：如果你用 Rejection Sampling 加速推理或训练，就别再用 CE/KL 损失了，直接上 TV Loss，收益肉眼可见。
- Agent 任务受益最大：在 SWE-Bench 和 Agent 任务上，TV Loss 带来了高达 8% 的接受率提升，这对长文本生成的加速效果尤为显著。
这篇论文没有搞复杂的架构创新，而是回归基础理论，用正确的 Loss 函数解决了工程痛点。这种“少即是多”的思路，值得所有追求训练效率的团队参考。
## 📝 AI 点评点评时间：2026-06-11 15:05 ｜ reviewer: DeepSeek V4 Flash核心贡献: 揭示RL训练中MTP接受率下降的根本原因是策略模型熵的波动而非分布不匹配，提出端到端TV Loss直接优化拒绝采样接受率，并证明仅需SFT阶段预训练即可在整个RL过程中保持高接受率，无需在线更新MTP。
亮点: 1. 博文准确抓住了“熵是元凶”这一反直觉发现，并清晰对比了Target-Only与Rejection Sampling在熵敏感性上的本质差异。2. 对TV Loss梯度特性的提炼（“自动抑制长尾噪声，将优化资源集中在高概率token上”）直观传达了方法的核心机制。3. 实验数据表格（Math/Code/SWE/Agent）与原文一致，且“1.8×加速”、“Agent任务受益最大”等工程结论呈现到位。
挑刺: 1. 博文开头称“一旦进入 RL 阶段，MTP 的接受率就会断崖式下跌，加速效果直接归零”，但原文仅表述为“suffers from a significant decline…limited speedup”（§1），并未断言加速效果“归零”，属于过度夸张。2. 博文总结“只需要在 SFT 阶段用 TV Loss 预训练一次 MTP，后续 RL 全程冻结即可”，但原文Limitations（§9）明确指出当RL探索使策略熵显著超出SFT覆盖范围时，TV训练也会恢复熵-接受率依赖，此时仍需在线MTP协同训练，博文未提及这一关键边界条件。3. 博文对TV Loss梯度的描述“ ∂LTV∂zj∝qj\frac{\partial L_{TV}}{\partial z_j} \propto q_j ​ ∂ L T V ​ ​ ∝ q j ​ ”过于简化，原文式(11)为 ∂LTV∂zj=−qj[1[qj≤pj]−S]\frac{\partial L_{TV}}{\partial z_j} = - q_j [1[q_j \leq p_j] - S] ​ ∂ L T V ​ ​ = − q j ​ [ 1 [ q j ​ ≤ p j ​ ] − S ] ，其中包含区分接受/拒绝令牌的指示函数和全局项S，简化表述可能掩盖其选择性梯度行为的完整机制。
总评: ⭐⭐⭐ 博文准确传达了论文的核心发现与工程价值，但存在少量过度夸张和关键约束遗漏，整体忠实可用。