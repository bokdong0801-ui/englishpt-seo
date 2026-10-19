#!/usr/bin/env python3
"""Forensic GET-only Netlify canceled deploy, no new deploy, POST, billing, or Forms submissions."""
import os,json,urllib.request,urllib.error,datetime,hashlib,collections,sys
from pathlib import Path
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
FAILED="6ad30d01781992bcb8dd92a1"
OLD="6ac4bd517c30220008bb9661"
BASE="https://api.netlify.com/api/v1"
ROOT=Path("failed-deploy-forensic");ROOT.mkdir(exist_ok=True)
def read(endpoint,cap=120000000):
 req=urllib.request.Request(BASE+endpoint,headers={"Authorization":"Bearer "+os.environ["NETLIFY_AUTH_TOKEN"],"Accept":"application/json"},method="GET")
 try:
  with urllib.request.urlopen(req,timeout=100) as res:
   b=res.read(cap+1)
   if len(b)>cap: return None,{"http":res.status,"truncated":True}
   return json.loads(b),{"http":res.status,"bytes":len(b),"link":res.headers.get("Link"),"total":res.headers.get("X-Total-Count")}
 except urllib.error.HTTPError as e:return None,{"http":e.code,"error":"HTTPError"}
 except Exception as e:return None,{"error":type(e).__name__}
def summarize_deploy(d):
 if not isinstance(d,dict):return {}
 fields=("id","site_id","state","context","created_at","updated_at","published_at","deploy_time","retrying","error_message","framework","build_id","review_id","draft","locked","ready","required","required_functions","uploading","uploaded","skipped","warnings","processing","branch","commit_ref","total_files","file_count","file_size","upload_seconds","deploy_ssl_url","deploy_url","url","summary")
 out={}
 for f in fields:
  if f not in d:continue
  v=d[f]
  if isinstance(v,list):out[f+"_count"]=len(v)
  elif isinstance(v,dict):out[f+"_keys"]=list(v)[:25]
  elif isinstance(v,(str,int,bool,float)) or v is None:out[f]=v
 out["available_key_names"]=sorted(d.keys())
 return out
def main():
 report={"status":"GET_ONLY_DIAGNOSTIC","target_failed_deploy_id":FAILED,"previous_published_deploy_id":OLD,
  "checked_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"Netlify_writes":0,"form_submissions":0,"deployments_created":0,"queries":{}}
 site,sm=read("/sites/"+SITE);report["queries"]["site"]=sm
 if site:
  report["current_published_deploy_id"]=(site.get("published_deploy") or {}).get("id")
  report["old_still_published"]=report["current_published_deploy_id"]==OLD
  report["production_form_detection_enabled"]=(site.get("processing_settings") or {}).get("ignore_html_forms") is False
 for name,endpoint in (("failed_deploy_global","/deploys/"+FAILED),
                      ("failed_deploy_site","/sites/"+SITE+"/deploys/"+FAILED),
                      ("existing_old_production","/sites/"+SITE+"/deploys/"+OLD)):
  payload,meta=read(endpoint)
  report["queries"][name]=meta
  if payload: report[name]=summarize_deploy(payload)
 # Try the immutable FAILED deploy manifest, not the current 1,791-file published site manifest.
 data,meta=read("/deploys/"+FAILED+"/files",cap=120000000)
 report["queries"]["failed_deploy_files"]=meta
 if isinstance(data,list):
  paths=[v.get("path") or v.get("id") for v in data]
  paths=[str(p).lstrip("/") for p in paths if p]
  count_root=sum("/" not in p for p in paths)
  ext=collections.Counter((p.rsplit(".",1)[-1].lower() if "." in p else "(none)") for p in paths)
  report["failed_deploy_file_inventory"]={
   "returned_count":len(data),
   "root_entries":count_root,
   "html_count":sum(p.endswith(".html") for p in paths),
   "extension_counts_top20":ext.most_common(20),
   "known_files_present":{p:p in paths for p in ("index.html","pilot.js","gyeongnam-milyang-naeidong-elem-tutor.html","robots.txt")},
   "list_has_more_pages":bool(meta.get("link") and 'rel="next"' in meta.get("link","")),
   "total_header":meta.get("total"),
   "file_digest_of_response":hashlib.sha256(json.dumps(paths,ensure_ascii=False).encode("utf8")).hexdigest()}
  report["failed_deploy_manifest_partial_if_canceled"]=True
 else:report["failed_deploy_file_inventory"]="INACCESSIBLE_OR_PENDING"
 report["status"]="PASS_READONLY_FORENSIC" if report.get("old_still_published") and "failed_deploy_site" in report else "HOLD_UNKNOWN_STATE"
 (ROOT/"FAILED_NETLIFY_DEPLOY_FORENSIC_REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("FAILED_PRODUCTION_DEPLOY_FORENSIC",json.dumps(report,ensure_ascii=False),flush=True)
 return 0
if __name__=="__main__":sys.exit(main())
