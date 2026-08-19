# ⭐⭐⭐ DRA取代HAMi？云原生GPU共享的终局之战

**日期**: 2026-08-07

---

原文 : Does Kubernetes DRA Replace HAMi?
来源 : https://www.cncf.io/blog/2026/08/07/does-kubernetes-dra-replace-hami/Kubernetes 动态资源分配（DRA）在 v1.34 GA 后，社区里最热的讨论莫过于：它是否让 HAMi 这类 GPU 虚拟化方案变得多余？答案很明确： 没有取代，而是分工重组。 DRA 接管了“请求与调度”的语言权，而 HAMi 保留了“运行时强制隔离”的肌肉。
## 痛点：当 API 只会数数时早期的 Kubernetes Device Plugin API 极其简陋，它只能做整数计数（ nvidia.com/gpu: 1 ）。如果你想让一个 Pod 只占用一张卡 8GB 显存和 10% 算力，API 根本听不懂。
HAMi 为此构建了一套复杂的“ workaround ”流水线：
- Mutating Webhook：拦截 Pod，因为默认调度器看不懂自定义资源。
- Scheduler Extender：HAMi 自己的调度插件负责过滤节点、计算显存余量（比如判断 24GB 卡能不能塞进两个 8GB 请求）。
- Annotation 记录：将分配结果写入注解，因为 API 没有字段存储“具体哪张卡、多少份额”。
- Device Plugin 注入：读取注解，注入环境变量和 libvgpu.so 库。
这套方案在 DaoCloud 等大规模场景验证有效，但本质上是“私有协议”。每个 GPU 共享项目都有自己的注解方言，调度器与 Kubelet 之间的契约全靠字符串解析，脆弱且难以扩展。
## DRA 的介入：从计数到 ClaimDRA 引入了类似 PVC（持久卷声明）的 Claim 模型 。核心对象包括 ResourceSlice （描述硬件）、 DeviceClass （定义设备类别）和 ResourceClaim （用户请求）。
真正改变游戏规则的是 Consumable Capacity （可消耗容量）特性。它允许驱动程序标记设备支持多分配，并让 Pod 请求特定数量的资源（如 10Gi 显存），而非独占整个设备。
⚠️ 关键洞察 ：DRA 解决的是“承诺追踪”问题。调度器现在原生理解 GPU 内存和算力的切片逻辑，不再需要 HAMi 的调度扩展器来做数学题。 CardInsufficientMemory 这种私有错误码，变成了标准的 Unscheduling 状态。
## 架构重构：HAMi 的三分法面对 DRA，HAMi 没有硬刚，而是优雅地拆分了职责，形成了三个仓库协同工作：
- k8s-dra-driver：基础驱动。发布 GPU 容量为 Consumable Capacity，通过 CDI（容器设备接口）连接运行时。
- HAMi-DRA：兼容层。一个 Mutating Webhook，将旧的 nvidia.com/gpumem 请求自动翻译为标准的 ResourceClaim。这让存量 YAML 无需修改即可运行在 DRA 模式下。
- HAMi-core：运行时强制力。这是 DRA 做不到的部分。 DRA 只管调度承诺，不管容器内是否越界。HAMi-core 通过预加载 libvgpu.so 拦截 CUDA 调用，确保容器不超过分配的显存和算力。
## 对比与选型建议特性 Device Plugin 模式 (旧) DRA 模式 (新) 请求语言 扩展资源 (Opaque Integers) ResourceClaim (Typed API) 调度决策 HAMi Scheduler Extender 默认 kube-scheduler 分配记录 Annotation (私有字符串) ResourceClaim Status (RBAC 可见) 运行时强制 HAMi-core (libvgpu.so) HAMi-core (不变) K8s 版本要求 任意支持版本 v1.34+ (v1.36 默认开启)
工程启示：
- 如果你控制集群且 K8s >= v1.36：强烈建议迁移到 DRA 模式。原生 API 意味着更好的可观测性、RBAC 支持和未来扩展性（如优先级列表）。
- 混合厂商环境：如果集群里有 Ascend、Hygon DCU 等非 NVIDIA 芯片，且缺乏对应的 DRA 驱动，请继续使用传统 Device Plugin 模式。HAMi 目前支持 12+ 种设备家族，DRA 的生态还在追赶。
- 多租户隔离：无论哪种模式，libvgpu.so 的软件拦截都不是硬件级隔离。对于恶意负载，仍需依赖 NVIDIA MIG 等硬件分区技术。
## 局限与思考DRA 并非银弹。目前的 Consumable Capacity 仍是 Beta 状态，且 DRA 模式无法表达复杂的拓扑约束（如 NVLink 带宽感知）。如果工作负载对 GPU 间通信延迟极其敏感，可能需要保留具备拓扑感知的定制调度器。
此外， 严禁在同一集群混用两种模式 。两个记账系统会互相看不见对方的承诺，导致超卖和 OOM。
GPU 共享的未来已定：DRA 负责“说清楚需求”，HAMi 负责“守住边界”。对于云原生工程师而言，拥抱 DRA 不仅是技术升级，更是向标准化、可组合的云基础设施迈进的关键一步。
## 📝 AI 点评点评时间：2026-08-10 20:10 ｜ reviewer: DeepSeek V4 Flash核心贡献: 原文解答了“DRA是否取代HAMi”这一核心问题，指出DRA接管了GPU分片请求的调度层（通过Consumable Capacity特性），而HAMi保留了运行时强制隔离层（通过libvgpu.so拦截CUDA调用），最终将HAMi拆分为三个仓库实现分工，使请求、调度和强制使用同一标准语言。
亮点: 博文准确抓住了原文的核心论点（DRA不取代HAMi而是分工重组），并清晰提炼了三个仓库的职责（k8s-dra-driver、HAMi-DRA、HAMi-core），以及用对比表格直观呈现Device Plugin模式与DRA模式的关键差异。原文中真正有工程价值的点——HAMi-core的软件强制隔离和DRA Consumable Capacity的承诺追踪——均在博文中得到正确强调。
挑刺:
- 博文遗漏了原文中关于k8s-dra-driver Helm chart状态的关键约束。原文明确说“the k8s-dra-driver’s own Helm chart is still marked work in progress”，而博文未提及，这会影响用户对DRA模式成熟度的判断。
- 博文简化了原文的对比表格，遗漏了“Production mileage”和“Vendor coverage”两行。原文表格包含“16 releases, 10,000+ GPUs at DaoCloud”和“12+ device families”等选型关键依据，博文仅在文字中部分提及，削弱了决策参考价值。
- 博文在“工程启示”中建议“如果你控制集群且K8s >= v1.36：强烈建议迁移到DRA模式”，而原文作者实际措辞是“stand up DRA mode in staging now… let the results decide your production timeline”，并附有三个caveats（consumable capacity未stable、driver覆盖率低等）。博文的语气更激进，忽略了原文的谨慎态度。
总评: ⭐⭐⭐ 博文准确反映了原文的核心内容，但遗漏了部分关键细节和约束，整体忠实，属于默认档。
