# ⭐⭐⭐½ K8s DRA 实战：告别 Device Plugin 的 GPU 调度新范式

**日期**: 2026-07-01

---

原文 : Understanding dynamic resource allocation in Kubernetes来源 : https://www.cncf.io/blog/2026/07/01/understanding-dynamic-resource-allocation-in-kubernetes/Kubernetes v1.35 正式 GA 的动态资源分配（Dynamic Resource Allocation, DRA）不仅是 API 的升级，更是 GPU 调度逻辑的重构。NVIDIA 官方驱动也随即跟进，这意味着我们终于可以用更优雅的方式解决异构算力调度的痛点。
## 为什么 Device Plugin 不够用了？
过去几年，我们通过 NVIDIA Device Plugin 实现 GPU 共享和分配。但它的核心缺陷在于“节点视角”的局限：
- 强绑定 Node：调度器只能看到节点上的资源总量，无法感知具体设备的属性（如显存大小、架构型号）。
- 配置僵化：要实现按型号调度，必须依赖复杂的 nodeSelector 或 affinity 标签管理。
- 缺乏细粒度控制：难以表达“优先用 A5000，没有则降级用 T10”这种弹性需求。
DRA 引入了类似存储卷（PV/PVC）的设计模式，将设备抽象为集群级别的资源对象，彻底解耦了设备发现与 Pod 调度。
## 核心架构拆解：从 ResourceSlice 到 ClaimDRA 的核心工作流由三个关键 CRD 组成，理解它们的关系是上手的关键：
- DeviceClass：相当于 StorageClass，定义设备类别（如 gpu.nvidia.com、MIG、VFIO）。
- ResourceSlice：这是 DRA 的“眼睛”。每个节点上的 DRA 驱动会自动生成 ResourceSlice，上报该节点所有设备的详细属性（架构、显存、PCI Bus ID 等）。
注意：如果单节点设备超过 128 个，驱动会自动拆分 Slice。调度器通过 generation 字段确保获取最新视图。
- ResourceClaim：这是 Pod 的“订单”。Pod 不再直接请求 nvidia.com/gpu: 1，而是引用一个 Claim。
## 实战场景：DRA 的四重境界原文通过四个场景展示了 DRA 相比传统方案的压倒性优势：
### 1. 基础共享：多容器共用 GPU通过手动创建 ResourceClaim，多个 Container 可以引用同一个 Claim。这实现了进程级的 GPU 共享，且生命周期独立于 Pod。删除 Pod 后，Claim 状态回归 pending ，资源未被释放但可供其他 Pod 复用。
### 2. 弹性降级：优先 A5000，备选 T10这是 DRA 最杀手级的功能。利用 ResourceClaimTemplate 和 CEL 表达式，我们可以定义优先级列表：
firstAvailable :
- name : a5000selectors :
- cel : device.attributes["gpu.nvidia.com"].productName == "NVIDIA RTX A5000"
- name : fallback-t10selectors :
- cel : device.attributes["gpu.nvidia.com"].productName == "Tesla T10"
当 Deployment 扩容时，调度器会自动匹配最优选。若 A5000 耗尽，新 Pod 自动降级到 T10。 无需修改节点标签，无需重启调度器 。
⚠️ 陷阱提示 ：在 RollingUpdate 期间，旧 Pod 未终止前其 Claim 仍被占用。新创建的 Pod 可能因为首选资源不可用而直接落入备选方案，导致集群中出现“新旧 Pod 使用不同型号 GPU”的现象。这是预期行为，但需知晓。
### 3. 属性过滤：显存大于 20GiB利用 CEL 的 isGreaterThan 函数，可以直接在 Claim 中要求显存容量：
expression : device.capacity["gpu.nvidia.com"].memory.isGreaterThan(quantity("20Gi"))
如果集群中没有满足条件的 GPU（如只有 16GiB 的 T10），Pod 将停留在 Pending 状态。这种声明式约束比在应用代码中做运行时检查要安全得多。
### 4. 时间片复用：Time Slicing 的现代化DRA 也支持传统的时间片共享，但配置方式更统一。通过 config 字段指定 TimeSlicing 策略和间隔（如 Long ），无需再手动计算切片数量。多个 Pod 共享同一个 ResourceClaim，实现逻辑上的多租户隔离。
## 工程启示与未来展望对运维团队的建议：
- 迁移时机：如果你正在构建新的 GPU 集群，或者现有 Device Plugin 方案已无法满足混合算力调度需求，现在是测试 DRA 的最佳窗口期（K8s v1.35+）。
- 驱动升级：确保使用支持 DRA 的 NVIDIA Driver 版本（如 v26.3.1），并正确配置 nvidia.com/dra-kubelet-plugin 标签。
- 监控适配：DRA 引入了新的对象类型，监控体系需同步更新以追踪 ResourceSlice 和 Claim 的状态。
未来演进：
随着 K8s v1.36 引入设备健康报告，Pod 错误将能区分是应用故障还是硬件故障。更令人期待的是，Cluster Autoscaler 未来可能基于 GPU 短缺自动扩容节点，实现真正的“算力即服务”。
DRA 不是简单的 API 替换，它是 Kubernetes 迈向精细化异构资源管理的关键一步。对于 AI/ML 团队而言，掌握 DRA 意味着更高的资源利用率和更灵活的调度策略。
## 📝 AI 点评点评时间：2026-07-01 20:08 ｜ reviewer: DeepSeek V4 Flash核心贡献：原文通过CNTUG Infra Labs的实际Kubernetes集群，演示了DRA（Dynamic Resource Allocation）在v1.35 GA后的完整部署流程和四个典型使用场景，展示了如何利用DeviceClass、ResourceSlice、ResourceClaim/ResourceClaimTemplate以及CEL表达式实现精细化的GPU调度。
亮点：博文准确提炼了原���的核心思想——将DRA与Device Plugin对比，强调了DRA解耦设备发现与Pod调度的优势，并抓住了“优先A5000回退T10”和“显存容量过滤”两个最具工程价值的能力。对RollingUpdate期间资源竞争陷阱的提示也忠实地转述了原文的WARNING段落。
挑刺：
- 术语错位：博文在“工程启示”中写“确保使用支持DRA的NVIDIA Driver版本（如v26.3.1）”，但原文中v26.3.1是NVIDIA GPU Operator的版本，而非Driver版本；DRA Driver GPU的版本为v25.12.0。原文明确区分了两者，博文混淆了组件版本号。
- 遗漏关键警告：在描述场景四“GPU Time Slicing”时，博文直接呈现配置为可用方法，但原文明确注明“As of June 2026, neither the NVIDIA official documentation nor the NVIDIA DRA Driver GPU wiki contains any tutorials on Time Slicing.”并指出配置来自demo/specs和第三方文章，可能随版本变化。博文遗漏了这一重要前提，可能误导读者认为该配置是官方稳定方案。
- 数字遗漏：博文在介绍ResourceSlice拆分规则时仅提到“超过128个设备自动拆分”，但原文补充了“or 64 if any device uses taints or counters”，这一约束条件对理解调度器行为有实际意义，博文未提及。
总评：⭐⭐⭐½ 博文整体忠实反映了原文的技术脉络和主要场景，但存在一处版本号混淆和一处关键警告遗漏，略有减损，仍属合格的技术解读。