#!/usr/bin/env python3
"""Fresh V3.1 pre-approval hard gate, GET ONLY, no form test here, no publish.
Verify Netlify exact IDs, all 44 live sitemap shards and 21,964 URLs, SEO and media samples,
7 fixes, 21 region/core entry routes, forms/hooks config; issue HOLD for external inbox.
"""
from __future__ import annotations
import collections,datetime,json,os,pathlib,re,urllib.request,urllib.error,xml.etree.ElementTree as ET
from html.parser import HTMLParser
OUT=pathlib.Path("v31-preapproval-gate");OUT.mkdir(exist_ok=True)
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
PUB="6adafef5f2c6d196833683db"
DRAFT="6ae06963f085b33a5ee903eb"
BASE="https://review-enpt-v3-1-20261027--englishpt-seo.netlify.app"
EXPECTED_TITLE="ENPT-V3-1-20261027-BYEONGMOKANDONG-7-CORRECTED-NONPUB"
TOKEN=os.environ["NETLIFY_AUTH_TOKEN"]
API="https://api.netlify.com/api/v1/"
class Meta(HTMLParser):
 def __init__(self):super().__init__();self.canon=[];self.robots=[];self.og=[];self.form=False;self.title=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=="link" and d.get("rel","").lower()=="canonical":self.canon.append(d.get("href",""))
  if tag=="meta" and d.get("name","").lower()=="robots":self.robots.append(d.get("content",""))
  if tag=="meta" and d.get("property","").lower()=="og:image":self.og.append(d.get("content",""))
  if tag=="form" and d.get("name")=="englishpt-consultation":self.form=True
def api(path):
 req=urllib.request.Request(API+path,headers={"Authorization":"Bearer "+TOKEN},method="GET")
 with urllib.request.urlopen(req,timeout=40) as r:return json.load(r)
def get(url,limit=16000000):
 req=urllib.request.Request(url,method="GET",headers={"User-Agent":"ENPT-V31-SAFE-FINAL-READONLY"})
 with urllib.request.urlopen(req,timeout=42) as r:return r.status,r.headers,r.read(limit)
rep={"checked_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"phase":"FINAL_PREAPPROVAL_GETONLY","draft_id":DRAFT,"production_id_expected":PUB,"files_expected":202786,"production_deploys":0,"form_posts":0,"errors":[],"http_pages":[],"xml_sitemaps":[],"og_assets":[]}
site=api("sites/"+SITE)
draft=api("sites/"+SITE+"/deploys/"+DRAFT)
rep["production_id_actual"]=(site.get("published_deploy") or {}).get("id")
assert rep["production_id_actual"]==PUB,"PRODUCTION_DEPLOY_ID_CHANGED"
assert site.get("custom_domain")=="englishpt.kr"
assert draft.get("id")==DRAFT and draft.get("state")=="ready" and draft.get("published_at") is None and draft.get("draft") is not False
assert draft.get("title")==EXPECTED_TITLE and not draft.get("required") and not draft.get("required_edge_functions")
rep["draft_only"]=True
forms=api("sites/"+SITE+"/forms")
rep["registered_consultation_forms"]=sum(x.get("name")=="englishpt-consultation" for x in forms)
assert rep["registered_consultation_forms"]==1
hooks=api("hooks?site_id="+SITE)
rep["email_submission_hooks_count"]=sum(h.get("type")=="email" and h.get("event")=="submission_created" for h in hooks)
assert rep["email_submission_hooks_count"]>=1
routes=["englishpt.html","courses.html","student-english.html","regions/"]+["regions/"+p+".html" for p in ("gangwon","gyeonggi","gyeongnam","gyeongbuk","gwangju","daegu","daejeon","busan","seoul","sejong","ulsan","incheon","jeonnam","jeonbuk","jeju","chungnam","chungbuk")]
routes+=["gyeonggi-anyang-manan-byeongmokandong-"+p+".html" for p in ("elem-tutor","elem-conv","mid-tutor","mid-conv","high-tutor","high-conv","worker-english-conv-academy")]
assert len(routes)==28
for p in routes:
 try:
  status,h,b=get(BASE+"/"+p,250000)
  assert status==200,(p,status)
  s=b.decode("utf8","replace")
  meta=Meta();meta.feed(s)
  assert meta.form,("FORM_MISSING",p)
  assert len(meta.canon)==1 and meta.canon[0].startswith("https://englishpt.kr/"),("CANONICAL",p,meta.canon)
  if p.startswith("gyeonggi-anyang-manan-byeongmokandong-"):
   assert meta.canon==["https://englishpt.kr/"+p],("CANONICAL_PATH",p)
   assert "병목안동" in s and "가장 어려운 부분안동" not in s
  elif p in ("englishpt.html","courses.html","student-english.html"):
   assert 'enpt-regions-entry-20261027' in s
  elif p.startswith("regions/"):
   assert any("noindex" in t.lower() for t in meta.robots),("HUB_NO_NOINDEX",p)
  rep["http_pages"].append({"path":p,"http":200,"form":True,"canonical":meta.canon[0],"meta_robots":meta.robots})
  if p in ("englishpt.html","courses.html","student-english.html"):
   assert len(meta.og)==1
   ogurl=meta.og[0]
   code,headers,image=get(ogurl,300000)
   assert code==200 and (headers.get("content-type") or "").startswith("image/") and len(image)>500,("OG",p)
   rep["og_assets"].append({"path":p,"url":ogurl,"http":code,"mime":headers.get("content-type"),"bytes_sampled":len(image)})
 except Exception as ex:rep["errors"].append({"page":p,"reason":str(ex)[:300]})
try:
 status,h,rob=get(BASE+"/robots.txt")
 assert status==200 and b"Disallow: /" not in rob,("PRODUCTION_ROBOTS_LEAK")
 status,h,index=get(BASE+"/sitemap-index.xml")
 assert status==200
 locs=[x.text for x in ET.fromstring(index).iter() if x.tag.endswith("loc")]
 assert len(locs)==44
 total=0
 for u in locs:
  assert u.startswith("https://englishpt.kr/")
  status,h,data=get(BASE+u[len("https://englishpt.kr"):])
  assert status==200
  n=sum(el.tag.endswith("loc") for el in ET.fromstring(data).iter())
  total+=n
  rep["xml_sitemaps"].append({"url":u,"status":status,"loc_count":n})
 assert total==21964,("SITEMAP_INDEXABLE_TOTAL",total)
 rep["sitemap_index_count"]=len(locs);rep["sitemap_loc_total"]=total
except Exception as e:rep["errors"].append({"sitemap_or_robots":str(e)[:300]})
after=api("sites/"+SITE)
assert (after.get("published_deploy") or {}).get("id")==PUB
rep["status"]="PASS_V31_PREAPPROVAL_GETONLY_ALL_28_PAGES_44_SITEMAPS" if not rep["errors"] and len(rep["http_pages"])==28 and len(rep["xml_sitemaps"])==44 else "HOLD_V31_PREAPPROVAL_ERRORS"
rep["inbox_delivery_verification"]="REQUIRES_NAVER_MAILBOX_OBSERVATION"
rep["publish_approval"]="NOT_REQUESTED_NO_PUBLISH"
(OUT/"V31_PREAPPROVAL_FINAL_GETONLY_GATE.json").write_text(json.dumps(rep,ensure_ascii=False,indent=2),"utf8")
print("ENPT_V31_FINAL_APPROVAL_GATE",json.dumps({k:v for k,v in rep.items() if k not in ("http_pages","xml_sitemaps","og_assets")},ensure_ascii=False),flush=True)
assert rep["status"].startswith("PASS"),"HOLD_FINAL_GATE"
