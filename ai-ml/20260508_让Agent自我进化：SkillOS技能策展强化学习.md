# 让Agent自我进化：SkillOS技能策展强化学习

**日期**: 2026-05-08

---

论文 : SkillOS: Learning Skill Curation for Self-Evolving Agents链接 : https://arxiv.org/abs/2605.06614现在的LLM Agent大多还是“一次性用品”，做完一个任务就忘了下一个。虽然有了记忆模块，但大多依赖人工筛选或启发式规则，导致技能库要么臃肿无用，要么更新滞后。 SkillOS 的核心价值在于：它不再把技能管理看作静态存储，而是将其转化为一个可学习的 强化学习（Reinforcement Learning, RL）问题 。通过训练一个专门的“技能策展人（Skill Curator）”，让Agent在长期流式任务中自动实现技能的插入、更新和删除。
### 痛点：为什么现有的记忆方案不够用？
在流式任务（Streaming Tasks）场景中，Agent需要不断从过往交互中提取经验。现有方案主要卡在两个瓶颈：
- 人工策展不可扩展：如Anthropic的Skills，依赖人类专家编写，无法应对海量异构任务。
- 启发式规则缺乏反馈：现有的自动记忆管理多基于固定规则（如基于相似度插入），缺乏对“该技能是否真的对后续任务有帮助”这一长期结果的感知。
简言之，现有方法要么太贵（人工），要么太笨（无反馈）。SkillOS试图解决的核心问题是： 如何利用间接且延迟的环境反馈，训练出复杂的长期策展策略？
### 方法拆解：冻结执行者，训练策展人SkillOS采用了一种解耦的模块化设计，直觉非常清晰： 让擅长推理的模型专心干活，让擅长管理的模型专心整理。
#### 1. 架构解耦- Agent Executor（执行者）：这是被冻结的模型（如Qwen3-8B），负责根据检索到的技能执行具体任务。它不参与学习，保证推理环境的稳定性。
- Skill Curator（策展人）：这是可训练的模型（也是Qwen3-8B），负责观察执行轨迹，并决定如何修改外部的 SkillRepo。它通过函数调用（Function Calls）执行三种操作：insert_skill（插入）、update_skill（更新）、delete_skill（删除）。
#### 2. 核心Insight：任务分组与复合奖励这是SkillOS最精彩的设计。如果让策展人在单个任务后立刻优化，信号太稀疏且短视。SkillOS引入了 任务分组（Task Grouping） ：
- 分组机制：将具有技能依赖关系的任务聚在一起。策展人在前几个任务中更新 SkillRepo，后续相关任务使用这些更新后的技能进行推理。
- 长程反馈：策展人的决策质量，由后续任务的成功率来评判。这解决了“延迟反馈”问题，让策展人明白“我现在删掉这个旧技能，是因为它能提升后面三个任务的效率”。
为了引导策展人行为，作者设计了 复合奖励函数（Composite Reward） ：
r=rtask+λfrfc+λurcnt+λcrcompr = r_{task} + \lambda_f r_{fc} + \lambda_u r_{cnt} + \lambda_c r_{comp} r t a s k ​ + λ f ​ r f c ​ + λ u ​ r c n t ​ + λ c ​ r co m p ​- rtaskr_{task}​：任务结果奖励。后续相关任务的成功率，提供主要的性能信号。
- rfcr_{fc}​：函数调用有效性。确保策展人输出的插入/更新指令语法正确。
- rcntr_{cnt}​：内容质量。使用外部Judge模型评估技能语义的有效性。
- rcompr_{comp}​：压缩奖励。惩罚直接复制原始轨迹，鼓励提炼精简的技能描述。
这种设计迫使策展人不仅要把技能“存下来”，还要“存得精”、“存得对”。
### 关键结果：小模型也能打败大模型？
实验在ALFWorld、WebShop及推理任务上进行。最惊人的发现来自Table 1和Table 2的数据对比：
基准测试 基线方法 (Memory-based) SkillOS (Qwen3-8B Curator) 提升幅度 ALFWorld SR ReasoningBank: 55.7% 61.2% +5.5% ALFWorld Steps ReasoningBank: 8.8 steps 6.4 steps -2.4 steps WebShop Score ReasoningBank: 35.4 40.6 +5.2 AIME25 Acc ReasoningBank: 69.6% 73.8% +4.2%更值得工程师关注的是 效率与规模的对比 ：
- 以弱胜强：SkillOS训练的8B策展人，性能甚至超过了直接使用 Gemini-2.5-Pro（顶级大模型）作为策展人的基线（SkillOS-gemini）。在ALFWorld上，Qwen3-8B策展人配合Qwen3-8B执行者，SR达到46.7%，而Gemini-2.5-Pro策展人仅36.0%。
- 通用性：训练好的策展人可以跨Executor泛化。当搭配更强的Gemini-2.5-Pro执行者时，SkillOS的SR进一步提升至80.2%（Table 1）。
这说明： 经过针对性RL训练的较小模型，其策展能力优于直接调用强大模型的零样本能力。 强推理能力不等于好的管理能力。
### 工程启示- 技能即代码（Skills as Code）：SkillOS使用Markdown格式存储技能，包含YAML头部和具体工作流。这种结构化、可编辑的格式比非结构化的向量记忆更利于Agent理解和复用。
- 策展与执行分离：在构建长期运行的Agent系统时，不要试图让同一个模型既思考又整理记忆。分离出专门的“记忆管理模块”并通过RL优化，能显著提升系统的长期稳定性。
- 分组训练的重要性：在RLHF/RLAIF场景中，如果反馈信号稀疏，务必构造“任务流”或“分组”，让早期决策的影响能在后续步骤中被观测到。
### 局限与展望SkillOS目前主要依赖BM25进行技能检索，可能在高维语义匹配上存在瓶颈。此外，分析显示，从推理任务学到的技能向具身任务（如ALFWorld）迁移时效果较好，但反之则较弱，暗示了不同领域技能抽象层级的差异。未来如何进一步自动化技能的分层与元技能（Meta-skills）发现，将是提升Agent自我进化能力的关键。
