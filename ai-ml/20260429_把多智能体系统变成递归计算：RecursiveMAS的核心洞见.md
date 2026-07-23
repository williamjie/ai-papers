# 把多智能体系统变成递归计算：RecursiveMAS 的核心洞见

**日期**: 2026-04-29

---

论文 : Recursive Multi-Agent Systems链接 : https://arxiv.org/abs/2604.25917这篇论文提出了一个非常规的思路： 不要试图让每个智能体变得更聪明，而是让整个系统的交互过程本身变得更聪明 。
现有的多智能体系统（MAS）有个根本矛盾：智能体之间通过文本来回对话，信息密度低、计算开销大，而且梯度在文本传递中会消失。RecursiveMAS 的解法是——把整个 MAS 变成一个大号的递归语言模型（RLM），所有智能体在潜在空间里循环传递”思维”，只在最后一轮输出文本。
## 问题：文本交互的代价标准的多智能体协作本质上是 文本管道 ：Agent A 生成一段话，Agent B 读这段话再生成新的话，如此反复。这种设计有三大硬伤：
- 每次跨智能体传递都要完整解码+重新编码：latent → token → token → latent，这个转换过程在公式里体现为 m∣V∣dhm|V|d_h​ 的复杂度（∣V∣|V| 是词表大小，通常 3 万以上）
- 梯度在文本离散空间中断：BP 传不过去，每个智能体只能靠自己的 SFT，无法 end-to-end 优化整个协作流程- token 爆炸：递归轮数 rr 一增加，中间文本累积，总 token 数线性增长Proposition 3.1 给出了严格的复杂度对比。Text-MAS 是 Θ(N(m∣V∣dh+(t+m)dh2+(t+m)2dh))\Theta(N(m|V|d_h + (t+m)d_h^2 + (t+m)^2d_h)) ​ + ( t + m ) d h 2 ​ + ( t + m ) 2 d h ​ )) ，而 RecursiveMAS 是 Θ(N(mdh2+(t+m)dh2+(t+m)2dh))\Theta(N(md_h^2 + (t+m)d_h^2 + (t+m)^2d_h)) 2 ​ + ( t + m ) d h 2 ​ + ( t + m ) 2 d h ​ )) 。 核心差别就是第一项从 m∣V∣dhm|V|d_h ​ 降到了 mdh2md_h^2 2 ​ 。由于 dh≪∣V∣d_h \ll |V| ​ ≪ ∣ V ∣ （4096 vs 32000），这就是 1.2–2.4× 加速的数学来源。
## 核心 insight：智能体 = RLM 的 layer递归语言模型（RLM）的思路是： 同一组 Transformer 层重复用 nn 次 ，而不是一次跑完。公式是 H(r)=fθ(H(r−1))H^{(r)} = f_\theta(H^{(r-1)}) = f θ ​ ( H ( r − 1 ) ) 。
RecursiveMAS 把这条思路从”层”扩展到了”智能体”： 每个智能体 AiA_i ​ 就是一个 RLM layer，整个 MAS 就是一个深层递归网络 。信息在潜在空间里循环流动，每轮都在加深系统的”思考”。
这样做有三大优势：
- 统一的计算图：整个系统可以 end-to-end BP，外循环直接通过梯度给所有智能体的 RecursiveLink 分配 credit- 信息无损传递：latent 是浮点向量，没有信息损失；文本有歧义、有压缩、有丢失- 计算密集在矩阵乘法：GPU 最擅长的就是矩阵乘法，mdh2md_h^22​ 完全 batched 友好## 关键技术：RecursiveLink这是整篇论文最轻量但最关键的组件。它解决两个问题：
- Dense-to-Shallow Transition：当前轮的 last-layer embedding 要变回下一轮的 input embedding（同一个智能体内）
- Cross-Model Transition：Agent A 的 latent 要给 Agent B 用（跨智能体，hidden_dim 可能不同）
对应的就是 Inner Link 和 Outer Link。
Inner Link 的公式是 Rin(h)=h+W2σ(W1h)R^{in}(h) = h + W_2 \sigma(W_1 h) ( h ) = h + W 2 ​ σ ( W 1 ​ h ) ，就一个带残差的两层 MLP。
为什么用残差？ 论文给出了清晰的设计直觉：残差分支保留了原始语义，让网络只需要学习分布对齐（distribution alignment），而不是从零学投影。这在实验部分的 6.1 节有验证——去掉残差会掉点。
Outer Link 多加了一个 W3W_3 ​ 用来 dimension mapping： Rout(h)=W3h+W2σ(W1h)R^{out}(h) = W_3 h + W_2 \sigma(W_1 h) ( h ) = W 3 ​ h + W 2 ​ σ ( W 1 ​ h ) 。这个 W3W_3 ​ 把一个智能体的潜在空间线性映射到另一个智能体的输入空间。
整个 RecursiveLink 只有几十万个参数（两层 MLP），而智能体本身是 1–10B 的大模型。 这就是”系统级优化不更新模型参数”的关键 ：只优化这些 link，就能让整个系统协同进化。
## 训练：内循环 + 外循环训练分两阶段，对应 Figure 4 的流程图。
内循环（Inner Loop） ：每个智能体单独 warm-start。目标是让智能体的 latent generation 更接近真实的 token embedding 分布。用余弦相似度 loss：
Lin=1−cos⁡(Rin(H),Embθi(y))\mathcal{L}_{in} = 1 - \cos(R^{in}(H), \text{Emb}_{\theta_i}(y)) ​ = 1 − cos ( R in ( H ) , Emb θ i ​ ​ ( y ))
HH 是智能体自己生成的 latent sequence， Emb(y)\text{Emb}(y) ( y ) 是真实答案的 embedding。这个 loss 鼓励智能体生成的”思维”在语义空间对齐答案， 相当于让每个智能体先在脑子里预演正确答案的 latent 长什么样 。
外循环（Outer Loop） ：把整个系统展开 nn 轮，BP 从最后一轮的文本输出往回传。关键公式：
Lout=CE(S(n)(S(n−1)(⋯S(1)(x))),y)\mathcal{L}_{out} = \text{CE}\left( S^{(n)}(S^{(n-1)}(\cdots S^{(1)}(x))), y \right) ​ = CE ( S ( n ) ( S ( n − 1 ) ( ⋯ S ( 1 ) ( x ))) , y )
梯度会沿着完整的递归路径传回去，每个 RecursiveLink 都拿到全局的 credit signal。这就是 系统级共同优化 。
Theorem 4.1 从学习动力学角度解释了为什么潜在空间 BP 更稳定。文本交互 Rtext(h)R^{text}(h) ( h ) 会让梯度范数接近 0（梯度消失），而 RecursiveLink R(h)R(h) 能保持接近 1 的稳定梯度。直观理解：文本是离散映射，每一步都有信息损失；latent 是连续可微的，梯度可以无损回传。
## 实验结果：性能与效率双赢基线设置 （Table 2 和 Table 3）：
- 对比了 Single Agent（LoRA 微调、全参数微调）、Mixture-of-Agents、TextGrad、LoopLM、Recursive-TextMAS- 数据集：MATH500、AIME2025/26、GPQA-Diamond、MedQA、LiveCodeBench、MBPP+ 等 9 个- 智能体配置：轻量版用 Qwen3-1.7B / Llama3.2-1B / Qwen2.5-Math-1.5B；扩展版用 Gemma3-4B / Qwen3.5-4B/9B核心数字 （来自 Table 2 和正文）：
指标 数值 准确率提升 平均 +8.3% (vs 最强基线) AIME2025 提升 +18.1% (86.7% vs 73.3%) AIME2026 提升 +13.0% (86.7% vs 76.7%) GPQA-Diamond 提升 +5.4% (66.2% vs 62.8%) 推理加速 1.2× → 2.4× (随递归轮数增加) Token 减少 34.6% → 75.6% (r=1→3)
递归轮数的影响 （Table 2，r=1/2/3）：
- Recursive-TextMAS 在 r=3 时完全崩盘：AIME2025 从 73.3% 降到 73.3%（没提升但 token 暴增），AIME2026 从 73.3% 降到 73.3%- RecursiveMAS 则持续提升：r=1 时 +3.4% avg，r=2 时 +6.0%，r=3 时 +7.2%跨架构泛化 （Figure 1 Down）：
- Mixture Style（多专家并行）：+6.2% 超过最强单专家- Distillation Style（大专家→小学徒）：小学徒 +8.0% 同时保持 1.5× 速度优势- Deliberation Style（工具调用+反思）：+4.8% 超过原始工具调用智能体效率趋势 （Figure 5 & 6）：
- 加速比和 token 节省都随递归轮数加深而增大，这说明潜在空间交互的收益是 compounding 的- Text-MAS 的 token 使用随 r 线性增长，而 RecursiveMAS 几乎 flat——因为中间轮次都待在 latent 空间## 工程启示：这方法能用在哪？
1. 本地部署的场景最受益RecursiveMAS 的加速来自于 绕过词汇表解码 。在本地跑 7B 模型时，解码是瓶颈（vocab size 大、采样慢），潜在空间循环能直接省掉 34.6–75.6% 的 token 生成。这意味着：
- 更低的推理延迟- 更少的内存带宽压力- 更长的上下文有效利用率2. 异构智能体编排的新范式Table 1 里混用了 Qwen/Llama/Gemma/Mistral，尺寸从 1B 到 9B。RecursiveLink 的 outer 层天然支持不同 hidden_dim 的映射（ W3W_3 ​ 的作用）。这意味着你可以：
- 把计算密集的环节（数学、代码）分给大模型- 把快速响应的环节（检索、反思）分给小模型- 通过 RecursiveLink 把它们缝合成一个循环系统，end-to-end 优化3. 不更新原模型的低成本微调整个系统只训练数十万个参数的 RecursiveLink，原始 LLM 完全 frozen。这带来：
- 训练成本极低（只需要 forward 存梯度，无需 optim step 在大模型上）
- 可以快速适配不同基座模型（只需要重新训练 RecursiveLink）
- 规避了多智能体系统常见的灾难性遗忘问题4. Scaling Law 的系统级版本Figure 1 (Up) 显示了 训练递归轮数 和 推理递归轮数 的联合 scaling：训练时更深的递归让系统学会”生成更容易精化的 latent state”，推理时更深的递归把这些 latent state 进化到更好。 两者互补，右下角最优 。
这暗示一个系统工程准则： 递归是一种比参数量更高效的”深度”扩展方式 ——通过重复使用现有计算，在相同 FLOPs 预算下获得更深的”思考”。
## 局限与边界论文在附录提到了几个边界条件：
- 最后一轮仍需文本解码：只有 Agent N 在最终轮输出文本，所以文本生成的开销没完全消除（但只在末端一次）
- 递归深度受梯度稳定性制约：虽然 Theorem 4.1 证明了稳定性，但实践中 r>4 会开始出现收敛困难（Figure 1 只画到了 r=3）
- 依赖高质量的初始智能体：RecursiveLink 只做 alignment，不创造能力。如果所有参与智能体都弱，系统还是弱- 训练需要多样化数据：内循环+外循环都需要跨域训练集（s1K、m1k、OpenCodeReasoning 等），不然泛化不佳## 总结RecursiveMAS 真正的价值不是”多智能体”，而是 把系统级交互变成了可微分的深度网络 。传统 MAS 是 pipeline，每个环节各自为政；RecursiveMAS 是 end-to-end 可优化的递归计算图。
核心洞见一句话 ：智能体之间的”对话”不应该用文本，而应该用潜在空间里的向量——这样整个对话过程可以被视为一个深层网络，用梯度 collectively 优化。
对工程师的直接启发是： 当你的 multi-agent workflow 已经搭建好但效果卡住时，与其换更强的模型，不如尝试把它改造成潜在空间递归 。只需要加几层 MLP（RecursiveLink），就能让整个系统获得梯度信号，end-to-end 提升 8% 以上，同时速度更快、token 更少。
这不是小修小补，这是架构层面的范式转换。
