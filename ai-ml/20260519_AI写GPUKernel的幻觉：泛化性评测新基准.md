# AI 写 GPU Kernel 的幻觉：泛化性评测新基准

**日期**: 2026-05-19

---

论文 : AgentKernelArena: Generalization-Aware Benchmarking of GPU Kernel Optimization Agents链接 : https://arxiv.org/abs/2605.16819如果你正在用 AI 辅助编写 GPU Kernel，这篇论文必须看。它揭示了一个残酷真相：目前的 Coding Agent 在优化现有代码时表现优异，但在从零生成代码时，往往只是在“死记硬背”测试用例的形状，一旦输入维度变化，代码就会崩溃。
## 为什么现有的 Benchmark 不够用了？
现有的代码基准测试（如 HumanEval, SWE-bench）大多关注功能正确性，且多为单次调用（Single-shot）。对于 GPU Kernel 这种极度依赖性能优化的场景，它们存在两个致命缺陷：
- 缺乏 Agent 工作流评估：真正的工程师是“写代码-编译-报错-调试-Profiling”循环迭代的，而不是让 LLM 猜一次。
- 忽视泛化性（Generalization）：之前的基准（如 KernelBench）只测试 Agent 见过的输入形状。这导致 Agent 可以硬编码特定尺寸下的优化策略，从而刷高分，但在生产环境遇到新尺寸时直接失效。
AMD 提出的 AgentKernelArena 旨在解决这些问题。它是一个开源基准，包含 196 个真实世界任务，强制 Agent 在沙盒中完成完整的编译、正确性检查和性能测试闭环，并首次引入了 未见配置泛化协议 （Unseen-configuration Generalization Protocol）。
## 核心设计：如何测出 Agent 的真本事？
AgentKernelArena 的设计直觉非常工程化： 不要相信 Agent 自己说的性能，要由隔离的评估器来验证。
### 1. 三类任务覆盖不同难度- HIP-to-HIP (24 tasks)：给定参考 HIP Kernel，要求优化。考察 Agent 对底层硬件特性（如 Warp Shuffle, Vectorized Loads）的应用。
- Triton-to-Triton (148 tasks)：给定参考 Triton Kernel，要求优化。考察对块级编程模型（Block-level Programming）的调优能力。
- PyTorch-to-HIP (24 tasks)：给定 PyTorch Module，从零写 HIP Kernel。这是最难的模式，要求 Agent 跨越抽象鸿沟，处理内存布局和线程映射。
### 2. 门控评估流水线（Gated Pipeline）
评估严格分为三步，前一步失败则后续不执行：
- 编译：必须成功编译。
- 正确性：输出必须与参考实现一致（容忍数值误差）。
- 性能：计算加速比 s=tbase/topts = t_{base} / t_{opt}tbase​/topt​。
得分公式设计巧妙： Score=20⋅1compile+100⋅1correct+100⋅sk⋅1correctScore = 20 \cdot \mathbb{1}_{compile} + 100 \cdot \mathbb{1}_{correct} + 100 \cdot s_k \cdot \mathbb{1}_{correct} 20 ⋅ 1 co m p i l e ​ + 100 ⋅ 1 cor r ec t ​ + 100 ⋅ s k ​ ⋅ 1 cor r ec t ​ 。这意味着 正确性高于一切 ，即使编译通过但结果错误，得分也无法超过正确但无加速的代码。
### 3. 未见配置泛化测试这是本文最大的亮点。Agent 在优化时只能看到有限的输入形状。评估时，系统会注入 Agent 从未见过 的输入配置（如非 2 的幂次维度、极端长宽比等），计算泛化间隙 Δg\Delta_g ​ 。如果 Δg\Delta_g ​ 很大，说明 Agent 只是过拟合了训练时的形状。
## 关键结果：Agent 真的懂 GPU 吗？
论文测试了 Cursor Agent, Claude Code, Codex Agent 等主流工具。硬件平台为 AMD Instinct MI300X。
### 1. 优化现有代码：Agent 很强在 HIP-to-HIP 和 Triton-to-Triton 任务中，Agent 的表现令人印象深刻：
- HIP-to-HIP：最佳配置（Claude Code / Opus 4.6）实现了 6.69x 的平均加速比。
- Triton-to-Triton：最佳配置（Cursor Agent / Opus 4.7 High）实现了 2.13x 的平均加速比。
- 正确率：绝大多数配置的正确率超过 95%，编译率接近 100%。
### 2. 从零生成代码：幻觉严重在 PyTorch-to-HIP 任务中，虽然加速比看起来很高（最高达 6.89x ，因为基线是较慢的 PyTorch Eager 模式），但泛化性测试暴露了严重问题：
- 正确率暴跌：Agent 生成的 Kernel 在未见配置上的条件正确率仅为 59.7% - 90.3%。
- 硬编码假设：许多 Agent 在生成代码时硬编码了特定维度的假设，导致在遇到新形状时直接崩溃或产生错误结果。
### 3. 不同模型的策略差异- Claude Code：最啰嗦（平均 39-86K tokens），但在 HIP 优化上表现最佳。
- Cursor Agent：在 Triton 优化上略胜一筹，且 Opus 4.7 High 在 PyTorch-to-HIP 上达到了最高的几何平均加速比（4.64x）。
- Codex Agent：最简洁（13-17K tokens），在 PyTorch-to-HIP 上保持了较好的平衡（90.3% 条件正确率）。
## 工程启示- 不要盲目信任 AI 生成的 Kernel：尤其是从零生成的代码，必须经过严格的泛化性测试。仅仅在几个固定尺寸上跑通是不够的。
- Agent 更适合“优化”而非“创造”：目前 Agent 在修改和优化现有 Kernel（HIP-to-HIP, Triton-to-Triton）上表现稳定，泛化性好；但在从零生成低层代码时，仍容易陷入形状特定的陷阱。
- 评估标准需升级：如果你的团队正在评估 AI 编程工具，建议引入类似 AgentKernelArena 的“未见配置”测试。这能帮你过滤掉那些只会“背题”的模型。
## 局限与展望目前基准仅针对 AMD GPU，且主要评估商业闭源模型。开源模型在单轮调用中编译失败率高，需要更复杂的 Agent 循环支持。未来，随着 Agent 迭代次数的增加和更多硬件平台的支持，我们有望看到真正具备通用泛化能力的 Kernel 生成 Agent。
