#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Strict POST-publication GET-only verification. Never run the publisher again."""
import datetime,json,pathlib,os,urllib.request,hashlib,re,io,xml.etree.ElementTree as ET
from html.parser import HTMLParser
from shutil import which
from PIL import Image
from playwright.sync_api import sync_playwright
BASE="https://englishpt.kr"
PREVIEW="https://enptog21964prodsafereview20--englishpt-seo.netlify.app"
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
EXPECTED="6ad7506cdeb778280a54ee2a"
ROLLBACK="6ad5eb4918f9411c4d5e1ba4"
FORMID="6ad31619a0da0424ffd54af9"
TESTID="6ad751390919add0ec06f61c"
MARKER="ENPT_OG21964_FINAL_QA_SINGLE_20261020"
OUT=pathlib.Path("production-readonly-verification");OUT.mkdir(exist_ok=True)
r={"checked_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
   "status":"HOLD","expected_published_deploy":EXPECTED,
   "original_rollback_deploy":ROLLBACK,
   "netlify_write_actions":0,"consultation_POSTs":0,"new_deploys":0,
   "published_page_parity":[],"image_checks":[],"screenshots":[],"errors":[]}
def ensure(x,msg):
    if not x:raise RuntimeError(msg)
def api(path):
    req=urllib.request.Request("https://api.netlify.com/api/v1/"+path,method="GET",
      headers={"Authorization":"Bearer "+os.environ["NETLIFY_AUTH_TOKEN"]})
    with urllib.request.urlopen(req,timeout=30) as res:return json.load(res)
def get(base,path):
    req=urllib.request.Request(base+path,method="GET",
       headers={"Cache-Control":"no-cache","User-Agent":"ENPT-PostApprovedPublication-GET-Only"})
    with urllib.request.urlopen(req,timeout=32) as res:
        ensure(res.status==200 and res.geturl().startswith(base),"GET HTTP non200 or cross-host "+path)
        return res.read(2700000),{k.lower():v for k,v in res.headers.items()}
class Doc(HTMLParser):
    def __init__(self):
        super().__init__();self.meta=[];self.links=[];self.forms=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=="meta":self.meta.append(d)
        if tag=="link":self.links.append(d)
        if tag=="form":self.forms.append(d)
    def meta1(self,k,v):return [x.get("content") for x in self.meta if x.get(k)==v]
    def can(self):return [x.get("href") for x in self.links if x.get("rel")=="canonical"]
try:
    site=api("sites/"+SITE)
    ensure(site.get("id")==SITE and site.get("custom_domain")=="englishpt.kr","Site ID/domain drift")
    actual=(site.get("published_deploy") or {}).get("id")
    ensure(actual==EXPECTED,"STOP live published deploy not EXACT user-approved Draft")
    d=api("sites/"+SITE+"/deploys/"+EXPECTED)
    ensure(d.get("state")=="ready" and d.get("published_at") is not None,
           "Approved Draft not READY published")
    old=api("sites/"+SITE+"/deploys/"+ROLLBACK)
    ensure(old.get("id")==ROLLBACK and old.get("site_id")==SITE,
           "Previous rollback deploy not retrievable")
    r["rollback_deploy_retrievable"]=True
    paths=["/index.html","/englishpt.html",
           "/station-419minjumyoji-toeic.html",
           "/station-419minjumyoji-ielts.html",
           "/gyeongnam-milyang-naeidong-elem-tutor.html",
           "/seoul-jongno-sajikdong-high-tutor.html"]
    images={}
    for path in paths:
        live,lh=get(BASE,path);draft,dh=get(PREVIEW,path)
        ensure(hashlib.sha256(live).digest()==hashlib.sha256(draft).digest(),
               "Production and exact approved Draft have different HTML bytes "+path)
        ensure(lh.get("content-type","").startswith("text/html"),"Invalid HTML MIME "+path)
        ensure("noindex" not in lh.get("x-robots-tag","").lower(),
               "Global preview noindex leaked to public page "+path)
        p=Doc();p.feed(live.decode("utf8","replace"))
        c="https://englishpt.kr/englishpt.html" if path=="/index.html" else BASE+path
        ensure(p.can()==[c],"Canonical changed "+path)
        robot=p.meta1("name","robots")
        ensure(len(robot)==1 and ("noindex" in robot[0].lower())==("tutor" in path),
               "Original page-level index/noindex policy wrong "+path)
        og=p.meta1("property","og:image")
        ensure(len(og)==1,"OG image missing/duplicate "+path)
        if path in ("/index.html","/englishpt.html"):
            ensure(p.meta1("name","google-site-verification")==
               ["OTG-5ooTZYTm-HnTOi8I0TRV4bZHUD-uSYSOih3E8ig"],"Google owner missing")
            ensure(p.meta1("name","naver-site-verification")==
               ["340f4e7dc8c5f3ec806e68f6f09b9949f941a0de"],"Naver owner missing")
        if "tutor" in path:
            ensure(any(f.get("name")=="englishpt-consultation" for f in p.forms),
                   "Real tutor form missing "+path)
        images[path]=og[0]
        r["published_page_parity"].append(
            {"path":path,"HTTP":200,"same_as_approved_preview_sha256":True,
             "robot_meta":robot[0],"canonical":c,"og":og[0]})
    # Exactly approved real JPEG bytes from the same preview, plus original 1200² dimensions.
    for path in paths[2:4]:
        img=images[path]
        ensure(img.startswith(BASE+"/assets/images/seo-square/v1/") and img.endswith(".jpg"),
               "Unexpected station square JPEG URI")
        suffix=img.removeprefix(BASE)
        live,headers=get(BASE,suffix);preview,_=get(PREVIEW,suffix)
        ensure(live==preview and live[:2]==b"\xff\xd8",
               "Production JPEG differs from immutable verified Draft "+suffix)
        ensure(headers.get("content-type","").lower().startswith("image/jpeg"),
               "Square JPEG content type wrong")
        with Image.open(io.BytesIO(live)) as im:
            ensure(im.format=="JPEG" and im.size==(1200,1200),"Square JPEG not 1200x1200")
        r["image_checks"].append({"path":suffix,"HTTP":200,
              "SHA256":hashlib.sha256(live).hexdigest(),"dimensions":"1200x1200"})
    for path in ("/robots.txt","/sitemap-index.xml","/__pages/23/englishpt.page"):
        live,header=get(BASE,path);draft,_=get(PREVIEW,path)
        ensure(live==draft,"Original approved Draft asset changed "+path)
        if path=="/robots.txt":
            ensure("Sitemap: https://englishpt.kr/sitemap-index.xml" in live.decode(),
                   "Production robots sitemap missing")
            ensure(not re.search(r"(?im)^\s*Disallow:\s*/\s*$",live.decode()),
                   "Production robots blanket crawl block")
        elif path=="/sitemap-index.xml":
            root=ET.fromstring(live)
            urls=[e.text for e in root.iter() if e.tag.endswith("loc") and e.text]
            ensure(len(urls)==len(set(urls))==44,"Sitemap shards count not 44")
        else:
            ensure("noindex" in header.get("x-robots-tag","").lower(),
                   "Internal sharded page unexpectedly indexable")
    r["robots_sitemap_internal_page"]="PASS_EXACT_BYTES_ROBOTS_ALLOW_44_SITEMAPS_INTERNAL_NOINDEX"
    forms=api("sites/"+SITE+"/forms")
    ensure(any(x.get("id")==FORMID and x.get("name")=="englishpt-consultation" for x in forms),
           "Netlify registered consultation form missing")
    subs=api("forms/"+FORMID+"/submissions?per_page=100")
    ensure(any(x.get("id")==TESTID and
               MARKER in json.dumps(x.get("data") or {},ensure_ascii=False)
               for x in subs),"Previously verified one real test missing, DO NOT resubmit")
    hooks=api("hooks?site_id="+SITE)
    ensure(any(x.get("event")=="submission_created" and x.get("type")=="email" and
                "cicada3865@naver.com" in json.dumps(x.get("data") or {},ensure_ascii=False)
                for x in hooks),"Naver notification email hook missing")
    r["consultation_backend_and_notification"]="PASS_EXISTING_VERIFIED_TEST_AND_EMAIL_HOOK_NO_NEW_POST"
    chrome=which("google-chrome") or which("chromium") or which("chromium-browser")
    ensure(chrome,"Chrome not installed")
    with sync_playwright() as pw:
        b=pw.chromium.launch(headless=True,executable_path=chrome,
                args=["--no-sandbox","--disable-dev-shm-usage"])
        try:
            for width in (390,1440):
                context=b.new_context(viewport={"width":width,"height":850})
                def block_non_get(route):
                    if route.request.method in ("GET","HEAD"):route.continue_()
                    else:route.abort()
                context.route("**/*",block_non_get)
                page=context.new_page()
                res=page.goto(BASE+"/gyeongnam-milyang-naeidong-elem-tutor.html",
                              wait_until="domcontentloaded",timeout=65000)
                ensure(res and res.status==200,"Mobile/PC tutor page not HTTP200")
                anchor=page.locator('a[href="#consultation-preview"]').first
                ensure(anchor.count()==1,"Consultation CTA missing")
                anchor.click(timeout=18000)
                page.locator('#consultation-preview form#leadForm').wait_for(state="visible",timeout=16000)
                ensure(page.url.endswith("#consultation-preview"),"Consultation anchor failed")
                ensure(page.locator('#leadForm input[name="name"]').count()==1,
                    "Consultation name input missing")
                ensure(page.locator('#leadForm input[name="phone"]').count()==1,
                    "Consultation phone input missing")
                ensure(page.locator('#leadForm button[type="submit"]').count()==1,
                    "Consultation submit button missing")
                screenshot="PRODUCTION_"+str(width)+"PX_CONSULTATION_CTA.png"
                page.screenshot(path=str(OUT/screenshot),full_page=False)
                r["screenshots"].append(screenshot)
                context.close()
        finally:b.close()
    r["mobile_390_and_desktop_1440"]="PASS_BOTH_REAL_BROWSER_CTA_INPAGE_FORM_VISIBLE_NO_POST"
    final=api("sites/"+SITE)
    ensure((final.get("published_deploy") or {}).get("id")==EXPECTED,
           "Published site changed during QA")
    r["current_published_deploy_id"]=EXPECTED
    r["status"]="PASS_EXACT_USER_APPROVED_DEPLOY_LIVE_HTTP_SEO_SITEMAP_JPEG_FORM_MOBILE_DESKTOP"
except Exception as ex:
    r["errors"].append(type(ex).__name__+": "+str(ex)[:650])
    r["status"]="HOLD_POSTPRODUCTION_QA_PRODUCTION_ALREADY_PUBLISHED_NO_AUTOMATIC_ROLLBACK"
finally:
    r["finished_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
    (OUT/"POSTPUBLISH_READONLY_FINAL_QA.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("ENPT_EXACT_PRODUCTION_POSTPUBLISH_READONLY_FINAL_QA",
          json.dumps({k:v for k,v in r.items() if k!="published_page_parity"},ensure_ascii=False),flush=True)
    if r["status"].startswith("HOLD"):raise SystemExit(1)
