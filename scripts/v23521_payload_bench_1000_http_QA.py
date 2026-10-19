#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Real small diagnostic Draft HTTP smoke. GET only. No Forms POST, no indexing."""
import argparse,datetime,hashlib,json,re,struct,urllib.request,urllib.error,pathlib
SAMPLES=[
"gyeongnam-milyang-naeidong-elem-tutor.html",
"gyeongnam-milyang-naeidong-mid-tutor.html",
"gyeongnam-milyang-naeidong-high-tutor.html",
"seoul-jongno-sajikdong-elem-tutor.html",
"seoul-jongno-sajikdong-mid-tutor.html",
"seoul-jongno-sajikdong-high-tutor.html",
"englishpt.html"]
PNG="beginner toeic ielts toefl opic tos duolingo elementary middle high student worker college jobseeker housewife stations region academy tutor conversation exam courses englishpt reading writing international phone video general".split()
def get(url,maxb=500000):
 req=urllib.request.Request(url,headers={"User-Agent":"EnglishPT-SMALL-GET-ONLY-DraftQA/1.0"},method="GET")
 with urllib.request.urlopen(req,timeout=20) as resp:return resp.status,dict(resp.headers),resp.read(maxb),resp.geturl()
def main():
 p=argparse.ArgumentParser();p.add_argument("--draft-url",required=True);p.add_argument("--report",required=True)
 a=p.parse_args();url=a.draft_url.rstrip("/")
 if not url.startswith("https://") or not url.endswith(".netlify.app"):raise ValueError("Only immutable Netlify Draft host allowed")
 r={"status":"HOLD","draft_url":url,"checked_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "GET_only":True,"Production_not_published":True,"Forms_POST_count":0,"errors":[],"checked":[]}
 for path in ["/index.html","/robots.txt","/_redirects",*["/"+x for x in SAMPLES],"/pilot.js"]:
  if path=="/_redirects":continue
  try:
   status,h,body,final=get(url+path)
   if status!=200:raise ValueError("Expected HTTP 200")
   if path.endswith(".html"):
    if not h.get("Content-Type","").lower().startswith("text/html"):
     raise ValueError("Edge failed to return text/html Content-Type: "+str(h.get("Content-Type")))
    if "noindex" not in h.get("X-Robots-Tag","").lower():
     raise ValueError("Draft HTTP noindex header missing")
    if path!="/index.html":
     page=body.decode("utf8","replace")
     if "https://englishpt.kr/"+path.lstrip("/") not in page:
      raise ValueError("Public canonical missing")
     if "tutor" in path:
      for token in ('name="englishpt-consultation"','name="form-name"','name="requestType"'):
       if token not in page:raise ValueError("static tutor form markup "+token)
   if path=="/robots.txt" and b"Disallow: /" not in body:raise ValueError("Draft robots disallow missing")
   if path=="/pilot.js":
    actual=hashlib.sha256(body).hexdigest()
    if actual!="d604994a74352a81978002fd6f6286c7d0f4f4c99278745bbf6dad1abce29ede":
     raise ValueError("Wrong patched JS sha256")
   r["checked"].append({"path":path,"status":status,"noindex":h.get("X-Robots-Tag")})
  except Exception as exc:r["errors"].append({"path":path,"error":str(exc)[:200]})
 for name in PNG:
  path="/assets/images/og-pages/"+name+".png"
  try:
   s,h,body,final=get(url+path,maxb=24)
   if s!=200 or body[:8]!=bytes.fromhex("89504e470d0a1a0a") or len(body)<24 or struct.unpack(">II",body[16:24])!=(1200,630):
    raise ValueError("OG master image PNG 1200x630 missing")
   r["checked"].append({"path":path,"status":s})
  except Exception as exc:r["errors"].append({"path":path,"error":str(exc)[:150]})
 r["checks_ok"]=len(r["checked"])
 r["status"]="PASS_SMALL_REAL_REVIEW_DRAFT_EDGE_FORMS_STATIC_NOINDEX_OG29" if not r["errors"] else "HOLD_SMALL_DRAFT_HTTP_QA"
 pth=pathlib.Path(a.report);pth.parent.mkdir(parents=True,exist_ok=True)
 pth.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("SMALL_REAL_DRAFT_HTTP_QA",json.dumps({k:v for k,v in r.items() if k!="checked"},ensure_ascii=False),flush=True)
 return 0 if not r["errors"] else 1
if __name__=="__main__":raise SystemExit(main())
