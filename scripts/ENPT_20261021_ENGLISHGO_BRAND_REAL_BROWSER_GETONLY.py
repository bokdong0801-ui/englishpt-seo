#!/usr/bin/env python3
"""Live GET-only ENGLISHGO nonpublished Draft 390/768/1440 browser, SEO, OG, navigation, forms QA."""
import datetime,json,os,pathlib,urllib.request
from shutil import which
from playwright.sync_api import sync_playwright
BASE="https://enptenglishgobrandreview20261021--englishpt-seo.netlify.app"
SID="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
PRODUCTION="6ad7506cdeb778280a54ee2a"
OUT=pathlib.Path("englishgo-brand-live-qa");OUT.mkdir(exist_ok=True)
def api(path):
 req=urllib.request.Request("https://api.netlify.com/api/v1/"+path,headers={"Authorization":"Bearer "+os.environ["NETLIFY_AUTH_TOKEN"]},method="GET")
 with urllib.request.urlopen(req,timeout=35) as r:return json.load(r)
assert api("sites/"+SID).get("published_deploy",{}).get("id")==PRODUCTION
allpaths=[
"/englishpt.html","/student-english.html","/english-conversation.html",
"/courses.html","/exam-english.html","/stations.html",
"/guides/international-school-english.html","/guides/senior-english.html",
"/guides/elementary-english.html",
"/station-ganeung.html","/station-ganeung-elem-tutor.html",
"/ulsan-buk-nongso2dong-beginner-english-conv.html",
"/ulsan-buk-nongso2dong-elem-conv.html","/ulsan-buk-nongso2dong-mid-tutor.html",
"/ulsan-buk-nongso2dong-high-tutor.html","/ulsan-buk-nongso2dong-toeic.html"]
rows=[];issues=[];nonget=[]
chrome=which("google-chrome") or which("chromium") or which("chromium-browser")
assert chrome
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,executable_path=chrome,args=["--no-sandbox","--disable-dev-shm-usage"])
 for width in (390,768,1440):
  context=browser.new_context(viewport={"width":width,"height":850},device_scale_factor=1,locale="ko-KR")
  def route_guard(route):
   if route.request.method not in ("GET","HEAD"):
    nonget.append({"method":route.request.method,"url":route.request.url[:140]});route.abort()
   else:route.continue_()
  context.route("**/*",route_guard)
  page=context.new_page();page.set_default_timeout(15000)
  for path in allpaths:
   result={"viewport":width,"path":path,"errors":[]}
   try:
    response=page.goto(BASE+path,wait_until="domcontentloaded",timeout=60000)
    if response is None or response.status!=200:result["errors"].append("HTTP_NOT200")
    head=page.evaluate("""() => ({
      title:document.title,canonical:document.querySelector('link[rel=canonical]')?.href,
      robot:document.querySelector('meta[name=robots]')?.content,
      site:document.querySelector('meta[property="og:site_name"]')?.content,
      form:document.querySelectorAll('form[name="englishpt-consultation"]').length,
      body:document.documentElement.outerHTML,
      overflow:document.documentElement.scrollWidth>innerWidth+10
    })""")
    result.update({k:v for k,v in head.items() if k!="body"})
    if head["overflow"]:result["errors"].append("OVERFLOW")
    shared_guide=path=="/guides/elementary-english.html"
    if head["site"]!="잉글리시GO" and not shared_guide:result["errors"].append("OG_SITE_NAME")
    if not head["canonical"] or not head["canonical"].startswith("https://englishpt.kr/"):result["errors"].append("CANONICAL")
    if head["form"]!=(0 if shared_guide else 1):result["errors"].append("FORM")
    if "잉글리시PT" in head["body"] or "ENGLISH PT" in head["body"]:result["errors"].append("OLD_BRAND_REMAINS")
    if not shared_guide and ("잉글리시GO" not in head["body"] or "ENGLISH GO" not in head["body"]):result["errors"].append("NEW_BRAND_MISSING")
    isguide=path.startswith("/guides/")
    if isguide and "noindex" not in (head["robot"] or "").lower():result["errors"].append("GUIDE_INDEXED")
    if not isguide and (head["robot"] is None or "noindex" in head["robot"]):result["errors"].append("UNEXPECTED_NOINDEX")
    if path=="/englishpt.html":
     body=head["body"]
     if '"name":"ENGLISH GO"' not in body or '"alternateName":["잉글리시GO","English GO"]' not in body:result["errors"].append("STRUCTURED_DATA_SITE_BRAND")
     if page.locator('a[href="/guides/senior-english.html"]').count()<1:result["errors"].append("SENIOR_NAVIGATION")
    if path=="/student-english.html":
     opts=[v for v in page.locator("[data-region-intent] option").all() if v.get_attribute("value")]
     if len(opts)!=6:result["errors"].append("SIX_STUDENT_COURSE_OPTIONS")
     if page.locator('a[href="/guides/international-school-english.html"]').count()<1:result["errors"].append("INTERNATIONAL_NAVIGATION")
    if path=="/english-conversation.html" and page.locator('article#senior a[href="/guides/senior-english.html"]').count()<1:result["errors"].append("SENIOR_COURSE_LINK")
    if "beginner-english-conv" in path:
     align=page.locator(".mass-context .context-block p").first.evaluate("x=>getComputedStyle(x).textAlign")
     if align!="center":result["errors"].append("COMPARISON_LEFT_ALIGNED")
    if isguide and not shared_guide:
     button=page.locator('button[data-open-form]:visible').first
     if not button.count():result["errors"].append("GUIDE_CTA_NOT_VISIBLE")
     else:
      button.click(timeout=12000)
      if not page.locator('form[name="englishpt-consultation"]').first.is_visible():result["errors"].append("GUIDE_FORM_NOT_VISIBLE_AFTER_CLICK")
    if width in (390,1440) and path in ("/englishpt.html","/student-english.html","/guides/international-school-english.html","/guides/senior-english.html"):
     screenshot=path.split("/")[-1].replace(".html","")+"-"+str(width)+".png"
     page.screenshot(path=str(OUT/screenshot),full_page=False)
     result["screenshot"]=screenshot
   except Exception as exc:result["errors"].append(type(exc).__name__+":"+str(exc).splitlines()[0][:175])
   if result["errors"]:issues.append({"width":width,"page":path,"errors":result["errors"]})
   rows.append(result)
  context.close()
 browser.close()
fav_req=urllib.request.Request(BASE+"/assets/favicon.svg",method="GET")
with urllib.request.urlopen(fav_req,timeout=20) as resp:
 icon=resp.read().decode("utf8")
 assert resp.status==200 and ">GO</text>" in icon and ">PT</text>" not in icon,("FAVICON",icon[:140])
prod_now=api("sites/"+SID).get("published_deploy",{}).get("id")
assert prod_now==PRODUCTION
report={"status":"PASS_ENGLISHGO_BRAND_16_PAGES_3_VIEWPORTS_FORM_AND_SEO" if not issues and not nonget else "HOLD_ENGLISHGO_BROWSER_OR_SEO",
 "draft_url":BASE,"tested_pages":len(allpaths),"viewports":[390,768,1440],"total_checks":len(rows),
 "errors":issues,"nonget_requests":nonget,"favicon_go_text":True,"production_unchanged":prod_now,
 "brand_legally_cleared":False,"forms_submitted":0,"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"records":rows}
(OUT/"ENGLISHGO_FINAL_BROWSER_QA.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),"utf8")
print("ENPT_ENGLISHGO_LIVE_BROWSER_QA",json.dumps({k:v for k,v in report.items() if k!="records"},ensure_ascii=False),flush=True)
if issues or nonget:raise SystemExit(1)
