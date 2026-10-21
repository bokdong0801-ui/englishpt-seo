#!/usr/bin/env python3
"""Live Playwright GET-only navigation and comparison style test on unique nonpublished Draft."""
import datetime,json,os,pathlib,urllib.request
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path("four-nav-v2-browser-qa");ROOT.mkdir(exist_ok=True)
BASE="https://enptfourpathsfix2review20261021--englishpt-seo.netlify.app"
EXPECTED_PRODUCTION="6ad7506cdeb778280a54ee2a"
SID="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
def api(p):
 req=urllib.request.Request("https://api.netlify.com/api/v1/"+p,headers={"Authorization":"Bearer "+os.environ["NETLIFY_AUTH_TOKEN"]},method="GET")
 with urllib.request.urlopen(req,timeout=35) as f:return json.load(f)
site=api("sites/"+SID);assert site.get("published_deploy",{}).get("id")==EXPECTED_PRODUCTION
rows=[];issues=[];blocked=[]
def record(width,page,case,fn):
 rec={"width":width,"page":page.url.replace(BASE,""),"test":case,"errors":[]}
 try:fn(rec)
 except Exception as exc:rec["errors"].append(type(exc).__name__+":"+str(exc).splitlines()[0][:200])
 rows.append(rec)
 if rec["errors"]:issues.append(rec)
def valid_html(p,rec):
 assert p.title()
 assert p.evaluate("document.documentElement.scrollWidth<=innerWidth+10"),"OVERFLOW"
 assert p.locator('link[rel="canonical"]').count()==1,"CANONICAL"
 assert p.locator('form[name="englishpt-consultation"]').count()==1,"FORM"
def test_student(p,rec):
 valid_html(p,rec)
 opts=p.locator('[data-region-intent] option')
 got=[x.get_attribute("value") for x in opts.all() if x.get_attribute("value")]
 need=["elem-tutor","elem-conv","mid-tutor","mid-conv","high-tutor","high-conv"]
 assert got==need,(got,need)
 intl=p.locator('article#international a.route-cta[href="/guides/international-school-english.html"]')
 assert intl.count()==1,"INTERNATIONAL_LINK"
 mid=p.locator('article#middle-tutor a[data-region-preset="mid-tutor"]')
 hi=p.locator('article#high-tutor a[data-region-preset="high-tutor"]')
 assert mid.count()==hi.count()==1
 rec["six_intents"]=got
def test_home(p,rec):
 valid_html(p,rec)
 assert p.locator('a[href="/guides/senior-english.html"]').count()>=1,"SENIOR_LINK_MISSING"
def test_conv(p,rec):
 valid_html(p,rec)
 assert p.locator('article#senior a[href="/guides/senior-english.html"]').count()==1
def test_guide(p,rec,slug):
 valid_html(p,rec)
 assert p.locator('meta[name="robots"]').get_attribute("content")=="noindex,follow"
 assert p.locator('button[data-open-form]:visible').count()>=1
 btn=p.locator('button[data-open-form]:visible').first
 btn.click(timeout=15000)
 assert p.locator('form[name="englishpt-consultation"]').first.is_visible()
 rec["modal_opened"]=True
def test_center(p,rec):
 valid_html(p,rec)
 section=p.locator('.mass-context').first
 assert section.count()==1,"MASS_CONTEXT_NOT_FOUND"
 ps=p.locator('.mass-context .context-block p')
 assert ps.count()>=1,"CONTEXT_CARD_MISSING"
 styles=ps.first.evaluate("""e=>({align:getComputedStyle(e).textAlign,font:getComputedStyle(e).fontSize})""")
 rec["computed"]=styles
 assert styles["align"]=="center","COMPARISON_TEXT_LEFT"
 head=p.locator('.mass-context h2').first
 assert head.evaluate("e=>getComputedStyle(e).textAlign")=="center","COMPARE_HEADING_LEFT"
def station_six(p,rec):
 valid_html(p,rec)
 idx=p.locator('[data-region-finder] [data-region-sido]')
 p.wait_for_function("document.querySelector('[data-region-sido]').options.length>1",timeout=30000)
 data=p.evaluate("""async()=>{const x=await fetch('/assets/locality-index.json');return(await x.json()).find(r=>r.slug==='ulsan-buk-nongso2dong')}""")
 assert data, "EXPECTED_USER_LOCALITY_MISSING"
 for name in ("elem-tutor","elem-conv","mid-tutor","mid-conv","high-tutor","high-conv"):
  p.locator('[data-region-sido]').select_option(data["sido"])
  p.locator('[data-region-jurisdiction]').select_option(data["jurisdiction"])
  p.locator('[data-region-dong]').select_option(data["slug"])
  p.locator('[data-region-intent]').select_option(name)
  with p.expect_navigation(wait_until="domcontentloaded",timeout=45000):
   p.locator('[data-region-go]').click()
  expected="/ulsan-buk-nongso2dong-"+name+".html"
  assert p.url.endswith(expected),(p.url,expected)
  assert p.locator('h1').count()>=1 and p.locator('form[name="englishpt-consultation"]').count()==1
  rec.setdefault("route_results",[]).append({"intent":name,"url":expected,"status":"PASS"})
  if name!="high-conv":p.goto(BASE+"/student-english.html#region",wait_until="domcontentloaded")
 assert len(rec["route_results"])==6
with sync_playwright() as pw:
 from shutil import which
 chrome=which("google-chrome") or which("chromium") or which("chromium-browser")
 assert chrome,"CHROME_NOT_INSTALLED"
 browser=pw.chromium.launch(executable_path=chrome,headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
 for width in [390,768,1440]:
  context=browser.new_context(viewport={"width":width,"height":850},locale="ko-KR",device_scale_factor=1)
  def only_read(r):
   if r.request.method not in ("GET","HEAD"):
    blocked.append({"method":r.request.method,"url":r.request.url[:200]});r.abort()
   else:r.continue_()
  context.route("**/*",only_read)
  page=context.new_page();page.set_default_timeout(20000)
  for path,fn in [
   ("/student-english.html#region",test_student),
   ("/englishpt.html#audience-path",test_home),
   ("/english-conversation.html#senior",test_conv),
   ("/guides/international-school-english.html",lambda p,r:test_guide(p,r,"intl")),
   ("/guides/senior-english.html",lambda p,r:test_guide(p,r,"senior")),
   ("/ulsan-buk-nongso2dong-beginner-english-conv.html",test_center),
   ("/ulsan-buk-nongso2dong-toeic.html",test_center),
   ("/ulsan-buk-nongso2dong-adult-english-conv-academy.html",test_center),
  ]:
   resp=page.goto(BASE+path,wait_until="domcontentloaded",timeout=70000)
   assert resp and resp.status==200,(path,resp.status if resp else None)
   record(width,page,path,lambda rec,cb=fn:cb(page,rec))
   if width in (390,1440) and path in ("/student-english.html#region","/ulsan-buk-nongso2dong-beginner-english-conv.html","/guides/international-school-english.html","/guides/senior-english.html"):
    page.screenshot(path=str(ROOT/(path.split("/")[-1].split(".html")[0]+"_"+str(width)+".png")),full_page=False)
  if width==390:
   page.goto(BASE+"/student-english.html#region",wait_until="domcontentloaded")
   record(width,page,"six_actual_local_navigation",lambda rec:station_six(page,rec))
  page.close();context.close()
 browser.close()
assert api("sites/"+SID)["published_deploy"]["id"]==EXPECTED_PRODUCTION
rep={"status":"PASS_FULL_FOUR_LINKS_AND_CSS_BROWSER" if not issues and not blocked else "HOLD_BROWSER_ERRORS","tested":len(rows),"viewports":[390,768,1440],"route_types":8,"six_actual_local_routes":6,"errors":issues,"non_GET_requests":blocked,"forms_submitted":0,"production_id_unchanged":EXPECTED_PRODUCTION,"timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),"checks":rows}
(ROOT/"BROWSER_SUMMARY.json").write_text(json.dumps(rep,ensure_ascii=False,indent=2),"utf8")
print("ENPT_FOUR_LIVE_BROWSER_RESULT",json.dumps({k:v for k,v in rep.items() if k!="checks"},ensure_ascii=False),flush=True)
if issues or blocked:raise SystemExit(1)
