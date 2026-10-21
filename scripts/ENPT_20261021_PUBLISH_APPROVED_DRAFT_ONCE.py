#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Once-only, fail-closed Netlify promotion of a user-approved exact Draft.
No new deploy creation. No GitHub source, form, robots, sitemap, or asset mutation.
Runs only on isolated release branch, and uses existing NETLIFY_AUTH_TOKEN secret.
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
DOMAIN="englishpt.kr"
EXPECTED_OLD="6ad7506cdeb778280a54ee2a"
TARGET="6ad87e6bd3bc041359320392"
MARKER="ENPT-20261021-MINIMAL-PROD-OG-FOUR-FIXES-ONLY"
PREVIEW="https://enptminimalfix20261021--englishpt-seo.netlify.app"
LIVE="https://englishpt.kr"
OUT=Path("release-20261021-prod-evidence")
OUT.mkdir(exist_ok=True)
TOKEN=os.environ["NETLIFY_AUTH_TOKEN"].strip()
assert TOKEN and len(TOKEN)>20, "HOLD_AUTH_UNAVAILABLE"
API="https://api.netlify.com/api/v1/"
report={"status":"HOLD_NOT_STARTED","candidate":TARGET,
        "production_expected_before":EXPECTED_OLD,
        "site_id":SITE,"preview":PREVIEW,"production":LIVE,
        "post_count":0,"new_deploys_created":0,"form_submissions":0,
        "checks":[],"errors":[],"utc":dt.datetime.now(dt.timezone.utc).isoformat()}
def persist():
    (OUT/"EXACT_DRAFT_ONE_TIME_PROMOTION.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def api_get(p):
    req=urllib.request.Request(API+p,method="GET",
      headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=35) as f:return json.load(f)
def http_get(base,path):
    req=urllib.request.Request(base+path,method="GET",
         headers={"User-Agent":"Mozilla/5.0 (compatible; ENPTProductionReleaseCheck/1.0)"})
    with urllib.request.urlopen(req,timeout=32) as response:
        body=response.read(3_000_000).decode("utf8","replace")
        h={k.lower():v for k,v in response.headers.items()}
        status=response.status
    return {"status":status,"path":path,"sha256":hashlib.sha256(body.encode()).hexdigest(),
        "length":len(body),"headers":h,"body":body}
def check_public(base,stage):
    paths=["/","/englishpt.html","/student-english.html",
      "/english-conversation.html","/guides/international-school-english.html",
      "/guides/senior-english.html","/courses.html","/exam-english.html",
      "/stations.html","/ulsan-buk-nongso2dong-mid-tutor.html",
      "/ulsan-buk-nongso2dong-high-conv.html",
      "/seoul-jongno-sajikdong-high-tutor.html","/robots.txt","/sitemap-index.xml"]
    for path in paths:
        item=http_get(base,path); html=path.endswith(".html") or path=="/"
        row={"phase":stage,"path":path,"http":item["status"],
          "bytes":item["length"],"sha256":item["sha256"]}
        content=item["body"]
        assert item["status"]==200,("HTTP",stage,path,item["status"])
        if html:
            assert '<link rel="canonical"' in content,("CANONICAL",stage,path)
            assert 'property="og:image"' in content,("OG",stage,path)
            assert ('name="englishpt-consultation"' in content or "name='englishpt-consultation'" in content) and '<form' in content,("FORM",stage,path)
            assert not re.search(r'<meta\s+name="robots"\s+content="[^"]*noindex',content,re.I) or path.startswith("/guides/") or path.startswith("/ulsan-") or path.startswith("/seoul-jongno-"),("UNEXPECTED_NOINDEX",path)
            assert 'noindex' not in item["headers"].get("x-robots-tag","").lower(),("HEADER_NOINDEX",path)
            assert '잉글리시GO' not in content and 'ENGLISH GO' not in content,("BRAND_DRIFT",path)
            if path.startswith("/guides/"):
                assert '<meta name="robots" content="noindex,follow">' in content,("GUIDE_NOINDEX",path)
            row["canonical"]=True;row["og"]=True;row["form"]=True
        if path=="/robots.txt":
            assert "User-agent:" in content, "ROBOTS_USER_AGENT"
            assert "Disallow: /" not in content, "ROBOTS_BLOCKS_ALL"
            row["robots_all_blocked"]=False
        if path=="/sitemap-index.xml":
            root=ET.fromstring(content)
            count=sum(1 for el in root.iter() if el.tag.endswith("loc"))
            assert count==44,("SITEMAP_SHARD_COUNT",count)
            row["child_sitemaps"]=count
        if path in ("/","/englishpt.html"):
            assert 'google-site-verification' in content and 'naver-site-verification' in content,("OWNERSHIP_META",path)
            row["both_verification_tags"]=True
        report["checks"].append(row);persist()

def site_checked():
    site=api_get("sites/"+SITE)
    assert site.get("id")==SITE,("SITE_ID_MISMATCH",site.get("id"))
    assert site.get("custom_domain")==DOMAIN,("DOMAIN_MISMATCH",site.get("custom_domain"))
    pub=(site.get("published_deploy") or {}).get("id")
    return pub
try:
    current=site_checked()
    report["published_before"]=current
    if current==TARGET:
        # An earlier authorized execution may already have published; never POST twice.
        report["status"]="ALREADY_PUBLISHED_NO_POST_RECHECK"
        check_public(LIVE,"already_published_live")
        report["published_after"]=site_checked()
        assert report["published_after"]==TARGET
        report["status"]="PASS_ALREADY_PUBLISHED_NO_DUPLICATE_POST"
        persist()
        print("ENPT_EXACT_DEPLOY_ALREADY_PUBLISHED_NO_SECOND_RESTORE",json.dumps(
            {k:v for k,v in report.items() if k!="checks"},ensure_ascii=False),flush=True)
        sys.exit(0)
    assert current==EXPECTED_OLD,("UNEXPECTED_EXISTING_PRODUCTION",current)
    deploy=api_get("sites/"+SITE+"/deploys/"+TARGET)
    report["draft_gate"]={k:deploy.get(k) for k in ("id","site_id","state","title","draft","published_at","context","deploy_ssl_url","locked")}
    assert deploy.get("id")==TARGET and deploy.get("site_id")==SITE, "DRAFT_OWNERSHIP"
    assert deploy.get("state")=="ready","DRAFT_NOT_READY"
    assert deploy.get("title")==MARKER,("DRAFT_MARKER_NOT_EXACT",deploy.get("title"))
    assert deploy.get("published_at") is None, "DRAFT_ALREADY_PUBLISHED_OUTSIDE_EXPECTED_SITE_STATE"
    check_public(PREVIEW,"before_preview")
    report["status"]="PRECHECK_PASSED_READY_TO_POST"
    persist()
    assert site_checked()==EXPECTED_OLD,"PRODUCTION_CHANGED_DURING_PREFLIGHT"
    print("ENPT_EXACT_DRAFT_RELEASE_PREFLIGHT_PASS",flush=True)
    # Exactly ONE requested Netlify state change: publish the already-uploaded
    # atomic draft. Never auto-retry this POST on timeouts or HTTP errors.
    req=urllib.request.Request(API+f"sites/{SITE}/deploys/{TARGET}/restore",
          data=b"",method="POST",headers={
          "Authorization":"Bearer "+TOKEN,"Accept":"application/json",
          "Content-Type":"application/json"})
    report["post_count"]=1
    report["status"]="RESTORE_POST_INFLIGHT"
    persist()
    with urllib.request.urlopen(req,timeout=70) as response:
        report["restore_http"]=response.status
        data=response.read(2_000_000).decode("utf8","replace")
    assert report["restore_http"] in (200,201,202),("RESTORE_RESPONSE",report["restore_http"])
    report["restore_response_id"]=json.loads(data).get("id") if data.strip().startswith("{") else None
    report["status"]="POST_RETURNED_VERIFYING"
    persist()
    for _ in range(8):
        if site_checked()==TARGET:break
        time.sleep(2)
    report["published_after"]=site_checked()
    assert report["published_after"]==TARGET,("TARGET_NOT_PUBLISHED",report["published_after"])
    report["status"]="PUBLISHED_HTTP_QA_RUNNING"
    persist()
    check_public(LIVE,"after_production")
    report["published_after_final"]=site_checked()
    assert report["published_after_final"]==TARGET,"PRODUCTION_CHANGED_AFTER_PUBLISH"
    report["status"]="PASS_EXACT_DRAFT_PUBLISHED_ONCE_LIVE_HTTP_ROBOTS_OG_CANONICAL_FORMS_VERIFIED"
except Exception as e:
    report["errors"].append(repr(e)[:1200])
    report["status"]="HOLD_RELEASE_ERROR_INSPECT_CURRENT_PRODUCTION"
    persist()
    print("ENPT_PRODUCTION_RELEASE_HOLD",json.dumps(
        {k:v for k,v in report.items() if k!="checks"},ensure_ascii=False),flush=True)
    raise
else:
    persist()
    print("ENPT_EXACT_DRAFT_PUBLISHED_ONCE_SUCCESS",json.dumps(
        {k:v for k,v in report.items() if k!="checks"},ensure_ascii=False),flush=True)
