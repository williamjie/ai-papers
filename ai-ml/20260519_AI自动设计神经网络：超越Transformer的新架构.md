# AI 自动设计神经网络：超越 Transformer 的新架构

**日期**: 2026-05-19

---

论文 : Agentic Discovery of Neural Architectures: AIRA-Compose and AIRA-Design链接 : https://arxiv.org/abs/2605.15871Meta FAIR 最新这篇工作有点意思。它不只是让 AI 写代码，而是让 AI Agent 自主发现比人类设计的 Transformer 更高效、更强大的神经网络架构。这对于我们理解“下一代基础模型长什么样”以及“如何自动化科研”具有极高的工程参考价值。
### 为什么需要 AI 来设计模型？
目前主流的大模型几乎都基于 Transformer，但其二次方复杂度（Attention）和 KV Cache 内存开销是硬伤。虽然 Mamba 等状态空间模型（SSM）提供了线性复杂度的替代方案，但如何混合使用 Attention、MLP 和 SSM 以构建高效的“混合架构”，其组合空间是巨大的（例如 16 层架构有 316≈43003^{16} \approx 4300 ≈ 4300 万种排列）。
依靠人类专家的经验（Human Intuition）去遍历这个空间既低效又容易陷入局部最优。Meta 提出的核心 Insight 是：将神经架构搜索（NAS）转化为 AI Agent 的任务，利用 LLM 的逻辑推理能力去探索组合空间，而不是依赖传统的贝叶斯优化或随机搜索。
### 核心方法拆解：双框架策略论文提出了两个互补的框架，分别解决“高层结构”和“底层机制”的设计问题：
-AIRA-Compose（高层架构搜索）
任务：在固定的计算预算（24 小时）下，11 个 Agent 协作搜索由 Attention、MLP 和 Mamba 组成的 16 层小模型架构。
- 策略：Agent 不是随机组合，而是通过“假设-验证-迭代”循环。例如，Agent 会提出“使用周期性 Attention 锚点配合 Mamba 段”的假设，生成代码，评估性能，再根据反馈改进。
- 缩放：小模型筛选出的 Top 架构会被外推（Extrapolate）到 350M、1B 和 3B 参数规模进行最终评估。
-AIRA-Design（底层机制实现）
任务：要求 Agent 从零编写处理长程依赖的新型 Attention 机制代码，或优化训练脚本。
- 场景：针对 Long Range Arena (LRA) 基准测试和 Autoresearch 训练效率挑战。
### 关键实验结果Agent 发现的架构在多个维度上超越了人工设计的基线（Llama 3.2）和传统 NAS 工具（Composer）：
指标/模型 对比基线 (Llama 3.2) 提升幅度 备注 AIRAformer-D Llama 3.2 +2.4% 下游任务准确率提升 AIRAhybrid-D Llama 3.2 +3.8% Transformer-Mamba 混合架构 AIRAformer-C Llama 3.2 54% 更快 计算最优缩放前沿 (Scaling Frontier) AIRAformer-C Composer 最佳 71% 更快 相比传统自动化搜索工具 AIRAhybrid-C Nemotron-2 23% 更快 混合架构的缩放效率在底层设计方面，Agent 设计的架构在 LRA 基准测试中，文档匹配准确率仅比人类 SOTA 低 2.3%，文本分类低 2.6%。在 Autoresearch 任务中，最佳 Agent 达到了 0.968 的验证 BPB（Bits-per-Byte），超越了公开参考值。
### 工程启示- 混合架构是趋势：实验表明，简单的 Transformer 堆叠并非最优。Agent 发现的 AIRAhybrids 证明了 Attention 和 Mamba 的混合排列能带来显著的缩放效率提升。我们在构建私有化部署模型时，可以关注这类混合结构以平衡推理速度和精度。
- Agent 作为科研助手：AIRA-Compose 展示了 Agent 如何理解“架构设计原则”（如残差连接、归一化位置）。未来，我们可以利用类似的 Agent 框架，针对特定业务数据自动搜索最优的轻量级模型结构，而非盲目微调通用大模型。
- 小模型代理大模型：在百万参数级别筛选架构，再外推到十亿级别，这种 Proxy Training 策略极大地降低了搜索成本。这是工程落地中极具价值的低成本探索范式。
### 局限与展望目前的方法仍依赖于预定义的基元（Primitives）池。虽然 AIRA-Design 允许从零编写代码，但在复杂度的控制上仍有挑战。此外，Agent 的搜索深度受限于计算预算（24 小时/500 步）。随着 LLM 推理能力的增强，未来 Agent 可能发现完全颠覆现有范式的新型计算基元。
