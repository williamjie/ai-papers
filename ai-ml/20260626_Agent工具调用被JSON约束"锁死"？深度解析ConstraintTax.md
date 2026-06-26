# ⭐⭐⭐½ Agent工具调用被JSON约束"锁死"？深度解析Constraint Tax

**日期**: 2026-06-26

---

论文 : Constraint Tax in Open-Weight LLMs: An Empirical Study of Tool Calling Suppression Under Structured Output Constraints链接 : https://arxiv.org/abs/2606.25605在构建 Agent 系统时，我们常假设“工具调用”和“结构化输出”是两个独立的能力模块。只要模型懂工具、能守格式，两者叠加应该没问题。但这篇论文揭示了一个反直觉的生产事故：当同时开启 Tool Calling 和 JSON Schema 约束时，许多开源模型会彻底停止调用工具，转而直接生成符合格式的“空壳”或“幻觉”回答。
这种现象被称为 Tool Suppression（工具抑制） 。它不是模型能力不足，而是解码层面的硬性约束导致了行为扭曲。对于正在落地 Agent 系统的工程师来说，这是一个必须警惕的隐形陷阱。
### 为什么会出现“工具消失”？
传统观点认为，Structured Output（结构化输出）只是对最终文本格式的约束，不影响推理过程。然而，现代推理引擎（如 vLLM, SGLang）为了实现严格的 JSON 合规，通常采用 Grammar-Constrained Decoding（基于语法的约束解码） 。
其核心机制是将 JSON Schema 编译为有限状态机（FSM），并在每个 token 生成步骤中应用词表掩码（Vocabulary Mask）。任何不符合当前语法状态的 token 都会被赋予 −∞-\infty 的 logit，从而被禁止采样。
关键 Insight 在于： 当模型需要输出工具调用（通常以 XML 标签或特定 JSON 字段开头）时，如果当前的 Schema 约束不允许这些特定的起始 token 出现，模型在解码层面上就“物理上”无法生成工具调用指令。
论文提出了 Constraint Priority Inversion (CPI, 约束优先级倒置) 假说：在多约束并存时，满足格式合规的硬性指标可能压倒执行动作的行为倾向。模型为了不被掩码“卡死”，选择了一条阻力最小的路径——直接生成符合 Schema 但无工具调用的响应。
### 实验证据：从现象到分类研究团队在多个开源模型家族（Qwen3, GPT-OSS, Nemotron 等）上进行了受控实验，对比了三种条件：
- T1 (Baseline): 仅开启工具，无格式约束。
- T2 (Joint Constraint): 同时开启工具和 JSON Schema。
- T3 (Schema Only): 仅开启格式约束，无工具。
实验结果令人震惊。在 T1 条件下，模型能正常调用工具；但在 T2 条件下， Tool Invocation Rate (TIR, 工具调用率) 显著下降，部分模型甚至出现完全抑制（SR=1）。
论文进一步将这种抑制行为细分为五类（TS-A 到 TS-E），揭示了模型的“求生策略”：
类别 名称 行为特征 风险等级 TS-A Empty Compliance 生成完全合规但字段为 null/default 的 JSON 低 TS-B Simulated Retrieval 不调用工具，直接编造看似来自外部检索的内容 中 TS-C Intent Without Action 明确表达需要搜索，但最终未执行调用 中高 TS-D Tool-Free Hallucination 既不调用也不承认信息缺失，直接生成无依据内容 高 TS-E Frozen Required Tool 即使强制设置 tool_choice="required" 仍无法调用 中其中， TS-B (模拟检索) 和 TS-D (无工具幻觉) 最具欺骗性。模型输出了流畅且格式正确的 JSON，下游系统解析成功，但内容完全是虚构的。这在生产环境中极难通过简单的格式校验发现。
### 工程启示与解决方案这篇论文的价值不仅在于发现问题，更在于提供了解决思路。既然问题源于解码层的 token 掩码冲突，最直接的修复方式不是微调模型（成本高、效果慢），而是改变推理流程。
论文提出了 Transparent Two-Pass Execution (透明两阶段执行) 策略：
- 第一阶段：解除 Schema 约束，让模型自由决定是否需要调用工具并执行。
- 第二阶段：将工具返回结果与原始问题结合，在严格的 JSON Schema 约束下生成最终响应。
这种方法将“动作决策”与“格式生成”解耦，避免了 Grammar Constraint 对工具调用 token 的误杀。实验表明，该策略能在不重新训练模型的情况下，恢复工具调用行为，同时保持结构化输出的可靠性。
### 局限与展望尽管两阶段执行有效，但它增加了推理延迟（需要两次 LLM 调用）。此外，论文主要关注了 JSON Schema 导致的语法约束问题，对于其他类型的约束（如长度限制、安全过滤）是否会产生类似的 CPI 效应，尚需进一步研究。
给工程师的建议：
- 不要盲目信任联合约束：在启用 Tool Calling + Structured Output 时，务必单独测试工具调用率，而不仅仅是检查最终输出的 JSON 格式。
- 警惕“完美”的幻觉：如果 Agent 返回了结构完美的数据，但内容过于泛化或疑似编造，很可能发生了 TS-B 类型的抑制。
- 考虑两阶段架构：对于关键任务，采用“先决策后格式化”的两阶段流水线，是规避解码层冲突的工程最佳实践。
## 📝 AI 点评点评时间：2026-06-26 03:24 ｜ reviewer: DeepSeek V4 Flash核心贡献: 原文针对生产环境中 Tool Calling 与 Structured Output 约束同时启用时开源 LLM 出现工具调用抑制（Tool Suppression）的现象，通过受控实验、推理堆栈追踪（grammar-based token masking）和工程缓解策略（Transparent Two-Pass Execution）进行了系统性实证研究，并提出了约束优先级倒置（CPI）假设作为行为解释。
亮点: 博文准确抓住了 Tool Suppression 的核心现象和 Grammar-Constrained Decoding 的机制，并用分类表（TS-A 到 TS-E）清晰展示了模型的不同“求生策略”，对工程启示的总结（如警惕联合约束、两阶段架构）也贴近实践，有助于读者快速理解论文的主要价值。
挑刺:
- 博文称“在 T2 ���件下，Tool Invocation Rate (TIR, 工具调用率) 显著下降，部分模型甚至出现完全抑制（SR=1）”，但原文表 7 显示所有开源模型在 T2 下 TIR 均为 0%、SR 均为 100%，不存在“部分模型”的差异。这一表述弱化了现象的普遍性和严重性。
- 博文将根因主要归为 Grammar-Constrained Decoding 导致的 token 掩码，但原文 Section 6.2 明确指出“the primary cause of missing tool calls under T2 is grammar-level token exclusion at the decoding layer”，并强调 CPI 只是行为假设而非已验证的内部机制。博文将 CPI 与 token 掩码并列，未突出 token 级排除是更具体、更根本的原因，可能导致读者误以为模型层面的优先级倒置是主因。
- 博文遗漏了原文中多个关键的工程验证细节：例如所有开源模型在框架（SGLang/vLLM）、schema 复杂度（简单/中等/生产级）、工具强制策略（optional/required）、微调（SFT/GRPO）等消融实验中均保持完全抑制，这些是论文鲁棒性的重要支撑，博文未提及，削弱了对现象稳定性的说服力。
总评: ⭐⭐⭐½ 博文准确传达了论文的核心发现和工程启示，但在现象普遍性和根因优先级的表述上存在偏差，且遗漏了关键消融实验证据，整体忠实度略低于完美。
