# AI 沙箱正在经历它的 Kubernetes 时刻

**日期**: 2026-04-30

---

原文 : AI sandboxing is having its Kubernetes moment来源 : https://www.cncf.io/blog/2026/04/30/ai-sandboxing-is-having-its-kubernetes-moment/Anthropic 的新模型 Mythos autonomously 找到了所有主流操作系统和浏览器的零日漏洞——包括一个 27 年历史的、历经数十年人工审查和数百万自动化测试的遗留 bug。模型不需要专门训练，也不需要人类研究员引导。
一个 AI 能自主串联漏洞实现 Linux 内核提权，那你怎么看那些让成千上万个 workload 共享同一个内核、彼此毫无结构隔离的基础设施设计？Mythos 没有引入新威胁，它只是让一个旧设计决策的后果变得难以再拖延下去。
## 问题：我们现在的安全架构到底在防什么？
先看市场上那些主流安全产品。除了少数例外，大部分都是 glorified log generators and dashboards of doom —— 花哨的日志生成器和末日仪表板。Runtime 检测代理、漏洞扫描器、准入控制器……一长串清单，它们都基于同一个假设：要么阻止入侵，要么快速检测到，你就赢了。
但它们并没有让系统变得更安全。扫描器发现一个严重 CVE，生成一个 ticket，扔给开发团队——而开发团队有自己的优先级。Architecture doesn’t self-heal（架构不会自愈）。It doesn’t contain the blast（不会控制爆炸范围）。It watches itself burn and takes very thorough notes（它只是看着自己燃烧，并做了非常详细的笔记）。
想象一下如果 Kubernetes 这样工作：你的 pod 崩溃了，kubelet 不开自动重启，而是打开一个 Jira ticket：“Pod 不健康。建议重启。指派给：平台团队。“——这很荒谬。但这正是大多数组织今天在生产环境中的安全现状。
Pre-fail controls 还需要不切实际的知识量才能正确配置。每个网络策略、每个 RBAC 规则、每个 seccomp profile，都必须针对它所保护的工作负载的具体行为进行调优。在一个运行数千个容器的多租户 Kubernetes 集群里，这意味着 someone needs to know exactly which APIs each service calls（有人需要精确知道每个服务调用哪些 API）、which ports it needs（需要哪些端口）、what filesystem paths it accesses（访问哪些文件系统路径）、what constitutes “normal” behavior（什么算”正常”行为）——对每一个工作负载来说都是如此。
这不是工具问题，是信息问题。正确配置 pre-fail controls 所需的知识是 distributed across teams（跨团队分布的），从未在任何单一地方整合。Perfect configuration requires omniscience（完美配置需要全知），而全知不是你 can ship 的功能。
所以 industry plays an infinite game of incremental hardening —— 打这个 CVE，收紧那个网络策略，加一条检测规则……每次改进都 forever 把负担放在防御者身上。Attackers need to find one viable chain（攻击者只需要找到一条可行的攻击链）——初始访问、提权、横向移动。Defender has to hold every configuration correct simultaneously across thousands of workloads（防御者必须同时保持所有配置在数千个工作负载上正确）。The math doesn’t work（数学上行不通）。
## 核心问题：如果假设工作负载已被入侵，你会怎么设计？
这是大多数安全架构无法回答的问题：
How would you architect your systems if you assumed a workload was already compromised, the way you assume a pod can crash at any time?
这就是 SRE 对待可靠性的方式。你不会设计一个分布式系统，假设每个节点都保持健康。你假设节点不可预测地失败，engineer 让单个失败不会级联。Circuit breakers halt propagation（断路器阻止传播）。Failure domains contain blast radius（故障域控制爆炸范围）。你不需要保持每个节点存活就能让应用服务流量，因为 architecture was built to survive failure（架构是为生存而建）。
如果我们将同样的思维应用到安全上呢？如果一个被入侵的工作负载被以 Kubernetes 对待崩溃 pod 的相同方式对待：一种系统自动绕过的预期失败？Not a catastrophe（不是灾难）。Not a dashboard alert（不是仪表板告警）。Not a war room（不是战争室）。Just another Tuesday（只是又一个周二）。
## Kubernetes 的讽刺：容错平台 + 脆弱的安全层Irony is sharpest in the Kubernetes ecosystem（讽刺在 Kubernetes 生态中最尖锐）。Kubernetes 是基础设施的 SRE moment——“design for failure” 最成功的体现。Pods crash and get rescheduled（Pod 崩溃并被重新调度）。Nodes die and workloads migrate（节点死亡，工作负载迁移）。整个系统假设任何单个组件都可能失败，platform handles it automatically（平台自动处理）。
然而，运行在同一平台上的安全模型却是一个 catastrophic single point of failure（灾难性的单点故障）。
大多数 Kubernetes 集群的所有容器共享同一个 Linux 内核。节点上的每个 workload——每个微服务、每个 sidecar、每个批处理作业——来自每个团队——共享同一个内核地址空间。一个内核漏洞不会只危及一个容器；它会危及节点上的每个容器。更糟糕的是，你部署用于检测入侵的安全控制——eBPF-based agents、LSM modules、seccomp-bpf filters——也运行在同一个内核上。一个单一的内核利用不仅会 breach every container（破坏每个容器），它还会 simultaneously blinds every monitor watching it（同时致盲每一个监控它的人）。你的检测层和你的爆炸范围是同一个东西。
我们运营一个自动处理任何 pod、任何节点、任何基础设施组件失败的 platform——然后我们在其上运行安全层，却 zero isolation（零隔离）、zero failure domains（零故障域）、zero plan for what happens when the kernel fails（对内核这一单一共享基础设施失败时会发生什么零计划）。
## 方案拆解：结构隔离才是根本解如果共享内核是单个漏洞级联到节点上每个工作的原因，那么架构修复正是分布式系统工程几十年前解决的那个方案： eliminate the single point of failure（消除单点故障） 。
Stop sharing one kernel across all workloads（停止在所有工作负载间共享一个内核）。Distribute the failure domain across independent kernel instances（将故障域分布在独立的内核实例上），就像你会将单体数据库分布到多个副本上一样。A compromise of one kernel instance is contained to one workload（一个内核实例的泄露被限制在一个工作负载内），not because of a policy someone remembered to configure（不是因为有人记得配置的策略），but because the failure domain boundary is structural（而是因为故障域边界是结构性的）。
这种方法不消除对安全策略的需求。你仍然需要网络分段、最小权限 IAM、供应链安全。改变的是配置错误的后果。With structural isolation（有了结构隔离），一个策略失败被限制在它影响的工作负载内。Pre-fail controls become best-effort hardening with a safety net underneath——它们不再是最后一道防线。
## AI 代理的实验证据是什么让这个时刻不同？AI 行业刚刚为我们做了实验。
每个主要 AI 实验室 shipping autonomous agents 都独立得出了相同的架构决策——containment first（首先 containment）、hard boundaries（硬边界）、sandboxed execution environments（沙箱执行环境），其中策略失败无法 cascades beyond the sandbox wall（超越沙箱墙）。他们仍使用策略，但将策略视为沙箱内的一层，而不是边界本身。
为什么？Because you can’t write a complete security policy for something when you don’t know what it’s going to do next（因为你无法为某物写出完整的安全策略，当你不知道它接下来要做什么）。一个 AI 代理可能需要 legitimately 安装包、写入任意路径、进行网络调用。它也可能做一些灾难性的事。The behavior space is too wide for policy alone to cover（行为空间太宽，仅靠策略无法覆盖）。所以他们 built walls and put the rules inside them（建了墙，把规则放在里面）。
AI 行业重新发现了一些安全行业几十年前就应该建立的东西。问题是我们为什么仍在运行生产工作负载——处理客户数据、金融交易、关键基础设施的——在共享内核上，其隔离保证比浏览器标签页还弱。Chrome 十多年前就想通了一个崩溃或受损的标签页不应该拖垮浏览器。你的运行支付处理的 Kubernetes 集群的隔离保证比浏览 Reddit 还弱。
## 工程启示：云原生安全的范式转移这篇文章的价值在于它提出了 “failure domain”（故障域） 这一分布式系统核心概念在安全领域的映射。在云原生世界里，我们接受 Pod 会崩溃、节点会宕机，于是设计了自动恢复机制。但安全上，我们还在追求”永不出错”——试图用完美的策略和配置来防止每一次入侵。
现实是， 攻击面是无限的，防御资源是有限的 。正如文章指出的：攻击者只需要找到一条可行的攻击链，防御者却必须同时保持所有配置在数千个工作负载上正确。
真正的解不是更精细的策略，而是改变失败的影响范围——让单点失败无法 cascades（级联）。如果每个工作负载运行在独立的内核实例上，一个内核漏洞只会影响该工作负载，而不是整个节点。这听起来像是性能开销，但 AI 行业的实践已经验证了这种设计是可行的。
这篇文章值得关注，因为它把云原生基础设施的容错思维直接移植到了安全领域。它不是在介绍一个新工具，而是在质疑基本假设：我们是否应该改变安全架构，来适应”失败必然发生”这一现实？
如果你负责 Kubernetes 集群的安全，这篇文章提供一个根本性的视角转换：从”如何防止所有入侵”转向”如何限制每次入侵的影响范围”。前者是无限游戏，后者是有限游戏。
← 上一篇（更早） FD-loss：把FID从评分器变成训练器，一步到位 下一篇（更新） → 预测市场信号可信度指数：基于微观结构的诊断框架 ← 返回首页 © 2026 前沿研读 · Frontier Studies. All rights reserved.
📡 RSSfunction d(){const o=document.getElementById("article-toc");if(!o)return;const i=document.querySelectorAll(".prose h2, .prose h3");if(i.length {e.id||(e.id="h-"+c);const n=document.createElement("li");n.className=e.tagName.toLowerCase();const t=document.createElement("a");t.href="#"+e.id,t.textContent=(e.textContent||"").trim(),n.appendChild(t),s.appendChild(n),r.push({a:t,h:e})}),o.appendChild(s);const l=new IntersectionObserver(e=>{e.forEach(c=>{if(!c.isIntersecting)return;const n=r.find(t=>t.h===c.target);n&&(r.forEach(t=>t.a.classList.remove("active")),n.a.classList.add("active"))})},{rootMargin:"-80px 0px -70% 0px"});i.forEach(e=>l.observe(e))}d();
