#!/usr/bin/env python3
"""Reverify only 31 preliminary V3 scan anomalies with <=2 GET concurrency. No Production writes.
"""
import concurrent.futures,csv,datetime,html.parser,json,os,pathlib,re,time,urllib.error,urllib.request
OUT=pathlib.Path("v3-anomaly-retry");OUT.mkdir(exist_ok=True)
paths=[pathlib.Path("anomalies/elem/ISSUES_ONLY.csv"),pathlib.Path("anomalies/worker/ISSUES_ONLY.csv")]
rows=[]
for p in paths:
 assert p.exists(),("MISSING_INPUT",str(p))
 rows+=list(csv.DictReader(p.open(encoding="utf-8-sig")))
assert len(rows)==31,(len(rows),"EXPECTED_31")
class Head(html.parser.HTMLParser):
 def __init__(self):super().__init__();self.title=[];self.h1=[];self.canon=[];self.cap=""
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=="title":self.cap="title"
  if tag=="h1":self.cap="h1"
  if tag=="link" and "canonical" in d.get("rel","").lower():self.canon.append(d.get("href",""))
 def handle_endtag(self,tag):
  if tag==self.cap:self.cap=""
 def handle_data(self,s):
  if self.cap=="title":self.title.append(s)
  if self.cap=="h1":self.h1.append(s)
def check(row):
 dong=row["region_full"].removesuffix(" 지역 영어 안내").split()[-1]
 for round in range(3):
  try:
   req=urllib.request.Request(row["preview_url"],method="GET",headers={"User-Agent":"ENPT-OWNER-V3-RETRY-31-GETONLY","Accept-Encoding":"identity"})
   with urllib.request.urlopen(req,timeout=25) as r:
    stat=r.status;final=r.geturl();content=r.read(90000).decode("utf8","replace")
   p=Head();p.feed(content);title=" ".join(p.title);h1=" ".join(p.h1)
   can=p.canon[0] if p.canon else ""
   passed=stat==200 and final==row["preview_url"] and can==row["production_url"] and dong in (title+" "+h1)
   return {"preview_url":row["preview_url"],"production_url":row["production_url"],"original_issue":row["class"],"http":stat,"final_url":final,"canonical":can,"dong":dong,"title":title[:170],"h1":h1[:170],"status":"PASS_RECHECK" if passed else "HOLD_SEO_OR_REGION_REVIEW","attempt":round+1,"error":""}
  except urllib.error.HTTPError as ex:
   err=f"HTTP_{ex.code}"
   if ex.code==429:return {"preview_url":row["preview_url"],"original_issue":row["class"],"http":ex.code,"status":"HOLD_RATE_LIMIT","attempt":round+1,"error":err}
  except Exception as ex:err=type(ex).__name__+":"+str(ex)[:130]
  if round<2:time.sleep(1.2*(round+1))
 return {"preview_url":row["preview_url"],"production_url":row["production_url"],"original_issue":row["class"],"http":"","status":"UNCONFIRMED_AFTER_RETRY","attempt":3,"error":err}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(check,rows))
result={"attempted":len(results),"passed":sum(x["status"]=="PASS_RECHECK" for x in results),
 "still_problematic":[r for r in results if r["status"]!="PASS_RECHECK"],
 "status":"PASS_ALL_31_RETEST" if all(x["status"]=="PASS_RECHECK" for x in results) else "HOLD_31_RETEST_NOT_ALL",
 "published_writes":0,"form_post_count":0}
(OUT/"RETRY_31_RESULT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),"utf8")
with (OUT/"RETRY_31_ROWS.csv").open("w",encoding="utf-8-sig",newline="") as f:
 keys=list(dict.fromkeys(k for r in results for k in r))
 w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(results)
print("ENPT_V3_31_RETRY_RESULT",json.dumps(result,ensure_ascii=False)[:5500],flush=True)
