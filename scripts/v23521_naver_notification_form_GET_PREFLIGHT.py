#!/usr/bin/env python3
"""READ-ONLY: live Netlify production Form+notification recipient and fields discovery.
Never submit form, send email, or update any Netlify setting. Private recipient is compared
as a SHA256 digest and never written into repo, artifact or action logs.
"""
import datetime,hashlib,json,os,pathlib,re,sys,urllib.request,urllib.error
from html.parser import HTMLParser
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
EXPECTED_LIVE="6ad5ca0f1f2051f04bdd9287"
EXPECTED_RECIPIENT_SHA="6d153d8d6d5380e35fa611e0bac4a2d34c56f1ff25636f392fbf7cf5e1b10998"
OUT=pathlib.Path("single-form-test-evidence");OUT.mkdir(exist_ok=True)
URL="https://englishpt.kr/gyeongnam-milyang-naeidong-elem-tutor.html"
def api(path):
    req=urllib.request.Request("https://api.netlify.com/api/v1/"+path,
       headers={"Authorization":"Bearer "+os.environ["NETLIFY_AUTH_TOKEN"],"Accept":"application/json"},method="GET")
    with urllib.request.urlopen(req,timeout=40) as r:return json.load(r)
def page():
    req=urllib.request.Request(URL,headers={"User-Agent":"ENPT-live-Forms-QA-GET-only"},method="GET")
    with urllib.request.urlopen(req,timeout=40) as r:
      if r.status!=200:raise ValueError("Live form sample not HTTP 200")
      return r.read(650000).decode("utf8",errors="replace")
class Forms(HTMLParser):
    def __init__(self):super().__init__();self.forms=[];self.now=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="form":
            self.now={"name":a.get("name"),"method":a.get("method"),"action":a.get("action"),
                      "netlify":a.get("data-netlify"),"inputs":[]}
            self.forms.append(self.now)
        elif self.now and tag in ("input","select","textarea"):
            self.now["inputs"].append({"tag":tag,"name":a.get("name"),
              "type":a.get("type"),"required":"required" in a,
              "hidden_default":a.get("value") if a.get("type")=="hidden" else None})
    def handle_endtag(self,tag):
        if tag=="form":self.now=None
def recipients(hook):
    """Find address-like strings only in hook settings, no secrets or full hook JSON emitted."""
    fields=hook.get("data") or {}
    if not isinstance(fields,dict):fields={}
    candidates=[]
    for k in ("email","emails","address","addresses","to","recipient","recipients"):
        v=fields.get(k)
        if isinstance(v,str):candidates.append(v)
        elif isinstance(v,list):candidates.extend(x for x in v if isinstance(x,str))
    for value in candidates:
        for address in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",value):
            yield address.strip().lower()
def main():
    r={"status":"HOLD","checked_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "production_expected_deploy_id":EXPECTED_LIVE,"Netlify_writes":0,"real_form_POSTs":0,
       "Naver_inbox_access":False,"checks":[],"issues":[]}
    try:
        site=api("sites/"+SITE)
        live=(site.get("published_deploy") or {}).get("id")
        r["published_deploy_id"]=live
        if site.get("custom_domain")!="englishpt.kr" or live!=EXPECTED_LIVE:
            raise ValueError("Production deploy/domain drift")
        if (site.get("processing_settings") or {}).get("ignore_html_forms") is not False:
            raise ValueError("Form detection not enabled")
        r["checks"].append("exact_published_site_and_Forms_detection")
        registered=api("sites/"+SITE+"/forms")
        r["registered_form_names"]=sorted(set(f.get("name") for f in registered if f.get("name")))
        if "englishpt-consultation" not in r["registered_form_names"]:
            raise ValueError("Expected Form not registered")
        r["checks"].append("englishpt_consultation_registered")
        hooks=api("hooks?site_id="+SITE)
        emailhooks=[h for h in hooks if h.get("event")=="submission_created" and h.get("type")=="email"]
        r["submission_created_email_hook_count"]=len(emailhooks)
        r["email_recipient_matches_naver"]=sum(1 for h in emailhooks
             if EXPECTED_RECIPIENT_SHA in {hashlib.sha256(e.encode("utf8")).hexdigest() for e in recipients(h)})
        r["configured_recipient_address_inspection"]="digest_match_only_email_not_disclosed"
        r["email_hook_configs_with_recipient_candidates"]=sum(bool(list(recipients(h))) for h in emailhooks)
        r["email_hook_event_types"]=[h.get("event") for h in emailhooks]
        p=Forms();p.feed(page())
        contracts=[f for f in p.forms if f["name"]=="englishpt-consultation"]
        r["page_url_path"]="/gyeongnam-milyang-naeidong-elem-tutor.html"
        r["expected_page_form_count"]=len(contracts)
        if len(contracts)!=1:raise ValueError("Expected exactly one consultation form")
        r["form_contract"]=contracts[0]
        if (contracts[0]["method"] or "").lower()!="post":raise ValueError("Form method mismatch")
        names={v["name"] for v in contracts[0]["inputs"] if v["name"]}
        if not {"form-name","name","grade","requestType","subject"}.issubset(names):
            raise ValueError("Key Netlify Form names not found")
        r["checks"].append("live_actual_form_POST_contract_and_fields")
        if r["email_recipient_matches_naver"]==0:
            r["status"]="HOLD_RECIPIENT_NOT_VERIFIED_DO_NOT_SUBMIT"
        elif len(emailhooks)!=1:
            r["status"]="HOLD_MULTIPLE_EMAIL_HOOKS_CHECK_MANUALLY"
        else:
            r["status"]="PASS_NAVER_RECIPIENT_MATCH_FORM_READY_FOR_SINGLE_TEST"
    except Exception as e:
        r["issues"].append(type(e).__name__+": "+str(e)[:260])
        r["status"]="HOLD_FORM_PREFLIGHT"
    (OUT/"LIVE_NAVER_FORM_NOTIFICATION_GET_ONLY.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("LIVE_NAVER_NOTIFICATION_PREFLIGHT",json.dumps(r,ensure_ascii=False),flush=True)
    return 0 if r["status"].startswith("PASS_") else 1
if __name__=="__main__":sys.exit(main())
