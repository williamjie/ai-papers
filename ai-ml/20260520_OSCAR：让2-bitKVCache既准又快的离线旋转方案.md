# OSCAR：让2-bit KV Cache既准又快的离线旋转方案

**日期**: 2026-05-20

---

论文 : OSCAR: Offline Spectral Covariance-Aware Rotation for 2-bit KV Cache Quantization链接 : https://arxiv.org/abs/2605.17757在长上下文 LLM 推理中，KV Cache 的内存占用是吞吐量（Throughput）的最大瓶颈。INT2 量化理论上能带来 8 倍的内存压缩，但之前的尝试往往因为精度崩塌而难以落地。这篇来自 Together AI 的论文提出了一种名为 OSCAR 的离线旋转量化方案，它不仅解决了 INT2 精度丢失的老大难问题，还完美兼容现有的 PagedAttention 推理栈，是目前工程落地价值极高的工作。
### 痛点：为什么普通的旋转量化在 INT2 下失效？
现有的 KV Cache 量化方案（如 QuaRot）通常使用 Hadamard 变换或随机正交矩阵对激活值进行旋转。这种“数据无关”的旋转能抹平激活值的异常值（Outliers），使得分布更均匀，从而利于量化。
但在 INT2（仅 4 个量化等级）这种极端低位宽下，单纯抹平分布是不够的。核心 Insight 在于： Attention 机制并不直接消费 KV Cache 的原始欧氏距离，而是消费 Query 与 Key 的相关性以及 Score 加权的 Value 聚合。
如果旋转矩阵没有对齐 Attention 实际关注的协方差结构，量化引入的噪声就会直接破坏 Attention Score 的分布。之前的方案把误差均匀分散，但在 INT2 下，这些误差累积起来足以让模型“失忆”。
### 方法拆解：用 Attention 的协方差指导旋转OSCAR 的核心设计逻辑是： 让量化误差发生在 Attention 不敏感的方向上。
它通过一个轻量级的离线校准（Calibration）过程，分别计算 Key 和 Value 的“注意力感知协方差矩阵”，并据此推导旋转矩阵：
- Key 的旋转（Query-Aware）：
Key 用于计算 Logits。OSCAR 估算 Query 的协方差矩阵 CQC_Q​，对其进行特征分解，得到旋转矩阵 RKR_K​。这样旋转后的 Key，其量化误差在 Query 的视角下是最小的。
- Value 的旋转（Score-Aware）：
Value 用于加权求和。OSCAR 利用 Attention Score 矩阵 SS，构建目标协方差 CS=VTSTSVC_S = V^T S^T S V​=VTSTSV，并分解得到 RVR_V​。这确保了量化后的 Value 在 Attention 加权聚合时，误差最小。
- 工程优化组合：
最终的旋转矩阵是 R=U⋅HHad⋅PbrR = U \cdot H_{Had} \cdot P_{br}U⋅HHad​⋅Pbr​。其中 UU 是上述协方差导向的特征向量，HHadH_{Had}​ 是 Hadamard 变换（进一步平滑能量分布），PbrP_{br}​ 是比特反转置换（让相邻通道的动态范围相似，利于 Block Quantization）。
此外，OSCAR 采用混合精度策略：保留 Sink Token（前 64 个）和 Recent Window（最近 256 个）为 BF16 精度，中间的长历史部分使用 INT2。这种设计在极小的内存开销下（仅增加 0.24% BF16 开销）大幅提升了精度。
### 关键结果：精度与吞吐量的双杀OSCAR 在多个基准测试中展现了统治级的表现，以下是关键数据对比：
1. 精度对比（Qwen3-8B, AIME25 任务）
方法 有效比特率 (BPE) AIME25 准确率 相比 BF16 的差距 BF16 (Baseline) 16.00 66.00 - Saw-INT4 4.25 59.67 -6.33 QuaRot-INT2 2.25 2.22 -63.78 OSCAR (INT2) 2.28 66.67 +0.67注：Naive INT2 和 QuaRot-INT2 在长上下文下精度几乎归零，而 OSCAR 甚至略微超越了 BF16 基线。在 Qwen3-32B 上，OSCAR 也将 BF16 的精度差距缩小到了 3.78 分。
2. 长上下文鲁棒性（RULER-NIAH, 128K 上下文）
在 128K 的极端长上下文中，QuaRot-INT2 的检索准确率已降至 0%，而 OSCAR 仍保持 39.5% 的准确率，显著优于其他 INT2 方案。
3. 系统吞吐量提升由于 KV Cache 内存占用减少约 8 倍，OSCAR 大幅缓解了显存带宽压力：
- 单用户解码：在 100K 上下文长度下，OSCAR 比 BF16 快 3.08 倍。
- 高并发场景：在 GLM-4.7-FP8 (358B) 模型上，BS=32 时，OSCAR 的吞吐量比 BF16 高出 7.83 倍。
### 工程启示与局限为什么这篇论文值得你关注？
- 即插即用的兼容性：OSCAR 不需要修改模型权重，也不依赖特殊的稀疏格式。它通过自定义的 Triton 内核实现了 Rotate-Clip-Quantize 的融合，可以直接集成到 SGLang 或 vLLM 中。对于正在部署长上下文服务的工程师来说，这是目前最成熟的 INT2 方案。
- 离线校准的低成本：旋转矩阵和裁剪阈值只需通过少量校准数据（如 8k tokens 的 MMLU）一次性计算得出，推理阶段无额外计算开销，非常适合生产环境。
局限与思考- 校准数据的依赖性：虽然论文声称对校准数据不敏感，但协方差矩阵的估计仍依赖于校准分布。如果实际业务数据的分布与校准数据差异巨大，旋转矩阵的有效性可能会下降。
- 硬件支持：目前的 INT2 加速依赖于 Triton 内核的软件实现。随着 NVIDIA 新架构对 INT2 算子的原生支持增强，OSCAR 的收益可能会进一步扩大，但也可能面临来自硬件原生量化方案的竞争。
总体而言，OSCAR 证明了在 KV Cache 量化中，“对齐下游任务（Attention）”比“单纯压缩激活值”重要得多。对于追求极致吞吐量的长上下文推理服务，这是一个必须尝试的方案。
