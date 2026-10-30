#!/usr/bin/env python3
"""Resume one EXISTING immutable Netlify draft: GET and same-path SHA PUT only.
NEVER POST a deploy or publish; never mutate original published/V3.1 draft.
"""
import argparse,datetime,gzip,hashlib,json,os,pathlib,re,time,urllib.error,urllib.parse,urllib.request
R=pathlib.Path(__file__).resolve().parents[1]
ROOT=R/"seo-v31-minimal"
OUTPUT=R/"seo-v31-resume-evidence"
OUTPUT.mkdir(exist_ok=True)
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
PUB="6adafef5f2c6d196833683db"
OLD="6ae06963f085b33a5ee903eb"
DRAFT="6ae44a45133b105058f6f9ef"
MARKER="ENPT-SEO-A-V31-20261028-21864-HEAD-ONLY-REVIEW-NONPUB"
EDGE_SHA="1359b9c72eadd149ad8cde014235de40b91e0d33e2132c2d5609bf76a6e4653b"
EDGE=R/"seo-v31-verbatim-edge"/(EDGE_SHA+".tar.gz")
API="https://api.netlify.com/api/v1/"
TOKEN=os.environ.get("NETLIFY_AUTH_TOKEN","")
def hold(msg):raise RuntimeError("HOLD_EXISTING_DRAFT_RESUME_"+msg)
def sha(b):return hashlib.sha1(b).hexdigest()
def write(name,obj):
    (OUTPUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),"utf8")
    print("ENPT_DRAFT_RESUME_LEDGER",name,json.dumps(obj,ensure_ascii=False)[:850],flush=True)
def request(method,url,data=None,headers=None,timeout=50):
    h={"Authorization":"Bearer "+TOKEN,"User-Agent":"ENPT-V31-20261030-OWNER-EXISTING-DRAFT-RESUME"}
    if headers:h.update(headers)
    q=urllib.request.Request(url,method=method,data=data,headers=h)
    with urllib.request.urlopen(q,timeout=timeout) as res:
        return res.status,res.read(400000),res.headers
def api_get(p):
    status,raw,_=request("GET",API+p,headers={"Accept":"application/json"})
    if status!=200:hold("GET_STATUS_"+str(status))
    return json.loads(raw)
def identity():
    site=api_get("sites/"+SITE)
    old=api_get("sites/"+SITE+"/deploys/"+OLD)
    current=api_get("sites/"+SITE+"/deploys/"+DRAFT)
    if (site.get("published_deploy") or {}).get("id")!=PUB:hold("PRODUCTION_DRIFT")
    if old.get("state")!="ready" or old.get("published_at") is not None or old.get("draft") is False:hold("ORIGINAL_V31_DRIFT")
    if current.get("id")!=DRAFT or current.get("title")!=MARKER:hold("WRONG_DRAFT_OR_MARKER")
    if current.get("published_at") is not None or current.get("draft") is False:hold("NEW_DRAFT_WAS_PUBLISHED")
    if current.get("state") not in ("prepared","uploading","uploaded","ready"):hold("NEW_DRAFT_STATE_"+str(current.get("state")))
    return current
def retry_put(url,content,description,pace):
    last=None
    for attempt in range(7):
        try:
            status,reply,headers=request("PUT",url,data=content,headers={"Content-Type":"application/octet-stream"},timeout=55)
            if status not in (200,201,202,204):hold("UPLOAD_HTTP_"+str(status))
            return {"status":status,"remaining":headers.get("X-RateLimit-Remaining"),"reset":headers.get("X-RateLimit-Reset")}
        except urllib.error.HTTPError as e:
            last=e.code
            if e.code==429:
                retry=e.headers.get("Retry-After")
                reset=e.headers.get("X-RateLimit-Reset")
                wait=75
                if retry and retry.isdecimal():wait=max(wait,min(300,int(retry)+5))
                elif reset and reset.isdecimal():wait=max(wait,min(300,int(reset)-int(time.time())+6))
                print("ENPT_NETLIFY_429_BACKOFF",description,attempt+1,wait,flush=True)
                time.sleep(wait)
                continue
            if e.code in (500,502,503,504):
                time.sleep(12*(attempt+1));continue
            hold("PERMANENT_UPLOAD_HTTP_"+description+"_"+str(e.code))
        except (TimeoutError,ConnectionError,urllib.error.URLError) as e:
            last=type(e).__name__
            time.sleep(10*(attempt+1));continue
    hold("UPLOAD_RETRIES_EXHAUSTED_"+description+"_"+str(last))
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--smoke",type=int,default=0)
    p.add_argument("--pace",type=float,default=0.35)
    a=p.parse_args()
    if len(TOKEN)<20 or not 0.30<=a.pace<=2.0:hold("BAD_TOKEN_OR_PACE")
    def readgz(name):
        with gzip.open(name,"rt",encoding="utf8") as f:return json.load(f)
    original=readgz(R/"v3-1-patch-evidence/V3_1_202786_CANDIDATE_FILES_SHA1.json.gz")
    latest=readgz(ROOT/"SEO_A_V31_202786_STATIC_FILES_SHA1.json.gz")
    if len(original)!=len(latest)!=202786:hold("MANIFEST_COUNT_WRONG")
    if len(original)!=202786 or set(original)!=set(latest):hold("STATIC_MANIFEST_DRIFT")
    changed=[k for k in original if original[k]!=latest[k]]
    if len(changed)!=21864 or any(not k.startswith("/__pages/") or not k.endswith(".page") for k in changed):hold("CHANGE_SCOPE_DRIFT")
    paths=sorted(changed)
    status=identity()
    if status.get("state")=="ready":
        write("already_ready.json",{"status":"READY_PRESERVED","draft_id":DRAFT,"draft_url":status.get("deploy_ssl_url")})
        return
    # Netlify GET /deploys/{id} returns [] required while uploading; do not
    # falsely conclude that all uploaded files are accounted for.
    write("00_SAFE_EXISTING_DRAFT.json",{"draft_id":DRAFT,"initial_state":status["state"],
        "published":PUB,"old_v31":OLD,"manifest_paths":len(latest),
        "signed_delta_paths":len(paths),"no_new_draft_posts":True,
        "rate_limit_per_minute_target":round(60/a.pace,1),"smoke":a.smoke})
    limit=len(paths) if a.smoke==0 else min(a.smoke,len(paths))
    done=0;rate_limit_hits=0;last_start=0.0
    for index,path in enumerate(paths[:limit]):
        content_path=ROOT/"delta"/path.lstrip("/")
        if not content_path.is_file():hold("DELTA_MISSING_"+path)
        b=content_path.read_bytes()
        if sha(b)!=latest[path]:hold("DELTA_SHA_MISMATCH_"+path)
        wait=last_start+a.pace-time.monotonic()
        if wait>0:time.sleep(wait)
        last_start=time.monotonic()
        url=API+"deploys/"+DRAFT+"/files/"+urllib.parse.quote(path.lstrip("/"),safe="/")
        reply=retry_put(url,b,str(index),a.pace)
        done+=1
        if done%100==0 or done==limit:
            write("01_UPLOAD_PROGRESS.json",{"draft_id":DRAFT,"uploaded_in_this_run":done,"total_expected":len(paths),
                "last_index":index,"last_file":path,"request_limited_to":limit,
                "new_draft_posts":0,"production_publishes":0,"last_http":reply["status"],
                "remaining_at_checkpoint":reply.get("remaining")})
            print("ENPT_DRAFT_RESUME_PROGRESS",done,"of",limit,"target",len(paths),flush=True)
        if done%1000==0:identity()
    if a.smoke:
        identity()
        write("02_SMOKE_PASS.json",{"status":"PASS_SMOKE_SAME_DRAFT","uploaded":done,"draft_id":DRAFT,
            "remaining_expected_for_complete_reupload":len(paths)-done,"new_posts":0})
        return
    if len(paths)!=done:hold("UPLOAD_COUNT_INCOMPLETE")
    # Only after all exact-SHA files accepted, finish immutable edge bundle.
    identity()
    if not EDGE.exists() or len(EDGE.read_bytes())!=2137 or hashlib.sha256(EDGE.read_bytes()).hexdigest()!=EDGE_SHA:
        hold("EDGE_TAR_SHA_OR_SIZE")
    edge_before=api_get("sites/"+SITE+"/deploys/"+DRAFT)
    if EDGE_SHA in (edge_before.get("required_edge_functions") or []):
        url=API+"deploys/"+DRAFT+"/edge_functions/"+EDGE_SHA
        write("03_EDGE_PUT_ATTEMPT.json",{"draft_id":DRAFT,"edge_sha256":EDGE_SHA,"attempted":True})
        resp=retry_put(url,EDGE.read_bytes(),"EDGE_BUNDLE",a.pace)
        write("03_EDGE_PUT_ACCEPTED.json",{"draft_id":DRAFT,"status":resp["status"],"edge_sha256":EDGE_SHA})
    for n in range(50):
        current=identity()
        if current["state"]=="ready":
            if current.get("required_edge_functions") or current.get("required"):
                hold("READY_WITH_REQUIRED_FILES")
            out={"status":"PASS_EXISTING_DRAFT_READY","draft_id":DRAFT,
                 "preview_url":current.get("deploy_ssl_url") or current.get("deploy_url"),
                 "published_at":current.get("published_at"),"original_published_id":PUB,
                 "original_v31_id":OLD,"original_202786_static_paths":len(original),
                 "seo_head_only_file_count":len(paths),
                 "actual_put_accepted":done,"draft_created_in_this_run":False,
                 "published":False,"consultation_posts":0}
            write("04_EXISTING_DRAFT_READY.json",out)
            print("ENPT_EXISTING_DRAFT_READY",json.dumps(out,ensure_ascii=False),flush=True)
            return
        time.sleep(12)
    hold("READY_TIMEOUT_AFTER_ALL_SIGNED_SHA_PUT")
if __name__=="__main__":main()
