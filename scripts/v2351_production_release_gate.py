#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepare v23.5.1 PRODUCTION-READY archive from immutable full SEO-corrected Draft source.

Never makes network calls; never deploys. Explicitly removes only the global
Draft noindex HTTP response header while preserving per-page noindex metadata.
All immutable counts, URLs, metadata and sitemap remain independently audited.
"""
import argparse
import hashlib
import json
import re
import sys
import traceback
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone

BASE="https://englishpt.kr"
ROBOTS=re.compile(r'<meta\s+name="robots"\s+content="([^"]+)"',re.I)
CANONICAL=re.compile(r'<link\s+rel="canonical"\s+href="([^"]+)"',re.I)
OG=re.compile(r'<meta\s+property="og:image"\s+content="([^"]+)"',re.I)
TITLE=re.compile(r'<title>.*?</title>',re.I|re.S)
DESC=re.compile(r'<meta\s+name="description"\s+content="([^"]+)"',re.I)
NOINDEX_HEADER=re.compile(r'(?im)^[ \t]*X-Robots-Tag:[ \t]*noindex\b[^\r\n]*$')
PREVIEW_HOST='englishpt-final-ia-review-bokdong.netlify.app'

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while b:=f.read(4*1024*1024):h.update(b)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--headers-candidate',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    opts=parser.parse_args()
    root=opts.root.resolve()
    report={"status":"RUNNING","version":"v23.5.1",
            "source_full_seo_corrected_run":38868768031,
            "source_student_six_run":38864767374,
            "source_base_run":38689660290,
            "source_base_sha":"a18b8901ecda7d37f65e35b15f03d579ec63c70f",
            "live_integrated_qa_run":38869423163,
            "release_type":"PRODUCTION_READY_NOT_DEPLOYED",
            "production_deployed":False,"form_submitted":False,
            "error_count":0,"errors":[],"generated_count":0,
            "indexable":0,"noindex":0,"canonical_match":0,"title_ok":0,
            "description_ok":0,"og_meta_ok":0,"new_student_noindex":0,
            "provenance":"validated SEO corrected Draft package; Production response _headers candidate only",
            "seo_sitemap_urls_expected":21964,
            "production_global_noindex_removed":False,
            "review_global_noindex_present_before":False,
            "production_host_and_canonical":"englishpt.kr",
            "site_files_sha256":{},
            "limitations":["GO means archive is deployment-ready, not actually deployed",
                           "Form submission and downstream email cannot be verified without real submission",
                           "Google/Naver search coverage requires observation after production deployment"]}
    try:
        headers=root/"_headers"
        if not headers.is_file():raise ValueError("_headers missing")
        original=headers.read_text(encoding="utf8")
        if not NOINDEX_HEADER.search(original):
            raise ValueError("Expected isolated Draft X-Robots-Tag noindex header is missing; refusing to guess")
        report["review_global_noindex_present_before"]=True
        clean=NOINDEX_HEADER.sub("",original)
        clean="\n".join(line for line in clean.splitlines() if line.strip())+"\n"
        candidate=opts.headers_candidate.read_text(encoding="utf8")
        # Whitespace may differ, but every meaningful header and top-level path must remain.
        if [x.strip() for x in clean.splitlines()] != [x.strip() for x in candidate.splitlines() if x.strip()]:
            raise ValueError("Production _headers does not match prior reviewed candidate")
        if "X-Robots-Tag" in clean or not clean.lstrip().startswith("/*"):
            raise ValueError("Unsafe or malformed Production _headers output")
        # Match the exact audited Production candidate. Do not invent extra
        # response headers absent from the frozen site; changes to security
        # policy require their own review and should not be release blockers.
        for required in ("X-Content-Type-Options", "Referrer-Policy"):
            if required not in clean:raise ValueError("Lost previously approved response header "+required)
        headers.write_text(clean,encoding="utf8")
        report["production_global_noindex_removed"]=True
        files=sorted(root.glob("*.html"))
        if len(files)!=158573:raise ValueError("Unexpected HTML count "+str(len(files)))
        generated=[p for p in files if p.name not in ("index.html","404.html")]
        if len(generated)!=158571:raise ValueError("Unexpected generated page count")
        station_modes=("-mid-tutor.html","-high-tutor.html","-elem-conv.html")
        for idx,p in enumerate(generated):
            raw=p.read_text(encoding="utf8",errors="replace")
            if PREVIEW_HOST in raw:
                raise ValueError("Draft hostname leaked into final Production HTML: "+p.name)
            canonical=CANONICAL.findall(raw)
            if len(canonical)!=1 or canonical[0]!=BASE+"/"+p.name:
                raise ValueError("canonical mismatch or duplication: "+p.name)
            report["canonical_match"]+=1
            if len(TITLE.findall(raw))!=1:
                raise ValueError("title missing or duplicated: "+p.name)
            report["title_ok"]+=1
            if len(DESC.findall(raw))!=1:
                raise ValueError("description missing or duplicated: "+p.name)
            report["description_ok"]+=1
            og=OG.findall(raw)
            if len(og)!=1 or not og[0].startswith(BASE+"/assets/images/og-pages/"):
                raise ValueError("OG image source not Production domain or ambiguous: "+p.name)
            image_path=root/og[0].split(BASE+"/",1)[1]
            if not image_path.is_file():
                raise ValueError("OG image asset does not exist: "+p.name)
            report["og_meta_ok"]+=1
            robots=ROBOTS.findall(raw)
            if len(robots)!=1:
                raise ValueError("robots meta missing/duplicated: "+p.name)
            values={s.strip().lower() for s in robots[0].split(",")}
            if "index" in values and "noindex" in values:
                raise ValueError("contradictory robots meta "+p.name)
            if "noindex" in values:
                report["noindex"]+=1
                if p.name.startswith("station-") and p.name.endswith(station_modes):
                    report["new_student_noindex"]+=1
            else:
                report["indexable"]+=1
            if (idx+1)%35000==0:
                print("PRODUCTION_ARCHIVE_PAGE_CHECK",idx+1,"index",report["indexable"],"noindex",report["noindex"],flush=True)
        report["generated_count"]=len(generated)
        if (report["indexable"],report["noindex"])!=(21964,136607):
            raise ValueError("index/noindex totals changed from approved SEO QA "+str((report["indexable"],report["noindex"])))
        for path in ("robots.txt","sitemap-index.xml","pilot.css","assets/styles.css"):
            target=root/path
            if not target.is_file():raise ValueError("Production required asset missing: "+path)
            report["site_files_sha256"][path]=digest(target)
        robots=(root/"robots.txt").read_text(encoding="utf8")
        if "Sitemap: https://englishpt.kr/sitemap-index.xml" not in robots:
            raise ValueError("Production robots.txt missing sitemap")
        if "Disallow: /" in robots:raise ValueError("Production crawling blocked globally")
        report["site_files_sha256"]["_headers"]=digest(headers)
        report["status"]="PASS_V2351_PRODUCTION_RELEASE_GATED_AND_AUDITED"
    except Exception:
        report["error_count"]+=1
        report["errors"].append(traceback.format_exc()[-2000:])
        report["status"]="HOLD_V2351_PRODUCTION_RELEASE"
    finally:
        opts.report.parent.mkdir(parents=True,exist_ok=True)
        opts.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print(report["status"],"pages",report["generated_count"],"index",report["indexable"],
              "noindex",report["noindex"],"errors",report["error_count"],flush=True)
    return 0 if report["status"].startswith("PASS") else 1

if __name__=="__main__":sys.exit(main())
