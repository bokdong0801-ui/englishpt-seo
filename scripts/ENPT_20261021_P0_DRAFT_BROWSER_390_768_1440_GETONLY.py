#!/usr/bin/env python3
"""P0 nonpublished Draft real Chromium responsive + form route GET-only QA. NO SUBMISSIONS."""
import datetime,json,os,pathlib
from shutil import which
from playwright.sync_api import sync_playwright
BASE="https://enptp01816review20261021--englishpt-seo.netlify.app"
OUT=pathlib.Path("p0-final-browser-readonly");OUT.mkdir(exist_ok=True)
PAGES=[
"/englishpt.html",
"/station-ganeung.html","/station-ganeung-elem-tutor.html",
"/station-donong.html","/station-donong-elem-tutor.html",
"/station-419minjumyoji.html","/station-419minjumyoji-elem-tutor.html",
"/station-seolleung.html","/station-seolleung-elem-tutor.html",
"/station-geumgok.html","/station-geumgok-elem-tutor.html",
"/station-yangjeong.html","/station-yangjeong-elem-tutor.html",
]
rows=[];issues=[];network_non_get=[]
chromium=which("google-chrome") or which("chromium") or which("chromium-browser")
assert chromium,"Chromium required"
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=chromium,headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
 try:
  for width in (390,768,1440):
   context=browser.new_context(viewport={"width":width,"height":850},device_scale_factor=1)
   def guard(route):
    method=route.request.method
    if method not in ("GET","HEAD"):
     network_non_get.append({"method":method,"url":route.request.url[:170]})
     route.abort()
    else:route.continue_()
   context.route("**/*",guard)
   for route in PAGES:
    page=context.new_page()
    page.set_default_timeout(15000)
    row={"viewport":width,"path":route,"errors":[]}
    try:
     response=page.goto(BASE+route,wait_until="domcontentloaded",timeout=60000)
     if not response or response.status!=200:row["errors"].append("HTML_HTTP_NOT_200")
     page.locator("body").wait_for(state="visible",timeout=15000)
     dimension=page.evaluate("""() => ({
       scroll:document.documentElement.scrollWidth,inner:innerWidth,
       bodyScroll:document.body.scrollWidth,
       title:document.title,
       hasPatch:!!document.querySelector('[data-enpt-p0="20261021"]'),
       formCount:document.querySelectorAll('form[name="englishpt-consultation"]').length,
       canonical:document.querySelector('link[rel="canonical"]')?.href,
       robots:document.querySelector('meta[name="robots"]')?.content
     })""")
     row["dimensions"]=dimension
     if dimension["scroll"]>width+10 or dimension["bodyScroll"]>width+10:row["errors"].append("HORIZONTAL_OVERFLOW")
     if not dimension["canonical"] or not dimension["canonical"].startswith("https://englishpt.kr/"):row["errors"].append("CANONICAL")
     if not dimension["robots"] or "noindex" in dimension["robots"].lower():row["errors"].append("INDEX_ROBOTS")
     if route.startswith("/station-") and "toeic" not in route and not dimension["hasPatch"]:row["errors"].append("P0_CONTENT_MISSING")
     if dimension["formCount"]<1:row["errors"].append("CONSULTATION_FORM_MISSING")
     form=page.locator('form[name="englishpt-consultation"]').first
     if form.count():
      if form.locator('input[name="name"]').count()<1:row["errors"].append("NAME_MISSING")
      if form.locator('input[name="phone"]').count()<1:row["errors"].append("PHONE_MISSING")
      if form.locator('button[type="submit"]').count()<1:row["errors"].append("SUBMIT_MISSING")
      if form.locator('input[name="consent"]').count()<1:row["errors"].append("CONSENT_MISSING")
     # Actual click path: prioritize in-page anchor, then modal open; never press submit.
     btn=page.locator('a[href="#consultation-preview"]').first
     if btn.count():
      btn.click(timeout=14000)
      page.locator('form[name="englishpt-consultation"]').first.wait_for(state="visible",timeout=14000)
      row["cta"]="inpage"
     else:
      btn=page.locator('button[data-open-form]').first
      if btn.count():
       btn.click(timeout=14000)
       page.locator('form[name="englishpt-consultation"]').first.wait_for(state="visible",timeout=14000)
       row["cta"]="modal"
      else:row["errors"].append("CTA_MISSING")
     if row.get("cta"):row["form_visible_after_click"]=form.is_visible()
     if not row.get("form_visible_after_click"):row["errors"].append("FORM_INVISIBLE_AFTER_CTA")
     if route in ("/station-ganeung.html","/station-ganeung-elem-tutor.html","/englishpt.html"):
      ss="P0_"+str(width)+"_"+route.strip("/").replace(".html","")+".png"
      page.screenshot(path=str(OUT/ss),full_page=False)
      row["screenshot"]=ss
    except Exception as exc:
     row["errors"].append(type(exc).__name__+":"+str(exc).splitlines()[0][:170])
     try:
      ss="ERROR_"+str(width)+"_"+route.strip("/").replace(".html","")+".png"
      page.screenshot(path=str(OUT/ss),full_page=False);row["error_screenshot"]=ss
     except Exception:pass
    rows.append(row)
    if row["errors"]:issues.append({"viewport":width,"path":route,"errors":row["errors"]})
    page.close()
   context.close()
 finally:browser.close()
res={"status":"PASS_ALL_P0_DRAFT_BROWSER_CTA_390_768_1440_NO_POST" if not issues and not network_non_get else "HOLD_BROWSER_CTA_ISSUES","timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),"draft_alias":BASE,"viewports":[390,768,1440],"pages_per_viewport":len(PAGES),"total_checks":len(rows),"errors":issues,"non_get_requests":network_non_get,"forms_submitted":0,"production_published":False,"rows":rows}
(OUT/"P0_BROWSER_MOBILE_CTA_REPORT.json").write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding="utf8")
print("P0_BROWSER_MOBILE_CTA_FINAL",json.dumps({k:v for k,v in res.items() if k!="rows"},ensure_ascii=False),flush=True)
if issues or network_non_get:raise SystemExit(1)
