# MedConclusion：LLM 写结论，不是做摘要

**日期**: 2026-04-21

---

论文 : MedConclusion: A Benchmark for Biomedical Conclusion Generation from Structured Abstracts链接 : https://arxiv.org/abs/2604.06505最近哈佛医学院那帮人发了篇很有意思的论文。他们搞了个 570 万条 PubMed 结构化摘要的大数据集，就为了回答一个看似简单、实则棘手的问题： LLM 能不能从 Background、Methods、Results 推导出 Conclusion？
听起来不就是摘要吗？错了。这篇论文的核心发现恰恰是： 结论生成和摘要生成在行为上是截然不同的两件事。
## 为什么这篇论文值得关注？
现在做 Scientific AI 的越来越多，但绝大多数工作集中在”检索+总结”或者”问答”上。真正聚焦于**证据到结论推理（Evidence-to-Conclusion Reasoning）**的数据集几乎没有。
现有的结论生成数据集要么规模小（几万条），要么局限于特定研究类型（比如只覆盖随机对照试验），要么根本没标注期刊级别元数据，导致你根本无法分析不同领域、不同期刊难度的差异。
MedConclusion 的切入点很聪明—— 利用 PubMed 天然的结构化摘要做监督信号 。每篇论文的作者写好的 Conclusion 就是 Gold Label，输入是去掉 Conclusion 的其他部分。这比人工标注便宜得多，也自然得多。
## 方法拆解：数据集是怎么来的？
数据收集流程其实很朴素，但胜在规模够大：
- 用 Entrez Direct (EDirect) 从 PubMed 拉取 2000-2025 年间所有带结构化摘要的文章- 解析 XML，按 (label, nlm category, text) 元组提取结构化段落- 按 PMID、DOI、标准化标题去重- 过滤规则：英文、核心字段非空、至少 3 个摘要段落、至少 1 个 Conclusion 段- 最终保留 5,692,839 条记录，覆盖 3,772 本期刊、141 个学科分类每个样本还附带了 SCImago Journal Rank (SJR) 分数，这意味着你可以按期刊影响力分层分析——这在之前的工作中几乎没人做过。
## 核心实验设计：4 种 Prompt 模式论文评估了 4 种提示方式，这才是有趣的地方：
模式 任务 格式约束 A 写 Conclusion 无 B 写 Summary 无 C 写 Conclusion 有字数/句数限制 + 风格匹配 D 写 Summary 有字数/句数限制 + 风格匹配关键洞察：A vs B 的对比直接验证了”结论≠摘要”这个假设。
如果用 LLM-as-a-Judge 评估（从语义相似度、风格相似度、非矛盾率、数值一致性、正式度 5 个维度打分），结果很有意思：
### 结论 vs 摘要：行为差异显著以 GPT-5.4 为例（GPT-5.4-mini 作为 Judge）：
指标 A(结论, 无约束) B(摘要, 无约束) 差距 语义相似度 71.20 62.60 -8.60 风格相似度 84.61 83.96 -0.65 非矛盾率 88.24 83.96 -4.28 数值一致性 89.80 66.24 -23.56 正式度 73.22 72.11 -1.11B 模式（写摘要）在数值一致性上崩了整整 23.56 分。这意味着摘要模式下，模型会选择和原文 Conclusion 不同的数字、不同的细节粒度、不同的限定范围 ——虽然它可能仍然忠实于 Abstract 的其他部分，但它不再”像”Conclusion。
更有趣的是 C 模式： 加了格式约束后，数值一致性从 89.80 提升到 91.36 ，说明给模型明确的长度和风格指令，能帮助它更好地匹配原文 Conclusion 的数值选择性。这给工程实践一个直接信号—— 在 Conclusion 生成任务上，约束式 Prompt 比自由生成更好。
### 模型对比：头部模型差距极小再看模型层面的表现（Judge: GPT-5.4-mini，模式 A）：
模型 语义相似度 数值一致性 非矛盾率 GPT-5.4 71.20 89.80 88.24 Gemini 3.1 Pro 70.13 89.49 86.92 Gemini 3 Flash 69.87 89.17 86.45 DeepSeek-V3.2 68.21 88.59 86.22 Gemma-3-27B 69.18 89.36 84.13 Llama-3.1-8B 66.69 88.03 79.82 Qwen2.5-7B 65.74 86.60 77.31 Llama-3.2-1B 50.69 78.35 82.69GPT-5.4 确实最强，但 Gemini 3.1 Pro、Gemini 3 Flash、DeepSeek-V3.2、Gemma-3-27B 都只在几分的差距内。论文原话是： “strong models remain closely clustered under current automatic metrics” ——当前自动指标很难拉开强模型之间的差距。
### ROUGE vs LLM Judge：指标之间的分裂更值得警惕的是规则指标和 Judge 指标之间的 不一致 ：
指标 DeepSeek-V3.2 GPT-5.4 Gemma-2-9B ROUGE-1 0.35 0.34 0.32 ROUGE-2 0.11 0.10 0.10 ROUGE-L 0.23 0.21 0.20 BLEU 0.05 0.04 0.04 嵌入相似度 0.76 0.77 0.78 语义相似度(Judge) 68.21 71.20 69.18DeepSeek-V3.2 在 ROUGE 和 BLEU 上全面领先，但在 Judge 的语义相似度上反而落后 GPT-5.4 近 3 分。Gemma-2-9B 嵌入相似度最高（0.78），但 Judge 给的分数不如 GPT-5.4。
这说明什么？ ROUGE/BLEU 和 LLM-Judge 捕捉的是不同维度的质量 。 lexical overlap 高的输出不一定在语义或事实一致性上更好。论文强烈建议用 混合评估协议 ，单一指标会掩盖真正的质量差异。
## Judge 敏感性：换个 Judge，分数大变同样的模型输出，用 GPT-5.4-mini 和 Gemini 3 Flash 当 Judge，绝对分数差异巨大：
生成模型 指标 GPT-5.4-mini Judge Gemini 3 Flash Judge GPT-5.4 语义相似度 71.20 71.49 GPT-5.4 风格相似度 84.61 97.51 GPT-5.4 数值一致性 89.80 98.18 Gemini 3 Flash 语义相似度 69.87 70.04 Gemini 3 Flash 风格相似度 81.76 96.62 Gemini 3 Flash 数值一致性 89.17 97.28风格相似度和数值一致性的绝对分数被 Gemini 3 Flash 拉高了 10-15 分。 Ranking 相对稳定 （GPT-5.4 依然是第一），但绝对分数不可跨 Judge 比较。这对做 benchmark 的人是个提醒：Judge 的选择会显著影响结论的”绝对”解读。
## 学科难度差异按期刊 SJR 分数分析，高影响力期刊的 Conclusion 在 ROUGE 和语义相似度上略高（r=+0.068~0.104），但 非矛盾率和数值一致性没有显著趋势 。期刊影响力对结论生成难度有影响，但不大。
按学科分类， Software、Computer Science Applications、Applied Microbiology and Biotechnology 在所有指标上都是最差的——跨学科、非临床领域的结论生成明显更难。有趣的是，Gerontology 在 ROUGE-L 上排前 5，但在 Judge 的风格和数值一致性上却很差——再次印证了 ROUGE 的不可靠性。
## 工程启示- 不要混用结论和摘要的 Prompt。如果你在构建科研 Agent，写 Conclusion 和写 Summary 应该走不同的流水线，用不同的 prompt 模板。
- 约束式 Prompt 对数值一致性有帮助。在 A/C 对比中，加格式约束让数值一致性提升了 ~1.5 分（GPT-5.4 从 89.80 到 91.36），在要求精确的医疗场景下这很关键。
- 别太信任 ROUGE/BLEU。它们和 Judge 评分的相关性远不如你想象的那么高。做评估时至少加一个语义/事实维度的 Judge。
- 头部模型差距比你以为的小。GPT-5.4 强，但 Gemini 3.1 Pro、DeepSeek-V3.2、Gemma-3-27B 差距不大。如果你的场景不需要极致质量，开源模型完全可用。
- Judge 选好后别换来换去。绝对分数没有可比性，跨论文比较 Benchmark 结果时要特别注意 Judge 的一致性。
## 局限与展望论文本身也坦诚了一些边界：
- 只评估了 30K 随机子集（成本约束），570 万数据的大规模微调还没做- Judge 虽然多维，但本质还是 LLM 主观判断，没有人工标注的黄金标准- 只覆盖了 PubMed 的结构化摘要，非结构化摘要或全文结论生成是下一步- 结论生成中”不引入新主张”的约束是否合理，在开放科学场景下有争议总的来说，MedConclusion 最大的价值不是某个模型刷了多少分，而是它 系统地揭示了结论生成和摘要生成的行为差异，以及当前评估指标的局限性 。对做 Scientific AI 的工程师来说，这是一个值得反复参考的基准。
