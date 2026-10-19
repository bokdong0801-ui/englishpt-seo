#!/usr/bin/env python3
"""GET-only safety gate around exactly ONE unpublished GSC-tag Draft.
Approved site stays on existing published v23.5.2.1. No form posts, site writes or publishes.
"""
import argparse,datetime,hashlib,json,os,pathlib,urllib.request
PROD="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
BASELINE="6ad5ca0f1f2051f04bdd9287"
OLD_BACKUP="6ac4bd517c30220008bb9661"
CHANGED_SHA="3ee78c417da2a91bc6f86d2cfd0c4be6c196334a0eaa89a222d99e83365a2acb"
MARKER="ENPT-GSC-TAG-HOME-DRAFT-ONCE-20261019"
ALIAS="enptgscmetaonceoct19"
DIR=pathlib.Path("gsc-draft-evidence")
DIR.mkdir(exist_ok=True)
def sha(path):
 h=hashlib.sha256()
 with open(path,"rb") as f:
  for data in iter(lambda:f.read(2*1024*1024),b""):h.update(data)
 return h.hexdigest()
def get(path):
 token=os.environ.get("NETLIFY_AUTH_TOKEN")
 if not token:raise ValueError("Missing token")
 req=urllib.request.Request("https://api.netlify.com/api/v1/"+path,method="GET",
  headers={"Authorization":"Bearer "+token,"Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)
def match(d):
 s=" ".join(str(d.get(k) or "") for k in ("title","name","alias","deploy_url","deploy_ssl_url"))
 return MARKER in s or ALIAS in s
def main():
 p=argparse.ArgumentParser();p.add_argument("--phase",choices=("before","after"),required=True)
 p.add_argument("--tar",default="");a=p.parse_args()
 r={"status":"HOLD","phase":a.phase,"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
   "site_id":PROD,"expected_live_baseline":BASELINE,"expected_changed_SHA":CHANGED_SHA,
   "no_Netlify_writes":True,"no_new_Production_published":True,"no_email_sent":True,
   "errors":[]}
 try:
  site=get("sites/"+PROD)
  if site.get("id")!=PROD or site.get("custom_domain")!="englishpt.kr":
   raise ValueError("Wrong site/domain")
  live=(site.get("published_deploy") or {}).get("id")
  r["actual_live_published_ID"]=live
  if live!=BASELINE:raise ValueError("Production drift. Abort Draft.")
  if (site.get("processing_settings") or {}).get("ignore_html_forms") is not False:
   raise ValueError("Forms detection unexpectedly disabled")
  old=get("sites/"+PROD+"/deploys/"+OLD_BACKUP)
  if old.get("state")!="ready":raise ValueError("Original rollback pointer not READY")
  source=get("sites/"+PROD+"/deploys/"+BASELINE)
  if source.get("state")!="ready":raise ValueError("Current Production baseline not READY")
  acc=get("accounts/"+site["account_id"])
  cr=(acc.get("capabilities") or {}).get("credits") or {}
  r["credits_remaining"]=cr.get("included",0)-cr.get("used",0)
  if (r["credits_remaining"]<=0 or acc.get("in_operational_mode") is True or
      acc.get("usages_exceeded") or acc.get("configurable_limits_exceeded")):
   raise ValueError("Netlify account not available")
  d=get("sites/"+PROD+"/deploys?per_page=100")
  matches=[item for item in d if match(item)]
  r["existing_marker_count"]=len(matches)
  if a.phase=="before":
   if matches:raise ValueError("Already attempted this exact Draft; NEVER retry")
   if not a.tar or sha(a.tar)!=CHANGED_SHA:
    raise ValueError("Wrong exact GSC-only candidate SHA")
   r["status"]="PASS_PRE_GSC_DRAFT_ONE_APPROVED_NO_PRODUCTION"
  else:
   if len(matches)!=1:raise ValueError("Exactly one matching Draft expected")
   dep=get("sites/"+PROD+"/deploys/"+matches[0]["id"])
   u=dep.get("deploy_ssl_url") or dep.get("deploy_url") or ""
   if not u.startswith("https://") or not u.endswith(".netlify.app"):
    raise ValueError("Bad immutable Draft URL")
   if dep.get("id")==live or dep.get("published_at"):
    raise ValueError("Unexpected Draft publication")
   r["draft_url"]=u;r["draft_id"]=dep.get("id")
   r["draft_state"]=dep.get("state");r["draft_error"]=dep.get("error_message")
   r["status"]="PASS_GSC_HOME_DRAFT_READY_UNPUBLISHED" if dep.get("state")=="ready" else "HOLD_DRAFT_NOT_READY"
 except Exception as exc:
  r["status"]="HOLD_GSC_DRAFT_SAFETY"
  r["errors"].append(type(exc).__name__+": "+str(exc)[:200])
 (DIR/("GSC_DRAFT_BEFORE.json" if a.phase=="before" else "GSC_DRAFT_AFTER.json")).write_text(
  json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("GSC_META_ONLY_DRAFT_GETONLY_VERDICT",json.dumps(r,ensure_ascii=False),flush=True)
 return 0 if r["status"].startswith("PASS_") or a.phase=="after" else 1
if __name__=="__main__":raise SystemExit(main())
