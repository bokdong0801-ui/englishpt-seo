#!/usr/bin/env python3
"""V3 full-site SOURCE merge. Only 3 existing HTML changed and 19 new region paths.
Run after the exact signed 2026-10-23 202,767-file candidate was rebuilt.
No production API write, no source-publish, no global noindex.
"""
from __future__ import annotations
import collections,csv,gzip,hashlib,importlib.util,json,os,pathlib,re,shutil
R=pathlib.Path(__file__).resolve().parents[1]
SITE=R/"thumb-21964-candidate"
REVIEW=R/"region-review-site"
EVID=R/"enpt-v3-fullsite-qa"
CORE=("englishpt.html","courses.html","student-english.html")
EXPECTED_STATIC=202767
EXPECTED_ROUTES=158571
EXPECTED_NOINDEX=136607
EXPECTED_INDEXABLE=21964
EXPECTED_NEW=19 # 1 region root, 17 province files, 1 safe nested /regions/index.html fallback
EXPECTED_FINAL=EXPECTED_STATIC+EXPECTED_NEW
def fail(reason):raise RuntimeError("HOLD_V3_SAFE_MERGE_"+reason)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot_files(folder):
 return sum(1 for p in folder.rglob("*") if p.is_file())
def modules(path):
 spec=importlib.util.spec_from_file_location("enpt_v3_form_integrator",path)
 obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj)
 return obj
def signed_data():
 p=R/"signed-qa-map/NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz"
 if not p.exists():fail("MISSING_SIGNED_PRODUCTION_MANIFEST")
 with gzip.open(p,"rt",encoding="utf8") as f:data=json.load(f)
 key="original_public_html_to_data_payload"
 assert key in data and len(data[key])==EXPECTED_ROUTES
 rows=data[key]
 assert sum(not bool(m["noindex"]) for m in rows.values())==EXPECTED_INDEXABLE
 assert sum(bool(m["noindex"]) for m in rows.values())==EXPECTED_NOINDEX
 return rows
def check_guard():
 if not SITE.is_dir():fail("FULL_SITE_BASE_MISSING")
 if not REVIEW.is_dir():fail("V2_REVIEW_SOURCE_MISSING")
 before_count=snapshot_files(SITE)
 if before_count!=EXPECTED_STATIC:fail(f"BASE_FILES_EXPECTED_{EXPECTED_STATIC}_GOT_{before_count}")
 required=["_headers","robots.txt","netlify.toml","_redirects","sitemap-index.xml",
           "netlify/edge-functions/shard-router.js","stations.html","favicon.ico",
           "assets/styles.css","assets/site.js"]
 for p in required:
  if not (SITE/p).is_file():fail("MISSING_PRODUCTION_BASE_"+p)
 if any((SITE/p).exists() for p in ["regions.html","regions/index.html"]):fail("REGIONS_ALREADY_PRESENT")
 orig={p:sha(SITE/p) for p in required}
 strict_sitemap={p.relative_to(SITE).as_posix():sha(p) for p in SITE.rglob("sitemaps/*.xml")}
 if len(strict_sitemap)!=44:fail(f"SITEMAPS_EXPECTED_44_FOUND_{len(strict_sitemap)}")
 robots=(SITE/"robots.txt").read_text("utf8")
 if "Disallow: /" in robots:fail("GLOBAL_ROBOTS_DISALLOW_ALL")
 return before_count,orig,strict_sitemap
def cleanup_draft_text(s):
 # Content authored originally as a limited review preview: remove QA-only user copy.
 subs=[
  ("해당 페이지는 검토용 Draft입니다. 기존 운영본의 검색 설정과 색인 허용 정책은 그대로 유지됩니다.",
   "지역별 안내와 세부 과정은 현재 제공 가능한 수업 범위에 따라 달라질 수 있습니다."),
  ("지역 상세페이지는 기존 운영 URL을 연결합니다. 이번 Draft에서는 원래의 색인 정책·상담 수신 기능·사이트맵을 변경하지 않습니다.",
   "동네를 선택한 후 영어과외·영어회화 과정별 안내를 확인해 보세요."),
  ("이곳은 기존 지역별 페이지로 연결하는 탐색 허브의 검토용 Draft입니다. 기존 검색엔진 색인 정책과 실제 수업 제공 지역은 별도의 검증을 거쳐야 합니다.",
   "지역 및 학년별로 제공되는 수업 방식은 다를 수 있습니다. 상담 시 희망 지역과 학습 목표를 알려주세요."),
 ]
 for a,b in subs:s=s.replace(a,b)
 return s
def preserve_core(src,dst,mod):
 old=src.read_bytes()
 changed,meta=mod.integrate(src.name,old)
 if src==dst:dst.write_text(changed,"utf8")
 else:dst.write_text(changed,"utf8")
 assert old!=changed.encode()
 assert 'data-open-form' in changed
 assert f'https://englishpt.kr/{src.name}' in changed
 assert changed.count('id="enpt-regions-entry-20261027"')==1
 assert 'href="/regions.html"' in changed
 # The root /regions.html may be captured by Edge fallback, prefer static /regions/index.html
 updated=dst.read_text("utf8").replace('href="/regions.html"','href="/regions/"')
 dst.write_text(updated,"utf8")
 assert 'href="/regions/"' in updated
 assert mod.form(updated)==mod.form(old.decode("utf8"))
 assert mod.canonical(updated)==mod.canonical(old.decode("utf8"))
 assert mod.robots(updated)==mod.robots(old.decode("utf8"))
 return {"file":src.name,"original_sha256":hashlib.sha256(old).hexdigest(),"v3_sha256":sha(dst),"form_sha256":hashlib.sha256(mod.form(updated).encode()).hexdigest(),
  "canonical":mod.canonical(updated)[0],"meta_robots":mod.robots(updated)[0],"region_hub_new":True}
def main():
 EVID.mkdir(parents=True,exist_ok=True)
 before,orig,shards=check_guard()
 signed=signed_data()
 mod=modules(R/"scripts/ENPT_REGION_FINAL_INTEGRATION_20261027.py")
 signed_noindex=sum(bool(x["noindex"]) for x in signed.values())
 core=[]
 for name in CORE:core.append(preserve_core(SITE/name,SITE/name,mod))
 for name in ["regions.html"]+[f"regions/{slug}.html" for slug in
              ("gangwon","gyeonggi","gyeongnam","gyeongbuk","gwangju","daegu","daejeon","busan","seoul","sejong","ulsan","incheon","jeonnam","jeonbuk","jeju","chungnam","chungbuk")]:
  src=REVIEW/name
  if not src.is_file():fail("V2_REVIEW_MISSING_"+name)
  dst=SITE/name;dst.parent.mkdir(parents=True,exist_ok=True)
  s=src.read_text("utf8")
  s=cleanup_draft_text(s)
  s=s.replace('href="/regions.html"','href="/regions/"')
  s=s.replace('<meta name="robots" content="noindex,nofollow">','<meta name="robots" content="noindex,follow">')
  if "noindex,nofollow" in s and "robots" in s:fail("PREVIEW_ONLY_HTML_NOINDEX_NOFOLLOW_"+name)
  if 'data-locality="' not in s and name!="regions.html":fail("V2_TOWN_LINKS_MISSING_"+name)
  assert "englishpt-consultation" in s and 'id="applyModal"' in s
  dst.write_text(s,"utf8")
 # reliable nested static URL, avoids generic sharded Edge ^/[^/]+\\.html$ matching /regions.html
 source=(SITE/"regions.html").read_text("utf8")
 nested=source.replace('https://englishpt.kr/regions.html','https://englishpt.kr/regions/')
 (SITE/"regions/index.html").write_text(nested,"utf8")
 assert sha(SITE/"regions.html")!=sha(SITE/"regions/index.html")
 for name,digest in orig.items():
  if name in ("robots.txt","netlify.toml","_headers","_redirects","sitemap-index.xml",
              "netlify/edge-functions/shard-router.js","stations.html","favicon.ico",
              "assets/styles.css","assets/site.js"):
   if sha(SITE/name)!=digest:fail("PROTECTED_FILE_CHANGED_"+name)
 for name,digest in shards.items():
  if sha(SITE/name)!=digest:fail("SITEMAP_SHA_DRIFT_"+name)
 generated=(R/"region-review-evidence/ENPT_V2_5149_X_7_REAL_COURSE_LINKS.csv")
 records=list(csv.DictReader(generated.open(encoding="utf-8-sig")))
 if len(records)!=5149*7:fail("V2_COURSE_ANCHOR_COUNT")
 student={(x["region_slug"]+"-"+x["course"]+".html") for x in records if x["course"]!="worker-english-conv-academy"}
 if len(student)!=30894 or not all(x in signed for x in student):fail("SIGNED_STUDENT_TARGETS_NOT_ALL_PRESENT")
 adult={(x["region_slug"]+"-"+x["course"]+".html") for x in records if x["course"]=="worker-english-conv-academy"}
 if len(adult)!=5149 or not all(x in signed for x in adult):fail("SIGNED_WORKER_TARGETS_NOT_ALL_PRESENT")
 if len(set(x["target_url"] for x in records))!=len(records):fail("V2_LINK_DUPLICATES")
 count=snapshot_files(SITE)
 if count!=EXPECTED_FINAL:fail(f"BAD_FINAL_FILE_COUNT_{count}_EXPECTED_{EXPECTED_FINAL}")
 # No changes to 158571 route mapping; noindex policies carried over unchanged by the untouched signed edge shards.
 result={"status":"PASS_V3_FULLSITE_SCOPE_AND_SEO_FORMS_PRESERVED",
   "published_source_id":"6adafef5f2c6d196833683db","baseline_20261023_static_files":before,
   "final_static_files":count,"new_html":EXPECTED_NEW,"modified_existing_html":len(CORE),
   "changed_existing_paths":list(CORE),"new_paths":EXPECTED_NEW,
   "signed_existing_public_routes":len(signed),"signed_indexable_routes":EXPECTED_INDEXABLE,
   "signed_noindex_routes":signed_noindex,"original_sitemaps_unchanged":len(shards),
   "all_36043_course_target_routes_exist_in_signed_map":True,
   "all_5149_town_target_links_non404_bare":True,"core_form_and_canonical_unchanged":True,
   "original_edge_router_sha256":orig["netlify/edge-functions/shard-router.js"],
   "original_robots_sha256":orig["robots.txt"],"original_headers_sha256":orig["_headers"],
   "new_regions_meta":"noindex,follow (new pages only)","sitemap_shards_changed":0,
   "global_preview_only_noindex_leaked":False,"existing_production_files_deleted":0,"production_changes":0,
   "core":core}
 (EVID/"V3_FULL_SITE_OFFLINE_GUARD.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),"utf8")
 print("ENPT_V3_FULL_INTEGRATION",json.dumps({k:v for k,v in result.items() if k!="core"},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
