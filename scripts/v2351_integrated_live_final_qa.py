#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v23.5.1 representative integrated LIVE Preview QA: 3 audiences x 2 breakpoints.
Never submit forms or POST; no remote mutation, no Netlify deploy.
"""
import argparse
import json
import os
import re
import sys
import traceback
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
from datetime import datetime,timezone

import requests
from playwright.sync_api import sync_playwright

HOST_SUFFIX="--englishpt-final-ia-review-bokdong.netlify.app"
STUDENT={
    "elem-tutor":("초등학생영어과외","읽기"),
    "mid-tutor":("중학생영어과외","내신"),
    "high-tutor":("고등학생영어과외","수능"),
    "elem-conv":("초등학생영어회화","말하기"),
    "mid-conv":("중학생영어회화","말하기"),
    "high-conv":("고등학생영어회화","발표"),
}
SLUGS=("gyeongnam-milyang-naeidong","seoul-jongno-sajikdong")
EXAM_TYPES={
    "toeic":"토익","toeic-speaking":"토익스피킹","opic":"오픽",
    "ielts":"아이엘츠","toefl":"토플","duolingo":"듀오링고",
    "toeic-academy":"토익학원","ielts-academy":"아이엘츠학원",
}
ADULT_TYPES={
    "worker-english-conv-academy":"직장인영어회화학원",
    "beginner-english-conv":"왕초보영어회화",
    "adult-english-conv-academy":"성인영어회화학원",
    "english-conv-academy":"영어회화학원",
    "biz-business-conv":"비즈니스영어",
    "housewife-conv":"주부영어회화",
    "univ-conv":"대학생영어회화",
    "jobseeker-conv":"취준생영어회화",
}
HUBS=("englishpt.html","courses.html","student-english.html",
      "exam-english.html","english-conversation.html","stations.html")
STATIONS=("station-gangnam.html","station-amsayeoksagongwon.html")
CHECKS=[]
for name in HUBS:CHECKS.append(("hub",name,None))
for slug in SLUGS:
    for mode,(label,focus) in STUDENT.items():
        CHECKS.append(("student",slug+"-"+mode+".html",{"mode":mode,"label":label,"focus":focus}))
for mode,label in EXAM_TYPES.items():
    CHECKS.append(("exam",SLUGS[0]+"-"+mode+".html",{"mode":mode,"label":label}))
for mode,label in ADULT_TYPES.items():
    CHECKS.append(("adult",SLUGS[0]+"-"+mode+".html",{"mode":mode,"label":label}))
for name in STATIONS:CHECKS.append(("station",name,None))
assert len(CHECKS)==36,len(CHECKS)

def run():
    p=argparse.ArgumentParser()
    p.add_argument("--draft",required=True)
    p.add_argument("--og-alias",required=True)
    p.add_argument("--report-dir",type=Path,default=Path("v2351-audience-final"))
    args=p.parse_args()
    BASE=args.draft.rstrip("/")
    OG_ALIAS=args.og_alias.rstrip("/")
    OUT=args.report_dir
    OUT.mkdir(parents=True,exist_ok=True)
    for domain in (BASE,OG_ALIAS):
        u=urlsplit(domain)
        assert u.scheme=="https" and (u.hostname or "").endswith(HOST_SUFFIX)
        assert "englishpt.kr" not in domain
    assert BASE!=OG_ALIAS
    rows=[];issues=[];warnings=[];counter=Counter()
    screens=OUT/"screenshots";screens.mkdir(exist_ok=True)
    result={"status":"RUNNING","draft":BASE,"og_alias":OG_ALIAS,
        "started_at":datetime.now(timezone.utc).isoformat(),
        "categories":{"hub":0,"student":0,"exam":0,"adult":0,"station":0},
        "tested_pages":len(CHECKS),"viewports":[390,1440],
        "expected_browser_combinations":len(CHECKS)*2,
        "browser_checked":0,"http_checked":0,
        "student_course_labels_checked":0,
        "consultation_cta_activated":0,"consultation_forms_reached":0,
        "consultation_fields_verified":0,
        "screenshots":0,"errors":[],"warnings":[],
        "form_submissions":0,"non_get_requests_blocked":0,
        "production_deployed":False,"draft_deployed_by_this_workflow":False,
        "coverage_note":"Representative LIVE HTTP+browser tests; all generated pages were separately checked offline in runs 38864767374 and SEO full-audit run",
        "limitations":["Never tested actual form submission / email receipt",
                       "Not every one of 158571 pages was opened in a live browser",
                       "No claim of real Google/Naver indexing from Preview checks"]}
    def problem(name,width,message):
        x={"page":name,"viewport":width,"problem":str(message)[:700]}
        issues.append(x)
        print("::error::"+json.dumps(x,ensure_ascii=False),flush=True)
    def report():
        result["browser_checked"]=len(rows)
        result["screenshots"]=len(list(screens.glob("*.png")))
        result["errors"]=issues
        result["warnings"]=warnings
        result["categories"]=dict(counter)
        result["status"]="PASS_V2351_AUDIENCE_FINAL_LIVE_QA" if not issues and len(rows)==len(CHECKS)*2 else "HOLD_V2351_AUDIENCE_FINAL_LIVE_QA"
        result["finished_at"]=datetime.now(timezone.utc).isoformat()
        (OUT/"V2351_AUDIENCE_FINAL_QA.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        (OUT/"V2351_AUDIENCE_DETAIL_ROWS.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print(result["status"],"checks",len(rows),"errors",len(issues),"forms",result["consultation_forms_reached"],flush=True)
    try:
        # One simple HTTP HEAD/GET to every URL first; fail independently per URL.
        client=requests.Session()
        client.headers.update({"User-Agent":"ENGLISHPT v23.5.1 safe integrated QA"})
        for category,name,expect in CHECKS:
            try:
                r=client.get(BASE+"/"+name,timeout=38,allow_redirects=False)
                if r.status_code!=200:raise ValueError(f"HTTP {r.status_code}")
                robot=r.headers.get("X-Robots-Tag","")
                if "noindex" not in robot.lower():
                    raise ValueError("Preview missing X-Robots-Tag noindex")
                doc=r.text
                if not re.search(r'<h1\b[^>]*>',doc,re.I):
                    raise ValueError("H1 missing")
                if not re.search(r'<meta property="og:image" content="'+re.escape(OG_ALIAS)+r'/assets/images/og-pages/[^"]+\.png"',doc):
                    raise ValueError("OG image is not on Draft-only alias")
                if category in ("student","exam","adult"):
                    canonical=f'<link rel="canonical" href="https://englishpt.kr/{name}">'
                    if canonical not in doc:raise ValueError("canonical mismatch")
                if category=="student":
                    label=expect["label"]
                    h1=re.search(r'<h1[^>]*>(.*?)</h1>',doc,re.I|re.S)
                    plain=re.sub(r'<[^>]*>',"",h1.group(1)) if h1 else ""
                    if label not in plain:raise ValueError("wrong student course in H1")
                    if expect["focus"] not in doc:
                        raise ValueError("course-specific content missing "+expect["focus"])
                    # Validate all six regional student links, NOT generic hub fallbacks.
                    group=re.search(r'<article class="related-group"><h3>학생 영어</h3><div class="related-course-links">(.*?)</div></article>',doc,re.S)
                    if not group:raise ValueError("student six links absent")
                    slug=name[:-(len(expect["mode"])+6)]
                    # Netlify Pretty URLs may serve links without ".html".
                    # Accept only the exact locality-and-course target, with or
                    # without that suffix. No generic student hub fallbacks.
                    for mode,(label2,_) in STUDENT.items():
                        target="/"+slug+"-"+mode
                        anchors=re.findall(r'<a\b[^>]*>.*?</a>',group.group(1),re.S|re.I)
                        found=False
                        for anchor in anchors:
                            href_match=re.search(r'\bhref=["\x27]([^"\x27]+)["\x27]',anchor)
                            if not href_match:continue
                            href=href_match.group(1).strip()
                            if href not in (target,target+".html"):continue
                            label_plain=re.sub(r'<[^>]*>',"",anchor)
                            if label2 not in label_plain:
                                raise ValueError("student local route category label mismatch "+href)
                            found=True
                            break
                        if not found:raise ValueError("missing exact student local route "+target)
                        result["student_course_labels_checked"]+=1
                if category in ("exam","adult"):
                    if expect["label"] not in doc:
                        raise ValueError("intended course label absent "+expect["label"])
                result["http_checked"]+=1
                print("Q3_LIVE_HTTP_PASS",category,name,flush=True)
            except Exception as ex:
                problem(name,"HTTP",ex)
        # Actual user journeys on mobile and PC. Only GET/HEAD is permitted.
        with sync_playwright() as pw:
            import shutil
            chrome=shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
            cfg={"headless":True,"args":["--no-sandbox","--disable-dev-shm-usage"]}
            if chrome:cfg["executable_path"]=chrome
            browser=pw.chromium.launch(**cfg)
            try:
                for width in (390,1440):
                    context=browser.new_context(viewport={"width":width,"height":900},
                        device_scale_factor=1,is_mobile=(width<600),has_touch=(width<600))
                    def only_get(route):
                        if route.request.method not in ("GET","HEAD"):
                            result["non_get_requests_blocked"]+=1
                            route.abort()
                        else:route.continue_()
                    context.route("**/*",only_get)
                    try:
                        for category,name,expected in CHECKS:
                            page=context.new_page()
                            # Prevent all form submits, even via accidental Enter key.
                            page.add_init_script("""document.addEventListener('submit',e=>{
                                e.preventDefault();e.stopImmediatePropagation();
                            },true)""")
                            problems=[]
                            mode="none"
                            form_reached=False
                            try:
                                response=page.goto(BASE+"/"+name,wait_until="domcontentloaded",timeout=55000)
                                if not response or response.status!=200:raise ValueError("invalid browser HTTP")
                                page.evaluate("() => document.fonts.ready")
                                state=page.evaluate("""() => {
                                    let e=document.querySelector('.hero h1')||document.querySelector('h1'),
                                        r=e?.getBoundingClientRect();
                                    return {h1:e?.innerText||'',h1visible:!!r&&r.width>0&&r.height>0,
                                       x:r?.x||0,right:r?.right||0,height:r?.height||0,
                                       viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth};
                                }""")
                                if not state["h1visible"]:problems.append("H1 invisible")
                                if state["scrollWidth"]>width+3:problems.append("page horizontal overflow")
                                if state["right"]>width+3 or state["x"]< -3:problems.append("H1 outside viewport")
                                if category=="student" and expected["label"] not in state["h1"]:
                                    problems.append("student course H1 not aligned to category")
                                # Use visible CTA modal or inline, preserve distinction for station hub.
                                modal=page.locator("[data-open-form]:visible")
                                inline=page.locator('a[href="#consultation-preview"]:visible')
                                if modal.count():
                                    modal.first.click(timeout=9000)
                                    mode="modal"
                                    dialog=page.locator("#applyModal")
                                    form_reached=dialog.count()>0 and dialog.evaluate(
                                        "e=>e.classList.contains('open') && e.getAttribute('aria-hidden') !== 'true'")
                                elif inline.count():
                                    inline.first.click(timeout=9000)
                                    mode="inline"
                                    target=page.locator("#consultation-preview")
                                    form_reached=target.count()>0
                                    if form_reached:target.scroll_into_view_if_needed(timeout=6000)
                                elif name=="stations.html":
                                    link=page.locator('a[href*="station-"]').first
                                    if link.count():
                                        link.scroll_into_view_if_needed(timeout=7000)
                                        link.click(timeout=9000)
                                        page.wait_for_load_state("domcontentloaded",timeout=30000)
                                        modal2=page.locator("[data-open-form]:visible")
                                        if modal2.count():
                                            modal2.first.click(timeout=9000)
                                            dialog=page.locator("#applyModal")
                                            form_reached=dialog.count()>0 and dialog.evaluate("e=>e.classList.contains('open')")
                                            mode="station-directory-to-modal"
                                        else:
                                            inline2=page.locator('a[href="#consultation-preview"]:visible')
                                            if inline2.count():
                                                inline2.first.click(timeout=9000)
                                                form_reached=page.locator("#consultation-preview").count()>0
                                                mode="station-directory-to-inline"
                                if mode!="none":result["consultation_cta_activated"]+=1
                                if not form_reached:problems.append("consultation CTA not reachable")
                                else:
                                    result["consultation_forms_reached"]+=1
                                    root=page.locator("#applyModal") if "modal" in mode else page.locator("#consultation-preview")
                                    form=root.locator("form").first
                                    if form.count()!=1:problems.append("consultation form missing after CTA")
                                    else:
                                        needed=("name","phone","area","consent")
                                        missing=[key for key in needed if form.locator('[name="'+key+'"]').count()!=1]
                                        if missing:problems.append("missing form fields:"+",".join(missing))
                                        else:result["consultation_fields_verified"]+=1
                                shot=screens/(name.removesuffix(".html")+"-"+str(width)+".png")
                                page.screenshot(path=str(shot),full_page=False,timeout=22000)
                                rows.append({"category":category,"page":name,"width":width,
                                    "h1":state["h1"],"scroll":state["scrollWidth"],
                                    "mode":mode,"form_reached":form_reached,
                                    "errors":problems,"screenshot":shot.name})
                                counter[category]+=1
                                print("Q3_CHROMIUM",width,category,name,"PASS" if not problems else problems,flush=True)
                            except Exception as exc:
                                problems.append(str(exc)[:500])
                                rows.append({"category":category,"page":name,"width":width,
                                    "mode":mode,"form_reached":False,"errors":problems})
                            for err in problems:problem(name,width,err)
                            page.close()
                    finally:context.close()
            finally:browser.close()
    except Exception:
        problem("(runner)","fatal",traceback.format_exc()[-2100:])
    finally:report()
    return 0 if result["status"].startswith("PASS") else 1
if __name__=="__main__":sys.exit(run())
