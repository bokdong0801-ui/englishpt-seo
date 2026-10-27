#!/usr/bin/env python3
"""Real nonpublished Netlify Draft: all 21 HTML pages, 390/768/1440 desktop/mobile.
Never POST a lead, create a deployment or change production.
"""
import collections,datetime,json,os,pathlib,urllib.request
from playwright.sync_api import sync_playwright
OUT=pathlib.Path("region-browser-qa-20261027")
OUT.mkdir(exist_ok=True)
BASE="https://enpt-regions-final-review-20261027--englishpt-seo.netlify.app"
core=["englishpt.html","courses.html","student-english.html"]
regions=["regions.html"]+["regions/"+x+".html" for x in ("gangwon","gyeonggi","gyeongnam","gyeongbuk","gwangju","daegu","daejeon","busan","seoul","sejong","ulsan","incheon","jeonnam","jeonbuk","jeju","chungnam","chungbuk")]
targets=core+regions
def audit():
 report={"started_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"mode":"GET_ONLY","target_html_pages":len(targets),"viewports":[390,768,1440],"results":[],"errors":[],"missing_assets":[],"form_POST_count":0,"production_writes":0,"status":"HOLD"}
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
  for width,height in ((390,844),(768,1024),(1440,900)):
   page=browser.new_page(viewport={"width":width,"height":height},device_scale_factor=1)
   js_errors=[];failed_assets=[]
   page.on("pageerror",lambda exc:js_errors.append(str(exc)[:250]))
   def on_response(response):
    if response.status>=400 and response.url.startswith(BASE):
     failed_assets.append({"page":page.url,"url":response.url,"status":response.status})
   page.on("response",on_response)
   for name in targets:
    try:
     resp=page.goto(BASE+"/"+name,wait_until="domcontentloaded",timeout=48000)
     assert resp is not None and resp.status==200,("HTTP",resp.status if resp else None)
     assert "noindex" in (resp.headers.get("x-robots-tag") or "").lower(),("NOINDEX_HEADER",name)
     canonical=page.locator('link[rel="canonical"]')
     assert canonical.count()==1,("CANONICAL_COUNT",name)
     href=canonical.get_attribute("href")
     assert href.startswith("https://englishpt.kr/"),("CANONICAL_HOST",name,href)
     assert page.locator("#applyModal").count()==1 and page.locator("#leadForm").count()==1,("FORM_MARKUP",name)
     for field in ("#leadName","#leadPhone","#leadArea","#leadConsent"):
      assert page.locator(field).count()==1,("FORM_FIELD",name,field)
     assert page.locator("body").evaluate("(el)=>el.scrollWidth <= innerWidth + 2"),("OVERFLOW",name,width)
     if name in core:
      assert page.locator("#enpt-regions-entry-20261027").count()==1,("REGION_SECTION_MISSING",name)
      link=page.locator("#enpt-regions-entry-20261027 a").first
      assert "regions" in (link.get_attribute("href") or ""),("REGION_HREF",name)
      page.locator("#enpt-regions-entry-20261027 button[data-open-form]").click()
      assert page.locator("#applyModal").get_attribute("aria-hidden")=="false",("MODAL_OPEN",name)
      assert page.locator("#leadName").is_visible(),("MODAL_VISIBLE",name)
      page.locator("[data-close-form]").last.click()
      assert page.locator("#applyModal").get_attribute("aria-hidden")=="true",("MODAL_CLOSE",name)
      if width in (390,1440):
       page.screenshot(path=str(OUT/("LIVE_"+name.replace(".html","")+"_"+str(width)+".png")),full_page=True)
      link.click();page.wait_for_load_state("domcontentloaded")
      assert page.locator(".rg-card").count()==17,("REGION_NAV_FAILED",name)
     elif name=="regions.html":
      assert page.locator(".rg-card").count()==17,("PROVINCE_COUNT",width)
      if width in (390,1440):page.screenshot(path=str(OUT/f"LIVE_NATIONAL_{width}.png"),full_page=True)
     else:
      assert page.locator(".rg-district").count()>0,("DISTRICT_MISSING",name)
      assert page.locator(".rg-town-links a").count()>0,("TOWN_MISSING",name)
      if name=="regions/seoul.html":
       page.locator("#rgSearch").fill("사직동")
       assert page.locator(".rg-town-links a:visible").count()>=1,("SEARCH_NO_RESULT",width)
       page.locator("#rgSearch").fill("없는지역000")
       assert page.locator("#rgEmpty").is_visible(),("SEARCH_EMPTY_STATE",width)
       page.locator("#rgSearch").fill("")
       if width in (390,1440):page.screenshot(path=str(OUT/f"LIVE_SEOUL_{width}.png"),full_page=True)
     report["results"].append({"width":width,"url_path":name,"status":200,"seo":"PASS","forms":"PASS","responsive":"PASS"})
    except Exception as ex:
     report["errors"].append({"width":width,"url_path":name,"reason":str(ex)[:350]})
   report["missing_assets"].extend(failed_assets)
   report["errors"].extend([{"width":width,"type":"JS_ERROR","reason":e} for e in js_errors])
   page.close()
  browser.close()
 with urllib.request.urlopen(BASE+"/robots.txt",timeout=35) as r:
  report["robots_disallow_all"]="Disallow: /" in r.read().decode("utf8","replace")
 report["attempted_expected"]=len(targets)*3
 report["passed_checks"]=len(report["results"])
 report["missing_asset_count"]=len(report["missing_assets"])
 report["status"]="PASS_ALL_21_PAGES_390_768_1440" if not report["errors"] and not report["missing_assets"] and report["robots_disallow_all"] and report["passed_checks"]==report["attempted_expected"] else "HOLD_REVIEW_ISSUES"
 (OUT/"ENPT_LIVE_DRAFT_QA.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
 print("ENPT_LIVE_DRAFT_SUMMARY",json.dumps({k:v for k,v in report.items() if k not in ("results","missing_assets")},ensure_ascii=False),flush=True)
 assert report["status"].startswith("PASS"),"HOLD_QA_RESULTS_NEED_REVIEW"
if __name__=="__main__":audit()
