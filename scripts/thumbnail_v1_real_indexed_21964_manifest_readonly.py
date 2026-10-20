#!/usr/bin/env python3
# coding: utf-8
"""Read-only, fail-closed 21,964 route to square thumbnail metadata mapping.
Input: signed-off full release GitHub Actions QA artifact and canonical data/stations.json.
No Netlify mutations, no image files, no full-site source archive download.
"""
import collections
import csv
import datetime
import gzip
import hashlib
import html
import json
import pathlib
import re
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"thumb-21964-outputs"
OUT.mkdir(exist_ok=True)
QA_DIR=ROOT/"qa-source"
QA_MAP=QA_DIR/"NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz"
EVIDENCE=QA_DIR/"FINAL_NAVER_GOOGLE_VERIFICATION_META_QA.json"
BASE="https://englishpt.kr/"
SOURCE_RUN="https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39234109195"
SOURCE_ARCHIVE_SHA="6d0272d1601a1a47abeccc4d740359af9e7678293ee0a3d257eecd2ca478d884"
NAVER_GOOGLE_PUBLISHED_DEPLOY="6ad5eb4918f9411c4d5e1ba4"

# 23 actual station route intent slugs; distinct academic purpose and mode preserved.
STATION_INTENTS={
 "adult-english-conv-academy":("conversation","성인 영어회화","학원",["성인","영어회화","학원"],"성인 회화 · 과정 안내"),
 "beginner-english-conv":("beginner","왕초보 영어회화","회화",["왕초보","영어회화"],"기초 영어 · 쉬운 표현"),
 "biz-business-conv":("worker","비즈니스 영어회화","회화",["비즈니스","영어회화"],"업무 영어 · 회화 준비"),
 "duolingo-academy":("duolingo","Duolingo English Test 학원","학원",["Duolingo","English Test","학원"],"영어시험 · 과정 안내"),
 "duolingo":("duolingo","Duolingo English Test 과외","과외",["Duolingo","English Test","과외"],"영어시험 · 1:1 안내"),
 "elem-tutor":("elem","초등학생 영어과외","과외",["초등학생","영어과외"],"기초 영어 · 학습관리"),
 "english-conv-academy":("conversation","영어회화 학원","학원",["영어회화","학원"],"회화 과정 · 수업 안내"),
 "high-conv":("high","고등학생 영어회화","회화",["고등학생","영어회화"],"학생 영어 · 말하기"),
 "housewife-conv":("conversation","주부 영어회화","회화",["주부","영어회화"],"생활 영어 · 기초 회화"),
 "ielts-academy":("ielts","IELTS 학원","학원",["IELTS","학원"],"목표 Band · 4영역"),
 "ielts":("ielts","IELTS 과외","과외",["IELTS","과외"],"목표 Band · 개별 준비"),
 "jobseeker-conv":("worker","취준생 영어회화","회화",["취준생","영어회화"],"면접 영어 · 말하기"),
 "mid-conv":("mid","중학생 영어회화","회화",["중학생","영어회화"],"중학생 영어 · 회화"),
 "opic-academy":("opic","OPIc 학원","학원",["OPIc","학원"],"목표 등급 · 시험 안내"),
 "opic":("opic","OPIc 과외","과외",["OPIc","과외"],"실전 말하기 · 등급"),
 "toefl-academy":("toefl","TOEFL 학원","학원",["TOEFL","학원"],"점수 목표 · 영역별"),
 "toefl":("toefl","TOEFL 과외","과외",["TOEFL","과외"],"목표 점수 · 1:1 준비"),
 "toeic-academy":("toeic","TOEIC 학원","학원",["TOEIC","학원"],"LC·RC · 점수 대비"),
 "toeic-speaking-academy":("toeic-speaking","TOEIC Speaking 학원","학원",["TOEIC","Speaking","학원"],"시험 말하기 · 목표 레벨"),
 "toeic-speaking":("toeic-speaking","TOEIC Speaking 과외","과외",["TOEIC","Speaking","과외"],"말하기 · 1:1 대비"),
 "toeic":("toeic","TOEIC 과외","과외",["TOEIC","과외"],"LC·RC · 맞춤 준비"),
 "univ-conv":("misc","대학생 영어회화","회화",["대학생","영어회화"],"발표 · 회화 준비"),
 "worker-english-conv-academy":("worker","직장인 영어회화 학원","학원",["직장인","영어회화","학원"],"실용 회화 · 과정 안내"),
}
HUBS={
 "courses.html":("과정 찾기",["영어","과정 찾기"]),
 "englishpt.html":("영어과외",["영어","과외"]),
 "english-conversation.html":("영어회화",["영어","회화"]),
 "exam-english.html":("시험영어",["시험","영어"]),
 "student-english.html":("학생영어",["학생","영어"]),
 "stations.html":("역별 영어수업",["역별","영어수업"]),
}
BASE_PALETTE={
 "main":"#EFA296","hub":"#A5C3CE","region":"#C1B6A0",
 "beginner":"#A5C9AE","conversation":"#A5C7C6","worker":"#B5A9D0",
 "elem":"#B5C5AB","mid":"#A9C3E4","high":"#D2B4A9",
 "toeic":"#A6C5E5","toeic-speaking":"#D5B595",
 "opic":"#BEADE1","ielts":"#E5C493","toefl":"#A6C6BA",
 "duolingo":"#BCD5A5","misc":"#C4CEC5","international":"#B9ACCB"
}
RE_EXAM=[
 (re.compile("토익스피킹|TOEIC[ -]?Speaking",re.I),"TOEIC Speaking"),
 (re.compile("아이엘츠|IELTS",re.I),"IELTS"),
 (re.compile("듀오링고|Duolingo",re.I),"Duolingo English Test"),
 (re.compile("오픽|OPIc",re.I),"OPIc"),
 (re.compile("토플|TOEFL",re.I),"TOEFL"),
 (re.compile("토익|TOEIC",re.I),"TOEIC"),
]
def normalise(text):
 for rx,replace in RE_EXAM:text=rx.sub(replace,text)
 return re.sub(r"\s+"," ",text).strip(" -|")
def extract_h1(contents):
 m=re.search(r"<h1\b[^>]*>(.*?)</h1>",contents,re.I|re.S)
 if not m:return ""
 return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",m.group(1)))).strip()
def title_lines(keyword):
 # Stable and semantic; fitting must be checked in separate render QA.
 for exam in ("TOEIC Speaking","Duolingo English Test","TOEIC","OPIc","IELTS","TOEFL"):
  if keyword.startswith(exam):
   remainder=keyword[len(exam):].strip()
   if exam=="TOEIC Speaking":return ["TOEIC","Speaking"]+([remainder] if remainder else [])
   if exam=="Duolingo English Test":return ["Duolingo","English Test"]+([remainder] if remainder else [])
   return [exam]+([remainder] if remainder else [])
 kw=keyword.replace(" ","")
 for marker in ("영어과외","영어학원","영어회화","영어수업"):
  if marker in kw and not kw.startswith(marker):
   i=kw.index(marker)
   left=kw[:i];right=kw[i:]
   if left and right:return [left,right]
 if len(keyword)<=8:return [keyword]
 words=keyword.split()
 if len(words)>=2:return [" ".join(words[:len(words)//2])," ".join(words[len(words)//2:])]
 return [keyword]
def intent_from_local_h1(route):
 path=ROOT/route
 if not path.is_file():return None,"REPOSITORY_HTML_NOT_FOUND"
 t=extract_h1(path.read_text("utf8"))
 if not t:return None,"REPOSITORY_HTML_H1_MISSING"
 if not t.startswith("송현동"):return None,"REGION_PREFIX_NOT_IN_H1"
 kw=normalise(t.removeprefix("송현동").strip())
 if not kw or len(kw)>34:return None,"REGIONAL_H1_NOT_CONCISE"
 return kw,"REPO_H1_SEMANTIC_ONLY"
def category_from_keyword(keyword):
 for pattern,cat in [("TOEIC Speaking","toeic-speaking"),("TOEIC","toeic"),("OPIc","opic"),("IELTS","ielts"),("TOEFL","toefl"),
  ("Duolingo","duolingo"),("국제학교","international"),("초등","elem"),("중학생","mid"),("고등","high"),
  ("직장인","worker"),("취준","worker"),("왕초보","beginner"),("기초","beginner"),("영어회화","conversation")]:
  if pattern in keyword:return cat
 return "misc"
def colour_for(key,cat,used):
 base=BASE_PALETTE.get(cat,BASE_PALETTE["misc"])
 orig=tuple(bytes.fromhex(base[1:]))
 for tries in range(2048):
  h=hashlib.blake2b((key+"|"+str(tries)).encode("utf8"),digest_size=6).digest()
  rgb=tuple(min(238,max(155,orig[i]+(h[i]%49)-24)) for i in range(3))
  color="#"+ "".join(f"{x:02X}" for x in rgb)
  if color not in used:
   used.add(color);return color
 raise ValueError("Palette color uniqueness exhausted")
def write_csv(name,rows,cols):
 with (OUT/name).open("w",encoding="utf-8-sig",newline="") as f:
  writer=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore");writer.writeheader();writer.writerows(rows)

with gzip.open(QA_MAP,"rt",encoding="utf8") as file: signed=json.load(file)
proof=json.loads(EVIDENCE.read_text("utf8"))
stations_json=json.loads((ROOT/"data/stations.json").read_text("utf8"))
stations=stations_json["stations"]
station_by_slug={s["slug"]:s for s in stations}
if len(stations)!=911 or len(station_by_slug)!=911 or stations_json["station_count"]!=911:
 raise SystemExit("HOLD station canonical dictionary does not contain 911 unique records")
routes=signed["original_public_html_to_data_payload"]
if len(routes)!=158571 or sum(not d["noindex"] for d in routes.values())!=21964:
 raise SystemExit("HOLD full URL signed manifest no longer matches index/noindex count")
if proof["new_candidate_sha256"]!=SOURCE_ARCHIVE_SHA or proof["sitemap_url_count"]!=21964:
 raise SystemExit("HOLD source QA artifact not the approved audited build")
actual_indexed=sorted(k for k,v in routes.items() if not v["noindex"])
noindexed=sorted(k for k,v in routes.items() if v["noindex"])
if len(noindexed)!=136607:raise SystemExit("HOLD noindex partition")
station_paths=[r for r in actual_indexed if r.startswith("station-")]
if len(station_paths)!=21864:raise SystemExit("HOLD station SEO count")
if len(STATION_INTENTS)!=23:raise SystemExit("HOLD station course intent count")
counts=collections.Counter();intents=collections.Counter();statuses=collections.Counter()
unused=[];errors=[];result=[];held=[];unique_colours=set()
columns=[
 "route","canonical_url","indexable","route_type","location_name","location_slug",
 "intent_slug","category","course_mode","search_keyword","header_label",
 "title_line_1","title_line_2","title_line_3","subtitle",
 "palette_family","accent_hex","image_key","planned_image_path","planned_og_image_url",
 "source_edge_path","source_page_sha1","mapping_status","mapping_evidence","hold_reason"
]
for route in actual_indexed:
 meta=routes[route];basename=route[:-5]
 typ="";slug="";loc="";intent="";category="misc";mode="";keyword="";lines=[];subtitle=""
 hold="";source_kind=""
 if route in HUBS:
  typ="national_hub";loc="ENGLISH PT";slug="englishpt";intent=basename;category="main" if route=="englishpt.html" else "hub"
  keyword,lines=HUBS[route];subtitle="1:1 맞춤 · 영어 수업 안내";source_kind="SOURCE_QA_ROUTE_AND_FIXED_HUB"
 elif route.startswith("station-"):
  typ="station";part=basename[len("station-"):]
  if part in station_by_slug:
   slug=part;intent="station-hub"
   keyword="역별 영어수업";lines=["영어","수업 안내"];subtitle="역 주변 · 과정 찾기";category="region";mode="안내"
  else:
   # Exact prefix against the verified canonical 911 station slugs, then exact intent.
   # Avoid a wrong intent from suffix collisions and keep the station slug untouched.
   matches=[(candidate,part[len(candidate)+1:]) for candidate in station_by_slug
            if part.startswith(candidate+"-") and part[len(candidate)+1:] in STATION_INTENTS]
   if len(matches)==1:
    slug,intent=matches[0]
    category,keyword,mode,lines,subtitle=STATION_INTENTS[intent]
   else:
    hold="UNKNOWN_OR_AMBIGUOUS_STATION_SLUG_OR_INTENT"
  if slug:
   loc=station_by_slug[slug]["name"]
   if not loc:hold="MISSING_OFFICIAL_STATION_NAME"
  source_kind="VERIFIED_STATION_DATA_AND_URL_SUFFIX"
 else:
  typ="regional";loc="송현동";slug="dalseo-songhyeondong"
  if not route.startswith(slug):hold="UNEXPECTED_NONSTATION_REGION"
  intent=basename.removeprefix(slug).lstrip("-") or "region-hub"
  extracted,reason=intent_from_local_h1(route)
  if extracted:
   keyword=extracted;lines=title_lines(keyword);category=category_from_keyword(keyword)
   subtitle="학습 목적 · 수업 방식 안내"
   source_kind=reason
  else:
   hold=reason;source_kind="SIGNED_URL_ROUTE_ONLY"
 if not keyword:keyword="";hold=hold or "KEYWORD_UNRESOLVED"
 if not lines or len(lines)>3:hold=hold or "INVALID_TITLE_LINES"
 if any(len(v)>27 for v in lines):hold=hold or "LONG_LINE_NEEDS_MANUAL_FITTING"
 if not loc:hold=hold or "LOCATION_UNRESOLVED"
 status="HOLD_REVIEW" if hold else "READY_METADATA_ONLY"
 col=colour_for(route,category,unique_colours)
 key=hashlib.sha256(("square-v1|"+route).encode("utf8")).hexdigest()[:20]
 image_path="assets/images/seo-square/v1/"+key+".jpg"
 record={
  "route":route,"canonical_url":BASE+route,"indexable":"TRUE","route_type":typ,
  "location_name":loc,"location_slug":slug,"intent_slug":intent,
  "category":category,"course_mode":mode,"search_keyword":keyword,"header_label":loc,
  "title_line_1":lines[0] if len(lines)>0 else "",
  "title_line_2":lines[1] if len(lines)>1 else "",
  "title_line_3":lines[2] if len(lines)>2 else "",
  "subtitle":subtitle,"palette_family":category,"accent_hex":col,
  "image_key":key,"planned_image_path":image_path,
  "planned_og_image_url":BASE+image_path,
  "source_edge_path":meta["to"],"source_page_sha1":meta["sha1"],
  "mapping_status":status,"mapping_evidence":source_kind,"hold_reason":hold
 }
 result.append(record)
 counts[typ]+=1;statuses[status]+=1
 if typ=="station":intents[intent]+=1
 if hold:held.append(record)
 if typ=="station":unused.append(slug)
if len(result)!=21964 or len(set(x["route"] for x in result))!=21964:
 errors.append("URL count or uniqueness mismatch")
if len(unique_colours)!=21964:errors.append("Accent colour uniqueness fail")
if len(set(x["image_key"] for x in result))!=21964:errors.append("Image key collision")
if counts["station"]!=21864 or counts["regional"]!=94 or counts["national_hub"]!=6:
 errors.append("Exact indexed route family breakdown differs")
by_station=collections.Counter(unused)
if len(by_station)!=911 or any(v!=24 for v in by_station.values()):
 errors.append("Every station must have exactly 24 indexable URL routes")
# The signed route inventory, rather than an incidental suffix count, is authoritative.
expected_station_routes={f"station-{slug}.html" for slug in station_by_slug}
expected_station_routes.update(f"station-{slug}-{intent}.html" for slug in station_by_slug for intent in STATION_INTENTS)
if set(station_paths)!=expected_station_routes:
 errors.append("Actual station route keys differ from authoritative exact 911 by 24 cross product")
# Every mapped row must retain the same station name and exact intent as its route.
for row in result:
 if row["route_type"]!="station":continue
 expected_station=f"station-{row['location_slug']}"
 expected_route=expected_station+(".html" if row["intent_slug"]=="station-hub" else f"-{row['intent_slug']}.html")
 if row["route"]!=expected_route:
  errors.append("Incorrect station/intent decomposition: "+row["route"])
  if len(errors)>=25:break
# These independent checks catch mistakes while allowing the original map to be rebuilt.
if intents["station-hub"]!=911:errors.append("Station hub count not 911")
if len(held)>0 and any(x["route_type"]=="station" for x in held):
 errors.append("Station routes unexpectedly HOLD")
if errors:raise SystemExit("HOLD: "+str(errors))
write_csv("ALL_21964_INDEXABLE_THUMBNAIL_MAP.csv",result,columns)
write_csv("HOLD_MANUAL_REVIEW.csv",held,columns)
write_csv("STATIONS_911_VERIFIED_DIMENSION.csv",[
 {"station_slug":s["slug"],"station_name":s["name"],
  "routes_in_indexable_map":by_station[s["slug"]],
  "rail_lines":";".join(s.get("lines") or [])} for s in stations],
 ["station_slug","station_name","routes_in_indexable_map","rail_lines"])
write_csv("STATION_INTENTS_23_DIMENSION.csv",[
 {"intent_slug":i,"category":v[0],"keyword":v[1],"course_mode":v[2],
  "title_layout":" | ".join(v[3]),"subtitle":v[4],
  "expected_indexable_urls":intents[i]} for i,v in sorted(STATION_INTENTS.items())],
 ["intent_slug","category","keyword","course_mode","title_layout","subtitle","expected_indexable_urls"])
write_csv("PREVIEW_120_VALIDATED_ROUTE_ROWS.csv",result[:120],columns)
with (OUT/"ALL_21964_IMAGE_RENDER_PAYLOAD.jsonl.gz").open("wb") as raw:
 with gzip.GzipFile(fileobj=raw,mode="wb",compresslevel=6) as z:
  for r in result:
   z.write((json.dumps({
     "route":r["route"],"header":r["header_label"],
     "lines":[r[k] for k in ("title_line_1","title_line_2","title_line_3") if r[k]],
     "subtitle":r["subtitle"],"accent_hex":r["accent_hex"],
     "category":r["category"],"output_path":r["planned_image_path"],
     "mapping_status":r["mapping_status"]
   },ensure_ascii=False,separators=(",",":"))+"\n").encode("utf8"))
# A noindex fence prevents accidentally wiring image metadata to excluded routes.
digest=hashlib.sha256("\n".join(noindexed).encode("utf8")).hexdigest()
(OUT/"NOINDEX_LOCK_136607_SHA256.txt").write_text(
 "count=136607\nsha256_sorted_newline_delimited_url_paths="+digest+
 "\nNo noindex route is part of the 21,964 indexable mapping.\n",encoding="utf8")
schema={c:{"required":c in ["route","canonical_url","indexable","route_type","mapping_status"],
  "source":"signed Netlify full production QA manifest" if c in
   ["route","source_edge_path","source_page_sha1","indexable"] else
   "rule-based planned image metadata; NOT published"} for c in columns}
(OUT/"SCHEMA_25_FIELDS.json").write_text(json.dumps(schema,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
report={
 "status":"PASS_REAL_21964_ROUTE_MAPPING_SOURCE_VERIFIED_WITH_REVIEW_HOLDS",
 "generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "source_manifest":SOURCE_RUN,
 "source_full_release_sha256":SOURCE_ARCHIVE_SHA,
 "prior_verified_published_deploy_id":NAVER_GOOGLE_PUBLISHED_DEPLOY,
 "original_public_urls":len(routes),"indexable_urls":len(actual_indexed),
 "noindex_fence_count":len(noindexed),"noindex_guard_sha256":digest,
 "indexed_family_counts":dict(counts),"station_count":len(stations),
 "station_course_intents":len(STATION_INTENTS),
 "station_urls_per_station":24,
 "mapping_status":dict(statuses),
 "unique_accent_colors":len(unique_colours),
 "unique_planned_image_paths":len({r["planned_image_path"] for r in result}),
 "final_png_jpeg_images_generated":0,
 "production_og_metadata_changed":False,
 "production_deploy_triggered":False,
 "search_volume_externally_verified":False,
 "notes":[
   "Verified real 158571 route identities, 21964 indexable and 136607 noindex from published signed QA archive.",
   "Station 911 names and station slugs originate from repository data/stations.json, not guessed.",
   "Each indexable station URL joins one of 23 intent suffixes or 911 station hubs.",
   "Regional page H1 is sourced only from available repository HTML and must be verified against live on deployment.",
   "READY_METADATA_ONLY denotes route-to-planned-image metadata readiness; no actual image asset generated or website updated.",
   "HOLD_REVIEW rows must be resolved before rendering or release.",
   "Square image SEO metadata still needs rendering, QA and explicitly approved Draft/Production stages."
 ],
 "errors":[]
}
(OUT/"QA_21964_REAL_MAPPING_REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("ENPT_THUMBNAIL_REAL_INDEXED_MAPPING_RESULT",json.dumps(report,ensure_ascii=False),flush=True)
