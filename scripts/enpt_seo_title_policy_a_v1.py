#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ENGLISH PT approved SEO title policy A. No publishing or index-policy changes.

Apply to existing station hub and 23 specialized intents. Neighborhood hub title
can be reused only when a separately approved real neighborhood hub exists.
"""
from __future__ import annotations

HUB_SUFFIX = "영어회화 영어과외 | 1:1 맞춤 직장인 학생 주부"

# The 23 intents match stage9-clean-mass-renderer.py's SERVICE, EXAM,
# ACADEMY and CONV_DERIVED groups exactly. No unrelated audiences in specialties.
COURSE_TITLES = {
    "elem-tutor": ("초등학생 영어과외", "1:1 맞춤 기초학습"),
    "mid-conv": ("중학생 영어회화", "1:1 맞춤 수행평가"),
    "high-conv": ("고등학생 영어회화", "1:1 맞춤 발표·면접"),
    "univ-conv": ("대학생 영어회화", "1:1 맞춤 발표·교환학생"),
    "jobseeker-conv": ("취준생 영어회화", "1:1 맞춤 영어면접"),
    "biz-business-conv": ("직장인 영어회화", "1:1 맞춤 비즈니스 영어"),
    "housewife-conv": ("주부 영어회화", "기초부터 1:1 맞춤"),
    "toeic": ("토익 과외", "1:1 맞춤 LC·RC"),
    "toeic-speaking": ("토익스피킹 과외", "1:1 맞춤 답변 연습"),
    "opic": ("오픽 과외", "1:1 맞춤 말하기"),
    "ielts": ("아이엘츠 과외", "1:1 맞춤 4영역"),
    "duolingo": ("듀오링고 영어테스트", "1:1 맞춤 시험 대비"),
    "toefl": ("토플 과외", "1:1 맞춤 4영역"),
    "toeic-academy": ("토익학원 비교", "1:1 맞춤 수업 선택"),
    "toeic-speaking-academy": ("토익스피킹학원 비교", "1:1 맞춤 피드백"),
    "opic-academy": ("오픽학원 비교", "1:1 맞춤 말하기"),
    "ielts-academy": ("아이엘츠학원 비교", "1:1 맞춤 첨삭"),
    "duolingo-academy": ("듀오링고학원 비교", "1:1 맞춤 시험 대비"),
    "toefl-academy": ("토플학원 비교", "1:1 맞춤 통합형"),
    "english-conv-academy": ("영어회화학원 비교", "1:1 맞춤 수업"),
    "adult-english-conv-academy": ("성인 영어회화학원 비교", "기초부터 1:1 맞춤"),
    "worker-english-conv-academy": ("직장인 영어회화학원 비교", "1:1 맞춤 비즈니스"),
    "beginner-english-conv": ("왕초보 영어회화", "기초부터 1:1 맞춤"),
}

def hub_title(place: str) -> str:
    """A-type for a *real* station or neighborhood general hub."""
    place = place.strip()
    if not place:
        raise ValueError("missing place label")
    return f"{place} {HUB_SUFFIX}"

def course_title(place: str, intent: str) -> str:
    """Specific-intent title, no brand and no other audience targeting."""
    place = place.strip()
    if not place:
        raise ValueError("missing place label")
    left, right = COURSE_TITLES[intent]  # Unknown intent is a hard failure.
    return f"{place} {left} | {right}"

def station_hub_description(place: str) -> str:
    return (
        f"{place} 영어회화·영어과외 안내. 직장인·학생·주부를 위한 1:1 맞춤 영어부터 "
        "왕초보·기초회화, 비즈니스 영어, 토익·오픽 등 23개 과정을 비교하고 "
        "현재 수준과 학습 목표에 맞게 선택해 보세요."
    )
