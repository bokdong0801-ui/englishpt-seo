#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v23.5.2 Live isolated Netlify Draft visual and consultation-journey QA.
GET/HEAD only; blocks all POSTs and native form submits. No deployment.
"""
import json,os,re,sys,time,traceback,struct,urllib.request,urllib.error
from pathlib import Path
from urllib.parse import urlsplit,urljoin,unquote
from playwright.sync_api import sync_playwright

HOST="englishpt-final-ia-review-bokdong.netlify.app"
URL=(os.environ.get("V2352_UNIQUE_DRAFT_URL") or os.environ.get("REVIEW_DEPLOY_URL") or "").rstrip("/")
ALIAS=(os.environ.get("V2352_DRAFT_OG_ALIAS") or os.environ.get("OG_ALIAS_URL") or "").rstrip("/")
OUT=Path("v2352-live-report");OUT.mkdir(parents=True,exist_ok=True)
SCREEN=OUT/"screenshots";SCREEN.mkdir(parents=True,exist_ok=True)
COURSES={"elem-tutor":"초등학생영어과외","mid-tutor":"중학생영어과외","high-tutor":"고등학생영어과외"}
AREAS={"gyeongnam-milyang-naeidong":"내이동","seoul-jongno-sajikdong":"사직동",
       "chungbuk-cheongju-seowon-sajikdong":"사직동"}
TEST_AREAS=("gyeongnam-milyang-naeidong","seoul-jongno-sajikdong")
ALL_MODES=("elem-tutor","mid-tutor","high-tutor","elem-conv","mid-conv","high-conv")
VIEWPORTS=(320,390,430,1440)
CHECKSECTIONS=("levels","lesson","errors","timeline","parent")
OG_IMAGES=("beginner","toeic","ielts","toefl","opic","tos","duolingo",
    "elementary","middle","high","student","worker","college","jobseeker",
    "housewife","stations","region","academy","tutor","conversation",
    "exam","courses","englishpt","reading","writing","international",
    "phone","video","general")

def check_host(uri,mutable=False):
    u=urlsplit(uri)
    if u.scheme!="https" or not u.hostname or not u.hostname.endswith("--"+HOST):
        raise ValueError("Not an isolated HTTPS Review domain "+uri)
    if u.hostname.startswith("englishpt.kr") or u.hostname in ("englishpt.kr","www.englishpt.kr"):
        raise ValueError("Production URL blocked")
    if not mutable and not re.match(r"^[a-f0-9]{16,}--"+re.escape(HOST)+r"$",u.hostname):
        raise ValueError("Need immutable Deploy ID, not mutable alias "+uri)
    return True

def http(url):
    exc=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"ENGLISHPT-v2352-read-only-QA"})
            with urllib.request.urlopen(req,timeout=50) as res:
                return res.status,res.read(),dict(res.headers),res.url
        except Exception as e:
            exc=e
            if attempt<2:time.sleep(attempt+2)
    raise exc

def failure(result,where,issue,details=None):
    o={"where":where,"issue":issue}
    if details:o["details"]=str(details)[:600]
    result["errors"].append(o)
    if len(result["errors"])<=40:
        print("::error::"+json.dumps(o,ensure_ascii=False),flush=True)

def emit(name,value):
    path=OUT/name
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("V2352_QA_REPORT",name,value.get("status"),flush=True)

def http_qa():
    r={"status":"RUNNING","url":URL,"og_alias":ALIAS,"page_checks":[],"og_checked":0,
       "errors":[],"production_deployed":False,"form_submitted":False}
    try:
        check_host(URL);check_host(ALIAS,True)
        for slug in TEST_AREAS:
            name=AREAS[slug]
            for kind,label in COURSES.items():
                filename=slug+"-"+kind+".html"
                try:
                    status,body,headers,landed=http(URL+"/"+filename)
                    doc=body.decode("utf8","replace")
                    if status!=200 or urlsplit(landed).hostname!=urlsplit(URL).hostname:
                        raise ValueError("HTTP non-200 or redirected off immutable Preview "+landed)
                    if "noindex" not in headers.get("x-robots-tag",headers.get("X-Robots-Tag","")).lower():
                        raise ValueError("Draft response not protected by X-Robots-Tag: noindex")
                    if doc.count('data-v2352-tutor-content="parent-guide-v1"')!=5:
                        raise ValueError("Five new v2352 sections missing")
                    for tag in CHECKSECTIONS:
                        if doc.count('data-v2352-section="'+tag+'"')!=1:
                            raise ValueError("Duplicate or missing content section "+tag)
                    if doc.count('class="faq-item"')!=6:
                        raise ValueError("Six FAQ items missing")
                    h1=re.search(r"<h1\b[^>]*>(.*?)</h1>",doc,re.I|re.S)
                    if not h1 or name+" "+label not in re.sub(r"<[^>]*>","",h1.group(1)):
                        raise ValueError("Hero grade/locality title incorrect")
                    if ('href="#consultation-preview"' not in doc or
                        '<a class="v2352-small-cta" href="#consultation-preview">' not in doc):
                        raise ValueError("Parent consultation CTA destination missing")
                    if doc.count('id="consultation-preview"')!=1 or 'name="consent"' not in doc:
                        raise ValueError("Consultation form missing")
                    if '<link rel="canonical" href="https://englishpt.kr/'+filename+'">' not in doc:
                        raise ValueError("Canonical not preserved")
                    m=re.search(r'<meta property="og:image" content="([^"]+)"',doc)
                    if not m or not m.group(1).startswith(ALIAS+"/assets/images/og-pages/"):
                        raise ValueError("OG should resolve inside isolated Draft alias")
                    group=re.search(r'<article class="related-group"><h3>학생 영어</h3><div class="related-course-links">(.*?)</div></article>',doc,re.S)
                    if not group:raise ValueError("Six-card student navigation missing")
                    # Read raw HTML with an HTML parser; Netlify may serialize
                    # valid href attributes without quotes (or with Pretty URLs).
                    # The actual Chromium click verifier separately checks arrival.
                    from html.parser import HTMLParser
                    class StudentHrefCollector(HTMLParser):
                        def __init__(self):
                            super().__init__(convert_charrefs=True)
                            self.hrefs=[]
                        def handle_starttag(self, tag, attrs):
                            if tag=="a":
                                value=dict(attrs).get("href")
                                if value:self.hrefs.append(value)
                    parsed=StudentHrefCollector()
                    parsed.feed(group.group(1))
                    actual={u.rstrip("/") for u in parsed.hrefs}
                    for mode in ALL_MODES:
                        stem="/"+slug+"-"+mode
                        if not (stem in actual or stem+".html" in actual):
                            raise ValueError("Wrong regional student link: "+stem+
                                " [parsed hrefs="+str(sorted(actual)[:8])+"]")
                    r["page_checks"].append({"url":URL+"/"+filename,"http":200,
                       "h1":name+" "+label,"updated_sections":5,"faqs":6,"student_links":6,"draft_noindex":True})
                    print("V2352_HTTP_PASS",filename,flush=True)
                except Exception as exc:failure(r,filename,"http_content_cta_or_seo",exc)
        # Current 29 landscape OG source variants, not thousands of legacy square PNGs.
        for name in OG_IMAGES:
            try:
                st,content,head,landed=http(ALIAS+"/assets/images/og-pages/"+name+".png")
                if st!=200 or content[:8]!=b"\x89PNG\r\n\x1a\n":
                    raise ValueError("Not HTTP 200 PNG")
                if struct.unpack(">II",content[16:24])!=(1200,630):
                    raise ValueError("Incorrect 1200x630 OG dimensions")
                r["og_checked"]+=1
            except Exception as exc:failure(r,"og/"+name+".png","OG_Draft_asset",exc)
        r["status"]="PASS_V2352_LIVE_HTTP_CONTENT_CTA_SEO_OG" if len(r["page_checks"])==6 and r["og_checked"]==29 and not r["errors"] else "HOLD_V2352_LIVE_HTTP_CONTENT_CTA_SEO_OG"
    except Exception:
        failure(r,"(http_runner)","exception",traceback.format_exc()[-1800:])
        r["status"]="HOLD_V2352_LIVE_HTTP_CONTENT_CTA_SEO_OG"
    finally:emit("V2352_LIVE_HTTP_QA.json",r)
    return r["status"].startswith("PASS")

def browser_qa():
    r={"status":"RUNNING","url":URL,"viewports":VIEWPORTS,
       "actual_page_combinations":0,"section_layout_checks":0,
       "cta_click_checks":0,"consultation_form_reached":0,
       "verified_form_structures":0,"student_navigation_checks":0,
       "screenshot_count":0,"errors":[],"screenshots":[],
       "non_get_requests_blocked":0,"form_submitted":False,
       "production_deployed":False,"checks":[]}
    try:
        check_host(URL)
        with sync_playwright() as pw:
            import shutil
            exe=shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
            args={"headless":True,"args":["--no-sandbox","--disable-dev-shm-usage"]}
            if exe:args["executable_path"]=exe
            browser=pw.chromium.launch(**args)
            try:
                for width in VIEWPORTS:
                    ctx=browser.new_context(viewport={"width":width,"height":900},
                         is_mobile=width<=430,has_touch=width<=430,device_scale_factor=1)
                    def deny_mutations(route):
                        if route.request.method not in ("GET","HEAD"):
                            r["non_get_requests_blocked"]+=1;route.abort()
                        else:route.continue_()
                    ctx.route("**/*",deny_mutations)
                    try:
                        for slug in TEST_AREAS:
                            for course,label in COURSES.items():
                                filename=slug+"-"+course+".html"
                                page=ctx.new_page()
                                try:
                                    page.add_init_script("""document.addEventListener('submit',ev=>{
                                        ev.preventDefault();ev.stopImmediatePropagation();
                                        window.__DISABLED_REAL_SUBMISSION__=true;
                                    },true)""")
                                    url=URL+"/"+filename
                                    rr=page.goto(url,wait_until="domcontentloaded",timeout=70000)
                                    if not rr or rr.status!=200:raise ValueError("HTTP 200 required")
                                    page.evaluate("() => document.fonts.ready")
                                    page.wait_for_timeout(180)
                                    d=page.evaluate("""() => {
                                        const h=document.querySelector('h1'),rect=h?.getBoundingClientRect();
                                        return {h1:h?.innerText||'',font: h?getComputedStyle(h).fontFamily:null,
                                                h1left:rect?.left||0,h1right:rect?.right||0,
                                                h1height:rect?.height||0,
                                                scrollWidth:document.documentElement.scrollWidth,
                                                innerWidth:innerWidth,deviceScale:devicePixelRatio};
                                    }""")
                                    if AREAS[slug]+" "+label not in d["h1"]:
                                        raise ValueError("H1 locality or category mismatch: "+d["h1"])
                                    if d["scrollWidth"]>width+3:raise ValueError("Document horizontal overflow "+str(d["scrollWidth"]))
                                    if d["h1right"]>width+4 or d["h1left"]<-4:raise ValueError("H1 outside viewport")
                                    if d["h1height"]<=0:raise ValueError("Invisible H1")
                                    sections=page.locator("[data-v2352-tutor-content='parent-guide-v1']")
                                    if sections.count()!=5:raise ValueError("Five content blocks not visible")
                                    for section in CHECKSECTIONS:
                                        el=page.locator('[data-v2352-section="'+section+'"]')
                                        if el.count()!=1:raise ValueError("Missing section "+section)
                                        el.scroll_into_view_if_needed(timeout=9000)
                                        geometry=el.evaluate("""e=>{
                                          const r=e.getBoundingClientRect();
                                          const h=e.querySelector('h2'),t=h?.getBoundingClientRect();
                                          const cards=Array.from(e.querySelectorAll('.v2352-card,.v2352-step')).map(
                                            n=>{const b=n.getBoundingClientRect();return {
                                              left:b.left,right:b.right,width:b.width,scroll:n.scrollWidth,client:n.clientWidth};});
                                          return {rect:{left:r.left,right:r.right,top:r.top,bottom:r.bottom},
                                            heading:!!h&&t.width>0&&t.height>0&&t.left>=-4&&t.right<=innerWidth+4,
                                            cards};}""")
                                        if not geometry["heading"]:raise ValueError(section+" H2 clipped")
                                        for pos,card in enumerate(geometry["cards"]):
                                            if card["left"]<-4 or card["right"]>width+4:
                                                raise ValueError(section+" card extends beyond viewport "+str(pos))
                                            if card["scroll"]>card["client"]+3:
                                                raise ValueError(section+" internal text overflows "+str(pos))
                                        r["section_layout_checks"]+=1
                                        if section in ("levels","parent","errors"):
                                            screenshot=SCREEN/(filename[:-5]+"-"+str(width)+"-"+section+".png")
                                            page.screenshot(path=str(screenshot),full_page=False,timeout=24000)
                                            r["screenshots"].append(screenshot.name)
                                    faq=page.locator("details.faq-item")
                                    if faq.count()!=6:raise ValueError("Missing 6 FAQ questions")
                                    r["actual_page_combinations"]+=1
                                    # Verify real button click and actual form reachable (never POST).
                                    for cta_kind,selector in (("hero",".hero-actions a[href='#consultation-preview']"),
                                                              ("parent","a.v2352-small-cta[href='#consultation-preview']")):
                                        link=page.locator(selector)
                                        if link.count()<1:raise ValueError(cta_kind+" consultation CTA absent")
                                        link.first.scroll_into_view_if_needed(timeout=10000)
                                        link.first.click(timeout=13000)
                                        dest=page.locator("#consultation-preview")
                                        if dest.count()!=1:raise ValueError(cta_kind+" anchor target absent")
                                        form=dest.locator("form").first
                                        if form.count()!=1:raise ValueError(cta_kind+" consultation form absent")
                                        structure=form.evaluate("""f=>{
                                            const fields=['name','phone','area','consent'];
                                            const out={};
                                            for(const field of fields){let e=f.querySelector('[name="'+field+'"]');
                                                out[field]=!!e&&(!(['name','phone','area','consent'].includes(field))||e.required)}
                                            const hidden=f.querySelector('[name="wantedClass"]');
                                            out.wantedClass=hidden?.value||'';
                                            out.submitButton=!!f.querySelector('button[type="submit"],button:not([type])');
                                            return out;}""")
                                        if not all(structure.get(n) for n in ("name","phone","area","consent","submitButton")):
                                            raise ValueError(cta_kind+" mandatory form field missing "+str(structure))
                                        if label not in structure["wantedClass"]:
                                            raise ValueError(cta_kind+" wrong selected course "+str(structure))
                                        r["cta_click_checks"]+=1
                                        r["consultation_form_reached"]+=1
                                        r["verified_form_structures"]+=1
                                        shot=SCREEN/(filename[:-5]+"-"+str(width)+"-"+cta_kind+"-consultation.png")
                                        dest.scroll_into_view_if_needed(timeout=12000)
                                        page.screenshot(path=str(shot),full_page=False,timeout=24000)
                                        r["screenshots"].append(shot.name)
                                    group=page.locator("article.related-group").filter(
                                        has=page.locator("h3",has_text="학생 영어")).first
                                    if group.count()!=1 or group.locator("a").count()!=6:
                                        raise ValueError("Expected 6 locality student navigation cards")
                                    for mode in ALL_MODES:
                                        anchor=group.locator('a.related-course-tutor, a.related-course-conversation').filter(
                                            has=page.locator("span",has_text=(
                                                "초등학생영어과외" if mode=="elem-tutor" else
                                                "중학생영어과외" if mode=="mid-tutor" else
                                                "고등학생영어과외" if mode=="high-tutor" else
                                                "초등학생영어회화" if mode=="elem-conv" else
                                                "중학생영어회화" if mode=="mid-conv" else
                                                "고등학생영어회화"))).first
                                        if anchor.count()!=1:
                                            raise ValueError("Student link text absent "+mode)
                                        href=anchor.get_attribute("href") or ""
                                        expected="/"+slug+"-"+mode
                                        if href.rstrip("/") not in (expected,expected+".html"):
                                            raise ValueError("Student link wrong "+mode+" href="+href)
                                        r["student_navigation_checks"]+=1
                                    r["checks"].append({"file":filename,"width":width,
                                          "h1":d["h1"],"sections":5,"faqs":6,
                                          "consultation_ctas":2,"student_links":6,
                                          "doc_width":d["scrollWidth"],"status":"PASS"})
                                    print("V2352_BROWSER_PASS",width,filename,"5SECTIONS_2CTA_6LINKS",flush=True)
                                except Exception as exc:
                                    failure(r,filename+"@"+str(width),"chromium_screen_or_journey",repr(exc))
                                    if len(r["errors"])<10:
                                        try:page.screenshot(path=str(SCREEN/(filename[:-5]+"-"+str(width)+"-failure.png")),full_page=False,timeout=8000)
                                        except Exception:pass
                                finally:page.close()
                    finally:ctx.close()
            finally:browser.close()
        r["screenshot_count"]=len(list(SCREEN.glob("*.png")))
        expected=6*len(VIEWPORTS)
        r["status"]="PASS_V2352_LIVE_TUTOR_RESPONSIVE_CTA" if (
            len(r["checks"])==expected and r["section_layout_checks"]==expected*5 and
            r["cta_click_checks"]==expected*2 and r["student_navigation_checks"]==expected*6 and
            not r["errors"]) else "HOLD_V2352_LIVE_TUTOR_RESPONSIVE_CTA"
    except Exception:
        failure(r,"(browser_runner)","exception",traceback.format_exc()[-2500:])
        r["status"]="HOLD_V2352_LIVE_TUTOR_RESPONSIVE_CTA"
    finally:emit("V2352_LIVE_BROWSER_QA.json",r)
    return r["status"].startswith("PASS")

if __name__=="__main__":
    phase=sys.argv[1] if len(sys.argv)>1 else "http"
    sys.exit(0 if (http_qa() if phase=="http" else browser_qa()) else 1)
