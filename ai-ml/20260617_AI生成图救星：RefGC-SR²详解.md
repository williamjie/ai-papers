# ⭐⭐⭐ AI生成图救星：RefGC-SR²详解

**日期**: 2026-06-17

---

论文 : RefGC-SR^2: Reference-guided Generated Content Super-Resolution and Refinement链接 : https://arxiv.org/abs/2606.15158现在的参考引导生成（Reference-guided Generation）管线有个致命伤：用户给的高清参考图，进模型前就被强行降采样成 512x512。高频细节在生成开始前就丢了，生成的低分辨率结果还带着各种伪影。
这篇论文提出了 RefGC-SR² 任务，专门解决这个“最后一公里”的问题。它不只是做超分（Super-Resolution），而是利用原始高清参考图，同时修复生成伪影并恢复高分辨率细节。
### 痛点：现有方案的错位现有的方案都在“偏科”。
传统的图像超分（ISR）假设退化是模糊或压缩，完全不懂生成模型的伪影分布。
参考引导超分（RefSR）虽然用了参考图，但也是针对自然图像的。
而生成内容修复（GCR）能修伪影，却做不到分辨率提升。
更尴尬的是，现有的 RefGC 管线为了喂给模型，把用户的高清参考图（HRRI）直接下采样。这导致最终输出既丢失了细节，又引入了身份扭曲（Identity Distortion）。我们需要一个后处理步骤，把丢掉的细节找回来，顺便把生成的瑕疵修掉。
### 核心 Insight：频率分层与姿态对齐作者的核心直觉非常清晰： 不同频率的信息，应该由不同的机制处理。
-数据构造的巧思训练这种模型需要三元组数据：低分辨率生成图（LRGI）、高清参考图（HRRI）和高清真值（HRGT）。直接拿现成模型生成 LRGI 会导致姿态不对齐，模型会学偏。
作者设计了 DipRefGC，利用双 ControlNet（Inpainting 控制外观，Canny 控制姿态），强制生成的 LRGI 保持与 HRGT 一致的姿态，同时继承 HRRI 的外观。这确保了模型只学习“修复”和“超分”，而不是“矫正姿态”。
-FreqMoLE：频率自适应专家混合基于对 FLUX-Kontext 的分析，作者发现 DiT 的浅层主要捕获低频（全局结构），深层才处理高频（细节）。
因此，他们设计了 FreqMoLE，在每个 DiT 块插入两个 LoRA 专家：低频专家和高频专家。
通过一个门控函数 α\alpha，在浅层让低频专家主导，深层让高频专家主导。这种“由粗到细”的路径设计，完美契合扩散模型的层级特性。
-频率感知损失为了引导模型，损失函数也被拆分：
低频部分：对齐 HRGT 的全局结构。
- 高频部分：匹配 HRRI 的通道统计量（而非像素值，因为视角不同）。
这种设计让模型知道：结构听真值的，细节听参考图的。
### 关键结果：全面碾压基线在 RefGC-SR² Benchmark 上，RefGC-SR² 的表现非常稳健。
任务 模型 CLIP-I ↑\uparrow DINO ↑\uparrow PSNR ↑\uparrow SSIM ↑\uparrow LPIPS ↓\downarrow SR DiT4SR* 0.8186 0.6545 15.1005 0.5726 0.3884 RefSR AdaRefSR* 0.8310 0.6858 15.6200 0.5629 0.3523 RefGCR ImageCritic* 0.8542 0.7165 17.2090 0.6060 0.3039 RefGC-SR² Ours 0.8696 0.7474 17.5148 0.6335 0.2746注：带 * 表示在作者数据集上微调过，以保证公平对比。
可以看到，RefGC-SR² 在所有指标上均取得 SOTA。特别是在 DINO（身份一致性）和 LPIPS（感知质量）上优势明显。
在真实场景（In-the-wild）测试中，面对 DreamFuse、InsertAnything 等模型生成的低质输入，RefGC-SR² 依然保持了最佳性能。
用户研究数据 ：在修复忠实度、细节恢复和整体质量三个维度，RefGC-SR² 的 Top-1 选择率分别高达 83%、82% 和 83%，而竞争方法最高仅为 8%。
### 工程启示与局限对于工程师来说，这篇论文提供了一个清晰的 后处理范式 。
如果你正在构建���考引导生成的管线，不要指望生成模型一次性输出完美高清结果。引入一个专门的 RefGC-SR² 模块，可以显著降低前端生成模型的负担，同时提升最终交付质量。
设计亮点值得借鉴：
- 解耦控制：DipRefGC 中分离外观和姿态控制的思路，对构建可控生成数据很有参考价值。
- 频率路由：FreqMoLE 展示了如何利用模型内部的结构先验来优化 LoRA 注入策略，这比盲目全量微调更高效。
局限性：
目前依赖 FLUX-Kontext backbone，计算成本较高。且需要原始高清参考图作为输入，这在某些无参考图的生成场景中不适用。此外，40K 的训练数据规模相对较小，泛化能力的长期表现仍需更多真实场景验证。
## 📝 AI 点评点评时间：2026-06-17 19:07 ｜ reviewer: DeepSeek V4 Flash我们被要求基于原文（arxiv 2606.15158 全文）和一篇由 Qwen3.6-27B 自动生成的中文技术博客进行点评。博客内容已给出。我们需要输出四个部分：核心贡献、亮点、挑刺、总评。评分标准严格，要基于原文和博客的对照。
首先，理解原文的核心贡献：原文提出了 RefGC-SR2 任务，即参考引导的生成内容超分辨率和细化，同时处理超分辨率和伪影修复。核心方法包括：构建第一个真实世界三元组数据集（使用 DipRefGC 生成 LRGI），并提出频率感知的扩散变换器模型（FreqMoLE 和频率损失）。博客中基本反映了这些，但可能有些细节不准确。
我们需要仔细对比博客和原文。博客是一篇技术博客，可能有些简化。我们逐条分析。
核心贡献：提炼原文要解决什么，用了什么核心方法。原文要解决的是：现有参考引导生成管线中，用户的高分辨率参考图被降采样导致细节丢失，且生成结果有伪影。核心方法是：提出 RefGC-SR2 任务，构建三元组数据集（使用 DipRefGC 合成对齐的 LRGI），并提出频率感知模型（FreqMoLE + 频率损失）。博客开头也提到了痛点，但核心贡献表述需要更准确。
亮点：博文相对原文的提炼/取舍是否到位？原文里真正有工程价值或方法新意的点。亮点可以包括：频率分层与姿态对齐的洞察，FreqMoLE 设计，DipRefGC 的构造。博客中提到了这些，但可能没有完全突出原文的工程价值。例如，原文对层间频率层次的分析（图5a）是关键的动机，博客提到了，但不够具体。另外，博客中用户研究数据也引用了，但原文中用户研究的细节在附录，博客中提到了 Top-1 率。
挑刺：必须引用原文或博文的具体片段或数据做依据。指出博文遗漏的关键约束/数字/条件、过度解读、术语错位、引用偏差等。需要仔细检查。
可能的问题：
- 博客中说“用户给的高清参考图，进模型前就被强行降采样成 512x512。”原文中确实提到“downsample these references to a fixed low-resolution (LR) before injecting them into the generation process, e.g., 224^2 visual tokens or 512^2 diffusion inputs”。512x512 是常见设置，但博客直接说“512x512”，原文没有明确说是所有管线都是512，但可以接受。不过更精确的是“512^2 diffusion inputs”，但博客说“512x512”没问题。
- 博客中说“现有的方案都在‘偏科’。”然后列举 ISR、RefSR、GCR。原文中表格1分类更详细，博客概括得不错。
- 博客中核心 Insight 部分说“数据构造的巧思：作者设计了 DipRefGC，利用双 ControlNet（Inpainting 控制外观，Canny 控制姿态），强制生成的 LRGI 保持与 HRGT 一致的姿态，同时继承 HRRI 的外观。”这个描述基本正确。
- 博客中“FreqMoLE：频率自适应专家混合”描述正确。
- 博客中“频率感知损失”描述正确。
- 博客中关键结果表格，数据来自原文 Table 2。博客中表格里 DiT4SR* 的 PSNR 是 15.1005，原文是 15.1005，正确。AdaRefSR* 的 PSNR 是 15.6200，原文是 15.6200，正确。ImageCritic* 的 PSNR 是 17.2090，原文是 17.2090，正确。Ours 的 PSNR 是 17.5148，原文是 17.5148，正确。其他指标也一致。但博客中表格没有显示 SSIM 和 LPIPS 的值？哦，博客表格中有 SSIM 和 LPIPS 列，但显示的数字？实际上博客表格中 SSIM 列：DiT4SR* 0.5726，AdaRefSR* 0.5629，ImageCritic* 0.6060，Ours 0.6335。LPIPS 列：0.3884, 0.3523, 0.3039, 0.2746。这些和原文一致。
- 博客中说“在真实场景（In-the-wild）测试中…依然保持了最佳性能。”原文有 Table 3，博客没有具体数字，但提到“最佳性能”，可以接受。
- 博客中用户研究数据：83%、82%、83%，原文中 Fig.7 显示的是 top-1 rates: refine 83%, detail 82%, overall quality 83%。准确。
- 博客中工程启示部分提到“设计亮点值得借鉴：解耦控制、频率路由”。局限中“目前依赖 FLUX-Kontext backbone，计算成本较高。且需要原始高清参考图作为输入…此外，40K 的训练数据规模相对较小”。原文局限部分提到“Our RefGC-SR2 Dataset is synthesized by DipRefGC rather than directly sampled from real RefGC pipelines… restricted to object-centric scenes across 12 categories… Our RefGC-SR2 Model is also tied to the FLUX-Kontext backbone…”。博客说的计算成本较高是合理的推断。但原文没有明确说计算成本，不过可以接受。训练数据规模40K，原文确实提到40K训练三元组。博客说“相对较小”，原文没有评价大小，但可以视为合理。
可能的问题：
- 博客中“核心 Insight”部分说“作者的核心直觉非常清晰：不同频率的信息，应该由不同的机制处理。”这确实是核心，但原文更具体地通过分析层间频率特性（图5a）来支撑。博客没有提到这个分析，但不算严重遗漏。
- 博客中“数据构造的巧思”部分提到“直接拿现成模型生成 LRGI 会导致姿态不对齐”，原文确实有说明。但博客没有提到 DipRefGC 使用 diptych formulation 和两个 ControlNet 分别控制外观和姿态，但博客有提到“双 ControlNet（Inpainting 控制外观，Canny 控制姿态）”，正确。
- 博客中“频率感知损失”部分说“高频部分：匹配 HRRI 的通道统计量（而非像素值，因为视角不同）”。原文确实使用 channel-wise statistics (mean and variance) 来匹配。博客表述正确。
- 博客中表格下面有注释“注：带 * 表示在作者数据集上微调过，以保证公平对比。”原文中也有说明。正确。
- 博客中“用户研究数据”部分说“Top-1 选择率分别高达 83%、82% 和 83%，而竞争方法最高仅为 8%”。原文 Fig.7 显示竞争方法最高是 ImageCritic 在 refine 上 8%? 原文图中显示 DiT4SR 约 2%，AdaRefSR 约 3%，ImageCritic 约 8%，所以最高是 8%。正确。
- 博客中“工程启示与局限”部分说“如果你正在构建参考引导生成的管线，不要指望生成模型一次性输出完美高清结果。引入一个专门的 RefGC-SR² 模块，可以显著降低前端生成模型的负担，同时提升最终交付质量。”这个观点在原文中没有明确说，但符合论文精神。不过可能算过度解读？但不算严重。
- 博客中“局限”部分说“目前依赖 FLUX-Kontext backbone，计算成本较高。”原文在 Limitations 中说“Our RefGC-SR2 Model is also tied to the FLUX-Kontext backbone”，但没说计算成本高。不过这是合理的推断。原文��提到“may struggle when HRRI and LRGI exhibit large viewpoint or geometry gaps.”博客没有提到这一点，而是说“需要原始高清参考图作为输入，这在某些无参考图的生成场景中不适用”。原文没有讨论无参考图场景，因为任务本身需要参考图。博客说的“不适用”是合理的，但原文局限中没有提到这个。这不算错误。
- 博客中“40K 的训练数据规模相对较小”原文没有说相对较小，但可以接受。
更重要的挑刺：博客中可能存在术语错位或遗漏关键约束。例如，博客开头说“用户给的高清参考图，进模型前就被强行降采样成 512x512。”原文提到“224^2 visual tokens [3,13] or 512^2 diffusion inputs [10]”，所以不一定是512，但博客用512作为例子，可以。但博客没有提到原文中强调的“object-centric”和“pose alignment”等关键点。在数据构造部分，博客说“强制生成的 LRGI 保持与 HRGT 一致的姿态”，但原文中 DipRefGC 是通过 Canny ControlNet 来强制姿态一致。博客提到“Canny 控制姿态”，正确。但博客没有说明 DipRefGC 是在低分辨率（512^2）下生成的 LRGI，然后 HRRI 和 HRGT 保留原始高分辨率。原文中 Stage 2 提到“we downsample the curated HRRI-HRGT pairs to 512^2 resolution, while retaining the original HR images as HRRI and HRGT in the final triplets.”博客没有提到这个下采样步骤，但这不是关键。不过博客说“生成的 LRGI 保持与 HRGT 一致的姿态”，而原文强调“LRGI should be aligned (with object pose preserved) with the corresponding HRGT”。正确。
另一个可能的挑刺：博客中“FreqMoLE”部分说“通过一个门控函数 α，在浅层让低频专家主导，深层让高频专家主导。”原文中 α 是 learnable 的，并初始化为 coarse-to-fine prior，且在训练早期冻结。博客没有提到可学习和冻结细节，但不算大问题。博客说“这种‘由粗到细’的路径设计，完美契合扩散模型的层级特性。”这是合理的。
博客中“频率感知损失”部分说“低频部分：对齐 HRGT 的全局结构。高频部分：匹配 HRRI 的通道统计量（而非像素值，因为视角不同）。”原文中 LLF 使用 L1 norm restricted by object mask，LHF 使用 channel-wise statistics (mean and variance)。博客表述准确。
博客中“关键结果”表格中，对于 DiT4SR* 的 PSNR 是 15.1005，原文是 15.1005，但原文表格中 DiT4SR* 的 PSNR 是 15.1005? 检查原文 Table 2：DiT4SR∗ (ICCV’25) 行，PSNR 是 15.1005。正确。SSIM 0.5726，LPIPS 0.3884。原文中 DiT4SR∗ 的 SSIM 是 0.5726，LPIPS 0.3884，正确。
博客中表格的标题和列名与原文一致。博客省略了 OmniPaint 等结果，但只列出了对比的主要几个，可以接受。
博客中“在真实场景（In-the-wild）测试中，面对 DreamFuse、InsertAnything 等模型生成的低质输入，RefGC-SR² 依然保持了最佳性能。”原文中 Table 3 显示了在 compositing 和 customization 上的结果，博客没有具体数字，但总结正确。
博客中“用户研究数据”部分引用正确。
博客中“工程启示”部分提到“解耦控制”和“频率路由”是设计亮点。原文中没有明确说“工程启示”，但这是博客作者的解读，可以接受。
博客中“局限”部分：原文局限还包括“restricted to object-centric scenes across 12 categories”，博客没有提到12类限制，而是说“40K 的训练数据规模相对较小”。这算是一个遗漏。原文明确说“12 object category”在数据收集时，但博客没有提。不过这不是严重错误。另外，博客没有提到原文局限中的“may struggle when HRRI and LRGI exhibit large viewpoint or geometry gaps.”这也是一个遗漏。但挑刺要求指出具体遗漏，我们可以指出这些。
还需要检查博客是否有过度解读。博客说“这篇论文提出了 RefGC-SR² 任务，专门解决这个‘最后一公里’的问题。”原文中确实提到“helping to achieve the last mile of personalized image editing”。所以是准确的。
博客说“作者的核心直觉非常清晰：不同频率的信息，应该由不同的机制处理。”原文确实基于频率分析。但博客没有引用原文的具体图或数据来支持这个直觉，不过这不影响。
博客中“数据构造的巧思”部分说“直接拿现成模型生成 LRGI 会导致姿态不对齐，模型会学偏。”原文有详细论述。博客说“作者设计了 DipRefGC，利用双 ControlNet（Inpainting 控制外观，Canny 控制姿态），强制生成的 LRGI 保持与 HRGT 一致的姿态，同时继承 HRRI 的外观。”但原文中 DipRefGC 的 Inpainting ControlNet 接收 diptych 输入，左面板是分割后的对象，右面板是掩码背景和对象掩码。博客没有提到 diptych 和左面板右面板的细节，但这是合理的简化。
博客中“FreqMoLE”部分说“基于对 FLUX-Kontext 的分析，作者发现 DiT 的浅层主要捕获低频（全局结构），深层才处理高频（细节）。”原文图5a显示的是LF和HF能量随层的变化，博客概括正确。
博客中“频率感知损失”部分说“高频部分：匹配 HRRI 的通道统计量（而非像素值，因为视角不同）。”原文确实使用 channel-wise statistics。但原文还提到 LHF 使用 mean 和 variance 的 L1 距离。博客表述正确。
总的来说，这篇博文准确反映了原文的主要贡献和方法，没有严重的错误。但遗漏了原文的一些细节，例如数据集的12类限制、姿态大差异时的局限性、DipRefGC 的 diptych 具体设计等。但按照评分标准，这些遗漏属于次要细节，不构成严重事实或术语错位。博文没有过度夸大，没有核心论断不准。因此应该属于 ⭐⭐⭐ 档，即“博文准确反映论文，论文是有意义的工作”。但考虑博文提炼较好，且用户研究数据引用准确，可以给 ⭐⭐⭐ 或 ⭐⭐⭐½？需要看是否有亮点。
亮点部分：博文相对于原文的提炼/取舍是否到位？原文真正有工程价值或方法新意的点包括：1. 新任务 RefGC-SR2 的定义和问题定位；2. DipRefGC 数据生成方法；3. FreqMoLE 和频率损失。博文都提到了，并且用简明的语言表达。但博文没有强调原文中 Table 1 的定位分析，也没有强调在真实世界基准上的结果。但作为博客，已经不错。
挑刺：我们需要具体指出博文遗漏的关键约束/数字/条件。可能包括：
- 博文没有说明 DipRefGC 生成 LRGI 时是将 HRRI 和 HRGT 下采样到 512^2 后再生成，然后 HRRI 和 HRGT 保留原始高分辨率。原文明确说了“we downsample the curated HRRI-HRGT pairs to 512^2 resolution, while retaining the original HR images as HRRI and HRGT in the final triplets.” 博文没有提及这个下采样步骤，可能导致读者误解 LRGI 是从原始高分辨率直接生成的。但这不是严重错误。
- 博文没有提到数据集中包含12个物体类别（原文 Step 1 提到“12 object category”），以及来自三个数据集（ORIDa, uCO3D, UltraVideo）。虽然不影响理解，但可以视为遗漏。
- 博文没有提到原文中 FreqMoLE 的 α 是 learnable 且初始化 coarse-to-fine，并且在早期冻结。但博文只说“通过一个门控函数 α”，没有说明可学习性和初始化。不过这不是关键。
- 博文在关键结果表格中只列出了 SR、RefSR、RefGCR 和 Ours，但没有列出 OmniPaint 和 ReFIR 等，原文表格中有。但博客只选取了几个代表，可以接受。
- 博文在局限中说“计算成本较高”，原文没有明确说���但可以推断。不过原文局限中明确提到“Our RefGC-SR2 Model is also tied to the FLUX-Kontext backbone”，没有说计算成本。但这不是错误。
更重要的挑刺：博文在“核心 Insight”部分说“数据构造的巧思”时，说“直接拿现成模型生成 LRGI 会导致姿态不对齐，模型会学偏。”但原文中还有一个关键点：使用现成模型不仅姿态不对齐，而且生成的 LRGI 包含的伪影分布可能不真实，因为 DipRefGC 专门设计来模拟真实 RefGC 伪影。博文没有强调 DipRefGC 是为了产生“realistic artifact-containing RefGC output”。但也不算遗漏关键。
博文在“频率感知损失”部分说“高频部分：匹配 HRRI 的通道统计量（而非像素值，因为视角不同）。”原文还提到 LHF 计算时使用 object mask 吗？原文说“µM(HF(z0))”其中 M 表示 object mask。博文没有提到 mask 约束。但原文中 LHF 也是使用 channel-wise statistics with object mask? 原文公式：LHF = ||µM(HF(z0)) - µM(HF(zHRRI))|| + ||σM(HF(z0)) - σM(HF(zHRRI))||。M 是 object mask。博文没有提到 mask，但可以理解。
挑刺需要具体引用原文或博文片段。我们可以引用博文中的表述和原文对应表述进行对比。
例如：
- 博文说“用户给的高清参考图，进模型前就被强行降采样成 512x512。”原文提到“512^2 diffusion inputs”但同时也提到“224^2 visual tokens”，所以不全是512。但这不是大问题。
- 博文说“40K 的训练数据规模相对较小”，原文没有评价大小，但可以认为这是博文的判断，不算错误。
- 博文遗漏了原文中关于 DipRefGC 的 diptych formulation 的细节，但博客简化了。
更严格的挑刺：博文在“关键结果”表格中，将 DiT4SR* 的 PSNR 写为 15.1005，原文也是 15.1005，但原文表格中 DiT4SR* 的 PSNR 是 15.1005，SSIM 0.5726，LPIPS 0.3884。博文表格中 SSIM 列的数字与原文一致。但博文表格中“SR”行下的 DiT4SR* 的 SSIM 是 0.5726，原文是 0.5726。没问题。
但注意原文 Table 2 中 DiT4SR (ICCV’25) 没有 * 的行 PSNR 是 15.3762，SSIM 0.4932。DiT4SR∗ 行是 15.1005，0.5726。博文写的是 DiT4SR*，对应的是微调后的。正确。
博文表格中 RefSR 行下的 AdaRefSR* 的 PSNR 是 15.6200，SSIM 0.5629，LPIPS 0.3523。原文 AdaRefSR∗ 行 PSNR 15.6200，SSIM 0.5629，LPIPS 0.3523。正确。
博文表格中 RefGCR 行下的 ImageCritic* 的 PSNR 是 17.2090，SSIM 0.6060，LPIPS 0.3039。原文 ImageCritic∗ 行 PSNR 17.2090，SSIM 0.6060，LPIPS 0.3039。正确。
所以数据准确。
现在考虑评分。博文准确反映了论文，论文是有意义的工作。按照标准，⭐⭐⭐ 是“博文准确反映论文，论文是有意义的工作（多数博文的默认档）”。这里博文没有严重事实/术语错位，核心论断准确。但博文有一些遗漏，但不算严重。所以 ⭐⭐⭐ 是合适的。但可能可以考虑半星提升，如果博文在提炼和呈现上特别出色？博文结构清晰，抓住了核心，但有些细节缺失。我认为 ⭐⭐⭐ 是合理的。
但注意评分标准中 ⭐⭐⭐⭐ 是“论文有显著创新或工程价值 + 博文准确传达 insight”。论文本身确实有显著创新（新任务、新数据集、新模型），博文也准确传达了 insight。但博文是否“精准呈现”？博文可能遗漏了一些重要细节如12类限制、DipRefGC的具体输入输出结构等，但整体上传达了核心。如果严格来说，博文没有达到“精准呈现”的程度，因为遗漏了一些关键约束（如12类、姿态大差距问题）。但也许可以给 ⭐⭐⭐½。我们需要判断。
从原文来看，论文贡献很大：第一个 RefGC-SR2 任务，第一个三元组数据集，第一个模型。博文准确地传达了这些。但是博文在局限部分没有提到原文中明确的局限（如仅限物体中心场景、12类、可能在大视角差距下失败），而是自己推断计算成本高和数据规模小。这算不算“核心论断不准”？不算，因为博文局限部分也是基于原文的，但遗漏了原文明确指出的局限。不过博文没有过度夸大，所以应该还是准确反映的。
考虑到 HF Daily Papers 已预筛过质量，blog 只要忠实就到 ⭐⭐⭐。博文是忠实的，但有一些遗漏。我倾向于给 ⭐⭐⭐，因为博文没有严重错误，但也没有特别突出的提炼。但是博文在“工程启示”部分加入了自己的见解，这超出了单纯复述，但这是允许的。我认为 ⭐⭐⭐ 是安全的。
但是让我们再仔细看看是否有严重问题。博文说“用户给的高清参考图，进模型前就被强行降采样成 512x512。”原文是“downsample these references to a fixed low-resolution (LR) before injecting them into the generation process, e.g., 224^2 visual tokens [3,13] or 512^2 diffusion inputs [10]”。所以不一定是512，但博客说“512x512”作为例子，没有说所有，可以接受。但严格来说，原文列举了两个例子，博客只提了一个，且没有说明还有224。但这不算严重。
博文说“这篇论文提出了 RefGC-SR² 任务，专门解决这个‘最后一公里’的问题。”原文确实提到“helping to achieve the last mile of personalized image editing”。准确。
博文说“作者设计了 DipRefGC，利用双 ControlNet（Inpainting 控制外观，Canny 控制姿态）”。原文中 DipRefGC 使用了 Inpainting ControlNet 和 Canny ControlNet，但具体实现是 diptych formulation，每个 ControlNet 接收 diptych 输入。博客简化了，但正确。
博文说“强制生成的 LRGI 保持与 HRGT 一致的姿态，同时继承 HRRI 的外观。”原文目标是“inherits the object appearance from HRRI while following the object pose of HRGT”。正确。
博文说“FreqMoLE”部分“通过一个门控函数 α，在浅层让低频专家主导，深层让高频专家主导。”原文中 α 是 gating function，但原文也说明 α 是可学习的并初始化。博文没有说可学习，但说“门控函数”可以接受。没有错误。
博文说“频率感知损失”部分“低频部分：对齐 HRGT 的全局结构。高频部分：匹配 HRRI 的通道统计量（而非像素值，因为视角不同）。”原文确实使用 LLF 和 LHF。正确。
博文表格数据准确。
博文用户研究数据准确。
博文局限中说“目前依赖 FLUX-Kontext backbone，计算成本较高。”原文没有明确说计算成本，但可以推断。但原文局限中第一句话就是“Our RefGC-SR2 Dataset is synthesized by DipRefGC rather than directly sampled from real RefGC pipelines, and is restricted to object-centric scenes across 12 categories”。博文没有提到这个，而是说“40K 的训练数据规模相对较小”。这算是一个遗漏，但不算错误。
博文局限中说“且需要原始高清参考图作为输入，这在某些无参考图的生成场景中不适用。”这是合理的，因为任务本身就需要参考图，所以这是任务定义的限制，不是模型局限。但博文作为局限提出来，可以接受。
综合来看，博文没有严重失实，核心内容准确，但有一些次要遗漏。按照评分标准，⭐⭐⭐ 是默认档，博文达到了这个水平。但考虑到博文在提炼上比较清晰，且加入了工程启示，可以给 ⭐⭐⭐½ 吗？我认为半星提升需要博文在精准呈现方面有额外亮点，比如对频率分析动机的强调等。但博文没有详细引用原文的图5，只是概括。所以我觉得 ⭐⭐⭐ 是合理的。
但再读评分标准：“⭐⭐⭐ 博文准确反映论文，论文是有意义的工作（多数博文的默认档）”。博文准确反映论文，论文是有意义的工作，所以 ⭐⭐⭐。没有理由给更高或更低。
因此总评为 ⭐⭐⭐。
现在撰写四部分。
核心贡献：1-2句。基于原文。
亮点：1-3条。指出博文提炼到位之处。
挑刺：1-3条。必须引用原文或博文具体片段。需要仔细找。
挑刺可能包括：
-博文在数据构造部分遗漏了 DipRefGC 将 HRRI 和 HRGT 下采样到 512^2 再生成 LRGI 的细节，以及最终三元组中 HRRI 和 HRGT 保留原始高分辨率。博文说“强制生成的 LRGI 保持与 HRGT 一致的姿态”，但没有说明 LRGI 是低分辨率（256x256？原文中 LRGI 是 512x512 然后下采样到 256x256？原文说“we downsample the original 1024 × 1024 images to 256 × 256 using bicubic interpolation”作为 LRGI。但 DipRefGC 生成的是 512x512 的 LRGI？原文 Stage 2 说“we downsample the curated HRRI-HRGT pairs to 512^2 resolution, while retaining the original HR images as HRRI and HRGT in the final triplets.” 然后训练时 LRGI 是 256x256（从512下采样？原文说“For LRGI, we downsample the original 1024 × 1024 images to 256 × 256 using bicubic interpolation.” 这里有点混乱，但大致是 DipRefGC 生成 512x512 的 LRGI，然后训练 RefGC-SR2 时再下采样到 256x256 作为输入。博文没有提到分辨率细节，但这不是关键。
-博文没有提到数据集的12个类别和来源（ORIDa, uCO3D, UltraVideo）。原文明确说了。这算遗漏，但不算严重。
-博文在局限中没有提到原文明确的“restricted to object-centric scenes across 12 categories”和“may struggle when HRRI and LRGI exhibit large viewpoint or geometry gaps”。博文自己说了“计算成本较高”和“40K数据较小”，但原文没有强调计算成本。这算不准确？但也不算错误。
更严格的挑刺：博文说“用户给的高清参考图，进模型前就被强行降采样成 512x
