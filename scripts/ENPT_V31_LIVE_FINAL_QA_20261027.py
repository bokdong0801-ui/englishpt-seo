#!/usr/bin/env python3
"""Exact nonpublished V3.1 GET-only browser validation of 7 repaired neighborhood pages,
21 regional/core HTML pages, 44 site maps, indexed/robots and production immutability.
"""
from __future__ import annotations
import collections,datetime,json,os,pathlib,re,urllib.request,urllib.error,xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
PUBLISHED="6adafef5f2c6d196833683db"
DRAFT="6ae06963f085b33a5ee903eb"
TOKEN=os.environ["NETLIFY_AUTH_TOKEN"]
OUT=pathlib.Path("v3-1-live-qa-evidence");OUT.mkdir(exist_ok=True)
PREFIX="gyeonggi-anyang-manan-byeongmokandong-"
COURSES=("elem-tutor","elem-conv","mid-tutor","mid-conv","high-tutor","high-conv","worker-english-conv-academy")
TOWNS=[PREFIX+c+".html" for c in COURSES]
REGIONS=["regions/"]+["regions/"+p+".html" for p in ("gangwon","gyeonggi","gyeongnam","gyeongbuk","gwangju","daegu","daejeon","busan","seoul","sejong","ulsan","incheon","jeonnam","jeonbuk","jeju","chungnam","chungbuk")]
CORE=["englishpt.html","courses.html","student-english.html"]
def api(path):
 q=urllib.request.Request("https://api.netlify.com/api/v1/"+path,method="GET",headers={"Authorization":"Bearer "+TOKEN})
 with urllib.request.urlopen(q,timeout=38) as r:return json.load(r)
def get(url):
 q=urllib.request.Request(url,method="GET",headers={"User-Agent":"ENPT-Owner-V31-Live-ReadOnly"})
 with urllib.request.urlopen(q,timeout=42) as r:return r.status,r.headers,r.read(15000000)
site=api("sites/"+SITE);d=api("sites/"+SITE+"/deploys/"+DRAFT)
assert (site.get("published_deploy") or {}).get("id")==PUBLISHED,"PRODUCTION_CHANGED"
assert d.get("state")=="ready" and d.get("published_at") is None and d.get("draft") is not False
assert d.get("title")=="ENPT-V3-1-20261027-BYEONGMOKANDONG-7-CORRECTED-NONPUB"
assert not d.get("required") and not d.get("required_edge_functions")
BASE=d.get("deploy_ssl_url") or d.get("deploy_url")
assert BASE and DRAFT in BASE and BASE.startswith("https://"),("UNEXPECTED_DRAFT_URL",BASE)
BASE=BASE.rstrip("/")
report={"draft_id":DRAFT,"preview":BASE,"published_id":PUBLISHED,"status":"HOLD","routes":[],"errors":[],"browser":[],"sitemaps":[],"form_posts":0,"production_changes":0}
for path in CORE+TOWNS+["regions/","regions/seoul.html","regions/gyeonggi.html","favicon.ico","robots.txt"]:
 try:
  status,headers,raw=get(BASE+"/"+path)
  assert status==200,("HTTP_NOT_200",status)
  row={"path":path,"status":status,"bytes":len(raw),"xrobots":headers.get("X-Robots-Tag","")}
  if path in TOWNS:
   s=raw.decode("utf8","replace")
   assert "병목안동" in s,("CORRECTED_NAME_ABSENT",path)
   assert "가장 어려운 부분안동" not in s,("WRONG_PHRASE_REMAINS",path)
   title=re.search(r"<title>(.*?)</title>",s,re.S|re.I)
   assert title and "병목안동" in title.group(1),("TITLE_WRONG",path)
   canonical=re.search(r'<link\s+rel=["\x27]canonical["\x27]\s+href=["\x27]([^"\x27]+)',s,re.I)
   assert canonical and canonical.group(1)=="https://englishpt.kr/"+path,("CANONICAL_WRONG",path)
   assert "englishpt-consultation" in s
   row["repair"]="PASS";row["canonical"]=canonical.group(1)
  if path in CORE:
   assert b'enpt-regions-entry-20261027' in raw
   assert b'englishpt-consultation' in raw
   assert b'rel="canonical"' in raw or b"rel='canonical'" in raw
  if path in REGIONS:
   assert b'englishpt-consultation' in raw
  if path=="robots.txt":
   assert b"Disallow: /" not in raw,("DRAFT_BLOCK_RULE_LEAK",path)
  report["routes"].append(row)
 except Exception as e:report["errors"].append({"path":path,"error":str(e)[:300]})
try:
 status,headers,index=get(BASE+"/sitemap-index.xml")
 assert status==200
 root=ET.fromstring(index)
 children=[e.text for e in root.iter() if e.tag.endswith("loc")]
 assert len(children)==44,("CHILD_SITEMAPS",len(children))
 total=0
 for child in children:
  assert child.startswith("https://englishpt.kr/")
  path=child[len("https://englishpt.kr/"):]
  http,headers,data=get(BASE+"/"+path)
  assert http==200
  roots=ET.fromstring(data)
  n=sum(x.tag.endswith("loc") for x in roots.iter())
  report["sitemaps"].append({"path":path,"status":http,"url_count":n})
  total+=n
 assert total==21964,("SITEMAP_URL_COUNT",total)
 report["total_sitemap_urls"]=total
except Exception as e:report["errors"].append({"sitemap":"ERROR","detail":str(e)[:300]})
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
 for width,height in [(390,844),(768,1024),(1440,900)]:
  page=browser.new_page(viewport={"width":width,"height":height})
  js=[]
  page.on("pageerror",lambda x:js.append(str(x)[:200]))
  for path in CORE+REGIONS+TOWNS:
   try:
    r=page.goto(BASE+"/"+path,wait_until="domcontentloaded",timeout=45000)
    assert r and r.status==200,("BROWSER_HTTP",path,r.status if r else None)
    assert page.locator("body").evaluate("(el)=>el.scrollWidth<=innerWidth+2"),("WIDTH_OVERFLOW",path,width)
    assert page.locator("#leadForm").count()==1,("FORM_MISSING",path)
    if path in CORE:
     assert page.locator("#enpt-regions-entry-20261027").count()==1
     page.locator("#enpt-regions-entry-20261027 button[data-open-form]").click()
     assert page.locator("#applyModal").get_attribute("aria-hidden")=="false"
     assert page.locator("#leadName").is_visible() and page.locator("#leadPhone").is_visible()
     page.locator("[data-close-form]").last.click()
     assert page.locator("#applyModal").get_attribute("aria-hidden")=="true"
     page.locator("#enpt-regions-entry-20261027 a").first.click()
     page.wait_for_load_state("domcontentloaded")
     assert page.locator(".rg-card").count()==17,("REGION_ROUTE_NAV_FAILED",path)
    if path=="regions/":
     assert page.locator(".rg-card").count()==17
     if width in (390,1440):page.screenshot(path=str(OUT/f"V31_NATIONAL_{width}.png"),full_page=True)
    elif path=="regions/seoul.html":
     page.locator("#rgSearch").fill("사직동")
     target=page.locator('.rg-town[data-locality="seoul-jongno-sajikdong"]')
     assert target.count()==1
     if not target.evaluate("(e)=>e.open"):target.locator("summary").click()
     assert target.locator("a").count()==7 and target.locator("a").first.is_visible()
    elif path.startswith("regions/"):
     assert page.locator(".rg-town").count()>0
    elif path in TOWNS:
     title=page.locator("title").text_content()
     assert "병목안동" in title and "가장 어려운 부분안동" not in title
     if width in (390,1440) and path.endswith("elem-tutor.html"):
      page.screenshot(path=str(OUT/f"V31_BYEONGMOKANDONG_{width}.png"),full_page=True)
  except Exception as e:report["errors"].append({"width":width,"path":path,"error":str(e)[:300]})
  report["browser"].append({"width":width,"routes_attempted":len(CORE+REGIONS+TOWNS),"js_errors":js[:5]})
  if js:report["errors"].append({"width":width,"js_errors":js[:5]})
  page.close()
 browser.close()
site=api("sites/"+SITE)
assert (site.get("published_deploy") or {}).get("id")==PUBLISHED
report["status"]="PASS_V31_7_REPAIRS_21_REGIONS_44_SITEMAPS_390_768_1440" if not report["errors"] else "HOLD_REVIEW_QA_ISSUES"
(OUT/"V31_FINAL_NONPUBLISHED_LIVE_QA.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),"utf8")
print("ENPT_V31_FINAL_LIVE_QA",json.dumps({k:v for k,v in report.items() if k not in ("routes","sitemaps")},ensure_ascii=False),flush=True)
assert not report["errors"],"HOLD_V31_QA_INCOMPLETE"
