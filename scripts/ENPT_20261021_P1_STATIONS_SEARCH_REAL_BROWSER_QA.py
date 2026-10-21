#!/usr/bin/env python3
"""P1 alias: 911 station search UI mobile/desktop and content/official addresses, GET only."""
import datetime,json,os,pathlib,urllib.request
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path("p1-20261021-browser-qa");ROOT.mkdir(exist_ok=True)
BASE="https://enptp1stationsreview20261021--englishpt-seo.netlify.app"
PRODUCTION_ID="6ad7506cdeb778280a54ee2a"
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
def api(p):
 req=urllib.request.Request("https://api.netlify.com/api/v1/"+p,headers={"Authorization":"Bearer "+os.environ["NETLIFY_AUTH_TOKEN"]},method="GET")
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
prod=api("sites/"+SITE)
assert (prod.get("published_deploy") or {}).get("id")==PRODUCTION_ID
out=[];errors=[];blocked=[]
from shutil import which
chrome=which("google-chrome") or which("chromium") or which("chromium-browser")
assert chrome
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,executable_path=chrome,args=["--no-sandbox","--disable-dev-shm-usage"])
 for width in (390,768,1440):
  cx=browser.new_context(viewport={"width":width,"height":880},locale="ko-KR",device_scale_factor=1)
  cx.route("**/*",lambda route:(route.continue_() if route.request.method in ("GET","HEAD") else (blocked.append(route.request.url[:110]),route.abort())))
  for path in ("/stations.html","/station-donong.html","/station-donong-elem-tutor.html","/station-ganeung.html","/station-ganeung-elem-tutor.html"):
   p=cx.new_page();row={"width":width,"path":path,"errors":[]}
   try:
    resp=p.goto(BASE+path,wait_until="domcontentloaded",timeout=60000)
    if resp is None or resp.status!=200:row["errors"].append("HTTP")
    metrics=p.evaluate("""() => ({vw:innerWidth,sw:document.documentElement.scrollWidth,
      title:document.title,canon:document.querySelector('link[rel=canonical]')?.href,
      form:document.querySelectorAll('form[name="englishpt-consultation"]').length,
      p1:document.querySelectorAll('[data-enpt-learning-evidence="20261021"]').length,
      official:document.querySelectorAll('.enpt-official-station-address').length})""")
    row.update(metrics)
    if metrics["sw"]>width+10:row["errors"].append("HORIZONTAL_OVERFLOW")
    if not metrics["canon"] or not metrics["canon"].startswith("https://englishpt.kr/"):row["errors"].append("CANONICAL")
    if metrics["form"]!=1:row["errors"].append("FORM")
    if "ganeung" not in path and "stations.html" not in path and metrics["p1"]!=1:row["errors"].append("P1_MISSING")
    if "donong" in path and metrics["official"]!=1:row["errors"].append("OFFICIAL_ADDRESS_MISSING")
    if path=="/stations.html":
     field=p.locator("#stationSearch")
     if not field.is_visible():row["errors"].append("SEARCH_HIDDEN")
     style=field.evaluate("""e=>({width:e.getBoundingClientRect().width,border:getComputedStyle(e).borderTopWidth,background:getComputedStyle(e).backgroundColor})""")
     row["search_style"]=style
     if style["width"]<260:row["errors"].append("SEARCH_TOO_NARROW")
     if style["border"] in ("0px","1px"):row["errors"].append("SEARCH_BORDER_WEAK")
     select=p.locator("#enptStationLine")
     options=select.locator("option").count()
     row["line_options"]=options
     if options!=38:row["errors"].append("37_LINES_UNAVAILABLE")
     assert p.locator(".station-index-link").count()>=911
     field.fill("강남역")
     p.wait_for_timeout(250)
     row["matched"]=p.locator(".station-index-link:visible").count()
     if row["matched"]<1 or row["matched"]>10:row["errors"].append("STATION_SEARCH_RESULTS")
     if "검색 결과" not in p.locator("#enptStationResults").inner_text():row["errors"].append("SEARCH_COUNT_NOT_VISIBLE")
     p.locator("#enptStationClear").click()
     p.wait_for_timeout(250)
     if p.locator("#stationSearch").input_value():row["errors"].append("CLEAR_BROKEN")
     if not p.locator(".station-index-link").first.is_visible():row["errors"].append("STATION_LINKS_HIDDEN")
     select.select_option(index=1)
     p.wait_for_timeout(250)
     if p.locator("#enptStationLine").input_value()=="":row["errors"].append("LINE_SELECT_NOT_WORKING")
     if width in (390,1440):
      p.screenshot(path=str(ROOT/("stations_"+str(width)+".png")),full_page=False)
     row["search"]="PASS_FUNCTIONAL_FILTER_CLEAR_LINE_SELECT"
    else:
     cta=p.locator('button[data-open-form]:visible').first
     if cta.count()>0:
      cta.click(timeout=15000)
      p.locator('form[name="englishpt-consultation"]').first.wait_for(state="visible",timeout=15000)
      row["cta"]="OPENED"
     else:
      link=p.locator('a[href="#consultation-preview"]:visible').first
      if link.count():link.click();row["cta"]="ANCHOR"
      else:row["errors"].append("CTA_MISSING")
     if width==390 and path=="/station-donong.html":
      p.screenshot(path=str(ROOT/"official_donong_390.png"),full_page=False)
   except Exception as e:row["errors"].append(type(e).__name__+":"+str(e).splitlines()[0][:140])
   out.append(row)
   if row["errors"]:errors.append({"width":width,"path":path,"errors":row["errors"]})
   p.close()
  cx.close()
 browser.close()
prod2=api("sites/"+SITE)
assert (prod2.get("published_deploy") or {}).get("id")==PRODUCTION_ID
summary={"status":"PASS_P1_STATIONS_SEARCH_15_REAL_BROWSER_GETONLY" if not errors and not blocked else "HOLD_P1_BROWSER_QA","checks":len(out),"viewports":[390,768,1440],"errors":errors,"blocked_non_GET":blocked,"production_id":PRODUCTION_ID,"form_POSTs":0,"timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),"rows":out}
(ROOT/"P1_BROWSER_QA.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),"utf8")
print("P1_BROWSER_FINAL",json.dumps({k:v for k,v in summary.items() if k!="rows"},ensure_ascii=False),flush=True)
if errors or blocked:raise SystemExit(1)
