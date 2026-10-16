#!/usr/bin/env python3
"""Independent v23.5.1 full-site student routing & semantic content QA.
Check 158571 generated HTML, 6060 regions x26 intents, 945360 six-way links.
No network access, no Production deployment or submissions.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit
from collections import Counter

COURSES=("elem-tutor","mid-tutor","high-tutor","elem-conv","mid-conv","high-conv")
LABELS=("초등학생영어과외","중학생영어과외","고등학생영어과외",
        "초등학생영어회화","중학생영어회화","고등학생영어회화")
NAV=re.compile(r'<article class="related-group"><h3>학생 영어</h3><div class="related-course-links">(.*?)</div></article>',re.S)
ANCHOR=re.compile(r'<a\b[^>]*>.*?</a>',re.S)
SPAN=re.compile(r'<span>(.*?)</span>',re.S)
LINK=re.compile(r'\bhref="([^"]+)"')
HEADLINE=re.compile(r'<h1\b[^>]*>(.*?)</h1>',re.I|re.S)
CANONICAL=re.compile(r'<link rel="canonical" href="([^"]+)">')
OG_IMAGE=re.compile(r'<meta property="og:image" content="([^"]+)">')
SUBJECT=re.compile(r'<input\b[^>]*name="wantedClass"[^>]*value="([^"]*)"')
CONTENT_REQUIRED={
 "elem-tutor":("학교 영어","읽기","문장"),
 "mid-tutor":("내신","문법","독해"),
 "high-tutor":("내신","수능","독해"),
 "elem-conv":("회화","말하기","듣기"),
 "mid-conv":("수행평가","말하기"),
 "high-conv":("내신","발표"),
}
def clean(s):return re.sub(r'<[^>]+>','',s).strip()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--report",type=Path,required=True)
    ap.add_argument("--expected-generated",type=int,default=158571)
    ap.add_argument("--expected-regions",type=int,default=6060)
    args=ap.parse_args()
    root=args.root.resolve()
    regions=sorted(root.glob("*-elem-tutor.html"))
    report={"status":"RUNNING","generated_expected":args.expected_generated,
            "regions_expected":args.expected_regions,"regions":len(regions),
            "generated_found":0,"html_checked":0,"student_blocks_checked":0,
            "student_links_checked":0,"student_local_destinations_verified":0,
            "six_detailed_pages_checked":0,"missing_detailed_pages":0,
            "page_categories":dict(Counter()),"form_fields_checked":0,
            "canonical_checked":0,"og_metadata_checked":0,
            "nearby_same_course_links_checked":0,"errors_count":0,
            "error_samples":[],"noindex_status":"preserved (not promoted to index)",
            "source_run":38689660290,
            "source_sha":"a18b8901ecda7d37f65e35b15f03d579ec63c70f",
            "production_deployed":False,"draft_deployed":False,"form_submitted":False}
    errors=[]
    counts=Counter()
    def fail(page,reason,detail=""):
        report["errors_count"]+=1
        if len(errors)<100:errors.append({"file":page,"reason":reason,"detail":str(detail)[:240]})
    try:
        files=list(root.glob("*.html"))
        report["generated_found"]=len(files)-2
        if len(files)!=args.expected_generated+2:fail("(root)","wrong_generated_page_count",len(files)-2)
        if len(regions)!=args.expected_regions:fail("(root)","wrong_region_count",len(regions))
        paths={p.name for p in files}
        # Build a map of exact regional slugs to the display name in elementary tutor H1.
        dong={}
        for p in regions:
            text=p.read_text(encoding="utf-8")
            h=HEADLINE.search(text)
            if not h:
                fail(p.name,"missing_h1")
                continue
            full=clean(h.group(1))
            if not full.endswith("초등학생영어과외"):
                fail(p.name,"elementary_h1_is_not_tutoring",full)
                continue
            slug=p.name[:-len("-elem-tutor.html")]
            dong[slug]=full[:-len("초등학생영어과외")].strip()
        # Audit all actual student nav components in ALL 158573 HTML files.
        for index,p in enumerate(files):
            try:
                t=p.read_text(encoding="utf-8",errors="replace")
                report["html_checked"]+=1
                if t.count('property="og:image"')==1 and t.count('name="twitter:image"')==1:
                    report["og_metadata_checked"]+=1
                else:fail(p.name,"missing_or_duplicate_og")
                c=CANONICAL.search(t)
                if c:report["canonical_checked"]+=1
                if 'related-course-fallback' in t and NAV.search(t):
                    fail(p.name,"stale_generic_student_fallback")
                groups=NAV.findall(t)
                if not groups:continue
                if len(groups)!=1:
                    fail(p.name,"duplicate_student_group",len(groups))
                    continue
                report["student_blocks_checked"]+=1
                m=ANCHOR.findall(groups[0])
                if len(m)!=6:
                    fail(p.name,"not_six_course_cards",len(m))
                    continue
                # Find exact locality suffix by one of 26 generated-page intents.
                slug=None
                for candidate in COURSES:
                    if p.name.endswith("-"+candidate+".html"):
                        prefix=p.name[:-len("-"+candidate+".html")]
                        if prefix in dong:slug=prefix;break
                if slug is None:
                    for candidate in ("worker-english-conv-academy","beginner-english-conv",
                                      "english-conv-academy","toeic-academy","toeic-speaking-academy",
                                      "adult-english-conv-academy","opic-academy","ielts-academy",
                                      "duolingo-academy","toefl-academy","toeic-speaking",
                                      "jobseeker-conv","biz-business-conv","housewife-conv",
                                      "univ-conv","toeic","opic","ielts","toefl","duolingo"):
                        if p.name.endswith("-"+candidate+".html"):
                            prefix=p.name[:-len("-"+candidate+".html")]
                            if prefix in dong:slug=prefix;break
                if not slug:
                    fail(p.name,"student_group_not_regional_or_bad_slug")
                    continue
                place=dong[slug]
                for i,a in enumerate(m):
                    report["student_links_checked"]+=1
                    expect="/"+slug+"-"+COURSES[i]+".html"
                    href=LINK.search(a)
                    label=SPAN.search(a)
                    value=clean(label.group(1)) if label else ""
                    if value != place+" "+LABELS[i]:
                        fail(p.name,"wrong_grade_or_course_label",f"{i} {value}")
                    if not href or href.group(1)!=expect:
                        fail(p.name,"wrong_student_course_href",f"{i} {href.group(1) if href else '-'}")
                    if expect[1:] not in paths:
                        fail(p.name,"missing_student_course_destination",expect)
                    else:report["student_local_destinations_verified"]+=1
                if (index+1)%40000==0:
                    print("STUDENT_NAV_FULL_AUDIT_PROGRESS",index+1,len(files),flush=True)
            except Exception as exc:
                fail(p.name,"parse_exception",repr(exc))
        # Deep audit content and metadata on every 6060 x six course-specific detail pages.
        for index,(slug,place) in enumerate(dong.items()):
            for mode,label in zip(COURSES,LABELS):
                file=root/(slug+"-"+mode+".html")
                if not file.exists():
                    report["missing_detailed_pages"]+=1
                    fail(file.name,"six_course_detail_file_missing")
                    continue
                t=file.read_text(encoding="utf-8",errors="replace")
                head=HEADLINE.search(t)
                if not head or clean(head.group(1)) != place+" "+label:
                    fail(file.name,"landing_H1_mismatches_course")
                if f'<link rel="canonical" href="https://englishpt.kr/{file.name}">' not in t:
                    fail(file.name,"landing_canonical_mismatch")
                if f'name="wantedClass" value="{place} {label}"' not in t:
                    fail(file.name,"consultation_course_hidden_field_wrong")
                if not all('name="'+item+'"' in t for item in
                           ("name","phone","area","consent","form-name")):
                    fail(file.name,"missing_consultation_form_input")
                if '<meta name="robots" content="noindex,follow' not in t:
                    fail(file.name,"changed_indexing_status")
                if 'data-v235-hero-wrap=' not in t:
                    fail(file.name,"adaptive_mobile_H1_missing")
                # Four rewritten/new pages have fully specialized course content.
                if mode in ("elem-tutor","mid-tutor","high-tutor","elem-conv"):
                    for term in CONTENT_REQUIRED[mode]:
                        if term not in t:
                            fail(file.name,"missing_course_specific_content",term)
                if mode not in ("mid-conv","high-conv"):
                    if t.count('class="faq-item"')<3:
                        fail(file.name,"course_FAQ_too_shallow")
                counts[mode]+=1
                report["six_detailed_pages_checked"]+=1
                report["form_fields_checked"]+=1
            if (index+1)%1000==0:
                print("DEEP_SIX_COURSE_QA_PROGRESS",index+1,len(dong),flush=True)
        # New pages must lead to matching same-course pages in nearby neighborhoods.
        for slug,place in dong.items():
            for mode in ("mid-tutor","high-tutor","elem-conv"):
                file=root/(slug+"-"+mode+".html")
                t=file.read_text(encoding="utf-8",errors="replace")
                match=re.search(r'<section class="section nearby-localities">.*?</section>',t,re.S)
                if not match:
                    fail(file.name,"missing_nearby_localities")
                    continue
                found=re.findall(r'href="(/[^"]+\.html)"',match.group(0))
                if not found:fail(file.name,"nearby_same_course_links_absent")
                for href in found:
                    report["nearby_same_course_links_checked"]+=1
                    if not href.endswith("-"+mode+".html"):
                        fail(file.name,"nearby_course_wrong",href)
                    elif href[1:] not in paths:
                        fail(file.name,"nearby_target_missing",href)
        report["page_categories"]=dict(counts)
        required_nav=6060*26 if args.expected_regions==6060 else args.expected_regions*26
        if report["student_blocks_checked"]!=required_nav:
            fail("(root)","regional_nav_coverage",f"{report['student_blocks_checked']} vs {required_nav}")
        if report["six_detailed_pages_checked"]!=args.expected_regions*6:
            fail("(root)","six_detail_coverage",report["six_detailed_pages_checked"])
    except Exception as exc:
        fail("(runner)","audit_crashed",traceback.format_exc()[-1200:])
    finally:
        report["error_samples"]=errors
        report["status"]="PASS_V2351_ALL_158571_STUDENT_NAV_SEMANTIC_QA" if report["errors_count"]==0 else "FAIL_V2351_ALL_158571_STUDENT_NAV_SEMANTIC_QA"
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(report["status"],"all",report["generated_found"],"nav",report["student_blocks_checked"],
              "student_links",report["student_links_checked"],"landing",report["six_detailed_pages_checked"],
              "nearby",report["nearby_same_course_links_checked"],
              "errors",report["errors_count"],flush=True)
        for row in errors[:15]:print("::error::"+json.dumps(row,ensure_ascii=False),flush=True)
    return 0 if report["errors_count"]==0 else 1

if __name__=="__main__":sys.exit(main())
