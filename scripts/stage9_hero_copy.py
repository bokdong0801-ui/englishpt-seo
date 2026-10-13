#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic audience-led Hero + compact next-step copy for Stage 9 locality pages.

Scope: visible Hero and the immediate guide only. Preserve localized SEO H1,
canonical, metadata, existing forms and all other substantive page content.
"""
from __future__ import annotations

import hashlib
import html

STUDENT = {"elem-tutor", "mid-conv", "high-conv"}
WORKER = {"biz-business-conv", "worker-english-conv-academy"}
EXAM = {
    "toeic", "toeic-speaking", "opic", "ielts", "duolingo", "toefl",
    "toeic-academy", "toeic-speaking-academy", "opic-academy",
    "ielts-academy", "duolingo-academy", "toefl-academy",
}
BEGINNER = {"beginner-english-conv"}

# Copy banks rotate independently; locality+intent+salt makes output stable
# across rebuilds while reducing repeated openings between neighboring pages.
COPY = {
    "student": {
        "label": "학생 영어 · 학부모 안내",
        "cta": "우리 아이 영어 상담하기",
        "guide": "우리 아이에게 맞는 수업은 무엇부터 확인할까요?",
        "hooks": [
            "우리 아이 영어 공부, 지금 수준에 맞게 시작하세요.",
            "학년이 같아도 영어의 어려운 부분은 다를 수 있어요.",
            "영어 기초부터 학교 일정까지, 아이에게 필요한 순서를 찾아보세요.",
            "무엇부터 해야 할지 고민된다면 아이가 어려워하는 부분부터 살펴보세요.",
            "진도를 더 나가기 전에 현재 이해하는 범위를 확인해보세요.",
            "기초가 부족해도 지금 할 수 있는 부분부터 차근차근 시작할 수 있어요.",
            "학교 영어가 부담스럽다면 작은 학습 목표부터 나눠보세요.",
            "우리 아이에게 맞는 영어 공부 방향을 함께 찾아보세요.",
        ],
        "copies": [
            "{dong}에서 {service}를 알아본다면 학년뿐 아니라 최근 어려워한 내용과 학교 일정도 함께 살펴보세요.",
            "{service}를 선택할 때는 아이의 현재 읽기·어휘·문장 이해부터 확인하는 편이 좋아요. {dong}에서 가능한 과정을 알아보세요.",
            "아이마다 필요한 영어 공부는 다릅니다. {dong}의 {service} 안내에서 우선순위를 비교해보세요.",
            "{dong}에서 아이의 영어 수업을 찾고 있나요? 기초, 수행평가, 내신 가운데 가까운 과제부터 정리해보세요.",
            "단어·문법·독해·말하기 중 아이에게 필요한 부분을 먼저 좁혀보세요. {dong} {service} 안내에서 시작할 수 있어요.",
            "{dong}의 {service} 수업을 비교한다면 현재 공부 습관과 어려운 부분을 함께 생각해보세요.",
            "아이에게 적합한 영어 방향은 점수만으로 정해지지 않아요. {dong}에서 필요한 과정과 수업 방식을 살펴보세요.",
            "{service}를 고민할 때는 학년별 정해진 진도보다 아이의 출발점을 확인하는 게 중요해요. {dong} 안내를 참고해보세요.",
        ],
        "steps": [
            ("현재 어려운 부분", "어휘·읽기·문장·말하기 중 부담되는 부분을 알려주세요."),
            ("다가오는 학교 일정", "수행평가·내신·학교 발표 등 가까운 일정을 살펴봅니다."),
            ("가능한 수업 방식", "학생의 일정과 지역에 맞는 수업 방식을 확인합니다."),
        ],
    },
    "beginner": {
        "label": "왕초보 영어회화 · 편안한 시작",
        "cta": "왕초보 영어회화 상담하기",
        "guide": "영어를 처음 시작할 때 이 세 가지면 충분해요.",
        "hooks": [
            "영어가 처음이어도 괜찮아요. 쉬운 한 문장부터 시작해요.",
            "영어를 오래 쉬었어도 지금 할 수 있는 말부터 시작하세요.",
            "알파벳부터 다시 배우고 싶다면 부담 없이 시작해도 괜찮아요.",
            "첫 영어회화는 긴 문장보다 짧은 인사부터 시작해요.",
            "영어로 한마디가 어렵다면 친숙한 표현부터 배워보세요.",
            "틀릴까 걱정된다면 말하기 쉬운 상황부터 골라보세요.",
            "영어가 낯설어도 한 문장씩 천천히 익혀갈 수 있어요.",
            "오늘 할 수 있는 쉬운 표현 하나부터 시작해보세요.",
        ],
        "copies": [
            "{dong}에서 왕초보 영어회화를 찾는다면 인사와 자기소개처럼 익숙한 상황부터 천천히 시작해보세요.",
            "영어를 거의 못해도 괜찮습니다. {dong}에서 기초부터 시작할 수 있는 수업 방식을 먼저 알아보세요.",
            "어려운 문법을 모두 알아야 말할 수 있는 건 아니에요. {dong}에서 짧은 질문과 대답부터 배워보세요.",
            "{dong}에서 {service}를 알아보고 있나요? 여행이나 일상에서 자주 쓰는 표현부터 시작해도 좋아요.",
            "수업에 앞서 유창하게 말할 필요는 없습니다. {dong}에서 내 속도에 맞는 {service} 안내를 살펴보세요.",
            "오랫동안 영어를 쉬었다면 인사·주문·길 묻기처럼 쉬운 목표 하나만 정해보세요. {dong} 안내에서 시작해요.",
            "{dong} {service}를 고를 때는 말하기 부담이 적고 쉬운 문장부터 배울 수 있는지를 살펴보세요.",
            "지금 아는 단어 몇 개로도 첫 문장을 시작할 수 있어요. {dong}에서 나에게 맞는 수업을 알아보세요.",
        ],
        "steps": [
            ("지금 가능한 표현", "인사·자기소개처럼 알고 있는 말부터 이야기해요."),
            ("배우고 싶은 상황", "여행·일상·직장 중 가장 가까운 목표를 골라요."),
            ("편한 시간과 방식", "부담 없는 횟수와 수업 방식을 함께 살펴봐요."),
        ],
    },
    "worker": {
        "label": "직장인 영어회화 · 업무 상황 중심",
        "cta": "직장인 영어회화 상담하기",
        "guide": "직장인 회화는 실제 업무 상황부터 정리합니다.",
        "hooks": [
            "직장인 영어회화, 필요한 상황부터 시작하세요.",
            "회의에서 첫 한마디가 어렵다면 가까운 업무 상황부터 준비하세요.",
            "업무 영어는 어려운 표현보다 자주 쓰는 문장부터 익혀보세요.",
            "출장·전화·발표 중 가장 가까운 일정에 집중해보세요.",
            "영어 회의가 걱정된다면 짧게 답하는 표현부터 준비하세요.",
            "퇴근 후에도 가능한 회화, 업무 목표를 작게 나누어 시작해보세요.",
            "직장에서 영어를 쓰는 순간, 필요한 말부터 골라보세요.",
            "업무에서 쓸 영어가 있다면 목표를 구체적으로 정해보세요.",
        ],
        "copies": [
            "{dong}에서 {service}를 찾는다면 회의·전화·출장 중 가장 가까운 업무 상황을 먼저 정해보세요.",
            "바쁜 직장인에게는 자주 쓰는 표현부터 시작하는 방식이 현실적이에요. {dong}의 {service}를 살펴보세요.",
            "{dong}의 {service} 안내에서 사용 목적과 가능한 시간을 함께 비교해보세요.",
            "문장을 길게 외우기보다 질문에 짧게 답하는 것부터 시작해보세요. {dong}에서 필요한 업무 영어를 정리합니다.",
            "회의나 발표가 예정되어 있나요? {dong}에서 일정에 맞는 {service} 방향을 알아보세요.",
            "{dong}에서 업무 영어를 시작한다면 메일·전화·대화 중 가장 잦은 상황부터 선택해보세요.",
            "업무에 바로 필요한 말이 무엇인지 좁혀보세요. {dong}의 {service} 안내에서 시작할 수 있어요.",
            "시간이 부족해도 목표를 구체적으로 정하면 수업을 선택하기 쉬워집니다. {dong}에서 비교해보세요.",
        ],
        "steps": [
            ("자주 쓰는 업무 상황", "회의·전화·고객 대응 중 필요한 상황을 골라보세요."),
            ("가까운 사용 일정", "출장·발표·면접 등 다가오는 일정을 알려주세요."),
            ("가능한 수업 시간", "업무 일정을 고려해 수업 방식을 비교해보세요."),
        ],
    },
    "exam": {
        "label": "시험영어 · 목표와 일정 중심",
        "cta": "시험영어 상담하기",
        "guide": "시험영어는 목표와 남은 시간을 먼저 확인합니다.",
        "hooks": [
            "시험영어, 목표 점수와 일정에 맞게 준비하세요.",
            "시험까지 남은 시간부터 살펴보고 준비 순서를 정해보세요.",
            "목표 점수와 지금 어려운 영역을 나누어 확인해보세요.",
            "시험 종류가 정해졌다면 필요한 영역부터 비교해보세요.",
            "모든 문제를 같은 비중으로 공부하기보다 목표부터 정해보세요.",
            "시험일이 가까울수록 지금 필요한 공부부터 추려보세요.",
            "첫 응시라도 괜찮습니다. 시험 구성과 목표부터 살펴보세요.",
            "현재 수준과 제출 일정에 맞는 시험 준비 방향을 찾아보세요.",
        ],
        "copies": [
            "{dong}에서 {service}를 알아본다면 목표 점수·시험일·어려운 영역을 먼저 정리해보세요.",
            "시험을 처음 준비한다면 출제 영역과 일정부터 살펴보세요. {dong}의 {service} 안내를 참고할 수 있어요.",
            "{dong}의 {service} 수업을 비교할 때는 시험일까지 가능한 학습 시간도 함께 확인해보세요.",
            "최근 성적이 없어도 괜찮아요. {dong}에서 {service}의 시험 구성부터 차근차근 살펴보세요.",
            "{dong}에서 시험 준비를 시작하려면 목표와 현재 어려운 부분을 분리해보세요. {service} 방향을 안내합니다.",
            "점수 목표와 제출 마감이 다르면 준비 순서도 달라집니다. {dong}의 {service}를 비교해보세요.",
            "{dong} {service}를 찾고 있다면 듣기·읽기·말하기·쓰기 중 필요한 영역부터 살펴보세요.",
            "시험 준비가 막막하다면 가까운 일정과 공부 가능한 시간부터 정해보세요. {dong} {service} 안내를 확인해보세요.",
        ],
        "steps": [
            ("목표 점수 또는 등급", "목표가 정해지지 않았다면 응시 목적부터 이야기해요."),
            ("시험·제출 일정", "시험일이나 제출 마감 날짜를 먼저 확인합니다."),
            ("어려운 시험 영역", "독해·듣기·말하기·쓰기에서 필요한 부분을 골라보세요."),
        ],
    },
    "campus": {
        "label": "대학생 영어 · 발표와 학교생활",
        "cta": "대학생 영어 상담하기",
        "guide": "대학생 영어, 어떤 일정부터 준비할까요?",
        "hooks": [
            "대학생 영어, 다가오는 발표와 수업부터 준비해보세요.",
            "교환학생·세미나·발표 중 가까운 목표부터 시작하세요.",
            "전공 영어가 어렵다면 필요한 표현부터 나누어 살펴보세요.",
            "학교생활에서 영어가 필요한 순간부터 준비해보세요.",
            "영어 발표가 걱정된다면 짧은 설명부터 연습해보세요.",
            "대학에서 쓸 영어는 목표에 따라 준비 순서가 달라집니다.",
            "영어로 의견을 전해야 한다면 핵심 문장부터 시작해보세요.",
            "대학생활과 진로 목표에 맞는 영어 공부를 찾아보세요.",
        ],
        "copies": [
            "{dong}에서 {service}를 찾는다면 전공 수업·발표·세미나 중 가까운 일정부터 생각해보세요.",
            "학교 과제나 교환학생 계획이 있다면 필요한 영어가 달라집니다. {dong}의 {service}를 살펴보세요.",
            "{dong}에서 대학생 영어를 준비한다면 발표 주제와 실제 사용 상황부터 정리해보세요.",
            "{service}를 선택할 때는 단어 암기뿐 아니라 설명·질문 답하기까지 필요한지 살펴보세요. {dong}에서 비교해보세요.",
            "{dong}에서 영어를 다시 시작한다면 수업·면접·교환학생 중 가장 가까운 목표부터 정해보세요.",
            "학업과 진로를 모두 준비할 때는 첫 번째로 필요한 영어를 좁혀보세요. {dong} {service} 안내를 참고하세요.",
            "{dong} {service} 안내에서 발표·토론·질문 대응에 필요한 수업 방식을 살펴보세요.",
            "영어가 필요한 일정이 분명할수록 준비 내용도 달라집니다. {dong}에서 현재 목표에 맞춰 알아보세요.",
        ],
        "steps": [
            ("가장 가까운 학교 일정", "발표·세미나·전공 수업에서 필요한 영어를 골라요."),
            ("학교 밖 영어 목표", "교환학생·인턴·면접 일정이 있는지 살펴봐요."),
            ("가능한 준비 시간", "과제와 수업 시간표에 맞는 방식을 비교해요."),
        ],
    },
    "jobseeker": {
        "label": "취준생 영어 · 면접과 자기소개",
        "cta": "영어면접 상담하기",
        "guide": "영어면접은 실제 지원 상황부터 살펴보세요.",
        "hooks": [
            "영어면접, 내 경험을 쉬운 문장으로 전하는 것부터 시작하세요.",
            "취업 영어가 고민된다면 자기소개 첫 문장부터 준비해보세요.",
            "지원 직무에 맞춰 필요한 영어 질문부터 골라보세요.",
            "외운 답변보다 내 이야기를 영어로 말할 수 있게 준비하세요.",
            "영어 질문 앞에서 멈춘다면 짧게 답하는 표현부터 시작해보세요.",
            "자기소개와 지원 동기, 가장 가까운 면접 목표부터 살펴보세요.",
            "취준생 영어회화, 제출과 면접 일정에 맞춰 준비해보세요.",
            "영어면접이 처음이라면 자주 나오는 질문부터 알아보세요.",
        ],
        "copies": [
            "{dong}에서 {service}를 알아본다면 지원 직무·면접 일정·자기소개부터 정리해보세요.",
            "영어로 경력을 설명하기 어렵나요? {dong}에서 {service}의 질문 대응과 말하기 방식을 살펴보세요.",
            "{dong} {service} 안내에서는 면접에서 자주 받는 질문과 내 경험을 연결하는 방법을 비교할 수 있어요.",
            "지원 동기와 직무 경험을 영어로 말해야 한다면 쉬운 답변 구조부터 준비해보세요. {dong}에서 시작할 수 있어요.",
            "{dong}에서 영어면접을 준비한다면 가까운 일정을 기준으로 첫 답변부터 차근차근 연습해보세요.",
            "취업 영어를 한꺼번에 준비하기보다 지원 분야에 필요한 질문부터 정리해보세요. {dong}의 {service}를 확인하세요.",
            "{dong}의 {service}를 비교할 때는 직접 답변해보고 피드백을 받을 수 있는지 살펴보세요.",
            "영어면접 준비에는 나만의 사례가 중요합니다. {dong}에서 자기소개와 답변 방식을 먼저 살펴보세요.",
        ],
        "steps": [
            ("지원 직무와 회사", "어떤 업무로 지원하는지 알려주세요."),
            ("가까운 면접 일정", "면접일·지원 마감을 기준으로 범위를 정합니다."),
            ("어려운 영어 질문", "자기소개·경험·지원 동기 중 필요한 부분을 골라요."),
        ],
    },
    "adult": {
        "label": "성인 영어회화 · 일상과 목표 중심",
        "cta": "영어회화 상담하기",
        "guide": "성인 영어회화, 이런 부분부터 살펴보세요.",
        "hooks": [
            "성인 영어회화, 필요한 표현부터 편하게 시작하세요.",
            "오래 쉬었던 영어도 가까운 생활 표현부터 다시 시작할 수 있어요.",
            "여행·생활·자기계발 중 나에게 맞는 회화를 골라보세요.",
            "영어로 대화하고 싶은 순간부터 연습 내용을 정해보세요.",
            "어떤 표현이 필요한지 모르겠다면 일상에서 자주 쓰는 말부터 알아보세요.",
            "영어 공부를 다시 시작한다면 부담 없는 목표부터 정해보세요.",
            "짧은 문장으로 대화를 이어가는 것부터 시작해보세요.",
            "내 생활에 맞는 영어회화, 쉬운 주제부터 골라보세요.",
        ],
        "copies": [
            "{dong}에서 {service}를 알아본다면 여행·일상에서 가장 자주 쓰는 상황부터 정해보세요.",
            "영어를 오래 쉬었어도 괜찮습니다. {dong}의 {service} 안내에서 편한 시작점을 찾아보세요.",
            "{dong}에서 영어회화를 찾는다면 목표와 사용할 시간을 함께 생각해보세요.",
            "막연한 회화보다 쓰고 싶은 표현을 한두 개 정하는 것이 좋아요. {dong}의 {service}를 살펴보세요.",
            "일상에서 영어를 쓸 일이 있나요? {dong}에서 원하는 수업 방향부터 찾아보세요.",
            "{dong}의 {service} 수업을 비교할 때 내 수준과 가능한 시간대를 먼저 정리해보세요.",
            "여행·취미·생활 가운데 가까운 상황을 골라보세요. {dong} {service} 안내에서 시작할 수 있어요.",
            "영어 문장이 바로 떠오르지 않아도 괜찮아요. {dong}에서 쉬운 표현부터 준비해보세요.",
        ],
        "steps": [
            ("영어를 쓰고 싶은 상황", "여행·일상·취미 등 목표를 하나 골라보세요."),
            ("지금 편한 영어 수준", "쉬운 인사부터 대화 경험까지 편하게 알려주세요."),
            ("가능한 수업 시간", "생활 일정에 맞는 수업 방식을 살펴보세요."),
        ],
    },
}


def group_for(intent: str) -> str:
    if intent in BEGINNER:
        return "beginner"
    if intent in STUDENT:
        return "student"
    if intent in WORKER:
        return "worker"
    if intent in EXAM:
        return "exam"
    if intent == "univ-conv":
        return "campus"
    if intent == "jobseeker-conv":
        return "jobseeker"
    return "adult"


def choose(items: list, loc: dict, intent: str, salt: str):
    key = f'{loc["slug"]}|{intent}|hero-v2|{salt}'
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return items[int.from_bytes(digest[:8], "big") % len(items)]


def render_hero(loc: dict, intent: str, existing_h1: str) -> str:
    """Use existing geographic H1 for SEO; rotate visible subline and guide only."""
    config = COPY[group_for(intent)]
    dong = loc["dong"]
    service = loc["service"]
    subline = choose(config["hooks"], loc, intent, "hook")
    supporting = choose(config["copies"], loc, intent, "copy").format(
        dong=dong, service=service
    )
    cta = config["cta"]
    guide_title = config["guide"]
    steps = config["steps"]
    # Rotate guide first step without misrepresenting the service.
    offset = int.from_bytes(
        hashlib.sha256((loc["slug"] + "|" + intent + "|guide-v2").encode()).digest()[:2],
        "big",
    ) % len(steps)
    steps = steps[offset:] + steps[:offset]
    e = lambda value: html.escape(str(value), quote=True)
    cards = "".join(
        f'<article><strong>{e(title)}</strong><p>{e(detail)}</p></article>'
        for title, detail in steps
    )
    return (
        '<section class="hero simple-hero" data-hero-copy="audience-v2">'
        '<div class="wrap simple-hero-inner">'
        f'<p class="eyebrow">ENGLISH PT · {e(config["label"])}</p>'
        f'<h1>{e(existing_h1)}</h1>'
        f'<p class="hero-subline">{e(subline)}</p>'
        f'<p class="hero-copy">{e(supporting)}</p>'
        '<div class="hero-actions">'
        f'<a class="btn primary" href="#consultation-preview">{e(cta)}</a>'
        '<a class="btn ghost" href="#detail">수업 안내 보기</a>'
        '</div></div></section>'
        '<section class="section hero-next-step" aria-label="상담 전에 살펴볼 내용">'
        '<div class="wrap"><p class="kicker">시작 전에 살펴볼 세 가지</p>'
        f'<h2>{e(guide_title)}</h2>'
        f'<div class="hero-next-grid">{cards}</div></div></section>'
    )


def audit_copy(loc: dict, intent: str, existing_h1: str) -> list[str]:
    rendered = render_hero(loc, intent, existing_h1)
    problems = []
    if rendered.count('href="#consultation-preview"') != 1:
        problems.append("consultation_cta")
    if rendered.count('class="hero-next-grid"') != 1:
        problems.append("guide_cards")
    if rendered.count("<article>") != 3:
        problems.append("guide_card_count")
    if rendered.count("<h1>") != 1:
        problems.append("h1_count")
    if intent in BEGINNER:
        for forbidden in ("훈련", "진단", "실전", "교정", "병목", "재점검", "재검증"):
            if forbidden in rendered:
                problems.append(f"pressure_term:{forbidden}")
    return problems
