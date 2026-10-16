#!/usr/bin/env python3
"""v23.5.1 immutable DRAFT-only live QA: 6 local courses x 2 areas, mobile & desktop.
Read-only GET/HEAD; never send or submit consultation forms.
"""
import json,os,re,struct,sys,traceback,urllib.request
from pathlib import Path
from urllib.parse import urlsplit,unquote
from html import unescape

SITE="englishpt-final-ia-review-bokdong.netlify.app"
BASE=os.environ.get("REVIEW_DEPLOY_URL","").rstrip("/")
ALIAS=os.environ.get("OG_ALIAS_URL","").rstrip("/")
REPORT=Path("v2351-review-reports")
REPORT.mkdir(exist_ok=True,parents=True)
MODES=("elem-tutor","mid-tutor","high-tutor","elem-conv","mid-conv","high-conv")
OG_NAMES=("beginner","toeic","ielts","toefl","opic","tos","duolingo",
          "elementary","middle","high","student","worker","college","jobseeker",
          "housewife","stations","region","academy","tutor","conversation",
          "exam","courses","englishpt","reading","writing","international",
          "phone","video","general")

TITLES=("초등학생영어과외","중학생영어과외","고등학생영어과외","초등학생영어회화","중학생영어회화","고등학생영어회화")
SLUGS=("gyeongnam-milyang-naeidong","seoul-jongno-sajikdong")
UA={"User-Agent":"ENGLISH-PT-v2351-read-only-QA"}
GROUP=re.compile(r'<article class="related-group"><h3>학생 영어</h3><div class="related-course-links">(.*?)</div></article>',re.S)
A=re.compile(r'<a\b[^>]*>.*?</a>',re.S)
def report(name,data):
    (REPORT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("REPORT",name,data.get("status"),flush=True)
def fetch(url):
    import time
    last=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers=UA)
            with urllib.request.urlopen(req,timeout=45) as r:
                return r.status,r.read(),dict(r.headers),r.url
        except Exception as exc:
            last=exc
            if attempt<2:time.sleep(2+2*attempt)
    raise last
def error(data,where,reason):
    data["errors"].append({"where":where,"reason":str(reason)[:400]})
    print("::error::"+where+" "+str(reason)[:300],flush=True)
def start(phase):
    return {"phase":phase,"status":"RUNNING","draft":BASE,"alias":ALIAS,
        "source_run":38864767374,"original_source_run":38689660290,
        "original_sha":"a18b8901ecda7d37f65e35b15f03d579ec63c70f",
        "errors":[],"checks":[],"production_deployed":False,"form_submitted":False}
def guard():
    for u in (BASE,ALIAS):
        x=urlsplit(u)
        if x.scheme!="https" or not x.hostname or not x.hostname.endswith("--"+SITE) or "englishpt.kr" in u:
            raise ValueError("Unsafe Draft URL "+u)
    if BASE==ALIAS: raise ValueError("Mutable alias cannot be immutable Draft")
def stage_http():
    d=start("http")
    try:
        guard()
        for slug in SLUGS:
            parent=slug+"-worker-english-conv-academy.html"
            names=[parent]+[slug+"-"+mode+".html" for mode in MODES]
            for name in names:
                try:
                    code,body,headers,landed=fetch(BASE+"/"+name)
                    html=body.decode("utf8","replace")
                    if code!=200 or urlsplit(landed).hostname!=urlsplit(BASE).hostname:
                        raise ValueError("non-200 or redirect off unique Draft")
                    robots=headers.get("x-robots-tag",headers.get("X-Robots-Tag",""))
                    if "noindex" not in robots.lower():raise ValueError("Draft noindex response header missing")
                    if not re.search(r'<h1\b[^>]*data-v235-hero-wrap="(?:regular|long|xlong)"',html):
                        raise ValueError("missing responsive H1")
                    if name==parent:
                        m=GROUP.search(html)
                        if not m:raise ValueError("missing student links group")
                        links=A.findall(m.group(1))
                        if len(links)!=6:raise ValueError("student link count mismatch")
                        for i,link in enumerate(links):
                            dest="/"+slug+"-"+MODES[i]+".html"
                            if ('href="'+dest+'"') not in link or TITLES[i] not in unescape(link):
                                raise ValueError("bad student link "+str(i))
                    else:
                        i=MODES.index(next(c for c in MODES if name.endswith("-"+c+".html")))
                        if TITLES[i] not in re.sub(r'<[^>]*>',"",html.split("</h1>")[0]):
                            raise ValueError("wrong detailed page H1 intent")
                        if 'name="wantedClass" value="' not in html or TITLES[i] not in html:
                            raise ValueError("missing course-specific form preset")
                        if f'<link rel="canonical" href="https://englishpt.kr/{name}">' not in html:
                            raise ValueError("wrong canonical")
                    og=re.search(r'<meta property="og:image" content="([^"]+)">',html)
                    if not og or not og.group(1).startswith(ALIAS+"/assets/images/og-pages/"):
                        raise ValueError("OG image is not on review alias")
                    d["checks"].append({"page":name,"http":200,"og":og.group(1),"noindex":True})
                    print("LIVE_V2351_HTTP_PASS",name,flush=True)
                except Exception as exc:error(d,name,exc)
        # Thousands of historical square PNGs are stored here.
        # Inspect only 29 current 1200x630 OG templates.
        # Read-only verifier: validate all 29 CDN Draft image endpoints.
        # No 158571-page archive download or local assets needed.
        images=[Path(name+".png") for name in OG_NAMES]

        for p in images:
            try:
                code,content,headers,landed=fetch(ALIAS+"/assets/images/og-pages/"+p.name)
                if code!=200 or content[:8]!=b'\x89PNG\r\n\x1a\n':
                    raise ValueError("not accessible valid PNG")
                w,h=struct.unpack(">II",content[16:24])
                if (w,h)!=(1200,630):raise ValueError("wrong OG dimensions")
            except Exception as exc:error(d,p.name,exc)
        if len(images)!=29:error(d,"OG inventory","Expected exactly 29 current OG templates")
        d["og_images_verified"]=len(images)
        d["status"]="PASS_V2351_DRAFT_HTTP_SEO_OG" if not d["errors"] and len(d["checks"])==14 else "FAIL_V2351_DRAFT_HTTP_SEO_OG"
    except Exception as exc:
        error(d,"(runner)",traceback.format_exc()[-1300:])
        d["status"]="FAIL_V2351_DRAFT_HTTP_SEO_OG"
    finally:report("V2351_DRAFT_HTTP_SEO_OG.json",d)
    return not d["errors"] and d["status"].startswith("PASS")
def stage_chromium():
    d=start("chromium")
    folder=REPORT/"screenshots";folder.mkdir(exist_ok=True)
    try:
        guard()
        from playwright.sync_api import sync_playwright
        import shutil
        with sync_playwright() as pw:
            browser_file=shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
            options={"headless":True,"args":["--no-sandbox","--disable-dev-shm-usage"]}
            if browser_file:options["executable_path"]=browser_file
            browser=pw.chromium.launch(**options)
            try:
                for width in (390,1440):
                    ctx=browser.new_context(viewport={"width":width,"height":900},is_mobile=width<600,has_touch=width<600,device_scale_factor=1)
                    ctx.route("**/*",lambda route:route.abort() if route.request.method not in ("GET","HEAD") else route.continue_())
                    page=ctx.new_page()
                    try:
                        for slug in SLUGS:
                            parent=slug+"-worker-english-conv-academy.html"
                            main_url=BASE+"/"+parent
                            response=page.goto(main_url,wait_until="domcontentloaded",timeout=60000)
                            if response is None or response.status!=200:raise ValueError("parent not loaded")
                            page.evaluate("() => document.fonts.ready")
                            group=page.locator("article.related-group").filter(has=page.locator("h3",has_text="학생 영어")).first
                            if group.count()!=1 or group.locator("a").count()!=6:raise ValueError("parent six cards missing")
                            for i,(mode,title) in enumerate(zip(MODES,TITLES)):
                                href="/"+slug+"-"+mode+".html"
                                link=group.locator("a").nth(i)
                                if link.get_attribute("href")!=href:raise ValueError("student card href wrong: "+href)
                                link.scroll_into_view_if_needed(timeout=7000)
                                link.click(timeout=11000)
                                page.wait_for_load_state("domcontentloaded",timeout=45000)
                                if urlsplit(page.url).path.rstrip("/") not in (href,href[:-5]):
                                    raise ValueError("click navigation wrong: "+page.url)
                                h1=page.locator("h1").first.inner_text()
                                if title not in h1:raise ValueError("clicked into incorrect content: "+h1)
                                form=page.locator("#consultation-preview form")
                                if form.count()!=1:raise ValueError("consultation form missing")
                                values=page.evaluate("() => ({width:innerWidth,scroll:document.documentElement.scrollWidth})")
                                if values["scroll"]>width+3:raise ValueError("horizontal overflow")
                                pic=folder/(slug+"-"+mode+"-"+str(width)+".png")
                                page.screenshot(path=str(pic),full_page=False,timeout=22000)
                                d["checks"].append({"slug":slug,"mode":mode,"width":width,
                                                    "h1":h1,"url":page.url,"screenshot":pic.name})
                                print("V2351_BROWSER_CLICK_PASS",slug,mode,width,flush=True)
                                page.goto(main_url,wait_until="domcontentloaded",timeout=45000)
                                group=page.locator("article.related-group").filter(has=page.locator("h3",has_text="학생 영어")).first
                    finally:ctx.close()
            finally:browser.close()
        d["status"]="PASS_V2351_DRAFT_MOBILE_PC_CLICKS" if len(d["checks"])==24 and not d["errors"] else "FAIL_V2351_DRAFT_MOBILE_PC_CLICKS"
    except Exception as exc:
        error(d,"(browser)",traceback.format_exc()[-1900:])
        d["status"]="FAIL_V2351_DRAFT_MOBILE_PC_CLICKS"
    finally:report("V2351_DRAFT_CHROMIUM.json",d)
    return not d["errors"] and d["status"].startswith("PASS")
if __name__=="__main__":
    phase=sys.argv[1] if len(sys.argv)>1 else "http"
    sys.exit(0 if (stage_http() if phase=="http" else stage_chromium()) else 1)
