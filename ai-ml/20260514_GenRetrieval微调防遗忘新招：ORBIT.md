# GenRetrieval微调防遗忘新招：ORBIT

**日期**: 2026-05-14

---

在推荐系统领域，生成式检索（Generative Retrieval, GenRetrieval）正迅速取代传统的向量召回，因为它能让模型直接“生成”商品ID，减少索引维护成本。但工程师们发现，一旦用大语言模型（LLM）做这个任务，模型就会迅速“失忆”——原本擅长的逻辑推理、常识问答能力瞬间崩塌。这篇来自 Google DeepMind 和 Johns Hopkins University 的论文提出了一种名为 ORBIT 的方法，通过动态监控参数漂移并介入合并，在保持检索性能的同时，救回了模型的语言能力。
## 为什么传统方法救不了 GenRetrieval？
先看看这个问题的严重性。论文在 Gemma3-1B 上微调 GenRetrieval 时发现，遗忘发生得极快。如图 2b 所示，在微调的前 2000 步内，文本基准测试的平均性能就跌破了 0.15，几乎归零。
传统的**模型汤（Model Soups）**或事后插值方法（Post-hoc Merging）在这里失效了。论文 Figure 3 显示，无论怎么调整初始权重和微调后权重的混合比例，都无法同时获得高的检索召回率（Recall@10）和文本准确率。原因在于，当微调结束时，模型已经偏离原点太远了，这时候再强行拉回，只会让模型在两个任务上都表现不佳。
这意味着，我们需要一种**过程中（In-process）**的干预机制，而不是事后补救。
## ORBIT 的核心设计：距离即触发器ORBIT 的全称是 O rigin- R egulated B ack- M erging of I terative T rajectories。它的核心直觉非常朴素但有效： 如果模型参数偏离初始状态太远，就把它拉回来一点。
### 1. 怎么衡量“偏离”？
论文对比了两种距离度量：
- L2 距离：参数向量的欧氏距离。
- 符号相异度（Sign Dissimilarity, SD）：计算有多少参数的符号发生了翻转。
作者最终推荐 SD 。为什么？因为 SD 计算极快（只需按位异或操作），且它捕捉的是参数的“方向性变化”，这比单纯的幅度变化更能反映知识结构的改变。此外，SID（Semantic ID）相关的随机初始化参数被排除在计算之外，避免噪声干扰。
### 2. 怎么干预？
ORBIT 维护一个最大距离阈值 ϵ\epsilon 。在每一步梯度更新后，检查当前参数 θcurrent\theta_{current} ​ 与初始参数 θinit\theta_{init} ​ 的距离 d(θcurrent,θinit)d(\theta_{current}, \theta_{init}) ​ , θ ini t ​ ) 。
- 如果距离 >ϵ> \epsilonϵ，立即执行反向合并（Back-merging）：θnew=0.5×(θcurrent+θinit)\theta_{new} = 0.5 \times (\theta_{current} + \theta_{init})​=0.5×(θcurrent​+θinit​)。
- 如果合并后距离仍 >ϵ> \epsilonϵ，继续合并，直到满足条件。
这种设计带来了两个优势：
- 硬性约束：保证模型永远不会偏离初始状态太远，从物理上限制了遗忘的程度。
- 自适应频率：相比 Soup-to-Go 这种固定步数合并的方法，ORBIT 的合并频率是动态的。如图 7 所示，训练初期合并频繁，后期随着模型收敛，合并间隔逐渐拉长并稳定在约 3000 步。这种“学习到的节奏”比固定节奏更灵活。
## 关键结果：帕累托最优的赢家论文在 Amazon Product Reviews 数据集上进行了全面对比。核心指标是 DTIP（Distance To Ideal Point） ，即文本性能和检索性能归一化后到理想点 (1,1) 的距离。越小越好。
表 3：Sports and Outdoors 子集结果方法 Avg Text Perf. Recall@10 DTIP Text Baseline (原始) 35.72 0 1.00 Retrieval Baseline (纯微调) 15.52 2.16 1.00 L2 Weight Decay 15.76 1.92 0.99 Soup-to-Go (k=3K) 26.73 2.32 0.63 ORBIT (SD=7.5e-3) 28.95 2.58 0.49可以看到，ORBIT 在文本性能上达到了 28.95（远高于基线的 15.52），同时 Recall@10 也优于所有基线。在 Figure 6 的帕累托前沿图中，ORBIT 的所有检查点都优于 Soup-to-Go 和 L2 Decay，证明其在多目标优化上的优越性。
值得注意的是，即使将模型放大到 Gemma3-4B（表 5），ORBIT 依然有效，文本性能从 48.12 提升到 47.94（相对于基线提升显著），且 DTIP 保持在 0.42 的低水平，说明该方法具有良好的可扩展性。
## 工程启示- 不要相信事后合并：如果你的任务遗忘发生极快（如 GenRetrieval），事后插值无效。必须在训练循环中引入干预。
- 距离比步数更靠谱：固定步数合并（如每 1000 步合并一次）是“盲盒”，而基于距离的合并是“按需触发”。在资源受限场景下，ORBIT 能更精细地平衡性能与遗忘。
- 计算开销极低：SD 计算只需 bitwise XOR，合并只是简单的加法平均，对训练延迟的影响几乎可以忽略不计。
## 局限与展望ORBIT 目前主要验证了在单一任务适配（Single-task adaptation）场景下的有效性。对于更复杂的多任务持续学习（Continual Learning），如何动态调整 ϵ\epsilon 或处理不同任务间的参数干扰，仍是开放问题。但作为一个轻量级的正则化模块，它值得在各类 LLM 微调任务中尝试。
