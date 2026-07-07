# ⭐⭐⭐ 用截图喂出GUI Agent：GUICrafter弱监督训练实战

**日期**: 2026-06-30

---

论文 : GUICrafter: Weakly-Supervised GUI Agent Leveraging Massive Unannotated Screenshots链接 : https://arxiv.org/abs/2606.29705做 GUI Agent 的工程师都知道，最大的拦路虎不是模型算力，而是 高质量标注数据的极度匮乏 。
UI-TARS 这类 SOTA 模型动辄需要 1840 万条轨迹数据，这种“数据堆砌”模式在工程上既烧钱又难以复制。GUICrafter 的出现提供了一个极具吸引力的替代方案： 用海量无标注截图 + 极少量高质量数据，实现同等甚至更强的性能。
这篇论文的核心价值在于它验证了“弱监督预训练”在 GUI 领域的可行性，为中小团队低成本构建 Agent 指明了方向。
### 痛点：为什么我们缺数据？
现有 GUI Agent 主要依赖视觉定位（Visual Grounding），但标注像素级坐标和多步操作极其耗时。
更致命的是，由于训练数据覆盖的界面风格有限，模型在面对跨设备、跨领域的真实场景时，泛化能力急剧下降。GUICrafter 认为， 解决定位不准和泛化差的关键，在于让模型“看”到更多样化的界面，而不是死记硬背少数标注样本。
### 核心 Insight：两阶段课程学习GUICrafter 没有盲目追求全监督，而是设计了一个巧妙的**两阶段强化学习（RLVR）**框架。
第一阶段：无标注截图的弱监督预训练这是本文最精彩的设计。作者利用爬虫收集海量网页和开源移动数据集截图，提取其中的交互信号（如可点击区域），并将其转化为“元任务”（Meta-Task）。
- 设计直觉：与其让模型学习复杂的业务逻辑，不如先让它学会“什么是可点击的”。
- 具体做法：将任务抽象为“点击页面上任意一个按钮，不要点空白处”。这种去语义化的指令，让模型专注于视觉特征的提取。
- 奖励机制：引入高斯分布奖励（Gaussian Reward），预测点越接近交互区域中心，奖励越高。这比传统的“框内即得分”的二值奖励更精细，能有效引导模型定位核心控件。
第二阶段：高质量数据微调校准在模型具备了基础的视觉感知能力后，仅使用极少量（约 6,795 条）人工清洗的高质量数据进行强化学习微调，以校准具体的操作逻辑和语义理解。
### 关键结果：数据效率的降维打击实验数据有力地证明了该方法的有效性。GUICrafter-3B 在 Mind2Web 基准测试中表现优异：
模型 训练数据量 Mind2Web 平均准确率 UI-TARS-2B ~18.4M 59.5% GUI-R1-3B ~3K 38.3% GUICrafter-3B ~27K (0.1% of UI-TARS) 60.2%⚠️ 反直觉发现 ：GUICrafter 仅使用了 UI-TARS 约 0.1% 的数据量，却在 Mind2Web 上取得了更高的平均准确率（60.2% vs 59.5%）。
在 ScreenSpot-Pro 基准中，GUICrafter-3B 的平均准确率为 33.5%，同样超越了 GUI-R1-3B（28.6%）和 UI-TARS-2B（27.7%）。
此外，消融实验显示，仅进行第一阶段训练，模型在 Mind2Web 上的准确率就提升了 12.4% ；加入第二阶段后，又提升了 9.1% 。这证明了“先泛化、后校准”的课程学习策略是有效的。
### 工程启示对于正在落地 GUI Agent 的团队，GUICrafter 提供了三个关键指导：
- 数据收集策略转型：不要只盯着昂贵的标注公司。利用自动化脚本抓取网页 DOM 和截图，构建大规模的“元任务”数据集，成本几乎为零。
- 奖励函数的精细化：在视觉定位任务中，简单的二值奖励容易导致模型收敛到边缘区域。采用基于距离的高斯奖励，能显著提升点击的精准度。
- 小数据微调的价值：如果基础模型已经通过无标注数据学会了“看”，那么只需极少量的高质量 SFT/RL 数据即可激发其业务能力。
### 局限与展望尽管效果显著，该方法目前主要依赖网页和特定移动数据集的交互信号提取。对于高度定制化、非标准控件的企业内部软件，自动提取交互信号的难度较大。
此外，论文未深入探讨多步长程任务中的状态记忆问题，这在复杂工作流中仍是挑战。但无论如何，GUICrafter 证明了**“数据密度”比“数据总量”更重要**，这是 GUI Agent 走向普惠的重要一步。
## 📝 AI 点评点评时间：2026-06-30 21:07 ｜ reviewer: DeepSeek V4 Flash我们被要求写一篇点评，基于原文（arxiv 2606.29705）和一篇由Qwen3.6-27B自动生成的中文技术博客。点评需要包含：核心贡献、亮点、挑刺、总评（带评分）。评分标准从1星到5星，半星用½符号。
我们需要仔细阅读原文和博文。博文是一篇中文技术博客，标题“用截图喂出GUI Agent：GUICrafter弱监督训练实战”。博文内容比较简洁，概括了论文的主要思想、方法、结果和启示。我们需要对比原文，指出博文是否准确、遗漏了什么、有无过度解读、术语错位等。
首先，核心贡献：原文要解决什么？原文提出GUICrafter，利用大量无标注截图进行弱监督预训练（Stage 1），再结合少量高质量数据通过强化学习微调（Stage 2），从而大幅减少对人工标注的依赖，提升GUI agent的视觉定位和泛化能力。核心方法：两阶段课程学习框架，使用RLVR（GRPO）算法，Stage 1从无标注数据中提取交互信号并构造元任务进行训练，Stage 2用少量高质量数据进行强化学习微调。
博文核心贡献提炼：博文提到“用海量无标注截图 + 极少量高质量数据，实现同等甚至更强的性能”，基本准确。但博文强调“验证了弱监督预训练的可行性”，这也对。我们可以用1-2句总结。
亮点：博文相对原文的提炼/取舍是否到位？原文有工程价值或方法新意的点：比如高斯奖励、元任务设计、两阶段课程学习、数据效率极高（0.1%数据量达到甚至超越UI-TARS）。博文抓住了这些点，比如提到了高斯奖励、元任务、两阶段、数据效率对比。但博文可能遗漏了一些细节，比如高斯奖励的具体公式、噪声分析、数据可扩展性实验等。不过这些属于次要细节。博文整体提炼是到位的，特别是对工程团队有启示的部分。
挑刺：需要具体指出博文遗漏的关键约束/数字/条件、过度解读、术语错位、引用偏差等。每条必须引用原文或博文的具体片段或数据做依据。
我们仔细对比：
- 博文在关键结果表格中，将GUICrafter-3B的训练数据量写为“~27K (0.1% of UI-TARS)”，原文说“总训练数据量约���UI-TARS的0.1%”，原文中Stage 1使用了20,000个弱监督样本（主实验中），Stage 2使用了6,795个高质量样本，合计约26,795，约27K，确实约为UI-TARS 18.4M的0.1% (18.4M*0.001=18.4K, 27K略大于0.1%? 实际上0.1%是18.4K，27K是0.147%，但博文说“约0.1%”可以接受，因为原文也说了“approximately 0.1%”，原文在摘要中说“using only 0.1% of its data”，在正文4.3节说“The total number of training data used in our Stage 1 and Stage 2 is only approximately 0.1% of UI-TARS”，但注意原文在4.3节说“In our main experiments, we used 20,000 samples” for Stage 1 web & desktop, and 6,795 for Stage 2, 以及mobile平台另外有数据，但Mind2Web实验用的是web&desktop模型，所以总数是20,000+6,795=26,795，而UI-TARS-2B是18.4M，比例是0.1456%，原文说approximately 0.1%有点近似，但可以接受。博文写0.1%没问题。
但博文在表格中写“GUICrafter-3B: ~27K (0.1% of UI-TARS)”并且准确率60.2%。原文Table 2中GUICrafter-3B（ours）的平均Ele.Acc是60.2，博文正确。然而博文表格中UI-TARS-2B的准确率是59.5%，原文Table 2中UI-TARS-2B的平均Ele.Acc是59.5（All列），正确。GUI-R1-3B的准确率博文写38.3%，原文Table 2中GUI-R1-3B（原版，使用3K数据）平均Ele.Acc是38.3？注意原文Table 2中有两个GUI-R1-3B：一个是用3.0K数据（标注为1），另一个是用7.7K数据（标注为2，即full Mind2Web训练）。博文写的是GUI-R1-3B ~3K 38.3%，对应原文GUI-R1-3B¹（3.0K）平均Ele.Acc是38.3？我们看原文Table 2：GUI-R1-3B¹的All Ele.Acc是38.3（没错，第8行）。但博文说“GUI-R1-3B: ~3K, 38.3%”，正确。
但博文在“关键结果”部分说“GUICrafter-3B 在 Mind2Web 基准测试中表现优异”，然后给出了表格。这个表格是博文自己总结的，不是原文的完整表格。博文省略了其他模型，但关键数字正确。
-博文在“核心 Insight：两阶段课程学习”中，描述Stage 1时说“作者利用爬虫收集海量网页和开源移动数据集截图，提取其中的交互信号（如可点击区域），并将其转化为‘元任务’（Meta-Task）。” 原文确实如此。博文提到“高斯分布奖励（Gaussian Reward）”，但原文公式(1)给出了具体计算。博文没有提到高斯奖励的具体公式，但作为博客，这可以接受。但博文说“这比传统的‘框内即得分’的二值奖励更精细”，原文确实有对比，博文正确。
-博文在“工程启示”中提到“奖励函数的精细化”，并说“在视觉定位任务中，简单的二值奖励容易导致模型收敛到边缘区域”。原文在5.1节消融实验中确实比较了高斯奖励与二元奖励，并指出高斯奖励更好。博文正确。
-博文在“局限与展望”中说“对于高度定制化、非标准控件的企业内部软件，自动提取交互信号的难度较大。”原文没有专门讨论这个，但原文确实依赖网页DOM和移动端accessibility tree，对于定制控件可能提取困难，这合理。
现在找挑刺：博文是否有遗漏关键约束/数字/条件、过度解读、术语错位、引用偏差？
仔细检查：
-博文在“关键结果”表格中，将GUICrafter-3B的训练数据量写为“~27K (0.1% of UI-TARS)”。但原文中GUICrafter-3B的训练数据包括Stage 1的20K（web & desktop）加上Stage 2的6,795，总共约26.8K。但注意原文在4.3节说“For the web & desktop platform, we obtained 500K weakly-supervised samples. In our main experiments, we used 20,000 samples, while in the scalability study, we utilized the entire dataset.” 所以主实验用了20K。博文写27K是包含Stage 2的6,795。但原文在摘要中说“using only 0.1% of its data”，但UI-TARS-2B数据是18.4M，0.1%是18.4K，而27K是0.147%，所以博文说0.1%可能不太精确，但原文也是近似说0.1%，所以不算大问题。但我们可以指出博文没有区分Stage 1和Stage 2的数据量分别来自不同平台，不过这不是关键遗漏。
-博文在“关键结果”表格中，UI-TARS-2B的准确率是59.5%，但原文Table 2中UI-TARS-2B的All Ele.Acc是59.5，但注意原文Table 2中还有Step SR、Op.F1等指标，博文只取了Ele.Acc，这可以接受。但博文说“GUICrafter-3B 在 Mind2Web 基准测试中表现优异”，实际上原文中GUICrafter-3B的Ele.Acc是60.2，UI-TARS-2B是59.5，确实略高，但注意UI-TARS-2B是2B参数，GUICrafter-3B是3B参数，直接比较可能不完全公平，但原文也直接比较了。博文没有提到参数大小的差异，但原文中也是3B vs 2B，不过UI-TARS还有2B版本，GUICrafter也有7B版本。这不算严重问题。
-博文在“关键结果”部分还提到了ScreenSpot-Pro的结果：“GUICrafter-3B 的平均准确率为 33.5%，同样超越了 GUI-R1-3B（28.6%）和 UI-TARS-2B（27.7%）”。原文Table 3中GUICrafter-3B Avg是33.5，GUI-R1-3B是28.6，UI-TARS-2B是27.7，正确。但注意UI-TARS-2B在ScreenSpot-Pro上原文是28.6? 我们看原文Table 3: UI-TARS-2B的All Avg是27.7？原文Table 3中UI-TARS-2B的Avg列是27.7（在3B部分最后一行），而GUI-R1-3B是28.6。但博文写UI-TARS-2B 27.7，正确。但博文说“超越了GUI-R1-3B（28.6%）和UI-TARS-2B（27.7%）”，GUICrafter-3B是33.5，确实超越。但注意原文Table 3中还有“only Stage1”的结果24.4，“only Stage2”的结果30.5，博文没有提及这些细节，但不算遗漏关键。
-博文在“关键结果”部分还有一个“反直觉发现”的框，说“GUICrafter 仅使用了 UI-TARS 约 0.1% 的数据量，却在 Mind2Web 上取得了更高的平均准确率（60.2% vs 59.5%）”。这个说法基本正确，但需要指出UI-TARS-2B是2B参数，GUICrafter-3B是3B参数，参数不同可能影响比较，但原文也做了这个比较，所以可以接受。
-博文在“工程启示”中建议“利用自动化脚本抓取网页DOM和截图，构建大规模的‘元任务’数据集，成本几乎为零。”但原文中Stage 1的数据收集确实使用了Playwright等工具，但需要一定工程成本，说“几乎为零”有点夸张，但作为启示可以接受。
-博文在“局限与展望”中说“论文未深入探讨多步长程任务中的状态记忆问题”，但原文实际上在Mind2Web等基准上评估了多步任务（Step SR），但确实没有专门探讨状态记忆。这个评价合理。
现在寻找可能的术语错位或引用偏差：
-博文在“核心 Insight”中说“第一阶段：无标注截图的弱监督预训练”，并说“设计直觉：与其让模型学习复杂的业务逻辑，不如先让它学会‘什么是可点击的’。” 原文中Stage 1确实训练模型进行元任务，如“点击任何可点击区域”。但原文也提到，Stage 1还包括type和select的元任务。博文只提了click，但作为举例可以接受。
-博文说“奖励机制：引入高斯分布奖励（Gaussian Reward），预测点越接近交互区域中心，奖励越高。” 原文中高斯奖励是基于预测点到最近交互框中心的距离，但博文说“越接近交互区域中心”，这基本正确。但原文公式中使用的是高斯函数，且协方差由框的宽高缩放得到。博文没有提到缩放因子等细节，但博客不需要。
-博文在“关键结果”表格中，GUICrafter-3B的准确率60.2%，但原文Table 2中GUICrafter-3B的All Ele.Acc是60.2，但注意这是平均准确率，原文还细分了三个子集。博文只给了平均值，可以。
-博文在“关键结果”部分还提到了消融实验的改进：“仅进行第一阶段训练，模型在Mind2Web上的��确率就提升了12.4%；加入第二阶段后，又提升了9.1%。” 我们检查原文：原文在Table 2中，GUICrafter-3B only Stage1的All Ele.Acc是39.7？原文Table 2中GUICrafter-3B only Stage1的All Ele.Acc是39.7？仔细看：原文Table 2中GUICrafter-3B的“– only Stage1”行，All列是39.7。但注意原文说“After only Stage 1 … an average accuracy improvement of over 10% across all subcategories”，但具体数字：base model Qwen2.5-VL-3B zero-shot是27.3，Stage1后是39.7，提升了12.4个百分点，比例是45.4%，但原文说“over 10%”可能指绝对百分点。博文写“提升了12.4%”，可能指绝对百分点，但表述容易误解为相对提升。原文在Figure 1中标注了“Stage1 +12.4”（在Mind2Web上）。所以博文说“提升了12.4%”可以理解为绝对提升12.4个百分点。但博文随后说“加入第二阶段后，又提升了9.1%”，原文Figure 1中Stage2提升是+20.5（从40.5到60.2？注意Figure 1中标注了Stage2 +20.5，但那是从Stage1后的40.5到60.2，提升19.7个百分点，但Figure 1中写的是+20.5？我们再看原文Figure 1: 左侧图显示Grounding Accuracy (%)，Qwen2.5-VL-3B是14.1？不对，那是ScreenSpot-Pro的图？Figure 1右图是Mind2Web和ScreenSpot-Pro两个柱状图。在Mind2Web上，Qwen2.5-VL-3B是27.3，GUI-R1-3B是28.6，UI-TARS-2B是27.7，GUICrafter-3B是54.7？不对，仔细看原文Figure 1右图：上面是Mind2Web，下面是ScreenSpot-Pro。Mind2Web部分：Qwen2.5-VL-3B是27.3，UI-R1-3B是28.6，GUI-R1-3B是33.5，UI-TARS-2B是27.7，GUICrafter-3B是54.7？但原文Table 2中GUICrafter-3B的All Ele.Acc是60.2，而Figure 1中GUICrafter-3B在Mind2Web上是54.7？这似乎矛盾。注意Figure 1的标题是“Right: Our GUICrafter model achieves a higher average grounding accuracy than all baselines on both Mind2Web [8] and ScreenSpot-Pro [16] benchmarks.” 图中显示GUICrafter-3B在Mind2Web上是54.7，但Table 2中是60.2。可能Figure 1中的数值是Stage1+Stage2? 但Table 2中Stage1+Stage2是60.2，Figure 1中却是54.7，不一致。仔细看Figure 1中Mind2Web的柱状图：Qwen2.5-VL-3B: 27.3, UI-R1-3B: 28.6, GUI-R1-3B: 33.5, UI-TARS-2B: 27.7, GUICrafter-3B: 54.7。但原文Table 2中GUI-R1-3B（3K）是38.3，UI-TARS-2B是59.5，UI-R1-3B是40.5？这完全对不上。可能Figure 1中的数值是ScreenSpot-Pro? 但Figure 1右图有两个子图，上面标了Mind2Web，下面标了ScreenSpot-Pro。在Mind2Web子图中，GUI-R1-3B是33.5，UI-TARS-2B是27.7，GUICrafter-3B是54.7。但Table 2中GUI-R1-3B（3K）是38.3，UI-TARS-2B是59.5。矛盾极大。可能Figure 1中的数值是ScreenSpot-Pro? 但ScreenSpot-Pro子图中，Qwen2.5-VL-3B: 14.1, UI-R1-3B: 17.9, GUI-R1-3B: 27.7, UI-TARS-2B: 28.6, GUICrafter-3B: 33.5。这与Table 3中ScreenSpot-Pro的数值一致（Table 3中Qwen2.5-VL-3B是14.1，UI-R1-3B是17.9，GUI-R1-3B是28.6，UI-TARS-2B是27.7，GUICrafter-3B是33.5）。所以Figure 1右图实际上搞反了标签？上面子图标注了Mind2Web但数值对应ScreenSpot-Pro？下面子图标注了ScreenSpot-Pro但数值对应Mind2Web？这可能是论文排版错误。但博文没有引用Figure 1的具体数值，所以不影响。博文提到的提升12.4%和9.1%来自原文Figure 1中的标注：在Mind2Web子图上（实际可能是ScreenSpot-Pro？），Stage1 +12.4，Stage2 +9.1？但原文Figure 1中Mind2Web子图上标注了Stage1 +12.4，Stage2 +20.5？实际上Figure 1左图是管道，右图有两个子图，上面子图标注了Mind2Web，下面子图标注了ScreenSpot-Pro。上面子图（Mind2Web）中，GUICrafter-3B柱子上方有“Stage2 +20.5”，并且有“Stage1 +12.4”标注在中间。但上面子图的数值是GUICrafter-3B 54.7，而Stage1后的值是多少？从图上可以看出，Qwen2.5-VL-3B是27.3，Stage1后是40.5？但图中没有直接显示Stage1后的柱。实际上Figure 1右图上面子图中，GUICrafter-3B的柱子是54.7，然后旁边有一个浅色柱子可能是Stage1后的？看不太清。但原文在Figure 1标题中说“We also highlight the significant improvements brought by Stage 1 and Stage 2 respectively.” 并在Mind2Web子图上标注了“Stage1 +12.4”和“Stage2 +20.5”。从数值看，27.3 + 12.4 = 39.7，接近Table 2中Stage1的39.7。然后39.7 + 20.5 = 60.2，正是最终结果。所以Figure 1中的Stage1 +12.4和Stage2 +20.5是针对Mind2Web的绝对百分点提升。但Figure 1中Mind2Web子图的GUICrafter-3B柱子显示54.7，与60.2不符。这明显是论文绘图错误。博文引用了“提升了12.4%”和“又提升了9.1%”来自原文的Figure 1? 博文写“仅进行第一阶段训练，模型在 Mind2Web 上的准确率就提升了 12.4%；加入第二阶段后，又提升了 9.1%。” 但原文Figure 1中Stage2是+20.5，不是9.1。博文说的9.1%可能来自ScreenSpot-Pro的Stage2提升？在Figure 1中ScreenSpot-Pro子图标注了Stage1 +10.3，Stage2 +9.1。所以博文混淆了：它说“在Mind2Web上提升了12.4%，加入第二阶段后又提升了9.1%”，但实际原文中Mind2Web的Stage2提升是20.5，ScreenSpot-Pro的Stage2提升是9.1。博文将ScreenSpot-Pro的Stage2提升错误地套用到了Mind2Web上。这是一个明显的引用偏差或数据错误。需要指出。
-另外，博文说“加入第二阶段后，又提升了9.1%”，但原文中Stage2是在Stage1基础上的提升，Mind2Web上Stage2提升20.5个百分点，ScreenSpot-Pro上Stage2提升9.1个百分点。博文可能误读了Figure 1，将ScreenSpot-Pro的Stage2提升当成了Mind2Web的。这是关键错误。
-还有，博文在“关键结果”部分说“消融实验显示，仅进行第一阶段训练，模型在 Mind2Web 上的准确率就提升了 12.4%；加入第二阶段后，又提升了 9.1%。” 这不符合原文数据。原文Table 2中，GUICrafter-3B base (Qwen2.5-VL-3B zero-shot) 是27.3，Stage1后是39.7，提升12.4个百分点；Stage1+2后是60.2，相对于Stage1提升20.5个百分点，相对于base提升32.9个百分点。博文说“又提升了9.1%”是错误的。可能博文作者看到了Figure 1中ScreenSpot-Pro的Stage2提升9.1，误以为是Mind2Web。需要指出。
-另外，博文在表格中写“GUI-R1-3B: ~3K, 38.3%”，但原文GUI-R1-3B（3K）的准确率是38.3，但注意GUI-R1-3B还有7B版本。没问题。
-博文在“核心 Insight”中说“第一阶段：无标注截图的弱监督预训练”，但原文中Stage 1的数据包括web和mobile，且web数据是爬取的真实网页，mobile数据来自开源数据集。博文提到“利用爬虫收集海量网页和开源移动数据集截图”，正确。
-博文在“关键结果”部分提到“在 ScreenSpot-Pro 基准中，GUICrafter-3B 的平均准确率为 33.5%，同样超越了 GUI-R1-3B（28.6%）和 UI-TARS-2B（27.7%）。” 正确。
-博文在“工程启示”中说“利用自动化脚本抓取网页 DOM 和截图，构建大规模的‘元任务’数据集，成本几乎为零。” 原文中确实使用Playwright提取DOM，但需要爬取和存储成本，说几乎为零有点夸张，但不算严重错误。
-博文在“局限与展望”中说“论文未深入探讨多步长程任务中的状态记忆问题”，原文在Mind2Web上评估了多步任务，但确实没有专门研究记忆，可以接受。
现在，根据挑刺要求，每条必须引用原文或博文的具体片段或数据做依据。
挑刺1：博文在“关键结果”部分说“消融实验显示，仅进行第一阶段训练，模型在 Mind2Web 上的准确率就提升了 12.4%；加入第二阶段后，又提升了 9.1%。” 但原文中Mind2Web的Stage2提升是20.5个百分点（从39.7到60.2），而非9.1。9.1是ScreenSpot-Pro的Stage2提升（从24.4到33.5）。博文混淆了数据集。引用博文片段：“仅进行第一阶段训练，模型在 Mind2Web 上的准确率就提升了 12.4%；加入第二阶���后，又提升了 9.1%。” 原文Figure 1中ScreenSpot-Pro标注了Stage1 +10.3, Stage2 +9.1；Mind2Web标注了Stage1 +12.4, Stage2 +20.5。博文错误地将ScreenSpot-Pro的Stage2提升用于Mind2Web。
挑刺2：博文在关键结果表格中，将GUICrafter-3B的训练数据量写为“~27K (0.1% of UI-TARS)”。原文在4.3节说“The total number of training data used in our Stage 1 and Stage 2 is only approximately 0.1% of UI-TARS”。但UI-TARS-2B使用18.4M数据，0.1%为18.4K，而27K约为0.147%，并非精确0.1%。虽然原文也说approximately，但博文直接写0.1%可能不够精确，但不算严重。不过我们可以指出博文没有说明Stage 1和Stage 2分别的数据量，且将27K作为0.1%略显不精确，但原文也这么写，所以可能不算是挑刺，而是可以接受。但更关键的是，博文表格中UI-TARS-2B的准确率59.5%是Mind2Web的平均，但原文Table 2中UI-TARS-2B的All Ele.Acc是59.5，正确。但注意UI-TARS-2B在Mind2Web上的表现是59.5，而GUICrafter-3B是60.2，差距很小。博文强调了“更高的平均准确率”，但未提及参数差异（3B vs 2B），这可能导致读者误以为GUICrafter在同等参数下更优。但原文也是直接比较，所以不算严重。
挑刺3：博文在“核心 Insight”中描述“元任务”时说“设计直觉：与其让模型学习复杂的业务逻辑，不如先让它学会‘什么是可点击的’。” 但原文Stage 1的元任务包括click, type, select三种，而不仅仅是click。博文只提了click，可能过于简化。但作为举例，可以接受。不过更严重的是，博文没有提到Stage 1中对于mobile平台还有checkable和editable等元素，以及AITZ数据集中的icon元素。这不算关键遗漏。
另一个可能的挑刺：博文在“关键结果”表格中，将GUICrafter-3B的准确率写为60.2%，但原文Table 2中GUICrafter-3B的All Ele.Acc是60.2，但注意原文中GUICrafter-3B的All Ele.Acc是60.2，但Step SR等指标未列出。博文只取了Ele.Acc，这可以。但博文在“反直觉发现”中说“GUICrafter 仅使用了 UI-TARS 约 0.1% 的数据量，却在 Mind2Web 上取得了更高的平均准确率（60.2% vs 59.5%）”。实际上UI-TARS-2B的Ele.Acc是59.5，GUICrafter-3B是60.2，确实更高，但差距很小，且UI-TARS-2B是2B参数，GUICrafter-3B是3B参数，参数增加可能带来提升。但原文也做了这个比较，所以不算错误。
现在考虑总评。