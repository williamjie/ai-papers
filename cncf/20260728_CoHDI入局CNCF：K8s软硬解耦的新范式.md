# ⭐⭐⭐ CoHDI入局CNCF：K8s软硬解耦的新范式

**日期**: 2026-07-28

---

原文 : Welcome CoHDI to the CNCF: Evolving Kubernetes into composable-disaggregated-infrastructures来源 : https://www.cncf.io/blog/2026/07/28/welcome-cohdi-to-the-cncf-evolving-kubernetes-into-composable-disaggregated-infrastructures/Kubernetes 的编排能力早已成熟，但硬件资源的僵化分配仍是云原生落地的隐形瓶颈。CoHDI 正式加入 CNCF Sandbox，标志着 K8s 开始真正深入底层硬件，实现 PCIe 设备的动态热插拔与细粒度调度。
## 为什么我们需要“可组合”的基础设施？
传统 K8s 集群中，GPU、网卡等 PCIe 设备通常绑定在物理节点上。一旦 Pod 调度完成，硬件资源就被静态锁定。这种模式在 AI 时代显得尤为笨重：
- 资源错配：LLM 推理的 Prefill（预填充）阶段计算密集，而 Decode（解码）阶段内存密集。静态分配导致一方闲置，另一方瓶颈。
- 弹性不足：Agentic AI 工作流在不同阶段对算力需求波动极大，传统扩容需要重启或长时间等待。
- 能效低下：无法根据负载动态调整硬件连接，导致能源浪费。
CoHDI（Composable Hardware in Disaggregated Infrastructure）的核心目标，就是打破物理节点的硬件边界。它让 Kubernetes 不仅能调度容器，还能调度“硬件连接”。
## 架构拆解：如何打通 K8s 与底层硬件？
CoHDI 并非凭空造轮子，而是深度集成 K8s 现有的 Dynamic Resource Allocation (DRA) 机制。其软件栈由三个核心组件构成，形成从声明到执行的闭环：
组件 角色 关键能力 Composable-DRA-Driver 桥梁 将 CoHDI 管理器中的可用资源暴露为 K8s 的 ResourceSlices ，供调度器发现。 Dynamic-Device-Scaler 执行者 根据 Pod 请求动态添加或移除设备， 无需重启操作系统 。 Composable Resource Operator 控制器 通过外部 API 调用底层管理器，实现 GPU 等资源的动态挂载与卸载。
⚠️ 关键点 ：这里的“动态”指的是主机级别的 PCIe 设备热插拔。这意味着 K8s 调度器发出的指令，能直接改变物理机上的硬件拓扑结构，而不仅仅是虚拟资源的分配。
## 技术深潜：DRA 的核心地位CoHDI 选择 DRA 作为集成点，而非传统的 Device Plugin，是极具前瞻性的决策。
- Device Plugin 仅负责发现和管理已存在的设备，无法处理设备生命周期的动态变化。
- DRA 允许更复杂的资源描述和分配逻辑，支持资源的“创建”与“销毁”。
CoHDI 利用 DRA 的 ResourceSlice 对象，将底层可组合基础设施中的硬件资源抽象化。当 Pod 请求特定资源时，Driver 协调 Scaler 在物理层完成设备连接，再通知 K8s 资源就绪。这种设计实现了 软件定义硬件 （Software-Defined Hardware）在云原生领域的落地。
## 工程启示与适用场景对于关注 AI 基础设施优化的团队，CoHDI 提供了新的思路：
- LLM 推理优化：利用 Prefill/Decode 的资源特性差异，动态调整计算与内存资源的配比，提升吞吐量。
- 绿色计算：通过更精细的资源匹配，减少空闲硬件能耗，符合可持续运营趋势。
- 多云/多厂商兼容：CoHDI 旨在建立标准生态，避免被单一厂商的专有硬件锁定。
## 局限与思考尽管愿景宏大，但 CoHDI 仍处于 Sandbox 阶段，面临挑战：
- 硬件依赖：需要底层基础设施支持 PCIe 设备的动态重配置（如 CXL 或特定 Switch 架构），并非所有数据中心都能直接适配。
- 稳定性风险：运行时热插拔 PCIe 设备对内核驱动和系统稳定性要求极高，生产环境需谨慎验证。
- 生态成熟度：目前主要由 Red Hat、NTT 等巨头推动，社区贡献者和实际用例尚需时间积累。
CoHDI 的出现提醒我们：K8s 的边界正在从“容器编排”向“基础设施编排”扩展。对于云原生工程师而言，理解 DRA 机制及底层硬件交互，将成为未来的核心竞争力。
## 📝 AI 点评点评时间：2026-07-29 08:10 ｜ reviewer: DeepSeek V4 Flash核心贡献: 原文介绍 CoHDI 项目被 CNCF Sandbox 接受，其核心目标是使 Kubernetes 节点能在可组合的分解基础设施中，通过 Dynamic Resource Allocation (DRA) 实现主机级 PCIe 设备的动态附着与分离，从而支持灵活高效的资源分配。核心方法是通过三个组件（Composable-DRA-Driver、Dynamic-Device-Scaler、Composable Resource Operator）集成 DRA 框架来管理底层硬件拓扑变化。
亮点: 博文准确抓住了 CoHDI 最关键的工程价值——实现无需 OS 重启的 PCIe 设备动态增减（原文 “without requiring OS reboots”），并具体关联到 LLM 推理的 Prefill/Decode 阶段资源差异和 Agentic AI 工作流的动态适应性。博文对三个组件的角色提炼（桥梁、执行者、控制器）清晰且忠于原文，没有添加虚构信息。
挑刺:
-术语过度解读：博文将原文的 “dynamic attachment and detachment” 直接称为“PCIe 设备的动态热插拔”，而原文并未使用 “hotplug” 一词，且热插拔通常指带电物理插拔，CoHDI 的机制更多是软件驱动下的拓扑重配置，可能依赖特定硬件能力。这一表述可能误导读者理解为传统热插拔。
原文: “CoHDI enables host-level dynamic attachment and detachment of PCIe devices”
- 博文: “实现 PCIe 设备的动态热插拔与细粒度调度”
-遗漏关键背景信息：博文未提及 CoHDI 的前身 InfraDDS、具体发起时间（March 2025）以及合作方包括 FSAS、Fujitsu、IBM Research 等，而原文明确列出这些以体现生态多元性。这削弱了博文对项目背景完整性的传达。
原文: “Launched in March 2025 as a collaborative effort between Red Hat, FSAS, Fujitsu, IBM Research, and NTT, CoHDI (formerly known as InfraDDS)”
- 博文: 仅提到 “Red Hat、NTT 等巨头”
-引用偏差：博文在“技术深潜”部分声称 “CoHDI 选择 DRA 作为集成点，而非传统的 Device Plugin，是极具前瞻性的决策”，并断言 “Device Plugin 仅负责发现和管理已存在的设备，无法处理设备生命周期的动态变化”。原文并未对 Device Plugin 做任何比较或批评，这一论断属于博文作者自行添加的价值判断，且忽略了 Device Plugin 也能通过外部控制器实现类似效果的可能性，存在过度解读风险。
原文: 仅描述 CoHDI 如何与 DRA 集成，未提及 Device Plugin。
- 博文: “CoHDI 选择 DRA 作为集成点，而非传统的 Device Plugin，是极具前瞻性的决策。”
总评: ⭐⭐⭐ 博文准确传达了 CoHDI 的核心功能和架构，但存在术语不够精确、遗漏关键背景信息以及过度引申原文未提及的比较，整体忠实度尚可但细节处理不够严谨，符合三星档。
