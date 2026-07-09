# ⭐⭐⭐½ 告别校准数据：DiT量化新范式OrbitQuant

**日期**: 2026-07-06

---

论文 : OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion Transformers链接 : https://arxiv.org/abs/2607.02461扩散模型（Diffusion Models）正全面转向 Transformer 架构（DiT），但推理成本居高不下。后训练量化（Post-Training Quantization, PTQ）是降本利器，却长期受困于一个工程噩梦： 激活值分布随时间步和提示词剧烈漂移 。现有方案必须为每个新模型收集校准集并重新拟合参数，这在快速迭代的生成式 AI 领域简直无法接受。
OrbitQuant 的出现，旨在彻底终结这种“依赖数据”的量化流程。它提出了一种**数据无关（Data-Agnostic）**的量化方法，无需任何校准数据即可实现高精度量化，甚至能在 W2A4（权重 2 位、激活 4 位）这种极端低位宽下保持可用画质。
### 痛点：为什么 DiT 难量化？
在 LLM 中，激活值统计特性相对稳定，一次校准可复用多次。但在 DiT 中，情况完全不同：
- 分布漂移：去噪过程跨越多个时间步（timesteps），激活值范围随步骤剧烈变化。
- 条件敏感：不同的提示词（Prompt）和无分类器自由引导（CFG）分支会导致激活值分布显著不同。
现有的 PTQ 方法（如 SVDQuant、ViDiT-Q）试图通过收集校准数据来“捕捉”这些变化，但这导致每次更换模型或分辨率时，都要重新跑一遍昂贵的校准流程。OrbitQuant 的核心洞察是： 既然无法预测激活值的具体范围，不如将其旋转到一个已知且固定的分布空间中。
### 方法拆解：旋转与固定码本OrbitQuant 的设计哲学非常优雅，主要包含三个关键步骤：
-随机置换块哈达玛变换（RPBH）
这是核心创新。作者使用一种高效的正交旋转矩阵 RPBH 对激活值进行旋转。
直觉：经过这种特定旋转后，无论原始输入是什么，归一化后的坐标都会收敛到一个固定的边际分布 fd≈N(0,1/d)f_d \approx \mathcal{N}(0, 1/d)​≈N(0,1/d)。
这意味着，我们不再需要针对每个输入动态计算量化尺度（Scale），因为所有输入在旋转后都遵循同一套统计规律。
-离线构建 Lloyd-Max 码本基于上述固定分布，作者预先计算了一个 MSE 最优的 Lloyd-Max 量化码本。这个码本仅依赖于维度 dd 和位宽 bb，与具体数据无关。
-权重吸收旋转（Weight Absorption）
为了保持数学等价性，旋转操作被“折叠”进权重矩阵中。
离线阶段：将旋转矩阵 ΠdT\Pi_d^TT​ 乘到权重 WW 上，得到 W′=WΠdTW' = W\Pi_d^T=WΠdT​，并对 W′W' 进行量化。
- 在线阶段：输入激活值 xx 先经过正向旋转 Πdx\Pi_d x​x，再使用固定码本量化。
最终计算为 W′x^′≈WΠdT(Πdx)=WxW'\hat{x}' \approx W\Pi_d^T (\Pi_d x) = Wx x ^ ′ ≈ W Π d T ​ ( Π d ​ x ) = W x 。旋转在矩阵乘法内部抵消，推理时只需执行一次前向旋转和查表操作，无需逆旋转重建，极大降低了延迟。
### 关键结果：碾压式领先OrbitQuant 在图像和视频生成任务上均取得了 SOTA 的 PTQ 性能，且完全无需校准数据。
图像生成（GenEval 基准）
在 FLUX.1-dev 模型上，W4A4 量化下 OrbitQuant 的表现几乎无损：
方法 Bit-width Overall Score (FLUX.1-dev) 备注 FP16 (Baseline) 16/16 0.667 原始精度 SVDQuant W4A4 0.573 需校准 ViDiT-Q W4A4 0.280 需校准 OrbitQuant W4A4 0.633 无需校准，接近 FP16更令人震惊的是在 W2A4 极端低位宽下：
- 其他所有 PTQ 基线（QuaRot, SmoothQuant 等）得分均跌至 0.000 - 0.001，生成结果完全崩溃。
- OrbitQuant 依然保持了 0.475 的 Overall Score，是唯一能产生可用图像的方法。
视频生成（VBench 基准）
在 Wan 2.1-1.3B 模型上，W4A6 量化下：
- OrbitQuant 在整体一致性（Overall Consistency）上达到 24.35%，优于 ViDiT-Q 的 19.58%。
- 在动态程度（Dynamic Degree）等关键指标上也全面领先。
效率优势由于去除了复杂的校准和动态尺度计算，OrbitQuant 的推理开销最低。在 FLUX.1-dev 上，其延迟仅为 QuaRot 的约 78% （QuaRot 慢 1.28 倍），且峰值内存与未量化模型持平。
### 工程启示- 部署简化：对于希望将 DiT 模型部署到边缘设备或低成本云服务的团队，OrbitQuant 消除了“校准数据收集”这一繁琐步骤。你只需下载模型权重，应用预计算的码本即可直接推理。
- 极致压缩潜力：W2A4 的可用性证明了 DiT 对低位宽的容忍度比预期高。虽然目前 W2A4 画质仍有损失，但为未来进一步压缩（如 W1A4）提供了理论可行性验证。
- 通用性：该方法从图像无缝迁移到视频模型（Wan, CogVideoX），无需任何模态特定的调整，体现了极强的泛化能力。
### 局限与展望尽管效果显著，OrbitQuant 并非完美：
- AdaLN 层处理：自适应层归一化（AdaLN）层的调制参数无法通过旋转吸收，目前仍保留为 INT4 权重。论文指出若进一步降低 AdaLN 位宽会导致性能崩溃，这部分仍是压缩瓶颈。
- 视觉伪影：在 W2A4 下，虽然结构保持，但细节纹理仍存在一定模糊，距离 FP16 仍有肉眼可见差距。
OrbitQuant 证明了通过数学变换（旋转）将动态问题静态化是解决 DiT 量化难题的有效路径。对于追求极致推理效率的工程师而言，这是一个值得深入研究的开源方案。
## 📝 AI 点评点评时间：2026-07-06 17:06 ｜ reviewer: DeepSeek V4 Flash我们被要求基于原文（arxiv 2607.02461 全文）和博文（Qwen3.6-27B 根据它自动生成的中文技术博客）进行点评。需要输出四个部分：核心贡献、亮点、挑刺、总评。评分标准严格按标尺。注意博文是自动生成的，可能存在遗漏、过度解读、术语错位等。我们需要对照原文和博文。
先梳理原文核心贡献：原文提出OrbitQuant，一种数据无关（data-agnostic）的权重激活量化方法用于扩散Transformer。核心方法：通过随机置换块哈达玛（RPBH）旋转将激活和权重归一化到固定分布，然后使用离线构建的Lloyd-Max码本进行量化，旋转被吸收进权重，只需前向旋转激活。解决了DiT激活分布漂移问题，无需校准数据。
博文标题：告别校准数据：DiT量化新范式OrbitQuant。内容基本正确概括了要点，但需要检查细节。
亮点：博文对原文的提炼是否到位？原文真正有工程价值或方法新意的点：1) RPBH旋转+固定分布码本实现数据无关量化；2) 权重吸收旋转，取消逆旋转；3) 在W2A4极端低位宽下仍可用，且跨图像视频通用。博文提到了这些，但可能不够精确。
挑刺：需要指出博文遗漏的关键约束/数字/条件、过度解读、术语错位等。必须引用原文或博文的具体片段或数据做依据。
仔细对比：
-博文说“无需任何校准数据即可实现高精度量化”。原文确实说data-agnostic，但注意原文在实验中使用的是“no calibration data”，但博文说“无需校准数据”正确。但需要检查是否有遗漏细节：比如AdaLN层处理，原文说“AdaLN modulation projections … we still quantize these projections to INT4 rather than keep them in BF16”。博文提到了“AdaLN层处理…目前仍保留为INT4权重”，但原文提到“AdaLN modulation projections … kept at INT4 weight RTN”，且图6显示AdaLN权重量化到INT4几乎匹配BF16，但到W2会崩溃。博文说“若进一步降低AdaLN位宽会导致性能崩溃”，正确。
-博文中的表格：对于FLUX.1-dev W4A4，原文Table 1显示OrbitQuant Overall 0.633，ViDiT-Q 0.280，SVDQuant 0.573。但博文表格中ViDiT-Q写0.280，SVDQuant写0.573，OrbitQuant写0.633。但注意原文中SVDQuant在FLUX.1-dev W4A4的Overall是0.573，但博文表格中SVDQuant写0.573正确。但是博文表格中ViDiT-Q是0.280？原文Table 1中ViDiT-Q在FLUX.1-dev W4A4 Overall是0.280（确实是0.280）。正确。
-但博文表格中FP16 Baseline Overall是0.667，原文Table 1中FLUX.1-dev FP16 Overall是0.667，正确。
-博文说“在FLUX.1-dev模型上，W4A4量化下OrbitQuant的表现几乎无损”，并给出0.633 vs 0.667，确实接近，但说“几乎无损”有点夸张，因为0.633比0.667低0.034，不过原文说“trailing it by 0.034”，博文可以接受。
-博文说“效率优势：由于去除了复杂的校准和动态尺度计算，OrbitQuant的推理开销最低。在FLUX.1-dev上，其延迟仅为QuaRot的约78%（QuaRot慢1.28倍）”。原文说“OrbitQuant has the lowest overhead … with SmoothQuant, QuaRot, and ViDiT-Q running 1.09×, 1.28×, and 1.40× slower”。注意是“慢1.28倍”即QuaRot延迟是OrbitQuant的1.28倍，所以OrbitQuant延迟是QuaRot的约78%（1/1.28≈0.78）。博文表述正确。
-博文在“关键结果”中写“在FLUX.1-dev模型上，W4A4量化下OrbitQuant的表现几乎无损”，但原文Table 1中OrbitQuant在FLUX.1-dev W4A4 Overall 0.633，低于FP16 0.667，且低于SVDQuant 0.573？等等，SVDQuant是0.573，低于OrbitQuant的0.633��所以OrbitQuant是第二？实际上Table 1中FLUX.1-dev W4A4：SVDQuant 0.573, AdaTSQ 0.618, OrbitQuant 0.633。所以OrbitQuant最高。博文说“几乎无损”可以接受，因为比FP16低0.034，但仍是SOTA。
-但博文表格中SVDQuant写0.573，ViDiT-Q写0.280，OrbitQuant写0.633。但原文中SVDQuant是0.573，AdaTSQ是0.618，OrbitQuant是0.633。博文没有提到AdaTSQ，但这不是大问题。博文表格中“备注”列写“需校准”对于SVDQuant和ViDiT-Q，正确。
-博文在“方法拆解”中描述“随机置换块哈达玛变换（RPBH）”，提到“归一化后的坐标都会收敛到一个固定的边际分布 fd≈N(0,1/d)f_d \approx \mathcal{N}(0, 1/d)​≈N(0,1/d)”。原文Proposition 1给出方差集中，并且说“For d ≥ 64, this marginal is tightly approximated by N(0, 1/d)”。博文正确。
-博文说“旋转操作被‘折叠’进权重矩阵中”，并解释离线阶段和在线阶段。原文Algorithm 1详细描述了。博文简洁正确。
-博文“关键结果”中写“在Wan 2.1-1.3B模型上，W4A6量化下：OrbitQuant在整体一致性（Overall Consistency）上达到24.35%，优于ViDiT-Q的19.58%”。原文Table 2中Wan 2.1-1.3B W4A6 Overall Consistency：OrbitQuant 24.35, ViDiT-Q 19.58。正确。
-博文“局限与展望”提到“AdaLN层处理…目前仍保留为INT4权重。论文指出若进一步降低AdaLN位宽会导致性能崩溃，这部分仍是压缩瓶颈。”原文图6确实显示AdaLN权重降到W2导致FLUX模型崩溃。但博文说“保留为INT4权重”，原文说“OrbitQuant fixes AdaLN modulation projections at INT4 weight RTN”。但注意原文中AdaLN权重是INT4，但激活是BF16。博文没有明确激活是BF16，但说“保留为INT4权重”可以接受。不过更精确地，原文说“We therefore quantize only their weights, with INT4 RTN at group size 64 and BF16 activations。”博文未提及激活保留BF16，但不算严重遗漏。
-博文说“视觉伪影：在W2A4下，虽然结构保持，但细节纹理仍存在一定模糊，距离FP16仍有肉眼可见差距。”原文没有明确说“模糊”，但图1和定性比较显示W2A4有退化。可以接受。
现在需要找挑刺：博文是否遗漏关键约束/数字/条件？是否有过度解读或术语错位？
-博文说“OrbitQuant 的出现，旨在彻底终结这种‘依赖数据’的量化流程。” 原文确实data-agnostic，但注意原文在实验设置中仍然有一些处理：AdaLN层需要INT4 RTN，并且使用了group size 64。博文没有提到AdaLN的group size。但这不是关键。
-博文在“关键结果”表格中，对于FLUX.1-dev W4A4，OrbitQuant的Overall Score 0.633，但原文Table 1中OrbitQuant在FLUX.1-dev W4A4是0.633，但注意原文中还有AdaTSQ 0.618，SVDQuant 0.573。博文没有列出AdaTSQ，但这不是错误，只是简化。
-博文说“在FLUX.1-dev模型上，W4A4量化下OrbitQuant的表现几乎无损”，但原文指出“trailing it by 0.034”，且对比FP16是0.667 vs 0.633，差距约5%，严格说不是“几乎无损”。但博文用了“几乎无损”可能有点过度，但可以接受。
-博文在“方法拆解”中说“无论原始输入是什么，归一化后的坐标都会收敛到一个固定的边际分布”。原文Proposition 1给出的是高概率下方差集中，并且需要归一化。博文没有提及需要归一化（除以L2范数），但前面提到了“归一化后的坐标”，所以正确。
-博文在“关键结果”中说“更令人震惊的是在 W2A4 极端低位宽下：其他所有 PTQ 基线（QuaRot, SmoothQuant 等）得分均跌至 0.000 - 0.001，生成结果完全崩溃。OrbitQuant 依然保持了 0.475 的 Overall Score”。注意原文Table 1中FLUX.1-dev W2A4 OrbitQuant Overall是0.475？原文Table 1中FLUX.1-dev W2A4 OrbitQuant Overall是0.475（正确），但注意FLUX.1-schnell W2A4是0.604，Z-Image-Turbo是0.319。博文说0.475，可能是针对FLUX.1-dev。但博文没有明确是哪个模型，上下文是“在FLUX.1-dev模型上”，但前面表格是针对FLUX.1-dev，所以0.475正确。但博文说“其他所有PTQ基线得分均跌至0.000-0.001”，原文Table 1中QuaRot、SmoothQuant、ViDiT-Q在FLUX.1-dev W2A4确实都是0.001或0.000，正确。
-博文在“工程启示”中说“你只需下载模型权重，应用预计算的码本即可直接推理。” 原文中码本是预计算的，但还需要应用RPBH旋转（虽然被吸收进权重，但激活需要旋转）。博文说“应用预计算的码本”可能忽略旋转步骤，但前面已经说明了旋转吸收。不过“直接推理”可能简化了，但整体正确。
-博文在“关键结果”表格的备注列中写“需校准”对于SVDQuant和ViDiT-Q，但原文中SVDQuant和ViDiT-Q确实是校准-based。正确。
-博文在“效率优势”中说“由于去除了复杂的校准和动态尺度计算，OrbitQuant的推理开销最低。” 原文中确实如此，但注意OrbitQuant的激活量化需要查表（nearest-centroid lookup），而QuaRot是动态per-token uniform quantization。博文说“去除了动态尺度计算”正确。
-博文“方法拆解”中描述“离线构建 Lloyd-Max 码本”时，说“这个码本仅依赖于维度 d 和位宽 b，与具体数据无关。”原文中确实如此。
-博文“方法拆解”中描述“权重吸收旋转”时，说“离线阶段：将旋转矩阵 Π_d^T 乘到权重 W 上，得到 W’ = WΠ_d^T，并对 W’ 进行量化。”原文Algorithm 1第7行是W’ ← WΠ_d^T，正确。但注意原文中旋转是Π_d，博文写Π_d^T，但正交矩阵转置等于逆，所以一致。但博文说“正向旋转 Π_d x”，原文是x’ ← xΠ_d^T（第13行），所以激活旋转是乘以Π_d^T，而不是Π_d。博文说“输入激活值 x 先经过正向旋转 Π_d x”，但原文中x’ = Π_d x（公式7？原文公式7是x’ = Π_d x？检查：原文Section 4.3公式(7)：“x’ = Π_d x”。但注意在Algorithm 1第13行是“x’ ← xΠ_d^T”。有冲突？原文公式(7)写的是“x’ = Π_d x”，但算法中却是xΠ_d^T。实际上，在4.3节开头：“each incoming activation x is rotated by Π_d before it enters the layer”，公式(7)写x’ = Π_d x。但在算法第13行，因为权重已经乘了Π_d^T（第7行），所以激活需要乘Π_d以保持等价？但算法第7行W’ = WΠ_d^T，第13行x’ = xΠ_d^T？这样乘积是W’ x’ = WΠ_d^T (xΠ_d^T) = W (xΠ_d^T Π_d^T)？不对。需要仔细看原文：Algorithm 1第7行：W’ ← WΠ_d^T，第13行：x’ ← xΠ_d^T。那么W’ x’ = WΠ_d^T xΠ_d^T = W (xΠ_d^T Π_d^T) = W x (Π_d^T Π_d^T)？这不等价。实际上，原文描述是“The weight absorbs Π_d^T and the activation applies Π_d, so the two cancel in the product, W’ x’ = WΠ_d^T Π_d x = Wx.” 但算法第7行W’ = WΠ_d^T，第13行x’ = xΠ_d^T，乘积是WΠ_d^T xΠ_d^T，不是Wx。矛盾。再看原文：Section 4.2公式(4): W’ = WΠ_d^T。Section 4.3公式(7): x’ = Π_d x。但算法第13行是x’ ← xΠ_d^T。可能是笔误？实际上，如果激活旋转是左乘Π_d，则x’ = Π_d x（shape (d, N)？通常激活是N×d，所以需要右乘Π_d^T得到N×d？原文中x是N×d，所以x’ = xΠ_d^T是右乘，得到N×d。而公式(7)写x’ = Π_d x可能是为了符号简洁，但实际实现是右乘。算法第13行x’ ← xΠ_d^T是正确的，因为x是N×d，Π_d是d×d，xΠ_d^T得到N×d。而权重W是m×d，W’ = WΠ_d^T也是右乘，得到m×d。那么乘积W’ (x’)^T？不对，线性层是y = W x^T？通常y = W x，x是列向量。如果x是行向量，则y = x W^T。这里需要统一。原文中，对于token-wise，每个token是行向量，线性层是y = x W^T（因为W是m×d，输出m维）。但原文写Wx（公式1），假设x是列向量。为了简化，通常实现中x是(batch, d)，W是(m, d)，输出是(batch, m)通过x @ W^T。原文可能使用列向量约定。但无论如何，关键点是旋转吸收后，乘积不变。算法第7行W’ = WΠ_d^T，第13行x’ = xΠ_d^T，那么x’ @ W’^T = xΠ_d^T @ (WΠ_d^T)^T = xΠ_d^T @ Π_d W^T = x (Π_d^T Π_d) W^T = x W^T，因为Π_d^T Π_d = I。所以乘积不变。所以算法中x’ = xΠ_d^T是对的，因为W’也是右乘Π_d^T。博文说“输入激活值 x 先经过正向旋转 Π_d x”，如果理解为左乘Π_d，则与算法不符。但博文说“正向旋转 Π_d x”，然后“最终计算为 W’ x̂’ ≈ WΠ_d^T (Π_d x) = Wx”，这假设了x是列向量，W’ = WΠ_d^T，x’ = Π_d x，乘积是WΠ_d^T Π_d x = Wx。如果x是列向量，那么x’ = Π_d x是列向量，W’ = WΠ_d^T是矩阵，乘积是WΠ_d^T * (Π_d x) = Wx。但此时W’的维度是m×d，Π_d x是d×1，乘积正确。但在算法中，x是N×d，所以需要右乘。博文的描述在数学上正确（假设列向量），但实际实现有转置差异。这不算严重错误，因为博文是概念性描述。但可能引起混淆。
然而，博文没有提到算法中的具体转置，所以不算错。但我们可以指出博文在描述旋转方向时没有明确，但这不是关键。
主要挑刺点：
-博文在“方法拆解”中说“离线构建 Lloyd-Max 码本”时，没有提到码本是对归一化后的方向向量使用的，且需要与权重行归一化配合。原文中权重行量化也是先归一化再量化方向，然后乘以行范数。博文只说“离线构建 Lloyd-Max 码本”，没有详细说明权重量化也使用相同码本且需要行归一化。但博文在“权重吸收旋转”中提到“对 W’ 进行量化”，但没有说明量化方式。可能读者会误解为直接量化W’的每个元素。原文中权重量化是：先计算行范数，归一化行方向，用Lloyd-Max量化方向，再乘回行范数。博文没有提到行归一化步骤，这是一个遗漏。但博文在“方法拆解”第三点说“对 W’ 进行量化”，可能隐含了同样的量化流程。但不够清晰。
-博文在“关键结果”表格中，对于FLUX.1-dev W4A4，OrbitQuant的Overall Score是0.633，但原文中OrbitQuant在FLUX.1-dev W4A4是0.633，而FP16是0.667。博文说“几乎无损”，但严格来说有5%的损失。不过可以接受。
-博文在“局限与展望”中说“AdaLN层处理…目前仍保留为INT4权重。”但原文中AdaLN权重是INT4，但激活是BF16。博文没有说激活，但“保留为INT4权重”正确。然而，原文指出AdaLN层占27%的权重，如果留在BF16会降低压缩比，所以OrbitQuant选择INT4。博文没有提及这个权衡。
-博文在“工程启示”中说“你只需下载模型权重，应用预计算的码本即可直接推理。”实际上还需要应用RPBH旋转到激活（虽然被吸收进权重，但激活侧仍需要旋转）。博文前面已经说明了，但这里说“应用预计算的码本”可能忽略旋转。不过整体意思正确。
-博文在“关键结果”中写“在FLUX.1-dev模型上，W4A4量化下OrbitQuant的表现几乎无损”，但原文Table 1中还有AdaTSQ达到0.618，SVDQuant 0.573，OrbitQuant 0.633，确实最好。但“几乎无损”可能稍过，但鉴于差距0.034，可以算接近。
-博文在“关键结果”表格中，SVDQuant在FLUX.1-dev W4A4是0.573，但原文中SVDQuant在FLUX.1-dev W4A4是0.573，但注意原文中SVDQuant在FLUX.1-schnell W4A4是0.624，在Z-Image-Turbo是0.718。博文只列了FLUX.1-dev，没问题。
现在考虑评分。博文整体准确反映了论文内容，没有严重事实错误。遗漏了一些细节（如权重量化的行归一化步骤、AdaLN激活精度、码本构建细节），但这些都是次要细节。博文没有过度夸大（除了“几乎无损”有点宽松，但不算严重）。术语使用正确。因此应该属于三星档：博文准确反映论文，论文是有意义的工作。但博文是否达到了“准确传达 insight”？是的。所以三星。但可以加半星？博文在关键结果表格中有一个小错误：在“备注”列写“需校准”，但SVDQuant和ViDiT-Q确实是需校准，正确。但注意原文中SVDQuant和ViDiT-Q是calibration-based，但SVDQuant也使用了低秩分支，博文没提。但没问题。
仔细看博文“关键结果”表格中，ViDiT-Q的Overall Score是0.280，但原文Table 1中ViDiT-Q在FLUX.1-dev W4A4 Overall是0.280，正确。但博文在表格上面写“在FLUX.1-dev模型上，W4A4量化下OrbitQuant的表现几乎无损”，然后表格显示OrbitQuant 0.633 vs FP16 0.667，确实接近。但表格中ViDiT-Q 0.280和SVDQuant 0.573，但SVDQuant是0.573，比OrbitQuant低，但博文没有强调SVDQuant也是需校准且表现也不错。但这不是问题。
另一个潜在问题：博文在“关键结果”中说“更令人震惊的是在 W2A4 极端低位宽下：其他所有 PTQ 基线（QuaRot, SmoothQuant 等）得分均跌至 0.000 - 0.001，生成结果完全崩溃。” 注意原文中QuaRot和SmoothQuant在W2A4下确实是0.001和0.000，但ViDiT-Q也是0.001。但博文说“等”包括了所有基线，正确。但注意原文中还有SVDQuant和AdaTSQ没有在W2A4列出？原文Table 1中W2A4只有QuaRot、SmoothQuant、ViDiT-Q和OrbitQuant。所以博文说“其他所有PTQ基线”是指这些。正确。
博文在“关键结果”表格中，对于FLUX.1-dev W4A4，只列出了SVDQuant和ViDiT-Q，没有列出AdaTSQ、Q-DiT、SmoothQuant、QuaRot等。但博文在文字中说“其他所有PTQ基线（QuaRot, SmoothQuant等）”，表格中只选了代表性两个。这不算遗漏。
现在需要写核心贡献、亮点、挑刺、总评。
核心贡献：以原文为准。原文核心贡献：提出OrbitQuant，一种数据无关的权重激活量化方法，通过RPBH旋��将激活和权重映射到固定分布，使用离线Lloyd-Max码本量化，无需校准数据。在图像和视频DiT上达到SOTA PTQ，支持W2A4。
博文亮点：博文准确提炼了方法的核心：旋转+固定码本、权重吸收、数据无关。突出了W2A4的突破性结果。强调了工程启示（部署简化、极致压缩）。博文结构清晰。
挑刺：需要指出具体遗漏或偏差。
可能的挑刺：
-博文在描述权重量化时，没有提及行归一化步骤，可能让读者误以为直接量化W’的每个元素。原文明确将每行归一化再量化方向，并保留行范数。这是一个关键细节，因为Lloyd-Max码本是对单位向量设计的。博文在“权重吸收旋转”中说“并对W’进行量化”，过于简略，可能造成误解。
-博文在“关键结果”表格中，对于FLUX.1-dev W4A4，只列出了三个方法，但原文有七个基线。虽然不致命，但可能让读者以为只有这些对比。但博文在文字中提到了“其他所有PTQ基线”，表格是示例，可以接受。
-博文在“效率优势”中说“其延迟仅为QuaRot的约78%（QuaRot慢1.28倍）”。原文中QuaRot慢1.28倍，即OrbitQuant延迟是QuaRot的1/1.28≈0.78，正确。但博文没有说明是在什么设置下（FLUX.1-dev 1024^2 50 steps）。但可以。
-博文在“方法拆解”中说“经过这种特定旋转后，无论原始输入是什么，归一化后的坐标都会收敛到一个固定的边际分布 f_d ≈ N(0,1/d)。” 原文中Proposition 1给出了方差集中，并且需要d≥64。博文没有提及d≥64的条件，但这不是关键。
-博文在“局限与展望”中说“AdaLN层处理…目前仍保留为INT4权重。”但原文中AdaLN权重是INT4，但激活是BF16。博文没有明确激活精度，可能误导读者以为整个层都是INT4。不过说“保留为INT4权重”可以理解为权重是INT4。
-博文在“工程启示”中说“你只需下载模型权重，应用预计算的码本即可直接推理。”实际上还需要在激活上应用RPBH旋转（虽然旋转被吸收进权重，但激活侧仍然需要旋转）。博文前面已经描述了在线阶段需要旋转，但这里说“应用预计算的码本”不够完整。
总体来看，博文质量较高，没有严重事实错误，遗漏了权重量化行归一化的细节，但这是次要的。根据评分标准，多数博文默认档是三星，如果博文准确反映论文，就到三星。我认为可以给三星半（⭐⭐⭐½），因为博文在关键点上准确，且结构清晰，但遗漏了权重量化的重要细节（行归一化），这可能导致理解偏差。不过评分标准中“博文遗漏次要细节不算严重瑕疵”，行归一化算是关键细节吗？我认为是核心方法的一部分，因为Lloyd-Max码本是对单位向量设计的，如果不归一化，直接量化W’的每个元素会破坏分布。所以遗漏这个细节算是一个小瑕疵，但不算严重。所以三星半合适。
但需要权衡。也可以给三星。我倾向于三星半，因为博文整体很好，但有一个关键细节遗漏。
现在撰写输出。
注意格式：不要加标题前缀，不要markdown代码块包装。输出完毕后单独一行写