#!/usr/bin/env python3
"""
Remove files under public/wp-content/uploads that are not referenced from repo source
or from text assets (CSS/JS) outside uploads.
"""
from __future__ import annotations

import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPLOADS = ROOT / "public" / "wp-content" / "uploads"

# Scan these roots; skip anything under uploads and heavy/binary dirs.
SCAN_ROOTS = [ROOT / "src", ROOT / "public" / "css", ROOT / "public" / "wp-content"]

SKIP_SCAN_SUFFIXES = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".gif",
        ".ico",
        ".avif",
        ".bmp",
        ".tiff",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".pdf",
        ".zip",
        ".mp4",
        ".webm",
        ".mp3",
    }
)

# Match /wp-content/uploads/... or ../wp-content/uploads/... up to URL-safe end.
RE_UPLOAD = re.compile(
    r"(?:\.\./)?/?wp-content/uploads/([^\s\"'<>)\]]+)",
    re.IGNORECASE,
)


def normalize_upload_rel(fragment: str) -> str | None:
    fragment = fragment.strip()
    if not fragment or fragment.startswith("{"):
        return None
    fragment = urllib.parse.unquote(fragment.split("?", 1)[0].split("#", 1)[0])
    fragment = fragment.strip("/")
    if ".." in fragment or fragment.startswith("/"):
        return None
    if "*" in fragment or "\\" in fragment:
        return None
    # WordPress dated uploads (YYYY/MM/filename)
    if not re.match(r"^\d{4}/\d{2}/.+", fragment):
        return None
    if len(fragment) > 512:
        return None
    return fragment or None


def extract_from_text(text: str) -> set[str]:
    out: set[str] = set()
    for m in RE_UPLOAD.finditer(text):
        rel = normalize_upload_rel(m.group(1))
        if rel:
            out.add(rel)
    return out


def should_scan_file(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix.lower() in SKIP_SCAN_SUFFIXES:
        return False
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        return False
    parts = rel.parts
    if "node_modules" in parts or "dist" in parts or ".git" in parts:
        return False
    if parts[:4] == ("public", "wp-content", "uploads"):
        return False
    return True


def collect_referenced_paths() -> set[str]:
    refs: set[str] = set()
    for base in SCAN_ROOTS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not should_scan_file(path):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            refs |= extract_from_text(text)
    return refs


def main() -> int:
    dry = "--apply" not in sys.argv
    if not UPLOADS.is_dir():
        print("No uploads dir", UPLOADS)
        return 1

    refs = collect_referenced_paths()
    all_files = [p for p in UPLOADS.rglob("*") if p.is_file()]

    keep: set[Path] = set()
    missing: list[str] = []
    for rel in refs:
        p = UPLOADS / rel
        if p.is_file():
            keep.add(p.resolve())
        else:
            missing.append(rel)

    to_delete = [p for p in all_files if p.resolve() not in keep]

    print("Referenced upload path strings:", len(refs))
    print("Resolved to existing files:", len(keep))
    print("Referenced but missing on disk:", len(missing))
    if missing and len(missing) <= 25:
        for m in sorted(missing)[:25]:
            print("  MISSING", m)
    elif missing:
        for m in sorted(missing)[:15]:
            print("  MISSING", m)
        print("  ...")

    print("Files on disk under uploads:", len(all_files))
    print("Delete:", len(to_delete), "Keep:", len(keep))

    if dry:
        print("\nDry run only. Re-run with --apply to delete unreferenced files.")
        return 0

    for p in sorted(to_delete, key=lambda x: len(str(x)), reverse=True):
        p.unlink(missing_ok=True)

    # Remove empty dirs bottom-up
    for dirpath in sorted(
        {d for d in UPLOADS.rglob("*") if d.is_dir()},
        key=lambda d: len(d.parts),
        reverse=True,
    ):
        try:
            next(dirpath.iterdir())
        except StopIteration:
            dirpath.rmdir()

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
