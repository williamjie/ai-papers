# ⭐⭐⭐ STARE：用Surprisal加权拯救GRPO熵崩溃

**日期**: 2026-06-18

---

论文 : STARE: Surprisal-Guided Token-Level Advantage Reweighting for Policy Entropy Stability链接 : https://arxiv.org/abs/2606.19236做 LLM 强化学习（RL）的朋友一定遇到过这个噩梦：训练刚跑几百步，模型就“僵化”了。输出多样性消失，策略熵（Policy Entropy）直接归零，无论怎么调超参，性能就是上不去。这就是 GRPO 等算法的顽疾—— 策略熵崩溃 。
这篇来自清华和腾讯混元团队的 STARE 论文，不仅给出了一个极简的工程解法，更从一阶梯度层面把“为什么会崩溃”讲得明明白白。对于正在搞长思维链（Long CoT）或 Agent 训练的同学来说，这篇值得精读。
### 痛点：GRPO 的“信用分配错位”
现有的缓解方案大多在 trajectory（轨迹）级别打补丁，比如 DAPO 调整裁剪阈值，或者对正负样本加权。但这些方法太粗粒度了。
作者通过一阶梯度分析发现了一个反直觉的现象： 在 GRPO 中，同一个轨迹内的所有 token 共享同一个 Advantage 信号。
这就导致了严重的 信用分配错位（Credit Assignment Mismatch） ：
- 低 Surprisal Token（高频词）：采样概率高，数量庞大。在正 Advantage 轨迹中，它们主导了梯度更新，倾向于让分布更集中，导致熵降低。
- 高 Surprisal Token（低频/探索词）：虽然能增加熵，但因为采样少，其“增加熵”的贡献被海量低频词的“减少熵”贡献稀释了。
⚠️ 核心 Insight ：GRPO 的熵崩溃不是因为模型不想探索，而是因为梯度数学上天然偏向于“集中分布”。只要稍微放大那些“高 Surprisal + 正 Advantage” token 的权重，就能扭转整个批次的熵演化方向。
### 方法拆解：STARE 的极简设计基于上述理论，STARE 提出了一种 惊喜度引导的 Token 级优势重加权 机制。它的工程实现极其优雅，不需要改模型结构，只需在 Loss 计算时加一个权重系数 ωi,t\omega_{i,t} ​ 。
具体步骤如下：
- 识别关键 Token：在每个 batch 内部，按 Surprisal（−ln⁡π-\ln \pi）排序，选取 Top-P%（默认 10%）的高惊喜度 token。
- 双向调节：
放大：对于正 Advantage 且高 Surprisal 的 token，将其优势乘以权重 WW（默认 1.1）。
- 衰减：对于负 Advantage 且高 Surprisal 的 token，将其优势乘以权重 MM（默认 0.9，可选）。
- 闭环门控：设定目标熵 HtgtH_{tgt}​。只有当当前批次平均熵低于目标值时，才激活上述重加权；一旦熵恢复，立即退化为标准 GRPO。
这种设计利用了论文的**近临界性（Near-Criticality）**性质：只需要微小的权重扰动（如 W=1.1W=1.1 1.1 ），就足以翻转熵的演化方向，且对��参数不敏感。
### 关键结果：稳得住，更打得赢作者在 1.5B 到 32B 多个规模上进行了验证，结果非常硬核。
1. 训练稳定性对比（Qwen2.5-7B）
- GRPO-ds：训练约 1000 步后熵接近 0，AIME24/25 准确率见顶。
- STARE：稳定运行超过 5000 步，熵始终维持在目标带（~0.3），准确率持续攀升。
2. 性能提升（Table 1 数据）
在 Short CoT 场景下，STARE 全面碾压基线：
模型规模 基准方法 (GRPO-ds) STARE-O1 平均提升 AIME24/25 表现 7B Avg: 49.1% Avg: 54.4% +5.3% AIME24: 44.2% vs 39.8% 14B Avg: 46.1% Avg: 52.0% +5.9% AIME24: 24.2% vs 17.6% 32B Avg: 56.1% Avg: 60.7% +4.6% AIME24: 43.3% vs 38.1%在更具挑战性的 Long CoT（1.5B）场景下，STARE-O1 平均准确率 65.9%，比 SOTA 的 EAPO 高出 8.9% 。
### 工程启示- 别只盯着 KL 惩罚：传统的熵正则化往往容易过拟合或震荡。STARE 证明了在 Advantage 层面做精细化的 Token 级调节，效果更直接且稳定。
- 闭环控制是必须的：开环的重加权（一直放大）会导致过度探索。STARE 的 H < H_tgt 门控机制非常实用，建议在实际部署时务必加上。
- 超参数宽容度高：论文消融实验显示，WW 在 [1.05, 1.5] 之间表现都很稳健，Top-P% 在 5%-20% 也有效。这意味着落地时不需要极致的调参，开箱即用即可见效。
### 局限与展望STARE 目前主要验证在数学推理和工具使用场景。虽然理论通用，但在多模态或需要极低熵（如代码生成特定片段）的场景下，目标熵 HtgtH_{tgt} ​ 的设定可能需要更细致的动态策略。此外，论文未深入讨论在分布式训练通信开销上的影响，尽管其计算复杂度仅为排序和乘法，理论上开销极小。
总之，如果你正在被 RL 训练的熵崩溃困扰，STARE 提供了一个既有理论深度又极易落地的解决方案。
## 📝 AI 点评点评时间：2026-06-18 20:07 ｜ reviewer: DeepSeek V4 Flash0.30.20.10.001000200030004000Training StepsFraction of Selected Tokens1.00.80.60.401000200030004000Training Steps(a) Fraction of selected tokens that are within the the- (b) Cumulative net entropy contribution of the selected∗oretical entropy-increasing region (si,t > si,t).
token subset, computed as ∑(i,t)∈L+ Âi Φi,t .
qFigure 11: Validation of the high-surprisal quantile proxy on Qwen2.5-Math-7B-Base over 4000 RL trainingsteps, using W = 1.1, P = 10%, and Htgt = 0.3.
Qwen-1.5B, Qwen3-8B-Base), and the Tool-Use scenario(7B), a consistent pattern emerges: GRPO-dsexperiences entropy collapse and performance saturation, whereas STARE maintains stable entropy andcontinuous accuracy improvement. Notably, on DeepSeek-R1-Distill-Qwen-1.5B, the entropy of GRPO-dsdecays to below 0.2 by step 5000, whereas STARE rapidly restores the entropy to the target band startingaround step 3500, accompanied by corresponding improvements in AIME24/25 accuracy (Figure 7),which demonstrates the intervention-recovery capability of STARE and its robustness across scales andscenarios.
B.2Validation of the High-Surprisal Quantile Proxy.
To verify the effectiveness of the batch-internal high-surprisal quantile proxy for approximating the∗ , we conduct an empirical analysis ontheoretically defined entropy-increasing token set {si,t > si,tQwen2.5-Math-7B-Base over 4000 RL training steps (W = 1.1, P = 10%, Htgt = 0.3). As shown inFigure 11(a), the proportion of tokens selected by the top-P% quantile proxy that indeed belong tothe theoretical entropy-increasing region rises from approximately 60% in the early training stage toconsistently above 95% in the later stage. This demonstrates that as training stabilizes, the quantile proxybecomes increasingly aligned with the theoretical partition. Furthermore, Figure 11(b) shows that thecumulative net entropy contribution of the selected subset remains positive and monotonically increasing,confirming that the selected tokens consistently provide an entropy-increasing effect, consistent with thetheoretical predictions in Corollary 3.3. The above results indicate that the batch-internal high-surprisalquantile proxy reliably identifies entropy-critical tokens while avoiding the need for per-position solvingof Φ( p∗ ) = 0, thereby providing a computationally efficient and theoretically grounded approximationfor STARE.
B.3Detailed Effects of Single-Polarity and Combined Operations in STARE.
To validate the token-level reweighting mechanism under the four-quadrant decomposition and toinvestigate the effect of each operation, we conduct comprehensive ablation experiments on Qwen2.5Math-7B-Base over 4000 RL training steps. Table 2 and Figure 9 compare all four single-polarityoperations (O1–O4) and four combined operations (C1–C4). The results demonstrate that while GRPO-dsexperiences rapid entropy collapse, all eight variants of STARE effectively mitigate this collapse andachieve substantial improvements over GRPO-ds on AIME24/25. Among these, the single-polarityoperation O1 (amplifying L+q ) yields the best AIME24 accuracy (44.2%), while the combined operationC2 (amplifying L+andattenuatingL)
achievesthe best AIME25 accuracy (24.2%). Therefore, we adoptqqO1 as the default single-polarity configuration and C2 as the dual-sided variant. Moreover, among thecombined operations, those involving attenuation of L−q (C2, C4) consistently outperform those involving+attenuation of Lq (C1, C3) on both AIME24 and AIME25, suggesting that reducing the entropy-decreasingpressure from negative-advantage trajectories is more impactful than further modulating positiveadvantage tokens beyond the O1 baseline. Meanwhile, the single-polarity operations O2 and O4, whichattenuate tokens in low-surprisal regions, also achieve improvements over GRPO-ds, which alignswith the theoretical predictions in Proposition 3.2 and Corollary 3.3, confirming that low-surprisaltokens with entropy-decreasing effects also constitute a viable target for intervention. Overall, theexperimental results consistently support the four-quadrant decomposition and demonstrate that tokenlevel credit rebalancing guided by the advantage-surprisal structure is an effective approach to mitigatingpolicy entropy collapse in GRPO.
20Table 3: Ablation on target-entropy gating (Htgt = 0.3) under varying W on Qwen2.5-Math-7B-Base.
W1.01 1.051.11.21.52.03.04.0w/o Gate Entropy0.250.560.811.31 2.23 3.73 5.21 7.30AIME2433.8 34.0 34.8 35.4 35.9 36.1 35.2 34.9w/ Gate Entropy0.330.330.330.360.360.390.400.42AIME2444.7 44.4 44.2 44.5 43.8 43.1 42.7 42.5B.4Detailed Ablation on Key Hyperparameters and Target-Entropy GatingWe conduct a detailed ablation study of the key hyperparameters W, P, and the target-entropy gate onQwen2.5-Math-7B-Base, as presented in Table 3 and Figure 4. Under the open-loop configuration (withouttarget-entropy gating), as shown in Table 3, even W = 1.01 effectively alleviates the entropy collapse ofGRPO-ds, and W ≥ 1.05 leads to a steady increase in entropy. When W ≥ 2.0, entropy diverges, whichcorroborates the near-criticality property (Corollary 3.6) that beyond the critical threshold, the specificvalue of W controls the magnitude rather than the direction of the per-step entropy shift. However,open-loop reweighting stabilizes entropy at an excessively high level, which induces over-explorationand hinders overall training performance, as reflected by the lower AIME24 accuracy compared toclosed-loop gating at the same W value. In contrast, under the closed-loop gating (Htgt = 0.3), Table 3shows that for all W ∈ [1.01, 4.0], the policy entropy is constrained within the target band with boundedoscillations, confirming the stability and robustness of the closed-loop mechanism, which substantiallyreduces sensitivity to the choice of W.
Moreover, Figure 4(c) demonstrates the effect of varying the high-surprisal selection ratio P under fixedW = 1.1 and Htgt = 0.3. The results show that for P ∈ [5%, 20%], the entropy remains well withinthe target band, and even at P = 40%, the entropy stays within [0.1, 0.2], effectively preventing entropycollapse. These findings indicate that STARE is robust to both W and P, and the target-entropy gateprovides stable control over the policy entropy.
B.5Effectiveness of Target-Entropy Closed-Loop GatingTo further analyze the effectiveness of the target-entropy closed-loop gating mechanism, we comparethe entropy evolution of the open-loop and closed-loop variants at W = 1.1 in Figure 12. The open-loopvariant exhibits a continuously increasing entropy trend, which, as discussed in Appendix B.4, inducesover-exploration and leads to lower final AIME24 accuracy compared to the closed-loop variant (34.8%vs. 44.2%, as shown in Table 3). In contrast, the closed-loop gating mechanism constrains the entropywithin a bounded range centered near Htgt = 0.3, achieving a favorable exploration-exploitation balance.
Moreover, as shown in Figure 12, the closed-loop variant rapidly activates the reweighting mechanismwhen entropy drops below the target threshold (e.g., during the initial training phase) and deactivates itwhen entropy recovers, thereby demonstrating effective closed-loop regulation.
These results confirm the design principles established in Section 4: (i) open-loop reweighting alone isinsufficient for stable entropy regulation and may lead to over-exploration; (ii) the closed-loop gating0.60.5Entropy0.40.30.20.1GRPO-dsSTARE (w/o Gate)
STARE (w/ Gate)
0.0 01000200030004000Training StepsFigure 12: Comparison of entropy evolution between STARE with and without target-entropy gating onQwen2.5-Math-7B-Base (W = 1.1, P = 10%, Htgt = 0.3). The open-loop variant (w/o Gate) exhibitscontinuously increasing entropy, while the closed-loop variant (w/ Gate) constrains entropy within thetarget band.
21Table 4: Ablation on single-polarity (O1–O4) and combined (C1–C4) STARE operations on Qwen2.5-Math7B-Base over 4000 RL training steps (P = 10%, W = 1.1, M = 0.9, Htgt = 0.3).
MethodAIME24AIME25GRPO-dsSTARE-O1STARE-O2STARE-O3STARE-O4STARE-C1STARE-C2STARE-C3STARE-C437.144.240.539.642.143.142.539.941.717.723.820.321.619.923.524.220.822.6mechanism provides stable, bounded, and controllable entropy regulation; (iii) the combination oftoken-level reweighting and closed-loop gating achieves robust performance across diverse hyperparameter configurations.
B.6Details about Emergent Reflection Behaviors.
To investigate how STARE elicits deep reasoning, we analyze the tokens selected for advantage reweighting during RL training. As shown in the word cloud visualization in Figure 10, which is generated fromSTARE training on Qwen2.5-32B-Base, the reweighted tokens predominantly concentrate on uncertaintyand self-correction vocabulary, such as “should be,” “but,” “instead,” and “verification.” This observationconfirms that the batch-internal surprisal-quantile proxy effectively identifies rare forking tokens withexploratory semantics, which correspond to critical decision points in the reasoning chain(Wang et al.,2025b).
Reflection CountFurthermore, we conduct a detailed reflection behavior analysis by categorizing tokens selected forreweighting into six reflection categories: Self-Correction, Self-Questioning, Verification, Alternative,Re-evaluation, and Uncertainty, based on the linguistic patterns and lexical features of the tokens. Asshown in Figure 13, STARE markedly surpasses GRPO-ds across all six reflection categories, with thelargest margins observed in reflection and self-correction. This result demonstrates that STARE activatesdeep exploration and delivers consistent gains through token-level credit rebalancing that encouragesthe model to engage in more reflective and self-corrective reasoning processes.
GRPO-dsSTARE0Self-CorrectionSelf-QuestioningVerificationAlternativeRe-evaluationUncertaintyReflection CategoryFigure 13: Reflection token count comparison between STARE and GRPO-ds across six reflection categories on Qwen2.5-32B-Base in the Short CoT scenario.
22Table 5: Comparison of fixed and adaptive weighting strategies on Qwen2.5-Math-7B-Base over 4000 RLtraining steps.
StrategyAIME24AIME25EntropyFixed (W=1.1)
Adaptive (α=0.01, Wmax=1.5, Mmin=0.5)
44.244.823.824.10.330.31Table 6: Ablation on target entropy threshold Htgt on Qwen2.5-Math-7B-Base over 4000 RL training steps(W = 1.1, P = 10%).
HtgtAIME24AIME25Entropy0.20.30.443.744.243.923.123.823.50.230.330.42B.7Fixed vs. Adaptive WeightsWe compare fixed and adaptive weighting strategies on Qwen2.5-Math-7B-Base over 4000 RL trainingsteps. As shown in Table 5, the adaptive strategy achieves marginally better performance (44.8% onAIME24 vs. 44.2%) while maintaining a similar entropy level. However, the fixed-weight configurationalready yields strong performance, and the additional gain from adaptive weighting is modest, whichaligns with the near-criticality property that beyond the critical threshold, the specific weight valueprincipally controls the magnitude rather than the sign of the entropy shift. Given the simplicity androbustness of fixed weights, we adopt them as the default configuration. Detailed adaptive weightingformulations are provided in Section 4.4.
B.8Ablation on Target Entropy ThresholdWe examine the sensitivity of STARE to the target entropy threshold Htgt on Qwen2.5-Math-7B-Base over4000 RL training steps. As shown in Table 6, the performance is relatively stable across Htgt ∈ {0.2, 0.3, 0.4},with Htgt = 0.3 yielding the best AIME24 accuracy. When Htgt = 0.2, the entropy is constrained at a lowerlevel, which may limit exploration; when Htgt = 0.4, the higher entropy level may lead to excessiveexploration. The default value of Htgt = 0.3 achieves a favorable balance across all configurations.
B.9Ablation on Target-Entropy Gate GranularityWe compare three granularities of target-entropy gating: batch-level gating (default), sample-level gating,and token-level gating, as detailed in Appendix G.6. As shown in Table 7, the batch-level gating achievesa good balance between performance and computational efficiency (44.2% on AIME24). Sample-levelgating yields slightly higher AIME24 accuracy (44.6%), but at the cost of increased computationaloverhead. Token-level gating achieves 44.4% AIME24, which is comparable to batch-level gating, butincurs significantly higher complexity due to per-token gating decisions. Given its simplicity, efficiency,and competitive performance, we adopt batch-level gating as the default configuration.
Table 7: Ablation on target-entropy gate granularity on Qwen2.5-Math-7B-Base over 4000 RL trainingsteps (W = 1.1, P = 10%, Htgt = 0.3).
GranularityAIME24AIME25ComplexityBatch-level (default)
Sample-levelToken-level44.244.644.423.823.924.1O(1)
O(B)
O(N)
23Table 8: Validation of STARE under off-policy training on Qwen2.5-Math-7B-Base over 4000 RL trainingsteps.
MethodAIME24AIME25GRPO-ds (on-policy)
STARE (on-policy)
GRPO-ds (off-policy, η=0.5)
STARE (off-policy, η=0.5)
37.144.235.842.717.723.816.922.4Table 9: STARE vs. fixed-threshold low-probability token reweighting on Qwen2.5-Math-7B-Base over4000 RL training steps.
MethodAIME24AIME25GRPO-dsFixed-Threshold (τ=0.1)
STARE (P=10%)
37.139.244.217.719.323.8B.10Validation of STARE under Off-Policy TrainingTo evaluate the generality of STARE beyond the on-policy setting, we conduct additional experimentsunder off-policy training with an importance sampling ratio mixing factor η = 0.5 (i.e., the update usesa mixture of on-policy and off-policy samples). As shown in Table 8, STARE maintains a substantialimprovement over GRPO-ds in the off-policy setting, with AIME24 accuracy of 42.7% vs. 35.8% forGRPO-ds. This result confirms that STARE’s token-level credit rebalancing mechanism is effectiveregardless of whether the training data is strictly on-policy or contains off-policy samples, demonstratingthe generality of the proposed approach.
B.11STARE vs. Fixed-Threshold Low-Probability Token ReweightingWe compare STARE with a fixed-threshold baseline that selects tokens with πθ (oi,t | xi , oi,<t ) < τ (whereτ = 0.1) for advantage reweighting, which is a common heuristic in prior work. As shown in Table 9,STARE significantly outperforms the fixed-threshold approach (44.2% vs. 39.2% on AIME24), demonstrating the advantage of the theoretically motivated batch-internal surprisal-quantile proxy over a fixedprobability threshold. The fixed threshold fails to adapt to the evolving distribution during training,whereas the quantile-based selection in STARE dynamically adjusts to the current policy distribution,ensuring consistent identification of entropy-critical tokens throughout training.
24CAlgorithm: Main STARE ProcedureAlgorithm 1 STARE (Variant O1, Batch-Level Target-Entropy Gating, Fixed Weights)
Input: current policy πθ , reference policy πθold , prompt set D, hyperparameters: number of responsesG per prompt, clipping threshold ϵ, target entropy Htgt , weight W > 1, quantile ratio P, step size η.
Output: updated policy πθ1: for each training step k do2:
Sample a batch of B prompts from D3:
for each prompt xi do4:
Sample G responses {oi, j }Gj=1 from πθold5:
Compute reward ri, j for each response6:
Compute group-normalized advantages Âi, j = (ri, j − mean({ri,· }))/ std({ri,· })
7:
end for8:
Compute batch mean entropy H̄k from the current policy πθ over all generated tokens9:
Set gate gk = 1[ H̄k < Htgt ]10:
Construct the token set T + = {(i, j, t) : Âi, j > 0}11:
Compute the P-th percentile surprisal threshold s̃+ = Q P ({si, j,t }(i,j,t)∈T + )
12:
Select the entropy-critical set L+ = {(i, j, t) ∈ T + : si, j,t ≥ s̃+ }13:
for each token (i, j, t) do14:
Assign token weight ωi, j,t :
�1 + gk (W − 1), if (i, j, t) ∈ L+ ,ωi, j,t =1,otherwise.
15:
end for16:
Compute STARE objective:
JSTARE (θ) =1N∑i, j,tωi, j,t min ρi, j,t (θ) Âi, j , clip(ρi, j,t (θ), 1−ϵ, 1+ϵ) Âi, j17:
Perform gradient update θ ← θ + η ∇θ JSTARE (θ)
18: end for26(1)
DBasic Derivations for Sections 2 and 3.1D.1Softmax Jacobian DerivationThe softmax function maps logits z ∈ R|V| to a probability distribution over the vocabulary V:
πv ≜ πθ (v | c) =exp(zv )
∑v′ ∈V exp(zv′ )
∀v ∈ V .
The Jacobian matrix of the softmax map with respect to the logits is given by the following well-knownexpression (Bridle, 1990; Bishop, 2006; Goodfellow et al., 2016):
∂πv′= πv′ (δvv′ − πv )
∂zv∀v, v′ ∈ V ,(2)
where δvv′ is the Kronecker delta. This expression can be verified by direct differentiation:
∂∂πv′ =∂zv∂zvexp(zv′ )
∑k exp(zk )
!
# δvv′ ∑k exp(zk ) − exp(zv′ ) exp(zv )
# (∑k exp(zk ))2δvv′ ∑k exp(zk )
exp(zv′ ) exp(zv )
−(∑k exp(zk ))2 (∑k exp(zk ))2= δvv′ πv′ − πv′ πv= πv′ (δvv′ − πv ).
This identity is used extensively in the gradient derivations below.
D.2Token-Level Logit Update in the Unclipped GRPO RegimeIn the unclipped regime (i.e., when the importance ratio ρi,t (θ) falls strictly within the interval (1−ϵ, 1+ϵ)
and the min operator selects the unclipped term), the GRPO objective at a single token position wheretoken a was sampled simplifies to:
LGRPO (θ) = ρi,t (θ) Âi .
Taking the gradient with respect to θ and applying the standard policy-gradient identity (Schulman et al.,2015; Sutton & Barto, 2018; Williams, 1992), we obtain:
∇θ LGRPO (θ) = Âi ∇θ log πθ (oi,t | xi , oi,<t ).
Under a softmax parameterization, the per-logit gradient of the log-probability is:
∂∂log πθ (a | c) =(log exp(za ) − log ∑ exp(zv′ ))
∂zv∂zvv′exp(zv )
= δva −∑v′ exp(zv′ )
= δva − πv .
Therefore, the GRPO logit update for vocabulary item v at a single position is:
∂LGRPO= Âi (δva − πv ).
∂zv(3)
When performing gradient ascent with an infinitesimal step size η > 0, the resulting update to logit zvis:
∆zv = η Âi (δva − πv ).
(4)
This update is the building block for the entropy variation analysis in Theorem 3.1. The intuition is thatthe GRPO update increases the logit of the sampled token a proportionally to the advantage Âi anddecreases all other logits by the same total magnitude, thereby preserving the normalization of thesoftmax.
27D.3Lemma 2.1 (Entropy Gradient with Respect to Logits: Surprisal-Deviation Form)
Lemma 2.1 (Restated). For a next-token distribution π parameterized by logits z ∈ R|V| via the softmaxfunction, the partial derivative of the policy entropy H = − ∑v∈V πv ln πv with respect to the logit zv is:
∂H= πv (sv − H ) ,∂zv(5)
where sv = − ln πv is the token surprisal and H = Eπ [s] is the policy entropy.
Proof. Applying the chain rule:
∂H∂πv′= − ∑ (1 + ln πv′ )
.
∂zv∂zvv′ ∈V(6)
Substituting the softmax Jacobian from Equation (2):
∂H= − ∑ (1 + ln πv′ ) πv′ (δvv′ − πv )
∂zvv′ ∈V= − (1 + ln πv ) πv (1 − πv ) − ∑ (1 + ln πv′ ) πv′ (−πv )
v′ ∈V {v}= −πv (1 + ln πv ) + πv ∑ πv′ (1 + ln πv′ )
v′ ∈V= πv −(1 + ln πv ) + ∑ πv′ (1 + ln πv′ )
v′ ∈V= πv −1 − ln πv + 1 + ∑ πv′ ln πv′!
(7)
v′ ∈V= πv (− ln πv − H )
= πv (sv − H ) .
The last line uses sv = − ln πv and the definition of entropy H = − ∑v′ πv′ ln πv′ = Eπ [s]. This completesthe proof.
Interpretation. Lemma 2.1 reveals that increasing the logit zv raises the policy entropy precisely whenthe token v has above-average surprisal (sv > H), i.e., when it is rarer than the “typical” token under thecurrent distribution. Conversely, increasing the logit of a token with below-average surprisal (sv < H)
decreases the entropy. This surprisal-deviation form directly links the geometry of the softmax parameterization to the information-theoretic properties of the resulting distribution and serves as the foundationfor the token-level entropy dynamics derived in the following sections.
Connection to prior work. This gradient form is closely related to the concept of “surprisal” in psycholinguistics (Hale, 2001; Levy, 2008; Smith & Levy, 2013) and to the role of surprisal in language modeltraining dynamics (Oh & Schuler, 2023; Oh et al., 2024). The deviation sv − H captures whether a tokenis more surprising (informative) than the average token under the current policy, and the gradient
