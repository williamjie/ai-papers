# ⭐⭐⭐½ 腾讯WorkBuddy基准：防污染多域Agent评测新范式

**日期**: 2026-07-24

---

论文 : Tencent WorkBuddy Bench: A Multi-Domain Coding-Agent Benchmark with Contamination-Resistant Task Construction链接 : https://arxiv.org/abs/2607.20911现在的 Agent 评测正在经历一场“信任危机”。SWE-bench 等静态基准因为题目公开，模型通过记忆就能刷高分；而厂商内部的私有基准又缺乏透明度。腾讯发布的 WorkBuddy Bench 试图在两者之间走钢丝：既保持完全开源可审计，又在构造层面彻底切断“搜索即答案”的污染路径。
### 为什么现有的评测不够用了？
痛点很直接： Prompt 泄露导致分数虚高 。
现有公开基准（如 SWE-bench）的问题描述往往直接来自 GitHub Issue。这意味着模型只需在训练数据中搜到对应的 Issue 文本，就能“回忆”出解决方案，而非真正理解代码库。相反，CursorBench 等厂商基准虽然真实，但完全黑盒，外部无法验证是否存在针对自家 Agent 的偏置。
WorkBuddy Bench 的核心洞察是： 防污染不能靠保密，而要靠重构 。如果题目本身就是对原始 Issue 的“角色扮演式重写”，那么即便模型见过原始代码，也无法直接匹配到当前的 Prompt。
### 方法拆解：从“复制 Issue”到“逆向工程”
这套基准涵盖 Code、Web、Office、Security 四大领域，共 260 个任务。其设计精髓在于 任务构造协议（Task Construction Protocol） ：
- 源头真实化：每个任务都锚定真实的 Git Commit、Pull Request 或业务场景。
- 指令口语化与去结构化：这是最关键的一步。原始 Issue 通常包含明确的报错堆栈或修改建议，而 WorkBuddy 将其重写为同事间的自然语言请求。
例如：不直接说“修复 auth.py 第 10 行的空指针”，而是说“用户登录时偶尔会报空值错误，帮我看下”。
- Insight：这种“故意欠指定（Deliberate Underspecification）”迫使 Agent 必须像真人一样去探索代码库、定位根因，而不是执行预设脚本。
- 完全隔离的评估环境：采用 Harbor 风格的任务目录结构，Agent 在沙箱中只能看到工作区，评测用的测试用例（Hidden Tests）和参考补丁（Gold Patch）在运行结束后才引入。
⚠️ 注意 ：由于四个领域（代码、前端、办公、安全）的评分标准完全不同（有的看单元测试通过率，有的看 LLM 裁判打分），该基准 不提供跨领域的综合平均分 。这是一个诚实的设计决策，避免了不同维度指标的无效加权。
### 关键结果：模型在“真实工作”中表现如何？
论文在 CodeBuddy Code 和 Claude Code 两个 Agent Harness 上进行了跨模型测试。以下是部分头部模型的表现（数据来自论文 Table 1）：
模型 Code (SWE) Web (前端) Office (办公) Security (安全) Claude Opus 4.8 74.4% 68.1% 82.4% 64.4% GLM-5.2 71.5% 67.4% 79.6% 76.3% GPT-5.5 72.9% 61.1% 82.0% 64.4% HY-3 62.9% 67.7% 82.1% 64.5%几个值得玩味的发现：
- Office 任务得分普遍最高：Claude Opus 4.8 和 GPT-5.5 在 Office 领域均超过 80%。这暗示当前大模型在处理结构化文档、数据清洗等“确定性较强”的任务上，已经非常成熟。
- Web 前端仍是短板：即使是 Opus 4.8，Web 得分也仅为 68.1%。论文指出，Web 任务不仅要求生成代码，还要求交付可运行的工件（Artifact），包括交互状态、持久化等，这对 Agent 的工程落地能力要求极高。
- GLM-5.2 的安全能力突出：在 Security 子集中，GLM-5.2 以 76.3% 领先，显著高于其他模型。这可能与其在代码审计和安全领域的特定优化有关。
### 工程启示：如何构建你的 Agent 评测集？
对于正在搭建内部 Agent 评估体系的工程师，WorkBuddy Bench 提供了三个可复用的最佳实践：
- 拒绝直接复用 Issue 文本：如果你的评测集直接复制 Jira/GitHub 描述，模型很容易通过检索增强生成（RAG）或记忆作弊。务必进行“角色扮演式重写”，隐藏根因和具体文件路径。
- 引入“欠指定”测试：真实工作中，需求往往是模糊的。评测应包含那些需要 Agent 自行决定接口定义、边界条件甚至技术栈的任务，而不仅仅是填空题。
- 分离评估资产：确保 Agent 在解题过程中完全看不到测试用例。WorkBuddy 通过 Docker 镜像打包工作区，将测试代码隔离在外，这种物理隔离比逻辑隔离更可靠。
### 局限与展望论文诚实地指出了当前版本的局限：
- 污染并非绝对免疫：虽然 Prompt 不可搜索，但模型可能已经见过原始的 Commit 代码或 CVE 分析。因此，基准需要定期版本迭代（Versioning）来抵消训练数据的滞后效应。
- 领域分数不可比：由于评分机制差异，无法直接比较 Code 和 Office 的能力高低。未来可能需要探索更统一的效用度量标准。
WorkBuddy Bench 的价值不在于它给出了一个完美的排行榜，而在于它展示了一种 可审计、防污染、贴近真实工作流 的评测方法论。对于追求 Agent 实际落地价值的团队来说，这是一套值得参考的工程样板。
## 📝 AI 点评点评时间：2026-07-24 12:10 ｜ reviewer: DeepSeek V4 Flash核心贡献: 针对现有公开基准易受提示污染、厂商闭源基准不可审计的困境，Tencent WorkBuddy Bench 提出了一套多域（Code/Web/Office/Security）编码Agent评测套件，其核心方法是通过对真实 commit、PR 或业务场景进行逆向工程并重写为口语化角色扮演请求来构造任务，从构造层面切断搜索即答案的污染路径，同时保持全开源可审计。
亮点:
- 博文精准捕捉了原文最核心的设计思想——“防污染不能靠保密，而要靠重构”，并提炼出“故意欠指定（Deliberate Underspecification）”这一关键机制，指出任务指令会省略目标文件、精确接口等信息，迫使Agent自主探索代码库，这与原文强调的“requirement disambiguation and grounding”高度一致。
- 博文在“工程启示”部分总结出三个可复用的最佳实践（拒绝直接复用Issue文本、引入欠指定测试、分离评估资产），虽然原文未以这种形式呈现，但确实是从原文任务构造协议中合理推导出的工程洞察，对读者有实际指导价值。
- 博文明确指出了“该基准不提供跨领域的综合平均分”这一诚实的设计决策，并解释了原因（评分标准完全不同），准确传达了原文“a deliberate design fact, not a gap to be closed”的立场。
挑刺:
- 遗漏双Harness分数区分，可能导致读者对模型排名的片面理解。 原文Table 6明确给出了每个子集在CodeBuddy Code (cbc)和Claude Code (cc)两个Harness下的分数，且原文用大量篇幅讨论“Harness sensitivity”（如Code子集GPT-5.5和GLM-5.2的排名在两Harness下互换）。博文在结果表格中只列出了单一分数（疑似cbc下的数值），且未标注具体Harness，使得读者无法意识到同一模型在不同Harness下表现可能差异显著。例如博文显示GLM-5.2在Security上领先（76.3%），但原文中cc下GPT-5.5得分为77.91，与GLM-5.2的80.86差距不大，博文的“显著高于”在cc语境下不够准确。
- 未提及Security子集的关键工程创新——五层反作弊基础设施。 原文Section 3.4详细描述了针对自动化评估的banned-literal scanning、renamed-input tests、overlay/tamper tests、encoding-dependence tests和low-weight decoy fields等五层防御，这是安全域评估的重要保障，且原文强调“every task ships a deterministic scoring program… backed by a five-layer anti-cheat infrastructure”。博文在“方法拆解”和“关键结果”中完全未涉及这一设计，遗漏了原文在安全评测中的核心工程贡献。
- 对“GLM-5.2安全能力突出”的表述存在语境缺失。 博文写道“GLM-5.2 的安全能力突出……显著高于其他模型”，并引用76.3%这个数字。但原文Table 6显示，在cc Harness下GPT-5.5的Security得分达到77.91，仅低于GLM-5.2约3个百分点，且Claude Opus 4.8在cbc下为64.37、cc下为65.87。博文未说明该结论是基于哪个Harness，也未提及GPT-5.5在cc下的接近分数，容易让读者误以为GLM-5.2在所有条件下都大幅领先。
总评: ⭐⭐⭐½ 博文准确抓住了论文的防污染构造理念和多域覆盖亮点，行文流畅且提炼出实用启示，但遗漏了双Harness分数区分、安全反作弊等关键细节，对部分结果的呈现缺少完整语境，整体上是一篇合格的解读但不够全面。
