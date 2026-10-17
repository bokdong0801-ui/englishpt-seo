#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Preapproval audit, read-only. No Netlify/Production changes and no form POST."""
import argparse, datetime, hashlib, json, re, sys, urllib.request
from html.parser import HTMLParser
from pathlib import Path

SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
PUBLISHED_PREVIOUS="6ac4bd517c30220008bb9661"
SOURCE_SHA="e06c6a7b33a3042c9c52e73e95f1ed8a25819dde8584873f939fa14cff9c4bba"
PILOT_JS_SHA="d604994a74352a81978002fd6f6286c7d0f4f4c99278745bbf6dad1abce29ede"
SLUGS=("gyeongnam-milyang-naeidong","seoul-jongno-sajikdong")
GRADES=("elem-tutor","mid-tutor","high-tutor")

class HTMLForms(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.forms=[]
        self.active=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="form":
            self.active={"name":a.get("name"),"method":(a.get("method") or "").upper(),
                "data_netlify":a.get("data-netlify"),
                "netlify_attribute":"netlify" in a,"input_names":[],"hidden_form_name":[]}
            self.forms.append(self.active)
        elif self.active is not None and tag in ("input","textarea","select"):
            n=a.get("name")
            if n:
                self.active["input_names"].append(n)
                if n=="form-name":self.active["hidden_form_name"].append(a.get("value"))
    def handle_endtag(self,tag):
        if tag=="form":self.active=None

def get_json(path,token):
    req=urllib.request.Request("https://api.netlify.com/api/v1/"+path,method="GET",
        headers={"Authorization":"Bearer "+token,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=35) as resp:return json.load(resp)

def form_settings(site):
    # Site representation varies by Netlify API version; report unknown rather than guess.
    out={}
    for key,v in site.items():
        if "form" in key.lower() and isinstance(v,(str,bool,int,float,type(None))):
            out[key]=v
    processing=site.get("processing_settings")
    if isinstance(processing,dict):
        for section,vals in processing.items():
            if isinstance(vals,dict):
                out["processing_settings."+section+".keys"]=list(sorted(vals))
                for k,v in vals.items():
                    if "form" in k.lower() and isinstance(v,(str,bool,int,float,type(None))):
                        out["processing_settings."+section+"."+k]=v
    return out

def main():
    import os
    p=argparse.ArgumentParser()
    p.add_argument("--candidate",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    root=args.candidate
    result={"status":"HOLD_PREAPPROVAL", "checked_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "candidate_archive_sha256":SOURCE_SHA,"production_site_id":SITE,
        "production_deployed":False,"netlify_requests_all_get":True,"form_submitted":False,
        "failures":[],"manual_holds":[],"passes":[],"form_samples":[]}
    try:
        tok=os.environ.get("NETLIFY_AUTH_TOKEN","")
        if not tok:raise RuntimeError("Missing Netlify GET-only auth token")
        site=get_json("sites/"+SITE,tok)
        if site.get("id")!=SITE or site.get("custom_domain") not in ("englishpt.kr","www.englishpt.kr"):
            raise ValueError("Production site/domain mismatch")
        current=(site.get("published_deploy") or {}).get("id")
        result["current_published_deploy_id"]=current
        old=get_json("sites/"+SITE+"/deploys/"+PUBLISHED_PREVIOUS,tok)
        if old.get("state")!="ready" or old.get("context")!="production":
            raise ValueError("Old immutable rollback deploy does not exist in ready Production state")
        result["previous_production_deploy_state"]=old["state"]
        if current!=PUBLISHED_PREVIOUS:
            result["manual_holds"].append("published_deploy_changed_since_initial_backup: recapture new baseline before release")
        else:
            result["passes"].append("live_published_deploy_matches_protected_rollback_point")
        account=get_json("accounts/"+site["account_id"],tok)
        credit=((account.get("capabilities") or {}).get("credits") or {})
        included=credit.get("included");used=credit.get("used")
        remaining=included-used if isinstance(included,(int,float)) and isinstance(used,(int,float)) else None
        result["billing"]={"plan":account.get("type_name"),"credits_included":included,"credits_used":used,
            "remaining_calculated":remaining,"in_operational_mode":account.get("in_operational_mode"),
            "usage_exceeded":bool(account.get("usages_exceeded")),
            "configured_limits_exceeded":bool(account.get("configurable_limits_exceeded"))}
        if remaining is not None and remaining>0 and account.get("in_operational_mode") is False and not account.get("usages_exceeded") and not account.get("configurable_limits_exceeded"):
            result["passes"].append("netlify_billing_readonly_no_current_overage")
        else:result["failures"].append("netlify_credit_or_account_state_requires_review")
        result["netlify_form_detection_metadata"]=form_settings(site)
        if not result["netlify_form_detection_metadata"]:
            result["manual_holds"].append("confirm_form_detection_enabled_in_Netlify_UI_before_deployment")
        forms=get_json("sites/"+SITE+"/forms",tok)
        names=sorted(set(x.get("name","") for x in forms if x.get("name")))
        result["current_registered_forms_count"]=len(forms)
        result["current_registered_forms_names"]=names
        if "englishpt-consultation" not in names:
            result["manual_holds"].append("form_not_registered_on_current_old_Production: must verify new form after_deploy")
        js=(root/"pilot.js").read_bytes()
        if hashlib.sha256(js).hexdigest()!=PILOT_JS_SHA:
            raise ValueError("Incorrect new Production pilot.js SHA")
        result["passes"].append("pilot_js_patched_sha256")
        headers=(root/"_headers").read_text("utf8")
        if re.search(r"(?im)^\s*X-Robots-Tag:\s*noindex",headers):
            raise ValueError("Global Draft noindex header leaked into production candidate")
        result["passes"].append("no_global_draft_noindex")
        for area in SLUGS:
            for grade in GRADES:
                fn=area+"-"+grade+".html"
                html=(root/fn).read_text("utf8")
                h=HTMLForms();h.feed(html)
                matches=[a for a in h.forms if a["name"]=="englishpt-consultation"]
                if len(matches)!=1:raise ValueError("Expected exactly one real Netlify consultation form: "+fn+" "+str(len(matches)))
                form=matches[0]
                valid=form["method"]=="POST" and (str(form["data_netlify"]).lower()=="true" or form["netlify_attribute"])
                if not valid:raise ValueError("Missing static Netlify form detection markup: "+fn)
                expected={"requestType","subject"}
                if not expected.issubset(set(form["input_names"])):
                    raise ValueError("Missing context field(s) in form: "+fn)
                if "영어과외 상담 신청" not in html:
                    raise ValueError("Tutoring consultation copy missing: "+fn)
                result["form_samples"].append({"file":fn,"form_name":form["name"],"method":form["method"],
                    "netlify_static_detection_markup":True,"input_count":len(set(form["input_names"])),
                    "hidden_form_name_values":form["hidden_form_name"],"has_requestType":True,"has_subject":True})
        result["passes"].append("six_static_tutoring_netlify_form_definitions")
        result["manual_holds"].extend([
          "obtain_portable_old_Production_deploy_ZIP_and_verify_SHA256",
          "confirm_Netlify_UI_form_detection_before_deploy",
          "ensure_one_new_Production_deployment_only_and_postdeploy_form_registration",
          "explicit_separate_user_authorization_for_Production_release"])
        result["status"]="PASS_TECHNICAL_PREAPPROVAL_WITH_EXPLICIT_HOLDS" if not result["failures"] else "HOLD_TECHNICAL_PREAPPROVAL"
    except Exception as e:
        result["failures"].append(type(e).__name__+": "+str(e)[:250])
        result["status"]="HOLD_TECHNICAL_PREAPPROVAL"
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("PRODUCTION_PREAPPROVAL_GATE",json.dumps(result,ensure_ascii=False),flush=True)
    return 0 if not result["failures"] and result["status"].startswith("PASS_") else 1

if __name__=="__main__":sys.exit(main())
