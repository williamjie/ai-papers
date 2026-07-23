# 从打分器到验证器：Image Editing的RLHF新思路

**日期**: 2026-05-01

---

论文 : Leveraging Verifier-Based Reinforcement Learning in Image Editing链接 : https://arxiv.org/abs/2604.27505这篇论文干了一件有意思的事： 把图像编辑的 reward model 从”总分裁判”变成了”逐项质检员” 。
当前 T2I 生成已经玩转 RLHF（比如 DPO、GRPO），但图像编辑的 RLHF 还停留在 SFT 阶段。核心卡点在于—— 没有靠谱的 reward model 。图像编辑比 pure generation 复杂得多：既要改对地方，又要保住没动的区域，还得保持视觉质量。现有方法简单地把 VLM 当黑箱打分器，输出一个总分，结果是——要么偏科，要么幻觉。
Edit-R1 的核心洞察是： 图像编辑的 reward 必须是可验证的（verifiable），而不是可回归的（regressive） 。你不能问 VLM”这张图打几分”，而要问”这五个原则都满足了吗”。
## 方法拆解：两阶段训练一个”较真”的奖励模型### 阶段一：冷启动 SFT —— 用外脑筛出高质量的推理轨迹训练一个能”边想边评”的模型，最难的是第一批训练数据从哪来。论文的做法很实在：
-原则分解（Principle Decomposition）：用 Seed-1.5-VL 把编辑指令拆成三类原则：
Keep：哪些东西不准动（比如背景、主体）
- Follow：必须改的地方（颜色、位置、数量）
- Quality：通用视觉质量（无 artifacts、光影合理）
-大规模 quadruple 数据构造：对每条指令，用多个编辑模型（FLUX.Kontext、Bagel、SeedEdit-3.0）生成候选图，形成（原图、指令、原则集、编辑结果）四元组，总共约 200 万条。
-VLM 池生成 CoT：用多个 VLM 对每个四元组生成多份”思考过程 + 最终分”的推理轨迹。
-外部验证过滤：关键一步——再用一个独立的 SeedVLM-1.5 当”质量裁判”，重新检查每条推理轨迹中的原则验证是否准确。只留下准确率最高的那条 CoT 作为 SFT 数据。
这步”先让模型想，再用另一个模型验”的冷启动策略，相当于给模型配了个带教老师，确保它一开始就学会正确的检查逻辑。
### 阶段二：GCPO —— 用组间对比对齐人类偏好SFT 后的模型虽然会推理了，但判断可能还是”想当然”。比如指令说”左移一点”，它可能觉得”动了就算成功”，而人类会觉得”没动到位”。
标准 RLHF 算法（DPO、GRPO）直接优化 scalar reward，但 Edit-R1 的 RRM 输出的是 多步推理token + 最终分数的组合 ，整个过程是非连续的，没法直接求导。
Group Contrastive Preference Optimization (GCPO) 的解法很巧妙：
- 对每一对人类偏好的编辑对（胜者图 xw、败者图 xl），让 RRM 分别生成 N 条推理轨迹和分数- 计算跨组胜率：胜者组里每条推理的分数，要跟败者组所有 N 条比；败者组的每条，也要跟胜者组所有 N 条比- 胜率 = 赢过对方组多少条推理 / N；败率 = 输给胜者组多少条 / N- 然后在组内计算优势：胜者组里胜率越高的推理，优势越大；败者组里败率越高的，劣势越大- 最后用 GRPO 的 clipped surrogate loss 优化，但reward 是组间对比得出的胜率，优势是在组内标准化本质上是把” pairwise preference “转化成了” group-level advantage “，让非连续的 CoT 生成过程也能用 RL 优化。
### 阶段三：下游编辑模型训练 —— 用 GRPO 做RLHF训练好的 RRM 作为非可微的 verifier， plugged 进标准的 GRPO 流程里优化编辑模型（FLUX.Kontext、Qwen-Image-Edit）。对每组生成结果，用 RRM 打分后在组内归一化得到 advantage，驱动 policy 更新。
## 关键结果：稳 but 不暴Model (7B) Internal Benchmark Accuracy EditRewardBench Accuracy Seed-1.5-VL (API) 79.3% — Edit-RRM (SFT only) 75.4% 73.3% Edit-RRM (SFT + GCPO) 82.2% 78.2%编辑模型提升（FLUX.Kontext 家族）：
Metric Baseline + RL-RRM (7B) 提升 Overall Score (O) 5.77 6.24 +8.2% Semantic Consistency (SC) 6.27 6.86 +9.4% Motion Change 类别 SC 4.01 4.62 +15.2%几个有意思的点：
- Scaling Law 依然有效：3B → 7B，准确率从 75.4% 提到 82.2%，说明更大的模型确实能更好地执行原则分解和 CoT 推理- GCPO 是质变关键：同样的 SFT 数据，加上 GCPO 后在公开 benchmark 上从 73.3% 跳到 78.2%，远超 EditScore-7B 的 65.9%- Human Evaluation 验证：优化后的 FLUX.Kontext 相比原始 baseline 的 GSB score 达到 +23.2，用户确实能感知差异- 对强基线也有用：Qwen-Image-Edit 本身已经很强，整体分只从 7.45 提到 7.50，但在它薄弱的 Motion Change 类别硬生生拉了 15.2%## 工程启示-Reward 要拆得足够细：图像编辑的奖励必须对应到可验证的子任务。原则分解的三分类（Keep/Follow/Quality）是个实用模板，比笼统说”评估编辑质量”可操作得多。
-冷启动数据质量控制 > 数据量：论文用 200K 数据点（ quadruple ）做 SFT，但关键是用另一个 VLM 做外部验证筛选。如果你要做类似的事，与其堆数据，不如先想想怎么给种子数据配个”质检员”。
-RL for Reasoning Models 的通用解法：当 reward 本身是生成式推理模型时，GCPO 的”组间对比、组内优势”思路可以复用。核心是：别直接 optimize 非连续 output，用 pairwise preference 构造 group-level advantage signal。
-成本与收益权衡：GCPO 只用了 10k 人类偏好对（不到 SFT 数据的 1%），但提升显著。这说明高质量偏好数据 + 针对性 RL 算法 > 盲目扩大 SFT 规模。
-Verifier 的 downstream 价值：训练好的 RRM 不仅能当 reward，还能当评估工具——组内归一化的 advantage 让它 naturally 成为一个更严格的裁判，这对模型迭代很实用。
## 局限与边界论文没明说但能看出来的限制：
- 成本高：冷启动要调用 VLM 池生成并验证 200 万条 CoT，部署时每次 reward 调用也要做多步推理。不适合实时场景- 依赖强 VLM 做数据构造：原则分解和外部验证都靠 Seed-VLM-1.5，如果换 weaker 的模型，数据质量会滑坡- Motion Change 提升显著，其他类别温和：说明这个范式在细粒度、难以量化的编辑任务上收益最大，对简单颜色替换等任务优势不明显- 原则手动设计：Keep/Follow/Quality 三类原则是人工设定的，是否覆盖所有编辑类型？复杂指令可能需要更多/不同的原则维度## 一句话总结不是所有reward model都要回归一个数，有时候”逐项打勾”比”总体打分”更可靠——特别是在编辑这种既要精准又要保质的任务上。
