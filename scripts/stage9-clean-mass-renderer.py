#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render Stage 9 mass pages from audited Gold content, not Stage 5 lexical noise."""
from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://englishpt.kr"
PHONE = "010-5006-8027"
PHONE_HREF = "tel:+821050068027"

SERVICE_ORDER = [
    "elem-tutor","mid-conv","high-conv","univ-conv",
    "jobseeker-conv","biz-business-conv","housewife-conv",
]
EXAM_ORDER = ["toeic","toeic-speaking","opic","ielts","duolingo","toefl"]
VARIATIONS = ["scene","deadline","error","use","reuse"]

EMAILJS_TAG = '<script defer src="https://cdn.jsdelivr.net/npm/@emailjs/browser@4/dist/email.min.js"></script>'
LIVE_FORM = '''<form id="pilotForm" class="lead-form">
<label>이름 <span>*</span><input name="name" autocomplete="name" required></label>
<label>연락처 <span>*</span><input name="phone" inputmode="tel" autocomplete="tel" placeholder="010-0000-0000" required></label>
<label class="full">가장 가까운 일정<input name="deadline" placeholder="시험·발표·면접·사용 일정"></label>
<label class="full">가장 막히는 장면<textarea name="difficulty" rows="3" placeholder="최근 어려웠던 문제·응답·상황"></textarea></label>
<label class="privacy-check"><input name="consent" type="checkbox" required><span>상담을 위한 개인정보 수집·이용에 동의합니다.</span></label>
<div class="submit-row"><button class="btn primary" type="submit">무료 PT 진단 신청 →</button><a class="btn phone" href="tel:+821050068027">전화 010-5006-8027</a></div>
<p class="pilot-status" aria-live="polite"></p>
</form>'''

MASS_SLOTS = [
    [
        "{dong}에서 {service}를 비교할 때는 광고 문구보다 다음에 영어를 실제로 써야 하는 장면과 날짜를 먼저 정리하는 편이 좋습니다. 목표가 선명하면 지금 하지 않아도 되는 범위도 함께 줄일 수 있습니다.",
        "{service} 선택은 과정 이름보다 다음 일정에서 무엇을 해야 하는지부터 시작합니다. {dong}에서 수업을 알아보더라도 시험·발표·면접·대화처럼 실제 결과가 생기는 장면에 따라 우선순위는 달라집니다.",
        "{dong}에서 같은 {service}를 찾더라도 필요한 영어는 서로 다를 수 있습니다. 가장 가까운 일정과 그때 해야 하는 행동을 한 문장으로 정하면 상담에서 확인할 항목도 구체적으로 바뀝니다.",
        "검색 결과를 비교할 때는 {dong}이라는 지역명보다 현재 목표와 다음 사용 장면을 먼저 봅니다. {service}가 지금 목적에 직접 연결되는지 확인한 뒤 학습 범위를 정하는 편이 안전합니다.",
    ],
    [
        "현재 상태는 점수 하나나 막연한 수준 표현으로만 판단하지 않습니다. 최근 자료에서 혼자 가능한 부분, 짧은 도움이 있으면 수정되는 부분, 조건이 바뀌면 다시 흔들리는 부분을 나눠 보는 것이 출발점입니다.",
        "잘하는 영역과 어려운 영역을 동시에 확인해야 불필요한 반복을 줄일 수 있습니다. 이미 혼자 안정적으로 되는 부분은 유지 확인으로 넘기고 실제 결과를 막는 부분에 시간을 더 씁니다.",
        "최근 한 번의 성공이나 실패만으로 방향을 정하지 않습니다. 비슷한 장면이 다시 나타났을 때 같은 기준을 사용할 수 있는지, 도움의 양을 줄여도 처리할 수 있는지를 함께 확인합니다.",
        "현재 수준을 확인할 때는 무엇을 모르는지뿐 아니라 어디까지 혼자 되는지도 기록합니다. 이 차이를 알아야 처음부터 전 범위를 다시 시작하지 않고 필요한 지점에서 이어갈 수 있습니다.",
    ],
    [
        "일정은 이상적인 공부량이 아니라 실제로 지킬 수 있는 횟수와 시간을 기준으로 잡습니다. 주중과 주말의 가능 시간이 다르면 같은 과제량을 강요하지 않고 다음 수업 전 다시 볼 최소 단위를 먼저 정합니다.",
        "남은 기간을 볼 때는 달력의 날짜보다 실제 연습 가능한 횟수를 함께 계산합니다. 시간이 촉박할수록 새 범위를 넓히기보다 이미 확인한 병목을 실제 조건에서 줄이는 쪽에 비중을 둡니다.",
        "계획이 밀렸을 때 누적된 과제를 한꺼번에 따라잡는 방식은 피합니다. 마지막으로 안정된 지점에서 다시 시작하고 가까운 일정에 직접 필요한 행동부터 재배치합니다.",
        "학습량은 많을수록 좋다고 가정하지 않습니다. 실제 생활 안에서 반복 가능한 분량을 먼저 만들고, 유지되는 것이 확인되면 그다음 범위를 늘리는 방식으로 조정합니다.",
    ],
    [
        "상담 전에는 자료를 많이 준비할 필요가 없습니다. 최근 문제·답변·녹음·글 가운데 하나와 가장 막힌 장면, 다음 일정을 함께 알려주면 현재 우선순위를 훨씬 빠르게 좁힐 수 있습니다.",
        "최근 사용한 자료 하나만 있어도 충분한 경우가 많습니다. 정답 여부보다 왜 그렇게 선택했는지, 시간이 충분하면 달라지는지, 도움 뒤 다시 했을 때 무엇이 남는지를 확인합니다.",
        "현재 상태를 설명하기 어렵다면 최근에 실제로 멈춘 장면 하나를 가져오면 됩니다. 그 장면에서 첫 시도와 도움 뒤 수정, 새 조건에서의 재사용을 나누면 필요한 훈련을 구체화할 수 있습니다.",
        "상담용 자료는 완벽하게 정리할 필요가 없습니다. 최근 결과 한 개와 '여기에서 계속 막힌다'고 느낀 지점만 있어도 어떤 진단부터 할지 정하는 데 도움이 됩니다.",
    ],
    [
        "설명을 들은 직후 되는 것과 혼자 다시 되는 것은 구분합니다. 같은 문제를 반복해 맞히는 데서 끝내지 않고 질문·자료·순서를 바꿔도 같은 판단을 다시 할 수 있는지 확인합니다.",
        "한 번 잘한 결과를 그대로 변화로 보지 않습니다. 힌트가 줄어들었을 때도 수정할 수 있는지, 비슷하지만 다른 문제나 질문에서도 같은 기준이 남는지를 다시 봅니다.",
        "재사용 확인에서는 난도를 갑자기 높이지 않습니다. 문장이나 질문 표현처럼 한 조건씩 바꿔 어디에서 다시 흔들리는지를 찾고 그 지점을 다음 연습의 시작점으로 남깁니다.",
        "익숙한 자료에서 성공했다면 다음에는 조건 하나만 바꿔봅니다. 새 문제에서도 기준이 유지되면 범위를 넓히고, 다시 막히면 어떤 단서에 의존했는지부터 확인합니다.",
    ],
    [
        "피드백은 '잘했다/부족하다'보다 다음에 무엇을 다시 확인할지 남기는 형태가 유용합니다. 처음 시도, 도움 뒤 변화, 새 조건에서의 결과를 짧게 기록하면 다음 수업의 출발점이 분명해집니다.",
        "수업 기록에는 진도만 남기지 않습니다. 혼자 된 부분과 끝까지 도움이 필요했던 부분, 다음에 조건을 바꿔 다시 볼 항목을 구분하면 변화 여부를 더 구체적으로 확인할 수 있습니다.",
        "피드백의 목적은 평가 문장을 길게 남기는 것이 아니라 다음 행동을 정하는 데 있습니다. 어떤 기준을 다시 적용할지 한두 가지로 줄여야 실제 복습으로 연결하기 쉽습니다.",
        "다음 수업에서 사용할 수 없는 피드백은 길어도 활용하기 어렵습니다. 반복 오류와 수정 기준, 다음 재확인 장면을 짧게 남겨 실제 행동으로 이어지게 합니다.",
    ],
    [
        "비용을 비교할 때는 월 총액 하나만 보지 않습니다. 주당 횟수, 한 회 시간, 첨삭·녹음·과제 피드백 범위, 방문·온라인 방식과 다음 일정까지의 운영 기간을 함께 확인해야 실제 구성이 보입니다.",
        "수업료는 횟수와 시간만으로 판단하기 어렵습니다. 진단, 피드백, 재점검, 자료 확인이 어디까지 포함되는지 함께 보면 같은 횟수라도 운영 방식의 차이를 비교하기 쉽습니다.",
        "가격을 보기 전에 수업 안에서 무엇을 확인하고 수업 밖에서 어떤 피드백이 이어지는지 묻는 편이 좋습니다. 필요한 관리 범위가 다르면 적절한 횟수와 방식도 달라질 수 있습니다.",
        "비용과 수업 방식은 현재 목표와 일정이 정해진 뒤 비교하는 편이 정확합니다. 가까운 결과에 필요한 피드백 범위가 보이면 과도한 횟수나 불필요한 구성도 줄일 수 있습니다.",
    ],
    [
        "방문과 온라인 중 어느 방식이 무조건 낫다고 정하지 않습니다. 현재 자료를 공유하기 쉬운지, 말하기·쓰기 피드백이 필요한지, 일정 안에서 실제 반복을 유지할 수 있는지를 기준으로 비교합니다.",
        "수업 방식은 지역명보다 실제 사용 환경과 일정에 맞춰 정합니다. 이동 시간, 자료 공유, 녹음·첨삭 여부처럼 확인 가능한 조건을 놓고 방문·온라인의 장단점을 비교할 수 있습니다.",
        "같은 {service}라도 필요한 상호작용이 다르면 적합한 방식도 달라질 수 있습니다. 현재 장면을 재현하고 피드백을 다시 적용하기 쉬운 쪽을 우선해서 봅니다.",
        "형식 자체보다 반복 가능성이 중요합니다. 방문이든 온라인이든 수업 뒤 혼자 다시 확인할 시간이 확보되고 다음 피드백으로 연결되는지를 기준으로 판단합니다.",
    ],
    [
        "모든 문의를 같은 과정으로 연결하지 않습니다. 현재 목적이 다른 시험이나 학교 일정, 면접, 일상 회화에 더 직접적으로 연결된다면 그 경로를 먼저 비교하는 편이 낫습니다.",
        "{service}가 익숙한 이름이라고 해서 항상 가장 직접적인 선택은 아닙니다. 제출처 요구조건과 실제 사용 목적이 다른 과정에 더 가깝다면 준비 경로를 바꿀 수 있습니다.",
        "과정 선택에는 '하지 않아도 되는 것'을 정하는 기준도 필요합니다. 현재 목표와 직접 연결되지 않는 범위는 뒤로 미루고 다른 경로가 더 가까운 경우에는 함께 비교합니다.",
        "지금 필요한 결과와 {service}의 훈련 방식이 맞지 않으면 억지로 연결하지 않습니다. 다른 시험이나 학습 방식이 더 직접적인 경우 그 이유를 먼저 확인하는 편이 좋습니다.",
    ],
    [
        "복습은 같은 문제를 여러 번 보는 일로만 잡지 않습니다. 짧은 간격을 두고 다른 자료에서 같은 기준을 다시 써보는 방식으로 실제 재사용 범위를 확인합니다.",
        "혼자 공부할 때는 수업 내용을 전부 다시 보는 대신 다음에 사용할 기준 한두 개를 정합니다. 새 문제나 질문에 적용해보고 안 되는 조건만 다음 수업으로 가져오는 편이 효율적입니다.",
        "바쁜 주에는 최소 루틴을 따로 둡니다. 짧은 문제 한 세트, 답변 한 번, 글 한 단락처럼 다시 시작하기 쉬운 단위를 유지하면 일정이 흔들려도 학습 전체가 끊기지 않습니다.",
        "과제는 양보다 다음 수업에서 확인할 기준이 남는지가 중요합니다. 무엇을 다시 해볼지 분명하면 짧은 복습도 다음 진단 자료로 사용할 수 있습니다.",
    ],
    [
        "상담에서는 '어떤 교재를 쓰나요'보다 '다음 일정에서 무엇이 되어야 하나요'를 먼저 묻는 것이 좋습니다. 그 답이 정해지면 문제풀이·녹음·첨삭·시간 연습 중 필요한 비중을 구체화할 수 있습니다.",
        "비교 상담을 받을 때는 현재 목표, 가장 가까운 일정, 최근 막힌 장면 세 가지를 같은 기준으로 물어보세요. 설명이 달라도 이 세 항목을 기준으로 보면 과정 차이를 판단하기 쉽습니다.",
        "등록 여부보다 먼저 상담에서 무엇을 확인할 수 있는지를 봅니다. 현재 상태와 우선순위, 수업 흐름, 재점검 방식이 구체적으로 설명되는지 비교하면 결정에 필요한 정보가 늘어납니다.",
        "상담의 목적은 바로 결정하는 것이 아니라 현재 기준을 선명하게 만드는 데 둘 수 있습니다. 여러 곳을 비교하더라도 같은 질문으로 확인하면 자신에게 필요한 구성의 차이를 보기 쉽습니다.",
    ],
    [
        "{jurisdiction} {dong}이라는 위치 정보는 수업 가능 지역을 구분하기 위한 기준으로 사용합니다. 지역명만으로 학습 성향이나 생활 패턴을 임의로 가정하지 않고 실제 목표·일정·현재 자료를 중심으로 판단합니다.",
        "이 페이지에서 {dong}이라는 지역명은 서비스 범위를 찾기 쉽게 구분하기 위한 정보입니다. 학습자의 수준과 필요한 방식은 지역이 아니라 최근 수행과 다음 일정으로 확인합니다.",
        "{dong} 지역 페이지라도 내용의 중심은 지역에 대한 추측이 아니라 실제 영어 목표입니다. 위치는 수업 가능 범위를 설명하고 학습 계획은 개인의 자료·일정·사용 장면을 기준으로 정합니다.",
        "지역별 페이지를 나누는 이유는 {dong}에서 과정을 찾는 사람이 자신의 선택지를 쉽게 확인하도록 하기 위해서입니다. 수업 방향은 지역 특성이라는 가정 대신 확인 가능한 학습 정보로 결정합니다.",
    ],
]

SECTION_TITLES = [
    ["지역에서 과정을 비교할 때", "검색 결과보다 먼저 확인할 것", "현재 목표를 좁히는 기준", "수업 선택 전에 정리할 것"],
    ["수업과 피드백을 비교할 때", "반복과 피드백을 보는 방법", "실제 운영에서 확인할 기준", "설명 이후를 비교하는 기준"],
    ["상담 전에 마지막으로 확인할 것", "결정 전에 같은 질문으로 비교하세요", "등록보다 먼저 확인할 기준", "상담에서 확인하면 좋은 항목"],
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@lru_cache(maxsize=1)
def gold_modules():
    svc = load_module("stage9_service_gold", ROOT / "scripts" / "generate-v45-full-depth-pilot.py")
    ex = load_module("stage9_exam_gold", ROOT / "scripts" / "generate-v45-exam-pilot.py")
    return svc, ex


def esc(x: str) -> str:
    return html.escape(str(x), quote=True)


def intent_from_name(name: str) -> tuple[str, str]:
    for intent in sorted(SERVICE_ORDER + EXAM_ORDER, key=len, reverse=True):
        suffix = f"-{intent}.html"
        if name.endswith(suffix):
            return name[:-len(suffix)], intent
    raise ValueError(f"unknown mass-page filename: {name}")


def plain_h1(raw: str) -> str:
    m = re.search(r"<h1\b[^>]*>(.*?)</h1>", raw, re.S | re.I)
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""


def location_from_source(raw: str, name: str, intent: str) -> dict:
    svc, ex = gold_modules()
    h1 = plain_h1(raw)
    if intent in SERVICE_ORDER:
        service = svc.PROFILES[intent]["service_h1"]
    else:
        service = next(v["service"] for v in ex.EXAMS.values() if v["intent"] == intent)
    dong = h1[:-len(service)].strip() if h1.endswith(service) else h1.split()[0]
    m = re.search(r'<p class="eyebrow">(.*?)\s*·\s*ENGLISH PT</p>', raw, re.S)
    jurisdiction = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""
    if not jurisdiction:
        first = re.search(r'<p>([^<]{2,80}?)\s+' + re.escape(dong) + r'에서', raw)
        jurisdiction = first.group(1).strip() if first else ""
    full_name = f"{jurisdiction} {dong}".strip()
    slug, _ = intent_from_name(name)
    digest = hashlib.sha256(f"{slug}|{intent}|stage9-clean-gold-v1".encode()).hexdigest()
    variation = VARIATIONS[int(digest[:8], 16) % len(VARIATIONS)]
    return {
        "full_name": full_name,
        "jurisdiction": jurisdiction,
        "dong": dong,
        "variation": variation,
        "slug": slug,
        "service": service,
    }


@lru_cache(maxsize=None)
def service_source(intent: str):
    svc, _ = gold_modules()
    matches = sorted((ROOT / "pilot-v45-5x7").glob(f"*-{intent}.html"))
    if not matches:
        raise RuntimeError(f"missing audited service pilot for {intent}")
    return svc.extract_source(matches[0])


TOPIC_MODULES = [
    {
        "key":"goal-deadline","families":{"service","exam"},"title":"목표와 가장 가까운 일정을 먼저 맞춥니다",
        "p1":"{service}를 시작하기 전에 다음 시험·발표·면접·사용 일정 가운데 가장 가까운 날짜를 하나 정합니다. 일정이 선명해야 지금 필요한 연습과 뒤로 미뤄도 되는 범위를 나눌 수 있습니다.",
        "p2":"남은 날짜만 세지 않고 실제로 연습할 수 있는 횟수까지 함께 봅니다. 시간이 짧다면 새 범위를 넓히기보다 현재 결과를 가장 크게 흔드는 행동부터 안정시키는 편이 현실적입니다."
    },
    {
        "key":"baseline-material","families":{"service","exam"},"title":"최근 자료 하나가 가장 좋은 출발점이 될 수 있습니다",
        "p1":"점수표 전체가 없어도 최근 문제·답변·녹음·글 가운데 하나면 현재 상태를 확인할 수 있습니다. 무엇을 틀렸는지보다 어디에서 멈췄고 어떤 도움 뒤에 다시 이어졌는지를 함께 봅니다.",
        "p2":"이미 혼자 되는 부분은 유지 확인으로 넘기고 조건이 바뀌면 흔들리는 부분만 다음 연습으로 남깁니다. 이렇게 하면 처음부터 전 범위를 다시 시작하는 일을 줄일 수 있습니다."
    },
    {
        "key":"error-tags","families":{"service","exam"},"title":"오답과 막힘은 원인별로 나눠 기록합니다",
        "p1":"같은 실패처럼 보여도 지식 부족, 질문 이해, 시간 압박, 표현 회수, 답변 구조처럼 원인은 다를 수 있습니다. 원인이 다르면 다음에 반복할 연습도 달라져야 합니다.",
        "p2":"정답 설명을 길게 옮기기보다 왜 그렇게 선택했는지 한 문장, 다음에는 무엇을 확인할지 한 문장 정도로 남깁니다. 새 자료에서 같은 원인이 다시 나타나는지가 실제 재점검 기준입니다."
    },
    {
        "key":"transfer","families":{"service","exam"},"title":"같은 문제를 맞히는 것보다 새 조건에서 다시 되는지 봅니다",
        "p1":"설명을 들은 직후 맞힌 결과만으로 변화라고 판단하지 않습니다. 질문 표현·자료·순서·준비 시간 가운데 한 조건을 바꿔도 같은 기준을 사용할 수 있는지 다시 확인합니다.",
        "p2":"새 조건에서 다시 막히면 새로운 내용을 바로 추가하기보다 어떤 단서가 사라졌을 때 문제가 생겼는지부터 찾습니다. 끝까지 필요한 도움은 다음 수업의 첫 연습 항목이 됩니다."
    },
    {
        "key":"minimum-routine","families":{"service","exam"},"title":"바쁜 주에도 다시 시작하기 쉬운 최소 루틴을 둡니다",
        "p1":"매일 긴 시간을 확보하는 계획보다 중단 뒤 다시 돌아오기 쉬운 최소 단위를 정하는 편이 유지에 도움이 됩니다. 짧은 문제 세트, 답변 한 번, 글 한 단락처럼 실제로 지킬 수 있는 크기로 시작합니다.",
        "p2":"여유가 있는 날에만 분량을 추가하고 기본 루틴이 유지되는지를 먼저 봅니다. 계획이 밀렸을 때 누적 과제를 쌓기보다 마지막으로 안정된 지점에서 다시 시작합니다."
    },
    {
        "key":"feedback","families":{"service","exam"},"title":"피드백은 다음 행동을 정하는 기록이어야 합니다",
        "p1":"진도나 평가 문장만 남기지 않고 혼자 된 부분, 짧은 도움 뒤 수정된 부분, 새 조건에서 다시 볼 부분을 구분합니다. 그래야 다음 수업에서 무엇부터 확인할지 바로 이어집니다.",
        "p2":"한 번에 모든 오류를 고치려 하지 않습니다. 반복해서 나타나는 한두 가지 기준을 다음 연습의 체크포인트로 정하고 새 자료에서 실제로 줄었는지를 확인합니다."
    },
    {
        "key":"cost-scope","families":{"service","exam"},"title":"비용은 횟수보다 포함 범위를 함께 비교합니다",
        "p1":"월 총액만 비교하면 수업 구성을 알기 어렵습니다. 주당 횟수, 한 회 시간, 진단·첨삭·녹음·과제 피드백과 재점검이 어디까지 포함되는지를 함께 확인하는 편이 좋습니다.",
        "p2":"현재 목표에 필요하지 않은 관리까지 많이 포함됐다고 항상 유리한 것은 아닙니다. 가까운 일정에 직접 필요한 피드백 범위를 먼저 정하면 적절한 횟수와 방식을 비교하기 쉬워집니다."
    },
    {
        "key":"online-visit","families":{"service","exam"},"title":"방문과 온라인은 실제 반복 가능성을 기준으로 비교합니다",
        "p1":"어느 방식이 무조건 낫다고 정하지 않습니다. 자료를 공유하기 쉬운지, 말하기·쓰기 피드백이 필요한지, 이동 시간을 포함해 일정 안에서 반복을 유지할 수 있는지를 확인합니다.",
        "p2":"형식보다 수업 뒤 혼자 다시 적용할 시간이 확보되는지가 중요합니다. 방문이든 온라인이든 다음 피드백까지 실제 행동을 이어갈 수 있는 구성이 더 적합할 수 있습니다."
    },
    {
        "key":"consult-questions","families":{"service","exam"},"title":"상담에서는 같은 질문으로 여러 곳을 비교해보세요",
        "p1":"현재 목표, 가장 가까운 일정, 최근 막힌 장면 세 가지를 같은 기준으로 설명하면 과정마다 무엇을 다르게 제안하는지 비교하기 쉽습니다. 자료는 한두 개만 있어도 충분합니다.",
        "p2":"등록을 바로 결정하기보다 진단 기준, 수업 흐름, 수업 밖 피드백, 재점검 방식이 얼마나 구체적으로 설명되는지를 확인하세요. 비교 기준이 같아야 가격과 횟수의 차이도 해석하기 쉬워집니다."
    },
    {
        "key":"progress-evidence","families":{"service","exam"},"title":"변화는 느낌보다 관찰 가능한 행동으로 확인합니다",
        "p1":"정답률이나 점수도 참고하지만 그것만으로 수업 효과를 단정하지 않습니다. 첫 반응이 빨라졌는지, 필요한 힌트가 줄었는지, 근거를 설명할 수 있는지처럼 실제 행동을 함께 봅니다.",
        "p2":"한 번의 좋은 결과보다 비슷한 새 조건에서도 같은 행동이 유지되는지가 중요합니다. 안정된 항목은 반복을 줄이고 끝까지 흔들리는 항목만 다음 우선순위로 남깁니다."
    },
    {
        "key":"materials","families":{"service","exam"},"title":"교재보다 다음 행동을 반복할 수 있는 자료인지 봅니다",
        "p1":"자료가 많다고 항상 좋은 것은 아닙니다. 다음 일정에서 필요한 행동을 실제로 연습하고 결과를 다시 확인할 수 있는지에 따라 문제·녹음·글쓰기·첨삭 자료의 비중을 정합니다.",
        "p2":"새 자료를 계속 늘리기보다 이미 확인한 병목을 다른 예시에서 다시 적용할 수 있는 자료를 우선합니다. 자료 선택의 기준도 학습량이 아니라 재사용 가능성에 둡니다."
    },
    {
        "key":"priority-reset","families":{"service","exam"},"title":"일정이 바뀌면 우선순위도 다시 조정합니다",
        "p1":"처음 세운 계획을 끝까지 고정하지 않습니다. 시험·발표·면접 날짜가 가까워지거나 새로운 결과가 나오면 이미 안정된 영역의 비중은 낮추고 다음 결과에 직접 필요한 행동으로 시간을 옮깁니다.",
        "p2":"단기 일정이 끝난 뒤에는 그동안 미뤄둔 기초 항목을 다시 꺼냅니다. 이렇게 하면 한 번의 대비가 끝난 뒤 모든 계획을 처음부터 다시 세우지 않아도 됩니다."
    },
    {
        "key":"speaking-record","families":{"service","exam"},"title":"말하기는 녹음으로 첫 반응과 반복 패턴을 확인할 수 있습니다",
        "p1":"말하는 동안에는 공백, 반복 표현, 답변 길이를 스스로 정확히 느끼기 어렵습니다. 짧게 녹음해 첫 문장까지 걸린 시간과 중간에 끊긴 지점을 표시하면 수정 기준이 구체적으로 보입니다.",
        "p2":"좋은 문장을 외우는 것보다 질문을 조금 바꿔 다시 답해보는 과정이 중요합니다. 같은 구조를 다른 질문에서도 만들 수 있어야 실제 사용 범위가 넓어졌다고 보기 쉽습니다."
    },
    {
        "key":"writing-revision","families":{"service","exam"},"title":"쓰기는 첨삭을 읽는 데서 끝내지 않고 다시 써봅니다",
        "p1":"수정된 문장을 이해해도 새 주제에서 같은 오류가 반복될 수 있습니다. 논리, 문단 역할, 근거의 구체성, 표현 오류 가운데 반복되는 항목을 골라 직접 재작성합니다.",
        "p2":"재작성 뒤에는 다른 문제에서도 같은 기준을 적용합니다. 첨삭 횟수보다 스스로 수정할 수 있는 범위가 넓어지는지가 다음 학습 비중을 정하는 자료가 됩니다."
    },
    {
        "key":"reading-evidence","families":{"service","exam"},"title":"읽기는 정답보다 근거를 어디에서 찾았는지 확인합니다",
        "p1":"내용을 대략 이해했다고 해도 제한 시간 안에 핵심 근거를 찾는 과정에서 흔들릴 수 있습니다. 답을 고른 위치와 이유를 짧게 표시하면 어휘 문제인지 구조 문제인지 구분하기 쉬워집니다.",
        "p2":"같은 지문을 반복해 맞히는 것보다 새로운 지문에서 근거 찾는 순서를 다시 적용합니다. 시간이 부족한 경우에는 읽기 실력뿐 아니라 풀이 순서와 머무는 시간도 함께 기록합니다."
    },
    {
        "key":"listening-process","families":{"service","exam"},"title":"듣기는 모든 문장을 번역하기보다 놓친 정보의 종류를 봅니다",
        "p1":"듣는 동안 대략 이해했는데 답변이나 선택으로 이어지지 않는다면 핵심어, 관계, 숫자·고유명사, 질문 의도 중 어디에서 정보가 빠지는지 구분합니다.",
        "p2":"다시 들을 때는 정답을 기억하는지보다 이전에 놓친 단서를 실제로 잡는지를 확인합니다. 다른 음원에서도 같은 정보 유형을 놓치는지 보면 연습 범위를 좁힐 수 있습니다."
    },
    {
        "key":"vocab-recall","families":{"service","exam"},"title":"단어는 아는지보다 문장 안에서 다시 꺼낼 수 있는지 봅니다",
        "p1":"뜻을 보고 아는 단어와 듣거나 말할 때 바로 나오는 단어는 다를 수 있습니다. 현재 목표에 자주 필요한 표현을 문장 안에서 사용하고 며칠 뒤 다시 꺼내보는 방식으로 확인합니다.",
        "p2":"단어 목록을 무작정 늘리기보다 실제 문제·답변·글에서 반복해서 막히는 표현을 우선합니다. 이미 안정적으로 쓰는 표현은 유지 확인만 하고 새로운 표현과 혼동되는 부분에 시간을 더 씁니다."
    },
    {
        "key":"grammar-transfer","families":{"service","exam"},"title":"문법은 규칙 설명보다 새 문장에 적용되는지 확인합니다",
        "p1":"규칙을 설명할 수 있어도 말하거나 쓸 때 같은 구조를 바로 사용하지 못할 수 있습니다. 현재 필요한 문장 안에서 적용하고 주어·시제·질문 형태를 바꿔도 다시 만들 수 있는지 봅니다.",
        "p2":"모든 문법을 처음부터 다시 보는 대신 최근 오류와 실제 목표에 직접 연결되는 구조부터 다룹니다. 새 문장에서 스스로 수정할 수 있게 되면 다음 항목으로 이동합니다."
    },
    {
        "key":"alternative-path","families":{"service","exam"},"title":"현재 목적에 더 직접적인 다른 경로가 있는지도 확인합니다",
        "p1":"{service}가 익숙한 이름이라고 해서 항상 지금 목표에 가장 가까운 선택은 아닙니다. 제출처 요구조건, 학교 일정, 면접, 실제 대화처럼 결과가 다른 경우에는 다른 과정이 더 직접적일 수 있습니다.",
        "p2":"상담에서 맞지 않는 경로까지 억지로 연결하지 않는 것이 중요합니다. 지금 해야 하는 행동과 평가 방식이 다른 과정에 더 가깝다면 그 이유를 먼저 비교한 뒤 선택할 수 있습니다."
    },
    {
        "key":"locality-honesty","families":{"service","exam"},"title":"지역 정보는 서비스 범위를 구분하는 데만 사용합니다",
        "p1":"{jurisdiction} {dong}이라는 위치만으로 학습 성향이나 생활 패턴을 임의로 만들지 않습니다. 지역명은 수업 가능 범위를 찾기 쉽게 구분하고 학습 계획은 실제 자료·목표·일정을 기준으로 정합니다.",
        "p2":"같은 {dong} 안에서도 필요한 영어와 가능한 시간은 서로 다를 수 있습니다. 페이지의 지역 정보보다 상담에서 확인되는 현재 조건을 우선해 수업 방식과 비중을 조정합니다."
    },
    {
        "key":"exam-official","families":{"exam"},"title":"시험 형식과 제출 조건은 최신 공식 안내를 다시 확인합니다",
        "p1":"시험 시간, 문항 구성, 점수 체계, 접수 정책과 지원기관의 인정 기준은 바뀔 수 있습니다. 실제 응시와 제출 일정을 정하기 전에는 시험 주관기관과 제출기관의 최신 안내를 직접 확인해야 합니다.",
        "p2":"공식 정보는 공부 방향과 분리하지 않습니다. 형식이 바뀌면 실전 연습 조건도 달라질 수 있으므로 최신 구조를 확인한 뒤 현재 병목을 그 조건 안에서 다시 점검합니다."
    },
    {
        "key":"exam-simulation","families":{"exam"},"title":"시험이 가까워질수록 실제 시간 조건으로 재확인합니다",
        "p1":"마감이 가까울 때는 새로운 자료를 많이 추가하기보다 이미 정한 풀이·답변 기준이 제한 시간에서도 유지되는지를 확인합니다. 시작 순서와 멈춘 지점도 함께 기록합니다.",
        "p2":"실전 세트는 새로운 공부라기보다 재검증 자료로 사용합니다. 점수 하나보다 어느 영역에서 시간이 무너졌고 어떤 오류가 다시 나타났는지를 다음 연습에 연결합니다."
    },
    {
        "key":"exam-choice","families":{"exam"},"title":"공인시험은 제출 목적과 자신의 강점을 함께 비교합니다",
        "p1":"비슷한 영어시험이라도 요구하는 행동과 제출처가 다를 수 있습니다. 점수 이름만 보고 선택하기보다 실제 지원기관 요구조건과 자신이 상대적으로 안정적인 기능을 함께 확인합니다.",
        "p2":"시험을 바꾸는 것이 항상 답은 아니지만 현재 강점과 형식이 크게 맞지 않는다면 비교할 가치는 있습니다. 마감과 응시 가능 횟수까지 놓고 현실적인 경로를 정합니다."
    },
    {
        "key":"service-family","families":{"service"},"title":"대상별 목표와 가까운 실제 장면을 중심으로 수업을 좁힙니다",
        "p1":"{audience} 과정이라도 같은 방식으로 고정하지 않습니다. 학교 일정, 발표·면접, 업무, 생활 대화처럼 실제 사용 장면을 먼저 확인하고 그 장면에 필요한 기능을 우선합니다.",
        "p2":"연령이나 신분만으로 교재와 진도를 정하지 않습니다. 현재 혼자 가능한 범위와 다음 일정, 수업 밖에서 실제로 반복할 수 있는 시간을 함께 놓고 범위를 조정합니다."
    },
    {
        "key":"service-output","families":{"service"},"title":"회화와 과외는 실제로 꺼내 쓰는 장면까지 연결합니다",
        "p1":"설명을 이해한 것과 질문을 받았을 때 직접 말하거나 쓰는 것은 다른 행동입니다. 배운 표현과 기준을 실제 질문·발표·서술·대화에 옮겨보고 어디에서 다시 멈추는지 확인합니다.",
        "p2":"준비한 문장을 그대로 외우는 것만으로 끝내지 않습니다. 질문이나 상대가 바뀌어도 핵심을 다시 구성할 수 있도록 의미 단위와 근거를 나눠 연습합니다."
    },
]


def _topic_modules(loc: dict, intent: str, family: str, audience: str) -> list[dict]:
    pool=[m for m in TOPIC_MODULES if family in m["families"]]
    count=8
    ranked=sorted(
        pool,
        key=lambda m: hashlib.sha256(
            f'{loc["slug"]}|{intent}|{m["key"]}|stage9-topic-v2'.encode()
        ).hexdigest()
    )
    chosen=ranked[:count]
    values={
        "dong":loc["dong"],"jurisdiction":loc["jurisdiction"],
        "service":loc["service"],"audience":audience or "학습자",
    }
    return [
        {
            "key":m["key"],
            "title":m["title"].format(**values),
            "p1":m["p1"].format(**values),
            "p2":m["p2"].format(**values),
        }
        for m in chosen
    ]


def mass_context(loc: dict, intent: str, family: str, audience: str = "") -> str:
    modules=_topic_modules(loc,intent,family,audience)
    cards="".join(
        f'<article class="context-block" data-topic="{esc(m["key"])}">'
        f'<h3>{esc(m["title"])}</h3><p>{esc(m["p1"])}</p><p>{esc(m["p2"])}</p></article>'
        for m in modules
    )
    return (
        '<section class="section mass-context"><div class="wrap narrow">'
        '<p class="kicker">지역별 비교 기준</p>'
        f'<h2>{esc(loc["dong"])}에서 {esc(loc["service"])}를 비교할 때 확인할 내용</h2>'
        + cards + '</div></section>'
    )


def _select_by_seed(items: list[str], count: int, seed: str) -> list[str]:
    if len(items) <= count:
        return items
    ranked=sorted(
        enumerate(items),
        key=lambda x: hashlib.sha256(f"{seed}|{x[0]}".encode()).hexdigest()
    )
    keep={i for i,_ in ranked[:count]}
    return [item for i,item in enumerate(items) if i in keep]


def trim_gold_page(raw: str, seed: str, family: str) -> str:
    """Keep audited intent facts while varying the support modules by locality."""
    def select_items(body: str, pattern: str, keep: int, salt: str) -> str:
        items=re.findall(pattern,body,re.S)
        if not items:
            return body
        chosen=_select_by_seed(items,min(keep,len(items)),f"{seed}|{salt}")
        return "".join(chosen)

    # Situation/problem cards: two concrete scenes per locality. The intent still
    # remains explicit in hero, goal, priority and deep sections.
    sm=re.search(
        r'(<p class="kicker">(?:실제 장면|실제 막힘)</p>.*?<div class="grid4">)(.*?)(</div>)',
        raw,re.S
    )
    if sm:
        body=select_items(sm.group(2),r'<article class="card">.*?</article>',2,"scenes")
        raw=raw[:sm.start()]+sm.group(1)+body+sm.group(3)+raw[sm.end():]

    # Priority bullets: keep three relevant priorities.
    pm=re.search(
        r'(<p class="kicker">우선순위</p>.*?<ul>)(.*?)(</ul>)',
        raw,re.S
    )
    if pm:
        body=select_items(pm.group(2),r'<li>.*?</li>',3,"priority")
        raw=raw[:pm.start()]+pm.group(1)+body+pm.group(3)+raw[pm.end():]

    # Training flow: retain three steps, selected in source order.
    fm=re.search(
        r'(<p class="kicker">수업 흐름</p>.*?<ol class="steps">)(.*?)(</ol>)',
        raw,re.S
    )
    if fm:
        body=select_items(fm.group(2),r'<li>.*?</li>',3,"flow")
        raw=raw[:fm.start()]+fm.group(1)+body+fm.group(3)+raw[fm.end():]

    # Proof points: three visible evidence points.
    pr=re.search(r'(<ul class="proofs">)(.*?)(</ul>)',raw,re.S)
    if pr:
        body=select_items(pr.group(2),r'<li>.*?</li>',3,"proof")
        raw=raw[:pr.start()]+pr.group(1)+body+pr.group(3)+raw[pr.end():]

    # Feedback: two examples are enough to demonstrate the record format.
    fb=re.search(
        r'(<p class="kicker">피드백 예시</p>.*?<div class="grid4">)(.*?)(</div>)',
        raw,re.S
    )
    if fb:
        body=select_items(fb.group(2),r'<article class="card">.*?</article>',2,"feedback")
        raw=raw[:fb.start()]+fb.group(1)+body+fb.group(3)+raw[fb.end():]

    # Intent-specific deep guide: two cards from the audited Gold pool.
    dm=re.search(
        r'(<p class="kicker">더 깊게 보기</p>.*?<div class="grid4">)(.*?)(</div>)',
        raw,re.S
    )
    if dm:
        body=select_items(dm.group(2),r'<article class="card">.*?</article>',2,"deep")
        raw=raw[:dm.start()]+dm.group(1)+body+dm.group(3)+raw[dm.end():]

    # FAQ: three questions per locality from the audited pool.
    fq=re.search(r'(<div class="faq">)(.*?)(</div>)',raw,re.S)
    if fq:
        body=select_items(fq.group(2),r'<details>.*?</details>',3,"faq")
        raw=raw[:fq.start()]+fq.group(1)+body+fq.group(3)+raw[fq.end():]

    # Opening detail: keep the core intent question plus a locality-specific
    # subset of explanatory paragraphs instead of repeating the whole Gold intro.
    det=re.search(
        r'(<section id="detail" class="section"><div class="wrap narrow"><p class="kicker">.*?</p><h2>.*?</h2>)(.*?)(</div></section>)',
        raw,re.S
    )
    if det:
        ps=re.findall(r'<p>.*?</p>',det.group(2),re.S)
        if ps:
            keep=3 if family=="service" else 2
            body=select_items("".join(ps),r'<p>.*?</p>',keep,"detail")
            raw=raw[:det.start()]+det.group(1)+body+det.group(3)+raw[det.end():]

    # Process/fit section: two concise paragraphs are sufficient; the topic
    # modules carry the broader comparison questions.
    fit=re.search(
        r'(<section class="section"><div class="wrap narrow"><p class="kicker">(?:과정 선택|시험 선택)</p>.*?<h2>.*?</h2>)(.*?)(</div></section>)',
        raw,re.S
    )
    if fit:
        ps=re.findall(r'<p>.*?</p>',fit.group(2),re.S)
        if ps:
            body=select_items("".join(ps),r'<p>.*?</p>',min(2,len(ps)),"fit")
            raw=raw[:fit.start()]+fit.group(1)+body+fit.group(3)+raw[fit.end():]

    # Service Gold pages contain a long generic diagnosis section. Keep its
    # heading + first and last explanatory paragraph only; topic modules carry
    # the locality-specific decision support.
    if family=="service":
        dg=re.search(
            r'(<p class="kicker">막히는 이유</p><h2>.*?</h2>)(.*?)(</div></section>)',
            raw,re.S
        )
        if dg:
            ps=re.findall(r'<p>.*?</p>',dg.group(2),re.S)
            chosen=[]
            if ps:
                chosen.append(ps[0])
                if len(ps)>1: chosen.append(ps[-1])
            raw=raw[:dg.start()]+dg.group(1)+"".join(chosen)+dg.group(3)+raw[dg.end():]

    # Exam Gold has a long generic learning-frame section. Diverse topic modules
    # replace it; exam-specific deep guide and official-information sections remain.
    if family=="exam":
        raw=re.sub(
            r'<section class="section"><div class="wrap narrow"><p class="kicker">학습 프레임</p>.*?</section>',
            '',
            raw,count=1,flags=re.S,
        )

    return raw


def all_related(loc: dict, current_intent: str) -> str:
    svc, ex = gold_modules()
    links = []
    for intent in SERVICE_ORDER:
        if intent == current_intent:
            continue
        label = f'{loc["dong"]} {svc.PROFILES[intent]["service_h1"]}'
        links.append(f'<a href="/{loc["slug"]}-{intent}.html">{esc(label)}</a>')
    for intent in EXAM_ORDER:
        if intent == current_intent:
            continue
        exam = next(v for v in ex.EXAMS.values() if v["intent"] == intent)
        label = f'{loc["dong"]} {exam["service"]}'
        links.append(f'<a href="/{loc["slug"]}-{intent}.html">{esc(label)}</a>')
    return (
        '<section class="section related"><div class="wrap">'
        '<p class="kicker">관련 과정</p>'
        f'<h2>{esc(loc["dong"])}에서 다른 영어 목표도 비교해보세요</h2>'
        '<div class="links">' + "".join(links) + '</div></div></section>'
    )


def add_breadcrumb_schema(raw: str, h1: str, canonical: str) -> tuple[str, bool]:
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)
    if not m:
        return raw, False
    try:
        data = json.loads(m.group(1))
        graph = data.get("@graph")
        if not isinstance(graph, list):
            return raw, False
        if not any(isinstance(x,dict) and x.get("@type")=="BreadcrumbList" for x in graph):
            graph.append({
                "@type":"BreadcrumbList",
                "itemListElement":[
                    {"@type":"ListItem","position":1,"name":"잉글리시PT","item":BASE_URL+"/englishpt.html"},
                    {"@type":"ListItem","position":2,"name":h1,"item":canonical},
                ],
            })
        rep = '<script type="application/ld+json">' + json.dumps(data,ensure_ascii=False,separators=(",",":")) + '</script>'
        return raw[:m.start()] + rep + raw[m.end():], True
    except Exception:
        return raw, False


def productionize(raw: str, loc: dict, intent: str, family: str) -> tuple[str,list[str]]:
    problems=[]
    raw = trim_gold_page(raw, loc["slug"] + "|" + intent, family)
    h1 = plain_h1(raw)
    canonical = f'{BASE_URL}/{loc["slug"]}-{intent}.html'
    theme = (
        gold_modules()[0].PROFILES[intent]["theme"] + " intent-audience"
        if family=="service" else "theme-test intent-test"
    )

    raw = re.sub(
        r'<meta name="robots" content="noindex,nofollow">',
        '<meta name="robots" content="index,follow">',
        raw,
        count=1,
    )
    raw = raw.replace('href="../englishpt.html"','href="/englishpt.html"')
    raw = raw.replace('href="pilot.css"','href="pilot.css"')
    raw = raw.replace('href="../pilot-v45-5x7/pilot.css"','href="pilot.css"')
    raw = raw.replace('src="pilot.js"','src="pilot.js"')
    raw = raw.replace('src="../pilot-v45-5x7/pilot.js"','src="pilot.js"')
    raw = re.sub(
        r'<body class="[^"]*"[^>]*data-production-deploy="false">',
        f'<body class="{theme}" data-production-deploy="true" data-stage9-clean="true">',
        raw,
        count=1,
    )
    raw = re.sub(
        r'<header><div class="wrap header"><a href="/englishpt.html" class="brand">ENGLISH PT</a><span>.*?</span></div></header>',
        '<header><div class="wrap header"><a href="/englishpt.html" class="brand">ENGLISH PT</a><span>지역별 맞춤 영어 안내</span></div></header>',
        raw, count=1, flags=re.S,
    )

    if EMAILJS_TAG not in raw:
        raw = raw.replace('<script defer src="pilot.js"></script>', EMAILJS_TAG+'<script defer src="pilot.js"></script>',1)

    raw, n = re.subn(r'<form id="pilotForm">.*?</form>', LIVE_FORM, raw, count=1, flags=re.S)
    if n!=1:
        problems.append("live_form")

    # Remove only preview-only explanations, never substantive content.
    raw = re.sub(r'<p>[^<]*(?:검수용|파일럿)[^<]*(?:전송|production|미배포)[^<]*</p>', '', raw, flags=re.I)
    raw = re.sub(r'<p>[^<]*(?:production 미배포|검수용 페이지)[^<]*</p>', '', raw, flags=re.I)

    # Replace family-limited related links with the full 13-intent local cluster.
    raw = re.sub(r'<section class="section related">.*?</section>', all_related(loc,intent), raw, count=1, flags=re.S)
    related_marker = '<section class="section related">'
    ctx = mass_context(loc,intent,family, gold_modules()[0].PROFILES[intent]["audience"] if family=="service" else "")
    if related_marker in raw:
        raw = raw.replace(related_marker, ctx + related_marker, 1)
    else:
        raw = raw.replace('<section id="consultation-preview"', ctx+'<section id="consultation-preview"',1)

    crumb=(
        '<div class="breadcrumb wrap" aria-label="현재 위치">'
        '<a href="/englishpt.html">잉글리시PT</a><span aria-hidden="true">/</span>'
        f'<strong>{esc(h1)}</strong></div>'
    )
    raw = raw.replace("<main>","<main>"+crumb,1)

    # Production footer and final wording.
    raw = re.sub(
        r'<footer><div class="wrap"><strong>ENGLISH PT</strong><p>.*?</p></div></footer>',
        f'<footer><div class="wrap"><strong>ENGLISH PT</strong><p>{esc(loc["full_name"])} · 지역별 맞춤 영어 안내</p></div></footer>',
        raw, count=1, flags=re.S,
    )
    raw = re.sub(
        r'(<section class="final"><div class="wrap"><h2>).*?(</h2>)',
        lambda m:m.group(1)+esc(f"{h1}, 등록보다 먼저 현재 상태와 목표부터 확인하세요.")+m.group(2),
        raw,count=1,flags=re.S,
    )

    # Add missing social description from the audited meta description.
    dm = re.search(r'<meta name="description" content="([^"]*)">',raw)
    if dm and 'property="og:description"' not in raw:
        raw=raw.replace(dm.group(0),dm.group(0)+f'<meta property="og:description" content="{esc(html.unescape(dm.group(1)))}">',1)
    if 'property="og:type"' not in raw:
        raw=raw.replace('<meta property="og:title"', '<meta property="og:type" content="website"><meta property="og:title"',1)

    raw, schema_ok = add_breadcrumb_schema(raw,h1,canonical)
    if not schema_ok:
        problems.append("breadcrumb_schema")

    raw = raw.replace('</body>','<div class="mobile-sticky"><a href="#consultation-preview">무료 PT 진단 신청</a></div></body>',1)

    forbidden=[
        "production 미배포","검수용 페이지","실제 상담 전송은 비활성화",
        "흐름 Band","시점 배분","직접 방식 방식","회수 회수","상기 횟수",
        "이어지는 정체가 어디서 생기는지 검토합니다",
        "근거를 찾을 수 되는지","반복되는 문제가 어디서 생기는지 검토합니다",
    ]
    required=[
        '<meta name="robots" content="index,follow">',
        f'<body class="{theme}" data-production-deploy="true" data-stage9-clean="true">',
        'name="name"','name="phone"','name="consent"',
        'class="breadcrumb wrap"','class="mobile-sticky"',
        EMAILJS_TAG,'class="section mass-context"',
    ]
    if any(x not in raw for x in required):
        problems.append("production_contract")
    bad=[x for x in forbidden if x in raw]
    if bad:
        problems.append("stale_or_machine_copy:"+",".join(bad))
    if raw.count('href="/'+loc["slug"]+'-') < 12:
        problems.append("cluster_links")
    visible = re.sub(r'<script.*?</script>|<style.*?</style>|<[^>]+>', ' ', raw, flags=re.S|re.I)
    visible = re.sub(r'\s+',' ',html.unescape(visible)).strip()
    if not (5500 <= len(visible) <= 16000):
        problems.append(f"visible_chars:{len(visible)}")
    return raw,problems


def render_production_page(source_raw: str, name: str) -> tuple[str,list[str]]:
    svc, ex = gold_modules()
    slug,intent=intent_from_name(name)
    loc=location_from_source(source_raw,name,intent)
    if intent in SERVICE_ORDER:
        profile=svc.PROFILES[intent]
        cards,steps,proofs,feedback=service_source(intent)
        rendered=svc.render_page(slug,loc,intent,profile,cards,steps,proofs,feedback)
        family="service"
    else:
        key=next(k for k,v in ex.EXAMS.items() if v["intent"]==intent)
        rendered=ex.render(slug,loc,key,ex.EXAMS[key])
        family="exam"
    return productionize(rendered,loc,intent,family)
