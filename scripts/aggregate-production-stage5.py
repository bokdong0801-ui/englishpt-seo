#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aggregate Stage 5 shard artifacts without deploying them."""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "stage5_localities_5149_v1.jsonl"
EXPECTED_LOCALITIES = 5149
EXPECTED_PAGES = 66937
EXPECTED_SHARDS = 26
SITEMAP_SHARD_SIZE = 500
SERVICE_ORDER = ["elem-tutor","mid-conv","high-conv","univ-conv","jobseeker-conv","biz-business-conv","housewife-conv"]
EXAM_ORDER = ["toeic","toeic-speaking","opic","ielts","duolingo","toefl"]
INTENTS = SERVICE_ORDER + EXAM_ORDER


def sitemap_xml(urls: list[str]) -> str:
    body = "".join(f"<url><loc>{xml_escape(u)}</loc></url>" for u in urls)
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + body + "</urlset>\n"


def index_xml(names: list[str]) -> str:
    body = "".join(f"<sitemap><loc>https://englishpt.kr/{xml_escape(n)}</loc></sitemap>" for n in names)
    return '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + body + "</sitemapindex>\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    work = Path(args.work_root).resolve()
    out = Path(args.output).resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    sample_dir = out / "sample-pages"
    sample_dir.mkdir(parents=True, exist_ok=True)

    shard_root = work / "stage5-full-generation"
    manifests = sorted(shard_root.glob("shard-*/STAGE5_SHARD_MANIFEST_V1.json"))
    qas = sorted(shard_root.glob("shard-*/STAGE5_SHARD_QA_V1.json"))
    failures: list[object] = []

    if len(manifests) != EXPECTED_SHARDS:
        failures.append({"shard_manifest_count": [len(manifests), EXPECTED_SHARDS]})
    if len(qas) != EXPECTED_SHARDS:
        failures.append({"shard_qa_count": [len(qas), EXPECTED_SHARDS]})

    manifest_objs = [json.loads(p.read_text(encoding="utf-8")) for p in manifests]
    qa_objs = [json.loads(p.read_text(encoding="utf-8")) for p in qas]

    for qa in qa_objs:
        if qa.get("status") != "PASS":
            failures.append({"shard_qa_fail": qa.get("shard", {}).get("name")})
        if qa.get("duplicate_gate", {}).get("status") != "PASS":
            failures.append({"shard_duplicate_fail": qa.get("shard", {}).get("name")})
        if qa.get("file_integrity", {}).get("reserved_95_conflicts") != 0:
            failures.append({"reserved_95_conflict": qa.get("shard", {}).get("name")})

    files: list[dict] = []
    locality_rows: list[dict] = []
    for m in manifest_objs:
        files.extend(m.get("files", []))
        locality_rows.extend(m.get("localities", []))

    filenames = [m["file"] for m in files]
    canonicals = [m["canonical"] for m in files]
    local_slugs = [r["region_slug"] for r in locality_rows]
    if len(files) != EXPECTED_PAGES:
        failures.append({"page_count": [len(files), EXPECTED_PAGES]})
    if len(set(filenames)) != EXPECTED_PAGES:
        failures.append({"filename_unique": [len(set(filenames)), EXPECTED_PAGES]})
    if len(set(canonicals)) != EXPECTED_PAGES:
        failures.append({"canonical_unique": [len(set(canonicals)), EXPECTED_PAGES]})
    if len(locality_rows) != EXPECTED_LOCALITIES or len(set(local_slugs)) != EXPECTED_LOCALITIES:
        failures.append({"locality_integrity": [len(locality_rows), len(set(local_slugs)), EXPECTED_LOCALITIES]})

    by_locality: dict[str, list[dict]] = defaultdict(list)
    by_key: dict[tuple[str, str], dict] = {}
    for m in files:
        by_locality[m["locality"]].append(m)
        by_key[(m["locality"], m["intent"])] = m
    bad_cluster_counts = [slug for slug, vals in by_locality.items() if len(vals) != 13 or len({x["intent"] for x in vals}) != 13]
    if bad_cluster_counts:
        failures.append({"locality_cluster_count_failures": bad_cluster_counts[:100], "count": len(bad_cluster_counts)})

    total_html_bytes = sum(int(m["bytes"]) for m in files)
    shortest = min(files, key=lambda x: int(x["visible_chars"])) if files else None
    longest = max(files, key=lambda x: int(x["visible_chars"])) if files else None

    shard_top_pairs = []
    within_shard_pair_count = 0
    max_cosine = 0.0
    max_jaccard = 0.0
    for qa in qa_objs:
        dg = qa["duplicate_gate"]
        within_shard_pair_count += int(dg["pairs"])
        max_cosine = max(max_cosine, float(dg["max_cosine"]))
        max_jaccard = max(max_jaccard, float(dg["max_5_shingle_jaccard"]))
        for p in dg.get("top_pairs", []):
            shard_top_pairs.append({**p, "shard": qa["shard"]["name"]})
    shard_top_pairs.sort(key=lambda x: (x["jaccard5"], x["cosine"]), reverse=True)
    highest_observed = shard_top_pairs[0] if shard_top_pairs else None

    canonicals_sorted = sorted(canonicals)
    sitemap_names = []
    for i in range(0, len(canonicals_sorted), SITEMAP_SHARD_SIZE):
        name = f"sitemap-stage5-{i // SITEMAP_SHARD_SIZE + 1:03d}.xml"
        sitemap_names.append(name)
        (out / name).write_text(sitemap_xml(canonicals_sorted[i:i + SITEMAP_SHARD_SIZE]), encoding="utf-8")
    (out / "sitemap-stage5-index.xml").write_text(index_xml(sitemap_names), encoding="utf-8")
    if len(sitemap_names) != math.ceil(EXPECTED_PAGES / SITEMAP_SHARD_SIZE):
        failures.append({"sitemap_shard_count": len(sitemap_names)})
    sitemap_urls = sum(
        len(re.findall(r"<url><loc>", (out / name).read_text(encoding="utf-8")))
        for name in sitemap_names
    )
    if sitemap_urls != EXPECTED_PAGES:
        failures.append({"sitemap_url_count": [sitemap_urls, EXPECTED_PAGES]})

    frozen_rows = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines() if line.strip()]
    frozen_rows = sorted(frozen_rows, key=lambda r: r["region_slug"])
    row_by_slug = {r["region_slug"]: r for r in frozen_rows}

    representative_slugs = []
    for sido in ["서울특별시", "부산광역시", "제주특별자치도"]:
        choices = [r["region_slug"] for r in frozen_rows if r["sido"] == sido]
        if not choices:
            failures.append({"representative_sido_missing": sido})
        else:
            representative_slugs.append(sorted(choices)[0])

    representatives = []
    for slug in representative_slugs:
        for intent in INTENTS:
            m = by_key.get((slug, intent))
            if m:
                representatives.append(m)
            else:
                failures.append({"representative_page_missing": [slug, intent]})
    if len(representatives) != 39:
        failures.append({"representative_count": [len(representatives), 39]})

    spot_indexes = [0, EXPECTED_LOCALITIES // 4, EXPECTED_LOCALITIES // 2, (EXPECTED_LOCALITIES * 3) // 4, EXPECTED_LOCALITIES - 1]
    spot_intents = [INTENTS[0], INTENTS[3], INTENTS[7], INTENTS[10], INTENTS[12]]
    deterministic_spots = []
    for idx, intent in zip(spot_indexes, spot_intents):
        slug = frozen_rows[idx]["region_slug"]
        m = by_key.get((slug, intent))
        if m:
            deterministic_spots.append(m)
        else:
            failures.append({"deterministic_spot_missing": [slug, intent]})

    same_name = []
    name_groups: dict[str, list[dict]] = defaultdict(list)
    for r in frozen_rows:
        name_groups[r["dong_name"]].append(r)
    for name in sorted(name_groups):
        group = name_groups[name]
        jurisdictions = {r["jurisdiction_full"] for r in group}
        if len(group) >= 2 and len(jurisdictions) >= 2:
            chosen = sorted(group, key=lambda r: r["region_slug"])[:2]
            for r in chosen:
                m = by_key.get((r["region_slug"], "toeic"))
                if m:
                    same_name.append(m)
            if len(same_name) == 2:
                break
    if len(same_name) != 2:
        failures.append({"same_name_sample_count": len(same_name)})

    pair_pages = []
    if highest_observed:
        for key in ["file_a", "file_b"]:
            file_name = highest_observed[key]
            m = next((x for x in files if x["file"] == file_name), None)
            if m:
                pair_pages.append(m)

    extremes = [x for x in [shortest, longest] if x]
    categories = {
        "representative_39": representatives,
        "deterministic_spot_5": deterministic_spots,
        "highest_observed_within_shard_pair": pair_pages,
        "shortest_longest": extremes,
        "same_visible_name_cross_jurisdiction": same_name,
    }

    copy_map: dict[str, dict] = {}
    for vals in categories.values():
        for m in vals:
            copy_map[m["file"]] = m

    render_targets = []
    for name, m in sorted(copy_map.items()):
        src = work / "stage5-full-generation" / m["path"]
        if not src.exists():
            failures.append({"sample_source_missing": str(src)})
            continue
        shutil.copy2(src, sample_dir / name)
        render_targets.append({
            "file": name,
            "h1": m["h1"],
            "intent": m["intent"],
            "locality": m["locality"],
            "source_path": str(src.relative_to(work)),
        })

    css_candidates = list(shard_root.glob("shard-*/pages/pilot.css"))
    js_candidates = list(shard_root.glob("shard-*/pages/pilot.js"))
    if css_candidates:
        shutil.copy2(css_candidates[0], sample_dir / "pilot.css")
    if js_candidates:
        shutil.copy2(js_candidates[0], sample_dir / "pilot.js")

    file_manifest_path = out / "STAGE5_66937_FILE_MANIFEST_V1.jsonl"
    with file_manifest_path.open("w", encoding="utf-8") as fp:
        for m in sorted(files, key=lambda x: x["file"]):
            fp.write(json.dumps(m, ensure_ascii=False, separators=(",", ":")) + "\n")

    sample_pack = {
        "version": "1.0",
        "status": "READY_FOR_RENDER_REVIEW" if not failures else "FAIL",
        "stage": "STAGE5_FULL_GENERATION_SAMPLE_PACK",
        "representative_localities": [
            {
                "region_slug": slug,
                "full_name_ko": row_by_slug[slug]["full_name_ko"],
                "sido": row_by_slug[slug]["sido"],
            }
            for slug in representative_slugs
        ],
        "categories": categories,
        "render_targets": render_targets,
        "highest_duplicate_note": (
            "Highest pair observed across exact within-shard scans. Cross-shard global duplicate candidate search is a Stage 6 bulk-QA gate."
        ),
        "safety": {"production_deploy": False, "main_merge": False, "sitemap_live": False},
    }
    (out / "STAGE5_SAMPLE_PACK_V1.json").write_text(json.dumps(sample_pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    regression = None
    regression_path = ROOT / "REGRESSION_95_REDIRECTS_V1.json"
    if regression_path.exists():
        regression = json.loads(regression_path.read_text(encoding="utf-8"))
        if regression.get("status") != "PASS":
            failures.append({"preserved_95_redirect_74_regression": regression.get("status")})

    qa = {
        "version": "1.0",
        "status": "PASS_FULL_GENERATION_ARTIFACTS_READY_STAGE6_REQUIRED_NOT_PRODUCTION" if not failures else "FAIL",
        "stage": "STAGE5_5149_X_13_FULL_GENERATION",
        "page_count": len(files),
        "locality_count": len(set(local_slugs)),
        "intent_count": 13,
        "shard_count": len(manifests),
        "file_integrity": {
            "filenames_unique": len(set(filenames)),
            "canonicals_unique": len(set(canonicals)),
            "locality_clusters_13_of_13": len(by_locality) - len(bad_cluster_counts),
            "reserved_95_conflicts": sum(int(q["file_integrity"]["reserved_95_conflicts"]) for q in qa_objs),
        },
        "static_qa": {
            "status": "PASS" if all(q.get("static_failure_count") == 0 for q in qa_objs) else "FAIL",
            "failures": sum(int(q.get("static_failure_count", 0)) for q in qa_objs),
        },
        "duplicate_qa": {
            "status": "PASS_WITHIN_SHARDS_STAGE6_GLOBAL_PENDING" if all(q["duplicate_gate"]["status"] == "PASS" for q in qa_objs) else "FAIL",
            "thresholds_unchanged": {"cosine_lt": 0.82, "jaccard5_lt": 0.24},
            "within_shard_exact_pair_count": within_shard_pair_count,
            "max_cosine_observed": round(max_cosine, 4),
            "max_5_shingle_jaccard_observed": round(max_jaccard, 4),
            "highest_observed_pair": highest_observed,
            "cross_shard_global_gate": "STAGE6_REQUIRED",
        },
        "visible_chars": {
            "min": shortest["visible_chars"] if shortest else None,
            "max": longest["visible_chars"] if longest else None,
        },
        "package_sizing": {
            "html_bytes": total_html_bytes,
            "html_mib": round(total_html_bytes / 1024 / 1024, 2),
            "html_gib": round(total_html_bytes / 1024 / 1024 / 1024, 3),
        },
        "sitemap_prototype": {
            "status": "PASS" if sitemap_urls == EXPECTED_PAGES else "FAIL",
            "shard_size": SITEMAP_SHARD_SIZE,
            "shard_count": len(sitemap_names),
            "url_count": sitemap_urls,
            "index": "sitemap-stage5-index.xml",
            "deployed": False,
        },
        "regression_95_redirects_74": {
            "status": regression.get("status") if regression else "MISSING",
        },
        "sample_pack": {
            "representative_pages": len(representatives),
            "deterministic_spots": len(deterministic_spots),
            "render_targets": len(render_targets),
            "file": "STAGE5_SAMPLE_PACK_V1.json",
        },
        "render_qa": "PENDING",
        "failures": failures,
        "next_gate": "STAGE6_FULL_BULK_QA",
        "safety": {
            "robots": "noindex,nofollow",
            "live_lead_submission": False,
            "sitemap_live": False,
            "main_merge": False,
            "production_deploy": False,
        },
    }
    (out / "STAGE5_66937_QA_V1.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": qa["status"],
        "pages": qa["page_count"],
        "localities": qa["locality_count"],
        "shards": qa["shard_count"],
        "html_gib": qa["package_sizing"]["html_gib"],
        "sitemaps": qa["sitemap_prototype"]["shard_count"],
        "sample_render_targets": qa["sample_pack"]["render_targets"],
        "next_gate": qa["next_gate"],
    }, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
