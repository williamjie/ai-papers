# ⭐⭐⭐ DRIFT：用加权 SFT 替代多轮 RL

**日期**: 2026-06-02

---

论文 : DRIFT: Decoupled Rollouts and Importance-Weighted Fine-Tuning for Efficient Multi-Turn Optimization链接 : https://arxiv.org/abs/2605.31455让大模型学会“听劝”并自我修正，是构建智能体（Agent）的核心痛点。
目前的工程实践面临一个死结：在线强化学习（Online RL）效果好但贵得离谱；离线监督微调（SFT）便宜但容易陷入分布偏移。
DRIFT 论文提出了一种优雅的解法：用加权 SFT 完美替代多轮 RL，既保留了 RL 的效果，又拥有 SFT 的速度。
### 为什么多轮优化这么难？
在数学推理或复杂任务中，模型犯错是常态。用户给出“答案错误，请重试”的反馈，模型需要修正。
现有的两条路都很窄：
- 在线 RL（如 PPO、UFO）：为了更新策略，必须不断生成完整的交互轨迹。多轮对话越长，Rollout 成本越高，计算开销呈指数级增长。
- 离线 SFT：直接用“错误-修正”的数据对训练。模型往往只学会了第一轮的准确率，遇到后续反馈时直接摆烂或重复错误（Behavioral Collapse）。
DRIFT 的核心洞察在于： KL 正则化的 RL 目标，在数学上等价于重要性加权的监督学习。
这意味着，我们不需要在线交互，只需离线采样一次，算出权重，然后像跑普通 SFT 一样训练即可。
### DRIFT 是怎么设计的？
DRIFT（Decoupled Rollouts and Importance-Weighted Fine-Tuning）将过程拆分为两个完全解耦的阶段：
1. 离线轨迹生成与加权使用固定的参考策略（Reference Policy）一次性采样多条多轮交互轨迹。
关键步骤是计算每条轨迹的权重 w(τ)w(\tau) ：
w(τ)=exp⁡(R(τ)/β)Z(x)w(\tau) = \frac{\exp(R(\tau)/\beta)}{Z(x)} Z ( x ) e x p ( R ( τ ) / β ) ​- Return 设计：不仅看最终对错，还引入折扣因子 γ\gamma 鼓励尽早修正，并惩罚重复错误。
- Prompt 级归一化：分母 Z(x)Z(x) 确保权重在同一问题的不同解法间相对合理，避免方差爆炸。
2. 终端步加权 SFT这是工程上的一个精妙近似。
理论上应该对整条轨迹加权，但 DRIFT 发现： 只给最终成功的“最后一击”加高权重效果更好。
反直觉发现 ：如果给中间的错误尝试也加上高权重，模型会学习到“被拒绝的路径也是好路径”，导致梯度噪声变大。
论文实验证明（Figure 3），仅监督终端步（Terminal-step）的准确率更高，且训练曲线更平滑。
### 效果与效率对比DRIFT 在 Qwen2.5-3B 和 Llama3.1-8B 上进行了广泛测试，结果非常硬核。
1. 性能碾压 SFT，持平甚至超越 RL以 Qwen2.5-3B 为例（Table 1）：
- MATH 基准：SFT 提升 +12.9%，在线 RL (UFO) 提升 +17.2%，DRIFT 达到 +17.6%。
- 通用推理 (GPQA)：SFT 仅微涨，而 DRIFT 大幅提升 +24.8%，远超 SFT 的 +1.4%。
2. 训练效率接近纯 SFT这是工程落地最关心的部分（Figure 6）：
- UFO (在线 RL)：随着轮数增加，GPU 时间急剧上升（5 轮时耗时是单轮的数倍）。
- DRIFT：由于 Rollout 是一次性的离线操作，训练阶段的 GPU 耗时与 SFT 几乎持平。
方法 MATH 提升 (Qwen-3B) GPQA 提升 (Qwen-3B) 训练效率特征 SFT-5turn +12.9% +1.4% 极高，但效果差 UFO-5turn +17.2% +23.3% 极低，Rollout 成本高 DRIFT-5turn +17.6% +24.8% 高，接近 SFT### 工程启示与局限对工程师的价值：
- 低成本构建 Agent：如果你需要模型具备多轮自我修正能力，不要再折腾复杂的 PPO 或 GRPO 流程。用 DRIFT 的加权 SFT 方案，算力成本降低一个数量级。
- 数据构造策略：不需要人工标注“正确路径”。只需让基础模型跑多几轮，自动收集“错误-反馈-修正”轨迹，按公式算权重即可。
局限与边界：
- 依赖参考策略质量：DRIFT 的离线采样来自 Reference Policy。如果基础模型连“第一次尝试”都做不好，采样的轨迹可能全是垃圾，加权也无济于事（Garbage in, garbage out）。
- 终端步近似：虽然论文证明了终端步加权更好，但这依然是一种近似。对于极长且复杂的推理链条，中间步骤的信用分配可能仍有优化空间。
DRIFT 证明了在特定设定下，我们不需要真正的在线强化学习也能获得其收益。这是一个典型的“用数学等价性换取工程效率”的优秀案例。
## 📝 AI 点评点评时间：2026-06-02 02:19 ｜ reviewer: DeepSeek V4 Flash核心贡献: 原文旨在解决多轮交互中在线RL成本过高而离线SFT效果差（分布偏移、行为崩溃）的矛盾，核心方法是利用KL-正则化RL目标与重要性加权SFT的理论等价性，将rollout与优化解耦，通过固定参考策略离线采样轨迹并加权微调来实现多轮优化。
亮点: 博文准确抓住了DRIFT最关键的工程价值——用加权SFT替代在线RL从而大幅降低训练成本，并重点突出了“终端步保留”这一反直觉但有效的近似（引用Figure 3说明终端步监督效果更好）。博文对Return设计（折扣因子γ和重复惩罚）以及Prompt级归一化稳定权重的描述也清晰到位，这些正是原文中具有实操指导意义的细节。
挑刺:
- 数据引用混淆：博文表格中SFT-5turn在MATH上的提升写为“+12.9%”，但原文Table 1中SFT-5turn在MATH上的提升为+15.0%（53.3-38.3），而+12.9%实际上是单轮SFT的提升（51.2-38.3）。博文将单轮SFT的数据错误地归到了多轮SFT-5turn上，属于引用偏差。原文Table 1明确列出SFT-5turn的MATH值为53.3 ↑15.0，博文未忠实引用。
- 遗漏关键约束条件：博文未提及原文强调的适用边界——DRIFT适用于“short-horizon, verifier-guided correction with lightweight deterministic feedback”（原文Limitations节），且假设“deterministic transition dynamics with fixed feedback”（原文Problem Setup节）。博文将DRIFT描述为通用多轮优化方案，可能使读者忽略这些重要前提，导致过度泛化。
- 理论等价性表述过于简化：博文称“KL正则化的RL目标在数学上等价于重要性加权的监督学习”，但原文是通过Forward-KL作为Reverse-KL的替代来推导的，并依赖Lemma 3（realizability）和Lemma 4（local validity）保证近似有效性。博文未区分Forward与Reverse KL，也未提及realizability假设，可能造成“无条件等价”的误解。
总评: ⭐⭐⭐ 博文准确传达了DRIFT的核心思想和工程价值，但存在数据引用混淆和关键边界条件遗漏，总体忠实但略有瑕疵。
