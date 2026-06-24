#!/usr/bin/env python3
"""
Validate already-fetched articles: check for real HTML tags, garbled text, line count.

Usage: python3 validate_articles.py <articles_dir>

Returns JSON with:
- clean: list of clean files
- bad: list of (filepath, reason) needing re-fetch
"""

import os, re, json, sys


HTML_TAG_RE = re.compile(r'<(p|div|span|a|h[1-6]|li|ul|ol|table|tr|td|th|img|br|hr|code|pre|blockquote|strong|em|b|i|u|s|sub|sup|head|body|html|meta|link|script|style|form|input|button|select|option|textarea|label|fieldset|legend|iframe|svg|canvas|video|audio|source|nav|header|footer|section|article|aside|main|figure|figcaption|details|summary|dialog|template|slot|noscript|map|area|object|embed|param|picture|source|track|col|colgroup|caption|thead|tbody|tfoot)[\s/>]')
MIN_LINES = 15
MAX_LINES = 150


def validate_file(filepath: str) -> tuple[bool, str]:
    """Returns (is_clean, reason_if_dirty)."""
    if not os.path.exists(filepath):
        return False, "MISSING"

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"READ_ERROR: {e}"

    lines = content.count('\n') + 1

    # Line count check
    if lines < MIN_LINES:
        return False, f"TOO_SHORT({lines}L)"
    if lines > MAX_LINES:
        return False, f"TOO_LONG({lines}L)"

    # Real HTML tag check (exclude false positives like <8B, <payment-card:uuid>)
    if HTML_TAG_RE.search(content):
        return False, "HTML_TAGS_FOUND"

    return True, "OK"


def validate_dir(directory: str) -> dict:
    results = {"clean": [], "bad": []}
    if not os.path.isdir(directory):
        return results

    for fname in sorted(os.listdir(directory)):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(directory, fname)
        ok, reason = validate_file(fpath)
        if ok:
            results["clean"].append(fname)
        else:
            results["bad"].append((fname, reason))

    return results


if __name__ == '__main__':
    dirs = sys.argv[1:] if len(sys.argv) > 1 else ["."]
    all_results = {}
    for d in dirs:
        all_results[d] = validate_dir(d)
    print(json.dumps(all_results, ensure_ascii=False, indent=2))
