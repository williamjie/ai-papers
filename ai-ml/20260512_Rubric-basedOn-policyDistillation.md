# Rubric-based On-policy Distillation

**日期**: 2026-05-12

---

论文 : Rubric-based On-policy Distillation链接 : https://arxiv.org/abs/2605.07396在LLM的对齐训练中，On-policy Distillation (OPD) 已经成了标配。但有个致命痛点：主流OPD方法（如OPD、ExOPD）都依赖Teacher模型的Logits。这意味着你只能蒸馏开源模型，像GPT-4/5这样闭源且只提供文本接口的“黑盒”强者，你根本拿不到它的内部概率分布，只能望洋兴叹。
这篇来自新加坡国立大学、USTC和腾讯的论文提出了 ROPD (Rubric-based On-policy Distillation) ，核心思路非常性感： 既然拿不到Logits，那就用“评分细则”来替代。 它证明了，在复杂推理任务中，结构化语义指导比细粒度的Logits信号更有效，甚至能实现10倍的样本效率提升。
## 为什么Logits不够好？
传统白盒OPD假设Teacher的Logits是完美的监督信号。但论文指出，Logits本质上衡量的是“分布相似度”，而非“答案正确性”。
看一个直观例子：学生模型可能生成了与Teacher风格极度相似但逻辑错误的回答，Logits会给予高奖励；而学生模型可能生成了逻辑正确但表述新颖的回答，Logits反而给低分。这就是所谓的“拟合噪声，丢失真理”。
ROPD的设计直觉是：将“模仿Teacher的Token分布”转变为“遵循结构化的推理原则”。通过从Teacher和Student的对比中提炼出Prompt特定的Rubric（评分细则），用Rubric对Student的Rollout进行打分，从而引导策略优化。
## 方法拆解：ROPD是怎么工作的？
ROPD框架极其简洁，主要包含两个核心模块，且通常都由Teacher模型兼任：
-Rubric Induction (Rubricator)：
对于每个Prompt xx，收集 mm 个Teacher响应 YxTY^T_xT​ 和 nn 个Student Rollout YxSY^S_xS​。Rubricator通过对比这些响应，生成一组Prompt特定的Rubric Cx={ck}C_x = \{c_k\}​={ck​}。
每个Rubric项 ckc_k​ 包含文本标准 ρk\rho_k​ 和权重 wkw_k​。
关键设计：这组Rubric对同一个Prompt下的所有Student Rollout是共享的。这保证了组内奖励的一致性，非常适合GRPO等基于组的优化算法。
-Rubric-based Verification (Verifier)：
Verifier根据生成的Rubric对每个Student Rollout进行打分。对于第 ii 个Student回答和第 kk 条Rubric，计算二值结果 vi,k∈{0,1}v_{i,k} \in \{0, 1\}​∈{0,1}。
最终奖励 sis_i​ 计算为加权通过率：
si=∑k=1Kwkvi,k∑k=1Kwk+ϵs_i = \frac{\sum_{k=1}^K w_k v_{i,k}}{\sum_{k=1}^K w_k + \epsilon}​=∑k=1K​wk​+ϵ∑k=1K​wk​vi,k​​这个 sis_i​ 直接作为GRPO优化中的奖励信号。
核心Insight ：
- 盲评校准：Verifier在打分时，是“盲目”地对Teacher和Student响应一起评分，不暴露身份。这能消除因题目难度差异带来的偏差。如果只评Student，Verifier容易受题目难易影响，导致奖励坍缩。
- 多Teacher种子：使用多个Teacher响应（m=4m=44）来生成Rubric，能覆盖更多解题路径，防止Rubric坍缩为对特定“解题套路”的模仿，而是聚焦于“逻辑有效性”。
## 关键结果：黑盒胜白盒？
实验设置：Student为Qwen3-4B，Teacher为GPT-5.2-chat（黑盒场景）或Qwen3-30B-A3B（白盒场景）。数据为DAPOMath-17K。
### 1. 黑盒场景：碾压现有基线在只能访问Teacher文本输出的情况下，ROPD表现惊人：
模型 AIME24 AIME25 HMMT25 (Feb) HMMT25 (Nov) GPQA-D HealthBench IFEval GPT-5.2 (Teacher) 80.83 67.08 43.75 57.50 78.66 92.82 94.37 SFT (Static) 24.17 20.83 10.42 7.08 35.66 83.32 85.21 T-Judge 28.94 29.11 12.84 14.11 36.29 84.52 84.40 OVD 38.75 37.92 14.11 15.05 35.74 83.68 84.23 GAD 27.52 23.34 12.84 14.11 36.02 83.57 85.12 ROPD (Ours) 65.02 61.56 61.56 55.71 61.56 84.92 85.28注：表格数据摘自论文Table 1，ROPD在绝大多数基准上显著优于其他黑盒方法。
在最具挑战性的HMMT25 (Nov.)上，Base模型仅得7.08分，ROPD直接拉升至55.71分（+48.6%），甚至接近Teacher水平的57.50分。
### 2. 白盒场景：Text-only 击败 Logit-based更令人震惊的是，即使Teacher提供了Logits，ROPD（故意忽略Logits，仅用Text）依然表现强劲：
- AIME24: ROPD (63.33) vs LOPD (47.92) vs ExOPD (50.66)。ROPD领先LOPD达15.4个点。
- 样本效率: ROPD仅需1.6k样本即可达到LOPD的最佳性能（48.3%），而LOPD需要15.4k样本。样本效率提升近10倍。
- 收敛稳定性: LOPD在训练后期常出现性能退化（过拟合Teacher分布），而ROPD在整个训练过程中保持稳定上升。
## 工程启示- 黑盒蒸馏新范式：如果你无法获取闭源模型的Logits，ROPD提供了一种可行的、高性能的替代方案。它不需要Token对齐，支持跨架构蒸馏（如GPT-5蒸馏Qwen或Gemma）。
- 语义监督优于概率监督：在复杂推理任务中，明确的结构化标准（Rubric）比模糊的概率分布更能引导模型学到正确的逻辑。Logits容易诱导模型模仿“说话方式”，而Rubric强制模型关注“推理步骤”。
- 计算效率：虽然每步计算Rubric和Verifier增加了少量开销，但由于样本效率大幅提升，ROPD在Wall-clock时间上比LOPD快6.3倍（5.5h vs 34.4h）。
## 局限与展望- 任务类型：目前主要验证在数学、科学等推理任务上。对于主观性或创造性任务，Rubric的构建难度较大，效果待验证。
- 依赖Evaluator：ROPD的性能依赖于Rubricator和Verifier的能力。虽然论文证明用辅助LLM替换Teacher模型影响不大，但Meta-evaluation（对评估的评估）本身仍存在不确定性。
总的来说，ROPD不仅是一个实用的黑盒蒸馏工具，更提出了一个深刻的观点： 未来的OPD可能不再局限于更密集的数值信号（Logits），而在于更清晰的语义指导（Rubrics）。 对于工程师来说，这是一条值得深入探索的路径。
