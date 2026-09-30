#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the Stage 8 production-approval packet without deploying."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://englishpt.kr"
EXPECTED_TOTAL = 67032
EXPECTED_NEW = 66937
EXPECTED_PRESERVED = 95
EXPECTED_SITEMAP_SHARDS = 135
EXPECTED_REDIRECTS = 74
EXPECTED_PACKAGES = 26


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage7-root", required=True)
    ap.add_argument("--package-root", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--stage7-run", type=int, required=True)
    ap.add_argument("--source-commit", required=True)
    args = ap.parse_args()

    stage7 = Path(args.stage7_root).resolve()
    package_root = Path(args.package_root).resolve()
    out = Path(args.output).resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    failures: list[object] = []
    q_path = stage7 / "STAGE7_DEPLOY_PREVIEW_QA_V1.json"
    if not q_path.exists():
        raise RuntimeError(f"missing Stage 7 QA: {q_path}")
    q = json.loads(q_path.read_text(encoding="utf-8"))

    if q.get("status") != "PASS_STAGE7_DEPLOY_PREVIEW_ROLLBACK_READY_NOT_PRODUCTION":
        failures.append("stage7_status_not_pass")
    if q.get("counts", {}).get("new_pages") != EXPECTED_NEW:
        failures.append("new_pages_not_66937")
    if q.get("counts", {}).get("preserved_pages") != EXPECTED_PRESERVED:
        failures.append("preserved_pages_not_95")
    if q.get("counts", {}).get("deploy_html_total") != EXPECTED_TOTAL:
        failures.append("deploy_total_not_67032")
    if q.get("counts", {}).get("legacy_redirects") != EXPECTED_REDIRECTS:
        failures.append("redirects_not_74")
    if q.get("counts", {}).get("final_shard_packages") != EXPECTED_PACKAGES:
        failures.append("package_count_not_26")
    if q.get("sitemap_preview", {}).get("base_url") != BASE_URL:
        failures.append("stage7_base_url_mismatch")
    if q.get("sitemap_preview", {}).get("domain_status") != "CONFIRMED_FINAL_DOMAIN":
        failures.append("final_domain_not_confirmed")
    if q.get("approval_gate", {}).get("final_domain") != BASE_URL:
        failures.append("approval_final_domain_mismatch")
    if q.get("approval_gate", {}).get("final_domain_confirmed") is not True:
        failures.append("approval_domain_not_confirmed")
    if q.get("source_proof", {}).get("stage6_global_status") != "PASS_STAGE6_GLOBAL_CROSS_SHARD_QA_NOT_PRODUCTION":
        failures.append("stage6_global_proof_not_pass")
    if q.get("source_proof", {}).get("stage6_incremental_status") != "PASS_STAGE6_INCREMENTAL_GLOBAL_PROOF_NOT_PRODUCTION":
        failures.append("stage6_incremental_proof_not_pass")
    if float(q.get("source_proof", {}).get("stage6_max_cosine", 9)) >= 0.82:
        failures.append("stage6_cosine_not_below_threshold")

    for key in ("main_merge", "production_deploy", "sitemap_live", "bulk_index_request"):
        if q.get("safety", {}).get(key) is not False:
            failures.append(f"stage7_safety_{key}_not_false")

    # Validate the currently committed production-domain controls.
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    if f"Sitemap: {BASE_URL}/sitemap-index.xml" not in robots:
        failures.append("repo_robots_domain_mismatch")
    if "Disallow: /" in robots:
        failures.append("repo_robots_blocks_all")

    redirects = (ROOT / "_redirects").read_text(encoding="utf-8").splitlines()
    redirect_rules = [x for x in redirects if x.strip() and not x.lstrip().startswith("#")]
    if len(redirect_rules) < EXPECTED_REDIRECTS + 1:
        failures.append({"netlify_redirect_rule_count_too_small": len(redirect_rules)})
    if not any(x.startswith("/ /englishpt.html 301") for x in redirect_rules):
        failures.append("root_redirect_missing")

    # Convert Stage 7 preview sitemap names into final production names.
    src_dir = stage7 / "sitemaps"
    src_shards = sorted(src_dir.glob("sitemap-stage7-preview-*.xml"))
    src_shards = [p for p in src_shards if not p.name.endswith("-index.xml")]
    if len(src_shards) != EXPECTED_SITEMAP_SHARDS:
        failures.append({"stage7_sitemap_shards": len(src_shards)})

    release = out / "release-config"
    final_sitemap_dir = release / "sitemaps"
    final_sitemap_dir.mkdir(parents=True)
    final_names: list[str] = []
    total_urls = 0
    stale_hosts: list[str] = []

    for i, src in enumerate(src_shards, start=1):
        final_name = f"sitemap-{i:03d}.xml"
        final_names.append(final_name)
        text = src.read_text(encoding="utf-8")
        locs = re.findall(r"<loc>(.*?)</loc>", text)
        total_urls += len(locs)
        stale_hosts.extend([u for u in locs if not u.startswith(BASE_URL + "/")][:3])
        (final_sitemap_dir / final_name).write_text(text, encoding="utf-8")

    if total_urls != EXPECTED_TOTAL:
        failures.append({"final_sitemap_url_count": total_urls})
    if stale_hosts:
        failures.append({"sitemap_domain_mismatches": stale_hosts[:10]})

    index_body = "".join(
        f"<sitemap><loc>{xml_escape(BASE_URL + '/sitemaps/' + name)}</loc></sitemap>"
        for name in final_names
    )
    final_index = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + index_body + "</sitemapindex>\n"
    )
    (release / "sitemap-index.xml").write_text(final_index, encoding="utf-8")
    (release / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap-index.xml\n",
        encoding="utf-8",
    )
    shutil.copy2(ROOT / "_redirects", release / "_redirects")
    shutil.copy2(ROOT / "netlify.toml", release / "netlify.toml")
    shutil.copy2(ROOT / "redirects.json", release / "redirects.json")

    # Confirm the final 26 proven page packages are present and fingerprint them.
    packages = sorted(package_root.glob("stage5-shard-*-of-026.tar.zst"))
    if len(packages) != EXPECTED_PACKAGES:
        failures.append({"stage5_package_count": len(packages)})
    package_manifest = [
        {"file": p.name, "bytes": p.stat().st_size, "sha256": sha256_file(p)}
        for p in packages
    ]
    (out / "STAGE8_FINAL_PACKAGE_FINGERPRINTS_V1.json").write_text(
        json.dumps(package_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    rollback_candidates = list(package_root.glob("stage7-rollback-95-baseline.tar.zst"))
    if len(rollback_candidates) != 1:
        failures.append({"rollback_package_count": len(rollback_candidates)})

    sample_pages = q.get("representative_13", {}).get("pages", [])
    if len(sample_pages) != 13:
        failures.append({"representative_page_count": len(sample_pages)})
    bad_sample_canonicals = [
        x.get("canonical") for x in sample_pages
        if not str(x.get("canonical", "")).startswith(BASE_URL + "/")
    ]
    if bad_sample_canonicals:
        failures.append({"representative_domain_mismatch": bad_sample_canonicals})

    status = (
        "PASS_STAGE8_PRODUCTION_APPROVAL_PACKET_READY_NOT_DEPLOYED"
        if not failures else "FAIL_STAGE8_PRODUCTION_APPROVAL_PACKET"
    )
    report = {
        "version": "1.0",
        "status": status,
        "stage": "STAGE8_PRODUCTION_APPROVAL_PACKET",
        "final_domain": BASE_URL,
        "final_domain_confirmed": True,
        "source": {
            "stage7_run": args.stage7_run,
            "source_commit": args.source_commit,
            "stage7_status": q.get("status"),
            "stage6_global_status": q.get("source_proof", {}).get("stage6_global_status"),
            "stage6_incremental_status": q.get("source_proof", {}).get("stage6_incremental_status"),
            "stage6_max_cosine": q.get("source_proof", {}).get("stage6_max_cosine"),
        },
        "counts": {
            "new_pages": EXPECTED_NEW,
            "preserved_pages": EXPECTED_PRESERVED,
            "deploy_html_total": EXPECTED_TOTAL,
            "legacy_redirects": EXPECTED_REDIRECTS,
            "sitemap_urls": total_urls,
            "sitemap_shards": len(final_names),
            "final_shard_packages": len(packages),
            "representative_pages": len(sample_pages),
        },
        "release_config": {
            "sitemap_index": "release-config/sitemap-index.xml",
            "sitemap_dir": "release-config/sitemaps",
            "robots": "release-config/robots.txt",
            "redirects": "release-config/_redirects",
            "netlify": "release-config/netlify.toml",
        },
        "rollback": {
            "available": len(rollback_candidates) == 1,
            "package": rollback_candidates[0].name if rollback_candidates else None,
        },
        "approval": {
            "status": "AWAITING_EXPLICIT_PRODUCTION_DEPLOY_APPROVAL",
            "next_stage": "STAGE9_PRODUCTION_DEPLOY",
            "requires_explicit_deploy_approval": True,
        },
        "safety": {
            "main_merge": False,
            "production_deploy": False,
            "sitemap_live": False,
            "bulk_index_request": False,
        },
        "failures": failures,
    }
    (out / "STAGE8_PRODUCTION_APPROVAL_PACKET_V1.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    md = [
        "# ENGLISH PT Stage 8 Production Approval Packet",
        "",
        f"- Status: {status}",
        f"- Final domain: {BASE_URL}",
        f"- Deploy HTML total: {EXPECTED_TOTAL:,}",
        f"- New pages: {EXPECTED_NEW:,}",
        f"- Preserved pages: {EXPECTED_PRESERVED}",
        f"- Sitemap URLs: {total_urls:,}",
        f"- Sitemap shards: {len(final_names)}",
        f"- Legacy redirects: {EXPECTED_REDIRECTS}",
        f"- Proven page packages: {len(packages)}",
        f"- Stage 6 max cosine: {report['source']['stage6_max_cosine']}",
        f"- Rollback package available: {report['rollback']['available']}",
        "",
        "## Safety",
        "- Production deploy: false",
        "- Main merge: false",
        "- Sitemap live: false",
        "- Google Search Console bulk/index submission: false",
        "",
        "## Next action",
        "- Explicit approval is required before Stage 9 production deployment.",
    ]
    (out / "STAGE8_PRODUCTION_APPROVAL_CHECKLIST.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )

    print(json.dumps({
        "status": status,
        "domain": BASE_URL,
        "total": EXPECTED_TOTAL,
        "sitemap_urls": total_urls,
        "sitemap_shards": len(final_names),
        "redirects": EXPECTED_REDIRECTS,
        "packages": len(packages),
        "rollback": len(rollback_candidates) == 1,
        "next_stage": report["approval"]["next_stage"],
    }, ensure_ascii=False))

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
