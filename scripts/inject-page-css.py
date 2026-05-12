#!/usr/bin/env python3
"""
Add per-page critical CSS link to each Astro page's head slot.
The CSS files were extracted by extract-inline-css.py.
"""

import os
import re

PAGES_DIR = '/Users/macbookpro14m1pro/Desktop/splendid-astro/src/pages'
CSS_DIR = '/Users/macbookpro14m1pro/Desktop/splendid-astro/public/css/pages'

# Map: relative astro file path -> css slug
FILE_SLUG_MAP = {
    'index.astro': '__home__',
    'accounting/index.astro': 'accounting',
    'become-our-partner/index.astro': 'become-our-partner',
    'book-stores-software/index.astro': 'book-stores-software',
    'computer-accessories-software/index.astro': 'computer-accessories-software',
    'contact/index.astro': 'contact',
    'customer-portal-app/index.astro': 'customer-portal-app',
    'distribution-wholesale-software/index.astro': 'distribution-wholesale-software',
    'ecommerce-accounting/index.astro': 'ecommerce-accounting',
    'electronics-appliances-software/index.astro': 'electronics-appliances-software',
    'fbr-digital-invoicing-software/index.astro': 'fbr-digital-invoicing-software',
    'free-trial/index.astro': 'free-trial',
    'garment-shop-software/index.astro': 'garment-shop-software',
    'inventory/index.astro': 'inventory',
    'inventory-management-system/index.astro': 'inventory-management-system',
    'manufacturing/index.astro': 'manufacturing',
    'online-crm-system/index.astro': 'online-crm-system',
    'online-pos-fbr-integration/index.astro': 'online-pos-fbr-integration',
    'order-booking-app/index.astro': 'order-booking-app',
    'point-of-sale/index.astro': 'point-of-sale',
    'pricing-plan/index.astro': 'pricing-plan',
    'privacy-policy/index.astro': 'privacy-policy',
    'purchases/index.astro': 'purchases',
    'reporting/index.astro': 'reporting',
    'restaurant-software/index.astro': 'restaurant-software',
    'restaurants-bakers-software/index.astro': 'restaurants-bakers-software',
    'retail-stores-software/index.astro': 'retail-stores-software',
    'sales/index.astro': 'sales',
    'sales-tracking-app/index.astro': 'sales-tracking-app',
    'shoe-stores-software/index.astro': 'shoe-stores-software',
    'splendid-invoices-app/index.astro': 'splendid-invoices-app',
    'terms-and-conditions/index.astro': 'terms-and-conditions',
    'user-data-deletion-request/index.astro': 'user-data-deletion-request',
    'video/index.astro': 'video',
}

LINK_PATTERN = re.compile(r'href="/css/pages/')

for rel_path, slug in FILE_SLUG_MAP.items():
    css_file = os.path.join(CSS_DIR, f'{slug}.css')
    if not os.path.exists(css_file):
        print(f'NO CSS FILE: {slug}')
        continue

    astro_file = os.path.join(PAGES_DIR, rel_path)
    if not os.path.exists(astro_file):
        print(f'NO ASTRO FILE: {rel_path}')
        continue

    with open(astro_file, 'r', encoding='utf-8') as f:
        content = f.read()

    css_href = f'/css/pages/{slug}.css'
    css_link = f'<link rel="stylesheet" href="{css_href}" />'

    # Already injected?
    if f'href="{css_href}"' in content:
        print(f'SKIP (already injected): {rel_path}')
        continue

    # Insert as first child of the Fragment slot="head"
    new_content = content.replace(
        '<Fragment slot="head">',
        f'<Fragment slot="head">\n    {css_link}',
        1  # only first occurrence
    )

    if new_content == content:
        print(f'NO CHANGE (no slot="head" found?): {rel_path}')
        continue

    with open(astro_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f'OK  {rel_path}')
