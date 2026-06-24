#!/usr/bin/env python3
"""
Clean .prose HTML from io.gf.com.cn into readable markdown.

Usage:
    # Pipe HTML from cdp.mjs:
    node scripts/cdp.mjs html <TAB> '.prose' | python3 clean_article.py

The HTML contains:
  - Standard <p>, <h2>, <h3>, <blockquote>, <ul>, <ol>, <table> tags
  - KaTeX math rendered as <span class="katex-html"> (visual noise) +
    <math> MathML (semantic text)
  - <a> links to arxiv papers

Strategy:
  1. Remove katex-html spans (visual rendering fragments)
  2. Extract text from MathML
  3. Strip all HTML tags
  4. Clean up whitespace
"""

import re, sys, html as html_mod


def clean_prose_html(raw_html: str) -> str:
    """Clean .prose div HTML into readable text."""
    text = raw_html

    # Step 1: Remove katex-html blocks (visual noise, hundreds of single-char spans)
    text = re.sub(
        r'<span class="katex-html"[^>]*>.*?</span>\s*</span>',
        '',
        text,
        flags=re.DOTALL,
    )

    # Step 2: Collapse katex wrappers - keep only MathML
    # Remove orphaned katex spans (their content was already removed)
    text = re.sub(r'<span class="katex"[^>]*>\s*</span>', '', text)
    text = re.sub(r'<span class="katex-display"[^>]*>\s*</span>', '', text)

    # Step 3: Convert MathML to readable text
    def mathml_to_text(match):
        inner = match.group(1)
        return re.sub(r'<[^>]+>', '', inner)

    text = re.sub(
        r'<math[^>]*>(.*?)</math>',
        mathml_to_text,
        text,
        flags=re.DOTALL,
    )

    # Step 4: Handle <blockquote> — wrap in markdown quote style
    text = re.sub(r'</?blockquote>', '\n', text)

    text = re.sub(r'</?p>', '\n', text)

    text = re.sub(r'</?ul>', '\n', text)
    text = re.sub(r'</?ol>', '\n', text)

    # Step 5: Handle list items — convert <li> to bullets
    text = re.sub(
        r'<li[^>]*>(.*?)</li>',
        lambda m: '- ' + re.sub(r'<[^>]+>', '', m.group(1)),
        text,
        flags=re.DOTALL,
    )

    # Step 6: Handle headings — h2→##, h3→###, etc
    def heading_to_md(match):
        level = int(match.group(1))
        content = re.sub(r'<[^>]+>', '', match.group(2).strip())
        return f'\n{"#" * level} {content}\n'

    text = re.sub(
        r'<h(\d)[^>]*>(.*?)</h\1>',
        heading_to_md,
        text,
        flags=re.DOTALL,
    )

    # Step 7: Strip all remaining HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)

    # Step 8: Decode HTML entities
    text = html_mod.unescape(text)

    # Step 9: Clean up whitespace
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # Step 10: Merge broken lines (lines that are continuation of previous)
    # A line is a continuation if the previous line doesn't end with sentence end
    merged = []
    for l in lines:
        if (
            merged
            and merged[-1]
            and not merged[-1].endswith(('.', '。', ':', '：', '!', '？', '?', '》', '）', ')', '"', '”'))
        ):
            merged[-1] += l
        else:
            merged.append(l)

    # Step 11: Remove blank duplicates and normalize spacing
    final = []
    for l in merged:
        # Collapse multiple spaces
        l = re.sub(r' {2,}', ' ', l)
        if l == '' and final and final[-1] == '':
            continue
        final.append(l)

    while final and final[-1].strip() == '':
        final.pop()

    return '\n'.join(final)


if __name__ == '__main__':
    raw = sys.stdin.read()
    print(clean_prose_html(raw))
