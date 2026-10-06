#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render Stage 9 mass pages from audited Gold content, not Stage 5 lexical noise."""
from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import os
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
ACADEMY_BASE = {
    "toeic-academy": "toeic",
    "toeic-speaking-academy": "toeic-speaking",
    "opic-academy": "opic",
    "ielts-academy": "ielts",
    "duolingo-academy": "duolingo",
    "toefl-academy": "toefl",
}
ACADEMY_ORDER = list(ACADEMY_BASE)
ACADEMY_SERVICE = {
    "toeic-academy": "토익학원",
    "toeic-speaking-academy": "토익스피킹학원",
    "opic-academy": "오픽학원",
    "ielts-academy": "아이엘츠학원",
    "duolingo-academy": "듀오링고학원",
    "toefl-academy": "토플학원",
}

CONV_DERIVED_BASE = {
    "english-conv-academy": "housewife-conv",
    "adult-english-conv-academy": "housewife-conv",
    "worker-english-conv-academy": "biz-business-conv",
    "beginner-english-conv": "housewife-conv",
}
CONV_DERIVED_ORDER = list(CONV_DERIVED_BASE)
CONV_DERIVED_SERVICE = {
    "english-conv-academy": "영어회화학원",
    "adult-english-conv-academy": "성인영어회화학원",
    "worker-english-conv-academy": "직장인영어회화학원",
    "beginner-english-conv": "왕초보영어회화",
}
CONV_ACADEMY_INTENTS = {
    "english-conv-academy",
    "adult-english-conv-academy",
    "worker-english-conv-academy",
}

CONV_DERIVED_PROFILE = {
    "english-conv-academy": {
        "audience":"영어회화를 배우려는 학습자",
        "service_h1":"영어회화학원","service_body":"영어회화 수업",
        "theme":"theme-univ","blueprint":"v4-derived-general-conv-academy",
        "intro_q":"영어회화학원을 알아볼 때, 수업 인원보다 내가 직접 말하고 피드백받는 시간을 확인해보셨나요?",
        "scope":"영어회화는 문법 설명을 많이 듣는 것보다 질문을 듣고 직접 답하고, 고친 표현을 다시 말해보는 시간이 중요합니다.",
        "boundary":"정해진 진도와 그룹 활동이 잘 맞는 경우도 있고, 현재 수준과 목적에 맞춰 말하기 비중과 피드백을 조정해야 하는 경우도 있습니다.",
        "priority":["현재 말하기 수준 확인","질문을 듣고 첫 문장 시작","문장을 조금씩 길게 확장","피드백 후 다른 질문으로 다시 말하기"],
        "deep":[
            ["말하는 시간이 실제로 얼마나 되는지 확인합니다","영어회화 수업은 수업 시간이 길어도 직접 말하는 시간이 짧으면 연습량이 부족할 수 있습니다. 설명과 활동 비중보다 내가 질문을 받고 답하는 시간이 충분한지 확인하는 편이 좋습니다."],
            ["피드백은 바로 다시 말해볼 수 있어야 합니다","틀린 표현을 알려주는 것에서 끝나지 않고 고친 문장을 다시 말해보면 어떤 부분이 아직 어려운지 확인하기 쉽습니다."],
            ["수업 밖 복습도 짧고 구체적으로 잡습니다","많은 숙제보다 수업에서 고친 문장 몇 개를 다시 말하거나 짧게 녹음하는 방식이 회화 복습에는 더 직접적일 수 있습니다."],
        ],
        "faq":[
            ["영어를 거의 못해도 시작할 수 있나요?","가능합니다. 현재 할 수 있는 인사·자기소개·짧은 답변부터 확인하고 문장 길이를 단계적으로 늘립니다."],
            ["문법도 같이 배우나요?","말할 때 반복해서 막히는 문법은 필요한 만큼 설명하고 바로 문장으로 다시 사용합니다."],
            ["원어민 수업이 꼭 필요한가요?","강사의 국적보다 현재 수준에서 충분히 말하고 이해 가능한 피드백을 받을 수 있는지가 더 중요합니다."],
            ["수업은 얼마나 자주 하는 게 좋나요?","목표와 가능한 복습 시간에 따라 다릅니다. 무리한 횟수보다 수업 사이에 짧게 다시 말해볼 시간이 있는지 함께 봅니다."],
            ["여행영어와 일상회화를 같이 할 수 있나요?","가능합니다. 가까운 여행 일정이 있다면 여행 상황 비중을 높이고, 이후에는 일상회화로 범위를 넓힐 수 있습니다."],
            ["변화는 어떻게 확인하나요?","첫 문장을 시작하는 속도, 질문이 달라졌을 때 답을 이어가는지, 같은 표현을 다른 상황에도 쓰는지 확인합니다."],
        ],
        "reader_intro":{"kicker":"영어회화 수업 선택","h2":"영어회화학원을 고를 때는 ‘얼마나 직접 말하는지’부터 확인해보세요","p1":"회화는 설명을 많이 듣는 것보다 질문을 듣고 직접 답하고, 바로 피드백받은 뒤 다시 말해보는 시간이 중요합니다.","p2":"현재 수준과 목적을 먼저 확인하고 일상·여행·학교·업무처럼 실제로 영어가 필요한 상황에 맞춰 수업 비중을 정합니다."},
        "management_focus":["매 수업 직접 말하는 시간을 충분히 확보","고친 표현은 바로 다시 말해보며 확인","수업 후 짧은 복습을 다음 수업과 연결"],
    },
    "adult-english-conv-academy": {
        "audience":"성인","service_h1":"성인영어회화학원","service_body":"성인 영어회화 수업",
        "theme":"theme-housewife","blueprint":"v4-derived-adult-conv-academy",
        "intro_q":"성인영어회화학원을 찾고 있지만, 여행·생활·자기계발 중 어떤 영어가 가장 필요한지 정해보셨나요?",
        "scope":"성인 회화는 영어를 다시 시작하는 이유와 가능한 학습 시간이 사람마다 다릅니다. 기초 문장부터 여행·생활 대화까지 현재 목적에 맞춰 범위를 좁히는 편이 좋습니다.",
        "boundary":"공인시험 점수가 급하거나 업무 발표·면접처럼 목적이 뚜렷하다면 해당 목적에 맞춘 과정이 일반 성인회화보다 더 직접적일 수 있습니다.",
        "priority":["현재 말할 수 있는 문장 확인","생활·여행 등 가까운 목적 선택","짧은 질문·답변 반복","꾸준히 이어갈 복습량 정하기"],
        "deep":[
            ["오랜만에 영어를 시작해도 기초부터 다시 잡을 수 있습니다","처음부터 어려운 표현을 외우기보다 지금 말할 수 있는 짧은 문장을 확인하고 자주 필요한 상황부터 표현을 늘립니다."],
            ["생활에 맞는 복습량이 중요합니다","성인은 일정이 자주 바뀔 수 있으므로 매일 많은 양보다 10분 안팎으로 다시 말해볼 수 있는 분량을 정하는 편이 지속하기 쉽습니다."],
            ["목표가 바뀌면 수업 내용도 조정합니다","여행을 앞두고 있다면 여행 표현을 먼저 보고 일정이 끝난 뒤에는 일상 대화나 자기계발 목표로 자연스럽게 전환할 수 있습니다."],
        ],
        "faq":[
            ["나이가 있어도 회화를 시작하기 늦지 않나요?","나이보다 현재 수준과 실제 사용할 목적이 더 중요합니다. 짧은 문장부터 시작할 수 있습니다."],
            ["기초 문법을 다 끝내고 회화를 해야 하나요?","모든 문법을 먼저 끝낼 필요는 없습니다. 자주 쓰는 문장을 말하면서 필요한 문법을 함께 정리할 수 있습니다."],
            ["여행을 앞두고 단기간 준비도 가능한가요?","가능합니다. 출국 일정과 자주 사용할 상황을 기준으로 범위를 줄여 준비합니다."],
            ["숙제가 많으면 부담스러운데 괜찮을까요?","가능한 시간에 맞춰 짧게 반복할 수 있는 분량을 정합니다."],
            ["온라인과 방문 중 어떤 방식이 좋나요?","이동 시간, 말하기 환경, 자료 공유 방식과 일정에 따라 편한 방식을 비교하는 것이 좋습니다."],
            ["변화는 어떻게 확인하나요?","익숙한 질문에 답하는 것뿐 아니라 질문 표현이 달라졌을 때도 문장을 시작하고 이어갈 수 있는지 봅니다."],
        ],
        "reader_intro":{"kicker":"성인 영어회화","h2":"다시 시작하는 영어라면, 어려운 표현보다 자주 쓸 문장부터 시작합니다","p1":"여행·생활영어·자기계발처럼 영어를 다시 시작하는 이유를 먼저 확인하고 현재 말할 수 있는 수준에서 시작합니다.","p2":"짧은 질문과 답변을 반복하고, 수업에서 고친 표현을 생활 속 다른 상황에서도 다시 쓸 수 있게 연습합니다."},
        "management_focus":["생활·여행 등 가까운 목표부터 정리","현재 수준에서 바로 말할 수 있는 문장부터 시작","부담 없는 복습량으로 꾸준히 이어가기"],
    },
    "worker-english-conv-academy": {
        "audience":"직장인","service_h1":"직장인영어회화학원","service_body":"직장인 영어회화 수업",
        "theme":"theme-worker","blueprint":"v4-derived-worker-conv-academy",
        "intro_q":"직장인영어회화학원을 찾는 이유가 막연한 회화보다 다음 회의·발표·전화 때문은 아닌가요?",
        "scope":"직장인 회화는 업무에서 실제로 영어를 쓰는 상황이 분명한 경우가 많습니다. 회의·발표·전화·고객 응대 중 가까운 일정부터 준비하면 범위를 줄일 수 있습니다.",
        "boundary":"TOEIC·OPIc·TOEIC Speaking 등 점수나 등급 제출이 목적이라면 일반 직장인 회화보다 해당 시험 과정이 더 직접적입니다.",
        "priority":["가장 가까운 업무 일정 확인","회의·발표·전화 중 우선 상황 선택","실제 업무 표현을 직접 말해보기","피드백 후 다른 업무 질문으로 확장"],
        "deep":[
            ["업무에서 바로 쓸 문장을 먼저 준비합니다","회화 전체를 배우기보다 다음 회의에서 의견 말하기, 발표에서 수치 설명하기처럼 실제 업무 행동으로 범위를 줄입니다."],
            ["회의 영어는 길게 말하는 것만 중요하지 않습니다","짧게 의견을 내고, 확인 질문을 하고, 상대 의견에 반응하는 표현도 실제 회의 참여에 중요합니다."],
            ["민감한 업무자료는 일반화해서 연습합니다","회사명·금액·고객정보는 가상의 내용으로 바꾸고 설명 구조와 질문 방식만 살려 연습할 수 있습니다."],
        ],
        "faq":[
            ["비즈니스영어와 일반 회화가 많이 다른가요?","기본 대화 구조는 겹치지만 회의·발표·전화처럼 업무 목적이 분명해 필요한 표현과 피드백이 달라질 수 있습니다."],
            ["업무자료를 수업에 가져가도 되나요?","민감정보를 제거하거나 일반화한 뒤 필요한 설명·질문 구조만 활용하는 편이 안전합니다."],
            ["회의와 발표를 같이 준비할 수 있나요?","가능하지만 가장 가까운 일정에 더 많은 시간을 배정합니다."],
            ["영어가 기초인데 업무회화를 바로 시작해도 되나요?","가능합니다. 업무에서 꼭 필요한 짧은 문장부터 정리하면서 기초 표현을 함께 보완할 수 있습니다."],
            ["전화영어처럼 말하기만 하나요?","말하기가 중심이지만 필요한 듣기, 이메일·슬라이드 설명과 연결할 수도 있습니다."],
            ["변화는 어떻게 확인하나요?","실제 업무 질문에 첫 문장을 시작하는 속도, 핵심을 짧게 설명하는지, 추가 질문에 대응하는지 확인합니다."],
        ],
        "reader_intro":{"kicker":"직장인 영어회화","h2":"회의·발표·전화처럼 실제 업무에서 필요한 영어부터 준비합니다","p1":"업무에서 영어를 쓰는 상황과 가장 가까운 일정을 먼저 확인하면 불필요하게 넓은 범위를 공부하지 않아도 됩니다.","p2":"실제 업무에 가까운 질문과 설명을 직접 말해보고, 피드백 후 같은 내용을 다른 표현으로 다시 말해보며 준비합니다."},
        "management_focus":["가장 가까운 회의·발표·전화 일정부터 준비","실제 업무 표현을 직접 말하고 바로 교정","업무 변화에 따라 다음 수업 주제를 유연하게 조정"],
    },
    "beginner-english-conv": {
        "audience":"왕초보","service_h1":"왕초보영어회화","service_body":"왕초보 영어회화",
        "theme":"theme-housewife","blueprint":"v4-derived-beginner-conv",
        "intro_q":"영어를 보면 아는 단어는 있는데, 막상 한 문장을 말하려면 어디서 시작해야 할지 모르겠나요?",
        "scope":"왕초보 회화는 많은 문법과 단어를 먼저 끝내기보다 인사·자기소개·기본 질문처럼 자주 쓰는 짧은 문장을 직접 말하는 데서 시작합니다.",
        "boundary":"시험 점수나 면접 일정이 급하다면 왕초보 회화 전체보다 해당 목표에 필요한 표현을 먼저 보는 편이 직접적일 수 있습니다.",
        "priority":["인사·자기소개 한두 문장","be동사와 기본 문장 구조","짧은 질문을 듣고 한 문장으로 답하기","생활 표현을 조금씩 늘리기"],
        "deep":[
            ["문법을 다 끝낸 뒤 말하기를 시작하지 않습니다","기본 문장을 말하면서 필요한 문법을 함께 확인하면 배운 내용이 실제 표현과 연결되기 쉽습니다."],
            ["한 문장을 여러 상황에 바꿔 써봅니다","외운 예문 하나로 끝내지 않고 사람·장소·시간을 바꿔 같은 문장 구조를 여러 번 사용합니다."],
            ["짧게 자주 말하는 것이 중요합니다","처음부터 긴 대화를 목표로 하기보다 하루에 몇 문장이라도 소리 내어 말하고 다음 수업에서 다시 확인합니다."],
        ],
        "faq":[
            ["알파벳만 아는 수준도 가능한가요?","현재 읽기와 듣기 수준을 먼저 확인하고 필요한 경우 아주 짧은 기초 문장부터 시작할 수 있습니다."],
            ["문법책부터 한 권 끝내야 하나요?","모든 문법을 먼저 끝낼 필요는 없습니다. 말할 때 필요한 기본 구조부터 함께 정리합니다."],
            ["단어를 많이 외워야 하나요?","자주 쓸 단어부터 늘리되 단어만 외우지 않고 문장 안에서 직접 사용합니다."],
            ["발음이 좋지 않아도 괜찮나요?","완벽한 발음보다 상대가 이해할 수 있게 말하고 듣는 것이 먼저입니다. 반복해서 막히는 소리는 필요한 만큼 교정합니다."],
            ["얼마나 해야 말이 나오기 시작하나요?","기간을 단정하기보다 처음에는 인사·소개·기본 질문처럼 확인 가능한 작은 목표를 정합니다."],
            ["복습은 어떻게 하나요?","수업에서 사용한 짧은 문장을 다시 말하거나 녹음하고, 다음 수업에서 질문을 조금 바꿔 다시 답해봅니다."],
        ],
        "reader_intro":{"kicker":"왕초보 영어회화","h2":"문법책 한 권보다, 오늘 직접 말할 한 문장부터 시작합니다","p1":"아는 단어는 있지만 문장으로 말하기 어렵다면 인사·자기소개·기본 질문처럼 자주 쓰는 표현부터 직접 말해봅니다.","p2":"짧은 문장을 충분히 익힌 뒤 사람·장소·시간을 바꿔 다시 말하면서 자연스럽게 문장 범위를 넓혀갑니다."},
        "management_focus":["인사·자기소개 등 가장 쉬운 말하기부터 시작","기본 문장 구조를 실제 말하기와 함께 정리","짧은 복습으로 같은 문장을 다른 질문에도 사용"],
    },
}

CONV_DERIVED_SOURCE = {
    "english-conv-academy": {
        "cards":[("첫 문장 시작","질문은 이해했지만 첫 문장을 바로 시작하기 어려운 경우입니다."),("질문에 답하기","외운 문장은 말할 수 있지만 질문 표현이 달라지면 답이 짧아지는 경우입니다."),("문장 확장","한두 단어로 답한 뒤 이유나 예시를 붙이는 것이 어려운 경우입니다."),("다른 상황에 적용","수업에서 배운 표현을 다른 사람·장소·주제에서도 다시 쓰기 어려운 경우입니다.")],
        "steps":["현재 말하기 확인","필요한 표현 정리","질문·답변 연습","피드백 후 다시 말하기","짧은 복습과 다음 수업 연결"],
        "proofs":["첫 문장 반응","질문 이해","문장 길이","표현 교정","다른 질문 대응","수업 후 복습"],
        "feedback":"짧은 질문에는 바로 답할 수 있었지만 이유를 붙일 때 문장이 끊겼다면, 다음 수업에서는 이유를 연결하는 표현 두세 개를 먼저 연습합니다.",
    },
    "adult-english-conv-academy": {
        "cards":[("기초 문장","아는 단어는 있지만 문장으로 연결하는 것이 어려운 경우입니다."),("생활 대화","여행·식당·쇼핑처럼 익숙한 상황에서도 바로 표현이 떠오르지 않는 경우입니다."),("듣고 답하기","천천히 들으면 이해하지만 바로 답하는 데 시간이 필요한 경우입니다."),("꾸준한 복습","수업 때는 되지만 며칠 뒤 같은 표현을 다시 꺼내기 어려운 경우입니다.")],
        "steps":["현재 수준 확인","가까운 목표 선택","기본 문장 연습","상황을 바꿔 다시 말하기","생활에 맞는 복습 정리"],
        "proofs":["기본문장","첫 반응","생활표현","듣기 이해","다른 상황 적용","복습 유지"],
        "feedback":"여행 상황에서는 준비한 표현을 말했지만 질문이 조금 달라지면 멈췄다면, 같은 의미의 질문을 여러 방식으로 듣고 답하는 연습을 이어갑니다.",
    },
    "worker-english-conv-academy": {
        "cards":[("회의 참여","의견은 있지만 영어로 끼어드는 첫 문장이 늦는 경우입니다."),("업무 설명","제품·프로젝트·수치를 짧고 명확하게 설명하기 어려운 경우입니다."),("전화·화상","못 들은 부분을 다시 묻거나 확인하는 표현이 바로 나오지 않는 경우입니다."),("발표·Q&A","준비한 발표는 가능하지만 추가 질문에서 답이 길어지거나 끊기는 경우입니다.")],
        "steps":["업무 일정 확인","핵심 표현 정리","실제 질문으로 말하기","피드백 후 다시 답하기","다음 업무에 맞춰 조정"],
        "proofs":["회의 첫 반응","업무 설명","확인 질문","발표 구조","추가 질문 대응","실제 업무 적용"],
        "feedback":"회의에서 의견의 핵심은 말했지만 근거를 붙이는 데 시간이 길어졌다면, 다음에는 결론 한 문장과 이유 한 문장을 묶어 여러 안건으로 연습합니다.",
    },
    "beginner-english-conv": {
        "cards":[("인사와 자기소개","이름과 기본 정보도 영어로 말하려면 문장을 먼저 떠올려야 하는 경우입니다."),("기본문장 만들기","단어는 알지만 주어와 동사를 넣어 한 문장으로 만드는 것이 어려운 경우입니다."),("짧은 질문·대답","질문을 들었을 때 Yes/No 뒤에 한 문장을 이어 말하기 어려운 경우입니다."),("생활 표현","배운 문장을 실제 생활 상황으로 바꾸어 쓰는 것이 아직 익숙하지 않은 경우입니다.")],
        "steps":["현재 기초 확인","가장 쉬운 문장 만들기","소리 내어 반복","질문을 바꿔 다시 답하기","짧은 복습으로 연결"],
        "proofs":["인사·소개","기본문장","질문 이해","한 문장 답변","생활표현","다른 질문 적용"],
        "feedback":"자기소개는 준비한 순서대로 말할 수 있지만 질문 순서가 바뀌면 멈췄다면, 같은 내용을 질문형으로 바꿔 짧게 답하는 연습을 추가합니다.",
    },
}
EXAM_THEME = {
    "toeic": "theme-toeic",
    "toeic-speaking": "theme-toeic-speaking",
    "opic": "theme-opic",
    "ielts": "theme-ielts",
    "duolingo": "theme-duolingo",
    "toefl": "theme-toefl",
}
VARIATIONS = ["scene","deadline","error","use","reuse"]

TITLE_VARIANTS = {
    "elem-tutor": ["읽기·문장기초 진단", "학교영어·기초문장", "기초영어·문장훈련"],
    "mid-conv": ["수행평가·질문대응", "발표·말하기훈련", "학교영어·회화훈련"],
    "high-conv": ["수행평가·발표·질문대응", "발표·면접·말하기훈련", "학교영어·실전말하기"],
    "univ-conv": ["발표·세미나·면접영어", "대학수업·발표영어", "교환학생·면접·회화"],
    "jobseeker-conv": ["영어면접·답변훈련", "취업면접·자기소개", "면접질문·답변구성"],
    "biz-business-conv": ["회의·발표·업무영어", "비즈니스 회의·발표", "업무회화·회의영어"],
    "housewife-conv": ["여행·생활영어", "기초회화·여행영어", "생활회화·말하기기초"],
    "toeic": ["LC·RC 오답·시간관리", "파트별 약점·실전훈련", "시험일·오답원인 진단"],
    "toeic-speaking": ["답변구조·시간훈련", "파트별 답변·실전훈련", "말하기 약점·답변구성"],
    "opic": ["돌발질문·답변구성", "목표등급·실전답변", "말하기 약점·답변훈련"],
    "ielts": ["IELTS 4영역·Band 진단", "Writing·Speaking 피드백", "목표 Band·4영역 훈련"],
    "duolingo": ["실전유형·시간훈련", "DET 유형·실전훈련", "목표점수·문항대응"],
    "toefl": ["4영역·실전훈련", "TOEFL 4영역·시간관리", "Reading·Listening·말하기·쓰기"],
    "toeic-academy": ["수업방식·LC·RC 관리 비교", "학원수업·1:1 관리 비교", "시험일·파트별 관리 확인"],
    "toeic-speaking-academy": ["문항별 피드백·수업방식 비교", "학원수업·1:1 말하기 관리", "녹음·답변 피드백 비교"],
    "opic-academy": ["돌발·롤플레이 관리 비교", "학원수업·1:1 답변 피드백", "녹음·답변관리 방식 비교"],
    "ielts-academy": ["4영역·첨삭관리 비교", "IELTS 학원수업·1:1 비교", "Writing·Speaking 관리 확인"],
    "duolingo-academy": ["DET 유형·응답관리 비교", "듀오링고 학원수업·1:1 비교", "Speaking·Writing 관리 확인"],
    "toefl-academy": ["4영역·통합형 관리 비교", "TOEFL 학원수업·1:1 비교", "Speaking·Writing 피드백 비교"],
    "english-conv-academy": ["말하기시간·피드백 방식 비교", "영어회화 수업·관리방식 비교", "기초·실전회화 수업 비교"],
    "adult-english-conv-academy": ["기초·생활·여행회화 비교", "성인회화 수업·관리 비교", "초보부터 생활회화까지"],
    "worker-english-conv-academy": ["회의·발표·업무회화 비교", "직장인회화 수업·관리 비교", "업무 말하기·피드백 방식"],
    "beginner-english-conv": ["기초문장·첫 말하기", "왕초보 기초회화·말하기", "인사·자기소개부터 시작"],
}

EMAILJS_TAG = '<script defer src="https://cdn.jsdelivr.net/npm/@emailjs/browser@4/dist/email.min.js"></script>'
def consultation_form(loc: dict, h1: str) -> str:
    return f'''<form id="leadForm" class="lead-form">
<label>이름 <span>*</span><input id="leadName" name="name" autocomplete="name" required></label>
<label>연락처 <span>*</span><input id="leadPhone" name="phone" inputmode="tel" autocomplete="tel" placeholder="010-0000-0000" required></label>
<label>지역 <span>*</span><input id="leadArea" name="area" value="{esc(loc["dong"])}" required></label>
<label class="full">문의내용<textarea id="leadMessage" name="message" rows="4" placeholder="현재 어려운 부분, 목표하는 부분을 자유롭게 작성해주세요."></textarea></label>
<input type="hidden" id="leadClass" name="wantedClass" value="{esc(h1)}">
<label class="privacy-check"><input id="leadConsent" name="consent" type="checkbox" required> <span>상담을 위한 개인정보 수집·이용에 동의합니다.</span></label>
<details class="privacy-detail"><summary>수집·이용 안내</summary><p>수집 항목: 이름, 연락처, 지역, 문의내용. 이용 목적: 영어 학습 상담 및 연락. 상담 목적이 끝난 개인정보는 관계 법령상 보존 의무가 없는 한 지체 없이 파기합니다.</p></details>
<button class="submit-lead" type="submit">무료 PT 진단 신청 →</button>
<p class="form-alt">전송이 어려운 경우 <a href="tel:01050068027">010-5006-8027</a> 또는 <a href="mailto:cicada3865@naver.com">cicada3865@naver.com</a>로 문의할 수 있습니다.</p>
<div id="leadStatus" class="pilot-status lead-status" role="status" aria-live="polite"></div>
</form>'''


IMAGE_FAMILY = {
    "elem-tutor":"school",
    "mid-conv":"school-talk",
    "high-conv":"school-talk",
    "univ-conv":"campus",
    "jobseeker-conv":"interview",
    "biz-business-conv":"business",
    "housewife-conv":"conversation",
    "english-conv-academy":"conversation",
    "adult-english-conv-academy":"conversation",
    "worker-english-conv-academy":"business",
    "beginner-english-conv":"conversation",
    "toeic":"toeic",
    "toeic-academy":"toeic",
    "toeic-speaking":"speaking",
    "toeic-speaking-academy":"speaking",
    "opic":"speaking",
    "opic-academy":"speaking",
    "ielts":"four-skills",
    "ielts-academy":"four-skills",
    "toefl":"four-skills",
    "toefl-academy":"four-skills",
    "duolingo":"digital-test",
    "duolingo-academy":"digital-test",
}

IMAGE_CAPTION = {
    "school":"학교 일정과 현재 수준에 맞춰 필요한 영어부터 준비합니다.",
    "school-talk":"학교 영어를 발표·질문 대응 말하기로 연결합니다.",
    "campus":"발표·세미나·면접에 필요한 영어부터 준비합니다.",
    "interview":"영어면접 답변을 질문에 맞게 말하는 연습을 합니다.",
    "business":"회의·발표·전화에 필요한 업무 영어를 연습합니다.",
    "conversation":"직접 말하고 고친 표현을 다시 말하는 시간을 늘립니다.",
    "toeic":"LC·RC 오답과 시간 사용을 확인해 필요한 파트부터 관리합니다.",
    "speaking":"답변을 녹음하며 구성과 제한 시간을 함께 점검합니다.",
    "four-skills":"4영역을 나눠 목표 점수에 필요한 영역부터 준비합니다.",
    "digital-test":"시험 흐름에 익숙해지며 말하기·쓰기 응답을 연습합니다.",
}


@lru_cache(maxsize=1)
def page_image_config() -> dict:
    path = ROOT / "data" / "stage9-page-images.json"
    if not path.exists():
        return {"defaults": {}, "pages": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"defaults": {}, "pages": {}}
        data.setdefault("defaults", {})
        data.setdefault("pages", {})
        return data
    except Exception:
        return {"defaults": {}, "pages": {}}


def visual_asset(loc: dict, intent: str) -> dict | None:
    config = page_image_config()
    page_key = f'{loc["slug"]}-{intent}.html'
    item = config.get("pages", {}).get(page_key)
    if item is None:
        item = config.get("defaults", {}).get(intent)
    if not item:
        return None
    if isinstance(item, str):
        item = {"src": item}
    if not isinstance(item, dict) or not item.get("src"):
        return None
    family = IMAGE_FAMILY.get(intent, "conversation")
    return {
        "src": item["src"],
        "alt": item.get("alt") or f'{loc["dong"]} {loc["service"]} 수업 이미지',
        "caption": item.get("caption") or IMAGE_CAPTION.get(family, ""),
        "width": int(item.get("width", 1200)),
        "height": int(item.get("height", 720)),
        "loading": item.get("loading", "eager"),
    }


def visual_section(loc: dict, intent: str, h1: str) -> str:
    asset = visual_asset(loc, intent)
    if not asset:
        return ""
    caption = (
        f'<figcaption>{esc(asset["caption"])}</figcaption>'
        if asset.get("caption") else ""
    )
    return (
        '<section class="visual-break"><div class="wrap">'
        '<figure class="learning-visual">'
        f'<img src="{esc(asset["src"])}" width="{asset["width"]}" height="{asset["height"]}" '
        f'loading="{esc(asset["loading"])}" decoding="async" alt="{esc(asset["alt"])}">'
        + caption +
        '</figure></div></section>'
    )



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
    for intent in sorted(SERVICE_ORDER + EXAM_ORDER + ACADEMY_ORDER + CONV_DERIVED_ORDER, key=len, reverse=True):
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
    elif intent in ACADEMY_BASE:
        service = ACADEMY_SERVICE[intent]
    elif intent in CONV_DERIVED_BASE:
        service = CONV_DERIVED_SERVICE[intent]
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
    skip_topics={"locality-honesty","alternative-path","transfer"}
    pool=[m for m in TOPIC_MODULES if family in m["families"] and m["key"] not in skip_topics]
    base_intent = ACADEMY_BASE.get(intent, intent)
    if family == "exam" and base_intent == "toeic-speaking":
        count = 6
    elif family == "exam" and base_intent == "opic" and intent in ACADEMY_ORDER:
        count = 6
    elif family == "exam" and base_intent == "opic":
        count = 7
    elif family == "exam" and intent == "toefl-academy":
        count = 7
    elif family == "exam" and intent in ACADEMY_ORDER and base_intent in EXAM_READER_PILOT_INTENTS:
        count = 6
    elif family == "exam" and base_intent in EXAM_READER_PILOT_INTENTS:
        count = 8
    elif intent == "worker-english-conv-academy":
        count = 5
    elif intent in {"univ-conv","jobseeker-conv"}:
        count = 7
    else:
        count = 6
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
        '<p class="kicker">수업 비교 기준</p>'
        '<h2>수업을 비교할 때는 이런 부분을 확인해보세요</h2>'
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


def base_exam_intent(intent: str) -> str:
    return ACADEMY_BASE.get(intent, intent)


def is_academy_intent(intent: str) -> bool:
    return intent in ACADEMY_BASE or intent in CONV_ACADEMY_INTENTS


def theme_for_intent(intent: str, family: str) -> str:
    if intent in CONV_DERIVED_PROFILE:
        suffix = " intent-academy" if intent in CONV_ACADEMY_INTENTS else " intent-audience"
        return CONV_DERIVED_PROFILE[intent]["theme"] + suffix
    if family == "service":
        return gold_modules()[0].PROFILES[intent]["theme"] + " intent-audience"
    base = base_exam_intent(intent)
    theme = EXAM_THEME.get(base, "theme-test")
    return theme + (" intent-academy" if is_academy_intent(intent) else " intent-test")


def conversation_academy_compare_section(loc: dict, intent: str) -> str:
    service = CONV_DERIVED_SERVICE[intent]
    focus = {
        "english-conv-academy":"직접 말하는 시간·개인 피드백·복습 연결",
        "adult-english-conv-academy":"기초 수준·생활/여행 목표·꾸준한 복습",
        "worker-english-conv-academy":"회의·발표·전화 등 업무 상황별 피드백",
    }[intent]
    cards = [
        ("수업 인원과 말하기 시간","몇 명이 함께 듣는지보다 한 수업에서 내가 실제로 질문을 받고 말하는 시간이 얼마나 되는지 확인합니다."),
        ("현재 수준에 맞는 시작점","정해진 교재 진도를 그대로 따라가는지, 현재 말할 수 있는 범위에서 시작점을 조정하는지 비교합니다."),
        ("피드백 방식","표현을 고쳐주는 데서 끝나는지, 고친 문장을 다시 말해보고 다음 질문에도 적용하는지 확인합니다."),
        ("수업 후 관리",f"{focus}이 수업 밖 복습과 다음 수업에 어떻게 이어지는지 살펴봅니다."),
    ]
    digest = int(hashlib.sha256(f'{loc["slug"]}|{intent}|conv-academy'.encode()).hexdigest()[:8],16)
    shift = digest % len(cards)
    cards = cards[shift:] + cards[:shift]
    card_html = ''.join(
        f'<article><span>{i:02d}</span><h3>{esc(t)}</h3><p>{esc(p)}</p></article>'
        for i,(t,p) in enumerate(cards,1)
    )
    return (
        '<section class="section academy-choice"><div class="wrap">'
        '<p class="kicker">수업 방식 비교</p>'
        f'<h2>{esc(loc["dong"])} {esc(service)}, 학원 이름보다 실제 말하기와 피드백 방식을 먼저 비교해보세요</h2>'
        '<p class="academy-disclosure">ENGLISH PT는 특정 오프라인 학원으로 소개하는 페이지가 아닙니다. '
        '영어회화학원을 검색하는 분이 그룹형 수업과 1:1 맞춤 수업의 차이를 비교할 수 있도록 수업 방식과 관리 기준을 정리했습니다.</p>'
        '<div class="academy-compare">' + card_html + '</div>'
        '<div class="academy-fit">'
        '<div><b>학원형 수업이 잘 맞을 수 있는 경우</b><p>정해진 시간과 커리큘럼을 따라 꾸준히 배우는 방식이 편하고, 여러 학습자와 함께 연습하는 환경이 잘 맞는 경우입니다.</p></div>'
        '<div><b>1:1 방식이 잘 맞을 수 있는 경우</b><p>현재 수준이나 목적이 분명하고, 직접 말하는 시간과 개인 피드백을 더 많이 확보하고 싶은 경우입니다.</p></div>'
        '</div></div></section>'
    )


def academy_compare_section(loc: dict, intent: str) -> str:
    if intent in CONV_ACADEMY_INTENTS:
        return conversation_academy_compare_section(loc, intent)
    if intent not in ACADEMY_BASE:
        return ""
    base = base_exam_intent(intent)
    exam_label = {
        "toeic": "TOEIC",
        "toeic-speaking": "TOEIC Speaking",
        "opic": "OPIc",
        "ielts": "IELTS",
        "duolingo": "Duolingo English Test",
        "toefl": "TOEFL",
    }[base]
    exam_focus = {
        "toeic": "LC·RC 파트별 약점, 오답관리, 시간 배분",
        "toeic-speaking": "문항별 답변 구조, 녹음 피드백, 제한시간 연습",
        "opic": "설문·돌발·롤플레이, 답변 흐름, 녹음 피드백",
        "ielts": "Listening·Reading·Writing·Speaking 4영역, 첨삭과 말하기 피드백",
        "duolingo": "Reading·Listening·Speaking·Writing 응답, 문제 형식 적응과 시간 관리",
        "toefl": "Reading·Listening·Speaking·Writing 4영역과 통합형 연습",
    }[base]

    intro_variants = [
        (
            "학원을 알아보고 있다면",
            f'{loc["dong"]}에서 {ACADEMY_SERVICE[intent]}을 찾을 때, 수업 이름보다 관리방식을 먼저 비교해보세요',
            f'{exam_label} 준비는 같은 학원 이름을 보고 고르기보다 진도·질문·피드백이 어떻게 이어지는지 확인하는 편이 좋습니다.'
        ),
        (
            "수업을 고르기 전에",
            f'{ACADEMY_SERVICE[intent]}을 비교할 때는 내 시험일과 약한 영역부터 기준을 잡아보세요',
            f'{loc["dong"]}에서 {exam_label} 수업을 찾더라도 정해진 진도를 따라갈지, 필요한 영역을 먼저 보완할지에 따라 맞는 방식이 달라질 수 있습니다.'
        ),
        (
            "학원과 1:1을 비교한다면",
            f'{loc["dong"]} {ACADEMY_SERVICE[intent]}, 수업 횟수보다 피드백 범위를 먼저 확인해보세요',
            f'{exam_label}은 문제풀이만으로 끝나지 않는 시험이라 오답·첨삭·녹음·실전연습이 수업 밖에서도 어떻게 이어지는지 보는 것이 중요합니다.'
        ),
        (
            "시험일까지 남은 시간을 본다면",
            f'{ACADEMY_SERVICE[intent]} 선택은 시험일까지 무엇을 관리해주는지까지 확인해야 합니다',
            f'같은 {exam_label} 과정이라도 목표와 시험일, 약한 파트가 다르면 필요한 관리가 달라집니다. {loc["dong"]}에서 수업을 비교할 때 이 차이를 먼저 보세요.'
        ),
    ]
    v = int(hashlib.sha256(f'{loc["slug"]}|{intent}|academy-compare-v2'.encode()).hexdigest()[:8],16) % len(intro_variants)
    kicker, heading, disclosure = intro_variants[v]

    card_sets = [
        [
            ("진도와 질문","정해진 진도를 따라가는 방식이 편한지, 현재 약한 부분을 먼저 다루는 방식이 필요한지 확인합니다."),
            ("피드백 범위","수업 중 설명뿐 아니라 오답·첨삭·녹음처럼 수업 후 확인이 어디까지 이어지는지 비교합니다."),
            (f"{exam_label} 관리",f"{exam_focus} 중 지금 필요한 항목을 얼마나 구체적으로 관리하는지 살펴봅니다."),
            ("일정 조정","시험일이 가까워질 때 과제량·실전연습·보완 영역을 실제 일정에 맞춰 조정할 수 있는지 확인합니다."),
        ],
        [
            ("수업 속도","전체 진도를 일정하게 따라갈지, 약한 파트에 시간을 더 쓸 수 있는지 먼저 물어보는 것이 좋습니다."),
            ("질문과 교정","틀린 이유나 답변 표현을 바로 질문하고 고칠 시간이 충분한지 확인합니다."),
            ("과제 관리",f"{exam_focus}을 수업 밖에서도 이어갈 수 있도록 무엇을 남겨주는지 비교합니다."),
            ("시험 전 운영","시험 직전에는 새 범위를 넓히는지, 실전시간과 반복오답 중심으로 바꾸는지 살펴봅니다."),
        ],
        [
            ("현재 수준 확인","첫 수업 전에 최근 점수나 답변을 보고 어디부터 시작할지 정하는 방식인지 확인합니다."),
            ("개인 피드백","같은 문제를 풀어도 사람마다 틀리는 이유가 다르기 때문에 개인별 설명과 교정 범위를 비교합니다."),
            ("기록과 복습",f"{exam_label} 수업 후 오답·첨삭·녹음 결과가 다음 수업에 어떻게 이어지는지 살펴봅니다."),
            ("일정 맞춤","학교·업무 일정과 시험일을 함께 고려해 현실적인 과제량을 조정할 수 있는지 확인합니다."),
        ],
        [
            ("목표부터 확인","목표 점수·등급과 시험일을 먼저 묻고 계획을 잡는지 확인합니다."),
            ("약한 영역 집중",f"{exam_focus} 가운데 이미 안정된 부분과 더 연습할 부분을 나눠주는지 살펴봅니다."),
            ("피드백 방식","정답 해설만 하는지, 실제 답변·오답을 고쳐서 다시 해보게 하는지 비교합니다."),
            ("다음 수업 연결","그날 끝난 진도보다 다음에 다시 확인할 내용이 남는 수업인지 확인합니다."),
        ],
    ]
    cards = card_sets[v]
    # Rotate card order once more by locality so neighboring pages don't keep
    # identical paragraph sequences while preserving the same comparison logic.
    shift = int(hashlib.sha256(f'{loc["slug"]}|{intent}|academy-order'.encode()).hexdigest()[:4],16) % len(cards)
    cards = cards[shift:] + cards[:shift]
    card_html = ''.join(
        f'<article><span>{i:02d}</span><h3>{esc(title)}</h3><p>{esc(body)}</p></article>'
        for i,(title,body) in enumerate(cards,1)
    )

    fit_variants = [
        (
            "정해진 일정과 진도를 따라가며 꾸준히 학습하는 방식이 편하고, 비슷한 목표의 학습자와 함께 수업하는 환경이 잘 맞는 경우입니다.",
            "시험일이 촉박하거나 특정 파트만 약하고, 오답·답변·첨삭에 개인 피드백이 많이 필요한 경우입니다."
        ),
        (
            "정해진 커리큘럼과 수업 시간이 학습 리듬을 잡는 데 도움이 되고, 전체 범위를 순서대로 배우고 싶은 경우입니다.",
            "이미 잘하는 영역은 줄이고 부족한 부분에 시간을 더 쓰거나, 일정에 맞춰 수업 순서를 자주 조정해야 하는 경우입니다."
        ),
        (
            "혼자 계획을 세우기보다 정해진 수업 흐름을 따라가는 편이 편하고, 전체 시험 구조를 처음부터 익혀야 하는 경우입니다.",
            "특정 유형에서 반복해서 막히거나 말하기·쓰기처럼 개별 교정이 중요한 영역을 집중적으로 준비해야 하는 경우입니다."
        ),
        (
            "일정한 진도와 과제량이 있어야 공부가 꾸준히 이어지고, 전 범위를 균형 있게 확인하고 싶은 경우입니다.",
            "시험일까지 시간이 많지 않거나 현재 점수에서 부족한 영역이 분명해 개인별 연습량과 피드백을 조정해야 하는 경우입니다."
        ),
    ]
    academy_fit, one_fit = fit_variants[v]

    return (
        '<section class="section academy-choice"><div class="wrap">'
        f'<p class="kicker">{esc(kicker)}</p>'
        f'<h2>{esc(heading)}</h2>'
        '<p class="academy-disclosure">ENGLISH PT는 특정 오프라인 학원으로 소개하는 페이지가 아닙니다. '
        f'{esc(disclosure)}</p>'
        '<div class="academy-compare">' + card_html + '</div>'
        '<div class="academy-fit">'
        f'<div><b>학원형 수업이 잘 맞을 수 있는 경우</b><p>{esc(academy_fit)}</p></div>'
        f'<div><b>1:1 방식이 잘 맞을 수 있는 경우</b><p>{esc(one_fit)}</p></div>'
        '</div></div></section>'
    )


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
    for intent in ACADEMY_ORDER:
        if intent == current_intent:
            continue
        label = f'{loc["dong"]} {ACADEMY_SERVICE[intent]}'
        links.append(f'<a href="/{loc["slug"]}-{intent}.html">{esc(label)}</a>')
    for intent in CONV_DERIVED_ORDER:
        if intent == current_intent:
            continue
        label = f'{loc["dong"]} {CONV_DERIVED_SERVICE[intent]}'
        links.append(f'<a href="/{loc["slug"]}-{intent}.html">{esc(label)}</a>')
    return (
        '<section class="section related"><div class="wrap">'
        '<p class="kicker">관련 과정</p>'
        f'<h2>{esc(loc["dong"])}에서 다른 영어 목표도 비교해보세요</h2>'
        '<div class="links">' + "".join(links) + '</div></div></section>'
    )


def title_for(loc: dict, intent: str) -> str:
    variants = TITLE_VARIANTS[intent]
    digest = hashlib.sha256(f'{loc["slug"]}|{intent}|title-v2'.encode()).hexdigest()
    suffix = variants[int(digest[:8], 16) % len(variants)]
    return f'{loc["dong"]} {loc["service"]} | {suffix}'


EXAM_READER_PILOT_INTENTS = {"ielts","opic","toeic","toeic-speaking","duolingo","toefl"}

EXAM_READER_PILOT = {
    "ielts": {
        "label":"IELTS 수업",
        "headline":"아이엘츠는 듣기·읽기·쓰기·말하기 네 영역을 봅니다",
        "sub":"아이엘츠에서는 점수를 Band라고 부릅니다. 목표 점수(Band)와 시험일을 확인한 뒤 네 영역 중 가장 어려운 부분부터 수업 비중을 조정합니다.",
        "roadmap":[
            ("듣기 (Listening)","어떤 정보를 자주 놓치는지 확인하고, 다시 들었을 때 같은 부분을 잡을 수 있는지 봅니다."),
            ("읽기 (Reading)","정답만 확인하지 않고 답의 근거를 찾은 위치와 시간 사용을 함께 봅니다."),
            ("쓰기 (Writing)","첨삭을 읽는 데서 끝내지 않고, 고친 기준을 적용해 직접 다시 써봅니다."),
            ("말하기 (Speaking)","답변을 녹음하고, 질문이 달라져도 같은 내용을 자연스럽게 말할 수 있는지 확인합니다."),
        ],
        "outputs":[
            ("Writing","첨삭 표시 + 다시 쓸 항목"),
            ("Speaking","녹음 후 공백·반복 표현·답변 길이 체크"),
            ("Reading","오답 근거와 시간 사용 기록"),
            ("Listening","놓친 정보 유형과 다시 들을 포인트"),
        ],
        "note":"아이엘츠에는 응시 목적에 따라 Academic과 General이라는 시험 유형이 있습니다. 어떤 유형이 필요한지는 제출처 기준과 함께 확인합니다.",
    },
    "opic": {
        "label":"OPIc 수업",
        "headline":"오픽은 질문을 듣고 내 경험과 생각을 영어로 말하는 시험입니다",
        "sub":"목표 등급과 시험일을 확인한 뒤 실제로 말할 수 있는 경험을 먼저 고릅니다. 익숙한 질문부터 연습하고, 예상하지 못한 질문과 상황 말하기까지 넓혀갑니다.",
        "roadmap":[
            ("나와 가까운 주제","실제로 말할 경험이 충분한 주제를 골라 답변 소재를 먼저 정리합니다."),
            ("기본 질문","첫 문장과 이야기 순서를 잡아 짧게라도 끝까지 말해봅니다."),
            ("예상 밖 질문","준비한 경험을 처음 보는 질문에도 바꿔 쓸 수 있도록 연습합니다."),
            ("상황 말하기 (롤플레이)","질문·요청·문제 해결처럼 목적이 있는 대화를 실제처럼 이어봅니다."),
        ],
        "outputs":[
            ("녹음","공백·반복 표현·말하는 속도 확인"),
            ("답변 흐름","시작-내용-마무리 순서를 짧게 정리"),
            ("표현","자주 쓰는 표현과 고쳐야 할 표현 구분"),
            ("다음 연습","다음 수업 전에 다시 말해볼 질문 선정"),
        ],
        "note":"답변을 길게 외우기보다 자주 쓰는 경험을 여러 질문에 활용하는 쪽에 초점을 둡니다.",
    },
    "toeic": {
        "label":"TOEIC 수업",
        "headline":"토익은 크게 듣기와 읽기, 두 영역으로 나뉩니다",
        "sub":"듣기는 LC, 읽기는 RC라고 부릅니다. 최근 점수와 목표 점수, 시험일을 기준으로 어느 영역에서 자주 틀리는지와 시간 사용을 함께 확인합니다.",
        "roadmap":[
            ("듣기 (LC)","문제 유형별로 놓치는 이유가 단어인지, 발음·속도인지, 질문 이해인지 나눠봅니다."),
            ("읽기 (RC)","문법·어휘·독해를 구분하고 정답의 근거를 찾는 속도까지 확인합니다."),
            ("오답","정답 해설을 옮기기보다 왜 틀렸는지 한 줄로 남겨 같은 실수를 줄입니다."),
            ("시간 관리","실제 시험 순서와 남은 시간을 기준으로 어디에서 오래 머무는지 점검합니다."),
        ],
        "outputs":[
            ("파트별 기록","반복해서 틀리는 유형 정리"),
            ("오답 이유","문법·어휘·근거·시간 중 원인 표시"),
            ("시간표","파트별 목표 풀이 시간 확인"),
            ("다음 범위","다음 수업에서 먼저 볼 파트 선정"),
        ],
        "note":"시험이 가까워질수록 새 문제를 많이 추가하기보다 실제 시간 안에서 풀이 순서를 안정시키는 비중을 높입니다.",
    },
    "toeic-speaking": {
        "label":"TOEIC Speaking 수업",
        "headline":"토익스피킹은 컴퓨터에 영어 답변을 녹음하는 말하기 시험입니다",
        "sub":"시험에는 여러 문제 유형이 있습니다. 목표 등급과 시험일을 확인한 뒤 첫 문장, 답변 순서, 준비 시간, 말하는 속도 중 무엇이 가장 어려운지 먼저 봅니다.",
        "roadmap":[
            ("읽기·묘사","발음만 고치기보다 끊어 읽기와 핵심 정보 전달을 함께 봅니다."),
            ("질문 응답","질문을 듣고 첫 문장을 빠르게 시작하는 연습부터 합니다."),
            ("정보 활용","표·일정 정보를 확인하고 필요한 내용만 골라 답하는 순서를 익힙니다."),
            ("의견 말하기","입장-이유-예시 순서로 제한 시간 안에 마무리하는 연습을 합니다."),
        ],
        "outputs":[
            ("녹음","첫 문장까지 걸린 시간과 공백 확인"),
            ("답변 구조","유형별로 사용할 간단한 답변 순서"),
            ("표현 교정","반복 표현과 어색한 문장 수정"),
            ("실전 기록","제한 시간 안에 끝냈는지 확인"),
        ],
        "note":"완성 답안을 통째로 외우기보다, 유형별 답변 순서를 익혀 새 질문에도 적용할 수 있게 합니다.",
    },
    "duolingo": {
        "label":"듀오링고 영어시험 수업",
        "headline":"듀오링고 영어시험은 컴퓨터로 보는 영어 능력 시험입니다",
        "sub":"Duolingo English Test를 줄여서 DET라고 부릅니다. 읽기·듣기·쓰기·말하기를 함께 보며, 문제에 답하는 과정에서 난이도가 달라질 수 있는 방식에 익숙해지는 것도 중요합니다.",
        "roadmap":[
            ("시험 방식 익히기","문제 유형과 화면 진행 방식을 먼저 익혀 시험 당일 낯설지 않게 준비합니다."),
            ("읽기·듣기","문제를 이해할 때 자주 놓치는 단어나 정보를 확인합니다."),
            ("쓰기·말하기","짧게 끝내지 않고 질문에 답한 뒤 이유나 구체적인 내용을 붙이는 연습을 합니다."),
            ("시간 안에 답하기","정해진 시간 안에 끝까지 답하는 연습을 하며 속도와 정확성을 함께 봅니다."),
        ],
        "outputs":[
            ("문제 유형","자주 어려운 문제와 이유 정리"),
            ("말하기","녹음 후 공백·답변 길이 확인"),
            ("쓰기","고칠 문장과 다시 써볼 내용 정리"),
            ("다음 연습","다음 수업 전에 다시 볼 문제 유형 선정"),
        ],
        "note":"지원 학교나 기관이 듀오링고 영어시험 점수를 인정하는지는 제출 전에 해당 기관의 최신 기준을 확인합니다.",
    },
    "toefl": {
        "label":"TOEFL 수업",
        "headline":"토플은 읽기·듣기·말하기·쓰기 네 영역을 보는 시험입니다",
        "sub":"토플에는 읽거나 들은 내용을 이용해 말하거나 글을 쓰는 문제도 있습니다. 이런 문제를 ‘통합형’이라고 부르며, 영역별 약점과 함께 연결해서 연습합니다.",
        "roadmap":[
            ("읽기 (Reading)","답의 근거 위치와 문제 유형, 지문에 머무는 시간을 함께 확인합니다."),
            ("듣기 (Listening)","강의·대화에서 중요한 내용과 메모할 내용을 구분합니다."),
            ("말하기 (Speaking)","짧게 메모한 뒤 제한 시간 안에 핵심부터 말하는 연습을 합니다."),
            ("쓰기 (Writing)","읽거나 들은 내용을 정리한 뒤 문단별 역할과 근거를 분명하게 써봅니다."),
        ],
        "outputs":[
            ("Reading","문제 유형별 오답과 근거 위치"),
            ("Listening","메모 방식과 놓친 정보"),
            ("Speaking","녹음 후 구조·시간·표현 피드백"),
            ("Writing","첨삭 + 다시 쓸 문장·문단"),
        ],
        "note":"통합형은 영역별 공부를 따로 끝낸 뒤 하는 것이 아니라, 읽기·듣기·메모·말하기/쓰기를 함께 연결해 확인합니다.",
    },
}


BEGINNER_EXAM_GUIDE = {
    "toeic": {
        "intro":"토익은 크게 듣기와 읽기 두 영역으로 나뉩니다.",
        "terms":[
            ("듣기 (LC)","영어를 듣고 문제를 푸는 영역입니다."),
            ("읽기 (RC)","문법·어휘·독해 문제를 푸는 영역입니다."),
            ("파트","시험 안의 문제 종류를 나눈 구분입니다."),
        ],
    },
    "toeic-speaking": {
        "intro":"토익스피킹은 컴퓨터에 영어 답변을 녹음하는 말하기 시험입니다.",
        "terms":[
            ("문항","시험 문제 한 개를 뜻합니다."),
            ("답변 구조","첫 문장 뒤에 이유와 예시를 붙이는 순서입니다."),
            ("녹음","내 답변의 공백·속도·반복 표현을 다시 듣기 위해 사용합니다."),
        ],
    },
    "opic": {
        "intro":"오픽은 질문을 듣고 자신의 경험이나 생각을 영어로 말하는 시험입니다.",
        "terms":[
            ("배경설문","시험 전에 나와 관련 있는 생활·관심 주제를 고르는 단계입니다."),
            ("돌발 질문","미리 예상하지 못한 주제의 질문입니다."),
            ("롤플레이","주어진 상황에서 질문하거나 요청하는 말하기 문제입니다."),
        ],
    },
    "ielts": {
        "intro":"아이엘츠는 듣기·읽기·쓰기·말하기 네 영역을 보는 시험입니다.",
        "terms":[
            ("Band","아이엘츠에서 사용하는 점수 단계를 뜻합니다."),
            ("Overall Band","네 영역 점수를 종합한 전체 점수입니다."),
            ("Academic / General","응시 목적에 따라 나뉘는 시험 유형입니다."),
        ],
    },
    "duolingo": {
        "intro":"듀오링고 영어시험은 컴퓨터로 보는 영어 능력 시험입니다.",
        "terms":[
            ("DET","Duolingo English Test의 줄임말입니다."),
            ("난이도 변화","답변에 따라 다음 문제의 난이도가 달라질 수 있는 방식입니다."),
            ("말하기·쓰기 응답","직접 말하거나 글로 답하는 문제입니다."),
        ],
    },
    "toefl": {
        "intro":"토플은 읽기·듣기·말하기·쓰기 네 영역을 보는 영어 시험입니다.",
        "terms":[
            ("통합형","읽거나 들은 내용을 이용해 말하거나 글을 쓰는 문제입니다."),
            ("메모","들은 내용을 모두 적기보다 핵심을 짧게 남기는 기록입니다."),
            ("4영역","읽기·듣기·말하기·쓰기를 뜻합니다."),
        ],
    },
}


BEGINNER_GUIDE_LEADS = [
    "처음 보는 용어부터 짧게 정리한 뒤 아래 설명을 읽어보세요.",
    "시험 이름은 익숙해도 용어가 낯설다면 이 세 가지만 먼저 확인하면 됩니다.",
    "세부 공부법보다 먼저, 자주 나오는 용어의 뜻부터 간단히 확인해보세요.",
    "시험을 처음 알아보는 단계라면 아래 표현을 먼저 이해하고 넘어가면 편합니다.",
    "어려운 용어를 외울 필요는 없습니다. 아래 뜻만 알고 다음 내용을 읽어도 충분합니다.",
]


def beginner_exam_guide(intent: str, loc: dict) -> str:
    base = base_exam_intent(intent)
    d = BEGINNER_EXAM_GUIDE.get(base)
    if not d:
        return ""
    digest = hashlib.sha256(f'{loc["slug"]}|{base}|beginner-guide-v2'.encode()).hexdigest()
    variant = int(digest[:8], 16) % len(BEGINNER_GUIDE_LEADS)
    terms = list(d["terms"])
    shift = variant % len(terms)
    terms = terms[shift:] + terms[:shift]
    terms_html = ''.join(
        f'<div class="beginner-term"><b>{esc(term)}</b><span>{esc(desc)}</span></div>'
        for term, desc in terms
    )
    return (
        '<section class="beginner-exam-guide" data-beginner-guide="true"><div class="wrap">'
        '<div class="beginner-guide-box">'
        '<p class="kicker">이 시험이 처음이라면</p>'
        f'<h2>{esc(d["intro"])}</h2>'
        f'<p class="beginner-guide-lead">{esc(BEGINNER_GUIDE_LEADS[variant])}</p>'
        f'<div class="beginner-terms">{terms_html}</div>'
        '</div></div></section>'
    )


def exam_reader_pilot_enabled(intent: str) -> bool:
    # Promoted from preview-only pilot to the production reader-first structure.
    return intent in EXAM_READER_PILOT_INTENTS


def exam_reader_roadmap(intent: str) -> str:
    d=EXAM_READER_PILOT[intent]
    cards=''.join(
        f'<article class="exam-roadmap-card"><span>{i:02d}</span><h3>{esc(title)}</h3><p>{esc(body)}</p></article>'
        for i,(title,body) in enumerate(d["roadmap"],1)
    )
    return (
        '<section class="section exam-reader-roadmap" data-exam-reader-pilot="true"><div class="wrap">'
        f'<p class="kicker">{esc(d["label"])}</p>'
        f'<h2>{esc(d["headline"])}</h2>'
        f'<p class="exam-reader-lead">{esc(d["sub"])}</p>'
        f'<div class="exam-roadmap-grid">{cards}</div>'
        '</div></section>'
    )


def exam_reader_outputs(intent: str) -> str:
    d=EXAM_READER_PILOT[intent]
    rows=''.join(
        f'<div class="exam-output-row"><b>{esc(title)}</b><span>{esc(body)}</span></div>'
        for title,body in d["outputs"]
    )
    return (
        '<section class="section exam-reader-outputs"><div class="wrap exam-output-layout">'
        '<div class="exam-output-copy">'
        '<p class="kicker">수업 후 관리</p>'
        '<h2>수업이 끝나면, 다음에 무엇을 연습할지가 남아야 합니다</h2>'
        '<p>진도만 표시하지 않고 그날 잘된 부분과 다시 볼 부분을 나눠 다음 수업과 연결합니다.</p>'
        f'<p class="exam-output-note">{esc(d["note"])}</p>'
        '</div>'
        f'<div class="exam-output-list">{rows}</div>'
        '</div></section>'
    )


def remove_section_with_kicker(raw: str, kicker: str) -> str:
    pat=re.compile(
        r'<section\b[^>]*>(?:(?!</section>).)*?<p class="kicker">'
        + re.escape(kicker)
        + r'</p>(?:(?!</section>).)*?</section>',
        re.S,
    )
    return pat.sub('',raw,count=1)


def apply_exam_reader_pilot(raw: str, intent: str) -> str:
    if not exam_reader_pilot_enabled(intent):
        return raw

    # Remove the report-like sequence that repeats the same diagnosis logic.
    for kicker in (
        "실제 막힘","자주 어려운 상황","시험 구조와 개인 약점",
        "먼저 준비할 것","수업 진행","변화 확인","수업 기록 예시",
    ):
        raw=remove_section_with_kicker(raw,kicker)

    roadmap=exam_reader_roadmap(intent)
    outputs=exam_reader_outputs(intent)

    # Put concrete exam content before the management system.
    management_marker='<section class="section management">'
    if management_marker in raw:
        raw=raw.replace(management_marker,roadmap+management_marker,1)
    else:
        raw=raw.replace('</section><div class="trust">','</section>'+roadmap+'<div class="trust">',1)

    # Show what is left after class immediately after the management section.
    m=re.search(r'<section class="section management">.*?</section>',raw,re.S)
    if m:
        raw=raw[:m.end()]+outputs+raw[m.end():]
    else:
        raw=raw.replace('<section class="section mass-context">',outputs+'<section class="section mass-context">',1)

    # Keep the page focused: comparison content comes after exam-specific detail.
    raw=raw.replace(
        '<p class="kicker">수업 비교 기준</p><h2>수업을 비교할 때는 이런 부분을 확인해보세요</h2>',
        '<p class="kicker">수업을 고를 때</p><h2>설명보다 실제 관리 범위를 비교해보세요</h2>',
        1,
    )
    return raw


INTRO_CONTENT = {
    "elem-tutor": {
        "kicker":"초등 영어",
        "h2":"기초를 확인하고, 아이가 직접 말할 수 있는 문장부터 늘립니다",
        "p1":"처음부터 진도를 많이 나가기보다 읽기·단어·기초 문장 중 어디까지 혼자 할 수 있는지 먼저 확인합니다.",
        "p2":"학교 영어와 말하기를 함께 보면서 부담 없이 반복할 수 있는 분량을 정하고, 수업에서 배운 표현을 다시 써볼 수 있게 이어갑니다.",
    },
    "mid-conv": {
        "kicker":"중학생 영어",
        "h2":"학교 영어와 말하기를 따로 떼지 않고 함께 준비합니다",
        "p1":"수행평가·발표·교과서 영어처럼 당장 필요한 일정과 현재 수준을 먼저 확인합니다.",
        "p2":"외운 문장을 그대로 말하는 데서 끝내지 않고, 질문이 조금 달라져도 자신의 말로 이어갈 수 있도록 연습합니다.",
    },
    "high-conv": {
        "kicker":"고등학생 영어",
        "h2":"내신·수행평가·면접, 지금 필요한 영어부터 정합니다",
        "p1":"고등학생은 해야 할 공부가 많기 때문에 회화를 따로 크게 벌이기보다 학교 일정과 발표·면접처럼 가까운 목표에 맞춰 시작하는 편이 효율적입니다.",
        "p2":"최근 어려웠던 부분을 확인한 뒤 필요한 말하기·듣기·표현 연습만 골라 수업하고, 다음 일정에 맞춰 비중을 다시 조정합니다.",
    },
    "univ-conv": {
        "kicker":"대학생 영어",
        "h2":"발표·세미나·면접처럼 실제로 필요한 영어부터 준비합니다",
        "p1":"막연히 회화를 잘하고 싶다는 목표보다 다음에 영어를 써야 하는 상황을 먼저 정하면 준비 범위를 훨씬 빠르게 좁힐 수 있습니다.",
        "p2":"수업에서는 필요한 표현을 익힌 뒤 직접 말해보고, 질문이나 주제가 달라져도 자연스럽게 이어갈 수 있도록 피드백합니다.",
    },
    "jobseeker-conv": {
        "kicker":"취업 영어",
        "h2":"영어면접은 답을 외우기보다 내 경험을 말할 수 있어야 합니다",
        "p1":"지원 일정과 예상 질문을 확인하고, 자기소개·지원동기·경험 답변처럼 실제 면접에서 필요한 내용부터 준비합니다.",
        "p2":"완성 문장을 통째로 외우기보다 핵심 내용을 정리한 뒤 질문 표현이 달라져도 다시 말할 수 있도록 반복합니다.",
    },
    "biz-business-conv": {
        "kicker":"비즈니스 영어",
        "h2":"회의·발표·전화, 실제 업무에서 바로 쓸 영어부터 준비합니다",
        "p1":"직무와 영어 사용 상황을 먼저 확인하고, 자주 필요한 회의 표현·설명·질문·응답을 실제 업무에 가깝게 연습합니다.",
        "p2":"수업에서 익힌 표현은 다른 업무 상황에서도 다시 써보며, 자주 막히는 표현과 문장 구조를 중심으로 피드백합니다.",
    },
    "housewife-conv": {
        "kicker":"생활 영어",
        "h2":"여행과 생활에서 자주 쓰는 영어부터 편하게 시작합니다",
        "p1":"오랜만에 영어를 다시 시작해도 괜찮습니다. 현재 가능한 표현과 자주 필요한 상황을 먼저 확인해 무리하지 않는 범위에서 시작합니다.",
        "p2":"듣고 따라 하는 데서 끝내지 않고 직접 질문하고 대답하는 시간을 늘리면서 생활 속에서 쓸 수 있는 표현을 차근차근 넓혀갑니다.",
    },
    "toeic": {
        "kicker":"토익 준비",
        "h2":"듣기와 읽기 중 어디에서 자주 틀리는지부터 확인합니다",
        "p1":"토익의 듣기 영역을 LC, 읽기 영역을 RC라고 부릅니다. 목표 점수와 시험일, 최근 점수를 먼저 확인한 뒤 어느 쪽이 더 어려운지 나눠봅니다.",
        "p2":"문제를 많이 푸는 것보다 왜 틀렸는지와 어디에서 시간이 오래 걸리는지를 함께 확인해, 시험일까지 먼저 공부할 부분을 정합니다.",
    },
    "toeic-speaking": {
        "kicker":"토익스피킹 준비",
        "h2":"컴퓨터에 영어로 답을 녹음하는 시험, 어려운 문제 유형부터 연습합니다",
        "p1":"토익스피킹은 여러 문제 유형에 영어로 말해 답하는 시험입니다. 목표 등급과 시험일을 확인한 뒤 첫 문장, 답변 순서, 준비 시간 중 무엇이 가장 어려운지 먼저 봅니다.",
        "p2":"문제 유형별로 답하는 순서를 익히고 실제 제한 시간에 맞춰 말해본 뒤, 녹음을 다시 들으며 공백과 반복 표현을 줄여갑니다.",
    },
    "opic": {
        "kicker":"오픽 준비",
        "h2":"오픽은 내 경험과 생각을 영어로 말하는 시험입니다",
        "p1":"목표 등급과 시험일을 확인하고, 여행·취미·일상처럼 실제로 말할 수 있는 경험부터 정리합니다.",
        "p2":"익숙한 질문부터 시작해 예상하지 못한 질문에도 내 경험을 바꿔 활용할 수 있도록 연습하고, 녹음을 다시 들으며 부족한 부분을 확인합니다.",
    },
    "ielts": {
        "kicker":"아이엘츠 준비",
        "h2":"아이엘츠는 듣기·읽기·쓰기·말하기 네 영역을 보는 시험입니다",
        "p1":"아이엘츠에서는 점수를 Band라고 부릅니다. 지원 목적과 목표 점수(Band), 시험일을 확인한 뒤 네 영역 중 어디가 가장 어려운지 먼저 봅니다.",
        "p2":"쓰기는 고친 글을 다시 써보고, 말하기는 질문을 바꿔 다시 답합니다. 듣기와 읽기는 틀린 이유와 시간 사용을 함께 확인합니다.",
    },
    "duolingo": {
        "kicker":"듀오링고 영어시험 준비",
        "h2":"컴퓨터로 보는 시험이라, 영어 실력과 시험 방식 적응을 함께 준비합니다",
        "p1":"Duolingo English Test를 줄여서 DET라고 부릅니다. 목표 점수와 제출 일정을 확인한 뒤 읽기·듣기·쓰기·말하기 중 자주 어려운 부분을 나눠봅니다.",
        "p2":"문제 형식에 익숙해지고, 말하기와 쓰기 문제는 짧게 끝내지 않고 질문에 맞는 내용을 끝까지 완성하는 연습을 반복합니다.",
    },
    "toefl": {
        "kicker":"토플 준비",
        "h2":"토플은 읽기·듣기·말하기·쓰기 네 영역을 보는 시험입니다",
        "p1":"목표 점수와 시험일을 기준으로 네 영역 중 점수를 자주 잃는 부분을 먼저 확인합니다.",
        "p2":"토플에는 읽거나 들은 내용을 이용해 말하거나 글을 쓰는 ‘통합형’ 문제도 있습니다. 메모·내용 정리·답변 순서와 시간 사용을 함께 연습합니다.",
    },
}

MANAGEMENT_FOCUS = {
    "elem-tutor":["읽기·단어·기초 문장 중 필요한 부분부터 시작","학교 진도와 말하기를 함께 확인","짧은 복습으로 수업 내용을 다시 사용"],
    "mid-conv":["수행평가·발표 일정을 수업 계획에 반영","교과서 표현을 실제 질문·답변으로 연결","수업 후 다시 말해볼 내용과 복습 범위 정리"],
    "high-conv":["내신·수행평가·면접 일정에 맞춰 비중 조정","발표·질문 대응을 실제 상황처럼 연습","시험기간에는 부담을 줄이고 필요한 영역만 유지"],
    "univ-conv":["발표·세미나·면접 일정에 맞춘 준비","직접 말한 답변을 바로 교정하고 다시 연습","수업 밖에서도 이어갈 짧은 말하기 과제 설정"],
    "jobseeker-conv":["지원기업·면접 일정에 맞춰 질문 우선순위 조정","자기소개·경험 답변을 질문별로 정리","모의 질문 후 표현·논리·말하는 속도 피드백"],
    "biz-business-conv":["회의·발표·전화 등 업무 상황별 표현 준비","실제 업무 문장과 답변을 중심으로 교정","일정과 업무 변화에 따라 다음 수업 주제 조정"],
    "housewife-conv":["현재 수준과 생활·여행 목표부터 확인","자주 쓰는 짧은 표현을 직접 말하는 연습","부담 없는 복습량으로 꾸준히 이어가기"],
    "toeic":["듣기(LC)·읽기(RC)를 나눠 반복해서 틀리는 부분 확인","틀린 이유를 문법·어휘·답의 근거·시간으로 구분","시험 전에는 실제 시간에 맞춰 풀이 순서 점검"],
    "toeic-speaking":["문제 유형별로 답변 순서 정리","녹음으로 첫 문장·속도·반복 표현 확인","실제 제한 시간에 맞춰 다시 답하고 고칠 부분 확인"],
    "opic":["시험 전 고르는 주제와 실제 경험을 먼저 정리","익숙한 질문부터 시작해 예상 밖 질문으로 확장","녹음으로 반복 표현·공백·답변 길이 확인"],
    "ielts":["듣기·읽기·쓰기·말하기를 따로 확인해 공부 비중 조정","쓰기(Writing)는 고친 뒤 다시 쓰고 말하기(Speaking)는 질문을 바꿔 다시 답하기","읽기·듣기는 틀린 이유와 시간 사용까지 기록"],
    "duolingo":["읽기·듣기·쓰기·말하기 중 어려운 부분 확인","말하기·쓰기 답변은 질문에 맞게 끝까지 완성하는 연습","공식 연습문제로 시험 전 결과를 다시 확인"],
    "toefl":["읽기·듣기·말하기·쓰기를 영역별로 확인","통합형은 읽거나 들은 내용을 메모하고 말하거나 쓰는 흐름으로 연습","말하기·쓰기는 답변 순서와 시간 사용을 함께 확인"],
}


def intro_content(intent: str) -> dict:
    if intent in CONV_DERIVED_PROFILE:
        return CONV_DERIVED_PROFILE[intent]["reader_intro"]
    if intent not in ACADEMY_BASE:
        return INTRO_CONTENT[intent]
    base = ACADEMY_BASE[intent]
    base_intro = INTRO_CONTENT[base]
    service = ACADEMY_SERVICE[intent]
    return {
        "kicker": f"{service} 선택",
        "h2": f"{service}을 알아볼 때는 진도보다 내 시험일과 피드백 방식을 먼저 확인합니다",
        "p1": "학원을 찾는 이유가 정해진 일정과 체계적인 관리 때문인지, 특정 약점을 빠르게 보완하기 위해서인지 먼저 생각해보면 수업방식을 비교하기 쉬워집니다.",
        "p2": base_intro["p2"],
    }


def management_section(loc: dict, intent: str, family: str) -> str:
    if intent in ACADEMY_BASE:
        focus = MANAGEMENT_FOCUS[base_exam_intent(intent)]
    elif intent in CONV_DERIVED_PROFILE:
        focus = CONV_DERIVED_PROFILE[intent]["management_focus"]
    else:
        focus = MANAGEMENT_FOCUS[intent]
    intro_variants = [
        ("수업만 하고 끝내지 않고, 다음 수업까지 이어서 관리합니다",
         "진도를 많이 나가는 것보다 지금 필요한 내용을 정확히 연습하고, 수업 후에도 다시 써볼 수 있게 만드는 데 초점을 둡니다."),
        ("매 수업의 결과가 다음 수업으로 이어지도록 관리합니다",
         "그날 배운 내용을 그날로 끝내지 않고, 잘된 부분과 다시 볼 부분을 나눠 다음 수업의 시작점으로 연결합니다."),
        ("배운 내용을 실제로 다시 써볼 수 있게 수업 전후를 연결합니다",
         "한 번 설명하고 넘어가기보다 직접 해보고 피드백한 뒤, 다음 수업에서 다시 확인해 필요한 부분만 이어갑니다."),
    ]
    digest = hashlib.sha256(f'{loc["slug"]}|{intent}|manage-copy-v1'.encode()).hexdigest()
    manage_h2, manage_p = intro_variants[int(digest[:8],16) % len(intro_variants)]
    steps = [
        ("01","처음 상담","목표와 가장 가까운 일정, 최근 결과나 어려웠던 부분을 확인합니다."),
        ("02","수업 계획","한 번에 많은 내용을 잡기보다 먼저 바꿔야 할 한두 가지를 정합니다."),
        ("03","수업 시간","설명을 들은 뒤 직접 풀고, 말하고, 써보면서 바로 수정합니다."),
        ("04","수업 후","오늘 잘된 부분과 다시 연습할 내용을 정리해 다음 수업과 연결합니다."),
        ("05","다음 수업","지난 내용을 짧게 확인한 뒤 결과에 따라 분량과 순서를 다시 조정합니다."),
    ]
    step_html = ''.join(
        f'<div class="manage-step"><span>{n}</span><div><h3>{esc(t)}</h3><p>{esc(p)}</p></div></div>'
        for n,t,p in steps
    )
    focus_html = ''.join(f'<li>{esc(x)}</li>' for x in focus)
    label = "시험 관리" if family == "exam" else "학습 관리"
    return (
        '<section class="section management">'
        '<div class="wrap manage-layout">'
        '<div class="manage-copy">'
        f'<p class="kicker">{label}</p>'
        f'<h2>{esc(manage_h2)}</h2>'
        f'<p>{esc(manage_p)}</p>'
        '<ul class="manage-focus">' + focus_html + '</ul>'
        '</div>'
        '<div class="manage-steps">' + step_html + '</div>'
        '</div></section>'
    )


def rewrite_reader_headings(raw: str, loc: dict, intent: str, family: str) -> str:
    service = loc["service"]
    mapping = {
        "자주 어려운 상황": "어디에서 자주 어려워지는지부터 확인합니다",
        "실제 막힘": "어디에서 자주 어려워지는지부터 확인합니다",
        "시험 구조와 개인 약점": "시험 방식은 알고, 내 약점은 따로 찾아야 합니다",
        "어려운 이유": "왜 어려운지 알면 연습 방법도 달라집니다",
        "먼저 준비할 것": "모든 걸 한꺼번에 하지 않고, 먼저 할 것부터 정합니다",
        "수업 진행": "설명만 듣고 끝나지 않게 이렇게 진행합니다",
        "변화 확인": "잘하고 있는지는 이렇게 확인합니다",
        "수업 기록 예시": "수업 후에는 이런 내용을 남깁니다",
        "시험 선택": "지금 목표에 맞는 시험인지도 함께 확인합니다",
        "수업 선택": "지금 목표에 맞는 수업인지도 함께 확인합니다",
        "더 깊게 보기": f"{service}에서 많이 어려워하는 부분",
        "자주 묻는 질문": "상담 전에 많이 물어보는 내용",
        "공식정보 확인": "시험 정보는 공식 안내로 한 번 더 확인하세요",
        "수업 비교 기준": "수업을 비교할 때는 이런 부분을 확인해보세요",
        "상담 전 확인": "상담 전에 이 정도만 알려주셔도 됩니다",
    }
    for kicker, heading in mapping.items():
        pattern = re.compile(r'(<p class="kicker">' + re.escape(kicker) + r'</p><h2>).*?(</h2>)', re.S)
        raw = pattern.sub(lambda m: m.group(1) + esc(heading) + m.group(2), raw, count=1)
    return raw


def description_for(loc: dict, intent: str) -> str:
    if intent in CONV_DERIVED_PROFILE:
        service = CONV_DERIVED_SERVICE[intent]
        desc = {
            "english-conv-academy":"영어회화학원을 비교할 때 직접 말하는 시간, 현재 수준에 맞는 진도, 개인 피드백과 수업 후 복습 관리 기준을 확인하세요.",
            "adult-english-conv-academy":"성인영어회화학원을 비교할 때 기초 수준, 생활·여행 목적, 말하기 피드백과 꾸준히 이어갈 수 있는 관리 방식을 확인하세요.",
            "worker-english-conv-academy":"직장인영어회화학원을 비교할 때 회의·발표·전화 등 실제 업무 상황, 개인 피드백과 수업 후 관리 방식을 확인하세요.",
            "beginner-english-conv":"왕초보영어회화 안내. 인사·자기소개·기본 질문부터 직접 말하고, 기초 문장을 다른 상황에도 사용할 수 있게 연습하는 방법을 확인하세요.",
        }[intent]
        return f'{loc["dong"]} {service} 안내. ' + desc
    if intent in ACADEMY_BASE:
        base = ACADEMY_BASE[intent]
        exam_name = {
            "toeic":"TOEIC","toeic-speaking":"TOEIC Speaking","opic":"OPIc","ielts":"IELTS","duolingo":"Duolingo English Test","toefl":"TOEFL"
        }[base]
        return (
            f'{loc["dong"]} {ACADEMY_SERVICE[intent]} 검색 안내. {exam_name} 학원형 수업과 1:1 맞춤 수업을 비교할 때 '
            '진도·피드백·시험일 관리와 영역별 보완 방식을 확인할 수 있도록 정리했습니다.'
        )
    templates = {
        "elem-tutor": f'{loc["dong"]} 초등학생영어과외 안내. 읽기·기초 문장·학교영어에서 어려운 부분을 확인하고 현재 수준에 맞는 수업 방향과 상담 기준을 정리했습니다.',
        "mid-conv": f'{loc["dong"]} 중학생영어회화 안내. 수행평가·발표·질문 대응과 학교영어에서 어려운 부분을 확인하고 필요한 연습 순서를 살펴보세요.',
        "high-conv": f'{loc["dong"]} 고등학생영어회화 안내. 수행평가·발표·면접과 학교영어 일정을 기준으로 현재 어려운 부분과 수업 방향을 확인하세요.',
        "univ-conv": f'{loc["dong"]} 대학생영어회화 안내. 발표·세미나·교환학생·면접처럼 실제 영어가 필요한 상황에 맞춰 준비할 내용을 확인하세요.',
        "jobseeker-conv": f'{loc["dong"]} 취준생영어회화 안내. 영어면접·자기소개·경험 답변에서 어려운 부분을 확인하고 답변 연습과 피드백 방식을 살펴보세요.',
        "biz-business-conv": f'{loc["dong"]} 직장인비즈니스영어 안내. 회의·발표·전화·고객 대응처럼 가까운 업무 일정에 필요한 영어를 중심으로 수업 방향을 확인하세요.',
        "housewife-conv": f'{loc["dong"]} 주부영어회화 안내. 여행·생활영어·기초회화를 현재 수준과 가능한 학습 시간에 맞춰 어떻게 시작할지 확인하세요.',
        "toeic": f'{loc["dong"]} 토익과외 안내. 목표 점수와 시험일을 기준으로 LC·RC 약점, 오답 원인, 시간 관리와 실전 연습 방향을 확인하세요.',
        "toeic-speaking": f'{loc["dong"]} 토익스피킹과외 안내. 답변 구조·첫 문장·시간 관리·파트별 어려운 부분을 확인하고 실전 말하기 연습 방향을 살펴보세요.',
        "opic": f'{loc["dong"]} 오픽과외 안내. 목표 등급과 시험일을 기준으로 돌발 질문, 답변 구성, 경험 활용과 말하기 연습 방향을 확인하세요.',
        "ielts": f'{loc["dong"]} 아이엘츠과외 안내. IELTS Listening·Reading·Writing·Speaking 4영역의 현재 약점과 목표 Band, 시험일까지의 준비 방향을 확인하세요.',
        "duolingo": f'{loc["dong"]} 듀오링고영어테스트 안내. DET 목표 점수와 제출 일정을 기준으로 영역별 약점, 말하기·쓰기 응답과 실전 연습 방향을 확인하세요.',
        "toefl": f'{loc["dong"]} 토플과외 안내. TOEFL Reading·Listening·Speaking·Writing 4영역의 약점과 시간 관리, 실전 연습 방향을 확인하세요.',
    }
    return templates[intent]


def humanize_visible_copy(raw: str, family: str) -> str:
    """Make user-facing Korean conversational while leaving head SEO/schema untouched."""
    if "</head>" not in raw:
        return raw
    head, body = raw.split("</head>", 1)

    # Exact phrases first; generic replacements later.
    replacements = {
        "현재 장면과 다음 일정을 먼저 알려주세요": "지금 가장 어려운 부분과 가까운 일정을 알려주세요",
        "최근 막힌 장면 하나": "최근 가장 어려웠던 상황 하나",
        "최근 막힌 장면": "최근 어려웠던 상황",
        "가장 막히는 장면": "가장 어려운 부분",
        "최근 영어가 막혔던 순간": "최근 영어가 특히 어려웠던 순간",
        "현재 필요한 영어 장면": "지금 영어가 필요한 상황",
        "다음 실제 사용 장면": "다음에 실제로 영어를 써야 하는 상황",
        "실제 사용 장면": "실제로 영어를 쓰는 상황",
        "실제 업무 장면": "실제 업무 상황",
        "학교 장면": "학교에서 영어가 필요한 상황",
        "캠퍼스 장면": "학교생활 속 상황",
        "생활 장면": "생활 속 상황",
        "장면 기록": "어려웠던 상황 기록",
        "장면 기록형": "최근 어려웠던 상황을 기준으로 보는 방식",
        "장면 전용 암기": "특정 상황에만 맞춘 암기",
        "다음 행동": "다음에 연습할 내용",
        "실제 행동": "실제로 해야 하는 내용",
        "결과 행동": "실제로 해야 하는 내용",
        "독립 수행 범위": "혼자 할 수 있는 범위",
        "현재 수행": "최근 결과",
        "현재 독립 수행 범위": "현재 혼자 할 수 있는 범위",
        "재점검": "다시 확인",
        "재검증": "다시 확인",
        "재검사": "다시 확인",
        "재평가": "다시 확인",
        "재답변": "질문을 바꿔 다시 답하기",
        "재작성": "고쳐서 다시 쓰기",
        "태깅": "원인별로 구분",
        "open response": "말하기·쓰기 응답",
        "productive response": "직접 말하기·쓰기 응답",
        "adaptive format": "난이도가 달라지는 시험 방식",
        "Skill별": "영역별",
        "skill별": "영역별",
        "skill": "영역",
        "실전 조건으로": "실제 시험 시간에 맞춰" if family == "exam" else "실제 상황에 맞춰",
        "실전 조건에서": "실제 시험처럼 연습할 때" if family == "exam" else "실제 상황에서",
        "실전 조건": "실제 시험 환경" if family == "exam" else "실제 상황",
        "재사용 범위": "다른 문제에서도 적용되는 범위",
        "재사용 확인": "다른 문제에서도 적용되는지 확인",
        "재사용 테스트": "다른 문제에 적용해보는 확인",
        "경험 재사용": "같은 경험을 다른 질문에도 활용",
        "재사용": "다른 상황에도 활용",
        "병목": "가장 어려운 부분",
        "발화 명료성": "말이 또렷하게 들리는지",
        "문항 요구": "문제가 무엇을 묻는지",
        "질문 변형": "질문이 달라졌을 때",
        "입력정보": "읽거나 들은 정보",
        "스크립트": "외운 답변",
    }
    if family == "exam":
        replacements.update({
            "실제 병목 파트": "점수를 가장 많이 깎는 파트",
            "파트별 병목": "파트별 약점",
            "Band 병목": "목표 Band를 막는 영역",
            "영역별 병목": "영역별 약점",
            "skill별 병목": "영역별 약점",
            "기초 병목": "기초 약점",
            "현재 병목": "현재 약점",
            "병목 영역": "가장 약한 영역",
            "병목": "약점",
        })

    for old, new in replacements.items():
        body = body.replace(old, new)

    # Keep ordinary Korean natural instead of replacing every occurrence mechanically.
    body = body.replace("장면형에서는", "최근 어려웠던 상황을 기준으로 볼 때는")
    body = body.replace("사용 장면형에서는", "실제로 영어를 쓰는 상황을 기준으로 볼 때는")
    body = body.replace("다음 장면", "다음 상황")
    body = body.replace("같은 장면", "비슷한 상황")

    heading_replacements = {
        '<p class="kicker">실제 상황</p>': '<p class="kicker">자주 어려운 상황</p>',
        '<p class="kicker">막히는 이유</p>': '<p class="kicker">어려운 이유</p>',
        '<p class="kicker">우선순위</p>': '<p class="kicker">먼저 준비할 것</p>',
        '<p class="kicker">수업 흐름</p>': '<p class="kicker">수업 진행</p>',
        '<p class="kicker">중간 확인</p>': '<p class="kicker">중간 점검</p>',
        '<p class="kicker">판단 기준</p>': '<p class="kicker">변화 확인</p>',
        '<p class="kicker">피드백 예시</p>': '<p class="kicker">수업 기록 예시</p>',
        '<p class="kicker">과정 선택</p>': '<p class="kicker">수업 선택</p>',
        '<p class="kicker">지역별 비교 기준</p>': '<p class="kicker">수업 비교 기준</p>',
        '<p class="kicker">상담 안내</p>': '<p class="kicker">상담 전 확인</p>',
    }
    for old, new in heading_replacements.items():
        body = body.replace(old, new)

    body = body.replace(
        "실제 후기가 아니라 수업 기록 형식을 보여주는 예시입니다",
        "수업에서는 이런 내용을 확인하고 기록합니다",
    )
    body = body.replace(
        "무엇을 관찰하고 다음에 무엇을 다시 확인하는지 보여주기 위한 예시 형식입니다.",
        "특정 학생의 후기가 아니라, 수업에서 어떤 부분을 확인하고 다음 연습으로 이어가는지 보여주는 예시입니다.",
    )
    body = body.replace(
        "등록보다 먼저 현재 상태와 목표부터 확인하세요.",
        "바로 결정하기보다 지금 필요한 수업부터 확인해보세요.",
    )

    return head + "</head>" + body


def v44_header() -> str:
    return (
        '<header class="site-header"><div class="wrap header">'
        '<a href="/englishpt.html" class="brand"><span class="brand-mark">PT</span><span class="brand-name">ENGLISH PT</span></a>'
        '<nav class="nav" aria-label="주요 메뉴">'
        '<a class="phone-cta" href="tel:+821050068027">전화 010-5006-8027</a>'
        '<a class="nav-link" href="#detail">수업 보기</a>'
        '<a class="nav-cta" href="#consultation-preview">무료 PT 진단</a>'
        '</nav></div></header>'
    )


def v44_snapshot(loc: dict, family: str) -> str:
    if family == "exam":
        rows = [
            ("목표", "목표 점수·등급과 가장 가까운 시험 일정"),
            ("현재", "최근 문제·답변에서 자주 어려운 부분"),
            ("다음", "다음 수업에서 먼저 연습할 내용"),
        ]
    else:
        rows = [
            ("목표", "다음 발표·면접·학교·생활 영어 상황"),
            ("현재", "최근 어려웠던 부분과 혼자 할 수 있는 범위"),
            ("계획", "수업 밖에서도 이어갈 수 있는 시간과 방식"),
        ]
    body = ''.join(
        f'<div class="snaprow"><small>{esc(k)}</small><strong>{esc(v)}</strong></div>'
        for k, v in rows
    )
    return (
        '<aside class="snapshot">'
        '<h3>처음 상담에서 먼저 보는 것</h3>'
        '<p>레벨 이름보다 지금 필요한 목표와 어려운 부분부터 확인합니다.</p>'
        + body + '</aside>'
    )


def v44_trust(family: str) -> str:
    items = (
        ["✓ 목표 점수·시험일 확인", "✓ 약한 영역부터 집중", "✓ 실제 시험 시간에 맞춰 연습"]
        if family == "exam"
        else ["✓ 현재 수준부터 확인", "✓ 필요한 영어부터 연습", "✓ 수업 후 피드백·복습 연결"]
    )
    return '<div class="trust"><div class="wrap trust-in">' + ''.join(f'<div>{x}</div>' for x in items) + '</div></div>'


def rewrite_schema_page_title(raw: str, page_title: str) -> str:
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)
    if not m:
        return raw
    try:
        data = json.loads(m.group(1))
        graph = data.get("@graph")
        if isinstance(graph, list):
            for node in graph:
                if isinstance(node, dict) and node.get("@type") == "WebPage":
                    node["name"] = page_title
        rep = '<script type="application/ld+json">' + json.dumps(data,ensure_ascii=False,separators=(",",":")) + '</script>'
        return raw[:m.start()] + rep + raw[m.end():]
    except Exception:
        return raw


def _audience_label(intent: str, family: str) -> str:
    if intent in CONV_DERIVED_PROFILE:
        return CONV_DERIVED_PROFILE[intent]["audience"]
    if intent in SERVICE_ORDER:
        return gold_modules()[0].PROFILES[intent]["audience"]
    base = base_exam_intent(intent)
    labels = {
        "toeic":"TOEIC 준비생",
        "toeic-speaking":"TOEIC Speaking 준비생",
        "opic":"OPIc 준비생",
        "ielts":"IELTS 준비생",
        "duolingo":"Duolingo English Test 준비생",
        "toefl":"TOEFL 준비생",
    }
    return labels.get(base, "영어 학습자")


def enrich_machine_schema(
    raw: str, loc: dict, intent: str, family: str,
    h1: str, page_title: str, page_description: str, canonical: str
) -> tuple[str, bool]:
    """Create a consistent entity graph for search and AI ingestion."""
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)
    if not m:
        return raw, False
    try:
        data = json.loads(m.group(1))
        graph = data.get("@graph")
        if not isinstance(graph, list):
            return raw, False

        org_id = BASE_URL + "/#organization"
        site_id = BASE_URL + "/#website"
        service_id = canonical + "#service"
        page_id = canonical + "#webpage"

        def find_type(type_name: str):
            for node in graph:
                if isinstance(node, dict) and node.get("@type") == type_name:
                    return node
            return None

        org = find_type("EducationalOrganization")
        if org is None:
            org = {"@type":"EducationalOrganization"}
            graph.insert(0, org)
        org.update({
            "@id": org_id,
            "name": "잉글리시PT",
            "alternateName": "ENGLISH PT",
            "url": BASE_URL + "/englishpt.html",
            "telephone": "+82-10-5006-8027",
            "email": "cicada3865@naver.com",
            "knowsAbout": [
                "영어회화","초등 영어","중등 영어","고등 영어","비즈니스 영어",
                "TOEIC","TOEIC Speaking","OPIc","IELTS","TOEFL","Duolingo English Test"
            ],
        })
        # Organization-level locality must not change page by page.
        # Local search intent belongs on the Service node instead.
        org.pop("areaServed", None)

        website = find_type("WebSite")
        if website is None:
            website = {
                "@type":"WebSite","@id":site_id,"url":BASE_URL+"/englishpt.html",
                "name":"잉글리시PT","alternateName":"ENGLISH PT",
                "inLanguage":"ko-KR","publisher":{"@id":org_id},
            }
            graph.append(website)
        else:
            website.update({
                "@id":site_id,"url":BASE_URL+"/englishpt.html",
                "name":"잉글리시PT","alternateName":"ENGLISH PT",
                "inLanguage":"ko-KR","publisher":{"@id":org_id},
            })

        service = find_type("Service")
        if service is None:
            service = {"@type":"Service"}
            graph.append(service)

        academy_like = is_academy_intent(intent)
        service_name = (
            f'{loc["dong"]} {loc["service"]} 수업 비교 안내'
            if academy_like else h1
        )
        service_type = (
            "영어교육 수업 비교 및 1:1 맞춤 수업 안내"
            if academy_like else (
                "영어시험 1:1 맞춤 수업" if family == "exam" else "1:1 맞춤 영어교육"
            )
        )
        service.update({
            "@id":service_id,
            "name":service_name,
            "serviceType":service_type,
            "description":page_description,
            "provider":{"@id":org_id},
            "areaServed":{"@type":"AdministrativeArea","name":loc["full_name"]},
            "audience":{"@type":"Audience","audienceType":_audience_label(intent,family)},
            "url":canonical,
            "inLanguage":"ko-KR",
        })
        if academy_like:
            service["additionalType"] = "https://schema.org/Service"

        webpage = find_type("WebPage")
        if webpage is None:
            webpage = {"@type":"WebPage"}
            graph.append(webpage)
        webpage.update({
            "@id":page_id,
            "url":canonical,
            "name":page_title,
            "description":page_description,
            "inLanguage":"ko-KR",
            "isPartOf":{"@id":site_id},
            "publisher":{"@id":org_id},
            "about":{"@id":service_id},
            "mainEntity":{"@id":service_id},
        })

        rep = '<script type="application/ld+json">' + json.dumps(
            data, ensure_ascii=False, separators=(",",":")
        ) + '</script>'
        return raw[:m.start()] + rep + raw[m.end():], True
    except Exception:
        return raw, False


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
    page_title = title_for(loc, intent)
    page_description = description_for(loc, intent)
    theme = theme_for_intent(intent, family)

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
    raw = re.sub(r'<title>.*?</title>', f'<title>{esc(page_title)}</title>', raw, count=1, flags=re.S)
    raw = re.sub(
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="{esc(page_description)}">',
        raw,
        count=1,
    )
    raw = re.sub(
        r'<meta property="og:title" content="[^"]*">',
        f'<meta property="og:title" content="{esc(page_title)}">',
        raw,
        count=1,
    )
    raw = re.sub(
        r'<body class="[^"]*"[^>]*data-production-deploy="false">',
        f'<body class="{theme}" data-production-deploy="true" data-stage9-clean="true">',
        raw,
        count=1,
    )
    raw = re.sub(
        r'<header>.*?</header>',
        v44_header(),
        raw, count=1, flags=re.S,
    )

    hero_html = (
        '<section class="hero simple-hero"><div class="wrap simple-hero-inner">'
        f'<p class="eyebrow">ENGLISH PT · {esc(loc["dong"])}</p>'
        f'<h1>{esc(h1)}</h1>'
        '<div class="hero-actions">'
        '<a class="btn primary" href="#detail">내용 보기</a>'
        '<a class="btn ghost" href="#consultation-preview">무료 PT 진단</a>'
        '</div></div></section>'
        + visual_section(loc,intent,h1)
        + (beginner_exam_guide(intent, loc) if family == "exam" else "")
    )
    raw = re.sub(r'<section class="hero">.*?</section>', hero_html, raw, count=1, flags=re.S)

    detail = re.search(
        r'<section id="detail" class="section"><div class="wrap narrow">(.*?)</div></section>',
        raw, re.S,
    )
    if detail:
        intro = intro_content(intent)
        intro_copy = (
            f'<p class="kicker">{esc(intro["kicker"])}</p>'
            f'<h2>{esc(intro["h2"])}</h2>'
            f'<p>{esc(intro["p1"])}</p>'
            f'<p>{esc(intro["p2"])}</p>'
        )
        intro_html = (
            '<section class="section intro-detail" id="detail"><div class="wrap"><div class="intro-grid">'
            '<div class="intro-copy">' + intro_copy + '</div>'
            + v44_snapshot(loc, family)
            + '</div></div></section>' + v44_trust(family)
            + academy_compare_section(loc,intent)
            + management_section(loc,intent,family)
        )
        raw = raw[:detail.start()] + intro_html + raw[detail.end():]
    else:
        problems.append("v44_intro")

    if EMAILJS_TAG not in raw:
        raw = raw.replace('<script defer src="pilot.js"></script>', EMAILJS_TAG+'<script defer src="pilot.js"></script>',1)

    raw, n = re.subn(r'<form id="(?:pilotForm|leadForm)"[^>]*>.*?</form>', consultation_form(loc, h1), raw, count=1, flags=re.S)
    if n!=1:
        problems.append("live_form")

    # Remove only preview-only explanations, never substantive content.
    raw = re.sub(r'<p>[^<]*(?:검수용|파일럿)[^<]*(?:전송|production|미배포)[^<]*</p>', '', raw, flags=re.I)
    raw = re.sub(r'<p>[^<]*(?:production 미배포|검수용 페이지)[^<]*</p>', '', raw, flags=re.I)

    # Replace family-limited related links with the full 13-intent local cluster.
    raw = re.sub(r'<section class="section related">.*?</section>', all_related(loc,intent), raw, count=1, flags=re.S)
    related_marker = '<section class="section related">'
    if family == "service":
        audience = CONV_DERIVED_PROFILE[intent]["audience"] if intent in CONV_DERIVED_PROFILE else gold_modules()[0].PROFILES[intent]["audience"]
    else:
        audience = ""
    ctx = mass_context(loc,intent,family,audience)
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
        raw=raw.replace(dm.group(0),dm.group(0)+f'<meta property="og:description" content="{esc(page_description)}">',1)
    if 'property="og:type"' not in raw:
        raw=raw.replace('<meta property="og:title"', '<meta property="og:type" content="website"><meta property="og:title"',1)

    raw, schema_ok = add_breadcrumb_schema(raw,h1,canonical)
    if not schema_ok:
        problems.append("breadcrumb_schema")
    raw = rewrite_schema_page_title(raw, page_title)
    raw, machine_schema_ok = enrich_machine_schema(
        raw, loc, intent, family, h1, page_title, page_description, canonical
    )
    if not machine_schema_ok:
        problems.append("machine_schema")

    raw = humanize_visible_copy(raw, family)
    raw = rewrite_reader_headings(raw, loc, intent, family)
    raw = apply_exam_reader_pilot(raw, base_exam_intent(intent))
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
        'name="name"','name="phone"','name="area"','name="message"','name="wantedClass"','name="consent"',
        'class="breadcrumb wrap"','class="mobile-sticky"',
        EMAILJS_TAG,'class="section mass-context"',
        'class="site-header"','class="hero simple-hero"','class="snapshot"','class="trust"','class="section management"',
        '"@type":"Service"','"@type":"WebSite"','"mainEntity":{"@id":',
    ]
    if any(x not in raw for x in required):
        problems.append("production_contract")
    bad=[x for x in forbidden if x in raw]
    if bad:
        problems.append("stale_or_machine_copy:"+",".join(bad))
    min_cluster_links = 22
    if raw.count('href="/'+loc["slug"]+'-') < min_cluster_links:
        problems.append("cluster_links")
    if is_academy_intent(intent) and 'class="section academy-choice"' not in raw:
        problems.append("academy_choice_missing")
    visible = re.sub(r'<script.*?</script>|<style.*?</style>|<[^>]+>', ' ', raw, flags=re.S|re.I)
    visible = re.sub(r'\s+',' ',html.unescape(visible)).strip()
    stiff_visible = ["현재 장면","가장 막히는 장면","최근 막힌 장면","병목","재점검","재검증","상태으로","상황형"]
    visible_for_language_qa = visible.replace(loc["dong"], "")
    stiff_found = [x for x in stiff_visible if x in visible_for_language_qa]
    if stiff_found:
        problems.append("stiff_visible_copy:"+",".join(stiff_found))
    min_visible = 4000 if exam_reader_pilot_enabled(base_exam_intent(intent)) else 5200
    if not (min_visible <= len(visible) <= 16000):
        problems.append(f"visible_chars:{len(visible)}")
    return raw,problems


def render_academy_page(source_raw: str, source_name: str, academy_intent: str) -> tuple[str,list[str]]:
    if academy_intent not in ACADEMY_BASE:
        raise ValueError(f"not academy intent: {academy_intent}")
    svc, ex = gold_modules()
    source_slug, source_intent = intent_from_name(source_name)
    base = ACADEMY_BASE[academy_intent]
    if source_intent != base:
        raise ValueError(f"academy source mismatch: {source_name} -> {academy_intent}")
    base_loc = location_from_source(source_raw, source_name, base)
    loc = dict(base_loc)
    loc["service"] = ACADEMY_SERVICE[academy_intent]
    key = next(k for k,v in ex.EXAMS.items() if v["intent"] == base)
    exam = dict(ex.EXAMS[key])
    exam["service"] = ACADEMY_SERVICE[academy_intent]
    exam["intent"] = academy_intent
    rendered = ex.render(source_slug, loc, key, exam)
    # Make schema honest: these are comparison/1:1 guidance pages, not a claim
    # that ENGLISH PT is a physical academy in every locality.
    rendered = rendered.replace('"serviceType":"영어시험 과외"', '"serviceType":"영어시험 수업 비교 및 1:1 맞춤 수업 안내"')
    rendered = rendered.replace('"serviceType": "영어시험 과외"', '"serviceType": "영어시험 수업 비교 및 1:1 맞춤 수업 안내"')
    return productionize(rendered, loc, academy_intent, "exam")


def render_conversation_derived_page(source_raw: str, source_name: str, derived_intent: str) -> tuple[str,list[str]]:
    if derived_intent not in CONV_DERIVED_BASE:
        raise ValueError(f"not conversation derived intent: {derived_intent}")
    svc, _ = gold_modules()
    source_slug, source_intent = intent_from_name(source_name)
    base = CONV_DERIVED_BASE[derived_intent]
    if source_intent != base:
        raise ValueError(f"conversation source mismatch: {source_name} -> {derived_intent}")
    base_loc = location_from_source(source_raw, source_name, base)
    loc = dict(base_loc)
    loc["service"] = CONV_DERIVED_SERVICE[derived_intent]
    profile = CONV_DERIVED_PROFILE[derived_intent]
    source = CONV_DERIVED_SOURCE[derived_intent]
    rendered = svc.render_page(
        source_slug, loc, derived_intent, profile,
        source["cards"], source["steps"], source["proofs"], source["feedback"]
    )
    if derived_intent in CONV_ACADEMY_INTENTS:
        rendered = rendered.replace(
            '"serviceType":"영어교육"',
            '"serviceType":"영어회화 수업 비교 및 1:1 맞춤 수업 안내"'
        )
        rendered = rendered.replace(
            '"serviceType": "영어교육"',
            '"serviceType": "영어회화 수업 비교 및 1:1 맞춤 수업 안내"'
        )
    return productionize(rendered, loc, derived_intent, "service")


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
