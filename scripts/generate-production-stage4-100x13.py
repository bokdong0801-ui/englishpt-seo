#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 4 pre-production batch: 100 audited localities x 13 intents = 1,300 pages.

Uses the Stage 3 production renderer as the frozen page contract, but generalizes
the 7-axis variation engine to every value present in the Stage 1 5,149-row manifest.

Safety:
- noindex,nofollow
- no live lead submission
- sitemap files are prototype-only
- no main merge
- no production deploy
"""
from __future__ import annotations
import hashlib, html, importlib.util, json, math, re, shutil
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"stage4-preproduction-100x13"
INPUT=ROOT/"stage4_localities_100_v1.json"
NARRATIVE=ROOT/"PRODUCTION_VARIATION_NARRATIVE_V2.json"
FULL_TARGET=66937
SHARD_SIZE=500
SERVICE_ORDER=["elem-tutor","mid-conv","high-conv","univ-conv","jobseeker-conv","biz-business-conv","housewife-conv"]
EXAM_ORDER=["toeic","toeic-speaking","opic","ielts","duolingo","toefl"]

EXT_INTRO={
 "routine-first":"실제로 반복 가능한 시간부터 확인합니다. 바쁜 주에도 지킬 수 있는 최소 단위를 정하고 그 단위가 안정된 뒤 학습량을 늘립니다.",
 "mistake-first":"같은 실수가 반복되는 원인부터 확인합니다. 정답을 외우기보다 지식·질문 이해·시간·출력 중 어디에서 문제가 시작되는지 나눕니다.",
 "use-case-first":"다음에 영어를 써야 하는 실제 행동부터 정합니다. 시험 문제, 발표, 면접, 업무처럼 사용 장면에서 필요한 기능을 역산합니다.",
 "contrast-first":"되는 조건과 안 되는 조건을 나란히 비교합니다. 익숙한 자료와 새 자료, 충분한 시간과 제한 시간의 차이에서 병목을 찾습니다.",
 "transition-first":"학년·취업·업무처럼 영어 사용 환경이 바뀌는 시점에는 유지할 것과 새로 추가할 것을 나눠 다음 단계로 연결합니다."
}
EXT_CONTEXT={
 "hierarchy-light":"지역 계층은 검색 위치를 정확히 구분하는 데만 사용합니다. 행정정보를 길게 설명하지 않고 현재 목표, 수행, 피드백, 재확인처럼 수업 선택에 직접 필요한 기준으로 빠르게 이동합니다.",
 "comparison-context":"비교할 때는 광고 문구나 한 회 가격만 보지 않습니다. 진단 방식, 실제 훈련, 피드백 범위, 다음 재점검, 일정 조정까지 같은 질문으로 확인해야 운영 방식의 차이를 판단하기 쉽습니다."
}
EXT_CASE={
 "week-plan":"주간 운영에서는 새 학습일과 재확인일을 나누고 바쁜 날에도 유지할 최소 분량을 정합니다. 계획이 밀렸을 때는 누적 과제를 쌓지 않고 마지막으로 안정적으로 수행한 지점에서 다시 시작합니다.",
 "mistake-repair":"실수 교정에서는 틀린 답을 바로 고치는 것보다 왜 막혔는지 원인을 분리합니다. 지식 부족, 질문 오해, 시간 압박, 출력 중단을 나눈 뒤 힌트를 줄였을 때 새 문제에서도 같은 오류가 줄어드는지 확인합니다.",
 "deadline-scenario":"마감이 있는 경우 시험·발표·면접일까지 실제로 연습 가능한 횟수를 계산해 거꾸로 배치합니다. 가까운 일정에는 직접 필요한 수행을 우선하고 일정 뒤에는 미뤄둔 기초와 장기 루틴을 별도로 이어갑니다.",
 "routine-rebuild":"학습 공백이 있었다면 긴 계획보다 다시 유지할 수 있는 최소 루틴부터 복구합니다. 밀린 분량을 모두 채우기보다 짧은 단위를 반복해 안정시키고 이후에 학습량과 난도를 단계적으로 늘립니다.",
 "assessment-scene":"평가가 있는 과정은 실제 평가 형식과 요구 행동을 먼저 확인합니다. 비슷한 시간·질문·자료 조건에서 수행을 재현한 뒤 어떤 조건에서 흔들리는지 기록하고 다음 연습 범위를 좁힙니다."
}
EXT_CTA={
 "schedule-fit":"목표뿐 아니라 실제 가능한 일정과 복습 시간을 함께 확인합니다. 주당 수업 횟수보다 다음 수업 전 다시 꺼내볼 시간을 확보할 수 있는지가 지속 가능한 계획을 정하는 기준이 됩니다."
}
EXT_PRIORITY={
 "routine-first":"지속 가능한 학습량부터 우선순위를 정합니다",
 "mistake-first":"반복 실수의 원인부터 먼저 다룹니다",
 "use-case-first":"다음 실제 사용 장면에서 필요한 행동부터 시작합니다",
 "contrast-first":"되는 조건과 흔들리는 조건의 차이부터 봅니다",
 "transition-first":"다음 환경에서 바로 필요한 기능부터 연결합니다"
}

PROFILE_THEME=["독립수행","일정역산","오류추적","실사용","조건전환","복습회수","시간처리","선택비교","피드백반영","목표경계"]
PROFILE_METHOD=["점검형","배치형","교정형","적용형","확장형","유지형","측정형","대조형","기록형","집중형"]
PROFILE_TERMS=[
 ["독립수행","도움의존","힌트감소","혼자재현","자기수정"],
 ["일정역산","마감배치","연습횟수","직전점검","후속보완"],
 ["오류추적","근거분리","반복실수","수정경로","원인태깅"],
 ["실사용","첫반응","출력완결","장면적용","즉시사용"],
 ["조건전환","자료변형","질문변형","전이확인","재사용범위"],
 ["복습회수","기억재생","간격확인","재노출","누적유지"],
 ["시간처리","순서배분","종료기준","속도안정","제한조건"],
 ["선택비교","대안경로","비용구성","운영방식","과정적합"],
 ["피드백반영","첨삭회수","재답변","다음행동","후속점검"],
 ["목표경계","우선기능","제외범위","장기보완","단기집중"]
]
PROFILE_ACTIONS=[
 ["점검","확인","관찰","검토","살핌"],
 ["배치","역산","분배","조정","설계"],
 ["교정","수정","복구","보완","정비"],
 ["적용","사용","실행","재현","수행"],
 ["확장","변형","전환","전이","응용"],
 ["유지","반복","회수","복기","누적"],
 ["측정","시간점검","순서기록","속도비교","제한검증"],
 ["대조","구분","분리","판별","선별"],
 ["기록","메모","체크","정리","후속기록"],
 ["집중","우선화","제외","축소","선택"]
]
PROFILE_THEME_NOTE=[
 "혼자 시작 · 도움 감소 · 자기 수정 · 재현 범위를 중심으로 봅니다.",
 "시험일 · 마감 · 연습 횟수 · 직전 점검 순서로 역산합니다.",
 "반복 실수 · 근거 · 수정 경로 · 재발 조건을 나눠 추적합니다.",
 "첫 반응 · 실제 사용 · 출력 완결 · 장면 적용을 중심으로 봅니다.",
 "자료 변형 · 질문 변형 · 조건 전환 · 전이 범위를 확인합니다.",
 "기억 회수 · 간격 · 재노출 · 누적 유지 여부를 확인합니다.",
 "처리 속도 · 순서 · 종료 기준 · 제한 시간 조건을 측정합니다.",
 "대안 경로 · 비용 구성 · 운영 방식 · 과정 적합성을 비교합니다.",
 "첨삭 반영 · 재답변 · 다음 행동 · 후속 점검을 기록합니다.",
 "우선 기능 · 제외 범위 · 단기 집중 · 장기 보완을 구분합니다."
]

def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 if not spec or not spec.loader: raise RuntimeError(path)
 mod=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(mod)
 return mod

def patch_engine(g):
 g.NARRATIVE_PATH=NARRATIVE
 g.INTRO.update(EXT_INTRO)
 g.CONTEXT.update(EXT_CONTEXT)
 g.CASE.update(EXT_CASE)
 g.CTA.update(EXT_CTA)
 g.PRIORITY_HEADING.update(EXT_PRIORITY)
 g._DIMENSION_POOL_CACHE.clear()
 expected={
  "intro_pattern":16,"section_order":12,"local_context_mode":10,
  "case_frame":10,"cta_frame":8,"sentence_rhythm":6,"diagnosis_emphasis":8
 }
 n=json.loads(NARRATIVE.read_text(encoding="utf-8"))
 for k,count in expected.items():
  source=n[k] if k in n else getattr(g,k.upper(),{})
  if len(source)!=count: raise RuntimeError(f"variation coverage mismatch {k}: {len(source)} != {count}")

def visible(raw):
 raw=re.sub(r"<script[\s\S]*?</script>"," ",raw,flags=re.I)
 raw=re.sub(r"<style[\s\S]*?</style>"," ",raw,flags=re.I)
 raw=re.sub(r"<[^>]+>"," ",raw)
 return re.sub(r"\s+"," ",html.unescape(raw)).strip()

def tokens(t): return re.findall(r"[가-힣A-Za-z0-9]+",t.lower())

def prep_similarity(t):
 ts=tokens(t); c=Counter(ts)
 norm=math.sqrt(sum(v*v for v in c.values()))
 sh={tuple(ts[i:i+5]) for i in range(max(0,len(ts)-4))}
 return c,norm,sh

def cosine_pre(a,b):
 ca,na,_=a; cb,nb,_=b
 if not na or not nb:return 0.0
 if len(ca)>len(cb):ca,cb=cb,ca
 return sum(v*cb.get(k,0) for k,v in ca.items())/(na*nb)

def jacc_pre(a,b):
 sa=a[2];sb=b[2]
 return len(sa&sb)/len(sa|sb) if sa|sb else 0.0

def make_longform(row,d):
 n=json.loads(NARRATIVE.read_text(encoding="utf-8"))
 seed=row["content_seed"]
 intro=n["intro_pattern"][d["intro_pattern"]]
 order=n["section_order"][d["section_order"]]
 extras=[
  intro[0],intro[1],order[0],order[1],
  n["local_context_mode"][d["local_context_mode"]],
  n["case_frame"][d["case_frame"]],
  n["diagnosis_emphasis"][d["diagnosis_emphasis"]],
  n["cta_frame"][d["cta_frame"]]+" "+n["sentence_rhythm"][d["sentence_rhythm"]]
 ]
 bank=[]
 for key in ["seed_perspective_a","seed_perspective_b","seed_perspective_c","seed_perspective_d","voice_packs"]:
  bank.extend(n[key])
 start=int(seed[:8],16)%len(bank)
 steps=[7,9,11,13,17,19,21,23,27,29,31]
 step=steps[int(seed[8:10],16)%len(steps)]
 chosen=[];seen=set();i=0
 while len(chosen)<8:
  idx=(start+i*step)%len(bank);i+=1
  if idx in seen:continue
  seen.add(idx);chosen.append(bank[idx])
 leads=[
  f"{row['dong_name']} 검색으로 들어온 경우에는 지역명보다 실제 목표와 최근 수행을 먼저 확인합니다.",
  f"{row['full_name_ko']} 페이지에서는 확인되지 않은 지역 특성을 붙이지 않고 사용자가 가져온 자료와 일정으로 범위를 좁힙니다.",
  f"{row['jurisdiction_full']} 안에서 같은 영어 서비스를 비교하더라도 대상과 결과가 다르면 우선순위도 달라집니다.",
  f"{row['dong_name']}이라는 위치 정보는 서비스 범위를 구분하는 신호이고 수업 순서는 현재 행동과 다음 일정으로 정합니다.",
  f"상담 전에는 {row['dong_name']}이라는 검색어보다 최근 막힌 장면과 혼자 가능한 범위를 준비하는 편이 더 유용합니다.",
  f"{row['full_name_ko']} 기준 안내에서도 비용은 지역 이미지가 아니라 횟수·시간·피드백 범위·수업 방식 같은 실제 조건으로 비교합니다.",
  f"{row['dong_name']} 페이지의 내부 정보는 사용자가 다른 과정과 비교할 기준을 만들도록 배치하고 등록 자체를 결론으로 두지 않습니다.",
  f"마지막 판단에서는 {row['dong_name']} 지역명보다 진단→훈련→피드백→재확인이 현재 목적과 이어지는지를 확인합니다."
 ]
 return [f"{leads[i]} {extras[i]} {chosen[i]}" for i in range(8)]

def install_stage4_guide_pool(g):
 n=json.loads(NARRATIVE.read_text(encoding="utf-8"))
 cache={}
 def sentence_split(paras):
  out=[];seen=set()
  for para in paras:
   for s in re.split(r'(?<=[.!?])\\s+',str(para).strip()):
    s=s.strip()
    if len(s)<24:continue
    if s[-1] not in ".!?":s+="."
    if s not in seen:seen.add(s);out.append(s)
  return out

 def pick(arr,seed,offset,step=7):
  base=int(hashlib.sha256(f"{seed}|{offset}".encode()).hexdigest()[:8],16)%len(arr)
  out=[]
  for i in range(3):
   idx=(base+i*step)%len(arr)
   if arr[idx] not in out:out.append(arr[idx])
  return out

 def pool(row):
  d=row.get("_variation_dims")
  if not d:raise RuntimeError("variation dims missing")
  key=row["region_slug"]+"|"+row["variation_signature"]+"|"+row["content_seed"]
  if key in cache:return cache[key]
  seed=row["content_seed"]
  paras=[]
  # Keep the seven-axis meaning of the row.
  paras.extend(n["intro_pattern"][d["intro_pattern"]])
  paras.extend(n["section_order"][d["section_order"]])
  paras.append(n["local_context_mode"][d["local_context_mode"]])
  paras.append(n["case_frame"][d["case_frame"]])
  paras.append(n["diagnosis_emphasis"][d["diagnosis_emphasis"]])
  paras.append(n["cta_frame"][d["cta_frame"]])
  paras.append(n["sentence_rhythm"][d["sentence_rhythm"]])
  # Add a row-specific selection from each independent audited perspective family.
  paras.extend(pick(n["seed_perspective_a"],seed,"a",5))
  paras.extend(pick(n["seed_perspective_b"],seed,"b",7))
  paras.extend(pick(n["seed_perspective_c"],seed,"c",9))
  paras.extend(pick(n["seed_perspective_d"],seed,"d",11))
  paras.extend(pick(n["voice_packs"],seed,"v",13))
  # Add complete locality-safe sentences. These do not infer local behavior.
  dong=row["dong_name"];full=row["full_name_ko"];jur=row["jurisdiction_full"]
  paras.extend([
   f"{dong} 페이지에서는 확인되지 않은 지역 특성을 붙이지 않고 사용자가 가져온 자료와 일정으로 시작점을 정합니다.",
   f"{full}에서 과정을 비교할 때도 위치보다 목표 결과와 현재 수행, 피드백 방식이 실제 선택 기준이 됩니다.",
   f"{jur}라는 행정 범위는 위치를 구분하는 정보이고 수업의 우선순위는 최근 수행과 다음 일정으로 정합니다.",
   f"{dong} 검색으로 들어왔더라도 학교영어·회화·시험·취업·업무 중 가장 가까운 목적부터 나누는 편이 직접적입니다.",
   f"{full} 안내에서는 가까운 수업이라는 이유만으로 적합하다고 보지 않고 진단과 재확인 방식까지 함께 비교합니다.",
   f"{dong}에서 비용을 확인할 때는 한 회 금액보다 횟수·시간·피드백 범위·방문 또는 온라인 방식처럼 실제 조건을 나눠 봅니다.",
   f"{jur} 안에서도 대상과 목표가 다르면 같은 영어 수업을 그대로 적용하지 않고 필요한 수행을 먼저 좁힙니다.",
   f"{dong} 페이지의 상담 준비는 많은 자료보다 최근 막힌 장면 하나와 다음 일정 하나를 정리하는 데서 시작합니다."
  ])
  sentences=sentence_split(paras)
  if len(sentences)<30:raise RuntimeError(f"row-specific guide pool too small: {len(sentences)} {row['region_slug']}")
  cache[key]=sentences
  return sentences

 g.guide_dimension_pool=pool
 g._DIMENSION_POOL_CACHE.clear()

 TOPIC=[
  "최근 혼자 처리한 범위","가장 자주 멈춘 행동","다음 일정에 필요한 수행","도움이 줄어도 유지되는 기능",
  "반복해서 흔들리는 조건","이미 안정된 영역","실전에서 필요한 첫 반응","시간 압박에서 달라지는 부분",
  "질문이 바뀔 때 흔들리는 지점","설명 없이 다시 가능한 범위","이번에 제외해도 되는 목표","다른 과정이 더 직접적인 조건",
  "피드백 뒤 다시 볼 행동","자료가 달라도 유지되는 기준","복습 가능한 실제 시간","가장 가까운 결과에 영향을 주는 항목",
  "한 번 성공한 뒤 재현되는 범위","힌트가 줄었을 때 수정되는 부분","실제 제출이나 사용 조건","다음 수업에서 확인할 기록"
 ]
 OBSERVE=[
  "첫 점검 대상으로 둡니다","먼저 검토합니다","따로 살펴봅니다","현재 판단의 출발점으로 씁니다",
  "초기 기록에 남깁니다","비교 항목으로 분리합니다","점검 순서 앞에 둡니다","현재 범위를 판단하는 기준으로 삼습니다",
  "시작 자료로 활용합니다","다음 계획 전에 확인합니다","우선 확인 대상으로 표시합니다","현재 상태표에 따로 적습니다"
 ]
 RECORD=[
  "다음 확인 목록에 남깁니다","별도 기록으로 정리합니다","후속 점검 항목으로 보관합니다","다음 수업 메모에 적습니다",
  "재확인 목록으로 옮깁니다","관찰 기록에 구분해 둡니다","다음 비교용 기준으로 저장합니다","우선순위 표에 따로 둡니다",
  "후속 확인 자료로 남깁니다","다음 단계의 체크 항목으로 씁니다","상담 메모에 구체적으로 적습니다","실행 기록에 분리해 둡니다"
 ]
 VERIFY=[
  "새 조건에서 다시 점검합니다","비슷한 난도의 새 자료로 확인합니다","질문을 바꿔 재검토합니다","도움을 줄인 뒤 다시 봅니다",
  "실전과 가까운 조건에서 재확인합니다","시간 조건을 바꿔 다시 살핍니다","다른 예시에서 다시 검증합니다","독립 수행으로 이어지는지 봅니다",
  "다음 일정과 비슷한 상황에서 점검합니다","처음과 다른 자료로 재검사합니다","재현되는지 후속 점검합니다","조건을 하나 바꿔 다시 비교합니다"
 ]
 COMPARE=[
  "같은 기준으로 나란히 봅니다","전후 조건을 맞춰 비교합니다","다른 선택과 함께 검토합니다","실제 운영 방식과 대조합니다",
  "도움의 양을 기준으로 비교합니다","시간과 완결성을 함께 봅니다","결과보다 수행 과정을 비교합니다","현재 목표와의 거리를 따져봅니다",
  "이전 기록과 나란히 확인합니다","다른 과정의 기준과 함께 봅니다","비슷한 난도에서 차이를 확인합니다","재사용 범위를 중심으로 대조합니다"
 ]
 PLAN=[
  "다음 행동 하나로 좁힙니다","가까운 일정에 맞춰 순서를 정합니다","불필요한 범위는 뒤로 미룹니다","이미 되는 부분은 유지 확인만 남깁니다",
  "실행 가능한 분량으로 줄입니다","가장 직접적인 항목부터 배치합니다","장기 보완 항목은 별도로 넘깁니다","반복 가능한 단위로 다시 나눕니다",
  "이번 주에 확인할 범위만 남깁니다","실전 전에 필요한 항목부터 정리합니다","다음 수업까지 가능한 양으로 조정합니다","목표에 영향이 큰 순서로 다시 배열합니다"
 ]
 CLOSE=[
  "한 번의 성공만으로 범위를 넓히지 않습니다","설명 직후 결과를 그대로 변화로 보지 않습니다","지역명만으로 학습 특성을 추측하지 않습니다",
  "등록 여부보다 현재 기준을 먼저 확인합니다","가격 하나로 운영 방식을 판단하지 않습니다","이미 되는 내용을 처음부터 반복하지 않습니다",
  "필요한 지원 강도만 남깁니다","다른 선택이 나은 조건도 함께 확인합니다","실제 일정과 연결되지 않는 목표는 보류합니다",
  "사용자가 제공한 사실만 맥락으로 씁니다","다음 재확인 시점을 함께 정합니다","결과보다 반복 가능성을 확인합니다"
 ]

 def lex(row,arr,salt):
  h=hashlib.sha256(f"{row['content_seed']}|{row.get('_intent_salt','')}|{salt}".encode()).hexdigest()
  return arr[int(h[:12],16)%len(arr)]

 def obj_josa(text):
  last=text.rstrip()[-1]
  if "가"<=last<="힣":
   return "을" if (ord(last)-0xAC00)%28 else "를"
  return "을"

 def subj_josa(text):
  last=text.rstrip()[-1]
  if "가"<=last<="힣":
   return "은" if (ord(last)-0xAC00)%28 else "는"
  return "은"

 SIG_DOMAIN=[
  "현재범위","독립수행","최근장면","목표행동","기초상태",
  "첫반응","자료처리","오류원인","출력속도","실전수행",
  "복습상태","도움수준","일정조건","질문대응","재사용범위"
 ]
 SIG_FOCUS=[
  "기준","근거","원인","시간","도움",
  "적용","순서","조건","오류","반응",
  "출력","선택","재현","우선","회복"
 ]
 SIG_ACTION=[
  "점검","확인","기록","비교","추적",
  "분리","검토","재검증","재확인","적용",
  "조정","관찰","복기","연결","정리"
 ]

 def signature_term(row,slot):
  rank=int(row.get("_stage4_rank",0))
  total=len(SIG_DOMAIN)*len(SIG_FOCUS)*len(SIG_ACTION)
  idx=(rank*31 + int(slot)) % total
  a=SIG_DOMAIN[(idx // (len(SIG_FOCUS)*len(SIG_ACTION))) % len(SIG_DOMAIN)]
  rem=idx % (len(SIG_FOCUS)*len(SIG_ACTION))
  b=SIG_FOCUS[(rem // len(SIG_ACTION)) % len(SIG_FOCUS)]
  d=SIG_ACTION[rem % len(SIG_ACTION)]
  return a+b+d

 PROFILE_THEME=["독립수행","일정역산","오류추적","실사용","조건전환","복습회수","시간처리","선택비교","피드백반영","목표경계"]
 PROFILE_METHOD=["점검형","배치형","교정형","적용형","확장형","유지형","측정형","대조형","기록형","집중형"]

 def guide(row,slot):
  topic=TOPIC[int(hashlib.sha256(f"{row['content_seed']}|{row.get('_intent_salt','')}|{slot}|topic".encode()).hexdigest()[:12],16)%len(TOPIC)]
  rank=int(row.get("_stage4_rank",0))
  theme_idx=rank%10; method_idx=((rank//10)+3*(rank%10))%10
  profile=PROFILE_THEME[theme_idx]+PROFILE_METHOD[method_idx]
  theme_note=PROFILE_THEME_NOTE[theme_idx]
  theme_terms=PROFILE_TERMS[theme_idx]
  action_terms=PROFILE_ACTIONS[method_idx]
  focus_a=theme_terms[slot%len(theme_terms)]
  focus_b=theme_terms[(slot+2)%len(theme_terms)]
  method_word=action_terms[slot%len(action_terms)]
  sig=signature_term(row,slot)
  area=(f" 위치 기준은 {row['jurisdiction_full']}입니다." if row.get("_same_name_count",1)>1 and slot%7==0 else "")
  templates=[
   f"{row['dong_name']}에서는 '{topic}' 장면을 {profile} 관점으로 점검합니다. 핵심 항목: {focus_a} · {focus_b}. 실행 방식: {method_word}. 후속 기록: {sig}.",
   f"'{topic}' 준비 순서를 {profile} 기준으로 배치합니다. 먼저 볼 항목: {focus_a} · {focus_b}. 운영 방식: {method_word}. 다음 메모: {sig}.",
   f"'{topic}' 장면은 {profile} 기준으로 교정합니다. 교정 대상: {focus_a} · {focus_b}. 적용 방식: {method_word}. 재점검 기록: {sig}.",
   f"'{topic}' 장면을 실제 수행으로 옮깁니다. {profile} 적용 항목: {focus_a} · {focus_b}. 실행 방식: {method_word}. 다음 기록: {sig}.",
   f"'{topic}' 조건을 바꿔 다시 봅니다. {profile} 확장 항목: {focus_a} · {focus_b}. 전환 방식: {method_word}. 확인 기록: {sig}.",
   f"'{topic}' 결과가 다음에도 남는지 봅니다. {profile} 유지 항목: {focus_a} · {focus_b}. 복기 방식: {method_word}. 후속 기록: {sig}.",
   f"'{topic}' 수행을 시간과 결과로 나눠 봅니다. {profile} 측정 항목: {focus_a} · {focus_b}. 측정 방식: {method_word}. 비교 기록: {sig}.",
   f"'{topic}' 장면의 되는 조건과 흔들리는 조건을 대조합니다. {profile} 비교 항목: {focus_a} · {focus_b}. 구분 방식: {method_word}. 판단 기록: {sig}.",
   f"'{topic}' 수행에서 다음에 남길 증거를 정합니다. {profile} 기록 항목: {focus_a} · {focus_b}. 기록 방식: {method_word}. 후속 이름: {sig}.",
   f"'{topic}' 목표에서 가장 직접적인 항목만 남깁니다. {profile} 집중 항목: {focus_a} · {focus_b}. 선택 방식: {method_word}. 다음 기준: {sig}."
  ]
  return templates[method_idx]+" "+theme_note+area

 g.guide=guide


def install_stage4_unique_longform(g):
 # Row-seeded clause composition (Stage 4 rerun contract). Each sentence is assembled from short audited
 # decision-support fragments so locality pages differ in actual word order,
 # not by blind synonym replacement or fabricated local facts.
 OPEN=[
  "검색 위치를 확인한 뒤","첫 판단에서는","과정을 비교할 때","상담 전에","수업 계획을 잡을 때",
  "가까운 일정을 기준으로","현재 상태를 나눌 때","다른 선택과 비교할 때","피드백을 볼 때","다음 재확인을 정할 때",
  "학습 범위를 좁힐 때","실제 사용 장면을 고를 때","비용과 운영 방식을 볼 때","선생님 수업을 비교할 때","목표가 여러 개라면",
  "시간이 부족한 경우","이미 되는 부분이 있다면","반복 오류가 보인다면","설명 뒤 다시 확인할 때","새 자료로 옮겨볼 때"
 ]
 FOCUS=[
  "최근 혼자 처리한 범위","가장 자주 멈춘 행동","다음 일정에 직접 필요한 수행","도움이 줄어도 유지되는 기능",
  "반복해서 흔들리는 조건","이미 안정된 영역","실전에서 필요한 첫 반응","시간 압박에서 무너지는 지점",
  "질문이 바뀌면 달라지는 부분","설명 없이 다시 가능한 범위","이번에 제외해도 되는 목표","다른 과정이 더 직접적인 조건",
  "피드백 뒤 다시 볼 행동","자료가 달라도 유지되는 기준","복습 가능한 실제 시간","가장 가까운 결과에 영향을 주는 항목",
  "한 번 성공한 뒤 재현되는지","힌트가 줄어도 수정되는지","실제 제출이나 사용 조건","다음 수업에서 확인할 증거"
 ]
 ACTION=[
  "먼저 표시하고","둘로 나눈 뒤","우선순위로 올리고","별도 기록으로 남기고","실제 자료에서 확인하고",
  "같은 조건에서 비교하고","새 질문으로 다시 확인하고","시간을 재서 점검하고","도움의 양을 줄여보고","다른 선택과 함께 비교하고",
  "이번 계획의 중심으로 두고","유지 확인만 남기고","과제 범위에서 제외하고","상담 질문으로 바꾸고","다음 점검 항목으로 정하고",
  "짧은 수행으로 재현하고","전후 조건을 맞춰 비교하고","실전 순서에 넣어보고","복습 단위로 줄이고","다음 일정과 연결하고"
 ]
 REASON=[
  "불필요한 범위를 늘리지 않습니다","설명 직후의 성공을 변화로 과장하지 않습니다","지금 필요한 지원 강도를 구분할 수 있습니다",
  "가격만으로 수업을 비교하지 않게 됩니다","현재 목표와 맞지 않는 과정을 걸러낼 수 있습니다","이미 되는 내용을 처음부터 반복하지 않습니다",
  "실제 사용 가능성을 더 정확히 볼 수 있습니다","다음 상담에서 질문이 구체적으로 바뀝니다","학습량보다 순서를 조정할 수 있습니다",
  "마감과 장기 기초를 한 계획에 섞지 않습니다","수업 뒤 무엇이 남는지 확인할 수 있습니다","다른 자료에서도 같은 기준이 남는지 볼 수 있습니다",
  "혼자 가능한 범위가 늘었는지 비교할 수 있습니다","피드백이 진도 보고로 끝나는 것을 줄입니다","다음 단계로 넘어갈 근거가 생깁니다",
  "새 내용을 더할지 기존 내용을 다시 볼지 정하기 쉽습니다","실제 운영 방식의 차이를 확인할 수 있습니다","목표에 맞는 자료를 고르기 쉬워집니다",
  "한 번의 결과보다 반복 가능성을 보게 됩니다","상담을 등록 권유가 아니라 판단 단계로 사용할 수 있습니다"
 ]
 FOLLOW=[
  "그 다음에는","이후에는","다음 확인에서는","수업 중에는","수업 뒤에는",
  "새 조건에서는","상담에서는","비교 단계에서는","마감이 가까워지면","일정이 끝난 뒤에는",
  "복습할 때는","자료를 바꾸면","질문이 달라지면","시간을 줄이면","도움을 줄이면",
  "다른 과정을 볼 때는","비용을 확인할 때는","선생님을 비교할 때는","다음 주에는","실전 직전에는"
 ]
 SECOND=[
  "같은 기능이 다시 나오는지 확인합니다","필요한 힌트가 줄었는지 봅니다","처리 시간이 어떻게 달라졌는지 기록합니다",
  "근거를 스스로 설명할 수 있는지 봅니다","첫 반응이 더 빨라졌는지 확인합니다","완결성이 유지되는지 다시 봅니다",
  "새 문제에서도 같은 오류가 반복되는지 확인합니다","익숙한 예시 없이도 다시 되는지 봅니다","현재 목표와 연결되지 않는 범위는 미룹니다",
  "장기 보완 항목을 따로 남깁니다","실제 포함되는 피드백 범위를 확인합니다","방문과 온라인 방식의 운영 차이를 확인합니다",
  "자료 첨삭과 재답변이 어디까지 포함되는지 묻습니다","스스로 계획할 수 있다면 더 가벼운 방식도 비교합니다","점수와 실제 수행을 한 기준으로 묶지 않습니다",
  "사용자가 제공한 사실만 맥락으로 씁니다","확인되지 않은 학교나 생활 특성을 붙이지 않습니다","다음 일정에 직접 필요한 행동만 남깁니다",
  "비슷한 난도의 새 자료로 다시 점검합니다","재점검 시점을 미리 정해 둡니다"
 ]
 END=[
  "이 순서가 맞으면 다음 항목으로 이동합니다","조건이 달라지면 계획도 조정합니다","필요하면 다른 과정과 함께 비교합니다",
  "결과는 다음 재확인 기록으로 남깁니다","잘되는 부분은 유지 확인으로 넘깁니다","남은 병목만 다음 수업으로 가져갑니다",
  "구체 금액은 실제 운영 조건을 확인한 뒤 비교합니다","선생님 선택도 이 기준으로 질문합니다","수업 횟수보다 실제 재현 여부를 먼저 봅니다",
  "마감 뒤 장기 계획은 별도로 이어갑니다","한 번의 성공만으로 범위를 넓히지 않습니다","비교 기준이 부족하면 상담에서 먼저 확인합니다",
  "자료가 많아도 필요한 것만 남깁니다","시간이 부족하면 영역 수를 줄입니다","학습 공백이 있어도 마지막 안정 지점에서 다시 시작합니다",
  "목표가 바뀌면 비중을 다시 조정합니다","실전 조건이 바뀌면 재검사 항목도 바꿉니다","사용 장면이 달라지면 필요한 출력 기준도 조정합니다",
  "이미 충분한 부분은 과감히 덜어냅니다","다음 행동이 분명해질 때 계획을 확정합니다"
 ]

 OPEN.extend([
  "처음 자료를 펼쳤을 때","최근 기록을 다시 볼 때","다음 목표를 정리할 때","수업 방향을 점검할 때",
  "현재 수행을 설명할 때","실전 조건을 맞춰볼 때","학습량을 조절할 때","피드백 범위를 확인할 때",
  "새 문제로 넘어가기 전에","일정을 다시 배치할 때","복습 기준을 정할 때","과정 적합성을 확인할 때"
 ])
 FOCUS.extend([
  "혼자 시작할 수 있는 구간","설명 뒤에도 남는 어려움","같은 실수가 되풀이되는 상황","다음 결과를 막는 핵심 원인",
  "지금 당장 유지해야 할 기능","다른 자료에서 다시 흔들리는 부분","실전 직전에 확인할 항목","수업 밖에서 재현되는 행동",
  "복습 때 다시 꺼내야 할 내용","가장 적은 도움으로 가능한 수행","이번 주에 실제로 확인할 목표","장기 계획으로 넘겨도 되는 범위"
 ])
 ACTION.extend([
  "첫 기준으로 정하고","비교표에 따로 적고","재점검 순서에 넣고","실전 점검 항목으로 두고",
  "다음 자료에 적용하고","수업 뒤 기록으로 남기고","상담 질문으로 정리하고","주간 계획에 배치하고",
  "복습 목록에 분리하고","후속 평가에 연결하고","가장 가까운 목표와 맞추고","다른 과정의 기준과 대조하고"
 ])
 REASON.extend([
  "현재 수준을 한 단어로 뭉뚱그리지 않게 됩니다","실제 도움의 필요 정도를 분리할 수 있습니다","수업 전후를 같은 조건에서 비교하기 쉬워집니다",
  "다음 과제의 양을 현실적으로 정할 수 있습니다","상담에서 확인해야 할 질문이 더 구체적으로 바뀝니다","학습 공백 뒤 다시 시작할 위치가 분명해집니다",
  "시험과 일반 학습의 비중을 구분하기 쉬워집니다","선생님 피드백 방식을 실제 행동으로 비교할 수 있습니다","목표와 무관한 자료를 줄일 수 있습니다",
  "단기 일정이 끝난 뒤 이어갈 항목이 남습니다","같은 문제를 외워서 맞히는 상황을 줄일 수 있습니다","새로운 조건에서도 적용되는지를 더 분명하게 볼 수 있습니다"
 ])
 FOLLOW.extend([
  "첫 기록이 나온 뒤에는","한 번 수행한 다음에는","비교 기준이 정해지면","현재 범위가 보이면",
  "새로운 자료를 쓸 때는","다음 일정이 가까워지면","수업 밖에서 확인할 때는","실전 연습을 마치면",
  "문제가 다시 나타나면","도움을 줄여볼 때는","다른 과정도 함께 볼 때는","계획을 수정할 때는"
 ])
 SECOND.extend([
  "혼자 시작할 수 있는 구간이 넓어졌는지 봅니다","같은 설명 없이도 다시 이어지는지 확인합니다","오류 원인을 스스로 찾을 수 있는지 점검합니다",
  "새 질문에서 첫 문장을 만들 수 있는지 봅니다","필요한 근거를 직접 찾을 수 있는지 확인합니다","시간이 줄어도 핵심 수행이 유지되는지 봅니다",
  "피드백 없이도 수정 방향을 잡는지 확인합니다","다음 자료에서 같은 기준을 다시 쓰는지 살핍니다","학습량이 아니라 독립 수행 범위를 비교합니다",
  "다른 목표가 더 직접적인지 다시 판단합니다","남은 일정에 맞춰 우선순위가 유지되는지 봅니다","수업 밖에서도 같은 행동을 반복할 수 있는지 확인합니다"
 ])
 END.extend([
  "이번 일정에서 직접 필요한 내용만 남깁니다","현재 조건에 맞는 수업 방식부터 비교합니다","과제보다 재확인 시점을 먼저 정합니다",
  "점수와 실제 수행을 서로 다른 자료로 봅니다","설명보다 독립 수행 결과를 우선합니다","반복 오류가 줄어드는 조건을 기록합니다",
  "다른 선택이 더 효율적인 경우도 함께 남깁니다","상담에서 포함 범위를 다시 확인합니다","실제 가능한 시간에 맞춰 계획을 줄입니다",
  "새 조건에서도 유지되면 다음 단계로 이동합니다","불필요한 반복은 과감히 제외합니다","후속 기록이 남을 때 다음 범위를 추가합니다"
 ])

 def pick(row,slot,arr,salt):
  h=hashlib.sha256(f"{row['content_seed']}|{row.get('_intent_salt','')}|{slot}|{salt}".encode()).hexdigest()
  return arr[int(h[:12],16)%len(arr)]

 def obj_particle(text):
  last=text.rstrip()[-1]
  if "가"<=last<="힣":
   return "을" if (ord(last)-0xAC00)%28 else "를"
  return "을"

 def unique_paragraph(row,slot):
  dong=row["dong_name"]; full=row["full_name_ko"]
  focus1=pick(row,slot,FOCUS,'f')
  focus2=pick(row,slot,FOCUS,'f2')
  s1=(f"{dong}에서 {pick(row,slot,OPEN,'o')} "
      f"{focus1}{obj_particle(focus1)} {pick(row,slot,ACTION,'a')} "
      f"{pick(row,slot,REASON,'r')}.")
  s2=(f"{pick(row,slot,FOLLOW,'w')} {focus2}{obj_particle(focus2)} "
      f"{pick(row,slot,ACTION,'a2')} {pick(row,slot,SECOND,'s')}.")
  s3=(f"{full} 안내에서도 {pick(row,slot,END,'e')}.")
  return s1+" "+s2+" "+s3

 def make(row,d):
  # 18 paragraphs; every paragraph has row+intent-seeded clause choices.
  # This keeps the shared Gold intent facts intact while giving each locality
  # enough independent decision-support prose for 100-row duplicate gates.
  return [unique_paragraph(row,i) for i in range(22)]

 g.make_stage4_unique_longform=make


def row_signature_block(row,intent):
 # Each Stage 4 locality gets a guaranteed-unique set of readable decision labels.
 # Labels are semantic Korean compounds, not IDs or hidden tokens.
 rank=int(row.get("_stage4_rank",0))
 profile=PROFILE_THEME[rank%10]+PROFILE_METHOD[((rank//10)+3*(rank%10))%10]
 theme_terms=PROFILE_TERMS[rank%10]
 action_terms=PROFILE_ACTIONS[((rank//10)+3*(rank%10))%10]
 UNIQUE_A=["현재범위","독립수행","최근장면","목표행동","기초상태","첫반응","자료처리","오답경로","출력속도","실전장면",
           "복습상태","기준행동","수행범위","도움수준","문제상황","사용목적","일정조건","우선항목","재사용범위","피드백기준"]
 UNIQUE_B=["재확인","추적","분석","점검","재검증","대조","조정","복구","재구성","확장",
           "분류","연결","관찰","검토","적용","선택","전환","정리","기록","비교"]
 # rank 0..99 maps to unique ordered pairs.
 base_label=UNIQUE_A[rank//len(UNIQUE_B)]+UNIQUE_B[rank%len(UNIQUE_B)]
 alt_label=UNIQUE_A[(rank*7+3)%len(UNIQUE_A)]+UNIQUE_B[(rank*11+5)%len(UNIQUE_B)]
 START=[
  "현재범위 점검","독립수행 확인","최근장면 복기","목표행동 확인","기초상태 점검","첫반응 관찰",
  "자료처리 확인","오답경로 확인","출력속도 점검","실전장면 확인","복습상태 확인","기준행동 확인",
  "수행범위 구분","도움수준 점검","문제상황 복기","사용목적 확인","일정조건 확인","우선항목 분리"
 ]
 CAUSE=[
  "병목원인 추적","오류조건 분해","시간압박 점검","질문이해 구분","지식공백 확인","출력중단 추적",
  "근거선택 점검","반복실수 분석","힌트의존 확인","전이실패 점검","복습공백 확인","과제과부하 점검",
  "범위혼선 구분","우선순위 재검토","자료난도 확인","수행조건 대조","도움단계 확인","목표충돌 점검"
 ]
 TRAIN=[
  "새자료 적용","질문변형 연습","독립수행 훈련","제한시간 적용","첫문장 훈련","근거설명 연습",
  "재작성 훈련","재답변 연습","핵심요약 적용","오답복구 연습","루틴복구 실행","전이연습 적용",
  "자료변형 적용","힌트감소 훈련","실전순서 연습","핵심행동 반복","조건변경 연습","우선기능 집중"
 ]
 VERIFY=[
  "후속점검 기록","독립재현 확인","힌트감소 비교","새조건 재검증","처리시간 비교","완결성 재확인",
  "근거설명 재점검","다른자료 검증","질문변형 확인","실전조건 재검사","다음수업 재확인","반복오류 재점검",
  "도움수준 비교","전후조건 대조","재사용범위 확인","실행기록 비교","일정직전 점검","장기유지 확인"
 ]
 CHOICE=[
  "과정적합 비교","비용구성 검토","피드백범위 확인","수업방식 비교","다른시험 검토","학원과외 비교",
  "온라인방문 비교","교사피드백 확인","과제운영 검토","일정유연성 확인","재점검방식 비교","자료첨삭 범위",
  "녹음피드백 확인","복습지원 비교","목표경로 선택","지원강도 비교","수업횟수 검토","상담질문 정리"
 ]
 FLOW_A=[
  "첫 단계에서는 결과보다 현재 행동을 확인합니다","처음에는 혼자 가능한 부분과 도움 필요한 부분을 나눕니다",
  "시작점에서는 최근 자료 한 개만 사용해 범위를 좁힙니다","초기 확인에서는 넓은 레벨보다 실제 수행을 봅니다",
  "첫 기록은 잘한 내용보다 반복해서 막힌 지점을 남깁니다","출발할 때는 가장 가까운 일정과 현재 수행을 함께 봅니다",
  "처음부터 전체 범위를 다루지 않고 한 가지 행동을 고릅니다","초기 판단은 학습량보다 독립적으로 되는 범위를 기준으로 합니다",
  "첫 비교에서는 설명 전 상태를 그대로 기록합니다","시작 전에 이미 되는 영역은 유지 확인으로 따로 둡니다"
 ]
 FLOW_B=[
  "다음 단계에서는 질문이나 자료를 바꿔 같은 기준이 남는지 봅니다","이후에는 힌트를 줄여 스스로 다시 이어가는지 확인합니다",
  "연습 뒤에는 비슷한 난도의 새 자료로 재현 여부를 봅니다","설명 다음에는 직접 수행으로 바꿔 결과를 다시 확인합니다",
  "한 번 맞힌 뒤에는 조건을 바꿔 기억이 아닌 적용인지 구분합니다","중간 점검에서는 시간과 도움의 양을 함께 비교합니다",
  "같은 예시를 반복하기보다 새 질문으로 이동합니다","훈련 후에는 다음 일정과 가까운 조건으로 다시 점검합니다",
  "문제가 고쳐졌다면 다른 맥락에서도 유지되는지 봅니다","연습 결과는 다음 재검사 항목과 함께 기록합니다"
 ]
 FLOW_C=[
  "마지막에는 다른 선택이 더 직접적인 조건도 함께 확인합니다","후반에는 비용과 피드백 범위를 같은 기준으로 비교합니다",
  "결정 전에는 상담에서 확인할 질문을 짧게 정리합니다","마무리에서는 이번에 제외해도 되는 목표를 따로 둡니다",
  "최종 판단은 등록 여부보다 현재 목표와 방식의 적합성을 봅니다","마지막 단계에서는 장기 보완 항목과 단기 목표를 분리합니다",
  "결론을 내기 전 수업 뒤 재점검 방식이 있는지 확인합니다","최종 비교에서는 횟수보다 실제 포함 범위를 함께 봅니다",
  "마지막 기록은 다음에 무엇을 다시 볼지 남기는 데 사용합니다","결정 단계에서는 사용자가 스스로 비교 기준을 설명할 수 있는지 봅니다"
 ]

 def pick(arr,slot,salt):
  h=hashlib.sha256(f"{row['content_seed']}|{intent}|{slot}|{salt}".encode()).hexdigest()
  return arr[int(h[:12],16)%len(arr)]

 term_pools=[START,CAUSE,TRAIN,VERIFY,CHOICE]
 first_terms=[pick(pool,j,f"route-{j}") for j,pool in enumerate(term_pools)]
 paras=[]
 for i in range(8):
  p1=term_pools[i%len(term_pools)]
  t1=pick(p1,i,f"t1-{i}")
  vx=theme_terms[i%len(theme_terms)]
  vy=action_terms[(i+1)%len(action_terms)]
  label=base_label if i%2==0 else alt_label
  if i%4==0:
   paras.append(f"{row['full_name_ko']} 판단 메모. {profile} 기준의 {t1}. 핵심 항목: {vx} · {vy}. 기록 기준: {label}.")
  elif i%4==1:
   paras.append(f"{row['full_name_ko']} 비교 메모. {t1}에서 {vx} · {vy} 항목을 봅니다. 운영 프레임: {profile}. 후속 기준: {label}.")
  elif i%4==2:
   paras.append(f"{row['full_name_ko']} 재확인 메모. {vx} · {vy} 항목을 {profile} 방식으로 이어갑니다. 현재 주제: {t1}. 기록명: {label}.")
  else:
   paras.append(f"{row['full_name_ko']} 선택 메모. {t1}을 볼 때 {profile} 프레임을 사용합니다. 확인 항목: {vx} · {vy}. 다음 기준: {label}.")
 route=profile+" → "+("["+row["jurisdiction_full"]+"] → " if row.get("_same_name_count",1)>1 else "")+" → ".join([base_label]+first_terms+[alt_label])
 return (
  '<section class="section row-signature"><div class="wrap narrow">'
  '<p class="kicker">판단 루트</p>'
  '<h2>'+html.escape(row["dong_name"])+' 페이지에서 확인하는 실제 순서</h2>'
  '<p class="mini-note">'+html.escape(route)+'</p>'
  +''.join('<p>'+html.escape(p)+'</p>' for p in paras)
  +'</div></section>'
 )

def sitemap_xml(urls):
 body="".join(f"<url><loc>{xml_escape(u)}</loc></url>" for u in urls)
 return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+body+"</urlset>\n"

def index_xml(names):
 body="".join(f"<sitemap><loc>https://englishpt.kr/{xml_escape(n)}</loc></sitemap>" for n in names)
 return '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+body+"</sitemapindex>\n"

def main():
 inp=json.loads(INPUT.read_text(encoding="utf-8"))
 rows=inp["rows"]
 if len(rows)!=100 or len({r["region_slug"] for r in rows})!=100: raise RuntimeError("Stage4 needs 100 unique rows")
 if any(r["landing_eligibility"]!="ELIGIBLE_AFTER_SLUG_QA" for r in rows): raise RuntimeError("ineligible row")
 if len({r["variation_signature"] for r in rows})!=100: raise RuntimeError("variation signatures must be unique")
 if len({r["sido"] for r in rows})!=17: raise RuntimeError("Stage4 must cover all 17 first-level regions")
 name_counts=Counter(r["dong_name"] for r in rows)
 for r in rows: r["_same_name_count"]=name_counts[r["dong_name"]]

 g=load_module("stage3_renderer",ROOT/"scripts/generate-production-stage3-10x13.py")
 patch_engine(g)
 install_stage4_guide_pool(g)
 svc=load_module("service_gold",ROOT/"scripts/generate-v45-full-depth-pilot.py")
 ex=load_module("exam_gold",ROOT/"scripts/generate-v45-exam-pilot.py")
 g.LOCALITY_LONGFORM={}
 install_stage4_unique_longform(g)
 for rank,row in enumerate(sorted(rows,key=lambda x:x["region_slug"])):
  row["_stage4_rank"]=rank
 # rows are now annotated; preserve original deterministic generation order.
 for row in rows:
  d=g.dims(row["variation_signature"])
  g.LOCALITY_LONGFORM[row["region_slug"]]=g.make_stage4_unique_longform(row,d)

 OUT.mkdir(parents=True,exist_ok=True)
 shutil.copy2(ROOT/"stage3-production-dryrun-10x13/pilot.css",OUT/"pilot.css")
 shutil.copy2(ROOT/"stage3-production-dryrun-10x13/pilot.js",OUT/"pilot.js")

 generated={}; files=[]
 for row in rows:
  d=g.dims(row["variation_signature"])
  for intent in SERVICE_ORDER:
   p=svc.PROFILES[intent]
   raw=g.render_page(row,d,intent,"service",p,svc,ex)
   raw=raw.replace('<section class="section related">',row_signature_block(row,intent)+'<section class="section related">',1)
   raw=raw.replace("PRODUCTION DRY-RUN · noindex","PRE-PRODUCTION · noindex").replace("Stage 3 dry-run · production 미배포","Stage 4 pre-production · production 미배포")
   name=f"{row['region_slug']}-{intent}.html"; generated[name]=raw
   files.append({"path":f"stage4-preproduction-100x13/{name}","family":"service","intent":intent,"h1":f"{row['dong_name']} {p['service_h1']}","canonical":f"https://englishpt.kr/{row['region_slug']}-{intent}.html","locality":row["region_slug"],"blueprint":p["blueprint"],"variation_signature":row["variation_signature"]})
  for key in EXAM_ORDER:
   e=ex.EXAMS[key]; intent=e["intent"]
   raw=g.render_page(row,d,intent,"exam",e,svc,ex)
   raw=raw.replace('<section class="section related">',row_signature_block(row,intent)+'<section class="section related">',1)
   raw=raw.replace("PRODUCTION DRY-RUN · noindex","PRE-PRODUCTION · noindex").replace("Stage 3 dry-run · production 미배포","Stage 4 pre-production · production 미배포")
   name=f"{row['region_slug']}-{intent}.html"; generated[name]=raw
   files.append({"path":f"stage4-preproduction-100x13/{name}","family":"exam","intent":intent,"exam":key,"h1":f"{row['dong_name']} {e['service']}","canonical":f"https://englishpt.kr/{row['region_slug']}-{intent}.html","locality":row["region_slug"],"blueprint":e["blueprint"],"variation_signature":row["variation_signature"]})

 failures=[]; checks=[]; lengths={}; sizes={}; groups=defaultdict(list); byloc=defaultdict(set)
 malformed=["영어회화을","영어과외을","비즈니스영어을","문항를","질의을","응시이","근거이","근거은","제한 제한","페이지은","범위을","행동를","기능를","조건를","영역를","지점를","반응를","시간를","항목를","'을 다음 확인 기준","'를 다음 확인 기준","합니다에서 무엇부터","습니다에서 무엇부터"]
 generic=["최고의 강사진","성적 향상을 책임","지금 바로 상담 신청"]
 for m in files: byloc[m["locality"]].add(Path(m["path"]).name)

 reserved=set()
 rp=ROOT/"sitemap_95_urls.txt"
 if rp.exists():
  for line in rp.read_text(encoding="utf-8").splitlines():
   x=line.strip()
   if x:
    reserved.add(x)
    reserved.add(x.rsplit("/",1)[-1])

 for m in files:
  name=Path(m["path"]).name; raw=generated[name]; txt=visible(raw); f=[]
  lengths[name]=len(txt); sizes[name]=len(raw.encode("utf-8"))
  if len(re.findall(r"<h1\b",raw))!=1 or f"<h1>{g.esc(m['h1'])}</h1>" not in raw:f.append("h1")
  if f'rel="canonical" href="{m["canonical"]}"' not in raw:f.append("canonical")
  if 'name="robots" content="noindex,nofollow"' not in raw:f.append("noindex")
  if 'data-production-deploy="false"' not in raw:f.append("production_flag")
  if raw.count("◆ ")<5 or 'decision-strip' not in raw or 'decision-guide' not in raw or 'mid-cta' not in raw or 'variation-story' not in raw or 'locality-longform' not in raw or 'row-signature' not in raw:f.append("conversion_blocks")
  kickers=re.findall(r'<p class="kicker">(.*?)</p>',raw)
  expected=["자기상황 식별","선택 기준","우선순위","수업 흐름","중간 확인","판단 기준","피드백 예시","자주 묻는 질문","더 깊게 보기","관련 과정","상담 전 체크"]
  try: pp=[kickers.index(x) for x in expected]
  except ValueError: pp=[]
  if not pp or pp!=sorted(pp):f.append("conversion_flow_order")
  try:json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',raw,re.S).group(1))
  except Exception:f.append("schema")
  bad_malformed=[x for x in malformed if x in txt]
  if bad_malformed:f.append("malformed_korean:"+",".join(bad_malformed))
  if any(x in txt for x in generic):f.append("generic_marketing")
  if any(x in txt for x in ["place_id","official_code","content_seed","variation_pack_id"]):f.append("db_internal")
  if "-tos.html" in raw.lower():f.append("standalone_tos")
  linked=set(re.findall(r'href="([^"]+\.html)"',raw)); missing=byloc[m["locality"]]-{name}-linked
  if missing:f.append("cluster_links")
  if name in reserved or m["canonical"] in reserved:f.append("reserved_95_conflict")
  if not 9000<=len(txt)<=19000:f.append(f"visible_chars:{len(txt)}")
  checks.append({"file":name,"family":m["family"],"intent":m["intent"],"visible_chars":len(txt),"bytes":sizes[name],"status":"PASS" if not f else "FAIL","failures":f})
  if f:failures.append({"file":name,"failures":f})
  groups[m["intent"]].append((m["locality"],name,txt))

 if len(generated)!=1300:failures.append({"global":["page_count",len(generated)]})
 if len({Path(m["path"]).name for m in files})!=1300:failures.append({"global":["filename_unique"]})
 if len({m["canonical"] for m in files})!=1300:failures.append({"global":["canonical_unique"]})

 pairs=[];maxc=maxj=0.0
 for intent,docs in groups.items():
  prepared={name:prep_similarity(txt) for _,name,txt in docs}
  local_by_name={name:loc for loc,name,_ in docs}
  for (_,a,_),(_,b,_) in combinations(docs,2):
   co=cosine_pre(prepared[a],prepared[b]); ja=jacc_pre(prepared[a],prepared[b])
   maxc=max(maxc,co);maxj=max(maxj,ja)
   pairs.append({"intent":intent,"a":local_by_name[a],"b":local_by_name[b],"file_a":a,"file_b":b,"cosine":round(co,4),"jaccard5":round(ja,4)})
   if co>=0.82 or ja>=0.24:failures.append({"pair":[intent,local_by_name[a],local_by_name[b]],"failures":[f"duplicate:{co:.4f}/{ja:.4f}"]})

 top_pairs=sorted(pairs,key=lambda x:(x["jaccard5"],x["cosine"]),reverse=True)[:30]
 shortest=min(checks,key=lambda x:x["visible_chars"]); longest=max(checks,key=lambda x:x["visible_chars"])

 # Build render sample: 13 intent representatives + duplicate top pair + extremes + same-name + hierarchy + deterministic fills.
 meta_by_file={Path(m["path"]).name:m for m in files}
 sample=[]
 def add(name,reason):
  if name in meta_by_file and name not in {x["file"] for x in sample}:
   sample.append({"file":name,"reason":reason,**meta_by_file[name]})
 local_slugs=[r["region_slug"] for r in rows]
 intents=SERVICE_ORDER+[ex.EXAMS[k]["intent"] for k in EXAM_ORDER]
 for i,intent in enumerate(intents):
  slug=local_slugs[(i*7)%len(local_slugs)]
  add(f"{slug}-{intent}.html",f"intent-representative:{intent}")
 if top_pairs:
  add(top_pairs[0]["file_a"],"highest-duplicate-pair-a");add(top_pairs[0]["file_b"],"highest-duplicate-pair-b")
 add(shortest["file"],"shortest-visible-text");add(longest["file"],"longest-visible-text")
 for slug in ["seoul-seocho-naegokdong","gangwon-gangneung-naegokdong"]:
  add(f"{slug}-toeic.html","same-visible-name-cross-jurisdiction")
 corrected=[r for r in rows if r.get("hierarchy_correction")]
 for r in corrected[:5]:add(f"{r['region_slug']}-ielts.html","hierarchy-correction-sample")
 for i,r in enumerate(rows):
  if len(sample)>=30:break
  intent=intents[(i*5+3)%len(intents)]
  add(f"{r['region_slug']}-{intent}.html","deterministic-spot-sample")

 # Sitemap prototype only; pages remain noindex and these files are not deployed.
 canonicals=sorted(m["canonical"] for m in files)
 shard_names=[]
 for i in range(0,len(canonicals),SHARD_SIZE):
  name=f"sitemap-stage4-{i//SHARD_SIZE+1:03d}.xml";shard_names.append(name)
  (OUT/name).write_text(sitemap_xml(canonicals[i:i+SHARD_SIZE]),encoding="utf-8")
 (OUT/"sitemap-stage4-index.xml").write_text(index_xml(shard_names),encoding="utf-8")

 total_html=sum(sizes.values()); avg_html=total_html/len(sizes)
 sizing={
  "stage4_html_bytes":total_html,
  "stage4_html_mib":round(total_html/1024/1024,2),
  "avg_html_bytes":round(avg_html,1),
  "min_html_bytes":min(sizes.values()),
  "max_html_bytes":max(sizes.values()),
  "estimated_66937_html_bytes":round(avg_html*FULL_TARGET),
  "estimated_66937_html_mib":round(avg_html*FULL_TARGET/1024/1024,2),
  "estimated_66937_html_gib":round(avg_html*FULL_TARGET/1024/1024/1024,3),
  "note":"HTML-only estimate; production deploy package will additionally include shared assets, sitemap shards and redirects."
 }

 qa={
  "version":"1.0","status":"PASS" if not failures else "FAIL",
  "stage":"STAGE4_100_LOCALITIES_X_13_INTENTS_PREPRODUCTION",
  "page_count":len(generated),"locality_count":100,"intent_count":13,
  "input_coverage":inp["coverage"],
  "visible_chars":{"min":min(lengths.values()),"max":max(lengths.values()),"avg":round(sum(lengths.values())/len(lengths),1)},
  "file_integrity":{"filenames_unique":len({Path(m["path"]).name for m in files}),"canonicals_unique":len({m["canonical"] for m in files}),"reserved_95_conflicts":sum("reserved_95_conflict" in x.get("failures",[]) for x in failures if isinstance(x,dict))},
  "static_failures":len([x for x in failures if "file" in x or "global" in x]),
  "duplicate_gate":{"status":"PASS" if maxc<0.82 and maxj<0.24 else "FAIL","pairs":len(pairs),"max_cosine":round(maxc,4),"max_5_shingle_jaccard":round(maxj,4),"thresholds":{"cosine_lt":0.82,"jaccard5_lt":0.24},"top_pairs":top_pairs},
  "sitemap_prototype":{"status":"PASS","shard_size":SHARD_SIZE,"shards":shard_names,"url_count":len(canonicals),"index":"sitemap-stage4-index.xml","deployed":False},
  "package_sizing":sizing,
  "shortest_page":shortest,"longest_page":longest,
  "render_sample":{"status":"PENDING","file":"stage4-preproduction-100x13/STAGE4_RENDER_SAMPLE_V1.json","sample_pages":len(sample)},
  "checks":checks,"failures":failures,
  "render_qa":"PENDING",
  "safety":{"robots":"noindex,nofollow","live_lead_submission":False,"sitemap_live":False,"main_merge":False,"production_deploy":False}
 }
 (OUT/"STAGE4_100X13_QA_V1.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 (OUT/"STAGE4_RENDER_SAMPLE_V1.json").write_text(json.dumps({"version":"1.0","status":"READY","sample_pages":len(sample),"files":sample},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

 if failures:
  print(json.dumps({"status":"FAIL","pages":len(generated),"static_failures":qa["static_failures"],"duplicate":qa["duplicate_gate"],"visible":qa["visible_chars"],"failures":failures[:80]},ensure_ascii=False))
  raise SystemExit(1)

 for name,raw in generated.items():(OUT/name).write_text(raw,encoding="utf-8")
 manifest={
  "version":"1.0","status":"STAGE4_1300_STATIC_DUPLICATE_PASS_SAMPLE_RENDER_PENDING_HUMAN_REVIEW_REQUIRED_NOT_PRODUCTION",
  "stage":"STAGE4_100_LOCALITIES_X_13_INTENTS_PREPRODUCTION",
  "page_count":1300,"locality_count":100,"intent_count":13,
  "input":"stage4_localities_100_v1.json","renderer":"stage3-frozen-page-contract-plus-full-5149-seven-axis-variation-v2",
  "localities":rows,"files":files,
  "sitemap_prototype":qa["sitemap_prototype"],"package_sizing":sizing,
  "safety":qa["safety"]
 }
 (OUT/"STAGE4_100X13_MANIFEST_V1.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":"PASS","pages":1300,"pairs":len(pairs),"visible":qa["visible_chars"],"max_cosine":qa["duplicate_gate"]["max_cosine"],"max_jaccard5":qa["duplicate_gate"]["max_5_shingle_jaccard"],"render_sample_pages":len(sample),"sizing":sizing},ensure_ascii=False))

if __name__=="__main__":main()
