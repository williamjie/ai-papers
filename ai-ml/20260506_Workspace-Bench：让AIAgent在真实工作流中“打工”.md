# Workspace-Bench：让AI Agent在真实工作流中“打工”

**日期**: 2026-05-06

---

论文 : Workspace-Bench 1.0: Benchmarking AI Agents on Workspace Tasks with Large-Scale File Dependencies链接 : https://arxiv.org/abs/2605.03596现在的AI Agent评测，很多时候像是在考“开卷考试”：题目把材料直接喂到嘴边，Agent只要会调用工具就能拿高分。但在真实职场中，老板给你的往往是一堆散乱的文件、混乱的目录和模糊的需求。这篇论文提出的 Workspace-Bench 1.0 ，正是为了解决这个巨大的“最后一公里”鸿沟：它不再评估Agent在干净沙箱里的表现，而是把它们扔进一个包含20,476个文件、74种格式、充满噪声和隐式依赖的真实“数字工位”里，看看它们到底能不能干活。
### 现有评测的“虚假繁荣”
为什么需要这个Benchmark？因为现有的评测体系严重脱离实际。
- Prompt-Driven类（如OneMillion-Bench）：所有信息都在Prompt里，Agent不需要处理文件系统，直接考逻辑推理。
- Open-Source/Environment-Driven类（如OSWorld）：考的是GUI操作或API调用，但缺乏对本地文件生态中复杂依赖关系的评估。
- Task-File-Driven类（如OfficeQA-Pro）：虽然给了文件，但通常是针对单个任务打包好的“小礼包”，Agent不需要在海量文件中“大海捞针”，更像是在做文档QA。
真实的工作场景是：你需要从几十个层级的目录中，找到半年前的一份Excel源数据，结合几封邮件中的上下文，还要区分哪个是最终版（Lineage Tracing），最后生成一份跨部门的报告。现有的Benchmark几乎都忽略了 File Lineage Relations（文件血缘关系） 和 Semantic Content Relations（语义内容关系） 这两个核心痛点。
### Workspace-Bench 的核心设计：模拟“混乱”的真实工位Workspace-Bench 的聪明之处不在于用了多新的模型，而在于它构建了一个高度拟真的**Workspace Learning（工作区学习）**环境。
1. 五类真实用户画像它没有搞单一的测试集，而是构建了5种典型角色的数字工作区：运营经理、物流经理、产品经理、后端开发和研究人员。每个工作区都是一个独立的、自包含的数字环境，包含数千个文件。例如，研究人员的工作区包含11,020个文件，分布在2,059个目录中；而产品经理的工作区则相对紧凑，有1,379个文件。这种设计迫使Agent必须具备**角色感知（Role-Play）**能力，理解不同角色的文件组织习惯。
2. 74种异构文件格式现实中的工位不只有PDF和Word。Workspace-Bench 包含了从 .xlsx , .csv 到 .eml (邮件), .dat (统计数据), 甚至代码文件 .java , .py 等74种格式。这要求Agent不仅要是“文本处理器”，还得是“多模态解析器”。
3. 显式的依赖图与细粒度Rubrics这是该方法最硬核的部分。每个任务都配有一个 File Dependency Graph（文件依赖图） 。
- 传统评测：只看最终输出对不对。
- Workspace-Bench：评估过程。Agent是否找到了正确的源文件？是否使用了正确的版本（比如 report_v1 vs report_final）？是否忽略了必要的上下文文件？
- 每个任务平均有19.1个评估点（Rubrics），总计7,399个评估项。这种细粒度的评估能精准定位Agent是“猜对了”还是“真懂了”。
### 关键结果：Agent还没学会“打工”
评测了4种Agent Harness（ClaudeCode, DeepAgent, Hermes, OpenClaw）和7个基础模型（包括Opus-4.7, MiniMax-M2.7等），结果并不乐观。
模型/Harness组合 表现描述 最佳组合 (OpenClaw + Claude-Opus 4.7) 仅达到 68.7% 的Rubrics通过率，仍低于人类基准的 80.7% 。 平均表现 所有配置的加权平均通过率仅为 47.4% 。 开源方案困境 如 DeepAgent + MiniMax-M2.7，不仅成功率低（平均45%），还存在严重的“成本爆炸”，每个任务消耗高达58.1次交互轮次和0.61M tokens。
更细致的能力拆解显示：
- Workspace Exploration（工作区探索） 是最基础但也最耗时的能力，67.5%的任务涉及此能力。
- Lineage Tracing（血缘追踪） 和 Semantic Heterogeneous File Understanding（异构文件语义理解） 是主要的瓶颈，这也是Hard难度任务的主要特征。
- 随着任务难度从Easy到Hard，表现从57.6%骤降至40.5%。
### 工程启示- RAG不够用，需要“文件系统意识”：现有的RAG方案通常将文档切块为扁平的向量，忽略了文件的层级结构和版本关系。在Workspace-Bench中，Agent必须理解 src/ 和 docs/ 的语义区别，以及 v1 到 final 的演进路径。未来的Agent架构需要引入更结构化的记忆机制，而非单纯的向量检索。
- Harness的选择至关重要：对于弱模型（如MiniMax-M2.7），强大的Harness（如OpenClaw）能带来显著的性能提升；但对于强模型，Harness的提升边际效应递减。这意味着在资源受限场景下，优化Agent的执行策略（减少无效的文件读取和工具调用）比单纯堆砌模型更重要。
- 人类协作仍是王道：论文指出，Human + Tools (80.7%) 显著优于 Fully Autonomous (68.7%)。在涉及复杂跨文件依赖的任务中，完全自动化的Agent仍容易遗漏关键约束或引用过期文件。当前的最佳实践应是“Agent起草 + 人类审核关键依赖”。
### 局限与展望Workspace-Bench 虽然逼真，但毕竟是“模拟”的真实。文件内容虽由真实数据驱动，但部分任务场景仍经过人工简化。此外，74种文件格式的解析能力目前仍受限于基础模型的多模态理解上限。未来，随着多模态大模型对非文本文件（如图片、视频、复杂Excel公式）理解的提升，以及Agent在长程规划中对“文件血缘”建模能力的加强，我们可能会看到更接近人类水平的Workspace Agents。
