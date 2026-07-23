# ⭐⭐⭐½ Ingress NGINX 到 Envoy Gateway 零停机迁移实战

**日期**: 2026-05-25

---

原文 : Zero-Downtime migration from ingress NGINX to Envoy Gateway来源 : https://www.cncf.io/blog/2026/05/25/zero-downtime-migration-from-ingress-nginx-to-envoy-gateway/在 Kubernetes 网络层，从 Ingress NGINX 迁移到 Gateway API 已是大势所趋。但大多数团队卡在“如何平滑过渡”上：直接切换会导致流量丢失，而复杂的灰度方案又往往缺乏经过验证的落地细节。这篇文章分享了一个基于 AWS 的真实案例，展示了如何利用加权 DNS（Weighted DNS）实现真正的零停机迁移，并深入剖析了选型背后的工程逻辑。
### 为什么必须迁移？
Ingress NGINX 依然是 K8s 生态中最流行的控制器之一，但它正面临严峻挑战：
- 功能冻结：Ingress API 规范已停滞不前，缺乏对新特性的支持。
- 维护缺失：不再提供安全补丁和新功能更新。
- 配置混乱：依赖大量注解（Annotations）而非专用资源对象，导致配置分散且难以管理。
Gateway API 作为替代方案，提供了更规范的表达方式和专用的资源模型。但在众多实现中，选择哪一个控制器至关重要。
### 选型决策：为什么是 Envoy Gateway？
团队首先使用 ing-switch 工具扫描集群，评估迁移复杂度。在对比多个候选者时，他们设定了严格的过滤条件：
- CNCF 背书：优先选择 CNCF 项目，确保社区共识和生产就绪度。
- 功能对等：必须支持 mTLS、请求缓冲等生产级需求。
- 规范遵循：严格遵循 Gateway API 的资源模型，而非注解堆砌。
控制器 CNCF 状态 评估结论 Envoy Gateway CNCF 项目 入选 。CNCF 自身基础设施也在用，满足 mTLS/缓冲需求。 Traefik 非 CNCF 长期方向不符。 NGINX Gateway Fabric 非 CNCF 未通过 CNCF 过滤。 Istio CNCF 项目 功能全面但较重。 Higress CNCF 项目 未在官方一致性测试列表中。
最终选定 Envoy Gateway，不仅因为其技术实力，更因为 CNCF 自身的背书提供了极强的信心信号。
### 核心挑战：DNS TTL 导致的“伪”成功初次迁移看似顺利：部署 Envoy Gateway，配置 HTTPRoute，通过 ArgoCD 管理资源。然而，日志显示在切换瞬间出现了请求丢失。
根本原因 ：DNS 解析的滞后性。
当 A 记录从旧负载均衡器切换到新负载均衡器时，客户端缓存中的旧 IP 仍有效（受 TTL 限制）。如果此时直接删除旧的 Ingress 资源，指向旧 IP 的请求将无处可去，导致 502/504 错误。大多数迁移指南止步于“流量已转移”，忽略了这一关键窗口期的风险。
### 解决方案：加权 DNS 实现平滑过渡为了实现真正的零停机，团队采用了 ExternalDNS + AWS Route 53 加权记录 的策略。
- 并行运行：同时保留旧的 Ingress 和新的 HTTPRoute，两者指向相同的域名。
- 权重控制：
初始状态：Ingress 权重 100，HTTPRoute 权重 0。此时新网关已就绪但不接收流量。
- 切换时刻：将 Ingress 权重改为 0，HTTPRoute 权重改为 100。
- 自动管理：通过 ExternalDNS 监听资源注解（如 external-dns.alpha.kubernetes.io/aws-weight），自动同步 Route 53 记录。
优势 ：
- 零丢包：切换过程中，两个负载均衡器始终存活，只是流量比例变化。
- 秒级回滚：若新网关异常，只需将权重改回即可，无需重建 DNS 记录或重新部署资源。
- 控制器无关：此模式适用于任何支持 ExternalDNS 的 Gateway API 实现。
### 生产环境的额外考量在实际客户环境中，还暴露出两个关键问题：
- 多命名空间隔离：在 Gateway API 1.5 之前，主机名（Hostname）需在 Gateway 和 HTTPRoute 中重复定义。这打破了基础设施与应用的关注点分离，尤其在多环境共用集群时显得笨重。
- 规范演进：Gateway API 1.5 引入了 ListenerSet 资源，允许应用团队独立定义监听器，无需修改基础设施层面的 Gateway 资源。Envoy Gateway 已支持该特性（RC 阶段），这将极大改善多租户场景下的运维体验。
### 工程启示- 不要迷信“简单切换”：生产环境的迁移必须考虑 DNS 传播延迟和连接保持状态。
- 利用云原生工具链：ExternalDNS 不仅是 DNS 管理工具，更是流量治理的关键组件。
- 关注 API 演进：Gateway API 1.5 的 ListenerSet 是解决多命名空间配置痛点的关键，建议密切关注控制器对该特性的支持进度。
对于正在规划迁移的团队，建议先在 Kind 或本地集群中验证加权 DNS 方案，确保在正式割接前拥有可靠的回滚机制。
## 📝 AI 点评点评时间：2026-05-25 20:11 ｜ reviewer: DeepSeek V4 Flash核心贡献: 原文以真实客户案例为背景，解决从 Ingress NGINX 到 Gateway API 迁移中的零停机问题，核心方法是通过 ExternalDNS 与 AWS Route 53 加权 DNS 记录实现渐进式流量切换，并辅以 Envoy Gateway 作为控制器选型。
亮点: 博文精准抓住了原文的核心工程价值——加权 DNS 方案及其“控制器无关、回滚简单”的特性，以及第一次迁移因 DNS TTL 导致短暂停机的关键教训。原文中“大多数迁移指南止步于‘流量已转移’”这一痛点被博文突出强调，还原了从“成功但不够好”到“零停机”的迭代过程。此外，博文对 Gateway API 1.5 ListenerSet 的多命名空间隔离问题的提炼到位，点出了规范演进与控制器实现之间的时间差。
挑刺:
- 博文将“不再提供安全补丁和新功能更新”直接归因于 Ingress NGINX 控制器，原文实际表述是 “With no security patches, no new features, and an Ingress API frozen in place”，主语模糊。Ingress NGINX 社区仍在发布安全补丁，真正冻结的是 Ingress API 规范本身。博文写“功能冻结：Ingress API 规范已停滞不前”是准确的，但紧接着的“维护缺失：不再提供安全补丁和新功能更新”则容易误导读者认为 Ingress NGINX 控制器已 EOL。
- 博文在选型对比表中对 Istio 评价为“功能全面但较重”，原文仅写 “Comprehensive feature set”，并未提及“较重”。这一判断属于博文的主观添加，未引用原文依据，可能造成对 Istio 的偏向性解读。
- 博文遗漏了原文中关于 Envoy Gateway 贡献者数据的附注（“Envoy Gateway itself currently has 4 contributors with one organization at 51% or more”）。该数据是原文对单组织依赖风险的重要提示，博文未提及，削弱了选型透明度。
总评: ⭐⭐⭐½ 博文整体忠实反映了原文的工程案例和关键 insight，但在控制器维护状态和选型评价上有轻微术语偏差与过度解读，建议补充贡献者风险提示。
← 上一篇（更早） ⭐⭐⭐½ K8s策略执行太晚？把校验搬进代码评审 下一篇（更新） → ⭐⭐⭐ 最优传输重塑动态风险度量 ← 返回首页 © 2026 前沿研读 · Frontier Studies. All rights reserved.
📡 RSSfunction d(){const o=document.getElementById("article-toc");if(!o)return;const i=document.querySelectorAll(".prose h2, .prose h3");if(i.length {e.id||(e.id="h-"+c);const n=document.createElement("li");n.className=e.tagName.toLowerCase();const t=document.createElement("a");t.href="#"+e.id,t.textContent=(e.textContent||"").trim(),n.appendChild(t),s.appendChild(n),r.push({a:t,h:e})}),o.appendChild(s);const l=new IntersectionObserver(e=>{e.forEach(c=>{if(!c.isIntersecting)return;const n=r.find(t=>t.h===c.target);n&&(r.forEach(t=>t.a.classList.remove("active")),n.a.classList.add("active"))})},{rootMargin:"-80px 0px -70% 0px"});i.forEach(e=>l.observe(e))}d();
