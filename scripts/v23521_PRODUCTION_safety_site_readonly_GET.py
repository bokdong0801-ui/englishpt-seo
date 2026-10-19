#!/usr/bin/env python3
"""Final ENGLISH PT release safety inventory. GET-only and sanitized outputs.
Does NOT deploy, change settings, send Forms, publish, or submit to engines.
"""
import datetime as dt, hashlib, json, os, pathlib, sys, urllib.request, urllib.error
PROD="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
REVIEW="803550a8-03af-4776-bc8a-bd0bae85f5c7"
OLD="6ac4bd517c30220008bb9661"
READY_REVIEW="6ad5bd194b108d5fa1bc1eac"
ZIP_SHA="b490c4a19cb4deb04d3c6dd5927446cbda879991ba581e4654f2d5462686bac5"
CAND_SHA="0f72556e20ed2e22b45f144b4ccf687937e1b15cedc4d2dd109819fef65db7e8"
OUT=pathlib.Path("production-final-safety");OUT.mkdir(exist_ok=True)
TOKEN=os.environ.get("NETLIFY_AUTH_TOKEN","")
def get_api(path):
    req=urllib.request.Request("https://api.netlify.com/api/v1/"+path,headers={
      "Authorization":"Bearer "+TOKEN,"Accept":"application/json",
      "User-Agent":"ENGLISHPT-v23521-final-safety-GET-only"},method="GET")
    with urllib.request.urlopen(req,timeout=50) as r:return json.load(r)
def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
      for block in iter(lambda:f.read(2*1024*1024),b""):h.update(block)
    return h.hexdigest()
def assertion(cond,msg):
    if not cond:raise ValueError(msg)
def main():
    r={"state":"HOLD","time_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
       "site_id":PROD,"review_site_id":REVIEW,"old_Production_deploy_id":OLD,
       "expected_review_deploy_id":READY_REVIEW,
       "netlify_methods":["GET"],"netlify_mutations":0,"form_submissions":0,
       "production_published":False,"search_registration":False,
       "passes":[],"blocks":[],"manual_after_launch":[]}
    try:
        assertion(bool(TOKEN),"Netlify token missing")
        r["candidate_sha256"]=sha256(os.environ["PRODUCTION_CANDIDATE_TAR"])
        assertion(r["candidate_sha256"]==CAND_SHA,"Production candidate sha mismatch")
        r["passes"].append("immutable_Payload_Production_archive_sha256")
        r["old_zip_sha256"]=sha256(os.environ["ORIGINAL_PRODUCTION_BACKUP_ZIP"])
        assertion(r["old_zip_sha256"]==ZIP_SHA,"old rollback ZIP changed")
        import zipfile
        with zipfile.ZipFile(os.environ["ORIGINAL_PRODUCTION_BACKUP_ZIP"]) as z:
            assertion(len(z.namelist())==1791,"old backup not exactly 1791 files")
            assertion(z.testzip() is None,"old backup CRC failure")
        r["passes"].append("original_1791_file_full_zip_and_sha256")
        prod=get_api("sites/"+PROD)
        assertion(prod.get("id")==PROD and prod.get("custom_domain")=="englishpt.kr","Wrong Production target")
        cur=(prod.get("published_deploy") or {}).get("id")
        r["actual_Production_published_id"]=cur
        assertion(cur==OLD,"Published Production unexpectedly changed")
        d=get_api("sites/"+PROD+"/deploys/"+OLD)
        assertion(d.get("id")==OLD and d.get("state")=="ready" and d.get("context")=="production",
                  "Old rollback state/context not ready")
        r["passes"].append("old_live_Production_ID_and_immutable_restore_pointer")
        r["forms_detection_processing_ignore_html_forms"]=(prod.get("processing_settings") or {}).get("ignore_html_forms")
        assertion(r["forms_detection_processing_ignore_html_forms"] is False,
                  "Production Forms detection not explicitly enabled")
        r["passes"].append("Production_Forms_detection_enabled")
        account=get_api("accounts/"+prod["account_id"])
        cr=(account.get("capabilities") or {}).get("credits") or {}
        r["credits_included"]=cr.get("included")
        r["credits_used"]=cr.get("used")
        r["credits_calculated_remaining"]=None if cr.get("included") is None or cr.get("used") is None else cr["included"]-cr["used"]
        r["account_operational_mode"]=account.get("in_operational_mode")
        r["account_usages_exceeded_count"]=len(account.get("usages_exceeded") or [])
        r["account_configurable_limits_exceeded_count"]=len(account.get("configurable_limits_exceeded") or [])
        assertion(r["credits_calculated_remaining"] is not None and r["credits_calculated_remaining"]>0
          and r["account_operational_mode"] is False
          and r["account_usages_exceeded_count"]==0 and r["account_configurable_limits_exceeded_count"]==0,
          "Netlify credits/limits not green")
        r["passes"].append("positive_credit_no_limit_exceeded")
        review=get_api("sites/"+REVIEW)
        assertion(review.get("id")==REVIEW and review.get("account_id")==prod.get("account_id"),
                  "Review wrong site/account")
        ready=get_api("sites/"+REVIEW+"/deploys/"+READY_REVIEW)
        assertion(ready.get("id")==READY_REVIEW and ready.get("state")=="ready"
                  and not ready.get("published_at"),"Full-scale Review not ready as Draft")
        r["passes"].append("full_scale_Review_draft_READY_not_published")
        forms=get_api("sites/"+PROD+"/forms")
        assertion(isinstance(forms,list),"Netlify Forms inventory response invalid")
        r["registered_Production_Forms_count"]=len(forms)
        r["expected_form_already_registered"]="englishpt-consultation" in [f.get("name") for f in forms]
        # Form registration on old site does NOT establish the new blueprint/email pipeline.
        r["manual_after_launch"].extend([
          "Recheck form registration for englishpt-consultation after new deploy",
          "Confirm existing submission_created email hook is targeting intended inbox",
          "Perform exactly one authorized real consultation POST and verify inbox delivery",
          "Submit sitemap to Google Search Console/Naver only after production post-launch QA"
        ])
        # GET-only hook metadata; NEVER print hook config/URLs/email addresses.
        hooks=get_api("hooks?site_id="+PROD)
        assertion(isinstance(hooks,list),"Could not read Netlify site hook list")
        r["site_hooks_found"]=len(hooks)
        r["email_submission_created_hook_count"]=sum(1 for h in hooks if
          h.get("event")=="submission_created" and h.get("type")=="email")
        r["hook_metadata_support"]="metadata_only_no_recipient_or_content_exposed"
        # a global event hook can be unscoped: record accurately but don't infer deliverability.
        r["passes"].append("Forms_registered_inventory_and_notification_hook_metadata_read")
        r["state"]="PASS_NETLIFY_SITE_BACKUP_CREDIT_REVIEW_FORMS_READONLY"
    except Exception as e:
        r["blocks"].append(type(e).__name__+": "+str(e)[:300])
        r["state"]="HOLD_NETLIFY_SITE_OR_BACKUP_PRECHECK"
    p=OUT/"SITE_BACKUP_FORMS_CREDIT_READONLY.json"
    p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("PRODUCTION_SITE_BACKUP_READONLY_FINAL",json.dumps(r,ensure_ascii=False),flush=True)
    return 0 if r["state"].startswith("PASS_") else 1
if __name__=="__main__":sys.exit(main())
