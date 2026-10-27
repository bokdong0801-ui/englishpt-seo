#!/usr/bin/env python3
"""GET-only, bounded-live verification of 5,149 course links of one specified type on V3 Draft.
Runs as matrix seven types (36,043). No form submissions or production modifications.
Each row grounded in signed V2 link CSV. Distinguishes HTTP errors, regional/SEO issues, network gaps.
"""
from __future__ import annotations
import concurrent.futures,collections,csv,datetime,html.parser,json,os,pathlib,re,threading,time,urllib.error,urllib.request
from urllib.parse import urlsplit
COURSES=("elem-tutor","elem-conv","mid-tutor","mid-conv","high-tutor","high-conv","worker-english-conv-academy")
BASE="https://review-enpt-v3-fullsite-20261027--englishpt-seo.netlify.app"
PROD="https://englishpt.kr"
COURSE=os.environ["ENPT_COURSE"]
assert COURSE in COURSES
OUT=pathlib.Path("v3-36043-http-results")/COURSE
OUT.mkdir(parents=True,exist_ok=True)
INPUT=pathlib.Path("v2-evidence/ENPT_V2_5149_X_7_REAL_COURSE_LINKS.csv")
assert INPUT.is_file(),"HOLD_NO_SIGNED_V2_LINK_TABLE"
allrows=list(csv.DictReader(INPUT.open(encoding="utf-8-sig")))
assert len(allrows)==36043 and len({r["target_url"] for r in allrows})==36043
rows=[r for r in allrows if r["course"]==COURSE]
assert len(rows)==5149 and len({r["region_slug"] for r in rows})==5149
class Meta(html.parser.HTMLParser):
 def __init__(self):super().__init__();self.canonical=[];self.robots=[];self.title=[];self.h1=[];self.capture=None
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=="link" and "canonical" in d.get("rel","").lower():self.canonical.append(d.get("href",""))
  if tag=="meta" and d.get("name","").lower()=="robots":self.robots.append(d.get("content",""))
  if tag=="title":self.capture="title"
  if tag=="h1":self.capture="h1"
 def handle_endtag(self,tag):
  if tag==self.capture:self.capture=None
 def handle_data(self,t):
  if self.capture=="title":self.title.append(t)
  if self.capture=="h1":self.h1.append(t)
halt=threading.Event()
def visit(r):
 path=urlsplit(r["target_url"]).path
 url=BASE+path
 original=r["target_url"]
 answer={"course":COURSE,"region_slug":r["region_slug"],"region_full":r["region_full"],"preview_url":url,"production_url":original,"http":"","final_url":"","canonical":"","robots_meta":"","title":"","h1":"","region_text_match":"","class":"","error":""}
 if halt.is_set():answer["class"]="SKIPPED_ON_RATE_LIMIT";return answer
 for n in range(2):
  try:
   request=urllib.request.Request(url,method="GET",headers={"User-Agent":"ENPT-OWNER-V3-READONLY-LINK-QA/20261027","Accept":"text/html","Accept-Encoding":"identity"})
   with urllib.request.urlopen(request,timeout=20) as response:
    status=response.status;final=response.geturl();ctype=response.headers.get("Content-Type","");body=response.read(90000)
   answer["http"]=status;answer["final_url"]=final
   if status!=200:answer["class"]="HTTP_OTHER";return answer
   if not ctype.lower().startswith("text/html"):answer["class"]="NOT_HTML";return answer
   s=body.decode("utf8","replace");meta=Meta();meta.feed(s)
   answer.update(canonical=meta.canonical[0] if meta.canonical else "",robots_meta="|".join(meta.robots),title=" ".join(meta.title)[:200],h1=" ".join(meta.h1)[:200])
   # Locality full labels may have spaces and different conventions in the text;
   # single dong portion from region_full is stable and more robust.
   dong=r["region_full"].split()[-1]
   answer["region_text_match"]=int(dong in s)
   if final.rstrip("/")!=url.rstrip("/"):answer["class"]="UNEXPECTED_REDIRECT"
   elif answer["canonical"]!=original:answer["class"]="CANONICAL_REVIEW"
   elif not answer["region_text_match"]:answer["class"]="REGION_TEXT_REVIEW"
   elif re.search(r"찾을\s*수\s*없|not found|404",answer["title"]+" "+answer["h1"],re.I):answer["class"]="SOFT404"
   else:answer["class"]="PASS"
   return answer
  except urllib.error.HTTPError as e:
   answer["http"]=e.code;answer["final_url"]=e.geturl()
   answer["class"]="HTTP_404" if e.code==404 else "HTTP_429" if e.code==429 else "HTTP_5XX" if e.code>=500 else "HTTP_OTHER"
   answer["error"]=str(e)[:140]
   if e.code==429:halt.set()
   return answer
  except Exception as e:
   answer["error"]=type(e).__name__+":"+str(e)[:170]
   if n==0:
    time.sleep(.25)
    continue
   answer["class"]="NETWORK_ERROR";return answer
 answer["class"]="UNKNOWN";return answer
begin=time.monotonic();responses=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
 for i,result in enumerate(pool.map(visit,rows),1):
  responses.append(result)
  if i%500==0:
   print("ENPT_V3_LINK_PROGRESS",COURSE,i,"of",len(rows),"classes",dict(collections.Counter(x["class"] for x in responses)),flush=True)
responses.sort(key=lambda r:r["preview_url"])
assert len(responses)==5149 and len({r["preview_url"] for r in responses})==5149
with (OUT/"RESULTS_5149.csv").open("w",newline="",encoding="utf-8-sig") as f:
 wr=csv.DictWriter(f,fieldnames=list(responses[0]));wr.writeheader();wr.writerows(responses)
issues=[r for r in responses if r["class"]!="PASS"]
with (OUT/"ISSUES_ONLY.csv").open("w",newline="",encoding="utf-8-sig") as f:
 wr=csv.DictWriter(f,fieldnames=list(responses[0]));wr.writeheader();wr.writerows(issues)
summary={"course":COURSE,"status":"PASS_5149_V3_LIVE_DESTINATIONS" if not issues else "REVIEW_LIVE_ISSUES",
"attempted":5149,"http_replied":sum(r["http"]!="" for r in responses),"http200":sum(r["http"]==200 for r in responses),
"404_count":sum(r["http"]==404 for r in responses),"unconfirmed":sum(r["http"]=="" for r in responses),
"pass":len(responses)-len(issues),"class_counts":dict(sorted(collections.Counter(r["class"] for r in responses).items())),
"elapsed_seconds":round(time.monotonic()-begin,1),"form_posts":0,"production_changes":0,"first_issues":[{k:v for k,v in r.items() if k in ("preview_url","class","http","canonical","error")} for r in issues[:15]]}
(OUT/"SUMMARY.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),"utf8")
print("ENPT_V3_36043_COURSE_RESULT",json.dumps(summary,ensure_ascii=False)[:6000],flush=True)
