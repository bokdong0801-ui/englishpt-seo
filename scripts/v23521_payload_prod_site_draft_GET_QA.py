#!/usr/bin/env python3
"""Immutable production-site nonpublished Draft: GET-only 158571 route mixed-index QA.
Never sends Forms or changes Netlify settings. Must NOT be used as Production publication.
"""
import argparse,gzip,json,hashlib,re,urllib.parse,urllib.request,urllib.error,pathlib,datetime,struct
TUTORS=["gyeongnam-milyang-naeidong-elem-tutor.html","gyeongnam-milyang-naeidong-mid-tutor.html",
"gyeongnam-milyang-naeidong-high-tutor.html","seoul-jongno-sajikdong-elem-tutor.html",
"seoul-jongno-sajikdong-mid-tutor.html","seoul-jongno-sajikdong-high-tutor.html"]
OG=("beginner toeic ielts toefl opic tos duolingo elementary middle high student worker college jobseeker housewife stations region academy tutor conversation exam courses englishpt reading writing international phone video general").split()
def get(u,cap=512000):
 req=urllib.request.Request(u,headers={"User-Agent":"ENGLISHPT-20261019-READ-ONLY-PreProduction-Draft"},method="GET")
 with urllib.request.urlopen(req,timeout=30) as resp:return resp.status,dict(resp.headers),resp.read(cap),resp.geturl()
def main():
 cli=argparse.ArgumentParser()
 cli.add_argument("--url",required=True);cli.add_argument("--manifest",required=True);cli.add_argument("--output",required=True)
 a=cli.parse_args();url=a.url.rstrip("/")
 p=urllib.parse.urlsplit(url)
 if not (p.scheme=="https" and p.hostname and p.hostname.endswith(".netlify.app") and p.hostname!="englishpt.kr"):
  raise ValueError("Only Netlify immutable Draft URL allowed")
 with gzip.open(a.manifest,"rt",encoding="utf8") as f:mp=json.load(f)["original_public_html_to_data_payload"]
 yes=sorted(x for x,v in mp.items() if not v["noindex"])
 no=sorted(x for x,v in mp.items() if v["noindex"])
 if len(yes)!=21964 or len(no)!=136607:raise ValueError("Unexpected candidate indexing distribution")
 sampled=list(dict.fromkeys([yes[i*len(yes)//12] for i in range(12)]+
   [no[i*len(no)//12] for i in range(12)]+TUTORS))
 r={"status":"HOLD","sample_count":len(sampled),"sample_indexable":0,"sample_noindex":0,
    "sample_Forms":0,"OG29_verified":0,"public_global_header_noindex_on_Draft":[],"GET_requests":0,
    "issues":[],"Production_changed":False,"Netlify_POST":0,"Form_submissions":0,
    "tested_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"draft_url":url}
 for name in sampled:
  try:
   status,headers,body,_=get(url+"/"+urllib.parse.quote(name,safe=""))
   r["GET_requests"]+=1
   if status!=200 or "text/html" not in headers.get("Content-Type","").lower():
    raise ValueError("HTTP non200 or bad HTML content-type")
   text=body.decode("utf8",errors="replace")
   canonical=re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"',text,re.I)
   if not canonical or canonical.group(1)!="https://englishpt.kr/"+name:
    raise ValueError("Canonical mismatch")
   robots=re.search(r'<meta\s+name="robots"\s+content="([^"]+)"',text,re.I)
   if not robots:raise ValueError("No page robots meta")
   actual_noindex="noindex" in robots.group(1).lower()
   if actual_noindex!=bool(mp[name]["noindex"]):raise ValueError("Page robots meta differs")
   if actual_noindex:r["sample_noindex"]+=1
   else:r["sample_indexable"]+=1
   if "noindex" in headers.get("X-Robots-Tag","").lower():
    r["public_global_header_noindex_on_Draft"].append(name)
   if name in TUTORS:
    if not all(t in text for t in ['name="englishpt-consultation"','name="form-name"','name="requestType"','name="subject"']):
      raise ValueError("Static Tutor Form markup invalid")
    r["sample_Forms"]+=1
  except Exception as e:r["issues"].append({"route":name,"problem":type(e).__name__+": "+str(e)[:120]})
 for path in ("/robots.txt","/sitemap-index.xml","/pilot.js"):
  try:
   status,headers,b,_=get(url+path,512000);r["GET_requests"]+=1
   if status!=200:raise ValueError("Not HTTP 200")
   if path=="/robots.txt":
    if b"User-agent:" not in b or re.search(rb"(?im)^\s*Disallow:\s*/\s*$",b):
     raise ValueError("Production robots contains global disallow")
   if path=="/sitemap-index.xml" and b"sitemapindex" not in b:raise ValueError("XML sitemap invalid")
   if path=="/pilot.js":
    if hashlib.sha256(b).hexdigest()!="d604994a74352a81978002fd6f6286c7d0f4f4c99278745bbf6dad1abce29ede":
     raise ValueError("Wrong JS")
  except Exception as e:r["issues"].append({"route":path,"problem":str(e)[:120]})
 for stem in OG:
  path="/assets/images/og-pages/"+stem+".png"
  try:
   status,headers,b,_=get(url+path,24);r["GET_requests"]+=1
   if status!=200 or len(b)<24 or b[:8]!=bytes.fromhex("89504e470d0a1a0a") or struct.unpack(">II",b[16:24])!=(1200,630):
    raise ValueError("Broken OG PNG 1200x630")
   r["OG29_verified"]+=1
  except Exception as e:r["issues"].append({"route":path,"problem":str(e)[:120]})
 # Netlify may inject noindex on Deploy Previews. Do not falsely claim it's proof of live indexability.
 r["preview_header_protection"]="draft_noindex_observed" if r["public_global_header_noindex_on_Draft"] else "NO_DRAFT_GLOBAL_NOINDEX_OBSERVED"
 r["status"]="PASS_DRAFT_REAL_MIXED_ROBOTS_CANONICAL_EDGE_FORMS_STATIC_OG" if (
   not r["issues"] and r["sample_Forms"]==6 and r["OG29_verified"]==29 and
   r["sample_indexable"]>=12 and r["sample_noindex"]>=12) else "HOLD_DRAFT_GET_QA"
 output=pathlib.Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
 output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("ACTUAL_PRODUCTION_FORMAT_DRAFT_GET_QA",json.dumps({k:v for k,v in r.items() if k not in ("public_global_header_noindex_on_Draft",)},ensure_ascii=False),flush=True)
 return 0 if r["status"].startswith("PASS_") else 1
if __name__=="__main__":raise SystemExit(main())
