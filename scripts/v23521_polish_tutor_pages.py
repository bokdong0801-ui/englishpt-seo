#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v23.5.2.1 parent-focused editorial polish on previously verified tutoring HTML only.

Review-only. Preserves hrefs, canonical, OG, meta, scripts, Netlify form
structure/field names, course-selection hidden fields and other 140391 pages.
"""
import argparse,html,json,re,sys,traceback,hashlib
from pathlib import Path
from collections import Counter

OLD_STEPS=re.compile(r'<section class="section mass-context"><div class="wrap narrow"><p class="kicker">1:1 수업 진행</p>.*?</div></section>',re.S)
OLD_EXAMPLE=re.compile(r'<section class="section"><div class="wrap narrow"><p class="kicker">수업에서 확인하는 예시</p>.*?</div></section>',re.S)
PARENT_BLOCK=re.compile(r'(<section class="section soft v2352-tutor"[^>]*data-v2352-section="parent"[^>]*>.*?)(<p class="v2352-note">.*?</p>)(</div></section>)',re.S)
NAV=re.compile(r'<article class="related-group"><h3>학생 영어</h3><div class="related-course-links">.*?</div></article>',re.S)
FORM=re.compile(r'<form\b[^>]*>.*?</form>',re.S)
COURSES=('elem-tutor','mid-tutor','high-tutor')
INTRO_FAQ={
    "elem-tutor":(
       '<summary>학교 시험 대비와 기초 영어를 동시에 할 수 있나요?</summary><p>학교',
       '<summary>학교 영어가 어렵다면 읽기·문법 중 무엇부터 살펴봐야 하나요?</summary><p>학교')
}
# Do not modify user-visible FAQ by global substring: replace the entire
# FAQ detail after checking exact current phrasing.
FAQ_OLD_ELEMENTARY=(
    '<summary>학교 시험 대비와 기초 영어를 동시에 할 수 있나요?</summary>',
    '<summary>학교 영어가 어렵다면 읽기·문법 중 무엇부터 살펴봐야 하나요?</summary>'
)
FAQ_OLD_HIGH=(
    '<summary>고2·고3은 내신과 수능 영어를 동시에 관리할 수 있나요?</summary><p>시험 일정·목표·기초 수준에 따라 우선순위를 달리할 수 있습니다. 학교 시험이 가까운 기간과 모의고사 약점 보완 기간에 같은 비중을 유지할 필요는 없습니다.</p>',
    '<summary>고2에서 고3으로 올라가기 전 무엇을 먼저 점검해야 하나요?</summary><p>최근 모의고사를 바탕으로 어휘·긴 문장 이해·독해 유형·시간 부족의 원인을 구분해보는 것이 좋습니다. 새로운 문제집을 늘리기보다 반복되는 약점을 확인한 뒤 다음 학년의 학습 우선순위를 정합니다.</p>'
)
CTA_REPLACEMENTS=(
    ('<a class="nav-cta" href="#consultation-preview">체험수업 신청</a>',
     '<a class="nav-cta" href="#consultation-preview">영어과외 상담 신청</a>'),
    ('<button class="submit-lead" type="submit">체험수업 신청 →</button>',
     '<button class="submit-lead" type="submit">영어과외 상담 신청 →</button>'),
    ('<a class="floating-contact-btn floating-trial" href="#consultation-preview" data-trial-cta><strong>체험수업 신청</strong>',
     '<a class="floating-contact-btn floating-trial" href="#consultation-preview" data-trial-cta><strong>영어과외 상담 신청</strong>'),
    ('id="leadSubject" name="subject" data-remove-prefix value="ENGLISH PT 체험수업 신청"',
     'id="leadSubject" name="subject" data-remove-prefix value="ENGLISH PT 영어과외 상담 신청"'),
    ('id="leadRequestType" name="requestType" value="체험수업 신청"',
     'id="leadRequestType" name="requestType" value="영어과외 상담 신청"'),
)
def normalize_forms(s):
    match=FORM.findall(s)
    if len(match)!=1:raise ValueError("expected unique Netlify consultation form")
    block=match[0]
    fields=tuple(sorted(re.findall(r'\bname="([^"]+)"',block)))
    ids=tuple(sorted(re.findall(r'\bid="([^"]+)"',block)))
    method=block.split('>',1)[0]
    return fields,ids,method

def patch(s,mode):
    if mode not in COURSES:raise ValueError("Only school English tutoring permitted")
    head=s.split('</head>',1)[0]
    nav=NAV.findall(s)
    if len(nav)!=1:raise ValueError("existing student group missing")
    form_before=normalize_forms(s)
    if s.count('data-v2352-tutor-content="parent-guide-v1"')!=5:
        raise ValueError("existing five tutoring content sections missing")
    if s.count('class="faq-item"')!=6:
        raise ValueError("existing 6 FAQ entries missing")
    if len(OLD_STEPS.findall(s))!=1 or len(OLD_EXAMPLE.findall(s))!=1:
        raise ValueError("duplicated original 4-step/example sections not unique")
    s,n1=OLD_STEPS.subn("",s)
    s,n2=OLD_EXAMPLE.subn("",s)
    if (n1,n2)!=(1,1):raise ValueError("unable to remove duplicate older sections")
    s,note_count=PARENT_BLOCK.subn(lambda m:m.group(1)+m.group(3),s)
    if note_count!=1:raise ValueError("cannot identify repeated parent disclaimer")
    for before,after in CTA_REPLACEMENTS:
        if s.count(before)!=1:raise ValueError("expected one explicit CTA or hidden field: "+before[:100])
        s=s.replace(before,after,1)
    if '체험수업 신청' in s:raise ValueError("old trial wording remains on tutoring page")
    if mode=="elem-tutor":
        before,after=FAQ_OLD_ELEMENTARY
        if s.count(before)!=1:raise ValueError("old elementary FAQ missing")
        s=s.replace(before,after,1)
        # Also replace misleading old answer referring to school exams.
        faq_start=s.index(after)+len(after)
        faq_end=s.index('</p></details>',faq_start)
        s=s[:faq_start]+ '<p>먼저 현재 교과 문장을 혼자 읽고 뜻을 설명할 수 있는지 확인합니다. 낱말 읽기부터 어렵다면 읽기 출발점을, 문장은 읽지만 해석이 막힌다면 어휘와 문장 구조를 살펴보는 방식이 도움이 될 수 있습니다.' +s[faq_end:]
    elif mode=="high-tutor":
        before,after=FAQ_OLD_HIGH
        if s.count(before)!=1:raise ValueError("duplicated high-school FAQ missing")
        s=s.replace(before,after,1)
    if s.split('</head>',1)[0]!=head:raise ValueError("SEO/head mutated")
    if NAV.findall(s)!=nav:raise ValueError("student course navigation was mutated")
    fields,ids,opening=normalize_forms(s)
    if (fields,ids,opening)!=form_before:raise ValueError("Netlify form field schema mutated")
    if s.count('data-v2352-tutor-content="parent-guide-v1"')!=5:
        raise ValueError("new grade-level explanations mutated")
    if s.count('class="faq-item"')!=6:raise ValueError("FAQ length changed")
    if s.count('class="v2352-note"')!=1:raise ValueError("single actual example disclaimer expected")
    if s.count('href="#consultation-preview"')!=3 and s.count('href="#consultation-preview"')!=4:
        raise ValueError("consultation anchor count altered")
    if s.count('data-trial-cta')!=1:raise ValueError("sticky CTA JS hook changed")
    return s

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--report",type=Path,required=True)
    ap.add_argument("--overlay-dir",type=Path,required=True)
    ap.add_argument("--pilot",action="store_true")
    ap.add_argument("--expected-regions",type=int,default=6060)
    args=ap.parse_args()
    root=args.root
    report={"status":"RUNNING","version":"v23.5.2.1","source_run":38878640560,
      "old_sections_removed":0,"disclaimers_deduplicated":0,
      "consultation_text_and_classification_aligned":0,
      "faq_questions_refined":0,"changed_tutor_pages":0,
      "non_tutor_html_changed":False,"page_head_modified":False,
      "form_fields_changed":False,"student_links_changed":False,
      "error_count":0,"errors":[],"production_deployed":False,"form_submitted":False}
    try:
        slugs=[]
        if args.pilot:
            stems=sorted(root.glob("*-elem-tutor.html"))
            slugs=[x.name[:-len("-elem-tutor.html")] for x in stems]
        else:
            stems=sorted(root.glob("*-elem-tutor.html"))
            for f in stems:
                prefix=f.name[:-len("-elem-tutor.html")]
                if (root/(prefix+"-worker-english-conv-academy.html")).is_file() and (
                   root/(prefix+"-mid-conv.html")).is_file() and (
                   root/(prefix+"-high-conv.html")).is_file():
                    slugs.append(prefix)
        if len(slugs)!=args.expected_regions:
            raise ValueError("regional scope mismatch: "+str(len(slugs))+
                 " expected="+str(args.expected_regions))
        args.overlay_dir.mkdir(parents=True,exist_ok=True)
        for i,slug in enumerate(slugs):
            for course in COURSES:
                file=root/(slug+"-"+course+".html")
                if not file.is_file():raise ValueError("missing regional tutor page "+file.name)
                current=file.read_text("utf8")
                updated=patch(current,course)
                file.write_text(updated,encoding="utf8")
                (args.overlay_dir/file.name).write_text(updated,encoding="utf8")
                report["old_sections_removed"]+=2
                report["disclaimers_deduplicated"]+=1
                report["consultation_text_and_classification_aligned"]+=5
                report["faq_questions_refined"]+=int(course!="mid-tutor")
                report["changed_tutor_pages"]+=1
            if (i+1)%1000==0:
                print("V23521_PARENT_COPY_POLISH_PROGRESS",i+1,len(slugs),report["changed_tutor_pages"],flush=True)
        if report["changed_tutor_pages"]!=args.expected_regions*3:raise ValueError("incomplete page count")
        report["status"]="PASS_V23521_PARENT_COPY_POLISH_TUTORS_ONLY"
    except Exception:
        report["error_count"]=1;report["errors"].append(traceback.format_exc()[-1800:])
        report["status"]="HOLD_V23521_PARENT_COPY_POLISH_TUTORS_ONLY"
    finally:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print(report["status"],report["changed_tutor_pages"],report["errors"][:1],flush=True)
    return 0 if report["status"].startswith("PASS") else 1

if __name__=="__main__":sys.exit(main())
