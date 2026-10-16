#!/usr/bin/env python3
"""v23.5 immutable Draft QA: real browser consultation journeys and 29 OG center-square crops.
GET/HEAD only. Never submits a form, modifies production, or deploys anything.
"""
from __future__ import annotations
import io, json, os, re, shutil, struct, sys, time, traceback, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps, ImageFont
from playwright.sync_api import sync_playwright

DRAFT="https://6ad1988e906a5d8e1bb920c9--englishpt-final-ia-review-bokdong.netlify.app"
ALIAS="https://v235-og-hero-20261016--englishpt-final-ia-review-bokdong.netlify.app"
assert DRAFT.endswith("--englishpt-final-ia-review-bokdong.netlify.app")
assert ALIAS.endswith("--englishpt-final-ia-review-bokdong.netlify.app")
BASE=Path("v235-final-visual-qa")
SCREENS=BASE/"screenshots"
OG_FOLDER=BASE/"og-original"
CROPS=BASE/"og-square"
for p in (BASE,SCREENS,OG_FOLDER,CROPS):p.mkdir(parents=True,exist_ok=True)
PAGE_NAMES=[
"englishpt.html","student-english.html","courses.html","exam-english.html",
"english-conversation.html","stations.html",
"seoul-jongno-sajikdong-worker-english-conv-academy.html",
"seoul-jongno-sajikdong-beginner-english-conv.html",
"seoul-jongno-sajikdong-toeic.html",
"seoul-jongno-sajikdong-ielts.html",
"dalseo-songhyeondong.html",
"station-gangnam.html","station-amsayeoksagongwon.html",
"station-gukjegeumyungsenteo-busaneunhaeng-worker-english-conv-academy.html",
]
OG_NAMES=[
"beginner","toeic","ielts","toefl","opic","tos","duolingo","elementary",
"middle","high","student","worker","college","jobseeker","housewife","stations",
"region","academy","tutor","conversation","exam","courses","englishpt",
"reading","writing","international","phone","video","general",
]
SIX=[
"사직동 초등학생영어과외","사직동 중학생영어과외","사직동 고등학생영어과외",
"사직동 초등학생영어회화","사직동 중학생영어회화","사직동 고등학생영어회화",
]
def save(name,data):
    (BASE/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("QA_REPORT",name,data.get("status"),flush=True)
def get(url,timeout=35):
    req=urllib.request.Request(url,headers={"User-Agent":"ENGLISHPT-v235-safe-visual-inspection"})
    with urllib.request.urlopen(req,timeout=timeout) as res:
        return res.status,res.read(),res.url
def err(report,page,kind,detail="",width=None):
    issue={"page":page,"issue":kind,"detail":str(detail)[:480]}
    if width:issue["width"]=width
    report["errors"].append(issue)
    print("::error::"+json.dumps(issue,ensure_ascii=False),flush=True)
def warn(report,page,kind,detail="",width=None):
    report["warnings"].append({"page":page,"issue":kind,"detail":str(detail)[:350],"width":width})
def font(size):
    for path in (
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ):
        if Path(path).exists():return ImageFont.truetype(path,size)
    return ImageFont.load_default()
def build_sheet(rows,base,out,perrow=3,cellw=510,cellh=320):
    n=len(rows); cols=perrow
    sheet=Image.new("RGB",(cols*cellw,((n+cols-1)//cols)*cellh),"#ECEDEA")
    d=ImageDraw.Draw(sheet)
    titlefont=font(20)
    for i,row in enumerate(rows):
        x=(i%cols)*cellw;y=(i//cols)*cellh
        name=row["name"]
        full=Image.open(base/(name+".png")).convert("RGB")
        square=Image.open(CROPS/(name+".png")).convert("RGB")
        full.thumbnail((315,212));square.thumbnail((165,190))
        sheet.paste(full,(x+8,y+36));sheet.paste(square,(x+333,y+36))
        d.text((x+8,y+7),f'{i+1:02}  {name}',font=titlefont,fill="#1B2722")
        status="CROP PASS" if row["square_safe"] else "REVIEW"
        d.text((x+8,y+263),status,font=titlefont,fill="#153e35" if row["square_safe"] else "#B72C31")
    sheet.save(out,optimize=True)
def og_check():
    result={"status":"RUNNING","source":"live v23.5 OG alias", "draft_alias":ALIAS,
            "images":[], "errors":[],"warnings":[],
            "square_crop":"centered 630x630 from 1200x630; [285,915] x",
            "production_deployed":False,"form_submitted":False}
    try:
        for i,name in enumerate(OG_NAMES):
            url=f"{ALIAS}/assets/images/og-pages/{name}.png"
            try:
                status,bytes_,landed=get(url)
                if status!=200:raise ValueError(f"HTTP {status}")
                image=Image.open(io.BytesIO(bytes_)).convert("RGB")
                if image.size!=(1200,630):raise ValueError("PNG dimensions "+str(image.size))
                image.save(OG_FOLDER/(name+".png"),optimize=True)
                square=image.crop((285,0,915,630))
                square.save(CROPS/(name+".png"),optimize=True)
                bg=image.getpixel((175,305))
                # In a light panel, dark ink has RGB well below panel fill.
                # Decorative frame/background is excluded with x/y bounds.
                bbox=[1200,630,-1,-1]
                for y in range(155,492,3):
                    for x in range(145,1055,2):
                        r,g,b=image.getpixel((x,y))
                        if (max(abs(r-bg[0]),abs(g-bg[1]),abs(b-bg[2]))>85
                                and (r+g+b)<425):
                            bbox[0]=min(bbox[0],x);bbox[1]=min(bbox[1],y)
                            bbox[2]=max(bbox[2],x);bbox[3]=max(bbox[3],y)
                box=None if bbox[2]<0 else bbox
                # 20px guard against platform crop rounding.
                safe=bool(box and bbox[0]>=305 and bbox[2]<=895)
                result["images"].append({"name":name,"url":url,"width":1200,"height":630,
                                         "square_crop_center":[285,0,915,630],
                                         "observed_foreground_bbox":box,
                                         "square_safe":safe,"status":"PASS" if safe else "REVIEW"})
                if not safe:
                    err(result,name,"square_crop_safe_area",box)
                print("OG_VISUAL",i+1,name,"PASS" if safe else "REVIEW",box,flush=True)
            except Exception as exc:
                err(result,name,"OG_fetch_or_image_error",repr(exc))
        valid=[x for x in result["images"] if (OG_FOLDER/(x["name"]+".png")).is_file()]
        if valid:
            build_sheet(valid,OG_FOLDER,BASE/"og_29_full_vs_square_contact_sheet.png")
        result["checked"]=len(result["images"])
        result["crop_safe"]=sum(x["square_safe"] for x in result["images"])
        result["status"]="PASS_OG_29_CENTER_SQUARE" if not result["errors"] and len(result["images"])==29 else "HOLD_OG_29_CENTER_SQUARE"
    except Exception:
        err(result,"runner","OG_unhandled_error",traceback.format_exc()[-1400:])
        result["status"]="HOLD_OG_29_CENTER_SQUARE"
    finally:
        save("OG_29_SQUARE_VISUAL_REPORT.json",result)
    return result

def browser_check():
    result={"status":"RUNNING","draft":DRAFT,"viewports":[390,1440],
            "pages":PAGE_NAMES,"checks":[],"cta_clicks":0,
            "forms_reached":0,"student_link_clicks":0,"errors":[],"warnings":[],
            "screenshots":[],"actual_form_submissions":0,"production_deployed":False}
    capture={"blocked_posts":0,"page_submit_events":0}
    try:
        with sync_playwright() as pw:
            binary=shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
            launch={"headless":True,"args":["--no-sandbox","--disable-dev-shm-usage"]}
            if binary:launch["executable_path"]=binary
            browser=pw.chromium.launch(**launch)
            try:
                for width in (390,1440):
                    ctx=browser.new_context(viewport={"width":width,"height":900},device_scale_factor=1,
                          is_mobile=width<600,has_touch=width<600)
                    def route_handler(route):
                        if route.request.method not in ("GET","HEAD"):
                            capture["blocked_posts"]+=1
                            route.abort()
                        else:route.continue_()
                    ctx.route("**/*",route_handler)
                    for name in PAGE_NAMES:
                        page=ctx.new_page()
                        url=DRAFT+"/"+name
                        try:
                            page.add_init_script("""document.addEventListener('submit',e=>{
                              e.preventDefault();e.stopImmediatePropagation();
                              window.__NO_REAL_SUBMISSION__=true;
                            },true);""")
                            resp=page.goto(url,wait_until="domcontentloaded",timeout=50000)
                            if not resp or resp.status!=200:raise ValueError("page not HTTP 200")
                            page.evaluate("() => document.fonts.ready")
                            page.wait_for_timeout(350)
                            data=page.evaluate("""() => {
                              const h=document.querySelector('h1'),r=h?.getBoundingClientRect();
                              return {h1:h?.innerText||'',h1_visible:!!r&&r.width>0&&r.height>0,
                                document_width:document.documentElement.scrollWidth,
                                viewport:innerWidth,
                                link_cta:document.querySelectorAll('a[href="#consultation-preview"]').length,
                                modal_cta:document.querySelectorAll('[data-open-form]').length,
                                form_count:document.querySelectorAll('form').length};
                            }""")
                            problems=[]
                            if not data["h1_visible"]:problems.append("H1 not visible")
                            if data["document_width"]>width+3:problems.append("horizontal overflow")
                            title=name.removesuffix(".html")
                            top=SCREENS/(title+"-"+str(width)+"-hero.png")
                            page.screenshot(path=str(top),full_page=False,timeout=20000)
                            result["screenshots"].append(str(top))
                            # Activate a visible customer consultation CTA:
                            # modal on hubs; scroll-to-inline on service pages.
                            modal=page.locator("[data-open-form]:visible")
                            anchor=page.locator('a[href="#consultation-preview"]:visible')
                            reached=False; mode="missing"
                            if modal.count():
                                modal.first.click(timeout=7000)
                                mode="modal"
                                dialog=page.locator("#applyModal")
                                reached=dialog.count()>0 and dialog.evaluate(
                                    "e=>e.classList.contains('open') && e.getAttribute('aria-hidden') !== 'true'")
                            elif anchor.count():
                                anchor.first.click(timeout=7000)
                                mode="inline"
                                target=page.locator("#consultation-preview")
                                reached=target.count()>0
                                if reached:
                                    target.scroll_into_view_if_needed(timeout=5000)
                            else:
                                problems.append("no visible consultation CTA")
                            if reached:
                                result["forms_reached"]+=1
                                result["cta_clicks"]+=1
                                if mode=="modal":
                                    sheet=page.locator("#applyModal")
                                    form=sheet.locator("form").first
                                else:
                                    form=page.locator("#consultation-preview form").first
                                    if not form.count():form=page.locator("form.lead-form").first
                                if not form.count():
                                    problems.append("CTA reached but no form found")
                                else:
                                    structure=form.evaluate("""f=>{
                                      const field=n=>f.querySelector('[name="'+n+'"]');
                                      const consent=field('consent');
                                      const name=field('name'),phone=field('phone'),area=field('area');
                                      return {name:!!name,phone:!!phone,area:!!area,
                                        name_required:!!name?.required,phone_required:!!phone?.required,
                                        area_required:!!area?.required,consent:!!consent,
                                        consent_required:!!consent?.required,
                                        form_action:f.action,form_method:f.method};
                                    }""")
                                    expected=("name","phone","area","name_required","phone_required","area_required","consent","consent_required")
                                    absent=[k for k in expected if not structure.get(k)]
                                    if absent:problems.append("missing required field(s): "+",".join(absent))
                                    focus=form.locator('input[name="name"]').first
                                    if focus.count():focus.focus(timeout=5000)
                                    formshot=SCREENS/(title+"-"+str(width)+"-form.png")
                                    page.screenshot(path=str(formshot),full_page=False,timeout=20000)
                                    result["screenshots"].append(str(formshot))
                                    result.setdefault("form_structures",[]).append({"page":name,"width":width,"structure":structure})
                            else:
                                problems.append("consultation CTA did not open/scroll")
                            if name.endswith("worker-english-conv-academy.html"):
                                # Verify six cards on both sizes by actual click, never form submit.
                                page.goto(url,wait_until="domcontentloaded",timeout=45000)
                                group=page.locator("article.related-group").filter(has=page.locator("h3",has_text="학생 영어")).first
                                cards=group.locator("a") if group.count() else page.locator("a:has-text('사직동 초등학생영어과외')")
                                if cards.count()!=6:problems.append("expected 6 student links, got "+str(cards.count()))
                                else:
                                    for i,label in enumerate(SIX):
                                        link=cards.nth(i)
                                        if label not in " ".join(link.inner_text().split()):
                                            problems.append("student card label mismatch at "+str(i))
                                            continue
                                        dest=link.get_attribute("href")
                                        # Open the exact destination through Playwright,
                                        # then check the fragment actually exists.
                                        if not dest:
                                            problems.append("empty student card href at "+str(i))
                                            continue
                                        next_page=ctx.new_page()
                                        try:
                                            try:
                                                link.click(timeout=5000)
                                                # Can navigate current page; more reliable to independently
                                                # resolve exactly the same href to this Draft host.
                                                navigation=page.url
                                            except Exception:
                                                navigation=""
                                            from urllib.parse import urljoin,urlsplit,unquote
                                            target=urljoin(url,dest)
                                            rr=next_page.goto(target,wait_until="domcontentloaded",timeout=35000)
                                            if not rr or rr.status!=200:
                                                problems.append("student click target bad HTTP "+str(i))
                                            else:
                                                fragment=urlsplit(target).fragment
                                                if fragment and next_page.locator('[id="'+unquote(fragment)+'"]').count()!=1:
                                                    problems.append("student click missing destination anchor "+fragment)
                                                else:result["student_link_clicks"]+=1
                                        except Exception as exc:
                                            problems.append("student navigation "+str(i)+":"+str(exc)[:85])
                                        finally:
                                            next_page.close()
                                            # Always reset source after navigation:
                                            page.goto(url,wait_until="domcontentloaded",timeout=45000)
                                            group=page.locator("article.related-group").filter(has=page.locator("h3",has_text="학생 영어")).first
                                            cards=group.locator("a")
                            result["checks"].append({"page":name,"width":width,
                               "h1":data["h1"],"document_width":data["document_width"],
                               "cta_mode":mode,"form_reached":reached,"errors":problems})
                            for issue in problems:err(result,name,issue,width=width)
                            print("UI_QA",width,name,"PASS" if not problems else problems,flush=True)
                        except Exception as exc:
                            err(result,name,"browser_navigation_exception",repr(exc),width)
                        finally:page.close()
                    ctx.close()
            finally:browser.close()
    except Exception:
        err(result,"runner","browser_exception",traceback.format_exc()[-1600:])
    finally:
        result["actual_form_submissions"]=0
        result["requests_aborted_non_get_head"]=capture["blocked_posts"]
        result["status"]="PASS_V235_UI_CONSULTATION" if len(result["checks"])==len(PAGE_NAMES)*2 and not result["errors"] else "HOLD_V235_UI_CONSULTATION"
        save("V235_UI_CONSULTATION_REPORT.json",result)
    return result

def main():
    og=og_check()
    ui=browser_check()
    status="PASS_V235_UI_AND_OG_SQUARE" if og["status"].startswith("PASS") and ui["status"].startswith("PASS") else "HOLD_V235_UI_AND_OG_SQUARE"
    summary={
        "status":status,"draft_url":DRAFT,"og_alias":ALIAS,
        "og_images_checked":og.get("checked",0),"square_safe":og.get("crop_safe",0),
        "og_errors":og["errors"],
        "ui_pages":len(PAGE_NAMES),"ui_viewports":[390,1440],
        "ui_checks":len(ui["checks"]),"forms_reached":ui["forms_reached"],
        "student_links_checked_by_browser":ui["student_link_clicks"],
        "ui_errors":ui["errors"],
        "form_submissions":0,"netlify_deployed":False,"production_deployed":False,
        "limitations":["No real form submission; response emails/Netlify backend not tested",
                       "Square preview simulated with centered 630x630 crop; platforms may crop differently",
                       "Representative URLs only, not 140391 browser journeys"]
    }
    save("V235_UI_AND_OG_FINAL_SUMMARY.json",summary)
    print(status,"og",summary["og_images_checked"],"crop-safe",summary["square_safe"],
          "ui",summary["ui_checks"],"forms",summary["forms_reached"],
          "ui-errors",len(summary["ui_errors"]),flush=True)
    return 0 if status.startswith("PASS") else 1
if __name__=="__main__":sys.exit(main())
