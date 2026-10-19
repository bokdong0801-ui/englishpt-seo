#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One approved Netlify Draft: GET-only preflight. Fails closed.
No Netlify API writes, no Production publication, no Form submissions.
"""
import datetime,hashlib,json,os,pathlib,sys,urllib.request
SITE_ID="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
OLD_ID="6ac4bd517c30220008bb9661"
ALIAS="enptv23521shardonce"
MARKER="ENGLISHPT_V23521_SHARDED_DRAFT_APPROVED_ONCE_20261019"
NEW_SHA="e27ffd3e94687e0f2fc58c3951ee1262bca8fd22bd684cf7b4bdb62d014326b1"
OLD_ZIP_SHA="b490c4a19cb4deb04d3c6dd5927446cbda879991ba581e4654f2d5462686bac5"
OUT=pathlib.Path("approved-draft-evidence");OUT.mkdir(exist_ok=True)
def fetch(url,auth):
    request=urllib.request.Request(url,headers={"Authorization":"Bearer "+auth,"Accept":"application/json"},method="GET")
    with urllib.request.urlopen(request,timeout=45) as f:return json.load(f)
def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()
def main():
    r={"status":"HOLD_PREUPLOAD_GATE","checked_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "expected_Production_site_id":SITE_ID,"prior_published_deploy":OLD_ID,
       "approved_scope":"EXACTLY_ONE_DRAFT_NOT_PRODUCTION",
       "production_modified":False,"draft_uploaded":False,"forms_submitted":False,
       "pass":[],"blockers":[]}
    try:
        t=os.environ["NETLIFY_AUTH_TOKEN"]
        site=fetch("https://api.netlify.com/api/v1/sites/"+SITE_ID,t)
        if site.get("id")!=SITE_ID or site.get("custom_domain")!="englishpt.kr":
            raise ValueError("Production site/domain unexpected")
        current=(site.get("published_deploy") or {}).get("id")
        r["current_published_deploy_id"]=current
        if current!=OLD_ID:raise ValueError("Old Production changed since backup; no Draft")
        old=fetch("https://api.netlify.com/api/v1/sites/"+SITE_ID+"/deploys/"+OLD_ID,t)
        if old.get("state")!="ready" or old.get("context")!="production":
            raise ValueError("Immutable old deploy no longer ready")
        r["pass"].append("old_Production_id_state_and_site")
        ignore=(site.get("processing_settings") or {}).get("ignore_html_forms")
        r["Form_detection_enabled"]=ignore is False
        if ignore is not False:raise ValueError("Production site Netlify form detection disabled/unknown")
        r["pass"].append("form_detection_enabled")
        acc=fetch("https://api.netlify.com/api/v1/accounts/"+site["account_id"],t)
        cr=(acc.get("capabilities") or {}).get("credits") or {}
        available=(cr.get("included") or 0)-(cr.get("used") or 0)
        r["credit_included"]=cr.get("included")
        r["credit_used"]=cr.get("used")
        r["credit_calculated_remaining"]=available
        if available<=0 or acc.get("in_operational_mode") is True or acc.get("usages_exceeded") or acc.get("configurable_limits_exceeded"):
            raise ValueError("Credits/account reported unavailable")
        r["pass"].append("positive_ordinary_credits_no_exceeded_flags")
        recent=fetch("https://api.netlify.com/api/v1/sites/"+SITE_ID+"/deploys?per_page=100",t)
        if not isinstance(recent,list):raise ValueError("Deploy list not available")
        conflicts=[]
        for d in recent:
            ident=" ".join(str(d.get(k) or "") for k in ("title","name","deploy_url","deploy_ssl_url","alias"))
            if MARKER in ident or ALIAS in ident:
                conflicts.append(d.get("id"))
        r["existing_draft_conflicts"]=conflicts
        if conflicts:raise ValueError("Draft approved-once marker ALREADY EXISTS; no second attempt")
        r["pass"].append("no_preexisting_approved_once_draft_deploy")
        candidate=pathlib.Path(os.environ["CANDIDATE_ARCHIVE"])
        backup=pathlib.Path(os.environ["BACKUP_ZIP"])
        if sha256(candidate)!=NEW_SHA:raise ValueError("NEW shard archive SHA mismatch")
        if sha256(backup)!=OLD_ZIP_SHA:raise ValueError("Protected old site ZIP SHA mismatch")
        r["pass"].append("new_candidate_inner_sha256_and_old_full_zip_sha256")
        # no upload until every preflight condition is green
        r["status"]="PASS_ONE_APPROVED_DRAFT_PREUPLOAD_GATE"
    except Exception as e:
        r["blockers"].append(type(e).__name__+": "+str(e)[:300])
        r["status"]="HOLD_ONE_APPROVED_DRAFT_PREUPLOAD_GATE"
    finally:
        (OUT/"PREUPLOAD_GO_HOLD.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print("SHARDED_APPROVED_ONCE_DRAFT_PREUPLOAD_GATE",json.dumps(r,ensure_ascii=False),flush=True)
    return 0 if r["status"].startswith("PASS_") else 1
if __name__=="__main__":sys.exit(main())
