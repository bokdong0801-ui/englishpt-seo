#!/usr/bin/env python3
"""GET-only final V3 Form/SEO/OG validation. Never click submit, POST, or publish anything.
Netlify form registration is queried GET-only; notifications not triggered.
"""
from __future__ import annotations
import collections,datetime,json,os,pathlib,re,urllib.request,urllib.error,html.parser
from playwright.sync_api import sync_playwright
OUT=pathlib.Path("v3-forms-assets-qa");OUT.mkdir(exist_ok=True)
ROOT="https://review-enpt-v3-fullsite-20261027--englishpt-seo.netlify.app"
PUBLISHED="6adafef5f2c6d196833683db"
SITE_ID="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
TOK=os.environ.get("NETLIFY_AUTH_TOKEN","")
CORE=("englishpt.html","courses.html","student-english.html","regions/index.html","regions/seoul.html","regions/gyeonggi.html")
PROVINCES=("gangwon","gyeonggi","gyeongnam","gyeongbuk","gwangju","daegu","daejeon","busan","seoul","sejong","ulsan","incheon","jeonnam","jeonbuk","jeju","chungnam","chungbuk")
PAGES=sorted(set(CORE+tuple("regions/"+name+".html" for name in PROVINCES)))
FIELDS=("#leadName","#leadPhone","#leadArea","#leadMessage","#leadConsent")
report={"time_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"draft":ROOT,
"expected_pages":len(PAGES),"widths":[390,1440],"tests":[],"failures":[],"cross_page_form_contract_count":0,
"form_post_attempts":0,"production_writes":0,"real_email_received":"NOT_TESTED_NO_SUBMISSIONS","og_checks":[]}
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
 for width,height in [(390,844),(1440,900)]:
  context=browser.new_context(viewport={"width":width,"height":height})
  page=context.new_page()
  outbound=[]
  page.on("request",lambda req:outbound.append({"method":req.method,"url":req.url}) if req.method not in ("GET","HEAD") else None)
  for target in PAGES:
   try:
    if target=="regions/index.html":targetURL=ROOT+"/regions/"
    else:targetURL=ROOT+"/"+target
    resp=page.goto(targetURL,wait_until="domcontentloaded",timeout=55000)
    assert resp and resp.status==200,("STATUS",target,resp.status if resp else None)
    f=page.locator("#leadForm")
    assert f.count()==1,("FORM_COUNT",target)
    assert f.get_attribute("method").lower()=="post",("FORM_METHOD",target)
    assert f.get_attribute("name")=="englishpt-consultation",("FORM_NAME",target)
    assert f.locator("input[name='form-name']").get_attribute("value")=="englishpt-consultation",("NETLIFY_FORM_NAME",target)
    assert f.locator("input[name='bot-field']").count()==1,("HONEYPOT",target)
    assert f.locator("input[name='subject']").count()==1,("SUBJECT",target)
    assert f.locator("input[name='requestType']").count()==1,("REQUESTTYPE",target)
    assert f.locator("input[name='wantedClass']").count()==1,("WANTEDCLASS",target)
    for field in FIELDS:
     assert page.locator(field).count()==1,("FIELD",target,field)
    for required in ("#leadName","#leadPhone","#leadArea","#leadConsent"):
     assert page.locator(required).get_attribute("required") is not None,("REQUIRED_FIELD",target,required)
    assert f.locator("button[type='submit']").count()==1,("SUBMIT_BUTTON",target)
    assert page.locator("body").evaluate("(el)=>el.scrollWidth <= window.innerWidth + 2"),("OVERFLOW",target,width)
    report["cross_page_form_contract_count"]+=1
    if target in CORE:
     page.locator("button[data-open-form]:visible").first.click()
     assert page.locator("#applyModal").get_attribute("aria-hidden")=="false"
     assert not f.evaluate("(el)=>el.checkValidity()"),("EMPTY_FORM_VALID",target)
     page.locator("#leadName").fill("QA 검수")
     page.locator("#leadPhone").fill("01000000000")
     page.locator("#leadArea").fill("테스트 지역")
     page.locator("#leadMessage").fill("폼 UI 검사만 수행하고 전송하지 않음")
     page.locator("#leadConsent").check()
     assert f.evaluate("(el)=>el.checkValidity()"),("VALID_DATA_REJECTED",target)
     page.locator("[data-close-form]:visible").last.click()
     assert page.locator("#applyModal").get_attribute("aria-hidden")=="true"
    if target=="regions/seoul.html":
     page.locator("#rgSearch").fill("사직동")
     assert page.locator('.rg-town[data-locality="seoul-jongno-sajikdong"]').is_visible()
     page.locator("#rgSearch").fill("")
    report["tests"].append({"width":width,"page":target,"status":"PASS"})
   except Exception as e:report["failures"].append({"width":width,"page":target,"reason":str(e)[:400]})
  report["form_post_attempts"]+=len(outbound)
  page.close();context.close()
 browser.close()
# GET-only main sitemap robots; 10 diverse indexed image samples.
class Media(html.parser.HTMLParser):
 def __init__(self):super().__init__();self.og=[];self.canon=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=="meta" and d.get("property","").lower()=="og:image":self.og.append(d.get("content"))
  if tag=="link" and "canonical" in d.get("rel","").lower():self.canon.append(d.get("href"))
SAMPLES=("englishpt.html","courses.html","student-english.html",
 "seoul-jongno-sajikdong-elem-tutor.html","seoul-jongno-sajikdong-mid-conv.html",
 "gyeongnam-milyang-naeidong-elem-tutor.html","daegu-dalseo-songhyeondong-worker-english-conv-academy.html",
 "station-419minjumyoji-toeic.html","seoul-jongno-sajikdong-high-tutor.html")
for target in SAMPLES:
 try:
  req=urllib.request.Request(ROOT+"/"+target,headers={"User-Agent":"ENPT-OWNER-V3-OG-QA-READONLY"})
  with urllib.request.urlopen(req,timeout=35) as r:
   body=r.read(120000).decode("utf8","replace");resp=r.status
  media=Media();media.feed(body)
  row={"page":target,"http":resp,"canonical":media.canon,"og_images":media.og}
  assert resp==200 and len(media.og)==1,("MISSING_OG_IMAGE",target)
  imreq=urllib.request.Request(media.og[0],headers={"User-Agent":"ENPT-OWNER-V3-OG-QA-READONLY"})
  with urllib.request.urlopen(imreq,timeout=35) as imr:
   pixels=imr.read(120000);row["image_http"]=imr.status;row["mime"]=imr.headers.get("content-type","");row["signature_jpeg"]=pixels[:3]==b"\xff\xd8\xff"
  assert row["image_http"]==200 and row["mime"].lower().startswith("image/"),("OG_IMAGE_INVALID",target)
  report["og_checks"].append(row)
 except Exception as e:report["failures"].append({"sample":target,"reason":str(e)[:270]})
# Netlify GET-only forms and site identity. Do not emit contact address or payload fields to logs.
if TOK:
 def api(path):
  request=urllib.request.Request("https://api.netlify.com/api/v1/"+path,method="GET",headers={"Authorization":"Bearer "+TOK})
  with urllib.request.urlopen(request,timeout=35) as r:return json.load(r)
 try:
  site=api("sites/"+SITE_ID)
  assert (site.get("published_deploy") or {}).get("id")==PUBLISHED,"PRODUCTION_ID_CHANGED"
  report["published_id"]=PUBLISHED
  forms=api("sites/"+SITE_ID+"/forms")
  report["netlify_form_registration"]={"form_count":len(forms),"consultation_form_present":any(v.get("name")=="englishpt-consultation" for v in forms),"consultation_form_ids":sum(v.get("name")=="englishpt-consultation" for v in forms)}
  assert report["netlify_form_registration"]["consultation_form_present"],"FORM_NOT_REGISTERED"
 except Exception as e:report["failures"].append({"admin_form_readonly":str(e)[:220]})
report["status"]="PASS_V3_FORM_CONTRACT_OG_AND_NO_POST" if not report["failures"] and report["form_post_attempts"]==0 and report["cross_page_form_contract_count"]==len(PAGES)*2 else "HOLD_REVIEW_FORMS_OR_ASSETS"
(OUT/"FORM_CONTRACT_OG_CHECK.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),"utf8")
print("ENPT_V3_FINAL_FORM_OG_STATUS",json.dumps({k:v for k,v in report.items() if k not in ("tests","og_checks")},ensure_ascii=False),flush=True)
assert report["status"].startswith("PASS"),"HOLD_FORMS_OG_FAILED"
