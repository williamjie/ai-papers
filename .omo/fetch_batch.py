#!/usr/bin/env python3
"""Fetch up to N articles from io.gf.com.cn with retry and rate-limit handling."""

import json, os, re, subprocess, sys, time
from datetime import datetime, timedelta
from pathlib import Path

# ---------- config ----------
WORKSPACE = Path("/Users/zj/Documents/company_code/ai-papers")
CDP_DIR = Path.home() / ".agents" / "skills" / "chrome-cdp"
CLEANER = WORKSPACE / ".claude" / "skills" / "io-gf-fetch" / "scripts" / "clean_article.py"
FETCH_COUNT = 20
RETRY_WAIT = 60  # seconds to wait on rate limit / transient errors
MAX_RETRIES = 3
DELAY_BETWEEN = 30  # seconds between articles (anti-scraping)

TOPIC_DIR = {"AI": "ai-ml", "Q-Fin": "q-fin", "CNCF": "cncf"}
TAB = "6DD396E8"

# ---------- helpers ----------

def cdp(*args, timeout=30):
    r = subprocess.run(
        ["node", "scripts/cdp.mjs"] + list(args),
        cwd=str(CDP_DIR), capture_output=True, text=True, timeout=timeout,
    )
    out = r.stdout.strip()
    # Detect rate-limit / blocking signals with stricter patterns to avoid false positives
    lower = out.lower()
    if ("rate limit" in lower or "too many requests" in lower or "cloudflare" in lower or "captcha" in lower
            or re.search(r'\b429\b', out) or "access denied" in lower or "blocked" in lower):
        raise RuntimeError(f"RATE_LIMIT:{out[:200]}")
    if r.returncode != 0:
        raise RuntimeError(f"CDP_ERROR:{r.stderr[:200]}")
    return out


def slugify(text, maxlen=80):
    text = re.sub(r'[⭐★½\s]+', '', text).strip()
    text = re.sub(r'[<>:"/\\|?*]', '_', text)
    return text[:maxlen]


def existing_files():
    files = set()
    for folder in TOPIC_DIR.values():
        p = WORKSPACE / folder
        if p.exists():
            files.update(f.name for f in p.iterdir() if f.is_file() and f.suffix == ".md")
    return files


def validate_article(path: Path):
    """Lightweight validation: line count + no raw HTML tags."""
    text = path.read_text(errors="ignore")
    lines = text.splitlines()
    if not (15 <= len(lines) <= 150):
        return False, f"LINE_COUNT={len(lines)}"
    if re.search(r'<(p|div|span|ul|ol|li|h[1-6]|table|tr|td|th|pre|code|blockquote)\b', text):
        return False, "HTML_TAGS_FOUND"
    return True, "ok"


# ---------- main ----------

def main():
    print("[1] Extracting article list from io.gf.com.cn ...")
    raw = cdp("eval", TAB, "(()=>{let links=document.querySelectorAll('a'),seen=new Set(),arts=[];for(let a of links){let h=a.href||'';if(h.includes('/blog/')&&!seen.has(h)){seen.add(h);let t=(a.textContent||'').trim().replace(/\\s+/g,' ').substring(0,100);let topic=h.includes('qfin')?'Q-Fin':h.includes('cncf')?'CNCF':'AI';let dm=h.match(/blog\\/(?:qfin-|cncf-)?([0-9]{4}-[0-9]{2}-[0-9]{2})/);arts.push({href:h,title:t,date:dm?dm[1]:'',topic});}}arts.sort((a,b)=>b.date.localeCompare(a.date)||a.href.localeCompare(b.href));return JSON.stringify({count:arts.length,articles:arts});})()", timeout=60)

    data = json.loads(raw)
    all_articles = data["articles"]
    print(f"    Total articles on page: {data['count']}")

    # Default date range: today and recent days to ensure enough candidates
    today = datetime.now().date()
    date_from = today - timedelta(days=2)
    print(f"    Date range filter: {date_from} → {today}")

    # Deduplicate against existing files
    existing = existing_files()
    print(f"    Existing files: {len(existing)}")

    candidates = []
    seen_urls = set()
    for a in all_articles:
        if a["date"] < str(date_from):
            continue  # too old
        if a["href"] in seen_urls:
            continue
        seen_urls.add(a["href"])

        dp = a["date"].replace("-", "")
        ct = slugify(a["title"])
        fname = f"{dp}_{ct}.md"
        fpath = WORKSPACE / TOPIC_DIR[a["topic"]] / fname

        if fname in existing:
            continue  # already fetched

        candidates.append((a, fpath))

    print(f"    Candidates to fetch: {len(candidates)}")

    if not candidates:
        print("    Nothing to fetch. Exiting.")
        sys.exit(0)

    to_fetch = candidates[:FETCH_COUNT]
    print(f"    Will fetch: {len(to_fetch)}")

    fetched = 0
    skipped = 0
    failed = 0
    refetched = 0

    for idx, (a, fpath) in enumerate(to_fetch, 1):
        title = a["title"]
        print(f"\n[{idx}/{len(to_fetch)}] {title[:60]}...")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # 1. navigate
                print(f"    -> nav {a['href']}")
                cdp("nav", TAB, a["href"], timeout=60)
                time.sleep(3)

                # 2. metadata
                meta_raw = cdp("eval", TAB,
                    '(()=>JSON.stringify({title:document.querySelector(".article-title")?.textContent?.trim()||""}))()',
                    timeout=30)
                meta = json.loads(meta_raw)
                article_title = meta.get("title") or title

                # 3. html
                html = cdp("html", TAB, ".prose", timeout=60)

                # 4. clean
                clean = subprocess.run(
                    ["python3", str(CLEANER)],
                    input=html, capture_output=True, text=True, timeout=60,
                )
                if clean.returncode != 0:
                    raise RuntimeError(f"cleaner failed: {clean.stderr[:200]}")

                body = clean.stdout.strip()

                # 5. save
                md = f"# {article_title}\n\n**日期**: {a['date']}\n\n---\n\n{body}\n"
                fpath.parent.mkdir(parents=True, exist_ok=True)
                fpath.write_text(md, encoding="utf-8")
                print(f"    -> saved {fpath.relative_to(WORKSPACE)}")

                # 6. validate freshly saved file
                ok, reason = validate_article(fpath)
                if not ok:
                    print(f"    -> validation failed ({reason}), will retry")
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_WAIT)
                        continue
                    failed += 1
                else:
                    fetched += 1
                    print(f"    -> validation passed")

                # 7. back home
                cdp("nav", TAB, "http://io.gf.com.cn/", timeout=60)
                break  # success or final failure, move on

            except RuntimeError as e:
                msg = str(e)
                if "RATE_LIMIT" in msg:
                    print(f"    !! Rate limited (attempt {attempt}/{MAX_RETRIES}), waiting {RETRY_WAIT}s ...")
                    time.sleep(RETRY_WAIT)
                else:
                    print(f"    !! Error: {msg[:120]} (attempt {attempt}/{MAX_RETRIES})")
                    time.sleep(RETRY_WAIT)

                if attempt == MAX_RETRIES:
                    failed += 1
                    # try to go back home before next article
                    try:
                        cdp("nav", TAB, "http://io.gf.com.cn/", timeout=60)
                    except Exception:
                        pass

        # delay before next article (anti-scraping)
        if idx < len(to_fetch):
            print(f"    ... sleeping {DELAY_BETWEEN}s before next article")
            time.sleep(DELAY_BETWEEN)

    print("\n=== Summary ===")
    print(f"Fetched:   {fetched}")
    print(f"Skipped:   {skipped} (deduplicated)")
    print(f"Failed:    {failed}")
    print(f"Refetched: {refetched}")

    # Re-run validation
    print("\n[validate] Re-running article validation ...")
    result = subprocess.run(
        ["python3", str(WORKSPACE / ".claude/skills/io-gf-fetch/scripts/validate_articles.py"),
         "ai-ml/", "q-fin/", "cncf/"],
        cwd=str(WORKSPACE), capture_output=True, text=True, timeout=120,
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr[:500])

    # Write summary JSON for downstream
    summary = {
        "fetched": fetched,
        "skipped": skipped,
        "failed": failed,
        "refetched": refetched,
        "timestamp": datetime.now().isoformat(),
    }
    (WORKSPACE / ".omo" / "fetch-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\nSummary written to .omo/fetch-summary.json")


if __name__ == "__main__":
    main()
