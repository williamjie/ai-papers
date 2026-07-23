# 给Agent装个全局脑回路：StraTA策略抽象强化学习

**日期**: 2026-05-09

---

论文 : StraTA: Incentivizing Agentic Reinforcement Learning with Strategic Trajectory Abstraction链接 : https://arxiv.org/abs/2605.06642现在的LLM Agent在长程任务里经常“走一步看一步”，导致前面走错后面一直补救，甚至原地打转。这篇来自港中文、上海AI实验室和牛津大学合作的StraTA论文，直接指出了痛点： 纯反应式（Reactive）决策切断了长期规划与短期执行的联系 。它通过引入显式的“轨迹级策略（Trajectory-level Strategy）”，让Agent先想清楚再动手，在ALFWorld、WebShop和SciWorld上大幅超越了现有基线。
## 为什么纯反应式Agent不够用？
在传统的Agentic RL中，Agent在每个时刻 tt 只根据当前状态 sts_t ​ 决定动作 ata_t ​ 。这种设计看似简洁，实则隐藏了两个致命缺陷：
- 短视探索：Agent同时承担“长期规划”和“即时执行”的双重压力，容易陷入局部最优。
- 信用分配难：奖励通常在episode结束时才稀疏给出，很难判断哪一步是关键动作。
StraTA的核心Insight非常直观： 人类解决问题时，会先形成一个高层计划，再执行具体动作。 如果Agent也能先采样一个紧凑的自然语言策略 zz ，并在全过程固定这个策略，就能将复杂的长程决策解耦为“生成好策略”和“忠实执行策略”两个子目标。
## 方法拆解：分层GRPO与双重增强StraTA并不是简单地在Prompt里加一句“请制定计划”，而是从RL训练机制上做了重构。
### 1. 分层策略执行在Episode开始时，Agent基于初始状态 s1s_1 ​ 采样策略 z∼πθ(⋅∣s1)z \sim \pi_\theta(\cdot|s_1) π θ ​ ( ⋅ ∣ s 1 ​ ) 。随后的每一步动作 ata_t ​ 都同时 conditioned 于全局策略 zz 和局部状态 sts_t ​ ：
at∼πθ(⋅∣z,st)a_t \sim \pi_\theta(\cdot | z, s_t) ​ ∼ π θ ​ ( ⋅ ∣ z , s t ​ )
这意味着， zz 作为一个固定的前置信号，始终引导Agent的行为方向，避免了上下文过长导致的注意力分散。
### 2. 层级化GRPO训练为了同时优化策略生成和执行动作，StraTA设计了一个双层Group结构：
- 策略层：采样 NN 个策略，每个策略下执行 MM 次Rollout。
- 动作层：在同一个策略 ziz_i​ 下的 MM 个Rollout组成一个Group，用于比较动作优劣。
关键设计细节 ：
- 策略奖励计算：StraTA没有简单平均所有Rollout的奖励，而是取表现最好的前 δ\delta 分数的均值（Top-δ\delta Mean）。这能有效抑制早期动作噪声对策略质量评估的干扰，更真实地反映策略本身的价值。
- 多样性采样（Diverse Strategy Rollout）：为了防止采样出的策略过于雷同，论文引入了最远点采样（Farthest Point Sampling）。通过预训练Embedding模型计算语义相似度，贪婪地选择彼此差异最大的策略。这极大地拓宽了策略空间的探索范围。
- 关键自我判断（Critical Self-Judgment）：为了解决信用分配，Agent在Rollout结束后会自我审查，标记出那些“既未遵循策略又未推进任务”的无效步骤，并施加辅助惩罚。这迫使Agent不仅关注最终结果，还要关注过程的合规性。
## 关键结果：小模型也能打实验在三个主流Benchmark上进行，结果非常扎实。StraTA在1.5B和7B参数规模下均取得了SOTA性能。
ALFWorld 和 WebShop 表现对比 (Qwen2.5 Backbone)
Method Backbone ALFWorld Succ. WebShop Score WebShop Succ. GiGPO 1.5B 86.7% 52.8% 65.0% StraTA 1.5B 90.7% 82.5% 82.5% GiGPO 7B 96.2% 68.9% 72.8% StraTA 7B 93.1% 84.2% 84.2% GPT-5.1 - 72.9% 22.2% 22.2%注：数据源自论文Table 1。StraTA在1.5B规模下超越GiGPO约4-17个百分点，在7B规模下超越GiGPO在WebShop上约15个百分点。
SciWorld 表现在更复杂的科学实验任务SciWorld上，StraTA (7B) 取得了 63.5% 的整体得分，不仅超越了Grpo和PPO基线，还击败了GPT-5.1和Claude-4-Sonnet等闭源模型。特别是在Lifespan子集上，StraTA达到了完美的 100.0% 得分。
## 工程启示- 策略显式化是长程任务的关键：对于复杂的Agent任务，不要试图让模型在每一步都“即兴发挥”。强制引入一个高层Plan阶段，能显著降低探索难度，提升轨迹的一致性。
- 分层奖励优于单一奖励：在Agentic RL中，区分“策略好坏”和“执行优劣”非常重要。使用Top-δ\delta奖励评估策略，可以避免因为某次执行失误而错误地否定一个优秀的策略。
- 计算开销可控：尽管StraTA增加了策略采样和自我判断步骤，但论文实验显示（Figure 3），其每步Wall-clock time仅比GRPO略慢，且自我判断的开销仅占总Rollout时间的极小部分（约 1/H1/H），工程落地性价比很高。
## 局限与展望StraTA并非完美。其性能高度依赖于生成的策略质量，如果初始策略偏差过大，后续执行可能会受到限制。此外，当环境发生剧烈变化时，固定的全局策略可能变得僵化。未来的方向可能在于如何让策略具备动态调整的能力，或者在长程任务中引入更细粒度的策略修正机制。
