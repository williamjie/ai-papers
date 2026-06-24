# ⭐⭐½ Jaeger 拥抱 ClickHouse：万亿级 Trace 的存储革命

**日期**: 2026-06-23

---

原文 : Building Jaeger’s ClickHouse backend: 8.6× compression on 10 million spans来源 : https://www.cncf.io/blog/2026/06/23/building-jaegers-clickhouse-backend-8-6x-compression-on-10-million-spans/Jaeger v2.18.0 正式原生支持 ClickHouse，这不仅是多了一个存储后端选项，更是分布式追踪（Distributed Tracing）在大规模场景下的一次架构正名。对于被 Elasticsearch 高昂运维成本压得喘不过气的大厂团队来说，这是一个值得关注的转折点。
## 为什么是 ClickHouse？
过去几年，Jaeger 社区一直呼吁支持 ClickHouse。核心痛点很明确：Cassandra 和 Elasticsearch 虽然好用，但在海量数据面前，索引开销大、扩展复杂且存储成本高昂。
Trace 数据的本质是 高重复性 。服务名、操作名、状态码在数亿次调用中反复出现。行式存储（Row-oriented）无法有效压缩这种冗余，而列式存储（Columnar Storage）天生擅长此道。ClickHouse 作为 OLAP 数据库，其设计初衷就是处理高吞吐写入和复杂聚合查询，这与 Trace 数据的“追加写、多维查”特征完美契合。
## 核心架构决策：主键的博弈Schema 设计是这次集成的最大难点。ClickHouse 的主键（Primary Key）并非唯一性约束，而是决定了磁盘排序和稀疏索引（Sparse Index）。Jaeger 团队面临两个互斥的目标：
- 优化 Trace 检索：按 trace_id 排序。优点是单次读取完整链路极快；缺点是搜索查询（如按服务名过滤）无法利用主键索引，性能灾难。
- 优化搜索查询：按 (service_name, name, start_time) 排序。这是最终选择。
⚠️ 反直觉发现 ：牺牲 Trace 检索速度来换取搜索性能，是更优解。
通过引入 bloom_filter 跳过索引和物化视图（Materialized View），即使主键不匹配，Trace 检索也能维持在可接受范围。基准测试显示，按服务名排序后，Trace 检索从 27ms 增至 100ms，但多条件搜索从 880ms 骤降至 140ms。
## 关键性能指标在单节点、1000 万 Trace（共 1000 万 Span）的基准测试中，数据令人印象深刻：
- 压缩率：高达 8.6×。原本近 6 GiB 的数据被压缩至约 722 MiB。
- 写入吞吐：持续超过 50k spans/sec。
- 查询延迟：Trace 检索平均 100ms，简单搜索 <50ms，复杂过滤 ~140ms。
这种压缩率意味着存储成本的大幅下降，对于长期保留 Trace 数据的团队极具吸引力。
## 工程启示与局限谁应该关注？
如果你的日均 Trace 量超过千万级，且受限于 ES 集群的索引维护成本或查询延迟，ClickHouse 后端是必选项。此外，Jaeger v2.18 引入了基于 ClickHouse 的原生 SPM（Service Performance Monitoring）功能，可直接从 Trace 计算延迟、错误率等指标，无需额外构建 Metrics 管道。
需要注意的坑：
- 属性搜索代价高：由于主键优化的是服务/操作/时间，纯属性（Attribute）过滤无法充分利用索引。最佳实践是始终结合服务名或时间范围进行过滤。
- 类型复杂度：Jaeger v2 支持 OpenTelemetry 的强类型属性。存储层通过 Nested 列和元数据表（attribute_metadata）来解决类型歧义，但这增加了查询规划的复杂性。
## 总结Jaeger 集成 ClickHouse 不是简单的“多一个选项”，而是对 Trace 存储范式的一次纠偏。它证明了在特定场景下，专用 OLAP 数据库比通用搜索引擎更具性价比。虽然目前处于 Alpha 阶段，但其展现出的压缩率和查询性能，已足以让大型云原生团队开始规划迁移路径。
## 📝 AI 点评点评时间：2026-06-23 20:14 ｜ reviewer: DeepSeek V4 Flash核心贡献:
原文要解决 Jaeger 在大规模分布式追踪场景下存储后端的性能与成本瓶颈，核心方法是设计一套基于 ClickHouse 的列式存储架构，通过精心选择主键、物化视图、嵌套列等技术实现高压缩率与低延迟查询。
亮点:
博文准确提炼了原文最关键的工程决策——主键取舍，并清晰说明了“牺牲 trace 检索换取搜索性能”这一反直觉结论，同时保留了 8.6× 压缩率、50k spans/sec 写入、100 ms trace 检索等关键基准数据。对属性搜索代价和 SPM 功能的说明也与原文一致。
挑刺:
- 核心数据严重错位：原文明确基准测试使用 “10 million spans across 1 million traces”，而博文写成 “1000 万 Trace（共 1000 万 Span）”，将 trace 与 span 数量混淆（实际应为 100 万 trace、1000 万 span），属于关键事实错误。
- 标题过度夸大：原文仅测试千万级 span，标题却用 “万亿级 Trace”，原文并未提及万亿量级，存在明显夸大。
- 遗漏基准环境约束：原文强调 “These numbers should be read in the context of the benchmark environment and dataset” 并附有完整报告，博文未提及单节点部署、具体数据集等条件，可能让读者误以为这是通用性能。
总评:
⭐⭐½ 博文整体传达了原文核心设计思路，但存在关键数字错误和标题夸大，削弱了技术解读的严谨性。
