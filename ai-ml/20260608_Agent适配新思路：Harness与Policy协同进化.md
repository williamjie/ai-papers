# ⭐⭐⭐½ Agent适配新思路：Harness与Policy协同进化

**日期**: 2026-06-08

---

论文 : HarnessForge: Joint Harness and Policy Evolution for Adaptive Agent Systems链接 : https://arxiv.org/abs/2606.01779我们常陷入一个误区：Agent 表现差，要么怪 Prompt/Harness 写得烂，要么怪模型推理能力弱。于是工程师们要么没日没夜地调 Workflow，要么死磕 RLHF 微调。但北航与清华团队在 HarnessForge 中揭示了一个被忽视的事实： 外挂的执行框架（Harness）和内置的推理策略（Policy）必须“门当户对” 。单方面优化任何一方，都会因为“兼容性鸿沟”导致系统效能封顶。
### 痛点：组件隔离导致的“兼容性鸿沟”
现有方案通常将 Agent 适配视为局部组件优化。搜索类方法（如 AFlow、ADAS）专注于进化外部工作流，训练类方法（如 GRPO、RLOO）专注于强化内部策略。
这种做法存在致命缺陷： 外部 Harness 和内部 Policy 是解耦进化的 。
一个更复杂的 Harness 可能暴露了更有用的规划或记忆结构，但如果 Reasoner 无法可靠执行这些新协议，系统就会崩溃；反之，更强的 Policy 也可能被简陋的 Harness 束缚手脚。论文指出，真正的系统级元适应（Meta-adaptation）必须将“外挂执行接口”与“内置推理行为”视为一个耦合对进行联合优化。
### 方法拆解：故障引导的协同进化HarnessForge 的核心 Insight 在于： 不要试图训练一个通用的强 Reasoner，而是让 Reasoner 专门适配当前的 Harness 。其实现分为三个紧密咬合的阶段：
-故障归因与 Harness 裁剪（Fault-Guided Tailoring）
系统首先执行任务并收集轨迹。Meta-Agent 会像医生一样进行“故障归因”，精准定位失败是源于规划、动作还是记忆组件。
- 基于历史档案中的成功案例，生成改进报告，并对 Planning/Action/Memory 模块进行受控编辑。
- 关键设计：采用 Pareto 前沿选择机制，在性能与延迟之间筛选出幸存的 Harness 候选集，而非盲目保留所有变体。
-Harness 条件化的策略对齐（Harness-Conditioned Alignment）
这是最反直觉的一步。对于幸存的 Harness，系统不重新收集数据，而是直接复用上一阶段评估 Harness 时产生的成功轨迹。
- 将这些轨迹转化为监督微调（Supervised Fine-Tuning, SFT）数据，训练一个轻量级的 LoRA Adapter。
- 核心直觉：Adapter 的目标不是让模型变“聪明”，而是让它学会在当前特定 Harness 的约束下“听话”执行。
-配对选择与迭代每一轮进化都产出匹配的 (Harness, Policy) 对。下一轮基于此对继续进化，形成良性循环。
### 关键结果：协同效应显著在 Qwen3-4B/8B backbone 上，HarnessForge 展现了超越单一优化策略的性能：
- 综合性能提升：相比最强的 Harness-only 或 Policy-only 基线，平均提升 +3.56%。
- 极端场景突破：在 TMDB 数据集上，Qwen3-4B 的成功率比最强基线高出 12.0%；API-Bank 的 API 调用准确率平均提升 4.96%。
- 消融实验警示：移除 Harness 进化或 Policy 对齐中的任意一项，性能均显著下降。在第三轮进化中，仅保留 Policy 进化而放弃 Harness 裁剪，ToolHop 答案准确率暴跌 6.15%。
⚠️ 反直觉发现 ：
论文展示了“兼容性矩阵”（Fig. 4）。最终轮进化出的 Harness 若搭配早期的 Policy，性能仅为 71.93%；反之亦然。只有 匹配的对 才能达到 77.19% 的峰值。这证明收益并非来自组件绝对强度的提升，而是来自二者之间的 特异性兼容 。
### 工程启示：小模型时代的最佳实践对于资源受限的工程场景（如部署 4B-8B 模型），HarnessForge 提供了极具价值的指导：
- 拒绝盲目 RL：虽然 GRPO/RLOO 能带来额外增益，但 rollout 成本极高（Round 3 需 45.6K rollouts vs SFT 的 12.0K）。在 Harness 结构未稳定前，使用 SFT 对齐是性价比最高的选择。
- 保留多样性：实验表明，每轮保留 k=2 个幸存 Harness 是最佳平衡点。保留太少（k=1）会丧失探索空间，太多则削弱选择压力。
- 结构化进化：不要试图让 LLM 重写任意代码。限制编辑操作在 Planning/Action/Memory 三个明确组件内，既能保证可执行性，又便于审计。
### 局限与展望HarnessForge 目前主要在中小参数模型上验证。对于前沿大模型（Frontier Models），其内部推理能力已极强，Harness-Policy 的耦合必要性可能减弱。此外，长程任务中的重复 Rollout 成本依然较高，未来需引入代理评估或自适应分配机制来降低开销。
## 📝 AI 点评点评时间：2026-06-08 17:07 ｜ reviewer: DeepSeek V4 Flash我们被要求对一篇AI论文解读博文进行点评，基于原始论文（arxiv 2606.01779）和博文内容。需要输出四部分：核心贡献、亮点、挑刺、总评。评分标准从1星到5星，默认3星是忠实反映论文的有意义工作。
首先，阅读原始论文摘要和关键部分。论文标题：HarnessForge: Joint Harness and Policy Evolution for Adaptive Agent Systems。核心贡献：将LLM agent系统形式化为harness-policy pair，提出联合进化框架，通过故障引导的harness裁剪和harness条件化的policy对齐，实现系统级元适应。实验在5个benchmark上显示优于单独优化harness或policy的基线。
博文内容：标题”Agent适配新思路：Harness与Policy协同进化”。博文结构清晰，先指出痛点（兼容性鸿沟），然后拆解方法（三个阶段），关键结果，工程启示，局限。博文似乎是对论文的准确概括，语言生动，但需要检查是否有遗漏或曲解。
亮点：博文对核心insight提炼到位：外挂执行框架和内置推理策略必须联合优化。点出了故障引导、条件化对齐、兼容性矩阵等关键。工程启示部分有实践指导。
挑刺：需要对比原文与博文，找出博文遗漏的关键约束/数字/条件、过度解读、术语错位等。检查原文细节：博文说“综合性能提升：相比最强的Harness-only或Policy-only基线，平均提升+3.56%。” 原文Table 1确实说“averaging +3.56% over per-metric strongest baselines”。但原文也提到“up to 12.0%”。博文提到“在TMDB数据集上，Qwen3-4B的成功率比最强基线高出12.0%”，准确。博文提到“消融实验警示：移除Harness进化或Policy对齐中的任意一项，性能均显著下降。在第三轮进化中，仅保留Policy进化而放弃Harness裁剪，ToolHop答案准确率暴跌6.15%。” 原文Table 2显示HarnessForge在Round3 ToolHop Correct 52.82%，w/o Harness Evo 46.67%，下降6.15%，正确。博文说“仅保留Policy进化而放弃Harness裁剪”，对应w/o Harness Evo，但注意w/o Harness Evo是去掉Harness进化，保留Policy进化？原文w/o Harness Evo是移除Harness tailoring，保留Policy alignment？是的，所以博文表述基本正确。但注意博文说“仅保留Policy进化”，可能有点歧义，但总体OK。
需要检查是否有过度解读：博文说“不要试图训练一个通用的强Reasoner，而是让Reasoner专门适配当前的Harness。” 原文Sec 3.4说“its goal is not to train a universally stronger reasoner, but to align the inherited policy with the execution conventions induced by a particular harness.” 所以准确。
博文说“关键设计：采用Pareto前沿选择机制，在性能与延迟之间筛选出幸存的Harness候选集”。原文确实有Pareto selection，包括性能、token cost、延迟。但博文只提到“性能与延迟”，原文是“final response quality, negative token cost, negative latency”。所以基本OK。
博文说“综合性能提升：相比最强的Harness-only或Policy-only基线，平均提升+3.56%。” 注意原文表述是“improving over the strongest harness-only and policy-only baselines by 3.56% on average”。但注意基线包括search-style和training-style，但原文说“over per-metric strongest baselines”，即每个指标上最强基线的平均值。博文概括合理。
挑刺：需要找到遗漏的关键约束/数字/条件。例如，原文实验设置中，进化数据是3.8K训练池，博文没有提及这个规模，但不算严重遗漏。博文提到“使用SFT对齐是性价比最高的选择”，原文Table 3显示SFT在Rollout budget上更少，但原文也说“RL-style objectives provide additional improvement potential at higher cost”。博文正确。
可能存在的术语错位：博文说“外挂的执行框架（Harness）和内置的推理策略（Policy）必须‘门当户对’。” 原文用“compatibility”和“coupled harness–policy pair”。博文比喻恰当。
博文说“搜索类方法（如AFlow、ADAS）专注于进化外部工作流，训练类方法（如GRPO、RLOO）专注于强化内部策略。” 原文Related Work提到这些。准确。
博文说“系统首先执行任务并收集轨迹。Meta-Agent会像医生一样进行‘故障归因’，精准定位失败是源于规划、动作还是记忆组件。” 原文Sec 3.3描述故障归因。准确。
博文说“对于幸存的Harness，系统不重新收集数据，而是直接复用上一阶段评估Harness时产生的成功轨迹。” 原文Sec 3.4说“reuses the rollout pool already produced when H_k^{(r+1)} is evaluated during budgeted harness selection”。准确。
博文说“保留多样性：实验表明，每轮保留k=2个幸存Harness是最佳平衡点。” 原文Fig 3a显示k=2比k=1好，k=3边际增益小。博文正确。
博文说“HarnessForge目前主要在中小参数模型上验证。” 原文Limitations提到“primarily evaluated with Qwen3-4B and Qwen3-8B backbones”。准确。
但博文可能遗漏了原文一些重要细节：例如原文提到“HarnessForge also requires repeated rollouts for harness profiling, selection, and policy alignment. Although our design reuses rollout trajectories…”。博文在局限中提到了“长程任务中的重复Rollout成本依然较高”，但未提及具体设计如reuse。不过博文在方法中已提到复用轨迹，所以局限部分提到成本高也算合理。
另一个可能遗漏：原文在方法中定义agent system G=(H,Rδ)，H=(P,A,M)，博文提到了三个组件，但未提及“adapted reasoner Rδ = Rθ0+δ”的形式化。但博文不是技术报告，可以接受。
博文说“关键结果：协同效应显著”部分，列举了具体数字。但原文Table 1中HarnessForge在Qwen3-8B上ToolHop Correct是54.87%，但博文没有列出具体数值，只是说了提升百分比。这不算遗漏，因为博文是总结。
注意原文表1中HarnessForge在Qwen3-4B上ToolHop Correct 52.82%，但博文说“综合性能提升：相比最强的Harness-only或Policy-only基线，平均提升+3.56%。” 原文是平均，但博文没有给出具体每个benchmark的数值。可能读者会想知道具体数字，但这不是必须。
需要检查博文是否有过度夸大或错误。例如博文说“极端场景突破：在TMDB数据集上，Qwen3-4B的成功率比最强基线高出12.0%”。原文Table 1：TMDB Success Qwen3-4B: HarnessForge 80.00%, 最强基线是GRPO 70.00%? 实际上GRPO是70.00%，HarnessForge 80.00%，确实高出10个百分点（12%相对提升？原文说“improves success by 12.00% with Qwen3-4B”，可能指绝对提升？但原文是“12.00%”，注意基线70%，HarnessForge 80%，绝对提升10个百分点，相对提升14.3%。原文写“12.00%”，可能是指成功率从70%到80%是10个百分点，但原文写12.00%？检查原文：Table 1中TMDB Success: Qwen3-4B最强基线是GRPO 70.00%，HarnessForge 80.00%，差10个百分点。但原文文字说“largest gains appear on TMDB: HarnessForge improves success by 12.00% with Qwen3-4B and 6.00% with Qwen3-8B over the strongest baseline.” 仔细看：Qwen3-4B最强基线可能是RLOO或GRPO？Table 1中Qwen3-4B TMDB Success: ADAS 51.00, AgentSquare 38.00, AFlow 39.00, MaAS 43.00, MermaidFlow 47.00, SFT 69.00, RLOO 74.00, GRPO 70.00, HarnessForge 80.00。最强基线是RLOO 74.00%，HarnessForge 80.00%，提升6个百分点（相对8.1%），但原文说12.00%？等等，再检查Qwen3-4B TMDB Success: 原文表格中Qwen3-4B TMDB Success列：ADAS 51.00, AgentSquare 38.00, AFlow 39.00, MaAS 43.00, MermaidFlow 47.00, SFT 69.00, RLOO 74.00, GRPO 70.00, HarnessForge 80.00。所以最强基线是RLOO 74.00%，HarnessForge 80.00%，绝对提升6个百分点。但原文写12.00%？可能我看错了？原文是“improves success by 12.00% with Qwen3-4B”，但表格中TMDB Success列，Qwen3-4B的RLOO是74.00，GRPO是70.00，最强是RLOO 74，提升6个百分点。但原文说12%？再检查：原文表格中还有Qwen3-8B TMDB Success: ADAS 45.00, … RLOO 61.00, GRPO 61.00, HarnessForge 64.00? 不对，Qwen3-8B TMDB Success: ADAS 45.00, AgentSquare 35.00, AFlow 32.00, MaAS 37.00, MermaidFlow 39.00, SFT 61.00, RLOO 61.00, GRPO 64.00, HarnessForge 76.00。所以Qwen3-8B最强基线是GRPO 64.00%，HarnessForge 76.00%，提升12个百分点（绝对）。原文说“improves success by 12.00% with Qwen3-4B and 6.00% with Qwen3-8B”，但根据表格，Qwen3-4B提升6%，Qwen3-8B提升12%。可能是原文笔误？或者我读错列？再仔细看原文Table 1：TMDB列下有两个子列：Success和Path。Qwen3-4B的Success: ADAS 51.00, AgentSquare 38.00, AFlow 39.00, MaAS 43.00, MermaidFlow 47.00, SFT 69.00, RLOO 74.00, GRPO 70.00, HarnessForge 80.00。所以最强基线是RLOO 74.00，HarnessForge 80.00，提升6.00个百分点（绝对）。原文却说12.00%，可能是指相对提升？80/74≈1.081，相对提升8.1%，不是12%。所以原文可能有误？但博文引用了“高出12.0%”，可能是照搬原文，但原文有误？检查原文句子：“The largest gains appear on TMDB: HarnessForge improves success by 12.00% with Qwen3-4B and 6.00% with Qwen3-8B over the strongest baseline.” 结合表格，Qwen3-4B TMDB Success最强基线是RLOO 74.00，HarnessForge 80.00，绝对差6.00个百分点。Qwen3-8B TMDB Success最强基线是GRPO 64.00，HarnessForge 76.00，绝对差12.00个百分点。所以原文可能把Qwen3-4B和Qwen3-8B的数值写反了？或者我理解错了“success by 12.00%”指的是百分比点？如果是百分比点，Qwen3-4B是6.00，Qwen3-8B是12.00。但原文写“improves success by 12.00% with Qwen3-4B and 6.00% with Qwen3-8B”，显然颠倒了。这是一个潜在错误。博文直接引用“Qwen3-4B的成功率比最强基线高出12.0%”，这可能是照搬了原文的错误。但作为点评，我们需要指出博文是否准确传达了原文。如果原文有错，博文复述了错误，那么博文应该被批评吗？通常博文应该基于原文，���原文可能笔误。我们以原文为准，原文表格数字显示Qwen3-4B提升6%，Qwen3-8B提升12%。博文说“在TMDB数据集上，Qwen3-4B的成功率比最强基线高出12.0%”，这与表格不符。这是一个事实错误。所以挑刺可以指出博文数字引用错误。但注意博文写的是“Qwen3-4B的成功率比最强基线高出12.0%”，原文表格中Qwen3-4B最高基线RLOO 74，HarnessForge 80，差6个百分点。所以博文错了。原文文字描述可能错了，但博文应该核对表格。所以这是一个挑刺点。
另外，博文说“API-Bank的API调用准确率平均提升4.96%”，原文Table 1中API-Bank API accuracy: Qwen3-4B: 最强基线GRPO 73.76? 实际Qwen3-4B API-Bank API: ADAS 59.57, AgentSquare 53.90, AFlow 47.52, MaAS 60.28, MermaidFlow 62.41, SFT 73.05, RLOO 71.63, GRPO 73.76, HarnessForge 78.01。最强基线GRPO 73.76，HarnessForge 78.01，提升4.25个百分点。Qwen3-8B: 最强基线GRPO 73.76? 实际Qwen3-8B API-Bank API: ADAS 59.57, AgentSquare 53.90, AFlow 47.52, MaAS 60.28, MermaidFlow 62.41, SFT 73.05, RLOO 71.63, GRPO 73.76, HarnessForge 78.01? 等等Qwen3-8B表格不同：Qwen3-8B API-Bank: ADAS 60.99, AgentSquare 46.10, AFlow 41.13, MaAS 63.83, MermaidFlow 60.28, SFT 73.76, RLOO 76.60, GRPO 75.18, HarnessForge 82.27。所以最强基线RLOO 76.60，HarnessForge 82.27，提升5.67个百分点。平均提升(4.25+5.67)/2=4.96，所以博文正确。
其他遗漏：博文没有提到原文中的“训练方法无关性”分析（Table 3），但这不是必须。博文提到了“虽然GRPO/RLOO能带来额外增益，但rollout成本极高”，这与Table 3一致。
博文没有提到原文中的“retained-harness sensitivity”图（Fig 3a）和“budget-performance Pareto”图（Fig 3b）的具体细节，但提到了保留k=2的结论。可以接受。
博文没有提到原文中的“module ablation”表（Table 2），但提到了消融实验的结果。准确。
博文没有提到原文中的“case study”细节，但提到了“兼容性矩阵”。可以接受。
博文语言生动，但可能有些夸张，如“致命缺陷”、“门当户对”等，但这是风格，不算错误。
评分：博文准确反映了论文的核心贡献和方法，没有严重事实错误，但有一个数字引用错误（TMDB的12%可能不对，需要核实）。如果博文数字错误，那么算是一个事实错位。根据评分标准，严重事实错位会导致2星或更低。但这里错误是引用了原文可能的笔误，且博文没有独立核实。作为点评，我们应该基于原文表格判断。原文表格中Qwen3-4B TMDB Success HarnessForge 80.00，最强基线RLOO 74.00，绝对提升6.00个百分点。原文文字说12.00%可能是错误，博文照搬了错误。所以博文有一个事实错误。但博文其他部分准确。那么评分应该在3星左右，但因为有事实错误，可能降到2.5或2星？但错误不是核心概念错误，而是具体数字。而且原文本身可能笔误，博文作为解读，没有发现并纠正，算是一个瑕疵。但考虑到博文整体质量高，可以给3星。但根据严格标准，如果博文有严重事实错位，应该给2星。这里算不算严重？数字错误可能误导读者，但影响范围有限。我认为可以给3星-（3星减半星）=2.5星。但评分标准中3星是“博文准确反映论文，论文是有意义的工作”，2星是“博文有严重事实/术语错位、核心论断不准”。这里博文核心论断准确，但数字错误算事实错位。是否严重？如果读者因此认为Qwen3-4B提升12%而实际只有6%，这算误导。所以可以算中等程度错误。我倾向于给2.5星（⭐⭐⭐½? 不，半星是½，2.5星是⭐⭐½? 但评分标准说半星用½，两档之间。所以可以是⭐⭐⭐½? 3.5星是高于3星，这里错误是减分，所以应该是⭐⭐½? 即2.5星。但注意评分标准从1到5，半星可用。我决定给3星（⭐⭐⭐）但注明错误，或者2.5星。考虑到博文整体忠实，且错误源于原文，我选择给3星，但在挑刺中明确指出数字错误。总评可以写3星，但指出瑕疵。
再思考：原文文字说“improves success by 12.00% with Qwen3-4B and 6.00% with Qwen3-8B”，但表格显示相反。可能是表格中Qwen3-4B TMDB Success的HarnessForge是80.00，但最强基线不是RLOO 74.00？检查表格：Qwen3-4B TMDB Success: RLOO 74.00, GRPO 70.00, SFT 69.00。所以最强是74。那么绝对差6。但原文说12%，也许原文指的是相对提升？(80-74)/74=8.1%，不是12%。所以明显是笔误。博文没有核对表格，直接复制了文字错误。所以挑刺应指出。
另外，博文说“综合性能提升：相比最强的Harness-only或Policy-only基线，平均提升+3.56%。” 原文说“improving over the strongest harness-only and policy-only baselines by 3.56% on average”，注意原文是“over per-metric strongest baselines”，即每个指标上最强基线。博文表述准确。
博文说“在第三轮进化中，仅保留Policy进化而放弃Harness裁剪，ToolHop答案准确率暴跌6.15%。” 原文Table 2中Round3 HarnessForge 52.82，w/o Harness Evo 46.67，差6.15。博文说“仅保留Policy进化”，实际上w/o Harness Evo是移除Harness进化，保留Policy进化，但注意Policy进化本身也是HarnessForge的一部分，所以表述正确。
博文说“虽然GRPO/RLOO能带来额外增益，但rollout成本极高（Round 3需45.6K rollouts vs SFT的12.0K）。” 原文Table 3显示Round3 GRPO 45.6K，SFT 12.0K。正确。
博文说“保留多样性：实验表明，每轮保留k=2个幸存Harness是最佳平衡点。” 原文Fig 3a显示k=2比k=1好，k=3边际增益小。博文概括正确。
博文说“不要试图让LLM重写任意代码。限制编辑操作在Planning/Action/Memory三个明确组件内。” 原文Sec 3.3和Table 6说明编辑空间。正确。
博文在局限部分说“对于前沿大模型，其内部推理能力已极强，Harness-Policy的耦合必要性可能减弱。” 原文Limitations说“Whether the same magnitude of harness–policy compatibility gains holds for substantially larger frontier-scale models remains an open direction.” 博文说“可能减弱”，是一种合理推测，但原文没有明确说减弱，只是说未知。博文表述稍有过度，但不算严重。
整体博文质量较高，但有一个明显数字错误。我决定给⭐⭐⭐½（3.5星）？但错误是事实性，应该扣分。3.5星要求“准确传达 insight”，错误会降低准确度。我给3星，并在挑刺中强调错误。
但注意评分标准：3星是“博文准确反映论文，论文是有意义的工作（多数博文的默认档）”。这里博文基本准确，除一个数字错误。是否算不准确？如果数字错误，那么反映不够准确。但核心内容准确。我认为可以给3星，但注明错误。
另一种思路：因为错误来源于原文，博文没有纠正，但作为解读应该核查。所以可以给3星但指出问题。总评写“⭐⭐⭐ 博文整体准确传达了论文的核心方法，但有一处数字引用错误（TMDB提升幅度与实际表格不符），瑕不掩瑜。”
现在撰写输出。
核心贡献：1-2句提炼。原文要解决LLM agent系统在面对多样化任务时固定系统表现不佳的问题，提出HarnessForge框架，将agent系统形式化为harness-policy对，通过故障引导的harness裁剪和harness条件化的policy对齐实现联合进化。
亮点：博文对核心insight提炼到位（兼容性鸿沟、协同进化），工程启示部分有实践价值（小模型最佳实践）。
挑刺：1. 博文引用TMDB提升12.0%与原文表格不符（实际Qwen3-4B提升6个百分点），属于事实错误。2. 博文将“兼容性矩阵”称为“反直觉发现”，但原文已明确论证，不算反直觉。3. 博文未提及原文中的训练池规模（3.8K）和具体进化轮数（3轮）等关键实验设置，但不算严重遗漏。
总评：⭐⭐⭐ 博文准确概括了论文核心方法，但有一处数字引用错误，整体忠实。
注意：需要引用原文或博文具体片段。例如原文表格显示Qwen3-4B TMDB Success: RLOO 74.00, HarnessForge 80.00，差6。博文说“高出12.0%”。引用博文：“在TMDB数据集上，Qwen3-4B的成功率比最强基线高出12.0%”。原文：“The largest gains appear on TMDB: HarnessForge improves success by 12.00% with Qwen3-4B and 6.00% with Qwen3-8B over the strongest baseline.” 但原文表格显示相反。所以博文复述了原文的错误。但作为点评，我们以原文表格为准，指出错误。
另外，博文说“综合性能提升：相比最强的Harness-only或Policy-only基线，平均提升+3.56%。” 原文摘要说“improving over the strongest harness-only and policy-only baselines by 3.56% on average”。注意原文是“over the strongest harness-only and policy-only baselines”，但博文说“Harness-only或Policy-only基线”，准确。
博文说“在第三轮进化中，仅保留Policy进化而放弃Harness裁剪，ToolHop答案准确率暴跌6.15%。” 原文Table 2显示w/o Harness Evo在Round3下降6.15，但注意w/o Harness Evo是移除Harness进化，但Policy进化仍然进行（因为HarnessForge的policy alignment是基于幸存harness的，如果移除harness进化，policy alignment仍然在固定harness上？原文Table 2的w/o Harness Evo是“-w/o Harness Evo.”，描述是“without Harness Evolution”，即只进行Policy Evolution？但原文描述“removing either harness tailoring or policy alignment”，所以w/o Harness Evo是只进行policy alignment？博文说“仅保留Policy进化”，合理。
博文没有提到原文中的“training agnostic”分析，但这不是必须。
现在写挑刺。
注意：博文可能还有其他遗漏，但主要挑数字错误。另外，博文说“核心直觉：Adapter的目标不是让模型变‘聪明’，而是让它学会在当前特定Harness的约束下‘听话’执行。” 原文说“its goal is not to train a universally stronger reasoner, but to align the inherited policy with the execution conventions induced by a particular harness.” 博文比喻“听话”是合理的，不是过度解读。
博文说“不要试图训练一个通用的强Reasoner，而是让Reasoner专门适配当前的Harness。” 原文有类似表述。正确。
博文说“搜索类方法（如AFlow、ADAS）专注于进化外部工作流，训练类方法（如GRPO、RLOO）专注于强化内部策略。” 原文Related Work提到。正确。
博文说“系统首先执行任务并收集轨迹。Meta-Agent会像医生一样进行‘故障归因’，精准定位失败是源于规划、动作还是记忆组件。” 原文有Fault Attribution。正确。
博文说“对于幸存的Harness，系统不重新收集数据，而是直接复用上一阶段评估Harness时产生的成功轨迹。” 原文Sec 3.4。正确。
所以主要问题是数字错误。
另外，博文在“关键结果”部分没有列出具体表格数值，只是概括，所以数字错误只出现在TMDB一处。博文说“API-Bank的API调用准确率平均提升4.96%”，正确。
因此，挑刺第一条就是数字错误。
第二条：博文说“反直觉发现：论文展示了‘兼容性矩阵’（Fig. 4）。最终轮进化出的Harness若搭配早期的Policy，性能仅为71.93%；反之亦然。只有匹配的对才能达到77.19%的峰值。这证明收益并非来自组件绝对强度的提升，而是来自二者之间的特异性兼容。” 这实际上是论文的核心发现，不是反直觉，而是论文明确论证的。但博文用“反直觉”强调，不算错误，但可能有点过度渲染。不过不算严重。
第三条：博文没有提及原文中的“训练数据规模3.8K”和“进化轮数3轮”等具体实验配置，但博文提到了“三轮进化”，所以不算遗漏。博文没有提到“Pareto选择机制”的具体细节，但