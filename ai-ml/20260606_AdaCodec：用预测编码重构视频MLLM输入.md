# ⭐⭐ AdaCodec：用预测编码重构视频MLLM输入

**日期**: 2026-06-06

---

论文 : AdaCodec: A Predictive Visual Code for Video MLLMs链接 : https://arxiv.org/abs/2606.02569视频多模态大模型（Video MLLMs）正面临一个尴尬的瓶颈：为了理解长视频，我们被迫塞入海量视觉 Token，导致上下文窗口爆炸、推理延迟极高。这篇论文提供了一个反直觉但极其有效的解法——别再把每一帧都当成独立的 RGB 图片喂给模型了。
### 痛点：视频里的“废话”太多了现有方案通常采用每帧独立编码（Per-frame RGB encoding）。问题是，视频中相邻帧的背景、物体布局高度冗余。这种“重复造轮子”的方式不仅浪费了宝贵的 Token 预算，还导致模型注意力被大量无意义的重复信息稀释。
现有的优化手段（如帧选择、Token 压缩）大多是在保留完整 RGB 帧的前提下做减法，依然没有摆脱“独立图像”的思维定势。AdaCodec 的核心 Insight 是： 既然人类视觉系统和现代视频编解码器都只传输“预测误差”，为什么 LLM 不行？
### 核心方法：把视频变成“预测代码”
AdaCodec 借鉴了 H.264/AV1 等标准中的 I/P 帧概念，但针对 MLLM 进行了彻底的重构：
- I 帧（关键帧）：当模型无法通过上下文预测下一帧时，才投入完整的 ViT Token。
- P 帧（预测帧）：对于可预测的中间帧，不传图像，只传运动矢量（Motion Vectors）和残差（Residuals）。这些信号被编码为紧凑的 P-tokens。
为什么这么设计？
传统编解码器是为了人类视觉重建优化的，而 AdaCodec 是为了 LLM 推理优化的。它做了两个关键改动：
- 宏块对齐 ViT Patch：将运动估计的宏块大小调整为与 ViT 的 Patch Grid 一致（16x16），确保运动场能稳定地映射到视觉 Token 空间，避免特征错位。
- 自适应 GOP 构建：不再固定关键帧间隔，而是基于“预测成本（pcost）”。如果某一帧的预测误差超过阈值，就强制插入新的 I 帧。这意味着模型在场景剧烈变化时自动增加分辨率，在静态场景中极致压缩。
### 实验结果：少即是多论文在 Qwen3-VL-8B 上进行了详尽测试，结果令人印象深刻：
指标 Baseline (RGB) AdaCodec (1/7 Token) AdaCodec (匹配预算) MLVU (长视频) 62.2 62.7 (+0.5) 65.3 (+3.1) LongVideoBench 62.4 63.2 (+0.8) 67.8 (+5.4) MVBench (通用) 72.7 75.1 80.5 (+7.8) 首字延迟 (TTFT) 9.26s - 1.62s 端到端延迟 (E2EL) 11.18s - 3.20s⚠️ 反直觉发现 ：AdaCodec 在仅使用 1/7 Token 预算 （32k vs 224k）的情况下，在长视频基准测试中依然超越了全量 RGB 基线。这意味着预测编码不仅压缩了数据，还通过去除冗余噪声提升了信号质量。
### 工程启示：本地部署的福音对于工程师而言，AdaCodec 的价值在于 延迟的大幅降低 。
- Token 减少 84.7%：平均每个视频从 5.5 万 Token 降至 8,500 Token。
- 推理加速：首字延迟从 9.26 秒骤降至 1.62 秒，端到端延迟降至 3.2 秒。
这对于本地部署（On-device）或实时视频 Agent 至关重要。你不再需要昂贵的 GPU 集群来支撑长视频理解，消费级硬件即可实现低延迟响应。此外，其两阶段训练策略（先对齐 P-tokenizer，再微调 LLM）也证明了这种新接口可以平滑集成到现有架构中，无需从头预训练大模型。
### 局限与展望目前 AdaCodec 仍依赖固定分辨率输入，且 P 帧的 Token 数量是固定的（16 tokens）。未来若能根据帧内运动复杂度动态调整 P 帧的 Token 预算，效率边界还能进一步突破。此外，论文尚未评估流式视频场景，但其因果结构的 I/P 帧设计天然适合实时流处理，值得后续探索。
## 📝 AI 点评点评时间：2026-06-06 04:18 ｜ reviewer: DeepSeek V4 Flash核心贡献：原文针对视频MLLM中每帧独立RGB编码导致视觉token冗余和推理延迟高的问题，提出一种面向MLLM的预测视觉编码AdaCodec，通过自适应GOP结构（pcost阈值触发I帧）将可预测的中间帧编码为紧凑的运动矢量和残差P-token，在11个基准上以1/7 token预算超越全量RGB基线并大幅降低延迟。
亮点：博文准确抓住了AdaCodec的核心insight——将视频编解码中的I/P帧思想引入MLLM输入接口，并清晰解释了“只传预测误差”这一关键设计动机。对自适应GOP构建和宏块对齐ViT Patch这两个核心改动的描述到位，实验部分用表格直观展示了1/7 token和匹配预算下的性能提升，并突出了延迟降低（TTFT从9.26s降至1.62s）这一工程价值点。
挑刺：
- 关键数字错误：博文表格中Baseline (RGB)的MVBench值写作72.7，但原文Table 2明确给出Qwen3-VL-8B在该项为75.9。博文实际引用了LLaVA-Video-7B的数值（原文表2中LLaVA-Video-7B的MVBench为72.7），属于张冠李戴。这直接导致读者对AdaCodec提升幅度产生误解（博文暗示从72.7提升至80.5，实际原文是从75.9提升至80.5）。
原文：Qwen3-VL-8B在MVBench为75.9（Table 2）。
- 博文：Baseline (RGB) 72.7（表格第二行）。
- 遗漏核心设计改动：博文在“核心方法”中仅提到宏块对齐和自适应GOP两个关键改动，但原文Table 1列出了四个核心重设计：还包括Motion reference（每个P帧从前一帧预测而非标准codec的参考帧选择）和Search window（扩大搜索窗口以适应低帧率）。这两个设计对处理大时间间隔下的运动估计至关重要，博文完全未提及，导致方法描述不够完整。
原文：Table 1中“Motion reference: Each P-frame is estimated from the immediately preceding sampled frame for larger temporal gaps”和“Search window: Enlarged local window to absorb the larger displacement between low-FPS frames”。
- 过度简化I帧触发条件：博文说“当模型无法通过上下文预测下一帧时，才投入完整的ViT Token”，但原文明确I帧插入由pcost > γ触发，且γ通过训练集上目标中位GOP长度8帧来选取，并非一个简单的“无法预测”的定性判断。这种表述虽通俗但丢失了定量阈值的关键细节。
原文：3.1节“We choose γ on the training split by targeting a median of 8 P-frames per GOP”以及“start a new GOP when ℓt > γ”。
总评：⭐⭐（2星）博文整体结构清晰，核心insight传达正确，但存在关键数据引用错误（MVBench基线值），属于严重事实错位，且遗漏了原文中两个重要的codec设计改动，影响了读者对方法全貌和真实性能提升的准确理解。