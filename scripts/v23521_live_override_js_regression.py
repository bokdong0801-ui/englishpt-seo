#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only Chromium regression against immutable deployed HTML with ONLY pilot.js intercepted.

Exercise the exact proposed fix without uploading 158,571 pages a second time.
Never posts forms, never modifies deployed HTML, and tests non-tutor behavior too.
"""
import argparse,json,shutil,sys,traceback
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE="https://6ad22244efa528796be5b050--englishpt-final-ia-review-bokdong.netlify.app"
SLUGS=("gyeongnam-milyang-naeidong","seoul-jongno-sajikdong")
TUTORS=("elem-tutor","mid-tutor","high-tutor")
OTHER=("elem-conv","worker-english-conv-academy")
WIDTHS=(320,390,430,1440)

def main():
    args=argparse.ArgumentParser()
    args.add_argument("--patched-js",type=Path,required=True)
    args.add_argument("--report",type=Path,required=True)
    args.add_argument("--screenshots",type=Path,required=True)
    opt=args.parse_args()
    code=opt.patched_js.read_text("utf8")
    opt.screenshots.mkdir(parents=True,exist_ok=True)
    r={"status":"RUNNING","draft_redeployed":False,"production_deployed":False,
       "form_submitted":False,"patched_asset_interceptions":0,
       "tutor_viewports":0,"tutor_cta_clicks":0,"unchanged_other_course_cases":0,
       "errors":[],"checks":[]}
    try:
        with sync_playwright() as pw:
            bin=shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
            kwargs={"headless":True,"args":["--no-sandbox","--disable-dev-shm-usage"]}
            if bin:kwargs["executable_path"]=bin
            browser=pw.chromium.launch(**kwargs)
            try:
                for width in WIDTHS:
                    ctx=browser.new_context(viewport={"width":width,"height":900},
                      has_touch=width<=430,is_mobile=width<=430)
                    ctx.route("**/*",lambda route:route.continue_() if route.request.method in ("GET","HEAD") else route.abort())
                    page=ctx.new_page()
                    page.add_init_script("""document.addEventListener('submit',e=>{
                       e.preventDefault();e.stopImmediatePropagation();},true);""")
                    def patched_runtime(route):
                        r["patched_asset_interceptions"]+=1
                        route.fulfill(status=200,body=code,content_type="application/javascript")
                    page.route("**/pilot.js*",patched_runtime)
                    try:
                        for slug in SLUGS:
                            for mode in TUTORS:
                                page_name=slug+"-"+mode+".html"
                                try:
                                    response=page.goto(BASE+"/"+page_name,wait_until="domcontentloaded",timeout=70000)
                                    if not response or response.status!=200:
                                        raise ValueError("Missing tutor page")
                                    page.evaluate("() => document.fonts.ready")
                                    form=page.locator("#consultation-preview form")
                                    submit=form.locator('button[type="submit"]').first
                                    rt=form.locator('input[name="requestType"]').first
                                    sj=form.locator('input[name="subject"]').first
                                    nav=page.locator(".nav-cta").first
                                    def assert_correct(label):
                                        if "영어과외 상담 신청" not in submit.inner_text():
                                            raise ValueError(label+" visible tutor submit text wrong "+repr(submit.inner_text()))
                                        if rt.input_value()!="영어과외 상담 신청":
                                            raise ValueError(label+" requestType wrong "+repr(rt.input_value()))
                                        if "영어과외 상담 신청" not in sj.input_value():
                                            raise ValueError(label+" subject wrong "+repr(sj.input_value()))
                                        if "영어과외 상담 신청" not in nav.inner_text():
                                            raise ValueError(label+" nav tutor CTA wrong")
                                    assert_correct("load")
                                    for button in (".hero-actions a[href='#consultation-preview']",
                                                   "a.v2352-small-cta[href='#consultation-preview']"):
                                        cta=page.locator(button)
                                        if cta.count()!=1:raise ValueError("CTA missing "+button)
                                        cta.scroll_into_view_if_needed()
                                        cta.click(timeout=12000)
                                        assert_correct("after CTA")
                                        r["tutor_cta_clicks"]+=1
                                    if page.evaluate('document.documentElement.scrollWidth')>width+4:
                                        raise ValueError("Doc overflow after patched JS")
                                    r["tutor_viewports"]+=1
                                    if width in (390,1440):
                                        form.scroll_into_view_if_needed()
                                        page.screenshot(path=str(opt.screenshots/(page_name[:-5]+"-"+str(width)+"-patched-form.png")),full_page=False,timeout=25000)
                                    r["checks"].append({"page":page_name,"width":width,"type":"tutor","label":"PASS"})
                                    print("PATCHED_RUNTIME_TUTOR_FORM_PASS",width,page_name,flush=True)
                                except Exception as e:
                                    r["errors"].append({"page":page_name,"width":width,"error":repr(e)})
                                    print("::error::TUTOR_RUNTIME "+repr(e),flush=True)
                            for other_mode in OTHER:
                                if width not in (390,1440):continue
                                name=slug+"-"+other_mode+".html"
                                try:
                                    response=page.goto(BASE+"/"+name,wait_until="domcontentloaded",timeout=70000)
                                    if not response or response.status!=200:raise ValueError("Missing non-tutor sample page")
                                    form=page.locator("#consultation-preview form")
                                    if form.count()!=1:raise ValueError("Missing non-tutor form")
                                    rt=form.locator('input[name="requestType"]').first
                                    button=form.locator('button[type="submit"]').first
                                    if rt.input_value()!="체험수업 신청" or "체험수업 신청" not in button.inner_text():
                                        raise ValueError("Non-tutor existing mode altered: "+repr((rt.input_value(),button.inner_text())))
                                    page.locator(".hero-actions a[href='#consultation-preview']").first.click()
                                    if rt.input_value()!="체험수업 신청":
                                        raise ValueError("Non-tutor mode changed after CTA")
                                    r["unchanged_other_course_cases"]+=1
                                    r["checks"].append({"page":name,"width":width,"type":"other","label":"PASS"})
                                    print("PATCHED_RUNTIME_OTHER_COURSE_UNCHANGED",width,name,flush=True)
                                except Exception as e:
                                    r["errors"].append({"page":name,"width":width,"error":repr(e)})
                                    print("::error::OTHER_RUNTIME "+repr(e),flush=True)
                    finally:ctx.close()
            finally:browser.close()
    except Exception:
        r["errors"].append({"runner":traceback.format_exc()[-1600:]})
    expected_interceptions=24+8
    r["status"]="PASS_V23521_PATCHED_JS_REAL_BROWSER_BEFORE_DEPLOY" if (
      not r["errors"] and r["tutor_viewports"]==24 and r["tutor_cta_clicks"]==48 and
      r["unchanged_other_course_cases"]==8 and
      r["patched_asset_interceptions"]>=expected_interceptions) else "HOLD_V23521_PATCHED_JS_REAL_BROWSER_BEFORE_DEPLOY"
    opt.report.parent.mkdir(parents=True,exist_ok=True)
    opt.report.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(r["status"],"tutors",r["tutor_viewports"],"ctas",r["tutor_cta_clicks"],
      "other",r["unchanged_other_course_cases"],"intercept",r["patched_asset_interceptions"],
      "errors",r["errors"][:4],flush=True)
    return 0 if r["status"].startswith("PASS") else 1

if __name__=="__main__":sys.exit(main())
