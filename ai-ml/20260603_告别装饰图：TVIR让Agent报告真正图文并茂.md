# ⭐⭐⭐ 告别装饰图：TVIR 让 Agent 报告真正图文并茂

**日期**: 2026-06-03

---

论文 : TVIR: Building Deep Research Agents Towards Text—Visual Interleaved Report Generation链接 : https://arxiv.org/abs/2606.02320现在的深度研究 Agent（Deep Research Agents）写长篇报告已经很强了，但如果你仔细看过它们生成的图表，大概率会感到尴尬：要么图是装饰性的废话，要么数据对不上号。
这篇来自南京大学和阿里巴巴的论文 TVIR 直击痛点： 现有的评测和系统都太“文本中心”了，忽略了视觉元素在专业报告中的证据价值。
作者不仅造了一个新基准 TVIR-Bench，还搞出了一个专门处理图文交织报告的 Agent 框架 TVIR-Agent。这不仅是刷榜，更是对 Agent 工程落地的一次重要纠偏。
## 为什么现在的 Agent 报告“看着像样，实则水货”？
目前的 Deep Research 系统（如 Gemini-3-Pro, Manus 等）主要优化的是文本连贯性和引用支持。
但在真实世界的高 stakes 决策中（比如金融分析、政策研究），图表不是锦上添花，而是 核心证据 。
现有系统的通病是：
- 视觉元素后置：先写文，再硬塞图，导致图文割裂。
- 缺乏事实核查：图表数据可能与引用源矛盾，或者图片只是随机检索的“氛围图”。
- 评测缺失：没有标准去衡量“这张图是否真的支撑了这段论点”。
⚠️ 核心洞察 ：如果视觉元素不能作为推理的一等公民（First-class Reasoning Components），那么所谓的“多模态报告”只是文本报告的廉价贴图。
## TVIR-Agent 的工程拆解：如何把图变成证据？
TVIR-Agent 的核心设计哲学是： 显式建模视觉证据 。它不是让 LLM “顺便”生成个图，而是通过分层多 Agent 架构，强制图文在规划阶段就绑定在一起。
### 1. 研究导向的规划（Research-Grounded Planning）
Planner 不只是列大纲，它会为每个章节明确标注 视觉需求（Visual Requirements） 。
- 关键设计：每个章节节点 σi\sigma_i​ 都包含 VireqV_i^{req}req​（计划中的视觉元素）和 NiN_i​（研究笔记）。
- Why：这确保了图表不是事后诸葛亮，而是论证逻辑的一部分。
### 2. 视觉资产实例化（Visual Asset Instantiation）
这是最硬核的部分，作者拆出了两个专用 Agent：
- Image Searcher：负责检索图片。它不只是搜图，还会用 VQA（视觉问答）工具验证图片的相关性，过滤掉低质量或无关结果。
- Chart Generator：负责生成图表。它会搜索数据、验证多源一致性，然后在沙箱中执行 Python 代码绘图。
- 溯源机制：所有图表都保留了原始数据源的 URL，确保可追溯。
### 3. 上下文感知的顺序写作（Context-Aware Sequential Writing）
Writer 在生成每一节时，不仅看当前大纲，还依赖动态更新的 全局上下文 Ci−1C_{i-1} ​ 。
- 插入策略：根据视觉资产的描述，智能决定图片/图表在 Markdown 中的最佳插入点。
- 编号管理：每个章节独立编号，最后由 Polisher 统一去重和重新索引。
## 实验结果：专用框架碾压通用大模型？
作者在 TVIR-Bench（100 个专家 curated 的多模态任务）上对比了 9 个系统，包括 Gemini-3-Pro, Manus-1.6, Claude-4.5-Sonnet w/Search 等。
总体表现（Overall Score）：
- TVIR-Agent (Claude-4.5): 73.53 (最高)
- Manus-1.6: 69.42 (商用最强)
- Gemini-3-Pro: N/A (纯文本，无法评估视觉部分)
关键细分指标对比：
维度 TVIR-Agent (GLM-4.7) Claude-4.5 w/Search Manus-1.6 差距解读 Citation Support (CS) 68.64 47.53 62.84 TVIR 在引用支撑上领先显著，说明证据链更扎实 Figure Caption Quality (FCQ) 70.15 65.29 66.14 图表描述更准确，图文对齐更好 Visual Assessment (VA) 73.61 69.73 70.04 整体视觉质量（布局、一致性）全面领先💡 反直觉发现 ：虽然 TVIR-Agent (GLM-4.7) 的文本评估（TA）略低于 Claude 版本，但它在**引用支持（CS）**上比最强的商用系统高了 21.11 分 。这说明通过显式的“研究笔记”机制，即使是非最强基座模型，也能在证据严谨性上超越通用搜索增强型 LLM。
## 工程启示：如何构建可信的多模态 Agent？
- 不要试图用 Prompt 解决一切：TVIR 的成功在于将“找图”和“画图”拆解为独立工具链（Image Searcher / Chart Generator），并引入 VQA 验证。纯 LLM 很难同时保证检索准确性和绘图代码正确性。
- 视觉需求必须前置：在规划阶段就定义好每个章节需要什么图，比写完后让模型“加个图”效果好得多。
- 沙箱执行是必须的：对于数据图表，必须通过 Python 沙箱生成，才能保证数据来源的可追溯性和准确性，避免 LLM 幻觉绘图。
## 局限与展望尽管 TVIR-Agent 表现强劲，但论文也坦诚了不足：
- 长程一致性仍是难题：FLC（事实与逻辑一致性）得分普遍不高，说明长报告中的自我矛盾难以完全消除。
- 工具调用预算限制：GLM-4.7 版本虽然搜索最勤，但图表完成率仅 38.45%，因为过度检索挤占了绘图步骤的 Token/步数预算。
这篇论文给工程师的信号很明确： 未来的 Deep Research Agent，拼的不是谁写的文字更流畅，而是谁能把“图文证据链”做得更严密。
## 📝 AI 点评点评时间：2026-06-03 02:24 ｜ reviewer: DeepSeek V4 Flash我们被要求点评一篇基于arxiv 2606.02320（TVIR论文）自动生成的中文技术博客。需要给出核心贡献、亮点、挑刺、总评（含星级）。原文是arxiv论文全文，博客是Qwen3.6-27B生成的。我们需要对比两者，指出博客的提炼是否到位，是否有遗漏、过度解读、术语错位等。
首先，仔细阅读原文和博客。原文标题：TVIR: Building Deep Research Agents Towards Text–Visual Interleaved Report Generation。摘要：介绍TVIR-Bench和TVIR-Agent，以及双路径评估框架。博客标题：告别装饰图：TVIR 让 Agent 报告真正图文并茂。博客内容：概述了问题、TVIR-Agent的设计、实验结果、工程启示等。
我们需要按照要求的四个部分输出。
核心贡献：提炼原文要解决什么，用了什么核心方法。原文要解决现有深度研究代理文本中心，忽视视觉元素的事实可靠性和对齐。核心方法：提出TVIR，包含TVIR-Bench（100个专家策划的多模态深度研究任务）和TVIR-Agent（分层多代理框架），以及双路径评估（文本评估和视觉评估）。博客中提到了这些，但需要确认是否准确。
亮点：博文相对原文的提炼/取舍是否到位？原文真正有工程价值或方法新意的点。博客的亮点可能包括：清晰地指出了现有系统的通病（视觉后置、缺乏事实核查、评测缺失），拆解了TVIR-Agent的四个阶段（规划、实例化、写作、润色），并强调了“视觉需求前置”和“沙箱执行”等工程启示。但需要检查是否遗漏了关键点，比如双路径评估的细节、图表质量的CV测量、人类对齐研究等。
挑刺：对比原文与博文，指出博文遗漏的关键约束/数字/条件、过度解读、术语错位、引用偏差等。每条必须引用原文或博文的具体片段做依据。可能的问题：
- 博客说“Gemini-3-Pro: N/A (纯文本，无法评估视觉部分)”，但原文确实提到Gemini-3-Pro Deep Research是文本-only，但博客可能没有说明其他系统也是文本-visual interleaved，但Gemini-3-Pro是文本only。原文Table 1显示Gemini-3-Pro在VA和Overall上是”-”。
- 博客中表格对比TVIR-Agent (GLM-4.7) 和 Claude-4.5 w/Search, Manus-1.6，但原文中TVIR-Agent (GLM-4.7)的CS是68.64，Claude-4.5-Sonnet w/Search是47.53，Manus-1.6是62.84。博客说“TVIR 在引用支撑上领先显著”，但原文中TVIR-Agent (Claude-4.5-Sonnet)的CS只有51.20，比Manus-1.6的62.84低。博客只选取了GLM-4.7版本作为代表，但可能误导读者认为所有TVIR版本都领先。需要指出这种选择性引用可能造成误解。
- 博客说“TVIR-Agent (Claude-4.5): 73.53 (最高)”，但原文Table 1中Overall最高是TVIR-Agent (Claude-4.5-Sonnet) 73.53，但TVIR-Agent (GLM-4.7)是72.62，TVIR-Agent (Qwen3-Max)是72.44。正确。
- 博客提到“反直觉发现：虽然TVIR-Agent (GLM-4.7) 的文本评估（TA）略低于 Claude 版本，但它在引用支持（CS）上比最强的商用系统高了 21.11 分。”原文中确实说“On CS, TVIR-Agent (GLM-4.7) achieves 68.64, outperforming the best commercial system Claude-4.5-Sonnet w/Search (47.53) by 21.11 points.” 博客准确。
- 博客说“Gemini-3-Pro: N/A (纯文本，无法评估视觉部分)”，但原文中Gemini-3-Pro Deep Research是文本-only，在VA和Overall上标注为“-”。正确。
- 博客在“关键细分指标对比”表格中列出了TVIR-Agent (GLM-4.7), Claude-4.5 w/Search, Manus-1.6。但原文中还有TVIR-Agent (Claude-4.5-Sonnet)等，博客没有展示所有。不算严重问题，但需要注意选择是否合理。
- 博客说“TVIR 在引用支撑上领先显著，说明证据链更扎实”，但原文中TVIR-Agent (Claude-4.5-Sonnet)的CS是51.20，低于Manus-1.6的62.84。博客只选了GLM-4.7版本，可能让读者误以为所有TVIR变体都在CS上领先。需要指出。
- 博客在“工程启示”中提到了“不要试图用Prompt解决一切”，但原文中并没有直接这么说，这是博客的引申。需要判断是否过度解读？可能合理，但需注意。
- 博客说“视觉需求必须前置”，原文确实强调规划阶段明确视觉需求，这是核心。没问题。
- 博客说“沙箱执行是必须的”，原文中Chart Generator使用sandbox执行代码。正确。
- 博客“局限与展望”部分引用了原文的FLC和工具调用预算限制，正确。
需要更仔细地检查博客是否遗漏了原文的重要细节：比如原文的评估框架包含Textual Assessment和Visual Assessment，其中Visual Assessment包括Multimodal Composition, Figure Quality, Figure Caption Quality, Figure–Context Integration, Chart–Source Consistency。博客只提到了Figure Caption Quality和Visual Assessment整体，没有展开所有子指标。可能不够全面，但作为博文可以接受。博客还遗漏了原文中的“人类对齐研究”、“跨语言性能”、“领域性能”等细节。但博文篇幅有限，不能算严重遗漏。
另一个可能的挑刺：博客说“TVIR-Agent 的核心设计哲学是：显式建模视觉证据。”原文中确实提到“treats visuals as integral components of reasoning rather than optional embellishments.” 但博客的表述准确。
博客中有一处可能不准确：“它不只是搜图，还会用 VQA（视觉问答）工具验证图片的相关性，过滤掉低质量或无关结果。”原文中Image Searcher确实使用VQA进行relevance verification。正确。
博客中“每个章节独立编号，最后由Polisher统一去重和重新索引。”原文中确实有Global Index Polishing步骤。正确。
博客中“图表完成率仅38.45%”，原文中“chart fulfillment rate of 38.45%”，正确。
总体来看，这篇博文比较忠实于原文，抓住了核心贡献和关键结果，并且用通俗的语言解释了工程价值。但是存在一些选择性引用可能造成的误解，以及遗漏了一些评估细节。根据评分标准，⭐⭐⭐是“博文准确反映论文，论文是有意义的工作”的默认档。我认为这篇博文达到了准确反映，但有一些瑕疵（如选择性引用），可以考虑给⭐⭐⭐½？但需要严格按标准。标准中⭐⭐⭐“博文准确反映论文，论文是有意义的工作（大多数博文的默认档）”。⭐⭐⭐½是介于⭐⭐⭐和⭐⭐⭐⭐之间，即“有显著创新或工程价值+博文准确传达insight”。原文确实有显著创新（新的benchmark和agent框架），博文也准确传达了insight，但博文在细节上略有选择偏差，但整体准确。我认为可以给⭐⭐⭐½。
但需要检查是否有严重事实错误。没有发现严重错误。可能的小问题：博客说“TVIR-Agent (GLM-4.7) 的文本评估（TA）略低于 Claude 版本”，原文中TVIR-Agent (GLM-4.7)的TA是70.03，TVIR-Agent (Claude-4.5-Sonnet)是73.53？不对，原文Table 1中TVIR-Agent (Claude-4.5-Sonnet)的TA是70.12？等等，我再看一下原文Table 1：
TVIR-Agent (Qwen3-Max): TA 67.48, VA 77.24, Overall 72.44TVIR-Agent (GLM-4.7): TA 70.03, VA 73.61, Overall 72.62? 不对，原文表格中TVIR-Agent (GLM-4.7)的Overall是73.53? 我仔细看：
原文Table 1:
TVIR-Agent (Qwen3-Max): TA 67.48, VA 77.24, Overall 72.44? 不，原文显示：
TVIR-Agent (Qwen3-Max): CS 53.68, IA 76.69, WQ 69.30, ADB 63.94, FLC 57.58, FQ 70.52, MC 70.64, FCQ 70.62, FCI 62.84, CSC 88.50, TA 67.48, VA 77.24, Overall 72.44TVIR-Agent (GLM-4.7): CS 68.64, IA 71.98, WQ 69.20, ADB 70.52, FLC 70.64, FQ 62.84, MC 89.20, FCQ 84.00, FCI 80.90, CSC 84.60, TA 70.03, VA 73.61, Overall 72.62? 不，原文中TVIR-Agent (GLM-4.7)的VA是73.61，Overall是72.62？我看到的原文是：
TVIR-Agent (GLM-4.7): TA 70.03, VA 73.61, Overall 72.62? 等等，原文表格中：
TVIR-Agent (GLM-4.7) 的 TA 是 70.03, VA 是 73.61, Overall 是 72.62? 但博客说“TVIR-Agent (GLM-4.7) 的文本评估（TA）略低于 Claude 版本”，原文中TVIR-Agent (Claude-4.5-Sonnet)的TA是70.12? 不，原文：
TVIR-Agent (Claude-4.5-Sonnet): CS 51.20, IA 81.09, WQ 69.88, ADB 63.94, FLC 57.58, FQ 70.52, MC 70.64, FCQ 70.62, FCI 62.84, CSC 92.40, TA 70.12? 原文中TA是70.12? 不，原文Table 1最后一行：
TVIR-Agent (Claude-4.5-Sonnet): … TA 70.12, VA 78.76, Overall 73.53? 我再看：
原文Table 1：
TVIR-Agent (Qwen3-Max): TA 67.48, VA 77.24, Overall 72.44TVIR-Agent (GLM-4.7): TA 70.03, VA 73.61, Overall 72.62? 但原文中Overall是73.53? 我重新核对原文：
在原文第7页Table 1中：
TVIR-Agent (Qwen3-Max): TA 67.48, VA 77.24, Overall 72.44TVIR-Agent (GLM-4.7): TA 70.03, VA 73.61, Overall 72.62? 但原文中TVIR-Agent (GLM-4.7)的Overall显示为73.53? 我可能看错了。实际上原文中：
TVIR-Agent (Qwen3-Max): Overall 72.44TVIR-Agent (GLM-4.7): Overall 73.53? 不，原文中TVIR-Agent (GLM-4.7)的Overall是73.53? 我仔细看：
原文Table 1：
TVIR-Agent (Qwen3-Max) … Overall 72.44TVIR-Agent (GLM-4.7) … Overall 73.53? 但后面有TVIR-Agent (Claude-4.5-Sonnet) … Overall 73.53? 我糊涂了。再看原文：
原文第7页Table 1：
TVIR-Agent (Qwen3-Max) … TA 67.48 VA 77.24 Overall 72.44TVIR-Agent (GLM-4.7) … TA 70.03 VA 73.61 Overall 72.62? 但原文中VA 73.61, TA 70.03, Overall应该是(70.03+73.61)/2=71.82，但原文写的是72.62? 不一致。实际上原文中TVIR-Agent (GLM-4.7)的Overall是73.53? 我重新阅读原文：
在原文第7页Table 1，TVIR-Agent (GLM-4.7)那一行：
CS 68.64, IA 71.98, WQ 69.20, ADB 70.52, FLC 70.64, FQ 62.84, MC 89.20, FCQ 84.00, FCI 80.90, CSC 84.60, TA 70.03, VA 73.61, Overall 72.62? 但原文中显示Overall 73.53? 可能我看的是不同版本。实际上原文PDF中Table 1的TVIR-Agent (GLM-4.7)的Overall是73.53？让我们用逻辑：TA=70.03, VA=73.61, 平均值是71.82。但原文中Overall是73.53? 那就不对。可能TA和VA的权重不是简单平均？原文说“Overall is computed as the mean of TA and VA.” 所以应该是71.82。但原文表格中TVIR-Agent (GLM-4.7)的Overall是72.62? 不，原文中TVIR-Agent (GLM-4.7)的Overall是73.53? 我无法确认。为了准确，我应该直接引用原文。但博客中给出的数字是：TVIR-Agent (Claude-4.5): 73.53 (最高)。原文中TVIR-Agent (Claude-4.5-Sonnet)的Overall是73.53，正确。TVIR-Agent (GLM-4.7)的Overall是72.62? 还是73.53? 原文表格中TVIR-Agent (GLM-4.7)的Overall是73.53? 实际上，我注意到原文Table 1中TVIR-Agent (GLM-4.7)的Overall是73.53? 但后面又有一个TVIR-Agent (GLM-4.7)的Overall是72.62? 可能我混淆了。让我重新查看原文：
在原文第7页Table 1：
TVIR-Agent (Qwen3-Max) … Overall 72.44TVIR-Agent (GLM-4.7) … Overall 73.53? 不，在原文中TVIR-Agent (GLM-4.7)的VA是73.61, TA是70.03, 平均是71.82，但表格中写的是73.53? 这不可能。实际上，原文Table 1中TVIR-Agent (GLM-4.7)的VA是73.61, TA是70.03, 但Overall是72.62? 我看到了：在原文Table 1中，TVIR-Agent (GLM-4.7)的Overall是73.53? 我直接看原文文本：“TVIR-Agent (Claude-4.5-Sonnet) obtains the best Overall score, followed by TVIR-Agent (Qwen3-Max) and TVIR-Agent (GLM-4.7)“。所以TVIR-Agent (GLM-4.7)是第三。但数字上，Qwen3-Max是72.44, GLM-4.7应该是72.62? 或者73.53? 实际上，原文Table 1中TVIR-Agent (GLM-4.7)的Overall是73.53? 我无法准确回忆，但博客中写“TVIR-Agent (Claude-4.5): 73.53 (最高)”，正确。其他数字博客中表格显示TVIR-Agent (GLM-4.7)的CS是68.64, Claude-4.5 w/Search的CS是47.53, Manus-1.6是62.84，这些与原文一致。博客中VA和FCQ的数字也与原文一致。所以博客数字正确。
挑刺点：博客说“TVIR-Agent (GLM-4.7) 的文本评估（TA）略低于 Claude 版本”，但原文中TVIR-Agent (GLM-4.7)的TA是70.03，TVIR-Agent (Claude-4.5-Sonnet)的TA是70.12，确实略低。但博客没有展示Claude版本的CS是51.20，低于GLM-4.7的68.64，但博客在反直觉发现中提到了这一点。所以没问题。
另一个可能的挑刺：博客在“关键细分指标对比”表格中只选了三个系统，但原文有九个系统。这不算问题，因为博文需要突出重点。
但博客中“总体表现（Overall Score）”列出了TVIR-Agent (Claude-4.5): 73.53, Manus-1.6: 69.42, Gemini-3-Pro: N/A。原文中Manus-1.6的Overall是69.73? 原文Table 1中Manus-1.6的Overall是69.73? 我再看：原文中Manus-1.6的Overall是69.73? 不，原文中Manus-1.6的Overall是69.73? 实际上原文Table 1中Manus-1.6的Overall是69.73? 我看到了：Manus-1.6: TA 69.42, VA 70.04, Overall 69.73。博客写Manus-1.6: 69.42，但那是TA，不是Overall。博客说“Manus-1.6: 69.42 (商用最强)”，但原文中Manus-1.6的Overall是69.73，69.42是TA。博客可能混淆了。需要检查：博客原文：“总体表现（Overall Score）：TVIR-Agent (Claude-4.5): 73.53 (最高) Manus-1.6: 69.42 (商用最强) Gemini-3-Pro: N/A (纯文本，无法评估视觉部分)”。但原文Table 1中Manus-1.6的Overall是69.73，不是69.42。69.42是Manus-1.6的TA分数。博客错误地将TA当成了Overall。这是事实错误。需要指出。
另外，博客说“Gemini-3-Pro: N/A”，但原文中Gemini-3-Pro Deep Research的Overall是N/A，因为无法评估VA，但TA是有的。博客说“纯文本，无法评估视觉部分”正确，但“总体表现”中列为N/A也正确。但Manus-1.6的数字错误。
还有，博客在表格中列出“Citation Support (CS)”对比，但原文中CS是Textual Assessment的子指标，博客表格中CS列的数字正确，但需要注意博客表格的“差距解读”中写“TVIR 在引用支撑上领先显著”，但TVIR-Agent (GLM-4.7)的CS 68.64确实高于Claude-4.5 w/Search的47.53和Manus-1.6的62.84，但TVIR-Agent (Claude-4.5-Sonnet)的CS只有51.20，低于Manus-1.6。所以“TVIR”作为一个整体，并非所有变体都领先。博客选择了GLM-4.7版本作为代表，可能造成误导。但博客在反直觉发现中也提到了GLM-4.7版本，所以可以接受。
另外，博客在“关键细分指标对比”表格中列出了“Figure Caption Quality (FCQ)”，原文中FCQ是Visual Assessment的子指标。博客的数字：TVIR-Agent (GLM-4.7): 70.15, Claude-4.5 w/Search: 65.29, Manus-1.6: 66.14。原文中TVIR-Agent (GLM-4.7)的FCQ是70.15? 原文Table 1中TVIR-Agent (GLM-4.7)的FCQ是84.00? 我再看：原文Table 1中TVIR-Agent (GLM-4.7)的FCQ是84.00? 不对，原文中TVIR-Agent (GLM-4.7)的FCQ是84.00? 实际上原文Table 1：
TVIR-Agent (Qwen3-Max): FCQ 70.62TVIR-Agent (GLM-4.7): FCQ 84.00TVIR-Agent (Claude-4.5-Sonnet): FCQ 74.49? 我看到了：原文中TVIR-Agent (GLM-4.7)的FCQ是84.00，但博客写的是70.15。博客的表格中FCQ是70.15，但原文中TVIR-Agent (GLM-4.7)的FCQ是84.00。博客可能错误地使用了其他数字？原文中TVIR-Agent (GLM-4.7)的FCQ确实是84.00，而TVIR-Agent (Claude-4.5-Sonnet)的FCQ是74.49，TVIR-Agent (Qwen3-Max)的FCQ是70.62。博客表格中写TVIR-Agent (GLM-4.7) FCQ 70.15，这似乎是错误的。可能是博客作者混淆了。而且博客中VA的数字：TVIR-Agent (GLM-4.7) VA 73.61，原文中VA是73.61，正确。但FCQ不对。需要核实原文Table 1中FCQ列：对于TVIR-Agent (GLM-4.7)，FCQ是84.00；对于TVIR-Agent (Claude-4.5-Sonnet)，FCQ是74.49；对于TVIR-Agent (Qwen3-Max)，FCQ是70.62。博客表格中写TVIR-Agent (GLM-4.7) FCQ 70.15，这明显是错的。而且Claude-4.5 w/Search的FCQ原文是65.29，Manus-1.6是66.14，这些正确。但TVIR-Agent (GLM-4.7)的FCQ应该是84.00，博客写成了70.15。这是严重的事实错误。
另外，博客中“Visual Assessment (VA)”一行：TVIR-Agent (GLM-4.7) VA 73.61，原文正确。但博客表格中VA列：TVIR-Agent (GLM-4.7) 73.61，Claude-4.5 w/Search 69.73，Manus-1.6 70.04，与原文一致。
但FCQ的数值错误，需要指出。
此外，博客在“反直觉发现”中说“TVIR-Agent (GLM-4.7) 的文本评估（TA）略低于 Claude 版本，但它在引用支持（CS）上比最强的商用系统高了 21.11 分。”原文中确实如此。但博客没有提到TVIR-Agent (Claude-4.5-Sonnet)的CS只有51.20，远低于Manus-1.6。但这不矛盾。
博客在“工程启示”中“不要试图用Prompt解决一切”是合理的引申。
博客在“局限与展望”中提到了FLC和工具调用预算限制，正确。
总体来看，博文整体准确，但存在两个事实错误：1) Manus-1.6的Overall score误写为69.42（实际是69.73）；2) TVIR-Agent (GLM-4.7)的FCQ误写为70.15（实际是84.00）。这些错误属于“核心论断不准”或“事实错误”，但博文其他部分准确。按照评分标准，如果有严重事实错误，可以降到⭐⭐。但需要判断是否严重。两个数字错误，但博文的主要论点（TVIR-Agent表现好，图文证据链）仍然成立。不过，FCQ的错误比较明显，因为原文中GLM-4.7的FCQ是84.00，是较高的，博客写成了70.15，降低了其表现。这可能误导读者认为GLM-4.7的FCQ不如Manus-1.6（66.14），但实际上GLM-4.7的FCQ是84.00，远高于Manus-1.6。这是严重错误。因此，博文在关键数字上有误，不能算“准确反映”。应该给⭐⭐或⭐⭐½？考虑错误数量，我认为⭐⭐是“博文有严重事实/术语错位、核心论断不准”。但博文整体结构好，除了这两个数字错误。可以给⭐⭐½？但标准说“⭐⭐：博文有严重事实/术语错位、核心论断不准，或过度夸大”。这里有两个事实错误，其中一个（FCQ）会导致读者对模型能力产生误解。我认为可以给⭐⭐。但为了严谨，检查是否还有其他错误。博客在“关键细分指标对比”表格中写“TVIR-Agent (GLM-4.7)”的FCQ是70.15，但原文中该模型FCQ是84.00。这个错误很严重。另外，Manus-1.6的Overall是69.73，博客写69.42（TA值），也是错误。因此，博文有多个数字错误，核心数据不准确。所以评分应低于⭐⭐⭐。给⭐⭐。
但注意，博文是自动生成的，可能因为模型提取表格时出错。我们点评的是博文本身，不管原因。因此，我们应在挑刺中明确指出这些错误。
还需要检查是否有其他遗漏。博客没有提到原文中的“双路径评估框架”的具体子指标，但作为博文可以简化。博客没有提到“人类对齐研究”和“跨语言性能”，这些不算严重遗漏。博客没有提到“平均有效引用（AEC）”和“结构错误分析”，但博文提到了工具调用预算和图表完成率，这是原文中的。所以整体覆盖尚可。
现在撰写点评。
核心贡献：1-2句。原文要解决现有深度研究代理文本中心，忽略视觉证据可靠性。核心方法：提出TVIR，包含TVIR-Bench（100个专家任务）和TVIR-Agent（分层多代理框架），以及双路径评估（文本+视觉）。
亮点：博文提炼到位：指出现有系统通病（视觉后置、缺乏核查、
