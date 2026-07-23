# 别瞎判了：让 Agent 自己去验证 Agent

**日期**: 2026-04-22

---

论文 : AJ-Bench: Benchmarking Benchmarking Agent-as-a-Judge for Environment-Aware Evaluation链接 : https://arxiv.org/abs/2604.18240RL 训练 Agent 越来越火，但一个尴尬的问题悬而未决： 怎么判断 Agent 做对了？
以前我们要么写死规则（rule-based verifier），要么让 LLM 当裁判（LLM-as-a-Judge）。规则写不完的，LLM 则纯靠”看文本猜结果”——两者在复杂环境里都容易翻车。
中科大和美团联合推出的 AJ-Bench 提出了一个朴素但有力的思路： 让裁判自己也变成一个 Agent，去环境里动手验证。
## 痛点：LLM 当裁判，本质是”盲人摸象”
LLM-as-a-Judge 的问题很直观。它只能看到 Agent 输出的文本轨迹，没法确认环境里的真实状态。
论文举了个例子：Agent 说”某技术报告的发布日期是 2025-08-09”。LLM 裁判说”我不确定，没法验证”。而 Agent-as-a-Judge 会直接去搜一下，发现实际发布日期是 2025-09-19，于是判定 Agent 答错了。
核心洞察 ：判断一个 Agent 对不对，最好的方式不是读它的报告，而是自己去执行一遍、去查一遍、去看最终状态。
## 方法拆解：三维评估体系AJ-Bench 不是随便找几个任务凑数，而是从三个维度来评估裁判 Agent 的能力：
维度 做什么 怎么验证 信息获取 (Information Acquisition) 裁判自己上网搜答案 通过搜索工具获取外部信息 状态验证 (State Verification) 检查环境最终状态对不对 回放 Agent 操作后的环境快照 过程验证 (Process Verification) 检查关键步骤有没有做对 检查中间动作和执行情况这三个维度覆盖了 Agent 行为评估的主要场景。
### 任务覆盖：三个领域，155 个任务，516 条轨迹AJ-Bench 选了三个差异化的领域：
- 搜索 (Search)：从 Mind2Web2 和 WideSearch 挑选，涵盖深度搜索（多跳推理）和广度搜索（宽泛信息收集）。剔除了电商、旅游等时效性太强、URL/价格变化快的任务。
- 数据系统 (Data Systems, DS)：基于 MCPMark 的 Filesystem 和 Postgres 子集，通过检查文件结构和数据库记录来直接验证状态。
- 图形界面 (GUI)：基于 OSWorld 的 Office 三件套（PPT、Word、Excel），要求精确执行位置和动作序列，当前 Agent 在这块仍然很吃力。
数据构成如下：
领域 子领域 任务数 轨迹数 工具数 搜索 Wide 9 27 共享 22 个 搜索 Deep 52 156 共享 22 个 DS FileSystem 24 129 14 个 DS Postgres 18 100 9 个 GUI PPT 21 42 共享 15 个 GUI Word 12 24 共享 15 个 GUI Excel 19 38 共享 15 个 总计 155 516 60### 评测流程：环境回放 + 主动交互这才是 AJ-Bench 设计最花心思的地方。传统 benchmark 给裁判一份静态的 Agent 轨迹，让它判断对错。AJ-Bench 的做法是：
- 先回放：把 Agent 的操作序列在环境中执行一遍，恢复到 Agent 操作后的最终状态- 再交互：裁判 Agent 基于这个环境状态，使用工具（搜索、文件操作、GUI 操作等）主动获取额外信息- 最后判决：结合回放状态和主动获取的证据，输出判定结果DS 类任务在本地回放，GUI 类任务部署在隔离的 AWS 实例上。搜索类任务则依赖外部网络环境。
## 关键结果：工具让裁判强了一个量级实验对比了 LLM-as-a-Judge 和 Agent-as-a-Judge 两种范式。Agent-as-a-Judge 用 gpt-5-mini-low 和 deepseek-v3.2 分别作为闭源和开源的代表。
核心发现 ：
模型 LLM-as-a-Judge F1 Agent-as-a-Judge F1 提升 gpt-5-mini-low 59.00 72.41 +13.41 deepseek-v3.2 64.49 77.34 +12.85一个模型加了工具调用，F1 直接涨 13 个点左右。 而且 gpt-5-mini-low 做成 Agent-as-a-Judge 之后，表现超过了 claude-opus-4.5、gemini-3-pro-preview 等更强的 LLM-as-a-Judge 基线。这说明 让裁判去验证，比裁判本身有多聪明更重要。
具体到各个领域，Agent-as-a-Judge 的提升幅度差异很大：
子领域 gpt-5-mini-low 提升 deepseek-v3.2 提升 PPT (GUI) +31.23 +24.76 Excel (GUI) +17.53 +9.59 Word (GUI) +23.81 +8.87 FileSystem (DS) +7.13 +12.29 Postgres (DS) +1.78 +6.39 Wide (Search) +5.09 +8.82 Deep (Search) +7.27 +19.23PPT 任务的提升最夸张——31 个点。 这说明在 GUI 这种视觉状态难以从文本推断的场景里，让裁判直接去看屏幕/检查状态，价值极大。而 Postgres 这种有精确脚本验证的 DS 任务，LLM-as-a-Judge 本身就不差，Agent 额外的搜索能力反而帮助有限。
## 消融实验：几个反直觉的发现### 推理能力 ≠ 工具使用能力论文做了一个 Thinking 消融实验，发现 开深度思考 (thinking) 并不一定更好 ：
- gpt-5-mini：medium 设定好于 low，high 设定反而在某些子领域不如 medium- deepseek-v3.2：thinking 版本比不 thinking 版本更差这说明”会思考”不等于”会有效地使用工具去验证”。更强的推理能力跟更好的工具调用策略之间，没有必然联系。
### 交互次数越多越好，但有边际递减给 deepseek-v3.2 设置不同的最大交互轮数上限，发现 F1 随交互次数单调递增，但收益最大的在少数几轮（1-4 轮之间）。Word 和 PPT 任务对交互次数更敏感，说明这些任务需要多轮信息收集。
### 多模态输入不一定更好在 GUI 域做模态消融：只用辅助树 (Accessibility Tree)、只用截图、还是两者混合。结果发现：
- PPT：辅助树和混合模式差不多- Word：截图最好- Excel：截图最好混合输入在某些场景下反而引入噪声，干扰判断。 这个发现对实际系统设计很有指导意义——别一股脑把所有模态都塞给裁判。
## 工程启示-如果你在做 Agent 的 RL 训练，Reward Model 的设计值得重新思考。 纯文本判定的 reward 信号质量有限，让 reward 模型具备环境交互能力可能是更靠谱的方向。
-Agent-as-a-Judge 的绝对性能还有很大提升空间。 最好的表现（deepseek-v3.2）F1 也只有 77%，意味着 23% 的判断仍然是错的。这个赛道远未饱和，值得投入。
-工具选择比模型大小更重要。 gpt-5-mini-low 做成 Agent 后打败了 claude-opus-4.5 的 LLM judge，说明给裁判赋能工具，比换更强的裁判模型收益更高。
## 局限- 任务大多改编自现有 benchmark，原创任务比例不高，未来需要更大规模独立构建- 搜索域依赖外部网络，网络不稳定性可能影响评测可靠性- Agent-as-a-Judge 的实验只用了两个模型做代表，更大规模的模型矩阵尚未覆盖
