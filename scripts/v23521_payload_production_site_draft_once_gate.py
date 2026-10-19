#!/usr/bin/env python3
"""One approved nonpublished Draft on existing englishpt.kr SITE. GET only; no writes."""
import argparse,hashlib,json,os,pathlib,urllib.request,datetime
PROD="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
OLD="6ac4bd517c30220008bb9661"
CAND="0f72556e20ed2e22b45f144b4ccf687937e1b15cedc4d2dd109819fef65db7e8"
ZIP="b490c4a19cb4deb04d3c6dd5927446cbda879991ba581e4654f2d5462686bac5"
MARKER="ENGLISHPT_V23521_PRODUCTION_SITE_DRAFT_ONLY_ONCE_OCT19"
ALIAS="enpt23521prodfinaldraft1"
OUT=pathlib.Path("prod-draft-evidence");OUT.mkdir(exist_ok=True)
def api(path):
  req=urllib.request.Request("https://api.netlify.com/api/v1/"+path,method="GET",headers={
  "Authorization":"Bearer "+os.environ["NETLIFY_AUTH_TOKEN"],"Accept":"application/json"})
  with urllib.request.urlopen(req,timeout=40) as resp:return json.load(resp)
def sha(p):
  h=hashlib.sha256()
  with open(p,"rb") as f:
    for part in iter(lambda:f.read(2*1024*1024),b""):h.update(part)
  return h.hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument("--mode",choices=["before","after"],required=True)
 a.add_argument("--candidate",default="");a.add_argument("--backup",default="")
 args=a.parse_args()
 r={"status":"HOLD","checked_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "mode":args.mode,"site":PROD,"attempt_scope":"ONE_DRAFT_NO_PRODUCTION_PUBLICATION",
 "writes":0,"form_POSTs":0,"search_submissions":0,"issues":[]}
 try:
  site=api("sites/"+PROD)
  assert site["id"]==PROD and site.get("custom_domain")=="englishpt.kr"
  prev=(site.get("published_deploy") or {}).get("id")
  r["current_production_published"]=prev
  assert prev==OLD, "Live Production unexpectedly changed"
  assert (site.get("processing_settings") or {}).get("ignore_html_forms") is False, "Form detection OFF/unknown"
  prev_deploy=api("sites/"+PROD+"/deploys/"+OLD)
  assert prev_deploy.get("state")=="ready","Old restore pointer not ready"
  ds=api("sites/"+PROD+"/deploys?per_page=100")
  matches=[d for d in ds if MARKER in " ".join(str(d.get(k) or "") for k in ("title","name","alias")) or
        ALIAS in " ".join(str(d.get(k) or "") for k in ("deploy_url","deploy_ssl_url","alias"))]
  r["matching_approved_Drafts"]=len(matches)
  if args.mode=="before":
    assert not matches,"This one-time Draft attempt already exists; do not redeploy"
    assert sha(args.candidate)==CAND,"Wrong exact frozen Production-formatted archive SHA"
    assert sha(args.backup)==ZIP,"Wrong original 1791-file fallback ZIP SHA"
    credits=(api("accounts/"+site["account_id"]).get("capabilities") or {}).get("credits") or {}
    r["remaining_credit"]=credits.get("included",0)-credits.get("used",0)
    assert r["remaining_credit"]>0,"Netlify credits exhausted"
    r["status"]="PASS_ONE_PRODUCTION_SITE_DRAFT_PREUPLOAD_NO_PROD"
  else:
    assert len(matches)==1,"Expected precisely 1 approved Draft; no additional attempt"
    d=api("sites/"+PROD+"/deploys/"+matches[0]["id"])
    r["draft_id"]=d.get("id");r["draft_state"]=d.get("state")
    r["draft_error"]=d.get("error_message")
    r["draft_context"]=d.get("context")
    r["draft_published_at"]=d.get("published_at")
    u=d.get("deploy_ssl_url") or d.get("deploy_url") or ""
    r["draft_url"]=u
    assert u.startswith("https://") and u.endswith(".netlify.app"),"Untrusted Draft URL"
    assert not d.get("published_at") and d.get("id")!=prev,"Unexpected Draft publication"
    forms=api("sites/"+PROD+"/forms")
    r["form_registered_names"]=[f.get("name") for f in forms if f.get("name")]
    r["form_englishpt_consultation_registered"]="englishpt-consultation" in r["form_registered_names"]
    r["status"]="PASS_DRAFT_READY_NOT_PUBLISHED" if d.get("state")=="ready" else "HOLD_DRAFT_NOT_READY_OR_CANCELED"
 except Exception as e:
  r["issues"].append(type(e).__name__+": "+str(e)[:200])
  r["status"]="HOLD_DRAFT_GATE"
 (OUT/("PREUPLOAD.json" if args.mode=="before" else "ACTUAL_DRAFT_STATUS.json")).write_text(
  json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("PRODUCTION_SITE_DRAFT_ONCE_REAL_STATUS",json.dumps(r,ensure_ascii=False),flush=True)
 return 0 if r["status"].startswith("PASS_") or args.mode=="after" else 1
if __name__=="__main__":raise SystemExit(main())
