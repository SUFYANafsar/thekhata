#!/usr/bin/env python3
"""
Phase 4: Bulk extract all WP static pages → .astro files
"""

import os
import re
import sys

SOURCE = "/Users/macbookpro14m1pro/Desktop/splendidaccounts/SpartanTech.org"
DEST   = "/Users/macbookpro14m1pro/Desktop/splendid-astro/src/pages"

# All WP "page" type slugs — skip homepage (index.astro done), blog (done), accounting (done)
PAGES = [
    "become-our-partner",
    "book-stores-software",
    "computer-accessories-software",
    "contact",
    "customer-portal-app",
    "distribution-wholesale-software",
    "ecommerce-accounting",
    "electronics-appliances-software",
    "fbr-digital-invoicing-software",
    "free-trial",
    "garment-shop-software",
    "inventory",
    "inventory-management-system",
    "knowledge-base",
    "manufacturing",
    "online-crm-system",
    "online-pos-fbr-integration",
    "order-booking-app",
    "point-of-sale",
    "pricing-plan",
    "privacy-policy",
    "purchases",
    "reporting",
    "restaurant-software",
    "restaurants-bakers-software",
    "retail-stores-software",
    "sales",
    "sales-tracking-app",
    "shoe-stores-software",
    "splendid-invoices-app",
    "terms-and-conditions",
    "user-data-deletion-request",
    "video",
    # unclassified — treat same as WP pages
    "accounting-software-pricing-plan",
    "garments-fashion-software",
    "online-accounting-software",
]


def extract_meta(html: str) -> dict:
    title = re.search(r'<title>(.*?)</title>', html)
    title = title.group(1).strip() if title else ""

    desc = re.search(r'name="description"\s+content="([^"]*)"', html)
    if not desc:
        desc = re.search(r'content="([^"]*)"\s+name="description"', html)
    desc = desc.group(1).strip() if desc else ""

    og_image = re.search(r'property="og:image"\s+content="([^"]*)"', html)
    if not og_image:
        og_image = re.search(r'content="([^"]*)"\s+property="og:image"', html)
    og_image = og_image.group(1).strip() if og_image else ""
    # normalise image path
    og_image = re.sub(r'^https?://splendidaccounts\.pk', '', og_image)
    og_image = re.sub(r'^\.\./wp-content/', '/wp-content/', og_image)
    if og_image and not og_image.startswith('/'):
        og_image = '/' + og_image

    # page-specific CSS from et-cache
    et_css = re.findall(r'href=["\']([^"\']*et-cache[^"\']*\.css)[^"\']*["\']', html)
    et_css_clean = []
    for c in et_css:
        c = re.sub(r'^\.\./wp-content/', '/wp-content/', c)
        if not c.startswith('/'):
            c = '/wp-content/' + c.lstrip('wp-content/')
        # strip query string
        c = c.split('?')[0]
        et_css_clean.append(c)

    return {
        "title": title,
        "description": desc.replace('"', '&quot;').replace('&#039;', "'"),
        "og_image": og_image,
        "et_css": et_css_clean,
    }


def extract_body(html: str) -> str:
    # Find start of main area
    start = html.find('<div id="et-main-area">')
    if start == -1:
        start = html.find('<div id="main-content">')
    if start == -1:
        return ""

    # Find start of footer
    end = html.find('<footer class="et-l et-l--footer">')
    if end == -1:
        end = html.find('</footer>')
    if end == -1:
        # fallback: everything to </div>\n</div> before </body>
        end = html.rfind('</div>', 0, html.find('</body>'))

    return html[start:end].strip()


def fix_paths(html: str) -> str:
    # Remove base64 lazy-load placeholders and replace data-src with src
    html = re.sub(r'\s*src="data:image/gif;base64,[^"]*"', '', html)
    html = re.sub(r'data-src="(\.\./wp-content/)', r'src="/wp-content/', html)
    html = re.sub(r'data-src="(wp-content/)', r'src="/wp-content/', html)
    # Fix src= and href= relative wp-content
    html = re.sub(r'(src|href)="\.\./wp-content/', r'\1="/wp-content/', html)
    html = re.sub(r'(src|href)="wp-content/', r'\1="/wp-content/', html)
    # Fix internal page links: href="slug/index.html" → href="/slug/"
    html = re.sub(r'href="([^"#:][^"/][^"]*)/index\.html"', r'href="/\1/"', html)
    html = re.sub(r'href="\.\./([^"]*)/index\.html"', r'href="/\1/"', html)
    # Fix root index.html link → /
    html = re.sub(r'href="index\.html"', 'href="/"', html)
    html = re.sub(r'href="\.\./index\.html"', 'href="/"', html)
    return html


def write_astro(slug: str, meta: dict, body: str):
    out_dir = os.path.join(DEST, slug)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "index.astro")

    # Depth from pages/ root: all these are one level deep
    layout_import = "../../layouts/PageLayout.astro"

    # Page-specific CSS links
    css_links = "\n    ".join(
        f'<link rel="stylesheet" href="{c}" media="all" />'
        for c in meta["et_css"]
    ) if meta["et_css"] else ""

    head_slot = ""
    if css_links:
        head_slot = f"""  <Fragment slot="head">
    {css_links}
  </Fragment>
"""

    # Escape backticks in body (safety)
    safe_body = body.replace('`', '&#96;').replace('${', '&#36;{')

    content = f"""---
import PageLayout from '{layout_import}'
const body = `{safe_body}`
---
<PageLayout
  title="{meta['title']}"
  description="{meta['description']}"
  canonical="/{slug}/"
  ogImage="{meta['og_image']}"
>
{head_slot}  <div set:html={{body}} />
</PageLayout>
"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    return out_path


def main():
    ok = 0
    skipped = 0
    errors = []

    for slug in PAGES:
        src_file = os.path.join(SOURCE, slug, "index.html")
        if not os.path.exists(src_file):
            print(f"  SKIP (no source): {slug}")
            skipped += 1
            continue

        try:
            with open(src_file, encoding="utf-8", errors="replace") as f:
                html = f.read()

            meta = extract_meta(html)
            body = extract_body(html)
            body = fix_paths(body)

            if not body:
                print(f"  WARN (empty body): {slug}")

            out = write_astro(slug, meta, body)
            print(f"  ✓ {slug}")
            ok += 1

        except Exception as e:
            print(f"  ERROR {slug}: {e}")
            errors.append(slug)

    print(f"\nDone: {ok} written, {skipped} skipped, {len(errors)} errors")
    if errors:
        print(f"Errors: {errors}")
        sys.exit(1)


if __name__ == "__main__":
    main()
