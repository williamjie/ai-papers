# GRPO聚合偏差：为何Token平均不如Balanced Aggregation

**日期**: 2026-05-08

---

在强化学习验证奖励（RLVR）微调大模型时，GRPO 因其无需训练 Critic 模型而成为工业界首选。然而，一个常被忽视的底层细节—— 策略梯度项的聚合方式 ，正在悄悄影响模型的收敛稳定性。复旦大学与清华大学等机构联合提出的 Balanced Aggregation (BA) 指出，现有的 Token 聚合和 Sequence 聚合都存在系统性偏差，而 BA 通过简单的权重重构，在保持训练稳定性的同时提升了最终性能。
## 问题与动机：被忽视的“聚合”陷阱GRPO 的核心逻辑是：对每个 Prompt 采样一组响应，计算组内归一化优势（Advantage），然后优化 PPO 目标。但这里有一个关键设计选择： 如何将 Token 级的 PPO 贡献聚合为 Group 级的 Loss？
目前主流方案只有两种：
- Sequence Aggregation (Seq-Agg)：先对每个 Response 内的 Token 求平均，再对所有 Response 求平均。这是标准 GRPO 的做法。
- Token Aggregation (Tok-Agg)：直接对 Group 内所有 Token 求平均。DAPO 和 Dr.GRPO 等近期工作推崇此法，认为它能避免长序列被低估。
论文指出，这两种方法并非简单的实现差异，而是引入了截然不同的 优化偏差（Optimization Bias） ：
- Token Aggregation 引入了“符号-长度耦合”（Sign-Length Coupling）：正样本和负样本对梯度的贡献不仅取决于优势值，还取决于它们的平均长度。如果正负样本长度分布不均，梯度平衡会被打破。
- Sequence Aggregation 引入了“序列等权偏差”：它强制每个 Response 贡献相同的权重，无论其包含多少 Token。这会导致长响应被隐式降权，短响应被隐式升权。
## 方法拆解：Balanced Aggregation (BA) 的核心直觉BA 的设计目标很明确：既要消除 Token Aggregation 的符号-长度耦合，又要避免 Sequence Aggregation 的强等权惩罚。
BA 的操作步骤非常直观，且是一个即插即用的模块（Drop-in Replacement）：
- 分组：根据归一化优势的正负，将 Group 内的 Response 分为正样本集 S+S_+​ 和负样本集 S−S_-​。
- 组内 Token 平均：分别在正样本集和负样本集内部计算 Token 级的平均 Loss。这保留了 Token 聚合的信息密度，但不混合正负信号。
- 序列计数加权：将正负两组的平均 Loss 按照序列数量进行加权合并。权重分别为 k/Gk/G 和 (G−k)/G(G-k)/Gk)/G，其中 kk 是正样本数量，GG 是总样本数。
为什么这么设计？
BA 在组内保留了 Token 级平均，避免了 Sequence Aggregation 中“每个 Response 权重相等”的极端情况；但在组间，它使用了与 Sequence Aggregation 相同的平衡系数（即正负样本数量的比例）。这意味着 BA 继承了 Sequence Aggregation 的 符号平衡性 （确保正负梯度方向正确抵消），同时消除了 Token Aggregation 中因长度差异导致的权重偏移。
## 关键结果：稳定压倒一切论文在 Qwen2.5-Math-7B 和 Qwen3-1.7B 模型上，使用 DAPO-17k 和 Polaris 数据集进行了实验，评估涵盖 Math-500, AIME 2024/2025, LiveCodeBench 等六个基准。
以下是 Table 1 中的核心数据对比（Last-Step Accuracy，即最终步骤准确率）：
模型 数据集 seq-agg token-agg balanced-agg (BA) Qwen2.5-Math-7B DAPO-17k 0.3446 0.3364 0.3424 Polaris 0.3172 0.3292 0.3319 Qwen3-1.7B DAPO-17k 0.4481 0.4360 0.4695 Polaris 0.4614 0.4349 0.4640数据解读：
- BA 始终是最强或最接近最强的：在所有四个设置中，BA 的 Last-Step Accuracy 均优于或持平于基线。
- 稳定性优势明显：Token Aggregation 虽然在部分场景下 Peak Performance 较高，但在训练后期经常出现性能崩塌（如 Qwen3-1.7B 在 Polaris 上从 0.6058 跌至 0.5608）。BA 则能更好地保留训练成果。
- 模型依赖性：Token Aggregation 在 Qwen2.5 上表现尚可，但在 Qwen3 上表现较差；而 BA 在不同模型间表现稳健。
## 工程启示：何时该用哪种聚合？
论文通过分析训练过程中的长度统计，给出了更细致的工程建议：
- 如果正负样本长度差异大（如 Qwen3）：Token Aggregation 会严重扭曲梯度，导致训练不稳定。此时 Sequence Aggregation 或 BA 更优。
- 如果响应长度方差大但正负长度差异小（如 Qwen2.5）：Sequence Aggregation 会过度惩罚长响应，此时 Token Aggregation 可能暂时领先，但 BA 依然能提供最佳稳定性。
结论 ：对于大多数工程实践， 直接使用 Balanced Aggregation 是最安全的选择 。它不需要调整超参数，只需修改聚合逻辑，即可在保持训练稳定性的同时，获得优于单一聚合策略的最终效果。
## 局限与展望BA 目前主要基于二元奖励（Binary Reward，如正确/错误）推导得出，虽然论文提到可推广至非二元奖励，但尚未提供详细的实证支持。此外，BA 的计算开销略高于 Token Aggregation，因为需要额外的分组和统计步骤，但在现代 GPU 集群上，这一开销几乎可以忽略不计。
