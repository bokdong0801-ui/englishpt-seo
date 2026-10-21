#!/usr/bin/env python3
"""Chromium GET-only QA for P3 shared guide and navigation station pages."""
import datetime,json,os,pathlib,urllib.request
from playwright.sync_api import sync_playwright
BASE="https://enptp3guide20261021--englishpt-seo.netlify.app"
OUT=pathlib.Path("p3-910-browser-qa");OUT.mkdir(exist_ok=True)
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
OLDPROD="6ad7506cdeb778280a54ee2a"
def api(path):
 req=urllib.request.Request("https://api.netlify.com/api/v1/"+path,headers={"Authorization":"Bearer "+os.environ["NETLIFY_AUTH_TOKEN"]},method="GET")
 with urllib.request.urlopen(req,timeout=35) as r:return json.load(r)
assert (api("sites/"+SITE).get("published_deploy") or {}).get("id")==OLDPROD
checks=[];errors=[];blocked=[]
from shutil import which
bin=which("google-chrome") or which("chromium") or which("chromium-browser")
assert bin
paths=["/guides/elementary-english.html","/station-ganeung-elem-tutor.html","/station-donong-elem-tutor.html","/station-geumgok-elem-tutor.html","/station-ganeung.html","/stations.html"]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=bin,headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
 for width in (390,768,1440):
  ctx=browser.new_context(viewport={"width":width,"height":880},locale="ko-KR")
  def guard(route):
   if route.request.method in ("GET","HEAD"):route.continue_()
   else:blocked.append(route.request.url[:90]);route.abort()
  ctx.route("**/*",guard)
  for path in paths:
   page=ctx.new_page();row={"path":path,"viewport":width,"issues":[]}
   try:
    resp=page.goto(BASE+path,wait_until="domcontentloaded",timeout=60000)
    if resp is None or resp.status!=200:row["issues"].append("HTTP")
    p=page.evaluate("""() => ({scroll:document.documentElement.scrollWidth,inner:innerWidth,
    robots:document.querySelector('meta[name="robots"]')?.content,
    formCount:document.querySelectorAll('form[name="englishpt-consultation"]').length,
    p3Count:document.querySelectorAll('[data-enpt-elemdir="20261021"]').length,
    guideLinks:document.querySelectorAll('a[href="/guides/elementary-english.html"]').length,
    canonical:document.querySelector('link[rel="canonical"]')?.href})""")
    row.update(p)
    if p["scroll"]>width+12:row["issues"].append("OVERFLOW")
    if not p["canonical"] or not p["canonical"].startswith("https://englishpt.kr/"):row["issues"].append("CANONICAL")
    if path.endswith("/guides/elementary-english.html"):
     if "noindex" not in (p["robots"] or ""):row["issues"].append("GUIDE_MUST_NOINDEX_PREVIEW")
     for id in ("reading","grammar","routine","consult"):
      if page.locator("#"+id).count()!=1:row["issues"].append("GUIDE_HEADING_"+id)
    elif path.endswith("-elem-tutor.html"):
     if p["p3Count"]!=1 or p["guideLinks"]<1:row["issues"].append("P3_NAV_MISSING")
     if p["formCount"]!=1:row["issues"].append("FORM_MISSING")
     if "noindex" in (p["robots"] or ""):row["issues"].append("STATION_INDEX_CHANGED")
     # Click cross page link without making consultation POST.
     page.locator('a[href="/guides/elementary-english.html"]').first.click()
     page.wait_for_url("**/guides/elementary-english.html",timeout=15000)
     if "초등 영어" not in page.locator("body").inner_text():row["issues"].append("SHARED_GUIDE_NAV")
     row["guide_link_click"]="PASS"
    elif path=="/stations.html":
     field=page.locator("#stationSearch")
     field.fill("강남역");page.wait_for_timeout(200)
     count=page.locator(".station-index-link:visible").count()
     row["search_match_count"]=count
     if count<1:row["issues"].append("STATION_SEARCH_FAIL")
     page.locator("#enptStationClear").click()
     if field.input_value():row["issues"].append("SEARCH_CLEAR_FAIL")
    elif path=="/station-ganeung.html":
     if p["formCount"]!=1:row["issues"].append("HUB_FORM")
    if width in (390,1440) and path in ("/station-ganeung-elem-tutor.html","/guides/elementary-english.html"):
     if path.endswith("-elem-tutor.html"):page.goto(BASE+path,wait_until="domcontentloaded")
     f=str(OUT/("P3_"+str(width)+"_"+path.rsplit("/",1)[-1].replace(".html","")+".png"))
     page.screenshot(path=f,full_page=False);row["screenshot"]=f
   except Exception as ex:row["issues"].append(type(ex).__name__+":"+str(ex).splitlines()[0][:170])
   if row["issues"]:errors.append({"path":path,"viewport":width,"errors":row["issues"]})
   checks.append(row);page.close()
  ctx.close()
 browser.close()
assert (api("sites/"+SITE).get("published_deploy") or {}).get("id")==OLDPROD
summary={"status":"PASS_P3_18_BROWSER_CHECKS" if not errors and not blocked else "HOLD_P3_BROWSER","tests":len(checks),"errors":errors,"blocked_nonGET":blocked,"forms_sent":0,"production_id":OLDPROD,"detail":checks,"utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
(OUT/"P3_BROWSER_QA.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf8")
print("P3_BROWSER_FINAL",json.dumps({k:v for k,v in summary.items() if k!="detail"},ensure_ascii=False),flush=True)
if errors or blocked:raise SystemExit(1)
