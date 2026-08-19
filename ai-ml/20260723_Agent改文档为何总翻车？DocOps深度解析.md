# ⭐⭐⭐½ Agent 改文档为何总翻车？DocOps 深度解析

**日期**: 2026-07-23

---

论文 : DocOps: A Verifiable Benchmark for Complex Document Operations链接 : https://arxiv.org/abs/2607.19865如果你指望现在的 AI Agent 能像人类一样，精准地修改 Excel 公式、调整 PPT 层级且不破坏文件结构，DocOps 这篇论文可能会让你“清醒”一下。
它揭示了一个残酷现实：即便是最顶尖的模型，在处理复杂文档操作时，成功率也远低于我们的预期。
### 现有评测的盲区目前的文档评测基准主要分两类，但都存在明显缺陷。
一类是静态框架（如 DocBench），只把文档当作只读的知识库，考的是信息提取或问答。另一类是工作流导向（如 OfficeBench），关注软件导航和流程编排，却把文档本身视为被动传输的数据载荷。
这两者都忽略了一个核心痛点： 文档是一个具有状态的第一类计算对象 。
在实际工作中，Agent 需要主动且连续地操纵文档内容、格式和结构，同时保证文件在修改后依然保持结构有效和功能完整。现有的评测无法回答：Agent 能否在执行端到端任务时，维持全局文档状态的一致性？
### DocOps 的核心设计直觉DocOps 的设计核心在于 确定性验证（Deterministic Verification） 与 分层复杂度 。
它不再依赖 LLM-as-a-Judge 这种主观且宽松的评价方式，而是通过原生文档库直接检查输出文件。每个任务包含三类谓词：
- 结构谓词：验证底层原生状态（如可执行公式、大纲层级），检测渲染输出中不可见的结构损坏。
- 语言锚点：验证所需文本内容，允许合理的语言变体。
- 保留谓词：检查指定范围外的元素（如受保护的样式、未修改的隐藏表格）是否保持原样。
这种设计强制 Agent 不仅要“做对”，还要“不破坏”。
### 实验结果：顶尖模型也只在及格线徘徊论文评估了包括 GPT-5.5、Claude Sonnet 4.6 以及多个开源模型在内的主流配置。数据令人咋舌：
- 最高成功率仅为 0.671：即便是最强的配置（GPT-5.5 + Codex + Skills），整体通过率也只有 67.1%。
- 复杂度导致性能断崖式下跌：在 L1/L2 级别的局部编辑任务中，模型表现尚可；但一旦进入 L3（单文档工作流）和 L4（跨文档工作流），成功率急剧下降。GPT-5.5 从 L1 的 0.725 跌至 L4 的 0.237。
- Excel 是重灾区：由于公式引用和数据验证边界的强耦合性，Excel 工作流在复杂任务中的成功率接近于零。相比之下，PDF 等低耦合格式的表现相对稳健。
模型/配置 整体通过率 (Pass Rate) 备注 GPT-5.5 + Codex + Skill 0.671 当前最高纪录 GPT-5.4 + Codex + Skill 0.648 Claude Sonnet 4.6 + Claude Code 0.552 无 Skill 配置下表现优异 DeepSeek-V4-Pro (Avg) ~0.35 开源模型代表⚠️ 反直觉发现 ：技能注入（Skill Injection）并不总是有益的。在某些情况下，过于僵化的程序化指导反而限制了模型的适应能力，导致性能下降。例如，Qwen3.6-27B 在 Codex 环境下加入 Skill 后，通过率反而下降了 3.8%。
### 三大失败模式：Agent 到底在哪翻车？
通过细粒度分析，论文归纳了 Agent 失败的三个主要模式：
- 长期状态跟踪崩溃（Long-term state tracking collapse）：Agent 能完成局部编辑，但在全局文档状态上“迷路”。例如，修改 PDF 页面时丢失了书签顺序或页码映射。
- 浅层语义验证（Shallow semantic verification）：Agent 接受表面看似合理的输出，却未检查底层计算或结构语义。比如，Excel 单元格显示了正确的数值，但背后的公式是错误的或被静态值替代。
- 破坏性编辑（Destructive editing）：模型倾向于将复杂的对象树降级为扁平文本，或不可逆地破坏公式、表格和结构元数据。
### 对工程实践的启示这篇论文给正在构建文档 Agent 的工程师们提了个醒：
- Harness 比 Model 更重要：开放式的编程环境（如 Codex, Terminus-2）通常优于静态 RPC 工具调用。文件系统反馈和脚本执行能力是处理复杂文档状态的关键。
- 不要迷信 Skill：对于具备零样本编排能力的顶尖模型，显式的 Skill 指导收益边际递减，甚至可能成为束缚。对于中等开源模型，Skill 则是重要的催化剂。
- 验证机制必须原生化：如果你的 Agent 要处理企业级文档，不能只看“文件能打开”，必须编写针对公式、层级、样式保留的确定性校验代码。
DocOps 不仅是一个基准，更是一份诊断报告。它告诉我们，当前的 Agent 离“可靠”还有很长的路要走，特别是在维护全局一致性和避免破坏性修改方面。未来的方向不是简单的工具调用，而是构建具备状态感知能力的非破坏性 Agent。
## 📝 AI 点评点评时间：2026-07-23 17:05 ｜ reviewer: DeepSeek V4 Flash核心贡献:
DocOps 提出了一个确定性可验证的评估框架，通过两轴分层分类法（操作轴：内容/格式/结构；难度轴：L1–L4）和三类谓词（结构、语言锚点、保留）的确定性验证器，系统评估 LLM 智能体在端到端原生文档操作中的能力，并识别出长期状态跟踪崩溃、浅层语义验证、破坏性编辑三种关键失败模式。
亮点:
- 博文准确提炼了原文“确定性验证”的设计核心（三类谓词）和“分层复杂度”的实验设计，并抓住了“最高成功率仅 0.671”这一关键数据，直观反映了当前 Agent 的局限。
- 对三大失败模式的归纳（长期状态跟踪崩溃、浅层语义验证、破坏性编辑）与原文一致，并用通俗例子（Excel 公式、PDF 页面顺序）帮助读者理解。
- 博文突出了“技能注入并不总有益”和“Harness 比 Model 更重要”的工程启示，这些是原文中有实际指导价值的发现。
挑刺:
-过度简化“Harness 比 Model 更重要”
博文在“对工程实践的启示”第一条写道：“Harness 比 Model 更重要”。原文强调的是两者相互作用：“performance is shaped by the interaction between model capability and execution framework”（Section 4.2.4），并指出“Harness effectiveness depends strongly on the paired model”。博文的表述过度简化，可能误导读者忽略模型能力的基础作用。
-遗漏关键约束：任务规模与人工审核成本博文未提及原文在“Limitations”中明确指出的限制：“DocOps currently contains 210 tasks… scaling the benchmark is substantially more labor-intensive than collecting read-only document examples”（Section Limitations）。这一约束对理解基准的扩展性和实用性至关重要，博文完全省略。
-“确定性验证”描述中术语不精确博文说“不再依赖 LLM-as-a-Judge 这种主观且宽松的评价方式”。原文并未直接提及“LLM-as-a-Judge”，而是说“deterministic artifact-level design is intended to reduce overly lenient evaluation”（Section 1）。将“overly lenient evaluation”等同于“LLM-as-a-Judge”属于过度引申，且原文在 Related Work 中明确对比的是“round-trip reconstruction or LLM-as-a-judge evaluation”（Table 1 注释），但博文将此作为 DocOps 的独有特点，表述不够严谨。
总评: ⭐⭐⭐½博文整体准确地传达了 DocOps 的核心发现和工程启示，但在“Harness vs Model”关系上存在过度简化，并遗漏了关键的任务规模约束。作为一篇技术博客，它成功吸引了读者对文档 Agent 失败模式的关注，但细节严谨性略逊于原文。
