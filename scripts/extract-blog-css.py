#!/usr/bin/env python3
import re, os

MIRROR = '/Users/macbookpro14m1pro/Desktop/splendidaccounts/splendidaccounts.pk'
OUT_DIR = '/Users/macbookpro14m1pro/Desktop/splendid-astro/public/css/pages'
STYLE_IDS = ['et-critical-inline-css','divi-style-inline-inline-css','divi-dynamic-critical-inline-css','minerva-kb/css-inline-css','global-styles-inline-css']

URL_RE = re.compile(r'url\((["\'])(.*?)\1\)|url\(([^"\'#][^)]*)\)')

def fix_urls(css):
    def rewrite(m):
        if m.group(1):
            q, path = m.group(1), m.group(2)
        else:
            q, path = '', m.group(3)
        if path.startswith(('data:','http','/','')):
            return m.group(0)
        return 'url(%s/%s%s)' % (q, path, q)
    return URL_RE.sub(rewrite, css)

def extract(src_path):
    with open(src_path, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    parts = []
    for sid in STYLE_IDS:
        pattern = r'<style[^>]+id=["\']' + re.escape(sid) + r'["\'][^>]*>(.*?)</style>'
        m = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
        if m:
            content = m.group(1).strip()
            if content:
                parts.append('/* %s */\n%s' % (sid, content))
    return fix_urls('\n\n'.join(parts))

# Blog index and pagination pages
PAGES = {
    'blog': 'blog/index.html',
    'blog-page-2': 'blog/page/2/indexf83b.html',
    'blog-page-3': 'blog/page/3/indexf83b.html',
    'blog-page-4': 'blog/page/4/indexf83b.html',
    'blog-page-5': 'blog/page/5/indexf83b.html',
    'knowledge-base': 'knowledge-base/index.html',
}

os.makedirs(OUT_DIR, exist_ok=True)
for slug, rel in PAGES.items():
    src = os.path.join(MIRROR, rel)
    if not os.path.exists(src):
        print('MISSING: %s' % src)
        continue
    css = extract(src)
    if css:
        out = os.path.join(OUT_DIR, '%s.css' % slug)
        with open(out, 'w', encoding='utf-8') as f:
            f.write(css + '\n')
        print('OK  %-30s %d bytes' % (slug, len(css)))
    else:
        print('NO CSS: %s' % slug)
