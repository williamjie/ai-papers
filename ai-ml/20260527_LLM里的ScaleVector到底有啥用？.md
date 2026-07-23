# ⭐⭐⭐½ LLM里的Scale Vector到底有啥用？

**日期**: 2026-05-27

---

论文 : Negligible in Size, Significant in Effect: On Scale Vectors in Large Language Models链接 : https://arxiv.org/abs/2605.26895大家调参的时候，有没有仔细想过 RMSNorm 后面那个小小的可学习向量 γ\gamma （Scale Vector）到底在干嘛？通常我们觉得它参数极少（在 Llama-1B 里占比仅 7.84×10−57.84 \times 10^{-5} 1 0 − 5 ），甚至认为它在 Pre-Norm 架构下是“表达能力冗余”的。但 ByteDance Seed 和北大联合发表的这篇新论文直接打脸： 别小看这几十万个参数，删掉它，预训练效果直接崩盘。
### 为什么它不可或缺？核心 Insight 是“优化加速器”
论文通过理论推导揭示了一个反直觉的事实：在 Pre-Norm 架构中，Scale Vector 并没有增加模型的表达能力 （因为它的缩放作用可以被后续的线性层吸收），但它极大地改善了 优化动力学 。
具体来说，Scale Vector 为后续的线性映射提供了一种**自放大预处理（Self-amplifying Preconditioning）**效果。
- 没有 Scale Vector：梯度下降是标准的，收敛速度受限于数据分布的固有几何结构。
- 有 Scale Vector：它引入了一个状态相关的预处理器 PP，使得有效参数的更新步长被动态放大。简单说，它让模型在训练初期就能更“聪明”地沿着损失函数下降最快的方向走，从而加速收敛。
实验数据很硬核：在 0.12B Llama 模型上，直接移除 Scale Vector，即使重新调优学习率，最终验证损失仍高出约 0.015 ；如果保持相同的学习率策略，Token 效率直接下降 1.4倍 。
### 权重衰减（Weight Decay）该怎么加？
工程界一直有个争议：Scale Vector 要不要加 Weight Decay？论文根据 Scale Vector 的位置给出了明确的分野建议：
- Input-Norm（输入侧归一化）：如标准的 Pre-Norm。必须加 WD。
原理：这里的 Scale Vector 主要起优化作用。不加 WD 会导致参数范数无界增长，Hessian 矩阵条件数恶化，训练不稳定。加 WD 能控制 Hessian 尖锐度，加速训练。
- Output-Norm（输出侧归一化）：如 Q/K-Norm 或 FFN 输出后的 Norm。千万别加 WD。
原理：这里的 Scale Vector 直接决定了子模块的输出尺度，关乎表达能力。加 WD 会强行缩小输出，限制模型容量。
在 Gemma-0.5B 的实验中，遵循“Input-Norm 加 WD，Output-Norm 不加”的策略（称为 IWD），验证损失显著低于统一加或不加 WD 的基线。
### 三大改进策略：让预处理更极致基于上述理解，作者提出了三个轻量级改进，组合起来效果拔群：
- 异构性（Heterogeneity, HG）：
痛点：Attention 中 Q、K、V 共享同一个 Scale Vector，但它们的训练动态不同。
- 解法：给 Q、K、V 分别配备独立的 Scale Vector。虽然不增加表达能力，但提供了更精细的分支级预处理。
- 位置优化（Placement, DP/DNP）：
痛点：标准做法只在输入侧缩放。
- 解法：双端放置（Dual Placement, DP），即在线性层的输入和输出都加 Scale Vector。理论证明这能同时提供行方向和列方向的预处理，加速更快。为了稳定性，还可以引入中间归一化（DNP）。
- 重参数化（Reparameterization, OR/ER）：
痛点：标准向量纠缠了“大小”和“方向”。
- 解法：将 Scale Vector 分解为全局幅度 β\beta 和方向 α\alpha。理论表明，这种各向异性的预处理能更激进地调整尺度，同时保持方向稳定。
### 实验结果：工业级验证作者将上述策略组合成统一方案（HG + DNP + OR + IWD），在 0.12B 到 2B 的 Dense 和 MoE 模型上进行了大规模预训练测试：
- 终端损失更低：在所有规模下，统一策略均优于精心调优的基线。
- Scaling Law 更优：在相同算力预算下，改进后的模型表现出更好的缩放行为。例如在 Dense-1B 模型上，改进方案的损失曲线始终低于基线。
- 开销极小：增加的参数量和计算量几乎可以忽略不计。
### 工程启示这篇论文对实际炼丹有直接指导意义：
- 别乱删参数：哪怕 Scale Vector 占比极小，也不要为了省显存或简化结构而移除它，它是预训练稳定的基石。
- 精细化 WD 配置：检查你的 Trainer 代码，确保 Pre-Norm 的 Scale Vector 应用了 Weight Decay，而 Output-Norm（如果有）没有应用。这是一个零成本的性能提升点。
- 尝试双端缩放：如果正在设计新架构或微调底层结构，可以考虑在 Attention 和 FFN 的线性层两侧都加入可学习缩放向量，这可能带来意外的收敛加速。
这篇工作再次证明，LLM 的成功不仅靠堆算力，更在于对每一个微小组件优化动力学的深刻理解。那些看似“微不足道”的设计细节，往往藏着提升效率的关键钥匙。
## 📝 AI 点评点评时间：2026-05-27 15:09 ｜ reviewer: DeepSeek V4 Flash核心贡献: 论文系统研究了 LLM 中 RMSNorm 的 scale vector（γ），通过理论分析揭示其在 Pre‑Norm 架构中不增加表达能力但通过自放大预处理改善优化动力学，并据此提出针对不同位置的权重衰减策略（Input‑Norm 应加、Output‑Norm 不应加）以及三项轻量级改进（异构性、双端放置、幅度‑方向重参数化），在大规模实验中验证了统一策略的持续收益。
亮点: 博文准确抓住了原文最关键的工程启示：1）scale vector 虽参数极少但不可或缺，删除后 loss 显著升高（约 0.015），并给出了 1.4× token 效率的具体数字；2）明确区分了 Input‑Norm 和 Output‑Norm 的权重衰减策略，并给出了“Pre‑Norm 必须加 WD，Output‑Norm 千万别加”的易执行建议；3）对三项改进（HG、DP/DNP、OR/ER）的核心动机和效果进行了简洁概括，没有偏离原文结论。
挑刺:
- 过度解读“崩盘”：博文称“删掉它，预训练效果直接崩盘”，原文实际是“terminal loss remains approximately 0.015 higher”和“1.4× token-efficiency gain”，loss 差异虽显著但远未到“崩盘”（训练崩溃/发散）的程度，属于情感化夸大。
- 遗漏关键条件“Pre‑Norm”限定：博文在解释 scale vector 不增加表达能力时仅提“在 Pre‑Norm 架构下”，但后文讨论权重衰减和改进时未始终强调该前提。原文明确 Theorem 2.2 和 Section 3 的改进均基于 Pre‑Norm 架构，而 Output‑Norm 的讨论则基于包含 Q/K‑Norm 的 Gemma 架构。博文未提及这一架构依赖，可能让读者误以为所有场景下 scale vector 均冗余。
- 简化理论机制，缺少数字支撑：博文描述“自放大预处理”时仅用“动态放大”等模糊表述，未引用原文中关键不等式（如 λ_min(P_f,j) ≥ γ_j² ≥ 1）或定理编号（Theorem 2.2）。对于改进策略，博文称“理论证明双端放置能同时提供行方向和列方向的预处理”，但原文 Theorem 3.1 的结论是“instantaneous at least as fast”，并非严格“加速更快”，博文的表述略强于原文保证。
总评: ⭐⭐⭐½ 博文基本准确传达了论文的核心发现和工程价值，在关键数字和策略建议上没有事实错误，但存在轻微过度解读和条件简化，整体质量在默认档之上，略优于单纯忠实反映的⭐⭐⭐。
