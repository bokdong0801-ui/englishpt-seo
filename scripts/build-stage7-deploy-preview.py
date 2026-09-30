#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build Stage 7 sitemap/deploy-preview/rollback artifacts without deploying."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import shutil
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_NEW = 66937
EXPECTED_PRESERVED = 95
EXPECTED_TOTAL = EXPECTED_NEW + EXPECTED_PRESERVED
EXPECTED_LOCALITIES = 5149
EXPECTED_INTENTS = 13
EXPECTED_REDIRECTS = 74
SITEMAP_SIZE = 500
BASE_URL = "https://englishpt.kr"
INTENTS = [
    "elem-tutor","mid-conv","high-conv","univ-conv","jobseeker-conv",
    "biz-business-conv","housewife-conv","toeic","toeic-speaking",
    "opic","ielts","duolingo","toefl",
]
BASE_STAGE5_RUN = 36671864892
REFRESH_RUN = 36676434790
STAGE6_GLOBAL_RUN = 36677053139
STAGE6_INCREMENTAL_RUN = 36677407709
REFRESH_SHARDS = {"stage5-shard-002-of-026.tar.zst", "stage5-shard-009-of-026.tar.zst"}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sitemap_xml(urls: list[str]) -> str:
    body = "".join(f"<url><loc>{xml_escape(u)}</loc></url>" for u in urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + body + "</urlset>\n"
    )


def sitemap_index(names: list[str]) -> str:
    body = "".join(
        f"<sitemap><loc>{BASE_URL}/{xml_escape(name)}</loc></sitemap>"
        for name in names
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + body + "</sitemapindex>\n"
    )


def safe_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", required=True)
    ap.add_argument("--package-root", required=True)
    ap.add_argument("--stage6-global", required=True)
    ap.add_argument("--stage6-incremental", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    work = Path(args.work_root).resolve()
    package_root = Path(args.package_root).resolve()
    out = Path(args.output).resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    failures: list[object] = []
    shard_root = work / "stage5-full-generation"
    manifests = sorted(shard_root.glob("shard-*/STAGE5_SHARD_MANIFEST_V1.json"))
    qas = sorted(shard_root.glob("shard-*/STAGE5_SHARD_QA_V1.json"))
    html_files = sorted(shard_root.glob("shard-*/pages/*.html"))

    if len(manifests) != 26:
        failures.append({"manifest_count": [len(manifests), 26]})
    if len(qas) != 26:
        failures.append({"qa_count": [len(qas), 26]})
    if len(html_files) != EXPECTED_NEW:
        failures.append({"new_html_count": [len(html_files), EXPECTED_NEW]})

    manifest_objs = [json.loads(p.read_text(encoding="utf-8")) for p in manifests]
    qa_objs = [json.loads(p.read_text(encoding="utf-8")) for p in qas]
    if any(q.get("status") != "PASS" for q in qa_objs):
        failures.append("one_or_more_final_shard_qa_not_pass")

    files: list[dict] = []
    for m in manifest_objs:
        files.extend(m.get("files", []))
    if len(files) != EXPECTED_NEW:
        failures.append({"manifest_page_count": [len(files), EXPECTED_NEW]})

    filenames = [x["file"] for x in files]
    canonicals = [x["canonical"] for x in files]
    if len(set(filenames)) != EXPECTED_NEW:
        failures.append({"filename_unique": len(set(filenames))})
    if len(set(canonicals)) != EXPECTED_NEW:
        failures.append({"canonical_unique": len(set(canonicals))})
    if any(name.endswith("-tos.html") for name in filenames):
        failures.append("standalone_tos_present")

    regression = json.loads((ROOT / "REGRESSION_95_REDIRECTS_V1.json").read_text(encoding="utf-8"))
    if regression.get("status") != "PASS":
        failures.append("regression_95_74_not_pass")
    preserved_checks = regression.get("page_checks", [])
    preserved_urls = [x["canonical"] for x in preserved_checks if x.get("canonical")]
    if len(preserved_urls) != EXPECTED_PRESERVED or len(set(preserved_urls)) != EXPECTED_PRESERVED:
        failures.append({"preserved_url_count": [len(preserved_urls), len(set(preserved_urls))]})
    if regression.get("redirects", {}).get("json_count") != EXPECTED_REDIRECTS:
        failures.append("redirect_count_not_74")
    if set(preserved_urls) & set(canonicals):
        failures.append("preserved_new_canonical_collision")

    all_urls = sorted(set(preserved_urls) | set(canonicals))
    if len(all_urls) != EXPECTED_TOTAL:
        failures.append({"total_sitemap_urls": [len(all_urls), EXPECTED_TOTAL]})

    global_qa = json.loads(Path(args.stage6_global).read_text(encoding="utf-8"))
    incremental = json.loads(Path(args.stage6_incremental).read_text(encoding="utf-8"))
    if global_qa.get("status") != "PASS_STAGE6_GLOBAL_CROSS_SHARD_QA_NOT_PRODUCTION":
        failures.append("stage6_global_not_pass")
    if global_qa.get("cosine_failure_count") != 0 or global_qa.get("jaccard5_failure_count") != 0:
        failures.append("stage6_global_duplicate_failure")
    if incremental.get("status") != "PASS_STAGE6_INCREMENTAL_GLOBAL_PROOF_NOT_PRODUCTION":
        failures.append("stage6_incremental_not_pass")

    sitemap_dir = out / "sitemaps"
    sitemap_dir.mkdir()
    sitemap_names: list[str] = []
    for i in range(0, len(all_urls), SITEMAP_SIZE):
        name = f"sitemap-stage7-preview-{i // SITEMAP_SIZE + 1:03d}.xml"
        sitemap_names.append(name)
        (sitemap_dir / name).write_text(sitemap_xml(all_urls[i:i+SITEMAP_SIZE]), encoding="utf-8")
    index_name = "sitemap-stage7-preview-index.xml"
    (sitemap_dir / index_name).write_text(sitemap_index(sitemap_names), encoding="utf-8")
    if len(sitemap_names) != math.ceil(EXPECTED_TOTAL / SITEMAP_SIZE):
        failures.append({"sitemap_shards": len(sitemap_names)})
    counted = sum(
        len(re.findall(r"<url><loc>", (sitemap_dir / x).read_text(encoding="utf-8")))
        for x in sitemap_names
    )
    if counted != EXPECTED_TOTAL:
        failures.append({"sitemap_url_count": counted})

    package_files = sorted(package_root.glob("stage5-shard-*-of-026.tar.zst"))
    if len(package_files) != 26:
        failures.append({"deploy_package_shards": len(package_files)})
    package_manifest = []
    for p in package_files:
        package_manifest.append({
            "file": p.name,
            "bytes": p.stat().st_size,
            "sha256": sha256_file(p),
            "source_run": REFRESH_RUN if p.name in REFRESH_SHARDS else BASE_STAGE5_RUN,
            "refreshed_final": p.name in REFRESH_SHARDS,
        })
    (out / "STAGE7_FINAL_SHARD_PACKAGE_MANIFEST_V1.json").write_text(
        json.dumps(package_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    by_locality: dict[str, dict[str, dict]] = {}
    for x in files:
        by_locality.setdefault(x["locality"], {})[x["intent"]] = x
    preferred = "seoul-jongno-sajikdong"
    sample_locality = preferred if len(by_locality.get(preferred, {})) == 13 else sorted(
        k for k,v in by_locality.items() if len(v) == 13
    )[0]
    sample_rows = [by_locality[sample_locality][intent] for intent in INTENTS]
    sample_dir = out / "sample-site"
    sample_dir.mkdir()
    sample_urls = []
    for m in sample_rows:
        src = work / "stage5-full-generation" / m["path"]
        if not src.exists():
            failures.append({"sample_missing": m["file"]})
            continue
        safe_copy(src, sample_dir / m["file"])
        sample_urls.append({
            "intent": m["intent"],
            "file": m["file"],
            "h1": m["h1"],
            "canonical": m["canonical"],
        })
    css = next(iter(shard_root.glob("shard-*/pages/pilot.css")), None)
    js = next(iter(shard_root.glob("shard-*/pages/pilot.js")), None)
    if css:
        safe_copy(css, sample_dir / "pilot.css")
    if js:
        safe_copy(js, sample_dir / "pilot.js")
    if len(sample_urls) != 13:
        failures.append({"sample_13_count": len(sample_urls)})

    rollback = out / "rollback-root"
    rollback.mkdir()
    local_asset_refs: set[str] = set()
    for chk in preserved_checks:
        rel = chk["url"].lstrip("/")
        src = ROOT / rel
        if not src.exists():
            failures.append({"rollback_missing_preserved": rel})
            continue
        safe_copy(src, rollback / rel)
        text = src.read_text(encoding="utf-8", errors="ignore")
        for ref in re.findall(r'(?:href|src)=["\']([^"\']+)["\']', text, re.I):
            if ref.startswith(("http://","https://","mailto:","tel:","#","data:","javascript:")):
                continue
            ref = ref.split("#",1)[0].split("?",1)[0].lstrip("/")
            if ref:
                local_asset_refs.add(ref)
    for ref in sorted(local_asset_refs):
        src = (ROOT / ref).resolve()
        try:
            src.relative_to(ROOT.resolve())
        except ValueError:
            continue
        if src.is_file():
            safe_copy(src, rollback / ref)
    for name in ["_redirects","robots.txt","sitemap.xml","netlify.toml","redirects.json","sitemap_95_urls.txt","REGRESSION_95_REDIRECTS_V1.json"]:
        src = ROOT / name
        if src.exists():
            safe_copy(src, rollback / name)

    preview_robots = (
        "User-agent: *\n"
        "Disallow: /\n\n"
        "# Stage 7 preview only. Do not publish or submit this sitemap.\n"
    )
    (out / "robots.preview.txt").write_text(preview_robots, encoding="utf-8")
    (out / "robots.production.template.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: {{FINAL_DOMAIN}}/sitemap-index.xml\n",
        encoding="utf-8",
    )
    safe_copy(ROOT / "_redirects", out / "_redirects.preview")
    safe_copy(ROOT / "netlify.toml", out / "netlify.preview.toml")

    redirects_examples = regression.get("redirect_checks", [])[:5]
    report = {
        "version": "1.0",
        "status": "PASS_STAGE7_DEPLOY_PREVIEW_ROLLBACK_READY_NOT_PRODUCTION" if not failures else "FAIL",
        "stage": "STAGE7_SITEMAP_DEPLOY_PREVIEW_ROLLBACK",
        "source_proof": {
            "base_stage5_run": BASE_STAGE5_RUN,
            "refresh_run": REFRESH_RUN,
            "stage6_global_run": STAGE6_GLOBAL_RUN,
            "stage6_incremental_run": STAGE6_INCREMENTAL_RUN,
            "stage6_global_status": global_qa.get("status"),
            "stage6_max_cosine": global_qa.get("max_cosine"),
            "stage6_max_hashed_jaccard5_screen": global_qa.get("max_hashed_jaccard5_screen"),
            "stage6_incremental_status": incremental.get("status"),
            "incremental_changed_html": incremental.get("delta_verification", {}).get("changed_html", []),
        },
        "counts": {
            "new_pages": len(files),
            "preserved_pages": len(preserved_urls),
            "deploy_html_total": len(files) + len(preserved_urls),
            "localities": EXPECTED_LOCALITIES,
            "intents": EXPECTED_INTENTS,
            "legacy_redirects": regression.get("redirects", {}).get("json_count"),
            "final_shard_packages": len(package_manifest),
        },
        "sitemap_preview": {
            "base_url": BASE_URL,
            "domain_status": "PLACEHOLDER_REQUIRES_EXPLICIT_FINAL_DOMAIN_CONFIRMATION",
            "live": False,
            "index": f"sitemaps/{index_name}",
            "shards": len(sitemap_names),
            "urls": counted,
            "shard_size": SITEMAP_SIZE,
        },
        "representative_13": {
            "locality": sample_locality,
            "pages": sample_urls,
        },
        "redirect_examples": redirects_examples,
        "rollback": {
            "preserved_html": sum(1 for p in rollback.rglob("*.html")),
            "file_count": sum(1 for p in rollback.rglob("*") if p.is_file()),
            "purpose": "restore current 95-URL baseline plus redirects/config/assets before any bulk release",
        },
        "approval_gate": {
            "next_stage": "STAGE8_EXPLICIT_PRODUCTION_APPROVAL",
            "requires_final_domain": True,
            "requires_user_approval": True,
        },
        "failures": failures,
        "safety": {
            "main_merge": False,
            "production_deploy": False,
            "sitemap_live": False,
            "bulk_index_request": False,
            "preview_robots": "Disallow: /",
        },
    }
    (out / "STAGE7_DEPLOY_PREVIEW_QA_V1.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    md = [
        "# ENGLISH PT Stage 7 Deploy Preview / Rollback",
        "",
        f"- Status: {report['status']}",
        f"- New pages: {report['counts']['new_pages']:,}",
        f"- Preserved pages: {report['counts']['preserved_pages']}",
        f"- Preview sitemap URLs: {report['sitemap_preview']['urls']:,}",
        f"- Sitemap shards: {report['sitemap_preview']['shards']}",
        f"- Legacy redirects: {report['counts']['legacy_redirects']}",
        f"- Stage 6 max cosine: {report['source_proof']['stage6_max_cosine']}",
        f"- Stage 6 hashed Jaccard5 max: {report['source_proof']['stage6_max_hashed_jaccard5_screen']}",
        "- Production deploy: false",
        "- Main merge: false",
        "- Sitemap live: false",
        "- Final domain confirmation required before Stage 8.",
        "",
        "## Representative 13 URLs",
    ]
    md += [f"- {x['intent']}: {x['canonical']}" for x in sample_urls]
    (out / "STAGE7_DEPLOY_PREVIEW_SUMMARY.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": report["status"],
        "new_pages": report["counts"]["new_pages"],
        "preserved_pages": report["counts"]["preserved_pages"],
        "deploy_html_total": report["counts"]["deploy_html_total"],
        "sitemap_urls": report["sitemap_preview"]["urls"],
        "sitemap_shards": report["sitemap_preview"]["shards"],
        "redirects": report["counts"]["legacy_redirects"],
        "rollback_files": report["rollback"]["file_count"],
        "next_stage": report["approval_gate"]["next_stage"],
    }, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
