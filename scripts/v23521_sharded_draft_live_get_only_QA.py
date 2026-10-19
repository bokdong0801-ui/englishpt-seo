#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Draft immutable URL QA AFTER separate authorization. All requests GET, no Netlify writes.
No form submission, no search indexing, no Production publication.
"""
import argparse,gzip,hashlib,json,random,re,struct,sys,urllib.parse,urllib.request,urllib.error
from pathlib import Path
BASE_STEMS=("beginner toeic ielts toefl opic tos duolingo elementary middle high "
"student worker college jobseeker housewife stations region academy tutor "
"conversation exam courses englishpt reading writing international phone video general").split()
TUTORS=("gyeongnam-milyang-naeidong-elem-tutor.html","gyeongnam-milyang-naeidong-mid-tutor.html",
 "gyeongnam-milyang-naeidong-high-tutor.html","seoul-jongno-sajikdong-elem-tutor.html",
 "seoul-jongno-sajikdong-mid-tutor.html","seoul-jongno-sajikdong-high-tutor.html")
CANONICAL=re.compile(r'<link\s+rel="canonical"\s+href="([^"]+)"',re.I)
ROBOT=re.compile(r'<meta\s+name="robots"\s+content="([^"]+)"',re.I)
def get(url,cap=250000):
 req=urllib.request.Request(url,headers={"User-Agent":"ENGLISHPT-v23521-GET-only-Draft-QA","Accept":"*/*"},method="GET")
 with urllib.request.urlopen(req,timeout=35) as r:return r.status,r.headers,r.read(cap),r.geturl()
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--draft-url",required=True)
 p.add_argument("--map",required=True)
 p.add_argument("--report",required=True)
 a=p.parse_args()
 base=a.draft_url.rstrip("/")
 u=urllib.parse.urlsplit(base)
 if u.scheme!="https" or not u.hostname or not u.hostname.endswith(".netlify.app") or u.hostname=="englishpt.kr":
  raise ValueError("Forbidden live host, immutable Netlify Draft URL only")
 with gzip.open(a.map,"rt",encoding="utf8") as f:source=json.load(f)["original_to_new"]
 candidates=[x for x,v in source.items() if v["to"].startswith("__pages/") and x.endswith(".html")]
 candidates.sort()
 # Exactly 24 representatives dispersed across source filename ordering plus six parent/student samples.
 chosen=list(dict.fromkeys([candidates[(i*len(candidates))//24] for i in range(24)]+list(TUTORS)))
 result={"status":"RUNNING","draft_host":u.hostname,"draft_only":True,
    "queries_total":0,"http200_pages":0,"all_forms_samples":0,
    "content_errors":[],"all_OG_1200x630":0,"requested_routes":len(chosen),
    "actual_form_submissions":0,"production_published":False,"netlify_api_POST_count":0,
    "edge_function_runtime_observed":"UNVERIFIED_UNTIL_ROUTE_GET_RESPONSES"}
 try:
  for key in chosen:
   url=base+"/"+urllib.parse.quote(key,safe="")
   try:
    status,headers,body,final=get(url,300000)
    txt=body.decode("utf8",errors="replace")
    match=CANONICAL.search(txt)
    expected="https://englishpt.kr/"+key
    if status!=200 or not match or match.group(1)!=expected:
     raise ValueError("Status or canonical not preserved")
    if ROBOT.search(txt) is None:raise ValueError("Missing page-level robots meta")
    if key in TUTORS:
     if 'name="englishpt-consultation"' not in txt or 'name="form-name"' not in txt or 'name="requestType"' not in txt:
      raise ValueError("Consultation form static markup missing")
     result["all_forms_samples"]+=1
    result["http200_pages"]+=1
   except Exception as exc:
    result["content_errors"].append({"page":key,"error":type(exc).__name__+":"+str(exc)[:120]})
   result["queries_total"]+=1
  for stem in BASE_STEMS:
   try:
    status,_,head,_=get(base+"/assets/images/og-pages/"+stem+".png",24)
    if status!=200 or len(head)!=24 or head[:8]!=bytes.fromhex("89504e470d0a1a0a") or struct.unpack(">II",head[16:24])!=(1200,630):
     raise ValueError("OG image not correct PNG 1200x630")
    result["all_OG_1200x630"]+=1
   except Exception as exc:
    result["content_errors"].append({"OG":stem,"error":type(exc).__name__+":"+str(exc)[:120]})
  for path in ("/robots.txt","/sitemap-index.xml","/pilot.js"):
   try:
    status,h,body,_=get(base+path,350000)
    if status!=200:raise ValueError("HTTP not 200")
    if path=="/pilot.js" and hashlib.sha256(body).hexdigest()!="d604994a74352a81978002fd6f6286c7d0f4f4c99278745bbf6dad1abce29ede":
     raise ValueError("Patched JS hash mismatch")
    if path=="/sitemap-index.xml" and b"sitemapindex" not in body:raise ValueError("Missing sitemap index")
    result["queries_total"]+=1
   except Exception as exc:
    result["content_errors"].append({"asset":path,"error":type(exc).__name__+":"+str(exc)[:120]})
  result["edge_function_runtime_observed"]="PUBLIC_ROUTE_200_AND_CANONICAL" if result["http200_pages"]==len(chosen) else "ERROR_OR_UNVERIFIED"
  result["status"]="PASS_ACTUAL_IMMUTABLE_DRAFT_PUBLIC_HTML_FORMS_STATIC_SEO_AND_29_OG" if not result["content_errors"] and result["all_forms_samples"]==6 and result["all_OG_1200x630"]==29 else "HOLD_DRAFT_RUNTIME_QA"
 except Exception as exc:
  result["content_errors"].append({"fatal":type(exc).__name__+":"+str(exc)[:200]})
  result["status"]="HOLD_DRAFT_RUNTIME_QA"
 Path(a.report).parent.mkdir(parents=True,exist_ok=True)
 Path(a.report).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("SHARDED_IMMUTABLE_DRAFT_HTTP_GET_ONLY_QA",json.dumps(result,ensure_ascii=False),flush=True)
 return 0 if result["status"].startswith("PASS_") else 1
if __name__=="__main__":sys.exit(main())
