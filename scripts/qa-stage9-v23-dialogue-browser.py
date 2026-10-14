#!/usr/bin/env python3
"""Browser-only v23.1 4-phase change report QA. Never submits a form."""
import base64
import json
import time
from pathlib import Path
import pychrome

OUT=Path("v23-dialogue-render-review")
(OUT/"screenshots").mkdir(parents=True,exist_ok=True)
PAGES=["englishpt.html","english-conversation.html"]
WIDTHS=[(360,True),(390,True),(768,True),(1440,False)]
browser=pychrome.Browser(url="http://127.0.0.1:9238")
tab=browser.new_tab()
tab.start()
tab.Page.enable()
tab.Runtime.enable()
checks=[]
errors=[]
try:
    for width,mobile in WIDTHS:
        tab.call_method("Emulation.setDeviceMetricsOverride",
            width=width,height=900,deviceScaleFactor=1,mobile=mobile,
            screenWidth=width,screenHeight=900,dontSetVisibleSize=False)
        for name in PAGES:
            tab.Page.navigate(url="http://127.0.0.1:8987/"+name)
            time.sleep(0.65)
            expr=r'''(()=>{
              const section=document.querySelector('.change-section');
              const grid=section?.querySelector('.change-grid-four');
              const cards=[...(section?.querySelectorAll('.change-card')||[])];
              const dialogues=cards.map(c=>c.querySelector('.change-dialogue'));
              const widths=grid?getComputedStyle(grid).gridTemplateColumns.split(' ').filter(Boolean).length:0;
              const lines=cards.map(c=>({
                phase:c.querySelector('.change-badge')?.textContent.trim()||'',
                english:c.querySelectorAll('.change-dialogue-english').length,
                korean:c.querySelectorAll('.change-dialogue-korean').length,
                tip:!!c.querySelector('.change-dialogue-tip'),
                escaped:[...c.querySelectorAll('.change-dialogue-english,.change-dialogue-korean')].some(e=>e.scrollWidth>e.clientWidth+3),
                visible:!!c.querySelector('.change-dialogue')&&getComputedStyle(c.querySelector('.change-dialogue')).display!=='none'
              }));
              const cta=section?.querySelector('[data-open-form]');
              return {
                viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,
                gridColumns:widths,cardCount:cards.length,
                intro:!!section?.querySelector('.change-dialogue-intro'),
                phases:lines,ctaPresent:!!cta,
                cssLoaded:getComputedStyle(grid||document.body).display==='grid',
                koreanMeaningsVisible:lines.every(x=>x.korean>=2),
                pendingFormVisibleBeforeClick:document.getElementById('applyModal')?.getAttribute('aria-hidden')==='true'
              };
            })()'''
            obj=tab.Runtime.evaluate(expression=expr,returnByValue=True)["result"]["value"]
            failures=[]
            if obj["viewport"]!=width:failures.append("viewport")
            if obj["scrollWidth"]>width+1:failures.append("horizontal_overflow")
            if obj["cardCount"]!=4:failures.append("four_cards")
            if obj["gridColumns"]!=(1 if width<=900 else 2):failures.append("grid_columns")
            if not obj["intro"]:failures.append("intro")
            if not obj["ctaPresent"]:failures.append("cta_button_missing")
            if not obj["cssLoaded"]:failures.append("stylesheet_not_applied")
            if not obj["koreanMeaningsVisible"]:failures.append("translations_missing")
            required=["1~3개월","3~6개월","6~9개월","9~12개월"]
            if len(obj["phases"])==4:
                for i,p in enumerate(obj["phases"]):
                    if required[i] not in p["phase"]:failures.append("phase_order:"+str(i))
                    if p["english"]<2 or p["english"]!=p["korean"]:failures.append("dialogue_pairs:"+str(i))
                    if p["escaped"] or not p["visible"]:failures.append("dialogue_hidden_or_overflow:"+str(i))
                    if not p["tip"]:failures.append("practice_tip:"+str(i))
            if width in (390,1440):
                indices=(0,2) if width==390 else (0,)
                for idx in indices:
                    tab.Runtime.evaluate(expression=f"document.querySelectorAll('.change-card')[{idx}].scrollIntoView({{block:'start'}})")
                    time.sleep(0.25)
                    screenshot=tab.Page.captureScreenshot(format="png",captureBeyondViewport=False)
                    file=OUT/"screenshots"/f"{name.replace('.html','')}-{width}-stage{idx+1}.png"
                    file.write_bytes(base64.b64decode(screenshot["data"]))
            # Direct browser click tests that the CTA opens the form; no submit.
            click=r'''(()=>{
              const btn=document.querySelector('.change-section [data-open-form]');
              const modal=document.getElementById('applyModal');
              if(!btn||!modal)return {ok:false,reason:'missing_button_or_modal'};
              btn.click();
              const ok=modal.classList.contains('open')&&modal.getAttribute('aria-hidden')==='false';
              const close=modal.querySelector('[data-close-form]');
              if(close)close.click();
              return {ok,afterClose:modal.getAttribute('aria-hidden')};
            })()'''
            result=tab.Runtime.evaluate(expression=click,returnByValue=True)["result"]["value"]
            if not result.get("ok"):failures.append("cta_modal_did_not_open")
            checks.append({"page":name,"width":width,"mobile_emulation":mobile,"observed":obj,"cta":result,"status":"PASS" if not failures else "FAIL","issues":failures})
            errors += [f"{name}@{width}:{v}" for v in failures]
finally:
    tab.stop()
    browser.close_tab(tab)
report={"status":"PASS_V23_DIALOGUE_MOBILE_BROWSER" if not errors else "FAIL_V23_DIALOGUE_MOBILE_BROWSER",
        "pages":PAGES,"widths":[x[0] for x in WIDTHS],
        "browser":"Chromium headless device-metrics emulation; rendered DOM and CTA click only",
        "form_submission":"NOT_PERFORMED","check_count":len(checks),"checks":checks,"errors":errors}
(OUT/"V23_DIALOGUE_BROWSER_QA.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(report["status"],json.dumps({"checks":len(checks),"errors":errors},ensure_ascii=False))
if errors:raise SystemExit(1)
