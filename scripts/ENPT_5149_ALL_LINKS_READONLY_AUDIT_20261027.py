#!/usr/bin/env python3
"""Read-only production audit of all 5,149 frozen ENGLISH PT neighborhood link targets.
Requests are GET only; may generate network traffic but cannot publish, update or submit forms.
"""
from __future__ import annotations
import collections,concurrent.futures,csv,datetime,gzip,hashlib,html.parser,json,os,pathlib,re,threading,time,urllib.error,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"region-link-audit-20261027"
SITE=ROOT/"region-review-site"
PROD="https://englishpt.kr"
FROZEN_SHA="3fe392df02bf76e0a6f84ef220433f0b901f97ae09a0a091269deeb2eaf8e9f0"
N=5149
MAX_WORKERS=12
stop=threading.Event()
class Head(html.parser.HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True)
  self.title=[];self.h1=[];self.capture=None;self.can=[];self.robots=[];self.description=[];self.text=[];self.form=False;self.metaOg=[];self.lang=""
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=="html":self.lang=d.get("lang","")
  if tag=="title":self.capture="title"
  if tag=="h1":self.capture="h1"
  if tag=="form" and d.get("name")=="englishpt-consultation":self.form=True
  if tag=="meta":
   if d.get("name","").lower()=="robots":self.robots.append(d.get("content",""))
   if d.get("name","").lower()=="description":self.description.append(d.get("content",""))
   if d.get("property","").lower()=="og:title":self.metaOg.append(d.get("content",""))
  if tag=="link" and "canonical" in d.get("rel","").lower():self.can.append(d.get("href",""))
 def handle_endtag(self,tag):
  if tag==self.capture:self.capture=None
 def handle_data(self,s):
  if self.capture=="title":self.title.append(s)
  if self.capture=="h1":self.h1.append(s)
  if len(self.text)<200:self.text.append(s)
def load():
 paths=[ROOT/"stage5-input"/f"production_locality_rows_5149_v1.part{i:03d}.jsonl" for i in range(1,7)]
 raw=b"".join(p.read_bytes() for p in paths)
 assert hashlib.sha256(raw).hexdigest()==FROZEN_SHA,"HOLD_REGION_SOURCE_CHANGED"
 rows=[json.loads(l) for l in raw.decode("utf8").splitlines() if l.strip()]
 assert len(rows)==N and len({r["region_slug"] for r in rows})==N
 return rows
def local_link_check(rows):
 source={}
 for p in SITE.glob("regions/*.html"):
  s=p.read_text("utf8")
  for url,slug in re.findall(r'href="(https://englishpt.kr/[a-z0-9-]+\.html)" data-locality="([a-z0-9-]+)"',s):
   source.setdefault(url,[]).append((str(p.relative_to(SITE)),slug))
 expected={PROD+r["hub_url"] for r in rows}
 found=set(source)
 duplicates={u:v for u,v in source.items() if len(v)!=1}
 mismatch=[]
 for r in rows:
  u=PROD+r["hub_url"]
  if source.get(u,[("",None)])[0][1]!=r["region_slug"]:mismatch.append(u)
 return {"static_expected":len(expected),"static_found":len(found),"missing":sorted(expected-found),"unexpected":sorted(found-expected),"duplicate_links":duplicates,"slug_mismatch":mismatch}
def fetch(row):
 url=PROD+row["hub_url"]
 fields={"url":url,"sido":row["sido"],"jurisdiction":row["jurisdiction_full"],"dong":row["dong_name"],"slug":row["region_slug"],"entity_mix":row.get("entity_mix",""),"http_status":"","final_url":"","error":"","title":"","h1":"","canonical":"","robots_meta":"","x_robots":"","town_match":"","district_match":"","self_canonical":"","soft404":"","form_marker":"","class":"","content_type":"","bytes_read":0}
 if stop.is_set():fields["class"]="SKIPPED_RATE_LIMIT";return fields
 for attempt in range(2):
  try:
   req=urllib.request.Request(url,method="GET",headers={"User-Agent":"ENGLISHPT-SAFE-SEO-READONLY-AUDIT/1.0 (+audit of owned site)","Accept":"text/html","Accept-Encoding":"identity","Range":"bytes=0-100000"})
   with urllib.request.urlopen(req,timeout=22) as response:
    code=response.status;final=response.geturl();headers=response.headers;body=response.read(120000)
   fields.update(http_status=code,final_url=final,content_type=headers.get("Content-Type",""),x_robots=headers.get("X-Robots-Tag",""),bytes_read=len(body))
   if code==429:
    stop.set();fields["class"]="RATE_LIMIT";return fields
   if code>=500:
    fields["class"]="HTTP_5XX";return fields
   if code not in (200,206):
    fields["class"]="HTTP_UNEXPECTED";return fields
   source=body.decode("utf8","replace")
   p=Head();p.feed(source)
   title=" ".join(p.title).strip()
   h1=" ".join(p.h1).strip()
   meta=" ".join(p.description).strip()
   content=" ".join([title,h1,meta]+p.metaOg+[" ".join(p.text[:80])])
   # Exact substring plus variant spaces to distinguish identical names in different jurisdictions.
   district=row["jurisdiction_full"].removeprefix(row["sido"]).strip()
   small=(district.split()[-1] if district else row["sido"])
   canonical=p.can[0] if p.can else ""
   fields.update(title=title[:200],h1=h1[:200],canonical=canonical[:250],robots_meta="|".join(p.robots)[:100],town_match=int(row["dong_name"] in content),district_match=int(small in content),self_canonical=int(canonical==url),form_marker=int(p.form))
   if "text/html" not in fields["content_type"].lower():fields["class"]="NON_HTML"
   elif final.rstrip("/")!=url.rstrip("/"):fields["class"]="UNEXPECTED_REDIRECT"
   elif re.search(r"찾을\s*수\s*없|page\s*not\s*found|404\s*not\s*found",title+" "+h1,re.I):fields["soft404"]=1;fields["class"]="SOFT_404"
   elif not fields["town_match"]:fields["class"]="REGION_NAME_MISMATCH"
   elif not fields["district_match"]:fields["class"]="DISTRICT_REVIEW"
   elif not canonical:fields["class"]="MISSING_CANONICAL"
   elif canonical!=url:fields["class"]="CANONICAL_NOT_SELF"
   else:fields["class"]="PASS"
   return fields
  except urllib.error.HTTPError as e:
   fields["http_status"]=e.code;fields["final_url"]=e.geturl();fields["error"]=str(e)[:130]
   if e.code==429:stop.set()
   fields["class"]="HTTP_404" if e.code==404 else "RATE_LIMIT" if e.code==429 else "HTTP_5XX" if e.code>=500 else "HTTP_OTHER"
   return fields
  except (TimeoutError, OSError, urllib.error.URLError) as e:
   fields["error"]=type(e).__name__+":"+str(e)[:160]
   if attempt==0:time.sleep(.25);continue
   fields["class"]="NETWORK_ERROR";return fields
  except Exception as e:
   fields["error"]=type(e).__name__+":"+str(e)[:160]
   fields["class"]="PARSE_ERROR";return fields
 fields["class"]="UNKNOWN";return fields
def main():
 rows=load()
 OUT.mkdir(exist_ok=True)
 static=local_link_check(rows)
 assert len(static["missing"])==len(static["unexpected"])==len(static["duplicate_links"])==len(static["slug_mismatch"])==0,("HOLD_STATIC_LINK_MISMATCH",{k:len(v) if isinstance(v,(list,dict)) else v for k,v in static.items()})
 print("ENPT_5149_EXACT_STATIC_HUB_LINKS_PASS",N,flush=True)
 started=time.time()
 result=[]
 # Concurrent GET only. At most 12 in flight. Any 429 triggers a global safety stop.
 with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
  futures=[pool.submit(fetch,row) for row in rows]
  for n,f in enumerate(concurrent.futures.as_completed(futures),1):
   result.append(f.result())
   if n%500==0:print("ENPT_5149_PROGRESS",n,collections.Counter(x["class"] for x in result).most_common(8),"elapsed_s",round(time.time()-started),flush=True)
 result.sort(key=lambda r:r["url"])
 assert len(result)==N and len({r["url"] for r in result})==N
 fields=list(result[0].keys())
 with (OUT/"ENPT_ALL_5149_LINK_TARGET_HTTP_SEO.csv").open("w",encoding="utf-8-sig",newline="") as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(result)
 for name,subset in {
  "ENPT_404_5XX_SOFT404.csv":[r for r in result if r["class"] in ("HTTP_404","HTTP_5XX","SOFT_404","HTTP_OTHER")],
  "ENPT_WRONG_REGION_AND_CANONICAL.csv":[r for r in result if r["class"] in ("REGION_NAME_MISMATCH","DISTRICT_REVIEW","CANONICAL_NOT_SELF","MISSING_CANONICAL","UNEXPECTED_REDIRECT")],
  "ENPT_NETWORK_INCOMPLETE.csv":[r for r in result if r["class"] in ("NETWORK_ERROR","RATE_LIMIT","SKIPPED_RATE_LIMIT","PARSE_ERROR")]
 }.items():
  with (OUT/name).open("w",encoding="utf-8-sig",newline="") as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(subset)
 counts=dict(sorted(collections.Counter(r["class"] for r in result).items()))
 codes=dict(sorted(collections.Counter(str(r["http_status"]) for r in result).items()))
 changed=[r for r in result if r["class"]!="PASS"]
 report={"audit_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"source":"published custom domain "+PROD,"source_region_rows":N,"static_link_check":{k:len(v) if isinstance(v,(list,dict)) else v for k,v in static.items()},"actual_http_checked":sum(1 for r in result if r["http_status"]!=""),"http_status_distribution":codes,"class_distribution":counts,"town_name_in_page":sum(int(r["town_match"] or 0) for r in result),"district_name_in_page":sum(int(r["district_match"] or 0) for r in result),"self_canonical":sum(int(r["self_canonical"] or 0) for r in result),"noindex_in_html":sum("noindex" in r["robots_meta"].lower() for r in result),"error_examples":[{"url":r["url"],"class":r["class"],"status":r["http_status"],"title":r["title"][:100],"canonical":r["canonical"][:100]} for r in changed[:45]],"rate_limit_or_network_incomplete":sum(v for k,v in counts.items() if k in ("RATE_LIMIT","SKIPPED_RATE_LIMIT","NETWORK_ERROR")),"elapsed_seconds":round(time.time()-started,1),"production_mutations":0,"form_submissions":0}
 (OUT/"ENPT_5149_SUMMARY.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),"utf8")
 md=["# ENGLISH PT 5,149 localities full HTTP audit","",f"Verified {report['actual_http_checked']:,} / {N:,} attempted HTTP GET endpoints; elapsed {report['elapsed_seconds']} seconds.","","## Results",f"- Static link mapping: {report['static_link_check']}","- HTTP status: "+json.dumps(codes,ensure_ascii=False),"- Classification: "+json.dumps(counts,ensure_ascii=False),f"- Same-page canonical: {report['self_canonical']:,}",f"- HTML noindex: {report['noindex_in_html']:,}","", "## Follow-up","Any NETWORK_ERROR or RATE_LIMIT rows must be retried before labeling as 404. DISTRICT_REVIEW flags are heuristic and must be manually reviewed.","", "No Production changes, no form submissions."]
 (OUT/"ENPT_5149_REPORT.md").write_text("\n".join(md),"utf8")
 print("ENPT_5149_AUDIT_SUMMARY",json.dumps({k:v for k,v in report.items() if k not in ("error_examples",)},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
