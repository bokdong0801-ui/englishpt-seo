#!/usr/bin/env python3
"""P2 Draft read-only Chromium QA: provisional ENGLODAM branding, real learning tasks and UX."""
import datetime,json,os,pathlib,urllib.request
from shutil import which
from playwright.sync_api import sync_playwright
BASE="https://enptp2englodamreview20261021--englishpt-seo.netlify.app"
ID="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
PROD="6ad7506cdeb778280a54ee2a"
OUT=pathlib.Path("p2-draft-real-browser-qa");OUT.mkdir(exist_ok=True)
paths=["/index.html","/englishpt.html","/stations.html","/station-ganeung-elem-tutor.html","/station-donong-elem-tutor.html","/station-geumgok-elem-tutor.html","/station-419minjumyoji-elem-tutor.html","/station-donong.html","/gyeongnam-milyang-naeidong-elem-tutor.html"]
def api(p):
 req=urllib.request.Request("https://api.netlify.com/api/v1/"+p,headers={"Authorization":"Bearer "+os.environ["NETLIFY_AUTH_TOKEN"]},method="GET")
 with urllib.request.urlopen(req,timeout=30) as f:return json.load(f)
assert (api("sites/"+ID).get("published_deploy") or {}).get("id")==PROD
chrome=which("google-chrome") or which("chromium") or which("chromium-browser")
assert chrome
rows=[];issues=[];blocked=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=chrome,headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
 for width in (390,768,1440):
  cx=browser.new_context(viewport={"width":width,"height":900},locale="ko-KR")
  def safe(route):
   if route.request.method not in ("GET","HEAD"):blocked.append(route.request.url[:140]);route.abort()
   else:route.continue_()
  cx.route("**/*",safe)
  for path in paths:
   p=cx.new_page();row={"width":width,"path":path,"problems":[]}
   try:
    response=p.goto(BASE+path,wait_until="domcontentloaded",timeout=60000)
    assert response and response.status==200
    p.locator("body").wait_for(state="visible")
    x=p.evaluate("""()=>({h:document.documentElement.scrollWidth,w:innerWidth,title:document.title,
      canonical:document.querySelector('link[rel=canonical]')?.href,
      robots:document.querySelector('meta[name=robots]')?.content,
      og:document.querySelector('meta[property="og:site_name"]')?.content,
      brand:document.body.innerText.includes('잉글로담'),
      p2:document.querySelectorAll('[data-enpt-elem-v2="20261021"]').length,
      forms:document.querySelectorAll('form[name="englishpt-consultation"]').length,
      old:document.body.innerText.includes('잉글리시PT'),
      grade:document.querySelectorAll('.enpt-elem-learning-block').length})""")
    row.update(x)
    if x["h"]>width+12:row["problems"].append("horizontal_overflow")
    if not x["brand"] or x["old"]:row["problems"].append("brand_inconsistent")
    if not x["canonical"] or not x["canonical"].startswith("https://englishpt.kr/"):row["problems"].append("canonical")
    is_noindex="gyeongnam-milyang" in path
    if is_noindex:
     if "noindex" not in (x["robots"] or ""):row["problems"].append("noindex_missing")
    elif "noindex" in (x["robots"] or ""):row["problems"].append("unwanted_noindex")
    is_elem=path.startswith("/station-") and path.endswith("-elem-tutor.html")
    if is_elem:
     if x["p2"]!=1 or x["grade"]!=4:row["problems"].append("P2_curriculum_missing")
     if p.locator(".mass-context").count():row["problems"].append("generic_mass_context_still_present")
    if path in ("/index.html","/englishpt.html") and x["og"]!="잉글로담":row["problems"].append("site_name_og")
    if x["forms"]!=1:row["problems"].append("form_missing")
    if path=="/stations.html":
     search=p.locator("#stationSearch");assert search.is_visible()
     search.fill("강남역");p.wait_for_timeout(250)
     row["matches"]=p.locator(".station-index-link:visible").count()
     if not (1<=row["matches"]<=10):row["problems"].append("search_broken")
     if p.locator("#enptStationLine option").count()!=38:row["problems"].append("line_menu")
     p.locator("#enptStationClear").click()
     if search.input_value():row["problems"].append("search_clear")
    elif x["forms"]:
     cta=p.locator('button[data-open-form]:visible').first
     if cta.count():
      cta.click(timeout=15000)
      p.locator('form[name="englishpt-consultation"]').first.wait_for(state="visible",timeout=15000)
     else:
      link=p.locator('a[href="#consultation-preview"]:visible').first
      if link.count():link.click(timeout=15000)
      else:row["problems"].append("cta_not_found")
    if width in (390,1440) and path in ("/englishpt.html","/stations.html","/station-ganeung-elem-tutor.html"):
     ss=path.strip("/").replace(".html","")+"_"+str(width)+".png"
     p.screenshot(path=str(OUT/ss),full_page=False)
   except Exception as exc:row["problems"].append(type(exc).__name__+":"+str(exc).splitlines()[0][:180])
   if row["problems"]:issues.append(row)
   rows.append(row);p.close()
  cx.close()
 browser.close()
assert (api("sites/"+ID).get("published_deploy") or {}).get("id")==PROD
rep={"status":"PASS_P2_BRAND_910_CTA_STATIONS_RESPONSIVE_SAMPLED" if not issues and not blocked else "HOLD_P2_BROWSER","draft":BASE,"pages_per_viewport":len(paths),"viewports":[390,768,1440],"cases":len(rows),"issues":issues,"non_get_blocked":blocked,"production_id_unchanged":PROD,"forms_submitted":0,"results":rows,"checked_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
(OUT/"P2_BROWSER_QA.json").write_text(json.dumps(rep,ensure_ascii=False,indent=2),"utf8")
print("P2_BROWSER_FINAL",json.dumps({k:v for k,v in rep.items() if k!="results"},ensure_ascii=False),flush=True)
if issues or blocked:raise SystemExit(1)
