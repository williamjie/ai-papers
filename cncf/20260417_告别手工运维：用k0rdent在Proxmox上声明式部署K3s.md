# 告别手工运维：用 k0rdent 在 Proxmox 上声明式部署 K3s

**日期**: 2026-04-17

---

原文 : K3s on On-Prem Infrastructures the GitOps Way: Writing a Custom k0rdent Template from Scratch来源 : https://www.cncf.io/blog/2026/04/17/k3s-on-on-prem-infrastructures-the-gitops-way-writing-a-custom-k0rdent-template-from-scratch/Kubernetes 12 岁了。
从 Google 的一个 Side Project 到现代基础设施的操作系统，K8s 的生态版图已经覆盖从大型机到 GPU，从多云到边缘的每一个角落。CNCF 的 Landscape 也随之膨胀，填补着 K8s 留下的空白。
但有一个痛点始终未解： 在 On-Prem（本地私有环境）跑 K8s，往往是一场“手工艺术”的灾难。
这篇文章来自 CNCF Ambassador 和 Improwised Tech 的工程团队，他们分享了一个非常务实的组合拳： Proxmox + K3s + k0rdent 。这不是什么高深莫测的理论，而是他们生产环境中真实运行的集群搭建方案。
核心就一句话：用 k0rdent 的 BYOT（Bring Your Own Template）机制，把“手搓”集群变成“声明式”配置。
## 痛点：On-Prem 的“部落知识”陷阱如果你亲手在本地机房或 Proxmox 上装过 K8s，你大概率经历过这种绝望：
- 手动创建 VM：一旦规模稍微大点，手动操作就是噩梦。
- 脆弱的 Bash 脚本：写脚本的人离职了，脚本成了只有他能懂的“部落知识”。
- 不可复现的集群：集群跑起来的时候好好的，想重建？对不起，你得重新回忆一遍当时的参数和顺序。
这种“能用就行”的状态，是云原生工程化的大忌。我们需要的是声明式（Declarative）、可重复、干净的交付。
## 方案拆解：k0rdent 的三层解耦k0rdent 是 CNCF 的一个多集群管理项目，它的核心设计理念是 分离关注点（Separation of Concerns） 。
在这个方案中，k0rdent 充当了“调度员”，将集群生命周期拆分为三层：
层级 职责 实现组件 Infrastructure 提供虚拟机资源 自定义 Helm Chart (Proxmox Provider) Control Plane 配置集群拓扑 K3s Control Plane Provider Bootstrap 安装初始化 K8s K3s Bootstrap Provider### 1. 基础设施层：BYOT 的聪明之处k0rdent 原生支持 AWS、Azure、vSphere 等主流云，但 原生不支持 Proxmox 。怎么办？
文章中的作者没有选择等待社区支持，而是用了一个 Helm Chart 写了一个自定义的 Infrastructure Provider。
这里有个关键决策： Bring Your Own Template (BYOT) 。
很多方案喜欢每次部署都动态构建虚拟机镜像。作者反其道而行之：
- 预先在 Proxmox 里准备好“母盘”（Template），内置好 OS、SSH 密钥、Cloud-init 和基础包。
- 部署时，直接从模板克隆 VM。
为什么这么干？
- 速度快：省去了每次部署都去编译镜像的耗时。
- 更安全：OS 加固在 K8s 流程之外单独管理，职责清晰。
- 更好查错：如果出问题了，VM 层是已知状态，不用去猜镜像里缺了什么包。
这个 Helm Chart 做的事很纯粹：调 Proxmox API -> 克隆 VM -> 分配 CPU/内存/网络 -> 注入 SSH Key -> 把 VM 元数据吐回给 k0rdent。 绝不碰任何 K8s 逻辑。
### 2. 控制面与引导层：K3s 的轻量化胜利VM 就绪后，k0rdent 把接力棒交给 Control Plane Provider。
在这个阶段，作者选择了 K3s 。
在 On-Prem 或边缘场景，K3s 依然是首选。它的理由很简单：
- 轻量、依赖少、安装快。
- 完美契合“自托管”环境对资源敏感的特性。
通过声明 API 对象（ BootstrapProvider 和 ControlPlaneProvider ），k0rdent 会自动去拉取 K3s 的安装组件。
# 伪代码逻辑：告诉 k0rdent 用哪个版本的 K3sapiVersion : operator.cluster.x-k8s.io/v1alpha2kind : BootstrapProvidermetadata :
name : k3sspec :
version : v0.3.0fetchConfig :
url : https://github.com/k3s-io/cluster-api-k3s/releases/...
一旦配置下发，K3s 引导程序会在第一个 Control Plane 节点上安装，提取 Token，然后让其他节点加入。至此，K8s 集群启动。
## 工程启示：声明式是唯一的出路这个方案最值得借鉴的不是技术栈本身，而是 工程方法论 。
在 On-Prem 环境下，我们往往因为“环境特殊”而妥协于脚本和手动操作。但 k0rdent 证明了，即便基础设施层不被原生支持，你依然可以通过 Helm Chart 封装 Provider 的方式，将其纳入 GitOps 流程。
核心转变 ：
- 从 “How”（怎么写脚本一步步跑）
- 转向 “What”（定义我想要的最终状态）
当一切变成配置，集群的扩缩容、重建、灾备就不再是“周末项目”或“恐怖故事”，而是简单的 git push 。
## 局限与思考当然，这个方案也有适用边界：
- 复杂度转移：虽然声明式部署爽了，但编写和维护自定义 Infrastructure Provider Helm Chart 需要较高的 Go/Helm 开发能力。
- 适用范围：对于只需要 1-2 个小集群的团队，这套重型工具链可能有点杀鸡用牛刀。但对于多集群管理、有标准化交付需求的团队，这是必经之路。
结论 ：
如果你的 On-Prem 环境还在靠手搓和脚本维系，k0rdent 的 BYOT 模式值得尝试。它告诉你： 基础设施不是二等公民，只要你会写 Helm Chart，就能把任何私有云变成一等公民。
← 上一篇（更早） AI 漏洞扫描泛滥：云原生项目如何自救 下一篇（更新） → 告警诊断的真相：跑模不如写手册 ← 返回首页 © 2026 前沿研读 · Frontier Studies. All rights reserved.
📡 RSSfunction d(){const o=document.getElementById("article-toc");if(!o)return;const i=document.querySelectorAll(".prose h2, .prose h3");if(i.length {e.id||(e.id="h-"+c);const n=document.createElement("li");n.className=e.tagName.toLowerCase();const t=document.createElement("a");t.href="#"+e.id,t.textContent=(e.textContent||"").trim(),n.appendChild(t),s.appendChild(n),r.push({a:t,h:e})}),o.appendChild(s);const l=new IntersectionObserver(e=>{e.forEach(c=>{if(!c.isIntersecting)return;const n=r.find(t=>t.h===c.target);n&&(r.forEach(t=>t.a.classList.remove("active")),n.a.classList.add("active"))})},{rootMargin:"-80px 0px -70% 0px"});i.forEach(e=>l.observe(e))}d();
