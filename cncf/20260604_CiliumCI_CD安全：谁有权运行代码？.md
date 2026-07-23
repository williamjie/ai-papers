# ⭐⭐⭐ Cilium CI/CD安全：谁有权运行代码？

**日期**: 2026-06-04

---

原文 : Securing CI/CD for an open source project: Controlling who runs what来源 : https://www.cncf.io/blog/2026/06/04/securing-ci-cd-for-an-open-source-project-controlling-who-runs-what/开源供应链安全不再是理论话题。Axios、LiteLLM 等项目的被入侵，以及 SolarWinds 事件，都证明了构建系统（Build System）一旦失守，后果是灾难性的。
对于像 Cilium 这样运行在数百万 Kubernetes Pod 内核网络路径上的基础设施项目，供应链安全的防线必须筑在 CI/CD 阶段。
Cilium 团队近期分享了他们加固 CI/CD 的第一部分实践： 访问控制 。核心逻辑很直接：严格控制“谁”能触发构建，以及构建过程中允许执行“什么”代码。
这套方案不仅适用于 Cilium，任何使用 GitHub Actions 的开源项目都能直接复用这些模式。
### 痛点：信任边界在哪里？
CI/CD 最大的风险在于权限滥用。攻击者往往通过 PR 注入恶意代码，利用 CI 的高权限环境（如访问 Secret、推送镜像）进行横向移动。
传统的 CI 配置往往过于宽松：任何人提交 PR 都能触发测试，或者 pull_request_target 事件被误用导致执行了未经验证的代码。
Cilium 的做法是彻底切断“外部贡献者代码”与“CI 核心逻辑”之间的直接执行路径。
### 方案拆解：三层防御体系#### 1. 触发控制：Ariane Bot 与白名单谁有权力启动昂贵的 CI 流程？Cilium 没有开放给所有人，而是开发了一个内部 Bot —— Ariane 。
- 身份验证：只有 organization-members 团队的成员才能通过 PR 评论（如 /test）触发工作流。
- 显式白名单：配置文件中明确列出了允许触发的具体 Workflow。随机的外部评论者输入命令会被直接忽略。
这解决了两个问题：防止资源耗尽攻击，以及确保只有可信人员能启动关键测试套件。
#### 2. 代码隔离：两阶段 Checkout 模式这是全文最核心的技术细节。当需要构建 PR 中的代码时，Cilium 必须使用 pull_request_target （因为它需要访问仓库 Secret 来推送镜像）。但这带来了巨大风险： PR 中的恶意代码可能在 CI 中执行 。
Cilium 采用了 两阶段 Checkout 策略：
- 第一阶段（可信）：Checkout 基础分支（Base Branch，即已合并的代码）。从这里加载所有的 Composite Actions、脚本和签名逻辑。
- 第二阶段（不可信）：Checkout PR 分支。关键点来了：PR 代码仅作为 Docker Build Context，绝不作为脚本执行。
⚠️ 反直觉发现 ：很多安全扫描工具看到 pull_request_target + 二次 Checkout 就会报警。但 Cilium 证明，只要严格控制后续步骤不执行 PR 分支的任何 Shell 命令，且所有 Action 均来自可信的基础分支，这种模式是安全的。
#### 3. 审查门控：CODEOWNERS 强制介入谁有权修改 CI 配置？Cilium 利用 CODEOWNERS 文件设置了硬性门槛：
- .github/ 目录下的任何变更，必须经过 @cilium/github-sec（安全团队）和 @cilium/ci-structure 的审查。
- 自动批准工作流 (auto-approve.yaml) 甚至需要 Maintainer 级别的审批。
这意味着，没有任何人能在未经安全团队同意的情况下，悄悄修改 CI 的执行逻辑或权限配置。
### 工程启示：如何落地？
对于云原生项目，这套方案提供了可操作的清单：
控制点 Cilium 实践 你的行动建议 触发源 Ariane Bot + 团队白名单 限制 CI 触发权限，避免公开 PR 随意触发重型测试 执行环境 基础分支加载逻辑，PR 仅做上下文 避免在 pull_request_target 中直接 run: ./script.sh (来自 PR) 代码审查 CODEOWNERS 强制安全团队 Review 将 .github/ 目录的 Owner 设为安全或核心维护团队 凭证隔离 CI 凭证仅能推送到 -ci 标签 生产环境凭证与 CI 开发环境严格物理隔离### 局限与思考Cilium 坦诚地指出了当前的不足：
- 尚未实现 SLSA Provenance（软件供应链级别认证）。
- 缺少 PR 阶段的依赖关系实时审查。
- 部分内部引用仍指向 @main，计划迁移到独立的 Composite Actions 仓库以进一步解耦。
这表明安全是一个持续演进的过程，没有一劳永逸的“银弹”。
### 总结Cilium 的实践核心在于 最小权限原则 和 信任分离 。它不盲目相信任何输入，包括来自贡献者的代码和来自自动化工具的配置变更。
对于正在构建高安全标准 CI/CD 管道的团队来说，Cilium 的“两阶段 Checkout”和“Ariane 触发控制”是两个值得立即借鉴的技术决策。记住：在 CI 中，默认不信任任何外部输入，直到它被证明是安全的。
## 📝 AI 点评点评时间：2026-06-04 20:07 ｜ reviewer: DeepSeek V4 Flash核心贡献: 原文针对开源项目CI/CD供应链安全，通过分层访问控制（触发控制、代码隔离、审查门控、凭证隔离）来防止构建系统被滥用或恶意代码执行。
亮点: 博文准确抓住了原文的核心三层防御——Ariane Bot白名单控制触发、两阶段Checkout实现代码隔离、CODEOWNERS强制审查，并以表格形式给出落地建议，便于读者快速理解；同时指出了原文中“两阶段Checkout模式常被安全扫描工具误报但实为有意设计”这一反直觉洞察。
挑刺:
- 博文遗漏了原文中两阶段Checkout模式的关键安全保证细节：原文明确说明“No run: steps execute scripts from the untrusted checkout. Every shell block after the second checkout is written inline in the workflow YAML”，博文仅概括为“绝不作为脚本执行”，未提及所有shell命令均为内联写入YAML这一具体约束，读者可能误解为只要不直接执行PR中的.sh文件就安全。
- 博文未提及原文中针对“Untrusted data flows into exactly one trusted action”的输入过滤机制——原文指出set-runtime-image action会检查镜像引用以quay.io/cilium/开头并去除换行防止GITHUB_ENV注入，博文完全略过这一重要安全边界。
- 博文在“局限与思考”中写“尚未实现SLSA Provenance（软件供应链级别认证）”正确，但遗漏了原文同时提到的“no govulncheck in CI”（原文原文：no govulncheck in CI），仅说“缺少PR阶段的依赖关系实时审查”，不够完整。
总评: ⭐⭐⭐ 博文准确传达了原文的核心思想和主要措施，适合快速了解Cilium CI/CD安全实践，但对关键安全机制的具体实现细节有所简化，可能影响深度读者的理解。
← 上一篇（更早） ⭐⭐⭐ MeshWeaver：把网格生成从坐标预测升级为顶点编织 下一篇（更新） → ⭐⭐⭐ 模型合并太慢？用 I/O 预算剪枝专家权重 ← 返回首页 © 2026 前沿研读 · Frontier Studies. All rights reserved.
📡 RSSfunction d(){const o=document.getElementById("article-toc");if(!o)return;const i=document.querySelectorAll(".prose h2, .prose h3");if(i.length {e.id||(e.id="h-"+c);const n=document.createElement("li");n.className=e.tagName.toLowerCase();const t=document.createElement("a");t.href="#"+e.id,t.textContent=(e.textContent||"").trim(),n.appendChild(t),s.appendChild(n),r.push({a:t,h:e})}),o.appendChild(s);const l=new IntersectionObserver(e=>{e.forEach(c=>{if(!c.isIntersecting)return;const n=r.find(t=>t.h===c.target);n&&(r.forEach(t=>t.a.classList.remove("active")),n.a.classList.add("active"))})},{rootMargin:"-80px 0px -70% 0px"});i.forEach(e=>l.observe(e))}d();
