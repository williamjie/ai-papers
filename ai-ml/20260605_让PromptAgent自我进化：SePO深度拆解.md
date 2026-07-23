# ⭐⭐⭐½ 让 Prompt Agent 自我进化：SePO 深度拆解

**日期**: 2026-06-05

---

论文 : SePO: Self-Evolving Prompt Agent for System Prompt Optimization链接 : https://arxiv.org/abs/2606.04465在 Agent 开发中，System Prompt 往往是性能瓶颈。我们习惯了人工调试 Prompt，或者用固定规则的优化器去“修修补补”。但有没有想过，那个负责优化 Prompt 的 Agent 本身，是不是也该被优化？SePO 给出了肯定的答案，它让优化器具备“自我进化”能力，打破了人工设计的天花板。
### 痛点：谁在优化优化器？
现有的 Prompt 优化方法（如 TextGrad、MetaSPO）存在一个明显的逻辑断层。它们引入一个“Prompt Agent”来根据反馈修改“Task Agent”的 Prompt。
然而，这个 Prompt Agent 自身的 System Prompt 通常是人工手写且固定的。这意味着，无论处理多少任务，优化器的能力上限被锁死在人类工程师的水平上。它无法从历史经验中学习如何更好地提出建议，也无法适应不同任务的特性。SePO 指出，只有将 Prompt Agent 自身也纳入优化目标，才能形成真正的闭环。
### 核心设计：自指与两阶段训练SePO 的核心 Insight 是 自指（Self-Referential）设计 。它将 Prompt Agent 视为一个特殊的 Task Agent，其任务是“改进其他 Agent 的 Prompt”。因此，Prompt Agent 的 System Prompt 和 Task Agent 的 Prompt 遵循同一套优化逻辑。
具体实现上，SePO 采用了 两阶段训练管道 ：
-预训练（Pre-training）：
Prompt Agent 在一个多任务池（Multi-task Pool）中运行自指进化。
- 它不断生成、评估并保留更优的自身 Prompt 候选者，形成一个“存档（Archive）”。
- 这一步的目标是积累通用的 Prompt 优化技能，而非记忆特定任务的解法。
-微调（Fine-tuning）：
使用预训练得到的最强 Prompt Agent，针对具体目标任务优化 Task Agent 的 Prompt。
- 此时 Prompt Agent 自身不再进化，而是作为成熟的“导师”工作。
这种设计借鉴了大模型的预训练-微调范式。通过多任务预训练，Prompt Agent 学会了如何针对不同领域（数学、代码、逻辑）提出有效的改进建议，实现了跨任务的泛化。
### 实验结果：全面超越基线SePO 在五个涵盖数学、抽象推理、科学、代码和逻辑的基准测试中进行了评估。结果显示，其性能显著优于人工 CoT 及主流自动优化方法。
方法 AIME’25 ARC-AGI-1 GPQA MBPP Sudoku 平均准确率 Manual-CoT 57.55 37.30 76.46 91.20 96.95 71.89 TextGrad 55.99 34.75 74.44 90.15 96.60 70.39 MetaSPO 57.71 37.27 75.51 89.30 96.80 71.32 SePO-Specialist 60.94 37.46 76.72 95.55 99.80 74.09 SePO-Generalist 64.22 43.39 78.18 96.20 99.90 76.38关键发现 ：SePO-Generalist 相比 Manual-CoT，平均准确率提升了 4.49 个百分点。在最具挑战性的 ARC-AGI-1 任务上，提升尤为明显（+6.09 分）。
此外，消融实验证实了两个组件的必要性：
- 移除自改进（即不使用预训练进化后的 Agent），平均准确率下降 1.44 分。
- 移除基于存档的开放式进化搜索，改用线性搜索，平均准确率下降 3.74 分。
### 工程启示与局限对实际应用的指导意义：
- 优化器即资产：不要将 Prompt 优化视为一次性脚本。构建一个可复用的、经过多任务训练的 Prompt Agent，能大幅降低新任务的冷启动成本。
- 跨任务泛化：SePO 证明，在未见过的任务（如 Sudoku）上，预训练积累的通用优化技能依然有效，无需针对每个任务重新从头进化优化器。
- 成本摊销：虽然两阶段训练看似复杂，但预训练只需运行一次。在多任务场景下，SePO-Generalist 的均摊成本低于为每个任务单独训练的 Specialist 版本。
局限与思考：
- 计算开销：进化搜索需要大量的评估调用（Evaluation Calls）。对于推理成本极高的模型，这可能成为瓶颈。
- 任务选择启发式：目前预训练任务池的选择依赖贪心启发式算法，更高级的任务选择策略可能带来进一步收益。
SePO 提醒我们，在 Agent 系统中，元能力（Meta-Capability）的进化往往比单一任务的优化更具长期价值。让工具自我完善，是通往更强自主性的关键一步。
## 📝 AI 点评点评时间：2026-06-05 18:19 ｜ reviewer: DeepSeek V4 Flash核心贡献: 解决现有系统提示优化方法中提示代理自身提示手工固定、无法从经验中学习的问题；采用自指设计，将提示代理自身提示也作为优化目标，通过两阶段训练（预训练+微调）和开放式进化搜索同时优化两类代理的提示。
亮点:
- 博文准确提炼了自指设计这一核心洞察，并清晰对比了现有方法（TextGrad、MetaSPO）的局限性，点出“优化器自身也被优化”的关键新意。
- 博文对两阶段训练管道的描述（预训练积累通用技能、微调针对性优化）基本到位，并强调了成本摊销和跨任务泛化的工程价值，符合原文重点。
- 博文在“工程启示”部分将结果转化为可操作的指导（优化器即资产、跨任务泛化、成本摊销），有助于读者理解实际意义。
挑刺:
-遗漏了跨任务泛化的关键实验数据。原文图4展示了SePO-Generalist在Sudoku（从未出现在预训练混合中）上从96.95提升至99.90，以及“无相关任务”设置下仍优于Manual-CoT的具体数字。博文仅泛泛提及“在未见过的任务上依然有效”，未引用任何数据，削弱了这一重要结论的说服力。
原文：Figure 4及对应正文“Sudoku never appears in any pre-training mixture and SePO-Generalist still improves it from 96.95 (Manual-CoT) to 99.90.”
- 博文：“SePO 证明，在未见过的任务（如 Sudoku）上，预训练积累的通用优化技能依然有效”。未给出具体数字。
-未提及模型对换的鲁棒性实验。原文Table 3使用Gemini 3.1 Flash-Lite + Claude Opus 4.6替换默认模型对，SePO-Generalist仍平均提升+2.13点。这一结果对方法实用性和泛化性至关重要，博文完全忽略。
原文：Table 3及正文“After rerunning all five tasks, SePO-Generalist again outperforms Manual-CoT on every task… average accuracy improves from 67.95 to 70.08”。
- 博文未涉及。
-微调阶段的具体算法描述不准确。博文说“微调（Fine-tuning）：使用预训练得到的最强 Prompt Agent，针对具体目标任务优化 Task Agent 的 Prompt。此时 Prompt Agent 自身不再进化”。但原文中微调阶段同样运行Algorithm 1的进化搜索（只是prompt agent的system prompt固定），博文未提及微调阶段也使用“基于存档的开放式进化搜索”来优化task agent的prompt，可能让读者误以为微调只是单次调用。
原文：Algorithm 1及Section 3.3 “Fine-tuning then applies this prompt agent to optimize a task agent’s prompt for a target task. It evolves a task agent’s system prompt from p(0) to p⋆ on a single task T. During fine-tuning, the prompt agent uses p̃⋆ as its system prompt throughout.”
- 博文：“使用预训练得到的最强 Prompt Agent，针对具体目标任务优化 Task Agent 的 Prompt”。未提及进化搜索。
总评: ⭐⭐⭐½ 博文准确传达了自指和两阶段训练的核心思想，主要实验结果正确，但遗漏了跨任务泛化定量证据和模型对换鲁棒性等关键支撑，微调阶段描述不够精确，整体忠实但不够完整。
