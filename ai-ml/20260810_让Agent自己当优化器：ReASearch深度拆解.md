# ⭐⭐⭐½ 让 Agent 自己当优化器：ReASearch 深度拆解

**日期**: 2026-08-10

---

论文 : The Optimizer Is the Agent: Reasoning-Driven Search across Prompts, Programs, and ML Workflows链接 : https://arxiv.org/abs/2608.06714现在的 AI 工程圈有个共识：LLM 适合做“执行者”，但不适合做“决策者”。
我们习惯用外部算法（如贝叶斯优化、遗传算法）来掌控搜索策略，让 LLM 仅仅负责生成候选方案。这种“外脑控制+内脑执行”的架构虽然稳定，却割裂了语义理解与搜索逻辑。
ReASearch 反其道而行之：它把整个优化过程封装成工具，让 Agent 自己决定何时探索、何时验证、何时回退。
结果令人惊讶：在 14 个任务中，这个“去中心化”的 Agent 不仅击败了专用优化器，还在部分数学问题上超越了人类已知最优解。
### 痛点：外部控制器不懂“语义”
传统的 Prompt 或代码优化系统，通常依赖明确的外部循环（Outer-loop）。
比如进化算法决定保留哪个候选者，Bandit 算法决定预算分配。LLM 只是被动的变异源。
这种设计的致命伤在于：外部算法无法理解代码或文本的深层结构。它不知道为什么某个 Prompt 在特定边缘案例上失败，也不知道某段代码的逻辑漏洞在哪里。
ReASearch 的核心 Insight 是： 搜索策略本身也可以被内化到 Agent 的推理过程中。
### 方法拆解：工具即策略ReASearch 没有硬编码任何搜索逻辑（如“每 5 步评估一次”）。
它提供了一个极简的代码 Agent 框架，核心组件只有三个：
- 领域专用工具：包括代码执行、模型评估、文件编辑等。
- 持久化记忆：一个 lessons.md 文件，记录成功模式与失败教训。
- Python 执行环境：这是最关键的设计。Agent 不只是生成文本，而是编写分析脚本来诊断问题。
关键直觉 ：通过暴露 python_exec 工具，Agent 从“纯文本推理者”变成了“计算推理者”。它可以统计日志、计算方差、甚至进行数学推导。
以 Prompt 优化为例，Agent 不会盲目地批量测试新 Prompt。它会先在小样本上验证，分析得分波动，判断是真正的能力提升还是偶然匹配。如果发现过拟合迹象，它会自动调整策略。这些行为不是代码写死的，而是 Agent 根据历史反馈“想”出来的。
### 实验结果：通用框架 vs 专用算法论文在三个领域进行了对比测试，数据非常硬核。
1. Prompt 优化（对比 GEPA）
任务 基线 GEPA (SOTA) ReASearch AIME 2025 46.00% 50.67% 52.00% GSM8K 81.20% 82.11% 83.40% HotpotQA 63.00% 65.80% 67.60% Terminal-Bench 35.56% 42.22% 53.33%ReASearch 在所有任务上均胜出，尤其在 Terminal-Bench 上提升了超过 10 个百分点。
2. 程序进化（对比 AdaEvolve）
在 Circle Packing（圆填充）问题中，ReASearch 发现了超越人类已知最优解的方案。
例如在 n=32n=32 32 时，人类最佳记录为 2.939，而 ReASearch (Sonnet 4.6) 达到了 2.940 。
更惊人的是 ARC-AGI-2 视觉推理任务：ReASearch 的测试准确率比 AdaEvolve 高出 4 倍。这是因为 Agent 会先通过 Python 分析训练样本的特征，再编写代码，而不是盲目生成。
3. ML 工作流优化（对比 Claude Code）
任务 Claude Code ReASearch IMG-100 (Accuracy) 78.59% 83.99% Atari Q*bert (Reward) 1250 4500 Crypto Kaggle Rank 29 6在 IMG-100 任务中，ReASearch 通过 Python 脚本计算训练时间，发现学习率调度不匹配，从而一次性提升 14% 的准确率。而 Claude Code 浪费了数十次实验才偶然发现类似问题。
### 工程启示：让 Agent “思考”而非“试错”
这篇论文对实际开发的指导意义巨大：
- 赋予 Agent 计算能力：不要只让 LLM 输出文本。提供 python_exec 等工具，让它能运行代码、分析数据、验证假设。
- 记忆至关重要：简单的 lessons.md 能让 Agent 避免重复犯错，并在长周期任务中积累经验。
- 去中心化控制：尝试减少硬编码的搜索逻辑。让 Agent 根据实时反馈自主决定下一步动作，往往能涌现出更高效的策略（如自动回退、双重验证）。
### 局限与展望ReASearch 目前主要依赖高性能模型（如 GPT-5, Claude Sonnet 4.6），成本较高。
此外，Agent 的推理轨迹虽然高效，但缺乏可解释性保障。在关键业务场景中，如何确保 Agent 不会陷入“看似合理实则错误”的逻辑陷阱，仍是待解难题。
## 📝 AI 点评点评时间：2026-08-10 11:07 ｜ reviewer: DeepSeek V4 Flash核心贡献:
提出 ReASearch 框架，将提示词、程序和 ML 工作流优化统一建模为推理驱动搜索问题，通过把整个优化流程封装成工具让 LLM agent 自主决定探索、验证、回退等策略，从而内化传统上由外部控制器执行的搜索逻辑。
亮点:
- 准确捕捉了核心设计哲学——“工具即策略”，并强调 python_exec 使 agent 从文本推理者变成计算推理者，这一 insight 是原文最具工程价值的创新点。
- 突出了持久化记忆（lessons.md）和涌现的优化行为（自动验证、回退、自适应探索），这些是原文区别于传统外循环方法的关键机制。
- 在实验结果部分选取了最具代表性的提升（Terminal‑Bench +10pp、ARC‑AGI‑2 四倍、Circle Packing 超人类最优），数字引用准确，能够有效传达 ReASearch 的竞争力。
挑刺:
-遗漏多个重要任务结果，削弱全面性博文在程序进化部分只提及 Circle Packing 和 ARC‑AGI‑2，但原文 Table 3（Heilbronn）、Table 4（TXN/EPLB）同样是重要对比，且 ReASearch 在这些任务上也显著优于 AdaEvolve（例如 Heilbronn n=14 从 0.00299 提升到 0.02429）。ML 工作流部分只列出 IMG‑100、Atari、Crypto，却未提 NanoGPT 和 MuJoCo（原文 Table 6），其中 MuJoCo 上 ReASearch 5267 vs Claude Code 3986 也是明显优势。这些遗漏使读者无法全面评估 ReASearch 的通用性。
-对可解释性的表述与原文有偏差博文在“局限与展望”中说“Agent 的推理轨迹虽然高效，但缺乏可解释性保障”。然而原文在 §3、附录 B 和附录 I 中大量展示了 agent 的 lessons.md、具体推理步骤（如 HotpotQA 的错误分类、Heilbronn 的对称性发现），并明确指出“None of this process is hardcoded; it emerges from the guiding instruction”。原文强调轨迹是可分析和可复现的，并非黑盒。博文的说法容易误导读者认为 agent 行为不可理解。
-未说明开源骨干实验结果原文 Appendix D 展示了 ReASearch 在开源模型 GLM‑5、Kimi‑2.5 上的表现，虽然略弱于 Claude/GPT，但仍显著优于基线，这证明了框架不依赖特定闭源模型。博文仅提“主要依赖高性能模型（如 GPT‑5, Claude Sonnet 4.6），成本较高”，忽略了开源适配的可能性，可能过度简化了实用化门槛。
总评:
⭐⭐⭐½ 博文准确传达了 ReASearch 的核心思想、关键机制和代表性成果，但遗漏了多个重要任务的结果，并对可解释性做出了有偏差的表述，降低了全面性和严谨度。
