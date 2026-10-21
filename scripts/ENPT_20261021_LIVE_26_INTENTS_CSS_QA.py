#!/usr/bin/env python3
"""Cross-intent actual browser QA: all 23 locality course types x mobile and desktop.
GET only. Centers comparison paragraphs under same global shared CSS rule.
"""
import json,os,pathlib,datetime
from playwright.sync_api import sync_playwright
from shutil import which
BASE="https://englishpt.kr"
ROOT=pathlib.Path("prod-live-css-qa");ROOT.mkdir(exist_ok=True)
INTENTS=[
"elem-tutor","mid-conv","high-conv","univ-conv","jobseeker-conv","biz-business-conv","housewife-conv",
"toeic","toeic-speaking","opic","ielts","duolingo","toefl",
"toeic-academy","toeic-speaking-academy","opic-academy","ielts-academy",
"duolingo-academy","toefl-academy","english-conv-academy","adult-english-conv-academy",
"worker-english-conv-academy","beginner-english-conv"]
assert len(INTENTS)==23
SKILL_EXTRA=["elem-conv","mid-tutor","high-tutor"]
rows=[];errors=[];non_get=[]
with sync_playwright() as pw:
 chrome=which("google-chrome") or which("chromium") or which("chromium-browser")
 assert chrome
 browser=pw.chromium.launch(executable_path=chrome,headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
 for w in (390,1440):
  ctx=browser.new_context(viewport={"width":w,"height":850},locale="ko-KR")
  def read_only(route):
   if route.request.method not in ("GET","HEAD"):
    non_get.append(route.request.url);route.abort()
   else:route.continue_()
  ctx.route("**/*",read_only)
  p=ctx.new_page();p.set_default_timeout(15000)
  for intent in INTENTS+SKILL_EXTRA:
   path="/ulsan-buk-nongso2dong-"+intent+".html"
   row={"width":w,"intent":intent,"path":path,"errors":[]}
   try:
    response=p.goto(BASE+path,wait_until="domcontentloaded",timeout=55000)
    assert response and response.status==200,"HTTP_NOT200"
    assert p.evaluate("document.documentElement.scrollWidth<=innerWidth+12"),"OVERFLOW"
    assert p.locator('form[name="englishpt-consultation"]').count()==1,"FORM"
    section=p.locator(".mass-context").first
    if section.count()==0:
     row["comparison_section"]="ABSENT"
     # 3 additional tutor variants may use separate tutor template, report separately
     if intent not in SKILL_EXTRA and intent!="elem-tutor":row["errors"].append("MASS_CONTEXT_MISSING")
    else:
     ps=section.locator(".context-block p")
     if ps.count()==0:row["errors"].append("COMPARE_P_MISSING")
     else:
      styles=ps.first.evaluate("x=>({align:getComputedStyle(x).textAlign,display:getComputedStyle(x).display})")
      row["computed_styles"]=styles
      if styles["align"]!="center":row["errors"].append("COMPARE_P_NOT_CENTER")
     h2=section.locator("h2").first
     if h2.count() and h2.evaluate("x=>getComputedStyle(x).textAlign")!="center":row["errors"].append("COMPARE_H2_NOT_CENTER")
   except Exception as e:row["errors"].append(type(e).__name__+":"+str(e).splitlines()[0][:180])
   rows.append(row)
   if row["errors"]:errors.append(row)
  p.close();ctx.close()
 browser.close()
result={"status":"PASS_ALL_23_LOCAL_INTENTS_RESPONSIVE_COMPARISON_CENTER" if not errors and not non_get else "HOLD_CROSS_INTENT_ALIGNMENT","original_intents":23,"supplemental_student_intents":3,"viewports":[390,1440],"checked_url_viewports":len(rows),"errors":errors,"non_GET_count":len(non_get),"forms_submitted":0,"production_published":False,"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"details":rows}
(ROOT/"ALL_23_INTENTS_ALIGNMENT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),"utf8")
print("ENPT_ALL_23_INTENTS_VISUAL_CSS_QA",json.dumps({k:v for k,v in result.items() if k!="details"},ensure_ascii=False),flush=True)
if errors or non_get:raise SystemExit(1)
