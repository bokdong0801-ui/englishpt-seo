#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch ONE shared pilot.js, preserving tutoring intent in runtime.

Before any upload: exact frozen JS fingerprint, two exact replacements,
Node syntax, and real Chromium interception across tutor & non-tutor pages.
Never deploys itself, and cannot submit forms.
"""
import argparse,hashlib,json
from pathlib import Path

KNOWN_JS_SHA256="f9e4f7e90de3924281ced3c346491661c5d047fcc34400063ac0145165d039e5"
OLD_MODE="""  const setMode=()=>{
    if(!form) return;
    if(requestType) requestType.value="체험수업 신청";
    if(subject) subject.value="ENGLISH PT 체험수업 신청";
    if(submit) submit.textContent="체험수업 신청 →";
  };"""
NEW_MODE="""  const trialMode="체험수업 신청";
  const tutorMode="영어과외 상담 신청";
  // Capture the server-rendered form intent BEFORE changing any field.
  // Keep trial behavior for every other audience/course automatically.
  const modeLabel=requestType?.value?.trim()===tutorMode ? tutorMode : trialMode;
  const setMode=()=>{
    if(!form) return;
    if(requestType) requestType.value=modeLabel;
    if(subject) subject.value="ENGLISH PT "+modeLabel;
    if(submit) submit.textContent=modeLabel+" →";
  };"""
OLD_FINALLY='          btn.textContent="체험수업 신청 →";'
NEW_FINALLY='          btn.textContent=(form===document.querySelector("#leadForm") ? modeLabel : trialMode)+" →";'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def patch(raw):
    original_sha=digest(raw)
    if original_sha!=KNOWN_JS_SHA256:
        raise ValueError("Unknown/shared runtime pilot.js SHA256; refusing unreviewed patch "+original_sha)
    old=raw.decode("utf8")
    for name,token in (("setMode",OLD_MODE),("submit finally",OLD_FINALLY)):
        if old.count(token)!=1:
            raise ValueError("Expected exactly one known "+name+" block; found "+str(old.count(token)))
    updated=old.replace(OLD_MODE,NEW_MODE,1).replace(OLD_FINALLY,NEW_FINALLY,1)
    # All other form actions, phone menu, Netlify handling and event listeners preserved.
    assert updated.count('fetch(location.pathname,{method:"POST"')==1
    assert updated.count('form.reportValidity()')==1
    assert updated.count('document.querySelectorAll("[data-trial-cta]")')==1
    assert 'modeLabel=requestType?.value?.trim()===tutorMode ? tutorMode : trialMode' in updated
    assert updated.count("체험수업 신청")>=2
    assert updated.count("영어과외 상담 신청")==1
    assert digest(updated.encode())!=original_sha
    return updated.encode(),original_sha

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--manifest",type=Path,required=True)
    args=parser.parse_args()
    raw=args.input.read_bytes()
    updated,old_sha=patch(raw)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(updated)
    doc={"status":"PASS_EXACT_SHARED_PILOT_JS_RUNTIME_MODE_PATCH",
         "previous_sha256":old_sha,"patched_sha256":digest(updated),
         "changed_files":["pilot.js"],"other_files_modified":False,
         "script_syntax_check_required":True,"runtime_check_required":True,
         "server_html_remains_unchanged":True,
         "production_deployed":False,"netlify_deployed":False,"form_submitted":False}
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    args.manifest.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(doc["status"],doc["patched_sha256"],flush=True)

if __name__=="__main__":
    main()
