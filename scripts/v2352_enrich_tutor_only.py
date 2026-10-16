#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v23.5.2: enrich the existing elementary/middle/high English TUTORING pages only.

Offline review-only renderer. Does not alter conversation landings, sources, SEO,
form schemas, linked destinations or deployments.
"""
import argparse
import html
import json
import re
import sys
import traceback
from collections import Counter
from pathlib import Path

COURSES={"elem-tutor":"elem","mid-tutor":"mid","high-tutor":"high"}
CONTENT_DIR=Path(__file__).resolve().parents[1]/"content"
FAQ_START='<section class="section soft"><div class="wrap narrow"><p class="kicker">학부모 질문</p>'
NAV=re.compile(r'<article class="related-group"><h3>학생 영어</h3><div class="related-course-links">.*?</div></article>',re.S)
CONSULT=re.compile(r'<section\b(?=[^>]*\bid="consultation-preview")(?=[^>]*class="[^"]*consult)[^>]*>.*?</section>',re.S)
META_STOP="</head>"
MARKER='data-v2352-tutor-content="parent-guide-v1"'
CSS_MARKER='/* ENGLISH PT v23.5.2 TUTOR EXTRA CONTEXT — SCOPE ONLY */'
CSS=r"""
/* ENGLISH PT v23.5.2 TUTOR EXTRA CONTEXT — SCOPE ONLY */
.v2352-tutor{overflow-wrap:break-word;word-break:keep-all}
.v2352-tutor .v2352-intro{max-width:760px;line-height:1.78;margin-bottom:19px}
.v2352-tutor .v2352-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px}
.v2352-tutor .v2352-card{background:var(--card,#fff);border:1px solid var(--line,#dce5de);border-radius:16px;padding:19px;min-width:0}
.v2352-tutor .v2352-card h3{font-size:18px;line-height:1.48;margin:0 0 9px;word-break:keep-all}
.v2352-tutor .v2352-card p{margin:0 0 11px;line-height:1.77}
.v2352-tutor .v2352-card p:last-child{margin-bottom:0}
.v2352-tutor .v2352-chip{display:inline-block;border-radius:999px;background:#e9f4ec;color:#245944;padding:5px 11px;font-size:13px;font-weight:700;margin-bottom:12px}
.v2352-tutor .v2352-check{border-top:1px solid var(--line,#dce5de);padding-top:11px;font-size:14px;line-height:1.7}
.v2352-tutor .v2352-check strong{color:#206347}
.v2352-tutor .v2352-steps{display:grid;gap:12px;max-width:920px}
.v2352-tutor .v2352-step{background:var(--card,#fff);border:1px solid var(--line,#dce5de);padding:17px 19px;border-radius:14px}
.v2352-tutor .v2352-step b{display:block;margin-bottom:5px;font-size:16px}
.v2352-tutor .v2352-step p{margin:0;line-height:1.75}
.v2352-tutor .v2352-note{max-width:900px;margin-top:18px;font-size:13px;line-height:1.85;color:var(--muted,#52645b)}
.v2352-tutor .v2352-parent-questions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.v2352-tutor .v2352-parent-questions blockquote{margin:10px 0 0;border-left:3px solid #1e8f63;padding:6px 0 6px 13px;line-height:1.65}
.v2352-tutor .v2352-small-cta{display:inline-flex;align-items:center;margin-top:17px;min-height:44px;border-radius:999px;padding:11px 20px;background:#1e8f63;color:white;text-decoration:none;font-weight:700;line-height:1.5}
@media(max-width:850px){.v2352-tutor .v2352-grid{grid-template-columns:1fr}.v2352-tutor .v2352-parent-questions{grid-template-columns:1fr}.v2352-tutor .v2352-card{padding:16px}}
@media(max-width:390px){.v2352-tutor .v2352-card h3{font-size:16px}.v2352-tutor .v2352-card p,.v2352-tutor .v2352-step p{font-size:14px}.v2352-tutor .v2352-step{padding:14px}.v2352-tutor .v2352-small-cta{width:100%;justify-content:center;text-align:center}}
"""
NOTE=("아래 내용은 수업 방식을 이해하기 위한 예시입니다. 실제 교재·과제량·수업 시간·횟수·학부모 피드백의 제공 방식은 학생 상황과 상담 결과에 따라 달라질 수 있습니다.")

def esc(v):
    return html.escape(str(v),quote=True)

def section(open_class,marker,headline,kicker,inner):
    return ('<section class="section '+open_class+' v2352-tutor" '+MARKER+
            ' data-v2352-section="'+marker+'"><div class="wrap">'+
            '<p class="kicker">'+esc(kicker)+'</p><h2>'+esc(headline)+'</h2>'+inner+'</div></section>')

def card(title,desc,note=None,chip=None):
    return ('<article class="v2352-card">'+
        ('<span class="v2352-chip">'+esc(chip)+'</span>' if chip else '')+
        '<h3>'+esc(title)+'</h3><p>'+esc(desc)+'</p>'+
        ('<p class="v2352-check"><strong>다음 확인</strong> '+esc(note)+'</p>' if note else '')+
        '</article>')

def render(course,loc,data):
    prefix=data["title"]
    intro=(
        '<p class="v2352-intro">'+esc(loc)+' '+esc(prefix)+
        '는 같은 학년이어도 어휘·문장 이해·학교 진도와 목표에 따라 출발점이 달라집니다. '+
        '아래는 학년별로 상담에서 살펴볼 수 있는 내용과 학습 계획의 예시입니다.</p>')
    levels='<div class="v2352-grid">'+''.join(card(title,d,check,grade) for grade,title,d,check in data["levels"])+'</div>'
    grade_section=section('soft','levels',data["level_title"],'학년별 수업 방향',intro+levels)
    steps='<p class="v2352-intro">선생님의 설명만 듣는 수업보다 학생이 실제로 무엇을 할 수 있는지 확인하는 과정을 구체적으로 살펴봅니다.</p>'
    steps+='<div class="v2352-steps">'+''.join(
        '<article class="v2352-step"><b>'+esc(str(i+1)+'. '+title)+'</b><p>'+esc(detail)+'</p></article>'
        for i,(title,detail) in enumerate(data["session"]))+'</div>'
    steps+='<p class="v2352-note">'+esc(NOTE)+'</p>'
    lesson_section=section('','lesson','실제 영어과외 한 번의 수업은 어떻게 이어질까요?','수업 흐름 예시',steps)
    cases='<p class="v2352-intro">같은 오답이라도 원인이 다르면 필요한 공부가 다릅니다. 아래 사례는 실제 학생 후기나 점수 향상을 의미하지 않습니다.</p>'
    cases+='<div class="v2352-grid">'+''.join(
      card("“"+symptom+"”","확인할 원인: "+cause+" / 수업에서: "+action,recheck)
      for symptom,cause,action,recheck in data["cases"])+'</div>'
    cases_section=section('soft','errors','자꾸 틀리는 영어 문제, 정답보다 원인을 확인합니다','오답·재학습의 실제 예시',cases)
    timeline='<p class="v2352-intro">시험 일정과 학습 수준에 따라 순서와 기간은 달라질 수 있습니다.</p>'
    timeline+='<div class="v2352-grid">'+''.join(card(label,detail) for label,detail in data["timeline"])+'</div>'
    timeline_section=section('','timeline',data["timeline_title"],'학습 계획 예시',timeline)
    parents='<p class="v2352-intro">실제 피드백의 주기·전달 방식은 상담에서 확인해야 합니다. 학부모가 공부 과정을 이해할 때 도움이 되는 질문을 정리했어요.</p>'
    parents+='<div class="v2352-parent-questions">'+''.join(
        '<article class="v2352-card"><h3>'+esc(label)+'</h3><p>'+esc(observe)+
        '</p><blockquote>“'+esc(question)+'”</blockquote></article>'
        for label,observe,question in data["parent"])+'</div>'
    parents+='<a class="v2352-small-cta" href="#consultation-preview">우리 아이에게 필요한 영어과외 상담하기 →</a>'
    parents+='<p class="v2352-note">'+esc(NOTE)+'</p>'
    parents_section=section('soft','parent','학부모는 무엇을 확인하면 좋을까요?','과정 점검·상담 질문',parents)
    return '\n'.join([grade_section,lesson_section,cases_section,timeline_section,parents_section])

def build(path,content):
    raw=path.read_text(encoding="utf8")
    if MARKER in raw: raise ValueError("v23.5.2 marker already present; no double injection")
    if raw.count(FAQ_START)!=1:raise ValueError("original tutor FAQ section not unique "+str(raw.count(FAQ_START)))
    if raw.count('class="faq-item"')!=3:raise ValueError("expected exactly three original FAQ details")
    if META_STOP not in raw:raise ValueError("missing HTML head")
    if len(NAV.findall(raw))!=1:raise ValueError("student navigation group absent/duplicated")
    if len(CONSULT.findall(raw))!=1:raise ValueError("consultation form section absent/duplicated")
    m=re.search(r'<h1[^>]*>(.*?)</h1>',raw,re.S|re.I)
    if not m:raise ValueError("missing H1")
    h1=html.unescape(re.sub('<[^>]+>','',m.group(1))).strip()
    if not h1.endswith(content["title"]):raise ValueError("page H1 course label differs: "+h1)
    region=h1[:-len(content["title"])].strip()
    if not region:raise ValueError("missing locality in H1")
    # Keep all existing user-visible sections; add grade-specific content before FAQ.
    insertion=render(path.stem,region,content)
    updated=raw.replace(FAQ_START,insertion+'\n'+FAQ_START,1)
    # Exactly three additional non-overlapping FAQ questions, appended in same FAQ block.
    start=updated.index(FAQ_START)+len(FAQ_START)
    end=updated.index('</div></section>',start)
    faqhtml=''.join('<details class="faq-item"><summary>'+esc(q)+'</summary><p>'+esc(a)+'</p></details>'
                    for q,a in content["faqs"])
    updated=updated[:end]+faqhtml+updated[end:]
    if updated.count(MARKER)!=5 or updated.count('class="faq-item"')!=6:
        raise ValueError("new section count or FAQ count invalid")
    if updated.split(META_STOP,1)[0]!=raw.split(META_STOP,1)[0]:
        raise ValueError("SEO/head unexpectedly changed")
    if NAV.findall(updated)!=NAV.findall(raw) or CONSULT.findall(updated)!=CONSULT.findall(raw):
        raise ValueError("Existing student navigation or consultation form mutated")
    if re.search(r'<h1[^>]*>.*?</h1>',updated,re.S|re.I).group(0)!=m.group(0):
        raise ValueError("H1 content changed")
    if updated.count('href="#consultation-preview"')!=raw.count('href="#consultation-preview"')+1:
        raise ValueError("new parent CTA anchor invalid")
    return updated,region

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--report",type=Path,required=True)
    ap.add_argument("--samples",type=Path,required=True)
    ap.add_argument("--expected-regions",type=int,default=6060)
    ap.add_argument("--expected-generated",type=int,default=158571)
    ap.add_argument("--pilot",action="store_true")
    args=ap.parse_args()
    root=args.root.resolve()
    result={"status":"STARTED","version":"v23.5.2","source_seo_run":38868768031,
        "base_source_run":38689660290,"base_sha":"a18b8901ecda7d37f65e35b15f03d579ec63c70f",
        "tutor_pages_expected":args.expected_regions*3,"tutor_pages_updated":0,
        "localities":0,"by_course":{},"faq_entries_added":0,
        "seo_headers_changed":False,"form_html_changed":False,"student_nav_changed":False,
        "css_files_updated":[],"errors_count":0,"errors":[],"production_deployed":False,"draft_deployed":False}
    sample={"elem-tutor":0,"mid-tutor":0,"high-tutor":0}
    counter=Counter()
    try:
        data={course:json.loads((CONTENT_DIR/("v2352_"+alias+"_tutor.json")).read_text(encoding="utf8"))
              for course,alias in COURSES.items()}
        for course,item in data.items():
            for key,n in (("levels",3),("session",5),("cases",3),("timeline",3),("parent",4),("faqs",3)):
                if len(item.get(key,[]))!=n:raise ValueError(course+" invalid "+key+" length")
        pages=sorted(root.glob("*-elem-tutor.html"))
        valid=[p for p in pages if (root/(p.name[:-len("-elem-tutor.html")]+"-worker-english-conv-academy.html")).is_file()
            and (root/(p.name[:-len("-elem-tutor.html")]+"-mid-conv.html")).is_file()
            and (root/(p.name[:-len("-elem-tutor.html")]+"-high-conv.html")).is_file()]
        if len(valid)!=args.expected_regions:
            raise ValueError("locality number mismatch: "+str(len(valid)))
        if not args.pilot:
            # Scanning other non-tutor pages is not needed; only assert source count.
            if len(list(root.glob("*.html")))-2!=args.expected_generated:
                raise ValueError("source HTML count differs from 158571")
        result["localities"]=len(valid)
        args.samples.mkdir(parents=True,exist_ok=True)
        for i,elem in enumerate(valid):
            slug=elem.name[:-len("-elem-tutor.html")]
            for course,contents in data.items():
                target=root/(slug+"-"+course+".html")
                if not target.is_file():raise ValueError("missing tutor page: "+target.name)
                updated,loc=build(target,contents)
                target.write_text(updated,encoding="utf8")
                counter[course]+=1
                result["tutor_pages_updated"]+=1
                result["faq_entries_added"]+=3
                if (loc in ("내이동","사직동") or sample[course]==0) and sample[course]<3:
                    (args.samples/target.name).write_text(updated,encoding="utf8")
                    sample[course]+=1
            if (i+1)%1000==0:
                print("V2352_TUTOR_ENRICH_PROGRESS",i+1,len(valid),result["tutor_pages_updated"],flush=True)
        for cssname in ("pilot.css","assets/styles.css"):
            stylesheet=root/cssname
            if stylesheet.is_file():
                css=stylesheet.read_text(encoding="utf8")
                if CSS_MARKER in css:raise ValueError("stylesheet already patched "+cssname)
                stylesheet.write_text(css+"\n"+CSS,encoding="utf8")
                result["css_files_updated"].append(cssname)
        if len(result["css_files_updated"])!=2:raise ValueError("both tutor CSS sources must exist")
        if result["tutor_pages_updated"]!=args.expected_regions*3:
            raise ValueError("incomplete tutor page coverage")
        result["by_course"]=dict(counter)
        result["sample_pages"]=sorted(p.name for p in args.samples.glob("*.html"))
        result["status"]="PASS_V2352_TUTOR_PAGES_ONLY_RENDERED"
    except Exception as exc:
        result["status"]="FAIL_V2352_TUTOR_PAGES_ONLY_RENDERED"
        result["errors_count"]=1
        result["errors"].append({"error":str(exc),"trace":traceback.format_exc()[-1800:]})
    finally:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print(result["status"],"localities",result["localities"],
              "updated",result["tutor_pages_updated"],"errors",result["errors_count"],flush=True)
        for error in result["errors"][:5]:print("::error::"+str(error),flush=True)
    return 0 if result["status"].startswith("PASS") else 1

if __name__=="__main__":sys.exit(main())
