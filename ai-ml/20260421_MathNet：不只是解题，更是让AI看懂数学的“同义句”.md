# MathNet：不只是解题，更是让 AI 看懂数学的“同义句”

**日期**: 2026-04-21

---

论文 : MathNet: a Global Multimodal Benchmark for Mathematical Reasoning and Retrieval链接 : https://arxiv.org/abs/2604.18584我们常说大模型“会做题”了，但如果你问它：“这题跟上面那道题是一回事吗？”它大概率会愣住。
ICLR 2026 接收的 MathNet 论文戳穿了这一现状：生成式模型（LLM/LMM）在解题上已经很强，但在**数学感知检索（Math-Aware Retrieval）**上几乎还是婴儿水平。这篇论文不仅扔出了目前最大的高质量奥赛数据集，更设计了一套让人后背发凉的评测体系，直接暴露了当前 Embedding 模型的致命缺陷。
## 为什么我们需要 MathNet？
现有的数学基准（如 MATH、GSM8K、Omni-MATH 等）主要关注一件事： 给道题，算出答案 。
但现实工程中有两个痛点这些基准没覆盖：
- 数据偏见严重：现有数据集多来自 AoPS 等社区平台，语言覆盖窄（基本只有英语和中文），且质量参差不齐。
- 检索盲区：在 RAG 场景中，我们需要模型找到“结构相似”的例题，而不是“字面相似”的废话。
MathNet 的动机很明确：如果 AI 连 x2+y2=1x^2 + y^2 = 1 + y 2 = 1 和 a2+b2=1a^2 + b^2 = 1 + b 2 = 1 视为同一道题都做不到，那它的 RAG 系统就是在瞎搞。
## 方法拆解：不仅仅是数据量大MathNet 的核心贡献不在于“量大”，而在于 数据质量 和 任务设计的细腻度 。
### 1. 数据收集：官方源头 + 专家级清洗MathNet-Solve 包含 30,676 道奥林匹克级别数学题。
- 来源：47 个国家、17 种语言、143 项竞赛、跨度 40 年（1985-2025）。注意，全是官方出版的试题册，而非社区搬运。
- 清洗管线：使用 DotsOCR 进行多语言文档解析，再通过 LLM（Gemini-2.5-Flash + GPT-4.1）进行问题-答案的对齐提取。
- 三重验证：规则检查 -> GPT-4.1 图像对比 -> 人工复核。只有三者一致才保留。这保证了每一道题的解法都是专家级质量。
### 2. 数学相似性分类学：Invariance, Resonance, Affinity这是论文最精彩的理论设计。它定义了三种数学相似性：
- 不变性（Invariance）：严格等价。例如变量重命名 x→ax \to aa，或代数变形。
- 共鸣（Resonance）：部分相似。解法策略相同，但题目不同。例如都用到同一个引理。
- 亲和力（Affinity）：主题相关。同属数论或几何，但解法无关。
现有的检索模型通常连第一层（Invariance）都做不到，因为它会被表面词汇误导。
### 3. 三大评测任务- Problem Solving：直接解题。使用 GPT-5 作为 Judge，0-7 分打分，≥6\ge 66 算对。
- Math-Aware Retrieval：检索等价题。构建 MathNet-Retrieve，从 10,000 道锚点题生成 1 个等价正例 + 3 个困难负例（Hard Negatives），共 40,000 对。
- Math RAG：检索增强解题。构建 MathNet-RAG，35 对专家精选的“共鸣”级题目对，评测 RAG 效果。
## 关键结果：检索性能令人尴尬实验评估了 27 个模型，结果揭示了三个残酷事实。
### 1. 解题能力：前沿模型已具“金牌”水准，但几何是硬伤在 MathNet-Solve-Test 上，推理模型表现最好：
模型 代数 (Algebra) 数论 (Num. Theory) 几何 (Geometry) 离散数学 (Discrete) 宏观平均 Gemini-3.1-Pro 83.7% 82.2% 74.6% 75.6% 78.4% Gemini-2.5-Pro 77.7% 73.3% 67.0% 64.0% 70.4% GPT-5 80.3% 73.6% 61.1% 65.3% 69.3% Claude-Opus-4.6 50.5% 42.6% 36.8% 31.0% 41.1%数据源自 Table 3解读 ：
- Gemini-3.1-Pro 以 78.4% 的宏观平均分领先。
- 几何和离散数学是所有人的噩梦。即使是 GPT-5，在几何上也只有 61.1%，比代数低了近 20 个百分点。
- 推理模型（Reasoning Models）大幅领先非推理模型，Claude-Opus-4.6 在没有明确推理提示下表现平平。
### 2. 检索能力：Embedding 模型几乎“瞎搞”
这才是重头戏。在 MathNet-Retrieve 上，评测 Embedding 模型能否找到数学等价题：
模型 Recall@1 (全局) Recall@5 (全局) Recall@10 (全局) Qwen3-embedding-4B 4.96% 64.95% - Gemini-embedding-001 4.83% 68.88% 83.79% text-embedding-ada-002 1.94% 42.02% - text-embedding-3-small 1.98% 35.49% -数据源自 Table 4解读 ：
- Recall@1 极低：最强的 Embedding 模型 Top-1 召回率仅 ~5%。这意味着 95% 的情况下，模型返回的“最相似”题目并不是数学等价题。
- Lexical Overlap 陷阱：论文 Figure 6 显示，非等价题对的余弦相似度往往高于等价题对。模型被关键词（如“triangle”、“polynomial”）误导，而不是理解数学结构。
- 老派模型（Ada-002, Embed-3-small）表现更差，Recall@5 甚至低于 40%。
### 3. RAG 效果：检索质量决定成败在 MathNet-RAG 上，对比 Zero-Shot、Embed-RAG（用 Embedding 检索）和 Expert-RAG（用专家配对题）：
模型 Zero-Shot Embed-RAG Expert-RAG DeepSeek-V3.2-Speciale 84.8% 89.5% 97.3% GPT-5 76.8% 75.2% 86.6% Gemini-3-Pro 89.1% 92.9% 87.5%数据源自 Table 5 (Human Grading)
解读 ：
- 检索质量至关重要：DeepSeek-V3.2-Speciale 在 Expert-RAG 下达到 97.3%，但在 Embed-RAG 下只有 89.5%。这说明 Embedding 检索经常引入“噪声”，反而干扰解题。
- 模型依赖性：Gemini-3-Pro 在 Embed-RAG 下表现不错（92.9%），但在 Expert-RAG 下反而下降（87.5%），说明它自身能力强，不需要外部帮助，甚至可能被误导。
- GPT-5 从 Zero-Shot 的 76.8% 提升到 Expert-RAG 的 86.6%，证明了高质量检索的增益潜力。
## 工程启示- 不要信任通用 Embedding 做数学检索：如果你在做数学 RAG 系统，直接用 text-embedding-ada-002 或类似模型，大概率是找错题。需要专门针对数学结构训练的 Embedding，或者引入公式解析（LaTeX）作为特征。
- RAG 不是银弹：Bad retrieval hurts. 如果检索回来的例题结构与目标题不匹配（Hard Negatives 陷阱），RAG 可能比 Zero-Shot 更差。在构建数学 RAG 时，必须引入结构相似度校验，而不仅仅是语义相似度。
- 几何是短板：如果应用涉及几何推理，当前 SOTA 模型（包括 GPT-5 和 Gemini-3.1）仍有巨大提升空间。多模态输入（图像+文本）有帮助，但不足以弥补根本性的推理缺陷。
- 数据质量 > 数据数量：MathNet 的 3 万题之所以有价值，是因为它有专家级解法和严格的来源。在构建垂直领域基准时，清洗和验证流程比盲目爬取更重要。
## 局限与展望论文也承认了局限：
- 检索基准的合成性：MathNet-Retrieve 的正负例部分由 GPT-5 生成，虽然经过人工校验，但仍可能引入生成偏差。
- RAG 规模小：MathNet-RAG 仅 35 对题目，主要用于定性分析，统计显著性有限。
- 符号推理架构缺失：当前基于 Next-Token Prediction 的架构在数学结构理解上存在根本瓶颈，未来可能需要结合符号推理（Symbolic Reasoning）的新架构。
总之，MathNet 告诉我们：AI 能解奥数题了，但它还没真正“理解”数学。在检索和结构对齐上，我们还有很长的路要走。
