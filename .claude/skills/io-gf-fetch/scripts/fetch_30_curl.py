#!/usr/bin/env python3
"""
Fetch 30 articles from io.gf.com.cn, one every 2 minutes.
Uses curl + clean_article.py instead of CDP.
"""

import json
import os
import re
import subprocess
import sys
import time

# Configuration
CLEANER = os.path.expanduser("~/Documents/company_code/ai-papers/.claude/skills/io-gf-fetch/scripts/clean_article.py")
ARTICLES_JSON = "/tmp/articles.json"

TOPIC_DIR = {"AI": "ai-ml", "Q-Fin": "q-fin", "CNCF": "cncf"}


def fetch_article(article):
    """Fetch a single article using curl and save to file."""
    topic = article["topic"]
    folder = TOPIC_DIR.get(topic)
    if not folder:
        print(f"[SKIP] Unknown topic: {topic}")
        return False

    date = article["date"].replace("-", "")

    print(f"[FETCH] {article['date']} | {topic} | {article.get('title', '')[:60]}")

    try:
        # 1. Get article HTML with curl
        result = subprocess.run(
            ["curl", "-s", article["href"]],
            capture_output=True,
            text=True,
            timeout=30
        )
        html = result.stdout

        if not html or len(html) < 1000:
            print(f"[WARN] Empty/short HTML for {article['href']}")
            return False

        title_match = re.search(r'<h1 class="article-title"[^>]*>(.*?)</h1>', html, re.DOTALL)
        if title_match:
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
        else:
            title = article.get("title", "Untitled")

        title_safe = re.sub(r'[⭐★½\s]+', '', title).strip()[:80]
        title_safe = re.sub(r'[<>:"/\\|?*]', '_', title_safe)
        fname = f"{date}_{title_safe}.md"
        fpath = os.path.join(folder, fname)

        if os.path.exists(fpath):
            print(f"[SKIP] Already exists: {fname}")
            return False

        prose_match = re.search(r'<div class="prose" [^>]*>(.*?)</div>\s*<nav', html, re.DOTALL)
        if not prose_match:
            prose_match = re.search(r'<div class="prose" [^>]*>(.*?)</div>\s*</div>\s*</article>', html, re.DOTALL)
        
        if not prose_match:
            print(f"[WARN] No .prose found for {article['href']}")
            return False

        prose_html = prose_match.group(1)

        result = subprocess.run(
            ["python3", CLEANER],
            input=prose_html,
            capture_output=True,
            text=True,
            timeout=30
        )
        body = result.stdout.strip()
        if not body:
            print(f"[WARN] Empty cleaned content for {article['href']}")
            return False

        md = f"# {title}\n\n**日期**: {article['date']}\n\n---\n\n{body}"
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(md)

        print(f"[OK] Saved: {fname}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to fetch {article['href']}: {e}")
        return False


def main():
    # Load articles
    if not os.path.exists(ARTICLES_JSON):
        print(f"[ERROR] Articles list not found: {ARTICLES_JSON}")
        sys.exit(1)

    with open(ARTICLES_JSON) as f:
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
    failed = 0
    commit_counter = 0

    for i, article in enumerate(to_fetch):
        success = fetch_article(article)
        if success:
            fetched += 1
            commit_counter += 1
        else:
            failed += 1

        if commit_counter >= 5:
            print("[GIT] Auto-committing...")
            subprocess.run(["git", "add", "."], cwd=os.path.expanduser("~/Documents/company_code/ai-papers"))
            subprocess.run(["git", "commit", "-m", f"Fetch {commit_counter} articles from io.gf.com.cn"])
            subprocess.run(["git", "push"], cwd=os.path.expanduser("~/Documents/company_code/ai-papers"))
            print("[GIT] Pushed to remote")
            commit_counter = 0

        print(f"[STATS] Progress: {i+1}/{len(to_fetch)} | Fetched: {fetched} | Failed: {failed}")
        print("=" * 60)

        # Wait 2 minutes before next article (except last)
        if i < len(to_fetch) - 1:
            print(f"[WAIT] Next article in 2 minutes... (Ctrl+C to stop)")
            time.sleep(120)

    # Final commit for remaining articles
    if commit_counter > 0:
        print("[GIT] Final commit...")
        subprocess.run(["git", "add", "."], cwd=os.path.expanduser("~/Documents/company_code/ai-papers"))
        subprocess.run(["git", "commit", "-m", f"Fetch {commit_counter} articles from io.gf.com.cn"])
        subprocess.run(["git", "push"], cwd=os.path.expanduser("~/Documents/company_code/ai-papers"))
        print("[GIT] Pushed to remote")

    print()
    print(f"[DONE] Fetched: {fetched}/{len(to_fetch)} | Failed: {failed}")


if __name__ == "__main__":
    main()
