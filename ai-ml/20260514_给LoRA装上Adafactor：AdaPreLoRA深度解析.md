# 给LoRA装上Adafactor：AdaPreLoRA深度解析

**日期**: 2026-05-14

---

论文 : AdaPreLoRA: Adafactor Preconditioned Low-Rank Adaptation链接 : https://arxiv.org/abs/2605.08734做大规模模型微调（Parameter-Efficient Fine-Tuning, PEFT）的工程师都知道，LoRA 虽然省内存，但优化过程往往比全量微调更“玄学”。这篇来自香港科技大学的论文直击痛点： LoRA 的参数分解导致优化空间奇异，现有的自适应优化器要么丢弃梯度统计信息，要么内存爆炸。
AdaPreLoRA 的核心贡献在于，它在不增加额外内存开销的前提下，巧妙地将 Adafactor 的预条件器（Preconditioner）引入到 LoRA 的因子空间中，并给出了一个闭式解。
## 为什么现有的 LoRA 优化器不够好？
要理解 AdaPreLoRA，得先搞懂 LoRA 优化中的一个根本障碍： 雅可比矩阵（Jacobian）的秩亏损（Rank-deficient） 。
LoRA 将权重更新分解为 W=BAW = BA B A ，其中 B∈Rm×r,A∈Rr×nB \in \mathbb{R}^{m \times r}, A \in \mathbb{R}^{r \times n} R m × r , A ∈ R r × n 。这种分解存在冗余：对任意可逆矩阵 CC ， (BC)(C−1A)(BC)(C^{-1}A) A ) 产生的权重更新是一样的。这意味着生成映射的雅可比矩阵 JGJ_G ​ 是奇异（不可逆）的。
当我们想在 WW 空间使用像 Adam 或 Adafactor 这样的自适应预条件器 FtF_t ​ 时，根据链式法则，因子空间的预条件算子形式为 JG∗FtJGJ_G^* F_t J_G ∗ ​ F t ​ J G ​ 。因为 JGJ_G ​ 奇异，这个算子也是奇异的。
这就导致了两个问题：
- 不可逆：标准链式法则无法唯一地映射回因子空间的更新方向。
- 不唯一：如果使用伪逆（Pseudoinverse），解空间是一个 r2r^2 维的仿射子空间，不同的选择对应不同的因子轨迹。
现有的方案大致分两类：
- 廉价因子空间方案（如 Vanilla LoRA, LoRA+）：直接忽略 WW 空间的梯度统计，或者用块对角近似，效果受限。
- 全权重预条件方案（如 LoRA-Pro AdamW, SOAP）：在 WW 空间使用复杂的预条件器（如 Shampoo），但需要维护 O(mn)O(mn) 的内存，这在 7B 模型上根本跑不动。
AdaPreLoRA 的目标很明确： 既要 WW 空间的梯度统计信息，又要保持 O((m+n)r)O((m+n)r) n ) r ) 的 LoRA 级内存。
## 方法拆解：Adafactor + 平衡准则AdaPreLoRA 的设计非常优雅，它解决了上述框架中的两个选择：
### 1. 选择 FtF_t​：Adafactor 对角 Kronecker 预条件器作者选择了 Adafactor 作为 WW 空间的预条件器。Adafactor 通过维护行和列的二阶矩（ lt,rtl_t, r_t ​ , r t ​ ），以 O(m+n)O(m+n) n ) 的极小内存实现了接近 Shampoo 的效果。
定义 Ht=Lt⊗RtH_t = L_t \otimes R_t ​ = L t ​ ⊗ R t ​ 为 Adafactor 的平方根算子，作用于矩阵 YY 为 LtYRtL_t Y R_t ​ Y R t ​ 。这个算子定义了一个加权内积空间。
### 2. 选择解：HtH_t​-平衡准则既然解空间不唯一，怎么选？AdaPreLoRA 提出一个直观的物理直觉： 平衡两个因子对更新的贡献 。
在解空间中，更新方向可以写为 ΔBtAt+BtΔAt\Delta B_t A_t + B_t \Delta A_t ​ A t ​ + B t ​ Δ A t ​ 。作者最小化 HtH_t ​ -范数下的不平衡项：
∥ΔBtAt−BtΔAt∥Ht2\|\Delta B_t A_t - B_t \Delta A_t\|_{H_t}^2 ​ A t ​ − B t ​ Δ A t ​ ∥ H t ​ 2 ​这个准则类似于非凸低秩矩阵恢复中的平衡正则化。通过最小化这个不平衡，作者推导出了一个 闭式解（Closed-form） 。
核心 Insight ：AdaPreLoRA 的因子更新 Δopt\Delta_{opt} ​ 是 Ht−1GtH_t^{-1} G_t − 1 ​ G t ​ 在 LoRA 可表达子空间 TtT_t ​ 上的 HtH_t ​ -正交投影。这意味着，它在 LoRA 的约束下，找到了最接近预条件后 WW 空间最优更新方向的那个解。
## 关键结果：7B 模型上的性价比之王论文在 GPT-2、Mistral-7B、Qwen2-7B 以及扩散模型上进行了广泛测试。以下是几个关键数据点：
### GPT-2 生成任务 (E2E, r=4)
在 GPT-2 Medium 上，AdaPreLoRA AdamW 取得了 BLEU 70.3 的成绩，优于 Scaled AdamW (69.6) 和 LoRA-Pro AdamW (69.8)。在 SGD 变体中，优势更明显，BLEU 达到 70.3，而 Vanilla LoRA 仅为 66.6。
### Mistral-7B & Qwen2-7B 微调 (r=8)
这是最体现工程价值的部分。Table 4 显示：
- Mistral-7B (RTE): AdaPreLoRA (89.5) vs Scaled AdamW (89.1)。
- Qwen2-7B (GSM8K): AdaPreLoRA (76.4) vs Scaled AdamW (74.2)。
- Qwen2-7B (ARC): AdaPreLoRA (85.6) vs Scaled AdamW (85.3)。
值得注意的是，那些需要 O(mn)O(mn) 内存的基线（LoRA-Pro AdamW, SOAP）在 7B 模型上不仅没赢，反而因为优化困难或过拟合，在某些任务上表现甚至不如基础的 AdamW。
### 内存与速度 (Mistral-7B)
Table 5 揭示了真正的杀手锏：
- LoRA-Pro AdamW: Peak Memory 50.4 GB (约 2x 开销)。
- AdaPreLoRA AdamW: Peak Memory 26.0 GB (与 Scaled AdamW 持平，接近 Vanilla LoRA)。
- AdaPreLoRA SGD: Peak Memory 21.5 GB (最低)。
AdaPreLoRA 用极低的内存代价，换来了比廉价优化器更好的收敛性和比昂贵优化器更低的内存占用。
## 工程启示- 不要忽视梯度统计：在 LoRA 中，简单的 AdamW 或 SGD 往往不是最优解。引入像 Adafactor 这样的轻量级二阶统计信息，能显著提升收敛质量，尤其是在低秩（small r）场景下。
- 7B 模型的内存墙：对于 7B 及以上模型，任何需要存储全量权重梯度或二阶矩的方法（如 LoRA-Pro, Shampoo-on-W）都难以落地。AdaPreLoRA 证明了 O((m+n)r)O((m+n)r)n)r) 内存下也能实现先进的预条件优化。
- 扩散模型同样受益：在 Mix-of-Show 实验中，AdaPreLoRA 在 CLIP Score 和 FID 上均达到最佳或次佳，说明该方法具有跨模态的通用性。
## 局限与展望论文也坦诚了方法的边界：
- 单一 HtH_t​ 假设：当前方法假设一个 HtH_t​ 概括每一步的梯度统计。对于 DiT 等复杂架构，可能需要更细致的处理。
- 量化兼容性：虽然提到了 QLoRA，但量化后的权重重构和预条件器统计的结合仍需进一步研究。
总的来说，AdaPreLoRA 是一篇理论扎实且工程价值极高的论文。它没有发明新的花哨结构，而是通过严谨的数学推导，在 LoRA 固有的数学缺陷中找到了最优解路径。对于正在纠结“LoRA 优化器选哪个”的工程师来说，AdaPreLoRA 是一个值得优先尝试的 SOTA 方案。
