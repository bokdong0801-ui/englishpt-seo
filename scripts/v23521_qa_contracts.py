#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One tested DOM/HTML contract for all future EnglishPT tutor page QAs.

Deliberately tolerant to attribute ordering, quote style, Netlify Pretty URLs
and HTML minification, but strict about all six courses and locality identity.
No network access and never submits any form.
"""
from html.parser import HTMLParser
from urllib.parse import urlsplit

COURSES=("elem-tutor","mid-tutor","high-tutor","elem-conv","mid-conv","high-conv")
TUTOR_CLASS="related-course-tutor"
CONV_CLASS="related-course-conversation"

class _StudentCards(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()!="a":return
        a=dict(attrs)
        classes=set((a.get("class") or "").split())
        matched=classes.intersection((TUTOR_CLASS,CONV_CLASS))
        if matched:
            self.links.append({"href":a.get("href") or "","category":next(iter(matched))})

def parse_regional_student_links(html_source,slug):
    """Return {course_mode: normalized href}; raise on missing, wrong, duplicate."""
    if not slug or "/" in slug or "\\" in slug:
        raise ValueError("Unsafe/empty regional identifier")
    p=_StudentCards()
    p.feed(html_source)
    if len(p.links)!=len(COURSES):
        raise ValueError("Expected exactly 6 student course cards; got "+str(p.links))
    found={}
    for item in p.links:
        href=item["href"]
        url=urlsplit(href)
        if url.scheme or url.netloc or url.query or url.fragment:
            raise ValueError("Expected internal same-region URL, got "+href)
        path=url.path.rstrip("/")
        if path.endswith(".html"):path=path[:-5]
        prefix="/"+slug+"-"
        if not path.startswith(prefix):
            raise ValueError("Student link has wrong locality: "+href)
        course=path[len(prefix):]
        if course not in COURSES:
            raise ValueError("Unknown regional student course: "+href)
        expected_class=TUTOR_CLASS if course.endswith("tutor") else CONV_CLASS
        if item["category"]!=expected_class:
            raise ValueError("Course/card class mismatch: "+href)
        if course in found:
            raise ValueError("Duplicate course link for "+course)
        found[course]=href
    if tuple(sorted(found))!=tuple(sorted(COURSES)):
        raise ValueError("Missing student courses: "+str(set(COURSES)-set(found)))
    return found

class _FormContent(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.forms=[]
        self.current=None
        self.in_button=False
        self.button_parts=[]
        self.form_depth=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="form":
            self.current={"attrs":a,"inputs":{},"buttons":[]}
            self.forms.append(self.current)
            self.form_depth+=1
        elif self.current is not None:
            if tag=="input" and a.get("name"):
                self.current["inputs"][a["name"]]=a.get("value","")
            elif tag=="button":
                self.in_button=True
                self.button_parts=[]
    def handle_data(self,data):
        if self.in_button:self.button_parts.append(data)
    def handle_endtag(self,tag):
        if tag=="button" and self.in_button and self.current is not None:
            self.current["buttons"].append("".join(self.button_parts).strip())
            self.in_button=False
        elif tag=="form" and self.form_depth:
            self.form_depth-=1
            if self.form_depth==0:self.current=None

def verify_tutoring_form_copy(html_source):
    """Validate visible submit and hidden subject/requestType separately."""
    parser=_FormContent()
    parser.feed(html_source)
    forms=[f for f in parser.forms if f["attrs"].get("name")=="englishpt-consultation"]
    if len(forms)!=1:
        raise ValueError("Expected exactly one Netlify consultation form")
    f=forms[0]
    fields=f["inputs"]
    if fields.get("requestType")!="영어과외 상담 신청":
        raise ValueError("Hidden requestType no longer matches tutoring consultation")
    if "영어과외 상담 신청" not in fields.get("subject",""):
        raise ValueError("Hidden subject no longer matches tutoring consultation")
    if len([s for s in f["buttons"] if "영어과외 상담 신청" in s])!=1:
        raise ValueError("Visible tutor submit CTA missing or duplicated")
    return {"requestType":fields["requestType"],"subject":fields["subject"],
            "visible_submit_text":[s for s in f["buttons"] if "영어과외 상담 신청" in s][0]}
