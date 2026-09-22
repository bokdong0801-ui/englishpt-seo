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
 # Preview copy: eliminate pilot-only language while retaining noindex safety.
 raw=raw.replace('V4.5 FULL-DEPTH PILOT · noindex','V4.5 PRODUCTION PREVIEW · noindex')
 raw=raw.replace('V4.5 EXAM FULL-DEPTH PILOT · noindex','V4.5 EXAM PRODUCTION PREVIEW · noindex')
 raw=raw.replace('현재 페이지는 5×7 소규모 검수용이라 폼의 실제 전송은 비활성화되어 있습니다.','현재 페이지는 배포 전 production preview라 폼의 실제 전송은 비활성화되어 있습니다.')
 raw=raw.replace('Full-depth 검수용 페이지 · production 미배포','Production preview · noindex · 미배포')
 raw=raw.replace('시험형 Full-depth 검수용 · production 미배포','시험형 Production preview · noindex · 미배포')
 raw=raw.replace('파일럿 폼','검수용 폼').replace('파일럿의 상담 폼','검수용 상담 폼').replace('이 파일럿','이 배포 전 검수 페이지')
 # Connect both frozen families: every page links to the other 12 Sajikdong intent pages.
 links=unified_links(slug,current,service_profiles,exam_map)
 raw,n=re.subn(r'(<div class="links">)[\s\S]*?(</div>)',lambda m:m.group(1)+links+m.group(2),raw,count=1)
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
 malformed=["영어회화을","영어과외을","비즈니스영어을","문항를","질의을","응시이","근거이","근거은","제한 제한","'질문 이해'과"]
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
  lo,hi=(4000,7000) if meta["family"]=="service" else (4500,7500)
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
