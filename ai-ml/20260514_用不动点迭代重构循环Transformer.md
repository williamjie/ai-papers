# 用不动点迭代重构循环Transformer

**日期**: 2026-05-14

---

论文 : Solve the Loop: Attractor Models for Language and Reasoning链接 : https://arxiv.org/abs/2605.12466如果你受够了循环神经网络（RNN）类架构在训练时的显存爆炸和梯度不稳定，这篇来自南加州大学的论文值得你停下来看看。它没有发明新的Transformer层，而是换了一种“解方程”的思路来处理迭代细化（Iterative Refinement），在语言建模和硬核推理两个极端场景下都打出了漂亮的帕累托改进（Pareto Improvement）。
## 痛点：循环架构的“原罪”
Loops（循环）或 Recurrence（递归）在理论上能赋予模型“思考”的能力，比如 Chain-of-Thought。但在工程落地时，它有三个致命伤：
- 显存线性增长：传统的 Looped Transformer 需要 Unroll（展开）固定步数，反向传播时需存储每一步的激活值，显存随步数线性膨胀，大模型直接 OOM。
- 训练不稳定：权重共享的循环结构容易发散，需要复杂的稳定化技巧。
- 推理与训练错位：训练时循环 TT 步，推理时多跑几步或少跑几步，性能就会剧烈波动。
## 核心 Insight：把“循环”变成“解方程”
Attractor Models 的核心直觉非常优雅： 既然循环最终会收敛到一个不动点（Fixed Point），为什么非要一步步跑完？直接解方程求根不就行了吗？
传统的隐式深度模型（如 DEQ）虽然也用不动点，但通常从随机噪声或零初始化开始迭代，这在语义空间里是无效的。Attractor 做了一个关键改进： 两阶段设计 。
- Backbone（主干）：一个标准的非循环 Transformer，负责根据输入生成一个“初始猜测”输出嵌入 y0y_0​。这个 y0y_0​ 已经包含了丰富的语义信息，是高质量的起点。
- Attractor（吸引子模块）：一个较小的循环网络，接收 y0y_0​ 作为条件，通过迭代 yt+1=Ta(yt,y0)y_{t+1} = T_a(y_t, y_0)​=Ta​(yt​,y0​) 来微调 y0y_0​，直到满足收敛条件 ∥yt+1−yt∥<ϵ\|y_{t+1} - y_t\| < \epsilon​−yt​∥<ϵ。
### 关键技术：隐式微分（Implicit Differentiation）
这是让显存解放的关键。在反向传播时，Attractor 不通过存储每一步的中间状态来计算梯度，而是利用 隐函数定理 ：
∂L∂θ=u⊤∂Ta(y∗,y0)∂θ\frac{\partial L}{\partial \theta} = u^\top \frac{\partial T_a(y^*, y_0)}{\partial \theta} ∂ L ​ = u ⊤ ∂ θ ∂ T a ​ ( y ∗ , y 0 ​ ) ​其中 uu 是通过对线性方程组 (I−Jy∗⊤)u=v(I - J_{y^*}^\top)u = v J y ∗ ⊤ ​ ) u = v 求解得到的伴随向量（Adjoint Vector）。
这意味着，无论求解器迭代了多少次（10次还是1000次）， 训练时的显存占用是常数级的 O(1) ，只与模型参数量有关。这彻底解决了循环架构的显存瓶颈。
## 关键结果：小模型也能打败大模型论文在两个截然不同的场景下验证了该方法的有效性：
### 1. 大规模语言建模（Language Modeling）
在 FineWeb-Edu 数据集上预训练，对比参数匹配的 Transformer 和现有 Looped 模型 Parcae：
模型规模 指标 Transformer Parcae Attractor (Ours) 相对 Transformer 提升 140M Lambada PPL ↓ 127.39 80.64 68.02 -46.6% 370M Lambada PPL ↓ 40.77 32.74 27.14 -33.4% 770M Lambada PPL ↓ 22.37 19.71 15.21 -32.0% 770M Core Accuracy ↑ 14.59 20.00 20.24 +15.9%- 帕累托优势：770M 的 Attractor 模型性能超过了 1.3B 的 Transformer（后者训练数据量是前者的两倍）。
- 训练效率：由于隐式微分和自适应收敛步数，Attractor 的训练 FLOPs 比 Parcae 低 25-31%，且峰值显存不随最大迭代步数增加。
### 2. 小规模硬核推理（Hard Reasoning）
在仅需 ~1000 个训练样本的极端小数据场景下，测试 Sudoku-Extreme 和 Maze-Hard 任务：
- 27M 参数的 Attractor 模型：
Sudoku-Extreme 准确率：91.4%- Maze-Hard 准确率：93.1%- 对比基线：
标准 Transformer：0%- 前沿模型（Claude, GPT o3-mini, DeepSeek R1）：0%- 专用递归模型（TRM）：低于 Attractor，且随规模扩大性能崩溃这证明了 Attractor 架构在处理需要多步逻辑推演的任务时，比单纯的自回归生成或浅层循环更鲁棒。
## 意外发现：平衡内部化（Equilibrium Internalization）
论文发现了一个有趣的现象：随着训练进行，Backbone 生成的初始猜测 y0y_0 ​ 会越来越接近最终的不动点 y∗y^* 。
这意味着模型实际上在“自我蒸馏”。Attractor 模块像一个移动的目标，迫使 Backbone 提前计算出更准确的结果。最终，在推理时，Attractor 模块需要的迭代步数极少，甚至可以被移除而几乎不损失精度。这解释了为什么 Attractor 在推理时既快又准。
## 工程启示- 显存友好：如果你想在本地部署具有“反思”或“自我修正”能力的模型，Attractor 架构比展开的 Recurrent Transformer 更适合，因为它不需要为每一步预留显存。
- 自适应计算：推理时的迭代次数由残差阈值 ϵ\epsilon 决定，简单样本几步收敛，复杂样本多跑几步，天然适合动态计算预算（Dynamic Compute Budget）。
- 小模型利器：在数据稀缺的垂直领域（如特定逻辑推理），Attractor 的小规模表现优于大模型，适合边缘设备或低成本微调场景。
## 局限与展望- 求解器依赖：虽然用了 Anderson Acceleration 加速收敛，但在某些病态问题上，RootFind 可能仍面临收敛困难。
- 实现复杂度：隐式微分的反向传播实现比标准 Transformer 复杂，需要小心处理数值稳定性（如谱半径约束）。
总的来说，Attractor Models 提供了一种将“迭代思考”稳定化、高效化的新范式。它没有改变 Transformer 的原子操作，但改变了我们利用循环的方式——从“一步步走”变成了“直接走到终点”。
