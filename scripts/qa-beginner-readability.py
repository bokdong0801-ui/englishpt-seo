#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Beginner-readability QA for ENGLISH PT Stage 9 output.

This QA intentionally keeps official exam names/SEO terminology available, but
requires beginner explanations to appear before detailed exam copy and blocks
known machine-like or expert-only wording from visible body text.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

EXAM_SUFFIXES = [
    ("toeic-speaking-academy", "toeic-speaking"),
    ("duolingo-academy", "duolingo"),
    ("ielts-academy", "ielts"),
    ("toefl-academy", "toefl"),
    ("opic-academy", "opic"),
    ("toeic-academy", "toeic"),
    ("toeic-speaking", "toeic-speaking"),
    ("duolingo", "duolingo"),
    ("ielts", "ielts"),
    ("toefl", "toefl"),
    ("opic", "opic"),
    ("toeic", "toeic"),
]

CONVERSATION_SUFFIXES = [
    "worker-english-conv-academy",
    "adult-english-conv-academy",
    "english-conv-academy",
    "beginner-english-conv",
    "biz-business-conv",
    "jobseeker-conv",
    "housewife-conv",
    "high-conv",
    "mid-conv",
    "univ-conv",
    "elem-tutor",
]

GUIDE_ANCHORS = {
    "toeic": [
        "토익은 크게 듣기와 읽기 두 영역으로 나뉩니다.",
        "듣기 (LC)",
        "읽기 (RC)",
    ],
    "toeic-speaking": [
        "토익스피킹은 컴퓨터에 영어 답변을 녹음하는 말하기 시험입니다.",
        "문항",
        "답변 구조",
    ],
    "opic": [
        "오픽은 질문을 듣고 자신의 경험이나 생각을 영어로 말하는 시험입니다.",
        "배경설문",
        "돌발 질문",
        "롤플레이",
    ],
    "ielts": [
        "아이엘츠는 듣기·읽기·쓰기·말하기 네 영역을 보는 시험입니다.",
        "Band",
        "Overall Band",
    ],
    "duolingo": [
        "듀오링고 영어시험은 컴퓨터로 보는 영어 능력 시험입니다.",
        "DET",
        "난이도 변화",
    ],
    "toefl": [
        "토플은 읽기·듣기·말하기·쓰기 네 영역을 보는 영어 시험입니다.",
        "통합형",
        "4영역",
    ],
}

# These terms have already been intentionally replaced by human-readable Korean
# in visible copy. Finding them again means a later change regressed readability.
FORBIDDEN_VISIBLE = [
    "academic performance",
    "adaptive format",
    "productive response",
    "open response",
    "발화 명료성",
    "문항 요구",
    "입력정보",
    "스크립트",
    "병목",
    "태깅",
    "재검증",
    "재평가",
    "재작성",
    "재답변",
]

HOME_REQUIRED = [
    "수준 확인 → 학습 계획 → 직접 연습 → 부족한 점 확인 → 다시 점검",
    "잘되는 부분과 반복해서 어려운 부분을 나눕니다.",
    "국제학교 수업과 평가 방식의 차이",
    "<small>현재</small>",
    "<small>계획</small>",
    "<small>연습</small>",
    "<small>점검</small>",
    "전체지역·과정 바로가기",
    "911개 역으로 찾기",
    "stations.html",
]

HUBS_REQUIRED = {
    "courses.html": ["영어 과정 찾기", "전국 과정 안내", "english-conversation.html", "exam-english.html", "student-english.html", "과정을 잘 몰라도 괜찮습니다", "어디서부터 시작할지 고민이라면", "무엇부터 해야 할지 모르겠다면", "희망 지역과 수업 방식은"],
    "english-conversation.html": ["1:1 영어회화", "왕초보 영어회화", "직장인 영어회화", "성인 영어회화", "상담에서 확인하기", "희망 지역과 수업 방식은"],
    "exam-english.html": ["시험영어", "토익", "토익스피킹", "오픽", "아이엘츠", "토플", "듀오링고 영어시험", "상담하기 →", "희망 지역과 수업 방식은"],
    "student-english.html": ["학생영어", "초등 영어", "중등 영어", "고등 영어", "국제학교 영어", "상담하기 →", "희망 지역과 수업 방식은"],
}

def visible_body(raw: str) -> str:
    body = raw.split("</head>", 1)[1] if "</head>" in raw else raw
    body = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", " ", body, flags=re.I | re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    return re.sub(r"\s+", " ", html.unescape(body)).strip()

def exam_base(name: str) -> str | None:
    for suffix, base in EXAM_SUFFIXES:
        if name.endswith("-" + suffix + ".html"):
            return base
    return None

def is_conversation(name: str) -> bool:
    return any(name.endswith("-" + suffix + ".html") for suffix in CONVERSATION_SUFFIXES)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--report", default="STAGE9_BEGINNER_READABILITY_QA.json")
    args = ap.parse_args()

    root = Path(args.root)
    failures: list[dict] = []
    warnings: list[dict] = []
    counts = {
        "html_total": 0,
        "exam_pages_checked": 0,
        "conversation_pages_checked": 0,
        "home_pages_checked": 0,
    }

    home = root / "englishpt.html"
    if not home.exists():
        failures.append({"file":"englishpt.html","rule":"home_missing"})
    else:
        raw = home.read_text(encoding="utf-8")
        text = visible_body(raw)
        counts["home_pages_checked"] += 1
        for phrase in HOME_REQUIRED:
            if phrase not in raw:
                failures.append({"file":"englishpt.html","rule":"home_easy_copy_missing","value":phrase})
        for phrase in FORBIDDEN_VISIBLE:
            if phrase in text:
                failures.append({"file":"englishpt.html","rule":"home_difficult_term","value":phrase})
        if raw.count('class="change-card"') != 3 or '변화 리포트' not in raw or '사례 유형' not in raw:
            failures.append({"file":"englishpt.html","rule":"home_change_report_missing_or_wrong_count","count":raw.count('class="change-card"')})
        if 'data-course="학습 변화 상담"' not in raw:
            failures.append({"file":"englishpt.html","rule":"home_change_report_cta_missing"})

        song_links = sorted(set(re.findall(r'href="([^"]*songhyeondong[^"]*)"', raw, flags=re.I)))
        if song_links:
            failures.append({
                "file":"englishpt.html",
                "rule":"national_home_still_links_to_songhyeondong",
                "count":len(song_links),
                "links":song_links,
            })
        for href in ("courses.html","english-conversation.html","exam-english.html","student-english.html","stations.html"):
            if href not in raw:
                failures.append({"file":"englishpt.html","rule":"national_hub_link_missing","value":href})

    for hub_name, required in HUBS_REQUIRED.items():
        hub = root / hub_name
        if not hub.exists():
            failures.append({"file":hub_name,"rule":"national_hub_missing"})
            continue
        hub_raw = hub.read_text(encoding="utf-8")
        hub_text = visible_body(hub_raw)
        if "songhyeondong" in hub_raw.lower() or "송현동" in hub_text:
            failures.append({"file":hub_name,"rule":"hub_contains_fixed_songhyeondong"})
        for phrase in required:
            if phrase not in hub_raw:
                failures.append({"file":hub_name,"rule":"hub_required_copy_missing","value":phrase})
        if not re.search(r'<meta name="robots" content="[^"]*index[^"]*follow[^"]*">', hub_raw, re.I):
            failures.append({"file":hub_name,"rule":"hub_index_follow_missing"})
        if f'https://englishpt.kr/{hub_name}' not in hub_raw:
            failures.append({"file":hub_name,"rule":"hub_canonical_missing"})
        if hub_name in ("exam-english.html","english-conversation.html"):
            if hub_raw.count('class="change-card"') != 3:
                failures.append({"file":hub_name,"rule":"change_report_card_count","expected":3,"actual":hub_raw.count('class="change-card"')})
            if '사례 유형' not in hub_raw:
                failures.append({"file":hub_name,"rule":"change_report_example_disclosure_missing"})

        expected_ctas={"courses.html":0,"english-conversation.html":6,"exam-english.html":6,"student-english.html":4}[hub_name]
        if hub_raw.count('class="route-cta"') != expected_ctas:
            failures.append({"file":hub_name,"rule":"hub_route_cta_count","expected":expected_ctas,"actual":hub_raw.count('class="route-cta"')})
        if hub_name == "courses.html":
            if 'class="hub-conversion-box"' not in hub_raw or 'data-course="과정 선택 상담"' not in hub_raw:
                failures.append({"file":hub_name,"rule":"course_finder_conversion_bridge_missing"})

    for p in root.glob("*.html"):
        counts["html_total"] += 1
        if p.name == "englishpt.html":
            continue

        base = exam_base(p.name)
        conv = is_conversation(p.name)
        if not base and not conv:
            continue

        raw = p.read_text(encoding="utf-8")
        text = visible_body(raw)

        for phrase in FORBIDDEN_VISIBLE:
            if phrase in text:
                failures.append({"file":p.name,"rule":"difficult_visible_term","value":phrase})

        if base:
            counts["exam_pages_checked"] += 1
            if 'data-beginner-guide="true"' not in raw:
                failures.append({"file":p.name,"rule":"beginner_guide_missing","exam":base})
                continue
            guide_i = raw.find('data-beginner-guide="true"')
            intro_i = raw.find('class="section intro-detail"')
            hero_i = raw.find('class="hero')
            # Current mass pages use intro-detail. Preserved legacy pages do not,
            # so for those we require the beginner guide to appear immediately
            # after the Hero and before the next substantive section.
            if intro_i >= 0:
                if guide_i > intro_i:
                    failures.append({"file":p.name,"rule":"beginner_guide_not_before_intro","exam":base})
            else:
                if hero_i < 0 or guide_i < hero_i:
                    failures.append({"file":p.name,"rule":"legacy_beginner_guide_not_after_hero","exam":base})
            for phrase in GUIDE_ANCHORS[base]:
                if phrase not in raw:
                    failures.append({"file":p.name,"rule":"beginner_definition_missing","exam":base,"value":phrase})
        elif conv:
            counts["conversation_pages_checked"] += 1

    report = {
        "status": "PASS_BEGINNER_READABILITY_QA" if not failures else "FAIL_BEGINNER_READABILITY_QA",
        "counts": counts,
        "rules": {
            "exam_beginner_guide_required": True,
            "guide_must_precede_intro_or_follow_legacy_hero": True,
            "blocked_visible_terms": FORBIDDEN_VISIBLE,
            "homepage_easy_copy_required": HOME_REQUIRED,
            "songhyeondong_home_links": "must_be_zero",
            "national_hubs_required": list(HUBS_REQUIRED),
        },
        "failures": failures[:250],
        "failure_count": len(failures),
        "warnings": warnings,
    }
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
