#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v23.5.1: create REAL six-way student locality detail destinations.
Offline-only; never deploys, never submits forms, never changes Production.
Input: immutable 140391 generated-page v23.5 artifact.
Output: 158571 generated pages (when 6060 localities and 3 new courses each).
"""
import argparse
import hashlib
import html
import json
import re
import sys
import traceback
import zipfile
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

COURSES=("elem-tutor","mid-tutor","high-tutor","elem-conv","mid-conv","high-conv")
GRADE=("초등학생","중학생","고등학생")
ORIGINAL_INTENTS=(
  "elem-tutor","mid-conv","high-conv","univ-conv",
  "jobseeker-conv","biz-business-conv","housewife-conv",
  "toeic","toeic-speaking","opic","ielts","duolingo","toefl",
  "toeic-academy","toeic-speaking-academy","opic-academy",
  "ielts-academy","duolingo-academy","toefl-academy",
  "english-conv-academy","adult-english-conv-academy",
  "worker-english-conv-academy","beginner-english-conv",
)
ALL_LOCAL_INTENTS=ORIGINAL_INTENTS+("mid-tutor","high-tutor","elem-conv")

SERVICE={
    "elem-tutor":"초등학생영어과외","mid-tutor":"중학생영어과외",
    "high-tutor":"고등학생영어과외","elem-conv":"초등학생영어회화",
    "mid-conv":"중학생영어회화","high-conv":"고등학생영어회화",
}
OG={"elem-tutor":"elementary","elem-conv":"elementary",
    "mid-tutor":"middle","mid-conv":"middle",
    "high-tutor":"high","high-conv":"high"}
TITLE_SUFFIX={
    "elem-tutor":"학교영어·독해·기초문법 맞춤관리",
    "mid-tutor":"내신·문법·독해 1:1 맞춤지도",
    "high-tutor":"내신·수능 영어 1:1 맞춤지도",
    "elem-conv":"초등 말하기·듣기 자신감 키우기",
}
SPECS={
 "elem-tutor":{
   "kicker":"초등학생 영어과외 · 학교 영어",
   "headline":"교과서 문장을 읽고 이해하는 힘부터 차근차근 살펴봅니다",
   "lead":"단어를 외웠는데 문장 뜻을 설명하기 어렵거나, 읽기는 하지만 내용을 이해하기 힘든 경우를 구분해 확인합니다. 학교 진도와 현재 학습 습관을 함께 살펴 학생에게 맞는 과외 계획을 세웁니다.",
   "goal":"읽기·어휘·문장 구조를 스스로 이해하고 학교 영어 문제에 적용하기",
   "problems":[("단어만 외우고 잊어버려요","어휘의 뜻을 확인한 뒤 교과서 문장과 짧은 글에서 다시 찾아 쓰는 과정을 만듭니다."),
               ("문장을 읽어도 뜻을 모르겠어요","주어·동사부터 찾고 짧은 문장의 구조를 익힌 뒤, 뜻을 설명하는 단계로 연결합니다."),
               ("숙제를 혼자 시작하지 못해요","과제량을 무리하게 늘리지 않고 스스로 시작할 수 있는 작은 분량부터 확인합니다."),
               ("학교 진도가 어렵게 느껴져요","현재 단원과 어려웠던 기초 개념을 연결해 필요한 부분을 순서대로 보완합니다.")],
   "plan":[("1. 현재 읽기·이해 수준 확인","최근 교과서 문장과 과제에서 학생이 도움 없이 읽고 설명하는 범위를 확인합니다."),
           ("2. 필요한 기초부터 정리","파닉스·어휘·문장 구조 중 실제로 부족한 부분만 골라 학교 진도와 연결합니다."),
           ("3. 스스로 풀이·설명하기","모르는 문장은 왜 어려운지 표시하고, 배운 구조를 다른 문장에 적용합니다."),
           ("4. 오답·복습 계획 만들기","틀린 문장을 다시 읽고 설명하며, 다음 수업에서 기억하고 있는지 확인합니다.")],
   "sample":"교과서 지문을 읽고 주어와 동사를 표시한 뒤 학생이 의미를 설명해봅니다. 막힌 부분만 짧게 설명하고 다음 문장에서도 같은 방식으로 이해되는지 확인합니다. 읽기와 문제풀이의 결과를 함께 기록합니다.",
   "questions":[("학교 시험 대비와 기초 영어를 동시에 할 수 있나요?","가능합니다. 현재 단원을 기준으로 시험에 필요한 내용과 부족한 기초를 연결해 수업의 우선순위를 조정합니다."),
                ("영어를 거의 처음 시작하는 초등학생도 가능한가요?","현재 읽기 수준을 먼저 확인하고 짧은 낱말·문장부터 시작하는 방식으로 부담을 조절합니다."),
                ("회화가 아니라 과외에서 집중하는 내용은 무엇인가요?","읽기·어휘·기초문법·교과서 이해·문제풀이·복습을 중심으로 하며, 말하기는 이해 확인을 돕는 활동으로 활용할 수 있습니다.")],
   "avoid":["초등학생영어회화 학년별 수업 안내","회화만 계속"],
 },
 "mid-tutor":{
   "kicker":"중학생 영어과외 · 내신관리",
   "headline":"교과서 본문·문법·서술형을 학교 일정에 맞춰 관리합니다",
   "lead":"중학교 영어는 단어를 알아도 본문 해석과 문법 문제, 서술형 답안을 함께 준비하기 어려울 수 있습니다. 최근 시험지와 학교 진도를 확인하고, 실수를 반복하는 단원부터 개별 과외 순서를 정합니다.",
   "goal":"내신·수행평가·문법·독해를 학교 시험 범위와 함께 관리하기",
   "problems":[("교과서 본문이 길어져요","핵심 문장 구조를 표시하고 문단별 의미를 파악하는 방법을 연습합니다."),
               ("문법은 아는데 문제에 적용하지 못해요","규칙 설명과 예문을 연결하고, 틀린 문항과 비슷한 새 문제를 다시 풀어봅니다."),
               ("서술형 답안이 자꾸 틀려요","문장 순서·시제·철자·주어와 동사의 일치를 확인하는 기준을 익힙니다."),
               ("시험 직전에 범위가 밀려요","학교 일정에서 역산해 본문·문법·서술형·오답 복습 시간을 나눕니다.")],
   "plan":[("1. 학교 자료와 진도 파악","교과서·부교재·프린트·최근 시험에서 실제 출제 범위와 약점을 확인합니다."),
           ("2. 내신 필수 문장·문법 정리","단원별 핵심 어휘·문법을 정리하고 틀리기 쉬운 문장을 구분합니다."),
           ("3. 객관식과 서술형 적용","정답을 외우는 방식 대신 왜 선택했고 어떻게 작성했는지 설명하게 합니다."),
           ("4. 오답 원인별 재확인","어휘 부족·문법 적용·지문 이해·시간 부족으로 나눠 다음 평가 전에 다시 봅니다.")],
   "sample":"최근 서술형에서 시제를 틀렸다면 규칙부터 다시 외우기보다 틀린 문장을 분석하고, 다른 주어와 시간 표현을 넣은 문장을 새로 완성해봅니다. 다음에는 설명 없이도 같은 기준을 적용하는지 확인합니다.",
   "questions":[("중학교 영어 내신 대비는 언제부터 시작하나요?","학교별 시험 일정과 현재 단원에 따라 달라집니다. 최근 시험지와 수행평가 일정을 함께 확인해 먼저 준비할 범위를 정합니다."),
                ("문법과 독해 중 무엇을 먼저 해야 하나요?","문제를 틀린 원인과 시험 범위를 기준으로 결정합니다. 문법이 지문 해석을 막는 경우 두 영역을 연결해 공부할 수 있습니다."),
                ("중학생영어회화와 어떤 차이가 있나요?","과외는 학교 내신·교과서·문법·독해·서술형 풀이와 오답을 중심으로 하고, 회화는 듣고 말하기·발표·질문 대응을 중심으로 합니다.")],
 },
 "high-tutor":{
   "kicker":"고등학생 영어과외 · 내신·수능",
   "headline":"내신 범위와 수능 독해의 약점을 분리해 우선순위를 잡습니다",
   "lead":"고등학교 영어는 교과서·부교재·모의고사 지문의 난이도와 일정이 다릅니다. 학교 내신에서 잃는 점수와 수능형 독해에서 어려운 유형을 구분한 뒤, 현재 학년과 목표에 맞는 과외 계획을 세웁니다.",
   "goal":"고등 내신·수능 독해·어법·시간관리의 약점 보완",
   "problems":[("긴 지문을 읽다가 흐름을 놓쳐요","문단 역할과 논리 연결을 표시해 핵심 내용·빈칸·순서 판단의 근거를 찾습니다."),
               ("내신 범위가 너무 많아요","학교 프린트와 교과서 지문에서 우선 복습할 자료와 서술형 기준을 구분합니다."),
               ("모의고사 시간이 부족해요","유형별 소요 시간과 반복 오답을 확인하고 풀이 순서를 조정합니다."),
               ("어법과 어휘에서 자꾸 감점돼요","문맥 속 의미와 문장 구조를 연결해 오답 원인을 기록합니다.")],
   "plan":[("1. 내신·모의고사 결과 분석","점수만 보지 않고 틀린 지문의 길이, 유형, 시간 사용과 원인을 함께 확인합니다."),
           ("2. 시험 일정에 맞춘 범위 조정","학교 시험이 가까우면 교과서·부교재를 우선하고, 그 외 기간에는 수능형 독해 약점을 보완합니다."),
           ("3. 독해·어법의 근거 찾기","정답 위치보다 글의 흐름과 문장 구조로 이유를 설명해보는 연습을 합니다."),
           ("4. 오답 유형·시간 재점검","새 지문에서도 같은 실수가 반복되는지 확인하고 풀이 전략을 보완합니다.")],
   "sample":"모의고사 빈칸 문제에서 틀린 이유가 어휘인지 글의 전개인지 분리합니다. 문단 핵심을 요약한 뒤 빈칸 앞뒤의 논리 연결을 설명하게 하고, 새 지문에 적용되는지 확인합니다.",
   "questions":[("내신과 수능 영어를 동시에 준비할 수 있나요?","가능하지만 같은 비중으로 공부하기보다 학교 시험 일정과 현재 모의고사 약점에 따라 주별 우선순위를 달리합니다."),
                ("독해 속도가 느린 학생은 무엇부터 하나요?","모르는 단어 때문인지 문장 구조·논리 연결 때문인지 확인하고, 시간 제한을 늘리기 전에 정확한 독해 기준을 세웁니다."),
                ("고등학생영어회화와 어떤 차이가 있나요?","과외는 내신·수능·독해·어법·서술형 대비에 집중하고, 회화는 발표·면접·질문 대응 중심으로 구성합니다.")],
 },
 "elem-conv":{
   "kicker":"초등학생 영어회화 · 말하기",
   "headline":"짧은 질문에 직접 답하는 경험부터 영어 자신감을 키웁니다",
   "lead":"영어를 처음 말하는 초등학생에게는 어려운 문장을 외우는 것보다 짧은 인사·자기소개·일상 질문부터 편하게 답해보는 시간이 중요합니다. 듣고 이해하는 표현을 실제로 말할 수 있는지 현재 수준을 확인합니다.",
   "goal":"기초 듣기·발음·짧은 말하기·질문 대응을 부담 없이 시작하기",
   "problems":[("알아듣는데 입에서 영어가 안 나와요","아주 짧은 질문부터 듣고 한 단어·한 문장으로 답하며 점차 길이를 늘립니다."),
               ("문장을 통째로 외우기만 해요","이름·시간·장소를 바꾼 질문에도 배운 표현을 다시 활용해봅니다."),
               ("발음 실수를 두려워해요","정확도보다 의사소통을 시작하는 경험을 우선하고 자주 쓰는 소리를 짧게 고쳐봅니다."),
               ("듣기 속도가 빠르면 놓쳐요","자주 나오는 질문 표현을 구분하고 다시 듣거나 확인하는 문장을 배웁니다.")],
   "plan":[("1. 친숙한 주제로 말하기 시작","좋아하는 것·학교생활·가족 등 이미 아는 내용으로 짧은 질문을 연습합니다."),
           ("2. 짧은 답변에서 한 문장으로","한 단어 답변을 주어·동사가 있는 문장으로 바꿔봅니다."),
           ("3. 새로운 질문에도 대응","대화 상대나 순서를 바꿔도 간단히 응답할 수 있는지 확인합니다."),
           ("4. 집에서도 부담 없는 복습","수업에서 배운 문장을 짧게 녹음하거나 하루 한 번 말해볼 정도로 복습을 조절합니다.")],
   "sample":"선생님이 'What do you like?'라고 질문하면 좋아하는 음식을 한 단어로 답해봅니다. 이어서 'I like apples.'처럼 한 문장으로 확장하고, 과목이나 취미로 주제를 바꾸어 다시 말합니다.",
   "questions":[("영어를 처음 접하는 초등학생도 회화를 시작할 수 있나요?","인사·이름·좋아하는 것처럼 친숙한 주제부터 시작하면 됩니다. 수준과 자신감에 따라 질문의 길이를 조절합니다."),
                ("영어회화와 초등학생영어과외의 차이는 무엇인가요?","회화는 듣기·질문·응답·발음과 말하기 자신감이 중심입니다. 과외는 학교 영어의 읽기·어휘·문법·문장 이해·복습을 우선합니다."),
                ("집에서 복습은 얼마나 해야 하나요?","처음에는 수업에서 말한 한두 문장을 짧게 다시 말해보는 정도로 시작하고 학생이 부담 없이 이어갈 수 있는지 확인합니다.")],
 },
}
NAV_RE=re.compile(r'(<article class="related-group"><h3>학생 영어</h3><div class="related-course-links">)(.*?)(</div></article>)',re.S)
H1_RE=re.compile(r'<h1\b[^>]*>.*?</h1>',re.S|re.I)
DETAIL=re.compile(r'<section class="section intro-detail" id="detail">.*?</section>',re.S)
CONSULT=re.compile(r'<section\b(?=[^>]*\bid="consultation-preview")(?=[^>]*class="[^"]*consult)[^>]*>.*?</section>',re.S)
RELATED=re.compile(r'<section class="section related local-navigation">.*?</section>',re.S)
NEARBY=re.compile(r'<section class="section nearby-localities">.*?</section>',re.S)
NEARBY_A=re.compile(r'<a\\b[^>]*>.*?</a>',re.S)
TRUST=re.compile(r'<div class="trust">.*?</div></div>',re.S)
MARKER=re.compile(r'<meta\b[^>]*>',re.I)
CANONICAL=re.compile(r'<link rel="canonical" href="[^"]+">')
IMG_SRC=re.compile(r'<link rel="image_src" href="[^"]+">')
SCHEMA=re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)',re.S)
NAME_RE=re.compile(r'(<input\b[^>]*\bname="wantedClass"[^>]*\bvalue=")[^"]*(")')
HERO_CLASS_RE=re.compile(r'\sdata-v235-hero-wrap="[^"]*"')

def e(x):return html.escape(str(x),quote=True)

def hero_mode(text):
    # same v23.5 sizing rule; preserve wording and calculate only the class.
    normalized=text.replace(" ","")
    words=re.findall(r'[가-힣A-Za-z0-9]+',text)
    longest=max((len(w) for w in words),default=0)
    return 'xlong' if longest>=13 or len(normalized)>=26 else 'long' if longest>=9 or len(normalized)>=18 else 'regular'

def nav_html(slug,dong):
    links=[]
    for intent in COURSES:
        title=e(dong+" "+SERVICE[intent])
        url="/"+e(slug)+"-"+intent+".html"
        kind="related-course-tutor" if intent.endswith("tutor") else "related-course-conversation"
        links.append(f'<a class="{kind}" href="{url}"><span>{title}</span><b>→</b></a>')
    return "".join(links)

def apply_nav(s,slug,dong):
    nav=nav_html(slug,dong)
    new,n=NAV_RE.subn(lambda m:m.group(1)+nav+m.group(3),s)
    if n!=1:raise ValueError("unexpected student group count "+str(n))
    return new

def extract_one(regex,s,label):
    m=regex.search(s)
    if not m:raise ValueError("missing html component "+label)
    return m.group(0)

def page_location(elem):
    m=H1_RE.search(elem)
    if not m:raise ValueError("elementary H1 not found")
    h=html.unescape(re.sub(r'<[^>]+>','',m.group(0))).strip()
    if not h.endswith("초등학생영어과외"):
        raise ValueError("elementary tutor H1 label mismatch: "+h)
    return h[:-len("초등학생영어과외")].strip()

def grade_blocks(loc,c):
    spec=SPECS[c]
    cards="".join(f'<article class="card"><b>{e(h)}</b><p>{e(desc)}</p></article>' for h,desc in spec["problems"])
    steps="".join(f'<article class="context-block"><h3>{e(h)}</h3><p>{e(desc)}</p></article>' for h,desc in spec["plan"])
    faqs="".join(f'<details class="faq-item"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q,a in spec["questions"])
    return (
       f'<section class="section intro-detail" id="detail"><div class="wrap"><div class="intro-grid">'
       f'<div class="intro-copy"><p class="kicker">{e(spec["kicker"])}</p><h2>{e(spec["headline"])}</h2>'
       f'<p>{e(spec["lead"])}</p><p>{e(loc)}에서 상담할 때에는 현재 학교 자료나 평소 어려워한 내용을 '
       '하나만 알려주셔도 시작점을 구체적으로 정하는 데 도움이 됩니다.</p></div>'
       f'<aside class="snapshot"><h3>처음 상담에서 확인하는 것</h3>'
       f'<div class="snaprow"><small>학습목표</small><strong>{e(spec["goal"])}</strong></div>'
       '<div class="snaprow"><small>현재</small><strong>최근 학교 자료·공부 습관·혼자 할 수 있는 범위</strong></div>'
       '<div class="snaprow"><small>진도</small><strong>학생 수준과 목표에 따른 1:1 개별 계획</strong></div>'
       '</aside></div></div></section>'
       '<div class="trust"><div class="wrap trust-in">'
       '<div>✓ 현재 수준에 맞춘 수업 시작점</div>'
       '<div>✓ 한국어 설명·피드백 가능</div>'
       '<div>✓ 학년별 공부 방법과 복습 계획</div></div></div>'
       f'<section class="section management"><div class="wrap manage-layout">'
       '<div class="manage-copy"><p class="kicker">맞춤 학습관리</p>'
       f'<h2>{e(SERVICE[c])} 수업은 학생의 목표와 학교 일정에 맞춰 진행합니다</h2>'
       f'<p>{e(spec["lead"])}</p><ul class="manage-focus">'
       f'<li>현재 어려운 단원·표현을 확인한 뒤 시작점을 정합니다.</li>'
       f'<li>{e(spec["goal"])}</li>'
       '<li>수업 뒤에는 다음에 다시 확인할 내용과 복습 기준을 남깁니다.</li></ul></div>'
       '<div class="manage-aftercare"><h3>수업 후 복습과 피드백</h3>'
       '<p>무조건 숙제를 많이 내기보다 수업에서 확인한 부분을 혼자 다시 할 수 있는지 살펴봅니다.</p>'
       '<ul class="manage-focus"><li>짧고 구체적인 복습 내용</li><li>반복되는 실수·질문 기록</li>'
       '<li>다음 수업에서 새 자료로 확인</li></ul></div></div></section>'
       '<section class="section soft"><div class="wrap"><p class="kicker">학년별 어려운 부분</p>'
       f'<h2>{e(loc)} {e(SERVICE[c])}에서 먼저 확인할 네 가지</h2>'
       f'<div class="grid4">{cards}</div></div></section>'
       '<section class="section mass-context"><div class="wrap narrow">'
       '<p class="kicker">1:1 수업 진행</p>'
       '<h2>확인부터 복습까지, 단계별로 어떻게 공부하나요?</h2>'
       f'{steps}</div></section>'
       '<section class="section"><div class="wrap narrow"><p class="kicker">수업에서 확인하는 예시</p>'
       f'<h2>{e(SERVICE[c])}에서는 이런 식으로 학습을 이어갑니다</h2>'
       f'<p>{e(spec["sample"])}</p>'
       '<p>위 내용은 실제 수업을 이해하기 위한 예시이며 특정 학생의 후기나 성과를 의미하지 않습니다. '
       '학생의 현재 수준과 학교 일정에 따라 활동과 복습량은 달라질 수 있습니다.</p></div></section>'
       '<section class="section soft"><div class="wrap narrow"><p class="kicker">학부모 질문</p>'
       f'<h2>{e(SERVICE[c])} 상담 전에 자주 궁금해하는 내용</h2>'
       f'{faqs}</div></section>'
       '<section class="section"><div class="wrap narrow"><p class="kicker">수업 선택 기준</p>'
       '<h2>과외와 회화를 구분하고 현재 필요한 과정부터 확인하세요</h2>'
       f'<p>{e(loc)}에서 영어 수업을 비교한다면 먼저 학교 성적·독해·문법이 어려운지, '
       '직접 말하고 듣는 일이 어려운지 구분하면 수업 방향이 명확해집니다. '
       '과외와 회화가 모두 필요하더라도 학생의 현재 목표를 기준으로 우선순위를 조정할 수 있습니다.</p>'
       '<p>일정·과목·방식은 상담에서 함께 확인할 수 있으며, 신청만으로 수업이 확정되지는 않습니다.</p>'
       '</div></section>'
    )


def filter_nonexistent_nearby(s, valid_filenames):
    """Hide broken links to locality pages that are not part of this release."""
    removed=[0]
    removed_sections=[0]
    def section_replace(m):
        content=m.group(0)
        def link_replace(a):
            href_match=re.search(r'\bhref="([^"]+)"',a.group(0))
            if not href_match:return a.group(0)
            u=urlsplit(href_match.group(1))
            if u.scheme or u.netloc or not u.path.startswith("/") or not u.path.endswith(".html"):
                return a.group(0)
            if u.path.lstrip("/") not in valid_filenames:
                removed[0]+=1
                return ""
            return a.group(0)
        cleaned=NEARBY_A.sub(link_replace,content)
        if not NEARBY_A.search(cleaned):
            removed_sections[0]+=1
            return ""
        return cleaned
    return NEARBY.sub(section_replace,s),removed[0],removed_sections[0]

def make_page(template,slug,dong,course):
    spec=SPECS[course]
    title=f"{dong} {SERVICE[course]}"
    page_title=f"{title} | {TITLE_SUFFIX[course]}"
    description=f"{title} 안내. {spec['lead'][:118]} 수업 방식과 학년별 상담을 확인하세요."
    canonical=f"https://englishpt.kr/{slug}-{course}.html"
    og=f"https://englishpt.kr/assets/images/og-pages/{OG[course]}.png"
    parts=re.search(r'^(.*?<main>)(.*?)(</main>.*)$',template,re.S)
    if not parts:raise ValueError("template has no <main>")
    main=parts.group(2)
    breadcrumb=f'<div class="breadcrumb wrap" aria-label="현재 위치"><a href="/englishpt.html">잉글리시PT</a><span aria-hidden="true">/</span><strong>{e(title)}</strong></div>'
    hero=(f'<section class="hero simple-hero" data-hero-copy="audience-v2"><div class="wrap simple-hero-inner">'
          f'<p class="eyebrow">ENGLISH PT · {e(spec["kicker"])}</p>'
          f'<h1 data-v235-hero-wrap="{hero_mode(title)}">{e(title)}</h1>'
          f'<p class="hero-subline">{e(spec["headline"])}</p>'
          f'<p class="hero-copy">{e(spec["lead"][:120])}</p>'
          '<div class="hero-actions"><a class="btn primary" href="#consultation-preview">우리 아이 영어 상담하기</a>'
          '<a class="btn ghost" href="#detail">수업 안내 보기</a></div></div></section>')
    hero_next=('<section class="section hero-next-step"><div class="wrap">'
      '<p class="kicker">첫 상담에서 살펴보는 기준</p><h2>우리 아이에게 필요한 공부부터 확인합니다</h2>'
      '<div class="hero-next-grid"><article><strong>현재 수준</strong><p>학생이 혼자 할 수 있는 부분과 어려운 부분을 구분합니다.</p></article>'
      '<article><strong>학교 일정</strong><p>학년·학교 진도·다가오는 평가 일정을 확인합니다.</p></article>'
      '<article><strong>수업 방식</strong><p>학생에게 맞는 수업 시간과 복습 방법을 함께 정합니다.</p></article>'
      '</div></div></section>')
    related=extract_one(RELATED,main,"related section")
    nearby_match=NEARBY.search(main)
    nearby=nearby_match.group(0) if nearby_match else ""
    if course!="elem-tutor" and nearby:
        # "Same course in other neighbourhoods" must follow the NEW grade/course.
        # Otherwise a new middle tutor page misleadingly opens elementary tutoring.
        nearby=re.sub(r'(href="/[^"]+)-elem-tutor\.html(")',
                      lambda m:m.group(1)+"-"+course+".html"+m.group(2),nearby)
        nearby=nearby.replace("<span>초등학생영어과외</span>",
                              "<span>"+e(SERVICE[course])+"</span>")
    consult=extract_one(CONSULT,main,"consultation section")
    # Change only values in cloned form; existing Netlify form / consent remain intact.
    old_val="사직동 초등학생영어과외"
    form_repl=re.compile(r'(<input\b[^>]*name="wantedClass"[^>]*value=")[^"]*(")')
    consult,n=form_repl.subn(lambda m:m.group(1)+e(title)+m.group(2),consult,count=1)
    if n!=1:raise ValueError("consultation wantedClass input missing")
    # Replace opening consultation subcopy to remove elementary-only context, if any
    consult=consult.replace(dong+" 초등학생영어과외",title)
    final=(f'<section class="final"><div class="wrap"><h2>{e(title)}, 현재 학습목표부터 확인해보세요.</h2>'
           '<a class="btn light" href="tel:+821050068027">전화 010-5006-8027</a></div></section>')
    body=breadcrumb+hero+hero_next+grade_blocks(dong,course)+related+nearby+consult+final
    html_page=parts.group(1)+body+parts.group(3)
    html_page,n=re.subn(r'<title>.*?</title>',lambda _:f'<title>{e(page_title)}</title>',html_page,count=1,flags=re.S)
    if n!=1:raise ValueError("missing title")
    for typ,key,value in (("name","description",description),("property","og:description",description),
                          ("property","og:title",page_title),("property","og:url",canonical),
                          ("property","og:image",og),("property","og:image:secure_url",og),
                          ("property","og:image:alt",page_title),("name","twitter:image",og)):
        pattern=re.compile(r'<meta '+typ+'="'+re.escape(key)+r'" content="[^"]*">')
        html_page,n=pattern.subn(lambda _:f'<meta {typ}="{key}" content="{e(value)}">',html_page,count=1)
        if n!=1:raise ValueError("missing metadata "+key)
    html_page,n=CANONICAL.subn('<link rel="canonical" href="'+canonical+'">',html_page,count=1)
    if n!=1:raise ValueError("missing canonical")
    html_page,n=IMG_SRC.subn('<link rel="image_src" href="'+og+'">',html_page,count=1)
    if n!=1:raise ValueError("missing image_src")
    # Render structured data from existing real source without stale primary course identities.
    m=SCHEMA.search(html_page)
    if not m:raise ValueError("structured schema missing")
    data=json.loads(m.group(2))
    old_canonical=f"https://englishpt.kr/{slug}-elem-tutor.html"
    for node in data.get("@graph",[]):
        kind=node.get("@type")
        if kind=="WebPage":
            node.update({"@id":canonical+"#webpage","url":canonical,"name":page_title,
                         "description":description,"about":{"@id":canonical+"#service"},
                         "mainEntity":{"@id":canonical+"#service"},"image":og,"thumbnailUrl":og})
        elif kind=="Service":
            node.update({"@id":canonical+"#service","name":title,
                         "url":canonical,"description":description,"serviceType":
                         "1:1 맞춤 영어과외" if course.endswith("tutor") else "초등 영어회화 1:1 수업",
                         "audience":{"@type":"Audience","audienceType":GRADE[0] if course.startswith("elem") else GRADE[1] if course.startswith("mid") else GRADE[2]},
                         "image":og,"thumbnailUrl":og})
        elif kind=="BreadcrumbList":
            arr=node.get("itemListElement",[])
            if len(arr)>=2:arr[-1].update({"name":title,"item":canonical})
    schema='<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False,separators=(",",":"))+'</script>'
    html_page=html_page[:m.start()]+schema+html_page[m.end():]
    html_page=html_page.replace('<body class="theme-elem intent-audience"',
        '<body class="'+("theme-elem" if course.startswith("elem") else "theme-mid" if course.startswith("mid") else "theme-high")+' intent-audience"',1)
    if SERVICE["elem-tutor"] in html_page and course!="elem-tutor":
        # Old elementary label in footer or links is fine; main new copy has separate text.
        pass
    return html_page

def get_links(blob):
    return re.findall(r'href="([^"]+)"',blob)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",required=True,type=Path)
    ap.add_argument("--report",required=True,type=Path)
    ap.add_argument("--expected-source",type=int,default=140391)
    ap.add_argument("--expected-locations",type=int,default=6060)
    ap.add_argument("--sample-zip",type=Path)
    ap.add_argument("--pilot",action="store_true",help="Small fixture without hub index and 23 intent coverage")
    args=ap.parse_args()
    root=args.root.resolve()
    page_count=len(list(root.glob("*.html")))
    elem_candidates=sorted(root.glob("*-elem-tutor.html"))
    # One or more hub/station pages may share the suffix but do NOT belong
    # to the 6060 full (23-intent) locality clusters.
    local_pages=[
        p for p in elem_candidates
        if (root/(p.name[:-len("-elem-tutor.html")]+"-worker-english-conv-academy.html")).is_file()
        and (root/(p.name[:-len("-elem-tutor.html")]+"-mid-conv.html")).is_file()
        and (root/(p.name[:-len("-elem-tutor.html")]+"-high-conv.html")).is_file()
    ]
    local_set=set(local_pages)
    excluded_elem_tutor=[p.name for p in elem_candidates if p not in local_set]
    expected_final=args.expected_source+args.expected_locations*3
    result={"status":"STARTED","source_expected":args.expected_source,
       "source_generated_count":page_count-2,"location_expected":args.expected_locations,
       "location_detected":len(local_pages),
       "excluded_non_locality_elem_tutor":excluded_elem_tutor,
       "new_expected":args.expected_locations*3,
       "final_generated_expected":expected_final,"new_pages_created":0,
       "elementary_tutor_rewritten":0,"regional_pages_nav_updated":0,
       "nav_links_checked":0,"new_page_labels":dict(Counter()),"naeidong_slugs":[],
       "nearby_dead_links_removed":0,"empty_nearby_sections_removed":0,
       "errors":[],"error_count":0,"source_run":38689660290,
       "source_sha":"a18b8901ecda7d37f65e35b15f03d579ec63c70f",
       "v235_source_run":38843408620,"production_deployed":False,
       "preview_deployed":False,"form_submitted":False}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    sample={}
    slugs={}
    errors=[]
    try:
        expected_html=args.expected_source if args.pilot else args.expected_source+2
        if page_count!=expected_html:raise ValueError("source page count "+str(page_count))
        if len(local_pages)!=args.expected_locations:raise ValueError("locality count "+str(len(local_pages)))
        for i,p in enumerate(local_pages):
            try:
                slug=p.name[:-len("-elem-tutor.html")]
                raw=p.read_text(encoding="utf-8")
                dong=page_location(raw)
                if slug in slugs:raise ValueError("duplicate slug "+slug)
                slugs[slug]=dong
                if dong=="내이동":result["naeidong_slugs"].append(slug)
                for existing in ("mid-conv","high-conv"):
                    if not (root/(slug+"-"+existing+".html")).is_file():
                        raise ValueError("missing existing "+existing)
                for course in ("elem-tutor","mid-tutor","high-tutor","elem-conv"):
                    dest=root/(slug+"-"+course+".html")
                    if course!="elem-tutor" and dest.exists():
                        raise ValueError("new course collides with existing page: "+dest.name)
                    content=make_page(raw,slug,dong,course)
                    if course!="elem-tutor":
                        dest.write_text(content,encoding="utf-8")
                        result["new_pages_created"]+=1
                    else:
                        dest.write_text(content,encoding="utf-8")
                        result["elementary_tutor_rewritten"]+=1
                    if dong in ("내이동","사직동") and course in COURSES:
                        sample[dest.name]=content
                if (i+1)%1000==0:
                    print("NEW_STUDENT_DETAILS_PROGRESS",i+1,"/",len(local_pages),
                          "created",result["new_pages_created"],flush=True)
            except Exception as exc:
                result["error_count"]+=1
                if len(errors)<80:errors.append({"file":p.name,"stage":"generate","error":str(exc)})
                # Fail quickly; an incomplete locality release must never be packaged.
                raise
        # Patch ALL 23 original locality intentions + all 3 newly-created intentions.
        # Links to nonexistent nearby locality pages are pruned, never left as 404s.
        valid_filenames={p.name for p in root.glob("*.html")}
        for i,(slug,dong) in enumerate(slugs.items()):
            nav=nav_html(slug,dong)
            for intent in ALL_LOCAL_INTENTS:
                page=root/(slug+"-"+intent+".html")
                if not page.is_file():
                    if args.pilot:continue
                    raise ValueError("missing expected locality intent: "+page.name)
                original=page.read_text(encoding="utf-8")
                updated,n=NAV_RE.subn(lambda m:m.group(1)+nav+m.group(3),original)
                if not args.pilot:
                    updated,dead,empty=filter_nonexistent_nearby(updated,valid_filenames)
                    result["nearby_dead_links_removed"]+=dead
                    result["empty_nearby_sections_removed"]+=empty
                if n==1:
                    if updated!=original:page.write_text(updated,encoding="utf-8")
                    result["regional_pages_nav_updated"]+=1
                    result["nav_links_checked"]+=6
                    if dong in ("내이동","사직동") and (
                        intent in COURSES or intent=="worker-english-conv-academy"
                    ):
                        sample[page.name]=updated
                elif n>1:
                    raise ValueError("multiple student nav groups: "+page.name)
                elif n==0 and page.name.endswith(tuple("-"+c+".html" for c in COURSES)):
                    raise ValueError("student landing missing nav: "+page.name)
            if (i+1)%1000==0:
                print("ALL_LOCALITY_STUDENT_NAV_PROGRESS",i+1,"/",len(slugs),flush=True)
        # UI should not pretend a shared generic student guide is a locality detail.
        # Keep the shared student-english hub as a separately accessible information page.
        final_pages=len(list(root.glob("*.html")))
        expected_full_html=expected_final if args.pilot else expected_final+2
        if final_pages!=expected_full_html:
            raise ValueError(f"unexpected final html total: {final_pages}; expected {expected_full_html}")
        if (not args.pilot and result["regional_pages_nav_updated"]!=args.expected_locations*26):
            raise ValueError("student nav group coverage not 26 per locality")
        if args.pilot and result["regional_pages_nav_updated"]<7:
            raise ValueError("pilot requires at least seven student navigation groups")
        for slug,dong in slugs.items():
            for course in COURSES:
                if not (root/(slug+"-"+course+".html")).is_file():
                    raise ValueError("missing six detail pages: "+slug+"-"+course)
        result["final_generated_found"]=final_pages-(0 if args.pilot else 2)
        result["samples"]=sorted(sample)
        if args.sample_zip:
            args.sample_zip.parent.mkdir(parents=True,exist_ok=True)
            with zipfile.ZipFile(args.sample_zip,"w",zipfile.ZIP_DEFLATED) as z:
                for name,content in sample.items():z.writestr(name,content)
                for item in ("pilot.css","pilot.js","assets/styles.css","assets/site.js"):
                    f=root/item
                    if f.is_file():z.write(f,item)
        result["status"]="PASS_ALL_LOCAL_STUDENT_SIX_DETAILS"
    except Exception as exc:
        result["status"]="FAIL_ALL_LOCAL_STUDENT_SIX_DETAILS"
        result["error_count"]+=1
        if len(errors)<80:errors.append({"stage":"fatal","error":str(exc),"trace":traceback.format_exc()[-1250:]})
    finally:
        result["errors"]=errors
        args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(result["status"],"localities",len(slugs),"new",result["new_pages_created"],
              "regional_nav_pages",result["regional_pages_nav_updated"],
              "links",result["nav_links_checked"],"errors",result["error_count"],flush=True)
        for error in errors[:6]:print("::error::"+json.dumps(error,ensure_ascii=False),flush=True)
    return 0 if result["status"].startswith("PASS") else 1

if __name__=="__main__":sys.exit(main())
