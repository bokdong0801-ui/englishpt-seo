#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exactly one real EnglishPT LIVE consultation test submission on englishpt.kr.
No retries, Netlify form + Naver email hook must pass GET-only checks before POST.
Writes an explicit POST marker BEFORE sending POST; verify Netlify submission GET only.
Never logs Netlify token, email recipient, test PII or raw submissions.
"""
import datetime as dt,hashlib,json,os,pathlib,re,sys,time,urllib.request,urllib.error,urllib.parse
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
EXPECTED_PUBLISHED="6ad5ca0f1f2051f04bdd9287"
FORM="englishpt-consultation"
TARGET_DIGEST="6d153d8d6d5380e35fa611e0bac4a2d34c56f1ff25636f392fbf7cf5e1b10998"
MARKER="ENPT-NAVER-FORM-ONE-REAL-TEST-20261019-01"
PUBLIC_URL="https://englishpt.kr/gyeongnam-milyang-naeidong-elem-tutor.html"
ROOT=pathlib.Path("single-form-test-evidence");ROOT.mkdir(exist_ok=True)
TOKEN=os.environ.get("NETLIFY_AUTH_TOKEN","")
def api(path):
    req=urllib.request.Request("https://api.netlify.com/api/v1/"+path,headers={
      "Authorization":"Bearer "+TOKEN,"Accept":"application/json"},method="GET")
    with urllib.request.urlopen(req,timeout=35) as r:return json.load(r)
def dests(h):
    d=h.get("data") or {}
    if not isinstance(d,dict):return []
    opts=[]
    for name in ("email","emails","address","addresses","to","recipient","recipients"):
        value=d.get(name)
        if isinstance(value,str):opts.append(value)
        if isinstance(value,list):opts.extend(v for v in value if isinstance(v,str))
    return [x.lower() for value in opts for x in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",value)]
def save(name,rep):
    (ROOT/name).write_text(json.dumps(rep,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def fetch_submissions():
    # Only site-level GET for confirmations; no raw returned data is printed/saved.
    x=api("sites/"+SITE+"/submissions?per_page=100")
    if not isinstance(x,list):raise ValueError("Submissions API did not return list")
    return x
def matching(x):
    hits=[]
    for v in x:
      data=v.get("data") or {}
      test_vals=[v.get("name",""),v.get("summary","")]
      if isinstance(data,dict):test_vals.extend(str(vv) for vv in data.values() if isinstance(vv,(str,int,float)))
      if any(MARKER in str(y) for y in test_vals):
        hits.append({"id":v.get("id"),"created_at":v.get("created_at"),"form_id":v.get("form_id")})
    return hits
def run():
    rep={"status":"HOLD_NOT_SENT","checked_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
      "test_marker":MARKER,"exact_authorized_attempt_count":1,"real_form_POST_count":0,
      "production_deployed":False,"settings_updated":False,"google_naver_submitted":False,
      "Naver_inbox_verified":False,"issues":[],"passed":[]}
    try:
      if os.environ.get("APPROVED_SINGLE_REAL_FORM_TEST")!="ENPT_USER_APPROVED_ONE_REAL_FORM_TEST_20261019":
        raise ValueError("Explicit user-authorized form test guard missing")
      if not TOKEN:raise ValueError("No Netlify auth for recipient/submission confirmation")
      if (ROOT/"SINGLE_REAL_POST_ATTEMPT_MARKER.json").exists():
        raise ValueError("Local test attempt marker already exists; no second POST")
      site=api("sites/"+SITE)
      if site.get("custom_domain")!="englishpt.kr" or (site.get("published_deploy") or {}).get("id")!=EXPECTED_PUBLISHED:
        raise ValueError("Production site/deploy changed")
      if (site.get("processing_settings") or {}).get("ignore_html_forms") is not False:
        raise ValueError("Form detection disabled/unknown")
      if FORM not in [f.get("name") for f in api("sites/"+SITE+"/forms")]:
        raise ValueError("Registered Netlify Form absent")
      rep["passed"].append("exact_live_site_and_registered_form")
      hooks=[h for h in api("hooks?site_id="+SITE) if h.get("event")=="submission_created" and h.get("type")=="email"]
      if len(hooks)!=1 or TARGET_DIGEST not in {
          hashlib.sha256(address.encode()).hexdigest() for h in hooks for address in dests(h)}:
        raise ValueError("Naver mail recipient not confirmed for live Form notification")
      rep["passed"].append("single_email_submission_hook_target_matches_user_naver")
      page_req=urllib.request.Request(PUBLIC_URL,method="GET",headers={"User-Agent":"ENPT-NAVER-FORM-SINGLE-TEST"})
      with urllib.request.urlopen(page_req,timeout=30) as response:
        if response.status!=200 or b'name="englishpt-consultation"' not in response.read(600000):
          raise ValueError("Original live Form page not HTTP200 or form missing")
      # Baseline is mandatory to ensure idempotence after any partial previous attempt.
      before=fetch_submissions()
      if matching(before):raise ValueError("Marker already present: NEVER duplicate user's test")
      rep["submissions_before_count_recent100"]=len(before)
      rep["passed"].append("GET_checked_no_existing_marker_in_recent100")
      fields={
        "form-name":FORM,
        "name":"[시스템테스트] ENGLISH PT 상담 이메일 확인",
        "phone":"010-0000-0000",
        "area":"테스트지역-실제상담아님",
        "message":"[TEST ONLY / 실제 상담 신청 아님] "+MARKER+
          " / Netlify Forms 접수 및 네이버 이메일 알림 점검. 회신 또는 전화 연락 불필요.",
        "wantedClass":"내이동 초등학생영어과외",
        "requestType":"영어과외 상담 신청",
        "subject":"[시스템테스트] ENGLISH PT 상담 이메일 도착 확인 "+MARKER,
        "pageTitle":"ENGLISH PT 초등학생 영어과외 상담 - 시스템 테스트",
        "pageUrl":PUBLIC_URL,
        "submittedAt":dt.datetime.now(dt.timezone.utc).isoformat(),
        "consent":"agreed",
        "bot-field":""
      }
      encoded=urllib.parse.urlencode(fields).encode("utf8")
      rep["real_form_POST_count"]=1
      rep["post_attempt_started_utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
      rep["status"]="POST_ATTEMPTED_PENDING_CONFIRMATION"
      save("SINGLE_REAL_POST_ATTEMPT_MARKER.json",rep.copy())
      # *** Exactly ONE POST; no retries even if network reports ambiguous failure ***
      try:
        req=urllib.request.Request(PUBLIC_URL,data=encoded,method="POST",
          headers={"Content-Type":"application/x-www-form-urlencoded",
                   "Accept":"text/html,application/json,*/*",
                   "User-Agent":"ENPT-20261019-Single-Authorized-Test"})
        with urllib.request.urlopen(req,timeout=40) as res:
          rep["real_form_http_status"]=res.status
          rep["real_form_redirected_url_host"]=urllib.parse.urlparse(res.geturl()).hostname
      except urllib.error.HTTPError as e:
        rep["real_form_http_status"]=e.code
        rep["issues"].append("Form POST HTTP error "+str(e.code)+"; no retry")
      except Exception as e:
        rep["issues"].append("Form POST uncertain "+type(e).__name__+"; no retry")
      # GET-only verification; do not assume HTTP 200 proves form was captured or email delivered.
      found=[]
      for i in range(8):
        try:
          found=matching(fetch_submissions())
        except Exception as exc:
          rep["issues"].append("Submission API GET unavailable "+type(exc).__name__)
          break
        if found:break
        if i<7:time.sleep(5)
      rep["Netlify_matching_submission_count"]=len(found)
      rep["Netlify_matching_submission_ids"]=[v.get("id") for v in found]
      rep["submission_observed_at_utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
      if len(found)==1:
        rep["status"]="PASS_ONE_REAL_FORM_CAPTURED_NAVER_HOOK_CONFIGURED_INBOX_UNVERIFIED"
        rep["passed"].append("exactly_one_form_submission_found_in_Netlify_records")
      elif len(found)>1:
        rep["status"]="HOLD_DUPLICATE_SUBMISSION_RECORDS"
        rep["issues"].append("Multiple submissions match single test")
      else:
        rep["status"]="HOLD_POST_NOT_CONFIRMED_IN_NETLIFY_NO_RETRY"
        rep["issues"].append("Submission not visible in Netlify GET; do not infer email delivery")
    except Exception as exc:
      rep["status"]="HOLD_REAL_FORM_TEST_NOT_COMPLETED"
      rep["issues"].append(type(exc).__name__+": "+str(exc)[:250])
    save("FINAL_SINGLE_TEST_NETLIFY_FORM_AND_NAVER_HOOK.json",rep)
    print("ENGLISHPT_ONE_REAL_NAVER_EMAIL_FORM_TEST_RESULT",json.dumps(rep,ensure_ascii=False),flush=True)
    # email inbox delivery remains user verified regardless of Netlify GET success.
    return 0 if rep["status"].startswith("PASS_") else 1
if __name__=="__main__":sys.exit(run())
