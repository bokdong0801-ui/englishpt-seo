#!/usr/bin/env python3
# coding: utf-8
"""Submit exactly ONE clearly labeled synthetic EnglishPT consultation through real
nonpublished production-safe Netlify Preview, verify backend submissions via GET.
NEVER claim Naver mailbox received without mailbox read access. Never publish.
"""
import datetime,json,os,pathlib,time,urllib.parse,urllib.request,urllib.error
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from shutil import which

SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
PROD="6ad5eb4918f9411c4d5e1ba4"
MARKER_DEPLOY="ENPT-21964-PRODSAFE-ORIGINAL-ROBOTS-CLI-FULL-NONPUBLISHED-ONCE-20261020"
BASE="https://enptog21964prodsafereview20--englishpt-seo.netlify.app"
ROUTE="/gyeongnam-milyang-naeidong-elem-tutor.html"
FORM="englishpt-consultation"
EXPECTED_EMAIL="cicada3865@naver.com"
ID="ENPT_OG21964_FINAL_QA_SINGLE_20261020"
OUT=pathlib.Path("candidate-real-form-evidence")
OUT.mkdir(exist_ok=True)
r={"status":"HOLD","checked_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
   "target_preview":BASE,"test_id":ID,"synthetic_test_only":True,
   "actual_submissions_sent":0,"Netlify_production_publishes":0,
   "errors":[],"backend_recorded":False,"naver_notification_hook_configured":False,
   "naver_mailbox_received":None,"naver_mailbox_received_verification":"NOT_CONNECTED",
   "test_sms_sent":False}
def ensure(x,msg):
    if not x:raise ValueError(msg)
def api(path):
    req=urllib.request.Request("https://api.netlify.com/api/v1/"+path,
      method="GET",headers={"Authorization":"Bearer "+os.environ["NETLIFY_AUTH_TOKEN"],
      "Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=35) as f:return json.load(f)
def list_submissions():
    # Netlify API documents per_page 100; include spam to prevent accidental repeats.
    verified=api("sites/"+SITE+"/submissions?per_page=100")
    spam=api("sites/"+SITE+"/submissions?state=spam&per_page=100")
    return verified,spam
try:
    site=api("sites/"+SITE)
    ensure(site.get("id")==SITE and site.get("custom_domain")=="englishpt.kr","Wrong site")
    ensure((site.get("published_deploy") or {}).get("id")==PROD,"Published site drift, stop")
    forms=api("sites/"+SITE+"/forms")
    matching=[f for f in forms if f.get("name")==FORM]
    ensure(len(matching)==1,"Netlify form registered ID count not exactly one")
    f=matching[0]
    r["form_id"]=f["id"]
    hooks=api("hooks?site_id="+SITE)
    r["naver_notification_hook_configured"]=any(
      h.get("type")=="email" and h.get("event")=="submission_created"
      and EXPECTED_EMAIL in json.dumps(h.get("data") or {},ensure_ascii=False)
      for h in hooks)
    ensure(r["naver_notification_hook_configured"],"Naver submission email notification hook not configured")
    matches=api("sites/"+SITE+"/deploys?per_page=100")
    own=[x for x in matches if x.get("title")==MARKER_DEPLOY]
    ensure(len(own)==1 and own[0].get("state")=="ready" and
           own[0].get("published_at") is None,"No unique READY nonpublished production-safe Draft")
    r["draft_id"]=own[0]["id"]
    def getpage(path):
      req=urllib.request.Request(BASE+path,method="GET",
        headers={"User-Agent":"ENPT-production-safe-exact-one-form-test"})
      with urllib.request.urlopen(req,timeout=30) as resp:
        return resp.status,dict(resp.headers),resp.read(1400000)
    status,headers,data=getpage(ROUTE)
    ensure(status==200 and b'<form' in data,"Form page not HTTP200")
    ensure("noindex" not in (headers.get("X-Robots-Tag") or "").lower(),
           "Unexpected review noindex leaked into production-safe draft")
    ensure(b'name="englishpt-consultation"' in data and b'data-netlify="true"' in data,
           "Live Netlify form not present")
    before_verified,before_spam=list_submissions()
    def existing(records):
        return [x for x in records if ID in json.dumps(x.get("data") or {},ensure_ascii=False)]
    ensure(not existing(before_verified+before_spam),
           "Identical test marker has already been submitted; no second submit")
    r["before_form_submission_count"]=f.get("submission_count")
    # One real browser submission, never with personal customer details.
    chrome=which("google-chrome") or which("chromium") or which("chromium-browser")
    ensure(chrome,"Chrome unavailable")
    request_events=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=chrome,
           args=["--no-sandbox","--disable-dev-shm-usage"])
        try:
            ctx=browser.new_context(viewport={"width":390,"height":850})
            def guard(route):
                method=route.request.method
                path=urlparse(route.request.url).path
                same=(route.request.url.startswith(BASE) and path==ROUTE)
                if method in ("GET","HEAD"):
                    route.continue_()
                elif method=="POST" and same and r["actual_submissions_sent"]==0:
                    r["actual_submissions_sent"]=1
                    request_events.append({"url_path":path,"method":"POST"})
                    route.continue_()
                else:
                    route.abort()
            ctx.route("**/*",guard)
            page=ctx.new_page()
            page.on("response",lambda response:request_events[-1].update({"response_status":response.status})
                    if request_events and response.request.method=="POST" else None)
            answer=page.goto(BASE+ROUTE,wait_until="domcontentloaded",timeout=60000)
            ensure(answer and answer.status==200,"Chrome form page not HTTP200")
            page.locator('a[href="#consultation-preview"]').first.click(timeout=18000)
            form=page.locator("#consultation-preview form#leadForm")
            form.wait_for(state="visible",timeout=16000)
            form.locator('input[name="name"]').fill("ENPT QA TEST - DO NOT CONTACT")
            form.locator('input[name="phone"]').fill("010-0000-0000")
            form.locator('input[name="area"]').fill("테스트(실제 상담 아님)")
            area=form.locator('textarea[name="message"]')
            if area.count():area.fill(ID+" / 자동 QA 시험 제출입니다. 실제 상담 신청이 아닙니다. 답장/연락 금지.")
            topic=form.locator('input[name="subject"]')
            if topic.count():topic.evaluate("(el, v) => {el.value=v}", ID+" - QA 시험 (고객 아님)")
            agree=form.locator('input[name="consent"]')
            ensure(agree.count()==1,"Consent form field absent")
            agree.check()
            ensure(form.evaluate("(f)=>f.reportValidity()"),"Form failed browser required validation")
            r["form_target"]=ROUTE
            r["browser_validation"]=True
            page.screenshot(path=str(OUT/"SYNTHETIC_TEST_FORM_FILLED_390.png"),full_page=False)
            form.locator('button[type="submit"]').click(timeout=15000)
            page.wait_for_timeout(4500)
            msg=page.locator("#leadStatus").inner_text(timeout=10000)
            r["browser_status_text"]=msg[:250]
            r["post_http_events"]=request_events
            r["post_http_success"]=bool(request_events and request_events[0].get("response_status") in (200,201,202,204))
            r["browser_success_message"]="신청이 접수됐습니다" in msg
            ctx.close()
        finally:
            browser.close()
    ensure(r["actual_submissions_sent"]==1,"Expected precisely one browser POST")
    ensure(r["post_http_success"] and r["browser_success_message"],
           "Browser POST did not return success; never auto retry")
    # Do not issue another POST: only read Netlify verified/spam submissions.
    for i in range(10):
        verified,spam=list_submissions()
        good=existing(verified);flagged=existing(spam)
        if good:
            r["backend_recorded"]=True
            r["submission_id"]=good[0].get("id")
            r["submission_created_at"]=good[0].get("created_at")
            r["submission_state"]="verified"
            break
        if flagged:
            r["backend_recorded"]=True
            r["submission_id"]=flagged[0].get("id")
            r["submission_created_at"]=flagged[0].get("created_at")
            r["submission_state"]="spam"
            r["errors"].append("Netlify marked test as spam; notification may not fire")
            break
        if i<9:time.sleep(3)
    if not r["backend_recorded"]:
        r["errors"].append("One POST returned HTTP success, but submissions API did not yet show test ID")
    site_after=api("sites/"+SITE)
    ensure((site_after.get("published_deploy") or {}).get("id")==PROD,"Published production changed")
    r["status"]="PASS_ONE_REAL_FORM_POST_NETLIFY_BACKEND_VERIFIED_EMAIL_HOOK_CONFIGURED_INBOX_UNVERIFIED" \
        if (r["backend_recorded"] and r.get("submission_state")=="verified" and not r["errors"]) \
        else "HOLD_FORM_POST_OR_BACKEND_RECEIPT_UNCONFIRMED"
except Exception as e:
    r["errors"].append(type(e).__name__+": "+str(e)[:400])
    r["status"]="HOLD_FORM_TEST_NO_UNCONDITIONAL_RETRY"
finally:
    (OUT/"REAL_ONE_SYNTHETIC_CONSULTATION_POST_AND_NETLIFY_SUBMISSION_EMAIL_HOOK_QA.json").write_text(
      json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("ENPT_EXACT_ONE_PROD_SAFE_DRAFT_CONSULTATION_TEST",json.dumps(r,ensure_ascii=False),flush=True)
    if r["status"].startswith("HOLD"):raise SystemExit(1)
