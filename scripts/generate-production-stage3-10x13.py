#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 3 production dry-run V2: 10 audited localities x 13 frozen intents.

Fresh production renderer built from frozen Gold facts, not copied full-page prose.
Conversion flow:
Hero -> decision strip -> self-identification -> context -> problem cards ->
priority -> training flow -> mid CTA -> proof -> sample feedback ->
5-point decision guide -> Deep Guide -> FAQ -> related links -> consultation check.

Safety: noindex, no live lead submission, no sitemap, no main merge, no production deploy.
"""
from __future__ import annotations
import html, importlib.util, json, math, re, shutil
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"stage3-production-dryrun-10x13"
INPUT=ROOT/"stage3_localities_10_v1.json"
PHONE_LABEL="전화 010-5006-8027"
PHONE_HREF="tel:+821050068027"
SERVICE_ORDER=["elem-tutor","mid-conv","high-conv","univ-conv","jobseeker-conv","biz-business-conv","housewife-conv"]
EXAM_ORDER=["toeic","toeic-speaking","opic","ielts","duolingo","toefl"]
DECISION_SUPPORT_PATH=ROOT/"PRODUCTION_DECISION_SUPPORT_13INTENT_V1.json"
NARRATIVE_PATH=ROOT/"PRODUCTION_VARIATION_NARRATIVE_V1.json"

INTRO={
"parent-view":"학생 영어를 볼 때는 진도량보다 최근 혼자 처리되는 범위와 도움이 필요한 장면을 먼저 나눕니다.",
"learner-view":"직접 영어를 배우는 입장에서는 최근 영어가 필요했던 순간 하나를 골라 시작점을 잡습니다.",
"decision-first":"과정 이름보다 지금 가장 먼저 바꿔야 할 영어 행동 하나를 정하면 비교 기준이 단순해집니다.",
"assessment-first":"시험·수행·발표처럼 평가 장면이 있다면 그 장면에서 실제로 요구하는 행동부터 확인합니다.",
"problem-first":"최근 반복해서 막힌 장면 하나를 출발점으로 삼아 필요한 연습 범위를 좁힙니다.",
"scene-first":"영어가 실제로 필요했던 순간을 먼저 떠올리고 무엇이 됐고 어디에서 멈췄는지 나눕니다.",
"question-first":"지금 내게 필요한 영어가 무엇인지 묻고 가장 가까운 사용 장면에서 거꾸로 범위를 정합니다.",
"diagnosis-first":"현재 수준을 한 점수로 묶지 않고 이해·출력·시간·재사용처럼 행동 기준으로 나눕니다.",
"comparison-first":"비슷해 보이는 과정도 목표와 평가 방식이 다르면 진단·훈련·재점검 순서가 달라집니다.",
"goal-first":"학교·시험·취업·업무 중 이번 영어의 목적을 먼저 한 문장으로 정합니다.",
"timeline-first":"시험일·발표일·면접일처럼 날짜가 있다면 남은 시간에 바꿀 수 있는 행동부터 역산합니다.",
}
CONTEXT={
"schedule-context":"주간 일정 안에서 실제 반복 가능한 연습량을 기준으로 계획합니다. 무리한 분량보다 다음 주에도 이어갈 수 있는 루틴을 우선합니다.",
"work-life-light":"지역 특성을 임의로 만들지 않고 회의·발표·수업·일상처럼 실제 영어 사용 장면으로 범위를 좁힙니다.",
"commute-light":"지역은 검색과 위치 식별에만 사용합니다. 목표·일정·복습 가능량이 실제 수업 판단의 중심입니다.",
"daily-life-light":"최근 일상에서 영어가 필요했던 순간을 기록해 시작점으로 사용합니다. 지역명만으로 학습 성향을 가정하지 않습니다.",
"minimal-context":"지역 설명은 정확한 위치 신호까지만 사용하고 본문은 실제 학습 판단과 재확인 기준에 집중합니다.",
"nearby-choice":"같은 지역에서도 대상과 목표가 다르면 과정이 달라질 수 있습니다. 가까운 위치보다 목적에 맞는 경로를 먼저 봅니다.",
"purpose-router":"학교영어·회화·시험·취업·업무 목적을 먼저 나눠 가장 직접적인 경로부터 비교합니다.",
"school-life-light":"학생 과정은 특정 학교를 추측하지 않고 읽기·듣기·말하기·수행처럼 실제 학교 영어 행동을 기준으로 봅니다.",
}
CASE={
"three-moments":"수업 전 현재 장면을 확인하고, 수업 중 필요한 행동을 연습하며, 수업 뒤 조건을 바꿔 다시 되는지 봅니다.",
"before-after-process":"넓은 고민을 구체적인 행동으로 좁힌 뒤 설명 전과 후에 혼자 처리되는 범위를 비교합니다.",
"usage-scene":"실제 사용 장면을 재현한 뒤 질문·자료·순서를 조금씩 바꿔 같은 기능을 다시 쓸 수 있는지 봅니다.",
"single-learner":"여러 목표를 동시에 늘리지 않고 현재 결과를 가장 크게 제한하는 기능 하나를 먼저 안정시킵니다.",
"decision-tree":"학교영어·회화·시험·취업·업무 중 목적을 먼저 나누고 현재 수준과 일정에 따라 다음 경로를 선택합니다.",
}
CTA={
"goal-check":"상담이나 수업 전에 이번에 가장 먼저 바꾸고 싶은 행동 하나를 정합니다.",
"current-state":"지금 혼자 가능한 것과 반복해서 막히는 것을 한두 가지씩 나눕니다.",
"first-plan":"첫 계획은 넓게 잡지 않고 가까운 일정에 바로 실행할 행동만 정합니다.",
"route-find":"대상과 사용 목적을 먼저 고르면 회화·과외·시험 중 더 직접적인 경로를 좁힐 수 있습니다.",
"diagnosis":"과정을 정하기 어렵다면 현재 되는 것과 막히는 것을 먼저 나눕니다.",
"priority-check":"목표가 여러 개라면 가장 가까운 결과에 영향을 주는 한 가지를 먼저 정합니다.",
"weakness-check":"최근 두세 번 반복된 막힘을 찾고 새 조건에서도 같은 문제가 생기는지 확인합니다.",
}
DIAG={
"comprehension-skill":"읽거나 들을 때 어휘 부족인지 문장 구조인지 정보 처리 속도인지 원인을 나눕니다.",
"usage-goal":"실제로 말하고 쓰고 선택해야 하는 행동을 먼저 정한 뒤 필요한 지식과 표현을 역산합니다.",
"error-pattern":"정답 여부보다 같은 실수가 왜 반복되는지를 기록하고 힌트를 줄였을 때 수정되는 범위를 봅니다.",
"deadline":"남은 기간 안에 바꿀 행동과 장기적으로 쌓아야 할 기초를 분리합니다.",
"study-volume":"많이 공부하는 계획보다 실제 반복 가능한 분량과 다음 재확인 시점을 정합니다.",
"output-skill":"알고 있는 표현이 실제 말이나 글로 바로 나오지 않는다면 첫 반응과 완결성을 봅니다.",
"current-level":"처음부터 다시 배우기보다 이미 혼자 가능한 범위와 도움이 필요한 범위를 분리합니다.",
"priority":"여러 약점을 동시에 다루지 않고 결과에 가장 직접적인 한두 항목을 먼저 선택합니다.",
}
RHYTHM={
"short-analytic":["현재 범위를 확인합니다.","기준을 하나로 좁힙니다.","직접 수행합니다.","새 조건에서 다시 확인합니다.","결과를 기록합니다.","실전 조건으로 재검증합니다."],
"balanced-editorial":["먼저 혼자 가능한 범위를 확인합니다.","필요한 기준을 정리한 뒤 바로 적용합니다.","실제 문제나 장면으로 옮깁니다.","자료나 질문을 바꿔 유지되는지 봅니다.","남은 병목을 다음 기록으로 남깁니다.","실제 일정과 비슷한 조건에서 확인합니다."],
"compact-direct":["현재 상태 확인.","핵심 기준 정리.","직접 수행.","새 조건 재사용.","결과 기록.","실전 재검증."],
"calm-explanatory":["현재 가능한 범위를 차분히 확인합니다.","필요한 부분만 설명한 뒤 혼자 해보게 합니다.","익숙한 예시에서 실제 문제로 천천히 옮깁니다.","조건을 하나씩 바꿔도 같은 기준이 남는지 봅니다.","잘된 부분과 다시 볼 부분을 나눕니다.","다음 실제 일정에 가까운 조건으로 확인합니다."],
"question-led":["지금 혼자 되는 것은 무엇인가요?","꼭 필요한 기준은 무엇인가요?","실제로 하면 어디에서 멈추나요?","질문이나 자료가 달라도 다시 되나요?","다음에 다시 볼 것은 무엇인가요?","실전 조건에서도 유지할 수 있나요?"],
"example-led":["첫 예시에서 현재 범위를 기록합니다.","다음 예시에는 기준 하나만 적용합니다.","새 문제에서 직접 수행합니다.","다른 예시로 조건을 바꿉니다.","마지막 예시를 다음 계획으로 연결합니다.","실전 예시에서 제한 조건과 함께 확인합니다."],
}
GUIDES=[
"최근 일주일 안에 영어 때문에 멈췄던 순간을 하나 적어봅니다. 구체적인 장면이 있으면 필요한 기능을 빨리 찾을 수 있습니다.",
"처음부터 전체 실력을 바꾸려 하지 않고 한 가지 수행을 반복합니다. 같은 조건에서 다시 된 뒤 다음 목표를 정합니다.",
"배운 내용을 그대로 따라 하는 것과 조건이 바뀌어도 다시 쓰는 것은 다릅니다. 질문·문제·상황을 바꿔 확인합니다.",
"학습 시간을 늘리기 어렵다면 영역 수를 줄입니다. 꼭 필요한 기능을 남기고 부가 목표는 다음 단계로 미룹니다.",
"모든 내용을 처음부터 다시 보기보다 실제로 막히는 기초 요소를 먼저 복구합니다. 이미 되는 부분은 반복을 줄입니다.",
"시험 점수와 실제 말하기·쓰기 수행은 다르게 나타날 수 있습니다. 서로 다른 결과를 한 레벨로 묶지 않습니다.",
"긴 복습을 계획하기보다 짧게 다시 꺼낼 단위를 남깁니다. 일정이 흔들려도 다시 시작할 위치가 있어야 합니다.",
"상담에서는 약점을 어떻게 확인하는지, 수업 뒤 무엇을 기록하는지, 다음 점검에서 무엇을 보는지 차례로 확인합니다.",
"정답률만 보지 않고 오답 이유와 공부 순서를 확인합니다. 스스로 다시 풀거나 설명할 수 있는지도 봅니다.",
"실제로 쓸 표현을 고르고 반복합니다. 지식을 늘리는 것보다 필요한 순간에 꺼내 쓰는 속도와 완결성을 봅니다.",
"마감이 없다면 한 달 단위 수행 목표를 둡니다. 목표가 안정되면 다음 기능을 추가하며 범위를 넓힙니다.",
"마감이 있다면 남은 날짜에 맞춰 우선순위를 좁히고 시험·발표·면접과 비슷한 조건으로 연습합니다.",
"가격이나 횟수만 비교하지 않고 진단→훈련→피드백→재점검이 어떻게 이어지는지 확인합니다.",
"목표가 바뀌면 계획을 전부 버리지 않고 가장 가까운 사용 장면에 맞춰 비중을 다시 조정합니다.",
"쉬운 과제만 반복하지 않고 성공 가능한 작은 수행과 약간 어려운 수행을 번갈아 배치합니다.",
"완료하지 못한 계획을 누적하지 않습니다. 실제로 소화한 양을 기준으로 다음 계획을 줄입니다.",
"모든 문장을 번역하기보다 핵심 정보와 문장 구조를 먼저 파악합니다. 어휘 부족과 구조 이해를 따로 봅니다.",
"완벽한 문장을 만들려는 시간을 줄이고 짧은 첫 문장부터 꺼냅니다. 이후 이유와 예시를 붙입니다.",
"놓친 구간이 단어인지 연결음인지 정보 처리인지 구분합니다. 원인에 따라 반복 방식도 달라집니다.",
"여러 시험을 동시에 준비하기보다 실제로 필요한 시험을 먼저 정하고 나머지 목표는 뒤로 이동합니다.",
"한 번 성공한 문제를 그대로 반복하지 않습니다. 비슷하지만 다른 자료에서 같은 기준이 남는지 확인합니다.",
"도움을 많이 받은 성공과 혼자 다시 한 결과를 구분합니다. 필요한 힌트가 줄어드는 과정도 기록합니다.",
"가까운 일정이 끝난 뒤 유지할 장기 목표를 따로 남깁니다. 단기 대비 때문에 기초 계획이 사라지지 않게 합니다.",
"잘하는 영역은 유지 확인만 하고 반복해서 막히는 영역에 시간을 더 씁니다. 학습량보다 배분을 조정합니다.",
"교재 진도보다 다음에 실제로 해야 할 행동을 먼저 정합니다. 자료는 그 행동을 연습할 수 있는지 보고 고릅니다.",
"질문을 받았을 때 바로 답이 나오지 않으면 첫 반응, 근거, 마무리를 나눠 어느 구간이 늦는지 확인합니다.",
"읽기나 듣기에서 정답을 맞혔더라도 근거를 설명하지 못하면 새 문제에서 다시 흔들릴 수 있습니다.",
"말하기와 쓰기는 준비한 문장보다 새 조건에서 내용을 다시 구성하는 범위를 확인하는 것이 중요합니다.",
"주간 계획에는 새 학습과 재확인을 따로 배치합니다. 배운 날의 성공만으로 다음 단계로 넘어가지 않습니다.",
"상담 전에 최근 자료 하나, 가장 어려운 장면 하나, 다음 일정 하나만 정리해도 시작점을 훨씬 구체적으로 잡을 수 있습니다.",
"목표가 여러 개라면 가장 가까운 결과에 직접 연결되는 행동부터 고르고 나머지는 순서를 뒤로 보냅니다.",
"다른 사람의 공부량을 기준으로 잡지 않습니다. 현재 반복 가능한 횟수와 복습 시간을 기준으로 계획합니다.",
]

def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 if not spec or not spec.loader:raise RuntimeError(path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def visible(raw):
 raw=re.sub(r"<script[\s\S]*?</script>"," ",raw,flags=re.I)
 raw=re.sub(r"<style[\s\S]*?</style>"," ",raw,flags=re.I)
 raw=re.sub(r"<[^>]+>"," ",raw)
 return re.sub(r"\s+"," ",html.unescape(raw)).strip()
def toks(t):return re.findall(r"[가-힣A-Za-z0-9]+",t.lower())
def cosine(a,b):
 ca,cb=Counter(toks(a)),Counter(toks(b));dot=sum(ca[k]*cb.get(k,0) for k in ca)
 na=math.sqrt(sum(v*v for v in ca.values()));nb=math.sqrt(sum(v*v for v in cb.values()))
 return dot/(na*nb) if na and nb else 0.0
def jacc(a,b,n=5):
 ta,tb=toks(a),toks(b);sa={tuple(ta[i:i+n]) for i in range(max(0,len(ta)-n+1))};sb={tuple(tb[i:i+n]) for i in range(max(0,len(tb)-n+1))}
 return len(sa&sb)/len(sa|sb) if sa|sb else 0.0
def dims(sig):
 keys=["intro_pattern","section_order","local_context_mode","case_frame","cta_frame","sentence_rhythm","diagnosis_emphasis"]
 vals=sig.split("|")
 if len(vals)!=7:raise RuntimeError(sig)
 return dict(zip(keys,vals))
def seed_int(row,slot):
 return int(row["content_seed"][slot%12:slot%12+4] or row["content_seed"][:4],16)
def guide(row,slot):
 return GUIDES[(seed_int(row,slot)+slot*7)%len(GUIDES)]

def rhythm(d,slot):
 arr=RHYTHM[d["sentence_rhythm"]]
 return arr[slot%len(arr)]
def esc(x):return html.escape(str(x))
def schema(canonical,h1,desc,row,service):
 return {"@context":"https://schema.org","@graph":[
  {"@type":"EducationalOrganization","@id":"https://englishpt.kr/#organization","name":"ENGLISH PT","url":"https://englishpt.kr/englishpt.html","telephone":"+82-10-5006-8027","areaServed":{"@type":"AdministrativeArea","name":row["full_name_ko"]}},
  {"@type":"WebPage","@id":canonical+"#webpage","url":canonical,"name":h1+" | ENGLISH PT","description":desc,"inLanguage":"ko-KR"},
  {"@type":"Service","@id":canonical+"#service","name":service,"provider":{"@id":"https://englishpt.kr/#organization"},"areaServed":row["full_name_ko"],"url":canonical}
 ]}

def links(row,current,svc,ex):
 out=[]
 for intent in SERVICE_ORDER:
  if intent!=current:out.append((intent,row["dong_name"]+" "+svc.PROFILES[intent]["service_h1"]))
 for key in EXAM_ORDER:
  e=ex.EXAMS[key]
  if e["intent"]!=current:out.append((e["intent"],row["dong_name"]+" "+e["service"]))
 return ''.join(f'<a href="{row["region_slug"]}-{i}.html">{esc(label)}</a>' for i,label in out)

def decision_strip(d,family):
 if family=="service":
  vals=[("출발점",INTRO[d["intro_pattern"]].split(".")[0]),("먼저 볼 것",DIAG[d["diagnosis_emphasis"]].split(".")[0]),("연습 방식",CASE[d["case_frame"]].split(".")[0]),("다음 확인",CTA[d["cta_frame"]].split(".")[0])]
 else:
  vals=[("시험 목표",INTRO[d["intro_pattern"]].split(".")[0]),("현재 병목",DIAG[d["diagnosis_emphasis"]].split(".")[0]),("훈련 방식",CASE[d["case_frame"]].split(".")[0]),("재확인",CTA[d["cta_frame"]].split(".")[0])]
 return '<section class="decision-strip"><div class="wrap"><div class="decision-grid">'+''.join(f'<div><b>{esc(a)}</b><span>{esc(b)}</span></div>' for a,b in vals)+'</div></div></section>'

def scene_cards(titles,row,d):
 cards=[]
 for i,title in enumerate(titles[:4]):
  p1=f"'{title}' 항목에서는 {rhythm(d,i)} {guide(row,i+1)}"
  p2=[DIAG[d["diagnosis_emphasis"]],CONTEXT[d["local_context_mode"]],CASE[d["case_frame"]],CTA[d["cta_frame"]]][i%4]+" "+guide(row,i+9)
  cards.append(f'<article class="card"><b>{esc(title)}</b><p>{esc(p1)}</p><p>{esc(p2)}</p></article>')
 return ''.join(cards)

def priority_block(priority,row,d):
 items=[]
 for i,label in enumerate(priority[:4]):
  note=[guide(row,i+3),DIAG[d["diagnosis_emphasis"]],CONTEXT[d["local_context_mode"]],CASE[d["case_frame"]]][i%4]
  items.append(f'<li><b>{esc(label)}</b><span>{esc(note)}</span></li>')
 return ''.join(items)

def flow_block(steps,row,d):
 items=[]
 for i,title in enumerate(steps):
  p=f"'{title}' 단계에서는 {rhythm(d,i)} {guide(row,i+12)}"
  q=[INTRO[d["intro_pattern"]],DIAG[d["diagnosis_emphasis"]],CASE[d["case_frame"]],CTA[d["cta_frame"]]][i%4]
  items.append(f'<li><span>{i+1:02d}</span><div><b>{esc(title)}</b><p>{esc(p)}</p><p>{esc(q)}</p></div></li>')
 return ''.join(items)

def proof_block(labels,row,d):
 return ''.join(f'<li><b>{esc(x)}</b><span>{esc(guide(row,i+18)+" "+rhythm(d,i+2))}</span></li>' for i,x in enumerate(labels[:5]))

def feedback_block(titles,row,d):
 out=[]
 for i,title in enumerate(titles[:3]):
  msg=f"'{title}' 항목은 특정 성과를 약속하는 기록이 아니라 다음에 다시 확인할 행동을 남기는 예시입니다. {guide(row,i+22)}"
  out.append(f'<article class="card"><b>기록 예시 {i+1}</b><p>{esc(msg)}</p></article>')
 return ''.join(out)

def decision_guide(intent,service):
 ds=json.loads(DECISION_SUPPORT_PATH.read_text(encoding="utf-8"))["intents"][intent]
 vals=[
  ("이런 경우 잘 맞습니다",ds["fit"]),
  ("이런 경우엔 다른 선택도 비교하세요",ds["alternative"]),
  ("비용을 좌우하는 4가지",ds["cost_factors"]+" · 구체 금액은 상담에서 안내"),
  ("선생님·수업은 이렇게 비교하세요",ds["teacher_or_class_selection"]),
  ("상담 전에 준비하실 것",ds["consult_preparation"]),
 ]
 return '<section class="section decision-guide"><div class="wrap narrow"><p class="kicker">선택 기준</p><h2>'+esc(service)+' 선택 전에, 이 다섯 가지를 먼저 확인하세요</h2><div class="decision-list">'+''.join(f'<div><b>◆ {esc(a)}</b><p>{esc(b)}</p></div>' for a,b in vals)+'</div></div></section>'

def variation_story(row,d,service):
 n=json.loads(NARRATIVE_PATH.read_text(encoding="utf-8"))
 parts=[]
 parts.extend(n["intro_pattern"][d["intro_pattern"]])
 parts.append(n["local_context_mode"][d["local_context_mode"]])
 parts.append(n["case_frame"][d["case_frame"]])
 parts.append(n["sentence_rhythm"][d["sentence_rhythm"]])
 parts.append(n["diagnosis_emphasis"][d["diagnosis_emphasis"]])
 parts.append(CTA[d["cta_frame"]])
 titles=["현재를 보는 관점","수업을 고르는 관점","지역과 생활 맥락","연습 전후 비교","설명 방식","진단 초점","다음 행동"]
 return '<section class="section variation-story"><div class="wrap narrow"><p class="kicker">판단 가이드</p><h2>'+esc(service)+'를 실제 일정에 연결하는 방법</h2>'+''.join(f'<article><b>{esc(t)}</b><p>{esc(p)}</p></article>' for t,p in zip(titles,parts))+'</div></section>'

def variation_story(row,d,service):
 blocks=[
  ("이번 페이지의 판단 순서",INTRO[d["intro_pattern"]]+" "+guide(row,32)+" "+rhythm(d,0)),
  ("현재 장면을 해석하는 방식",CONTEXT[d["local_context_mode"]]+" "+guide(row,34)+" "+guide(row,35)),
  ("실수와 병목을 다시 보는 방식",DIAG[d["diagnosis_emphasis"]]+" "+guide(row,36)+" "+CASE[d["case_frame"]]),
  ("수업에서 행동으로 옮기는 방식",rhythm(d,2)+" "+guide(row,38)+" "+guide(row,39)),
  ("기록을 남기는 방식",CTA[d["cta_frame"]]+" "+guide(row,40)+" "+rhythm(d,4)),
  ("다음 조건에서 재사용하는 방식",CASE[d["case_frame"]]+" "+guide(row,42)+" "+guide(row,43)),
  ("일정이 달라졌을 때 조정하는 방식",CONTEXT[d["local_context_mode"]]+" "+guide(row,44)+" "+CTA[d["cta_frame"]]),
  ("상담 전 스스로 확인할 질문",guide(row,46)+" "+DIAG[d["diagnosis_emphasis"]]+" "+guide(row,47)),
 ]
 return '<section class="section variation-story"><div class="wrap narrow"><p class="kicker">판단 가이드</p><h2>'+esc(service)+'를 실제 일정에 연결하는 방법</h2>'+''.join(f'<article><b>{esc(t)}</b><p>{esc(p)}</p></article>' for t,p in blocks)+'</div></section>'

def deep_block(scene_titles,priority,boundary,service,row,d):
 topics=[
  (f"{scene_titles[0]}에서 시작점을 잡는 법",f"{guide(row,27)} {DIAG[d['diagnosis_emphasis']]}"),
  (f"{priority[min(1,len(priority)-1)]}의 순서를 정하는 법",f"{guide(row,29)} {CONTEXT[d['local_context_mode']]}"),
  (f"{scene_titles[-1]}을 다시 확인하는 법",f"{guide(row,31)} {CASE[d['case_frame']]}"),
  ("다른 경로와 비교할 때",f"{boundary} {CTA[d['cta_frame']]}"),
 ]
 return '<section class="section soft"><div class="wrap"><p class="kicker">더 깊게 보기</p><h2>'+esc(service)+' 선택 전에 확인할 기준</h2><div class="grid4">'+''.join(f'<article class="card"><b>{esc(t)}</b><p>{esc(p)}</p></article>' for t,p in topics)+'</div></div></section>'

def faq_block(scene_titles,priority,proof,boundary,row,d):
 qas=[
  ("무엇부터 시작하면 되나요?",f"첫 우선순위는 '{priority[0]}'입니다. {guide(row,5)}"),
  ("현재 상태는 어떻게 확인하나요?",f"{DIAG[d['diagnosis_emphasis']]} {guide(row,7)}"),
  ("수업 뒤에는 무엇을 기록하나요?",f"'{proof[0]}'을 다음 확인 기준으로 남깁니다. {guide(row,11)}"),
  ("다른 과정이나 시험이 더 맞을 수도 있나요?",f"{boundary} {guide(row,13)}"),
  ("변화는 어떻게 다시 확인하나요?",f"'{scene_titles[-1]}'처럼 실제 장면을 다시 만들고 {rhythm(d,5)} {guide(row,17)}"),
 ]
 return '<section class="section"><div class="wrap narrow"><p class="kicker">자주 묻는 질문</p><h2>선택 전에 확인할 질문</h2><div class="faq">'+''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q,a in qas)+'</div></div></section>'

def render_page(row,d,intent,family,facts,svc,ex):
 slug=row["region_slug"];dong=row["dong_name"]
 if family=="service":
  p=facts
  service=p["service_h1"];service_body=p["service_body"];question=p["intro_q"];priority=p["priority"];boundary=p["boundary"]
  cards,steps,_proofs,_feedback=svc.extract_source(ROOT/"pilot-v45-5x7"/f"seoul-seocho-naegokdong-{intent}.html")
  scene_titles=[x[0] for x in cards];proof=priority
  context_title="현재 영어를 한 수준으로 묶지 않습니다"
  context_text=f"{DIAG[d['diagnosis_emphasis']]} {guide(row,20)}"
 else:
  e=facts
  service=e["service"];service_body=e["service"];question=e["first_question"];priority=e["priority"];boundary=e["boundary"]
  scene_titles=[x[0] for x in e["scenes"]];steps=e["flow"];proof=e["proof"]
  context_title="시험 구조와 개인 병목을 따로 봅니다"
  context_text=f"{DIAG[d['diagnosis_emphasis']]} 확인 항목은 {' · '.join(e['diagnosis'])}입니다. {guide(row,20)}"

 h1=f"{dong} {service}"
 canonical=f"https://englishpt.kr/{slug}-{intent}.html"
 desc=f"{h1} 안내. 현재 상황과 우선순위, 실제 훈련, 재확인, 다른 선택 경로와 상담 전 준비 정보를 확인합니다."
 js=json.dumps(schema(canonical,h1,desc,row,service),ensure_ascii=False)
 intro1=f"{row['full_name_ko']}에서 {service_body}를 알아볼 때는 이름이나 홍보문구보다 현재 목표와 실제 장면을 먼저 확인합니다."
 intro2=f"{INTRO[d['intro_pattern']]} {CONTEXT[d['local_context_mode']]}"
 mid=f"{CTA[d['cta_frame']]} {guide(row,23)}"
 related=links(row,intent,svc,ex)

 return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(h1)} | ENGLISH PT</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="noindex,nofollow"><link rel="canonical" href="{canonical}">
<meta property="og:title" content="{esc(h1)} | ENGLISH PT"><meta property="og:url" content="{canonical}"><link rel="stylesheet" href="pilot.css">
<script type="application/ld+json">{js}</script><script defer src="pilot.js"></script></head>
<body class="theme-test" data-production-deploy="false">
<header><div class="wrap header"><a href="../englishpt.html" class="brand">ENGLISH PT</a><span>PRODUCTION DRY-RUN · noindex</span></div></header><main>
<section class="hero"><div class="wrap"><p class="eyebrow">{esc(row["jurisdiction_full"])} · ENGLISH PT</p><h1>{esc(h1)}</h1><div class="hero-actions"><a class="btn primary" href="{PHONE_HREF}">{PHONE_LABEL}</a><a class="btn ghost" href="#detail">내용 보기</a><a class="btn ghost" href="#consultation-preview">상담 신청</a></div></div></section>
{decision_strip(d,family)}
<section id="detail" class="section"><div class="wrap narrow"><p class="kicker">{'시험 목표' if family=='exam' else '지금 상황'}</p><h2>{esc(question)}</h2><p>{esc(intro1)}</p><p>{esc(intro2)}</p><p>{esc(guide(row,0))}</p></div></section>
<section class="section soft"><div class="wrap"><p class="kicker">자기상황 식별</p><h2>내 상황과 가까운 장면부터 확인합니다</h2><div class="grid4">{scene_cards(scene_titles,row,d)}</div></div></section>
{decision_guide(intent,service)}
<section class="section"><div class="wrap narrow"><p class="kicker">{'시험 맥락 이해' if family=='exam' else '학습 맥락 이해'}</p><h2>{esc(context_title)}</h2><p>{esc(context_text)}</p><p>{esc(CASE[d["case_frame"]])}</p></div></section>
{variation_story(row,d,service)}
<section class="section soft"><div class="wrap"><p class="kicker">우선순위</p><h2>{esc(INTRO[d["intro_pattern"]].split(".")[0])}에서 무엇부터 볼지 정합니다</h2><ul class="proofs">{priority_block(priority,row,d)}</ul></div></section>
<section class="section dark"><div class="wrap"><p class="kicker">수업 흐름</p><h2>설명에서 끝내지 않고 실제 행동으로 다시 확인합니다</h2><ol class="steps">{flow_block(steps,row,d)}</ol></div></section>
<section class="mid-cta"><div class="wrap"><div><p class="kicker">중간 확인</p><h2>{esc(mid)}</h2></div><div class="mid-actions"><a class="btn primary" href="#consultation-preview">상담 전 확인하기</a><a class="btn phone" href="{PHONE_HREF}">{PHONE_LABEL}</a></div></div></section>
<section class="section"><div class="wrap"><p class="kicker">판단 기준</p><h2>변화를 추상적인 표현 대신 행동으로 확인합니다</h2><ul class="proofs">{proof_block(proof,row,d)}</ul></div></section>
<section class="section soft"><div class="wrap"><p class="kicker">피드백 예시</p><h2>성과를 약속하지 않고 다음 재확인 행동을 남깁니다</h2><p>아래 문장은 특정 수강생 후기나 점수 상승 사례가 아니라 기록 형식을 보여주는 예시입니다.</p><div class="grid4">{feedback_block(scene_titles,row,d)}</div></div></section>
{faq_block(scene_titles,priority,proof,boundary,row,d)}
{deep_block(scene_titles,priority,boundary,service,row,d)}
<section class="section related"><div class="wrap"><p class="kicker">관련 과정</p><h2>{esc(dong)}에서 다른 목표도 비교해보세요</h2><div class="links">{related}</div></div></section>
<section id="consultation-preview" class="section consult"><div class="wrap narrow"><p class="kicker">상담 전 체크</p><h2>최근 자료와 가장 막힌 장면, 다음 일정을 먼저 준비하세요</h2><p>{esc(CTA[d["cta_frame"]])} {esc(guide(row,30))}</p><form id="pilotForm"><label>가장 가까운 일정<input name="deadline" placeholder="시험·발표·면접·사용 일정"></label><label>가장 막히는 장면<textarea name="difficulty" rows="3" placeholder="최근 어려웠던 문제·응답·상황"></textarea></label><button class="btn primary" type="submit">상담 신청</button><a class="btn phone" href="{PHONE_HREF}">{PHONE_LABEL}</a><p class="pilot-status" aria-live="polite"></p></form></div></section>
<section class="final"><div class="wrap"><h2>{esc(h1)}, 등록보다 현재 기준부터 확인하세요.</h2><p>{esc(guide(row,31))}</p><a class="btn light" href="{PHONE_HREF}">{PHONE_LABEL}</a></div></section>
</main><footer><div class="wrap"><strong>ENGLISH PT</strong><p>{esc(row["full_name_ko"])} · Stage 3 dry-run · production 미배포</p></div></footer></body></html>'''

def main():
 rows=json.loads(INPUT.read_text(encoding="utf-8"))["rows"]
 if len(rows)!=10 or len({r["region_slug"] for r in rows})!=10:raise RuntimeError("Stage3 needs 10 unique rows")
 if any(r["landing_eligibility"]!="ELIGIBLE_AFTER_SLUG_QA" for r in rows):raise RuntimeError("ineligible row")
 svc=load_module("service_gold",ROOT/"scripts/generate-v45-full-depth-pilot.py")
 ex=load_module("exam_gold",ROOT/"scripts/generate-v45-exam-pilot.py")
 OUT.mkdir(parents=True,exist_ok=True)
 shutil.copy2(ROOT/"pilot-v45-5x7/pilot.css",OUT/"pilot.css")
 with (OUT/"pilot.css").open("a",encoding="utf-8") as fp:
  fp.write('''\n.decision-strip{background:#fff;border-bottom:1px solid #e6e2d9}.decision-grid{display:grid;grid-template-columns:repeat(4,1fr)}.decision-grid>div{padding:20px 18px;border-right:1px solid #e6e2d9}.decision-grid>div:last-child{border-right:0}.decision-grid b{display:block;font-size:13px;margin-bottom:4px}.decision-grid span{font-size:14px;color:#53605a}.mid-cta{padding:30px 0;background:#edeae2}.mid-cta .wrap{display:flex;align-items:center;justify-content:space-between;gap:20px}.mid-cta h2{font-size:clamp(22px,3vw,32px);margin:6px 0}.mid-actions{display:flex;gap:10px;flex-wrap:wrap}.decision-guide{background:#f4f8f5}.decision-list{display:grid;gap:14px}.decision-list>div{padding:16px 18px;background:#fff;border:1px solid #dce7e0;border-radius:14px}.decision-list b{display:block;margin-bottom:6px}.decision-list p{margin:0;color:#41574d}.variation-story article{padding:16px 0;border-bottom:1px solid #e6e2d9}.variation-story article:last-child{border-bottom:0}.variation-story b{display:block;margin-bottom:6px}.variation-story p{margin:0;color:#41574d;line-height:1.8}@media(max-width:760px){.decision-grid{grid-template-columns:1fr 1fr}.decision-grid>div:nth-child(2){border-right:0}.decision-grid>div{border-bottom:1px solid #e6e2d9}.mid-cta .wrap{display:block}.mid-actions{margin-top:16px}}\n''')
 shutil.copy2(ROOT/"pilot-v45-5x7/pilot.js",OUT/"pilot.js")

 generated={};files=[]
 for row in rows:
  d=dims(row["variation_signature"])
  for intent in SERVICE_ORDER:
   p=svc.PROFILES[intent];raw=render_page(row,d,intent,"service",p,svc,ex)
   name=f"{row['region_slug']}-{intent}.html";generated[name]=raw
   files.append({"path":f"stage3-production-dryrun-10x13/{name}","family":"service","intent":intent,"h1":f"{row['dong_name']} {p['service_h1']}","canonical":f"https://englishpt.kr/{row['region_slug']}-{intent}.html","locality":row["region_slug"],"blueprint":p["blueprint"],"variation_signature":row["variation_signature"]})
  for key in EXAM_ORDER:
   e=ex.EXAMS[key];intent=e["intent"];raw=render_page(row,d,intent,"exam",e,svc,ex)
   name=f"{row['region_slug']}-{intent}.html";generated[name]=raw
   files.append({"path":f"stage3-production-dryrun-10x13/{name}","family":"exam","intent":intent,"exam":key,"h1":f"{row['dong_name']} {e['service']}","canonical":f"https://englishpt.kr/{row['region_slug']}-{intent}.html","locality":row["region_slug"],"blueprint":e["blueprint"],"variation_signature":row["variation_signature"]})

 failures=[];checks=[];lengths={};groups=defaultdict(list);byloc=defaultdict(set)
 malformed=["영어회화을","영어과외을","비즈니스영어을","문항를","질의을","응시이","근거이","근거은","제한 제한","페이지은"]
 generic=["최고의 강사진","성적 향상을 책임","지금 바로 상담 신청"]
 for m in files:byloc[m["locality"]].add(Path(m["path"]).name)
 for m in files:
  name=Path(m["path"]).name;raw=generated[name];txt=visible(raw);lengths[name]=len(txt);f=[]
  if len(re.findall(r"<h1\b",raw))!=1 or f"<h1>{esc(m['h1'])}</h1>" not in raw:f.append("h1")
  if f'rel="canonical" href="{m["canonical"]}"' not in raw:f.append("canonical")
  if 'name="robots" content="noindex,nofollow"' not in raw:f.append("noindex")
  if 'data-production-deploy="false"' not in raw:f.append("production_flag")
  if raw.count("◆ ")<5 or 'decision-strip' not in raw or 'mid-cta' not in raw or 'variation-story' not in raw:f.append("conversion_blocks")
  kickers=re.findall(r'<p class="kicker">(.*?)</p>',raw)
  expected=["자기상황 식별","선택 기준","우선순위","수업 흐름","중간 확인","판단 기준","피드백 예시","자주 묻는 질문","더 깊게 보기","관련 과정","상담 전 체크"]
  try: pp=[kickers.index(x) for x in expected]
  except ValueError: pp=[]
  if not pp or pp!=sorted(pp):f.append("conversion_flow_order")
  try:json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',raw,re.S).group(1))
  except Exception:f.append("schema")
  if any(x in txt for x in malformed):f.append("malformed_korean")
  if any(x in txt for x in generic):f.append("generic_marketing")
  if any(x in txt for x in ["place_id","official_code","content_seed","variation_pack_id"]):f.append("db_internal")
  if "-tos.html" in raw.lower():f.append("standalone_tos")
  linked=set(re.findall(r'href="([^"]+\.html)"',raw));missing=byloc[m["locality"]]-{name}-linked
  if missing:f.append("cluster_links")
  lo,hi=(5200,9000)
  if not lo<=len(txt)<=hi:f.append(f"visible_chars:{len(txt)}")
  checks.append({"file":name,"family":m["family"],"intent":m["intent"],"visible_chars":len(txt),"status":"PASS" if not f else "FAIL","failures":f})
  if f:failures.append({"file":name,"failures":f})
  groups[m["intent"]].append((m["locality"],txt))

 pairs=[];maxc=maxj=0.0
 for intent,docs in groups.items():
  for (a,ta),(b,tb) in combinations(docs,2):
   co=cosine(ta,tb);ja=jacc(ta,tb);maxc=max(maxc,co);maxj=max(maxj,ja)
   p={"intent":intent,"a":a,"b":b,"cosine":round(co,4),"jaccard5":round(ja,4)};pairs.append(p)
   if co>=0.82 or ja>=0.24:failures.append({"pair":[intent,a,b],"failures":[f"duplicate:{co:.4f}/{ja:.4f}"]})
 if len(generated)!=130:failures.append({"global":["page_count",len(generated)]})
 qa={"version":"2.0","status":"PASS" if not failures else "FAIL","stage":"STAGE3_10_LOCALITIES_X_13_INTENTS","page_count":len(generated),"locality_count":10,"intent_count":13,"visible_chars":{"min":min(lengths.values()),"max":max(lengths.values()),"avg":round(sum(lengths.values())/len(lengths),1)},"static_failures":len([x for x in failures if "file" in x or "global" in x]),"duplicate_gate":{"status":"PASS" if maxc<0.82 and maxj<0.24 else "FAIL","pairs":len(pairs),"max_cosine":round(maxc,4),"max_5_shingle_jaccard":round(maxj,4),"thresholds":{"cosine_lt":0.82,"jaccard5_lt":0.24},"top_pairs":sorted(pairs,key=lambda x:(x["jaccard5"],x["cosine"]),reverse=True)[:20]},"checks":checks,"failures":failures,"render_qa":"PENDING","safety":{"robots":"noindex,nofollow","live_lead_submission":False,"sitemap":False,"main_merge":False,"production_deploy":False}}
 (OUT/"STAGE3_10X13_QA_V1.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 if failures:
  print(json.dumps({"status":"FAIL","visible":qa["visible_chars"],"duplicate":qa["duplicate_gate"],"failures":failures[:60]},ensure_ascii=False));raise SystemExit(1)
 for name,raw in generated.items():(OUT/name).write_text(raw,encoding="utf-8")
 manifest={"version":"2.0","status":"STAGE3_130_STATIC_DUPLICATE_PASS_RENDER_PENDING_HUMAN_REVIEW_REQUIRED_NOT_PRODUCTION","stage":"STAGE3_10_LOCALITIES_X_13_INTENTS","page_count":130,"locality_count":10,"intent_count":13,"input":"stage3_localities_10_v1.json","renderer":"production-v2-intent-facts-plus-seven-axis-variation","localities":rows,"files":files,"safety":{"robots":"noindex,nofollow","live_lead_submission":False,"sitemap":False,"main_merge":False,"production_deploy":False}}
 (OUT/"STAGE3_10X13_MANIFEST_V1.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":"PASS","pages":130,"visible":qa["visible_chars"],"max_cosine":qa["duplicate_gate"]["max_cosine"],"max_jaccard5":qa["duplicate_gate"]["max_5_shingle_jaccard"]},ensure_ascii=False))

if __name__=="__main__":main()
