#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble the explicitly approved Stage 9 production release."""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path

EXPECTED_NEW = 66937
EXPECTED_PRESERVED = 95
EXPECTED_TOTAL = 67032
EXPECTED_SITEMAPS = 135
EXPECTED_REDIRECTS = 74
BASE_URL = "https://englishpt.kr"

ROBOTS_RE = re.compile(
    r'<meta\s+name=["\']robots["\']\s+content=["\']noindex\s*,\s*nofollow["\']\s*/?>',
    re.I,
)


def count_redirect_rules(path: Path) -> list[str]:
    return [
        line.strip() for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage7-root", required=True)
    ap.add_argument("--stage8-root", required=True)
    ap.add_argument("--work-root", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    stage7 = Path(args.stage7_root).resolve()
    stage8 = Path(args.stage8_root).resolve()
    work = Path(args.work_root).resolve()
    out = Path(args.output).resolve()

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    failures: list[object] = []

    q7 = json.loads((stage7 / "STAGE7_DEPLOY_PREVIEW_QA_V1.json").read_text(encoding="utf-8"))
    q8 = json.loads((stage8 / "STAGE8_PRODUCTION_APPROVAL_PACKET_V1.json").read_text(encoding="utf-8"))

    if q7.get("status") != "PASS_STAGE7_DEPLOY_PREVIEW_ROLLBACK_READY_NOT_PRODUCTION":
        failures.append("stage7_not_pass")
    if q8.get("status") != "PASS_STAGE8_PRODUCTION_APPROVAL_PACKET_READY_NOT_DEPLOYED":
        failures.append("stage8_not_pass")
    if q8.get("final_domain") != BASE_URL or q8.get("final_domain_confirmed") is not True:
        failures.append("final_domain_not_confirmed")
    if q8.get("approval", {}).get("next_stage") != "STAGE9_PRODUCTION_DEPLOY":
        failures.append("stage8_next_stage_not_stage9")
    if q8.get("counts", {}).get("new_pages") != EXPECTED_NEW:
        failures.append("stage8_new_page_count")
    if q8.get("counts", {}).get("preserved_pages") != EXPECTED_PRESERVED:
        failures.append("stage8_preserved_page_count")
    if q8.get("counts", {}).get("deploy_html_total") != EXPECTED_TOTAL:
        failures.append("stage8_total_page_count")

    rollback = stage7 / "rollback-root"
    if not rollback.exists():
        failures.append("rollback_root_missing")
    else:
        shutil.copytree(rollback, out, dirs_exist_ok=True)

    new_pages = sorted((work / "stage5-full-generation").glob("shard-*/pages/*.html"))
    if len(new_pages) != EXPECTED_NEW:
        failures.append({"new_pages": [len(new_pages), EXPECTED_NEW]})

    transformed = 0
    bad_robot_pages: list[str] = []
    bad_domain_pages: list[str] = []
    for src in new_pages:
        raw = src.read_text(encoding="utf-8")
        raw, n = ROBOTS_RE.subn('<meta name="robots" content="index,follow">', raw, count=1)
        raw = raw.replace("FULL GENERATION · noindex", "ENGLISH PT · 지역별 맞춤 안내")
        if n != 1:
            bad_robot_pages.append(src.name)
        if "noindex" in raw.lower() or "nofollow" in raw.lower():
            bad_robot_pages.append(src.name)
        canonical = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', raw, re.I)
        if not canonical or not canonical.group(1).startswith(BASE_URL + "/"):
            bad_domain_pages.append(src.name)
        (out / src.name).write_text(raw, encoding="utf-8")
        transformed += 1

    first_pages_dir = next(iter((work / "stage5-full-generation").glob("shard-*/pages")), None)
    if first_pages_dir:
        for asset in ("pilot.css", "pilot.js"):
            src = first_pages_dir / asset
            if src.exists():
                shutil.copy2(src, out / asset)
    for asset in ("pilot.css", "pilot.js"):
        if not (out / asset).exists():
            failures.append(f"{asset}_missing")

    release_config = stage8 / "release-config"
    if not release_config.exists():
        failures.append("release_config_missing")
    else:
        for p in release_config.iterdir():
            dst = out / p.name
            if p.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(p, dst)
            else:
                shutil.copy2(p, dst)

    # The pre-release baseline sitemap contains only the historical 95 URLs.
    # Stage 9 publishes the final sitemap-index.xml instead.
    old_sitemap = out / "sitemap.xml"
    if old_sitemap.exists():
        old_sitemap.unlink()

    html_files = sorted(out.glob("*.html"))
    sitemap_files = sorted((out / "sitemaps").glob("sitemap-*.xml")) if (out / "sitemaps").exists() else []
    if len(html_files) != EXPECTED_TOTAL:
        failures.append({"deploy_html_total": [len(html_files), EXPECTED_TOTAL]})
    if transformed != EXPECTED_NEW:
        failures.append({"transformed_new": [transformed, EXPECTED_NEW]})
    if len(sitemap_files) != EXPECTED_SITEMAPS:
        failures.append({"sitemap_shards": [len(sitemap_files), EXPECTED_SITEMAPS]})
    if bad_robot_pages:
        failures.append({"robots_transform_failures": sorted(set(bad_robot_pages))[:20]})
    if bad_domain_pages:
        failures.append({"canonical_domain_failures": sorted(set(bad_domain_pages))[:20]})

    index = (out / "sitemap-index.xml").read_text(encoding="utf-8")
    if index.count("<sitemap><loc>") != EXPECTED_SITEMAPS:
        failures.append("sitemap_index_count")
    if f"{BASE_URL}/sitemaps/" not in index:
        failures.append("sitemap_index_domain")

    sitemap_urls = 0
    for p in sitemap_files:
        text = p.read_text(encoding="utf-8")
        sitemap_urls += text.count("<url><loc>")
        if "englishup.kr" in text or "example.com" in text:
            failures.append({"stale_sitemap_host": p.name})
            break
    if sitemap_urls != EXPECTED_TOTAL:
        failures.append({"sitemap_urls": [sitemap_urls, EXPECTED_TOTAL]})

    robots = (out / "robots.txt").read_text(encoding="utf-8")
    if "Disallow: /" in robots:
        failures.append("robots_blocks_all")
    if f"Sitemap: {BASE_URL}/sitemap-index.xml" not in robots:
        failures.append("robots_sitemap_mismatch")

    rules = count_redirect_rules(out / "_redirects")
    if len(rules) < EXPECTED_REDIRECTS + 1:
        failures.append({"redirect_rule_count": len(rules)})
    if not any(x.startswith("/ /englishpt.html 301") for x in rules):
        failures.append("root_redirect_missing")

    report = {
        "version": "1.0",
        "status": "PASS_STAGE9_RELEASE_ASSEMBLED_READY_TO_DEPLOY" if not failures else "FAIL_STAGE9_RELEASE_ASSEMBLY",
        "stage": "STAGE9_PRODUCTION_DEPLOY",
        "final_domain": BASE_URL,
        "counts": {
            "new_pages": transformed,
            "html_total": len(html_files),
            "sitemap_shards": len(sitemap_files),
            "sitemap_urls": sitemap_urls,
            "redirect_rules": len(rules),
        },
        "indexing": {
            "new_page_robots": "index,follow",
            "noindex_pages": len(set(bad_robot_pages)),
            "robots_txt_allows_crawl": "Disallow: /" not in robots,
        },
        "source": {
            "stage7_status": q7.get("status"),
            "stage8_status": q8.get("status"),
        },
        "failures": failures,
    }
    (out / "STAGE9_PRODUCTION_RELEASE_QA_V1.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
