#!/usr/bin/env python3
"""
Fix relative url() references in extracted per-page CSS files.
When inline <style> blocks are extracted to /css/pages/*.css, relative paths
like url(wp-content/...) break because they resolve relative to /css/pages/
instead of the site root. Prefix them with /.
"""

import os
import re

CSS_DIR = '/Users/macbookpro14m1pro/Desktop/splendid-astro/public/css/pages'

def fix_urls(css):
    def rewrite(m):
        quote = m.group(1) or m.group(3) or ''
        path  = m.group(2) or m.group(4) or m.group(5)
        end_quote = quote  # same quote char to close

        # Leave data URIs, absolute URLs, root-relative, and fragment refs alone
        if (path.startswith('data:') or
            path.startswith('http') or
            path.startswith('/') or
            path.startswith('#') or
            path.startswith("'")):
            return m.group(0)

        # Prefix with /
        return f'url({quote}/{path}{end_quote})'

    # Match url("..."), url('...'), url(...)
    pattern = r"""url\((['"])(.*?)\1\)|url\(('.*?')\)|url\(([^'"][^)]*)\)"""
    return re.sub(pattern, rewrite, css)

fixed = 0
for fname in os.listdir(CSS_DIR):
    if not fname.endswith('.css'):
        continue
    fpath = os.path.join(CSS_DIR, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        original = f.read()
    updated = fix_urls(original)
    if updated != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(updated)
        fixed += 1
        print(f'Fixed: {fname}')

print(f'\nDone. {fixed} files updated.')
