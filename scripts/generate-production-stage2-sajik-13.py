#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 2 production integration preview: one audited locality row x 13 frozen intents.

This adapter does not change frozen Gold copy/blueprints.
It connects the Sajikdong production locality contract to:
- V4.5 7-target full-depth Gold generator
- V4.5 6-exam full-depth Gold generator

Output remains noindex, lead-disabled, not in sitemap, and not production deployed.
"""
from __future__ import annotations
import html
import importlib.util
import json
import re
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"stage2-production-preview-sajik-13"
INPUT=ROOT/"small_deploy_candidate_sajikdong_v1.json"
PHONE_HREF="tel:+821050068027"
PHONE_LABEL="전화 010-5006-8027"

SERVICE_ORDER=["elem-tutor","mid-conv","high-conv","univ-conv","jobseeker-conv","biz-business-conv","housewife-conv"]
EXAM_ORDER=["toeic","toeic-speaking","opic","ielts","duolingo","toefl"]
DECISION_SUPPORT_PATH=ROOT/"PRODUCTION_DECISION_SUPPORT_13INTENT_V1.json"

# Frozen production-locality variation intro pattern -> frozen Gold locality frame.
# This is an adapter only; no Gold copy is edited.
FRAME_BY_INTRO={
 "problem-first":"scene","scene-first":"scene","parent-view":"scene","learner-view":"scene",
 "timeline-first":"deadline","routine-first":"deadline","assessment-first":"deadline",
 "diagnosis-first":"error","mistake-first":"error",
 "goal-first":"use","question-first":"use","use-case-first":"use",
 "decision-first":"reuse","comparison-first":"reuse","contrast-first":"reuse","transition-first":"reuse",
}
SOURCE_BY_FRAME={
 "scene":"seoul-seocho-naegokdong",
 "deadline":"gangwon-gangneung-naegokdong",
 "error":"gangwon-gangneung-gangnamdong",
 "use":"sejong-goundong",
 "reuse":"busan-haeundae-jungdong",
}

def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 if not spec or not spec.loader: raise RuntimeError(f"cannot load {path}")
 mod=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(mod)
 return mod

def visible(raw):
 raw=re.sub(r"<script[\s\S]*?</script>"," ",raw,flags=re.I)
 raw=re.sub(r"<style[\s\S]*?</style>"," ",raw,flags=re.I)
 raw=re.sub(r"<[^>]+>"," ",raw)
 return re.sub(r"\s+"," ",html.unescape(raw)).strip()

def signature_parts(sig):
 keys=["intro_pattern","section_order","local_context_mode","case_frame","cta_frame","sentence_rhythm","diagnosis_emphasis"]
 vals=sig.split("|")
 if len(vals)!=len(keys): raise RuntimeError(f"bad variation signature: {sig}")
 return dict(zip(keys,vals))

def unified_links(slug,current,service_profiles,exam_map):
 items=[]
 for intent in SERVICE_ORDER:
  if intent==current: continue
  p=service_profiles[intent]
  items.append(f'<a href="{slug}-{intent}.html">{html.escape("사직동 "+p["service_h1"])}</a>')
 for key in EXAM_ORDER:
  e=exam_map[key]; intent=e["intent"]
  if intent==current: continue
  items.append(f'<a href="{slug}-{intent}.html">{html.escape("사직동 "+e["service"])}</a>')
 return "".join(items)

def postprocess(raw,slug,current,service_profiles,exam_map):
 # Normalize shared assets into the Stage 2 folder.
 raw=raw.replace('../pilot-v45-5x7/pilot.css','pilot.css').replace('../pilot-v45-5x7/pilot.js','pilot.js')
 family="service" if current in service_profiles else "exam"
 if family=="service":
  strip=[("현재","막힌 순간"),("원인","원인 분리"),("훈련","행동 연습"),("재확인","새 조건")]
 else:
  strip=[("시험 목표","제출 목적·시험일·목표 결과"),("현재 병목","영역·오답원인·시간을 분리"),("훈련","실제 문항·응답으로 재연습"),("다음 확인","새 문제·실전 조건에서 재검증")]
 strip_html='<section class="decision-strip" aria-label="빠른 판단 요약"><div class="wrap"><div class="decision-grid">'+''.join('<div><b>'+html.escape(a)+'</b><span>'+html.escape(b)+'</span></div>' for a,b in strip)+'</div></div></section>'
 ds_all=json.loads(DECISION_SUPPORT_PATH.read_text(encoding="utf-8"))["intents"]
 ds=ds_all[current]
 decision_items=[
  ("이런 경우 잘 맞습니다",ds["fit"]),
  ("이런 경우엔 다른 선택도 비교하세요",ds["alternative"]),
  ("비용을 좌우하는 4가지",ds["cost_factors"]+" · 구체 금액은 상담에서 안내"),
  ("선생님·수업은 이렇게 비교하세요",ds["teacher_or_class_selection"]),
  ("상담 전에 준비하실 것",ds["consult_preparation"])
 ]
 h1_match=re.search(r"<h1>(.*?)</h1>",raw,re.S)
 page_title=re.sub(r"<[^>]+>"," ",h1_match.group(1)).strip() if h1_match else "이 과정"
 decision_html='<section class="section decision-guide"><div class="wrap narrow"><p class="kicker">선택 기준</p><h2>'+html.escape(page_title)+' 선택 전에, 이 다섯 가지를 먼저 확인하세요</h2><div class="decision-list">'+''.join('<div><b>◆ '+html.escape(a)+'</b><p>'+html.escape(b)+'</p></div>' for a,b in decision_items)+'</div></div></section>'
 hero_end=re.search(r'(</section>)(?=\s*<section id="detail")',raw)
 if not hero_end: raise RuntimeError(f"hero boundary not found for {current}")
 raw=raw[:hero_end.end()]+strip_html+raw[hero_end.end():]
 # Preview copy: eliminate pilot-only language while retaining noindex safety.
 raw=raw.replace('V4.5 FULL-DEPTH PILOT · noindex','V4.5 PRODUCTION PREVIEW · noindex')
 raw=raw.replace('V4.5 EXAM FULL-DEPTH PILOT · noindex','V4.5 EXAM PRODUCTION PREVIEW · noindex')
 raw=raw.replace('현재 페이지는 5×7 소규모 검수용이라 폼의 실제 전송은 비활성화되어 있습니다.','현재 페이지는 배포 전 production preview라 폼의 실제 전송은 비활성화되어 있습니다.')
 raw=raw.replace('Full-depth 검수용 페이지 · production 미배포','Preview · noindex · 미배포')
 raw=raw.replace('시험형 Full-depth 검수용 · production 미배포','시험 Preview · noindex · 미배포')
 raw=raw.replace('현재 페이지는 배포 전 production preview라 폼의 실제 전송은 비활성화되어 있습니다. 전화 상담은 아래 번호로 바로 연결할 수 있습니다.','검수용 페이지라 폼 전송은 꺼져 있습니다. 전화 상담은 아래 번호로 연결됩니다.')
 raw=raw.replace('이 검수용 상담 폼 전송은 꺼져 있습니다. 최근 문제나 답변에서 가장 답답했던 장면과 다음 응시일을 정리한 뒤 전화 상담으로 연결할 수 있습니다.','검수용 폼은 전송되지 않습니다. 최근 병목과 다음 응시일을 정리해 전화 상담에서 확인할 수 있습니다.')
 raw=raw.replace('파일럿 폼','검수용 폼').replace('파일럿의 상담 폼','검수용 상담 폼').replace('이 파일럿은','이 배포 전 검수 페이지는').replace('이 파일럿','이 배포 전 검수 페이지')
 # EnglishUp benchmark reinterpretation: one compact CTA after value/decision proof.
 mid_copy="최근 장면과 다음 일정으로 우선순위를 확인하세요." if family=="service" else "최근 병목과 다음 응시일로 우선순위를 확인하세요."
 mid='<section class="mid-cta"><div class="wrap"><div><p class="kicker">다음 단계</p><h2>'+html.escape(mid_copy)+'</h2></div><div class="mid-actions"><a class="btn primary" href="#consultation-preview">상담 전 확인하기</a><a class="btn phone" href="'+PHONE_HREF+'">'+PHONE_LABEL+'</a></div></div></section>'
 # Remove the late generic Fit/Other Path block. The concrete choice guide replaces it near the top.
 fit_pattern=r'<section class="section"><div class="wrap narrow"><p class="kicker">(과정 선택|시험 선택)</p>[\\s\\S]*?</section>'
 raw,nfit=re.subn(fit_pattern,"",raw,count=1)
 if nfit!=1: raise RuntimeError(f"fit/decision section not found for {current}")
 # Hero -> quick summary -> self-identification -> concrete decision support.
 detail_start=raw.find('<section id="detail"')
 if detail_start<0: raise RuntimeError(f"detail section not found for {current}")
 first_end=raw.find("</section>",detail_start)
 second_start=raw.find("<section",first_end+10)
 second_end=raw.find("</section>",second_start)
 if second_start<0 or second_end<0: raise RuntimeError(f"self-identification section boundary not found for {current}")
 raw=raw[:second_end+10]+decision_html+raw[second_end+10:]
 # Mid CTA after value has been established, immediately before feedback proof.
 marker='<section class="section soft"><div class="wrap"><p class="kicker">피드백 예시</p>'
 pos=raw.find(marker)
 if pos<0: raise RuntimeError(f"feedback boundary not found for {current}")
 raw=raw[:pos]+mid+raw[pos:]
 # Requested flow: FAQ -> Deep Guide -> internal links -> consultation pre-check.
 deep_faq=r'(<section[^>]*>[\\s\\S]*?<p class="kicker">더 깊게 보기</p>[\\s\\S]*?</section>)\\s*(<section[^>]*>[\\s\\S]*?<p class="kicker">자주 묻는 질문</p>[\\s\\S]*?</section>)'
 raw,nswap=re.subn(deep_faq,lambda m:m.group(2)+m.group(1),raw,count=1)
 if nswap!=1: raise RuntimeError(f"FAQ/Deep Guide order not found for {current}")
 # Connect both frozen families: every page links to the other 12 Sajikdong intent pages.
 links=unified_links(slug,current,service_profiles,exam_map)
 raw,n=re.subn(r'(<div class="links">)[\\s\\S]*?(</div>)',lambda m:m.group(1)+links+m.group(2),raw,count=1)
 if n!=1: raise RuntimeError(f"related-links block not found for {current}")
 return raw

def main():
 row=json.loads(INPUT.read_text(encoding="utf-8"))["locality"]
 if row["region_slug"]!="seoul-jongno-sajikdong": raise RuntimeError("Stage 2 input must be audited Sajikdong row")
 if row["landing_eligibility"]!="ELIGIBLE_AFTER_SLUG_QA": raise RuntimeError("Sajikdong is not eligible")
 dims=signature_parts(row["variation_signature"])
 frame=FRAME_BY_INTRO.get(dims["intro_pattern"])
 if not frame: raise RuntimeError(f"unmapped intro pattern {dims['intro_pattern']}")
 source_slug=SOURCE_BY_FRAME[frame]

 svc=load_module("v45_service_gold",ROOT/"scripts/generate-v45-full-depth-pilot.py")
 ex=load_module("v45_exam_gold",ROOT/"scripts/generate-v45-exam-pilot.py")

 loc={"full_name":row["full_name_ko"],"jurisdiction":row["jurisdiction_full"],"dong":row["dong_name"],"variation":frame}
 slug=row["region_slug"]
 OUT.mkdir(parents=True,exist_ok=True)
 shutil.copy2(ROOT/"pilot-v45-5x7/pilot.css",OUT/"pilot.css")
 css_extra='''\n.decision-strip{background:#fff;border-bottom:1px solid #e6e2d9}.decision-grid{display:grid;grid-template-columns:repeat(4,1fr)}.decision-grid>div{padding:20px 18px;border-right:1px solid #e6e2d9}.decision-grid>div:last-child{border-right:0}.decision-grid b{display:block;font-size:13px;margin-bottom:4px}.decision-grid span{font-size:14px;color:#53605a}.mid-cta{padding:30px 0;background:#edeae2}.mid-cta .wrap{display:flex;align-items:center;justify-content:space-between;gap:20px}.mid-cta h2{font-size:clamp(22px,3vw,32px);margin:6px 0}.mid-actions{display:flex;gap:10px;flex-wrap:wrap}.decision-guide{background:#f4f8f5}.decision-list{display:grid;gap:14px}.decision-list>div{padding:16px 18px;background:#fff;border:1px solid #dce7e0;border-radius:14px}.decision-list b{display:block;margin-bottom:6px}.decision-list p{margin:0;color:#41574d}@media(max-width:760px){.decision-grid{grid-template-columns:1fr 1fr}.decision-grid>div:nth-child(2){border-right:0}.decision-grid>div{border-bottom:1px solid #e6e2d9}.mid-cta .wrap{display:block}.mid-actions{margin-top:16px}}\n'''
 with (OUT/"pilot.css").open("a",encoding="utf-8") as fp: fp.write(css_extra)
 shutil.copy2(ROOT/"pilot-v45-5x7/pilot.js",OUT/"pilot.js")

 generated={}
 files=[]

 for intent in SERVICE_ORDER:
  profile=svc.PROFILES[intent]
  source=ROOT/"pilot-v45-5x7"/f"{source_slug}-{intent}.html"
  cards,steps,proofs,feedback=svc.extract_source(source)
  raw=svc.render_page(slug,loc,intent,profile,cards,steps,proofs,feedback)
  raw=postprocess(raw,slug,intent,svc.PROFILES,ex.EXAMS)
  name=f"{slug}-{intent}.html"
  generated[name]=raw
  files.append({"path":f"stage2-production-preview-sajik-13/{name}","family":"service","intent":intent,"h1":f"{row['dong_name']} {profile['service_h1']}","canonical":f"https://englishpt.kr/{slug}-{intent}.html","blueprint":profile["blueprint"]})

 for key in EXAM_ORDER:
  exam=ex.EXAMS[key]; intent=exam["intent"]
  raw=ex.render(slug,loc,key,exam)
  raw=postprocess(raw,slug,intent,svc.PROFILES,ex.EXAMS)
  name=f"{slug}-{intent}.html"
  generated[name]=raw
  files.append({"path":f"stage2-production-preview-sajik-13/{name}","family":"exam","intent":intent,"exam":key,"h1":f"{row['dong_name']} {exam['service']}","canonical":f"https://englishpt.kr/{slug}-{intent}.html","blueprint":exam["blueprint"]})

 all_names=set(generated)
 failures=[]; checks=[]; lengths={}
 forbidden_visible=["V4.5 FULL-DEPTH PILOT","V4.5 EXAM FULL-DEPTH PILOT","5×7 소규모 검수용","이 프로젝트에서는"]
 malformed=["영어회화을","영어과외을","비즈니스영어을","문항를","질의을","응시이","근거이","근거은","제한 제한","'질문 이해'과","페이지은"]
 reserved=set()
 rp=ROOT/"sitemap_95_urls.txt"
 if rp.exists(): reserved={x.strip() for x in rp.read_text(encoding="utf-8").splitlines() if x.strip()}

 for meta in files:
  name=Path(meta["path"]).name; raw=generated[name]; text=visible(raw); lengths[name]=len(text); f=[]
  if len(re.findall(r"<h1\b",raw))!=1:f.append("h1_count")
  if f"<h1>{html.escape(meta['h1'])}</h1>" not in raw:f.append("h1_exact")
  if f'rel="canonical" href="{meta["canonical"]}"' not in raw:f.append("canonical")
  if 'name="robots" content="noindex,nofollow"' not in raw:f.append("noindex")
  if 'data-production-deploy="false"' not in raw:f.append("production_flag")
  if 'class="decision-strip"' not in raw:f.append("decision_strip")
  if 'decision-guide' not in raw:f.append("decision_guide")
  if raw.count("◆ ")<5:f.append("decision_guide_items")
  if 'class="mid-cta"' not in raw:f.append("mid_cta")
  if '<section id="consultation-preview"' not in raw:f.append("consultation_precheck")
  order_tokens=['decision-strip','id="detail"','decision-guide','mid-cta','자주 묻는 질문','더 깊게 보기','class="section related"','id="consultation-preview"']
  positions=[raw.find(x) for x in order_tokens]
  if any(x<0 for x in positions) or positions!=sorted(positions):f.append("conversion_flow_order")
  if any(x in text for x in ["최고의 강사진","성적 향상을 책임","지금 바로 상담 신청"]):f.append("generic_marketing_copy")
  if PHONE_HREF not in raw or PHONE_LABEL not in raw:f.append("phone")
  if 'application/ld+json' not in raw:f.append("schema_missing")
  else:
   try:
    payload=re.search(r'<script type="application/ld\+json">(.*?)</script>',raw,re.S).group(1)
    json.loads(payload)
   except Exception:f.append("schema_invalid")
  expected_other={x for x in all_names if x!=name}
  linked=set(re.findall(r'href="([^"]+\.html)"',raw))
  missing=sorted(expected_other-linked)
  if missing:f.append("missing_related:"+",".join(missing[:3]))
  if any(x in text for x in forbidden_visible):f.append("pilot_copy")
  bad=[x for x in malformed if x in text]
  if bad:f.append("malformed:"+",".join(bad))
  if "place_id" in text or "official_code" in text or "content_seed" in text or "variation_pack_id" in text:f.append("db_internal_visible")
  if "-tos.html" in raw.lower():f.append("standalone_tos_link")
  if meta["canonical"] in reserved:f.append("reserved_95_conflict")
  lo,hi=(4000,7800) if meta["family"]=="service" else (4500,8000)
  if not (lo<=len(text)<=hi):f.append(f"visible_chars:{len(text)}")
  checks.append({"file":name,"family":meta["family"],"intent":meta["intent"],"visible_chars":len(text),"status":"PASS" if not f else "FAIL","failures":f})
  if f:failures.append({"file":name,"failures":f})

 if len(generated)!=13:failures.append({"global":["page_count",len(generated)]})
 if len({m["canonical"] for m in files})!=13:failures.append({"global":["canonical_unique"]})
 if len({Path(m["path"]).name for m in files})!=13:failures.append({"global":["filename_unique"]})

 qa={
  "version":"1.0",
  "status":"PASS" if not failures else "FAIL",
  "stage":"STAGE2_ONE_LOCALITY_X_13_INTENTS_PREVIEW",
  "locality":row["full_name_ko"],
  "region_slug":slug,
  "page_count":len(generated),
  "families":{"service":7,"exam":6},
  "visible_chars":{"min":min(lengths.values()),"max":max(lengths.values()),"avg":round(sum(lengths.values())/len(lengths),1)},
  "variation_adapter":{"variation_pack_id":row["variation_pack_id"],"variation_signature":row["variation_signature"],"dimensions":dims,"base_gold_frame":frame,"source_gold_locality":source_slug},
  "checks":checks,
  "failures":failures,
  "render_qa":"PENDING",
  "safety":{"robots":"noindex,nofollow","live_lead_submission":False,"sitemap":False,"main_merge":False,"production_deploy":False}
 }
 (OUT/"STAGE2_SAJIK_13_QA_V1.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 if failures:
  print(json.dumps({"status":"FAIL","failures":failures[:30]},ensure_ascii=False))
  raise SystemExit(1)

 for name,raw in generated.items():(OUT/name).write_text(raw,encoding="utf-8")
 manifest={
  "version":"1.0",
  "status":"STAGE2_1X13_STATIC_PASS_RENDER_PENDING_USER_REVIEW_REQUIRED_NOT_PRODUCTION",
  "stage":"STAGE2_ONE_LOCALITY_X_13_INTENTS_PREVIEW",
  "locality":{"locality_key":row["locality_key"],"sido":row["sido"],"jurisdiction_full":row["jurisdiction_full"],"dong_name":row["dong_name"],"full_name_ko":row["full_name_ko"],"entity_mix":row["entity_mix"],"region_slug":slug,"landing_eligibility":row["landing_eligibility"],"variation_pack_id":row["variation_pack_id"],"variation_signature":row["variation_signature"],"content_seed":row["content_seed"]},
  "variation_adapter":{"dimensions":dims,"base_gold_frame":frame,"source_gold_locality":source_slug,"note":"Stage 2 validates the integrated production interface. Full multi-locality variation composition is the Stage 3 gate."},
  "gold_sources":{"service":"V4_5_GOLD_SAMPLE_FREEZE_20260922.json","exam":"pilot-v45-exam-5x6/PILOT_EXAM_5X6_GOLD_FREEZE_V1.md"},
  "page_count":13,
  "files":files,
  "tos_policy":{"standalone_page":False,"canonical_exam":"toeic-speaking","aliases":["토스","TOS"]},
  "safety":{"robots":"noindex,nofollow","live_lead_submission":False,"sitemap":False,"main_merge":False,"production_deploy":False}
 }
 (OUT/"STAGE2_SAJIK_13_MANIFEST_V1.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":"PASS","pages":13,"frame":frame,"visible":qa["visible_chars"],"user_review_required":True},ensure_ascii=False))

if __name__=="__main__":
 main()
