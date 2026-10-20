#!/usr/bin/env python3
# coding: utf-8
"""GET-only live nonpublished Netlify review QA: mixed robots, Edge routing,
OG, consultation CTA browser at 390/1440. NO form submissions, NO deployments.
This proves preview runtime only; preview intentionally applies global noindex.
"""
import concurrent.futures
import csv
import datetime
import gzip
import hashlib
import html.parser
import io
import json
import os
import pathlib
import re
import subprocess
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse
from PIL import Image

BASE = "https://enptog21964prodsafereview20--englishpt-seo.netlify.app"
SITE = "98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
PROD = "6ad5eb4918f9411c4d5e1ba4"
MARKER = "ENPT-21964-PRODSAFE-ORIGINAL-ROBOTS-CLI-FULL-NONPUBLISHED-ONCE-20261020"
ROOT = pathlib.Path.cwd()
OUT = ROOT / "qa-live-prod-safe-runtime"
OUT.mkdir(exist_ok=True)
GOOGLE = "OTG-5ooTZYTm-HnTOi8I0TRV4bZHUD-uSYSOih3E8ig"
NAVER = "340f4e7dc8c5f3ec806e68f6f09b9949f941a0de"
FORMS = [
    "gyeongnam-milyang-naeidong-elem-tutor.html",
    "gyeongnam-milyang-naeidong-mid-tutor.html",
    "gyeongnam-milyang-naeidong-high-tutor.html",
    "seoul-jongno-sajikdong-elem-tutor.html",
    "seoul-jongno-sajikdong-mid-tutor.html",
    "seoul-jongno-sajikdong-high-tutor.html",
]
R = {"status":"HOLD", "checked_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
     "existing_preview":BASE,"published_expected":PROD,"published_unchanged":False,
     "preview_is_noindex":False,"new_deploys_created":0,"published_changes":0,
     "form_POST_submissions":0,"qa_mode":"GET_ONLY",
     "pages_checked":0,"indexable_source_pages_checked":0,"noindex_source_pages_checked":0,
     "form_markup_checked":0,"screenshots":[],"errors":[],"checks":[]}
def ensure(condition, message):
    if not condition: raise ValueError(message)
def api(path):
    req=urllib.request.Request("https://api.netlify.com/api/v1/"+path,
        headers={"Authorization":"Bearer "+os.environ["NETLIFY_AUTH_TOKEN"],
                 "Accept":"application/json"},method="GET")
    with urllib.request.urlopen(req,timeout=32) as f:return json.load(f)
def get(path, retry=0):
    u=BASE+path
    req=urllib.request.Request(u,headers={"User-Agent":"ENPT-v23521-FINAL-PREAPPROVAL-LIVE-GET-ONLY"},method="GET")
    try:
        with urllib.request.urlopen(req,timeout=45) as resp:
            ensure(resp.status==200, "HTTP non200 "+path)
            ensure(resp.geturl().startswith(BASE),"Host unexpected "+path)
            return resp.read(1400000), {k.lower():v for k,v in resp.headers.items()}
    except (urllib.error.URLError, TimeoutError) as e:
        if retry<2:
            time.sleep(1.5*(retry+1))
            return get(path,retry+1)
        raise

class PageInfo(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta=[];self.links=[];self.forms=[];self.inputs=[]
        self.open_buttons=0;self.ctas=0
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=="meta":self.meta.append(d)
        if tag=="link":self.links.append(d)
        if tag=="form":self.forms.append(d)
        if tag in ("input","select"):self.inputs.append(d)
        if "data-open-form" in d:self.open_buttons+=1
        if tag=="button" and d.get("type")=="submit":self.ctas+=1
    def find_meta(self,key,name):
        return [x.get("content") for x in self.meta if x.get(key,"").lower()==name.lower()]
    def canonical(self):
        return [x.get("href") for x in self.links if x.get("rel")=="canonical"]

try:
    # Hard gate existing nonpublished READY preview and production baseline.
    site=api("sites/"+SITE)
    ensure(site["id"]==SITE and site.get("custom_domain")=="englishpt.kr","Wrong site")
    R["published_current"]=(site.get("published_deploy") or {}).get("id")
    ensure(R["published_current"]==PROD,"PRODUCTION DRIFT")
    R["published_unchanged"]=True
    ds=api("sites/"+SITE+"/deploys?per_page=100")
    hits=[d for d in ds if d.get("title")==MARKER]
    ensure(len(hits)==1 and hits[0].get("state")=="ready" and hits[0].get("published_at") is None,
           "Expected exactly one READY unpublished draft")
    R["draft_id"]=hits[0]["id"]
    with gzip.open(ROOT/"signed-qa-map/NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz","rt",encoding="utf8") as f:
        man=json.load(f)["original_public_html_to_data_payload"]
    ensure(len(man)==158571 and sum(x["noindex"] for x in man.values())==136607,
           "original route/source noindex mismatch")
    with (ROOT/"signed-route-map/ALL_21964_INDEXABLE_THUMBNAIL_MAP.csv").open(encoding="utf-8-sig",newline="") as f:
        mapping={x["route"]:x for x in csv.DictReader(f)}
    ensure(len(mapping)==21964,"source OG map wrong count")
    indexed=sorted([p for p,x in man.items() if not x["noindex"]])
    excluded=sorted([p for p,x in man.items() if x["noindex"]])
    def stratified(seq, n):
        return [seq[i*len(seq)//n] for i in range(n)]
    # 18 pages from each indexing group + six named form pages + six main hubs
    routes=list(dict.fromkeys(stratified(indexed,18)+stratified(excluded,18)+FORMS))
    ensure(len(routes)>=38,"mixed page sample count")
    def verify(route):
        data,headers=get("/"+route)
        ensure(headers.get("content-type","").lower().startswith("text/html"),"HTML MIME bad "+route)
        ensure("noindex" not in headers.get("x-robots-tag","").lower(),
               "Global preview noindex unexpectedly added to production-safe page "+route)
        parser=PageInfo()
        parser.feed(data.decode("utf8",errors="replace"))
        bots=parser.find_meta("name","robots")
        ensure(len(bots)==1,"robots meta missing/duplicate "+route)
        actual_noindex="noindex" in (bots[0] or "").lower()
        ensure(actual_noindex==bool(man[route]["noindex"]),"page-level robots policy changed "+route)
        ensure(parser.canonical()==["https://englishpt.kr/"+route],
               "public canonical wrong "+route)
        if route in mapping:
            m=mapping[route]
            ensure(parser.find_meta("property","og:image")==[m["planned_og_image_url"]],
                   "new JPEG OG mismatch "+route)
        else:
            ensure(len(parser.find_meta("property","og:image"))<=1,
                   "OG duplicates on noindex route "+route)
        if route in FORMS:
            ensure(len(parser.forms)==1,"expected single consultation form "+route)
            form=parser.forms[0]
            ensure(form.get("name")=="englishpt-consultation" and "data-netlify" in form,
                   "Netlify Forms form source missing "+route)
            names={x.get("name") for x in parser.inputs}
            ensure({"form-name","requestType","subject","consent"} <= names,
                   "Required consultation fields absent "+route)
            # Tutor pages intentionally use an anchored in-page form
            # (#consultation-preview), not the modal data-open-form CTA.
            ensure(parser.ctas>0 and b'id="consultation-preview"' in data,
                   "In-page consultation section or submit CTA absent "+route)
        return {"route":route,"source_noindex":actual_noindex,"og_mapped":route in mapping,
                "form_present":route in FORMS,"bytes":len(data)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for result in pool.map(verify,routes):
            R["checks"].append(result)
    R["pages_checked"]=len(R["checks"])
    R["indexable_source_pages_checked"]=sum(not x["source_noindex"] for x in R["checks"])
    R["noindex_source_pages_checked"]=sum(x["source_noindex"] for x in R["checks"])
    R["form_markup_checked"]=sum(x["form_present"] for x in R["checks"])
    ensure(R["form_markup_checked"]==6,"All six original forms not checked")
    # 6 main hubs publicly route and own owner tags on both homepage paths.
    for path in ("/index.html","/englishpt.html","/courses.html","/student-english.html",
                 "/exam-english.html","/english-conversation.html"):
        data,headers=get(path)
        ensure("noindex" not in headers.get("x-robots-tag","").lower(),"Production-safe root/hub is globally noindexed "+path)
        if path in ("/index.html","/englishpt.html"):
            txt=data.decode("utf8",errors="replace")
            ensure(txt.count('name="google-site-verification"')==1 and
                   txt.count('content="'+GOOGLE+'"')==1,"Google owner missing "+path)
            ensure(txt.count('name="naver-site-verification"')==1 and
                   txt.count('content="'+NAVER+'"')==1,"Naver owner missing "+path)
    robots,h=get("/robots.txt")
    ensure("User-agent: *" in robots.decode("utf8"),"Root robots crawler policy missing")
    ensure(not re.search(r"(?m)^\\s*Disallow:\\s*/\\s*$",robots.decode("utf8")),
           "Unintended blanket crawler block in production-safe robots")
    sitemap,h=get("/sitemap-index.xml")
    ensure(sitemap.count(b"<sitemap>")==44,"Preview sitemap index not 44")
    # Verify direct original source assets still blocked from being indexed.
    raw,h=get("/__pages/23/englishpt.page")
    ensure("noindex" in h.get("x-robots-tag","").lower(),"Raw .page not noindex")
    # representative live JPEG cross-check against local QA ledger
    with (ROOT/"all-jpeg-qa/ALL21964_IMAGE_HASH_AND_URL.csv").open(encoding="utf-8-sig",newline="") as f:
        hashes={r["url_path"]:r for r in csv.DictReader(f)}
    for name in list(mapping)[:10]:
        path="/"+mapping[name]["planned_image_path"]
        raw,h=get(path)
        ensure(h.get("content-type","").lower().startswith("image/jpeg"),"JPEG wrong MIME")
        ensure(hashlib.sha256(raw).hexdigest()==hashes[name]["sha256"],"Live JPEG sha changed "+name)
        with Image.open(io.BytesIO(raw)) as img:
            ensure(img.size==(1200,1200),"Live image wrong size")
    R["live_JPEG_hash_crosschecks"]=10
    print("ENPT_LIVE_MIXED_ROBOTS_AND_FORM_GET_PASS",json.dumps({
        "pages":R["pages_checked"],"indexable":R["indexable_source_pages_checked"],
        "noindex":R["noindex_source_pages_checked"],"forms":R["form_markup_checked"]},
        ensure_ascii=False),flush=True)

    # Actual Chrome interaction: real CTA opens and closes; form submission blocked
    # even if clicked; verify 390px mobile and 1440px desktop screenshots.
    from playwright.sync_api import sync_playwright
    from shutil import which
    chrome=which("google-chrome") or which("chromium") or which("chromium-browser")
    ensure(bool(chrome),"Chrome browser unavailable")
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=chrome,
              args=["--no-sandbox","--disable-dev-shm-usage"])
        try:
            for width,route in ((390,FORMS[0]),(1440,FORMS[-1])):
                ctx=browser.new_context(viewport={"width":width,"height":900},
                                        ignore_https_errors=False)
                blocked=[0]
                def guard(request):
                    if request.request.method not in ("GET","HEAD"):
                        blocked[0]+=1
                        request.abort()
                    else:request.continue_()
                ctx.route("**/*",guard)
                page=ctx.new_page()
                page.add_init_script("""document.addEventListener('submit', event => {
                  event.preventDefault(); event.stopImmediatePropagation();
                  window.__FORM_QA_BLOCKED__=true; }, true);""")
                response=page.goto(BASE+"/"+route,wait_until="domcontentloaded",timeout=65000)
                ensure(response is not None and response.status==200,
                       "Browser returned non200 "+route)
                # Real tutor CTA jumps to in-page form section, never opens modal.
                anchor=page.locator('a[href="#consultation-preview"]').first
                ensure(anchor.count()==1,"In-page consultation CTA missing "+route)
                anchor.click(timeout=16000)
                page.wait_for_timeout(350)
                ensure(page.url.endswith("#consultation-preview"),"CTA anchor did not navigate to form "+route)
                form=page.locator("#consultation-preview form#leadForm")
                form.wait_for(state="visible",timeout=12000)
                ensure(page.locator('#leadForm input[name="name"]').count()==1 and
                       page.locator('#leadForm input[name="phone"]').count()==1,
                       "Consultation form name/phone missing "+route)
                ensure(page.locator('#leadForm button[type="submit"]').count()==1,
                       "Consultation form submit button missing "+route)
                ensure(form.is_visible(),"Consultation form is not visible after anchor click "+route)
                fp=OUT/("LIVE_"+str(width)+"PX_CONSULTATION_IN_PAGE.png")
                page.screenshot(path=str(fp),full_page=False)
                R["screenshots"].append(fp.name)
                ensure(blocked[0]==0,"Browser attempted a nonGET request unexpectedly")
                ctx.close()
        finally:
            browser.close()
    R["live_mobile_390px"]="PASS_REAL_CTA_ANCHOR_SCROLL_FORM_VISIBLE_NO_POST"
    R["live_desktop_1440px"]="PASS_REAL_CTA_ANCHOR_SCROLL_FORM_VISIBLE_NO_POST"
    R["status"]="PASS_PRODSAFE_DRAFT_MIXED_SEO_EDGE_FORMS_LIVE_BROWSER_NO_POST"
except Exception as e:
    R["status"]="HOLD_EXISTING_PREVIEW_RUNTIME_QA"
    R["errors"].append(type(e).__name__+": "+str(e)[:400])
finally:
    (OUT/"LIVE_DRAFT_ROUTE_MIXED_NOINDEX_FORMS_MOBILE_QA.json").write_text(
        json.dumps(R,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("ENPT_LIVE_PRODUCTION_CANDIDATE_RUNTIME_SIMULATION",
          json.dumps({k:v for k,v in R.items() if k!="checks"},
                     ensure_ascii=False),flush=True)
    if R["status"].startswith("HOLD"):raise SystemExit(1)
