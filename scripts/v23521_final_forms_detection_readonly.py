#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Netlify Forms detection read-only API/site HTML verification for ENGLISH PT.
Allowed: GET only. NO production deploy, form POST, settings writes, or email content.
"""
import datetime as dt
import json, os, sys, urllib.request, urllib.error
from html.parser import HTMLParser
from pathlib import Path

API="https://api.netlify.com/api/v1"
PROD_ID="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
REVIEW_ID="803550a8-03af-4776-bc8a-bd0bae85f5c7"
BASES={
 "production":"https://englishpt.kr",
 "review":"https://6ad2561619f2bc1574990fc9--englishpt-final-ia-review-bokdong.netlify.app"
}
IDS={"production":PROD_ID,"review":REVIEW_ID}
PAGES={
 "production":"/englishpt.html",
 "review":"/gyeongnam-milyang-naeidong-elem-tutor.html"
}
OUT=Path("forms-detection-readonly")
OUT.mkdir(exist_ok=True)

class Parser(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True)
  self.forms=[]
  self.active=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag.lower()=="form":
   self.active={"name":a.get("name"),"method":a.get("method"),
      "data_netlify_attr":a.get("data-netlify"),
      "netlify_attr_present":"netlify" in a,
      "form_name_inputs":[],"context_field_names":[]}
   self.forms.append(self.active)
  elif self.active and tag.lower() in ("input","textarea","select"):
   if a.get("name")=="form-name":
    self.active["form_name_inputs"].append(a.get("value"))
   elif a.get("name") in ("requestType","subject","pageUrl","grade","name"):
    self.active["context_field_names"].append(a.get("name"))
 def handle_endtag(self,tag):
  if tag.lower()=="form":self.active=None

def fetch(url,token=None,limit=450000):
 headers={"Accept":"application/json" if token else "text/html",
          "User-Agent":"englishpt-v23521-forms-detection-GET-only"}
 if token:headers["Authorization"]="Bearer "+token
 request=urllib.request.Request(url,headers=headers,method="GET")
 with urllib.request.urlopen(request,timeout=45) as r:
  return r.status,dict(r.headers),r.read(limit)

def main():
 token=os.environ.get("NETLIFY_AUTH_TOKEN","")
 result={"status":"RUNNING","checked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
    "netlify_write_requests":0,"actual_form_submissions":0,"production_deployed":False,
    "site_results":{},"errors":[]}
 try:
  if not token:raise ValueError("Missing Netlify token")
  for label,site_id in IDS.items():
   site_summary={"site_id":site_id,"error":None}
   try:
    _,_,raw=fetch(API+"/sites/"+site_id,token)
    site=json.loads(raw)
    assert site.get("id")==site_id,"Site id mismatch"
    process=site.get("processing_settings") or {}
    if not isinstance(process,dict):process={}
    # Netlify has an undocumented ignore_html_forms flag; lack of field is unknown,
    # never interpret missing as true or false.
    flag=process.get("ignore_html_forms","MISSING")
    site_summary["processing_settings_ignore_html_forms"]=flag
    site_summary["processing_settings_keys"]=sorted(process)
    site_summary["site_form_keys"]={k:v for k,v in site.items()
       if "form" in k.lower() and isinstance(v,(bool,int,float,str,type(None)))}
    site_summary["published_deploy_id"]=(site.get("published_deploy") or {}).get("id")
    site_summary["custom_domain"]=site.get("custom_domain")
    _,_,raw=fetch(API+"/sites/"+site_id+"/forms",token)
    forms=json.loads(raw)
    assert isinstance(forms,list),"Not a form array"
    site_summary["registered_form_names"]=sorted(set(f.get("name") for f in forms if f.get("name")))
    site_summary["registered_form_count"]=len(forms)
    _,_,raw=fetch(BASES[label]+PAGES[label],None)
    text=raw.decode("utf8",errors="replace")
    p=Parser()
    p.feed(text)
    site_summary["sample_http_200"]=True
    site_summary["sample_page"]=PAGES[label]
    site_summary["sample_page_form_count"]=len(p.forms)
    site_summary["sample_form_contracts"]=p.forms
    site_summary["expected_form_in_html"]=any(x.get("name")=="englishpt-consultation" for x in p.forms)
    site_summary["expected_form_registered_in_Netlify"]="englishpt-consultation" in site_summary["registered_form_names"]
    if flag is True:verdict="DETECTION_DISABLED_IN_API"
    elif flag is False:verdict="DETECTION_ENABLED_IN_API"
    elif "englishpt-consultation" in site_summary["registered_form_names"]:
      verdict="FORM_REGISTERED_BUT_DETECTION_TOGGLE_UNKNOWN"
    else:verdict="DETECTION_SETTING_UNKNOWN_UNTIL_UI_CONFIRMS"
    site_summary["detection_verdict"]=verdict
    print("SITE_FORMS_READONLY",label,json.dumps(site_summary,ensure_ascii=False),flush=True)
   except Exception as exc:
    site_summary["error"]=type(exc).__name__+" "+str(getattr(exc,"code",""))[:30]
    result["errors"].append({"site":label,"error":site_summary["error"]})
    print("SITE_FORMS_DIAGNOSTIC_FAILED",label,site_summary["error"],flush=True)
   result["site_results"][label]=site_summary
  result["status"]="PASS_AUTHENTICATED_FORMS_DIAGNOSTIC_WITH_NO_MUTATIONS" if not result["errors"] else "HOLD_FORMS_DIAGNOSTIC_INCOMPLETE"
 except Exception as e:
  result["errors"].append({"fatal":type(e).__name__+":"+str(e)[:180]})
  result["status"]="HOLD_FORMS_DIAGNOSTIC_INCOMPLETE"
 finally:
  (OUT/"FINAL_NETLIFY_FORMS_DETECTION_TWO_SITES.json").write_text(
    json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
  print("FINAL_NETLIFY_FORMS_DETECTION_VERDICT",json.dumps(result,ensure_ascii=False),flush=True)
 return 0 if result["status"].startswith("PASS_") else 1

if __name__=="__main__":sys.exit(main())
