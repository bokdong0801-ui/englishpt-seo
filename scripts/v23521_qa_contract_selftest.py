#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-fast regression suite for tutor QA itself BEFORE any expensive upload.

Uses six actual approved v23.5.2.1 HTML files and synthetic Netlify-style
attribute serialization (single/double/unquoted, mixed ordering, Pretty URLs).
Validates click-loop AST structure to avoid skipping a whole district.
"""
import ast
import argparse
import re
import sys
from html import escape
from pathlib import Path
from v23521_qa_contracts import parse_regional_student_links,verify_tutoring_form_copy,COURSES

SLUGS=("gyeongnam-milyang-naeidong","seoul-jongno-sajikdong")
MODES=("elem-tutor","mid-tutor","high-tutor")

def check(condition,msg):
    if not condition:raise AssertionError(msg)

def load_real_html(site_root):
    inspected=0
    for slug in SLUGS:
        for mode in MODES:
            p=site_root/(slug+"-"+mode+".html")
            check(p.is_file(),"Missing approved frozen sample: "+p.name)
            source=p.read_text("utf8")
            links=parse_regional_student_links(source,slug)
            check(len(links)==6,"Fewer than 6 regional student links: "+p.name)
            f=verify_tutoring_form_copy(source)
            check(f["visible_submit_text"].startswith("영어과외 상담 신청"),
                  "Wrong visible CTA in frozen source")
            inspected+=1
    check(inspected==6,"Did not inspect six real frozen localities")
    print("QA_CONTRACT_REAL_6_TUTOR_HTML_PASS",inspected,flush=True)

def synthetic_html(slug,style):
    parts=[]
    for i,course in enumerate(COURSES):
        classname="related-course-tutor" if course.endswith("tutor") else "related-course-conversation"
        url="/"+slug+"-"+course+(".html" if i%2==0 else "")
        if style=="single":
            parts.append("<a href='"+url+"' class='"+classname+" other'><span>student</span></a>")
        elif style=="unquoted":
            parts.append("<a class="+classname+" href="+url+"><span>student</span></a>")
        else:
            parts.append('<a href="'+url+'" data-test="1" class="other '+classname+'"><span>student</span></a>')
    return '<article class="related-group">'+''.join(parts)+'</article>'

def test_minified_html():
    for style in ("single","unquoted","double"):
        fragment=synthetic_html(SLUGS[0],style)
        links=parse_regional_student_links(fragment,SLUGS[0])
        check(len(links)==6,"Failed parser tolerance: "+style)
        try:
            parse_regional_student_links(fragment,SLUGS[1])
        except ValueError:pass
        else:raise AssertionError("Wrong regional links passed "+style)
    base=synthetic_html(SLUGS[0],"unquoted")
    try:parse_regional_student_links(base+base,SLUGS[0])
    except ValueError:pass
    else:raise AssertionError("Duplicate regional links should not pass")
    print("QA_CONTRACT_NETLIFY_SERIALIZATION_AND_NEGATIVE_TESTS_PASS",flush=True)

def test_form_fields():
    fragment="""<form data-netlify='true' name="englishpt-consultation">
<input type=hidden value="ENGLISH PT 영어과외 상담 신청" name=subject>
<input name='requestType' type=hidden value="영어과외 상담 신청">
<button type=submit class='submit-lead'>영어과외 상담 신청 →</button></form>"""
    data=verify_tutoring_form_copy(fragment)
    check(data["requestType"]=="영어과외 상담 신청","Incorrect semantic requestType")
    bad=fragment.replace("<button type=submit class='submit-lead'>영어과외 상담 신청 →</button>",
                         "<button type=submit>체험수업 신청 →</button>")
    try:verify_tutoring_form_copy(bad)
    except ValueError:pass
    else:raise AssertionError("Stale visible trial CTA incorrectly passed")
    print("QA_CONTRACT_VISIBLE_SUBMIT_AND_HIDDEN_FORM_FIELDS_PASS",flush=True)

def test_click_loop_structure(script):
    tree=ast.parse(script.read_text("utf8"))
    fn=next((x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="clicks_phase"),None)
    check(fn is not None,"clicks_phase missing")
    area_loops=[x for x in ast.walk(fn) if isinstance(x,ast.For) and
                isinstance(x.target,ast.Name) and x.target.id=="slug"]
    check(len(area_loops)==1,"Expected one primary locality loop")
    area_loop=area_loops[0]
    sub_loops=[x for x in area_loop.body if isinstance(x,ast.For)]
    has_navigation=any("LINKS.items" in ast.unparse(x.iter) for x in sub_loops)
    has_ctas=any("GRADES.items" in ast.unparse(x.iter) for x in sub_loops)
    check(has_navigation and has_ctas,
          "Navigation and consultation CTA loops must BOTH be inside locality loop")
    code=script.read_text("utf8")
    check("len(nav)==24 and len(ctas)==24" in code,
          "2 districts x 3 grades x 2 CTA = 12? Incorrect: each CTA pair counts 24; never skip one district")
    check("page.locator('#consultation-preview').inner_text()" not in code,
          "Never look for hidden requestType within visible form text")
    print("QA_CONTRACT_BOTH_DISTRICTS_24_REAL_CTA_CHECKS_AST_PASS",flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--site-root",type=Path,required=True)
    opts=p.parse_args()
    test_minified_html()
    test_form_fields()
    load_real_html(opts.site_root)
    test_click_loop_structure(Path(__file__).with_name("v23521_draft_live_readonly_qa.py"))
    print("PASS_V23521_QA_SCRIPT_ITSELF_REGRESSION_TESTED_BEFORE_DEPLOY",flush=True)

if __name__=="__main__":main()
