#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render ENGLISH PT nationwide station hubs and station × course pages."""
from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://englishpt.kr"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


clean = load_module("stage9_clean_station_base", ROOT / "scripts" / "stage9-clean-mass-renderer.py")
svc, ex = clean.gold_modules()

ALL_INTENTS = (
    clean.SERVICE_ORDER
    + clean.EXAM_ORDER
    + clean.ACADEMY_ORDER
    + clean.CONV_DERIVED_ORDER
)

SERVICE_LABELS = {
    **{intent: svc.PROFILES[intent]["service_h1"] for intent in clean.SERVICE_ORDER},
    **{intent: next(v["service"] for v in ex.EXAMS.values() if v["intent"] == intent) for intent in clean.EXAM_ORDER},
    **clean.ACADEMY_SERVICE,
    **clean.CONV_DERIVED_SERVICE,
}

GROUPS = [
    ("학생 영어", ["elem-tutor", "mid-conv", "high-conv"]),
    ("회화·목적별 영어", [
        "english-conv-academy", "adult-english-conv-academy",
        "worker-english-conv-academy", "beginner-english-conv",
        "univ-conv", "jobseeker-conv", "biz-business-conv", "housewife-conv",
    ]),
    ("시험 영어", ["toeic", "toeic-speaking", "opic", "ielts", "toefl", "duolingo"]),
    ("학원형·1:1 비교", [
        "toeic-academy", "toeic-speaking-academy", "opic-academy",
        "ielts-academy", "toefl-academy", "duolingo-academy",
    ]),
]

HUB_INTRO_VARIANTS = [
    (
        "영어를 배우고 싶은데 무엇부터 해야 할지 모르겠다면, 과정 이름보다 지금 영어가 필요한 장면부터 정리하는 편이 쉽습니다.",
        "회화·시험·학교 영어처럼 목적을 먼저 고르고, 현재 할 수 있는 것과 자주 막히는 부분을 나누면 첫 수업의 방향도 선명해집니다.",
    ),
    (
        "처음부터 모든 영어를 다시 공부할 필요는 없습니다. 가까운 목표와 최근 어려웠던 장면을 기준으로 필요한 과정부터 좁혀볼 수 있습니다.",
        "기초가 부족한지, 말하기가 어려운지, 시험 일정이 가까운지에 따라 같은 영어라도 시작 순서는 달라집니다.",
    ),
    (
        "영어를 다시 시작할 때 가장 어려운 건 교재 선택보다 ‘어디서부터 해야 하는지’ 정하는 일인 경우가 많습니다.",
        "현재 수준을 짧게 확인하고 다음 일정에 필요한 행동을 정하면 왕초보·성인회화·시험영어 중 어떤 경로가 가까운지 비교하기 쉬워집니다.",
    ),
    (
        "영어 공부를 오래 쉬었거나 여러 방법을 시도했어도 괜찮습니다. 지금 필요한 영어와 가능한 시간을 기준으로 다시 시작점을 잡을 수 있습니다.",
        "정답률·말하기·학교 일정·업무 장면처럼 확인 가능한 기준을 하나씩 나누어 보면 불필요하게 넓은 범위를 공부하는 일을 줄일 수 있습니다.",
    ),
]

HUB_MIDDLE_VARIANTS = [
    (
        "회화는 듣기만 하는 시간보다 직접 말하고 고친 표현을 다시 써보는 시간이 중요합니다.",
        "영어가 거의 처음이라면 인사·자기소개·짧은 질문처럼 바로 사용할 수 있는 한 문장부터 시작하고, 문장이 익숙해지면 질문과 상황을 조금씩 바꿉니다.",
    ),
    (
        "기초가 부족할수록 긴 프리토킹보다 짧은 문장을 정확하게 시작하는 연습이 먼저입니다.",
        "한 문장을 외우는 데서 끝내지 않고 사람·장소·시간을 바꿔 다시 말해보면 실제로 쓸 수 있는 범위가 넓어졌는지 확인하기 쉽습니다.",
    ),
    (
        "말하기는 ‘알고 있다’와 ‘바로 말할 수 있다’ 사이의 차이를 줄이는 연습입니다.",
        "짧은 질문에 한 문장으로 답하고, 피드백 뒤 다른 질문에서 같은 표현을 다시 써보는 방식으로 조금씩 말하기 범위를 넓힙니다.",
    ),
]

HUB_TEST_VARIANTS = [
    (
        "시험 목표가 있다면 일반 회화와 준비 순서를 나눠야 합니다.",
        "TOEIC은 듣기·읽기, OPIc·TOEIC Speaking은 말하기, IELTS·TOEFL·Duolingo는 여러 영역을 함께 보기 때문에 목표 시험과 일정부터 확인합니다.",
    ),
    (
        "시험 준비는 문제를 많이 푸는 것보다 어떤 영역에서 점수를 자주 잃는지 먼저 찾는 편이 좋습니다.",
        "시험 이름이 낯설다면 페이지 안에서 용어를 쉬운 뜻부터 설명하고, 최근 자료와 시험일까지 남은 시간을 기준으로 연습 비중을 정합니다.",
    ),
    (
        "점수나 등급 제출이 목적이라면 실제 시험 형식에 맞춰 준비해야 합니다.",
        "오답 이유, 답변 시작 속도, 쓰기 수정, 시간 사용처럼 시험별로 확인할 행동을 나누고 결과가 달라지는지 다시 봅니다.",
    ),
]

def esc(x) -> str:
    return html.escape(str(x), quote=True)


def station_loc(station: dict, intent: str) -> dict:
    service = SERVICE_LABELS[intent]
    jurisdiction = " ".join(
        x for x in [station.get("city"), (station.get("areas") or [None])[0]] if x
    ).strip()
    slug = f"station-{station['slug']}"
    digest = hashlib.sha256(f"{slug}|{intent}|station-v1".encode()).hexdigest()
    return {
        "full_name": " ".join(x for x in [jurisdiction, station["name"]] if x).strip(),
        "jurisdiction": jurisdiction,
        "dong": station["name"],
        "variation": clean.VARIATIONS[int(digest[:8], 16) % len(clean.VARIATIONS)],
        "slug": slug,
        "service": service,
        "station": True,
    }


def render_station_course(station: dict, intent: str, station_map: dict[str,dict]) -> tuple[str,list[str]]:
    loc = station_loc(station, intent)
    slug = loc["slug"]
    if intent in clean.SERVICE_ORDER:
        profile = svc.PROFILES[intent]
        cards,steps,proofs,feedback = clean.service_source(intent)
        rendered = svc.render_page(slug, loc, intent, profile, cards, steps, proofs, feedback)
        family = "service"
    elif intent in clean.EXAM_ORDER:
        key = next(k for k,v in ex.EXAMS.items() if v["intent"] == intent)
        rendered = ex.render(slug, loc, key, ex.EXAMS[key])
        family = "exam"
    elif intent in clean.ACADEMY_ORDER:
        base = clean.ACADEMY_BASE[intent]
        key = next(k for k,v in ex.EXAMS.items() if v["intent"] == base)
        exam = dict(ex.EXAMS[key])
        exam["service"] = clean.ACADEMY_SERVICE[intent]
        exam["intent"] = intent
        loc["service"] = clean.ACADEMY_SERVICE[intent]
        rendered = ex.render(slug, loc, key, exam)
        rendered = rendered.replace(
            '"serviceType":"영어시험 과외"',
            '"serviceType":"영어시험 수업 비교 및 1:1 맞춤 수업 안내"'
        ).replace(
            '"serviceType": "영어시험 과외"',
            '"serviceType": "영어시험 수업 비교 및 1:1 맞춤 수업 안내"'
        )
        family = "exam"
    elif intent in clean.CONV_DERIVED_ORDER:
        base = clean.CONV_DERIVED_BASE[intent]
        loc["service"] = clean.CONV_DERIVED_SERVICE[intent]
        profile = clean.CONV_DERIVED_PROFILE[intent]
        source = clean.CONV_DERIVED_SOURCE[intent]
        rendered = svc.render_page(
            slug, loc, intent, profile,
            source["cards"], source["steps"], source["proofs"], source["feedback"]
        )
        if intent in clean.CONV_ACADEMY_INTENTS:
            rendered = rendered.replace(
                '"serviceType":"영어교육"',
                '"serviceType":"영어회화 수업 비교 및 1:1 맞춤 수업 안내"'
            ).replace(
                '"serviceType": "영어교육"',
                '"serviceType": "영어회화 수업 비교 및 1:1 맞춤 수업 안내"'
            )
        family = "service"
    else:
        raise ValueError(intent)

    raw, problems = clean.productionize(rendered, loc, intent, family)

    # Add station navigation before the normal related-course cluster.
    nearby = [
        station_map[s] for s in station.get("nearby", [])
        if s in station_map
    ]
    nearby_html = "".join(
        f'<a href="/station-{esc(x["slug"])}.html">{esc(x["name"])} 영어 안내</a>'
        for x in nearby[:10]
    )
    meta_bits = [*(station.get("lines") or [])]
    if station.get("city"):
        meta_bits.append(station["city"])
    if station.get("areas"):
        meta_bits.extend(station["areas"][:1])
    context = (
        '<section class="section station-context"><div class="wrap">'
        '<p class="kicker">역 기준 영어 과정</p>'
        f'<h2>{esc(station["name"])}에서 과정별 영어를 한 번에 비교할 수 있습니다</h2>'
        f'<p>{esc(" · ".join(meta_bits))} 기준으로 역 페이지를 나누었지만, 학습 방향은 위치가 아니라 현재 수준·목표·일정으로 정합니다.</p>'
        f'<p><a class="station-hub-link" href="/station-{esc(station["slug"])}.html">{esc(station["name"])} 전체 과정 보기 →</a></p>'
        + (f'<div class="links station-nearby-links">{nearby_html}</div>' if nearby_html else '')
        + '</div></section>'
    )
    marker = '<section class="section related">'
    if marker in raw:
        raw = raw.replace(marker, context + marker, 1)
    else:
        raw = raw.replace('<section id="consultation-preview"', context + '<section id="consultation-preview"', 1)

    # Better breadcrumb: Home > 전국 역 > Station > Course.
    h1 = clean.plain_h1(raw)
    crumb = (
        '<div class="breadcrumb wrap" aria-label="현재 위치">'
        '<a href="/englishpt.html">잉글리시PT</a><span aria-hidden="true">/</span>'
        '<a href="/stations.html">전국 역</a><span aria-hidden="true">/</span>'
        f'<a href="/station-{esc(station["slug"])}.html">{esc(station["name"])}</a><span aria-hidden="true">/</span>'
        f'<strong>{esc(h1)}</strong></div>'
    )
    raw = re.sub(r'<div class="breadcrumb wrap".*?</div>', crumb, raw, count=1, flags=re.S)

    # Station pages should explicitly link to the station hub in machine-readable breadcrumbs too.
    schema = re.search(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)
    if schema:
        try:
            data = json.loads(schema.group(1))
            graph = data.get("@graph") or []
            for node in graph:
                if isinstance(node,dict) and node.get("@type") == "BreadcrumbList":
                    node["itemListElement"] = [
                        {"@type":"ListItem","position":1,"name":"잉글리시PT","item":BASE_URL+"/englishpt.html"},
                        {"@type":"ListItem","position":2,"name":"전국 역","item":BASE_URL+"/stations.html"},
                        {"@type":"ListItem","position":3,"name":station["name"],"item":f'{BASE_URL}/station-{station["slug"]}.html'},
                        {"@type":"ListItem","position":4,"name":h1,"item":f'{BASE_URL}/station-{station["slug"]}-{intent}.html'},
                    ]
            rep = '<script type="application/ld+json">' + json.dumps(data,ensure_ascii=False,separators=(",",":")) + '</script>'
            raw = raw[:schema.start()] + rep + raw[schema.end():]
        except Exception:
            problems.append("station_breadcrumb_schema")

    return raw, problems


def modal(station_name: str) -> str:
    return f'''<div class="form-modal" id="applyModal" aria-hidden="true"><div class="form-dim" data-close-form></div><section class="form-sheet" role="dialog" aria-modal="true" aria-labelledby="formTitle"><button class="form-close" type="button" aria-label="상담 신청 닫기" data-close-form>×</button><div class="form-kicker">무료 학습 진단</div><h2 id="formTitle">무료 PT 진단 신청</h2><p class="form-intro">과정을 정확히 몰라도 됩니다. 현재 어려운 부분과 목표부터 자유롭게 남겨주세요.</p><form id="leadForm"><label>이름 <span>*</span><input id="leadName" name="name" autocomplete="name" required></label><label>연락처 <span>*</span><input id="leadPhone" name="phone" inputmode="tel" autocomplete="tel" placeholder="010-0000-0000" required></label><label>지역 <span>*</span><input id="leadArea" name="area" value="{esc(station_name)}" required></label><label class="full">문의내용<textarea id="leadMessage" name="message" rows="4" placeholder="현재 어려운 부분, 목표하는 부분을 자유롭게 작성해주세요."></textarea></label><input type="hidden" id="leadClass" name="wantedClass" value="{esc(station_name)} 영어 상담"><label class="privacy-check"><input id="leadConsent" name="consent" type="checkbox" required> <span>상담을 위한 개인정보 수집·이용에 동의합니다.</span></label><details class="privacy-detail"><summary>수집·이용 안내</summary><p>수집 항목: 이름, 연락처, 지역, 문의내용. 이용 목적: 영어 학습 상담 및 연락. 상담 목적이 끝난 개인정보는 관계 법령상 보존 의무가 없는 한 지체 없이 파기합니다.</p></details><button class="submit-lead" type="submit">무료 PT 진단 신청 →</button><p class="form-alt">전송이 어려운 경우 <a href="tel:01050068027">010-5006-8027</a> 또는 <a href="mailto:cicada3865@naver.com">cicada3865@naver.com</a>로 문의할 수 있습니다.</p><div id="leadStatus" class="lead-status" role="status" aria-live="polite"></div></form></section></div>'''


def header() -> str:
    return '''<header class="site-header"><div class="wrap header-inner"><a class="brand" href="/englishpt.html"><span class="brand-mark">PT</span><span>ENGLISH PT</span></a><nav class="desktop-nav" aria-label="주요 메뉴"><a href="/courses.html">과정찾기</a><a href="/english-conversation.html">1:1영어회화</a><a href="/exam-english.html">시험영어</a><a href="/stations.html">역으로 찾기</a><button class="nav-form" type="button" data-open-form>무료 PT 진단</button></nav><button class="mobile-menu" type="button" aria-expanded="false" aria-controls="mobileNav" data-menu>메뉴</button></div><div id="mobileNav" class="mobile-nav" hidden><div class="wrap"><a href="/courses.html">과정찾기</a><a href="/english-conversation.html">1:1영어회화</a><a href="/exam-english.html">시험영어</a><a href="/stations.html">전국 역</a><button type="button" data-open-form>무료 PT 진단</button></div></div></header>'''


def course_groups(station: dict) -> str:
    blocks=[]
    for title,intents in GROUPS:
        links="".join(
            f'<a href="/station-{esc(station["slug"])}-{intent}.html"><span>{esc(station["name"])} {esc(SERVICE_LABELS[intent])}</span><b>→</b></a>'
            for intent in intents
        )
        blocks.append(
            f'<div class="station-course-group"><h3>{esc(title)}</h3><div class="station-course-links">{links}</div></div>'
        )
    return "".join(blocks)


def station_hub(station: dict, station_map: dict[str,dict]) -> str:
    digest = int(hashlib.sha256((station["slug"]+"|hub-v2").encode()).hexdigest()[:8],16)
    intro = HUB_INTRO_VARIANTS[digest % len(HUB_INTRO_VARIANTS)]
    middle = HUB_MIDDLE_VARIANTS[digest % len(HUB_MIDDLE_VARIANTS)]
    test = HUB_TEST_VARIANTS[digest % len(HUB_TEST_VARIANTS)]
    jurisdiction = " ".join(x for x in [station.get("city"), (station.get("areas") or [None])[0]] if x).strip()
    lines = " · ".join(station.get("lines") or ["역 기준"])
    title=f'{station["name"]} 영어회화·영어과외 | 1:1 맞춤 영어 | 잉글리시PT'
    desc=f'{station["name"]} 영어회화·영어과외를 왕초보·성인·직장인·학생·토익·오픽·아이엘츠·토플 등 과정별로 비교하고 1:1 맞춤 상담으로 연결합니다.'
    canonical=f'{BASE_URL}/station-{station["slug"]}.html'
    nearby=[station_map[s] for s in station.get("nearby",[]) if s in station_map][:10]
    nearby_html="".join(f'<a href="/station-{esc(x["slug"])}.html">{esc(x["name"])} 영어</a>' for x in nearby)

    schema={
        "@context":"https://schema.org",
        "@graph":[
            {"@type":"EducationalOrganization","@id":BASE_URL+"/#organization","name":"잉글리시PT","url":BASE_URL+"/englishpt.html","telephone":"+82-10-5006-8027","email":"cicada3865@naver.com"},
            {"@type":"WebSite","@id":BASE_URL+"/#website","url":BASE_URL+"/englishpt.html","name":"ENGLISH PT","inLanguage":"ko-KR","publisher":{"@id":BASE_URL+"/#organization"}},
            {"@type":"WebPage","@id":canonical+"#webpage","url":canonical,"name":title,"description":desc,"inLanguage":"ko-KR","isPartOf":{"@id":BASE_URL+"/#website"}},
            {"@type":"BreadcrumbList","itemListElement":[
                {"@type":"ListItem","position":1,"name":"잉글리시PT","item":BASE_URL+"/englishpt.html"},
                {"@type":"ListItem","position":2,"name":"전국 역","item":BASE_URL+"/stations.html"},
                {"@type":"ListItem","position":3,"name":station["name"],"item":canonical},
            ]},
        ],
    }

    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow,max-image-preview:large"><link rel="canonical" href="{esc(canonical)}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(canonical)}"><meta name="theme-color" content="#101915"><link rel="stylesheet" href="/assets/styles.css"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False,separators=(",",":"))}</script><script defer src="https://cdn.jsdelivr.net/npm/@emailjs/browser@4/dist/email.min.js"></script><script defer src="/assets/site.js"></script></head><body class="intent-hub station-hub-page">{header()}<main><div class="breadcrumb wrap" aria-label="현재 위치"><a href="/englishpt.html">잉글리시PT</a><span aria-hidden="true">/</span><a href="/stations.html">전국 역</a><span aria-hidden="true">/</span><strong>{esc(station["name"])}</strong></div><section class="hero station-hero"><div class="wrap hero-grid"><div><div class="eyebrow">{esc(lines)}{(" · "+esc(jurisdiction)) if jurisdiction else ""}</div><h1>{esc(station["name"])}<br>영어회화·영어과외</h1><p class="hero-statement">목적과 현재 수준에 맞는 과정부터 선택합니다.</p><p class="hero-copy">{esc(intro[0])}</p><button class="btn light" type="button" data-open-form>내 상황으로 상담하기 →</button></div><aside class="hero-sheet"><div class="sheet-head"><span>ENGLISH PT</span><span>{esc(station["name"])}</span></div><div><small>기초</small><strong>왕초보·기본문장</strong></div><div><small>회화</small><strong>성인·직장인·생활영어</strong></div><div><small>시험</small><strong>TOEIC·OPIc·IELTS·TOEFL</strong></div><div><small>학생</small><strong>초등·중등·고등 영어</strong></div></aside></div></section><section class="section soft"><div class="wrap editorial"><div class="eyebrow ink">시작점</div><h2>{esc(station["name"])}에서 영어를 시작한다면<br>과정명보다 지금 필요한 장면부터 봅니다.</h2><p>{esc(intro[1])}</p><p>역 이름은 검색과 수업 가능 범위를 찾기 위한 기준입니다. 실제 수업 방향은 지역 특성을 추측하지 않고 현재 자료·목표·일정·가능한 학습 시간을 기준으로 정합니다.</p></div></section><section class="section"><div class="wrap"><div class="section-head"><div><div class="eyebrow ink">기초·회화</div><h2>영어가 거의 처음이어도<br>짧은 한 문장부터 시작할 수 있습니다.</h2></div><p class="lead">{esc(middle[0])}</p></div><div class="quad"><article><div class="code">1</div><h3>현재 말하기 확인</h3><p>인사·자기소개·짧은 질문에서 지금 바로 말할 수 있는 범위를 봅니다.</p></article><article><div class="code">2</div><h3>쉬운 문장부터</h3><p>{esc(middle[1])}</p></article><article><div class="code">3</div><h3>바로 피드백</h3><p>고친 표현은 같은 시간에 다시 말해보고 질문을 조금 바꿔 재사용합니다.</p></article><article><div class="code">4</div><h3>다음 수업 연결</h3><p>혼자 된 부분과 다시 어려웠던 부분을 나눠 다음 연습의 첫 순서를 정합니다.</p></article></div></div></section><section class="section soft"><div class="wrap editorial"><div class="eyebrow ink">시험영어</div><h2>목표가 시험이라면<br>시험 방식과 일정부터 분리해서 봅니다.</h2><p>{esc(test[0])}</p><p>{esc(test[1])}</p></div></section><section class="section station-course-section" id="courses"><div class="wrap"><div class="section-head"><div><div class="eyebrow ink">과정별 바로가기</div><h2>{esc(station["name"])} 기준으로<br>23개 영어 과정을 바로 확인하세요.</h2></div><p class="lead">원하는 과정이 정해져 있으면 바로 이동하고, 아직 모르겠다면 상담에서 현재 상황부터 설명해도 됩니다.</p></div>{course_groups(station)}</div></section>{('<section class="section soft"><div class="wrap"><div class="section-head"><div><div class="eyebrow ink">인근 역</div><h2>같은 노선의 가까운 역도<br>함께 확인할 수 있습니다.</h2></div></div><div class="links station-nearby-links">'+nearby_html+'</div></div></section>') if nearby_html else ''}<section class="final"><div class="wrap final-box"><div><div class="eyebrow">상담 시작</div><h2>{esc(station["name"])} 영어,<br>무엇부터 시작할지 모르겠다면</h2><p>현재 어려운 부분과 영어가 필요한 이유만 알려주세요. 과정명은 미리 정하지 않아도 됩니다.</p></div><button class="btn light" type="button" data-open-form>무료 PT 진단 신청 →</button></div></section></main><footer><div class="wrap footer-grid"><div><div class="footer-brand">ENGLISH PT</div><p>{esc(station["name"])} · 1:1 맞춤 영어관리</p></div><div><p><a href="tel:01050068027">010-5006-8027</a><br><a href="mailto:cicada3865@naver.com">cicada3865@naver.com</a></p><p class="foot-note">지역보다 현재 수준과 목표를 기준으로 시작합니다.</p></div></div></footer>{modal(station["name"])}<div class="mobile-sticky"><button type="button" data-open-form>무료 PT 진단 신청</button></div></body></html>'''


def station_index(data: dict) -> str:
    lines_html=[]
    station_map={x["slug"]:x for x in data["stations"]}
    for line in data["lines"]:
        anchors="".join(
            f'<a class="station-index-link" data-station-name="{esc(station_map[s]["name"])}" href="/station-{esc(s)}.html">{esc(station_map[s]["name"])}</a>'
            for s in line["stations"] if s in station_map
        )
        lines_html.append(
            f'<section class="station-line-block"><h2>{esc(line["name"])} <small>{len(line["stations"])}개 역</small></h2><div class="station-index-grid">{anchors}</div></section>'
        )
    title="전국 지하철·철도역 영어회화·영어과외 | 911개 역 | 잉글리시PT"
    desc="전국 37개 노선 911개 역에서 영어회화·영어과외·토익·오픽·아이엘츠·토플·학생영어 과정을 역별로 찾을 수 있는 잉글리시PT 역 안내입니다."
    canonical=BASE_URL+"/stations.html"
    schema={
        "@context":"https://schema.org",
        "@graph":[
            {"@type":"EducationalOrganization","@id":BASE_URL+"/#organization","name":"잉글리시PT","url":BASE_URL+"/englishpt.html"},
            {"@type":"WebSite","@id":BASE_URL+"/#website","url":BASE_URL+"/englishpt.html","name":"ENGLISH PT","inLanguage":"ko-KR"},
            {"@type":"CollectionPage","@id":canonical+"#webpage","url":canonical,"name":title,"description":desc,"inLanguage":"ko-KR","isPartOf":{"@id":BASE_URL+"/#website"}},
            {"@type":"BreadcrumbList","itemListElement":[
                {"@type":"ListItem","position":1,"name":"잉글리시PT","item":BASE_URL+"/englishpt.html"},
                {"@type":"ListItem","position":2,"name":"전국 역","item":canonical},
            ]},
        ],
    }
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow,max-image-preview:large"><link rel="canonical" href="{canonical}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{canonical}"><meta name="theme-color" content="#101915"><link rel="stylesheet" href="/assets/styles.css"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False,separators=(",",":"))}</script><script defer src="/assets/site.js"></script></head><body class="intent-hub station-index-page">{header()}<main><div class="breadcrumb wrap" aria-label="현재 위치"><a href="/englishpt.html">잉글리시PT</a><span aria-hidden="true">/</span><strong>전국 역</strong></div><section class="hero station-index-hero"><div class="wrap"><div class="eyebrow">전국 37개 노선 · 911개 역</div><h1>자주 이용하는 역에서<br>영어 과정을 찾아보세요.</h1><p class="hero-copy">역을 고르면 왕초보·성인·직장인·학생영어와 TOEIC·OPIc·IELTS·TOEFL 등 과정별 페이지로 바로 이어집니다.</p><div class="station-search-box"><label for="stationSearch">역 이름 검색</label><input id="stationSearch" type="search" placeholder="예: 도봉산역, 강남역, 부산역" autocomplete="off"></div></div></section><section class="section"><div class="wrap"><div class="section-head"><div><div class="eyebrow ink">노선으로 찾기</div><h2>노선을 선택하거나<br>역 이름을 검색하세요.</h2></div><p class="lead">환승역은 여러 노선에 함께 표시되며, 같은 역 페이지로 연결됩니다.</p></div><div id="stationLines">{''.join(lines_html)}</div><p id="stationEmpty" class="station-empty" hidden>검색한 역을 찾지 못했습니다. 역 이름을 다시 확인해주세요.</p></div></section><section class="final"><div class="wrap final-box"><div><div class="eyebrow">과정으로 찾기</div><h2>역보다 과정이 먼저라면<br>전국 과정 허브에서 시작하세요.</h2><p>영어회화·시험영어·학생영어 중 목적에 가까운 과정을 먼저 확인할 수도 있습니다.</p></div><a class="btn light" href="/courses.html">영어 과정 찾기 →</a></div></section></main><footer><div class="wrap footer-grid"><div><div class="footer-brand">ENGLISH PT</div><p>전국 911개 역 · 1:1 맞춤 영어</p></div><div><p><a href="tel:01050068027">010-5006-8027</a><br><a href="mailto:cicada3865@naver.com">cicada3865@naver.com</a></p></div></div></footer><script>(function(){{const input=document.getElementById('stationSearch'),empty=document.getElementById('stationEmpty');if(!input)return;input.addEventListener('input',function(){{const q=this.value.trim().toLowerCase();let shown=0;document.querySelectorAll('.station-line-block').forEach(block=>{{let local=0;block.querySelectorAll('.station-index-link').forEach(a=>{{const ok=!q||a.dataset.stationName.toLowerCase().includes(q);a.hidden=!ok;if(ok){{local++;shown++;}}}});block.hidden=!!q&&local===0;}});empty.hidden=shown>0;}});}})();</script></body></html>'''


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    out=Path(args.output)
    out.mkdir(parents=True,exist_ok=True)
    data=json.loads((ROOT/"data"/"stations.json").read_text(encoding="utf-8"))
    if data.get("station_count") != 911 or data.get("line_count") != 37:
        raise RuntimeError("station dataset contract mismatch")
    station_map={x["slug"]:x for x in data["stations"]}

    errors=[]
    for station in data["stations"]:
        hub_name=f'station-{station["slug"]}.html'
        (out/hub_name).write_text(station_hub(station,station_map),encoding="utf-8")
        for intent in ALL_INTENTS:
            raw,problems=render_station_course(station,intent,station_map)
            name=f'station-{station["slug"]}-{intent}.html'
            if problems:
                errors.append({"file":name,"problems":problems})
            (out/name).write_text(raw,encoding="utf-8")

    (out/"stations.html").write_text(station_index(data),encoding="utf-8")

    expected=911*(1+len(ALL_INTENTS))+1
    actual=sum(1 for p in out.glob("station-*.html")) + int((out/"stations.html").exists())
    if actual != expected:
        raise RuntimeError(f"station page count mismatch: {actual} != {expected}")
    if errors:
        print(json.dumps({"status":"FAIL_STATION_RENDER","error_count":len(errors),"errors":errors[:50]},ensure_ascii=False,indent=2))
        return 1
    print(json.dumps({
        "status":"PASS_STATION_RENDER",
        "station_count":911,
        "intent_count":len(ALL_INTENTS),
        "station_hubs":911,
        "station_course_pages":911*len(ALL_INTENTS),
        "station_index":1,
        "total_station_html":expected,
        "dobongsan_hub":"station-dobongsan.html",
    },ensure_ascii=False,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
