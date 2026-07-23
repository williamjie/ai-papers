# Claw-Eval-Live：让 Agent 评估不再纸上谈兵

**日期**: 2026-05-01

---

论文 : Claw-Eval-Live: A Live Agent Benchmark for Evolving Real-World Workflows链接 : https://arxiv.org/abs/2604.28139这篇论文戳中了一个要害： 我们现在的 Agent 评测，可能在测一件根本不存在的东西 。
很多基准测试 freeze 一个任务集，然后看模型最后写了什么。但真实世界里，企业要的从来不是”写一封邮件”，而是”从 CRM 里拉出客户数据，核对财务系统，更新工单，再发邮件通知”。更麻烦的是，这些工作流每个月都在变——今天用 Slack，明天可能换 Teams；这个季度要处理退货，下个季度要合规审计。
Claw-Eval-Live 的核心思路很简单： 评估应该双重接地 。既要接地于”现在 people 真正想自动化什么”（外部需求信号），又要接地于”Agent 实际上做了什么”（可观测的执行证据）。这听起来理所当然，但做起来全是工程魔鬼细节。
## 现有方案到底有多”纸”？
现在的 Agent 基准测试基本是三类：
- 静态任务池：WebArena、OSWorld 一堆人工写的任务，发版就冻结。问题是工作流需求半年就变，你的基准可能 Already 脱离现实。
- 单一表面测试：要么测 web 点击（WebArena），要么测代码生成（HumanEval），要么测 workspace 维修（SWE-bench）。但真实工作流往往是混合的——既要调 API 又要改文件。
- 最终答案评分：看输出文本漂不漂亮。问题是 Agent 可能写了一封完美的邮件，但根本没从数据库拉数据，或者改了错误的文件。
结果就是 ：排行榜刷得飞起，落地一用一个不吱声。
## 方法拆解：信号层与快照层的分离设计Paper 的核心 insight 是 把任务构建分成两层 ：
- 信号层（Signal Layer）：随时间刷新的外部需求信号- 快照层（Snapshot Layer）：固定可复现的发布版本这就像股票指数——指数成分可以调整（信号层），但某个历史时间点的点位是固定的（快照层），这样才能比较不同时间点的表现。
### 从 ClawHub Top-500 到 105 个任务的 pipeline他们用 ClawHub（一个技能平台）的下载量 Top-500 作为 公开需求信号 。注意：信号本身不是任务，只是”这个方向有人用”的指示器。
然后经过 5 个阶段：
信号收集 → 模式聚类 → 家族加权 → 种子展开 → 公共发布选择关键技术直觉 ：
-家族加权（Family Weighting）：不是简单按技能数量分配任务，而是按上游信号质量加权。公式在 Paper Eq. (1)，本质是”哪个方向的热度高，就往那里多放几个任务种子”。
-MILP 子集选择：从 157 个通过 pilot 测试的候选中，用混合整数线性规划选 105 个公开任务。目标函数是最大化 pilot 模型排序的保持度——任务要能区分模型，不能 everyone pass 或 everyone fail。约束是：固定总任务数、保证每个家族至少 1 个、剔除零区分任务。
这个设计很聪明：把”主观选哪些任务上榜单”变成了”优化问题 + 可审计的约束”。
### 执行表面：Service-backed vs Workspace发布的任务分两大类（Table 2）：
- Service-backed workflows（87 任务）：模拟 CRM、财务、邮件、日历等业务系统。要求跨系统检索、协调、状态写入。评分证据：工具调用日志、服务审计日志、与固定 fixture 的对比。
- Workspace repair（18 任务）：终端和本地 workspace 维修。要求检查日志、改文件、跑命令、验证修复。评分证据：命令轨迹、post-run 状态、生成 artifact、测试结果。
关键设计 ：不只看最终输出，要看 整个轨迹 。每个任务都有专属 grader.py，评分从可观测证据出发，只在必要时用结构化 LLM judging（且必须绑定明确的 rubrics）。
## 关键结果：现状比想象中更糟### 整体天花板：没人过 70%Table 3 的排行榜很直观：
排名 模型 Pass Rate Overall 1 Claude Opus 4.6 66.7% 83.6 2 GPT-5.4 63.8% 81.7 3 Claude Sonnet 4.6 61.9% 79.9 13 Doubao Seed 2.0 43.8% 70.4最佳模型 66.7% pass rate，意味着每 3 个任务就有 1 个干不完 。而且 top-3 全是 Claude/OpenAI，国产模型最高 GLM-5 排第 4（61.9%）。
### Service-backed vs Workspace：天壤之别这是最扎眼的数据：
- Workspace repair：所有模型 ≥72.2%，Claude Opus 4.6 接近 100%- Service-backed：最高 Claude Opus 4.6 仅 59.8%，GPT-5.4 56.3%结论 ：当前 Agent 修本地环境已经比较稳，但跨系统业务工作流仍是硬骨头。问题不是”会不会用终端”，而是”会不会在多系统间保持状态、追证据、写对数据”。
### 家族级差异：HR 和管理彻底挂零Figure 4 的热力图按家族分组（7 个分析桶）：
- Development/Terminal：接近满分，Claude 系列 100%- HR/People：惨不忍睹，最高 22.2%，多个模型 0.0%- Productivity：差异最大，Claude Sonnet 4.6 88.0% vs Doubao 48.0%细看家族平均（Paper 文字描述）：
- PRODAPP（产品应用类）：84.2%，但最强最弱差 47.1 个点- HR：平均仅 6.8%- MGMT（管理类）：public pass rule 下全 fail- WORKFLOW（工作流专用）：平均 12.8%这意味着什么 ？招人选人、跨部门协调这类”软任务+硬证据”的混合工作流，当前 Agent 基本搞不定。即使是看似简单的任务，比如”为新员工准备入职材料”，也需要跨 HR 系统、权限服务、文档库，Agent 很容易漏掉某个步骤或引错数据。
### 任务区分度：中间集中，两端崩塌Figure 5 展示了 阈值效应 ：用 public pass rule（τ=0.80）后，105 个任务中：
- 19 个全通过（all-pass）
- 27 个全失败（all-fail）
- 剩下 59 个集中在中间 band，承担区分任务最区分的任务 ：电商月度对账、首次响应时间审计、多文档合并——全是”差一步全盘皆输”的多源提取任务。
最不区分的任务 ：SHELL/W 类维修任务，模型 Already 接近满分。
这说明： 排行榜排名 alone 会骗人 。两个模型 Pass Rate 相近，它们的 Overall Score 和实际完成度可能差很多（Figure 3 的点云分布）。
### 效率 vs 准确率的权衡Table 4 的资源消耗数据很有意思：
- GPT-5.4：最省 token（1.26M）、最快（104 分钟）、成本最低（$6.27）
- Claude Opus 4.6：最贵（$31.61）、最慢（213 分钟）、token 最多（3.32M）
- 国产模型：成本低（0.56−0.56-2.46），但准确率掉档工程启示 ：落地不能只看排行榜。如果你的任务是”e-commerce reconcile”这种硬骨头，该用 Claude 还得用；如果是轻度文档处理，MiniMax 或 DeepSeek 可能更划算。
## 工程启示：你的 Agent 该往哪使力-评估设计要双接地别再用”最终输出 match 度”当唯一指标。至少加上：工具调用序列检查、state 变更验证、post-run artifacts 比对。Paper 里的三种 grading pattern 值得参考：分析任务（evidence+judge）、操作验证（audit-log 为主）、workspace（script-first 全 deterministic）。
-Service-backed 是 next frontier本地维修（terminal/file edit）已经被 Agent 啃得差不多了，下一步的硬仗是跨系统业务工作流。这意味着你的 Agent scaffold 需要：
更强的 long-horizon planning（别干着干着忘了目标）
- 局外的 state tracking（别在 CRM 改了 A 客户，忘掉 B 客户）
- 可审计的执行轨迹（不只是 output，还有”我从哪查的数据”）
-Leaderboard 得看细粒度Pass Rate 告诉你”能不能干完”，Overall Score 告诉你”干成几成”。同分的模型，在 HR 任务上可能一个 0% 一个 20%，这对你的业务场景就是生死之差。
-成本不是次要问题Claude Opus 4.6 比 GPT-5.4 贵 5 倍，只换 3% 的 pass rate 提升。部署前算清楚：你的任务属于哪类家族？ tolerable error rate 是多少？
-基准本身需要”保鲜”
他们计划季度刷新（quarterly refreshes），因为 ClawHub 信号会变。你的内部评估集也得定期从真实工单/ ticket 里抽样更新，否则会训出”过时 Agent”。
## 局限与潜在坑- 信号单一：只依赖 ClawHub Top-500。如果某个工作流在 ClawHub 不流行（比如量化策略回测），它就不会被充分覆盖。
- 任务规模有限：105 个任务，22 个家族。对特定领域（如金融风控）的 coverage 可能不足。
- Judge-model bias：用 GPT-5.4 当 judge，而它自己也是参赛选手。虽然限定在 semantic 维度且基于 trace，但 bias 不可能完全消除。
- 环境简化：服务是模拟的、workspace 是沙箱的。真实系统有网络延迟、权限错误、脏数据——这些在 benchmark 里很难 fully replicate。
## 总结Claw-Eval-Live 的价值不在提出惊天新算法，而在于重新定义”测什么”和”怎么测” 。
它说：别再纸上谈兵了。
你的 Agent 能不能干活，得看它 在真实需求分布下 、 留下可审计轨迹 、 跨系统完成端到端工作流 的本事。
当前结果很清晰：天花板还很低（66.7%），软性任务（HR/管理）是黑洞，service-backed 难度是 workspace 的 2 倍以上。这意味着 Agent 距离”可靠自动化业务”仍有显著差距 ——不是调参能解决的差距，是架构和范式级别的挑战。
对工程团队的建议：如果你的目标是”自动化报销审批”或”跨系统数据同步”，拿这个 benchmark 的前 50 个任务做 internal eval，看看你的 Agent 在 service-backed 上能拿几分。别被 chat ability 骗了，那玩意儿和”干成事”是两码事。
