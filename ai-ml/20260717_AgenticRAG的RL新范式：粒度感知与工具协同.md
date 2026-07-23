# ⭐⭐⭐½ Agentic RAG 的 RL 新范式：粒度感知与工具协同

**日期**: 2026-07-17

---

论文 : GRASP: GRanularity-Aware Search Policy for Agentic RAG链接 : https://arxiv.org/abs/2607.10463Agentic RAG（智能体检索增强生成）正在从简单的“提示词工程”转向“策略学习”。这篇来自 UMass Amherst 和 Adobe Research 的论文提出了一种基于强化学习（Reinforcement Learning, RL）的新框架 GRASP，它让模型学会了像人类一样“先浏览、再精读、最后查证”的信息检索策略。对于正在构建复杂 Agent 系统的工程师来说，这提供了从 Prompting 到 Policy Learning 的关键思路。
### 现有方案的痛点：为什么静态 RAG 不够用？
传统的 RAG 是单步静态流程：检索器一次性召回固定数量的 Chunk（文本块），然后 LLM 生成回答。这种方式在多跳推理（Multi-hop Reasoning）中面临三大挑战：
- 信号单一：无法动态结合语义匹配（Semantic Similarity）和词法匹配（Lexical Matching）。
- 粒度失控：粗粒度的段落召回容易引入噪声，淹没关键证据，导致模型幻觉。
- 策略僵化：现有 Agentic RAG 多依赖 Prompting（如 IRCoT），缺乏对“何时检索、用什么工具、检索多少上下文”的自适应决策能力。
### 方法拆解：GRASP 的核心设计直觉GRASP 将 Agentic RAG 建模为有限视界的马尔可夫决策过程（MDP）。其核心 Insight 在于： 检索不仅是动作，更是需要学习的策略 。
1. 细粒度的工具空间设计GRASP 定义了三个原子动作：
- 语义搜索 (τs\tau_s​)：基于稠密向量，用于 broad exploration（广泛探索），解决词汇不匹配问题。
- 关键词搜索 (τk\tau_k​)：基于 BM25，用于 targeted lexical retrieval（针对性词法检索），精确锁定实体。
- 段落阅读 (τr\tau_r​)：将召回的句子级证据扩展为完整段落，用于 local verification（局部验证）。
这种“先搜句子、再读段落”的设计非常精妙。它强制模型先在细粒度上定位关键线索，避免一次性吞下大量无关上下文，从而保持 Context Window 的高信噪比。
2. 多目标奖励函数（Reward Design）
这是 GRASP 的灵魂。作者设计了联合奖励 R=RA+αRR+βRS+γRER = R_A + \alpha R_R + \beta R_S + \gamma R_E R A ​ + α R R ​ + β R S ​ + γ R E ​ ：
- 答案准确率 (RAR_A​)：Token-level F1，权重最高，确保最终任务完成。
- ** grounded reading (RRR_R​)**：鼓励模型读取包含黄金证据的段落，惩罚不必要的阅读。权重 α=0.7\alpha=0.70.7，引导模型学会“只读有用的”。
- 互补搜索 (RSR_S​)：仅当语义和关键词搜索都召回了黄金文档时才给分。权重 β=0.15\beta=0.150.15，强制模型利用互补信号，避免依赖单一检索器。
- 回合效率 (RER_E​)：奖励少步数完成，防止无限循环。权重 γ=0.15\gamma=0.150.15。
⚠️ 关键细节 ：辅助奖励总权重限制为 1.0，且仅在答案正确时给予效率奖励。这有效防止了“奖励黑客”（Reward Hacking），即模型为了刷分而忽略最终答案质量。
### 关键结果：RL 策略显著优于 Prompting实验在 HotpotQA、2WikiMultiHopQA 和 MuSiQue 上进行，基线包括单步检索、IRCoT (Prompting) 和 Search-R1 (RL)。
1. 检索召回率（Recall）
GRASP 在所有数据集上均实现了最高的检索召回率。在 HotpotQA 上，GRASP 的召回率达到 0.91 ，显著优于 IRCoT (0.76) 和 Search-R1 (0.74)。这表明学习到的策略能更可靠地找回多跳证据。
2. 问答性能（QA Metrics）
Method Retriever Granularity Policy Learning HotpotQA EM HotpotQA F1 Single-step (Hybrid) Hybrid Paragraph No 0.37 0.48 IRCoT Lexical Paragraph Prompting 0.24 0.36 Search-R1 (GRPO) Semantic Paragraph RL 0.45 0.56 GRASP Hybrid Sentence RL 0.53 0.66- GRASP 在 HotpotQA 上的 EM 达到 0.53，比 Search-R1 高出 8 个百分点。
- 消融实验显示，移除段落阅读工具 (τr\tau_r​) 导致 EM 下降 0.122，移除语义搜索 (τs\tau_s​) 下降 0.072。这证明了“细粒度定位 + 粗粒度验证”的必要性。
3. 涌现的人类行为模式定性分析发现，GRASP 学会了类似人类信息觅食（Information Foraging）的行为：先用语义搜索浏览大意，再用关键词搜索锁定实体，最后阅读段落验证事实。这种策略在避免“过早承诺错误”方面表现优异。
### 工程启示：如何落地？
- 从 Prompting 转向 RL：对于复杂的多跳任务，精心设计的 Prompt 可能不如一个经过 RL 微调的策略模型稳定。GRASP 展示了使用 GRPO（Group-Relative Policy Optimization）训练小型模型（3B 参数）的可行性。
- 工具原子化：不要只给 Agent 一个“搜索”按钮。将检索拆解为“语义搜”、“关键词搜”、“展开上下文”等原子操作，能让模型学会更精细的控制流。
- 奖励函数的平衡艺术：GRASP 的奖励设计极具参考价值。通过限制辅助奖励的权重，并绑定最终答案准确率，可以有效防止 Agent 陷入无效的工具调用循环。
### 局限与展望GRASP 目前依赖黄金标注（Gold Annotations）来计算 grounded reading 和互补搜索奖励，这在真实场景中难以获取。此外，模型仍存在保守终止或检索不全的问题。未来工作将探索弱监督信号以及动态粒度决策。但对于希望深入理解 Agentic RAG 策略学习的工程师而言，GRASP 提供了一个清晰且可复现的基线框架。
## 📝 AI 点评点评时间：2026-07-17 16:08 ｜ reviewer: DeepSeek V4 Flash核心贡献: 原文针对 Agentic RAG 中如何自适应地协调互补检索工具（语义搜索、关键词搜索）并控制上下文粒度（句子级检索 vs. 段落级扩展）的挑战，提出基于 GRPO 强化学习的框架 GRASP，通过联合奖励（答案准确率、有根据阅读、互补搜索、回合效率）训练策略，使模型在多步推理中动态选择检索信号和粒度，提升多跳问答的检索召回与生成质量。
亮点: 博文准确提炼了原文的核心设计，包括细粒度的工具空间（语义搜索、关键词搜索、段落阅读）和多目标奖励函数（权重分配及防 reward hacking 机制）。博文突出了原文最有工程价值的点：将检索从静态 pipeline 升级为可学习的策略，并通过消融实验验证了“句子级定位 + 段落级验证”的必要性，以及 RL 训练相比 Prompting 的显著优势。对涌现的类人类信息觅食行为（先语义浏览、再阅读验证、最后关键词查证）的概括基本到位。
挑刺:
- 定性分析中工具使用顺序描述错误。博文称“先用语义搜索浏览大意，再用关键词搜索锁定实体，最后阅读段落验证事实”，而原文明确顺序是“The agent often begins with semantic search τs … then chooses a paragraph to read using τr to verify … These bridge entities are subsequently used in keyword search τk”（原文第5.2节），即先语义搜索，再阅读段落，最后关键词搜索。博文将关键词搜索与阅读段落顺序颠倒。
- 消融实验部分未说明关键约束。博文直接引用“移除段落阅读工具导致 EM 下降 0.122”等数字，但原文明确指出消融实验是在“a randomly sampled subset of 5,500 questions”上训练的（原文第5.3节），而主结果是完整 HotpotQA 训练集的结果（EM 0.53 vs 消融基线 0.510）。博文未提及这一子集条件，可能使读者误以为消融结果与主结果在同一规模下可比。
- 召回率数字引用存在微小偏差。博文称“在 HotpotQA 上，GRASP 的召回率达到 0.91”，但原文 Table 1 中 GRASP 在 HotpotQA 上的 Recall 为 0.90（原文第5.1节表1）。虽然误差不大，但属于不精确引用。
总评: ⭐⭐⭐½ 博文整体忠实地传达了论文的核心贡献与关键结果，结构清晰，但存在两处事实性偏差（工具顺序错误、消融上下文缺失）和一处数字不精确，瑕不掩瑜，略高于默认档。
