# ⭐⭐⭐ StepPO：让 Agent 强化学习回归“步骤”本质

**日期**: 2026-06-16

---

论文 : StepPO: Step-Aligned Policy Optimization for Agentic Reinforcement Learning链接 : https://arxiv.org/abs/2604.18401训练 LLM Agent 时，我们常陷入一个误区：用处理文本生成的逻辑去优化决策过程。这篇来自中科大的论文指出了这个“粒度错配”问题，并提出了 StepPO 方案。它不改变模型架构，而是重构了强化学习（RL）的 MDP 建模和信用分配机制，让训练更贴合 Agent 的实际交互逻辑。
### 为什么 Token 级优化不适合 Agent？
现有的 RLHF 或 GRPO 算法大多基于“Token 中心”范式。在这种范式下，模型每生成一个 token 就被视为一次状态转移。
但在 Agentic RL 中，Agent 与环境的交互是以“步骤（Step）”为单位的：观察环境 -> 生成完整动作（如调用工具）-> 接收反馈 -> 进入下一步。
⚠️ 核心痛点 ：Token 级的信用分配过于局部，无法捕捉完整动作对后续状态的影响；而轨迹级（Trajectory-level）分配又过于粗糙，难以区分长序列中哪些中间步骤是关键决策。这种“粒度错配”导致优化信号与 Agent 的实际决策逻辑脱节。
### StepPO 的核心设计直觉StepPO 的解决思路很直接：将 MDP 从 Token 级重构为 Step 级。其核心创新在于两个对齐：
-Step 级 MDP 建模：
状态 sts_t​ 定义为当前步骤前的交互历史，动作 ata_t​ 定义为完整的响应（包含推理和工具调用）。只有当完整动作执行完毕并收到环境反馈后，才发生状态转移。这消除了 Token 级建模中因子词切分带来的噪声。
-Step 级信用分配与重要性采样：
优势估计：使用 Critic 模型在步骤边界估计价值 V(st)V(s_t)​)，并通过 GAE 计算步骤级的 TD 残差 δt\delta_t​。这避免了将延迟奖励分散到无关的表面 Token 上。
- 几何平均重要性采样：由于一个步骤包含多个 Token，直接相乘会导致长动作的比率极端化。StepPO 采用 Token 比率的几何平均作为步骤级的重要性采样权重 wt(θ)w_t(\theta)​(θ)。这种长度归一化设计确保了不同长度的动作在更新时具有可比性。
### 实验结果：全面超越基线论文在四个典型 Agent 场景下进行了评估，使用 Qwen3-1.7B 和 Qwen3-4B-Instruct 作为基座模型。StepPO 在所有指标上均优于 PPO、GRPO、GiGPO 等主流方法。
关键数据对比（Qwen3-4B-Instruct）：
任务 指标 PPO GRPO GiGPO StepPO HotpotQA (多跳问答) Acc 56.75 56.61 58.14 63.78 ALFWorld (文本世界) Seen Win Rate 76.43 81.43 88.57 92.14 WebShop (网购) Score 70.18 65.83 67.13 77.52 RealResearchQuery F1@all 0.303 0.294 0.306 0.327反直觉发现：
StepPO 在学术文献搜索任务中，使用的平均响应 Token 数最少（2646.35），但 F1@all 最高。这说明它并非通过“啰嗦”的推理来提升性能，而是学会了更高效的“搜索-扩展”策略平衡。相比之下，GiGPO 虽然搜索次数多，但覆盖效率更低。
此外，在折扣因子 γ\gamma 从 0.99 降至 0.95 时，Token 级 GAE 的 WebShop 分数下降了 13.09% ，而 Step 级 GAE 仅下降 5.53% 。这证明步骤级信用分配能更好地保留长程延迟奖励信号，对折扣参数更鲁棒。
### 工程启示与落地建议对于正在构建 Agent 训练流水线的工程师，StepPO 提供了以下实践指导：
- 数据结构重构：不要将交互轨迹存储为扁平的 Token 序列。应建立“步骤原生（Step-Native）”的数据记录，明确标记每个步骤的状态、动作和奖励边界。这能避免重分词漂移（Retokenization Drift），确保训练与推理的一致性。
- 异步训练支持：由于 Agent rollout 延迟差异大，StepPO 天然适合异步训练架构。通过网关统一异构 Agent 的交互痕迹，结合数据池管理，可以实现高效的离线/在线混合训练。
- 计算效率优化：StepPO 的 Critic 仅在步骤边界进行价值估计，而非每个 Token，这在一定程度上减少了监督信号的冗余。配合前缀树合并等技术，可显著降低长上下文训练的显存压力。
### 局限与展望尽管 StepPO 在多个基准上表现优异，但其依赖明确的“步骤”边界定义。对于非结构化或连续控制场景，如何界定“一步”仍具挑战。此外，论文主要基于 Qwen3 系列模型，在其他架构（如 MoE）上的泛化性仍需验证。
总体而言，StepPO 提醒我们：在 Agent 时代，RL 的优化单元应当从“词元”回归到“决策”。这种范式转变不仅提升了性能，更让训练过程更符合人类对 Agent 行为的直觉理解。
## 📝 AI 点评点评时间：2026-06-16 10:07 ｜ reviewer: DeepSeek V4 Flash我们被要求对一篇技术博文进行点评，基于原始论文（arxiv 2604.18401）和该博文。博文是由Qwen3.6-27B自动生成的，需要我们从几个维度分析：核心贡献、亮点、挑刺、总评。评分标准从1星到5星，大多数博文默认3星（准确反映论文）。需要严格对照原文和博文，指出遗漏、过度解读、术语错位等。博文内容已经给出，需要仔细阅读并对比原文。
首先，理解原文的核心贡献：原文提出StepPO，一种步骤中心（step-centric）的强化学习范式，用于训练LLM智能体。它解决了token级优化与step级决策之间的粒度不匹配问题。核心方法是将agentic RL重新表述为step-level MDP，包括step-level credit assignment（使用step-level GAE）和step-level importance sampling（几何平均）。实验在多个基准上取得一致改进。
博文标题：StepPO：让 Agent 强化学习回归“步骤”本质。博文内容概括了问题、核心设计、实验结果和工程启示。看起来比较忠实，但需要检查细节。
我们按照要求输出四个部分：核心贡献、亮点、挑刺、总评。
核心贡献：以原文为准，1-2句提炼。原文：提出StepPO，一种step-centric范式，通过step-level MDP和step-level credit assignment来解决token级优化与step级决策的粒度不匹配问题。博文提到了“粒度错配”和“重构MDP和信用分配机制”，但博文的核心贡献描述可能更简略。我们需要基于原文给出准确的核心贡献。
亮点：博文相对于原文的提炼/取舍是否到位？原文有工程价值或方法新意的点。博文提到了“几何平均重要性采样”、“Step级GAE对折扣因子鲁棒性”、“数据重构和异步训练”等，这些是原文的亮点。博文是否准确传达了？例如，博文强调了“反直觉发现”：StepPO使用更少token但F1更高，这确实是原文Table 3的内容。博文还提到了折扣因子实验，也是原文Table 4。博文也提到了系统层面的“步骤原生数据表示”和“异步训练”，这些是原文4.4节的内容。博文整体覆盖了核心方法和关键结果。
挑刺：需要对比原文与博文，指出博文遗漏的关键约束/数字/条件、过度解读、术语错位、引用偏差等。每条必须引用原文或博文的具体片段或数据做依据。
仔细检查博文：
-博文开头：“训练 LLM Agent 时，我们常陷入一个误区：用处理文本生成的逻辑去优化决策过程。” 原文中确实指出了token-centric paradigm的粒度不匹配。但博文表述为“误区”，原文没有用这个词，但意思一致，不算大问题。
-博文：“现有的 RLHF 或 GRPO 算法大多基于“Token 中心”范式。” 原文也这么说，没问题。
-博文：“在这种范式下，模型每生成一个 token 就被视为一次状态转移。” 原文token-level MDP：每个token是一个action，每个前缀是一个state，转移是确定性的。所以正确。
-博文：“但在 Agentic RL 中，Agent 与环境的交互是以“步骤（Step）”为单位的：观察环境 -> 生成完整动作（如调用工具）-> 接收反馈 -> 进入下一步。” 正确。
-博文：“核心痛点：Token 级的信用分配过于局部，无法捕捉完整动作对后续状态的影响；而轨迹级（Trajectory-level）分配又过于粗糙，难以区分长序列中哪些中间��骤是关键决策。” 这几乎是原文的 paraphrase。
-博文：“StepPO 的解决思路很直接：将 MDP 从 Token 级重构为 Step 级。其核心创新在于两个对齐：” 然后列举了Step-level MDP建模和Step-level credit assignment & importance sampling。博文对几何平均重要性采样的描述：“由于一个步骤包含多个 Token，直接相乘会导致长动作的比率极端化。StepPO 采用 Token 比率的几何平均作为步骤级的重要性采样权重 w_t(θ)。这种长度归一化设计确保了不同长度的动作在更新时具有可比性。” 这准确反映了原文公式(7)和描述。
-博文实验结果表格：使用Qwen3-4B-Instruct的结果，但表格中PPO, GRPO, GiGPO, StepPO的数据。我们对照原文Table 2：Qwen3-4B-Instruct部分，HotpotQA: StepPO 63.78, PPO 56.75, GRPO 56.61, GiGPO 58.14? 原文Table 2中Qwen3-4B-Instruct的HotpotQA: PPO 56.75, GRPO 56.61, GiGPO 58.14? 等一下，原文Table 2中Qwen3-4B-Instruct的HotpotQA：StepPO 63.78, PPO 56.75, Reinforce++ 55.94, GRPO 56.61, RLOO 56.31, GSPO 57.08, GiGPO 58.14? 原文中GiGPO那一行是Step-level MDP和Trajectory-level credit assignment，GiGPO在HotpotQA上Qwen3-4B是58.14吗？重新看原文Table 2：Qwen3-4B-Instruct部分，GiGPO一行：HotpotQA 58.14? 原文显示：GiGPO MDP Step, Credit Ass. Traj., HotpotQA 58.14? 但原文表格中GiGPO在HotpotQA的数值是58.14？等一下，我仔细看原文Table 2：
原文Table 2：
Qwen3-4B-Instruct-2507- ReAct – 37.45 … (HotpotQA Acc)
- PPO Token Token 56.75- Reinforce++ Token Token 55.94- GRPO Token Traj. 56.61- RLOO Token Traj. 56.31- GSPO Token Traj. 57.08- GiGPO Step Traj. 58.14- StepPO Step Step 63.78所以博文表格中GiGPO是58.14，正确。ALFWorld Seen: PPO 76.43, GRPO 81.43, GiGPO 88.57, StepPO 92.14，匹配。WebShop Score: PPO 70.18, GRPO 65.83, GiGPO 67.13, StepPO 77.52。RealResearchQuery F1@all: PPO 0.303, GRPO 0.294, GiGPO 0.306, StepPO 0.327。博文表格数据准确。
-博文“反直觉发现”：StepPO在学术文献搜索任务中，使用的平均响应Token数最少（2646.35），但F1@all最高。原文Table 3：StepPO Res. Tokens 2646.35，F1@all 0.314。PPO 2719.78, 0.284；GRPO 2951.57, 0.294；GiGPO 2814.79, 0.306。所以博文准确。
-博文“在折扣因子 γ 从 0.99 降至 0.95 时，Token 级 GAE 的 WebShop 分数下降了 13.09%，而 Step 级 GAE 仅下降 5.53%。” 原文Table 4：Token-level GAE: γ=0.99 Score 72.12, γ=0.95 Score 62.68, relative change -13.09%; Step-level GAE: γ=0.99 77.52, γ=0.95 73.23, relative change -5.53%。准确。
-博文工程启示：“数据结构重构”、“异步训练支持”、“计算效率优化”。这些对应原文4.4节。博文提到“不要将交互轨迹存储为扁平的 Token 序列。应建立“步骤原生（Step-Native）”的数据记录，明确标记每个步骤的状态、动作和奖励边界。这能避免重分词漂移（Retokenization Drift），确保训练与推理的一致性。” 原文确实讨论了retokenization drift和step-native representation。博文提到“Critic 仅在步骤边界进行价值估计，而非每个 Token，这在一定程度上减少了监督信号的冗余。” 原文4.4节提到“StepPO estimates values only at step boundaries rather than all generated tokens, making supervision more compact.” 所以准确。
-博文“局限与展望”：提到依赖明确的步骤边界定义，对于非结构化或连续控制场景如何界定“一步”仍具挑战；主要基于Qwen3系列模型，在其他架构上泛化性仍需验证。原文中是否有提到？原文主要实验使用Qwen3，但方法不依赖模型架构。原文没有明确讨论局限性，但博文提出的这两点合理，是常见的局限性。不过，博文是否过度解读了“局限”？原文没有专门讨论局限，博文自己添加了，但这是合理的总结，没有与原文冲突。
挑刺需要指出具体遗漏或错误。检查博文是否有遗漏的关键约束/数字/条件。
-博文没有提到原文中的“step-level MDP”具体定义中的状态和动作表示：状态是交互历史（包含之前步骤），动作是完整响应。博文提到“状态 s_t 定义为当前步骤前的交互历史，动作 a_t 定义为完整的响应（包含推理和工具调用）。” 正确。
-博文没有提到原文中关于“retokenization drift”的详细数学描述（公式2），但这不是必须的。
-博文没有提到原文中的“token-space consistency”概念，但博文提到了“重分词漂移”，可以。
-博文没有提到原文中“step-level importance sampling”的几何平均公式（7），但博文用文字描述了。
-博文在实验结果表格中只列出了PPO, GRPO, GiGPO, StepPO，省略了Reinforce++, RLOO, GSPO等。原文Table 2包含了这些。但博文选择只展示部分基线，这不算严重遗漏，因为博文是概括性的。
-博文没有提到原文的“Ablation Study”具体结果（图5），但博文提到了“反直觉发现”和折扣因子实验，但没有提到ablation。不过博文已经涵盖了核心结果，遗漏ablation不算严重，因为博文不是完整复现。
-博文没有提到原文的“Training Dynamics Analysis”（图6）和“Step-Wise Difficulty Analysis”（图7）和“Tool-Use Behavior Analysis”（Table 3已部分引用）。这些细节可能被省略，但博文选择了最突出的反直觉发现和鲁棒性实验。
-博文没有提到原文的“Case Study”（图8）和“A Research Path”部分（Agent-R1到Claw-R1）。博文主要聚焦方法核心，省略了这些，可以接受。
-博文在“工程启示与落地建议”中提到了“异步训练支持”，原文4.4节有讨论，但博文说“StepPO 天然适合异步训练架构”，原文确实描述了异步训练设计，但并非StepPO特有，而是系统设计。不过原文明确说“StepPO instead benefits from a decoupled design…”，所以博文表述准确。
-博文说“StepPO 的 Critic 仅在步骤边界进行价值估计，而非每个 Token，这在一定程度上减少了监督信号的冗余。” 原文4.4节说“StepPO estimates values only at step boundaries rather than all generated tokens, making supervision more compact.” 所以准确。
-博文“局限与展望”提到“对于非结构化或连续控制场景，如何界定“一步”仍具挑战。” 原文没有讨论这个局限性，但这是合理的推测。不过，这可能算是“过度解读”吗？原文主要针对有明确步骤边界的agent交互（工具调用、环境步骤）。博文指出非结构化场景的挑战，是合理的延伸，没有与原文矛盾。
-博文提到“论文主要基于 Qwen3 系列模型，在其他架构（如 MoE）上的泛化性仍需验证。” 原文实验确实只用了Qwen3，但方法不依赖特定架构，所以这个局限性是合理的。
-博文有没有术语错位？比如“MDP”等使用正确。“GAE”正确。“Critic”正确。
-博文有没有引用偏差？博文没有直接引用原文具体段落，但这是技术博客的常见做法，不是必须的。博文整体准确。
-博文是否遗漏了关键数字？例如，在“反直觉发现”中，博文说“StepPO 在学术文献搜索任务中，使用的平均响应 Token 数最少（2646.35），但 F1@all 最高。” 原文Table 3中F1@all是0.314，博文没有列出具体F1值，但提到了“最高”。可以接受。
-博文在实验结果表格中，WebShop的Score：StepPO 77.52，原文Table 2中StepPO的WebShop Score是77.52（Qwen3-4B），正确。但原文中WebShop还有Succ.列，博文没有列出Succ.。这不算遗漏，因为博文选择了Score作为代表。
-博文在表格中ALFWorld只列出了Seen Win Rate，没有Unseen。原文有Seen和Unseen。博文只列了Seen，但原文中Seen和Unseen都很重要。这可能是一个遗漏：博文只显示了Seen，但原文中StepPO的Unseen Win Rate是85.82（Qwen3-4B），而PPO是72.39，GRPO是74.63，GiGPO是79.10。博文没有提及Unseen，但这不是关键错误，只是不够全面。
-博文说“StepPO 在所有指标上均优于 PPO、GRPO、GiGPO 等主流方法。” 原文Table 2确实如此。但需要注意，原文中有些基线在某些任务上略高于StepPO？检查原文：没有，StepPO在所有指标上都是最好的。所以正确。
-博文说“它不改变模型架构，而是重构了强化学习（RL）的 MDP 建模和信用分配机制”。原文确实不改变模型架构，只是改变MDP formulation和credit assignment。
现在，考虑评分。博文准确反映了论文的核心贡献、方法、关键结果和工程启示。它没有重大错误，术语使用正确，没有过度夸大（如说“里程碑级”，但博文没有给出夸张评价，只是客观描述）。博文省略了一些细节（如ablation、训练动态、case study等），但作为一篇技术博客，这是合理的取舍。根据评分标准，⭐⭐⭐是“博文准确反映论文，论文是有意义的工作（多数博文的默认档）”。这篇博文属于准确反映，没有明显瑕疵，所以应该给3星。但考虑到博文在工程启示部分加入了实用的建议，并且准确传达了反直觉发现，可能可以给更高？评分标准说“⭐⭐⭐⭐ 论文有显著创新或工程价值 + 博文准确传达 insight”。论文本身有显著创新（step-centric paradigm），博文也准确传达了insight。但博文是否“准确传达 insight”？是的。但评分标准还要求“论文有显著创新或工程价值”。这篇论文在agentic RL领域提出了新范式，实验全面，方法简洁，我认为有显著创新。博文准确传达了核心insight。但是，评分标准说“⭐⭐⭐ 是多数博文的默认档——HF Daily Papers 已预筛过质量，blog 只要忠实就到这一档”。这里强调“只要忠实”就3星。但博文不仅忠实，还额外提炼了工程启示，并且没有错误。不过，3星到4星的区别在于“论文有显著创新或工程价值 + 博文准确传达 insight”。我认为这篇论文确实有显著创新（step-level MDP for agentic RL是一个新视角），博文也准确传达了。但博文是否“准确传达 insight”达到了“准确”水平？是的。但是，博文可能遗漏了原文一些重要的细节，比如对retokenization drift的详细分析、ablation study等。但insight（粒度错配、step级优化）传达得很好。所以可能可以给3.5星？但评分标准中半星用½ (U+00BD)。我倾向于3.5星，但需要确认是否有挑刺点。
现在，我们需要列出挑刺。必须引用原文或博文的具体片段或数据作为依据。需要找出博文遗漏的关键约束/数字/条件、过度解读、术语错位、引用偏差等。
仔细检查博文每个部分：
-博文开头：“训练 LLM Agent 时，我们常陷入一个误区：用处理文本生成的逻辑去优化决策过程。” 原文没有说“误区”，但意思一致。不算问题。
-博文：“现有的 RLHF 或 GRPO 算法大多基于“Token 中心”范式。” 原文提到“Most existing agentic RL methods inherit the RL algorithms for LLMs. Representative methods include PPO from RLHF, and GRPO from RLVR. These methods are largely token-centric.” 所以正确。
-博文：“在这种范式下，模型每生成一个 token 就被视为一次状态转移。” 原文：token-level MDP, each token is an action, each prefix is a state, transition is deterministic. 正确。
-博文：“但在 Agentic RL 中，Agent 与环境的交互是以“步骤（Step）”为单位的：观察环境 -> 生成完整动作（如调用工具）-> 接收反馈 -> 进入下一步。” 原文：LLM agents do not interact with environments one token at a time. The actual medium of interaction is a step. 正确。
-博文：“核心痛点：Token 级的信用分配过于局部，无法捕捉完整动作对后续状态的影响；而轨迹级（Trajectory-level）分配又过于粗糙，难以区分长序列中哪些中间步骤是关键决策。” 原文类似表述：token-level credit is often too local to capture the effect of complete actions on subsequent states, while trajectory-level credit is too coarse to identify key intermediate decisions. 正确。
-博文：“StepPO 的解决思路很直接：将 MDP 从 Token 级重构为 Step 级。其核心创新在于两个对齐：1. Step 级 MDP 建模；2. Step 级信用分配与重要性采样。” 博文对重要性采样的描述：“由于一个步骤包含多个 Token，直接相乘会导致长动作的比率极端化。StepPO 采用 Token 比率的几何平均作为步骤级的重要性采样权重 w_t(θ)。这种长度归一化设计确保了不同长度的动作在更新时具有可比性。” 正确。
-博文实验结果表格：数据正确。
-博文“反直觉发现”：引用了原文Table 3的数据，正确。
-博文折扣因子实验：数据正确。
-博文工程启示：提到“不要将交互轨迹存储为扁平的 Token 序列。应建立“步骤原生（Step-Native）”的数据记录，明确标记每个步骤的状态、动作和奖励边界。这能避免重分词漂移（Retokenization Drift），确保训练与推理的一致性。” 原文有详细讨论retokenization drift，博文准确。但原文提到retokenization drift是在3.2节，而博文将其放在工程启示中，没问题。
-博文“异步训练支持”：原文4.4节有异步训练设计。博文说“StepPO 天然适合异步训练架构”，原文说“StepPO instead benefits from a decoupled design”，所以准确。
-博文“计算效率优化”：原文提到“StepPO estimates values only at step boundaries rather than all generated tokens, making supervision more compact.” 博文说“Critic 仅在步骤边界进行价值估计，而非每个 Token，这在一定程度上减少了监督信号的冗余。” 正确。
-博文“局限与展望”：提到依赖明确的步骤边界定义。原文没有讨论这个局限，但这是合理的。不过，这可能算“过度解读”吗？原文的方法假设有明确的步骤边界（例如工具调用或环境步骤），对于没有明确边界的场景，方法可能不直接适用。博文指出这一点，是合理的延伸，没有与原文矛盾。
-博文“局限与展望”还提到“论文主要基于 Qwen3 系列模型，在其他架构（如 MoE）上的泛化性仍需验证。” 原文实验确实只用了Qwen3，所以这个局限性是合理的。
-博文有没有遗漏原文中关于“Step-Level Trajectory Representation”的细节？原文有图3(a)和描述，博文没有展开，但这不是必须的。
-博文有没有遗漏原文中关于“Ablation Study”的结果？博文没有提到ablation。但博文在“反直觉发现”中提到了折扣因子实验，这属于ablation的一部分。但完整的ablation（step-level GAE和step-level IS）博文没有提及。这可能算是一个遗漏，但不是关键信息。不过，如果博文声称全面概括，但遗漏了重要消融实验，可能算瑕疵。但博文没有声称全面，只是摘取亮点。所以不算严重。
-博文有没有提到“Training Dynamics Analysis”和“Step-Wise Difficulty Analysis”？没有。这些分析提供了insight，但博文选择了折扣因子实验作为鲁棒性证据。这可以接受。
-博文有没有提到“Tool-Use Behavior Analysis”（Table 3）？博文在“反直觉发现”中引用了。正确。
-博文有没有提到“Case Study”（图8）？没有。但也不是必须。
-博文有没有提到“Agent-R1 to Claw-R1”部分？没有。博文聚焦算法本身，省略了系统讨论，可以。
现在，检查是否有术语错位。博文使用“信用分配”对应“credit assignment”，正确。“GAE”正确。“Critic”正确。“MDP”正确。“几何平均”正确。
引用偏差：博文没有直接引用原文，但这是常见风格，不是问题。
过度解读：博文说“StepPO 天然适合异步训练架构”，原文说的是“StepPO instead benefits from a decoupled design”，没有说“天然”，但意思差不多。不算过度。
博文说“StepPO 的 Critic 仅在步骤边界进行价值估计，而非每个 Token，这在一定程度上减少了监督信号的冗余。” 原文说“making supervision more compact”，没有说“减少冗余”，但意思接近。不算错误。
博文说“这能避免重分词漂移（Retokenization Drift），确保训练与推理的一致性。” 原文3.2节详细讨论了retokenization drift，博文准确。
博文在实验结果表格中，ALFWorld只列出了Seen Win Rate，没有Unseen。原文中ALFWorld有Seen和Unseen两个指标，博文只列了Seen。这是否算“遗漏关键数字”？原文中StepPO在Unseen上的表现也很重要，但博文只选了一个代表性指标。这不算严重，因为博文表格标题是“关键数据对比”，并选择了几个任务的一个主要指标。但严格来说，博文没有提及Unseen，可能让读者忽略了这个维度。不过，博文在“反直觉发现”中提到了WebShop和学术搜索，没有提到ALFWorld的Unseen。我觉得可以接受，不算重大遗漏。
另一个可能的挑刺：博文在介绍核心创新时说“两个对齐”，但原文中StepPO的核心创新包括三个：step-level MDP formulation, step-level credit assignment, step-level importance sampling。博文将后两个合并为“信用分配与重要性采样”，但重要性采样是actor objective的一部分，与credit assignment并列。博文没有明确区分credit assignment和importance sampling，但概括为“两个对齐”也可以。不算错误。
博文在工程启示中建议“数据结构重构：不要将交互轨迹存储为扁平的 Token 序列。应建立“步骤原生（Step-Native）”的数据记录”。原文确实提倡step-native representation，但原文也提到了Flat Token-Space Representation的缺点。博文建议正确。
博文在“局限与展望”中提到了“对于非结构化或连续控制场景，如何界定“一步”仍具挑战。” 原文没有讨论这个，但这是合理的推断。不过，原文的方法本身就是针对有步骤边界的场景，所以这个局限是隐式的。博文明确提出来，不算过度解读。
综合来看，博文准确反映了论文的核心内容，没有严重错误，遗漏了一些次要细节但整体清晰。根据评分标准，我认为应该是⭐⭐⭐½（3.5星），因为博文不仅忠实，还提炼了工程启示，并且准确传达了insight，但仍有可以改进的地方（如未提及unseen结果、未提及ablation）。但评分标准说“⭐⭐⭐⭐ 论文有显著创新或工程价值 + 博文准确传达 insight”。这篇论文有显著创新，博文准确传达了insight，但博文是否完美呈现？可能接近4星，但考虑到博文省略了一些重要结果（如ablation, unseen），我认为3.5星是合理的。但也可以给3星，因为默认档是3星。我倾向于3.5星，因为博文质量高于一般忠实翻译，加入了实用总结。
但我们需要根据“硬约束”输出，不要加标题前缀，不要markdown代码块包装。输出完毕后单独一行写
