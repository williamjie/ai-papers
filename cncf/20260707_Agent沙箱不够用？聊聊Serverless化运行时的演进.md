# ⭐⭐⭐ Agent 沙箱不够用？聊聊 Serverless 化运行时的演进

**日期**: 2026-07-07

---

原文 : Why sandboxing your agent is not enough来源 : https://www.cncf.io/blog/2026/07/07/why-sandboxing-your-agent-is-not-enough/在 AI Agent 爆发式增长的当下，我们往往过度关注“如何让它跑起来”，却忽略了“如何让它跑得便宜且安全”。这篇文章揭示了一个被忽视的工程真相：单纯的沙箱隔离（Sandboxing）只是底线，真正的挑战在于大规模并发下的资源效率。
### 痛点：闲置资源的巨大浪费如果你熟悉 Kubernetes 生态，肯定听过 agent-sandbox 项目。它利用 K8s 的原生能力（身份、存储、网络）为 Agent 提供隔离环境，解决了“Agent 乱删文件”的安全噩梦。这很好，但它有一个致命缺陷： 资源独占 。
在传统模式下，每个 Agent 对应一个 Pod。如果这个 Agent 每天只被调用几次，其余时间都在休眠，它依然占用着 CPU 和内存配额。
⚠️ 反直觉发现 ：在大多数 K8s 集群中，保持 Agent 持续运行以换取低延迟，往往导致资源利用率极低。要么闲置浪费，要么频繁启停带来高延迟，两者都不可扩展。
### 方案拆解：从 Pod 到 Actor 的解耦为了解决这个问题，CNCF 社区出现了新项目 agent-substrate 。它的核心思路非常清晰： 将 Agent 的生命周期与底层 Worker Pod 解耦 。
我们可以用下表对比两者的设计哲学：
特性 agent-sandbox agent-substrate 核心目标 安全、隔离、K8s 原生管理 高密度、低延迟、动态伸缩 运行模型 1 Agent = 1 Pod (长期运行) 多 Agent 共享 Worker Pool (按需唤醒) 生命周期 跟随 Pod 启停 独立于 Pod，支持挂起/恢复 适用场景 关键任务、长连接 Agent 大规模、间歇性调用的 Agent 集群agent-substrate 借鉴了 Serverless 的理念。Agent 不再是持续运行的进程，而是类似“无状态函数”的实体。当被调用时，它在安全的 Worker Pod 中瞬间唤醒；闲置时，状态挂起，释放资源。底层依然可以使用 gVisor 或 Kata Containers 保证安全边界，但不再需要为每个 Agent 维护一个独立的容器实例。
### 工程实践：kagent 与 substrate 的集成作者通过 kagent 项目展示了这种架构的实际收益。在传统的 YAML 声明式管理中，我们通常显式定义每个 Agent 的资源。引入 agent-substrate 后，逻辑发生了转变：
- 模板化定义：6 个不同的 AIRE Agent 映射为 6 个 Actor 模板。
- 共享执行池：这些模板不需要各自的 Pod，而是共享一个 Worker Pool（如 kagent-default）。
- 动态调度：只要 Agent 不并发执行，它们可以复用同一个 Worker Pod 甚至同一进程空间。
这种模式带来的直接好处是： 闲置资源消耗显著降低 。你不再需要为数百个偶尔使用的 Agent 准备数百个 Pod。只有当并发量激增时，才水平扩展 Worker Pool 的副本数。
### 局限与思考当然，这套方案并非银弹。 agent-substrate 目前仍是独立项目，尚未纳入 K8s SIG，生态成熟度不如 agent-sandbox 。此外，状态挂起和恢复机制引入了额外的复杂性，对于需要极低冷启动延迟或复杂状态持久化的 Agent，可能需要更精细的配置。
但对于大多数“技能型”Agent（Skills-based Agents），这种 Serverless 化的运行时模型是必然趋势。
### 总结安全隔离是入场券，资源效率才是生死线。
随着 AI 成本成为企业采纳的最大阻碍之一，我们需要重新审视 Agent 在 K8s 中的存在形式。不要将 Agent 的生命周期死死绑定在 Pod 上。未来的云原生 AI 架构，将是**安全、高效且短暂（Ephemeral）**的。
对于正在构建大规模 Agent 平台的团队，建议密切关注 agent-substrate 的进展，并评估现有架构中是否存在“为了可用性而过度预留资源”的情况。
## 📝 AI 点评点评时间：2026-07-07 20:09 ｜ reviewer: DeepSeek V4 Flash核心贡献: 原文对比了 agent-sandbox（为 AI agent 提供 Kubernetes 原生安全隔离）与 agent-substrate（通过动态唤醒/挂起机制将 agent 生命周期与 worker pod 解耦，实现高密度、低延迟的按需执行），指出两者互补：沙箱解决安全性，substrate 解决大规模场景下的资源效率。
亮点: 博文准确地提炼了原文的核心矛盾——“资源独占”与“闲置浪费”，并用清晰的表格对比了两个项目的设计哲学。对 agent-substrate 的 serverless 类比（按需唤醒、状态挂起）以及 kagent 集成案例的转述（6 个 actor 模板共享单个 worker pod）都很到位，抓住了原文的工程价值点。
挑刺:
- 遗漏关键身份与存储细节：原文明确 agent-sandbox 提供“Strong identities for agents”和“Persistent storage that survives restarts”，博文仅笼统概括为“K8s 原生管理”，未提及身份与持久存储这两项对 agent 安全运行至关重要的特性，属于关键约束的省略。
- 过度解读“同一进程空间”：博文写道“它们可以复用同一个 Worker Pod 甚至同一进程空间”，而原文仅说“even same pod”（复用同一个 pod），从未提及“同一进程空间”。该表述可能误导读者以为多个 agent 在同一个容器进程内运行，实际上原文只强调共享 worker pod 内的执行，未涉及进程隔离级别的细节。
- 术语偏差：将“agent-substrate”直接称为“Serverless 化运行时”：原文仅将 agent 的运行模型类比为“on-demand serverless workloads”，并未将 agent-substrate 本身定义为“Serverless 化运行时”。博文标题和正文多次使用该术语，属于对原文比喻的过度固化，可能混淆其作为“runtime building blocks”的底层基础设施定位。
总评: ⭐⭐⭐ 博文准确传达了原文的核心对比和工程价值，但遗漏了身份/持久存储等关键细节，并存在少量过度解读和术语偏差，整体忠实度达到合格线。
