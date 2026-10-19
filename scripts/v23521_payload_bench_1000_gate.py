#!/usr/bin/env python3
"""Approved small Draft ONLY. Netlify API GET checks; never publish/POST."""
import argparse,datetime,hashlib,json,os,pathlib,urllib.request,urllib.error
REVIEW="803550a8-03af-4776-bc8a-bd0bae85f5c7"
PROD="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
OLD_PROD="6ac4bd517c30220008bb9661"
SHA="b66d6f5409dd13a4b974877e26e08457e0f42ce527c81fef0bf6daea3fdaaf0d"
ALIAS="enpt23521paybench1k"
MARKER="ENGLISHPT_V23521_PAYLOAD_BENCH_1000_ONCE_20261019"
OUT=pathlib.Path("small-draft-evidence");OUT.mkdir(parents=True,exist_ok=True)
def get(path):
 request=urllib.request.Request("https://api.netlify.com/api/v1/"+path,headers={
  "Authorization":"Bearer "+os.environ["NETLIFY_AUTH_TOKEN"],"Accept":"application/json"},method="GET")
 with urllib.request.urlopen(request,timeout=30) as r:return json.load(r)
def digest(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--mode",choices=("before","after"),required=True)
 p.add_argument("--archive",default="")
 a=p.parse_args()
 report={"status":"HOLD","phase":a.mode,"timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "production_writes":0,"draft_created_by_this_check":False,"form_POSTs":0,"search_submissions":0,
  "issues":[],"approved_attempt_count":1}
 try:
  prod=get("sites/"+PROD)
  review=get("sites/"+REVIEW)
  assert prod.get("id")==PROD and prod.get("custom_domain")=="englishpt.kr"
  assert review.get("id")==REVIEW and REVIEW!=PROD
  current_prod=(prod.get("published_deploy") or {}).get("id")
  current_review=(review.get("published_deploy") or {}).get("id")
  report.update({"production_published_id":current_prod,"review_published_id":current_review,
    "review_site_id":REVIEW,"pilot_SHA256":SHA})
  if current_prod!=OLD_PROD:raise ValueError("Production changed! HOLD")
  prior_path=OUT/"PREUPLOAD.json"
  if a.mode=="before":
   if not a.archive or digest(a.archive)!=SHA:raise ValueError("small candidate SHA mismatch")
   acc=get("accounts/"+review["account_id"]);credits=((acc.get("capabilities") or {}).get("credits") or {})
   if acc.get("usages_exceeded") or acc.get("configurable_limits_exceeded") or acc.get("in_operational_mode") is True:
    raise ValueError("Netlify account limited")
   if credits.get("included") is not None and credits.get("used") is not None:
    if credits["included"]-credits["used"]<=0:raise ValueError("No credit capacity")
   report["credits_remaining"]=credits.get("included",0)-credits.get("used",0)
   prior=get("sites/"+REVIEW+"/deploys?per_page=100")
   markers=[d["id"] for d in prior if MARKER in " ".join(str(d.get(x) or "") for x in ("title","name","alias")) or
      ALIAS in " ".join(str(d.get(x) or "") for x in ("deploy_url","deploy_ssl_url","alias"))]
   if markers:raise ValueError("Single-attempt marker already in Netlify: "+str(markers))
   report["status"]="PASS_SAFE_ONE_TINY_REVIEW_DRAFT"
  else:
   before=json.loads(prior_path.read_text("utf8"))
   if before.get("status")!="PASS_SAFE_ONE_TINY_REVIEW_DRAFT":raise ValueError("Prior safety gate not PASS")
   if current_review!=before.get("review_published_id"):
    raise ValueError("Existing Review published deploy changed")
   ds=get("sites/"+REVIEW+"/deploys?per_page=100")
   matches=[d for d in ds if MARKER in " ".join(str(d.get(x) or "") for x in ("title","name","alias")) or
      ALIAS in " ".join(str(d.get(x) or "") for x in ("deploy_url","deploy_ssl_url","alias"))]
   report["matches"]=len(matches)
   if len(matches)!=1:raise ValueError("Expected one draft, actual "+str(len(matches)))
   d=get("sites/"+REVIEW+"/deploys/"+matches[0]["id"])
   report["draft_id"]=d.get("id")
   report["draft_state"]=d.get("state")
   report["draft_context"]=d.get("context")
   report["draft_error"]=d.get("error_message")
   report["draft_published_at"]=d.get("published_at")
   url=d.get("deploy_ssl_url") or d.get("deploy_url") or ""
   if not url.startswith("https://") or not url.endswith(".netlify.app"):
    raise ValueError("Unexpected draft URL")
   report["draft_url"]=url
   if d.get("id")==current_review or d.get("id")==current_prod or d.get("published_at"):
    raise ValueError("Draft was published! HOLD")
   report["status"]="PASS_SMALL_DRAFT_READY_UNPUBLISHED" if d.get("state")=="ready" else "HOLD_SMALL_DRAFT_NOT_READY"
 except Exception as e:
  report["issues"].append(type(e).__name__+": "+str(e)[:260])
  report["status"]="HOLD_SMALL_DRAFT_SAFETY"
 (OUT/("PREUPLOAD.json" if a.mode=="before" else "AFTER_DRAFT.json")).write_text(
    json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("SMALL_ONE_DRAFT_API_GATE",json.dumps(report,ensure_ascii=False),flush=True)
 return 0 if report["status"].startswith("PASS_") or a.mode=="after" else 1
if __name__=="__main__":raise SystemExit(main())
