# AI Agent红队测试：DTap平台深度拆解

**日期**: 2026-05-11

---

论文 : DecodingTrust-Agent Platform (DTap): A Controllable and Interactive Red-Teaming Platform for AI Agents链接 : https://arxiv.org/abs/2605.04808当前，AI Agent 已经从“聊天机器人”进化为能自主调用工具、操作系统的“数字员工”。但在金融、医疗等高 stakes 领域，这种自主性是一把双刃剑：一旦 Agent 被恶意诱导，后果可能是数据泄露或资金损失。现有的评测集大多基于静态 Prompt 注入，无法模拟真实世界中 Agent 与动态环境交互的复杂性。
这篇论文提出的 DecodingTrust-Agent Platform (DTap) 正是为了解决这个痛点。它不仅是第一个支持多环境、多注入向量（Prompt, Tool, Skill, Environment）的红队测试平台，还引入了一个能自主寻找攻击路径的“红队 Agent”—— DTAP-RED 。
### 为什么现有的红队测试不够用？
以前的 Agent 安全评测（如 AgentDojo, AgentHarm）存在两个致命缺陷：
- 环境太假：大多数评测依赖静态的合成工具输出，或者硬编码的恶意回复。真实的 Agent 是在动态环境中运行的，它们会阅读邮件、查看日历、操作文件系统。静态测试无法捕捉到“上下文依赖”的攻击。
- 攻击维度单一：大多只关注直接 Prompt 注入（Direct Prompt Injection）。但在现实中，攻击者可以通过污染工具描述（Tool Injection）、植入恶意技能（Skill Injection）或在外部环境中埋点（Environment Injection）来绕过防御。
DTap 的核心 Insight 是： 要测出 Agent 的真实安全性，必须在一个完全可控但高度仿真的环境中，模拟真实世界的攻击面。
### DTap 平台：如何构建“可控的真实”？
DTap 平台覆盖了 14 个高风险领域（如金融、CRM、代码、医疗等），构建了 50+ 个仿真环境，包括 Gmail、PayPal、Slack、Windows 文件系统等。
这里的设计非常讲究：
- MCP 接口复刻：它复现了真实世界的 Model Context Protocol (MCP) 接口，确保工具调用的一致性。
- 状态可重置：所有环境都支持确定性状态重置，这意味着同样的攻击可以重复执行，保证评测的可复现性。
- 多向量注入：攻击者不仅可以通过 Prompt 攻击，还可以通过注入恶意邮件（Environment）、篡改工具描述（Tool）、或植入恶意脚本（Skill）来攻击 Agent。
### DTAP-RED：一个会“思考”的红队 Agent光有平台不够，还需要一个聪明的攻击者。论文提出了 DTAP-RED ，这是一个自主红队 Agent，它具备以下关键能力：
- 多步组合攻击：DTAP-RED 不会只发一条恶意 Prompt。它可以组合多种注入向量，例如先在邮件中埋入触发词，再在日历中安排会议，最后通过工具调用执行恶意操作。这种“组合拳”比单一攻击更难被防御。
- 基于环境的验证器（Verifiable Judge）：这是最关键的设计。传统的 LLM-as-a-Judge 容易被欺骗，而 DTAP 直接使用环境状态作为判决依据。例如，判断“数据泄露”是否成功，不是看 Agent 说了什么，而是看敏感数据是否真的被发送到了攻击者指定的端点。这种机制大幅降低了误报率。
- 迭代优化与记忆：DTAP-RED 拥有多层记忆模块，记录成功的攻击轨迹和失败模式。如果一次攻击失败，它会分析原因（如注入未被观察到或被拒绝），并尝试不同的攻击策略或 jailbreak 算法，直到成功。
### 关键实验结果：Agent 到底有多脆弱？
论文在 DTap-Bench（包含 6,682 个任务，覆盖 300+ 风险类别）上对主流 Agent 框架进行了大规模评测。结果令人震惊：
框架/模型 直接威胁模型 ASR 间接威胁模型 ASR 备注 Google ADK - 55.7% 间接攻击下最脆弱 OpenClaw (DeepSeek-V4-Pro) 59.6% - 直接攻击下最脆弱 Claude Code >25.2% >25.2% 最稳健的 Agent，但仍超 25% OpenAI Agents SDK - - 常见“先执行后拒绝”模式注：ASR (Attack Success Rate) 为攻击成功率。数据来源于论文实验部分。
几个值得关注的发现：
- 间接注入更危险：Skill 和 Tool 级别的注入成功率 consistently 高于 Environment 注入。这说明 Agent 对内部化工具的信任度过高，而对外部环境的警惕性不足。
- 组合攻击效果显著：多步组合攻击（如邮件+日历+工具链）的成功率远高于单一注入。
- 开源模型更脆弱：基于开源模型（如 DeepSeek-V4-Pro）的 Agent 在直接威胁模型下表现更差，因为它们更倾向于遵循指令，而难以区分恶意意图。
- Prompt 级防御不足：即使像 Claude Code 这样有较强 Prompt 级防御的 Agent，在面对复杂的组合攻击时，成功率仍超过 25%。这意味着仅靠 System Prompt 无法保障 Agent 安全。
### 工程启示- 不要信任外部输入：Agent 对工具、技能、外部环境的输入应视为不可信。需要在执行层增加沙箱隔离和权限限制。
- 警惕“组合拳”：单一维度的防御（如只过滤 Prompt）是无效的。攻击者可以绕过单一检查点，通过多步、多向量组合达成目标。
- 环境状态验证：在评估 Agent 安全性时，应使用基于环境状态的验证器（Verifiable Judge），而非依赖 LLM 的主观判断。
- 开源模型需加强对齐：如果选择开源模型作为 Agent 底座，需要在指令遵循与安全性之间做更精细的对齐，防止其被恶意诱导执行高危操作。
### 局限与展望DTap 目前主要关注黑盒攻击场景，且依赖仿真环境。虽然仿真环境高度逼真，但可能与真实世界的某些边缘情况存在差异。此外，DTAP-RED 的自动化攻击能力极强，未来可能需要开发更智能的防御 Agent 来对抗这种自动化红队测试。
总的来说，DTap 为 Agent 安全提供了一个全新的评估范式： 从静态 Prompt 测试转向动态环境交互测试 。对于任何在生产环境中部署 Agent 的团队来说，借鉴 DTap 的思路进行内部红队测试，是提升安全性的必经之路。
