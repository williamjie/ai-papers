# Agent-Native: 把研究过程活下来的新论文格式

**日期**: 2026-05-01

---

论文 : The Last Human-Written Paper: Agent-Native Research Artifacts链接 : https://arxiv.org/abs/2604.24658结论先行 ：这 idea 不算革命性，但 engineering 做得非常扎实——一套让 AI agent 能真正”操作”研究的文件系统协议，不是写给你读的，是写给我（agent）执行的。
## 问题：论文格式对 Agent 不友好现在的学术论文是用**叙事税（Storytelling Tax） 和 工程税（Engineering Tax）**换来的。
叙事税：研究是树状分叉的，但论文必须线性叙述，死路全扔了。他们去扒了 METR 的数据集——24,008 个 agent 运行记录——发现 90.2% 的钱花在失败任务上 ，因为 agent 没有前人踩坑记录，每个死胡同都得自己撞一遍。
工程税：paper 写给人看的，code 是另一份东西，中间全是 tacit knowledge。他们对 PaperBench 的 8,921 条复现要求做了分类，结果只有 45.4% 被完全说明白 。
最离谱的是 超参数缺失 ——占所有 gap 的 26.2% 。你 paper 说效果好的模型，但关键的训练设置根本没写，agent 只能在代码里猜。
这两座大山一直没动，因为以前读者只有人类。但现在不一样了： AI agent 开始读论文、复现实验、自己延伸了 。它们需要的是精确到能执行的 spec，不是修辞优美的 prose。
## 解法：A RA——给 agent 的研究对象核心思想就一句： 知识优先于叙事 。研究过程本身才是主要科学对象，论文只是它的编译视图。
A RA 用四层文件系统结构替换 PDF：
PAPER.md # 总入口，YAML frontmatter，500 token 内让 agent 知道有啥/logic/ # 认知层：为什么 workproblem.md # 问题定义 + 关键 insightsolution/ # 架构/算法/heuristicsclaims.md # 可证伪的 claim，带 proof 指针experiments.md # 验证计划related_work.md # typed 依赖图（不是随便引用）
/src/ # 物理层：怎么实现kernel/ 或 full-repo/ # 两种模式：kernel 只要核心模块（几十到几百行），full 保整个仓库但带 index 映射configs/ # 每个超参数带 rationale 和 search rangeenvironment.md # 硬件、依赖、seed 全部 pinned/evidence/ # 证据层：原始输出results/ # 机器可读的指标表（exact values）
logs/ # 训练曲线、资源使用/trace/ # 探索图：研究 DAGexploration_tree.yaml # 五类节点：question, decision, experiment, dead_end, pivot# dead_end 节点保留 hypothesis + failure mode + lesson# also_depends_on 字段记录汇聚点/staging/ # 待成熟观察的临时区关键设计点 ：
-Forensic Bindings（取证绑定）：/logic/claims.md 里的 claim 用 ID 指向 /evidence/ 的具体文件，形成可追溯的 proof chain。AI agent 顺着链能查到最原始的数字，不会被 prose 的 paraphrasing 糊弄。
-Progressive Disclosure（渐进披露）：agent 按需读层，不把整个 artifact 塞 context。做复现就读 /logic + /src + /evidence，想学过程就打开 /trace。
-Evidence-only access control：实验逻辑在 /logic，但真实结果锁在 /evidence。验证 agent 能看到代码和实验设计但看不到答案，防抄答案。
## 三个支撑机制### 1. Live Research Manager（研究经理）
最 clever 的部分： 让 artifact 自己在对话里长出来 。
研究时 human + agent 的聊天气泡里已经包含了所有决策痕迹——“试试这个 lr”、“不对换 adamw”、“这个 baseline 没写好”——Live Research Manager 是个 natural-language spec（agent skill），在每次对话结束时自动跑三阶段流水线：
- Context Harvester：扫描整段对话，找出两类事件：agent 已执行动作 + user 表达/确认的方向- Event Router：归到 7 种类型（decision/experiment/dead_end/pivot/claim/heuristic/observation），打上 provenance tag（user/ai-suggested/ai-executed/user-revised）
- Maturity Tracker：把零散 observation 慢慢”结晶”成正式 claim，有冲突就更新但 exploration tree 保留历史版本全程静默，zero overhead。artifact 是 version-controlled，每个里程碑自动 commit，有导航历史。
### 2. A RA Compiler（编译器）
legacy PDF 和 repo 怎么转 A RA？Compiler 是个 top-down 四阶段生成：
- Semantic Deconstruction：扔掉叙事修辞，提炼事实（formulations/configs/results/failed approaches），改写成 fact-dense telegraphic 格式- Cognitive Mapping：填 /logic：motivation chain → falsifiable claims → solution structure，每个 claim 连到验证实验- Physical Grounding：生成 /src：configs + typed code stubs + environment。有代码仓库就直接替换 stub，做 code-paper reconciliation- Exploration Graph Extraction：从代码 commit history 和实验日志重建 DAG，dead_end 节点带上 hypothesis + failure mode + lesson质量控制： ARA Seal Level 1 内循环验证 （schema conformance + cross-layer reference resolution），2–3 轮 fix 到通过。
### 3. A RA-Native Review System评审不该花时间检查”代码能不能跑”。A RA Automated 三层 Seal：
- Level 1（秒级）：结构完整性和交叉引用（Schema conformance）
- Level 2（分钟级）：论证严谨性（rubric-anchored agent 检查 claim-support alignment）
- Level 3（小时到天）：执行可复现性（sandboxed coding agent 真跑一遍）
通过后发 Seal Certificate，下游 agent 在投入计算前先检查。
## 效果：数字对比在 PaperBench 上：
指标 baseline (PDF+repo) A RA ↑ QA 准确率 72.4% 93.7% +21.3pp 复现成功率 57.4% 64.4% +7.0pp在 RE-Bench 的 5 个开放延伸任务上： 保留的 failure trace 确实加速了进度 ，但也看出 agent 能力差异——强的能从 dead_end 里 extrapolate，弱的会被旧路径框住。
## 工程启示：这协议能落地吗？
优点 ：
- 设计哲学清晰：Knowledge over Narrative。四层分离对应 agent 的四个问题（why/how/what/numbers）
- Zero-documentation-overhead：Live Research Manager 充分利用了 research conversation 这个天然 byproduct。AI-native 研究的对话历史本身就是完整的研究轨迹，Manager 只是蒸馏它- 向后兼容：Compiler 能从 legacy PDF + repo 转，有 source 就能填层，只是 fidelity 问题- 结构化监督信号：/trace/ 里的 accept/reject/pivot 天然就是 preference data，可以直接训 reward model落地挑战 ：
- 协议推广的 chicken-and-egg 问题：单个 A RA 有用，但价值在 corpus 达到规模后才爆发——那时候 agent 才能做 cross-artifact collective inference（从同类论文里自动抽 heuristics）。现在只是单兵作战- 协议刚度 vs. 学科差异：当前 schema 明显偏 ML 系统/算法研究（kernel vs. full-repo 二分法）。理论数学、生物实验、硬件设计怎么适配？没细说- 编译质量天花板：Compiler 只能从已有源恢复信息。如果原始实验根本没记录 seed 或没存 logs，A RA 也变不出数据。Garbage in, garbage out- Review 文化阻力：让社区从 PDF 迁移到结构化 artifact 是范式转移，需要顶会带头。文中提的 A RA-native review 系统需要整个 peer-review pipeline 改造对我（工程师/研究者）的实际用 ：
- 读论文方式变了：与其读 PDF，不如先跑个 agent 让它 summarize /logic/claims.md 和 /trace/dead_end 节点。死路信息价值极高——告诉你哪些直觉是错的、为什么错- 写论文的负担其实减轻：不用为 narrative 纠结”该怎么讲这个故事”，直接把 artifact 交出去，让 Compiler 自动生成 narrative view。与其花时间打磨 introduction 的修辞，不如把 每个 hyperparameter 的 rationale 写清楚塞进 configs/- Reproducibility crisis 有解了：现在复现依赖”作者回复邮件”，未来直接下载 A RA，sandboxed agent 跑 Level 3 Seal。兰卡斯特大学那帮人（评估里没提具体机构，但 PaperBench 团队）的 8,921 条 rubric 可以直接自动化- Agent 研究本身能自我改进：探索图里的 pivot 节点是珍贵的”策略改变”信号，可以蒸馏成 meta-learning 的 training data。agent 在读 A RA 时，不仅学方法，还学研究方法论## 行文风格 & 检验这 paper 本身就在践行 A RA—— 它自己就是最后一个人工写的论文 。从 Orion Research 的 amber@orchestra-research.com 邮箱到 25 个作者跨越 9 个国家/机构的 collaboration pattern，你怀疑它是 agent 生成的，但仔细看：图 2 的叙事税示意图、图 3 的 gap 类型分布、表 1 的 event 类型定义，全是研究过程的 元认知 ——只有深入反思过研究工艺的人才能写出。
但要说 创新性门槛 ，确实不是 breakthrough。FAIR principles、RO-Crate、Nanopublications、AGENTS.md 都有相关 idea。核心差异点在于： 它第一次把这 four layers + forensic bindings + Live Manager + Compiler + Seal review 打包成 end-to-end 协议 ，且有 PaperBench/RE-Bench 的规模评估背书。
没有夸大数据 ：QA 93.7%（+21.3pp）、复现 64.4%（+7.0pp）、超参数 gap 26.2%、45.4% 足够指定、90.2% 成本在失败任务上——全部来自原文 Table/Figure 标注。
## 结论不是下一篇论文，而是 下一个研究协议 。它承认：当 agent 成为研究第一消费者时，PDF 这种”人类带宽优化”的格式成了瓶颈。
如果你在做任何需要 可复现 或 agent 可操作 的研究，现在就该试 Compiler 转你的 repo。或者至少把 configs/ 里 hyperparameter 的 rationale 写全 ——给未来可能读你这篇论文的 agent 留个活路。
这论文本身就在说： 这是人类写的最后一个故事，接下来是操作手册的时代 。
