# ai-papers

## 项目说明

AI论文摘要收集与管理项目，从 io.gf.com.cn（前沿研读·Frontier Studies）抓取论文摘要并保存为 Markdown 文件。

## 目录结构

| 目录/文件 | 说明 |
|-----------|------|
| `ai-ml/` | AI/ML 论文摘要 |
| `q-fin/` | 量化金融论文摘要 |
| `cncf/` | CNCF 相关论文摘要 |
| `.claude/skills/io-gf-fetch/` | 抓取技能与脚本 |
| `.venv/` | Python 虚拟环境 |
| `AGENTS.md` | 本文件 |

## 虚拟环境

**Python 3.7.3**（系统自带）

```bash
# 激活
source .venv/bin/activate

# 脚本仅需标准库: re, json, subprocess, time, html, sys, os
# 无需额外 pip install
```

## 使用方法

### 抓取论文

使用 `io-gf-fetch` 技能：

```
io-gf-fetch [日期范围]
```

- 不传参数 → 默认抓取今天
- "最近7天" → 最近一周
