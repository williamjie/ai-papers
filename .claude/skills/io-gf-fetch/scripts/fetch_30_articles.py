#!/usr/bin/env python3
"""
Fetch 30 articles from io.gf.com.cn, one every 2 minutes.
"""

import json
import os
import re
import glob
import subprocess
import sys
import time
from datetime import datetime

# Configuration
CDP_DIR = os.path.expanduser("~/.agents/skills/chrome-cdp")
CLEANER = os.path.expanduser("~/Documents/company_code/ai-papers/.claude/skills/io-gf-fetch/scripts/clean_article.py")
TAB_ID = "6C10CC6E"  # 前沿研读 tab

TOPIC_DIR = {"AI": "ai-ml", "Q-Fin": "q-fin", "CNCF": "cncf"}


def cdp(*args, timeout=30):
    """Execute CDP command and return stdout."""
    try:
        r = subprocess.run(
            ["node", "scripts/cdp.mjs"] + list(args),
            cwd=CDP_DIR,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"[ERROR] CDP timeout: {' '.join(args)}")
        return ""
    except Exception as e:
        print(f"[ERROR] CDP failed: {e}")
        return ""


def fetch_article(article):
    """Fetch a single article and save to file."""
    topic = article["topic"]
    folder = TOPIC_DIR.get(topic)
    if not folder:
        print(f"[SKIP] Unknown topic: {topic}")
        return False

    date = article["date"].replace("-", "")
    title = re.sub(r'[⭐★½\s]+', '', article["title"]).strip()[:80]
    title = re.sub(r'[<>:"/\\|?*]', '_', title)
    fname = f"{date}_{title}.md"
    fpath = os.path.join(folder, fname)

    if os.path.exists(fpath):
        print(f"[SKIP] Already exists: {fname}")
        return False

    print(f"[FETCH] {article['date']} | {topic} | {article['title'][:60]}")

    try:
        # 1. Navigate to article
        cdp("nav", TAB_ID, article["href"])
        time.sleep(5)

        # 2. Get metadata
        meta_json = cdp("eval", TAB_ID,
            'JSON.stringify({title:document.querySelector(".article-title").textContent.trim()})')
        try:
            meta = json.loads(meta_json)
            title = meta.get("title", article["title"])
        except:
            title = article["title"]

        # 3. Get article content
        html = cdp("html", TAB_ID, ".prose")
        if not html:
            print(f"[WARN] Empty HTML for {article['href']}")
            return False

        # 4. Clean HTML to markdown
        result = subprocess.run(
            ["python3", CLEANER],
            input=html,
            capture_output=True,
            text=True,
            timeout=30
        )
        body = result.stdout.strip()
        if not body:
            print(f"[WARN] Empty cleaned content for {article['href']}")
            return False

        # 5. Save to file
        md = f"# {title}\n\n**日期**: {article['date']}\n\n---\n\n{body}"
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(md)

        print(f"[OK] Saved: {fname}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to fetch {article['href']}: {e}")
        return False


def main():
    # Load articles from cache
    with open("/tmp/articles.json") as f:
        data = json.load(f)

    articles = data.get("articles", [])
    if not articles:
        print("[ERROR] No articles found")
        sys.exit(1)

    # Sort by date descending (newest first)
    articles.sort(key=lambda a: a.get("date", ""), reverse=True)

    # Filter to valid topics
    articles = [a for a in articles if a.get("topic") in TOPIC_DIR]

    # Get first 30 articles to fetch (skip existing)
    to_fetch = []
    for a in articles:
        topic = a["topic"]
        folder = TOPIC_DIR.get(topic)
        if not folder:
            continue
        date = a["date"].replace("-", "")
        title = re.sub(r'[⭐★½\s]+', '', a.get("title", "")).strip()[:80]
        title = re.sub(r'[<>:"/\\|?*]', '_', title)
        fname = f"{date}_{title}.md"
        fpath = os.path.join(folder, fname)
        if not os.path.exists(fpath):
            to_fetch.append({**a, 'filename': fname, 'folder': folder})
        if len(to_fetch) >= 30:
            break

    if not to_fetch:
        print("[INFO] No articles to fetch")
        sys.exit(0)

    print(f"Will fetch {len(to_fetch)} articles, one every 2 minutes")
    print("=" * 60)

    fetched = 0
    skipped = 0
    failed = 0

    for article in to_fetch:
        success = fetch_article(article)
        if success:
            fetched += 1
        elif os.path.exists(os.path.join(article['folder'], article['filename'])):
            skipped += 1
        else:
            failed += 1

        print(f"[STATS] Fetched: {fetched} | Skipped: {skipped} | Failed: {failed}")
        print("=" * 60)

        if fetched + skipped < len(to_fetch):
            print(f"[WAIT] Next article in 2 minutes...")
            time.sleep(120)

    print()
    print(f"[DONE] Fetched: {fetched} | Skipped: {skipped} | Failed: {failed}")


if __name__ == "__main__":
    main()
