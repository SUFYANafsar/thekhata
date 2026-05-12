#!/usr/bin/env python3
"""Fill blog MDX frontmatter wpPostId + etInlineCss from article HTML + static export."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG_DIR = ROOT / "src" / "content" / "blog"
STATIC_ROOT = Path(
    "/Users/macbookpro14m1pro/Desktop/splendidaccounts/splendidaccounts.pk"
)


def extract_wp_post_id(text: str) -> int | None:
    m = re.search(r'<article[^>]*id="post-(\d+)"', text)
    return int(m.group(1)) if m else None


def extract_et_inline_css(static_html: str) -> str | None:
    """Return root-relative /wp-content/litespeed/css/....css from static head."""
    pat_divi = re.compile(
        r'et-divi-customizer-global-cached-inline-styles[^>]+href=[\'"]([^\'"]+)[\'"]',
        re.I,
    )
    pat_core = re.compile(
        r'et-core-unified-\d+-cached-inline-styles[^>]+href=[\'"]([^\'"]+)[\'"]',
        re.I,
    )
    for pat in (pat_divi, pat_core):
        m = pat.search(static_html)
        if not m:
            continue
        href = m.group(1)
        href = href.split("?", 1)[0]
        if href.startswith("../wp-content/"):
            return "/" + href.removeprefix("../")
        if href.startswith("/wp-content/"):
            return href
    return None


def upsert_frontmatter(text: str, wp_post_id: int, et_inline: str | None) -> str:
    m = re.match(r"^(---\n)(.*?)(\n---\n)", text, re.DOTALL)
    if not m:
        raise ValueError("missing frontmatter --- block")
    inner = m.group(2)
    inner = re.sub(r"^wpPostId:.*\n", "", inner, flags=re.MULTILINE)
    inner = re.sub(r"^etInlineCss:.*\n", "", inner, flags=re.MULTILINE)
    inner = inner.rstrip("\n") + f"\nwpPostId: {wp_post_id}\n"
    if et_inline:
        inner += f'etInlineCss: "{et_inline}"\n'
    return m.group(1) + inner + m.group(3) + text[m.end() :]


def main() -> int:
    if not BLOG_DIR.is_dir():
        print("no blog dir", file=sys.stderr)
        return 1
    updated = 0
    for path in sorted(BLOG_DIR.glob("*.mdx")):
        raw = path.read_text(encoding="utf-8")
        fm = re.match(r"^---\n.*?\n---\n", raw, re.DOTALL)
        if not fm:
            continue
        slug_m = re.search(r"^slug:\s*[\"']?([^\"'\n]+)[\"']?\s*$", fm.group(0), re.MULTILINE)
        slug = slug_m.group(1).strip("\"'") if slug_m else path.stem
        wpid = extract_wp_post_id(raw)
        if not wpid:
            print("skip (no post id):", path.name)
            continue
        static_path = STATIC_ROOT / slug / "index.html"
        et_inline = None
        if static_path.is_file():
            et_inline = extract_et_inline_css(static_path.read_text(encoding="utf-8", errors="ignore"))
        new_raw = upsert_frontmatter(raw, wpid, et_inline)
        if new_raw != raw:
            path.write_text(new_raw, encoding="utf-8")
            updated += 1
            print("updated", path.name, "wpPostId", wpid, "etInlineCss", et_inline or "(none)")
    print("done, files touched:", updated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
