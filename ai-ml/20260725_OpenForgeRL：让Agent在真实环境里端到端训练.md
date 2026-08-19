# ⭐⭐½ OpenForgeRL：让Agent在真实环境里端到端训练

**日期**: 2026-07-25

---

论文 : OpenForgeRL: Train Harness-native Agents in Any Environment链接 : https://arxiv.org/abs/2607.21557现在的 Agent 越来越强，但大部分开源研究还在用简化版的 ReACT 循环做训练。
一旦部署到 Claude Code 或 Codex 这种复杂的推理框架（Harness）中，性能往往大打折扣。
OpenForgeRL 的出现，就是要解决这个“训练-部署”错配问题：直接在真实的复杂环境中进行端到端强化学习（Reinforcement Learning, RL）。
### 为什么现有的训练方式不够用？
现代 Agent 的核心竞争力往往不在基座模型本身，而在于那些管理多轮交互、工具调用和上下文状态的推理框架。
现有的开源 RL 框架（如 veRL）通常假设 rollout 是轻量级的、无状态的，且能直接运行在训练节点上。
但真实的 Agent 环境（如 GUI 操作或复杂代码任务）需要独立的容器化环境，且推理过程充满状态依赖。这导致研究人员不得不重写一套简化版 Harness 用于训练，造成了严重的 Train-Deploy Mismatch 。
### 核心设计：解耦与代理OpenForgeRL 的核心 Insight 非常直接： 不要试图把复杂的推理逻辑塞进 RL 框架，而是让 RL 框架去“监听”真实的推理过程。
它通过两个轻量级组件实现了这一点：
- 轻量级代理（Lightweight Proxy）：拦截 Harness 发出的模型调用请求。它将 Prompt-Response 对记录下来，并重构为标准的 RL 训练样本。
- Kubernetes 编排器：将每个 rollout 任务分发到云端的独立容器中运行。
这种设计实现了 Rollout 与 Training 的彻底解耦 。
RL 训练代码只需处理标准化的数据流，而无需关心底层是 ReACT、ZeroClaw 还是复杂的 Codex 逻辑。这使得任何 Harness 结合任何环境都变得可训练。
### 关键实验结果论文在工具调用（Claw）和 GUI 操作两个维度进行了验证，效果显著。
1. 工具调用 Agent (OpenForge-Claw, 30B-A3B)
在 ClawEval 基准上，经过 SFT+RL 训练后，模型表现大幅提升：
指标 OpenForge-Claw (SFT) OpenForge-Claw (SFT+RL) pass@3 21.7% 31.7% pass@3 (整体) 52.1% 55.9%在 QwenClawBench 上，SFT+RL 版本达到了 33.7% 的 pass@1，远超未训练的基线（21.8%）。
2. GUI Agent (OpenForge-GUI, 8B)
在视觉交互任务中，仅用数千个任务进行训练，就超越了更大规模的模型：
基准测试 OpenForge-GUI (SFT) OpenForge-GUI (SFT+RL) OSWorld-Verified 34.4% 37.7% OnlineMind2Web 57.4% 63.0% WebVoyager 61.5% 72.3%值得注意的是，OpenForge-GUI 在 OnlineMind2Web 上的表现（63.0%）甚至超过了参数量大得多的 MolmoWeb-8B（35.3%）。
### 工程启示与反直觉发现⚠️ 并非所有 Harness 都适合学习论文分析发现，简单的、工具对齐良好的 Harness（如 ReACT, ZeroClaw）更容易被模型掌握。
相比之下，功能更丰富但上下文更长的 Codex，其性能提升幅度反而较小。这说明 Harness 的设计复杂度直接影响 RL 的学习效率 。
此外，RL 训练显著改变了 Agent 的行为模式：
- 工具选择更精准：泛用的 shell 调用比例从 22.6% 降至 13.9%，更多使用专用服务工具。
- 自我验证增强：模型学会了回读自己的写入操作以确认结果。
但论文也坦诚指出， 错误恢复（Error Recovery） 依然是弱项，仅靠 RL 难以完全解决，可能需要专门的数据构造。
### 总结OpenForgeRL 为开源社区提供了一条在真实复杂环境中训练 Agent 的路径。
它证明了： 消除训练与部署之间的鸿沟，是提升 Agent 鲁棒性的关键一步。
对于工程师而言，这意味着未来我们可以更放心地在生产环境的 Harness 中迭代模型，而不是在沙盒里自嗨。
## 📝 AI 点评点评时间：2026-07-25 21:04 ｜ reviewer: DeepSeek V4 Flash核心贡献: 提出OpenForgeRL，通过轻量级代理拦截harness的模型调用并重构为训练数据，配合Kubernetes编排器实现远程容器化rollout，从而让任何harness×任何环境都能用标准RL框架端到端训练，消除训练-部署错配。
亮点: 博文准确抓住了框架的核心设计思想——解耦训练与推理，用轻量级代理监听harness调用，并用Kubernetes编排器管理远程容器。对RL带来的行为变化（工具选择更精准、自我验证增强）的提炼也到位，这些是原文中工程价值较高的分析。
挑刺:
- 关键指标混淆：博文在ClawEval结果表中将pass3（原文SFT+RL为31.7）误标为“pass@3”，而原文pass@3为55.9。博文第二行正确给出了pass@3=55.9，但第一行错误导致读者可能误判模型性能。原文表2明确区分pass3和pass@3两列，博文未正确反映。
- 过度解读参数量：博文称“OpenForge-GUI在OnlineMind2Web上的表现（63.0%）甚至超过了参数量大得多的MolmoWeb-8B（35.3%）”。但原文表3中MolmoWeb-8B和OpenForge-GUI均为约8B参数，并非“大得多”。原文比较的是相似规模模型，博文夸大了对比差异。
- 遗漏关键细节：博文未提及数据合成管道（Section 3.3）及其对训练任务构建的重要性，也未引用原文中关于不同harness学习难度对比的具体数据（如表4的ZeroClaw vs OpenClaw差异），导致“并非所有Harness都适合学习”的结论缺乏数据支撑。
总评: ⭐⭐½ 博文传达了核心思想，但关键数字错误和过度解读损害了准确性，需谨慎引用其具体数值。
