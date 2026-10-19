#!/usr/bin/env python3
"""Publish exact approved Netlify Draft once; no retries or uploads. Confirm with GET."""
import os,json,hashlib,urllib.request,urllib.error,time,datetime,pathlib,zipfile,sys
S="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
OLD="6ac4bd517c30220008bb9661"
NEW="6ad5ca0f1f2051f04bdd9287"
SRC_SHA="0f72556e20ed2e22b45f144b4ccf687937e1b15cedc4d2dd109819fef65db7e8"
BAK_SHA="b490c4a19cb4deb04d3c6dd5927446cbda879991ba581e4654f2d5462686bac5"
OUT=pathlib.Path("publish-evidence");OUT.mkdir(exist_ok=True)
TOKEN=os.environ.get("NETLIFY_AUTH_TOKEN","")
def get(path):
 req=urllib.request.Request("https://api.netlify.com/api/v1/"+path,method="GET",headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)
def checksum(path):
 h=hashlib.sha256()
 with open(path,"rb") as f:
  for b in iter(lambda:f.read(2*1024*1024),b""):h.update(b)
 return h.hexdigest()
def save(name,v):
 (OUT/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def main():
 r={"status":"HOLD","approved_exactly_one":True,"post_count":0,"new_uploads":0,"real_form_posts":0,
    "source_deploy_id":NEW,"original_published_id":OLD,"checked_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "errors":[],"checks":[]}
 try:
  if os.environ.get("PUBLISH_APPROVED_ONCE")!="EXACT_V23521_USER_APPROVED_20261019":
   raise ValueError("Explicit one-time authorization guard missing")
  if not TOKEN:raise ValueError("Missing Netlify token")
  if checksum(os.environ["RELEASE_ARCHIVE"])!=SRC_SHA:raise ValueError("Source archive SHA mismatch")
  if checksum(os.environ["BACKUP_ZIP"])!=BAK_SHA:raise ValueError("Original rollback ZIP SHA mismatch")
  with zipfile.ZipFile(os.environ["BACKUP_ZIP"]) as z:
   if len(z.namelist())!=1791 or z.testzip() is not None:raise ValueError("Rollback ZIP corrupt")
  r["checks"].append("Immutable release SHA and portable original rollback backup CRC")
  site=get("sites/"+S)
  if site.get("id")!=S or site.get("custom_domain")!="englishpt.kr":raise ValueError("Wrong site/domain")
  r["live_before"]=(site.get("published_deploy") or {}).get("id")
  if r["live_before"]!=OLD:raise ValueError("Published deploy drifted before publish")
  if (site.get("processing_settings") or {}).get("ignore_html_forms") is not False:
   raise ValueError("Netlify Forms detection not enabled")
  old=get("sites/"+S+"/deploys/"+OLD)
  target=get("sites/"+S+"/deploys/"+NEW)
  if old.get("state")!="ready":raise ValueError("Old rollback not ready")
  if target.get("id")!=NEW or target.get("site_id")!=S or target.get("state")!="ready" or target.get("published_at"):
   raise ValueError("Approved Draft not ready or already published")
  r["checks"].append("Exact Netlify production site, old rollback and READY unpublished target")
  account=get("accounts/"+site["account_id"])
  cr=(account.get("capabilities") or {}).get("credits") or {}
  r["credits_left"]=cr.get("included",0)-cr.get("used",0)
  if r["credits_left"]<=0 or account.get("in_operational_mode") is True or account.get("usages_exceeded") or account.get("configurable_limits_exceeded"):
   raise ValueError("Netlify account limits not green")
  r["checks"].append("Netlify ordinary credits and forms detection")
  r["status"]="GO_IMMEDIATE_PREPUBLISH"
  save("PREPUBLISH_EXACT_GO.json",r.copy())
  r["post_count"]=1
  save("EXACTLY_ONE_PUBLISH_POST_MARKER.json",r.copy())
  # ONE authorized POST. Do not retry, including on an ambiguous timeout.
  try:
   req=urllib.request.Request("https://api.netlify.com/api/v1/sites/"+S+"/deploys/"+NEW+"/restore",
        headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"},
        method="POST",data=b"")
   with urllib.request.urlopen(req,timeout=45) as response:r["restore_http_status"]=response.status
  except urllib.error.HTTPError as e:r["errors"].append("restore_HTTP_"+str(e.code)+"_verify_GET_no_retry")
  except Exception as e:r["errors"].append("restore_uncertain_"+type(e).__name__+"_verify_GET_no_retry")
  for n in range(12):
   site=get("sites/"+S)
   r["live_after"]=(site.get("published_deploy") or {}).get("id")
   if r["live_after"]==NEW:
    r["status"]="PASS_APPROVED_EXACT_TARGET_PUBLISHED"
    break
   if r["live_after"]!=OLD:
    r["status"]="HOLD_UNEXPECTED_PUBLISHED_ID"
    break
   if n<11:time.sleep(3)
  else:r["status"]="HOLD_RESTORE_NOT_CONFIRMED_NO_RETRY"
 except Exception as e:
  r["status"]="HOLD_NO_FURTHER_POST"
  r["errors"].append(type(e).__name__+": "+str(e)[:220])
 save("PUBLISH_ACTUAL_RESULT.json",r)
 print("PRODUCTION_ONE_APPROVED_PUBLISH",json.dumps(r,ensure_ascii=False),flush=True)
 return 0 if r["status"]=="PASS_APPROVED_EXACT_TARGET_PUBLISHED" else 1
if __name__=="__main__":sys.exit(main())
