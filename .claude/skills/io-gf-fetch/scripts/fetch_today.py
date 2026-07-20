#!/usr/bin/env python3
"""
Fetch today's articles from io.gf.com.cn and save as markdown files.
Runs silently in background. Logs to /tmp/fetch_today.log
"""
import os, re, subprocess, time, sys
from urllib import request as urllib_request

BASE = 'http://io.gf.com.cn'
OUT_DIRS = {'AI': 'ai-ml', 'Q-Fin': 'q-fin', 'CNCF': 'cncf'}
CLEANER = os.path.join(os.path.dirname(__file__), 'clean_article.py')
TARGET_DATE = time.strftime('%Y-%m-%d')
LOG = '/tmp/fetch_today.log'

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(f'{time.strftime("%H:%M:%S")} {msg}\n')

def fetch(url):
    req = urllib_request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib_request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', errors='ignore')

def clean(html):
    p = subprocess.run(['python3', CLEANER], input=html, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr)
    return p.stdout

def slugify(title, max_len=80):
    t = re.sub(r'[⭐★½\s]+', '', title).strip()[:max_len]
    t = re.sub(r'[<>:"/\\|?*]', '_', t)
    return t.strip('_') or 'untitled'

def main():
    log(f'=== Starting fetch for {TARGET_DATE} ===')
    
    # Fetch homepage
    log('Fetching homepage...')
    home = fetch(BASE)
    
    # Find date block for target date
    date_header = f'<h2 class="date-divider" data-date="{TARGET_DATE}"'
    pos = home.find(date_header)
    if pos == -1:
        log(f'No articles found for {TARGET_DATE}')
        return
    
    # Extract article cards from this date block
    articles = []
    card_pattern = re.compile(
        r'data-path="(/blog/[^"]+)"[^>]*>\s*<span[^>]*>([^<]+)</span>\s*<a href="([^"]+)"[^>]*>([^<]+)</a>',
        re.DOTALL
    )
    for m in card_pattern.finditer(home[pos:]):
        href = m.group(3)
        title = m.group(4).strip()
        
        # Skip HF Daily articles
        if 'hf-' in href:
            continue
        
        # Determine topic from href
        if 'qfin' in href:
            topic = 'Q-Fin'
        elif 'cncf' in href:
            topic = 'CNCF'
        else:
            topic = 'AI'
        
        # Extract date from href
        dm = re.search(r'blog/(?:qfin-|cncf-)?(\d{4}-\d{2}-\d{2})', href)
        date = dm.group(1) if dm else TARGET_DATE
        
        articles.append({
            'href': href,
            'title': title,
            'date': date,
            'topic': topic,
            'url': BASE + href,
        })
    
    # Deduplicate by href
    seen = set()
    unique = []
    for a in articles:
        if a['href'] not in seen:
            seen.add(a['href'])
            unique.append(a)
    articles = unique
    
    log(f'Found {len(articles)} articles for {TARGET_DATE}')
    
    # Deduplicate against existing files and prepare fetch list
    to_fetch = []
    for a in articles:
        dp = a['date'].replace('-', '')
        ct = slugify(a['title'])
        fname = f"{dp}_{ct}.md"
        folder = OUT_DIRS[a['topic']]
        fpath = os.path.join(folder, fname)
        if os.path.exists(fpath):
            log(f'SKIP exists: {fpath}')
        else:
            to_fetch.append({**a, 'fpath': fpath, 'fname': fname})
    
    log(f'Need to fetch: {len(to_fetch)} articles')
    
    # Fetch each article with 30s delay
    for i, a in enumerate(to_fetch, 1):
        log(f'[{i}/{len(to_fetch)}] Fetching {a["url"]}')
        try:
            html = fetch(a['url'])
            # Extract .prose content
            m = re.search(r'<div class="prose"[^>]*>(.*?)</div>\s*</article>', html, re.DOTALL | re.IGNORECASE)
            if not m:
                m = re.search(r'<div class="prose"[^>]*>(.*)', html, re.DOTALL | re.IGNORECASE)
            prose = m.group(1) if m else html
            
            # Extract title from page
            title_match = re.search(r'<h1 class="article-title"[^>]*>(.*?)</h1>', html, re.DOTALL | re.IGNORECASE)
            if title_match:
                page_title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
            else:
                page_title = a['title']
            
            body = clean(prose)
            md = f"# {page_title}\n\n**日期**: {a['date']}\n\n---\n\n{body}"
            os.makedirs(os.path.dirname(a['fpath']), exist_ok=True)
            with open(a['fpath'], 'w', encoding='utf-8') as f:
                f.write(md)
            log(f'  -> Saved {a["fpath"]}')
        except Exception as e:
            log(f'  -> FAILED: {e}')
        
        if i < len(to_fetch):
            log(f'  -> sleeping 30s ...')
            time.sleep(30)
    
    log(f'=== Done. Fetched {len(to_fetch)} articles ===')

if __name__ == '__main__':
    main()
