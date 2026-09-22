#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 3 production dry-run: 10 audited locality rows x 13 frozen intents = 130 pages.

Goals:
- use frozen V4.5 service/exam Gold generators
- apply full locality variation signature without fabricated locality facts
- retain EnglishUp-benchmark conversion mechanics: decision strip + mid-value CTA
- enforce cross-locality duplicate gate before writing outputs
- remain noindex / lead-disabled / not production deployed
"""
from __future__ import annotations
import html, importlib.util, json, math, re, shutil
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"stage3-production-dryrun-10x13"
INPUT=ROOT/"stage3_localities_10_v1.json"
PHONE_HREF="tel:+821050068027"; PHONE_LABEL="전화 010-5006-8027"
SERVICE_ORDER=["elem-tutor","mid-conv","high-conv","univ-conv","jobseeker-conv","biz-business-conv","housewife-conv"]
EXAM_ORDER=["toeic","toeic-speaking","opic","ielts","duolingo","toefl"]

FRAME_BY_INTRO={
 "problem-first":"scene","scene-first":"scene","parent-view":"scene","learner-view":"scene",
 "timeline-first":"deadline","routine-first":"deadline","assessment-first":"deadline",
 "diagnosis-first":"error","mistake-first":"error",
 "goal-first":"use","question-first":"use","use-case-first":"use",
 "decision-first":"reuse","comparison-first":"reuse","contrast-first":"reuse","transition-first":"reuse",
}
SOURCE_BY_FRAME={"scene":"seoul-seocho-naegokdong","deadline":"gangwon-gangneung-naegokdong","error":"gangwon-gangneung-gangnamdong","use":"sejong-goundong","reuse":"busan-haeundae-jungdong"}

INTRO={
"parent-view":"학생 영어를 볼 때는 진도량보다 최근에 혼자 처리되는 범위와 도움이 필요한 장면을 먼저 나누는 편이 좋습니다.",
"learner-view":"직접 영어를 배우는 학습자라면 최근 영어가 필요했던 순간을 하나 고르고 그 장면에서 무엇이 안 됐는지를 기준으로 훈련을 좁힙니다.",
"decision-first":"과정 이름을 고르기 전에 지금 가장 먼저 바꿔야 할 영어 행동 하나를 정하면 비교 기준이 단순해집니다.",
"assessment-first":"시험·수행·발표처럼 실제 평가 장면이 있다면 그 장면에서 요구하는 행동을 기준으로 현재 준비 상태를 나눕니다.",
"problem-first":"최근 반복해서 막힌 장면 하나를 출발점으로 삼으면 필요한 표현과 연습 범위를 과하게 넓히지 않을 수 있습니다.",
"scene-first":"영어가 실제로 필요했던 순간을 먼저 떠올리고 그 장면에서 무엇이 됐고 어디에서 멈췄는지를 나눠봅니다.",
"question-first":"지금 내게 필요한 영어가 무엇인지 질문한 뒤 가장 가까운 사용 장면과 일정에서 거꾸로 준비 범위를 정합니다.",
"diagnosis-first":"현재 수준을 한 점수로 묶지 않고 이해·출력·시간·재사용처럼 실제 행동 기준으로 나눠 우선순위를 정합니다.",
"comparison-first":"비슷해 보이는 과정도 목표와 평가 방식이 다르면 준비 순서가 달라지므로 진단·훈련·재점검 구조를 함께 비교합니다.",
"goal-first":"학교·시험·취업·업무처럼 이번 영어의 목적을 먼저 한 문장으로 정하면 필요한 학습 경로가 선명해집니다.",
"timeline-first":"시험일·발표일·면접일처럼 날짜가 있다면 남은 시간에 바꿀 수 있는 행동부터 역산해 우선순위를 정합니다.",
}
CONTEXT={
"schedule-context":"주간 일정 안에서 실제로 반복 가능한 연습량을 기준으로 계획합니다. 무리한 분량보다 다음 주에도 다시 이어갈 수 있는 루틴을 우선합니다.",
"work-life-light":"지역 정보보다 실제 사용 장면을 우선합니다. 회의·발표·수업·일상처럼 영어를 써야 하는 상황을 기준으로 준비 범위를 좁힙니다.",
"commute-light":"위치 자체를 학습 특성으로 추측하지 않습니다. 해당 지역을 검색 기준으로만 사용하고 목표·일정·복습 가능량으로 과정을 판단합니다.",
"daily-life-light":"최근 일상에서 영어가 필요했던 순간을 짧게 기록해 출발점으로 사용합니다. 지역명만으로 학습 성향을 가정하지 않습니다.",
"minimal-context":"지역 설명은 정확한 위치 신호까지만 사용하고 본문은 실제 영어 학습 판단과 재확인 기준에 집중합니다.",
"nearby-choice":"같은 지역에서 찾더라도 대상과 목표가 다르면 과정도 달라질 수 있습니다. 가까운 위치보다 현재 목적에 맞는 경로를 먼저 봅니다.",
"purpose-router":"같은 지역 검색 안에서도 학교영어·회화·시험·취업·업무 목적을 나눠 가장 직접적인 경로부터 비교합니다.",
"school-life-light":"학생 과정은 특정 학교를 추측하지 않고 읽기·듣기·말하기·수행처럼 실제 학교 영어 행동을 기준으로 봅니다.",
"comparison-context":"과정을 비교할 때 광고 표현보다 진단 기준·훈련 방식·피드백·재점검 구조가 현재 목표와 맞는지 확인합니다.",
"hierarchy-light":"지역 계층은 검색과 위치 식별에만 사용하고, 본문에서는 실제 영어 목표와 학습 판단을 우선합니다.",
}
CASE={
"three-moments":"수업 전에는 현재 장면을 확인하고, 수업 중에는 필요한 행동을 연습하며, 수업 뒤에는 조건을 바꿔 다시 되는지 확인합니다.",
"before-after-process":"처음의 넓은 고민을 구체적인 행동으로 좁힌 뒤, 설명 전과 후에 혼자 처리되는 범위가 실제로 달라졌는지 비교합니다.",
"usage-scene":"실제 사용 장면을 재현한 뒤 질문·자료·순서를 조금씩 바꿔 같은 기능을 다른 조건에서도 다시 사용할 수 있는지 봅니다.",
"single-learner":"여러 목표를 동시에 늘리지 않고 현재 결과를 가장 크게 제한하는 기능 하나를 먼저 안정시킨 뒤 다음 범위로 이동합니다.",
"week-plan":"한 주 안에서 확인할 행동, 직접 연습할 행동, 다시 점검할 행동을 나눠 계획이 학습량만 늘리는 방향으로 가지 않게 합니다.",
"assessment-scene":"평가 형식과 요구 행동을 확인한 뒤 비슷한 조건으로 연습하고, 다음 시도에서 같은 기준이 유지되는지를 다시 확인합니다.",
"decision-tree":"학교영어·회화·시험·취업·업무 중 목적을 먼저 나누고 현재 수준과 일정에 따라 세부 경로를 선택합니다.",
"mistake-repair":"틀린 답만 고치지 않고 왜 막혔는지 원인을 분리한 뒤 다른 문제나 장면에서 같은 오류가 반복되는지 확인합니다.",
"deadline-scenario":"시험·발표·면접 날짜가 있으면 남은 기간에서 거꾸로 필요한 연습을 배치하고 마감 뒤 장기 학습을 따로 둡니다.",
"routine-rebuild":"공백이 있었다면 긴 공부보다 반복 가능한 최소 루틴부터 복구하고 안정된 뒤 학습량과 난도를 늘립니다.",
}
DIAG={
"comprehension-skill":"읽거나 들을 때 어휘 부족인지 문장 구조인지 정보 처리 속도인지 원인을 나눠 이해 단계의 병목을 먼저 찾습니다.",
"usage-goal":"실제로 말하고 쓰고 선택해야 하는 행동을 먼저 정한 뒤 그 행동에 필요한 지식과 표현만 역산합니다.",
"error-pattern":"정답 여부보다 같은 실수가 왜 반복되는지를 기록하고 힌트를 줄였을 때 스스로 수정되는 범위를 비교합니다.",
"deadline":"남은 기간 안에 바꿀 수 있는 행동과 장기적으로 쌓아야 할 기초를 나눠 가까운 일정에 필요한 범위를 우선합니다.",
"study-volume":"많이 공부하는 계획보다 실제로 반복 가능한 분량과 다음 재확인 시점을 정해 학습이 끊기지 않게 합니다.",
"priority":"여러 약점을 동시에 다루지 않고 현재 결과에 가장 직접적인 영향을 주는 한두 항목을 먼저 선택합니다.",
"output-skill":"알고 있는 표현이 실제 말이나 글로 바로 나오지 않는다면 첫 반응과 완결성을 중심으로 출력 연습 비중을 높입니다.",
"current-level":"처음부터 다시 배우기보다 이미 혼자 가능한 범위와 도움을 받아야 가능한 범위를 분리해 시작점을 정합니다.",
}
CTA={
"goal-check":"다음 상담이나 수업 전에 이번에 가장 먼저 바꾸고 싶은 행동 하나를 정해두면 우선순위를 빠르게 잡을 수 있습니다.",
"current-state":"지금 혼자 가능한 것과 반복해서 막히는 것을 한두 가지씩 나누면 필요한 훈련을 더 정확하게 고를 수 있습니다.",
"first-plan":"첫 계획은 넓게 잡지 않습니다. 가까운 일정과 현재 수준을 기준으로 바로 실행할 한두 가지 행동만 정합니다.",
"route-find":"대상과 사용 목적을 먼저 고르면 회화·과외·시험 중 어떤 경로가 더 직접적인지 불필요한 비교 없이 좁힐 수 있습니다.",
"diagnosis":"과정을 정하기 어렵다면 현재 되는 것과 막히는 것을 먼저 나누고, 가장 큰 병목 하나부터 확인합니다.",
"priority-check":"목표가 여러 개라면 가장 가까운 결과에 영향을 주는 한 가지를 먼저 정하고 나머지는 다음 순서로 연결합니다.",
"weakness-check":"최근 두세 번 반복된 막힘을 찾고 새 조건에서도 같은 문제가 생기는지 확인하면 우선 약점을 정하기 쉽습니다.",
"schedule-fit":"목표뿐 아니라 실제 가능한 일정과 복습 시간까지 함께 확인해 끊기지 않는 계획을 정합니다.",
}
SEED_END=[
"기록은 길게 남기지 않고 다음 시도에서 다시 볼 행동 한두 개만 남깁니다.",
"이미 안정된 부분은 반복을 줄이고 조건이 달라질 때 흔들리는 부분에 시간을 더 씁니다.",
"한 번의 성공보다 자료와 질문이 달라져도 같은 기준을 다시 쓸 수 있는지를 봅니다.",
"다음 일정이 가까울수록 새 범위를 넓히기보다 현재 병목을 실제 조건에서 줄이는 데 집중합니다.",
"최근 한 주의 실제 수행에서 가장 자주 멈춘 순간을 다음 연습의 첫 기준으로 삼습니다.",
"설명을 이해한 뒤에는 도움 없이 다시 처리되는지를 확인해 학습 범위를 조정합니다.",
"잘되는 영역을 계속 반복하기보다 새 조건에서 흔들리는 행동을 따로 남겨 다음 순서를 정합니다.",
"수업에서 다룬 내용을 다음 실제 장면에 한 번 적용하고 그 결과를 다음 점검 자료로 사용합니다.",
"문제 수를 늘리기 전에 같은 원인이 다른 문제에서도 반복되는지부터 확인합니다.",
"기간이 짧다면 새로운 범위를 넓히기보다 현재 가진 지식으로 실전 행동을 안정시키는 편이 먼저입니다.",
"목표가 바뀌면 이전 계획을 버리기보다 유지할 행동과 새로 필요한 행동의 비중을 다시 나눕니다.",
"힌트를 받아 해결한 항목은 다음 시도에서 힌트를 줄여도 같은 기준이 남는지 재확인합니다.",
"정답이나 완성 답변만 남기지 않고 어떤 판단을 거쳐 결과를 만들었는지 짧게 기록합니다.",
"다음 점검에서는 같은 자료를 반복하기보다 비슷한 기능을 요구하는 다른 자료로 재사용 범위를 확인합니다.",
"한 번에 여러 약점을 고치려 하지 않고 현재 결과에 가장 직접적인 한 항목부터 처리합니다.",
"학습량이 계획보다 많아지면 완료하지 못한 항목을 누적하지 않고 다음 주 범위를 다시 줄입니다.",
"첫 반응이 늦다면 완벽한 문장을 기다리기보다 핵심부터 짧게 시작하고 뒤에 이유를 붙이는 연습을 합니다.",
"이해가 흔들리면 어휘·문장 구조·정보 처리 중 어디에서 멈췄는지를 분리해 다시 봅니다.",
"실전 조건에서 결과가 달라지면 지식 부족인지 시간과 순서 문제인지 따로 확인합니다.",
"상담 전에는 최근 막힌 장면과 가장 가까운 일정만 정리해도 첫 우선순위를 정하는 데 충분합니다.",
]

FOCUS_NOTES=[
("최근 장면 하나에서 시작하기","최근 일주일 안에 영어 때문에 멈췄던 순간을 하나 적어봅니다. 구체적인 장면이 있으면 과정 이름보다 필요한 기능을 먼저 찾을 수 있습니다."),
("첫 목표를 작게 잡기","처음부터 전체 실력을 바꾸려 하지 않고 한 가지 수행을 반복합니다. 같은 조건에서 다시 해본 뒤 다음 목표를 정합니다."),
("설명보다 재사용 확인하기","배운 내용을 그대로 따라 하는 것과 조건이 바뀌어도 다시 쓰는 것은 다릅니다. 질문·문제·상황을 바꿔도 기능이 남는지 확인합니다."),
("시간이 부족할 때 범위 줄이기","학습 시간을 늘리기 어렵다면 영역 수를 줄입니다. 꼭 필요한 기능을 남기고 부가 목표는 다음 단계로 미룹니다."),
("기초가 부족할 때 시작점 찾기","모든 내용을 처음부터 다시 보기보다 현재 문장을 만들거나 지문을 이해할 때 실제로 막히는 기초 요소를 먼저 복구합니다."),
("점수와 실전이 다를 때","시험 점수와 실제 말하기·쓰기 수행은 다르게 나타날 수 있습니다. 서로 다른 결과를 한 레벨로 묶지 않고 필요한 행동을 따로 봅니다."),
("복습이 자주 끊길 때","한 번에 긴 복습을 계획하지 않고 짧게 다시 꺼낼 수 있는 단위를 남깁니다. 일정이 흔들려도 다시 시작할 위치가 있어야 합니다."),
("상담에서 확인할 질문","현재 약점을 어떻게 진단하는지, 수업 뒤 무엇을 기록하는지, 다음 점검에서 어떤 변화를 확인하는지 차례로 물어봅니다."),
("학생 영어의 관리 기준","정답률만 보는 대신 오답 이유와 공부 순서를 확인합니다. 스스로 다시 풀거나 설명할 수 있는지가 다음 단계 판단 기준이 됩니다."),
("성인 영어의 관리 기준","실제로 쓸 표현을 고르고 반복합니다. 알고 있는 지식을 늘리는 것보다 필요한 순간에 꺼내 쓰는 속도와 완결성을 봅니다."),
("마감이 없는 목표 운영","기간을 억지로 정하기보다 한 달 단위 수행 목표를 둡니다. 목표가 안정되면 다음 기능을 추가하며 범위를 넓힙니다."),
("마감이 있는 목표 운영","남은 날짜에 맞춰 우선순위를 좁히고 실제 시험·발표·면접과 비슷한 조건으로 연습합니다. 직전에는 새 범위를 무리하게 늘리지 않습니다."),
("서비스를 비교할 때","가격이나 횟수만 비교하지 않고 진단→훈련→피드백→재점검이 어떻게 이어지는지 확인합니다. 설명이 구체적일수록 선택하기 쉽습니다."),
("목표가 자주 바뀔 때","현재 가장 가까운 사용 장면 하나를 기준으로 시작합니다. 새 목표가 생기면 기존 계획을 버리는 대신 비중을 다시 조정합니다."),
("자신감이 떨어졌을 때","쉬운 과제만 반복하기보다 성공할 수 있는 작은 수행과 약간 어려운 수행을 번갈아 배치합니다. 변화가 보이도록 기록을 남깁니다."),
("학습량이 과할 때","완료하지 못한 계획을 계속 누적하지 않습니다. 실제로 소화한 양을 기준으로 다음 계획을 줄여 지속성을 우선합니다."),
("독해가 느릴 때","모든 문장을 번역하기보다 핵심 정보와 문장 구조를 먼저 파악합니다. 어휘 부족과 구조 이해를 따로 점검합니다."),
("말이 바로 안 나올 때","완벽한 문장을 만들려는 시간을 줄이고 짧은 첫 문장부터 꺼냅니다. 이후 이유와 예시를 붙여 문장을 확장합니다."),
("듣기가 불안정할 때","놓친 구간이 단어인지 연결음인지 정보 처리인지 구분합니다. 원인에 따라 반복 방식과 확인 기준을 다르게 잡습니다."),
("시험 준비가 분산될 때","여러 시험을 동시에 준비하기보다 실제로 필요한 시험을 먼저 정합니다. 나머지 목표는 현재 일정 뒤로 이동합니다.")
]

DECISION_NOTES=[
("첫 선택을 좁히는 세 질문",["가장 가까운 영어 사용 일정은 무엇인가?","최근 가장 자주 멈춘 기능은 무엇인가?","주중에 실제 반복 가능한 시간은 어느 정도인가?"]),
("과정 비교 전에 적어볼 항목",["목표를 한 문장으로 설명할 수 있는가?","최근 영어 때문에 불편했던 장면이 떠오르는가?","결과를 언제 다시 확인할지 정했는가?"]),
("학습 계획을 짧게 만드는 기준",["첫 단계에서 바꿀 행동을 하나만 고른다.","복습할 수 없는 양은 처음부터 줄인다.","다음 점검에서 확인할 기준을 미리 정한다."]),
("상담 전에 준비할 정보",["최근 어려웠던 문제·자료·응답을 하나 고른다.","시험·면접·발표 마감이 있다면 날짜를 적는다.","가능한 요일과 복습 시간을 현실적으로 계산한다."]),
("목표가 넓을 때 나누는 법",["평가가 있는 목표와 실제 사용 목표를 분리한다.","기초 보완과 즉시 필요한 실전 준비를 같은 비중으로 두지 않는다.","가장 급한 목표가 끝난 뒤 다음 목표를 연결한다."]),
("변화를 확인하는 방식",["공부한 시간보다 이전에 못 하던 행동이 달라졌는지 본다.","다른 문제나 장면에서도 기능이 유지되는지 확인한다.","재점검 결과에 따라 학습 비중을 다시 조정한다."]),
("수업 방식보다 먼저 볼 것",["누구를 위한 과정인지 대상이 분명한가?","진단 항목이 실제 목표와 연결되는가?","훈련 후 무엇을 다시 확인하는지 설명되어 있는가?"]),
("학습이 끊기지 않게 하는 장치",["바쁜 날에도 할 최소 복습량을 정한다.","한 주를 놓쳐도 다시 시작할 위치를 남긴다.","완벽한 계획보다 반복 가능한 계획을 선택한다."]),
("마감형 목표 체크포인트",["남은 기간을 주 단위로 나눈다.","점수와 실제 수행 가운데 더 급한 기준을 고른다.","마감 뒤 유지할 장기 학습을 따로 설계한다."]),
("비교 후 남길 기록",["어떤 설명이 내 문제와 직접 연결됐는지 적는다.","진단과 피드백 방식이 구체적인지 비교한다.","목표가 불분명하면 바로 등록하기보다 다시 정리한다."])
]

FAQ_SUFFIX={
"short-analytic":"다음 확인에서는 같은 조건이 반복되는지부터 짧게 점검합니다.",
"balanced-editorial":"한 번의 결과보다 다음 시도에서 같은 기준을 다시 적용할 수 있는지를 함께 봅니다.",
"compact-direct":"다음 연습에서는 이 항목만 따로 떼어 다시 확인합니다.",
"calm-explanatory":"설명을 들은 뒤 혼자 다시 해보는 과정까지 이어져야 실제로 남았는지 판단할 수 있습니다.",
"question-led":"조건이 바뀌어도 같은 답을 만들 수 있는지 질문을 바꿔 다시 확인합니다.",
"example-led":"익숙한 예시 한 번으로 끝내지 않고 다른 문제나 장면에서 같은 기준을 적용해봅니다."
}

def first_sentence(text):
 parts=re.split(r'(?<=[.!?])\s+',str(text).strip())
 return parts[0] if parts and parts[0] else str(text).strip()

def seeded(row,mod,offset=0):
 s=row["content_seed"]
 chunk=s[offset:offset+4] or s[:4]
 return int(chunk,16)%mod

def rewrite_deep_faq(raw,row,d,deep,faq,service_label):
 # Keep intent-specific titles/questions, but rebuild long explanatory copy with the audited locality variation library.
 start=seeded(row,len(FOCUS_NOTES),0)
 cards=[]
 for i,(title,text) in enumerate(deep):
  ft,fp=FOCUS_NOTES[(start+i*3)%len(FOCUS_NOTES)]
  body=first_sentence(text)+" "+fp
  cards.append('<article class="card"><b>'+html.escape(title)+'</b><p>'+html.escape(body)+'</p></article>')
 nt,items=DECISION_NOTES[seeded(row,len(DECISION_NOTES),4)]
 cards.append('<article class="card"><b>'+html.escape(nt)+'</b><p>'+html.escape(" ".join(items))+'</p><p>'+html.escape(CTA[d["cta_frame"]])+'</p></article>')
 deep_block='<section class="section soft"><div class="wrap"><p class="kicker">더 깊게 보기</p><h2>'+html.escape(service_label)+' 선택 전에 확인할 기준</h2><div class="grid4">'+''.join(cards)+'</div></div></section>'
 raw,n=re.subn(r'<section class="section soft"><div class="wrap"><p class="kicker">더 깊게 보기</p>[\s\S]*?</section>',deep_block,raw,count=1)
 if n!=1:raise RuntimeError("deep rewrite")
 # Five FAQs, deterministic order; preserve the question and the first factual sentence, vary the recheck explanation.
 offset=seeded(row,len(faq),8)
 selected=[faq[(offset+i)%len(faq)] for i in range(min(5,len(faq)))]
 suffix=FAQ_SUFFIX[d["sentence_rhythm"]]
 details=[]
 for i,(q,a) in enumerate(selected):
  extra=[suffix,DIAG[d["diagnosis_emphasis"]],CASE[d["case_frame"]],CTA[d["cta_frame"]],seed_pick(row,(i+3)%12)][i%5]
  details.append('<details><summary>'+html.escape(q)+'</summary><p>'+html.escape(first_sentence(a)+" "+extra)+'</p></details>')
 faq_block='<section class="section"><div class="wrap narrow"><p class="kicker">자주 묻는 질문</p><h2>선택 전에 확인할 질문</h2><div class="faq">'+''.join(details)+'</div></div></section>'
 raw,n=re.subn(r'<section class="section"><div class="wrap narrow"><p class="kicker">자주 묻는 질문</p>[\s\S]*?</section>',faq_block,raw,count=1)
 if n!=1:raise RuntimeError("faq rewrite")
 return raw

def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 if not spec or not spec.loader: raise RuntimeError(f"cannot load {path}")
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def visible(raw):
 raw=re.sub(r"<script[\s\S]*?</script>"," ",raw,flags=re.I);raw=re.sub(r"<style[\s\S]*?</style>"," ",raw,flags=re.I);raw=re.sub(r"<[^>]+>"," ",raw)
 return re.sub(r"\s+"," ",html.unescape(raw)).strip()
def toks(t):return re.findall(r"[가-힣A-Za-z0-9]+",t.lower())
def cosine(a,b):
 ca,cb=Counter(toks(a)),Counter(toks(b));dot=sum(ca[k]*cb.get(k,0) for k in ca);na=math.sqrt(sum(v*v for v in ca.values()));nb=math.sqrt(sum(v*v for v in cb.values()));return dot/(na*nb) if na and nb else 0.0
def jacc(a,b,n=5):
 ta,tb=toks(a),toks(b);sa={tuple(ta[i:i+n]) for i in range(max(0,len(ta)-n+1))};sb={tuple(tb[i:i+n]) for i in range(max(0,len(tb)-n+1))};return len(sa&sb)/len(sa|sb) if sa|sb else 0.0

def dims(sig):
 keys=["intro_pattern","section_order","local_context_mode","case_frame","cta_frame","sentence_rhythm","diagnosis_emphasis"];vals=sig.split("|")
 if len(vals)!=7:raise RuntimeError(sig)
 return dict(zip(keys,vals))
def seed_pick(row,offset=0):return SEED_END[(int(row["content_seed"][offset:offset+2],16) if len(row["content_seed"])>=offset+2 else 0)%len(SEED_END)]

def all_links(row,current,svc,ex):
 slug=row["region_slug"];dn=row["dong_name"];items=[]
 for intent in SERVICE_ORDER:
  if intent!=current:items.append(f'<a href="{slug}-{intent}.html">{html.escape(dn+" "+svc.PROFILES[intent]["service_h1"])}</a>')
 for key in EXAM_ORDER:
  e=ex.EXAMS[key]
  if e["intent"]!=current:items.append(f'<a href="{slug}-{e["intent"]}.html">{html.escape(dn+" "+e["service"])}</a>')
 return "".join(items)

STRIP_INTRO={
"problem-first":"최근 막힌 장면","scene-first":"실제 사용 순간","parent-view":"최근 학습 행동","learner-view":"직접 필요한 장면",
"timeline-first":"가장 가까운 일정","routine-first":"유지 가능한 루틴","assessment-first":"평가 장면",
"diagnosis-first":"현재 병목","mistake-first":"반복 오류","goal-first":"목표 행동","question-first":"필요한 영어",
"use-case-first":"실제 사용 목적","decision-first":"선택 순서","comparison-first":"비교 기준","contrast-first":"대상별 차이","transition-first":"다음 목표"
}
STRIP_DIAG={
"current-level":"되는 것/막히는 것","usage-goal":"실제 사용 행동","deadline":"남은 기간","error-pattern":"반복 원인",
"study-volume":"반복 가능한 분량","output-skill":"말·글 출력","comprehension-skill":"읽기·듣기 병목","priority":"가장 큰 병목"
}
STRIP_CASE={
"single-learner":"한 목표 집중","before-after-process":"전후 비교","three-moments":"전·중·후 연결","week-plan":"주간 운영",
"mistake-repair":"오류 교정","decision-tree":"선택 트리","deadline-scenario":"마감 역산","routine-rebuild":"루틴 복구",
"usage-scene":"사용 장면 반복","assessment-scene":"평가 조건 재현"
}

def benchmark_blocks(raw,family,row,d):
 strip=[
  ("출발점",STRIP_INTRO[d["intro_pattern"]]),
  ("먼저 볼 것",STRIP_DIAG[d["diagnosis_emphasis"]]),
  ("연습 방식",STRIP_CASE[d["case_frame"]]),
  ("다음 확인",CTA[d["cta_frame"]].split(" ")[0]+" 재점검"),
 ]
 sh='<section class="decision-strip" aria-label="빠른 판단 요약"><div class="wrap"><div class="decision-grid">'+''.join('<div><b>'+html.escape(a)+'</b><span>'+html.escape(b)+'</span></div>' for a,b in strip)+'</div></div></section>'
 m=re.search(r'(</section>)(?=\s*<section id="detail")',raw)
 if not m:raise RuntimeError("hero boundary")
 raw=raw[:m.end()]+sh+raw[m.end():]
 mid_copy=CTA[d["cta_frame"]]+" "+seed_pick(row,2)
 mid='<section class="mid-cta"><div class="wrap"><div><p class="kicker">다음 단계</p><h2>'+html.escape(mid_copy)+'</h2></div><div class="mid-actions"><a class="btn primary" href="#consultation-preview">상담 전 확인하기</a><a class="btn phone" href="'+PHONE_HREF+'">'+PHONE_LABEL+'</a></div></div></section>'
 marker='<section class="section soft"><div class="wrap"><p class="kicker">피드백 예시</p>';pos=raw.find(marker)
 if pos<0:raise RuntimeError("feedback boundary")
 return raw[:pos]+mid+raw[pos:]

def decision_block(raw,family,current,svc,ex,row,d):
 if family=="service":
  p=svc.PROFILES[current]
  items=[
   ("이런 경우 잘 맞습니다",STRIP_INTRO[d["intro_pattern"]]+"이 반복되고 "+STRIP_DIAG[d["diagnosis_emphasis"]]+"을 따로 확인해야 하는 경우"),
   ("다른 선택이 나을 수 있습니다",p["boundary"]),
   ("상담에서 확인할 비용·일정 조건","횟수 · 시간 · 진행 방식 · 준비 범위를 확인하며 구체 비용은 상담에서 안내합니다."),
   ("수업 계획은 이렇게 정합니다",STRIP_INTRO[d["intro_pattern"]]+" → "+STRIP_DIAG[d["diagnosis_emphasis"]]+" → "+STRIP_CASE[d["case_frame"]]+" → 재확인"),
   ("상담 전에 준비할 것","최근 자료 · "+STRIP_INTRO[d["intro_pattern"]]+" · 다음 일정 · 가능한 시간대"),
  ]
 else:
  e=next(v for v in ex.EXAMS.values() if v["intent"]==current)
  items=[
   ("이런 경우 잘 맞습니다","목표 시험·일정은 정해졌지만 "+STRIP_DIAG[d["diagnosis_emphasis"]]+"을 구분해 준비해야 하는 경우"),
   ("다른 선택이 나을 수 있습니다",e["boundary"]),
   ("상담에서 확인할 비용·일정 조건","횟수 · 시간 · 남은 기간 · 피드백 방식 · 준비 범위를 확인합니다."),
   ("수업 계획은 이렇게 정합니다","최근 수행 → "+STRIP_DIAG[d["diagnosis_emphasis"]]+" → "+STRIP_CASE[d["case_frame"]]+" → 실전 재검증"),
   ("상담 전에 준비할 것","목표 결과 · 시험일/마감 · 최근 성적·답변 · 가장 어려운 영역"),
  ]
 block='<section class="section decision-guide"><div class="wrap narrow"><p class="kicker">선택 기준</p><h2>광고 문구보다, 이 다섯 가지를 먼저 확인하세요</h2><div class="decision-list">'+''.join('<div><b>◆ '+html.escape(a)+'</b><p>'+html.escape(b)+'</p></div>' for a,b in items)+'</div></div></section>'
 pat=r'<section class="section"><div class="wrap narrow"><p class="kicker">(과정 선택|시험 선택)</p>[\s\S]*?</section>'
 raw,n=re.subn(pat,block,raw,count=1)
 if n!=1:raise RuntimeError("decision section")
 return raw

def replace_service_variation(raw,row,d,profile,cards,steps):
 # detail: keep target scope but replace frozen locality-frame prose with signature prose
 pat=r'(<section id="detail" class="section"><div class="wrap narrow"><p class="kicker">지금 상황</p><h2>.*?</h2>)([\s\S]*?)(</div></section>)'
 m=re.search(pat,raw)
 if not m:raise RuntimeError("service detail")
 base=f'<p>{html.escape(row["full_name_ko"])}에서 {html.escape(profile["service_body"])}를 알아볼 때는 과정 이름보다 지금 필요한 영어 장면을 먼저 확인합니다.</p><p>{html.escape(profile["scope"])}</p><p>{html.escape(INTRO[d["intro_pattern"]])}</p><p>{html.escape(CONTEXT[d["local_context_mode"]])}</p>'
 raw=raw[:m.start()]+m.group(1)+base+m.group(3)+raw[m.end():]
 # scene cards: symptom + two complete dimension-specific paragraphs
 for idx,(title,symptom) in enumerate(cards):
  p1=f"{title} 장면에서는 {DIAG[d['diagnosis_emphasis']]} {seed_pick(row,idx%4)}"
  p2=f"{CASE[d['case_frame']]} {CTA[d['cta_frame']]}"
  rg=r'(<article class="card"><b>'+re.escape(html.escape(title))+r'</b>)[\s\S]*?(</article>)'
  rep=r'\1<p>'+html.escape(symptom)+'</p><p>'+html.escape(p1)+'</p><p>'+html.escape(p2)+'</p>'+r'\2'
  raw,n=re.subn(rg,rep,raw,count=1)
  if n!=1:raise RuntimeError("service card "+title)
 # diagnosis body
 rg=r'(<p class="kicker">막히는 이유</p><h2>.*?</h2>)[\s\S]*?(</div></section>)'
 body='<p>'+html.escape(DIAG[d["diagnosis_emphasis"]])+'</p><p>'+html.escape(CASE[d["case_frame"]])+'</p><p>'+html.escape(seed_pick(row,4))+'</p>'
 raw,n=re.subn(rg,lambda m:m.group(1)+body+m.group(2),raw,count=1)
 if n!=1:raise RuntimeError("service diagnosis")
 # flow per step
 for idx,title in enumerate(steps):
  a=f"{INTRO[d['intro_pattern']]} 이 단계에서는 '{title}' 행동에 필요한 부분만 짧게 확인합니다."
  b=f"{CASE[d['case_frame']]} {seed_pick(row,(idx+6)%12)}"
  rg=r'(<li><span>\d+</span><div><b>'+re.escape(html.escape(title))+r'</b>)[\s\S]*?(</div></li>)'
  raw,n=re.subn(rg,lambda m:m.group(1)+'<p>'+html.escape(a)+'</p><p>'+html.escape(b)+'</p>'+m.group(2),raw,count=1)
  if n!=1:raise RuntimeError("service flow "+title)
 return raw

def replace_exam_variation(raw,row,d,exam):
 # detail signature paragraph
 rg=r'(<section id="detail" class="section"><div class="wrap narrow"><p class="kicker">시험 목표</p><h2>.*?</h2>)([\s\S]*?)(</div></section>)'
 m=re.search(rg,raw)
 if not m:raise RuntimeError("exam detail")
 body=f'<p>{html.escape(row["full_name_ko"])}에서 {html.escape(exam["service"])}를 알아볼 때는 제출 목적과 다음 시험일, 최근 반복된 병목을 먼저 확인합니다.</p><p>{html.escape(exam["goal"])}이 핵심 기준입니다.</p><p>{html.escape(INTRO[d["intro_pattern"]])} {html.escape(CONTEXT[d["local_context_mode"]])}</p>'
 raw=raw[:m.start()]+m.group(1)+body+m.group(3)+raw[m.end():]
 # actual scene cards
 for idx,(title,symptom) in enumerate(exam["scenes"]):
  a=f"{DIAG[d['diagnosis_emphasis']]} '{title}'에서 어떤 조건이 결과를 흔드는지 따로 기록합니다."
  b=f"{CASE[d['case_frame']]} {seed_pick(row,idx%4)}"
  rg=r'(<article class="card"><b>'+re.escape(html.escape(title))+r'</b>)[\s\S]*?(</article>)'
  raw,n=re.subn(rg,lambda m:m.group(1)+'<p>'+html.escape(symptom)+'</p><p>'+html.escape(a)+'</p><p>'+html.escape(b)+'</p>'+m.group(2),raw,count=1)
  if n!=1:raise RuntimeError("exam card "+title)
 # exam structure diagnosis section
 rg=r'(<p class="kicker">시험 구조와 개인 약점</p><h2>.*?</h2>)[\s\S]*?(</div></section>)'
 body='<p>'+html.escape(DIAG[d["diagnosis_emphasis"]])+'</p><p>'+html.escape(CONTEXT[d["local_context_mode"]])+'</p><p>이 시험에서는 '+html.escape(" · ".join(exam["diagnosis"]))+' 항목을 나눠 이미 안정된 부분과 다시 볼 부분을 구분합니다.</p>'
 raw,n=re.subn(rg,lambda m:m.group(1)+body+m.group(2),raw,count=1)
 if n!=1:raise RuntimeError("exam diagnosis")
 # flow descriptions
 for idx,title in enumerate(exam["flow"]):
  txt=f"{CASE[d['case_frame']]} '{title}' 단계에서는 {DIAG[d['diagnosis_emphasis']]} {seed_pick(row,(idx+5)%12)}"
  rg=r'(<li><span>\d+</span><div><b>'+re.escape(html.escape(title))+r'</b>)[\s\S]*?(</div></li>)'
  raw,n=re.subn(rg,lambda m:m.group(1)+'<p>'+html.escape(txt)+'</p>'+m.group(2),raw,count=1)
  if n!=1:raise RuntimeError("exam flow "+title)
 # replace long frozen learning-frame prose with full signature composition
 rg=r'<section class="section"><div class="wrap narrow"><p class="kicker">학습 프레임</p>[\s\S]*?</div></section>'
 paras=[INTRO[d["intro_pattern"]],CONTEXT[d["local_context_mode"]],DIAG[d["diagnosis_emphasis"]],CASE[d["case_frame"]],CTA[d["cta_frame"]],seed_pick(row,8)]
 repl='<section class="section"><div class="wrap narrow"><p class="kicker">학습 프레임</p><h2>현재 목표를 실제 시험 행동으로 바꾸는 기준</h2>'+''.join('<p>'+html.escape(x)+'</p>' for x in paras)+'</div></section>'
 raw,n=re.subn(rg,repl,raw,count=1)
 if n!=1:raise RuntimeError("exam learning frame")
 return raw

def rewrite_mid_sections(raw,row,d,priority,proof_labels,scene_titles,family):
 extras=[DIAG[d["diagnosis_emphasis"]],CONTEXT[d["local_context_mode"]],CASE[d["case_frame"]],CTA[d["cta_frame"]]]
 pri=[]
 for i,label in enumerate(priority[:4]):
  pri.append('<li><b>'+html.escape(label)+'</b><span>'+html.escape(extras[i%len(extras)])+'</span></li>')
 pblock='<section class="section soft"><div class="wrap narrow"><p class="kicker">우선순위</p><h2>'+html.escape(STRIP_INTRO[d["intro_pattern"]])+'에서 무엇부터 볼지 정합니다</h2><p>'+html.escape(INTRO[d["intro_pattern"]])+'</p><ul class="proofs">'+''.join(pri)+'</ul></div></section>'
 raw,n=re.subn(r'<section class="section soft"><div class="wrap narrow"><p class="kicker">우선순위</p>[\s\S]*?</section>',pblock,raw,count=1)
 if n!=1:raise RuntimeError("priority rewrite")

 pitems=[]
 labels=(proof_labels or priority)[:5]
 for i,label in enumerate(labels):
  note=[seed_pick(row,i),FOCUS_NOTES[(seeded(row,len(FOCUS_NOTES),5)+i*2)%len(FOCUS_NOTES)][1],extras[i%4]][i%3]
  pitems.append('<li><b>'+html.escape(label)+'</b><span>'+html.escape(note)+'</span></li>')
 proof='<section class="section"><div class="wrap"><p class="kicker">판단 기준</p><h2>'+html.escape(STRIP_DIAG[d["diagnosis_emphasis"]])+'이 실제로 달라졌는지 확인합니다</h2><p class="lead">'+html.escape(CASE[d["case_frame"]])+'</p><ul class="proofs">'+''.join(pitems)+'</ul></div></section>'
 raw,n=re.subn(r'<section class="section"><div class="wrap"><p class="kicker">판단 기준</p>[\s\S]*?</section>',proof,raw,count=1)
 if n!=1:raise RuntimeError("proof rewrite")

 fcards=[]
 for i,title in enumerate(scene_titles[:3]):
  if i==0: msg=f"'{title}' 항목은 첫 시도와 도움 뒤 결과를 나눠 기록합니다. "+DIAG[d["diagnosis_emphasis"]]
  elif i==1: msg=f"'{title}' 항목은 조건을 바꿔 다시 확인합니다. "+CASE[d["case_frame"]]
  else: msg=f"'{title}' 항목은 다음 일정에서 다시 볼 한 가지를 남깁니다. "+CTA[d["cta_frame"]]
  fcards.append('<article class="card"><b>기록 예시 '+str(i+1)+'</b><p>'+html.escape(msg)+'</p></article>')
 feedback='<section class="section soft"><div class="wrap"><p class="kicker">피드백 예시</p><h2>성과를 약속하지 않고, 다음에 확인할 행동을 기록합니다</h2><p>아래는 특정 수강생의 후기나 점수 변화가 아니라 수업 기록 형식을 보여주는 예시입니다.</p><div class="grid4">'+''.join(fcards)+'</div></div></section>'
 raw,n=re.subn(r'<section class="section soft"><div class="wrap"><p class="kicker">피드백 예시</p>[\s\S]*?</section>',feedback,raw,count=1)
 if n!=1:raise RuntimeError("feedback rewrite")
 return raw

def finalize(raw,row,d,current,svc,ex,family):
 raw=raw.replace('../pilot-v45-5x7/pilot.css','pilot.css').replace('../pilot-v45-5x7/pilot.js','pilot.js')
 raw=raw.replace('V4.5 FULL-DEPTH PILOT · noindex','V4.5 PRODUCTION DRY-RUN · noindex').replace('V4.5 EXAM FULL-DEPTH PILOT · noindex','V4.5 EXAM PRODUCTION DRY-RUN · noindex')
 raw=raw.replace('현재 페이지는 5×7 소규모 검수용이라 폼의 실제 전송은 비활성화되어 있습니다.','현재 페이지는 배포 전 production dry-run이라 폼의 실제 전송은 비활성화되어 있습니다.')
 raw=raw.replace('Full-depth 검수용 페이지 · production 미배포','Production dry-run · noindex · 미배포').replace('시험형 Full-depth 검수용 · production 미배포','시험형 Production dry-run · noindex · 미배포')
 raw=raw.replace('파일럿 폼','검수용 폼').replace('파일럿의 상담 폼','검수용 상담 폼').replace('이 파일럿은','이 배포 전 검수 페이지는').replace('이 파일럿','이 배포 전 검수 페이지')
 raw=benchmark_blocks(raw,family,row,d)
 raw=decision_block(raw,family,current,svc,ex,row,d)
 links=all_links(row,current,svc,ex)
 raw,n=re.subn(r'(<div class="links">)[\s\S]*?(</div>)',lambda m:m.group(1)+links+m.group(2),raw,count=1)
 if n!=1:raise RuntimeError("related links")
 return raw

FRAMES=["scene","deadline","error","use","reuse"]
PERMS=[
 (0,1,2,3,4),(1,0,3,4,2),(2,3,4,0,1),(3,4,1,2,0),(4,2,0,1,3),
 (1,2,4,3,0),(1,3,0,2,4),(1,4,2,0,3),(0,2,3,4,1),(3,0,4,1,2),
]
SERVICE_GROUPS=[
 ["__detail__","실제 장면"],
 ["막히는 이유","우선순위"],
 ["수업 흐름","판단 기준"],
 ["피드백 예시","과정 선택"],
 ["더 깊게 보기","자주 묻는 질문"],
]
EXAM_GROUPS=[
 ["__detail__","실제 막힘"],
 ["시험 구조와 개인 약점","우선순위"],
 ["수업 흐름","판단 기준"],
 ["피드백 예시","시험 선택"],
 ["학습 프레임","더 깊게 보기","자주 묻는 질문"],
]

def section_html(raw,key):
 marker='id="detail"' if key=="__detail__" else '<p class="kicker">'+key+'</p>'
 for m in re.finditer(r'<section\b[^>]*>[\s\S]*?</section>',raw):
  block=m.group(0)
  if marker in block:
   return block
 raise RuntimeError("section not found: "+key)

def replace_section(raw,key,new):
 old=section_html(raw,key)
 return raw.replace(old,new,1)

def compose_frames(raw_by_frame,perm,groups):
 base=raw_by_frame[FRAMES[perm[0]]]
 for gi,keys in enumerate(groups):
  src=raw_by_frame[FRAMES[perm[gi]]]
  for key in keys:
   base=replace_section(base,key,section_html(src,key))
 return base

def first_sentence(text):
 text=html.unescape(re.sub(r'<[^>]+>',' ',text)).strip()
 m=re.search(r'^(.+?[.!?]|.+?다\.)',text)
 return (m.group(1) if m else text).strip()

def row_line(row,slot):
 base=int(row["content_seed"][:8],16)
 return SEED_END[(base+slot*7)%len(SEED_END)]

def rewrite_cards(section,row,start_slot=0):
 slot=start_slot
 def repl(m):
  nonlocal slot
  title=m.group(1);body=m.group(2)
  ps=re.findall(r'<p>(.*?)</p>',body,re.S)
  core=first_sentence(ps[0]) if ps else ""
  line=row_line(row,slot);slot+=1
  return '<article class="card"><b>'+title+'</b><p>'+html.escape(core)+'</p><p>'+html.escape(line)+'</p></article>'
 return re.sub(r'<article class="card"><b>(.*?)</b>([\s\S]*?)</article>',repl,section)

def rewrite_shared_blocks(raw,row):
 # Deep Guide: preserve each card's first core sentence, replace copied tail with locality-variation guidance.
 deep=section_html(raw,"더 깊게 보기");deep2=rewrite_cards(deep,row,0);raw=raw.replace(deep,deep2,1)
 # Feedback examples: illustrative core + distinct recheck line.
 fb=section_html(raw,"피드백 예시");fb2=rewrite_cards(fb,row,6);raw=raw.replace(fb,fb2,1)
 # FAQ: preserve question and first answer sentence; rotate a complete recheck sentence.
 faq=section_html(raw,"자주 묻는 질문");slot=11
 def faq_repl(m):
  nonlocal slot
  q=m.group(1);a=m.group(2);core=first_sentence(a);line=row_line(row,slot);slot+=1
  return '<details><summary>'+q+'</summary><p>'+html.escape(core)+'</p><p>'+html.escape(line)+'</p></details>'
 faq2=re.sub(r'<details><summary>(.*?)</summary><p>([\s\S]*?)</p></details>',faq_repl,faq)
 raw=raw.replace(faq,faq2,1)
 # Decision-proof explanatory spans are process evidence, so make them vary by row without changing labels.
 proof=section_html(raw,"판단 기준");slot=3
 def proof_repl(m):
  nonlocal slot
  label=m.group(1);line=row_line(row,slot);slot+=1
  return '<li><b>'+label+'</b><span>'+html.escape(line)+'</span></li>'
 proof2=re.sub(r'<li><b>(.*?)</b><span>[\s\S]*?</span></li>',proof_repl,proof)
 raw=raw.replace(proof,proof2,1)
 return raw

def main():
 rows=json.loads(INPUT.read_text(encoding="utf-8"))["rows"]
 if len(rows)!=10:raise RuntimeError("need 10 rows")
 if len({r["region_slug"] for r in rows})!=10:raise RuntimeError("slug collision in Stage3 input")
 if any(r["landing_eligibility"]!="ELIGIBLE_AFTER_SLUG_QA" for r in rows):raise RuntimeError("ineligible row")
 svc=load_module("v45_service_gold",ROOT/"scripts/generate-v45-full-depth-pilot.py")
 ex=load_module("v45_exam_gold",ROOT/"scripts/generate-v45-exam-pilot.py")
 OUT.mkdir(parents=True,exist_ok=True)
 shutil.copy2(ROOT/"pilot-v45-5x7/pilot.css",OUT/"pilot.css")
 css_extra='''\n.decision-strip{background:#fff;border-bottom:1px solid #e6e2d9}.decision-grid{display:grid;grid-template-columns:repeat(4,1fr)}.decision-grid>div{padding:20px 18px;border-right:1px solid #e6e2d9}.decision-grid>div:last-child{border-right:0}.decision-grid b{display:block;font-size:13px;margin-bottom:4px}.decision-grid span{font-size:14px;color:#53605a}.mid-cta{padding:30px 0;background:#edeae2}.mid-cta .wrap{display:flex;align-items:center;justify-content:space-between;gap:20px}.mid-cta h2{font-size:clamp(22px,3vw,32px);margin:6px 0}.mid-actions{display:flex;gap:10px;flex-wrap:wrap}.decision-guide{background:#f4f8f5}.decision-list{display:grid;gap:14px}.decision-list>div{padding:16px 18px;background:#fff;border:1px solid #dce7e0;border-radius:14px}.decision-list b{display:block;margin-bottom:6px}.decision-list p{margin:0;color:#41574d}@media(max-width:760px){.decision-grid{grid-template-columns:1fr 1fr}.decision-grid>div:nth-child(2){border-right:0}.decision-grid>div{border-bottom:1px solid #e6e2d9}.mid-cta .wrap{display:block}.mid-actions{margin-top:16px}}\n'''
 with (OUT/"pilot.css").open("a",encoding="utf-8") as fp:fp.write(css_extra)
 shutil.copy2(ROOT/"pilot-v45-5x7/pilot.js",OUT/"pilot.js")
 generated={};files=[]
 for row_index,row in enumerate(rows):
  d=dims(row["variation_signature"]);slug=row["region_slug"];perm=PERMS[row_index]
  # Build each page only from already-frozen Gold frames, then compose five section groups
  # with a locality-specific permutation. No unverified local fact is introduced.
  for intent in SERVICE_ORDER:
   p=svc.PROFILES[intent];raw_by_frame={}
   for frame in FRAMES:
    src=SOURCE_BY_FRAME[frame];locf={"full_name":row["full_name_ko"],"jurisdiction":row["jurisdiction_full"],"dong":row["dong_name"],"variation":frame}
    cards,steps,proofs,feedback=svc.extract_source(ROOT/"pilot-v45-5x7"/f"{src}-{intent}.html")
    raw0=svc.render_page(slug,locf,intent,p,cards,steps,proofs,feedback)
    raw_by_frame[frame]=replace_service_variation(raw0,row,d,p,cards,steps)
   raw=compose_frames(raw_by_frame,perm,SERVICE_GROUPS)
   raw=rewrite_shared_blocks(raw,row)
   raw=finalize(raw,row,d,intent,svc,ex,"service")
   name=f"{slug}-{intent}.html";generated[name]=raw
   files.append({"path":f"stage3-production-dryrun-10x13/{name}","family":"service","intent":intent,"h1":f"{row['dong_name']} {p['service_h1']}","canonical":f"https://englishpt.kr/{slug}-{intent}.html","locality":slug,"blueprint":p["blueprint"],"variation_signature":row["variation_signature"],"gold_frame_permutation":[FRAMES[x] for x in perm]})
  for key in EXAM_ORDER:
   e=ex.EXAMS[key];intent=e["intent"];raw_by_frame={}
   for frame in FRAMES:
    locf={"full_name":row["full_name_ko"],"jurisdiction":row["jurisdiction_full"],"dong":row["dong_name"],"variation":frame}
    raw0=ex.render(slug,locf,key,e)
    raw_by_frame[frame]=replace_exam_variation(raw0,row,d,e)
   raw=compose_frames(raw_by_frame,perm,EXAM_GROUPS)
   raw=rewrite_shared_blocks(raw,row)
   raw=finalize(raw,row,d,intent,svc,ex,"exam")
   name=f"{slug}-{intent}.html";generated[name]=raw
   files.append({"path":f"stage3-production-dryrun-10x13/{name}","family":"exam","intent":intent,"exam":key,"h1":f"{row['dong_name']} {e['service']}","canonical":f"https://englishpt.kr/{slug}-{intent}.html","locality":slug,"blueprint":e["blueprint"],"variation_signature":row["variation_signature"],"gold_frame_permutation":[FRAMES[x] for x in perm]})

 failures=[];checks=[];lengths={};groups=defaultdict(list)
 reserved=set((ROOT/"sitemap_95_urls.txt").read_text(encoding="utf-8").splitlines()) if (ROOT/"sitemap_95_urls.txt").exists() else set()
 malformed=["영어회화을","영어과외을","비즈니스영어을","문항를","질의을","응시이","근거이","근거은","제한 제한","'질문 이해'과","페이지은"]
 forbidden=["V4.5 FULL-DEPTH PILOT","V4.5 EXAM FULL-DEPTH PILOT","5×7 소규모 검수용","이 프로젝트에서는"]
 byloc=defaultdict(set)
 for meta in files:
  name=Path(meta["path"]).name;raw=generated[name];text=visible(raw);lengths[name]=len(text);f=[]
  if len(re.findall(r"<h1\b",raw))!=1:f.append("h1_count")
  if f"<h1>{html.escape(meta['h1'])}</h1>" not in raw:f.append("h1_exact")
  if f'rel="canonical" href="{meta["canonical"]}"' not in raw:f.append("canonical")
  if 'name="robots" content="noindex,nofollow"' not in raw:f.append("noindex")
  if 'data-production-deploy="false"' not in raw:f.append("production_flag")
  if 'class="decision-strip"' not in raw or 'class="mid-cta"' not in raw or 'decision-guide' not in raw or raw.count("◆ ")<5:f.append("benchmark_blocks")
  if any(x in text for x in ["최고의 강사진","성적 향상을 책임","지금 바로 상담 신청"]):f.append("generic_marketing_copy")
  try:
   js=re.search(r'<script type="application/ld\+json">(.*?)</script>',raw,re.S).group(1);json.loads(js)
  except Exception:f.append("schema_invalid")
  if any(x in text for x in malformed):f.append("malformed_korean")
  if any(x in text for x in forbidden):f.append("pilot_copy")
  if any(x in text for x in ["place_id","official_code","content_seed","variation_pack_id"]):f.append("db_internal_visible")
  if "-tos.html" in raw.lower():f.append("standalone_tos")
  if meta["canonical"] in reserved:f.append("reserved_95_conflict")
  byloc[meta["locality"]].add(name)
  lo,hi=(4000,7200) if meta["family"]=="service" else (4500,7600)
  if not(lo<=len(text)<=hi):f.append(f"visible_chars:{len(text)}")
  checks.append({"file":name,"intent":meta["intent"],"family":meta["family"],"visible_chars":len(text),"status":"PASS" if not f else "FAIL","failures":f})
  if f:failures.append({"file":name,"failures":f})
  groups[meta["intent"]].append((meta["locality"],text))
 for meta in files:
  name=Path(meta["path"]).name;raw=generated[name];expected={x for x in byloc[meta["locality"]] if x!=name};linked=set(re.findall(r'href="([^"]+\.html)"',raw))
  if expected-linked:failures.append({"file":name,"failures":["missing_local_cluster_links"]})
 pairs=[];maxc=maxj=0.0
 for intent,docs in groups.items():
  for (a,ta),(b,tb) in combinations(docs,2):
   c=cosine(ta,tb);j=jacc(ta,tb);maxc=max(maxc,c);maxj=max(maxj,j);pair={"intent":intent,"a":a,"b":b,"cosine":round(c,4),"jaccard5":round(j,4)};pairs.append(pair)
   if c>=0.82 or j>=0.24:failures.append({"pair":[intent,a,b],"failures":[f"duplicate:{c:.4f}/{j:.4f}"]})
 if len(generated)!=130:failures.append({"global":["page_count",len(generated)]})
 if len({m["canonical"] for m in files})!=130:failures.append({"global":["canonical_unique"]})
 qa={"version":"1.0","status":"PASS" if not failures else "FAIL","stage":"STAGE3_10_LOCALITIES_X_13_INTENTS","page_count":len(generated),"locality_count":10,"intent_count":13,"visible_chars":{"min":min(lengths.values()),"max":max(lengths.values()),"avg":round(sum(lengths.values())/len(lengths),1)},"static_failures":len([x for x in failures if "file" in x or "global" in x]),"duplicate_gate":{"status":"PASS" if maxc<0.82 and maxj<0.24 else "FAIL","pairs":len(pairs),"max_cosine":round(maxc,4),"max_5_shingle_jaccard":round(maxj,4),"thresholds":{"cosine_lt":0.82,"jaccard5_lt":0.24},"top_pairs":sorted(pairs,key=lambda x:(x["jaccard5"],x["cosine"]),reverse=True)[:20]},"checks":checks,"failures":failures,"render_qa":"PENDING","safety":{"robots":"noindex,nofollow","live_lead_submission":False,"sitemap":False,"main_merge":False,"production_deploy":False}}
 (OUT/"STAGE3_10X13_QA_V1.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 if failures:
  print(json.dumps({"status":"FAIL","visible":qa["visible_chars"],"duplicate":qa["duplicate_gate"],"failures":failures[:60]},ensure_ascii=False));raise SystemExit(1)
 for name,raw in generated.items():(OUT/name).write_text(raw,encoding="utf-8")
 manifest={"version":"1.0","status":"STAGE3_130_STATIC_DUPLICATE_PASS_RENDER_PENDING_HUMAN_REVIEW_REQUIRED_NOT_PRODUCTION","stage":"STAGE3_10_LOCALITIES_X_13_INTENTS","page_count":130,"locality_count":10,"intent_count":13,"input":"stage3_localities_10_v1.json","gold_sources":{"service":"V4_5_GOLD_SAMPLE_FREEZE_20260922.json","exam":"pilot-v45-exam-5x6/PILOT_EXAM_5X6_GOLD_FREEZE_V1.md","reference_analysis":"EXAM_REFERENCE_ANALYSIS_V1.md"},"localities":[dict(r,gold_frame_permutation=[FRAMES[x] for x in PERMS[i]]) for i,r in enumerate(rows)],"files":files,"safety":{"robots":"noindex,nofollow","live_lead_submission":False,"sitemap":False,"main_merge":False,"production_deploy":False}}
 (OUT/"STAGE3_10X13_MANIFEST_V1.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":"PASS","pages":130,"visible":qa["visible_chars"],"max_cosine":qa["duplicate_gate"]["max_cosine"],"max_jaccard5":qa["duplicate_gate"]["max_5_shingle_jaccard"]},ensure_ascii=False))

if __name__=="__main__":main()
