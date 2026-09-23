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
import html, importlib.util, json, math, re, shutil
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
 paragraphs=[]
 for key in ["seed_perspective_a","seed_perspective_b","seed_perspective_c","seed_perspective_d","voice_packs"]:
  paragraphs.extend(n[key])
 # Use only complete, independently written sentences from the audited narrative library.
 bank=[]
 seen=set()
 for para in paragraphs:
  for s in re.split(r'(?<=[.!?])\\s+',str(para).strip()):
   s=s.strip()
   if len(s)<28:continue
   if s[-1] not in ".!?":s+="."
   if s not in seen:
    seen.add(s);bank.append(s)
 if len(bank)<120:raise RuntimeError(f"stage4 guide sentence bank too small: {len(bank)}")

 def local_sentence(row,slot):
  dong=row["dong_name"];full=row["full_name_ko"];jur=row["jurisdiction_full"]
  vals=[
   f"{dong} 페이지에서는 확인되지 않은 지역 특성을 붙이지 않고 사용자가 가져온 자료와 일정으로 시작점을 정합니다.",
   f"{full}에서 과정을 비교할 때도 위치보다 목표 결과와 현재 수행, 피드백 방식이 실제 선택 기준이 됩니다.",
   f"{jur}라는 행정 범위는 위치를 구분하는 정보이고 수업의 우선순위는 최근 수행과 다음 일정으로 정합니다.",
   f"{dong} 검색으로 들어왔더라도 학교영어·회화·시험·취업·업무 중 가장 가까운 목적부터 나누는 편이 직접적입니다.",
   f"{full} 안내에서는 가까운 수업이라는 이유만으로 적합하다고 보지 않고 진단과 재확인 방식까지 함께 비교합니다.",
   f"{dong}에서 비용을 확인할 때는 한 회 금액보다 횟수·시간·피드백 범위·방문 또는 온라인 방식처럼 실제 조건을 나눠 봅니다.",
   f"{jur} 안에서도 대상과 목표가 다르면 같은 영어 수업을 그대로 적용하지 않고 필요한 수행을 먼저 좁힙니다.",
   f"{dong} 페이지의 상담 준비는 많은 자료보다 최근 막힌 장면 하나와 다음 일정 하나를 정리하는 데서 시작합니다.",
   f"{full}에서 선생님이나 수업을 비교할 때는 경력 숫자만 보지 않고 설명 뒤 혼자 다시 하게 하는지와 재점검 방식을 확인합니다.",
   f"{dong}이라는 지역명은 검색 위치를 알려주지만 실제 학습 계획은 혼자 가능한 범위와 반복되는 병목을 기준으로 조정합니다.",
   f"{jur} 기준 페이지에서도 확인되지 않은 학교·직장·통학 정보를 만들지 않고 사용자가 제공한 사실만 맥락으로 사용합니다.",
   f"{dong}에서 다른 과정을 함께 볼 때는 맞는 경우뿐 아니라 더 가벼운 학습이나 다른 시험이 나은 조건도 같이 비교합니다."
  ]
  idx=int(hashlib.sha256(f"{row['content_seed']}|{slot}|local".encode()).hexdigest()[:8],16)%len(vals)
  return vals[idx]

 def guide(row,slot):
  salt=row.get("_intent_salt","")
  key=f"{row['content_seed']}|{salt}|{slot}|stage4-guide".encode("utf-8")
  h=hashlib.sha256(key).hexdigest()
  a=int(h[:8],16)%len(bank)
  b=int(h[8:16],16)%len(bank)
  if b==a:b=(b+37)%len(bank)
  # Most slots use one independent complete sentence; selected structural slots
  # also include a safe locality-specific decision sentence.
  if slot%5==0:
   return bank[a]+" "+local_sentence(row,slot)
  if slot%7==0:
   return local_sentence(row,slot)+" "+bank[b]
  return bank[a]

 g.guide=guide
 g._DIMENSION_POOL_CACHE.clear()

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

 g=load_module("stage3_renderer",ROOT/"scripts/generate-production-stage3-10x13.py")
 patch_engine(g)
 install_stage4_guide_pool(g)
 svc=load_module("service_gold",ROOT/"scripts/generate-v45-full-depth-pilot.py")
 ex=load_module("exam_gold",ROOT/"scripts/generate-v45-exam-pilot.py")
 g.LOCALITY_LONGFORM={}
 for row in rows:
  d=g.dims(row["variation_signature"])
  g.LOCALITY_LONGFORM[row["region_slug"]]=make_longform(row,d)

 OUT.mkdir(parents=True,exist_ok=True)
 shutil.copy2(ROOT/"stage3-production-dryrun-10x13/pilot.css",OUT/"pilot.css")
 shutil.copy2(ROOT/"stage3-production-dryrun-10x13/pilot.js",OUT/"pilot.js")

 generated={}; files=[]
 for row in rows:
  d=g.dims(row["variation_signature"])
  for intent in SERVICE_ORDER:
   p=svc.PROFILES[intent]
   raw=g.render_page(row,d,intent,"service",p,svc,ex)
   raw=raw.replace("PRODUCTION DRY-RUN · noindex","PRE-PRODUCTION · noindex").replace("Stage 3 dry-run · production 미배포","Stage 4 pre-production · production 미배포")
   name=f"{row['region_slug']}-{intent}.html"; generated[name]=raw
   files.append({"path":f"stage4-preproduction-100x13/{name}","family":"service","intent":intent,"h1":f"{row['dong_name']} {p['service_h1']}","canonical":f"https://englishpt.kr/{row['region_slug']}-{intent}.html","locality":row["region_slug"],"blueprint":p["blueprint"],"variation_signature":row["variation_signature"]})
  for key in EXAM_ORDER:
   e=ex.EXAMS[key]; intent=e["intent"]
   raw=g.render_page(row,d,intent,"exam",e,svc,ex)
   raw=raw.replace("PRODUCTION DRY-RUN · noindex","PRE-PRODUCTION · noindex").replace("Stage 3 dry-run · production 미배포","Stage 4 pre-production · production 미배포")
   name=f"{row['region_slug']}-{intent}.html"; generated[name]=raw
   files.append({"path":f"stage4-preproduction-100x13/{name}","family":"exam","intent":intent,"exam":key,"h1":f"{row['dong_name']} {e['service']}","canonical":f"https://englishpt.kr/{row['region_slug']}-{intent}.html","locality":row["region_slug"],"blueprint":e["blueprint"],"variation_signature":row["variation_signature"]})

 failures=[]; checks=[]; lengths={}; sizes={}; groups=defaultdict(list); byloc=defaultdict(set)
 malformed=["영어회화을","영어과외을","비즈니스영어을","문항를","질의을","응시이","근거이","근거은","제한 제한","페이지은","'을 다음 확인 기준","'를 다음 확인 기준","합니다에서 무엇부터","습니다에서 무엇부터"]
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
  if raw.count("◆ ")<5 or 'decision-strip' not in raw or 'decision-guide' not in raw or 'mid-cta' not in raw or 'variation-story' not in raw or 'locality-longform' not in raw:f.append("conversion_blocks")
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
