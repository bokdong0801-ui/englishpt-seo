#!/usr/bin/env python3
"""GET only parse HTML attributes reliably, V3 21 forms and original OG image URLs.
No browser install, submissions, or Production changes.
"""
import html.parser,urllib.request,urllib.error,os,pathlib,json
class Document(html.parser.HTMLParser):
 def __init__(self):super().__init__();self.forms=[];self.fields=[];self.og=[];self.canon=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=="form":self.forms.append(d)
  if tag in ("input","textarea","button"):self.fields.append({"tag":tag,**d})
  if tag=="meta" and d.get("property","").lower()=="og:image":self.og.append(d.get("content",""))
  if tag=="link" and "canonical" in (d.get("rel","") or "").lower():self.canon.append(d.get("href",""))
host="https://review-enpt-v3-fullsite-20261027--englishpt-seo.netlify.app"
provinces=("gangwon","gyeonggi","gyeongnam","gyeongbuk","gwangju","daegu","daejeon","busan","seoul","sejong","ulsan","incheon","jeonnam","jeonbuk","jeju","chungnam","chungbuk")
paths=("englishpt.html","courses.html","student-english.html","regions/")+tuple("regions/"+x+".html" for x in provinces)
report={"source":host,"pages_expected":len(paths),"pages_http200":0,"form_complete":0,"og_tests":[],"failed":[],"form_submissions":0,"published_writes":0}
def get(url,token=None):
 h={"User-Agent":"ENPT-Owner-Fast-DOM-ReadOnly"}
 if token:h["Authorization"]="Bearer "+token
 req=urllib.request.Request(url,method="GET",headers=h)
 with urllib.request.urlopen(req,timeout=35) as r:return r.status,r.headers,r.read(4000000)
for path in paths:
 try:
  stat,headers,data=get(host+"/"+path);assert stat==200,("BAD_HTTP",stat)
  d=Document();d.feed(data.decode("utf8","replace"))
  forms=[f for f in d.forms if f.get("id")=="leadForm"]
  assert len(forms)==1,("FORM_COUNT",len(forms))
  form=forms[0]
  assert form.get("name")=="englishpt-consultation",("FORM_NAME",form)
  assert form.get("method","").lower()=="post",("FORM_METHOD",form.get("method"))
  fields=d.fields
  for name in ("name","phone","area","message","consent","bot-field","form-name","wantedClass","requestType"):
   assert any(f.get("name")==name for f in fields),("FIELD_MISSING",name)
  assert any(f.get("name")=="form-name" and f.get("value")=="englishpt-consultation" for f in fields)
  assert any(f.get("id")=="leadConsent" and ("required" in f) for f in fields),("CONSENT_REQUIRED")
  report["pages_http200"]+=1;report["form_complete"]+=1
  if path in ("englishpt.html","courses.html","student-english.html"):
   assert len(d.og)==1,("OG_META_COUNT",len(d.og))
   og=d.og[0]
   assert og.startswith("https://englishpt.kr/"),("OG_HOST",og)
   res,imHeaders,raw=get(og)
   imagecheck={"page":path,"url":og,"status":res,"content_type":imHeaders.get("Content-Type",""),"jpeg_header":raw[:3].hex()}
   report["og_tests"].append(imagecheck)
   assert res==200 and imHeaders.get("content-type","").startswith("image/"),("OG_IMAGE_BAD",imagecheck)
 except Exception as e:report["failed"].append({"path":path,"reason":str(e)[:220]})
try:
 tok=os.environ["NETLIFY_AUTH_TOKEN"]
 resp,h,raw=get("https://api.netlify.com/api/v1/sites/98d96cc5-f0b7-4d3d-8072-6476d93e55a3/forms",token=tok)
 forms=json.loads(raw)
 report["netlify_consultation_registered"]=any(f.get("name")=="englishpt-consultation" for f in forms)
 assert report["netlify_consultation_registered"]
except Exception as e:report["failed"].append({"forms_api":str(e)[:220]})
report["status"]="PASS_ALL_21_FORM_AND_3_REAL_OG_IMAGES" if not report["failed"] and report["form_complete"]==21 and len(report["og_tests"])==3 else "HOLD_ERRORS"
out=pathlib.Path("v3-fast-htmlparser-qa");out.mkdir(exist_ok=True)
(out/"V3_21_FORM_AND_OG_IMAGES_PROPER_PARSE.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),"utf8")
print("ENPT_V3_HTMLPARSER_FORM_OG_QA",json.dumps(report,ensure_ascii=False),flush=True)
assert report["status"].startswith("PASS"),"HOLD_FORM_OR_OG_ERRORS"
