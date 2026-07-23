# ⭐⭐⭐½ Agent社会的操作系统：Foundation Protocol拆解

**日期**: 2026-05-26

---

论文 : Foundation Protocol: A Coordination Layer for Agentic Society链接 : https://arxiv.org/abs/2605.23218Agent 正在从“工具”演变为“社会基础设施”。当 Agent 开始自主浏览、购买、部署软件并相互协作时，瓶颈不再是模型本身的智能上限，而是 协调成本 。这篇来自 FoundationAgents 团队的论文提出了一套名为 Foundation Protocol (FP) 的图原生协调层，旨在解决异构实体（Agent、工具、人类、机构）之间的身份、权限、经济结算和审计问题。
### 为什么现在的协议不够用？
目前的 Agent 生态充斥着碎片化的协议：
- MCP 解决了模型与工具的接口；- A2A 定义了 Agent 间的任务协作；- DIDComm 处理安全消息；- UCP 关注商业交易。
痛点在于： 单一工作流往往跨越多个边界 。一个复杂的任务可能同时涉及工具调用、Agent 委托、UI 控制、身份验证和支付结算。当每个协议都有自己独立的身份定义、会话状态和日志格式时，集成成本极高，且 溯源（Provenance）在协议边界处断裂 。这导致 oversight 变成补丁式的日志拼接，难以审计。
### 核心 Insight：图原生与渐进式披露FP 的核心直觉是： Agent 社会本质上是一个动态图 。
- 节点：Agent、工具、资源、人类、机构。
- 边：关系、成员资格、会话。
- 活动：图上的事件流。
为了降低集成开销，FP 采用了两个关键设计原则：
-渐进式披露（Progressive Disclosure）：
当前许多集成模式会将巨大的 Tool Schema 塞进 Prompt Context，造成 Token 浪费和安全风险。FP 规定实体默认只暴露轻量级元数据（如目的、风险标签、Schema Hash）。只有在对方被选中或授权后，才通过引用获取完整细节。这显著降低了上下文负载。
-四平面架构（Four-Plane Architecture）：
FP 将协议拆分为四个正交平面，保持核心最小化：
Entity & Trust Plane：统一身份模型。无论是人类还是 AI，都是可寻址的 Entity。信任信号（如声誉、背书）作为钩子存在，而非全局强制系统。
- Transport & Routing Plane：传输无关。支持从本地 IPC 到 HTTP/SSE 的各种绑定，通过信封（Envelope）保持相关性追踪。
- Interaction & Organization Plane：原生支持多对多协作。Session 是显式的容器，绑定参与者、角色和政策。事件流支持回放和背压（Backpressure），避免慢消费者被淹没。
- Regulation & Oversight Plane：治理即协议。策略执行点和审计记录是一等公民。关键决策（如结算前）可在协议边界进行检查，证据可独立于负载进行验证。
### 对比现有协议：FP 定位在哪？
论文通过 Table 2 清晰划定了 FP 的边界。它不是要取代 MCP 或 A2A，而是提供它们共同缺失的 跨域控制面 。
能力维度 FP (Foundation Protocol) MCP A2A DIDComm UCP 统一实体模型 ✓ ◦ ◦ - - 原生组织/群组结构 ✓ - ◦ - - 经济原语 (收据/结算) ✓ - - - ✓ 策略/审计/溯源 ✓ - - ◦ - 渐进式披露 ✓ - - - -注：✓ 表示核心关注，◦ 表示部分/间接支持，- 表示不在范围内。
### 工程启示：如何落地？
对于构建 Agent 系统的工程师，FP 提供了以下实践指导：
- 不要重复造轮子：在实现多 Agent 协作时，显式定义 Session、Role 和 Membership，而不是在应用层用变量模拟。
- 证据先行：将审计日志视为协议的一部分，而非事后追加的 Log 文件。FP 的 Provenance 对象确保了决策的可解释性。
- 拥抱桥接（Bridges）：FP 设计了 Bridge 机制来适配现有协议（如 MCP）。你可以逐步迁移，先包裹少量工具获得一致的身份和追踪，再扩展经济原语。
### 局限与展望FP 目前是一个协调层标准， 不涉及具体的调度器、传输栈或支付轨道 。它依赖于 Profile 和 Extension 来处理具体实现。这意味着落地需要社区共同制定具体的 Binding 规范。此外，作为新兴协议，其生态成熟度和实际大规模并发下的性能表现仍需验证。
总之，Foundation Protocol 试图回答一个根本问题： 当 Agent 成为社会参与者时，我们如何确保协作是低成本、开放且可治理的？ 它提供了一套图原生的基础设施蓝图，值得所有关注 Agent 规模化部署的团队深入研究。
## 📝 AI 点评点评时间：2026-05-26 14:10 ｜ reviewer: DeepSeek V4 FlashFoundation Protocol (FP) 针对 Agentic Society 中异构实体（Agent、工具、人类、组织）跨边界的身份、信任、协作、经济结算和审计问题，提出一个图原生的四平面协调层，通过统一实体模型、原生组织原语、事件流交互、账本无关的经济原语和协议级治理，在不取代现有协议的前提下提供跨域控制面。
亮点：
- 博文准确抓住了 FP 的核心设计原则——图原生视图和渐进式披露，并用“Agent 社会本质上是一个动态图”直观解释，同时指出渐进式披露可降低 Token 开销，这是原文反复强调的工程价值点。
- 对比表格（Table 2）简洁呈现了 FP 与 MCP/A2A/DIDComm/UCP 的定位差异，帮助读者快速理解 FP 作为“跨域控制面”而非替代品的角色，与原文表 2 意图一致。
- “工程启示”部分提炼了 Session/Role/Membership 显式化、证据先行、拥抱 Bridges 三条实践指导，这些正是 FP 设计意图的落地体现，对工程师有参考价值。
挑刺：
- 标题“Agent社会的操作系统”过度解读。原文明确称 FP 为 “a coordination layer” 和 “control-plane substrate”（Section 1），从未使用“操作系统”这一术语。博文标题易误导读者认为 FP 是一个完整的运行时系统，而它仅是协议层面的协调标准。
- 博文完全未提及 FP 核心词汇表（Table 3）中的 Activity、Envelope、Event 等关键对象。原文强调这七个对象是“描述每次交互的最小语义”（Section 2.1），缺少它们会使读者对协议内部机制的理解流于表面。例如 Envelope 是签名包装器、Event 是追加式观察流，这些对理解 FP 的审计和溯源机制至关重要。
- 对比表格仅列出 MCP、A2A、DIDComm、UCP 四种协议，遗漏了原文 Table 2 中同样包含的 A2UI 和 ANP。原文明确将 A2UI 列为“可控的 UI 委托协议”，ANP 为“发现与协商协议”（Section 1.3），博文的省略可能导致读者低估 FP 与现有协议生态的覆盖范围。
总评：⭐⭐⭐½ 博文准确传达了 FP 的核心架构和定位，但标题夸大和核心词汇的遗漏使其完整性略有折扣。
