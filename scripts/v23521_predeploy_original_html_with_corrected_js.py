#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Predeploy LOCAL realistic JS run: never start 158571-page Netlify upload until PASS.

Serves the exact proposed Netlify deploy folder; no network mutations, never POSTs.
Verifies that corrected pilot.js is actually loaded by all local HTML pages.
"""
import json,shutil,threading,sys
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright

ROOT=Path("review-site").resolve()
OUT=Path("jsfix-local-preflight")
OUT.mkdir(exist_ok=True)
SLUGS=("gyeongnam-milyang-naeidong","seoul-jongno-sajikdong")
TUTORS=("elem-tutor","mid-tutor","high-tutor")
OTHERS=("elem-conv","worker-english-conv-academy")
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT),**kwargs)
    def log_message(self,*args):pass

server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f"http://127.0.0.1:{server.server_port}/"
stats={"status":"RUNNING","tutor_checked":0,"tutor_ctas":0,"non_tutor_checked":0,
       "pilot_js_loaded":0,"errors":[],"production_deployed":False,"draft_deployed":False,"form_submitted":False}
try:
 with sync_playwright() as pw:
  exe=shutil.which("google-chrome") or shutil.which("chromium")
  kw={"headless":True,"args":["--no-sandbox","--disable-dev-shm-usage"]}
  if exe:kw["executable_path"]=exe
  browser=pw.chromium.launch(**kw)
  try:
   for width in (390,1440):
    ctx=browser.new_context(viewport={"width":width,"height":900})
    ctx.route("**/*",lambda route:route.continue_() if route.request.method in ("GET","HEAD") else route.abort())
    page=ctx.new_page()
    page.add_init_script("""document.addEventListener('submit',e=>{
      e.preventDefault();e.stopImmediatePropagation();},true)""")
    page.on("response",lambda response: stats.__setitem__("pilot_js_loaded",stats["pilot_js_loaded"]+1)
        if "/pilot.js" in response.url and response.status==200 else None)
    try:
     for slug in SLUGS:
      for mode in TUTORS+OTHERS:
       name=slug+"-"+mode+".html"
       try:
        r=page.goto(base+name,wait_until="domcontentloaded",timeout=60000)
        if not r or r.status!=200:raise ValueError("not HTTP 200")
        form=page.locator("#consultation-preview form")
        btn=form.locator('button[type="submit"]').first
        rt=form.locator('input[name="requestType"]').first
        sj=form.locator('input[name="subject"]').first
        tutor=mode in TUTORS
        target="영어과외 상담 신청" if tutor else "체험수업 신청"
        def verify(stage):
         if rt.input_value()!=target:
          raise ValueError(stage+" wrong requestType "+repr(rt.input_value()))
         if "ENGLISH PT "+target!=sj.input_value():
          raise ValueError(stage+" wrong subject "+repr(sj.input_value()))
         if target not in btn.inner_text():
          raise ValueError(stage+" wrong visible submit button "+repr(btn.inner_text()))
        verify("load")
        link=page.locator('.hero-actions a[href="#consultation-preview"]').first
        if link.count()!=1:raise ValueError("hero CTA missing")
        link.click(timeout=13000)
        verify("after hero CTA")
        if tutor:
         parent=page.locator('a.v2352-small-cta[href="#consultation-preview"]')
         if parent.count()!=1:raise ValueError("parent tutoring CTA missing")
         parent.click(timeout=13000)
         verify("after parent CTA")
         stats["tutor_checked"]+=1;stats["tutor_ctas"]+=2
        else:stats["non_tutor_checked"]+=1
        if page.evaluate("document.documentElement.scrollWidth")>width+4:
         raise ValueError("page horizontal overflow")
        print("LOCAL_FIXED_SHARED_JS_REAL_PAGE_PASS",width,name,target,flush=True)
       except Exception as e:
        stats["errors"].append({"page":name,"width":width,"error":repr(e)})
        print("::error::LOCAL_FIXED_JS "+name+" "+repr(e),flush=True)
    finally:ctx.close()
  finally:browser.close()
finally:server.shutdown()
stats["status"]="PASS_V23521_FIXED_JS_REAL_STATIC_SITE_LOCAL_BEFORE_UPLOAD" if (
 not stats["errors"] and stats["tutor_checked"]==12 and stats["tutor_ctas"]==24
 and stats["non_tutor_checked"]==8 and stats["pilot_js_loaded"]>=20) else (
 "HOLD_V23521_FIXED_JS_REAL_STATIC_SITE_LOCAL_BEFORE_UPLOAD")
(OUT/"LOCAL_ACTUAL_JS_LOAD_FORM_QA.json").write_text(json.dumps(stats,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(stats["status"],stats,flush=True)
sys.exit(0 if stats["status"].startswith("PASS") else 1)
