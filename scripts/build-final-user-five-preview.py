#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build five reader-first exam pages from current Stage 9 production samples."""
from __future__ import annotations
import argparse, html, re, shutil
from pathlib import Path

INTENTS = {
    "ielts": {
        "label":"IELTS","service":"아이엘츠과외",
        "hero":"목표 Band와 시험일을 확인하고, 필요한 영역부터 집중해서 준비합니다.",
        "lead":"IELTS는 네 영역을 모두 준비해야 하지만, 매번 같은 비중으로 공부할 필요는 없습니다. 최근 결과와 목표 Band를 함께 보고 지금 점수를 가장 많이 막는 영역부터 정합니다.",
        "quick":[
            ("Listening","놓치는 정보가 무엇인지 확인","문제를 많이 듣기보다 숫자·관계·핵심어처럼 자주 놓치는 정보가 무엇인지 먼저 봅니다."),
            ("Reading","정답 근거와 시간 사용을 함께 확인","맞힌 문제도 근거를 찾는 데 오래 걸렸다면 실제 시험에서는 다시 흔들릴 수 있습니다."),
            ("Writing","첨삭 후 직접 다시 써보기","Task 1·2를 쓰고 첨삭을 읽는 데서 끝내지 않고, 같은 기준으로 직접 고쳐서 다시 써봅니다."),
            ("Speaking","질문을 바꿔 다시 답하기","Part별 답변을 만든 뒤 질문 표현을 바꿔도 자신의 말로 이어갈 수 있는지 확인합니다."),
        ],
        "manage":[
            "목표 Band·시험일·최근 성적 또는 답안을 확인합니다.",
            "Listening·Reading·Writing·Speaking의 공부 비중을 정합니다.",
            "Writing은 첨삭 후 다시 쓰고, Speaking은 녹음 후 다시 답합니다.",
            "Reading·Listening은 오답 이유와 시간 사용을 함께 기록합니다.",
            "다음 수업에서 지난 약점을 짧게 확인하고 비중을 다시 조정합니다.",
        ],
        "after":[
            ("Writing","첨삭된 글과 다시 쓴 글이 남습니다."),
            ("Speaking","녹음과 반복 표현·공백에 대한 피드백이 남습니다."),
            ("Reading·Listening","오답 이유와 시간 사용 기록이 남습니다."),
            ("다음 수업","다시 확인할 한두 가지 기준을 정해 이어갑니다."),
        ],
        "one":"네 영역 중 이미 안정적인 영역은 유지하고, 특정 영역이 목표 Band를 막고 있다면 그 영역에 수업 시간을 더 배분할 수 있습니다.",
    },
    "opic": {
        "label":"OPIc","service":"오픽과외",
        "hero":"외운 답변보다 내 경험을 여러 질문에 자연스럽게 연결하는 연습을 합니다.",
        "lead":"오픽은 준비한 문장을 그대로 말하는 시험이 아닙니다. 설문과 경험 소재를 정리한 뒤 익숙한 질문에서 시작해 돌발 질문과 롤플레이까지 넓혀갑니다.",
        "quick":[
            ("설문·주제","실제로 말할 수 있는 소재부터 고르기","경험이 거의 없는 주제를 억지로 고르기보다 자신의 생활과 연결되는 소재를 먼저 정리합니다."),
            ("답변 흐름","첫 문장부터 마무리까지 틀 만들기","완성 문장을 외우기보다 시작·이유·경험·마무리처럼 답변을 이어갈 순서를 익힙니다."),
            ("돌발·롤플레이","질문이 바뀌어도 다시 구성하기","준비한 경험을 다른 질문에도 활용하고 예상하지 못한 질문에도 핵심부터 답하는 연습을 합니다."),
            ("녹음 피드백","공백·반복 표현·답변 길이 확인","자신의 답변을 녹음해 너무 자주 반복하는 표현과 멈추는 구간을 직접 확인합니다."),
        ],
        "manage":[
            "목표 등급·시험일·설문 주제를 먼저 확인합니다.",
            "자주 사용할 경험 소재를 질문별이 아니라 주제별로 정리합니다.",
            "익숙한 질문으로 답변 흐름을 만든 뒤 돌발·롤플레이로 확장합니다.",
            "답변을 녹음해 공백·반복 표현·길이를 피드백합니다.",
            "다음 수업에서는 질문을 바꿔 같은 경험을 다시 활용해봅니다.",
        ],
        "after":[
            ("경험 소재","여러 질문에 활용할 수 있는 이야기 목록이 남습니다."),
            ("답변 녹음","직접 들으며 고칠 수 있는 답변 기록이 남습니다."),
            ("표현 피드백","자주 반복하는 표현과 바꿔 쓸 문장을 정리합니다."),
            ("다음 질문","다음 수업에서 다시 말해볼 질문을 정합니다."),
        ],
        "one":"이미 잘 말하는 주제는 반복을 줄이고, 돌발 질문·롤플레이·긴 답변처럼 실제로 어려운 부분에 시간을 더 쓸 수 있습니다.",
    },
    "toeic": {
        "label":"TOEIC","service":"토익과외",
        "hero":"LC·RC를 무조건 많이 풀기보다 점수를 자주 잃는 파트부터 정리합니다.",
        "lead":"같은 점수대라도 틀리는 이유는 다릅니다. 최근 성적과 시험일을 기준으로 LC·RC를 나누고, 오답 원인과 시간 사용을 함께 봅니다.",
        "quick":[
            ("LC","왜 놓쳤는지 이유부터 확인","어휘·연음·집중력·선지 해석 중 어디에서 놓치는지 구분해야 연습도 달라집니다."),
            ("RC 문법·어휘","반복해서 틀리는 기준 정리","모든 문법을 처음부터 보기보다 최근 오답에서 자주 나오는 항목부터 정리합니다."),
            ("RC 독해","정답 근거를 찾는 속도 확인","정답만 맞히는 것이 아니라 근거를 찾는 데 얼마나 오래 걸리는지도 함께 봅니다."),
            ("시간관리","파트별로 머무는 시간을 조정","마지막 문제를 못 푸는 경우에는 실력뿐 아니라 풀이 순서와 시간 배분도 다시 정합니다."),
        ],
        "manage":[
            "목표 점수·시험일·최근 점수를 확인합니다.",
            "LC·RC를 파트별로 나눠 반복 오답을 찾습니다.",
            "오답 이유를 어휘·문법·근거·시간으로 나눠 기록합니다.",
            "수업에서는 같은 원인의 문제를 다시 풀어 바로 적용해봅니다.",
            "시험이 가까워지면 실제 시간에 맞춰 풀이 순서와 속도를 점검합니다.",
        ],
        "after":[
            ("오답 기록","왜 틀렸는지 한 줄로 정리한 기록이 남습니다."),
            ("파트별 우선순위","다음 주에 시간을 더 써야 할 파트가 분명해집니다."),
            ("시간 기록","어디에서 시간이 많이 쓰이는지 확인할 수 있습니다."),
            ("다음 문제","같은 이유로 틀리는지 다시 볼 문제를 정합니다."),
        ],
        "one":"LC가 안정적이고 RC 시간이 부족하다면 RC 비중을 높일 수 있고, 반대라면 LC의 특정 파트에 더 집중할 수 있습니다.",
    },
    "toeic-speaking": {
        "label":"TOEIC Speaking","service":"토익스피킹과외",
        "hero":"유형별 답변 순서를 익히고, 제한 시간 안에서 끝까지 말하는 연습을 합니다.",
        "lead":"내용을 알고 있어도 첫 문장을 늦게 시작하거나 답변 구조가 흔들리면 점수로 연결되기 어렵습니다. 유형별로 시작 방법과 답변 순서를 정한 뒤 실제 시간에 맞춰 반복합니다.",
        "quick":[
            ("유형 파악","질문마다 먼저 해야 할 일을 정리","모든 문제를 같은 방식으로 답하지 않고 유형별로 필요한 핵심을 구분합니다."),
            ("첫 문장","준비가 끝나면 바로 시작하는 연습","첫 문장을 오래 고민하지 않도록 자주 쓰는 시작 구조를 익힙니다."),
            ("답변 구성","핵심→이유→예시 순서로 말하기","길게 말하려고 하기보다 제한 시간 안에 답변을 완성하는 데 초점을 둡니다."),
            ("녹음·수정","답해보고 고친 뒤 다시 말하기","녹음으로 속도·공백·반복 표현을 확인하고 수정한 답변을 다시 말합니다."),
        ],
        "manage":[
            "목표 등급·시험일·최근 답변을 확인합니다.",
            "자주 흔들리는 유형부터 답변 순서를 정리합니다.",
            "준비시간과 답변시간에 맞춰 실제로 말해봅니다.",
            "녹음 후 첫 문장·구성·속도·반복 표현을 피드백합니다.",
            "수정한 내용을 같은 유형의 다른 문제에서 다시 적용합니다.",
        ],
        "after":[
            ("유형별 틀","질문을 받았을 때 바로 시작할 수 있는 답변 순서가 남습니다."),
            ("녹음","현재 속도와 공백을 직접 확인할 수 있습니다."),
            ("표현 수정","반복 표현을 줄이고 바꿔 말할 문장을 정리합니다."),
            ("시간 감각","제한 시간 안에서 답을 끝내는 기준이 생깁니다."),
        ],
        "one":"이미 안정적인 유형은 빠르게 확인하고, 첫 문장·의견 제시·시간 관리처럼 실제 점수에 영향을 주는 유형에 더 많은 시간을 배분할 수 있습니다.",
    },
    "toefl": {
        "label":"TOEFL","service":"토플과외",
        "hero":"4영역을 따로 확인하고, 읽고 들은 내용을 말하고 쓰는 통합형까지 연결합니다.",
        "lead":"TOEFL은 영역별 실력뿐 아니라 여러 정보를 정리해 답으로 만드는 과정이 중요합니다. 목표 점수와 시험일을 기준으로 4영역의 약점을 확인하고 통합형까지 이어서 연습합니다.",
        "quick":[
            ("Reading","정답 근거와 읽는 속도 확인","문제 유형별로 근거를 찾는 순서를 정하고 시간이 오래 걸리는 구간을 확인합니다."),
            ("Listening","메모할 정보와 놓치는 정보 구분","모든 내용을 적으려 하지 않고 답변에 필요한 핵심 정보를 남기는 연습을 합니다."),
            ("Speaking","메모에서 답변까지 빠르게 구성","읽고 들은 내용을 짧게 정리해 제한 시간 안에 말하는 연습을 반복합니다."),
            ("Writing","정보를 묶어 논리적으로 작성","주어진 내용을 정리하고 핵심 관계를 분명하게 써낸 뒤 첨삭 후 다시 작성합니다."),
        ],
        "manage":[
            "목표 점수·시험일·최근 영역별 결과를 확인합니다.",
            "Reading·Listening·Speaking·Writing의 공부 비중을 정합니다.",
            "통합형은 메모→내용 정리→답변까지 한 번에 연습합니다.",
            "Speaking·Writing은 구성과 시간 사용을 함께 피드백합니다.",
            "다음 수업에서는 같은 방식이 다른 문제에도 적용되는지 확인합니다.",
        ],
        "after":[
            ("영역별 기록","어느 영역에서 점수를 잃는지 구체적으로 남습니다."),
            ("메모 기준","듣고 읽은 내용 중 무엇을 남길지 기준이 생깁니다."),
            ("말하기·쓰기 피드백","구성과 시간 사용을 함께 확인할 수 있습니다."),
            ("다음 연습","통합형에서 다시 확인할 과제를 정합니다."),
        ],
        "one":"4영역을 똑같이 반복하기보다 현재 점수를 가장 많이 막는 영역과 통합형 연결 과정에 시간을 더 배분할 수 있습니다.",
    },
}

def esc(x): return html.escape(str(x),quote=True)

def extract(pattern, raw, required=True):
    m=re.search(pattern,raw,re.S|re.I)
    if not m and required: raise ValueError(pattern)
    return m.group(0) if m else ""

def body_class(raw):
    m=re.search(r'<body class="([^"]+)"',raw)
    return m.group(1) if m else "theme-test intent-test"

def render_page(raw, intent):
    d=INTENTS[intent]
    head=extract(r'<head>.*?</head>',raw)
    head=head.replace('</head>','<link rel="stylesheet" href="final-five.css"></head>')
    header=extract(r'<header.*?</header>',raw)
    breadcrumb=extract(r'<div class="breadcrumb wrap".*?</div>',raw)
    consult=extract(r'<section id="consultation-preview".*?</section>',raw)
    related=extract(r'<section class="section related">.*?</section>',raw)
    footer=extract(r'<footer>.*?</footer>',raw)
    sticky=extract(r'<div class="mobile-sticky">.*?</div>',raw)
    h1=re.search(r'<h1>(.*?)</h1>',raw,re.S).group(1)
    loc=h1.split()[0]

    quick=''.join(f'<article><b>{esc(a)}</b><h3>{esc(b)}</h3><p>{esc(c)}</p></article>' for a,b,c in d["quick"])
    manage=''.join(f'<li><span>{i:02d}</span><p>{esc(x)}</p></li>' for i,x in enumerate(d["manage"],1))
    after=''.join(f'<article><b>{esc(a)}</b><p>{esc(b)}</p></article>' for a,b in d["after"])

    faq=[
        ("수업을 시작하기 전에 무엇을 준비하면 되나요?","최근 점수나 답변, 풀었던 문제 중 하나만 있어도 충분합니다. 자료가 없다면 목표와 시험일을 기준으로 상담부터 시작할 수 있습니다."),
        ("시험일까지 시간이 얼마 남지 않아도 가능한가요?","남은 기간에 따라 새 내용을 넓힐지, 이미 아는 내용을 실제 시험에 맞게 정리할지 비중을 달리합니다."),
        ("수업 횟수와 방식은 어떻게 정하나요?","현재 수준, 목표, 시험일까지 남은 기간과 가능한 학습 시간을 함께 보고 상담 후 정합니다."),
    ]
    faq_html=''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q,a in faq)

    hero=f'''<section class="five-hero"><div class="wrap five-hero-in"><p class="eyebrow">ENGLISH PT · {esc(loc)}</p><h1>{h1}</h1><p class="hero-copy">{esc(d["hero"])}</p><div class="hero-actions"><a class="btn primary" href="#start">수업 방식 보기</a><a class="btn ghost" href="#consultation-preview">무료 PT 진단</a></div></div></section>'''
    intro=f'''<section class="section five-intro" id="start"><div class="wrap"><p class="kicker">{esc(d["label"])} 준비</p><h2>{esc(d["hero"])}</h2><p class="intro-lead">{esc(d["lead"])}</p><div class="quick-grid">{quick}</div></div></section>'''
    management=f'''<section class="section five-manage"><div class="wrap manage-final-grid"><div class="manage-final-copy"><p class="kicker">수업 관리</p><h2>수업 전부터 다음 수업까지, 이렇게 이어서 관리합니다</h2><p>무엇을 배웠는지보다 실제로 다시 할 수 있는지가 중요합니다. 매 수업마다 확인하고, 연습하고, 피드백한 내용을 다음 수업의 시작점으로 연결합니다.</p><div class="manage-note"><b>{esc(d["label"])}에서는</b><p>{esc(d["one"])}</p></div></div><ol class="manage-final-steps">{manage}</ol></div></section>'''
    lesson=f'''<section class="section five-lesson"><div class="wrap"><p class="kicker">1:1 수업</p><h2>잘하는 부분은 줄이고, 필요한 부분에 시간을 더 씁니다</h2><p class="section-lead">{esc(d["one"])}</p><div class="lesson-callout"><b>수업의 기준</b><p>설명을 오래 듣는 것보다 직접 풀고·말하고·써본 결과를 기준으로 다음 연습을 정합니다.</p></div></div></section>'''
    after_sec=f'''<section class="section five-after"><div class="wrap"><p class="kicker">수업 후 관리</p><h2>수업이 끝난 뒤에도 다음에 무엇을 할지가 남습니다</h2><div class="after-grid">{after}</div></div></section>'''
    compare=f'''<section class="section five-choice"><div class="wrap"><p class="kicker">수업 선택</p><h2>학원과 1:1은 장점이 다릅니다</h2><div class="choice-grid"><article><b>정해진 진도와 함께 공부하는 게 편하다면</b><p>여러 사람과 같은 흐름으로 공부하는 방식이 잘 맞을 수 있습니다.</p></article><article><b>특정 영역이나 시험일에 맞춰 조정이 필요하다면</b><p>이미 잘하는 부분은 줄이고 어려운 부분에 시간을 더 쓰는 1:1 방식이 잘 맞을 수 있습니다.</p></article></div></div></section>'''
    faq_sec=f'''<section class="section five-faq"><div class="wrap narrow"><p class="kicker">자주 묻는 내용</p><h2>상담 전에 많이 궁금해하는 내용입니다</h2><div class="faq">{faq_html}</div></div></section>'''
    final=f'''<section class="final"><div class="wrap"><div><h2>{esc(loc)} {esc(d["service"])}, 지금 필요한 준비부터 확인해보세요.</h2><p>목표와 시험일, 최근 어려웠던 부분만 알려주셔도 어떤 순서로 시작할지 함께 정리할 수 있습니다.</p></div><a class="btn light" href="#consultation-preview">무료 PT 진단</a></div></section>'''

    return '<!doctype html><html lang="ko">'+head+f'<body class="{body_class(raw)} five-final-preview">'+header+'<main>'+breadcrumb+hero+intro+management+lesson+after_sec+compare+faq_sec+consult+related+final+'</main>'+footer+sticky+'</body></html>'

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--source",required=True);ap.add_argument("--output",required=True)
    a=ap.parse_args();src=Path(a.source);out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    for asset in ["pilot.css","pilot.js"]:
        shutil.copy2(src/asset,out/asset)
    rows=[]
    for intent,d in INTENTS.items():
        name=f"seoul-jongno-sajikdong-{intent}.html"
        raw=(src/name).read_text(encoding="utf-8")
        rendered=render_page(raw,intent)
        (out/name).write_text(rendered,encoding="utf-8")
        rows.append((name,d["label"],d["service"]))
    css=(Path(__file__).resolve().parents[1]/"assets"/"stage9-final-five.css")
    shutil.copy2(css,out/"final-five.css")
    cards=''.join(f'<a class="preview-card" href="/{esc(n)}"><span>{esc(l)}</span><b>사직동 {esc(s)}</b><small>최종 사용자형 페이지 보기 →</small></a>' for n,l,s in rows)
    index=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>ENGLISH PT 최종 사용자형 5페이지</title><style>*{{box-sizing:border-box}}body{{margin:0;font-family:Pretendard,"Apple SD Gothic Neo",Arial,sans-serif;background:#f4f1e8;color:#152019}}.wrap{{width:min(1050px,calc(100% - 36px));margin:auto;padding:56px 0}}h1{{font-size:clamp(32px,5vw,52px);margin:0 0 12px}}p{{color:#66716b;line-height:1.7}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-top:28px}}.preview-card{{display:grid;gap:7px;padding:20px;background:#fff;border:1px solid #d6ddd8;border-radius:18px;color:inherit;text-decoration:none}}.preview-card span{{font-size:11px;font-weight:900;color:#315f4c;letter-spacing:.08em}}.preview-card b{{font-size:17px}}.preview-card small{{color:#315f4c;font-weight:800}}.note{{margin-top:20px;padding:18px;background:#fff;border:1px solid #d6ddd8;border-radius:16px}}@media(max-width:700px){{.grid{{grid-template-columns:1fr}}.wrap{{padding:36px 0}}}}</style></head><body><main class="wrap"><p>FINAL USER FLOW · 5 EXAM PAGES</p><h1>처음 방문한 사람이 읽기 쉬운 구조로 다시 설계했습니다</h1><p>IELTS·OPIc·TOEIC·TOEIC Speaking·TOEFL만 먼저 비교합니다. 아직 67,032페이지 전체에는 확장하지 않았습니다.</p><div class="note"><b>확인 순서</b><p>첫 화면 → 시험별 핵심 → 실제 관리방식 → 1:1 조정 → 수업 후 남는 것 → 상담 순서가 자연스러운지 봐주세요.</p></div><div class="grid">{cards}</div></main></body></html>'''
    (out/"index.html").write_text(index,encoding="utf-8")
    (out/"_headers").write_text("/*\n  X-Robots-Tag: noindex, nofollow\n",encoding="utf-8")
if __name__=="__main__": main()
