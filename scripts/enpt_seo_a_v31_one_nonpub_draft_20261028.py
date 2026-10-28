#!/usr/bin/env python3
"""One NEW nonpublished frozen V3.1 SHA-reuse draft, 21,864 approved head deltas.

Only authorized changes: 911 station hubs and 20,953 station specialist metadata.
All 202,786 original source paths preserved, including 136,607 noindex.
Never publishes, restores, mutates settings, or submits consultations.
A single draft POST and only required static / bundled Edge PUTs.
"""
from __future__ import annotations
import concurrent.futures,gzip,hashlib,json,os,pathlib,re,time,urllib.parse,urllib.request,urllib.error
R=pathlib.Path(__file__).resolve().parents[1]
OUT=R/"seo-v31-new-draft-evidence";OUT.mkdir(exist_ok=True)
SRC=R/"seo-v31-minimal/SEO_A_V31_202786_STATIC_FILES_SHA1.json.gz"
DELTA=R/"seo-v31-minimal/delta"
MANIFEST_OLD=R/"v3-1-patch-evidence/V3_1_202786_CANDIDATE_FILES_SHA1.json.gz"
EDGE_FILE=R/"seo-v31-verbatim-edge/1359b9c72eadd149ad8cde014235de40b91e0d33e2132c2d5609bf76a6e4653b.tar.gz"
EDGE_SHA="1359b9c72eadd149ad8cde014235de40b91e0d33e2132c2d5609bf76a6e4653b"
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
PUB="6adafef5f2c6d196833683db"
V31="6ae06963f085b33a5ee903eb"
MARKER="ENPT-SEO-A-V31-20261028-21864-HEAD-ONLY-REVIEW-NONPUB"
API="https://api.netlify.com/api/v1/"
TOKEN=os.environ["NETLIFY_AUTH_TOKEN"]
def save(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),"utf8")
    print("ENPT_SEO_DRAFT_LEDGER",name,json.dumps(data,ensure_ascii=False)[:2000],flush=True)
def hold(msg):raise RuntimeError("HOLD_ENPT_SEO_DRAFT_"+str(msg))
def get(p):
    req=urllib.request.Request(API+p,method="GET",
      headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)
def sha(x):return hashlib.sha1(x).hexdigest()
def identity():
    site=get("sites/"+SITE)
    if site.get("id")!=SITE or site.get("custom_domain")!="englishpt.kr" or (site.get("published_deploy") or {}).get("id")!=PUB:
        hold("PUBLISHED_SITE_DRIFT")
    v31=get("sites/"+SITE+"/deploys/"+V31)
    if v31.get("title")!="ENPT-V3-1-20261027-BYEONGMOKANDONG-7-CORRECTED-NONPUB" or v31.get("state")!="ready" or v31.get("published_at") is not None or v31.get("draft") is False:
        hold("V31_READY_DRAFT_DRIFT")
    return site
def prepare():
    if len(TOKEN)<20:hold("MISSING_NETLIFY_TOKEN")
    gate=json.loads((R/"seo-v31-minimal/full-summary.json").read_text())
    if gate["status"]!="PASS" or gate["processed"]!=21864 or gate["failed"]:hold("FULL_SHA_OFFLINE_GATE_FAIL")
    with gzip.open(SRC,"rt",encoding="utf8") as f:files=json.load(f)
    with gzip.open(MANIFEST_OLD,"rt",encoding="utf8") as f:old=json.load(f)
    if len(files)!=202786 or len(old)!=202786 or set(files)!=set(old):hold("STATIC_PATH_COUNT_OR_SET")
    changed={p for p in files if files[p]!=old[p]}
    if len(changed)!=21864 or any(not p.startswith("/__pages/") or not p.endswith(".page") for p in changed):
        hold("CHANGED_SCOPE_UNEXPECTED")
    blobs={}
    for p in sorted(DELTA.rglob("*.page")):
        rel="/"+p.relative_to(DELTA).as_posix()
        if rel not in changed:hold("DELTA_NOT_IN_CHANGED_SET")
        h=sha(p.read_bytes())
        if files[rel]!=h:hold("DELTA_BYTES_SHA_CHANGED")
        if h in blobs:hold("DUPLICATE_SHA_ACROSS_DISTINCT_ROUTES")
        blobs[h]=rel
    if len(blobs)!=21864 or set(blobs.values())!=changed:hold("INCOMPLETE_DELTA")
    if not EDGE_FILE.exists() or len(EDGE_FILE.read_bytes())!=2137 or hashlib.sha256(EDGE_FILE.read_bytes()).hexdigest()!=EDGE_SHA:
        hold("VERBATIM_EDGE_TAR_NOT_PROVEN")
    site=identity()
    acct=get("accounts/"+site["account_id"])
    if acct.get("usages_exceeded") or acct.get("configurable_limits_exceeded"):hold("NETLIFY_ACCOUNT_LIMIT")
    credits=(acct.get("capabilities") or {}).get("credits") or {}
    if "used" in credits and "included" in credits and credits["used"]>=credits["included"]:hold("NO_ACCOUNT_CREDITS")
    hist=get("sites/"+SITE+"/deploys?per_page=100")
    if any(x.get("title")==MARKER for x in hist):hold("EXISTING_MARKER_DO_NOT_DUPLICATE")
    payload=json.dumps({"files":files,"edge_functions":{"tar":EDGE_SHA},
        "draft":True,"async":True,"branch":"review-enpt-seo-a-v31-20261028"},
        ensure_ascii=False,separators=(",",":")).encode()
    if len(payload)>24000000:hold("DIGEST_PAYLOAD_TOO_LARGE")
    pre={"status":"PASS_PREPOST","published_id":PUB,"v31_original_draft":V31,
         "static_count":len(files),"changed_payloads":len(changed),
         "source_immutable_sha_count":len(old)-len(changed),"edge_sha":EDGE_SHA,
         "credits":credits,"post_attempts":0,"production_publishes":0,"form_submits":0,
         "manifest_bytes":len(payload),"marker":MARKER}
    save("01_SAFE_SCOPE_PREPOST.json",pre)
    return blobs,payload
def main():
    blobs,manifest=prepare()
    attempt={"status":"POST_ATTEMPTED_DO_NOT_RETRY","draft_create_posts":1,
             "marker":MARKER,"original_v31":V31,"published":PUB}
    save("02_ONE_DRAFT_POST_LEDGER.json",attempt)
    url=API+"sites/"+SITE+"/deploys?"+urllib.parse.urlencode({"title":MARKER})
    req=urllib.request.Request(url,method="POST",data=manifest,
        headers={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=120) as res:
            d=json.load(res)
            if res.status not in (200,201,202):hold("DRAFT_POST_STATUS_"+str(res.status))
    except Exception as exc:
        attempt.update(status="HOLD_AMBIGUOUS_POST_NO_RETRY",error=str(exc)[:200])
        save("02_ONE_DRAFT_POST_LEDGER.json",attempt)
        raise
    did=d.get("id","")
    if not re.fullmatch(r"[0-9a-f]{24}",did):hold("NO_DRAFT_ID")
    if d.get("published_at") is not None or d.get("draft") is False:hold("DRAFT_FLAG_BAD")
    attempt.update(status="CREATED_NONPUBLISHED",draft_id=did,returned_state=d.get("state"))
    save("02_ONE_DRAFT_POST_LEDGER.json",attempt)
    for n in range(55):
        identity();d=get("sites/"+SITE+"/deploys/"+did)
        if d.get("state") in ("prepared","uploading","uploaded","ready"):break
        if d.get("state") in ("failed","error"):hold("DRAFT_PREPARE_FAILED")
        time.sleep(3)
    else:hold("DRAFT_PREPARE_TIMEOUT")
    needed=set(d.get("required") or [])
    edges=set(d.get("required_edge_functions") or [])
    if needed-set(blobs):hold("NETLIFY_NEEDS_UNEXPECTED_OLD_STATIC")
    if edges-{EDGE_SHA}:hold("NETLIFY_NEEDS_WRONG_EDGE_BUNDLE")
    save("03_REQUIRED_SHA_LIST.json",{"draft_id":did,"state":d.get("state"),"static_required":len(needed),
        "edge_required":list(edges),"protection_checked":True})
    # No retry of ambiguous PUTs. A subsequent separately-approved job must
    # reconcile via GET before any resume; never create a second Draft.
    uploaded=0;errors=[]
    sorted_required=sorted(needed)
    for offset in range(0,len(sorted_required),160):
        identity()
        chunk=sorted_required[offset:offset+160]
        def upload(h):
            rel=blobs[h]
            p=DELTA/rel.lstrip("/")
            raw=p.read_bytes()
            if sha(raw)!=h:hold("BLOB_SHA_DRIFT")
            dest=API+"deploys/"+did+"/files/"+urllib.parse.quote(rel.lstrip("/"),safe="/")
            q=urllib.request.Request(dest,method="PUT",data=raw,
                headers={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/octet-stream"})
            with urllib.request.urlopen(q,timeout=65) as r:
                if r.status not in (200,201,202,204):hold("FILE_PUT_STATUS_"+str(r.status))
            return h
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            fs={pool.submit(upload,h):h for h in chunk}
            for f in concurrent.futures.as_completed(fs):
                try:f.result();uploaded+=1
                except Exception as e:errors.append({"sha":fs[f],"error":str(e)[:180]})
        save("04_STATIC_PROGRESS.json",{"draft_id":did,"uploaded":uploaded,
            "required_initial":len(needed),"errors":errors[:10],"no_retry":True})
        if errors:hold("STATIC_PUT_ERROR_NO_AUTO_RETRY")
        if uploaded%640==0 or uploaded==len(needed):
            print("ENPT_SEO_DRAFT_STATIC_PROGRESS",uploaded,"of",len(needed),flush=True)
    if EDGE_SHA in edges:
        identity()
        blob=EDGE_FILE.read_bytes()
        assert len(blob)==2137 and hashlib.sha256(blob).hexdigest()==EDGE_SHA
        save("05_EDGE_ONE_PUT_ATTEMPT.json",{"draft_id":did,"sha256":EDGE_SHA,"status":"ATTEMPTED_DO_NOT_RETRY"})
        q=urllib.request.Request(API+"deploys/"+did+"/edge_functions/"+EDGE_SHA,
            method="PUT",data=blob,
            headers={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/octet-stream"})
        try:
            with urllib.request.urlopen(q,timeout=65) as r:
                if r.status not in (200,201,202,204):hold("EDGE_PUT_BAD_HTTP")
            save("05_EDGE_ONE_PUT_ATTEMPT.json",{"draft_id":did,"sha256":EDGE_SHA,"status":"ACCEPTED"})
        except Exception as e:
            save("05_EDGE_ONE_PUT_ATTEMPT.json",{"draft_id":did,"sha256":EDGE_SHA,"status":"HOLD_AMBIGUOUS_EDGE_NO_RETRY","error":str(e)[:200]})
            raise
    for n in range(90):
        identity();d=get("sites/"+SITE+"/deploys/"+did)
        if d.get("state")=="ready":break
        if d.get("state") in ("failed","error"):hold("FINAL_DRAFT_FAILED")
        time.sleep(4)
    else:hold("FINAL_DRAFT_NOT_READY")
    if d.get("published_at") is not None or d.get("draft") is False or d.get("required") or d.get("required_edge_functions"):
        hold("FINAL_DRAFT_NOT_SAFE_READY")
    identity()
    summary={"status":"PASS_NEW_NONPUBLISHED_SEO_A_V31_DRAFT_READY",
        "draft_id":did,"preview_url":d.get("deploy_ssl_url") or d.get("deploy_url"),
        "draft_only":True,"production_id_unchanged":PUB,"v31_original_draft_unchanged":V31,
        "static_paths":202786,"seo_head_only_payloads":21864,"static_uploaded":uploaded,
        "published":False,"form_submits":0}
    save("06_NEW_DRAFT_READY.json",summary)
    print("ENPT_SEO_A_NEW_NONPUB_DRAFT_READY",json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
