#!/usr/bin/env python3
"""Exactly ONE labeled synthetic consultation through LIVE unpublished ENPT V3.1;
Netlify Forms submission GET and email hook GET verified, no Production writes.
Never claim Naver inbox delivery without access. Never retry the POST.
"""
from __future__ import annotations
import datetime,json,os,pathlib,time,urllib.request,urllib.error
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
OUT=pathlib.Path("v31-consultation-real-test");OUT.mkdir(exist_ok=True)
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
PROD="6adafef5f2c6d196833683db"
DRAFT="6ae06963f085b33a5ee903eb"
BASE="https://review-enpt-v3-1-20261027--englishpt-seo.netlify.app"
ROUTE="/gyeonggi-anyang-manan-byeongmokandong-elem-tutor.html"
MARKER="ENPT_V31_ONE_QA_NO_CONTACT_20261027_V1"
NETLIFY_FORM="englishpt-consultation"
INBOX_ADDRESS="cicada3865@naver.com"
TOKEN=os.environ["NETLIFY_AUTH_TOKEN"]
report={"status":"HOLD","timestamp_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "draft_id":DRAFT,"published_expected":PROD,"synthetic_qa_only":True,"test_marker":MARKER,
        "POST_attempts":0,"production_posts":0,"sms_attempts":0,"inbox_receipt":"UNVERIFIED_NO_NAVER_MAIL_ACCESS",
        "netlify_submission_recorded":False,"email_notification_hook":False,"failures":[]}
API="https://api.netlify.com/api/v1/"
def api(path):
 r=urllib.request.Request(API+path,method="GET",headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"})
 with urllib.request.urlopen(r,timeout=38) as x:return json.load(x)
def require(cond,reason):
 if not cond:raise RuntimeError(reason)
def records():
 ver=api("sites/"+SITE+"/submissions?per_page=100")
 spam=api("sites/"+SITE+"/submissions?state=spam&per_page=100")
 return ver,spam
def hits(xs):
 return [x for x in xs if MARKER in json.dumps(x.get("data") or {},ensure_ascii=False)]
try:
 site=api("sites/"+SITE)
 draft=api("sites/"+SITE+"/deploys/"+DRAFT)
 require(site.get("custom_domain")=="englishpt.kr" and (site.get("published_deploy") or {}).get("id")==PROD,"HOLD_PRODUCTION_ID_DRIFT")
 require(draft.get("state")=="ready" and draft.get("published_at") is None and draft.get("draft") is not False,"HOLD_NONPUBLISHED_DRAFT_INVALID")
 require(draft.get("deploy_ssl_url")==BASE and draft.get("id")==DRAFT,"HOLD_WRONG_V31_ALIAS")
 forms=api("sites/"+SITE+"/forms")
 matching=[f for f in forms if f.get("name")==NETLIFY_FORM]
 require(len(matching)==1,"HOLD_NETLIFY_FORM_NOT_REGISTERED_ONCE")
 report["form_backend_registered"]=True
 report["form_id"]=matching[0]["id"]
 hooks=api("hooks?site_id="+SITE)
 hook_found=any(h.get("type")=="email" and h.get("event")=="submission_created" and
   INBOX_ADDRESS in json.dumps(h.get("data") or {},ensure_ascii=False) for h in hooks)
 report["email_notification_hook"]=hook_found
 require(hook_found,"HOLD_EXPECTED_EMAIL_NOTIFICATION_HOOK_NOT_CONFIGURED")
 req=urllib.request.Request(BASE+ROUTE,method="GET")
 with urllib.request.urlopen(req,timeout=40) as r:
  raw=r.read(500000);response=r.status
 require(response==200 and b"englishpt-consultation" in raw and b'leadForm' in raw,"HOLD_FORM_MISSING_LIVE_V31")
 before,spam=records()
 require(not hits(before+spam),"HOLD_ALREADY_SUBMITTED_THIS_MARKER_NO_REPEAT")
 with sync_playwright() as play:
  browser=play.chromium.launch(headless=True,args=["--no-sandbox"])
  context=browser.new_context(viewport={"width":390,"height":850})
  events=[]
  def guard(route):
   request=route.request
   method=request.method
   u=request.url
   if method in ("GET","HEAD"):return route.continue_()
   if method=="POST" and u.startswith(BASE) and urlparse(u).path==ROUTE and report["POST_attempts"]==0:
    report["POST_attempts"]=1
    events.append({"method":method,"path":urlparse(u).path,"status":None})
    return route.continue_()
   report["failures"].append("BLOCKED_UNEXPECTED_NON_GET:"+method+":"+urlparse(u).path)
   return route.abort()
  context.route("**/*",guard)
  page=context.new_page()
  def capture(response):
   if events and response.request.method=="POST" and response.request.url.startswith(BASE):
    events[0]["status"]=response.status
  page.on("response",capture)
  try:
   nav=page.goto(BASE+ROUTE,wait_until="domcontentloaded",timeout=50000)
   require(nav is not None and nav.status==200,"HOLD_BROWSER_V31_FORM_PAGE_NOT_200")
   form=page.locator("form#leadForm")
   # Popup on the existing page. Use validated opener - no external navigation.
   # Actual legacy course pages open the form via the #consultation-preview anchor.
   # Do not click a hidden mobile menu's data-open-form element.
   if not form.is_visible():
    candidates=[
      page.locator('a[href="#consultation-preview"]:visible'),
      page.locator('button[data-open-form]:visible'),
      page.locator('a[data-open-form]:visible'),
      page.locator('[data-open-form]:visible')
    ]
    visible=None
    for candidate in candidates:
     if candidate.count()>0:
      visible=candidate.first
      break
    require(visible is not None,"HOLD_NO_VISIBLE_CONSULTATION_OPEN_TRIGGER")
    visible.click(timeout=12000)
   form.wait_for(state="visible",timeout=15000)
   require(form.get_attribute("name")==NETLIFY_FORM,"HOLD_FORM_NAME_WRONG")
   require(form.locator('input[name="form-name"]').get_attribute("value")==NETLIFY_FORM,"HOLD_FORM_HIDDEN_NAME")
   require(form.locator('input[name="bot-field"]').count()==1,"HOLD_HONEYPOT_MISSING")
   form.locator('input[name="name"]').fill("ENPT V3.1 QA TEST - 연락금지")
   form.locator('input[name="phone"]').fill("010-0000-0000")
   form.locator('input[name="area"]').fill("QA 테스트(실제 상담 아님)")
   message=form.locator('textarea[name="message"]')
   if message.count():message.fill(MARKER+" / 자동 점검용 1회 제출입니다. 실제 고객 문의 아님. 답신 또는 전화 금지.")
   subj=form.locator('input[name="subject"]')
   if subj.count():subj.evaluate("(el,v)=>el.value=v",MARKER+" / QA TEST - DO NOT CONTACT")
   consent=form.locator('input[name="consent"]')
   require(consent.count()==1,"HOLD_CONSENT_MISSING")
   consent.check()
   require(form.evaluate("(f)=>f.checkValidity()"),"HOLD_BROWSER_FORM_VALIDATION_FAILED")
   report["browser_form_valid"]=True
   page.screenshot(path=str(OUT/"V31_QA_SYNTHETIC_FORM_READY_390.png"),full_page=False)
   # Do NOT retry on failure; browser should make exactly ONE form POST.
   form.locator('button[type="submit"]').click(timeout=16000)
   page.wait_for_timeout(5000)
   report["browser_status_message"]=page.locator("#leadStatus").inner_text(timeout=10000)[:220]
   report["response_events"]=events
   report["post_http_success"]=len(events)==1 and events[0].get("status") in (200,201,202,204)
   report["browser_success_message"]="신청이 접수됐습니다" in report["browser_status_message"]
   page.screenshot(path=str(OUT/"V31_QA_AFTER_SUBMISSION_390.png"),full_page=False)
  finally:
   context.close();browser.close()
 require(report["POST_attempts"]==1,"HOLD_ONE_SUBMISSION_NOT_SENT_OR_MULTIPLE")
 require(report["post_http_success"] and report["browser_success_message"],"HOLD_POST_RESPONSE_OR_CONFIRMATION")
 for trial in range(10):
  normal,spam=records()
  a=hits(normal);b=hits(spam)
  if a or b:
   submission=(a or b)[0]
   report.update(netlify_submission_recorded=True,submission_state="verified" if a else "spam",
    submission_record_id=submission.get("id"),submission_time=submission.get("created_at"))
   break
  if trial<9:time.sleep(3)
 require(report["netlify_submission_recorded"],"HOLD_NETLIFY_SUBMISSION_NOT_FOUND")
 after=api("sites/"+SITE)
 require((after.get("published_deploy") or {}).get("id")==PROD,"HOLD_PRODUCTION_CHANGED_POST_SUBMISSION")
 report["status"]="PASS_ONE_REAL_BROWSER_FORM_POST_NETLIFY_RECORDED_EMAIL_HOOK_READY_INBOX_UNVERIFIED" if report["submission_state"]=="verified" else "HOLD_TEST_MARKED_SPAM"
except Exception as exc:
 report["failures"].append(type(exc).__name__+": "+str(exc)[:300])
 report["status"]="HOLD_NO_UNCONDITIONAL_RETRY"
finally:
 (OUT/"V31_ONE_REAL_FORM_POST_RECEIPT_AND_NAVER_HOOK_QA.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),"utf8")
 print("ENPT_V31_REAL_ONCE_FORM_QA",json.dumps(report,ensure_ascii=False),flush=True)
 if report["status"].startswith("HOLD"):raise SystemExit(1)
