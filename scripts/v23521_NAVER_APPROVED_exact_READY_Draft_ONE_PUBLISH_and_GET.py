#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One user-approved Netlify restore; no file upload, no form POST, no retry.
Publication is separate from Naver Search Advisor ownership confirmation.
"""
import datetime
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
BEFORE="6ad5dce289bf03bfba2b534c"
TARGET="6ad5eb4918f9411c4d5e1ba4"
PREVIOUS="6ad5ca0f1f2051f04bdd9287"
ORIGINAL="6ac4bd517c30220008bb9661"
MARKER="ENPT-NAVER-META-PRESERVE-GOOGLE-ONE-DRAFT-20261019"
DRAFT="https://enptnavermetaonce19--englishpt-seo.netlify.app"
GOOGLE=b'<meta name="google-site-verification" content="OTG-5ooTZYTm-HnTOi8I0TRV4bZHUD-uSYSOih3E8ig" />'
NAVER=b'<meta name="naver-site-verification" content="340f4e7dc8c5f3ec806e68f6f09b9949f941a0de" />'
EXPECTED_SHA="6d0272d1601a1a47abeccc4d740359af9e7678293ee0a3d257eecd2ca478d884"
OUT=pathlib.Path("publish-evidence")
OUT.mkdir(exist_ok=True)
TOKEN=os.environ.get("NETLIFY_AUTH_TOKEN","")

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def save(name, body):
    (OUT/name).write_text(json.dumps(body,ensure_ascii=False,indent=2)+"\n",encoding="utf8")

def api_get(path):
    if not TOKEN: raise RuntimeError("Missing configured Netlify authentication")
    req=urllib.request.Request("https://api.netlify.com/api/v1/"+path,
      headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"},method="GET")
    with urllib.request.urlopen(req,timeout=40) as response:
        return json.load(response)

def http_get(base,path):
    req=urllib.request.Request(base+path,headers={"User-Agent":"ENPT-NAVER-APPROVED-PREPOST-READONLY"},method="GET")
    with urllib.request.urlopen(req,timeout=40) as response:
        if response.status!=200:raise ValueError("Non-200 "+path)
        if urlsplit(response.geturl()).hostname!=urlsplit(base).hostname:
            raise ValueError("Unexpected redirected host "+path)
        return response.read(800000),dict(response.headers)

def check_dual_meta(base,live=False):
    checks=[]
    for p in ("/index.html","/englishpt.html"):
        b,h=http_get(base,p)
        head=re.search(rb"<head\b[^>]*>(.*?)</head>",b,re.I|re.S)
        if not head or head.group(1).count(GOOGLE)!=1 or head.group(1).count(NAVER)!=1:
            raise ValueError("Google/Naver exact once meta missing from HEAD "+p)
        if "text/html" not in h.get("Content-Type","").lower():
            raise ValueError("Wrong HTML type "+p)
        if b'<link rel="canonical" href="https://englishpt.kr/englishpt.html"' not in b:
            raise ValueError("Main canonical missing "+p)
        if live and "noindex" in h.get("X-Robots-Tag","").lower():
            raise ValueError("Global X-Robots noindex on live home "+p)
        checks.append(p)
    for p in ("/robots.txt","/sitemap-index.xml","/gyeongnam-milyang-naeidong-elem-tutor.html"):
        b,_=http_get(base,p)
        if p=="/robots.txt" and re.search(rb"(?m)^\s*Disallow:\s*/\s*$",b):
            raise ValueError("Robots globally disallow")
        if p=="/sitemap-index.xml" and b"sitemapindex" not in b:
            raise ValueError("Sitemap index malformed")
        if p.endswith("elem-tutor.html") and b'name="englishpt-consultation"' not in b:
            raise ValueError("Tutor form missing")
        checks.append(p)
    return checks

def safe_inputs():
    path=pathlib.Path("qa-map/FINAL_NAVER_GOOGLE_VERIFICATION_META_QA.json")
    if not path.is_file():raise ValueError("Missing signed-off source QA record")
    qa=json.loads(path.read_text("utf8"))
    expected={
      "status":"PASS_2_HOME_NAVER_GOOGLE_TAG_180800_FULL_SOURCE_QA",
      "new_candidate_sha256":EXPECTED_SHA,
      "all_files_SHA1_verified":180800,
      "original_public_urls":158571,
      "indexable":21964,
      "noindex":136607,
      "sitemap_url_count":21964,
      "unchanged_files":180798,
      "Google_meta_preserved":True,
      "Naver_meta_added_exactly_once":True,
      "preserved_44_sitemap_shards":True,
      "preserved_netlify_Forms":True,
    }
    for key,value in expected.items():
        if qa.get(key)!=value:raise ValueError("QA source guard mismatch "+key)
    if not pathlib.Path("qa-map/NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz").is_file():
        raise ValueError("Missing full SEO per-page immutable manifest")
    return qa

def run():
    evidence={"checked_utc":now(),"approved_user_one_publish":True,
        "site_id":SITE,"baseline":BEFORE,"target":TARGET,
        "production_changed_by_new_file_upload":False,
        "file_upload_count":0,"real_consultation_POST_count":0,"publish_POST_count":0,
        "errors":[],"status":"HOLD_SAFE_NO_NETLIFY_POST"}
    try:
        if os.environ.get("NAVER_ONE_PUBLISH_APPROVED")!="EXPLICIT_USER_APPROVED_20261019_NAVER_TWO_META":
            raise ValueError("One-time user authorization missing")
        if not TOKEN:raise ValueError("Missing Netlify GitHub secret")
        safe_inputs()
        site=api_get("sites/"+SITE)
        live=(site.get("published_deploy") or {}).get("id")
        evidence["published_before"]=live
        if site.get("id")!=SITE or site.get("custom_domain")!="englishpt.kr":
            raise ValueError("Production site identity mismatch")
        if live!=BEFORE:raise ValueError("Production changed since review: HOLD WITHOUT POST")
        if (site.get("processing_settings") or {}).get("ignore_html_forms") is not False:
            raise ValueError("Netlify Forms disabled")
        for d in (BEFORE,PREVIOUS,ORIGINAL):
            rollback=api_get("sites/"+SITE+"/deploys/"+d)
            if rollback.get("state")!="ready":raise ValueError("Missing READY rollback "+d)
        draft=api_get("sites/"+SITE+"/deploys/"+TARGET)
        if draft.get("id")!=TARGET or draft.get("site_id")!=SITE or draft.get("state")!="ready" or draft.get("published_at"):
            raise ValueError("Draft not READY/unpublished")
        title=str(draft.get("title") or "")+" "+str(draft.get("name") or "")+" "+str(draft.get("deploy_ssl_url") or "")
        if MARKER not in title and "enptnavermetaonce19" not in title:
            raise ValueError("Unexpected new Draft marker")
        deploys=api_get("sites/"+SITE+"/deploys?per_page=100")
        marker_hits=[d for d in deploys if MARKER in str(d.get("title") or "") or
              "enptnavermetaonce19" in str(d.get("deploy_ssl_url") or "")]
        if len(marker_hits)!=1 or marker_hits[0].get("id")!=TARGET:
            raise ValueError("Another similar deploy exists: block duplicate publishing")
        account=api_get("accounts/"+site["account_id"])
        credit=(account.get("capabilities") or {}).get("credits") or {}
        remaining=credit.get("included",0)-credit.get("used",0)
        evidence["credits_remaining_before"]=remaining
        if remaining<=0 or account.get("in_operational_mode") is True or account.get("usages_exceeded") or account.get("configurable_limits_exceeded"):
            raise ValueError("Netlify limits are not clear")
        forms=api_get("sites/"+SITE+"/forms")
        if "englishpt-consultation" not in [x.get("name") for x in forms]:
            raise ValueError("Expected registration form missing")
        hooks=api_get("hooks?site_id="+SITE)
        if not any(h.get("type")=="email" and h.get("event")=="submission_created" for h in hooks):
            raise ValueError("Email notification hook missing")
        evidence["draft_GET_checks"]=check_dual_meta(DRAFT,live=False)
        evidence["status"]="GO_ALL_PREPUBLISH_READONLY_GATES_PASS"
        save("00_PREPUBLISH_GATE.json",evidence.copy())
    except Exception as err:
        evidence["status"]="HOLD_NO_POST_FAILED_PREPUBLISH"
        evidence["errors"].append(type(err).__name__+": "+str(err)[:260])
        save("01_PUBLISH_RESULT.json",evidence)
        print("HOLD_NAVER_NO_PUBLICATION",json.dumps(evidence,ensure_ascii=False),flush=True)
        return 1
    # Exactly one Netlify RESTORE request to publish pre-existing READY deploy.
    # Marker is persisted *before* making the POST; never retry on ambiguous errors.
    evidence["publish_POST_count"]=1
    evidence["status"]="POST_ATTEMPT_RECORDED_NO_RETRY"
    save("00_EXACT_ONE_POST_MARKER.json",evidence.copy())
    try:
        req=urllib.request.Request(
           "https://api.netlify.com/api/v1/sites/"+SITE+"/deploys/"+TARGET+"/restore",
           method="POST",data=b"",
           headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=45) as response:
            evidence["restore_http_status"]=response.status
    except urllib.error.HTTPError as err:
        evidence["errors"].append("RESTORE_HTTP_"+str(err.code)+"_verify_via_GET_no_retry")
    except Exception as err:
        evidence["errors"].append("RESTORE_UNCERTAIN_"+type(err).__name__+"_verify_via_GET_no_retry")
    # Only GET from here onwards; no second POST, even on uncertain response.
    try:
        for attempt in range(12):
            s=api_get("sites/"+SITE)
            evidence["published_after"]=(s.get("published_deploy") or {}).get("id")
            if evidence["published_after"]==TARGET:
                evidence["status"]="PASS_APPROVED_ONE_NETLIFY_DRAFT_PUBLISHED"
                break
            if evidence["published_after"]!=BEFORE:
                evidence["status"]="HOLD_UNEXPECTED_DEPLOY_PUBLISHED"
                break
            if attempt<11:time.sleep(3)
        else:
            evidence["status"]="HOLD_PUBLISH_NOT_CONFIRMED_NO_RETRY"
    except Exception as err:
        evidence["status"]="HOLD_POST_RETURN_CHECK_ERROR_NO_RETRY"
        evidence["errors"].append(type(err).__name__+": "+str(err)[:260])
    save("01_PUBLISH_RESULT.json",evidence)
    print("NAVER_APPROVED_ONE_POST_ACTUAL",json.dumps(evidence,ensure_ascii=False),flush=True)
    return 0 if evidence["status"]=="PASS_APPROVED_ONE_NETLIFY_DRAFT_PUBLISHED" else 1

def verify():
    r={"checked_utc":now(),"target":TARGET,"status":"HOLD","issues":[],
      "form_posts":0,"netlify_mutations":0}
    try:
        s=api_get("sites/"+SITE)
        r["published_id"]=(s.get("published_deploy") or {}).get("id")
        if r["published_id"]!=TARGET or s.get("custom_domain")!="englishpt.kr":
            raise ValueError("Unexpected production deployment after publish")
        r["live_GET_checks"]=check_dual_meta("https://englishpt.kr",live=True)
        forms=api_get("sites/"+SITE+"/forms")
        hooks=api_get("hooks?site_id="+SITE)
        r["consultation_registered"]="englishpt-consultation" in [f.get("name") for f in forms]
        r["email_hook_count"]=sum(1 for h in hooks if h.get("type")=="email" and h.get("event")=="submission_created")
        if not r["consultation_registered"] or r["email_hook_count"]<1:
            raise ValueError("Forms or existing email event hook missing")
        r["status"]="PASS_NAVER_GOOGLE_DUAL_META_LIVE_AND_FORMS"
    except Exception as err:
        r["status"]="HOLD_POSTPUBLISH_LIVE_META_FORMS"
        r["issues"].append(type(err).__name__+": "+str(err)[:300])
    save("02_LIVE_DUAL_META_FORMS.json",r)
    print("NAVER_POSTPUBLISH_LIVE_META",json.dumps(r,ensure_ascii=False),flush=True)
    return 0 if r["status"].startswith("PASS_") else 1

if __name__=="__main__":
    if len(sys.argv)!=2 or sys.argv[1] not in ("publish","verify"):
        raise SystemExit("Usage: python script.py publish|verify")
    raise SystemExit(run() if sys.argv[1]=="publish" else verify())
