#!/usr/bin/env python3
"""Read-only v23.5 review Draft HTTP + Chromium verification; no submissions or production actions."""
import argparse
import ast
import json
import os
import re
import struct
import sys
import time
import traceback
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote

SITE = "englishpt-final-ia-review-bokdong.netlify.app"
ALIAS = os.environ.get("V235_ALIAS_URL","").rstrip("/")
DRAFT = os.environ.get("REVIEW_DEPLOY_URL","").rstrip("/")
ROOT = Path("preview-site")
REPORTS = Path("draft-review-report")
SAMPLES = [
    "englishpt.html",
    "student-english.html",
    "seoul-jongno-sajikdong-worker-english-conv-academy.html",
    "seoul-jongno-sajikdong-beginner-english-conv.html",
    "seoul-jongno-sajikdong-toeic.html",
    "seoul-jongno-sajikdong-ielts.html",
    "seoul-jongno-sajikdong-high-conv.html",
    "dalseo-songhyeondong.html",
    "station-gangnam.html",
    "station-amsayeoksagongwon.html",
    "station-gukjegeumyungsenteo-busaneunhaeng-worker-english-conv-academy.html",
]
CHOICES=[
    "초등학생영어과외", "중학생영어과외", "고등학생영어과외",
    "초등학생영어회화", "중학생영어회화", "고등학생영어회화",
]
HUB_IDS=("elementary-tutor","middle-tutor","high-tutor","elementary","middle","high")
BINDING_RE = re.compile(r'<meta\b[^>]*>',re.I)
ATTR_RE = re.compile(r'([\w:.-]+)\s*=\s*["\x27]([^"\x27]*)["\x27]')
STUDENT_GROUP=re.compile(r'<article class="related-group"><h3>학생 영어</h3><div class="related-course-links">(.*?)</div></article>',re.S)
A_RE=re.compile(r'<a\b[^>]*>.*?</a>',re.S)
H1_RE=re.compile(r'<h1\b[^>]*>.*?</h1>',re.I|re.S)

def guard():
    for url in (ALIAS,DRAFT):
        u=urlsplit(url)
        if u.scheme!="https" or not u.hostname or not u.hostname.endswith("--"+SITE) or "englishpt.kr" in url:
            raise ValueError("Outside isolated v23.5 Review-only Netlify site: "+url)
    if ALIAS==DRAFT:raise ValueError("Expected distinct stable alias and immutable deploy ID URL")
    return True

def out(name,data):
    REPORTS.mkdir(parents=True,exist_ok=True)
    p=REPORTS/name
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("REPORT_PATH",p,flush=True)

def fetch(url):
    last=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'ENGLISH-PT-v235-read-only-verification'})
            with urllib.request.urlopen(req,timeout=40) as r:
                return r.status,r.read(),dict(r.headers),r.url
        except Exception as exc:
            last=exc
            if attempt<2:time.sleep(3+3*attempt)
    raise last

def attrs(tag):
    return {k.lower():v for k,v in ATTR_RE.findall(tag)}

def meta(doc,key,attr="property"):
    return [attrs(tag).get("content","") for tag in BINDING_RE.findall(doc)
            if attrs(tag).get(attr)==key]

class StudentAnchor(HTMLParser):
    """Parse HTML anchors regardless of whether Netlify quotes href attributes."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.href = None
    def handle_starttag(self,tag,attrs):
        if tag=="a" and self.href is None:
            self.href=dict(attrs).get("href")


def approved_og_template_paths():
    # Only the 29 approved 1200x630 templates used by the metadata generator
    # are share-image QA targets. A legacy asset folder contains ~22k
    # unrelated historical PNGs of different dimensions.
    script=Path("scripts/v23_4_og_landscape_all_pages.py")
    tree=ast.parse(script.read_text(encoding="utf-8"),filename=str(script))
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(
            isinstance(t,ast.Name) and t.id=="CATS" for t in node.targets
        ):
            cats=ast.literal_eval(node.value)
            names=[row[0]+".png" for row in cats]
            if len(names)!=29 or len(set(names))!=29:
                raise ValueError("29 unique OG design templates not found")
            root=ROOT/"assets/images/og-pages"
            missing=[name for name in names if not (root/name).is_file()]
            if missing:
                raise ValueError("Generated OG designs missing: "+str(missing[:10]))
            return [root/name for name in names]
    raise ValueError("Cannot read approved OG designs from source")


def identity():
    return dict(version="v23.5",draft_url=DRAFT,alias_url=ALIAS,
                source_run="38689660290",
                source_sha="a18b8901ecda7d37f65e35b15f03d579ec63c70f",
                hero_source_run="38843408620",
                published_to_production=False,forms_submitted=False,
                checked_at=datetime.now(timezone.utc).isoformat())

def http_check():
    report={**identity(),"status":"RUNNING","pages_checked":0,"images_checked":0,
            "checks":[],"errors":[],"warnings":[]}
    errors=report["errors"]
    try:
        guard()
        pages=sorted([p.name for p in ROOT.glob("*.html") if p.name not in ("index.html","404.html")])
        assert len(pages)==140391
        stride=max(1,len(pages)//22)
        selected=list(dict.fromkeys(["index.html","courses.html","exam-english.html","stations.html"]+SAMPLES+pages[::stride][:22]))
        images=set()
        for name in selected:
            try:
                url=DRAFT+"/"+name
                status,raw,headers,landed=fetch(url)
                html=raw.decode("utf-8",errors="replace")
                if status!=200 or urlsplit(landed).hostname!=urlsplit(DRAFT).hostname:
                    raise ValueError("HTTP status/redirect invalid")
                if not H1_RE.search(html):
                    raise ValueError("missing H1")
                if not re.search(r'<h1\b[^>]*data-v235-hero-wrap="(?:regular|long|xlong)"',html,re.I):
                    raise ValueError("v23.5 mobile H1 marker absent")
                if meta(html,"og:image:width")!=["1200"] or meta(html,"og:image:height")!=["630"]:
                    raise ValueError("incorrect OG image dimensions")
                og=meta(html,"og:image")
                tw=meta(html,"twitter:image","name")
                if len(og)!=1 or og!=tw or not og[0].startswith(ALIAS+"/assets/images/og-pages/"):
                    raise ValueError("OG/Twitter images not pointed at isolated draft alias")
                images.add(og[0])
                # Netlify _headers should prohibit Draft indexing.
                robot=headers.get("X-Robots-Tag",headers.get("x-robots-tag",""))
                if "noindex" not in str(robot).lower():
                    raise ValueError("Draft HTTP response missing X-Robots-Tag: noindex")
                if name=="seoul-jongno-sajikdong-worker-english-conv-academy.html":
                    m=STUDENT_GROUP.search(html)
                    if not m:raise ValueError("student nav group missing")
                    anchors=A_RE.findall(m.group(1))
                    if len(anchors)!=6:raise ValueError("student nav !=6")
                    for i,anchor in enumerate(anchors):
                        if CHOICES[i] not in anchor:
                            raise ValueError("student choices out of order: "+CHOICES[i])
                        parser=StudentAnchor()
                        parser.feed(anchor)
                        href=(parser.href or "").strip()
                        if not href or href.startswith(("javascript:","mailto:","tel:")):
                            raise ValueError("student href unusable: "+str(i)+" "+repr(href))
                        # Netlify may produce extensionless pretty routes and
                        # HTML minification may remove href quotes. Validate
                        # the actual destination and grade anchor, not syntax.
                        dest=urljoin(url,href)
                        target=urlsplit(dest)
                        if target.scheme!="https" or target.hostname!=urlsplit(DRAFT).hostname:
                            raise ValueError("student href leaves Draft host: "+repr(href))
                        status,body,_,_=fetch(dest.split("#",1)[0])
                        if status!=200 or b"<h1" not in body.lower():
                            raise ValueError("student href destination invalid: "+repr(href))
                        if i>0 and target.fragment!=HUB_IDS[i]:
                            raise ValueError("student href grade anchor mismatch: "+repr(href))
                        if target.fragment:
                            # Proper HTML parser tolerates either single or
                            # double quoted IDs in the destination page.
                            class IdParser(HTMLParser):
                                def __init__(self):
                                    super().__init__()
                                    self.ids=set()
                                def handle_starttag(self,tag,attrs):
                                    d=dict(attrs)
                                    if d.get("id"):
                                        self.ids.add(d["id"])
                            parser_ids=IdParser()
                            parser_ids.feed(body.decode("utf-8","replace"))
                            if target.fragment not in parser_ids.ids:
                                raise ValueError("student href anchor missing: "+repr(href))
                    print("PASS_V235_LIVE_STUDENT_LINKS",len(anchors),flush=True)
                report["pages_checked"]+=1
                report["checks"].append({"name":name,"http":200,"html_bytes":len(raw),"og":og[0],
                                         "noindex":True})
                print("V235_LIVE_HTTP_PAGE",name,"PASS",flush=True)
            except Exception as exc:
                errors.append({"page":name,"reason":repr(exc)})
                print("::error::HTTP "+name+" "+str(exc),flush=True)
        # Limit dimensions QA to the exact 29 approved 1200x630 OG PNGs.
        # 21,961 unrelated legacy PNGs must not cause false OG failures.
        paths=approved_og_template_paths()
        for image_url in images:
            if image_url.rsplit("/",1)[-1] not in {p.name for p in paths}:
                errors.append({"image":image_url,"reason":"OG refers to unapproved image"})
        for path in paths:
            try:
                url=ALIAS+"/assets/images/og-pages/"+path.name
                status,data,headers,landed=fetch(url)
                if status!=200 or not data.startswith(b'\x89PNG\r\n\x1a\n'):
                    raise ValueError("Draft OG image missing or not PNG")
                w,h=struct.unpack(">II",data[16:24])
                if (w,h)!=(1200,630):
                    raise ValueError("OG dimensions differ from 1200x630")
                report["images_checked"]+=1
            except Exception as exc:
                errors.append({"image":path.name,"reason":repr(exc)})
        for file in ("robots.txt","sitemap-index.xml"):
            try:
                status,data,_,_=fetch(DRAFT+"/"+file)
                if status!=200 or len(data)<30:
                    raise ValueError("missing/empty SEO file")
                report["checks"].append({"name":file,"http":200,"bytes":len(data)})
            except Exception as exc:
                errors.append({"file":file,"reason":repr(exc)})
        report["status"]="PASS_V235_DRAFT_HTTP_OG_SEO" if not errors else "FAIL_V235_DRAFT_HTTP_OG_SEO"
    except Exception:
        errors.append({"runner":"http","reason":traceback.format_exc()[-1500:]})
        report["status"]="FAIL_V235_DRAFT_HTTP_OG_SEO"
    finally:
        report["error_count"]=len(errors)
        out("V235_DRAFT_HTTP_OG_SEO.json",report)
        print(report["status"],"pages",report["pages_checked"],"images",report["images_checked"],
              "errors",len(errors),flush=True)
    return not errors

def chromium_check():
    report={**identity(),"status":"RUNNING","tested":[],"errors":[],"screenshots":0}
    failures=report["errors"]
    folder=REPORTS/"screenshots"
    folder.mkdir(parents=True,exist_ok=True)
    try:
        guard()
        from playwright.sync_api import sync_playwright
        import shutil
        with sync_playwright() as pw:
            binary=shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
            args={"headless":True,"args":["--no-sandbox","--disable-dev-shm-usage"]}
            if binary:args["executable_path"]=binary
            browser=pw.chromium.launch(**args)
            try:
                matrix=[(name,width) for width in (390,1440) for name in SAMPLES]
                for width in (320,430):
                    matrix.extend([(name,width) for name in SAMPLES if name.startswith(("station-amsa","station-gukje"))])
                for name,width in matrix:
                    context=browser.new_context(viewport={"width":width,"height":900},
                        device_scale_factor=1,is_mobile=(width<600),has_touch=(width<600))
                    # Guard against actual form submissions, even accidental script-initiated POST.
                    context.route("**/*",lambda route: route.abort() if route.request.method not in ("GET","HEAD") else route.continue_())
                    page=context.new_page()
                    try:
                        res=page.goto(DRAFT+"/"+name,wait_until="domcontentloaded",timeout=50000)
                        if res is None or res.status!=200:raise ValueError("Live page HTTP invalid")
                        page.evaluate("() => document.fonts.ready")
                        hero=page.locator(".hero h1").first
                        if hero.count()!=1:raise ValueError("H1 not in Hero")
                        m=hero.evaluate("""e=>{
                          const r=e.getBoundingClientRect(),st=getComputedStyle(e);
                          return {text:e.innerText,mode:e.dataset.v235HeroWrap,
                            left:r.left,right:r.right,height:r.height,
                            width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
                            lineHeight:parseFloat(st.lineHeight),font:st.fontSize};
                        }""")
                        problem=[]
                        if not m["mode"]:problem.append("hero wrap class missing")
                        if m["left"]< -3 or m["right"]>width+3 or m["scrollWidth"]>width+3:
                            problem.append("hero or document horizontal overflow")
                        rows=round(m["height"]/m["lineHeight"]) if m["lineHeight"] else 99
                        if rows>(5 if width==320 else 4 if width<600 else 3):
                            problem.append("hero line count excessive:"+str(rows))
                        # Navigate form without submitting anything.
                        if width in (390,1440) and name.endswith("worker-english-conv-academy.html"):
                            visible=page.locator("[data-open-form]:visible")
                            if visible.count():
                                visible.first.click(timeout=5000)
                                modal=page.locator("#applyModal")
                                if modal.count() and not modal.evaluate("e=>e.classList.contains('open')"):
                                    problem.append("form modal did not open")
                                page.goto(DRAFT+"/"+name,wait_until="domcontentloaded",timeout=45000)
                            elif page.locator('a[href="#consultation-preview"]').count() and page.locator("#consultation-preview").count():
                                pass
                            else:
                                problem.append("consultation navigation unavailable")
                        if width in (390,1440):
                            filename=name.removesuffix(".html")+"-"+str(width)+".png"
                            page.screenshot(path=str(folder/filename),full_page=False,timeout=15000)
                        report["tested"].append({"page":name,"viewport":width,"h1":m,
                                                 "line_count":rows,"errors":problem})
                        for issue in problem:
                            failures.append({"page":name,"viewport":width,"reason":issue})
                        print("V235_LIVE_CHROMIUM",width,name,"PASS" if not problem else problem,flush=True)
                    except Exception as exc:
                        failures.append({"page":name,"viewport":width,"reason":str(exc)[:650]})
                    finally:
                        context.close()
            finally:
                browser.close()
        report["status"]="PASS_V235_DRAFT_CHROMIUM" if not failures else "FAIL_V235_DRAFT_CHROMIUM"
    except Exception:
        failures.append({"runner":"chromium","reason":traceback.format_exc()[-1500:]})
        report["status"]="FAIL_V235_DRAFT_CHROMIUM"
    finally:
        report["screenshots"]=len(list(folder.glob("*.png")))
        report["error_count"]=len(failures)
        out("V235_DRAFT_CHROMIUM.json",report)
        print(report["status"],"checked",len(report["tested"]),"screenshots",report["screenshots"],
              "errors",len(failures),flush=True)
    return not failures

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--phase",choices=("http","chromium"),required=True)
    args=parser.parse_args()
    sys.exit(0 if (http_check() if args.phase=="http" else chromium_check()) else 1)
