#!/usr/bin/env python3
"""Real Netlify V2 Draft GET/browser checks with independent Production route click.
No form POST, deploy or production modification.
"""
import json,pathlib,urllib.request,os
from playwright.sync_api import sync_playwright
BASE=os.environ.get("ENPT_V2_PREVIEW_BASE","https://enpt-regions-v2-review-20261027--englishpt-seo.netlify.app")
OUT=pathlib.Path("v2-live-browser-qa");OUT.mkdir(exist_ok=True)
report={"preview":BASE+"/regions.html","status":"HOLD","desktop_mobile":[],"form_submissions":0,"production_changes":0}
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
 for width,height in [(390,844),(1440,900)]:
  page=browser.new_page(viewport={"width":width,"height":height})
  failures=[]
  page.on("pageerror",lambda e:failures.append(str(e)[:160]))
  for path in ["englishpt.html","courses.html","student-english.html","regions.html","regions/seoul.html","regions/gyeonggi.html"]:
   r=page.goto(BASE+"/"+path,wait_until="domcontentloaded",timeout=48000)
   assert r and r.status==200,(path,r.status if r else "null")
   assert "noindex" in (r.headers.get("x-robots-tag") or "").lower(),("PREVIEW_INDEXABLE",path)
   assert page.locator("body").evaluate("(e)=>e.scrollWidth<=innerWidth+2"),("OVERFLOW",path,width)
   assert page.locator("#leadForm").count()==1
   if path in ["englishpt.html","courses.html","student-english.html"]:
    page.locator("#enpt-regions-entry-20261027 a").first.click()
    page.wait_for_load_state("domcontentloaded")
    assert page.locator(".rg-card").count()==17
   if path=="regions/seoul.html":
    page.locator("#rgSearch").fill("사직동")
    a=page.locator('.rg-town[data-locality="seoul-jongno-sajikdong"]')
    assert a.count()==1 and a.is_visible(),("MISSING_SAJIKDONG",width)
    if not a.evaluate('(e)=>e.open'):a.locator("summary").click()
    assert a.locator("a").count()==7,("WRONG_COURSE_COUNT",width)
    assert a.locator('a[href$="-elem-tutor.html"]').is_visible(),("COURSE_LINK_NOT_VISIBLE",width)
    assert '−' in a.locator('summary').evaluate('(e)=>getComputedStyle(e,"::after").content'),("OPEN_ICON",width)
    a.locator("summary").click()
    assert not a.locator('a[href$="-elem-tutor.html"]').is_visible(),("COLLAPSE_FAILED",width)
    assert '+' in a.locator('summary').evaluate('(e)=>getComputedStyle(e,"::after").content'),("CLOSED_ICON",width)
    a.locator("summary").click()
    assert a.locator('a[href$="-elem-tutor.html"]').is_visible(),("REOPEN_FAILED",width)
    assert a.locator('a[href$="-elem-tutor.html"]').count()==1
    page.screenshot(path=str(OUT/f"V2_LIVE_SEOUL_SELECT_{width}.png"),full_page=False)
    link=a.locator('a[href$="-elem-tutor.html"]').get_attribute("href")
    req=urllib.request.Request(link,method="GET",headers={"User-Agent":"ENPT-GETONLY-LIVE-REVIEW"})
    with urllib.request.urlopen(req,timeout=35) as resp:assert resp.status==200,(link,resp.status)
   if path=="regions.html":
    assert page.locator(".rg-card").count()==17
    page.screenshot(path=str(OUT/f"V2_LIVE_NATION_{width}.png"),full_page=True)
  assert not failures,("JS_ERRORS",failures)
  report["desktop_mobile"].append({"width":width,"6_live_pages_HTTP":"PASS","SEO_block":"PASS","course_choice_7":"PASS","working_course_destination_200":"PASS","form_markup":"PASS","JS_errors":0})
  page.close()
 browser.close()
report["status"]="PASS_V2_LIVE_BROWSER_390_1440"
token=os.environ.get("NETLIFY_AUTH_TOKEN","")
if token:
 req=urllib.request.Request("https://api.netlify.com/api/v1/sites/"+os.environ["NETLIFY_SITE_ID"],method="GET",headers={"Authorization":"Bearer "+token})
 with urllib.request.urlopen(req,timeout=35) as r:site=json.load(r)
 report["published_id_after"]=(site.get("published_deploy") or {}).get("id")
 assert report["published_id_after"]=="6adafef5f2c6d196833683db"
(OUT/"V2_LIVE_CHROME_FINAL_QA.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print("ENPT_V2_REAL_BROWSER_PASS",json.dumps(report,ensure_ascii=False),flush=True)
