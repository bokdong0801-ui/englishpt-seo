#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""READ-ONLY authorization gate for EXACTLY ONE v23.5.2.1 Netlify Production deploy.
No write requests, no form submissions, no production deployment in this file.
Fail closed if current original production, account, Forms setting or artifact proofs differ.
"""
import datetime as dt
import hashlib, json, os, sys, urllib.request
from pathlib import Path
from zipfile import ZipFile
SITE_ID="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
REVIEW_ID="803550a8-03af-4776-bc8a-bd0bae85f5c7"
OLD_DEPLOY="6ac4bd517c30220008bb9661"
BACKUP_SHA="b490c4a19cb4deb04d3c6dd5927446cbda879991ba581e4654f2d5462686bac5"
NEW_ARCHIVE_SHA="e06c6a7b33a3042c9c52e73e95f1ed8a25819dde8584873f939fa14cff9c4bba"
EXPECTED_JS="d604994a74352a81978002fd6f6286c7d0f4f4c99278745bbf6dad1abce29ede"
RUN_FINAL=38992648694
RUN_BACKUP=39005690268
APPROVED_RELEASE="ENGLISH PT v23.5.2.1 englishpt.kr Production 1회, 사전 검증 통과 시만 배포"
OUT=Path("production-release-evidence")
OUT.mkdir(exist_ok=True)

def api(url, token):
    req=urllib.request.Request(url,headers={"Authorization":"Bearer "+token,
          "Accept":"application/json","User-Agent":"englishpt-v23521-one-time-prelaunch-GET"},method="GET")
    with urllib.request.urlopen(req,timeout=40) as resp:
        return json.load(resp)

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        while b:=f.read(4*1024*1024):h.update(b)
    return h.hexdigest()

def must(ok, reason):
    if not ok: raise RuntimeError(reason)

def main():
    report={"status":"HOLD_PREDEPLOY_CHECK_NOT_COMPLETE",
      "checked_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
      "approval":APPROVED_RELEASE,
      "target_site_id":SITE_ID,"expected_original_deploy_id":OLD_DEPLOY,
      "release_sha256":NEW_ARCHIVE_SHA,
      "rollback_zip_sha256":BACKUP_SHA,
      "production_deployed":False,
      "form_submissions":0,
      "netlify_mutations":0,
      "checks":[],"errors":[]}
    try:
        must(os.getenv("GITHUB_RUN_ATTEMPT")=="1","This workflow was rerun; a second Production attempt is forbidden")
        must(os.getenv("GITHUB_REF")=="refs/heads/release/v23521-approved-production-once-20261017",
             "Wrong branch for authorized release")
        must(os.getenv("GITHUB_REPOSITORY")=="bokdong0801-ui/englishpt-seo","Wrong repository")
        token=os.environ["NETLIFY_AUTH_TOKEN"]
        gh=os.environ["GH_TOKEN"]
        must(len(token)>10 and len(gh)>10,"API credentials missing")
        final=Path("frozen-source/ENGLISHPT_v23.5.2.1_JSFIX_PRODUCTION_READY_NOT_DEPLOYED.tar.zst")
        backup=Path("verified-original-backup/ENGLISHPT_ORIGINAL_PRODUCTION_"+OLD_DEPLOY+".zip")
        must(final.is_file() and sha(final)==NEW_ARCHIVE_SHA,"Frozen final candidate archive SHA256 mismatch")
        must(backup.is_file() and sha(backup)==BACKUP_SHA,"Original Production ZIP SHA256 mismatch")
        with ZipFile(backup) as z:
            files=z.namelist()
            must(len(files)==1791 and len(set(files))==1791,"Original backup file count/duplicates failed")
            must(z.testzip() is None,"Original backup ZIP integrity error")
            must("index.html" in files,"Original Production backup missing index.html")
        report["checks"].append("full_original_production_independent_zip_1791_SHA_CRC")
        candidate_run=api("https://api.github.com/repos/bokdong0801-ui/englishpt-seo/actions/runs/"+str(RUN_FINAL),gh)
        backup_run=api("https://api.github.com/repos/bokdong0801-ui/englishpt-seo/actions/runs/"+str(RUN_BACKUP),gh)
        must(candidate_run.get("conclusion")=="success" and backup_run.get("conclusion")=="success",
             "Provenance workflow not successful")
        for artifact_id, expected in (
          (12085981996,"englishpt-v23521-JSFIX-PRODUCTION-READY-158571-NOT-DEPLOYED"),
          (12091475871,"englishpt-v23521-OLD-PRODUCTION-ORIGINAL-FULL-SHA-VERIFIED-BACKUP")
        ):
            a=api("https://api.github.com/repos/bokdong0801-ui/englishpt-seo/actions/artifacts/"+str(artifact_id),gh)
            must(a.get("name")==expected and a.get("expired") is False,
                 "Source or backup GitHub artifact unavailable")
        report["checks"].append("source_and_full_backup_provenance_unexpired")
        site=api("https://api.netlify.com/api/v1/sites/"+SITE_ID,token)
        must(site.get("id")==SITE_ID and site.get("custom_domain")=="englishpt.kr" and site.get("state")=="current",
             "Wrong Netlify Production site/domain/state")
        must(site.get("disabled") is not True,"Netlify site disabled")
        must(site.get("id")!=REVIEW_ID,"Review site ID substituted for Production")
        must((site.get("published_deploy") or {}).get("id")==OLD_DEPLOY,
             "Published Production deploy ID changed; refuse to overwrite an unexpected new release")
        old=api("https://api.netlify.com/api/v1/sites/"+SITE_ID+"/deploys/"+OLD_DEPLOY,token)
        must(old.get("id")==OLD_DEPLOY and old.get("state")=="ready" and old.get("context")=="production",
             "Rollback deploy no longer restorable/ready")
        report["checks"].append("production_site_identity_current_published_deploy_and_ready_rollback")
        process=site.get("processing_settings") or {}
        must(isinstance(process,dict) and process.get("ignore_html_forms") is False,
             "Form detection must be enabled; do not deploy")
        report["checks"].append("production_Form_detection_enabled")
        account=api("https://api.netlify.com/api/v1/accounts/"+site["account_id"],token)
        cred=(account.get("capabilities") or {}).get("credits") or {}
        used=cred.get("used");total=cred.get("included")
        must(isinstance(used,(float,int)) and isinstance(total,(float,int)) and total-used>=15,
             "Insufficient confirmed Netlify credits for one production deploy")
        must(account.get("in_operational_mode") is False and not account.get("usages_exceeded")
          and not account.get("configurable_limits_exceeded"),"Netlify credit restriction now reported")
        report["netlify_credit_remaining_before_release"]=total-used
        report["checks"].append("Netlify_account_credit_and_limits")
        hooks=api("https://api.netlify.com/api/v1/hooks?site_id="+SITE_ID,token)
        must(any(x.get("event")=="submission_created" and x.get("type")=="email" for x in hooks),
             "No existing email notification hook; stop before deployment")
        report["checks"].append("email_notification_hook_configured_not_delivery_verified")
        forms=api("https://api.netlify.com/api/v1/sites/"+SITE_ID+"/forms",token)
        must(isinstance(forms,list),"Cannot inspect current forms")
        report["current_old_site_registered_forms"]=len(forms)
        page=Path("candidate-site/pilot.js")
        must(page.is_file() and sha(page)==EXPECTED_JS,"Unpacked Production JS does not match final patch")
        h=(Path("candidate-site")/"_headers").read_text("utf8")
        must("X-Robots-Tag: noindex" not in h,"Review noindex header leaked to Production")
        report["checks"].append("unpacked_corrected_Javascript_and_production_headers")
        report["status"]="PASS_FINAL_ONE_SHOT_PRODUCTION_AUTHORIZATION_GATE"
    except Exception as exc:
        report["status"]="HOLD_FINAL_ONE_SHOT_PRODUCTION_AUTHORIZATION_GATE"
        report["errors"].append(type(exc).__name__+": "+str(exc)[:220])
    finally:
        (OUT/"FROZEN_PREDEPLOY_AUTHORIZATION_GATE.json").write_text(
            json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print(report["status"],"checks",report["checks"],"errors",report["errors"],flush=True)
    return 0 if report["status"].startswith("PASS_") else 1

if __name__=="__main__":sys.exit(main())
