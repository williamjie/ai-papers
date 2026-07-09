#!/usr/bin/env python3
import json, re, os, subprocess, time, sys, signal

BASE = "/Users/zj/Documents/company_code/ai-papers"
CDP_DIR = os.path.expanduser("~/.agents/skills/chrome-cdp")
SKILL_DIR = os.path.join(BASE, ".claude/skills/io-gf-fetch")
CLEANER = os.path.join(SKILL_DIR, "scripts", "clean_article.py")
TAB = "6C10CC6E"
STATE_FILE = os.path.join(BASE, ".fetch_state.json")
LOG_FILE = os.path.join(BASE, "fetch.log")
INTERVAL = 120  # 2 minutes

def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, file=sys.stderr)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass

def cdp(*args, timeout=30):
    r = subprocess.run(
        ["node", "scripts/cdp.mjs"] + list(args),
        cwd=CDP_DIR,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return r.stdout.strip()

ARTICLE_JS = r'''(() => {
  let links = document.querySelectorAll("a"), seen = new Set(), arts = [];
  for (let a of links) {
    let h = a.href || "";
    if (h.includes("/blog/") && !seen.has(h)) {
      seen.add(h);
      let t = (a.textContent || "").trim().replace(/\s+/g, " ").substring(0, 120);
      let topic = h.includes("qfin") ? "Q-Fin" : h.includes("cncf") ? "CNCF" : "AI";
      let dm = h.match(/blog\/(?:qfin-|cncf-)?(\d{4}-\d{2}-\d{2})/);
      arts.push({ href: h, title: t, date: dm ? dm[1] : "", topic });
    }
  }
  arts.sort((a, b) => b.date.localeCompare(a.date) || a.href.localeCompare(b.href));
  return JSON.stringify({ count: arts.length, articles: arts });
})()'''

def get_articles():
    cdp("nav", TAB, "http://io.gf.com.cn/")
    time.sleep(2)
    out = cdp("eval", TAB, ARTICLE_JS)
    return json.loads(out)

def clean_filename(title):
    ct = re.sub(r'[⭐★½\s]+', '', title).strip()[:80]
    ct = re.sub(r'[<>:"/\\|?*]', '_', ct)
    return ct

def topic_dir(topic):
    return {"AI": "ai-ml", "Q-Fin": "q-fin", "CNCF": "cncf"}.get(topic, "ai-ml")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"fetched_urls": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def fetch_article(article, state):
    url = article["href"]
    topic = article["topic"]
    date = article["date"]
    title = article["title"]
    
    outdir = os.path.join(BASE, topic_dir(topic))
    os.makedirs(outdir, exist_ok=True)
    
    dp = date.replace("-", "")
    ct = clean_filename(title)
    fname = f"{dp}_{ct}.md"
    fpath = os.path.join(outdir, fname)
    
    if os.path.exists(fpath):
        return f"SKIP: {fname}"
    
    try:
        cdp("nav", TAB, url)
        time.sleep(3)
        
        meta_str = cdp("eval", TAB, 'JSON.stringify({title:document.querySelector(".article-title").textContent.trim()})')
        meta = json.loads(meta_str)
        real_title = meta.get("title", title)
        
        html_content = cdp("html", TAB, ".prose")
        
        cleaned = subprocess.run(
            ["python3", CLEANER],
            input=html_content,
            capture_output=True,
            text=True
        ).stdout
        
        md = f"# {real_title}\n\n**日期**: {date}\n\n---\n\n{cleaned}"
        with open(fpath, "w") as f:
            f.write(md)
        
        cdp("nav", TAB, "http://io.gf.com.cn/")
        state.setdefault("fetched_urls", []).append(url)
        return f"FETCHED: {fname}"
    except Exception as e:
        try:
            cdp("nav", TAB, "http://io.gf.com.cn/")
        except:
            pass
        return f"FAILED: {fname} - {e}"

def main():
    log(f"Starting io-gf fetcher (every {INTERVAL}s)")
    
    def handle_stop(signum, frame):
        log("Stopped by signal.")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)
    
    save_state(load_state())
    
    while True:
        try:
            state = load_state()
            data = get_articles()
            articles = data.get("articles", [])
            fetched = set(state.get("fetched_urls", []))
            
            new_articles = [a for a in articles if a["href"] not in fetched]
            
            if not new_articles:
                log("No new articles. Waiting...")
            else:
                article = new_articles[0]
                result = fetch_article(article, state)
                log(result)
                save_state(state)
            
            time.sleep(INTERVAL)
        except KeyboardInterrupt:
            log("Stopped by user.")
            sys.exit(0)
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
