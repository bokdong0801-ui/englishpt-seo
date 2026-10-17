#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v23.5.2.1 Netlify production prelaunch READ-ONLY + current deploy rollback snapshot.
ONLY GET/HEAD HTTP; no POST/PUT/PATCH/DELETE. No form submissions or deployments.
Save only sanitized metadata. Original deployed artifact is NOT re-uploaded.
"""
import datetime as dt
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.netlify.com/api/v1"
DOMAIN = "https://englishpt.kr"
EXPECTED_SHA = "e06c6a7b33a3042c9c52e73e95f1ed8a25819dde8584873f939fa14cff9c4bba"
EXPECTED_RUN = 38992648694
SITE_EXPECTED_DOMAIN = "englishpt.kr"
OUT = Path("prelaunch-readonly-report")
OUT.mkdir(exist_ok=True)
now = dt.datetime.now(dt.timezone.utc).isoformat()

def get_json(url, token, required=True):
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
        "User-Agent": "ENGLISHPT-v23521-production-readonly-preflight"
    }, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            return json.load(resp), None
    except Exception as exc:
        if required:
            raise RuntimeError("GET request failed for approved API resource: " +
                               urllib.parse.urlsplit(url).path + " - " + type(exc).__name__ +
                               " " + str(getattr(exc, "code", "")))
        return None, type(exc).__name__ + " " + str(getattr(exc, "code", ""))

def get_public(path):
    url = DOMAIN + path
    req = urllib.request.Request(url, headers={
        "Accept": "*/*", "User-Agent": "ENGLISHPT-v23521-public-GET-only"
    }, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            # Limit extraction, no personal info, no POST.
            blob = resp.read(200000)
            return {
                "path": path, "http_status": resp.status,
                "final_host": urllib.parse.urlsplit(resp.geturl()).hostname,
                "content_type": resp.headers.get("Content-Type"),
                "x_robots_tag": resp.headers.get("X-Robots-Tag"),
                "bytes_sampled": len(blob),
                "sha256_sample": hashlib.sha256(blob).hexdigest(),
                "redirected": resp.geturl() != url
            }
    except urllib.error.HTTPError as exc:
        return {"path":path,"http_status":exc.code,"error":"HTTPError"}
    except Exception as exc:
        return {"path":path,"http_status":None,"error":type(exc).__name__}

def save(name, payload):
    (OUT / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf8")

def main():
    summary = {
        "status": "HOLD_PENDING_PRODUCTION_PREFLIGHT",
        "checked_at_utc": now,
        "candidate_run": EXPECTED_RUN, "candidate_sha256": EXPECTED_SHA,
        "production_deployed": False, "form_submitted": False,
        "netlify_write_requests": 0,
        "errors": [], "warnings": [], "pass_items": [],
        "blocking_items": [], "manual_hold_items": []
    }
    point = {"status":"NOT_YET_VERIFIED", "captured_at_utc":now,
             "is_separate_site_file_backup":False,
             "notes":"This is a Netlify immutable deploy restoration pointer, not an exported full-file backup.",
             "production_deployed":False}
    try:
        gh = os.environ.get("GH_TOKEN","")
        token = os.environ.get("NETLIFY_AUTH_TOKEN","")
        repo = os.environ.get("GITHUB_REPOSITORY","bokdong0801-ui/englishpt-seo")
        if not gh or not token:
            raise RuntimeError("Missing GitHub or Netlify READ-only credential for preflight")
        run, _ = get_json(
            "https://api.github.com/repos/" + repo + "/actions/runs/" + str(EXPECTED_RUN), gh)
        if run.get("conclusion")!="success" or run.get("status")!="completed":
            raise ValueError("Approved offline candidate run did not pass")
        arts, _=get_json(
            "https://api.github.com/repos/"+repo+"/actions/runs/"+str(EXPECTED_RUN)+"/artifacts",gh)
        expected_name="englishpt-v23521-JSFIX-PRODUCTION-READY-158571-NOT-DEPLOYED"
        matching=[a for a in arts.get("artifacts",[]) if a.get("name")==expected_name and not a.get("expired")]
        if len(matching)!=1:
            raise ValueError("Expected unexpired final Production candidate artifact missing")
        summary["candidate_artifact_id"]=matching[0]["id"]
        summary["pass_items"].append("approved_final_candidate_run_and_artifact")
        site,_=get_json(API+"/sites/"+SITE_EXPECTED_DOMAIN,token)
        site_id=site.get("id")
        if not site_id or not site.get("name"):
            raise ValueError("Unknown Netlify site")
        if site.get("custom_domain") not in (SITE_EXPECTED_DOMAIN,"www."+SITE_EXPECTED_DOMAIN):
            raise ValueError("Netlify site custom_domain not englishpt.kr")
        if site.get("disabled") is True:
            summary["blocking_items"].append("netlify_site_disabled")
        pd=site.get("published_deploy") or {}
        current_id=pd.get("id")
        if not current_id:
            summary["blocking_items"].append("no_published_deploy_id_to_restore")
        else:
            current,_=get_json(API+"/sites/"+site_id+"/deploys/"+current_id,token)
            if current.get("id")!=current_id or current.get("state") not in ("ready","current"):
                summary["blocking_items"].append("current_published_deploy_not_verified")
            else:
                point.update({
                    "status":"PASS_EXISTING_PUBLISHED_IMMUTABLE_DEPLOY_POINTER",
                    "site_id":site_id, "site_name":site.get("name"),
                    "domain":SITE_EXPECTED_DOMAIN,
                    "published_deploy_id":current_id,
                    "published_deploy_state":current.get("state"),
                    "published_at":current.get("published_at") or current.get("created_at"),
                    "deploy_permalink":current.get("deploy_url"),
                    "rollback_api_path":"/api/v1/sites/"+site_id+"/deploys/"+current_id+"/restore",
                    "rollback_method_NOT_EXECUTED":"POST",
                    "old_published_deploy_url":"https://app.netlify.com/sites/"+site.get("name")+
                        "/deploys/"+current_id,
                    "immutable_restore_point_metadata_captured":True
                })
                summary["pass_items"].append("current_published_deploy_restoration_pointer")
        account_id=site.get("account_id")
        account=None
        account_error=None
        if account_id:
            account,account_error=get_json(API+"/accounts/"+account_id,token,required=False)
        if not account:
            summary["manual_hold_items"].append("account_credit_capacity_unverified")
            summary["warnings"].append("account GET: "+str(account_error or "no account id"))
        else:
            operational=account.get("in_operational_mode")
            over=account.get("usages_exceeded")
            configurable=account.get("configurable_limits_exceeded")
            summary["account_safety"]={
                "in_operational_mode":operational,"usages_exceeded":over,
                "configurable_limits_exceeded":configurable,
                "type_name":account.get("type_name")}
            if operational is False or over is True or configurable is True:
                summary["blocking_items"].append("netlify_account_credit_or_usage_block")
            elif operational is None and over is None and configurable is None:
                summary["manual_hold_items"].append("netlify_credit_status_unverified")
            else: summary["pass_items"].append("no_reported_account_block")
            # Successful API reads do not guarantee sufficient remaining deploy credits.
            summary["manual_hold_items"].append("confirm_remaining_upload_capacity_before_1_23GB_prod")
        # Forms and notification metadata ONLY, never retrieve existing submissions or addresses.
        forms,forms_err=get_json(API+"/sites/"+site_id+"/forms",token,required=False)
        hooks,hooks_err=get_json(API+"/hooks?site_id="+urllib.parse.quote(site_id),token,required=False)
        form_rows=forms if isinstance(forms,list) else []
        hook_rows=hooks if isinstance(hooks,list) else []
        form_name="englishpt-consultation"
        live_forms=[f for f in form_rows if f.get("name")==form_name]
        active_notifications=[h for h in hook_rows if h.get("event")=="submission_created" and h.get("type")=="email"
          and (not h.get("form_id") or any(f.get("id")==h.get("form_id") for f in live_forms))]
        summary["forms_notifications_metadata"]={
            "forms_get_success":forms_err is None,
            "form_name_registered":len(live_forms)>0,
            "form_name":form_name,
            "submission_email_hook_found":len(active_notifications)>0,
            "email_hook_count":len(active_notifications),
            "no_form_submissions_fetched":True
        }
        if forms_err or not live_forms:
            summary["manual_hold_items"].append("form_registration_requires_confirmation")
        else:summary["pass_items"].append("existing_form_registration")
        if hooks_err or not active_notifications:
            summary["manual_hold_items"].append("email_notification_hook_requires_confirmation")
        else:summary["pass_items"].append("existing_email_hook_configuration")
        summary["live_get_checks"]=[
            get_public(path) for path in (
                "/","/englishpt.html","/robots.txt","/sitemap-index.xml",
                "/gyeongnam-milyang-naeidong-elem-tutor.html"
            )]
        if not all(d.get("http_status")==200 for d in summary["live_get_checks"]):
            summary["manual_hold_items"].append("current_live_baseline_http_needs_review")
        else:summary["pass_items"].append("existing_public_baseline_http")
        summary["site_meta"]={
            "site_id":site_id,"name":site.get("name"),
            "domain":site.get("custom_domain"),
            "disabled":site.get("disabled"),"state":site.get("state"),
            "published_deploy_id":current_id,
            "published_deploy_locked":pd.get("locked"),
            "deploy_preview_site_id_DO_NOT_USE":"803550a8-03af-4776-bc8a-bd0bae85f5c7"
        }
        summary["manual_hold_items"].extend([
            "confirm_netlify_restore_permission_and_deploy_retention",
            "explicit_user_authorization_for_production_deployment",
            "live_form_submission_and_email_delivery_only_after_authorized_deploy",
            "google_naver_search_registration_only_after_authorized_deploy"
        ])
        if not summary["blocking_items"] and not summary["errors"]:
            summary["status"]="PASS_TECHNICAL_PREFLIGHT_WITH_MANUAL_GO_HOLDS"
        else: summary["status"]="HOLD_PRODUCTION_PREFLIGHT"
    except Exception as exc:
        summary["errors"].append(type(exc).__name__+": "+str(exc))
        summary["status"]="HOLD_PRODUCTION_PREFLIGHT"
    finally:
        save("GO_HOLD_PREFLIGHT.json",summary)
        save("ROLLBACK_PUBLISHED_DEPLOY_POINT.json",point)
        print(summary["status"], "passed",summary["pass_items"],
              "blocking",summary["blocking_items"],
              "manual_holds",summary["manual_hold_items"],
              "errors",summary["errors"],flush=True)
        print("ROLLBACK_POINT_STATUS",point["status"],point.get("published_deploy_id"),flush=True)
    # Job success only when site snapshot recorded and no technical blocking issues.
    # Manual holds remain; operational production GO is never granted here.
    return 0 if summary["status"].startswith("PASS_") and point["status"].startswith("PASS_") else 1

if __name__=="__main__":
    sys.exit(main())
