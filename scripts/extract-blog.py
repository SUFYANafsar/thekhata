#!/usr/bin/env python3
"""
Phase 5: Bulk extract all 51 blog posts → .mdx files in src/content/blog/
Skip posts that already exist (re-run safe).
"""

import os
import re
import sys

SOURCE = "/Users/macbookpro14m1pro/Desktop/spartanaccounts/SpartanTech.org"
DEST   = "/Users/macbookpro14m1pro/Desktop/splendid-astro/src/content/blog"


def is_blog_post(html: str) -> bool:
    return bool(re.search(r'<body[^>]*single single-post', html))


def extract_meta(html: str, slug: str) -> dict:
    title = re.search(r'<title>(.*?)</title>', html)
    title = title.group(1).strip() if title else slug

    # Strip " - Spartan Accounts" suffix from title
    title = re.sub(r'\s*[-–]\s*Spartan Accounts\s*$', '', title).strip()

    desc = re.search(r'name="description"\s+content="([^"]*)"', html)
    if not desc:
        desc = re.search(r'content="([^"]*)"\s+name="description"', html)
    desc = desc.group(1).strip() if desc else ""

    og_image = re.search(r'property="og:image"\s+content="([^"]*)"', html)
    if not og_image:
        og_image = re.search(r'content="([^"]*)"\s+property="og:image"', html)
    og_image = og_image.group(1).strip() if og_image else ""
    og_image = re.sub(r'^https?://spartanaccounts\.pk', '', og_image)
    og_image = re.sub(r'^\.\./wp-content/', '/wp-content/', og_image)
    if og_image and not og_image.startswith('/'):
        og_image = '/wp-content/' + og_image.lstrip('wp-content/')

    published = re.search(r'article:published_time"\s+content="([^"]*)"', html)
    if not published:
        published = re.search(r'content="([^"]*)"\s+property="article:published_time"', html)
    published = published.group(1).strip() if published else ""

    modified = re.search(r'article:modified_time"\s+content="([^"]*)"', html)
    if not modified:
        modified = re.search(r'content="([^"]*)"\s+property="article:modified_time"', html)
    modified = modified.group(1).strip() if modified else ""

    return {
        "title": title,
        "description": desc,
        "og_image": og_image,
        "published": published,
        "modified": modified,
    }


def extract_body(html: str) -> str:
    start = html.find('<div id="et-main-area">')
    if start == -1:
        start = html.find('<div id="main-content">')
    if start == -1:
        return ""

    end = html.find('<footer class="et-l et-l--footer">')
    if end == -1:
        end = html.find('\t</footer>')
    if end == -1:
        end = html.rfind('</div>', 0, html.find('</body>'))

    return html[start:end].strip()


def fix_paths(html: str) -> str:
    # Remove base64 lazy-load placeholders
    html = re.sub(r'\s*src="data:image/gif;base64,[^"]*"', '', html)
    # Replace data-src with src (lazy loaded images)
    html = re.sub(r'data-src="(\.\./wp-content/)', r'src="/wp-content/', html)
    html = re.sub(r'data-src="(wp-content/)', r'src="/wp-content/', html)
    # Fix relative asset paths
    html = re.sub(r'(src|href)="\.\./wp-content/', r'\1="/wp-content/', html)
    html = re.sub(r'(src|href)="wp-content/', r'\1="/wp-content/', html)
    # Fix internal page links
    html = re.sub(r'href="([^"#:][^"/][^"]*)/index\.html"', r'href="/\1/"', html)
    html = re.sub(r'href="\.\./([^"]*)/index\.html"', r'href="/\1/"', html)
    html = re.sub(r'href="index\.html"', 'href="/"', html)
    html = re.sub(r'href="\.\./index\.html"', 'href="/"', html)
    return html


def escape_for_template(s: str) -> str:
    return s.replace('`', '&#96;').replace('${', '&#36;{')


def write_mdx(slug: str, meta: dict, body: str):
    out_path = os.path.join(DEST, slug + ".mdx")

    # Escape special chars in frontmatter strings
    def fm(s):
        return s.replace('"', '&quot;')

    safe_body = escape_for_template(body)

    content = f'''---
title: "{fm(meta['title'])}"
description: "{fm(meta['description'])}"
slug: "{slug}"
canonical: "/{slug}/"
ogImage: "{meta['og_image']}"
published: "{meta['published']}"
modified: "{meta['modified']}"
---

<div class="entry-content" set:html={{`{safe_body}`}} />
'''

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    os.makedirs(DEST, exist_ok=True)

    # Collect all blog post slugs from source
    slugs = []
    for name in sorted(os.listdir(SOURCE)):
        src_file = os.path.join(SOURCE, name, "index.html")
        if not os.path.isfile(src_file):
            continue
        try:
            with open(src_file, encoding="utf-8", errors="replace") as f:
                html = f.read()
            if is_blog_post(html):
                slugs.append((name, html))
        except Exception:
            continue

    print(f"Found {len(slugs)} blog posts\n")

    ok = skipped = errors = 0

    for slug, html in slugs:
        out_path = os.path.join(DEST, slug + ".mdx")

        if os.path.exists(out_path) and slug == "the-benefits-of-cloud-based-accounting-software-for-small-businesses":
            print(f"  SKIP (already exists): {slug}")
            skipped += 1
            continue

        try:
            meta = extract_meta(html, slug)
            body = extract_body(html)
            body = fix_paths(body)

            if not body:
                print(f"  WARN (empty body): {slug}")

            write_mdx(slug, meta, body)
            print(f"  ✓ {slug}")
            ok += 1

        except Exception as e:
            print(f"  ERROR {slug}: {e}")
            errors += 1

    print(f"\nDone: {ok} written, {skipped} skipped, {errors} errors")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
