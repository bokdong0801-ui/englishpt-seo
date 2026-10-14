#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V23.2 real Chromium source-page readability and form-opening smoke QA.

All form interactions are click-only; no form submission or outbound contact.
This checks 5 real nationwide hubs and one clearly labeled generated-component
fixture, NOT live Netlify Preview and NOT all 140,391 rendered pages.
"""
from __future__ import annotations
import base64
import importlib.util
import json
import time
from pathlib import Path
import pychrome

ROOT=Path(".")
OUT=ROOT/"v23-easycopy-browser-review"
(OUT/"screenshots").mkdir(parents=True,exist_ok=True)
GEN=OUT/"beginner-component-fixture.html"
src=Path("scripts/stage9-clean-mass-renderer.py").resolve()
spec=importlib.util.spec_from_file_location("v23_gold_renderer",src)
renderer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)
loc={"slug":"seoul-jongno-sajikdong","dong":"사직동","service":"왕초보영어회화"}
management=renderer.management_section(loc,"beginner-english-conv","service")
GEN.write_text(
    '<!doctype html><html lang="ko"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1">'
    '<title>Generated component test only - NOT a public webpage</title>'
    '<link rel="stylesheet" href="/assets/stage9-mass-production.css">'
    '</head><body class="theme-housewife"><main>'
    '<div class="wrap"><h1>왕초보 영어회화 수업 예시 · 비공개 구성 검증용</h1></div>'
    +management+"</main></body></html>",
    encoding="utf-8",
)
PAGES=[
    "englishpt.html", "courses.html", "student-english.html",
    "english-conversation.html", "exam-english.html",
    "v23-easycopy-browser-review/beginner-component-fixture.html",
]
WIDTHS=[360,390,768,1440]
browser=pychrome.Browser(url="http://127.0.0.1:9239")
tab=browser.new_tab()
tab.start()
tab.Page.enable()
tab.Runtime.enable()
checks=[]
errors=[]
try:
    for width in WIDTHS:
        tab.call_method("Emulation.setDeviceMetricsOverride",
            width=width,height=900,deviceScaleFactor=1,mobile=(width!=1440),
            screenWidth=width,screenHeight=900,dontSetVisibleSize=False)
        for page in PAGES:
            tab.Page.navigate(url="http://127.0.0.1:8989/"+page)
            time.sleep(.5)
            probe=r'''(()=>{
                const section=document.querySelector('main');
                const original=document.querySelector('.change-section');
                const modal=document.getElementById('applyModal');
                const btn=document.querySelector('[data-open-form]');
                const example=document.querySelector('.beginner-sample');
                const en=[...(example?.querySelectorAll('strong[lang="en"]')||[])];
                const ko=[...(example?.querySelectorAll('.beginner-sample-line small')||[])];
                const heading=document.querySelector('h1');
                return {
                  width:innerWidth,
                  scrollWidth:document.documentElement.scrollWidth,
                  main:!!section,
                  heading:heading?.innerText||'',
                  face:getComputedStyle(document.body).fontFamily,
                  actualFontSize:heading?getComputedStyle(heading).fontSize:'',
                  button:!!btn,
                  modal:!!modal,
                  phaseCards:original?.querySelectorAll('.change-card').length??0,
                  examples:example?en.length:0,
                  translations:ko.length,
                  englishVisible:en.every(x=>x.offsetWidth>0&&x.scrollWidth<=x.clientWidth+4),
                  koreanVisible:ko.every(x=>x.offsetWidth>0&&x.scrollWidth<=x.clientWidth+4),
                  aftercare:!!document.querySelector('.manage-aftercare'),
                  termsShown:document.querySelector('main')?.innerText.includes('저가형 대량')??false,
                  siteStyle:!![...document.styleSheets].find(x=>x.href&&x.href.includes('css'))
                };
            })()'''
            result=tab.Runtime.evaluate(expression=probe,returnByValue=True)["result"]["value"]
            issues=[]
            is_fixture="fixture" in page
            if result["width"]!=width:issues.append("wrong_viewport")
            if result["scrollWidth"]>width+1:issues.append("horizontal_overflow")
            if not result["main"] or not result["heading"]:issues.append("missing_main_h1")
            if not result["siteStyle"]:issues.append("css_missing")
            if result["termsShown"]:issues.append("salesy_old_jargon")
            if is_fixture:
                if not result["aftercare"] or result["examples"]!=2 or result["translations"]!=2:
                    issues.append("beginner_qa_example")
                if not result["englishVisible"] or not result["koreanVisible"]:
                    issues.append("beginner_text_clipped")
            else:
                if not result["button"] or not result["modal"]:
                    issues.append("consultation_trigger_missing")
                if page in ("englishpt.html","english-conversation.html") and result["phaseCards"]!=4:
                    issues.append("four_card_timeline")
                if page=="exam-english.html" and result["phaseCards"]!=3:
                    issues.append("exam_card_count")
                click=r'''(()=>{
                  const btn=document.querySelector('[data-open-form]');
                  const modal=document.getElementById('applyModal');
                  if(!btn||!modal)return {opened:false};
                  btn.click();
                  const opened=modal.classList.contains('open')
                    &&modal.getAttribute('aria-hidden')==='false';
                  document.querySelector('[data-close-form]')?.click();
                  return {opened};
                })()'''
                state=tab.Runtime.evaluate(expression=click,returnByValue=True)["result"]["value"]
                if not state.get("opened"):issues.append("form_did_not_open")
            if width in (390,1440):
                if is_fixture:
                    tab.Runtime.evaluate(expression="document.querySelector('.beginner-sample').scrollIntoView({block:'start'})")
                    time.sleep(.1)
                snapshot=tab.Page.captureScreenshot(format="png",captureBeyondViewport=False)
                name=page.split("/")[-1].replace(".html","")+f"-{width}.png"
                (OUT/"screenshots"/name).write_bytes(base64.b64decode(snapshot["data"]))
            if issues:
                errors.append({"page":page,"width":width,"issues":issues})
            checks.append({"page":page,"width":width,"status":"FAIL" if issues else "PASS",
                           "details":result,"issues":issues})
finally:
    tab.stop()
    browser.close_tab(tab)

result={
    "status":"PASS_V23_EASYCOPY_BROWSER" if not errors else "FAIL_V23_EASYCOPY_BROWSER",
    "test_count":len(checks),
    "pages":PAGES,
    "responsive_widths":WIDTHS,
    "checks":checks,
    "failures":errors,
    "live_netlify_preview":"NOT_TESTED",
    "real_form_submission":"NOT_PERFORMED",
    "note":"Chromium rendered real national-hub source files and a separately generated beginner management component fixture.",
}
(OUT/"V23_EASYCOPY_BROWSER_QA.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(result["status"],json.dumps({"checks":len(checks),"errors":errors},ensure_ascii=False))
if errors: raise SystemExit(1)
