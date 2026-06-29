# ⭐⭐⭐ Cilium CI/CD 安全实战：凭证隔离与签名验证

**日期**: 2026-06-26

---

原文 : Securing CI/CD for an open source project, part 3: Credentials, verification, and what’s next来源 : https://www.cncf.io/blog/2026/06/26/securing-ci-cd-for-an-open-source-project-part-3-credentials-Cilium 团队这篇系列终章，揭示了顶级开源项目如何构建“纵深防御”的 CI/CD 体系。它不只是配置清单，更是关于“信任边界”的工程哲学。对于任何运行在 GitHub Actions 上的云原生项目，这都是必须参考的安全基线。
### 为什么凭证隔离是最后一道防线？
Cilium 的核心假设很残酷： 任何单一防御层都可能失效 。如果 CI 工作流被劫持，攻击者能否触及生产环境？答案是“不能”。
他们通过 GitHub Protected Environments 实现了严格的 凭证隔离（Credential Isolation） ：
- CI 凭证：仅能推送至 quay.io/cilium/*-ci 开发镜像仓库。即使工作流被攻破，攻击者只能污染开发环境，无法触及生产标签。
- 生产凭证：隐藏在 release 环境中，需要维护者手动批准才能访问。Fork 仓库、特性分支甚至普通的 CI 构建都无法读取这些密钥。
⚠️ 关键细节 ：所有 actions/checkout 都设置了 persist-credentials: false 。这防止了 GITHUB_TOKEN 泄露到 Runner 的 git config 中，避免后续步骤被恶意脚本窃取。
### 无密钥签名与 SBOM 自动化传统的签名方案依赖长期存储的私钥，一旦泄露后果灾难性。Cilium 采用 Sigstore Cosign 的无密钥（Keyless）OIDC 模式：
- 安装工具：固定使用 sigstore/cosign-installer@v4.1.1。
- 生成 SBOM：通过 anchore/sbom-action 生成 SPDX 格式的软件物料清单。
- 签名与关联：对容器镜像进行签名，并将 SBOM 作为声明（Attestation）附加到签名中。
这意味着消费者不仅能验证“谁签了名”，还能通过 SBOM 了解“里面有什么”。这种组合拳极大提升了供应链透明度。
### 诚实面对差距：我们还没做到什么？
最打动我的是 Cilium 团队对 现有缺陷的公开披露 。他们对照 OpenSSF Scorecard 和 SLSA 标准，列出了尚未解决的问题：
缺失项 现状与风险 改进计划 SLSA Provenance 未生成构建来源证明，用户无法验证构建过程 引入 slsa-github-generator 或启用 BuildKit 原生 provenance PR 依赖审查 仅靠 Renovate 被动告警已知漏洞 集成 actions/dependency-review-action 在合并前拦截恶意依赖 Go 漏洞扫描 未运行 govulncheck ，无法检测代码是否调用了脆弱函数 在 CI 中增加 govulncheck 步骤 内部引用可变性 68 处工作流引用了 @main 分支而非固定 SHA 将复合动作移至独立仓库，消除对主分支的依赖### GitHub 2026 路线图与我们的实践映射GitHub 发布的安全路线图验证了 Cilium 长期以来的痛点。特别是以下两点：
- 依赖锁定（Dependency Locking）：GitHub 计划支持 YAML 中的 dependencies: 字段，自动锁定所有直接和传递依赖的 SHA。这将彻底解决我们目前手动 Pin SHA 的繁琐问题。
- 作用域密钥（Scoped Secrets）：当前环境中所有工作流共享密钥。未来的作用域密钥允许将凭证绑定到特定工作流文件或分支，实现更细粒度的最小权限原则。
### 给云原生工程师的建议供应链安全不是“一劳永逸”的配置，而是不断追问“如果这个信任点被攻破会怎样”的过程。
- 立即行动：检查你的 GITHUB_TOKEN 权限，默认设为只读；启用 GitHub Releases 的标签不可变性（Tag Immutability）。
- 中期规划：引入 SBOM 生成和无密钥签名，这是行业合规的必经之路。
- 长期视角：关注 SLSA 框架和 GitHub 的新特性，逐步从“被动防御”转向“主动验证”。
开源供应链的安全水位取决于最弱的一环。Cilium 公开其防御细节，包括不完美的部分，正是为了提升整个社区的基准线。如果你也在维护开源项目，不妨对照这份清单，看看你的 CI/CD 管道是否足够健壮。
## 📝 AI 点评点评时间：2026-06-26 20:21 ｜ reviewer: DeepSeek V4 Flash核心贡献: 原文解决开源项目 CI/CD 供应链安全问题，核心方法是通过纵深防御——最小权限 GITHUB_TOKEN、生产/CI 凭证隔离、Sigstore 无密钥签名与 SBOM 附着，并结合公开审计和待改进清单来提升整体安全水位。
亮点: 博文准确抓住了原文最富工程价值的几个点：生产与 CI 凭证的物理隔离机制（通过 GitHub Protected Environments 分离 registry 权限）、无密钥签名与 SBOM 附着的自动化流水线，以及 Cilium 主动公开自身缺陷（如缺失 SLSA provenance、未运行 govulncheck）的透明做法。这些提炼到位，且用表格形式清晰呈现了原文的差距列表，便于读者对照检查。
挑刺:
- 博文遗漏了原文中关于 GITHUB_TOKEN 默认最小权限的关键设定。原文明确写道：“By default our GITHUB_TOKENs are scoped to minimal read permissions on contents and packages. Workflows that need anything more have to opt in explicitly”，而博文仅在文末建议中简略提到“检查你的 GITHUB_TOKEN 权限，默认设为只读”，正文中完全未展开这一重要的安全基线，导致读者可能忽略凭证隔离的第一层控制。
- 博文对原文“Additional layers”部分（Tag immutability、DCO sign-off enforcement、Third-party security audits）完全没有提及，原文明确将其列为“A few smaller things worth mentioning”，这些是 Cilium 安全体系中可操作的具体实践，博文的取舍导致内容不够完整。
- 博文在映射 GitHub 2026 路线图时只选取了“Dependency locking”和“Scoped secrets”，遗漏了“Policy-driven execution”“Native egress firewall”“Actions data stream”三个同样重要的规划，且未说明这是选择性提炼，可能给读者造成路线图仅包含这两项的误解。
总评: ⭐⭐⭐ 博文准确传达了原文的主要安全实践和待改进项，语言流畅且重点突出，但遗漏了 GITHUB_TOKEN 默认最小权限、Additional layers 等关键细节，对路线图的覆盖不够完整，整体忠实度足够但略有不���，属于合格的 AI 技术解读。