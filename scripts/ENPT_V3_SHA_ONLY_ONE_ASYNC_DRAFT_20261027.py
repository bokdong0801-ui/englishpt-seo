#!/usr/bin/env python3
"""ONE Netlify API async nonpublished Draft, source 202768 immutable Published files + V3 21 delta files.
No Production publish, restore, or site-setting mutation. One POST, bounded PUT only for new SHA.
If API result ambiguous, HOLD and reconcile by GET; NEVER retry POST automatically.
"""
from __future__ import annotations
import datetime,gzip,hashlib,json,os,pathlib,re,time,urllib.request,urllib.parse,urllib.error
R=pathlib.Path(__file__).resolve().parents[1]
SRC=R/"v3-digest-qa/V3_202786_CANDIDATE_FILES_SHA1.json.gz"
QA=R/"v3-digest-qa/V3_SHA_ONLY_SOURCE_GUARD.json"
DELTA=R/"v3-delta-files"
OUT=R/"v3-live-upload-evidence"
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
PUB="6adafef5f2c6d196833683db"
MARKER="ENPT-V3-20261027-202786-SHA-REUSE-NONPUBLISHED-ONCE"
EDGE_TAR="1359b9c72eadd149ad8cde014235de40b91e0d33e2132c2d5609bf76a6e4653b"
API="https://api.netlify.com/api/v1/"
TOKEN=os.environ.get("NETLIFY_AUTH_TOKEN","")
def output(name,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),"utf8")
    print("ENPT_V3_DEPLOY_LEDGER",name,json.dumps(obj,ensure_ascii=False)[:4000],flush=True)
def fail(message):raise RuntimeError("HOLD_V3_NONPUB_"+message)
def get(path):
    req=urllib.request.Request(API+path,headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"},method="GET")
    with urllib.request.urlopen(req,timeout=40) as r:return json.load(r)
def identity():
    x=get("sites/"+SITE)
    if x.get("id")!=SITE or x.get("custom_domain")!="englishpt.kr" or (x.get("published_deploy") or {}).get("id")!=PUB:fail("PRODUCTION_IDENTITY_DRIFT")
    return x
def sha(buf):return hashlib.sha1(buf).hexdigest()
def preflight():
    if len(TOKEN)<20:fail("MISSING_NETLIFY_TOKEN")
    q=json.loads(QA.read_text("utf8"))
    if q.get("status")!="PASS_V3_202786_SHA1_FILE_SOURCE_ONLY":fail("SOURCE_GUARD_NOT_PASS")
    with gzip.open(SRC,"rt",encoding="utf8") as f:files=json.load(f)
    if len(files)!=202786:fail("CANDIDATE_MANIFEST_COUNT")
    parts={}
    for f in DELTA.rglob("*"):
        if not f.is_file():continue
        p="/"+f.relative_to(DELTA).as_posix()
        blob=f.read_bytes()
        if files.get(p)!=sha(blob):fail("DELTA_FILE_DIGEST_CHANGED_"+p)
        parts[sha(blob)]=(p,blob)
    if len(parts)!=21:fail("DELTA_21_FILES_"+str(len(parts)))
    if any(p in ("robots.txt","sitemap-index.xml","_headers","netlify.toml") for p,_ in parts.values()):fail("SEO_CRITICAL_FILE_IN_DELTA")
    site=identity()
    account=get("accounts/"+site["account_id"])
    if account.get("usages_exceeded") or account.get("configurable_limits_exceeded"):fail("NETLIFY_ACCOUNT_LIMIT")
    credits=(account.get("capabilities") or {}).get("credits") or {}
    if "used" in credits and "included" in credits and credits["used"]>=credits["included"]:fail("NETLIFY_NO_REMAINING_CREDITS")
    history=get("sites/"+SITE+"/deploys?per_page=100")
    if any((x.get("title") or "")==MARKER for x in history):fail("EXISTING_DRAFT_ALREADY_HAS_MARKER")
    params={"files":files,"edge_functions":{"tar":EDGE_TAR},"draft":True,"async":True,"branch":"review-enpt-v3-fullsite-20261027"}
    payload=json.dumps(params,ensure_ascii=False,separators=(",",":")).encode("utf8")
    if len(payload)>24000000:fail("PAYLOAD_TOO_LARGE")
    return parts,payload,{"status":"PASS_IDENTITY_PREPOST","current_published":PUB,"files":len(files),"delta_sha":len(parts),"payload_bytes":len(payload),"credits":credits,"marker":MARKER,"production_post_attempts":0,"netlify_draft_post_attempts":0,"forms_submitted":0}
def post_once(data):
    request=urllib.request.Request(API+"sites/"+SITE+"/deploys?"+urllib.parse.urlencode({"title":MARKER}),data=data,
       method="POST",headers={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/json","Accept":"application/json"})
    with urllib.request.urlopen(request,timeout=120) as r:
        body=json.load(r)
        if r.status not in (200,201,202):fail("UNEXPECTED_POST_STATUS_"+str(r.status))
    return body
def state(did):return get("sites/"+SITE+"/deploys/"+did)
def main():
    parts,body,ledger=preflight()
    output("01_PREPOST_IDENTITY_GUARD.json",ledger)
    attempt={"status":"POST_ATTEMPTED_DO_NOT_AUTO_RETRY","attempts":1,"marker":MARKER,"source_published":PUB}
    output("02_ONE_DRAFT_CREATION_LEDGER.json",attempt)
    try:
        d=post_once(body)
    except Exception as e:
        attempt.update(status="HOLD_POST_AMBIGUOUS_NEVER_RETRY_WITHOUT_GET",error=type(e).__name__+":"+str(e)[:250])
        output("02_ONE_DRAFT_CREATION_LEDGER.json",attempt)
        raise
    did=d.get("id","")
    if not re.fullmatch("[a-f0-9]{24}",did):fail("NO_NETLIFY_DRAFT_ID")
    attempt.update(status="CREATED_NONPUBLISHED_DRAFT",draft_id=did,returned_state=d.get("state"),returned_draft=d.get("draft"),published_at=d.get("published_at"))
    output("02_ONE_DRAFT_CREATION_LEDGER.json",attempt)
    if d.get("draft") is False or d.get("published_at") is not None:fail("DRAFT_FLAG_UNSAFE")
    # Only GET polling. If Edge SHA is not already in Netlify storage, HALT; never substitute router.
    for n in range(45):
        identity()
        d=state(did)
        stage=d.get("state")
        if stage in ("prepared","uploading","uploaded","ready"):break
        if stage in ("error","failed"):fail("DRAFT_PREPARATION_"+str(stage))
        time.sleep(3)
    else:fail("DRAFT_PREPARE_TIMEOUT")
    needed=d.get("required") or []
    edge_needed=d.get("required_edge_functions") or []
    ledger2={"state":stage,"draft_id":did,"required_static_sha":len(needed),"required_edge_sha":edge_needed,"source_published":PUB,"new_sha_available":len(parts),"nonproduction":True}
    output("03_REQUIRED_SHA_PREFLIGHT.json",ledger2)
    if edge_needed:
        # Historical asynchronous deployments produced 502 due to unbundled Edge; do not publish a broken preview.
        fail("EDGE_BUNDLE_REQUIRED_STOP_NO_RISK")
    if len(needed)>len(parts):fail("UNEXPECTED_OLD_OR_TOO_MANY_SHA_REQUIRED")
    unexpected=set(needed)-set(parts)
    if unexpected:fail("MISSING_REQUIRED_SHA_FROM_EXISTING_NETLIFY_STORAGE_"+str(len(unexpected)))
    attempted=[]
    for required_sha in needed:
        identity()
        path,content=parts[required_sha]
        attempted.append({"sha":required_sha,"path":path,"bytes":len(content),"status":"ATTEMPT_BEFORE_PUT"})
        output("04_BOUNDED_DELTA_UPLOAD_LEDGER.json",{"draft_id":did,"files":attempted})
        url=API+"deploys/"+did+"/files/"+urllib.parse.quote(path.lstrip("/"),safe="/")
        req=urllib.request.Request(url,data=content,method="PUT",headers={
             "Authorization":"Bearer "+TOKEN,"Content-Type":"application/octet-stream"})
        try:
            with urllib.request.urlopen(req,timeout=55) as res:
                if res.status not in (200,201,202,204):fail("BAD_FILE_PUT_STATUS_"+str(res.status))
                attempted[-1]["status"]="UPLOADED"
        except Exception as e:
            attempted[-1]["status"]="HOLD_AMBIGUOUS_UPLOAD"
            attempted[-1]["error"]=str(e)[:170]
            output("04_BOUNDED_DELTA_UPLOAD_LEDGER.json",{"draft_id":did,"files":attempted})
            raise
        output("04_BOUNDED_DELTA_UPLOAD_LEDGER.json",{"draft_id":did,"files":attempted})
    for n in range(80):
        identity()
        d=state(did)
        stage=d.get("state")
        if stage=="ready":break
        if stage in ("error","failed"):fail("DRAFT_FINAL_ERROR_"+str(stage))
        time.sleep(3)
    else:fail("DRAFT_READY_TIMEOUT")
    if d.get("published_at") is not None or d.get("draft") is False:fail("PUBLISHED_UNEXPECTEDLY")
    identity()
    out={"status":"PASS_FULL_NONPUB_DRAFT_READY","draft_id":did,"draft_state":stage,"draft":d.get("draft"),
      "preview_url":d.get("deploy_ssl_url") or d.get("deploy_url"),"published_id_unchanged":PUB,
      "candidate_static_paths":202786,"old_paths_removed":0,"changed_existing_pages":3,"added_regions":18,
      "delta_upload_count":len(attempted),"edge_bundle_required":[],"published":False,"forms_posted":0}
    output("05_V3_FINAL_DRAFT_READY.json",out)
    print("ENPT_V3_FULL_DRAFT_READY",json.dumps(out,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
