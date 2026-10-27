#!/usr/bin/env python3
"""One scoped GET-only retry of the 57 V3 36043-scan anomalies from merged artifact.
Do not repeat whole 36043 traffic, never POST, verify actual 읍면동 and correct canonical.
"""
import collections,concurrent.futures,csv,datetime,html.parser,json,pathlib,time,urllib.error,urllib.request
ROOT=pathlib.Path("anomalies-final/NON_PASS_LINKS.csv")
OUT=pathlib.Path("v3-retry-57");OUT.mkdir(exist_ok=True)
assert ROOT.is_file(),"HOLD_MISSING_CERTIFIED_FULL_AUDIT"
items=list(csv.DictReader(ROOT.open(encoding="utf-8-sig")))
assert len(items)==57 and len({r["preview_url"] for r in items})==57,("HOLD_UNEXPECTED_ISSUE_COUNT",len(items))
class H(html.parser.HTMLParser):
 def __init__(self):super().__init__();self.title=[];self.h1=[];self.canon=[];self.capture=""
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=="link" and "canonical" in (d.get("rel") or "").lower():self.canon.append(d.get("href",""))
  if tag in ("title","h1"):self.capture=tag
 def handle_endtag(self,tag):
  if tag==self.capture:self.capture=""
 def handle_data(self,s):
  if self.capture=="title":self.title.append(s)
  if self.capture=="h1":self.h1.append(s)
def verify(row):
 dong=row["region_full"].removesuffix(" 지역 영어 안내").split()[-1]
 err=""
 for i in range(4):
  try:
   req=urllib.request.Request(row["preview_url"],method="GET",headers={"User-Agent":"ENPT-OWNER-RETEST-57-V3-NONPRODUCTION","Accept-Encoding":"identity"})
   with urllib.request.urlopen(req,timeout=25) as res:
    code=res.status;final=res.geturl();data=res.read(90000).decode("utf8","replace")
   p=H();p.feed(data);can=p.canon[0] if p.canon else "";title=" ".join(p.title);h1=" ".join(p.h1)
   good=(code==200 and final==row["preview_url"] and can==row["production_url"] and dong in (title+" "+h1))
   return {"preview_url":row["preview_url"],"production_url":row["production_url"],"prior_class":row["class"],"http":code,"final_url":final,"canonical":can,"dong":dong,"title":title[:170],"h1":h1[:170],"result":"PASS" if good else "HOLD_SEO_OR_ROUTE","attempt":i+1,"error":""}
  except urllib.error.HTTPError as ex:
   err=f"HTTP_{ex.code}"
   if ex.code==429:break
  except Exception as ex:err=type(ex).__name__+":"+str(ex)[:150]
  if i<3:time.sleep((i+1)*1.2)
 return {"preview_url":row["preview_url"],"production_url":row["production_url"],"prior_class":row["class"],"http":"","result":"HOLD_NETWORK_OR_HTTP","attempt":4,"error":err}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:got=list(pool.map(verify,items))
stats=dict(sorted(collections.Counter(x["result"] for x in got).items()))
report={"total_retried":len(got),"recovered":sum(x["result"]=="PASS" for x in got),"status":"PASS_ALL_57_REVERIFIED" if stats.get("PASS",0)==57 else "HOLD_UNVERIFIED",
"remaining":[x for x in got if x["result"]!="PASS"],"counts":stats,"production_modifications":0,"form_submissions":0}
(OUT/"RETRY_57_SUMMARY.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),"utf8")
with (OUT/"RETRY_57_DETAILS.csv").open("w",encoding="utf-8-sig",newline="") as f:
 fields=list(dict.fromkeys(k for r in got for k in r))
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(got)
print("ENPT_V3_RETRY_57_SUMMARY",json.dumps({k:v for k,v in report.items() if k!="remaining"},ensure_ascii=False),flush=True)
