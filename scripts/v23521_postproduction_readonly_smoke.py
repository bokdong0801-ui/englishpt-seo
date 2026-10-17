#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ENGLISH PT post-Production GET/HEAD-only verification. Never deploys, POSTs, or submits.
Call AFTER separately approved Production deployment, with exact expected deploy ID.
"""
import hashlib, json, os, re, struct, sys, urllib.error, urllib.request
from pathlib import Path
from urllib.parse import urlsplit
ROOT="https://englishpt.kr"
EXPECTED_JS_SHA="d604994a74352a81978002fd6f6286c7d0f4f4c99278745bbf6dad1abce29ede"
SITE_ID="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
OG=("beginner toeic ielts toefl opic tos duolingo elementary middle high "
"student worker college jobseeker housewife stations region academy tutor "
"conversation exam courses englishpt reading writing international phone video general").split()
SLUGS=("gyeongnam-milyang-naeidong","seoul-jongno-sajikdong")
GRADES=("elem-tutor","mid-tutor","high-tutor")
OUT=Path("postproduction-readonly-qa")
OUT.mkdir(exist_ok=True)
def get(path, headers=None, cap=300000):
    url=(ROOT+path) if path.startswith("/") else path
    request=urllib.request.Request(url,headers=headers or {},method="GET")
    with urllib.request.urlopen(request, timeout=30) as r:
        # NO cookies submitted, no actual form POST, no personal data accessed.
        return r.status,r.headers,r.read(cap),r.geturl()
def fail(errors,which,desc):
    errors.append({"where":which,"error":desc[:220]})
def main():
    expected=os.environ.get("EXPECTED_PUBLISHED_DEPLOY_ID","")
    consent=os.environ.get("READONLY_QA_APPROVAL","")
    record={"status":"HOLD_POSTPRODUCTION_GET_ONLY","checks":[],
      "errors":[],"production_deployed_by_this_job":False,
      "form_submitted":False,"search_submitted":False,
      "email_delivered_verified":False,"expected_published_deploy_id":expected}
    try:
        assert re.fullmatch(r"[a-f0-9]{24,32}",expected), "Production deploy ID not supplied"
        assert consent=="READ-ONLY-SMOKE", "Manual read-only approval missing"
        token=os.environ.get("NETLIFY_AUTH_TOKEN","")
        assert token, "Netlify API token missing"
        status,h,data,final=get("https://api.netlify.com/api/v1/sites/"+SITE_ID,
          {"Authorization":"Bearer "+token,"Accept":"application/json"},cap=350000)
        site=json.loads(data)
        actual=(site.get("published_deploy") or {}).get("id")
        assert actual==expected,("Current published deploy changed, STOP",actual,expected)
        record["checks"].append("current_published_deploy_matches_expected_id")
        basic=("/", "/englishpt.html", "/courses.html", "/exam-english.html",
          "/english-conversation.html", "/student-english.html",
          "/robots.txt", "/sitemap-index.xml", "/pilot.js")
        docs={}
        for p in list(basic)+["/"+s+"-"+g+".html" for s in SLUGS for g in GRADES]:
            try:
                status,h,data,final=get(p)
                if status!=200 or urlsplit(final).hostname not in ("englishpt.kr","www.englishpt.kr"):
                    fail(record["errors"],p,"Wrong HTTP 200/host")
                if p=="/pilot.js":
                    digest=hashlib.sha256(data).hexdigest()
                    if digest!=EXPECTED_JS_SHA:
                        fail(record["errors"],p,"JS SHA mismatch "+digest)
                elif p=="/robots.txt":
                    if b"Sitemap: https://englishpt.kr/sitemap-index.xml" not in data:
                        fail(record["errors"],p,"Sitemap directive absent")
                    if re.search(rb"(?m)^\s*Disallow:\s*/\s*$",data):
                        fail(record["errors"],p,"Blocked all crawling")
                elif p=="/sitemap-index.xml":
                    if b"<sitemapindex" not in data and b":sitemapindex" not in data:
                        fail(record["errors"],p,"Expected sitemap index XML")
                elif p.endswith(".html") and ("-tutor" in p):
                    text=data.decode("utf8",errors="replace")
                    if "영어과외 상담 신청" not in text:fail(record["errors"],p,"Tutor CTA phrase missing")
                    canonical="https://englishpt.kr"+p
                    if canonical not in text:fail(record["errors"],p,"Canonical/local path missing")
                docs[p]={"status":status,"content_type":h.get("Content-Type"),
                         "global_x_robots":h.get("X-Robots-Tag")}
            except Exception as exc:fail(record["errors"],p,type(exc).__name__+" "+str(getattr(exc,"code","")))
        record["site_results"]=docs
        if len(docs)==len(basic)+6 and not record["errors"]:
            record["checks"].append("all_15_selected_site_http_and_js_canonical")
        image_checks=0
        for key in OG:
            p="/assets/images/og-pages/"+key+".png"
            try:
                status,_,data,_=get(p,cap=30)
                if status!=200 or len(data)<24 or data[:8]!=bytes.fromhex("89504e470d0a1a0a"):
                    fail(record["errors"],p,"OG PNG HTTP/signature fail")
                elif struct.unpack(">II",data[16:24])!=(1200,630):
                    fail(record["errors"],p,"OG dimensions not 1200x630")
                else:image_checks+=1
            except Exception as exc:fail(record["errors"],p,type(exc).__name__)
        record["og_200_1200x630"]=image_checks
        if image_checks==29:record["checks"].append("29_production_og_images")
        # Read form / hook configuration only. Do not fetch real user submissions.
        headers={"Authorization":"Bearer "+token,"Accept":"application/json"}
        status,_,d,_=get("https://api.netlify.com/api/v1/sites/"+SITE_ID+"/forms",headers)
        forms=json.loads(d)
        status,_,d,_=get("https://api.netlify.com/api/v1/hooks?site_id="+SITE_ID,headers)
        hooks=json.loads(d)
        matched=[x for x in forms if x.get("name")=="englishpt-consultation"]
        emails=[x for x in hooks if x.get("event")=="submission_created" and x.get("type")=="email"]
        record["form_metadata"]={"expected_form_registered":bool(matched),"email_notification_hook_exists":bool(emails),
                                 "actual_test_submission_done":False,"email_delivery_confirmed":False}
        if not matched:fail(record["errors"],"forms","Production form not registered; do not test POST yet")
        if not emails:fail(record["errors"],"hooks","Email notification missing")
        record["status"]="PASS_POSTPRODUCTION_GET_ONLY_READY_FOR_AUTHORIZED_FORM_TEST" if not record["errors"] else "HOLD_POSTPRODUCTION_GET_ONLY"
    except Exception as exc:
        fail(record["errors"],"fatal",type(exc).__name__+" "+str(exc))
    (OUT/"RESULT.json").write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(record["status"],"checks",record["checks"],"errors",record["errors"],flush=True)
    return 0 if record["status"].startswith("PASS_") else 1
if __name__=="__main__":sys.exit(main())
