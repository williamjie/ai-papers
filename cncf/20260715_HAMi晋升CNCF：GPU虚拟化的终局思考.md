# ⭐⭐⭐½ HAMi 晋升 CNCF：GPU 虚拟化的终局思考

**日期**: 2026-07-15

---

原文 : HAMi becomes a CNCF incubating project来源 : https://www.cncf.io/blog/2026/07/15/hami-becomes-a-cnfc-incubating-project/AI 基础设施团队正面临一个残酷的现实：昂贵的 GPU 资源被严重碎片化。
很多时候，整张显卡只跑了一个只需几 GB 显存的小任务。这种“大马拉小车”的现象，让算力成本居高不下。
HAMi 正式成为 CNCF 孵化（Incubating）项目，标志着异构加速器的云原生调度终于有了统一的事实标准。这不仅仅是一个项目的晋升，更是 K8s 生态在 AI 时代的一次关键补全。
## 痛点：为什么我们需要 GPU 虚拟化？
传统 Kubernetes 对 GPU 的支持非常粗放。它通常采用“独占模式”，即一个 Pod 绑定整张物理 GPU。
这就导致了两个极端问题：
- 资源浪费：推理任务或轻量级训练往往用不满整卡，剩余算力无法共享。
- 调度僵化：不同厂商（NVIDIA、AMD、华为昇腾等）的 Device Plugin 接口各异，运维复杂度随硬件种类线性增长。
现有方案要么侵入应用代码，要么依赖特定厂商的闭源工具。HAMi 的出现，旨在解决“异构加速器”在 K8s 中的标准化调度与共享难题。
## 核心架构：无侵入的多厂商抽象HAMi 的核心价值在于其 多厂商设计（Multi-vendor Design） 和 无侵入性 。
它不需要修改现有的 Kubernetes 资源清单（Manifests），也不需要改动应用代码。通过以下组件协同工作，实现了硬件层的透明化：
- Mutating Webhook：拦截 Pod 提交，重写调度字段和资源请求。这是实现“虚拟设备”逻辑的关键入口。
- Scheduler Extender：提供 Binpack、Spread 和拓扑感知策略。它决定了哪个 Pod 能分到哪张卡的哪个切片。
- Device Plugins：针对特定厂商的插件，负责向 K8s 注册加速器并分配分数级资源。
- HAMi-Core：容器内的虚拟化层。这是最硬核的部分，它拦截原生 CUDA 驱动（针对 NVIDIA），强制实施 GPU 内存和计算的硬隔离。
关键洞察 ：HAMi 不仅仅是“切片”，它强调的是 硬运行时隔离（Hard Runtime Isolation） 。这意味着共享同一张卡的多个负载之间不会互相干扰显存或计算核心，解决了传统虚拟化方案中最担心的稳定性问题。
## 生态与数据：从 Sandbox 到 Incubating自 2024 年 8 月加入 CNCF Sandbox 以来，HAMi 的增长速度令人印象深刻。
- 贡献者：GitHub 贡献者总数达 2,687 人，同比增长 43%。
- 采用规模：DaoCloud 在超 10 个数据中心部署了超过 10,000 张 GPU；招商银行也用于大规模异构资源管理。
- 社区活跃度：GitHub Stars 约 3,500，Forks 超 550。
- 版本迭代：已发布 16 个版本，当前稳定版为 v2.9.0。
值得注意的是，维护者团队来自 Dynamia.ai、NVIDIA 等多家公司，这体现了 CNCF 所要求的 厂商中立治理（Vendor-neutral Governance） 。
## 工程启示：谁应该关注 HAMi？
如果你的团队符合以下任一场景，HAMi 值得纳入技术选型：
- 混合负载集群：同时运行训练和推理任务，且推理任务显存占用低但并发高。
- 多厂商硬件环境：集群中混用了 NVIDIA、AMD、华为昇腾等不同品牌的加速器。
- 成本敏感型 AI 平台：需要最大化 GPU 利用率，降低单位算力的基础设施成本。
HAMi 与 Volcano（批处理调度）和 Koordinator（资源协调）的深度集成，使其能融入更复杂的云原生 AI 基础设施栈。未来与 Kueue 等项目的合作，将进一步完善这一生态。
## 局限与展望尽管 HAMi 进展顺利，但异构虚拟化并非万能药。
- 硬件支持边界：目前主要聚焦 NVIDIA CUDA 生态的拦截，对 AMD Mi Series 和 PPU 的支持仍在扩展中。
- 调度复杂性：引入 Gang Scheduling、抢占（Preemption）等高级特性会增加调度的复杂度，对集群稳定性提出更高要求。
- 监控盲区：目前团队正致力于解决 DRA（Device Resource Allocation）消耗的监控问题，这是精细化运营的关键一环。
## 结语HAMi 的晋升，意味着 K8s 社区在“如何高效利用异构算力”这个问题上，找到了一条开源、中立且可落地的路径。
对于云原生工程师而言，关注 HAMi 不仅是关注一个工具，更是理解 AI 基础设施如何从“粗放式独占”走向“精细化共享”的最佳窗口。
## 📝 AI 点评点评时间：2026-07-16 08:08 ｜ reviewer: DeepSeek V4 Flash核心贡献: 解决 Kubernetes 上 GPU 等异构加速器碎片化、利用率低、多厂商接口不统一的问题；核心方法是提供开源的云原生 GPU 虚拟化中间件，通过设备切片、硬运行时隔离和统一调度策略实现。
亮点: 博文准确提炼了 HAMi 的核心价值——“多厂商设计”和“无侵入性”，并重点强调了“硬运行时隔离”这一工程关键点；同时引用了贡献者 2,687 人、DaoCloud 超 10,000 GPU 部署等关键数据，支撑了项目的生态说服力。
挑刺:
- 标题过度解读：博文标题“GPU 虚拟化的终局思考”暗示 HAMi 是终极方案，而原文仅描述其为“open source, cloud native GPU virtualization middleware”，并无“终局”或“事实标准”的断言。原文 TOC 赞助人评价是“solves a real problem”，并未宣称统一标准。
- 遗漏重要生态指标：原文明确提到“more than 550 contributing organizations”和“five independent CNCF case studies”，博文只提及了贡献者总人数和单个案例，遗漏了“550+ 参与组织”这一反映企业级采纳广度的关键数字。
- 局限表述不准确：博文说“目前主要聚焦 NVIDIA CUDA 生态的拦截”，而原文明确 HAMi 支持 NPU、DCU、MLU 等非 CUDA 加速器，且“multi-vendor design”是其区别于单厂商插件的核心卖点。博文此处将“主要”聚焦于 NVIDIA，弱化了多厂商原生支持的设计意图。
总评: ⭐⭐⭐½ 博文准确传达了 HAMi 的核心价值和关键里程碑，但标题略有夸大且遗漏了一处重要生态数据，整体仍是一篇合格的解读。