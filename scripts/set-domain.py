#!/usr/bin/env python3
"""Verify the locked ENGLISH PT production domain.

The final production domain was confirmed as https://englishpt.kr on 2026-09-30.
This script no longer performs an arbitrary domain migration; it verifies that the
requested domain matches the locked production host.
"""
from pathlib import Path
import sys

FINAL_DOMAIN = "https://englishpt.kr"
TARGET_FILES = {"sitemap.xml", "sitemap-index.xml", "robots.txt", "README_DEPLOY.txt", "REMOTE_DEPLOY_STATUS.txt"}


def normalize_domain(value: str) -> str:
    value = value.strip().rstrip("/")
    if not value.startswith(("https://", "http://")):
        value = "https://" + value
    return value


def main() -> int:
    domain = normalize_domain(sys.argv[1]) if len(sys.argv) == 2 else FINAL_DOMAIN
    if domain != FINAL_DOMAIN:
        print(f"ERROR: production domain is locked to {FINAL_DOMAIN}; received {domain}")
        return 2

    root = Path(__file__).resolve().parents[1]
    files = list(root.glob("*.html"))
    files += [root / name for name in TARGET_FILES if (root / name).exists()]

    mismatches = []
    checked = 0
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        checked += 1
        if "englishup.kr" in text or "example.com" in text or "{{FINAL_DOMAIN}}" in text:
            mismatches.append(str(path.relative_to(root)))

    if mismatches:
        print("ERROR: stale/placeholder domain references:", ", ".join(mismatches[:20]))
        return 1

    print(f"PASS: domain locked to {FINAL_DOMAIN}; checked {checked} repository file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
