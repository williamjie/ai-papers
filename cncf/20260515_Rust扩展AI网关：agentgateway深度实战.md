# Rust 扩展 AI 网关：agentgateway 深度实战

**日期**: 2026-05-15

---

原文 : Extending AI gateways with Rust: Custom transformations in agentgateway and kgateway来源 : https://www.cncf.io/blog/2026/05/15/extending-ai-gateway-with-rust-custom-transformations-in-agentgateway-and-kgateway/当 AI 应用从“能跑”走向“生产级”，标准网关策略（鉴权、限流、路由）往往显得捉襟见肘。你需要基于数据库动态注入 Header？需要自定义 Prompt 模板转换？现有开箱即用的过滤器根本覆盖不了这些长尾需求。这篇文章提供了一个极具实操价值的方案：利用 Rust 编写 Envoy 动态模块，无缝集成到 agentgateway 和 kgateway 中，实现完全自定义的请求/响应变换。
## 为什么是 Rust 和 Envoy 动态模块？
传统网关扩展通常依赖 Lua 脚本或 WebAssembly。Lua 性能瓶颈明显，Wasm 生态尚在成熟期。而 Envoy 原生支持的动态模块（Dynamic Modules）机制，允许以共享库（.so）形式加载代码，运行时加载无需重启代理。
选择 Rust 的核心逻辑很清晰：
- 零成本抽象：Rust 编译后的二进制文件直接调用 Envoy 的 C ABI，性能损耗极低。
- 内存安全：在高并发 AI 流量场景下，避免段错误导致网关崩溃至关重要。
- 生态成熟：envoy-proxy-dynamic-modules-rust-sdk 提供了完善的绑定，serde 处理 JSON 更是信手拈来。
## 架构拆解：本地零成本实验环境文章最巧妙的地方在于构建了一个完全本地化、零成本的测试闭环。没有云账单，没有复杂的密钥管理，只有纯粹的工程技术验证。
整个链路分为四层：
- 客户端：curl 发送 POST 请求。
- 数据平面：agentgateway-proxy (Envoy) 接收请求。
- 扩展层：自定义 Rust 模块 (.so) 拦截并修改请求。
- 后端模拟：httpbun 模拟 LLM 返回假响应。
这种架构解耦了 AI 业务逻辑与网关基础设施。你可以专注于网关层面的变换逻辑，而不必担心 LLM 调用成本或 API Key 泄露。
## 关键技术决策与坑点### 1. Rust 项目结构代码分为两个 crate：
- rustformations：核心过滤器，注册到 Envoy。
- transformations：辅助库，提供 Jinja 模板引擎和通用 Trait。
关键配置项 crate-type = ["cdylib"] 告诉 Rust 编译器生成 C 兼容的动态链接库。这是 Envoy 能加载它的前提。
### 2. 多阶段 Docker 构建为了保持生产镜像精简，采用了经典的多阶段构建：
- Stage 1 (Builder)：使用 rust:1.85 镜像编译代码，生成 librust_module.so。
- Stage 2 (Runtime)：基于 envoyproxy/envoy:v1.36.4，仅复制编译好的 .so 文件和启动脚本。最终镜像大小控制在 319MB 左右，既保留了构建工具的完整性，又避免了运行时携带庞大的 Rust 工具链。
### 3. Envoy 版本与 SDK 匹配这是最容易踩坑的地方。Envoy 的动态模块 API 变动频繁。文章明确指出，必须确保 Rust SDK 版本与 Envoy 版本严格对应。例如，Envoy v1.36.4 需要特定版本的 SDK，否则会出现 undefined symbol 错误。建议直接从 Envoy 源码目录复制 SDK 以确保一致性。
## 部署与验证部署流程标准化为 Kubernetes 资源：
- 安装 CRD：部署 Gateway API 和 agentgateway 自定义资源。
- 控制平面：通过 Helm 安装 kgateway (控制面) 和 agentgateway (AI 数据面)。
- 后端定义：定义 AgentgatewayBackend，指向本地的 httpbun 服务。
- 路由配置：创建 Gateway 和 HTTPRoute，将 /v1/chat/completions 路径流量导向后端。
测试时，通过 kubectl port-forward 将本地 8082 端口映射到网关，发送标准 OpenAI 格式请求即可验证。
## 工程启示- Mock 优先原则：在开发网关中间件时，使用 httpbun 这样的 Mock 服务可以极大降低调试成本。不要一上来就对接真实 LLM API，那只会增加噪音。
- 配置陷阱：Envoy 的 filter_config 需要包裹在 Protobuf Any 类型中（如 type.googleapis.com/google.protobuf.StringValue），否则解析会失败。这是一个文档中容易遗漏但实际部署必遇的细节。
- 生产化路径：从实验到生产，只需替换后端地址并引入 Kubernetes Secret 管理 API Key。agentgateway 原生支持通过 Policy CRD 实现鉴权、限流和可观测性，无需额外开发。
对于正在构建 AI 原生应用架构的团队，掌握 Rust 扩展 Envoy 的能力，意味着拥有了打破网关黑盒、实现极致灵活性的钥匙。这不仅是技术的延伸，更是架构自主权的体现。
← 上一篇（更早） AI 代码贡献者：KubeStellar 如何实现 81% PR 接受率 下一篇（更新） → 多教师协同蒸馏：CoRD 让长推理更高效 ← 返回首页 © 2026 前沿研读 · Frontier Studies. All rights reserved.
📡 RSSfunction d(){const o=document.getElementById("article-toc");if(!o)return;const i=document.querySelectorAll(".prose h2, .prose h3");if(i.length {e.id||(e.id="h-"+c);const n=document.createElement("li");n.className=e.tagName.toLowerCase();const t=document.createElement("a");t.href="#"+e.id,t.textContent=(e.textContent||"").trim(),n.appendChild(t),s.appendChild(n),r.push({a:t,h:e})}),o.appendChild(s);const l=new IntersectionObserver(e=>{e.forEach(c=>{if(!c.isIntersecting)return;const n=r.find(t=>t.h===c.target);n&&(r.forEach(t=>t.a.classList.remove("active")),n.a.classList.add("active"))})},{rootMargin:"-80px 0px -70% 0px"});i.forEach(e=>l.observe(e))}d();
