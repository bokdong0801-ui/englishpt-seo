#!/usr/bin/env python3
"""GET-only production validation: one known-present worker course per 5149 areas,
plus 7 different course intents for a fixed representative sample of province rows.
No form submission, no deploy. Preserve network errors distinct from 404.
"""
import concurrent.futures,collections,csv,hashlib,json,pathlib,threading,time,urllib.request,urllib.error
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=pathlib.Path("v2-region-live-http-qa");OUT.mkdir(exist_ok=True)
PARTS=[ROOT/"stage5-input"/f"production_locality_rows_5149_v1.part{i:03d}.jsonl" for i in range(1,7)]
RAW=b"".join(p.read_bytes() for p in PARTS)
assert hashlib.sha256(RAW).hexdigest()=="3fe392df02bf76e0a6f84ef220433f0b901f97ae09a0a091269deeb2eaf8e9f0"
rows=[json.loads(line) for line in RAW.decode().splitlines() if line.strip()]
assert len(rows)==5149
chosen={}
for r in rows:chosen.setdefault(r["sido"],r)
sample_courses=("elem-tutor","elem-conv","mid-tutor","mid-conv","high-tutor","high-conv","worker-english-conv-academy")
urls={}
for r in rows:
 u="https://englishpt.kr/"+r["region_slug"]+"-worker-english-conv-academy.html"
 urls[u]={"sido":r["sido"],"dong":r["dong_name"],"course":"worker-english-conv-academy"}
for r in chosen.values():
 for c in sample_courses:
  u="https://englishpt.kr/"+r["region_slug"]+"-"+c+".html"
  urls[u]={"sido":r["sido"],"dong":r["dong_name"],"course":c}
def one(pair):
 url,r=pair
 for attempt in range(3):
  try:
   req=urllib.request.Request(url,method="GET",headers={"User-Agent":"ENPT-Owner-GETONLY-V2-Check/1.0","Accept":"text/html"})
   with urllib.request.urlopen(req,timeout=15) as res:
    body=res.read(11000).decode("utf8","replace")
    return {"url":url,**r,"http":res.status,"final_url":res.geturl(),"dong_visible":int(r["dong"] in body),"canonical_self":int(url in body),"error":""}
  except urllib.error.HTTPError as e:return {"url":url,**r,"http":e.code,"final_url":e.geturl(),"dong_visible":"","canonical_self":"","error":""}
  except Exception as e:
   err=type(e).__name__+":"+str(e)[:120]
   if attempt!=2:time.sleep(.3*(attempt+1))
 return {"url":url,**r,"http":"","final_url":"","dong_visible":"","canonical_self":"","error":err}
st=time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
 result=list(pool.map(one,urls.items()))
result.sort(key=lambda r:r["url"])
assert len(result)==len(urls)
counts=dict(sorted(collections.Counter(str(x["http"]) for x in result).items()))
valid=sum(x["http"]==200 and x["final_url"]==x["url"] for x in result)
faults=[x for x in result if x["http"]!=200 or x["final_url"]!=x["url"]]
with (OUT/"V2_5149_WORKER_AND_7_INTENT_LIVE_HTTP.csv").open("w",newline="",encoding="utf-8-sig") as f:
 w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
with (OUT/"V2_NON200_REVIEW.csv").open("w",newline="",encoding="utf-8-sig") as f:
 w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(faults)
summary={"status":"PASS_ALL_REQUESTS_HTTP_200" if not faults else "HOLD_NON200_OR_NETWORK","frozen_localities":5149,"sido_samples":len(chosen),"requested_unique_course_urls":len(result),"verified_http200_canonical_route":valid,"http_distribution":counts,"bad_or_unverified":len(faults),"errors_examples":faults[:20],"elapsed_seconds":round(time.time()-st,1),"prod_mutations":0,"forms_submitted":0}
(OUT/"V2_5149_WORKER_GET_QA_SUMMARY.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),"utf8")
print("ENPT_V2_WORKER_5149_HTTP_SUMMARY",json.dumps({k:v for k,v in summary.items() if k!="errors_examples"},ensure_ascii=False),flush=True)
