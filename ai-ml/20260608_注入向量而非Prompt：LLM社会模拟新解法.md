# ⭐⭐⭐½ 注入向量而非Prompt：LLM社会模拟新解法

**日期**: 2026-06-08

---

论文 : Parametric Social Identity Injection and Diversification in Public Opinion Simulation链接 : https://arxiv.org/abs/2603.16142做基于大语言模型（LLM）的舆情仿真或 Agent 模拟时，大家常遇到一个尴尬： 生成的“人”太像机器人了 。
无论你怎么调整 Prompt，不同背景的 Agent 给出的回答往往趋同，缺乏真实社会中那种复杂的异质性。这篇来自清华大学和全承实验室的工作，直接指出了现有方法的致命伤—— 多样性坍塌（Diversity Collapse） ，并提出了一套在隐藏层直接注入身份向量的工程化方案。
### 痛点：Prompt 的“半衰期”与多样性坍塌现有的社会模拟主要靠 Persona-based Prompting（如“你是一个30岁的程序员”）。但作者发现，这种基于文本的条件输入存在严重的 语义衰减 。
随着 Transformer 层数的加深，Prompt 中的身份信息在隐藏表示中被逐渐平滑、稀释。作者通过可视化分析发现，底层和中间层的表示还算分散，但到了高层，不同身份的 Agent 其隐藏状态竟然坍缩成了密集的簇。这就是所谓的 Diversity Collapse 。
⚠️ 核心洞察 ：文本 Prompt 只是表面的“激活线索”，无法在深层推理中维持稳定的身份约束。要解决同质化，必须把身份变成模型内部可计算的参数，而不是外部的一串字符。
### 方法拆解：PSII（参数化社会身份注入）
作者提出了 Parametric Social Identity Injection (PSII) ，核心思路是把“人设”从 Prompt 搬进 Hidden States。
- 构建人口统计向量：
不再依赖文本描述，而是为每个属性值（如“已婚”、“高收入”）预计算一个向量。方法是让模型回答一系列探测问题，取条件均值与边缘均值的差值作为该属性的身份向量 dk,j\mathbf{d}_{k,j}​。
- 分层注入策略：
这是最精彩的工程直觉。Transformer 的不同层处理不同语义：
底层：注入行为约束（如“与父母同住”）。
- 中层：注入视角背景（如“宗教信仰”）。
- 高层：注入最终立场（如“教育程度”、“社会阶层”）。
- 噪声扰动机制：
为了避免同一身份下的 Agent 变成克隆人，PSII 在注入时加入高斯噪声 ϵ∼N(0,σ2I)\epsilon \sim N(0, \sigma^2 I)N(0,σ2I)。σ\sigma 的大小根据模型对扰动的敏感度动态校准（例如 Llama-3.1-8B 的 σ=0.07\sigma=0.070.07，而 Qwen2.5-14B 需要更大的 σ=0.35\sigma=0.350.35）。
### 关键结果：显著优于 Prompt Engineering在 World Values Survey (WVS) 数据集上，PSII 的表现碾压了包括 SimVBG、Persona Vectors 在内的主流基线��以 Qwen2.5-7B 为例，整体 KL 散度（越低越好）从 Direct 的 1.3915 降至 PSII 的 0.4843 。
方法 Qwen2.5-7B KL ↓\downarrow Qwen2.5-7B ED ↓\downarrow Direct 1.3915 0.7340 SimVBG 0.6945 0.2908 PSII 0.4843 0.0319注：ED (Entropy Deviation) 衡量分布多样性与人类真实数据的偏差，越低越接近真实人群。
在 Llama-3.1-8B 上，PSII 的整体 ED 仅为 0.0040 ，几乎完美复现了人类受访者的回答分布多样性。相比之下，单纯提高 Temperature (High-Temp) 虽然能增加随机性，但往往导致逻辑混乱，且在不同模型间表现极不稳定。
### 工程启示- Representation Steering 是刚需：对于需要长期维持特定角色或复杂背景的任务，仅靠 Prompt 是不可靠的。在 Hidden States 层面进行加法干预（Additive Intervention）是更稳健的路径。
- 分层注入的价值：不要把所有身份向量都加到最后一层。根据语义抽象程度选择注入层级，能显著提升 Agent 的行为一致性。
- 低成本、高复用：PSII 不需要微调模型权重，只需预计算一组向量库。这意味着你可以快速构建一个包含数百万种人口统计组合的 Agent 池，且存储成本极低。
### 局限与展望尽管效果显著，PSII 目前仍依赖预定义的属性集（如性别、收入），对于更细微的心理特质捕捉有限。此外，不同规模模型对噪声的敏感度差异巨大，跨模型迁移时仍需重新校准 σ\sigma 参数。
但这篇论文提供了一个清晰的范式： 当 Prompt 失效时，去操纵表示空间。 这对于构建高保真度的社会仿真系统具有重要的工程指导意义。
## 📝 AI 点评点评时间：2026-06-08 18:12 ｜ reviewer: DeepSeek V4 FlashParametric Social Identity Injection (PSII) 通过将人口统计属性和价值取向的参数化向量直接注入 LLM 中间隐藏状态，并采用分层注入与噪声扰动，解决公共舆论模拟中 prompt 级身份条件导致的多样性坍塌问题，无需微调模型权重。
亮点方面，博文准确提炼了“多样性坍塌”这一核心现象，并清晰传达了“把身份从 prompt 搬进 hidden states”的方法论转向，对分层注入的工程直觉（底层约束、中层视角、高层立场）做了通俗且准确的解释。文中给出的 Qwen2.5-7B 上 KL 从 1.3915 降至 0.4843、Llama-3.1-8B 上 ED 降至 0.0040 等关键数字与原文一致，凸显了 PSII 的显著提升。对噪声校准的模型特异性（如 Llama-3.1-8B 的 σ=0.07 与 Qwen2.5-14B 的 σ=0.35）也做了正确引用。
挑刺方面，博文存在两个重要遗漏与一处表述偏差。第一，博文在方法拆解中仅描述了“构建人口统计向量”，完全未提及 PSII 的另一个核心组件—— Value Vectors（语言值向量） 。原文第 3.1.3 节明确说明 Value Vectors 通过 CulturaX 数据集训练，用于注入文化语言背景并在最后一层注入，是 PSII 区别于 Persona Vectors 的关键创新之一。博文对此只字未提，导致读者对 PSII 的完整性理解不足。第二，博文说“把‘人设’从 Prompt 搬进 Hidden States”，暗示完全放弃 prompt 级身份。然而原文 PSII 仍使用 prompt-level agent profile（第 3.1.1 节），消融实验（表 2）显示移除 prompt-based profile 会使 KL 上升（如 Qwen2.5-7B 从 0.4843 升至 0.5024），说明 prompt 级注入仍是必要组件，并非完全“搬进”。第三，博文在“关键结果”表格中仅列出 Qwen2.5-7B 一个模型的局部数据，未像原文那样呈现四个模型、四个类别的完整结果（原文表 1），虽然可接受为简化，但遗漏了不同模型表现差异的讨论（如 PSII 在 Mistral-24B 上 ED 仍为 0.0774 而非“几乎完美”）。
总评：⭐⭐⭐½ 博文抓住了论文的核心洞察与主要结果，但遗漏了 Value Vectors 这一关键组件，并对 prompt 级与 representation 级的双轨设计表述有偏差，导致技术完整性和准确性略有折扣。