#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Before Netlify upload, locally render 6 tutor pages at 4 breakpoints.
Read-only localhost server; no form submissions, external network or deployment.
"""
import json,sys,shutil,threading
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
root=Path("review-site").resolve()
out=Path("v2352-live-report");out.mkdir(exist_ok=True)
names=[f"{slug}-{course}.html" for slug in
       ("gyeongnam-milyang-naeidong","seoul-jongno-sajikdong")
       for course in ("elem-tutor","mid-tutor","high-tutor")]
widths=(320,390,430,1440)
class Quiet(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(root),**kwargs)
    def log_message(self,*args):pass
site=ThreadingHTTPServer(("127.0.0.1",0),Quiet)
threading.Thread(target=site.serve_forever,daemon=True).start()
result={"status":"RUNNING","viewports":widths,"pages":names,
        "checks":[],"errors":[],"production_deployed":False,"form_submitted":False}
try:
    with sync_playwright() as pw:
        binary=shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
        args={"headless":True,"args":["--no-sandbox","--disable-dev-shm-usage"]}
        if binary:args["executable_path"]=binary
        browser=pw.chromium.launch(**args)
        try:
            for width in widths:
                ctx=browser.new_context(viewport={"width":width,"height":900},is_mobile=width<600,has_touch=width<600)
                try:
                    page=ctx.new_page()
                    for name in names:
                        try:
                            rr=page.goto(f"http://127.0.0.1:{site.server_port}/{name}",wait_until="domcontentloaded",timeout=45000)
                            assert rr and rr.status==200
                            page.evaluate("() => document.fonts.ready")
                            page.wait_for_timeout(130)
                            metrics=page.evaluate("""()=>{
                                const h=document.querySelector('h1'),r=h?.getBoundingClientRect();
                                return {docWidth:document.documentElement.scrollWidth,
                                        headline:r?{left:r.left,right:r.right,height:r.height}:null};
                            }""")
                            if metrics["docWidth"]>width+3:raise ValueError("global overflow "+str(metrics["docWidth"]))
                            if not metrics["headline"] or metrics["headline"]["height"]<=0:
                                raise ValueError("H1 invisible")
                            if metrics["headline"]["left"]<-3 or metrics["headline"]["right"]>width+3:
                                raise ValueError("H1 out of viewport")
                            for kind in ("levels","lesson","errors","timeline","parent"):
                                section=page.locator('[data-v2352-section="'+kind+'"]')
                                if section.count()!=1:raise ValueError("missing "+kind)
                                section.scroll_into_view_if_needed(timeout=9000)
                                clipped=section.evaluate("""e=>{
                                  const el=e.querySelector('h2'),r=el?.getBoundingClientRect();
                                  if(!r||r.width<=0||r.height<=0||r.left<-4||r.right>innerWidth+4)return true;
                                  return Array.from(e.querySelectorAll('.v2352-card,.v2352-step')).some(x=>{
                                    const b=x.getBoundingClientRect();
                                    return b.left<-4||b.right>innerWidth+4||x.scrollWidth>x.clientWidth+3;
                                  });}""")
                                if clipped:raise ValueError(kind+" content clipped")
                            for selector in ('.hero-actions a[href="#consultation-preview"]',
                                             'a.v2352-small-cta[href="#consultation-preview"]'):
                                cta=page.locator(selector)
                                if cta.count()<1:raise ValueError("CTA missing "+selector)
                                cta.first.scroll_into_view_if_needed(timeout=6000)
                                cta.first.click(timeout=10000)
                                if page.locator('#consultation-preview form').count()!=1:
                                    raise ValueError("form not reachable after CTA")
                            result["checks"].append({"page":name,"width":width,"status":"PASS"})
                            print("PREDEPLOY_LOCAL_TUTOR_UI_PASS",width,name,flush=True)
                        except Exception as ex:
                            result["errors"].append({"page":name,"width":width,"error":str(ex)[:350]})
                            print("::error::PREDEPLOY_UI "+name+" "+str(ex),flush=True)
                    page.close()
                finally:ctx.close()
        finally:browser.close()
finally:site.shutdown()
result["status"]="PASS_V2352_LOCAL_6_PAGES_4_VIEWPORTS" if len(result["checks"])==24 and not result["errors"] else "HOLD_V2352_LOCAL_6_PAGES_4_VIEWPORTS"
(out/"V2352_PREDEPLOY_LOCAL_4_WIDTH_QA.json").write_text(
    json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(result["status"],len(result["checks"]),len(result["errors"]),flush=True)
sys.exit(0 if result["status"].startswith("PASS") else 1)
