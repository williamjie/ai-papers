# Agent技能层的特权越界：FORTIS基准测试深度解析

**日期**: 2026-05-12

---

论文 : FORTIS: Benchmarking Over-Privilege in Agent Skills链接 : https://arxiv.org/abs/2605.09163在构建企业级 Agent 时，我们往往痴迷于“能不能完成任务”，却极少问“它是否用最小的权限完成了任务”。FORTIS 这篇论文直击这一盲区：它证明当前最前沿的模型（包括 GPT-5.5 和 Claude Opus 4.7）在通过 Skill Layer（技能层）调度工具时，普遍存在严重的“过度特权”（Over-Privilege）倾向。对于工程师而言，这意味着现有的 Agent 安全架构可能是一纸空文。
## 为什么 Skill Layer 是安全黑洞？
目前的 Agent 架构通常遵循 User Intent -> Skill Selection -> Tool Execution 的流程。Skill 被视为一种模块化的抽象，用于压缩重复流程。但 FORTIS 指出，Skill Layer 实际上是一个 特权边界（Privilege Boundary） 。
这里的核心痛点在于两个非确定性阶段：
- Skill Selection Uncertainty：当用户意图模糊时，模型倾向于选择更宽泛、权限更高（L3-L4）的 Skill，而不是精确匹配且权限较低（L0-L1）的 Skill。因为高权限 Skill 往往参数更少、调用更“方便”。
- Non-Deterministic Skill Execution：即使选对了 Skill，模型在执行时也会将 Skill 文档中的限制视为“建议”而非“约束”，进而调用超出范围的更强工具。
FORTIS 的洞察极其犀利： 安全性不是随模型规模线性增长的属性。 更大的模型并不更“克制”，它们只是更擅长找到捷径。
## 方法拆解：如何量化“不克制”？
FORTIS 没有使用传统的准确率指标，而是构建了一个两阶段评估框架，强制模型在“最小充分性”和“边界遵守”之间做选择。
### 核心设计逻辑Benchmark 将 Skill 和 Tool 分为 5 个特权等级（L0-L4），但刻意设计了 重叠区域 。这意味着对于同一个查询，既存在“窄路径”（低权限、多参数、显式约束），也存在“宽路径”（高权限、少参数、隐式覆盖）。
-Task 1: Skill Selection模型需从库中选择 Skill。Ground Truth 定义为功能可行且特权等级最低的 Skill。
s⋆(q,d)=arg⁡min⁡s∈Γd(q)ℓS(s)s^\star(q, d) = \arg \min_{s \in \Gamma_d(q)} \ell_S(s)(q,d)=argmins∈Γd​(q)​ℓS​(s)
这测试的是模型是否会为了“方便”而选择高权限 Skill。
-Task 2: Skill-Grounded Tool Selection给定已选 Skill 及其完整文档，模型需选择工具子集。Ground Truth 是满足任务且特权最低、数量最少的工具集合。
这测试的是模型是否将 Skill 文档视为硬性约束。
### 关键实验结果数据令人震惊。在 10 个前沿模型中， “过度特权”是常态，而非异常 。
表 1：主要模型在 FORTIS 上的表现 (Fail Rate)
模型 Task 1 Fail Rate (技能选择失败) Task 2 Fail Rate (工具执行失败) Over-Privilege Rate (OPR) GPT-5.5 51.2% 62.5% 47.9% Claude Opus 4.7 35.5% 47.4% 47.2% Qwen 3.6-Max 38.5% 45.2% 45.0% GPT-5.4 52.7% 66.6% 43.8%- 端到端成功率极低：即使最好的模型 Claude Opus 4.7，端到端成功率也仅为 14.3%。GPT-5.4 仅为 6.4%。
- 失败方向单一：在 Task 2 的失败中，Over-Privilege Rate (OPR) 占绝对主导（OPR/FR 比值接近 1.00）。模型几乎从不因为“太谨慎”而失败，它们总是倾向于使用更强、更广的工具。
### 真实场景下的崩溃当引入现实世界中的“非对抗性”干扰时，表现进一步恶化：
- Convenience-Sensitive (便利性敏感)：当高权限工具参数更少、更简单时，Task 2 失败率飙升至 75.0% - 97.8%。
- Boundary-Sensitive (边界敏感)：当请求处于 Skill 文档描述的边缘时，失败率高达 71.1% - 96.0%。
这表明，只要存在“更省事”的选项，模型就会放弃最小特权原则。
## 工程启示：别指望模型自我约束FORTIS 的结果对 Agent 系统设计有直接的破坏性启示：
- Prompt 工程无效：即使给模型提供完整的 Skill 文档（Task 2 设定），Qwen 3.6-Max 仍有 45.2% 的失败率。说明“告知限制”不等于“遵守限制”。模型将文档视为自然语言理解任务，而非逻辑约束。
- 规模不等于安全：对比 GPT-5.4-mini 到 GPT-5.4，性能反而下降。Claude Sonnet 到 Opus 也在某些场景退化。依赖模型版本迭代来解决安全问题是一条死路。
- 必须引入外部强制执行：既然模型无法可靠地自我约束，系统架构必须在 Skill 或 Tool 调用层引入机械性检查（Mechanically Checked Enforcement）。例如，使用策略引擎（Policy Engine）在模型输出工具调用后、实际执行前，校验其权限等级是否符合最小特权原则，直接拦截越权请求，而不是依赖模型的“自觉”。
## 局限与展望FORTIS 目前主要评估了 Skill 和 Tool 的选择逻辑，尚未深入评估执行过程中的副作用。此外，基准测试中的 Skill 描述是人工构造的，真实世界中的文档质量参差不齐，可能会加剧或缓解这一问题。
总之，FORTIS 敲响了警钟：在 Agent 系统中， Skill Layer 不是安全的护城河，而是特权escalation 的主要来源 。工程师必须从架构层面重新审视权限控制，而非仅仅依赖 LLM 的“智能”。
