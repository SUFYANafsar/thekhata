#!/usr/bin/env python3
"""
Generate Astro pages for author and category archive pages from HTTrack mirror.
"""

import os
import re

MIRROR = '/Users/macbookpro14m1pro/Desktop/splendidaccounts/splendidaccounts.pk'
ASTRO_PAGES = '/Users/macbookpro14m1pro/Desktop/splendid-astro/src/pages'

STYLE_IDS = [
    'et-critical-inline-css',
    'divi-style-inline-inline-css',
    'divi-dynamic-critical-inline-css',
    'minerva-kb/css-inline-css',
    'global-styles-inline-css',
]

def extract_meta(html):
    title = re.search(r'<title>(.*?)</title>', html)
    desc  = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)', html)
    canon = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']*)', html)
    bc    = re.search(r'<body[^>]+class=["\']([^"\']*)', html)
    return {
        'title':       (title.group(1)  if title  else '').replace('"', '&quot;'),
        'description': (desc.group(1)   if desc   else '').replace('"', '&quot;'),
        'canonical':   (canon.group(1)  if canon  else ''),
        'body_class':  (bc.group(1)     if bc     else ''),
    }

def extract_body(html):
    """Extract content between #et-main-area open and the footer nav."""
    m = re.search(r'(<div\s+id=["\']et-main-area["\'].*)', html, re.DOTALL)
    if not m:
        return ''
    chunk = m.group(1)
    cut = re.search(r'<div\s+id=["\']et-footer-nav["\']', chunk)
    if cut:
        chunk = chunk[:cut.start()]
    # Remove the broken ET dynamic-CSS loader script (it crashes because
    # divi-style-inline-inline-css element doesn't exist in our layout).
    chunk = re.sub(
        r'<script[^>]*>\s*\(function\s*\(\s*\)\s*\{[^}]*var\s+file\s*=\s*\[',
        '<!-- et-css-loader removed -->',
        chunk, flags=re.DOTALL
    )
    # Fully remove those script blocks
    chunk = re.sub(
        r'<script[^>]*>\s*\(function\s*\(\)\s*\{[\s\S]*?var file\s*=[\s\S]*?</script>',
        '',
        chunk
    )
    return chunk.strip()

def extract_inline_css(html):
    parts = []
    for sid in STYLE_IDS:
        pattern = r'<style[^>]+id=["\']' + re.escape(sid) + r'["\'][^>]*>(.*?)</style>'
        m = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
        if m:
            content = m.group(1).strip()
            if content:
                parts.append('/* %s */\n%s' % (sid, content))
    return '\n\n'.join(parts)

def fix_css_urls(css):
    def rewrite(m):
        quote = m.group(1) or ''
        path  = m.group(2) or m.group(3) or ''
        if path.startswith(('data:', 'http', '/', '#', "'")):
            return m.group(0)
        return 'url(%s/%s%s)' % (quote, path, quote)
    return re.sub(r"url\((['\"])(.*?)\1\)|url\(([^'\"][^)]*)\)", rewrite, css)

def extract_et_cache_links(html):
    """Extract et-cache CSS hrefs from <link> tags (relative paths from mirror)."""
    links = re.findall(r'<link[^>]+href=["\']([^"\']*et-cache[^"\']*)["\']', html)
    out = []
    for href in links:
        # Strip query string
        href = href.split('?')[0]
        # Convert relative ../../wp-content/... to /wp-content/...
        href = re.sub(r'^(?:\.\./)+', '/', href)
        out.append(href)
    return out

def archive_body_class(body_class):
    """Keep only the relevant layout classes for the body attribute."""
    keep = {
        'et_right_sidebar', 'et_left_sidebar', 'et_no_sidebar',
        'et_full_width_page', 'archive', 'author', 'category', 'tag',
        'et_pb_pagebuilder_layout',
    }
    parts = body_class.split()
    filtered = [p for p in parts if p in keep or p.startswith('author-') or p.startswith('category-') or p.startswith('tag-')]
    return ' '.join(filtered) if filtered else 'et_right_sidebar'

# ─── Page list ────────────────────────────────────────────────────────────────

PAGES = []

# Authors
author_dir = os.path.join(MIRROR, 'author')
for slug in sorted(os.listdir(author_dir)):
    slug_path = os.path.join(author_dir, slug)
    if not os.path.isdir(slug_path):
        continue
    index_html = os.path.join(slug_path, 'index.html')
    if os.path.exists(index_html):
        PAGES.append({
            'html':      index_html,
            'astro_dir': os.path.join(ASTRO_PAGES, 'author', slug),
            'css_slug':  'author-' + slug,
            'url':       '/author/%s/' % slug,
        })
    page_dir = os.path.join(slug_path, 'page')
    if os.path.isdir(page_dir):
        for pn in sorted(os.listdir(page_dir)):
            pn_html = os.path.join(page_dir, pn, 'index.html')
            if os.path.exists(pn_html):
                PAGES.append({
                    'html':      pn_html,
                    'astro_dir': os.path.join(ASTRO_PAGES, 'author', slug, 'page', pn),
                    'css_slug':  'author-%s-page-%s' % (slug, pn),
                    'url':       '/author/%s/page/%s/' % (slug, pn),
                })

# Categories
cat_dir = os.path.join(MIRROR, 'category')
for slug in sorted(os.listdir(cat_dir)):
    slug_path = os.path.join(cat_dir, slug)
    if not os.path.isdir(slug_path):
        continue
    index_html = os.path.join(slug_path, 'index.html')
    if os.path.exists(index_html):
        PAGES.append({
            'html':      index_html,
            'astro_dir': os.path.join(ASTRO_PAGES, 'category', slug),
            'css_slug':  'category-' + slug,
            'url':       '/category/%s/' % slug,
        })
    page_dir = os.path.join(slug_path, 'page')
    if os.path.isdir(page_dir):
        for pn in sorted(os.listdir(page_dir)):
            pn_html = os.path.join(page_dir, pn, 'index.html')
            if os.path.exists(pn_html):
                PAGES.append({
                    'html':      pn_html,
                    'astro_dir': os.path.join(ASTRO_PAGES, 'category', slug, 'page', pn),
                    'css_slug':  'category-%s-page-%s' % (slug, pn),
                    'url':       '/category/%s/page/%s/' % (slug, pn),
                })

# ─── Generate ─────────────────────────────────────────────────────────────────

CSS_OUT = '/Users/macbookpro14m1pro/Desktop/splendid-astro/public/css/pages'
os.makedirs(CSS_OUT, exist_ok=True)

for page in PAGES:
    with open(page['html'], 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()

    meta        = extract_meta(html)
    body        = extract_body(html)
    css         = fix_css_urls(extract_inline_css(html))
    et_links    = extract_et_cache_links(html)
    body_class  = archive_body_class(meta['body_class'])

    # Write per-page CSS
    if css:
        with open(os.path.join(CSS_OUT, page['css_slug'] + '.css'), 'w', encoding='utf-8') as f:
            f.write(css + '\n')

    canon = page['url']
    if meta['canonical'].startswith('https://splendidaccounts.pk'):
        canon = meta['canonical'].replace('https://splendidaccounts.pk', '')

    title = meta['title'] or 'Splendid Accounts'
    desc  = meta['description'] or 'Splendid Accounts - ERP software for Pakistan businesses.'

    head_links = ''
    if css:
        head_links += '\n    <link rel="stylesheet" href="/css/pages/%s.css" />' % page['css_slug']
    for href in et_links:
        head_links += '\n    <link rel="stylesheet" href="%s" media="all" />' % href

    depth = page['astro_dir'].replace(ASTRO_PAGES + '/', '').count('/') + 2
    layout_import = '../' * depth + 'layouts/PageLayout.astro'

    astro = '''---
import PageLayout from '%s'
const body = `%s`
---
<PageLayout
  title="%s"
  description="%s"
  canonical="%s"
  bodyClass="%s"
>
  <Fragment slot="head">%s
  </Fragment>
  <div set:html={body} />
</PageLayout>
''' % (
        layout_import,
        body.replace('`', '\\`').replace('${', '\\${'),
        title,
        desc,
        canon,
        body_class,
        head_links,
    )

    os.makedirs(page['astro_dir'], exist_ok=True)
    with open(os.path.join(page['astro_dir'], 'index.astro'), 'w', encoding='utf-8') as f:
        f.write(astro)

    print('OK  %-45s  bodyClass=%s' % (page['url'], body_class))
