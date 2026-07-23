# 长文本推理提速：CompactAttention 工程拆解

**日期**: 2026-05-19

---

论文 : CompactAttention: Accelerating Chunked Prefill with Block-Union KV Selection链接 : https://arxiv.org/abs/2605.16839在长上下文（Long Context）大模型的推理服务中， 分块预填充（Chunked Prefill） 已经成为主流调度策略。然而，现有的稀疏注意力（Sparse Attention）方案在分块场景下往往水土不服，要么 Kernel 效率暴跌，要么引入巨大的内存拷贝开销。这篇来自首尔大学的论文提出了一种巧妙的设计解耦思路： CompactAttention 。它不重新发明稀疏 Kernel，而是通过“块级联合选择（Block-Union Selection）”将稀疏掩码转化为 Paged Attention 的元数据，在保持精度的同时实现了显著的加速。
### 为什么现有方案在 Chunked Prefill 中失效？
要理解 CompactAttention 的价值，必须先看清当前工程实践中的两个痛点：
- 稀疏 Kernel 的并行度陷阱：传统的块稀疏注意力（如 XAttention、FlashPrefill）依赖于巨大的 Q×KVQ \times KVKV 矩阵来分摊不规则内存访问的开销。但在分块预填充中，查询序列长度（Query Length）被限制在较小的 Chunk Size（通常几百到 1000 tokens），而 Key-Value 缓存（KV Cache）却随着历史积累变得极长。这种 Q≪KVQ \ll KVKV 的极端不对称导致稀疏 Kernel 无法发挥并行优势，实际加速比远低于理论稀疏度。
- Token 级选择的拷贝成本：另一种思路如 QUOKA，通过采样查询来筛选重要的 Token 级 KV。但这带来了两个问题：一是可能漏掉对未采样查询至关重要的 KV，导致精度下降；二是必须在 Attention 计算前将分散的 KV 显式拷贝（Gather）到连续内存中，随着上下文变长，这种内存带宽开销成为了新的瓶颈。
### 核心 Insight：解耦“选择”与“执行”
CompactAttention 的核心直觉非常清晰： 稀疏掩码（Sparse Mask）不应直接作为 Kernel 的执行计划，而应作为 KV 选择的信号。
作者提出了一种两步走策略：
- 选择阶段（Selection）：利用轻量级的稀疏模式搜索方法（如 SeerAttention 或 FlashPrefill）生成初始的 2D 块稀疏掩码。
- 转换与执行阶段（Execution）：通过 Q-Block Union（查询块联合）和 Intra-Group Union（组内联合），将每个 Head 的 2D 掩码降级为每个 GQA 组的 1D KV 块表。
这种设计的精妙之处在于，它生成的块表是 Paged Attention 可以直接消费的元数据。通过修改 KV Cache 的内存布局为 KV-Head-Major （而非传统的 Sequence-Major），系统可以直接在原地（In-place）访问被选中的 KV 块，完全避免了显式的 KV 拷贝（Zero-Copy）。
### 关键实验结果论文在 LLaMA-3.1-8B-Instruct 和 Qwen3-30B 上进行了详尽评估，结果令人印象深刻：
- 速度提升：在 H200 GPU 上，针对 128K 上下文长度的分块预填充，CompactAttention-FP（基于 FlashPrefill）实现了 2.72× 的注意力加速，端到端（End-to-End）加速达到 1.96×。
- 精度保持：在 RULER 基准测试中，CompactAttention-SA 在 128K 长度下保持了 74.28% 的平均准确率，与密集注意力（Dense Attention）的 74.50% 几乎持平，且显著优于 QUOKA 的 70.44%。
- 消融实验验证：在匹配稀疏度的情况下，CompactAttention 的零拷贝执行策略比传统的稀疏 Kernel 执行快得多。即使考虑到元数据构建的微小开销，其总延迟仍远低于需要显式拷贝的方案。
方法 RULER 128K 准确率 H200 注意力加速 (128K) 核心机制 Dense Attention 74.50% 1.00× 基线 QUOKA 70.44% 1.73× 查询采样 + 显式拷贝 XAttention 74.50% 0.54× 块稀疏 Kernel (效率低) CompactAttention-FP 74.17% 2.72× 块联合 + 零拷贝 Paged### 工程启示对于从事 LLM 推理服务优化的工程师，这篇论文提供了三个重要指导：
- 不要盲目追求稀疏 Kernel：在 Q≪KVQ \ll KVKV 的分块场景下，稀疏 Kernel 的固定开销占比过高。利用成熟的、高度优化的密集 Paged Attention Kernel 往往能获得更好的实际性能。
- 元数据驱动优于数据移动：通过改变内存布局（KV-Head-Major）和元数据表（Block Table）来指导计算，比在计算前重组数据（Compaction）更高效。这符合现代 GPU 架构中“计算密集、访存受限”的特点。
- GQA 友好型设计：利用 GQA 中多个 Query Head 共享 KV Head 的特性进行组内联合（Intra-Group Union），虽然会略微降低稀疏度，但极大地简化了执行逻辑，且通过更激进的初始稀疏阈值即可补偿精度损失。
### 局限与展望CompactAttention 的效果高度依赖于底层稀疏模式搜索的质量。如果初始掩码漏掉了关键 KV，后续的联合操作无法恢复。此外，该方法在上下文较短时优势不明显，因为元数据构建和模式搜索的固定开销尚未被长序列分摊。未来，随着更高效的轻量级稀疏搜索算法的出现，CompactAttention 的加速潜力将进一步释放。
