# Article Output Format Reference

Each fetched article is saved as a markdown file with this structure:

```
## <star rating> <title>

<date>
<reading time>
Paper: <paper title>
Link: <arxiv_url>

<body text paragraphs>

## <section heading>

<section text>

## <section heading>

<section text>

...

## 📝 AI 点评

<review metadata>
<review body>
```

## Example

File: `ai-ml/20260624_DiT评估新范式ImageNetFID不再万能.md`

```markdown
## ⭐⭐⭐½ DiT评估新范式：ImageNet FID不再万能

2026年6月24日
9 分钟阅读
论文: DiffusionBench: On Holistic Evaluation of Diffusion Transformers
链接: https://arxiv.org/abs/2606.24888

过去几年，DiT（Diffusion Transformer）社区陷入了一种"唯ImageNet论"的内卷。
...

## 为什么 ImageNet FID 会失效？
...

## NANO GEN：工程上的"降维打击"
...

## 关键结果：谁才是真正的强者？
...

## 工程启示：如何评估你的 DiT？
...

## 局限与展望
...

## 📝 AI 点评
...
```

## Cleanup rules applied

- No HTML tags
- No raw `[StaticText]` markers
- No duplicate TOC headings at the end
- No "© 2026 前沿研读" footer
- No "← 上一篇" / "下一篇 →" navigation
- No "grammarly" integration text
- Math symbols merged (Σ + 𝑡 + 𝑜 + 𝑡 → Σtot)
