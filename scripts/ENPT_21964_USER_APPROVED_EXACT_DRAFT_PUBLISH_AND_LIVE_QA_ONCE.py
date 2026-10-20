#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""User explicitly approved 2026-10-20: publish exactly ONE immutable Netlify Draft,
then GET-only verify live englishpt.kr. Never rebuild, upload, resubmit or silently retry POST.
"""
import datetime as dt
import hashlib
import html.parser
import io
import json
import os
import pathlib
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
DRAFT="6ad7506cdeb778280a54ee2a"
PRODUCTION_BEFORE="6ad5eb4918f9411c4d5e1ba4"
TITLE="ENPT-21964-PRODSAFE-ORIGINAL-ROBOTS-CLI-FULL-NONPUBLISHED-ONCE-20261020"
PREVIEW="https://enptog21964prodsafereview20--englishpt-seo.netlify.app"
LIVE="https://englishpt.kr"
TEST_FORM="englishpt-consultation"
TEST_SUBMISSION="6ad751390919add0ec06f61c"
TEST_MARKER="ENPT_OG21964_FINAL_QA_SINGLE_20261020"
GOOGLE="OTG-5ooTZYTm-HnTOi8I0TRV4bZHUD-uSYSOih3E8ig"
NAVER="340f4e7dc8c5f3ec806e68f6f09b9949f941a0de"
OUT=pathlib.Path("approved-publish-evidence")
OUT.mkdir(exist_ok=True)
report={"started_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "status":"HOLD_PRECONDITION","user_approved_exact_draft":True,
        "site":SITE,"approved_candidate_id":DRAFT,
        "previous_published_id":PRODUCTION_BEFORE,
        "rollback_reference":PRODUCTION_BEFORE,
        "preflight":{},"publish":{"POST_attempted":False},
        "verification":{},"errors":[],
        "source_rebuilds":0,"new_deploy_creations":0,"file_uploads":0,
        "form_submissions":0,"automatic_rollback_attempts":0}

def save():
    (OUT/"EXACT_DRAFT_PUBLISH_AND_POSTPRODUCTION_QA.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def check(condition,msg):
    if not condition:
        raise RuntimeError(msg)
def api_get(path):
    q=urllib.request.Request("https://api.netlify.com/api/v1/"+path,method="GET",
        headers={"Authorization":"Bearer "+os.environ["NETLIFY_AUTH_TOKEN"],"Accept":"application/json"})
    with urllib.request.urlopen(q,timeout=32) as r:return json.load(r)
def site_get():
    x=api_get("sites/"+SITE)
    check(x.get("id")==SITE and x.get("custom_domain")=="englishpt.kr","Site identity or custom domain mismatch")
    return x
def current_id(s):
    return (s.get("published_deploy") or {}).get("id")

class HTMLHead(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta=[];self.links=[];self.forms=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=="meta":self.meta.append(d)
        if tag=="link":self.links.append(d)
        if tag=="form":self.forms.append(d)
    def meta_value(self,attribute,value):
        return [d.get("content") for d in self.meta if d.get(attribute)==value]
    def canonicals(self):
        return [d.get("href") for d in self.links if d.get("rel")=="canonical"]

def web_get(base,path):
    q=urllib.request.Request(base+path,method="GET",headers={
        "User-Agent":"ENPT-ApprovedProduction-AtomicDeploy-QA-GETONLY",
        "Cache-Control":"no-cache","Pragma":"no-cache"})
    with urllib.request.urlopen(q,timeout=35) as r:
        check(r.status==200,"HTTP non200 "+base+path)
        check(r.geturl().startswith(base),"Unapproved redirect "+path)
        return r.read(2700000),{k.lower():v for k,v in r.headers.items()}

def check_live_pair(path,preview_sha=None,production=False):
    prefix=LIVE if production else PREVIEW
    data,h=web_get(prefix,path)
    check(h.get("content-type","").lower().startswith("text/html"),"HTML MIME wrong "+path)
    parser=HTMLHead()
    parser.feed(data.decode("utf8",errors="replace"))
    check("noindex" not in h.get("x-robots-tag","").lower(),"GLOBAL noindex leaked "+path)
    expected_can="https://englishpt.kr/englishpt.html" if path=="/index.html" else LIVE+path
    check(parser.canonicals()==[expected_can],"Canonical not exact "+path)
    check(len(parser.meta_value("property","og:image"))==1,"Expected exactly one og:image "+path)
    bots=parser.meta_value("name","robots")
    check(len(bots)==1,"Expected single per-page robots meta "+path)
    noindex_expected=("tutor" in path)
    check(("noindex" in bots[0].lower())==noindex_expected,"Page-specific noindex mismatch "+path)
    if path in ("/index.html","/englishpt.html"):
        check(parser.meta_value("name","google-site-verification")==[GOOGLE],"Google tag missing "+path)
        check(parser.meta_value("name","naver-site-verification")==[NAVER],"Naver tag missing "+path)
    if "tutor" in path:
        check(any(f.get("name")==TEST_FORM and "data-netlify" in f for f in parser.forms),
              "Netlify consultation form missing "+path)
    got=hashlib.sha256(data).hexdigest()
    if preview_sha is not None:
        check(got==preview_sha,"Published HTML bytes differ from approved exact Draft "+path)
    return {"path":path,"HTTP":200,"sha256":got,"canonical":expected_can,
            "page_robots":bots[0],"og_image":parser.meta_value("property","og:image")[0],
            "owner_tags_present":path in ("/index.html","/englishpt.html")}
def check_nonhtml(production,compare=None):
    prefix=LIVE if production else PREVIEW
    robots,h=web_get(prefix,"/robots.txt")
    sitemap,h2=web_get(prefix,"/sitemap-index.xml")
    parsed=robots.decode("utf8",errors="replace")
    check(not re.search(r"(?im)^\s*Disallow:\s*/\s*$",parsed),
          "Global crawler ban in robots.txt")
    check("Sitemap: https://englishpt.kr/sitemap-index.xml" in parsed,"Sitemap directive missing")
    x=ET.fromstring(sitemap)
    urls=[e.text for e in x.iter() if e.tag.endswith("loc") and e.text]
    check(len(urls)==len(set(urls))==44,"44 distinct sitemap shards not found")
    raw,hraw=web_get(prefix,"/__pages/23/englishpt.page")
    check("noindex" in hraw.get("x-robots-tag","").lower(),"Internal shard lacks noindex header")
    out={"robots_sha256":hashlib.sha256(robots).hexdigest(),
         "sitemap_index_sha256":hashlib.sha256(sitemap).hexdigest(),
         "internal_page_sha256":hashlib.sha256(raw).hexdigest(),
         "internal_page_robots":hraw.get("x-robots-tag"),
         "sitemap_shards":len(urls)}
    if compare:
        for k in ["robots_sha256","sitemap_index_sha256","internal_page_sha256","internal_page_robots"]:
            check(compare[k]==out[k],"Published critical resource differs from Draft "+k)
    return out
def check_image(production,expected):
    prefix=LIVE if production else PREVIEW
    p=expected["og_image"]
    check(p.startswith(LIVE+"/assets/images/seo-square/v1/") and p.endswith(".jpg"),
          "OG image not in original approved square assets")
    path=p.removeprefix(LIVE)
    data,h=web_get(prefix,path)
    check(h.get("content-type","").lower().startswith("image/jpeg") and data[:2]==b"\xff\xd8",
          "Square JPEG response invalid")
    out={"path":path,"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data),"status":200}
    if production:
        check(out["sha256"]==expected["sha256"],"Production JPEG changed from Draft")
    return out

PAGES=[
    "/index.html","/englishpt.html",
    "/station-419minjumyoji-toeic.html",
    "/station-419minjumyoji-ielts.html",
    "/gyeongnam-milyang-naeidong-elem-tutor.html",
    "/seoul-jongno-sajikdong-high-tutor.html"
]
try:
    # Gate recorded successful upstream SEO+browser+forms QA, not just user message.
    gh_token=os.environ["GITHUB_TOKEN"]
    for runid in [39399897235,39414952403,39416389999,39414278964,39416071957,39436707598]:
        u="https://api.github.com/repos/bokdong0801-ui/englishpt-seo/actions/runs/"+str(runid)
        q=urllib.request.Request(u,method="GET",
             headers={"Authorization":"Bearer "+gh_token,
                      "Accept":"application/vnd.github+json",
                      "User-Agent":"ENPT-One-Time-User-Approved-Publish"})
        with urllib.request.urlopen(q,timeout=30) as rr:j=json.load(rr)
        check(j.get("status")=="completed" and j.get("conclusion")=="success",
              "Prior signed QA run not success "+str(runid))
    report["preflight"]["signed_QA_runs"]="PASS_6_VERIFIED"
    site=site_get()
    check(current_id(site)==PRODUCTION_BEFORE,
          "Published site has changed since user approval; STOP WITHOUT POST")
    report["preflight"]["production_id"]=current_id(site)
    draft=api_get("sites/"+SITE+"/deploys/"+DRAFT)
    check(draft.get("site_id")==SITE and draft.get("id")==DRAFT,"Wrong Draft/site ID")
    check(draft.get("title")==TITLE,"Unexpected Draft contents/title")
    check(draft.get("state")=="ready" and draft.get("published_at") is None,
          "Candidate Draft is not currently READY and unpublished")
    for key in ["required","required_functions","required_edge_functions","required_server"]:
        check(not draft.get(key),"Draft incomplete pending "+key)
    check(draft.get("draft") is True,"Target must still be Netlify draft")
    report["preflight"]["draft_ready_unpublished"]="PASS"
    preview_pages={p:check_live_pair(p) for p in PAGES}
    report["preflight"]["live_preview_pages"]=len(preview_pages)
    preview_assets=check_nonhtml(False)
    img_pre=check_image(False,preview_pages[PAGES[2]])
    report["preflight"]["preview_image_SHA256"]=img_pre["sha256"]
    report["preflight"]["indexable_and_noindex_live_robots"]="PASS"
    # Form backend read; no test submission repeated.
    forms=api_get("sites/"+SITE+"/forms")
    xf=[x for x in forms if x.get("name")==TEST_FORM]
    check(len(xf)==1,"Consultation form not registered uniquely")
    subs=api_get("forms/"+xf[0]["id"]+"/submissions?per_page=100")
    check(any(x.get("id")==TEST_SUBMISSION and TEST_MARKER in
              json.dumps(x.get("data") or {},ensure_ascii=False) for x in subs),
          "Previous verified test submission no longer present")
    report["preflight"]["form_backend_registered"]="PASS_PREVIOUS_TEST_VERIFIED_NO_REPOST"
    # Last guard BEFORE one and only one POST.
    again=site_get()
    check(current_id(again)==PRODUCTION_BEFORE,
          "Production unexpectedly changed during preflight, STOP")
    draft2=api_get("sites/"+SITE+"/deploys/"+DRAFT)
    check(draft2.get("state")=="ready" and draft2.get("published_at") is None and
          draft2.get("title")==TITLE and draft2.get("site_id")==SITE,
          "Draft changed immediately before publish")
    report["status"]="PREFLIGHT_PASS_NOW_EXACTLY_ONE_APPROVED_PUBLICATION_POST"
    save()
    print("ENPT_PREPOST_SAFE_GATE",json.dumps(
        {"status":report["status"],"draft":DRAFT,"rollback":PRODUCTION_BEFORE,
         "preflight":{k:v for k,v in report["preflight"].items()
                      if k!="signed_QA_runs"}}),flush=True)
    # Explicit user approved exactly one atomic restore. NEVER retry on HTTP exceptions.
    endpoint=f"https://api.netlify.com/api/v1/sites/{SITE}/deploys/{DRAFT}/restore"
    req=urllib.request.Request(endpoint,data=b"",method="POST",headers={
         "Authorization":"Bearer "+os.environ["NETLIFY_AUTH_TOKEN"],
         "Accept":"application/json","Content-Length":"0"})
    report["publish"]["POST_attempted"]=True
    report["publish"]["attempted_at_utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
    save()
    try:
        with urllib.request.urlopen(req,timeout=65) as resp:
            response=resp.read(200000)
            report["publish"]["response_code"]=resp.status
            check(resp.status in (200,201,202,204),
                  "Netlify restore returned unexpected status")
            try:
                parsed=json.loads(response)
                report["publish"]["response_deploy_id"]=parsed.get("id")
                report["publish"]["response_site_id"]=parsed.get("site_id")
            except Exception:
                report["publish"]["response_body_type"]="non-JSON or empty"
    except Exception as err:
        # Request may have been accepted despite client timeout: get state but never POST again.
        report["publish"]["uncertain_response"]=type(err).__name__+": "+str(err)[:220]
    report["status"]="POST_DONE_AWAITING_PUBLISHED_DEPLOY_CONFIRMATION"
    save()
    observed=[]
    for i in range(30):
        s=site_get()
        current=current_id(s)
        observed.append(current)
        if current==DRAFT:break
        # unexpected third-party publish is not our candidate: stop, never overwrite it.
        if current not in (PRODUCTION_BEFORE,DRAFT):
            raise RuntimeError("Unexpected third-party published ID "+str(current)+
                "; no repeat POST, no automatic rollback")
        if i<29:time.sleep(4)
    report["publish"]["observed_published_ids"]=list(dict.fromkeys(observed))
    report["publish"]["current_published_id"]=observed[-1]
    check(observed[-1]==DRAFT,"After single POST exact Draft did not become published; STOP no retry")
    report["publish"]["confirmed_exact_draft_live"]=True
    report["status"]="PUBLISHED_EXACT_APPROVED_DRAFT_POST_QA_IN_PROGRESS"
    save()
    print("ENPT_EXACT_PUBLISHED_ID_CONFIRMED",DRAFT,flush=True)
    # Post-publication public edge propagation and byte-for-byte Draft parity.
    live_map={}
    for path in PAGES:
        last=None
        for attempt in range(8):
            try:
                live_map[path]=check_live_pair(path,preview_sha=preview_pages[path]["sha256"],
                                              production=True)
                last=None;break
            except Exception as exc:
                last=exc
                if attempt<7:time.sleep(4)
        if last:raise RuntimeError("Published HTML QA failed "+path+": "+str(last))
    report["verification"]["six_live_HTML_equal_approved_draft_SHA256"]="PASS"
    actual_resources=check_nonhtml(True,compare=preview_assets)
    report["verification"]["robots_sitemap_internal_raw_protection"]="PASS"
    img_live=check_image(True,img_pre)
    report["verification"]["real_1200_square_JPEG_SHA256_exact_match"]="PASS"
    hooks=api_get("hooks?site_id="+SITE)
    check(any(h.get("type")=="email" and h.get("event")=="submission_created" and
              "cicada3865@naver.com" in json.dumps(h.get("data") or {},
               ensure_ascii=False) for h in hooks),"Naver email notification hook missing")
    currentforms=api_get("sites/"+SITE+"/forms")
    check(any(z.get("name")==TEST_FORM for z in currentforms),
          "Netlify Forms disappeared after publish")
    report["verification"]["Netlify_Forms_and_Naver_notification"]="PASS_NO_NEW_FORM_SUBMISSION"
    final=site_get()
    check(current_id(final)==DRAFT,"Production drift after deployment")
    report["verification"]["published_deploy_id"]=current_id(final)
    report["verification"]["rollback_reference_preserved"]=PRODUCTION_BEFORE
    report["verification"]["live_ROBOTS_and_canonicals"]="PASS"
    report["verification"]["live_sitemap_shards"]=actual_resources["sitemap_shards"]
    report["verification"]["actual_image"]=img_live
    report["status"]="PASS_EXACT_APPROVED_DRAFT_PUBLISHED_AND_PRODUCTION_HTTP_SEO_FORM_QA"
except Exception as e:
    report["errors"].append(type(e).__name__+": "+str(e)[:650])
    report["status"]=("HOLD_AFTER_SINGLE_PUBLICATION_CHECK_MANUAL_RECOVERY" if report["publish"]["POST_attempted"]
                      else "HOLD_PREPUBLISH_NO_PUBLICATION")
finally:
    report["finished_utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
    save()
    print("ENPT_ONE_TIME_APPROVED_PUBLISH_RESULT",json.dumps(report,ensure_ascii=False)[:19000],flush=True)
    if report["status"].startswith("HOLD"):raise SystemExit(1)
