#!/usr/bin/env python3
from __future__ import annotations
import json, re
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
BASE="https://englishpt.kr"

def read_lines(p):
    return [x.strip() for x in (ROOT/p).read_text(encoding="utf-8").splitlines() if x.strip() and not x.lstrip().startswith("#")]

def html_links(text):
    return re.findall(r'href=["\']([^"\']+\.html(?:#[^"\']*)?)["\']', text, re.I)

def canonical(text):
    pats=[
      r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
      r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']'
    ]
    for p in pats:
        m=re.search(p,text,re.I)
        if m:return m.group(1)
    return None

def main():
    preserved=read_lines("sitemap_95_urls.txt")
    redirects=json.loads((ROOT/"redirects.json").read_text(encoding="utf-8"))
    netlify=read_lines("_redirects")
    sitemap=(ROOT/"sitemap.xml").read_text(encoding="utf-8")
    sitemap_urls=re.findall(r"<loc>"+re.escape(BASE)+r"([^<]+)</loc>",sitemap)

    failures=[]
    page_checks=[]
    preserved_set=set(preserved)
    redirect_map={r["OLD URL"]:r["NEW URL"] for r in redirects}
    if len(preserved)!=95: failures.append(f"preserved_url_count={len(preserved)} expected=95")
    if len(set(preserved))!=95: failures.append("preserved URLs contain duplicates")
    if len(redirects)!=74: failures.append(f"redirect_count={len(redirects)} expected=74")

    repo_html={p.name for p in ROOT.glob("*.html")}
    for url in preserved:
        path=ROOT/url.lstrip("/")
        row={"url":url,"exists":path.exists()}
        if not path.exists():
            failures.append(f"missing preserved file {url}")
            page_checks.append(row); continue
        text=path.read_text(encoding="utf-8")
        can=canonical(text)
        h1_count=len(re.findall(r"<h1\b",text,re.I))
        row.update({"canonical":can,"canonical_ok":can==BASE+url,"h1_count":h1_count,"sitemap":url in sitemap_urls})
        if can!=BASE+url: failures.append(f"canonical mismatch {url}: {can}")
        if h1_count!=1: failures.append(f"H1 count {url}: {h1_count}")
        if url not in sitemap_urls: failures.append(f"sitemap missing {url}")
        # JSON-LD syntax
        for i,block in enumerate(re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>',text,re.I),1):
            try: json.loads(block)
            except Exception as e: failures.append(f"JSON-LD parse {url} block {i}: {e}")
        # relative internal html targets
        broken=[]
        for href in html_links(text):
            href=href.split("#",1)[0]
            if not href or href.startswith(("http://","https://","mailto:","tel:")): continue
            target="/"+href.lstrip("/")
            if (ROOT/target.lstrip("/")).exists(): continue
            if target in redirect_map: continue
            broken.append(target)
        row["broken_internal_html_links"]=sorted(set(broken))
        if broken: failures.append(f"broken internal links {url}: {sorted(set(broken))}")
        page_checks.append(row)

    # sitemap exact preserved set for current production sitemap
    extra_sitemap=sorted(set(sitemap_urls)-preserved_set)
    missing_sitemap=sorted(preserved_set-set(sitemap_urls))
    if missing_sitemap: failures.append(f"sitemap missing preserved URLs: {missing_sitemap}")
    if extra_sitemap: failures.append(f"sitemap unexpected URLs: {extra_sitemap}")

    netlify_map={}
    for line in netlify:
        parts=line.split()
        if len(parts)>=3:
            netlify_map[parts[0]]=(parts[1],parts[2])
    redirect_checks=[]
    for r in redirects:
        old,target=r["OLD URL"],r["NEW URL"]
        target_exists=(ROOT/target.lstrip("/")).exists()
        nl=netlify_map.get(old)
        ok=target_exists and nl is not None and nl[0]==target and nl[1].startswith("301")
        redirect_checks.append({"old":old,"target":target,"target_exists":target_exists,"netlify":nl,"pass":ok})
        if not target_exists: failures.append(f"redirect target missing {old} -> {target}")
        if nl is None: failures.append(f"_redirects missing source {old}")
        elif nl[0]!=target or not nl[1].startswith("301"): failures.append(f"_redirects mismatch {old}: {nl} expected {target} 301")

    # Production service batch count lock
    slug=json.loads((ROOT/"slug_manifest_summary_v1.json").read_text(encoding="utf-8"))
    gold=json.loads((ROOT/"V4_5_GOLD_SAMPLE_FREEZE_20260922.json").read_text(encoding="utf-8"))
    eligible=int(slug["structurally_eligible_candidates"])
    holds=int(slug["hold_admin_branch_offices"])
    resolver=int(slug["resolver_candidates"])
    targets=[
      {"intent_slug":"elem-tutor","blueprint":"v4-elem-parent-evidence-v2","h1":"{dong_name} 초등학생영어과외"},
      {"intent_slug":"mid-conv","blueprint":"v4-mid-school-bridge-v2","h1":"{dong_name} 중학생영어회화"},
      {"intent_slug":"high-conv","blueprint":"v4-high-priority-deadline-v2","h1":"{dong_name} 고등학생영어회화"},
      {"intent_slug":"univ-conv","blueprint":"v4-univ-campus-output-v2","h1":"{dong_name} 대학생영어회화"},
      {"intent_slug":"jobseeker-conv","blueprint":"v4-job-interview-evidence-v2","h1":"{dong_name} 취준생영어회화"},
      {"intent_slug":"biz-business-conv","blueprint":"v4-worker-work-output-v2","h1":"{dong_name} 직장인비즈니스영어"},
      {"intent_slug":"housewife-conv","blueprint":"v4-housewife-lifefit-v2","h1":"{dong_name} 주부영어회화"}
    ]
    service_pages=eligible*len(targets)
    hub_pages=eligible
    manifest={
      "version":"1.0",
      "status":"COUNT_LOCKED_ROW_MATERIALIZATION_PENDING_NOT_PRODUCTION",
      "created_at":"2026-09-22",
      "scope":"DONG_PHASE_1_SERVICE_PAGES_ONLY",
      "source_contracts":{
        "slug_summary":"slug_manifest_summary_v1.json",
        "gold_sample_freeze":"V4_5_GOLD_SAMPLE_FREEZE_20260922.json",
        "gold_standard":"V4_5_FULL_DEPTH_7TARGET_GOLD_STANDARD.md",
        "preserved_urls":"sitemap_95_urls.txt"
      },
      "locality_counts":{
        "resolver_candidates":resolver,
        "structurally_eligible":eligible,
        "hold_admin_branch_offices":holds,
        "check": resolver==eligible+holds
      },
      "page_counts":{
        "targets_per_locality":len(targets),
        "production_service_pages":service_pages,
        "region_hubs_not_in_this_batch":hub_pages,
        "service_plus_hub_if_future_batch_added":service_pages+hub_pages,
        "preserved_existing_urls":len(preserved),
        "root_html_after_service_batch_expected":len(preserved)+service_pages,
        "reserved_95_conflicts":int(slug["preserved_95_url_conflicts"])
      },
      "targets":targets,
      "url_contract":{
        "service":"/{region_slug}-{intent_slug}.html",
        "hero":"localized-minimal-keyword-v4.5",
        "render_time_romanization":False
      },
      "generation_policy":{
        "generate_all_eligible_service_files":True,
        "index_all_immediately":False,
        "staged_index_promotion_required":True,
        "row_manifest_required_before_generation":True,
        "row_manifest_status":"SOURCE_ROWS_NOT_COMMITTED_IN_ENGLISHPT_REPO",
        "production_deploy":False
      },
      "safety":{
        "preserve_95_urls":True,
        "preserve_74_redirects":True,
        "main_merge":False,
        "production_deploy":False
      }
    }
    if resolver!=eligible+holds: failures.append("slug candidate arithmetic mismatch")
    if service_pages!=36043: failures.append(f"service page count mismatch {service_pages}")
    if int(slug["preserved_95_url_conflicts"])!=0: failures.append("reserved 95 URL conflicts nonzero")
    if gold["status"]!="GOLD_SAMPLE_FROZEN_DEPLOYMENT_SYSTEM_PHASE": failures.append("Gold Sample freeze status mismatch")

    report={
      "version":"1.0",
      "status":"PASS" if not failures else "FAIL",
      "preserved_urls":{"expected":95,"actual":len(preserved),"existing":sum(1 for x in page_checks if x["exists"]),"canonical_failures":sum(1 for x in page_checks if x.get("canonical_ok") is False),"h1_failures":sum(1 for x in page_checks if x.get("h1_count")!=1),"sitemap_missing":missing_sitemap,"sitemap_extra":extra_sitemap},
      "redirects":{"expected":74,"json_count":len(redirects),"netlify_rule_count":len(netlify_map),"failed":sum(1 for x in redirect_checks if not x["pass"])},
      "batch_count":{"eligible_localities":eligible,"targets":len(targets),"service_pages":service_pages,"future_hubs_separate":hub_pages,"service_plus_hubs":service_pages+hub_pages},
      "failures":failures,
      "page_checks":page_checks,
      "redirect_checks":redirect_checks,
      "production_deploy":False
    }
    (ROOT/"REGRESSION_95_REDIRECTS_V1.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (ROOT/"DONG_PRODUCTION_BATCH_MANIFEST_V1.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"urls":report["preserved_urls"],"redirects":report["redirects"],"batch":report["batch_count"],"failure_count":len(failures)},ensure_ascii=False))
    if failures: raise SystemExit(1)

if __name__=="__main__":
    main()
