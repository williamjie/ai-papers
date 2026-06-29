# ⭐⭐⭐ Cilium CI/CD安全实战：如何锁死依赖供应链

**日期**: 2026-06-12

---

原文 : Securing CI/CD for an open source project: Locking down dependencies来源 : https://www.cncf.io/blog/2026/06/12/securing-ci-cd-for-an-open-source-project-locking-dependencies/Cilium 团队最近发布了一系列关于加固 CI/CD 流水线的深度文章。这是第二部分，专门讨论最容易被忽视、也最容易出事的环节： 依赖管理 。
在云原生时代，CI/CD 管道本身就是一个巨大的攻击面。如果你控制了谁能触发构建（第一部分的内容），但没控制住构建过程中拉取了什么代码，那你的流水线依然是敞开的。这篇文章详细拆解了 Cilium 如何通过“不可变引用”和“自动化信任边界”来锁死依赖供应链。
### 为什么 Tag 是不可信的？
很多团队习惯在 GitHub Actions 中使用 uses: actions/checkout@v6.0.2 。这看起来很稳，但本质上是 可变引用 。如果攻击者攻破了 actions/checkout 仓库并强制推送（force-push）恶意代码到 v6 tag，你的流水线就会自动执行恶意逻辑。
Cilium 的做法非常硬核： 所有 Action 必须通过完整的 40 位 Commit SHA 锁定 。
- uses : actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2这不仅适用于 Actions，连 Docker 镜像也通过 @sha256: 摘要锁定。这意味着无论上游 Tag 怎么变，你的 CI 始终运行在特定的、经过验证的代码版本上。
⚠️ 注意 ：目前 SHA 锁定有一个盲区—— 传递性依赖 。如果 A Action 引用了 B Action 的 Tag，攻击者可以通过篡改 B 来渗透 A。GitHub 计划在 2026 年推出工作流级别的依赖锁定机制（类似 Go 的 go.sum ），届时这一短板将被补齐。
### 自动化维护：Renovate 的信任边界手动维护 SHA 是反人类的行为。Cilium 使用自托管的 Renovate 机器人来自动化处理更新，但加了一层“信任冷却”机制：
- 发布冷却期：配置 minimumReleaseAge: 5 days。新发布的版本往往伴随着未被发现的供应链攻击风险，等待几天可以让社区先发现并撤回（yank）恶意包。
- 白名单自动合并：对于官方维护的高可信依赖（如 actions/, k8s.io/），Renovate 自动创建 PR 并在 CI 通过后自动合并。
- 身份校验：自动批准流程会严格检查 PR 作者是否为 cilium-renovate[bot]，防止有人伪造机器人账号提交恶意更新。
### Go 模块的“本地化”防御对于 Go 项目，Cilium 坚持使用 Vendoring（依赖打包） 。
- 切断外部连接：CI 构建时不访问外部模块代理（Module Proxy）。如果代理被投毒，你的构建不受影响。
- 可见性审查：所有依赖变更都体现为 vendor/ 目录的 Diff。代码审查时，人类可以看到具体的文件变化，而不是盲信一个版本号。
💡 反直觉观点 ：Cilium 不建议 Fork 所有第三方 Action 或 Go 模块。虽然 Fork 能物理隔离上游风险，但维护成本极高，且容易因同步滞后引入新的漏洞。 SHA 锁定 + 及时更新 是性价比最高的平衡点。
### 静态分析兜底即使策略再完美，人也会犯错。Cilium 引入了两层静态分析：
- CodeQL：强制检查工作流是否声明了 permissions。未显式声明权限的文件直接构建失败。
- actionlint：检查语法错误、不安全的模式（如使用 ubuntu-latest 而非固定版本）以及表达式注入漏洞。
特别是 GitHub Actions 表达式注入 ，这是一个隐蔽的杀手。如果在 run: 块中直接使用 ${{ github.event.pull_request.title }} ，攻击者可以通过标题注入 Shell 命令。正确的做法是先赋值给环境变量，再在 Shell 中引用。
### 工程启示对于任何严肃的云原生项目，依赖安全不是“最好有”，而是“必须有”。
- 立即行动：检查你的 CI 工作流，将所有 @tag 替换为 @sha。
- 引入自动化：使用 Renovate 或 Dependabot，但务必配置“发布冷却期”和严格的权限校验。
- 减少依赖树：Go 谚语说得好，“少量的复制胜过少量的依赖”。定期审计并移除那些只提供单一小功能的库，从根源上缩小攻击面。
安全是一个纵深防御体系。锁定依赖只是其中一环，但它是防止“特洛伊木马”进入构建过程的关键防线。
## 📝 AI 点评点评时间：2026-06-12 20:08 ｜ reviewer: DeepSeek V4 Flash核心贡献: 原文针对开源项目CI/CD流水线中依赖被篡改的供应链攻击风险，采用SHA摘要锁定所有GitHub Actions和容器镜像、自托管Renovate自动化更新并设置信任边界、Go模块vendoring、静态分析（CodeQL/actionlint）等多层防御方法。
亮点: 博文准确提炼了原文核心实践，包括“SHA锁定取代可变Tag”、“发布冷却期（5天）”、“白名单自动合并加身份校验”以及“表达式注入漏洞”的工程价值。对“是否Fork第三方Action”的权衡讨论（运维成本 vs 安全收益）也做了清晰呈现，抓住了原文最有工程新意的决策点。
挑刺:
- 博文在“身份校验”中只提及“严格检查PR作者是否为cilium-renovate[bot]”，但原文还检查了github.triggering_actor必须为cilium-renovate[bot]或auto-committer[bot]，这是防止攻击者伪造机器人身份的关键双重验证。博文遗漏此条件，削弱了安全机制描述的完整性。原文原文：“if: ${{ github.event.pull_request.user.login == ‘cilium-renovate[bot]’ && (github.triggering_actor == ‘cilium-renovate[bot]’ || github.triggering_actor == ‘auto-committer[bot]’) }}”
- 博文将“所有Action必须通过完整的40位Commit SHA锁定”作为通用规则，但原文明确对容器镜像使用@sha256: digest（64字符十六进制），而非“40位Commit SHA”。博文虽在后续提到Docker镜像也通过@sha256:锁定，但首句表述可能造成术语混淆。原文原文：“We pin container images used directly in workflow steps the same way, by @sha256: digest”。
- 博文在“自动化维护”一节未提及Renovate的matchUpdateTypes配置细节（如只匹配major/minor/patch的冷却期），以及白名单自动合并的groupName: "auto-merge-trusted-deps"分组机制，这些是原文中实现“信任边界”的重要工程参数。原文原文："matchUpdateTypes": ["major", "minor", "patch"], "minimumReleaseAge": "5 days" 和 "groupName": "auto-merge-trusted-deps"。
总评: ⭐⭐⭐ 博文基本忠实呈现了原文的依赖安全实践，虽有少量关键细节遗漏，但整体洞察准确，对读者理解Cilium的CI/CD加固思路有参考价值。