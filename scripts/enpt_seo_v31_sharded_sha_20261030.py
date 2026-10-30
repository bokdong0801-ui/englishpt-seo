#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only signed V3.1 SEO A shard QA: no Netlify POST, no publishing.
Each shard checks EXACT signed original bytes before modifying SEO HEAD.
"""
from __future__ import annotations
import argparse,concurrent.futures,gzip,hashlib,json,os,pathlib,sys,threading,time
import urllib.error,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from enpt_seo_title_policy_a_v1 import hub_title,course_title,station_hub_description,COURSE_TITLES
from enpt_seo_v31_shard_minimal_patch_20261030 import patch
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
PUB="6adafef5f2c6d196833683db"
V31="6ae06963f085b33a5ee903eb"
def sha(b):return hashlib.sha1(b).hexdigest()
def safe_get(payload,expected):
    token=os.environ.get("NETLIFY_AUTH_TOKEN","")
    sites=[
      ("published",f"https://{PUB}--englishpt-seo.netlify.app{payload}",False),
      ("draft",f"https://{V31}--englishpt-seo.netlify.app{payload}",False)
    ]
    if len(token)>20:
        sites.append(("draft_raw_api",
            f"https://api.netlify.com/api/v1/deploys/{V31}/files{payload}",True))
    evidence=[]
    for round_no in range(2):
        for label,url,is_api in sites:
            h={"Accept":"application/vnd.bitballoon.v1.raw" if is_api else "*/*",
               "User-Agent":"ENPT-SHA-20261030-READONLY-SHARD"}
            if is_api:h["Authorization"]="Bearer "+token
            try:
                q=urllib.request.Request(url,headers=h,method="GET")
                with urllib.request.urlopen(q,timeout=13) as r:
                    if r.status!=200:raise RuntimeError("HTTP_"+str(r.status))
                    body=r.read(700000)
                digest=sha(body)
                if digest==expected:
                    return body,{"source":label,"retry_count":round_no,"fallback":len(evidence)>0}
                evidence.append(f"{label}:MISMATCH:{digest}:{len(body)}")
            except urllib.error.HTTPError as e:
                evidence.append(f"{label}:HTTP_{e.code}")
            except Exception as e:
                evidence.append(f"{label}:{type(e).__name__}:{str(e)[:65]}")
        if round_no==0:time.sleep(1)
    raise RuntimeError("SIGNED_SHA_UNRECOVERABLE:"+payload+":expected="+expected+
                       ":observed="+str(evidence[-6:])[:470])

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--shard",type=int,required=True)
    p.add_argument("--total",type=int,default=16)
    p.add_argument("--workers",type=int,default=4)
    a=p.parse_args()
    if a.total!=16 or a.shard<0 or a.shard>=a.total:raise ValueError("SHARD_RANGE")
    out=ROOT/"seo-v31-sharded"/f"shard-{a.shard:02d}"
    out.mkdir(parents=True,exist_ok=True)
    def readgz(path):
        with gzip.open(path,"rt",encoding="utf8") as f:return json.load(f)
    old=readgz(ROOT/"v3-1-patch-evidence/V3_1_202786_CANDIDATE_FILES_SHA1.json.gz")
    signed=readgz(ROOT/"signed-qa-map/NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz")["original_public_html_to_data_payload"]
    stations=json.loads((ROOT/"data/stations.json").read_text(encoding="utf8"))["stations"]
    if len(old)!=202786 or len(stations)!=911 or len(COURSE_TITLES)!=23:raise ValueError("BASELINE_COUNT_DRIFT")
    all_targets=[]; seen=set()
    for station in stations:
        for intent in [None]+list(COURSE_TITLES):
            route="station-"+station["slug"]+("-"+intent if intent else "")+".html"
            entry=signed.get(route)
            if entry is None:raise ValueError("UNSIGNED_ROUTE:"+route)
            target="/"+entry["to"].lstrip("/")
            if target in seen or target not in old:raise ValueError("PAYLOAD_DUPLICATE_OR_MISSING:"+target)
            seen.add(target)
            title=hub_title(station["name"]) if intent is None else course_title(station["name"],intent)
            description=station_hub_description(station["name"]) if intent is None else None
            all_targets.append((route,target,old[target],title,description))
    if len(all_targets)!=21864 or len(seen)!=21864:raise ValueError("FULL_TARGET_COVERAGE")
    shard=[x for i,x in enumerate(all_targets) if i%a.total==a.shard]
    lock=threading.Lock()
    progress={"done":0,"failed":0,"fallback":0}
    def work(t):
        route,target,digest,title,desc=t
        raw,src=safe_get(target,digest)
        if not raw.lstrip().lower().startswith(b"<!doctype html"):
            raise ValueError("NON_HTML_SOURCE:"+route)
        new,before,after=patch(raw.decode("utf8","strict"),title,desc)
        content=new.encode("utf8")
        h=sha(content)
        if h==digest:raise ValueError("NO_HEAD_CHANGE:"+route)
        path=out/"delta"/target.lstrip("/")
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(content)
        if sha(path.read_bytes())!=h:raise ValueError("LOCAL_WRITE_SHA:"+route)
        with lock:
            progress["done"]+=1
            progress["fallback"]+=int(src["fallback"])
            if progress["done"]%250==0:print("ENPT_SHA_SHARD_PROGRESS",a.shard,progress["done"],len(shard),flush=True)
        return {"route":route,"path":target,"before_sha1":digest,"after_sha1":h,"source":src["source"],
                "fallback":src["fallback"],"title":title}
    successes=[];failures=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        jobs={pool.submit(work,t):t[0] for t in shard}
        for future in concurrent.futures.as_completed(jobs):
            try:successes.append(future.result())
            except Exception as e:
                failures.append({"route":jobs[future],"error":str(e)[:750]})
                print("ENPT_SHA_SHARD_ERROR",a.shard,jobs[future],str(e)[:450],flush=True)
    result={"status":"PASS" if len(successes)==len(shard) and not failures else "HOLD",
            "shard":a.shard,"total_shards":a.total,"expected":len(shard),"passed":len(successes),
            "failures":failures[:100],"fallbacks":progress["fallback"],"global_expected":21864,
            "manifest_paths":len(old),"published_posts":0,"draft_posts":0,"form_posts":0}
    (out/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
    (out/"files.json").write_text(json.dumps(sorted(successes,key=lambda x:x["route"]),ensure_ascii=False),encoding="utf8")
    print("ENPT_SHA_SHARD_SUMMARY",json.dumps(result,ensure_ascii=False),flush=True)
    if result["status"]!="PASS":sys.exit(1)
if __name__=="__main__":main()
