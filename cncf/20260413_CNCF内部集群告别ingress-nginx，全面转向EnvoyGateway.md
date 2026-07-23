# CNCF 内部集群告别 ingress-nginx，全面转向 Envoy Gateway

**日期**: 2026-04-13

---

原文 : ingress-nginx to Envoy Gateway migration on CNCF internal services cluster来源 : https://www.cncf.io/blog/2026/04/13/ingress-nginx-to-envoy-gateway-migration-on-cncf-internal-services-cluster/ingress-nginx 宣布退休的消息，对 K8s 社区来说不算新闻。真正值得看的是 CNCF 自己怎么迁的——不是 PPT 迁移，而是生产集群上真刀真枪的操作记录。他们选了 Gateway API + Envoy Gateway 这条路径，踩了不少坑，也留下了不少可复用的配置模式。
## 为什么值得看很多团队对 ingress-nginx 有感情，觉得”能用就不换”。但 CNCF 这次迁移的核心驱动力很明确：ingress-nginx 不维护了，而 Gateway API 已经是 K8s 的事实标准。更重要的是，他们的架构决策暴露了一个很多人忽略的问题—— Gateway API 不等于要多建 LoadBalancer 。
## 痛点：ingress-nginx 的单一架构ingress-nginx 的设计很直接：一个 LoadBalancer 服务，所有流量进来，按 Ingress 对象分发。简单粗暴，但也意味着所有策略、证书、监听器都绑在一起。
Gateway API 的多层架构提供了更大的灵活性，但灵活是有代价的——如果每个 HTTPRoute 都创建一个 Gateway 对象，每个 Gateway 又对应一个 LoadBalancer，成本会直接爆炸。
CNCF 的做法是 共享 Gateway 模式 ：一个 Gateway 对象服务于多个 HTTPRoute（codimd、GUAC、kcp 三个服务共用一个 Gateway）。这其实是 ingress-nginx 架构的等价替代，同时保留了 Gateway API 的扩展能力。
## 架构对比维度 ingress-nginx Gateway API + Envoy Gateway 流量入口 单个 LoadBalancer 可选共享 Gateway，单 LoadBalancer 证书管理 Ingress annotation certificateRefs + ReferenceGrant 后端协议 annotation 配置 BackendTLSPolicy 资源 跨命名空间 受限 ReferenceGrant 显式授权 水平扩展 HPA 支持 EnvoyProxy 资源控制 HPA## 关键踩坑记录### 1. externalTrafficPolicy 的坑这是整篇文章最有价值的技术细节。默认值是 Local ，意思是 NodePort 只在运行了 Envoy Pod 的节点上监听。Oracle Cloud 的负载均衡器对没有 Pod 的节点做健康检查时，直接判定后端不健康，流量全部丢弃。
改成 Cluster 就好了。这个问题在官方文档里藏得很深，CNCF 团队是碰壁之后才定位到的。如果你的云厂商负载均衡器做节点级别健康检查，大概率会遇到同样的问题。
### 2. 证书级联删除cert-manager 创建的 Certificate 资源默认带有 ownerReference，指向创建它的 Ingress 对象。删 Ingress 的时候，Certificate 和对应的 Secret 会被级联删除。迁移时直接删旧 Ingress，证书就没了。
他们用一个 jq 一行命令清掉了所有指向 Ingress 的 ownerReference：
kubectl get certificate -A -o json | jq -r '.items[] | select(.metadata.ownerReferences[]? | .kind == "Ingress") | "\(.metadata.namespace) \(.metadata.name)"' | while read NS NAMEdokubectl patch certificate $NAME -n $NS --type=json \-p= '[{"op": "remove", "path": "/metadata/ownerReferences"}]'done这个命令建议所有做类似迁移的团队收藏。
### 3. 跨命名空间证书访问Gateway 在 envoy-gateway 命名空间，证书在 guac、auth、codimd 等不同命名空间。Gateway API 默认不允许跨命名空间引用 Secret，必须通过 ReferenceGrant 显式授权。每个有证书的命名空间都要配一个。
### 4. 后端 HTTPS 代理有一个服务需要用 HTTPS 连接后端（kcp-front-proxy），原来的 ingress-nginx 用 annotation 配置了 backend-protocol: HTTPS 和 proxy-ssl-secret 。在 Gateway API 里，这个能力由 BackendTLSPolicy 资源提供：
apiVersion : gateway.networking.k8s.io/v1kind : BackendTLSPolicyspec :
targetRefs :
- group : ''kind : Servicename : kcp-front-proxyvalidation :
caCertificateRefs :
- name : kcp-cagroup : ''kind : Secrethostname : api.services.cncf.io注意这里的 hostname 字段——它做了服务端证书校验，不只是加密传输。
## Day 2 操作：证书自动续期迁移只是第一步。证书到期怎么办？CNCF 给了完整的 cert-manager + Gateway API 集成方案：
- 启用 cert-manager 的 Gateway API 支持：helm values 里加 enableGatewayAPI: true- 更新 ClusterIssuer：把 http01 solver 从 ingress 改成 gatewayHTTPRoute- 给 Gateway 加 annotation：cert-manager.io/cluster-issuer: letsencrypt-prod- 拆分 listener：每个域名一个 HTTPS listener + 对应的 HTTP listener（用于 HTTP-01 验证）。不能用一个 listener 包所有域名，除非用 DNS 验证最后一步删掉所有 ReferenceGrant，因为新证书直接生成在 Gateway 同命名空间，不需要跨命名空间引用了。
## 工程启示共享 Gateway 不是可选项，是必选项。 除非你的场景真的需要隔离（比如不同团队独立管理），否则一个 Gateway 对应一个 LoadBalancer 的成本是不可接受的。云厂商的 LB 不是免费的。
迁移策略上，CNCF 选了全量切换而非灰度。 他们没做双 IP 轮询，而是直接让 Envoy Gateway 接管现有 IP。对于他们这种流量不大的内部服务集群，这是合理的——风险可控，操作极简。如果你的集群承载的是核心业务，建议还是走双 IP 灰度路线。
Gateway API 的学习曲线不低。 ReferenceGrant、BackendTLSPolicy、EnvoyProxy 这些新资源类型，不是看文档就能搞懂的。建议先用 ingress2gateway 工具做初步转换，再手动调整。
## 谁应该关注- 还在用 ingress-nginx 的团队：迁移时间表已经摆在桌面上了- 正在评估 Gateway API 实现的企业：Envoy Gateway 是成熟选项，但要做好 Day 2 规划- 云厂商 K8s 用户：不同云厂商的 LB 健康检查行为差异很大，externalTrafficPolicy 这个坑可能以不同形式出现ingress-nginx 的落幕不是技术问题，是生态问题。Gateway API 标准化之后，真正的赢家是那些愿意在架构层面提前布局的团队。
← 上一篇（更早） 淘宝虚拟试穿大模型拆解：从MMDiT到RL，如何做到3.9秒出图 下一篇（更新） → AI 漏洞扫描泛滥：云原生项目如何自救 ← 返回首页 © 2026 前沿研读 · Frontier Studies. All rights reserved.
📡 RSSfunction d(){const o=document.getElementById("article-toc");if(!o)return;const i=document.querySelectorAll(".prose h2, .prose h3");if(i.length {e.id||(e.id="h-"+c);const n=document.createElement("li");n.className=e.tagName.toLowerCase();const t=document.createElement("a");t.href="#"+e.id,t.textContent=(e.textContent||"").trim(),n.appendChild(t),s.appendChild(n),r.push({a:t,h:e})}),o.appendChild(s);const l=new IntersectionObserver(e=>{e.forEach(c=>{if(!c.isIntersecting)return;const n=r.find(t=>t.h===c.target);n&&(r.forEach(t=>t.a.classList.remove("active")),n.a.classList.add("active"))})},{rootMargin:"-80px 0px -70% 0px"});i.forEach(e=>l.observe(e))}d();
