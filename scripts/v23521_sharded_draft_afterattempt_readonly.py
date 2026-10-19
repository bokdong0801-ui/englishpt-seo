#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only after ONE approved Netlify CLI Draft attempt. No retry and no publish."""
import datetime,json,os,pathlib,sys,urllib.parse,urllib.request
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
OLD="6ac4bd517c30220008bb9661"
MARKER="ENGLISHPT_V23521_SHARDED_DRAFT_REAPPROVED_ONCE_20261019"
ALIAS="enptv23521shardretry1"
OUT=pathlib.Path("approved-draft-evidence")
OUT.mkdir(exist_ok=True)
def fetch(u):
  req=urllib.request.Request(u,headers={"Authorization":"Bearer "+os.environ["NETLIFY_AUTH_TOKEN"],"Accept":"application/json"},method="GET")
  with urllib.request.urlopen(req,timeout=50) as r:return json.load(r)
def main():
 result={"status":"HOLD_DRAFT_AFTER_ATTEMPT","run_scope":"ONE_NONPUBLISHED_DRAFT",
         "time_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "Netlify_write_requests_by_this_check":0,"production_deployed_by_this_check":False,
         "form_submissions_by_this_check":0,"old_production_expected_id":OLD,
         "draft_id":None,"draft_url":None,"issues":[]}
 try:
  site=fetch("https://api.netlify.com/api/v1/sites/"+SITE)
  if site.get("id")!=SITE:raise ValueError("Unexpected site ID")
  published=(site.get("published_deploy") or {}).get("id")
  result["actual_published_deploy_id"]=published
  if published!=OLD:raise ValueError("Production changed; stop all activities!")
  result["existing_production_unmodified"]=True
  deploys=fetch("https://api.netlify.com/api/v1/sites/"+SITE+"/deploys?per_page=100")
  matches=[]
  for d in deploys:
   ident=" ".join(str(d.get(k) or "") for k in ("title","name","alias","deploy_url","deploy_ssl_url"))
   if MARKER in ident or ALIAS in ident:matches.append(d)
  result["attempt_marker_matched_deploy_count"]=len(matches)
  if len(matches)!=1:
   raise ValueError("Expected exactly one Draft deploy with unique marker, got "+str(len(matches)))
  dep=matches[0]
  result["draft_id"]=dep.get("id")
  result["draft_state"]=dep.get("state")
  result["draft_context"]=dep.get("context")
  result["draft_draft_flag"]=dep.get("draft")
  result["draft_published_at"]=dep.get("published_at")
  result["draft_error"]=dep.get("error_message")
  details=fetch("https://api.netlify.com/api/v1/sites/"+SITE+"/deploys/"+dep["id"])
  result["draft_summary_status"]=(details.get("summary") or {}).get("status")
  result["draft_edge_function_count"]=len(details.get("edge_functions") or [])
  url=dep.get("deploy_ssl_url") or dep.get("deploy_url") or dep.get("ssl_url")
  if not url:
   raise ValueError("Netlify Draft URL absent in API")
  parsed=urllib.parse.urlsplit(url)
  if parsed.scheme!="https" or not parsed.hostname or not parsed.hostname.endswith(".netlify.app"):
   raise ValueError("Unsafe or unexpected Draft URL")
  result["draft_url"]=url
  forms=fetch("https://api.netlify.com/api/v1/sites/"+SITE+"/forms")
  result["registered_form_names"]=sorted(set(f.get("name") for f in forms if f.get("name")))
  result["expected_form_registered"]="englishpt-consultation" in result["registered_form_names"]
  if dep.get("state")!="ready":
   result["status"]="HOLD_NETLIFY_DRAFT_NOT_READY_NO_RETRY"
  elif dep.get("id")==published or dep.get("published_at"):
   raise ValueError("Unexpectedly published deploy; must stop")
  else:
   result["status"]="PASS_DRAFT_READY_NOT_PUBLISHED_READY_FOR_HTTP_QA"
 except Exception as exc:
  result["issues"].append(type(exc).__name__+": "+str(exc)[:350])
 path=OUT/"AFTER_ATTEMPT_NETLIFY_DRAFT_STATUS.json"
 path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("ONE_APPROVED_DRAFT_ACTUAL_NETLIFY_STATUS",json.dumps(result,ensure_ascii=False),flush=True)
 if result["status"]=="PASS_DRAFT_READY_NOT_PUBLISHED_READY_FOR_HTTP_QA":
  with open(os.environ["GITHUB_OUTPUT"],"a") as f:
   f.write("draft_url="+result["draft_url"]+"\n")
   f.write("draft_id="+result["draft_id"]+"\n")
   f.write("ready=yes\n")
 return 0
if __name__=="__main__":sys.exit(main())
