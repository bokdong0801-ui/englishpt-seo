#!/usr/bin/env python3
"""Frozen V3.1 21,864 station-route SEO head delta. Never changes live or existing Draft.

Fetches exact immutable Published content-shard bytes (same sha in V3.1) and
edits ONLY head title, og:title, WebPage schema name, and hub description/og desc.
No full HTML regeneration. Fail closed on any sha, semantic or duplicate mismatch.
"""
from __future__ import annotations
import argparse,concurrent.futures,gzip,hashlib,html,json,os,pathlib,re,sys,threading,time,urllib.request,urllib.error
ROOT=pathlib.Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"v3-1-patch-evidence/V3_1_202786_CANDIDATE_FILES_SHA1.json.gz"
SIGNED=ROOT/"signed-qa-map/NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz"
OUT=ROOT/"seo-v31-minimal"
DIR=OUT/"delta"
PUB="6adafef5f2c6d196833683db"
SOURCE="https://"+PUB+"--englishpt-seo.netlify.app"
SITE_ID="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
V31="6ae06963f085b33a5ee903eb"
V31_TITLE="ENPT-V3-1-20261027-BYEONGMOKANDONG-7-CORRECTED-NONPUB"

def fail(s):raise RuntimeError("HOLD_SEO_V31_"+str(s))
def sha(b):return hashlib.sha1(b).hexdigest()
def metadata(raw):
    bits={}
    for key,pat in [
        ("title",r"<title>(.*?)</title>"),
        ("og_title",r'<meta\s+property="og:title"\s+content="([^"]*)"'),
        ("desc",r'<meta\s+name="description"\s+content="([^"]*)"'),
        ("og_desc",r'<meta\s+property="og:description"\s+content="([^"]*)"'),
        ("canonical",r'<link\s+rel="canonical"\s+href="([^"]*)"'),
        ("robots",r'<meta\s+name="robots"\s+content="([^"]*)"'),
        ("h1",r"<h1\b[^>]*>(.*?)</h1>")
    ]:
        m=re.search(pat,raw,re.I|re.S)
        bits[key]=html.unescape(m.group(1)) if m else None
    return bits

def patch(raw,title,hub_description=None):
    old=metadata(raw)
    assert old["title"] and old["og_title"] and old["desc"] and old["canonical"] and old["robots"] and old["h1"]
    head_sep="</head>"
    assert raw.count(head_sep)==1
    head,body=raw.split(head_sep,1)
    def change(pattern,value,source):
        altered,n=re.subn(pattern,lambda m:m.group(1)+html.escape(value,quote=True)+m.group(3),
                           source,count=1,flags=re.I|re.S)
        if n!=1:fail("HEAD_FIELD_MISSING_"+pattern[:22])
        return altered
    head=change(r"(<title>)(.*?)(</title>)",title,head)
    head=change(r'(<meta\s+property="og:title"\s+content=")([^"]*)(")',title,head)
    if hub_description is not None:
        head=change(r'(<meta\s+name="description"\s+content=")([^"]*)(")',hub_description,head)
        if 'property="og:description"' in head:
            head=change(r'(<meta\s+property="og:description"\s+content=")([^"]*)(")',hub_description,head)
    # Structured WebPage name must match title while preserving other JSON-LD nodes.
    pattern=r'(<script\s+type="application/ld\+json">)(.*?)(</script>)'
    modified_schema=[0]
    def schema_replace(m):
        try:data=json.loads(m.group(2))
        except Exception: fail("SCHEMA_PARSE")
        graph=data.get("@graph") or []
        changed=False
        for node in graph:
            if isinstance(node,dict) and node.get("@type")=="WebPage" and node.get("name")!=title:
                node["name"]=title;changed=True
        if changed:
            modified_schema[0]+=1
            return m.group(1)+json.dumps(data,ensure_ascii=False,separators=(",",":"))+m.group(3)
        return m.group(0)
    head=re.sub(pattern,schema_replace,head,flags=re.I|re.S)
    assert modified_schema[0]<=1
    result=head+head_sep+body
    after=metadata(result)
    if after["title"]!=title or after["og_title"]!=title:fail("TITLE_NOT_APPLIED")
    for k in ("canonical","robots","h1"):
        if after[k]!=old[k]:fail("IMMUTABLE_HEAD_DRIFT_"+k)
    if after["robots"] and "noindex" in after["robots"].lower():fail("STATION_WAS_NOINDEX")
    if hub_description is None and (after["desc"]!=old["desc"] or after["og_desc"]!=old["og_desc"]):fail("SPECIALTY_DESCRIPTION_DRIFT")
    if result.split(head_sep,1)[1]!=body:fail("HTML_BODY_MODIFIED")
    if hub_description is not None and after["desc"]!=hub_description:fail("HUB_DESC_MISMATCH")
    return result,old,after

def getraw(path,expected):
    url=SOURCE+path
    last=None
    for n in range(3):
        try:
            q=urllib.request.Request(url,method="GET",headers={"User-Agent":"ENPT-OWNER-SEO-A-V31-SHA-READONLY","Accept":"*/*"})
            with urllib.request.urlopen(q,timeout=32) as r:
                if r.status!=200:fail("SOURCE_HTTP_"+str(r.status))
                b=r.read(650000)
            if sha(b)!=expected:fail("SOURCE_SHA_MISMATCH_"+path)
            return b
        except urllib.error.HTTPError as e:
            if e.code==429:fail("SOURCE_RATE_LIMIT_429")
            last=e
        except Exception as e:
            if "SHA_MISMATCH" in str(e):raise
            last=e
        time.sleep(0.4*(n+1))
    fail("SOURCE_GET_FAILED_"+path+"_"+str(last)[:110])

def build(mode):
    from enpt_seo_title_policy_a_v1 import hub_title,course_title,station_hub_description,COURSE_TITLES
    OUT.mkdir(exist_ok=True)
    with gzip.open(MANIFEST,"rt",encoding="utf8") as f:base=json.load(f)
    with gzip.open(SIGNED,"rt",encoding="utf8") as f:signed=json.load(f)["original_public_html_to_data_payload"]
    rows=json.loads((ROOT/"data/stations.json").read_text(encoding="utf8"))["stations"]
    intents=list(COURSE_TITLES)
    assert len(base)==202786 and len(rows)==911 and len(intents)==23
    targets=[]
    seen=set()
    for st in rows:
        for intent in [None]+intents:
            route=f'station-{st["slug"]}'+("-"+intent if intent else "")+".html"
            item=signed.get(route)
            if item is None:fail("UNSIGNED_ROUTE_"+route)
            payload="/"+item["to"].lstrip("/")
            if payload not in base:fail("UNSIGNED_PAYLOAD_"+route)
            if payload in seen:fail("PAYLOAD_ROUTE_COLLISION_"+payload)
            seen.add(payload)
            title=hub_title(st["name"]) if intent is None else course_title(st["name"],intent)
            desc=station_hub_description(st["name"]) if intent is None else None
            targets.append((route,payload,base[payload],title,desc))
    assert len(targets)==21864 and len(seen)==21864
    if mode=="sample":
        slugset={"banwoldang","gangnam","seomyeon","sangmu","dongdaegu"}
        keep={"station-banwoldang.html","station-gangnam.html","station-seomyeon.html",
              "station-banwoldang-biz-business-conv.html","station-gangnam-opic.html",
              "station-sangmu-elem-tutor.html","station-dongdaegu-ielts.html"}
        targets=[t for t in targets if t[0] in keep]
        assert len(targets)==len(keep)
    LOCK=threading.Lock();done=[0];failed=[];results=[]
    def work(x):
        route,payload,digest,title,desc=x
        old=getraw(payload,digest)
        raw=old.decode("utf8","strict")
        if not raw.startswith("<!doctype html") and not raw.startswith("<!DOCTYPE html"):fail("NON_HTML_"+route)
        new,before,after=patch(raw,title,desc)
        content=new.encode("utf8")
        if sha(content)==digest:fail("NO_TITLE_CHANGE_"+route)
        loc=DIR/payload.lstrip("/")
        loc.parent.mkdir(parents=True,exist_ok=True)
        loc.write_bytes(content)
        with LOCK:
            done[0]+=1
            if done[0]%1000==0:print("ENPT_SEO_PATCH_PROGRESS",done[0],"of",len(targets),flush=True)
        return {"route":route,"payload_path":payload,"old_sha1":digest,"new_sha1":sha(content),
            "bytes":len(content),"title":title,"robots":after["robots"],
            "canonical_unchanged":after["canonical"]==before["canonical"],
            "body_unchanged":True,"description_changed":desc is not None}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12 if mode=="full" else 5) as pool:
        futures={pool.submit(work,t):t[0] for t in targets}
        for future in concurrent.futures.as_completed(futures):
            try:results.append(future.result())
            except Exception as e:
                failed.append({"route":futures[future],"reason":str(e)[:230]})
                if len(failed)>=4:
                    for f in futures:f.cancel()
                    break
    summary={
        "status":"PASS" if len(results)==len(targets) and not failed else "HOLD",
        "mode":mode,"target_count":len(targets),"processed":len(results),"failed":failed[:12],
        "expected_indexable_station_routes":21864,"frozen_v31_static_manifest_paths":len(base),
        "unchanged_sitemaps":44,"unchanged_noindex_routes":136607,"production_publishes":0,
        "form_submissions":0,"existing_v31_draft_mutations":0,"new_netlify_deploys":0
    }
    (OUT/f"{mode}-summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),"utf8")
    if summary["status"]=="PASS":
        if mode=="full":
            assert len(results)==21864
            mutated=dict(base)
            for row in results:mutated[row["payload_path"]]=row["new_sha1"]
            assert len(mutated)==202786 and sum(mutated[k]!=base[k] for k in base)==21864
            with gzip.open(OUT/"SEO_A_V31_202786_STATIC_FILES_SHA1.json.gz","wt",encoding="utf8") as f:json.dump(mutated,f,separators=(",",":"))
            (OUT/"title-route-diff-samples.json").write_text(json.dumps(sorted(results,key=lambda x:x["route"])[:40],ensure_ascii=False,indent=2),"utf8")
        print("ENPT_SEO_V31_PATCH_PASS",json.dumps(summary,ensure_ascii=False),flush=True)
    else:
        print("ENPT_SEO_V31_PATCH_HOLD",json.dumps(summary,ensure_ascii=False),flush=True)
        sys.exit(1)

if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--mode",choices=["sample","full"],required=True)
    build(a.parse_args().mode)
