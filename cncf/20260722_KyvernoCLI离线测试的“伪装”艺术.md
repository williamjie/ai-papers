# ⭐⭐⭐⭐ Kyverno CLI离线测试的“伪装”艺术

**日期**: 2026-07-22

---

原文 : I made a policy engine think it was in production来源 : https://www.cncf.io/blog/2026/07/22/i-made-a-policy-engine-think-it-was-in-production/Kyverno 作为 Kubernetes 原生的策略引擎，其核心优势在于无需额外语言即可实施安全合规。然而，在 CI/CD 阶段进行离线测试时，它曾面临一个致命痛点：依赖实时 API Server 的 GlobalContextEntry 无法解析。这意味着开发人员在本地跑通的政策，上线后可能完全失效。
这篇文章记录了一位 LFX 导师计划学员如何通过巧妙的架构设计，让 Kyverno CLI 在离线环境下“以为”自己正运行在生产集群中。这不仅是一次功能修复，更是对云原生工具链一致性的深刻思考。
### 痛点：离线测试的“静默失败”
在企业级场景中，Kyverno 策略常引用其他 Kubernetes 资源（如 ConfigMap、Secret）作为上下文数据。
- 生产环境：引擎通过 API Server 实时查询，一切正常。
- CI/CD 环境：没有真实的 API Server，CLI 无法解析这些引用。
结果并非报错，而是更可怕的“静默跳过”或测试恐慌（Panic）。策略报告与实际运行结果脱节，导致安全规则在本地验证通过，却在生产环境中形同虚设。这是 2026 年初 Kyverno CLI 面临的真实困境。
### 错误尝试：不要试图修改引擎作者最初的想法很直观：既然没有 API Server，那就让用户提供 YAML 文件模拟资源，直接传入策略引擎。
⚠️ 反直觉发现 ：这种“数据透传”思路是危险的。
如果为了适配离线测试而修改核心策略引擎（Policy Engine），会导致离线行为与生产行为产生分歧。离线测试的核心价值在于“一致性”，任何特殊处理都会破坏这一保证。
作者尝试将 YAML 反序列化为 map[string]interface{} 并传入 CEL 引擎，结果因类型不匹配导致编译失败。这证明：强行让引擎理解测试数据格式，是一条死路。
### 核心方案：伪装成 Informer Cache真正的突破点在于观察 Kubernetes Informer Cache 的行为。
当 Kyverno 在生产集群中解析 kubernetesResource 引用时，Informer Cache 返回的不是单个 JSON 对象，而是一个 []interface{} 切片，其中每个元素都是映射了 unstructured.Unstructured.Object 结构的字典。
解决方案：在 CLI 层构建“伪装层”
作者没有触碰策略引擎代码，而是在 CLI 层实现了一个名为 resolveResourcesMockData 的转换层：
- 解码：读取用户定义的 kyverno-test.yaml 中的模拟资源。
- 格式化：使用 runtime.RawExtension 解码 Manifest，强制转换为 unstructured map。
- 包装：将结果包裹进 []interface{} 切片。
当数据到达 CEL 编译器或 JMESPath 投影时，其结构形状与生产环境中的 Informer Cache 返回的数据 完全一致 。策略引擎根本不知道自己在离线运行，因为它接收到的数据结构从未变过。
### 工程启示：深度优于广度这位学员在为期 12 周的导师计划中，不仅解决了核心问题，还修复了多个底层 Bug：
- 基础修复：解决了 Fake Dynamic Client 中缺失 *List GVK 注册导致的 Panic。
- 静默失败修复：修正了 CEL 策略类型（如 ValidatingPolicy）测试结果被吞没的问题。
- 新功能支持：实现了 HTTP/Envoy 授权策略的离线测试，以及 CleanupPolicy 的 Dry-run 支持。
给开源贡献者的建议：
- 不要试图一次性读懂整个仓库。生产级 CNCF 代码库过于庞大，初期应聚焦于一个具体的 Bug 或 Panic。
- 提问的艺术。不要问“这怎么工作？”，而要问“我追踪到 resolveResource()，这里是否是离线 RESTMapping 失败的地方？”让维护者能在 60 秒内帮你解除阻塞。
- 从“学习项目”转变为“生产依赖”。当你的 PR 被其他团队视为 CI/CD 流水线的关键依赖时，你就真正进入了开源核心圈。
### 总结Kyverno CLI 的这次改进，通过“数据伪装”而非“引擎修改”，完美解决了离线测试与生产环境不一致的问题。它提醒我们：在云原生工程中，保持数据契约的一致性往往比增加新功能更重要。对于任何依赖 Kubernetes API 进行策略评估的工具来说，这种分层解耦的设计思路极具参考价值。
## 📝 AI 点评点评时间：2026-07-22 20:11 ｜ reviewer: DeepSeek V4 Flash核心贡献: 原文解决 Kyverno CLI 在 CI/CD 环境中无法解析 kubernetesResource 类型 GlobalContextEntry（依赖实时 API Server）的问题，核心方法是在 CLI 层构建 resolveResourcesMockData 伪装层，将用户提供的 mock 数据转换成与生产环境 Informer Cache 返回的 []interface{} 切片形状完全一致的数据，使策略引擎无感知离线运行，而不修改引擎自身。
亮点: 博文准确抓住了“伪装”这一核心工程思路，强调“不修改引擎，而是伪装数据形状”，并清晰地解释了 Informer Cache 返回切片而非单对象这一关键洞察。同时，博文保留了作者关于“提问艺术”和“深度优于广度”的实用建议，这些对开源贡献者具有启发价值。
挑刺:
- 博文在“错误尝试”部分写道：“作者尝试将 YAML 反序列化为 map[string]interface{} 并传入 CEL 引擎，结果因类型不匹配导致编译失败。” 原文描述的是 CEL 引擎抛出“no such overload”错误，这是运行时类型错误而非编译失败。虽然意思接近，但“编译失败”的表述容易让读者误解为语法编译阶段的问题，与原文的运行时类型系统行为有细微偏差。
- 博文在总结中称：“保持数据契约的一致性往往比增加新功能更重要。” 原文并未做出这种比较性论断，原文强调的核心是“离线测试应与生产行为一致”以及“任何特殊处理都会破坏保证”。博文将“一致性”与“增加新功能”进行对比属于过度引申，可能偏离原文的严谨基调。
- 博文遗漏了原文中社区成员请求将修复 backport 到 v1.18 的关键情节。该情节不仅体现了项目的生产依赖性和实际影响力，也侧面印证了“伪装”方案的正确性和紧迫性。虽然不算严重瑕疵，但削弱了博文对工程价值的呈现深度。
总评: ⭐⭐⭐⭐ 博文准确传达了原文的核心工程洞察，在关键术语和思路提炼上到位，但存在一处术语细微偏差和一处过度引申，整体仍是一篇优秀的技术解读。
