#!/usr/bin/env python3
"""
Background fetcher for io.gf.com.cn pending articles.
Reads a JSON list of pending articles (from /tmp/to_fetch.json by default),
fetches each via Chrome CDP, cleans HTML -> markdown, saves to the topic folder.
Honours a 30s anti-scraping delay between articles. Resumable: already-saved
files are skipped, and fetched hrefs are recorded in the state file.
"""

import json
import os
import re
import subprocess
import sys
import time

# ---- Configuration (overridable via env) ----
CDP_DIR = os.environ.get("CDP_DIR", os.path.expanduser("~/.agents/skills/chrome-cdp"))
CLEANER = os.environ.get(
    "CLEANER",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "clean_article.py"),
)
LIST_FILE = os.environ.get("LIST_FILE", "/tmp/to_fetch.json")
STATE_FILE = os.environ.get("STATE_FILE", "/tmp/fetch_state.json")
TAB_ID = os.environ.get("TAB_ID", "A4BFF7BF")
BASE_OUT = os.environ.get("BASE_OUT", "/data/self_code/ai-papers")
DELAY = int(os.environ.get("DELAY", "30"))

TOPIC_DIR = {"AI": "ai-ml", "Q-Fin": "q-fin", "CNCF": "cncf"}


def cdp(*args, timeout=40):
    """Execute CDP command and return stdout; '' on failure."""
    try:
        r = subprocess.run(
            ["node", "scripts/cdp.mjs"] + list(args),
            cwd=CDP_DIR, capture_output=True, text=True, timeout=timeout,
        )
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"[ERROR] CDP timeout: {' '.join(args)}", flush=True)
        return ""
    except Exception as e:
        print(f"[ERROR] CDP failed: {e}", flush=True)
        return ""


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_state(done):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(done), f)


def fetch_article(article):
    topic = article["topic"]
    folder = TOPIC_DIR.get(topic)
    if not folder:
        print("[SKIP] Unknown topic", topic, flush=True)
        return False

    date = article["date"].replace("-", "")
    title = re.sub(r"[⭐★½\s]+", "", article["title"]).strip()[:80]
    title = re.sub(r'[<>:"/\\|?*]', "_", title)
    fname = f"{date}_{title}.md"
    fpath = os.path.join(BASE_OUT, folder, fname)

    if os.path.exists(fpath):
        print(f"[SKIP] Already exists: {fname}", flush=True)
        return False

    print(f"[FETCH] {article['date']} | {topic} | {article['title'][:60]}", flush=True)

    # 1. Navigate
    cdp("nav", TAB_ID, article["href"])
    time.sleep(4)

    # 2. Metadata
    meta_json = cdp("eval", TAB_ID,
                    'JSON.stringify({title:document.querySelector(".article-title").textContent.trim()})')
    try:
        meta = json.loads(meta_json)
        meta_title = meta.get("title") or article["title"]
    except Exception:
        meta_title = article["title"]

    # 3. HTML content
    html = cdp("html", TAB_ID, ".prose")
    if not html:
        print(f"[WARN] Empty HTML for {article['href']}", flush=True)
        return False

    # 4. Clean -> markdown
    try:
        result = subprocess.run(
            ["python3", CLEANER], input=html,
            capture_output=True, text=True, timeout=30,
        )
        body = result.stdout.strip()
    except Exception as e:
        print(f"[ERROR] Cleaner failed: {e}", flush=True)
        return False
    if not body:
        print(f"[WARN] Empty cleaned content for {article['href']}", flush=True)
        return False

    # 5. Save
    md = f"# {meta_title}\n\n**日期**: {article['date']}\n\n---\n\n{body}"
    # ensure folder exists
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"[OK] Saved: {fname}", flush=True)
    return True


def main():
    if not os.path.exists(LIST_FILE):
        print(f"[ERROR] List file not found: {LIST_FILE}", flush=True)
        sys.exit(1)

    with open(LIST_FILE) as f:
        articles = json.load(f)

    done = load_state()
    print(f"Loaded {len(articles)} pending articles, {len(done)} already done", flush=True)

    fetched = skipped = failed = 0
    remaining = [a for a in articles if a["href"] not in done]

    for i, article in enumerate(remaining, 1):
        href = article["href"]
        ok = fetch_article(article)
        if ok:
            fetched += 1
        else:
            failed += 1
            done.add(href)  # don't retry a hard failure in this run
        done.add(href)
        save_state(done)
        print(f"[PROGRESS] {i}/{len(remaining)} fetched={fetched} failed={failed}", flush=True)

        if i < len(remaining):
            print(f"[WAIT] Next in {DELAY}s...", flush=True)
            time.sleep(DELAY)

    print(f"[DONE] fetched={fetched} failed={failed} skipped_already={skipped}", flush=True)


if __name__ == "__main__":
    main()