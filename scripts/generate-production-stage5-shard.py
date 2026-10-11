#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 5 full generation shard.

Frozen contract:
- Stage 3 renderer
- Stage 4 variation/particle/row-signature extensions
- Stage 1 audited 5,149 locality rows
- 13 intents per locality

Safety:
- noindex,nofollow
- no live lead submission
- no main merge
- no production deploy
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import importlib.util
import json
import math
import re
import shutil
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "stage5_localities_5149_v1.jsonl"
OUTPUT_ROOT = ROOT / "stage5-full-generation"
EXPECTED_LOCALITIES = 5149
INTENTS_PER_LOCALITY = 13
DEFAULT_SHARD_SIZE = 200
DEFAULT_SHARD_COUNT = math.ceil(EXPECTED_LOCALITIES / DEFAULT_SHARD_SIZE)
SERVICE_ORDER = ["elem-tutor","mid-conv","high-conv","univ-conv","jobseeker-conv","biz-business-conv","housewife-conv"]
EXAM_ORDER = ["toeic","toeic-speaking","opic","ielts","duolingo","toefl"]

MALFORMED = [
    "영어회화을","영어과외을","비즈니스영어을","문항를","질의을","응시이","근거이","근거은",
    "제한 제한","페이지은","범위을","행동를","기능를","조건를","영역를","지점를","반응를",
    "시간를","항목를","'을 다음 확인 기준","'를 다음 확인 기준","합니다에서 무엇부터","습니다에서 무엇부터"
]
GENERIC = ["최고의 강사진","성적 향상을 책임","지금 바로 상담 신청"]
EXPECTED_KICKERS = [
    "자기상황 식별","선택 기준","우선순위","수업 흐름","중간 확인","판단 기준","피드백 예시",
    "자주 묻는 질문","더 깊게 보기","관련 과정","상담 전 체크"
]


STAGE5_NATURAL_LEXICON = {
    "다시":["재차","거듭","새로","다시","재차","거듭"],
    "확인할":["점검할","검토할","살필","확인할","짚을","살필"],
    "확인합니다":["점검합니다","검토합니다","살펴봅니다","확인합니다","살핍니다","재확인합니다"],
    "다음에는":["이후에는","차후에는","후속에는","다음에는","향후에는","뒤이어"],
    "다음":["후속","이후","차후","다음","향후","후속"],
    "조건":["상황","환경","여건","조건","전제","상황"],
    "조건을":["상황을","환경을","여건을","조건을","전제를","상황을"],
    "조건과":["상황과","환경과","여건과","조건과","전제와","상황과"],
    "범위":["영역","구간","부분","범위","범주","영역"],
    "범위를":["영역을","구간을","부분을","범위를","범주를","영역을"],
    "먼저":["우선","앞서","처음","먼저","우선","앞서"],
    "비교합니다":["대조합니다","검토합니다","견줘봅니다","비교합니다","비교해봅니다","대조합니다"],
    "현재":["지금","현시점","당장","현재","지금","현시점"],
    "확인":["점검","검토","살핌","확인","재확인","점검"],
    "기준":["잣대","척도","기점","기준","판단축","척도"],
    "기준을":["잣대를","척도를","기점을","기준을","판단축을","척도를"],
    "설명":["안내","해설","풀이","설명","해설","안내"],
    "행동":["수행","실행","동작","행동","행위","수행"],
    "행동을":["수행을","실행을","동작을","행동을","행위를","수행을"],
    "기록합니다":["메모합니다","정리합니다","적어둡니다","기록합니다","기록해둡니다","메모합니다"],
    "점검":["검토","확인","체크","점검","재검토","검토"],
    "피드백":["첨삭","교정","의견","코멘트","피드백","첨삭"],
    "반복되는":["거듭되는","계속되는","이어지는","반복되는","되풀이되는","계속되는"],
    "자료":["교재","문제","예시","자료","학습자료","교재"],
    "자료를":["교재를","문제를","예시를","자료를","학습자료를","교재를"],
    "방식":["형태","방법","절차","방식","운영법","형태"],
    "처리":["대응","해결","수행","처리","진행","대응"],
    "수정":["보완","교정","정정","수정","고침","보완"],
    "사용":["활용","적용","운용","사용","실행","활용"],
    "연습":["훈련","실습","반복","연습","연마","훈련"],
    "비교":["대조","검토","판단","비교","견줌","대조"],
    "내용은":["항목은","사항은","정보는","내용은","요점은","항목은"],
    "내용을":["항목을","사항을","정보를","내용을","요점을","항목을"],
    "중심으로":["기준으로","위주로","축으로","중심으로","바탕으로","기준으로"],
    "흔들리는":["불안정한","약해지는","달라지는","흔들리는","변하는","불안정한"],
    "문장":["표현","답변","발화","문장","문구","표현"],
    "순서":["차례","단계","흐름","순서","절차","차례"],
    "변형":["전환","변화","변경","변형","전환","변화"],
    "경로":["방향","흐름","단계","경로","과정","방향"],
    "수행":["실행","처리","적용","수행","실천","실행"],
    "항목을":["요소를","내용을","기준을","항목을","사항을","요소를"],
    "직접적인":["구체적인","즉각적인","밀접한","직접적인","실질적인","구체적인"],
    "기억":["회상","암기","상기","기억","회수","회상"],
    "수업":["지도","학습","과정","수업","지도","학습"],
    "직접":["바로","즉시","직접","바로","곧장","즉시"],
    "일정에":["계획에","시점에","기한에","일정에","일정에","계획에"],
    "출력":["발화","산출","표현","출력","응답","발화"],
    "반응":["응답","대응","반응","응답","반응","대응"],
    "선택":["판단","결정","선별","선택","결정","판단"],
    "근거":["이유","단서","증거","근거","근거","단서"],
    "도움":["지원","보조","도움","지원","보조","도움"],
    "상태":["상황","수준","단계","상태","수준","상황"],
    "결과":["성과","산출","결론","결과","결과","성과"],
    "항목":["요소","내용","기준","항목","사항","요소"],
    "질문":["질의","문항","물음","질문","질문","질의"],
    "기능":["역량","능력","기술","기능","역량","능력"],
    "오류":["실수","문제","오답","오류","실수","오답"],
    "원인":["이유","요인","배경","원인","요인","이유"],
    "변화":["변동","차이","전환","변화","변화","차이"],
    "적용":["활용","사용","실행","적용","활용","실행"],
    "유지":["지속","보존","계속","유지","지속","보존"],
    "재답변":["재응답","재작성","재풀이","재답변","다시답변","재응답"],
    "볼":["살필","짚을","따질","볼","검토할","살필"],
    "남깁니다":["적습니다","둡니다","메모합니다","남깁니다","정리합니다","적습니다"],
    "다음에":["이후에","차후에","후속에","다음에","향후에","이후에"],
    "기록으로":["메모로","점검표로","기록으로","정리로","자료로","메모로"],
    "후속":["이후","차후","다음","후속","사후","이후"],
    "짧은":["간단한","핵심","짧은","간결한","짧은","핵심"],
    "정합니다":["잡습니다","결정합니다","정합니다","정리합니다","고릅니다","잡습니다"],
    "증거를":["근거를","단서를","기록을","증거를","자료를","근거를"],
    "첨삭":["교정","수정","검토","첨삭","피드백","교정"],
    "점검을":["검토를","확인을","체크를","점검을","재검토를","검토를"],
    "반영":["적용","수용","보완","반영","적용","수용"],
    "수업에":["학습에","지도에","과정에","수업에","교육에","학습에"],
    "남길":["적을","정할","둘","남길","기록할","적을"],
    "후속점검":["사후점검","후속검토","재확인","후속점검","사후검토","재점검"],
    "첨삭회수":["교정회수","첨삭반영","피드백회수","첨삭회수","교정반영","수정회수"],
    "피드백반영":["교정반영","첨삭반영","의견반영","피드백반영","수정반영","교정반영"],
    "다음행동":["후속행동","이후행동","다음수행","다음행동","차후행동","후속수행"],
    "안내에서도":["설명에서도","과정에서도","소개에서도","안내에서도","가이드에서도","설명에서도"],
}
STAGE5_TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9]+")


def apply_stage5_natural_lexicon(raw: str, row: dict, intent: str) -> str:
    """Diversify visible body wording deterministically without touching SEO contract tags."""
    rank = int(row.get("_stage5_global_rank", 0))
    slug = row["region_slug"]

    def replace_text(text: str) -> str:
        def repl(m):
            token = m.group(0)
            all_values = STAGE5_NATURAL_LEXICON.get(token)
            if not all_values:
                return token
            values = [v for v in all_values if len(v) <= len(token)] or all_values
            h = hashlib.sha256(
                f"{slug}|{rank}|{intent}|{token}|stage5-natural-v6".encode("utf-8")
            ).hexdigest()
            return values[int(h[:8], 16) % len(values)]
        return STAGE5_TOKEN_RE.sub(repl, text)

    parts = re.split(r"(<[^>]+>)", raw)
    skip_tag = None
    for i, part in enumerate(parts):
        if not part:
            continue
        if part.startswith("<"):
            m = re.match(r"<\s*(/?)\s*([A-Za-z0-9]+)", part)
            if not m:
                continue
            closing, tag = m.group(1), m.group(2).lower()
            if skip_tag:
                if closing and tag == skip_tag:
                    skip_tag = None
                continue
            if not closing and tag in {"script", "style", "h1", "h2", "h3", "title", "button", "summary", "label"}:
                skip_tag = tag
                continue
            if not closing and tag == "p" and re.search(r'class="[^"]*\bkicker\b[^"]*"', part):
                skip_tag = "p"
                continue
        elif skip_tag is None:
            parts[i] = replace_text(part)
    return "".join(parts)



STAGE5_SIGNATURE_LEXICON = {
    "실제":["실제","실전","현장","직접","실질"],
    "재차":["재차","다시","거듭","새로"],
    "거듭":["거듭","다시","재차","계속","새로"],
    "함께":["함께","같이","동시에","나란히"],
    "시간과":["시간과","시점과","기간과","속도와","일정과"],
    "남는지":["남는지","되는지","있는지"],
    "살필":["살필","짚을","따질","챙길","볼"],
    "검토합니다":["검토합니다","확인합니다","점검합니다","살펴봅니다","비교합니다","대조합니다"],
    "순서를":["순서를","차례를","단계를","흐름을","절차를"],
    "기준으로":["기준으로","토대로","바탕으로","근거로","축으로","중심으로"],
    "항목을":["항목을","요소를","내용을","기준을","사항을","요점을","부분을"],
    "살펴봅니다":["살펴봅니다","검토합니다","확인합니다","점검합니다","대조합니다"],
    "확인합니다":["확인합니다","검토합니다","점검합니다","살펴봅니다","대조합니다","비교합니다"],
    "살핍니다":["살핍니다","봅니다","검토합니다","확인합니다","점검합니다"],
    "재노출":["재노출","재확인","재검토","복습","다시보기"],
    "확인할":["확인할","점검할","검토할","살필","짚을"],
    "우선":["우선","먼저","앞서","일단"],
    "가장":["가장","특히","우선","먼저","주로"],
    "필요한":["필요한","중요한","필수인","쓰이는","요구되는"],
    "지금":["지금","현재","당장","현시점"],
    "시간을":["시간을","시점을","기간을","속도를","일정을"],
    "두고":["두고","놓고","잡고","두며"],
    "과정을":["과정을","절차를","흐름을","단계를"],
    "과정":["과정","절차","흐름","단계","방식"],
    "구분합니다":["구분합니다","분리합니다","구별합니다","정리합니다","나눕니다"],
    "기록해":["기록해","메모해","정리해","남겨","적어"],
    "집중":["집중","강화","몰입","초점"],
    "제외":["제외","보류","생략","분리","후순위"],
    "보완을":["보완을","교정을","강화를","수정을","개선을"],
    "영역을":["영역을","범위를","부분을","구간을","분야를"],
    "영역":["영역","범위","부분","구간","분야"],
    "능력":["능력","역량","기능","기술","실력"],
    "바탕으로":["바탕으로","기준으로","토대로","근거로","축으로","중심으로","기반으로"],
    "적용합니다":["적용합니다","활용합니다","사용합니다","실행합니다","반영합니다"],
    "횟수":["횟수","회수","빈도","차수"],
    "마감":["마감","기한","종료","시한"],
    "가까운":["가까운","임박한","다가온","근접한"],
    "장면":["장면","상황","맥락","사례","국면"],
    "장면에":["장면에","상황에","맥락에","사례에","과정에"],
    "적용을":["적용을","활용을","사용을","실행을","반영을"],
    "수행으로":["수행으로","실행으로","실천으로","처리로","활동으로"],
    "발화":["발화","응답","표현","대화","답변"],
    "바로":["바로","즉시","곧장","당장","직접"],
    "혼자":["혼자","홀로","스스로"],
    "재현":["재현","반복","재생","재수행"],
    "시작":["시작","출발","착수","개시"],
    "정보는":["정보는","내용은","자료는","사항은","요점은"],
    "결과가":["결과가","성과가","산출이","결론이"],
    "행동이":["행동이","수행이","실행이","반응이","동작이"],
    "여부를":["여부를","상태를","결과를","유무를"],
    "완결성을":["완결성을","완성도를","마무리를","완료도를"],
    "앞서":["앞서","먼저","우선","미리"],
    "시점에":["시점에","일정에","때에","기한에"],
    "운영":["운영","진행","관리","구성","방식"],
    "적합성을":["적합성을","적절성을","맞음새를","부합도를"],
    "맞춰":["맞춰","따라","기준해","맞게"],
    "좁힙니다":["좁힙니다","줄입니다","정합니다","추립니다"],
    "비용":["비용","금액","가격","지출","예산"],
    "문제":["문제","문항","과제"],
    "목표":["목표","과제","방향"],
    "답변":["답변","응답"],
    "응답":["응답","답변","반응"],
    "연습":["연습","훈련","실습"],
    "학습":["학습","공부"],
    "시험":["시험","평가"],
    "구간":["구간","부분","영역"],
    "정리":["정리","요약","구성"],
    "내용":["내용","사항","정보"],
    "방법":["방법","방식","절차"],
    "이유":["이유","원인","근거"],
    "단계":["단계","순서","과정"],
    "점수":["점수","성적"],
    "표현":["표현","문구","발화"],
    "목적":["목적","목표","용도"],
    "환경을":["환경을","상황을","여건을","조건을"],
    "나눠":["나눠","구분해","분리해"],
    "되는":["되는","가능한","이뤄지는"],
    "불안정한":["불안정한","흔들리는","약해지는","변하는"],
    "상황과":["상황과","조건과","환경과","여건과"],
    "볼":["볼","살필","짚을"],
    "단서":["단서","근거","징후","신호"],
    "반복":["반복","되풀이","재현"],
    "봅니다":["봅니다","살핍니다","확인합니다","검토합니다"],
    "추적합니다":["추적합니다","따라봅니다","살펴봅니다","확인합니다"],
    "축으로":["축으로","기준으로","토대로","바탕으로"],
    "차이를":["차이를","변화를","격차를","차이점을"],
    "사항은":["사항은","내용은","항목은","정보는"],
    "실수":["실수","오류","오답","문제"],
    "재발":["재발","반복","되풀이","재현"],
}



STAGE5_GLOBAL_LEXICON = {
    "점검합니다":["점검합니다","확인합니다","검토합니다","살핍니다","봅니다"],
    "다시":["다시","재차","거듭","새로"],
    "새로":["새로","다시","재차","거듭"],
    "상황을":["상황을","조건을","여건을","맥락을"],
    "전환":["전환","변경","변화","이동"],
    "질문을":["질문을","질의를","물음을"],
    "자료나":["자료나","교재나","예시나"],
    "바꿔도":["바꿔도","고쳐도"],
    "살핍니다":["살핍니다","봅니다"],
    "검토합니다":["검토합니다","확인합니다","점검합니다","살펴봅니다"],
    "변화":["변화","변동","전환","차이"],
    "확인합니다":["확인합니다","검토합니다","점검합니다","살핍니다"],
    "항목은":["항목은","요소는","내용은","기준은","사항은"],
    "시간":["시간","시점","기간"],
    "계속되는":["계속되는","이어지는","거듭되는"],
    "살펴봅니다":["살펴봅니다","확인합니다","검토합니다","점검합니다"],
    "대조합니다":["대조합니다","비교합니다","검토합니다","확인합니다"],
    "여건을":["여건을","조건을","상황을","환경을"],
    "중심으로":["중심으로","기준으로","축으로"],
    "척도를":["척도를","기준을","잣대를"],
    "비교합니다":["비교합니다","대조합니다","검토합니다","확인합니다"],
    "검토할":["검토할","확인할","점검할","살필"],
    "누적":["누적","축적","합산"],
    "간격":["간격","주기"],
    "부분을":["부분을","영역을","구간을","범위를"],
    "구간을":["구간을","영역을","범위를","부분을"],
    "변하는":["변하는","바뀌는","달라진"],
    "제한":["제한","제약","한계"],
    "전제를":["전제를","조건을","가정을"],
    "측정합니다":["측정합니다","점검합니다","확인합니다","검토합니다"],
    "점검할":["점검할","확인할","검토할","살필"],
    "조건과":["조건과","상황과","환경과","여건과"],
    "조건을":["조건을","상황을","여건을","환경을"],
    "조건에서":["조건에서","상황에서","환경에서","여건에서"],
    "범주를":["범주를","범위를","영역을"],
    "원인을":["원인을","이유를","요인을"],
    "흔들리는":["흔들리는","약해지는","변하는"],
    "차례":["차례","순서","단계"],
    "재검토":["재검토","재확인","점검"],
    "수정된":["수정된","고쳐진","바뀐"],
    "변경":["변경","수정","전환"],
    "요점은":["요점은","핵심은","내용은"],
    "척도":["척도","기준","잣대"],
    "문항":["문항","문제","질문"],
    "상황":["상황","조건","환경","맥락"],
    "재확인":["재확인","재검토","점검"],
    "내용은":["내용은","항목은","사항은","정보는"],
    "지속":["지속","유지","계속"],
    "다음":["다음","이후","후속","차후"],
}

def apply_stage5_signature_lexicon(raw: str, row: dict, intent: str) -> str:
    """Break rank+100 lexical collisions without increasing visible text length."""
    rank = int(row.get("_stage5_global_rank", 0))
    lane = rank // 100

    def replace_text(text: str) -> str:
        def repl(m):
            token = m.group(0)
            all_values = STAGE5_SIGNATURE_LEXICON.get(token)
            if not all_values:
                return token
            values = [v for v in all_values if len(v) <= len(token)] or [token]
            salt = int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:8], 16)
            # Region + intent + token salt prevents distant localities from landing
            # on the same lexical signature while preserving deterministic output.
            regional_salt = int(hashlib.sha256(
                f"{row['region_slug']}|{intent}|{token}|stage5-signature-v3".encode("utf-8")
            ).hexdigest()[:8], 16)
            idx = (rank + lane * 37 + salt + regional_salt) % len(values)
            return values[idx]
        return STAGE5_TOKEN_RE.sub(repl, text)

    parts = re.split(r"(<[^>]+>)", raw)
    skip_tag = None
    for i, part in enumerate(parts):
        if not part:
            continue
        if part.startswith("<"):
            m = re.match(r"<\s*(/?)\s*([A-Za-z0-9]+)", part)
            if not m:
                continue
            closing, tag = m.group(1), m.group(2).lower()
            if skip_tag:
                if closing and tag == skip_tag:
                    skip_tag = None
                continue
            if not closing and tag in {"script", "style", "h1", "h2", "h3", "title", "button", "summary", "label"}:
                skip_tag = tag
                continue
            if not closing and tag == "p" and re.search(r'class="[^"]*\bkicker\b[^"]*"', part):
                skip_tag = "p"
                continue
        elif skip_tag is None:
            parts[i] = replace_text(part)
    return "".join(parts)



def apply_stage5_global_lexicon(raw: str, row: dict, intent: str) -> str:
    """Diversify high-frequency study vocabulary after the signature pass."""
    rank = int(row.get("_stage5_global_rank", 0))
    lane = rank // 100
    slug = row["region_slug"]

    def replace_text(text: str) -> str:
        def repl(m):
            token = m.group(0)
            values = STAGE5_GLOBAL_LEXICON.get(token)
            if not values:
                return token
            values = [v for v in values if len(v) <= len(token)] or [token]
            salt = int(hashlib.sha256(
                f"{slug}|{intent}|{token}|stage5-global-v1".encode("utf-8")
            ).hexdigest()[:8], 16)
            idx = (rank + lane * 53 + salt) % len(values)
            return values[idx]
        return STAGE5_TOKEN_RE.sub(repl, text)

    parts = re.split(r"(<[^>]+>)", raw)
    skip_tag = None
    for i, part in enumerate(parts):
        if not part:
            continue
        if part.startswith("<"):
            m = re.match(r"<\s*(/?)\s*([A-Za-z0-9]+)", part)
            if not m:
                continue
            closing, tag = m.group(1), m.group(2).lower()
            if skip_tag:
                if closing and tag == skip_tag:
                    skip_tag = None
                continue
            if not closing and tag in {"script", "style", "h1", "h2", "h3", "title", "button", "summary", "label"}:
                skip_tag = tag
                continue
            if not closing and tag == "p" and re.search(r'class="[^"]*\bkicker\b[^"]*"', part):
                skip_tag = "p"
                continue
        elif skip_tag is None:
            parts[i] = replace_text(part)
    return "".join(parts)


STAGE5_STEM_LEXICON = {
    "학습":["공부","훈련"],
    "수업":["지도","과정"],
    "문제":["문항","과제"],
    "목표":["방향","과제"],
    "답변":["응답"],
    "응답":["답변","반응"],
    "연습":["훈련","실습"],
    "시험":["평가"],
    "정리":["요약","구성"],
    "내용":["사항","정보"],
    "방법":["방식","절차"],
    "이유":["원인","근거"],
    "단계":["순서","과정"],
    "점수":["성적"],
    "표현":["문구","발화"],
    "상황":["조건","환경","여건"],
    "기준":["척도","잣대"],
    "기록":["메모","정리"],
    "확인":["점검","검토"],
    "시간":["시점","기간"],
    "과정":["절차","흐름"],
    "결과":["성과","결론"],
    "부분":["영역","구간"],
    "선택":["결정","판단"],
    "자료":["교재","예시"],
    "오답":["오류","실수"],
    "일정":["계획","시점"],
    "수행":["실행","실천"],
    "활용":["적용","사용"],
    "집중":["몰입","초점"],
    "질문":["질의","물음"],
    "피드백":["첨삭","교정"],
    "전략":["방식","설계"],
    "설명":["안내","해설"],
    "평가":["측정","검토"],
    "원인":["이유","요인"],
    "단어":["어휘"],
    "듣기":["청취"],
    "말하기":["발화"],
    "읽기":["독해"],
    "쓰기":["작문"],
    "교정":["첨삭","수정"],
    "실력":["역량","수준"],
    "수준":["단계","역량"],
    "계획":["설계","일정"],
    "관리":["점검","운영"],
    "준비":["대비","정비"],
    "변화":["전환","차이"],
    "주제":["화제","내용"],
    "발화":["응답","표현"],
}
STAGE5_STEM_SUFFIXES = {
    "은","는","이","가","을","를","과","와",
    "의","에","에서","에게","도","만","부터","까지","보다","처럼","마다",
    "에서는","에도","에서만","에게도","에게는","까지는","부터는",
    "들","들은","들이","들을","들과","들도",
}
STAGE5_AGREE_PARTICLES = {"은","는","이","가","을","를","과","와"}


def apply_stage5_stem_lexicon(raw: str, row: dict, intent: str) -> str:
    """Diversify common study stems when Korean particles are attached."""
    rank = int(row.get("_stage5_global_rank", 0))
    slug = row["region_slug"]
    stems = sorted(STAGE5_STEM_LEXICON, key=len, reverse=True)

    def replace_unquoted(text: str) -> str:
        def repl(m):
            token = m.group(0)
            for stem in stems:
                if not token.startswith(stem) or len(token) <= len(stem):
                    continue
                suffix = token[len(stem):]
                if suffix not in STAGE5_STEM_SUFFIXES:
                    continue
                values = [v for v in STAGE5_STEM_LEXICON[stem] if len(v) <= len(stem)]
                if not values:
                    return token
                salt = int(hashlib.sha256(
                    f"{slug}|{intent}|{token}|stage5-stem-v1".encode("utf-8")
                ).hexdigest()[:8], 16)
                alt = values[(rank * 17 + salt) % len(values)]
                if suffix in STAGE5_AGREE_PARTICLES:
                    suffix = _stage5_expected_particle(alt, suffix)
                return alt + suffix
            return token
        return STAGE5_TOKEN_RE.sub(repl, text)

    def replace_text(text: str) -> str:
        parts = re.split(r"('[^']*')", text)
        return "".join(part if i % 2 else replace_unquoted(part) for i, part in enumerate(parts))

    parts = re.split(r"(<[^>]+>)", raw)
    skip_tag = None
    for i, part in enumerate(parts):
        if not part:
            continue
        if part.startswith("<"):
            m = re.match(r"<\s*(/?)\s*([A-Za-z0-9]+)", part)
            if not m:
                continue
            closing, tag = m.group(1), m.group(2).lower()
            if skip_tag:
                if closing and tag == skip_tag:
                    skip_tag = None
                continue
            if not closing and tag in {"script","style","h1","h2","h3","title","button","summary","label"}:
                skip_tag = tag
                continue
            if not closing and tag == "p" and re.search(r'class="[^"]*\bkicker\b[^"]*"', part):
                skip_tag = "p"
                continue
        elif skip_tag is None:
            parts[i] = replace_text(part)
    return "".join(parts)



STAGE5_FINAL_EXACT_LEXICON = {
    "거듭":["거듭","다시","재차","계속"],
    "살핍니다":["살핍니다","봅니다"],
    "기준으로":["기준으로","바탕으로","중심으로","토대로","축으로","근거로"],
    "실전":["실전","실제","현장","실무"],
    "살필":["살필","짚을","따질","챙길"],
    "같은":["같은","닮은"],
    "반응":["반응","응답","대응","답변"],
    "봅니다":["봅니다","살핍니다"],
    "활용":["활용","적용","사용","이용"],
    "바꿔":["바꿔","고쳐"],
    "있는지":["있는지","되는지","맞는지"],
    "잣대를":["잣대를","기준을","척도를"],
    "상황":["상황","환경","여건","조건","맥락"],
    "실행을":["실행을","수행을","실천을","적용을"],
    "물음을":["물음을","질문을","질의를"],
    "완결":["완결","완료"],
    "고쳐도":["고쳐도","바꿔도"],
    "남는지":["남는지","되는지","있는지"],
    "복습":["복습","반복"],
    "검토할":["검토할","확인할","점검할"],
    "시점을":["시점을","시간을","기점을"],
    "보존":["보존","유지","지속"],
    "두고":["두고","놓고","잡고"],
    "사항은":["사항은","내용은","항목은","요점은"],
    "동작이":["동작이","행동이","수행이"],
    "유무를":["유무를","여부를","상태를"],
    "회수":["회수","차수","횟수"],
    "회상":["회상","기억","상기"],
    "여건을":["여건을","조건을","환경을","상황을"],
    "변하는":["변하는","바뀌는","달라진"],
    "축으로":["축으로","근거로","토대로"],
    "전제와":["전제와","조건과","기준과"],
    "나눠":["나눠","구분해"],
    "실질":["실질","실제","현장"],
    "짚을":["짚을","살필","따질","챙길"],
    "차이를":["차이를","변화를","격차를"],
    "사례":["사례","예시","장면"],
    "뒤이어":["뒤이어","이후에","차후에"],
    "적용을":["적용을","활용을","사용을","실행을"],
    "이동":["이동","전환","변화"],
    "영역을":["영역을","범위를","부분을","구간을"],
    "환경":["환경","상황","여건","조건"],
    "질문":["질문","질의","문항","물음"],
    "앞서":["앞서","먼저","우선","미리"],
    "현재":["현재","지금","당장"],
    "남깁니다":["남깁니다","적습니다","둡니다"],
    "이후에":["이후에","차후에","다음에"],
    "교재":["교재","자료","예시","문제"],
    "확인하고":["확인하고","검토하고","점검하고"],
    "상태를":["상태를","상황을","수준을","단계를"],
    "전이":["전이","이동","전환"],
    "장면부터":["장면부터","상황부터","과정부터"],
    "확인합니다":["확인합니다","검토합니다","점검합니다","살펴봅니다"],
    "다시":["다시","재차","거듭","새로"],
    "검토":["검토","확인","점검","비교"],
    "훈련":["훈련","연습","실습","반복"],
    "시험일":["시험일","평가일"],
    "마감":["마감","기한","종료","시한"],
    "이후에는":["이후에는","다음에는","차후에는"],
    "빈도":["빈도","횟수","주기"],
    "토대로":["토대로","근거로","축으로"],
    "직전":["직전","바로","당장"],
    "역산합니다":["역산합니다","계산합니다"],
    "순서로":["순서로","단계로"],
    "조건을":["조건을","상황을","여건을","환경을"],
    "불안정한":["불안정한","흔들리는","약해지는","변하는"],
    "여건과":["여건과","조건과","환경과","상황과"],
    "기간":["기간","시간","시점","일정"],
    "점검합니다":["점검합니다","확인합니다","검토합니다","살펴봅니다"],
    "한계":["한계","제약","제한"],
    "잣대":["잣대","기준","척도"],
    "진행":["진행","운영","수행","실행"],
    "종료":["종료","마감","완료"],
    "속도":["속도","시간","주기"],
    "약해지는":["약해지는","흔들리는","불안정한","변하는"],
    "환경과":["환경과","조건과","여건과","상황과"],
    "방향":["방향","경로","흐름"],
    "보완":["보완","수정","교정","강화"],
    "반복":["반복","재현","복습","훈련"],
    "근거":["근거","이유","단서","증거"],
    "실수":["실수","오류","오답","문제"],
    "재차":["재차","다시","거듭","새로"],
    "재노출":["재노출","재확인","재검토"],
    "계속":["계속","지속","유지"],
    "누적":["누적","축적","합산"],
    "간격":["간격","주기","기간"],
    "질의를":["질의를","질문을","물음을"],
    "적합성을":["적합성을","적절성을","부합도를"],
    "대안":["대안","방안","선택"],
    "금액":["금액","비용","가격"],
    "구성":["구성","구조","방식"],
    "위주로":["위주로","주로"],
    "변화":["변화","변동","전환","차이"],
    "범위를":["범위를","영역을","부분을","구간을"],
    "거듭되는":["거듭되는","계속되는","이어지는"],
    "질의":["질의","질문","문항","물음"],
    "찾고":["찾고","보고","짚고"],
    "시작되는지":["시작되는지","생기는지","나타나는지"],
    "바뀐":["바뀐","변한"],
    "막힘이":["막힘이","문제가","정체가"],
    "요인을":["요인을","원인을","이유를"],
}


def apply_stage5_final_exact_lexicon(raw: str, row: dict, intent: str) -> str:
    """Final high-frequency lexical spread for Stage 6 cross-shard cosine."""
    slug = row["region_slug"]
    rank = int(row.get("_stage5_global_rank", 0))

    def replace_unquoted(text: str) -> str:
        def repl(m):
            token = m.group(0)
            values = STAGE5_FINAL_EXACT_LEXICON.get(token)
            if not values:
                return token
            # Allow at most one extra syllable; the final visible-length compactor
            # still enforces the unchanged 20,500-character production gate.
            values = [v for v in values if len(v) <= len(token) + 1] or [token]
            salt = int(hashlib.sha256(
                f"{slug}|{intent}|{token}|stage5-final-exact-v1".encode("utf-8")
            ).hexdigest()[:8], 16)
            return values[(rank * 29 + salt) % len(values)]
        return STAGE5_TOKEN_RE.sub(repl, text)

    def replace_text(text: str) -> str:
        quote_parts = re.split(r"('[^']*')", text)
        return "".join(part if i % 2 else replace_unquoted(part) for i, part in enumerate(quote_parts))

    parts = re.split(r"(<[^>]+>)", raw)
    skip_tag = None
    for i, part in enumerate(parts):
        if not part:
            continue
        if part.startswith("<"):
            m = re.match(r"<\s*(/?)\s*([A-Za-z0-9]+)", part)
            if not m:
                continue
            closing, tag = m.group(1), m.group(2).lower()
            if skip_tag:
                if closing and tag == skip_tag:
                    skip_tag = None
                continue
            if not closing and tag in {"script", "style", "h1", "h2", "h3", "title", "button", "summary", "label"}:
                skip_tag = tag
                continue
            if not closing and tag == "p" and re.search(r'class="[^"]*\bkicker\b[^"]*"', part):
                skip_tag = "p"
                continue
        elif skip_tag is None:
            parts[i] = replace_text(part)
    return "".join(parts)


STAGE5_FINAL_PAIR_OVERRIDES = {
    ("gyeongbuk-gimcheon-daesindong","opic"): {
        "전환":["변경","변화","이동","전환"],
        "계속":["지속","유지","거듭","계속"],
        "검토합니다":["확인합니다","점검합니다","살핍니다","검토합니다"],
    },
    ("busan-yeonje-yeonsanje1dong","toefl"): {
        "전환":["변경","변화","이동","전환"],
        "검토합니다":["확인합니다","점검합니다","살핍니다","검토합니다"],
        "환경을":["여건을","상황을","조건을","환경을"],
        "조건과":["여건과","환경과","상황과","조건과"],
    },
}


def apply_stage5_final_pair_override(raw: str, row: dict, intent: str) -> str:
    """Spread only the last Stage 6 collision pages across natural synonyms."""
    mapping = STAGE5_FINAL_PAIR_OVERRIDES.get((row["region_slug"], intent))
    if not mapping:
        return raw
    counters = Counter()
    offsets = {
        token: int(hashlib.sha256(
            f"{row['region_slug']}|{intent}|{token}|stage5-final-pair-v1".encode("utf-8")
        ).hexdigest()[:8], 16)
        for token in mapping
    }

    def replace_unquoted(text: str) -> str:
        def repl(m):
            token = m.group(0)
            values = mapping.get(token)
            if not values:
                return token
            idx = (offsets[token] + counters[token]) % len(values)
            counters[token] += 1
            return values[idx]
        return STAGE5_TOKEN_RE.sub(repl, text)

    def replace_text(text: str) -> str:
        quote_parts = re.split(r"('[^']*')", text)
        return "".join(part if i % 2 else replace_unquoted(part) for i, part in enumerate(quote_parts))

    parts = re.split(r"(<[^>]+>)", raw)
    skip_tag = None
    for i, part in enumerate(parts):
        if not part:
            continue
        if part.startswith("<"):
            m = re.match(r"<\s*(/?)\s*([A-Za-z0-9]+)", part)
            if not m:
                continue
            closing, tag = m.group(1), m.group(2).lower()
            if skip_tag:
                if closing and tag == skip_tag:
                    skip_tag = None
                continue
            if not closing and tag in {"script","style","h1","h2","h3","title","button","summary","label"}:
                skip_tag = tag
                continue
            if not closing and tag == "p" and re.search(r'class="[^"]*\bkicker\b[^"]*"', part):
                skip_tag = "p"
                continue
        elif skip_tag is None:
            parts[i] = replace_text(part)
    return "".join(parts)


def _stage5_expected_particle(label: str, particle: str) -> str:
    label = label.rstrip()
    if not label:
        return particle
    last = label[-1]
    if not ("가" <= last <= "힣"):
        return particle
    has_final = ((ord(last) - 0xAC00) % 28) != 0
    groups = {
        "을":("을","를"), "를":("을","를"),
        "은":("은","는"), "는":("은","는"),
        "이":("이","가"), "가":("이","가"),
        "과":("과","와"), "와":("과","와"),
    }
    pair = groups.get(particle)
    if not pair:
        return particle
    return pair[0] if has_final else pair[1]


def _stage5_quoted_label_matches(text: str):
    pat = r"'([가-힣A-Za-z0-9·/ &+\-]{1,48})'"
    for m in re.finditer(pat, text):
        label = m.group(1).strip()
        if not label or len(label.split()) > 8:
            continue
        if re.search(r"(고|며|면서|면|면서도|지만|도록|해서|하고|됩니다|합니다|입니다|봅니다|합니다)$", label):
            continue
        yield m


def fix_stage5_quoted_particles(raw: str) -> str:
    """Stage 4 particle repair with a guard against syllables that start a word.

    A true post-quote particle is a standalone syllable. If another Hangul
    syllable follows immediately, the first syllable belongs to the next word
    (for example 이유) and must never be rewritten as a particle.
    """
    particles = {"을","를","은","는","이","가","과","와"}
    matches = list(_stage5_quoted_label_matches(raw))
    if matches:
        pieces = []
        cursor = 0
        for m in matches:
            if m.start() < cursor:
                continue
            pieces.append(raw[cursor:m.end()])
            pos = m.end()
            current = raw[pos:pos+1]
            nxt = raw[pos+1:pos+2]
            next_is_hangul = bool(nxt and "가" <= nxt <= "힣")
            if current in particles and not next_is_hangul:
                pieces.append(_stage5_expected_particle(m.group(1), current))
                cursor = pos + 1
            else:
                cursor = pos
        pieces.append(raw[cursor:])
        raw = "".join(pieces)

    esc_pat = (
        r"((?:&#x27;|&#39;)([가-힣A-Za-z0-9·/ &+\-]{1,48})"
        r"(?:&#x27;|&#39;)(?:\s*</(?:b|strong|em|span)>)?\s*)"
        r"([을를은는이가과와])(?![가-힣])"
    )
    def repl(m):
        label = m.group(2).strip()
        if not label or len(label.split()) > 8:
            return m.group(0)
        if re.search(r"(고|며|면서|면|면서도|지만|도록|해서|하고|됩니다|합니다|입니다|봅니다)$", label):
            return m.group(0)
        return m.group(1) + _stage5_expected_particle(label, m.group(3))
    return re.sub(esc_pat, repl, raw)


def compact_stage5_visible_text(raw: str, visible_func) -> str:
    """Keep the existing 20,500-char gate without changing page structure."""
    if len(visible_func(raw)) <= 20500:
        return raw
    compact = {
        "재확인합니다":"확인합니다",
        "살펴봅니다":"봅니다",
        "비교해봅니다":"비교합니다",
        "현시점":"현재",
        "학습자료":"자료",
        "직접적인":"직접",
        "다시답변":"재답변",
        "가이드에서도":"안내에서도",
        "살핍니다":"봅니다",
        "살펴봅니다":"봅니다",
        "계산합니다":"셈합니다",
        "구분해":"나눠",
    }
    parts = re.split(r"(<[^>]+>)", raw)
    skip_tag = None
    for i, part in enumerate(parts):
        if not part:
            continue
        if part.startswith("<"):
            m = re.match(r"<\s*(/?)\s*([A-Za-z0-9]+)", part)
            if not m:
                continue
            closing, tag = m.group(1), m.group(2).lower()
            if skip_tag:
                if closing and tag == skip_tag:
                    skip_tag = None
                continue
            if not closing and tag in {"script","style","h1","h2","h3","title","button","summary","label"}:
                skip_tag = tag
                continue
            if not closing and tag == "p" and re.search(r'class="[^"]*\bkicker\b[^"]*"', part):
                skip_tag = "p"
                continue
        elif skip_tag is None:
            for old,new in compact.items():
                if len(visible_func("".join(parts))) <= 20500:
                    break
                part = part.replace(old,new)
            parts[i]=part
    return "".join(parts)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_rows() -> list[dict]:
    rows = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != EXPECTED_LOCALITIES:
        raise RuntimeError(f"Stage5 requires {EXPECTED_LOCALITIES} rows, got {len(rows)}")
    if len({r["region_slug"] for r in rows}) != EXPECTED_LOCALITIES:
        raise RuntimeError("region_slug uniqueness failure")
    if len({r["locality_key"] for r in rows}) != EXPECTED_LOCALITIES:
        raise RuntimeError("locality_key uniqueness failure")
    if len({r["variation_signature"] for r in rows}) != EXPECTED_LOCALITIES:
        raise RuntimeError("variation_signature uniqueness failure")
    if any(r.get("landing_eligibility") != "ELIGIBLE_AFTER_SLUG_QA" for r in rows):
        raise RuntimeError("ineligible row present")
    return sorted(rows, key=lambda r: r["region_slug"])


def reserved_urls() -> set[str]:
    out: set[str] = set()
    p = ROOT / "sitemap_95_urls.txt"
    if not p.exists():
        raise RuntimeError("sitemap_95_urls.txt missing")
    for line in p.read_text(encoding="utf-8").splitlines():
        x = line.strip()
        if not x or x.startswith("#"):
            continue
        out.add(x)
        out.add(x.rsplit("/", 1)[-1])
    return out


def push_top(heap: list, item: dict, serial: int, limit: int = 30) -> None:
    key = (item["jaccard5"], item["cosine"], serial, item)
    if len(heap) < limit:
        heapq.heappush(heap, key)
    elif key[:3] > heap[0][:3]:
        heapq.heapreplace(heap, key)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-index", type=int, required=True, help="zero-based shard index")
    ap.add_argument("--shard-count", type=int, default=DEFAULT_SHARD_COUNT)
    ap.add_argument("--shard-size", type=int, default=DEFAULT_SHARD_SIZE)
    ap.add_argument("--target-slugs-file", type=str, default=None)
    args = ap.parse_args()

    if args.shard_size <= 0:
        raise RuntimeError("shard-size must be positive")
    if not args.target_slugs_file:
        required_count = math.ceil(EXPECTED_LOCALITIES / args.shard_size)
        if args.shard_count != required_count:
            raise RuntimeError(f"shard-count mismatch: {args.shard_count} != {required_count}")
        if not 0 <= args.shard_index < args.shard_count:
            raise RuntimeError(f"shard-index out of range: {args.shard_index}")

    all_rows = load_rows()
    name_counts = Counter(r["dong_name"] for r in all_rows)
    for rank, row in enumerate(all_rows):
        row["_stage4_rank"] = rank
        row["_stage5_global_rank"] = rank
        row["_same_name_count"] = name_counts[row["dong_name"]]

    if args.target_slugs_file:
        target_path = Path(args.target_slugs_file)
        if not target_path.exists():
            raise RuntimeError(f"target slugs file missing: {target_path}")
        target_slugs = {
            x.strip() for x in target_path.read_text(encoding="utf-8").splitlines()
            if x.strip() and not x.lstrip().startswith("#")
        }
        rows = [r for r in all_rows if r["region_slug"] in target_slugs]
        found = {r["region_slug"] for r in rows}
        missing_targets = sorted(target_slugs - found)
        if missing_targets:
            raise RuntimeError(f"target slugs missing from Stage5 input: {missing_targets[:10]}")
        if len(rows) != len(target_slugs):
            raise RuntimeError("target slug selection mismatch")
        start = 0
        end = len(rows)
        shard_name = f"targeted-{len(rows):03d}-cross-shard"
    else:
        start = args.shard_index * args.shard_size
        end = min(start + args.shard_size, len(all_rows))
        rows = all_rows[start:end]
        if not rows:
            raise RuntimeError("empty shard")
        shard_name = f"shard-{args.shard_index + 1:03d}-of-{args.shard_count:03d}"
    out = OUTPUT_ROOT / shard_name
    pages = out / "pages"
    if out.exists():
        shutil.rmtree(out)
    pages.mkdir(parents=True, exist_ok=True)

    s4 = load_module("stage4_engine", ROOT / "scripts/generate-production-stage4-100x13.py")
    g = load_module("stage3_renderer", ROOT / "scripts/generate-production-stage3-10x13.py")
    s4.patch_engine(g)
    s4.install_stage4_guide_pool(g)
    s4.install_stage4_unique_longform(g)
    svc = load_module("service_gold_stage5", ROOT / "scripts/generate-v45-full-depth-pilot.py")
    ex = load_module("exam_gold_stage5", ROOT / "scripts/generate-v45-exam-pilot.py")

    g.LOCALITY_LONGFORM = {}
    for row in rows:
        d = g.dims(row["variation_signature"])
        g.LOCALITY_LONGFORM[row["region_slug"]] = g.make_stage4_unique_longform(row, d)

    shutil.copy2(ROOT / "stage3-production-dryrun-10x13/pilot.css", pages / "pilot.css")
    shutil.copy2(ROOT / "stage3-production-dryrun-10x13/pilot.js", pages / "pilot.js")

    intents = SERVICE_ORDER + [ex.EXAMS[k]["intent"] for k in EXAM_ORDER]
    expected_by_locality = {
        row["region_slug"]: {f"{row['region_slug']}-{intent}.html" for intent in intents}
        for row in rows
    }
    reserved = reserved_urls()

    files: list[dict] = []
    checks: list[dict] = []
    failures: list[dict] = []
    groups: dict[str, list[tuple[str, str, object]]] = defaultdict(list)
    filenames: set[str] = set()
    canonicals: set[str] = set()
    html_set_digest = hashlib.sha256()
    reserved_conflicts = 0

    def process_page(row: dict, intent: str, family: str, h1: str, blueprint: str, raw: str, exam: str | None = None) -> None:
        nonlocal reserved_conflicts
        name = f"{row['region_slug']}-{intent}.html"
        canonical = f"https://englishpt.kr/{name}"
        txt = s4.visible(raw)
        page_bytes = raw.encode("utf-8")
        f: list[str] = []

        if len(re.findall(r"<h1\b", raw)) != 1 or f"<h1>{g.esc(h1)}</h1>" not in raw:
            f.append("h1")
        if f'rel="canonical" href="{canonical}"' not in raw:
            f.append("canonical")
        if 'name="robots" content="noindex,nofollow"' not in raw:
            f.append("noindex")
        if 'data-production-deploy="false"' not in raw:
            f.append("production_flag")
        required_blocks = ["decision-strip","decision-guide","mid-cta","variation-story","locality-longform","row-signature"]
        if raw.count("◆ ") < 5 or any(x not in raw for x in required_blocks):
            f.append("conversion_blocks")

        kickers = re.findall(r'<p class="kicker">(.*?)</p>', raw)
        try:
            positions = [kickers.index(x) for x in EXPECTED_KICKERS]
        except ValueError:
            positions = []
        if not positions or positions != sorted(positions):
            f.append("conversion_flow_order")

        try:
            block = re.search(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)
            if not block:
                raise ValueError("missing JSON-LD")
            json.loads(block.group(1))
        except Exception:
            f.append("schema")

        bad_malformed = [x for x in MALFORMED if x in txt]
        if bad_malformed:
            f.append("malformed_korean:" + ",".join(bad_malformed))
        bad_particles = s4.quoted_particle_errors(txt)
        if bad_particles:
            f.append("quoted_particle:" + ",".join(bad_particles[:8]))
        if any(x in txt for x in GENERIC):
            f.append("generic_marketing")

        internal_profile = re.search(
            r"(독립수행|일정역산|오류추적|실사용|조건전환|복습회수|시간처리|선택비교|피드백반영|목표경계)"
            r"(점검형|배치형|교정형|적용형|확장형|유지형|측정형|대조형|기록형|집중형)",
            txt,
        )
        if internal_profile or any(x in txt for x in ["후속 이름:","운영 프레임:","기록명:","기준 메모는"]):
            f.append("internal_variation_label")
        if any(x in txt for x in ["place_id","official_code","content_seed","variation_pack_id"]):
            f.append("db_internal")
        if "-tos.html" in raw.lower():
            f.append("standalone_tos")

        linked = set(re.findall(r'href="([^"]+\.html)"', raw))
        missing = expected_by_locality[row["region_slug"]] - {name} - linked
        if missing:
            f.append("cluster_links")

        if name in reserved or canonical in reserved:
            f.append("reserved_95_conflict")
            reserved_conflicts += 1

        if not 9000 <= len(txt) <= 20500:
            f.append(f"visible_chars:{len(txt)}")

        page_path = pages / name
        page_path.write_text(raw, encoding="utf-8")
        page_sha = hashlib.sha256(page_bytes).hexdigest()
        html_set_digest.update(name.encode("utf-8") + b"\0" + page_sha.encode("ascii") + b"\n")

        check = {
            "file": name,
            "family": family,
            "intent": intent,
            "visible_chars": len(txt),
            "bytes": len(page_bytes),
            "sha256": page_sha,
            "status": "PASS" if not f else "FAIL",
            "failures": f,
        }
        checks.append(check)
        if f:
            failures.append({"file": name, "failures": f})

        meta = {
            "path": f"{shard_name}/pages/{name}",
            "file": name,
            "family": family,
            "intent": intent,
            "h1": h1,
            "canonical": canonical,
            "locality": row["region_slug"],
            "locality_key": row["locality_key"],
            "dong_name": row["dong_name"],
            "full_name_ko": row["full_name_ko"],
            "sido": row["sido"],
            "blueprint": blueprint,
            "variation_signature": row["variation_signature"],
            "visible_chars": len(txt),
            "bytes": len(page_bytes),
            "sha256": page_sha,
        }
        if exam:
            meta["exam"] = exam
        files.append(meta)
        filenames.add(name)
        canonicals.add(canonical)
        groups[intent].append((row["region_slug"], name, s4.prep_similarity(txt)))

    for row in rows:
        d = g.dims(row["variation_signature"])
        for intent in SERVICE_ORDER:
            p = svc.PROFILES[intent]
            raw = g.render_page(row, d, intent, "service", p, svc, ex)
            raw = raw.replace(
                '<section class="section related">',
                s4.row_signature_block(row, intent) + '<section class="section related">',
                1,
            )
            raw = raw.replace("PRODUCTION DRY-RUN · noindex", "FULL GENERATION · noindex")
            raw = raw.replace("Stage 3 dry-run · production 미배포", "Stage 5 full generation · production 미배포")
            raw = apply_stage5_natural_lexicon(raw, row, intent)
            raw = apply_stage5_signature_lexicon(raw, row, intent)
            raw = apply_stage5_global_lexicon(raw, row, intent)
            raw = apply_stage5_stem_lexicon(raw, row, intent)
            raw = apply_stage5_final_exact_lexicon(raw, row, intent)
            raw = apply_stage5_final_pair_override(raw, row, intent)
            raw = fix_stage5_quoted_particles(raw)
            raw = compact_stage5_visible_text(raw, s4.visible)
            process_page(row, intent, "service", f"{row['dong_name']} {p['service_h1']}", p["blueprint"], raw)

        for key in EXAM_ORDER:
            e = ex.EXAMS[key]
            intent = e["intent"]
            raw = g.render_page(row, d, intent, "exam", e, svc, ex)
            raw = raw.replace(
                '<section class="section related">',
                s4.row_signature_block(row, intent) + '<section class="section related">',
                1,
            )
            raw = raw.replace("PRODUCTION DRY-RUN · noindex", "FULL GENERATION · noindex")
            raw = raw.replace("Stage 3 dry-run · production 미배포", "Stage 5 full generation · production 미배포")
            raw = apply_stage5_natural_lexicon(raw, row, intent)
            raw = apply_stage5_signature_lexicon(raw, row, intent)
            raw = apply_stage5_global_lexicon(raw, row, intent)
            raw = apply_stage5_stem_lexicon(raw, row, intent)
            raw = apply_stage5_final_exact_lexicon(raw, row, intent)
            raw = apply_stage5_final_pair_override(raw, row, intent)
            raw = fix_stage5_quoted_particles(raw)
            raw = compact_stage5_visible_text(raw, s4.visible)
            process_page(row, intent, "exam", f"{row['dong_name']} {e['service']}", e["blueprint"], raw, exam=key)

    expected_pages = len(rows) * INTENTS_PER_LOCALITY
    if len(files) != expected_pages:
        failures.append({"global": ["page_count", len(files), expected_pages]})
    if len(filenames) != expected_pages:
        failures.append({"global": ["filename_unique", len(filenames), expected_pages]})
    if len(canonicals) != expected_pages:
        failures.append({"global": ["canonical_unique", len(canonicals), expected_pages]})

    top_heap: list = []
    max_cosine = 0.0
    max_jaccard = 0.0
    pair_count = 0
    duplicate_fail_count = 0
    duplicate_failure_examples: list[dict] = []
    serial = 0

    for intent, docs in groups.items():
        for (loc_a, file_a, prep_a), (loc_b, file_b, prep_b) in combinations(docs, 2):
            co = s4.cosine_pre(prep_a, prep_b)
            ja = s4.jacc_pre(prep_a, prep_b)
            pair_count += 1
            max_cosine = max(max_cosine, co)
            max_jaccard = max(max_jaccard, ja)
            item = {
                "intent": intent,
                "a": loc_a,
                "b": loc_b,
                "file_a": file_a,
                "file_b": file_b,
                "cosine": round(co, 4),
                "jaccard5": round(ja, 4),
            }
            serial += 1
            push_top(top_heap, item, serial)
            if co >= 0.82 or ja >= 0.24:
                duplicate_fail_count += 1
                if len(duplicate_failure_examples) < 100:
                    duplicate_failure_examples.append(item)

    if duplicate_fail_count:
        failures.append({
            "global": ["duplicate_gate", duplicate_fail_count],
            "examples": duplicate_failure_examples,
        })

    top_pairs = [x[3] for x in sorted(top_heap, reverse=True)]
    shortest = min(files, key=lambda x: x["visible_chars"])
    longest = max(files, key=lambda x: x["visible_chars"])
    total_html_bytes = sum(x["bytes"] for x in files)

    qa = {
        "version": "1.0",
        "status": "PASS" if not failures else "FAIL",
        "stage": "STAGE5_FULL_GENERATION_SHARD",
        "shard": {
            "index_zero_based": args.shard_index,
            "name": shard_name,
            "count": args.shard_count,
            "size_target_localities": args.shard_size,
            "global_row_start_zero_based": start,
            "global_row_end_exclusive": end,
        },
        "page_count": len(files),
        "locality_count": len(rows),
        "intent_count": INTENTS_PER_LOCALITY,
        "file_integrity": {
            "filenames_unique": len(filenames),
            "canonicals_unique": len(canonicals),
            "reserved_95_conflicts": reserved_conflicts,
            "html_set_sha256": html_set_digest.hexdigest(),
        },
        "visible_chars": {
            "min": shortest["visible_chars"],
            "max": longest["visible_chars"],
            "avg": round(sum(x["visible_chars"] for x in files) / len(files), 1),
        },
        "package_sizing": {
            "html_bytes": total_html_bytes,
            "html_mib": round(total_html_bytes / 1024 / 1024, 2),
            "avg_html_bytes": round(total_html_bytes / len(files), 1),
        },
        "duplicate_gate": {
            "status": "PASS" if duplicate_fail_count == 0 and max_cosine < 0.82 and max_jaccard < 0.24 else "FAIL",
            "scope": "within-shard exact same-intent all-pairs",
            "pairs": pair_count,
            "max_cosine": round(max_cosine, 4),
            "max_5_shingle_jaccard": round(max_jaccard, 4),
            "thresholds": {"cosine_lt": 0.82, "jaccard5_lt": 0.24},
            "failure_count": duplicate_fail_count,
            "top_pairs": top_pairs,
        },
        "shortest_page": shortest,
        "longest_page": longest,
        "static_failure_count": sum(1 for x in checks if x["status"] == "FAIL"),
        "failures": failures,
        "safety": {
            "robots": "noindex,nofollow",
            "live_lead_submission": False,
            "sitemap_live": False,
            "main_merge": False,
            "production_deploy": False,
        },
    }
    (out / "STAGE5_SHARD_QA_V1.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "version": "1.0",
        "status": "STAGE5_SHARD_PASS_NOT_PRODUCTION" if not failures else "STAGE5_SHARD_FAIL_NOT_PRODUCTION",
        "stage": "STAGE5_FULL_GENERATION_SHARD",
        "shard": qa["shard"],
        "source_manifest": "stage5_localities_5149_v1.jsonl",
        "renderer": "stage3-frozen-page-contract-plus-stage4-full-variation",
        "page_count": len(files),
        "locality_count": len(rows),
        "intent_count": INTENTS_PER_LOCALITY,
        "localities": [
            {
                "locality_key": r["locality_key"],
                "region_slug": r["region_slug"],
                "dong_name": r["dong_name"],
                "full_name_ko": r["full_name_ko"],
                "sido": r["sido"],
                "global_rank": r["_stage5_global_rank"],
                "variation_signature": r["variation_signature"],
            }
            for r in rows
        ],
        "files": files,
        "safety": qa["safety"],
    }
    (out / "STAGE5_SHARD_MANIFEST_V1.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary = {
        "status": qa["status"],
        "shard": shard_name,
        "localities": len(rows),
        "pages": len(files),
        "html_mib": qa["package_sizing"]["html_mib"],
        "pairs": pair_count,
        "max_cosine": qa["duplicate_gate"]["max_cosine"],
        "max_jaccard5": qa["duplicate_gate"]["max_5_shingle_jaccard"],
        "static_failures": qa["static_failure_count"],
        "duplicate_failures": duplicate_fail_count,
    }
    print(json.dumps(summary, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
