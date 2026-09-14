#!/usr/bin/env python3
"""Replace the placeholder production domain across ENGLISH PT SEO files.

Usage:
  python scripts/set-domain.py https://example.com

Run this once after the final domain is decided and before the first public deploy.
"""
from pathlib import Path
import sys

PLACEHOLDER = "https://englishpt.kr"
TARGET_FILES = {"sitemap.xml", "robots.txt", "README_DEPLOY.txt"}


def normalize_domain(value: str) -> str:
    value = value.strip().rstrip("/")
    if not value.startswith(("https://", "http://")):
        value = "https://" + value
    return value


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/set-domain.py https://example.com")
        return 2

    domain = normalize_domain(sys.argv[1])
    root = Path(__file__).resolve().parents[1]
    files = list(root.glob("*.html"))
    files += [root / name for name in TARGET_FILES if (root / name).exists()]

    changed_files = 0
    replacements = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        count = text.count(PLACEHOLDER)
        if not count:
            continue
        path.write_text(text.replace(PLACEHOLDER, domain), encoding="utf-8")
        changed_files += 1
        replacements += count
        print(f"updated {path.relative_to(root)}: {count} replacement(s)")

    print(f"done: {changed_files} file(s), {replacements} replacement(s), domain={domain}")
    if changed_files == 0:
        print("warning: placeholder domain was not found. It may already have been replaced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
