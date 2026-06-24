---
name: io-gf-fetch
description: |
  Fetch AI paper summaries from io.gf.com.cn (前沿研读·Frontier Studies) and save
  as clean markdown files organized by topic. Supports date range queries like
  "获取论文,最近7天", "抓取今天", "下载6月20到6月24的文章". MUST USE this skill
  whenever the user asks to download/fetch/scrape articles from io.gf.com.cn or
  前沿研读. Triggers: "下载io.gf文章", "保存前沿研读", "fetch io.gf.com.cn",
  "抓取文章", "调用技能获取论文", "获取论文", "fetch articles from io", or any
  request involving saving content from http://io.gf.com.cn/.
---

# io.gf.com.cn Article Fetcher

## Prerequisites

- Chrome remote debugging: `chrome://inspect/#remote-debugging`
- Node.js 22+ — Chrome CDP at `~/.agents/skills/chrome-cdp/`
- Python 3

---

## Phase 0: Parse user intent → date range

| User says | Date range |
|-----------|-----------|
| "今天" / "today" | single date ± 0 |
| "昨天" | single date - 1 day |
| "最近3天" / "最近7天" / "最近一周" | today - N days → today |
| "6月20到6月24" / "06-17→06-24" | explicit start → end |
| no date specified | default to "今天" |

Convert to `YYYY-MM-DD` for comparison against article list.

---

## Phase 1: Audit existing articles

Run before fetching to skip clean articles and identify ones needing re-fetch:

```bash
python3 .claude/skills/io-gf-fetch/scripts/validate_articles.py ai-ml/ q-fin/ cncf/
```

Returns JSON: `{"clean": [...], "bad": [[file, reason], ...]}`.

Validation rules:
- **Line count**: 15–150 lines (signals truncated or noise-filled files)
- **Real HTML tags**: matches `<p>`, `<div>`, `<span>` etc. — NOT false positives like `<8B`, `<5%`, `<payment-card:uuid>`

Delete files in the `bad` list and re-fetch them.

---

## Phase 2: Verify Chrome CDP + extract article list

```bash
cd ~/.agents/skills/chrome-cdp
node scripts/cdp.mjs list                          # find tab
node scripts/cdp.mjs nav <TAB> 'http://io.gf.com.cn/'
node scripts/cdp.mjs eval <TAB> '
let links=document.querySelectorAll("a"),seen=new Set(),arts=[];
for(let a of links){let h=a.href||"";if(h.includes("/blog/")&&!seen.has(h)){
seen.add(h);let t=(a.textContent||"").trim().replace(/\s+/g," ").substring(0,100);
let topic=h.includes("qfin")?"Q-Fin":h.includes("cncf")?"CNCF":"AI";
let dm=h.match(/blog\/(?:qfin-|cncf-)?(\d{4}-\d{2}-\d{2})/);
arts.push({href:h,title:t,date:dm?dm[1]:"",topic});}}
arts.sort((a,b)=>b.date.localeCompare(a.date)||a.href.localeCompare(b.href));
JSON.stringify({count:arts.length,articles:arts});
' > /tmp/articles.json
```

Filter articles by the parsed date range from Phase 0.

---

## Phase 3: Deduplicate

For each article in the filtered list, check if already exists:

```python
dp = date.replace("-", "")
ct = re.sub(r'[⭐★½\s]+','', title).strip()[:80]
ct = re.sub(r'[<>:"/\\|?*]','_', ct)
fname = f"{dp}_{ct}.md"
fpath = os.path.join(out_dir, topic_folder, fname)
if os.path.exists(fpath):
    skip  # already fetched
```

Only fetch: non-existent files + files flagged as `bad` by Phase 1.

---

## Phase 4: Fetch (30s delay)

Pipeline per article: `nav → eval meta → html .prose → clean_article.py → save → back → sleep 30`

```python
TOPIC_DIR = {"AI":"ai-ml","Q-Fin":"q-fin","CNCF":"cncf"}
CLEANER = ".claude/skills/io-gf-fetch/scripts/clean_article.py"

def cdp(*args, timeout=30):
    r = subprocess.run(["node","scripts/cdp.mjs"]+list(args),
        cwd=CDP_DIR, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()

# ... loop over articles_to_fetch ...

nav = cdp("nav", TAB, a["href"])            # 1. navigate
time.sleep(3)
meta = json.loads(cdp("eval", TAB,           # 2. metadata
    'JSON.stringify({title:document.querySelector(".article-title").textContent.trim()})'))
body = subprocess.run(["python3", CLEANER],  # 3+4. html → clean
    input=cdp("html", TAB, ".prose"),
    capture_output=True, text=True).stdout
# 5. save
md = f"# {meta['title']}\n\n**日期**: {a['date']}\n\n---\n\n{body}"
with open(fpath, "w") as f: f.write(md)
cdp("nav", TAB, "http://io.gf.com.cn/")     # 6. back home
time.sleep(30)                               # 7. anti-scraping
```

---

## Phase 5: Validate results

Re-run Phase 1 validation. Report: `fetched N, skipped M, failed K, re-fetched R`.

---

## Topic → Folder

| URL pattern | Topic | Folder |
|------------|-------|--------|
| `/blog/qfin-*` | Q-Fin | `q-fin/` |
| `/blog/cncf-*` | CNCF | `cncf/` |
| `/blog/2026-*` | AI/ML | `ai-ml/` |

Filename: `YYYYMMDD_title.md` (strip ⭐★½, max 80 chars, `<>:"/\|?*` → `_`)

---

## Bundled Scripts

| Script | Purpose |
|--------|---------|
| `scripts/clean_article.py` | HTML → markdown. Removes KaTeX visual fragments, keeps MathML text. |
| `scripts/validate_articles.py` | Quality audit: line count + real HTML tag detection. |

## Key Rules

1. Validate first → skip clean, re-fetch bad
2. 30s between articles (anti-scraping)
3. `nav` not `open` (reuse tab)
4. `html '.prose'` not `snap` (snap explodes KaTeX)
