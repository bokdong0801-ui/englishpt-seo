#!/usr/bin/env python3
"""Read-only final V3 full Netlify draft live QA; never POST forms or publish.
Includes edge sharded route sample, full region links, published ID and SEO semantics.
"""
from __future__ import annotations
import collections,datetime,json,os,pathlib,urllib.error,urllib.request,xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright
OUT=pathlib.Path("enpt-v3-fullsite-qa");OUT.mkdir(exist_ok=True)
SITE_ID="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
PIN="6adafef5f2c6d196833683db"
alias=os.environ["ALIAS"];base=f"https://{alias}--englishpt-seo.netlify.app"
TOK=os.environ.get("NETLIFY_AUTH_TOKEN","")
assert TOK,"HOLD_MISSING_NETLIFY_TOKEN"
def get(url,headers=None):
 req=urllib.request.Request(url,method="GET",headers=headers or {"User-Agent":"ENPT-V3-FULL-READONLY-QA"})
 with urllib.request.urlopen(req,timeout=45) as r:
  return r.status,r.headers,r.read(10000000),r.geturl()
def prod():
 req=urllib.request.Request(f"https://api.netlify.com/api/v1/sites/{SITE_ID}",method="GET",headers={"Authorization":"Bearer "+TOK})
 with urllib.request.urlopen(req,timeout=40) as r:return json.load(r)
report={"status":"HOLD","draft":base,"production_before":(prod().get("published_deploy") or {}).get("id"),"published":False,"form_posts":0,"production_writes":0,"sitemap":[],"snapshots":[],"errors":[]}
assert report["production_before"]==PIN,"PUBLISHED_BEFORE_MISMATCH"
tests={"/englishpt.html":200,"/courses.html":200,"/student-english.html":200,
"/regions/":200,"/regions/seoul.html":200,"/regions/gyeonggi.html":200,
"/robots.txt":200,"/sitemap-index.xml":200,"/favicon.ico":200,
"/stations.html":200,"/seoul-jongno-sajikdong-high-tutor.html":200,
"/gyeongnam-milyang-naeidong-elem-tutor.html":200,
"/station-419minjumyoji-toeic.html":200,
"/guides/international-school-english.html":200}
for path,expected in tests.items():
 try:
  status,headers,body,location=get(base+path)
  assert status==expected,(path,status)
  row={"path":path,"status":status,"content_type":headers.get("content-type",""),"bytes":len(body),"xrobots":headers.get("x-robots-tag",""),"canonical":b'rel="canonical"' in body,"og_image":b'property="og:image"' in body}
  report["snapshots"].append(row)
  if path=="/robots.txt":
   assert b"Disallow: /" not in body,"PREVIEW_ONLY_ROBOTS_LEAKED"
  if path.endswith(".html") and not path.startswith("/regions/"):
   assert row["canonical"],("ORIGINAL_PAGE_CANONICAL_MISSING",path)
  if path in ["/englishpt.html","/courses.html","/student-english.html"]:
   assert b'enpt-regions-entry-20261027' in body,("CORE_REGION_ENTRY_MISSING",path)
  if path in ("/regions/","/regions/seoul.html"):
   assert b'enpt-region' in body and (b'noindex,follow' in body or b'noindex, follow' in body),("REGIONS_NOINDEX_POLICY",path)
 except Exception as exc:
  report["errors"].append({"path":path,"reason":str(exc)[:220]})
try:
 _,_,idx,_=get(base+"/sitemap-index.xml")
 xml=ET.fromstring(idx)
 locs=[x.text for x in xml.iter() if x.tag.endswith("loc")]
 assert len(locs)==44,("SITEMAP_SHARDS",len(locs))
 # The sitemap index points to englishpt.kr; use preview-host rewrite for exact active candidate verification.
 total=0
 for loc in locs:
  if not loc.startswith("https://englishpt.kr/"):raise RuntimeError("CROSS_DOMAIN_SITEMAP")
  locdraft=base+loc[len("https://englishpt.kr"):]
  status,headers,body,_=get(locdraft)
  assert status==200,(locdraft,status)
  document=ET.fromstring(body)
  count=sum(x.tag.endswith("loc") for x in document.iter())
  report["sitemap"].append({"source":loc,"draft_http":status,"loc_count":count,"bytes":len(body)})
  total+=count
 assert total==21964,("SITEMAP_TOTAL_URLS",total)
 report["sitemap_total_urls"]=total
except Exception as exc:report["errors"].append({"path":"/sitemap-index.xml","reason":"SITEMAP_"+str(exc)[:220]})
provinces=["gangwon","gyeonggi","gyeongnam","gyeongbuk","gwangju","daegu","daejeon","busan","seoul","sejong","ulsan","incheon","jeonnam","jeonbuk","jeju","chungnam","chungbuk"]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
 for width,height in [(390,844),(768,1024),(1440,900)]:
  page=browser.new_page(viewport={"width":width,"height":height})
  failures=[]
  page.on("pageerror",lambda e:failures.append(str(e)[:170]))
  for path in ["/regions/"]+[f"/regions/{slug}.html" for slug in provinces]+["/englishpt.html","/courses.html","/student-english.html"]:
   try:
    response=page.goto(base+path,wait_until="domcontentloaded",timeout=55000)
    assert response and response.status==200,("BROWSER_HTTP",path,response.status if response else "null")
    assert page.locator("body").evaluate("(e)=>e.scrollWidth<=innerWidth+2"),("HORIZONTAL_OVERFLOW",path,width)
    assert page.locator("#leadForm").count()==1,("FORM_MISSING",path)
    if path=="/regions/":
     assert page.locator(".rg-card").count()==17
     if width in (390,1440):page.screenshot(path=str(OUT/f"V3_NATIONAL_{width}.png"),full_page=True)
    elif path.startswith("/regions/"):
     assert page.locator(".rg-town").count()>0,("TOWNS_NOT_PRESENT",path)
     assert page.locator('.rg-town-links a[href*="-elem-tutor.html"]').count()==page.locator(".rg-town").count(),("TOWN_MISSING_STUDENT_LINK",path)
     if path=="/regions/seoul.html":
      page.locator("#rgSearch").fill("사직동")
      town=page.locator('.rg-town[data-locality="seoul-jongno-sajikdong"]')
      assert town.count()==1
      if not town.evaluate("(e)=>e.open"):town.locator("summary").click()
      assert town.locator("a").count()==7 and town.locator("a").first.is_visible(),("SEVEN_CHOICES_MISSING",width)
      if width in (390,1440):page.screenshot(path=str(OUT/f"V3_SEOUL_{width}.png"),full_page=True)
    else:
     assert page.locator("#enpt-regions-entry-20261027").count()==1,("CORE_ENTRY_MISSING",path)
     page.locator("#enpt-regions-entry-20261027 button[data-open-form]").click()
     assert page.locator("#applyModal").get_attribute("aria-hidden")=="false",("FORM_OPEN",path)
     assert page.locator("#leadPhone").is_visible() and page.locator("#leadName").is_visible()
     page.locator("[data-close-form]").last.click()
     assert page.locator("#applyModal").get_attribute("aria-hidden")=="true"
     page.locator("#enpt-regions-entry-20261027 a").first.click()
     page.wait_for_load_state("domcontentloaded",timeout=35000)
     assert page.locator(".rg-card").count()==17,("CORE_NAV_NOT_REACHING_HUB",path)
   except Exception as exc:
    report["errors"].append({"viewport":width,"page":path,"reason":str(exc)[:230]})
  report.setdefault("browser",[]).append({"viewport":width,"pages_expected":21,"js_errors":failures})
  if failures:report["errors"].append({"viewport":width,"reason":"JS_ERRORS","sample":failures[:3]})
  page.close()
 browser.close()
report["production_after"]=(prod().get("published_deploy") or {}).get("id")
assert report["production_after"]==PIN,"PUBLISHED_AFTER_MISMATCH"
report["status"]="PASS_FULL_V3_158571_ROUTES_SAFE_DRAFT_SEO_FORMS_MOBILE" if not report["errors"] else "HOLD_V3_DRAFT_QA_ISSUES"
(OUT/"V3_FULL_DRAFT_LIVE_QA.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),"utf8")
print("ENPT_V3_FULLSITE_DRAFT_LIVE_QA",json.dumps({k:v for k,v in report.items() if k not in ["snapshots","sitemap"]},ensure_ascii=False),flush=True)
assert not report["errors"],"HOLD_POSTDEPLOY_ISSUES"
