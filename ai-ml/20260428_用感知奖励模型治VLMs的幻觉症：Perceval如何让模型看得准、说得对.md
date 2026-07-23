# 用感知奖励模型治VLMs的幻觉症：Perceval如何让模型看得准、说得对

**日期**: 2026-04-28

---

论文 : Improving Vision-language Models with Perception-centric Process Reward Models链接 : https://arxiv.org/abs/2604.24583一句话总结：这篇论文给出了一个治Vision-Language Models（VLMs）幻觉的实招——用**感知级过程奖励模型（PRM）**把GRPO的序列级奖励打成token级罚款，让模型在RL训练中为自己说的每句”瞎话”付出代价。
## 问题在哪？现有RLVR太”粗”了Vision-Language Models做复杂推理（比如数学图表分析、视觉搜索）时，经常在思维链中间”幻觉”——凭空捏造不存在的物体、错误的空间关系。现在的RL with Verifiable Rewards（RLVR）方法，比如GRPO，只在推理链条 末尾 给一个标量奖励。
问题来了：这个奖励是对整个序列的，序列里哪个token扯了谎、哪个token grounded，完全分不清。结果就是 稀疏奖励 ——模型要么全对全得奖，要么全错全受罚，中间的感知错误没人管。 credit assignment 难题就这么来了。
## 核心insight：从”结果打分”到”过程找茬”
作者的观察很直接：视觉推理里很多中间步骤是 可验证的感知声明 ——“桌上有个黑色笔记本”、“车在建筑的左侧”。这类声明直接对图像查证就行，不需要等最终答案。
基于此，设计思路就清晰了：
- 做个”找茬员”：训练一个PRM，专门从模型回复里提取与图像相关的声明，逐个与图像证据比对，标出哪些是幻觉。
- 把找茬结果变成训练信号：不在GRPO里用统一的序列advantage了，改成对幻觉span里的token单独惩罚。
- 推理阶段也用上：检测到幻觉就截断重写，多试几次， Test-time scaling。
这套组合拳的核心是： 把感知错误从模糊的序列级信号，解构为明确的token级惩罚 ，逼模型在生成每一步时都对照图像。
## 方法拆解：Perceval怎么工作### 1. 感知级PRM的设计Perceval采用 think-then-answer 范式：
- 先用 “ 标签内部分析回复里的每个声明是否与图像一致- 再用 <answer> 给出最终判定：若无幻觉，返回 “The response is correct.”；否则以Python列表形式精确返回原回复中被标为幻觉的字符串片段这种结构化输出是关键——它让后续定位token span变得简单：字符串精确匹配即可。
### 2. 训练数据怎么来论文提到一个四阶段流水线：
- 查询筛选：优先用视觉搜索数据集（如goal-directed visual search），这类任务天然要求精确的地面定位；少量其他领域数据保广度。
- Rollout生成：用Qwen2.5-VL-7B等开源VLM生成回复，这些回复自带真实幻觉，正好作负样本。
- 自动标注：用Gemini-2.5-Pro等强模型逐步检查幻觉，输出标准化格式。
- SFT微调：在聚合数据上微调PRM backbone。
重点：训练数据强调 感知密集型 场景，让PRM变成专业的”视觉事实核查员”。
### 3. Token级优势重分配这是把PRM集成进RL的核心。传统GRPO的序列advantage Âi 对序列内所有token都一样。现在改成：
Â′i,t := Âi − α · mi,t · |Âi |其中 mi,t 是二值掩码：若token t 落在幻觉span内则为1，否则为0。α是惩罚强度超参。
效果：
- 对正确token（mi,t=0）：advantage不变，照常学习- 对幻觉token（mi,t=1）：advantage被压低。若Âi为正，乘以(1−α)减小；若为负，乘以(1+α)变得更负——双重加重。
这样GRPO的目标函数里，幻觉token得到的梯度方向更明确地指向”少说这种话”。
### 4. 推理时的Truncate-Regenerate循环PRM的输出可直接用于推理阶段的纠错：
- Truncate–then–Regenerate：发现幻觉span后，截断到该span起始位置，保留已验证前缀作为上下文，让模型重写后半部分。可迭代多次，直到无新幻觉或达到k次上限。
- Truncate–Thinking–then–Regenerate：在截断处追加简短思考提示（如”Wait, I need to reconsider…”），引导模型自我反思错在哪，再重写。
论文指出，Truncate策略比加入思考提示的Feedback策略更稳定——因为训练数据中反思样本少，模型未必跟得上prompt，而Truncate更贴近模型自身分布。
## 关键结果：数字不会骗人### 训练阶段：PRM加持的RL显著提升感知能力Table 1是主要结果，挑关键的说：
3B模型 （Qwen2.5-VL-7B + GRPO baseline vs + Perceval）：
- V*（视觉搜索）整体：从80.10 → 83.25，+3.15- V*的Pos（空间关系）子任务：从69.73 → 72.37，+2.64- RealWorldQA：从62.1 → 64.9，+2.8- MathVision：从65.1 → 65.6，+0.5（虽小但稳定）
- ChartQA：从83.32 → 86.48，+3.167B模型 趋势类似，V*整体84.29 → 86.39（+2.1），RealWorldQA 66.4→67.4（+1.0），MathVision 71.7→72.0（+0.3）。
与SOTA基线比：3B模型在V*上83.25，超过大部分3B模型（VLM-R1 72.25, LMM-R1 49.21, Perception-R1 53.92）；7B模型86.39与Pixel-Reasoner（84.30）和DeepEyes（87.43）接近—— 注意后两者用了外部工具 ，而Perceval纯靠内部感知增强。
一个意外发现 ：虽然PRM训练和RL干预主要用视觉搜索数据，但模型在数学推理（MathVista, MathVision）和图表（ChartQA）上也涨了。论文归因于：这类任务底层依赖 细粒度感知能力 （定位图表数据点、读文本），感知基础打牢了，推理自然受益—— 所谓”能力迁移” 。
### 超参α的调优：不是越狠越好Table 3做了α的ablation（α=0就是纯GRPO）：
α V* RealWorldQA MathVision ChartQA 0.0 80.10 62.17 23.36 83.32 0.03 81.68 63.09 22.70 84.44 0.1 83.25 64.92 26.32 85.04 0.3 78.53 61.78 22.04 84.56趋势很明显：α太小（0.03）惩罚力度不够，提升有限；α太大（0.3） 误伤友军 ——因为PRM标记的是整个substring，高α会把span里所有token（包括”的”、“是”这类语法词）一起重罚，引入噪声，反而降性能。 α=0.1是甜点区 ，论文后续所有实验都用这个值。
### Test-time scaling：截断重写比投票更有效Table 2对比不同测试时扩展策略（k是生成/重写次数）：
策略 k=4 (V* attr) k=8 (V* attr) k=16 (V* attr) Major voting 91.30 92.17 92.17 Truncate 93.04 93.91 94.78 Truncate-Thinking 94.78 94.78 94.78Truncate系列稳定优于投票，且 随k增长持续提升 （94.78 vs 92.17），而投票早早就收敛了。这说明：外部干预（PRM纠错）比内部多样性（多采样）更能突破模型能力上限。
### 奖励黑客测试：曲线稳定说明没被忽悠Figure 2展示了训练过程中被Perceval标记为”含幻觉”的回复比例：初期下降（模型在学少说假话），但随后 趋于稳定 而非继续下降。如果是reward hacking（模型找到PRM的漏洞专门骗它），曲线会持续下降（模型学会了生成PRM爱看的但实际还是幻觉的回答）。稳定说明Perceval确实在引导模型 真正提升感知准确率 。
### 定性案例：GRPO vs 我们的方法Figure 3的对比很生动：
- GRPO模型面对”蓝色卡车在白色车的左侧还是右侧”的问题，直接回答”左侧”——典型的幻觉，根本没在图像里找车。
- 我们的模型：一步步来——先定位白色车，再找蓝色卡车，最后判断相对位置。这才是** grounded reasoning**。
## 工程启示：这套思路能怎么用？
-RLVR的精细化管理：别再用单一序列reward了。如果你有方法能定位错误span（不一定是感知，逻辑错误也能定位），都可以做成token级掩码，做advantage重加权。关键是掩码要准，否则误伤训练稳定性。
-Test-time scaling的务实选择：Major voting简单但提升有限；用外部critic做Truncate-Regenerate，尤其在事实性敏感任务（医疗报告、法律文件、视觉检查）里，可能更划算——多花一轮推理时间，换来可信度提升。
-PRM的训练数据策略：论文强调从感知密集型任务（visual search, Referring Expression Grounding）采query，因为这些任务的中间步骤天然可验证。如果你要训练的模型偏逻辑推理，也可以找类似”可验证中间步骤”的数据源。
-慎选惩罚强度α：0.1这个值不是普适的，但思路是对的：先从保守值（0.03）试，逐步加大，监控两个指标——（1）幻觉率是否降；（2）整体性能是否崩。崩的话说明span边界或α值有问题。
-能力迁移的宝贵馈赠：有时候你不需要为每个任务单独做RL。强化基础感知能力，可能让模型在多个推理任务上mutually benefit。如果你的模型在图表、数学上都表现平平，优先补感知也许是效率更高的路径。
## 局限与后续方向论文没明说但隐含的几点：
- 依赖强PRM：Perceval本身要用Gemini-2.5-Pro这类强模型标注，且用Qwen2.5-VL做backbone。如果换成更弱的模型，PRM的准确性会下降，token级惩罚反而变成噪音。
- 幻觉检测的覆盖度：目前专注感知幻觉（object/attribute/spatial misalignment），逻辑推理中的错误（计算错、因果颠倒）PRM未必能抓。
- 迭代成本：Test-time的Truncate-Regenerate要多次前向，延迟线性增长。k=16虽然效果更好，但实际部署需权衡。
后续可探索：让PRM同时检测感知+逻辑错误；或者 联合训练 PRM和policy，让policy学会主动避开PRM会 penalize 的生成路径。
## 结语Perceval的价值在于 把”幻觉”这个模糊概念，变成了可定位、可惩罚的token级信号 。对做VLM微调的工程师来说，这是RLVR工具箱里一个值得收藏的配件：如果你发现模型总在特定类型的感知错误上栽跟头，不妨试试token级advantage rescaling——先训练一个领域定制的PRM，再把它对错误span的标注转换成GRPO里的细粒度惩罚。效果可能比盲目堆数据、调超参更直接。
毕竟，让模型学会 对自己说的每句话负责 ，总比只对最终答案负责，要走得远一些。
