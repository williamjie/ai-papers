# EmbodiedMidtrain：用中间训练弥合VLM与VLA的分布鸿沟

**日期**: 2026-04-27

---

论文 : EmbodiedMidtrain: Bridging the Gap between Vision-Language Models and Vision-Language-Action Models via Mid-training链接 : https://arxiv.org/abs/2604.20012简单说：这篇论文干了一件事—— 把通用的视觉语言模型（VLM）通过中间训练（mid-training）变得更懂机器人操作，而不是直接拿过来就用 。
## 为什么值得关注？
现在做视觉-语言-动作模型（VLA）的主流做法，都是从现成的VLM（比如LLaVA、Qwen-VL）直接初始化。听起来合理——VLM已经懂视觉和语言了，再调一下就能输出动作。但问题来了：这些VLM是在image-caption、VQA这些数据上训练的，而VLA学的是 实打实的机器人操作轨迹 。两者数据分布相差太远，导致VLM的表示空间根本不适合 embodied 任务。
结果就是：你拿一个89分的VLM，fine-tune完可能还是只有70分的VLA性能。 不是模型不够强，是初始化选错了起点 。
## 现有方案的痛点- 专家VLA路线（如OpenVLA、π0）：用专门为机器人设计的架构，数据也精心筛选。性能确实好，但模型大、训练贵、难以复用。
- 通用VLM微调：把VLM直接在embodied数据上再训练。但Zhang et al. (2026)发现——VLM上embodied任务分数提升，不意味着VLA最终性能会更好。原因很简单：VLM学到的是”回答問題”，VLA需要的是”输出动作”，这是两种不同的信号。
- 无差别中间训练：把所有VLM数据不分青红皂白全喂进去。效果不稳定，甚至可能稀释embodied相关的信号。
核心矛盾在于：VLM训练数据总量巨大（LAION-400M、CC-12M），但真正对机器人操控有用的只占其中一小部分。 问题不是数据不够，而是噪声太多 。
## 核心Insight：数据分布不是均匀的论文首先做了个分布分析，用最大均值差异（MMD）量化数据集之间的距离：
数据集对 MMD距离 LAION vs CC-12M 0.10 LLaVA-Instruct vs VCR 0.18 VLM vs Libero 0.38 VLM vs Bridge-V2 0.35 VLM vs Calvin 0.38看到没？ 跨组距离（VLM vs VLA）普遍是组内距离的1.5-2倍 。图2a的矩阵和2b的t-SNE可视化更明显：VLA数据聚成三团紧密的簇，而VLM数据散得到处都是，只有 极小一部分 靠近VLA区域。
这说明什么？ 不是所有VLM数据都对embodied任务有价值 。有些数据天生就更接近机器人操作所需的视觉-空间推理。
## 方法设计：怎么找到”对”的数据？
思路很直接： 建一个轻量级分类器，学会区分哪些VLM样本像VLA数据 。基于密度比估计理论，一个能区分两个分布的最优分类器，其输出等价于密度比 pVLA(x)/pVLM(x)。得分高的样本，就是更接近VLA域的样本。
具体实现分三步：
Step 1. 训练proximity estimator- 用冻结的VLM特征（最后一层hidden state），接一个轻量MLP + sigmoid- 正样本：VLA轨迹数据；负样本：VLM候选数据- 损失函数：标准二值交叉熵- 早停条件：验证集准确率90%，防止过拟合Step 2. 对候选VLM数据打分排序- 所有LAION、CC-12M、LLaVA-Instruct、VCR、RefSpatial等数据过一遍estimator- 按score从高到低排，取top-KStep 3. Mid-training + VLA fine-tuning- 只用选出的子集训练VLM 5000步（batch size 256）
- 然后拿这个mid-trained VLM去初始化VLA，正常fine-tune关键设计决策：
- 特征解耦：proximity estimator在冻结的VLM上训练，与mid-training本身分离。这样选出的数据可以迁移到不同架构的VLM。
- 样本级选择：不是按数据集整体保留或丢弃，而是每个样本独立打分。即使是高潜力数据集（如RefSpatial）也会淘汰低分样本。
- 多样性保留：选出的数据分布比VLA数据更分散，比原始VLM更集中，在”对齐embodied”和”保留通用性”间取得平衡。
## 关键结果与数字直接看表1，这是最硬核的部分。
### 跨三个基准测试的一致提升模型 规模 训练样本量 Calvin ABC-D SimplerEnv Bridge Libero-10 Baseline (InternVL3.5-1B) 1.1B - 0.406 3.173 36.5 + EmbodiedMidtrain (Ours) 1.1B 1.0M/4.1M/4.1M 0.551 (+0.145) 3.714 (+0.541) 56.3 (+19.8) Expert VLA: OpenVLA 7.7B 7.7M/25.6M/25.6M 0.922 2.548 4.2 Expert VLA: π0 3.1B 7.7M/25.6M/25.6M 0.935 3.509 60.4 Off-the-shelf: Paligemma-1 2.9B 7.7M/25.6M/25.6M 0.814 3.506 55.3 Off-the-shelf: KosMos-2 1.7B 7.7M/25.6M/25.6M 0.721 3.096 60.4解读 ：
- 我们的1.1B小模型，Calvin上直接干掉了Paligemma-1（2.9B）和KosMos-2（1.7B），Libero上持平- 训练数据量只有专家VLA的1/7到1/6（1.0M vs 7.7M on Calvin），但性能差距并不悬殊- 在Simpler上提升最明显（+0.541），说明mid-training对需要空间推理的任务帮助更大### 跨架构迁移能力表1还显示了cross-backbone结果：用InternVL3.5-1B的特征空间选出的数据，喂给 Qwen3VL-2B 做mid-training，同样有提升：
模型 规模 Calvin Simpler Libero Qwen3VL-2B (w/o) 2.1B 0.887 3.173 36.5 Qwen3VL-2B (+ ours) 2.1B 0.922 (+0.035) 3.584 (+0.411) 45.8 (+9.3)
这说明proximity estimator学到的不是某个VLM的 idiosyncrasy，而是 embodied领域通用的对齐信号 。
### Ablation：为什么必须用learned estimator？
表2对比了不同选择策略：
策略 Calvin Simpler Libero Random Selection 3.398 43.8 48.4 Feat-space Avg Dist 3.126 53.1 51.2 VLA-cond Perplexity 3.159 55.2 48.0 Delta Perplexity 1.527 39.6 54.2 Learned Estimator 3.714 56.3 54.2随机采样连随机基线都不如 ，说明纯增加训练数据量没用，反而有害。
手工设计的特征距离和困惑度指标不稳定 ，delta-perplexity在Calvin上直接崩了。
只有 learned estimator 三项全优——它自动学会了embodied任务最需要的视觉-空间信号。
### 动态分析：优势从哪来？
图3展示了fine-tuning过程中的性能曲线。关键结论：
- 第0步（初始化时）mid-trained模型就更高：说明优势来自参数空间本身，不是训练过程- 随着fine-tuning进行，gap反而拉大：说明这个初始化不仅起点高，而且学习效率更高- 训练loss曲线几乎重合：说明loss指标看不出初始化质量差异，必须看下游任务## 工程启示：我们能抄什么作业？
### 1. 对本地/小模型部署如果你要在本地跑一个embodied agent（比如机器人、游戏NPC）， 不要直接用现成的VLM 。哪怕模型只有1B参数，经过针对性mid-training后，效果可能超过3-7B的通用模型。
### 2. 对数据curation数据质量 > 数据数量 。与其收集100万张通用图片，不如从现有数据池中 筛选出10万个”对味”的样本 。paper里的proximity estimator就是现成的筛选器——你只需要有少量VLA数据作为”正例”，就能给大量VLM数据打分。
### 3. 对多阶段训练设计很多模型训练分三步：pretrain → mid-train → fine-tune。但 mid-train阶段的数据选择往往被忽略 。这篇论文证明：mid-train用什么数据，和pretrain/fine-train同样重要，甚至更关键——因为它决定了下游任务起点的质量。
### 4. 对模型架构选择如果你的下游任务是 动作输出 而非文本生成，那么backbone的选择标准应该调整。不要只看VLM的caption/VQA分数，要看它在 空间推理、视觉定位 任务上的表现。paper里RefSpatial得分高的数据集，就是mid-training的最爱。
## 方法边界与局限论文没明说但值得注意的点：
1. 依赖VLA标注数据做proximity learningestimator训练需要VLA数据作为正例。如果你完全没有embodied轨迹，这个框架用不了。不过实践中，开源VLA数据（如Bridge、Calvin）已经不少，门槛不算太高。
2. 候选数据池的覆盖度paper用的VLM数据来自LAION、CC、LLaVA-Instruct等公开集。如果你的VLM是在更垂直的数据上预训练的（比如医疗影像、卫星图），这个selection pipeline可能需要重新验证。
3. 计算成本的隐藏部分虽然mid-training只训练5000步，但proximity estimator要先过一遍 全部候选数据打分 。LAION-400M级别的数据， inference成本不低。不过可以缓存特征，且只做一次。
4. 未探索的极端情况如果下游VLA任务非常特殊（比如水下机器人、太空机械臂），通用VLM数据可能根本不够。paper的three benchmarks都是桌面 manipulaion，跨域效果未知。
## 后续方向（从论文结尾延伸）
这篇work打开了几个有意思的方向：
方向1. 端到端联合优化现在流程是：先训练estimator → 选数据 → mid-train VLM → fine-tune VLA。 能否把selection和training一起优化 ？比如用可微分排序，让梯度反向传播到数据选择模块？
方向2. 多阶段渐进式mid-training现在的mid-training是一次性的。能否设计 课程式（curriculum）的mid-training ：先选最容易对齐的样本，再逐步增加难度？类似LLM的sft-iterative refinement。
方向3. 扩展到其他模态这个思路能不能迁移到 音频-语言-动作 （如语音控制机器人）或 3D-point cloud-语言-动作 ？核心都是找到”通用预训练数据”和”具身执行数据”之间的分布桥接。
方向4. 自动化评估指标paper里评估依赖下游VLA fine-tune后的成功率——这很重。能否设计一个 轻量级proximity评估器 ，不看下游任务就能判断mid-training质量？比如用某个layer的激活模式做代理指标。
## 总结：工程上的核心takeaway这篇论文最打动我的不是实验结果，而是一个 思维转变 ：
我们总在问：怎么让模型学得更好？但更该问的是：模型到底该学什么？
EmbodiedMidtrain的核心贡献，不是提出新的架构或损失函数，而是 通过数据选择重新定义学习目标 ——把通用的”理解图像和文本”目标，扭向”服务于动作生成的视觉-语言表示”。
对工程师的启发是：
- 当你发现fine-tune效果不达预期时，别急着调超参或换架构，先检查pretrain数据和downstream数据的分布对齐度- 如果你有少量高质量下游数据，训练一个分类器来筛选大规模上游数据，往往比盲目扩大训练量更有效- 中间训练阶段（mid-training）值得投入更多设计精力，它决定了模型从通用到专用的拐点质量最后说一句：这篇paper的代码、数据、模型全都会公开。建议立刻star，下次做embodied项目时——先跑一遍他们的data selection pipeline，再决定要不要从头训练。
