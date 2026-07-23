# Externalization in LLM Agents — Memory/Skills/Protocols/Harness 统一综述

**日期**: 2026-04-16

---

# Externalization in LLM Agents — Memory/Skills/Protocols/Harness 统一综述最近，上海交大、中山大学、CMU 以及 OPPO 的研究团队发布了一篇重量级的理论综述（arXiv: 2604.08224）。这篇文章很有意思，它没有去卷模型参数，而是用一条清晰的主线串起了过去三年 LLM Agent 的演进路径： 外化（Externalization） 。
简单来说，现在的趋势不再是试图让模型“变聪明”去硬扛所有认知负担，而是把记忆、技能、协议和治理逻辑迁移到运行时（Runtime）外部模块。
## 核心逻辑：从 Weights 到 Harness论文把 Agent 的进化史分成了三个阶段，大家可以对照一下自己现在的开发重心：
时期 主导力量 关键手段 Weights 时代 (Pre-2023) 模型参数 靠训练、微调或 RLHF 来硬灌知识 Context 时代 (2023-2024) 输入 Prompt 靠 Prompt Engineering 或 RAG 来临时喂数据 Harness 时代 (2024-2026) 运行时环境 靠记忆存储、工具集、协议定义和沙箱编排现在的核心哲学是： 把难以内部解决的认知负担，转化为模型能可靠处理的表征 。
## 四柱框架：Agent 架构的“审计透镜”
论文提出了一个极其好用的 Memory / Skills / Protocols / Harness 四柱分类学 。这不仅仅是理论，更是可以直接拿来用的审计 Checklist。
### 1. Memory（记忆）
记忆不是单纯的“存量”，而是跨时间的各种状态。论文将其细分为四个维度：
- Working Context（工作上下文）：当前的活跃状态。
- Episodic Experience（情景经验）：历次运行的记录。
- Semantic Knowledge（语义知识）：领域事实与约定。
- Personalized Memory（个性化记忆）：用户偏好与习惯。
我的观点 ：记忆质量的问题本质上是**检索（Retrieval）**问题，而不是容量问题。重点在于“可识读性（Legibility）”——如果半年后的模型读到这条记忆，它能不能明白当时的决策逻辑？
### 2. Skills（技能）
技能不再是即兴的生成（Generation），而是组件的组合（Composition）。一个完整的 Skill 应该包含三个组件：
- 操作程序（Operational Procedure）：任务的步骤分解。
- 决策启发式（Decision Heuristics）：分支点的经验规则。
- 规范约束（Normative Constraints）：什么情况下不该用这个技能。
### 3. Protocols（协议）
协议负责把“临时对话（Ad hoc）”转变为“结构化契约（Structured）”。这对于多 Agent 协作和复杂工作流的稳定性至关重要。
### 4. Harness（运行时外壳）
Harness 是承载前三者的统一层。它提供了控制流、沙箱隔离、人类监督（Human Oversight）以及上下文预算管理（Context Budget Management）。
## 总结与启发这篇文章给我们的架构设计指明了方向：如果你觉得 Agent 逻辑混乱、反复出错，可能不是模型不够强，而是你的“外化”做得不够彻底。
行动建议：
- 检查技能规范：你的 Skill 文档里有没有写“禁止触发场景”？如果没有，赶紧补上约束。
- 分类管理记忆：别把所有东西都塞进一个文件，按工作、情景、语义和个性化进行分层。
- 强化 Harness 审计：重点关注权限隔离（Sandboxing）和上下文预算管理，这是规模化落地的瓶颈。
来源: 42.55 Externalization in LLM Agents — Memory/Skills/Protocols/Harness 统一综述
